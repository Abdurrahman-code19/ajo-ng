#!/usr/bin/env python3
"""
test_migrations — prove the schema enforces the product rules, against a real
Postgres built only from the migration files.

    python3 scripts/test_migrations.py            # build a scratch DB and test
    python3 scripts/test_migrations.py --keep     # leave the scratch DB behind

The domain tests in packages/domain check the rules as the TypeScript code
understands them. That is not the same claim as "the database will not let a row
break them", and only a real database makes the second claim. A rule enforced in
one layer and forgotten in the other is a rule that will be violated the first
time something writes to the table without going through the application.

Every case below is a statement the product makes, expressed as a transaction
that must succeed or must fail:

  * an Ajo holds 5 to 20 members, and 3, 4, 21 and 25 are all rejected
  * position_count defaults to 10, so omitting it is not a way around the rule
  * the creator occupies one of the positions rather than one on top of them,
    so a ten-member Ajo is one organiser and nine invitees
  * an Ajo cannot be committed without its organiser being a member of it
  * an Ajo cannot leave DRAFT until at least five positions actually exist
  * reference data is present, because an Ajo cannot even be created without a
    contribution frequency to point at
  * the ledger stays balanced and stays append-only
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
import sys



# A base fixture: one active user and the monthly frequency every case needs.
USER = "INSERT INTO users (auth_subject_id, email, status) VALUES ('{sid}', '{email}', 'active');"

NEW_AJO = """
INSERT INTO ajos (organizer_user_id, name, contribution_amount_kobo, position_count,
                  total_rounds, frequency_id, enrollment_opens_at, enrollment_closes_at)
SELECT u.id, '{name}', 100000, {positions}, {positions}, cf.id, now(), now() + interval '5 days'
  FROM users u, contribution_frequencies cf
 WHERE cf.code = 'monthly' AND u.email = '{email}';
"""


class Failure(Exception):
    pass


def psql(db: str, sql: str) -> str:
    proc = subprocess.run(
        pg.psql(db, "-tAF", "|", "-c", sql),
        capture_output=True,
        text=True,
    )
    return (proc.stdout or "") + (proc.stderr or "")


def must_succeed(db: str, label: str, sql: str) -> str:
    out = psql(db, sql)
    if "ERROR" in out:
        raise Failure(f"{label}: expected success but got\n    {out.strip()[:300]}")
    return out


def must_fail(db: str, label: str, sql: str, expect: str | None = None) -> str:
    out = psql(db, sql)
    if "ERROR" not in out:
        raise Failure(f"{label}: expected a failure but the statement succeeded")
    if expect and expect not in out:
        raise Failure(
            f"{label}: rejected, but not for the expected reason ({expect!r})\n"
            f"    got: {out.strip()[:300]}"
        )
    return out


def transaction(body: str) -> str:
    """
    Wrap a case so it leaves nothing behind even if it fails.

    `SET CONSTRAINTS ALL IMMEDIATE` is what makes this work for the invariants
    that are enforced by a DEFERRABLE INITIALLY DEFERRED constraint trigger. Those
    fire at COMMIT, so a plain ROLLBACK would skip the check entirely and the case
    would pass for the wrong reason. Forcing them to run now means the assertion
    is genuinely tested and the transaction can still be rolled back.
    """
    return f"BEGIN;\n{body}\nSET CONSTRAINTS ALL IMMEDIATE;\nROLLBACK;"


# ---------------------------------------------------------------------------
# Cases. Each returns a short human-readable line describing what it proved.
# ---------------------------------------------------------------------------

CASES = []


def case(name: str):
    def register(fn):
        CASES.append((name, fn))
        return fn

    return register


def _organizer(
    db: str,
    key: str,
    positions: int = 10,
    rows: int | None = None,
) -> str:
    """
    Build a user and an Ajo, plus its position rows.

    `positions` is what the Ajo declares in position_count; `rows` is how many
    ajo_positions rows are actually created. They are separate on purpose: the
    draft-exit floor is precisely the rule that they have to agree, so a case
    that always created all the rows would never test it. `rows` defaults to
    `positions`.
    """
    email = f"{key}@example.ng"
    n = positions if rows is None else rows
    body = USER.format(sid=f"t-{key}", email=email)
    body += NEW_AJO.format(name=key, positions=positions, email=email)
    if n:
        body += f"""
INSERT INTO ajo_positions (ajo_id, position_number, status)
SELECT a.id, g, 'open' FROM ajos a, generate_series(1, {n}) g
 WHERE a.name = '{key}';
"""
    return body


@case("an Ajo holds 5 to 20 members")
def _size(db: str) -> str:
    for bad in (1, 3, 4, 21, 25, 100):
        sql = transaction(
            _organizer(db, f"size-{bad}", positions=bad)
        )
        must_fail(
            db,
            f"position_count={bad}",
            sql,
            expect="ajos_position_count_within_bounds",
        )
    for good in (5, 10, 20):
        must_succeed(
            db,
            f"position_count={good}",
            transaction(_organizer(db, f"size-{good}", positions=good)),
        )
    return "rejects 1, 3, 4, 21, 25, 100; accepts 5, 10 and 20"


@case("position_count defaults to 10")
def _default(db: str) -> str:
    out = must_succeed(
        db,
        "omitted position_count",
        transaction(
            USER.format(sid="t-def", email="def@example.ng")
            + """
INSERT INTO ajos (organizer_user_id, name, contribution_amount_kobo, total_rounds,
                  frequency_id, enrollment_opens_at, enrollment_closes_at)
SELECT u.id, 'defaulted', 100000, 10, cf.id, now(), now() + interval '5 days'
  FROM users u, contribution_frequencies cf
 WHERE cf.code = 'monthly' AND u.email = 'def@example.ng';
INSERT INTO ajo_positions (ajo_id, position_number, status)
SELECT a.id, g, 'open' FROM ajos a, generate_series(1, a.position_count) g
 WHERE a.name = 'defaulted';
SELECT position_count FROM ajos WHERE name = 'defaulted';
"""
        ),
    )
    if "10" not in out:
        raise Failure(f"expected the default to be 10, got: {out.strip()[:200]}")
    return "omitting position_count yields 10, so the rule cannot be bypassed"


@case("a pre-existing Ajo below 5 is grandfathered, not rejected")
def _grandfathered(db: str) -> str:
    """
    NOT VALID is deliberate, so it is pinned here.

    The database the schema was adopted from contains one three-member Ajo whose
    append-only ledger cannot be removed. Adding the constraint NOT VALID keeps
    that row while enforcing the rule on everything after it. If someone
    "tidies" this into a plain ADD CONSTRAINT, the migration starts failing on
    any database that has that history, and this case is what notices.
    """
    out = psql(
        db,
        "SELECT convalidated FROM pg_constraint "
        "WHERE conname = 'ajos_position_count_within_bounds';",
    )
    if "f" not in out:
        raise Failure(
            "expected the constraint to be NOT VALID so a pre-existing "
            f"three-member Ajo can be grandfathered, got convalidated: {out.strip()[:120]}"
        )

    # NOT VALID must not weaken the rule for anything written from now on.
    for bad in (3, 4, 21):
        must_fail(
            db,
            f"post-migration position_count={bad}",
            transaction(_organizer(db, f"grand-{bad}", positions=bad)),
            expect="ajos_position_count_within_bounds",
        )
    return (
        "the constraint is NOT VALID, so a legacy three-member Ajo survives, "
        "while every new Ajo is still held to 5 to 20"
    )


@case("the creator occupies one of the positions")
def _creator(db: str) -> str:
    out = must_succeed(
        db,
        "creator membership",
        transaction(
            _organizer(db, "creator", positions=10)
            + """
SELECT 'memberships=' || (SELECT count(*) FROM ajo_members m
  JOIN ajos a ON a.id = m.ajo_id JOIN users u ON u.id = m.user_id
 WHERE a.name = 'creator' AND u.email = 'creator@example.ng');
SELECT 'position=' || (SELECT p.position_number FROM ajo_members m
  JOIN ajos a ON a.id = m.ajo_id JOIN users u ON u.id = m.user_id
  JOIN ajo_positions p ON p.id = m.position_id
 WHERE a.name = 'creator' AND u.email = 'creator@example.ng');
SELECT 'open_seats=' || (SELECT count(*) FROM ajo_positions p
  JOIN ajos a ON a.id = p.ajo_id
 WHERE a.name = 'creator' AND p.status = 'open');
"""
        ),
    )
    if "memberships=1" not in out:
        raise Failure(f"organizer is not a member exactly once: {out.strip()[:200]}")
    if "position=1" not in out:
        raise Failure(f"organizer does not hold position 1: {out.strip()[:200]}")
    if "open_seats=9" not in out:
        raise Failure(
            "a ten-member Ajo must have nine seats left for invitees, "
            f"got: {out.strip()[:200]}"
        )
    return "organizer is a member in position 1, leaving 9 of 10 seats to invite"


@case("an Ajo cannot commit without its organizer being a member")
def _creator_required(db: str) -> str:
    must_fail(
        db,
        "orphan Ajo",
        transaction(_organizer(db, "orphan", positions=10, rows=0)),
        expect="who is not a member of it",
    )
    return "an Ajo with no positions is refused at COMMIT, not left half-built"


@case("an Ajo cannot leave DRAFT below 5 positions")
def _draft_exit(db: str) -> str:
    for rows, should_pass in ((4, False), (5, True), (2, False), (0, False)):
        key = f"draft-{rows}-{should_pass}"
        body = _organizer(db, key, positions=10, rows=rows)
        body += f"UPDATE ajos SET status = 'enrollment' WHERE name = '{key}';"
        if should_pass:
            must_succeed(db, f"draft exit with {rows} positions", transaction(body))
        else:
            must_fail(
                db,
                f"draft exit with {rows} positions",
                transaction(body),
                expect="at least 5",
            )
    return "rejects 0, 2 and 4 positions; allows 5, even when the Ajo declares 10"


@case("reference data is present")
def _reference(db: str) -> str:
    for table, want in (
        ("contribution_frequencies", 4),
        ("roles", 6),
        ("payment_channels", 3),
        ("document_types", 10),
        ("verification_check_types", 7),
        ("dispute_reasons", 8),
        ("platform_settings", 7),
    ):
        out = psql(db, f"SELECT count(*) FROM {table};")
        got = out.strip().splitlines()[0] if out.strip() else "?"
        if got != str(want):
            raise Failure(f"{table}: expected {want} rows, got {got!r}")
    return "4 frequencies, 6 roles, 3 channels, 10 document types, 7 checks, 8 dispute reasons, 7 settings"


@case("the ledger stays balanced and append-only")
def _ledger(db: str) -> str:
    # The invariant: at least two postings whose signed amounts sum to zero. The
    # escrow account is a contra account, so a contribution is a debit against
    # escrow and a credit against contributions receivable, and the two sides
    # cancel.
    def entry(postings: str) -> str:
        # member_id is a real foreign key onto ajo_members and the balance
        # invariant does not depend on it, so it is left unset rather than
        # dragging a user, an Ajo and a membership into a ledger test. The sign
        # is likewise not supplied: signed_kobo is generated from side and
        # amount_kobo, which is what stops a posting from lying about which way
        # the money moved.
        return f"""
DO $$
DECLARE v_tx uuid := gen_random_uuid();
BEGIN
  INSERT INTO ledger_transactions (id, kind, memo)
  VALUES (v_tx, 'contribution.received', 'invariant test');
  INSERT INTO ledger_postings (transaction_id, account_kind, side, amount_kobo)
  VALUES {postings};
END $$;
"""

    balanced = entry(
        "(v_tx, 'escrow_cash', 'debit', 100000), "
        "(v_tx, 'contributions_receivable', 'credit', 100000)"
    )
    must_succeed(db, "balanced entry", transaction(balanced))

    one_sided = entry("(v_tx, 'escrow_cash', 'debit', 100000)")
    must_fail(db, "one-sided entry", transaction(one_sided), expect="not a valid entry")

    mismatched = entry(
        "(v_tx, 'escrow_cash', 'debit', 100000), "
        "(v_tx, 'contributions_receivable', 'credit', 99999)"
    )
    must_fail(db, "mismatched entry", transaction(mismatched), expect="not a valid entry")

    must_fail(
        db,
        "delete a posting",
        # A DELETE against an empty table deletes nothing and so cannot prove the
        # trigger fires, so a real posting is written first and then removed.
        transaction(
            entry(
                "(v_tx, 'escrow_cash', 'debit', 100000), "
                "(v_tx, 'contributions_receivable', 'credit', 100000)"
            )
            + "DELETE FROM ledger_postings;"
        ),
        expect="append-only",
    )
    must_fail(
        db,
        "update a posting amount",
        transaction(
            entry(
                "(v_tx, 'escrow_cash', 'debit', 100000), "
                "(v_tx, 'contributions_receivable', 'credit', 100000)"
            )
            + "UPDATE ledger_postings SET amount_kobo = 1;"
        ),
        expect="append-only",
    )
    return (
        "a balanced entry commits; a one-sided entry, a mismatched entry, a "
        "DELETE and an UPDATE of history are all refused"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="ajo_migration_test")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))

    print(f"building {args.db} from the migration files only")
    subprocess.run(pg.admin("dropdb", "--if-exists", args.db), check=True)
    subprocess.run(pg.admin("createdb", args.db), check=True)

    applied = subprocess.run(
        [sys.executable, os.path.join(here, "migrate.py"), "--db", args.db],
        capture_output=True,
        text=True,
    )
    if applied.returncode != 0:
        print("migrations failed to apply:\n" + applied.stdout + applied.stderr)
        return 1

    failures = 0
    for name, fn in CASES:
        try:
            detail = fn(args.db)
        except Failure as exc:
            failures += 1
            print(f"  FAIL  {name}\n        {exc}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  ERROR {name}\n        {type(exc).__name__}: {exc}")
        else:
            print(f"  pass  {name}\n        {detail}")

    if not args.keep:
        subprocess.run(pg.admin("dropdb", "--if-exists", args.db), check=True)

    print()
    if failures:
        print(f"{failures} of {len(CASES)} case(s) failed")
        return 1
    print(f"all {len(CASES)} cases passed against a database built from migrations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
