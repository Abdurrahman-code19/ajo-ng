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



def as_role(db: str, role: str, user_email: str, body: str, commit: bool = False) -> str:
    """
    Run `body` as `role`, impersonating `user_email`.

    `commit=True` leaves the writes in place, which is the only way to assert
    something that a *different* transaction will observe. A trigger's effects
    are as much part of the write as the row itself, so an audit assertion has
    to look at the trail from outside the transaction that wrote it; wrapping
    both the insert and the count in one rolled-back transaction proves nothing,
    because the audit row is rolled back along with everything else.

    Two details are load-bearing and both cost a debugging session to find.

    The GUC has to be set in the *same session* as the query. `psql -c "select
    set_config(...); select ..."` looks equivalent and is not: each `-c` is its
    own transaction, and a GUC set in a transaction that then ends is gone by
    the time the next statement runs. So the GUC is set inside the same script
    as the body.

    `SET ROLE` has to come *after* the GUC. A GUC set before the role change is
    reset, because the GUC belongs to the session and the role change resets
    the session's privilege context.
    """
    return (
        "BEGIN;\n"
        # The GUC value is returned in a two-column row on purpose. `scalar`
        # skips any line containing the field separator, so this line is
        # invisible to it, and the body's own first line is what it reads. The
        # bare `SELECT set_config(...)` this replaced printed the uuid on a line
        # of its own, and every case that asked for a count silently got the
        # uuid instead -- which is how a case came to report "should see 1 of 3
        # users, saw '01a0f455-...'".
        f"SELECT 'guc' AS ignored, set_config('app.user_id', "
        f"(SELECT id::text FROM users WHERE email = '{user_email}'), false);\n"
        f"SET LOCAL ROLE {role};\n"
        f"{body}\n"
        + ("COMMIT;\n" if commit else "ROLLBACK;\n")
    )


def scalar(db: str, sql: str) -> str:
    """The first column of the first row, or '' when there are no rows."""
    out = psql(db, sql).strip().splitlines()
    for line in out:
        if line and not line.startswith("(") and "|" not in line and "---" not in line:
            return line.strip()
    return out[0].strip() if out else ""


def commit(body: str) -> str:
    """
    Run `body` and keep it.

    The lifecycle cases below need their fixtures to outlive the transaction that
    wrote them, because the assertion is usually made by a *different*
    transaction: a join that has to be refused at day six, a sweep that has to
    find the row a previous sweep created. `transaction()` rolls back precisely so
    the rest of the suite is unaffected, and that is the wrong tool here.

    Deferred constraint triggers still fire, because the COMMIT is the point at
    which they would have fired anyway -- unlike `transaction()`, which forces them
    early with `SET CONSTRAINTS ALL IMMEDIATE`.
    """
    return f"BEGIN;\n{body}\nCOMMIT;"


def _seed_users(db: str, label: str, users: list[tuple[str, str]]) -> None:
    """
    Create `users` and their profiles, and keep them.

    Split out from the case bodies because of a rule that is easy to trip over:
    the fixtures cannot be written *after* `SET LOCAL ROLE ajo_app`, which is what
    every `as_role` body does. `users` is RLS-protected, so the insert is refused
    with "new row violates row-level security policy" -- the role is in place
    precisely so that user rows cannot be planted by application code, and the
    test suite has to create them as itself.

    Kept rather than rolled back, because the cases assert across transactions:
    a join refused at day six needs an invite that an earlier transaction minted.
    """
    rows = ",\n       ".join(
        f"('{sid}', '{email}', 'active', true)" for sid, email in users
    )
    names = ",\n              ".join(
        f"'{email}'" for _, email in users
    )
    must_succeed(
        db,
        label,
        commit(
            f"""
INSERT INTO users (auth_subject_id, email, status, is_email_verified)
VALUES {rows};
INSERT INTO profiles (user_id, display_name)
SELECT id, left(email, 4) FROM users WHERE email IN ({names});
"""
        ),
    )

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


# ---------------------------------------------------------------------------
# The three roles. §9.2.
#
# These cases only mean anything after scripts/bootstrap_roles.sql has run, so
# the suite applies it. A migration-built database is owned by the superuser
# that ran the migrations, and every assertion here would pass vacuously against
# that owner -- which is precisely the mistake 9.13 warns about.
# ---------------------------------------------------------------------------


def _two_members(db: str) -> tuple[str, str]:
    """
    Two ordinary members and one platform support agent, all committed.

    This is a fixture, so it must persist for the cases that follow -- and it
    previously did not. It was wrapped in `transaction()`, whose ROLLBACK
    discarded the rows the docstring claimed were committed, so every case
    downstream that looked a member up by email found nothing and the role
    cases failed for a reason that had nothing to do with roles. The wrapper is
    gone.

    Leaving the statements in one `psql -c` still makes them atomic: PostgreSQL
    runs a multi-statement simple query inside a single implicit transaction, so
    either all four rows land or none do, and a partial fixture cannot happen.
    """
    must_succeed(
        db,
        "two members and a support agent",
        "\n".join(
            [
                # ON CONFLICT because three cases call this fixture and only the
                # first should do the inserting. Every role case needs the same
                # two members and the same support agent, and the alternative --
                # building the fixture once and sharing it -- would make each
                # case depend on the ones before it having run.
                "INSERT INTO users (auth_subject_id, email, status) VALUES "
                "('rls-1', 'rls-a@example.ng', 'active') "
                "ON CONFLICT DO NOTHING;",
                "INSERT INTO users (auth_subject_id, email, status) VALUES "
                "('rls-2', 'rls-b@example.ng', 'active') "
                "ON CONFLICT DO NOTHING;",
                "INSERT INTO users (auth_subject_id, email, status) VALUES "
                "('rls-3', 'rls-staff@example.ng', 'active') "
                "ON CONFLICT DO NOTHING;",
                # A support agent is the only way to reach the staff
                # branches of the policies, and R10 is about exactly that.
                "INSERT INTO role_assignments (user_id, role_id, scope, "
                "granted_by_user_id) SELECT u.id, 'support', 'platform', u.id "
                "FROM users u WHERE u.email = 'rls-staff@example.ng' "
                "ON CONFLICT DO NOTHING;",
            ]
        ),
    )
    return "rls-a@example.ng", "rls-b@example.ng"


@case("a role cannot bypass RLS, and only the policy decides")
def _rls_binds(db: str) -> str:
    """
    The load-bearing assertion of the whole role split.

    Run as the table owner, every member is visible. Run as `ajo_app`
    impersonating one member, only that member is. The difference is not the
    grant -- `ajo_app` has full DML on public -- it is that the owner is exempt
    from policies and `ajo_app` is not.
    """
    a, b = _two_members(db)

    as_owner = psql(db, "SELECT count(*) FROM users;").strip()
    if as_owner != "3":
        raise Failure(f"expected the 3 fixture users, owner saw {as_owner!r}")

    seen_by_a = scalar(db, as_role(db, "ajo_app", a, "SELECT count(*) FROM users;"))
    if seen_by_a != "1":
        raise Failure(
            "ajo_app impersonating a member should see exactly 1 of 3 users, "
            f"saw {seen_by_a!r}. If this is 3 the role is the owner, and the "
            "policies are decorative."
        )

    # And the row it does see must be its own, not merely a count of one.
    whose = scalar(db, as_role(db, "ajo_app", a, "SELECT string_agg(email, ',') FROM users;"))
    if whose != "rls-a@example.ng":
        raise Failure(f"ajo_app saw {whose!r} while impersonating rls-a")

    # A different member sees their own row instead: the policy is per-row, not
    # "the first row happens to be visible".
    whose_b = scalar(db, as_role(db, "ajo_app", b, "SELECT string_agg(email, ',') FROM users;"))
    if whose_b != "rls-b@example.ng":
        raise Failure(f"ajo_app saw {whose_b!r} while impersonating rls-b")

    return (
        f"the owner sees all 3 users, ajo_app sees 1 -- its own -- as either member"
    )


@case("the three roles hold exactly the privileges the spec asks for")
def _role_grants(db: str) -> str:
    a, _ = _two_members(db)

    # ajo_analytics: SELECT yes, write no.
    must_succeed(
        db, "analytics can SELECT", as_role(db, "ajo_analytics", a, "SELECT count(*) FROM users;")
    )
    must_fail(
        db,
        "analytics cannot INSERT",
        as_role(
            db,
            "ajo_analytics",
            a,
            "INSERT INTO users (auth_subject_id, email, status) "
            "VALUES ('nope', 'nope@example.ng', 'active');",
        ),
        expect="permission denied",
    )

    # ajo_app: DML granted, but a table with no INSERT policy still refuses.
    # Grants say which table; policies say which row, and the second can be
    # stricter than the first.
    must_fail(
        db,
        "app cannot INSERT without an INSERT policy",
        as_role(
            db,
            "ajo_app",
            a,
            "INSERT INTO users (auth_subject_id, email, status) "
            "VALUES ('nope2', 'nope2@example.ng', 'active');",
        ),
        expect="row-level security",
    )

    # Neither application role may create objects in public. A role that can
    # create a table can create one with a permissive policy and read through it.
    for role in ("ajo_app", "ajo_analytics"):
        must_fail(
            db,
            f"{role} cannot CREATE",
            as_role(db, role, a, "CREATE TABLE public.rls_probe (x int);"),
            expect="permission denied",
        )

    return (
        "analytics is read-only, app has DML but is bound by policies, and "
        "neither can create in public"
    )


@case("staff see the ledger and ordinary members see none of it")
def _staff_ledger(db: str) -> str:
    """R10 and R4: the two halves of the ledger rule, as the spec states them."""
    _, b = _two_members(db)

    # The rows have to exist. This case previously asserted that the support
    # agent "should see the 6 fixture ledger rows" while creating none and while
    # the case that does write ledger rows runs later and rolls them back, so
    # there was never anything to see. Both halves of the assertion were
    # therefore satisfied by an empty table, which is the weakest possible
    # evidence for a rule whose entire content is who can see what.
    for i in range(6):
        must_succeed(
            db,
            f"ledger fixture {i}",
            f"""
            DO $$
            DECLARE v_tx uuid := gen_random_uuid();
            BEGIN
              INSERT INTO ledger_transactions (id, kind, memo)
              VALUES (v_tx, 'contribution.received', 'staff visibility fixture');
              INSERT INTO ledger_postings (transaction_id, account_kind, side, amount_kobo)
              VALUES (v_tx, 'escrow_cash', 'debit', 100000),
                     (v_tx, 'contributions_receivable', 'credit', 100000);
            END $$;
            """,
        )

    member_rows = scalar(
        db, as_role(db, "ajo_app", b, "SELECT count(*) FROM ledger_transactions;")
    )
    if member_rows != "0":
        raise Failure(f"a member should see 0 ledger rows, saw {member_rows!r}")

    staff_rows = scalar(
        db,
        as_role(
            db, "ajo_app", "rls-staff@example.ng", "SELECT count(*) FROM ledger_transactions;"
        ),
    )
    if staff_rows == "0":
        raise Failure(
            "the support agent should see the 6 fixture ledger rows, saw 0. "
            "app.is_platform_staff() is not resolving through the grants."
        )

    return f"a member sees {member_rows} ledger rows, the support agent sees {staff_rows}"


@case("SECURITY DEFINER functions run as a bounded owner, not a superuser")
def _security_definer(db: str) -> str:
    """
    The six SECURITY DEFINER functions in app execute as their owner. If that
    owner is a superuser they can read anything, and every policy that calls
    them is a policy with a hole in it.
    """
    out = must_succeed(
        db,
        "read the SECURITY DEFINER owners",
        "SELECT p.proname || '=' || pg_get_userbyid(p.proowner) "
        "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE p.prosecdef AND n.nspname IN ('app', 'public') ORDER BY 1;",
    )
    if not out.strip():
        raise Failure("found no SECURITY DEFINER functions, so this proves nothing")

    for line in out.strip().splitlines():
        if "=" not in line:
            continue
        name, _, owner = line.partition("=")
        if owner != "ajo_migrator":
            raise Failure(
                f"app.{name.strip()} is SECURITY DEFINER and owned by {owner!r}, "
                "expected ajo_migrator"
            )
        # And the owner must not itself be exempt from the policies it enforces.
        bypass = must_succeed(
            db,
            f"check rolbypassrls for {owner}",
            f"SELECT rolbypassrls::text FROM pg_roles WHERE rolname = '{owner}';",
        ).strip()
        # `::text` on a boolean is 'false', not psql's display form 'f'. Comparing
        # against 'f' made this assert the opposite of what it meant: it failed
        # while the role correctly had no BYPASSRLS, and would have passed if the
        # role had it.
        if bypass.strip() not in ("false", "f"):
            raise Failure(f"{owner} has BYPASSRLS, so RLS does not bind it")

    return (
        f"all {len(out.strip().splitlines())} SECURITY DEFINER functions are owned by "
        "ajo_migrator, which has neither superuser nor BYPASSRLS"
    )


@case("the schema grant the owner needs is not optional")
def _owner_needs_schema_grant(db: str) -> str:
    """
    Guards the bug this bootstrap actually had.

    PUBLIC has no USAGE on schema public here, which is correct and deliberate.
    A superuser ignores that, so nothing notices until ownership moves off the
    superuser -- at which point the new owner cannot see its own tables, and
    every SECURITY DEFINER function reports "relation does not exist" while the
    bootstrap itself reports success.
    """
    usage = must_succeed(
        db,
        "check the owner's schema privilege",
        "SELECT has_schema_privilege('ajo_migrator', 'public', 'USAGE')::text;",
    ).strip()
    if usage != "true":
        raise Failure(
            "ajo_migrator owns the tables but has no USAGE on schema public, so "
            "it cannot read them. The SECURITY DEFINER functions are broken and "
            "the error is reported as a missing relation, not a missing grant."
        )

    # And prove the function that reads through the schema actually works.
    must_succeed(
        db,
        "has_platform_role resolves",
        "SELECT app.has_platform_role('support') IS NOT NULL;",
    )

    return (
        "ajo_migrator has USAGE on public, so the SECURITY DEFINER functions can "
        "resolve the tables they read"
    )


def uid(db: str, email: str) -> str:
    """
    A user's id, read as the superuser so it is not filtered by RLS.

    Needed because of a trap worth naming. A case that, while impersonating
    rls-a, selects the id of rls-b out of `users` to try to write a row owned by
    rls-b gets *no rows*, because `users` has a self-only SELECT policy and rls-b
    is not visible to rls-a. The INSERT then matches nothing, inserts nothing,
    raises nothing, and the case concludes the write was refused when in fact it
    was never attempted. That is a policy test passing for the wrong reason, and
    it is worse than no test, because the assertion it was written to make is
    precisely the one an attacker would try.

    So the id is fetched here, outside the role switch, and embedded as a
    literal. The write is then genuinely attempted and genuinely refused.
    """
    out = scalar(db, f"SELECT id FROM users WHERE email = '{email}';")
    if not out:
        raise Failure(f"no user {email!r} to build the assertion from")
    return out.strip()


@case("an audited write records an audit row")
def _audit_trail_writes(db: str) -> str:
    """
    Guards the failure that was silent for a whole round of work.

    `app.audit_row()` is SECURITY DEFINER, so all 18 audit triggers insert into
    `audit_logs` as `ajo_migrator` rather than as the caller. `audit_logs` is
    FORCE RLS, and FORCE binds the owner, so the insert needs a policy of its
    own. Without one, every audited write in the schema is refused by its own
    audit trigger, inside a transaction that rolls back.

    Nothing announces that. The write looks like it should work, the bootstrap
    reports success, and the only symptom is an absence -- so the way to catch
    it is to assert the row exists, which is what this does. A test that only
    asserted "the insert succeeded" would have passed before the split and
    failed after it, and neither fact would have told anyone the trail was gone.

    The second half is the property that makes the fix safe rather than merely
    working: `ajo_app` must still be unable to write `audit_logs` itself. A
    policy that let the application role insert audit rows would be a way to
    forge history, which is the one thing an audit table must not permit.
    """
    before = scalar(db, "SELECT count(*) FROM audit_logs;")
    rows_before = scalar(db, "SELECT count(*) FROM profiles;")
    owner = uid(db, "rls-a@example.ng")
    # Committed, because the audit row has to still be there when the count runs.
    # See `as_role`'s `commit` note -- a rolled-back insert takes its own audit
    # row with it, and the assertion passes against a table that never recorded
    # anything. The owning id is a literal rather than a subquery for the same
    # reason the count is a separate statement: both have to be real.
    must_succeed(
        db,
        "an audited insert as the application role",
        as_role(
            db,
            "ajo_app",
            "rls-a@example.ng",
            "INSERT INTO profiles (user_id, display_name) "
            f"VALUES ('{owner}', 'Audited');",
            commit=True,
        ),
    )

    # The row itself is checked before the audit row, and the reason is that
    # `must_succeed` only looks for "ERROR". An INSERT that matches no source
    # row reports INSERT 0 0, which is a success, so an earlier version of this
    # case named a document_type code that does not exist, inserted nothing,
    # triggered nothing, and then reported -- correctly, and uselessly -- that
    # the audit trail was empty. Asserting the write landed is what stops the
    # audit assertion from being evidence about a statement that never ran.
    if scalar(db, "SELECT count(*) FROM profiles;") == rows_before:
        raise Failure(
            "the audited insert inserted no row, so there was nothing for the "
            "trigger to record and the audit assertion below proves nothing"
        )

    after = scalar(db, "SELECT count(*) FROM audit_logs;")
    if after == before:
        raise Failure(
            "the insert succeeded but wrote no audit row, so the trail is not "
            "recording anything and every write here is unaccounted for"
        )

    must_fail(
        db,
        "the application role forging an audit row",
        as_role(
            db,
            "ajo_app",
            "rls-a@example.ng",
            "INSERT INTO audit_logs (actor_user_id, subject_type, action) "
            f"VALUES ('{owner}', 'user', 'forged');",
        ),
        expect="row-level security",
    )

    return (
        f"an audited write as ajo_app produced an audit row ({before} to {after}), "
        "and ajo_app still cannot insert one itself"
    )


@case("a member can create only their own identity rows")
def _self_insert(db: str) -> str:
    """
    The two grants in 096, and the shape every other self-owned INSERT follows.

    Both checks compare the row against the identity the request proved, so the
    only thing a member can do here is create a row that is already theirs. The
    refusal below is the half that matters: the same role must not be able to
    write a row attributed to somebody else, which is the only way a
    self-owned INSERT policy becomes a real hole.
    """
    # rls-b rather than rls-a: the audit case above commits a profile for rls-a,
    # and `profiles.user_id` is unique, so sharing a member makes this case fail
    # on a constraint instead of on the policy it is here to test. Each case
    # owning a different member is cheaper than ordering the cases.
    mine = uid(db, "rls-b@example.ng")
    theirs = uid(db, "rls-a@example.ng")

    must_succeed(
        db,
        "a member inserting their own profile",
        as_role(
            db,
            "ajo_app",
            "rls-b@example.ng",
            "INSERT INTO profiles (user_id, display_name) "
            f"VALUES ('{mine}', 'Self');",
        ),
    )
    must_fail(
        db,
        "a member inserting a profile for somebody else",
        as_role(
            db,
            "ajo_app",
            "rls-b@example.ng",
            "INSERT INTO profiles (user_id, display_name) "
            f"VALUES ('{theirs}', 'Not mine');",
        ),
        expect="row-level security",
    )

    # And the tables 096 deliberately leaves without an INSERT policy. Asserting
    # they are closed is what stops a later "just grant it" from going unnoticed.
    #
    # 105 moves two of them. Its own words for why is worth reading before
    # changing anything here: "an INSERT policy for the application role would be
    # the first thing in this schema to let a caller write an arbitrary ledger
    # entry". That is precisely and only about the application role. 105 supplies
    # the missing definer function, and the policy it adds is for `ajo_migrator`,
    # the function's owner, which no request ever assumes.
    #
    # So the claim is restated at the level it was actually about rather than
    # deleted. "No INSERT policy at all" was a proxy for "the API cannot write
    # this"; now that a legitimate writer exists, the proxy is wrong and the thing
    # it stood for is asserted directly. Deleting the loop would have dropped the
    # only check that `ajo_app` cannot reach a ledger insert.
    for table in ("payments", "payouts", "risk_events"):
        granted = scalar(
            db,
            "SELECT count(*) FROM pg_policies WHERE tablename = "
            f"'{table}' AND cmd = 'INSERT';",
        )
        if granted != "0":
            raise Failure(
                f"{table} has an INSERT policy, but 096 records that writing it "
                "is a product decision and no app function writes it yet. Who may "
                "write a payout is not a detail to change without noticing."
            )

    for table in ("ledger_transactions", "ledger_postings"):
        open_to_app = scalar(
            db,
            "SELECT count(*) FROM pg_policies WHERE tablename = "
            f"'{table}' AND cmd = 'INSERT' AND 'ajo_app' = ANY(roles);",
        )
        if open_to_app != "0":
            raise Failure(
                f"{table} has an INSERT policy for ajo_app. 105 gives the policy "
                "to ajo_migrator, which owns the ledger writer and is never "
                "assumed by a request; ajo_app writing entries directly is the one "
                "thing 096 refused and the one thing that would make the ledger an "
                "input rather than a record."
            )

        # And the refusal has to be real, not just unwritten: `ajo_app` holds
        # full DML grants on public from bootstrap, so the policy is the only
        # thing standing between the API and a forged ledger entry.
        must_fail(
            db,
            f"ajo_app inserting into {table}",
            as_role(
                db,
                "ajo_app",
                "rls-a@example.ng",
                (
                    f"INSERT INTO {table} (id, kind, occurred_at) "
                    "VALUES (gen_random_uuid(), 'contribution.received', now());"
                    if table == "ledger_transactions"
                    else f"INSERT INTO {table} (id, transaction_id, account_kind, "
                    "side, amount_kobo) VALUES (gen_random_uuid(), gen_random_uuid(), "
                    "'escrow_cash', 'debit', 1);"
                ),
            ),
            expect="row-level security",
        )

    return (
        "profiles accepts a self-owned row and refuses someone else's; payments, "
        "payouts and risk_events stay closed to INSERT entirely; and the two ledger "
        "tables have INSERT policies for the migrator alone, which ajo_app cannot "
        "use despite holding full DML grants"
    )


# ---------------------------------------------------------------------------
# Login, refresh rotation, and reuse detection. Migration 103.
#
# The cases below are grouped by the property they defend, and each one is a
# statement 12.4 makes rather than an implementation detail. The common shape is
# worth naming, because it is what 101 and 102 were about: the login flow is the
# first thing in this codebase that runs with *no* identity, and every function
# it depends on therefore executes as its owner with no GUC set. A self-only
# policy matches nothing, the function returns zero rows, and zero rows is the
# documented "wrong password" answer -- so a missing grant here does not fail
# loudly, it fails as a platform where nobody can log in.
# ---------------------------------------------------------------------------


def _loginable(
    db: str,
    email: str,
    status: str = "active",
    verified: bool = True,
) -> str:
    """
    A member with a credential row, and therefore a member who can log in.

    Committed, not rolled back: the refresh cases rotate real tokens and assert on
    what a *second* transaction sees, which a rollback would undo along with the
    state under test.

    The Argon2id hash is a syntactically valid PHC string with a deliberately
    wrong digest. Nothing here verifies a password -- that is Argon2's job and it
    lives in the API, which is the only process that has the library. What the
    database has to guarantee is that the hash reaches the caller intact and that
    nothing else can read it, and a real hash would not test either any better.
    """
    must_succeed(
        db,
        "loginable fixture",
        f"""
        INSERT INTO users (auth_subject_id, email, status, is_email_verified)
        VALUES ('login-{email}', '{email}', '{status}', {str(verified).lower()})
        ON CONFLICT DO NOTHING;
        INSERT INTO user_credentials (user_id, argon2_hash)
        SELECT id, '$argon2id$v=19$m=19456,t=2,p=1$ZmFrZXNhbHRzb21lc2FsdA$ZmFrZWhhc2hoYXNoZmFrZWhhc2hoYXNoZmFrZWg'
          FROM users WHERE email = '{email}'
        ON CONFLICT DO NOTHING;
        """,
    )
    return email


def _open_session(
    db: str,
    email: str,
    token_hex: str = "a1a1a1",
    expires_in: str = "30 days",
    device: str = "laptop",
) -> str:
    """
    A live session row with a known refresh token hash, owned by `email`.

    Written as the connection's own role rather than as the member because the
    point of several cases below is what the *member's* role can do to a session,
    and building the fixture through the same path the test is about would let a
    broken fixture mask a broken policy.

    `device` is a parameter rather than a constant because
    `sessions_one_active_per_device` makes (user_id, platform, device_label)
    unique among unrevoked sessions -- so a member cannot hold two active sessions
    for the same device, and a fixture that wanted two would collide on the index
    rather than on anything it was testing. That index is also why "log in again
    on the device you are already on" has to revoke the old session rather than
    add a second one.
    """
    must_succeed(
        db,
        f"session fixture for {email} on {device}",
        f"""
        INSERT INTO sessions (user_id, refresh_token_hash, device_label, platform,
                              refresh_expires_at)
        SELECT id, decode('{token_hex}', 'hex'), '{device}', 'web',
               now() + interval '{expires_in}'
          FROM users WHERE email = '{email}';
        """,
    )
    return token_hex


@case("a login can read the hash it needs, and nothing else can")
def _login_lookup(db: str) -> str:
    """
    `app.verify_login_credential` is the whole reason 103 exists, and it has two
    halves that pull in opposite directions.

    It has to return a password hash -- Argon2id cannot be verified in the
    database, so the hash has to reach the process that owns the library. And
    `user_credentials` deliberately has no SELECT policy for any application
    role, which is what stops a bug in a route from reading hashes out of the
    table it just wrote to.

    Both are asserted here, because either one alone passes for the wrong reason.
    A function that returns the hash but is reachable with a broader grant is a
    hole; a function that returns nothing leaves every login on the platform
    failing, and reporting "wrong password" for a correct one.
    """
    _loginable(db, "login-ok@example.ng")

    # The hash reaches its caller. Asserted on the *value*, not on the row count:
    # a function that returned the right number of rows with an empty hash would
    # satisfy a count and break every login.
    got = must_succeed(
        db,
        "look up a known member",
        "SELECT argon2_hash FROM app.verify_login_credential('login-ok@example.ng');",
    )
    if "$argon2id$" not in got:
        raise Failure(
            "verify_login_credential did not return the Argon2id hash, so the "
            f"API has nothing to verify against: {got.strip()[:200]}"
        )

    # The status comes back with it, because the two decisions are made together
    # and a caller that could not see the status would have to guess.
    state = must_succeed(
        db,
        "read the account state with the credential",
        "SELECT status, is_email_verified FROM app.verify_login_credential('login-ok@example.ng');",
    )
    if "active" not in state or "t" not in state:
        raise Failure(
            f"the credential came back without the account state: {state.strip()[:200]}"
        )

    # And an unknown address is an empty set, not an exception. Raising here
    # would let the API distinguish "no such member" from "no credential row" --
    # a user-enumeration oracle on an unauthenticated endpoint.
    unknown = must_succeed(
        db,
        "look up an unknown address",
        "SELECT count(*) FROM app.verify_login_credential('nobody-at-all@example.ng');",
    )
    if not unknown.strip().startswith("0"):
        raise Failure(
            "verify_login_credential returned a row for an unknown address, so a "
            f"caller could tell accounts apart: {unknown.strip()[:200]}"
        )

    # Case-insensitivity is the half that is easy to get wrong and invisible when
    # it is wrong: registration lowercases before it writes, so an address stored
    # with capitals and presented in lower case is the same member, and a
    # comparison that disagreed with the uniqueness check would create an account
    # that exists and cannot be logged into.
    #
    # Stored through the same fixture as every other member, deliberately. The
    # function's FROM clause is `user_credentials JOIN users`, so a users row
    # without a credential returns nothing -- and a case that inserted only the
    # user would have been asserting that a member with no password cannot log
    # in, which is true and is not the property under test.
    _loginable(db, "Mixed.Case@Example.NG")
    if not must_succeed(
        db,
        "look up a mixed-case address in lower case",
        "SELECT count(*) FROM app.verify_login_credential('mixed.case@example.ng');",
    ).strip().startswith("1"):
        raise Failure(
            "login is case-sensitive in a way registration is not, so this "
            "member has an account and cannot reach it"
        )

    return (
        "the hash and the account state reach the verifier, an unknown address "
        "is an empty set, and the lookup agrees with registration on case"
    )


@case("the application role still cannot read a password hash")
def _hash_still_closed(db: str) -> str:
    """
    The counterweight to the case above, and the one that would catch a future
    "just grant SELECT so the login code is simpler".

    `user_credentials` gained a policy for `ajo_migrator` in 103. If that policy
    had been written for `ajo_app`, or with no role at all, every hash in the
    table would become readable by any code path in the API -- including the one
    that wrote them.
    """
    _loginable(db, "login-closed@example.ng")
    owner = uid(db, "login-closed@example.ng")

    seen = scalar(
        db,
        as_role(
            db,
            "ajo_app",
            "login-closed@example.ng",
            "SELECT count(*) FROM user_credentials;",
        ),
    )
    if seen != "0":
        raise Failure(
            f"ajo_app read {seen} credential rows. Migration 103 granted the "
            "migrator, not the application role, and the difference is the whole "
            "point of the table."
        )

    # The same for `users`, which also gained a migrator policy. An application
    # role must still see exactly one user row: its own.
    _loginable(db, "login-other@example.ng")
    visible = scalar(
        db,
        as_role(db, "ajo_app", "login-closed@example.ng", "SELECT count(*) FROM users;"),
    )
    if visible != "1":
        raise Failure(
            f"ajo_app sees {visible} users while impersonating one member, so "
            "users_select_by_migrator leaked to the application role"
        )

    # And the spent-token ledger is closed too. A member can rotate their own
    # token without ever seeing which hashes have been spent, which is what makes
    # a token hash useless if the table is disclosed.
    spent = scalar(
        db,
        as_role(
            db, "ajo_app", "login-closed@example.ng", "SELECT count(*) FROM session_rotated_tokens;"
        ),
    )
    if spent != "0":
        raise Failure(f"ajo_app read {spent} spent-token rows")

    del owner
    return (
        "ajo_app sees no credential row, one user row, and no spent tokens, "
        "while the migrator reads all three"
    )


@case("a rotation leaves one live token and one spent record")
def _rotation_single_use(db: str) -> str:
    """
    What a rotation has to leave behind, which is the state the reuse case then
    reads.

    Two things, and both are asserted because either alone passes for the wrong
    reason. The successor has to be the *live* token, or a rotation that did not
    take effect would still look like a success. And the token that was just
    spent has to be in `session_rotated_tokens`, or the next use of it is
    indistinguishable from a forgery and 12.4.2's theft response never fires.

    This deliberately does **not** claim to test concurrency. Every statement here
    runs and settles in sequence, so a rolled-back first claim would leave the
    second reading the same live row and both would report `rotated` -- which is
    also what a missing `FOR UPDATE` produces under a real race. Two genuinely
    overlapping transactions cannot be expressed through `psql -c`, and asserting
    the lock this way would be a test that passes whether or not the lock exists.
    The race is asserted in `packages/api/test/integration.test.ts` instead, where
    two real requests overlap. What is pinned here is the schema half: that a
    rotation is durable, single-valued, and leaves the evidence behind.
    """
    email = _loginable(db, "login-rotate@example.ng")
    token = _open_session(db, email, "b1b1b1")
    successor = "c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2"

    first = scalar(
        db,
        as_role(
            db,
            "ajo_app",
            email,
            f"""SELECT coalesce((SELECT outcome FROM app.claim_refresh_token(
                    decode('{token}', 'hex'), decode('{successor}', 'hex'),
                    now(), now() + interval '30 days')), 'no-row');""",
            commit=True,
        ),
    )
    if first != "rotated":
        raise Failure(
            f"the first use of a live token reported {first!r} rather than "
            "'rotated', so the case below is not testing reuse"
        )

    # Committed, so the successor is real and the spent hash is really spent. A
    # rolled-back rotation would leave the fixture's original token live, and the
    # two checks below would then be reading the wrong state.
    live = scalar(
        db,
        f"SELECT count(*) FROM sessions s JOIN users u ON u.id = s.user_id "
        f"WHERE u.email = '{email}' AND s.refresh_token_hash = decode('{successor}', 'hex');",
    )
    if live != "1":
        raise Failure(
            f"the successor is the live token on {live} sessions; exactly one is "
            "correct, and zero means the rotation did not take effect"
        )

    # The old token is gone from the live column -- that is what "rotated" means --
    # and present in the spent ledger, which is what makes its next use detectable.
    spent = scalar(
        db,
        f"SELECT count(*) FROM session_rotated_tokens r "
        f"JOIN users u ON u.id = r.user_id "
        f"WHERE u.email = '{email}' AND r.token_hash = decode('{token}', 'hex');",
    )
    if spent != "1":
        raise Failure(
            f"the spent token is recorded {spent} times; a rotation that does not "
            "record the token it consumed makes reuse undetectable"
        )

    still_live = scalar(
        db,
        f"SELECT count(*) FROM sessions s JOIN users u ON u.id = s.user_id "
        f"WHERE u.email = '{email}' AND s.refresh_token_hash = decode('{token}', 'hex');",
    )
    if still_live != "0":
        raise Failure(
            f"the consumed token is still the live token on {still_live} sessions, "
            "so rotating did not replace it"
        )

    return (
        "a rotation makes the successor the single live token and records the "
        "consumed one in the spent ledger"
    )


@case("a used refresh token is theft, and it revokes every session")
def _reuse_detection(db: str) -> str:
    """
    The control 12.4.2 is built on.

    Rotating a token destroys the evidence that it was ever valid, which is why
    103 adds `session_rotated_tokens`. Without that table a replayed token and a
    forged one are the same event -- a lookup miss -- and there is nothing to act
    on. With it, a replay is observable, and the spec's response is the strongest
    one available: the whole lineage goes, and so does everything else the member
    holds.

    The second half is the part that limits the damage and the part a test has to
    pin. Revoking only the replayed lineage would leave an attacker who took two
    tokens holding the second one.
    """
    email = _loginable(db, "login-reuse@example.ng")
    other = _loginable(db, "login-reuse-2@example.ng")
    token = _open_session(db, email, "d1d1d1")

    # A second session on the same member, so "every session" means more than the
    # one the stolen token came from.
    # A second session on the same member, on a *different* device, so "every
    # session" means more than the one the stolen token came from. It has to be a
    # different device because `sessions_one_active_per_device` is unique over
    # (user_id, platform, device_label) among unrevoked rows -- a fixture wanting
    # two would collide on that index rather than on anything under test.
    _open_session(db, email, "d2d2d2", expires_in="30 days", device="phone")
    _open_session(db, other, "d3d3d3", expires_in="30 days")

    def run(commit: bool = False) -> str:
        return as_role(
            db,
            "ajo_app",
            email,
            f"""SELECT coalesce((SELECT outcome FROM app.claim_refresh_token(
                    decode('{token}', 'hex'), decode('d4d4d4', 'hex'),
                    now(), now() + interval '30 days')), 'no-row');""",
            commit=commit,
        )

    # Committed, so the rotation is real and the second call genuinely presents a
    # spent token. Rolled back, both calls would read the same untouched live row
    # and both would answer `rotated` -- the same output a missing spent-token
    # ledger produces, which is the failure this case exists to catch.
    if scalar(db, run(commit=True)) != "rotated":
        raise Failure("the first use of a live token did not rotate it, so the case is not testing reuse")

    # Second use of the same token. This is the event. Committed, because the
    # response to it is the revocation, and a rolled-back detection would report
    # `reused` correctly while leaving every session open -- the assertion below
    # would then fail having proved the detection fires but not that it protects.
    outcome = scalar(db, run(commit=True))
    if outcome != "reused":
        raise Failure(
            f"a spent token reported {outcome!r} rather than 'reused', which "
            "means reuse is not detectable and 12.4.2's theft response never fires"
        )

    remaining = scalar(
        db,
        f"SELECT count(*) FROM sessions s JOIN users u ON u.id = s.user_id "
        f"WHERE u.email = '{email}' AND s.revoked_at IS NULL;",
    )
    if remaining != "0":
        raise Failure(
            f"{remaining} of the member's sessions survived a confirmed token "
            "theft; 12.4.2 requires all of them invalidated"
        )

    # And another member is untouched, because "all sessions" means this member's.
    survivor = scalar(
        db,
        f"SELECT count(*) FROM sessions s JOIN users u ON u.id = s.user_id "
        f"WHERE u.email = '{other}' AND s.revoked_at IS NULL;",
    )
    if survivor != "1":
        raise Failure(
            f"the revocation reached another member's session ({survivor} left); "
            "the response is per-member, not global"
        )

    # The event is recorded. 12.10 lists token-reuse detection as something that
    # must be retained, and an audit trail nobody wrote is a question a member
    # cannot be answered months later.
    logged = scalar(
        db,
        "SELECT count(*) FROM audit_logs "
        "WHERE action = 'session.refresh_token_reuse';",
    )
    if logged == "0":
        raise Failure(
            "a confirmed token theft wrote no audit row, so 12.10's record does "
            "not exist and the detection is invisible after the fact"
        )

    # The successor the attacker's own rotation produced must also be refused.
    #
    # This is the assertion that was missing, and the API suite found it: the
    # lookup above matches on the token hash alone, so after the revocation the
    # newest token in the lineage still resolved to a row -- a row that was now
    # revoked. Detection therefore closed every session except the one the
    # attacker was standing in. Revoking is only the control if the token stops
    # working, and "the row is revoked" is not the same claim as "the token is
    # refused".
    successor = scalar(
        db,
        as_role(
            db,
            "ajo_app",
            email,
            """SELECT coalesce((SELECT outcome FROM app.claim_refresh_token(
                    decode('d4d4d4', 'hex'), decode('d5d5d5', 'hex'),
                    now(), now() + interval '30 days')), 'no-row');""",
            commit=True,
        ),
    )
    if successor != "no-row":
        raise Failure(
            f"the attacker's successor token reported {successor!r} after the "
            "theft was detected; 12.4.2's revocation has to stop the token "
            "itself, not only mark the row, or the attacker's own session "
            "survives the response meant to evict it"
        )

    return (
        "a spent token reports reuse, revokes all 2 of that member's sessions "
        "and no one else's, writes an audit row, and stops the successor too"
    )


@case("refresh tokens expire, and idle and absolute limits are separate rules")
def _session_timeouts(db: str) -> str:
    """
    12.4.3's three limits, which are three different rules and not one.

    They are asserted separately because they are enforced by different
    comparisons against different columns, and a single "expiry works" case would
    pass with all three collapsed into one. Idle is measured from `last_active_at`
    and absolute from `created_at`: a member who uses the app daily still loses the
    session at 90 days, and one who vanishes for a fortnight loses it at 14 with
    the absolute clock nowhere near.
    """
    checks: list[tuple[str, str, str]] = []

    # Distinct token hashes per iteration, because `sessions_refresh_token_hash`
    # is globally UNIQUE -- a shared literal would collide on that index on the
    # second iteration and the case would fail for a reason that has nothing to do
    # with timeouts.
    for index, (label, mutate) in enumerate(
        (
            ("expired", "refresh_expires_at = now() - interval '1 minute'"),
            ("idle", "last_active_at = now() - interval '15 days'"),
            ("absolute", "created_at = now() - interval '91 days'"),
        )
    ):
        email = _loginable(db, f"login-{label}@example.ng")
        token = _open_session(db, email, f"e{index}e{index}e{index}", expires_in="30 days")
        must_succeed(
            db,
            f"age the {label} session",
            # `SET column` cannot be qualified with the table alias in PostgreSQL,
            # so the alias appears on the table and the column stands alone.
            f"UPDATE sessions AS s SET {mutate} "
            f"FROM users u WHERE u.id = s.user_id AND u.email = '{email}';",
        )
        outcome = scalar(
            db,
            as_role(
                db,
                "ajo_app",
                email,
                f"""SELECT coalesce((SELECT outcome FROM app.claim_refresh_token(
                        decode('{token}', 'hex'), decode('e2e2e2', 'hex'),
                        now(), now() + interval '30 days')), 'no-row');""",
                # Committed, because the revocation these refusals perform is the
                # thing the last check in this case looks for. Rolled back, every
                # outcome above would still be `unknown` -- the token is refused
                # either way -- while `revoked_reason` came back empty, and the
                # case would fail having proved nothing about the revocation.
                commit=True,
            ),
        )
        checks.append((label, outcome, token))

    for label, outcome, _ in checks:
        if outcome == "rotated":
            raise Failure(
                f"a {label}-expired session still rotated, so a bearer secret "
                "past its limit is still accepted"
            )
        if outcome != "unknown":
            raise Failure(
                f"a {label}-expired session reported {outcome!r}; it should be "
                "refused the same way a forged token is"
            )

    # Each refusal revokes the session rather than leaving it to be retried, so
    # the row explains itself months later instead of being an inert active
    # session with an old timestamp.
    email = "login-idle@example.ng"
    reason = scalar(
        db,
        f"SELECT s.revoked_reason FROM sessions s JOIN users u ON u.id = s.user_id "
        f"WHERE u.email = '{email}';",
    )
    if not reason.strip():
        raise Failure("a timed-out session was not revoked, or was revoked without a reason")

    # A session that was signed out is refused too -- and refused *without* an
    # accusation. This is the case the `revoked_at IS NULL` filter being absent
    # from the lookup creates, and both halves of the answer are deliberate:
    #
    #   * the token must not work, because the member signed out and a stale
    #     client is still holding it;
    #   * it must not be reported as `reused`, because a member who signs out and
    #     whose phone wakes up and refreshes is not an attacker. Calling it
    #     theft would revoke every other session they hold and write an audit row
    #     naming them as a breach.
    #
    # So the answer is `no-row`, which the API turns into the same 401 as any
    # other refusal, and no other session is touched.
    signed_out = _loginable(db, "login-signedout@example.ng")
    stale = _open_session(db, signed_out, "c1c1c1", expires_in="30 days")
    _open_session(db, signed_out, "c2c2c2", expires_in="30 days", device="phone")
    must_succeed(
        db,
        "sign the first session out",
        f"UPDATE sessions AS s SET revoked_at = now(), revoked_reason = 'signed_out' "
        f"FROM users u WHERE u.id = s.user_id AND u.email = '{signed_out}' "
        f"AND s.refresh_token_hash = decode('{stale}', 'hex');",
    )
    stale_outcome = scalar(
        db,
        as_role(
            db,
            "ajo_app",
            signed_out,
            """SELECT coalesce((SELECT outcome FROM app.claim_refresh_token(
                    decode('c1c1c1', 'hex'), decode('c3c3c3', 'hex'),
                    now(), now() + interval '30 days')), 'no-row');""",
            commit=True,
        ),
    )
    if stale_outcome != "no-row":
        raise Failure(
            f"a signed-out session's token reported {stale_outcome!r}; a member "
            "who signed out and whose stale client refreshed must be refused "
            "quietly, not recorded as a token theft"
        )
    still_open = scalar(
        db,
        f"SELECT count(*) FROM sessions s JOIN users u ON u.id = s.user_id "
        f"WHERE u.email = '{signed_out}' AND s.revoked_at IS NULL;",
    )
    if still_open != "1":
        raise Failure(
            f"a stale refresh after signing out left {still_open} live sessions "
            "where 1 was expected; refusing a signed-out token must not revoke the "
            "member's other sessions as if it were a breach"
        )

    return (
        "an expired, a 15-day-idle and a 91-day-old session are all refused, a "
        f"revoked one is refused quietly, and the idle one is revoked with "
        f"reason {reason.strip()!r}"
    )


@case("a session is a member's own row to write and to revoke")
def _session_rls(db: str) -> str:
    """
    103 adds INSERT and UPDATE policies to `sessions`, which had only SELECT and
    DELETE, and both are needed by the login flow: creating a session on login is
    a write, and revoking one is a write.

    The refusal half matters more than the acceptance half, and it is the half
    that is easy to skip: a self-owned policy with a missing `USING` clause is not
    permissive, it is inert, and every revocation silently affects nothing while
    reporting success. So this asserts a member can revoke their own session and
    *cannot* revoke somebody else's.
    """
    mine = _loginable(db, "login-rls-mine@example.ng")
    theirs = _loginable(db, "login-rls-theirs@example.ng")
    theirs_id = uid(db, theirs)
    _open_session(db, mine, "f1f1f1")
    _open_session(db, theirs, "f2f2f2")

    # `sessions_one_active_per_device` is a partial unique index over
    # (user_id, platform, device_label) where not revoked, so a second session on
    # the same member and device label has to revoke the first rather than sit
    # next to it. That is the "log in again on the device you are already on"
    # case, and it is the common one.
    must_succeed(
        db,
        "revoke a member's own session",
        as_role(
            db,
            "ajo_app",
            mine,
            "UPDATE sessions SET revoked_at = now(), revoked_reason = 'member_revoked' "
            "WHERE user_id = app.request_user_id() AND revoked_at IS NULL;",
            commit=True,
        ),
    )
    still_open = scalar(
        db,
        f"SELECT count(*) FROM sessions s JOIN users u ON u.id = s.user_id "
        f"WHERE u.email = '{mine}' AND s.revoked_at IS NULL;",
    )
    if still_open != "0":
        raise Failure(
            f"{still_open} of the member's own sessions survived their own "
            "revocation, so sessions_update_own is not doing anything"
        )

    # The other direction, and the one an attacker would try. The target id is a
    # literal rather than a subquery, and that is the whole reason the assertion
    # means anything: `users` is FORCE RLS with a self-only SELECT policy, so
    # `(SELECT id FROM users WHERE email = ...)` run as `ajo_app` returns NULL,
    # the `WHERE` matches no rows, and the UPDATE changes nothing for a reason
    # that has nothing to do with the session policy. `uid` reads the id outside
    # the role switch for precisely this trap.
    #
    # And it is asserted on the *effect* rather than on an error, because an UPDATE
    # under a `USING` clause that matches no visible row updates nothing and
    # reports success. That is not a gap in the policy -- it is what row-level
    # security is for: a member learns nothing about the existence of a session
    # that is not theirs, which is why "no such row" and "not your row" have to be
    # the same answer. A test that expected `row-level security` here would be
    # asserting a stronger guarantee than the database makes, and would pass only
    # because the fixture used a NULL subquery.
    must_succeed(
        db,
        "attempt to revoke somebody else's session",
        as_role(
            db,
            "ajo_app",
            mine,
            "UPDATE sessions SET revoked_at = now(), revoked_reason = 'forged' "
            f"WHERE user_id = '{theirs_id}';",
        ),
    )
    untouched = scalar(
        db,
        f"SELECT count(*) FROM sessions s JOIN users u ON u.id = s.user_id "
        f"WHERE u.email = '{theirs}' AND s.revoked_at IS NULL;",
    )
    if untouched != "1":
        raise Failure(
            f"the other member's session was revoked by {mine!r} "
            f"({untouched} still open). A forged revocation is the worst thing "
            "this policy could allow, and it is what the case is here to catch."
        )

    # And a member cannot open a session attributed to somebody else. This one
    # *does* raise, because there is no row to be invisible: `sessions_insert_own`
    # is a `WITH CHECK` and there is no existing row for it to fail quietly
    # against. Same reason for the literal id -- a subquery would make the check
    # reject a NULL and the write would never be attempted for another member.
    must_fail(
        db,
        "open a session for somebody else",
        as_role(
            db,
            "ajo_app",
            mine,
            "INSERT INTO sessions (user_id, refresh_token_hash, device_label, platform) "
            f"VALUES ('{theirs_id}', decode('f3f3f3', 'hex'), 'laptop', 'web');",
        ),
        expect="row-level security",
    )

    # Reading one's own sessions is what 12.4.3's device management needs, and it
    # is the pre-existing SELECT policy rather than anything 103 added. Asserted
    # here so the pair is tested together: a member lists their devices and
    # revokes one, and sees nobody else's.
    seen = scalar(
        db,
        as_role(db, "ajo_app", mine, "SELECT count(*) FROM sessions;"),
    )
    if seen != "1":
        raise Failure(
            f"a member sees {seen} sessions, expected their own 1. Device "
            "management lists devices, so this has to be bounded."
        )

    return (
        "a member revokes their own session, is refused somebody else's and the "
        "one others', and still lists exactly their own"
    )


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


@case("a reused token tells the member, and cannot be made to tell anyone else")
def _reuse_notification(db: str) -> str:
    """
    The half of 12.4.2 that 103 could not reach.

    103 detects a replayed refresh token, revokes every session the member holds,
    and writes an audit row. That is the whole of what it did. The spec's other
    half -- `security.suspicious_token_reuse` "is sent to every registered
    contact" -- went unimplemented, so a member whose sessions were all revoked at
    three in the morning had no way to find out short of noticing that the app had
    quietly forgotten them.

    The mechanism is the transactional outbox, and the reason it is a trigger on
    `audit_logs` rather than a call in the request handler is the thing this case
    mostly pins: **the alarm has to be in the same transaction as the
    revocation.** A worker that polls afterwards has a window in which a crash, a
    deploy or a backlog turns a compromise alarm into silence, and for this one
    event the entire value is that it cannot be lost.

    So the assertion that matters most here is the rollback one. A notification
    that survives a rolled-back revocation is worse than no notification: it tells
    a member their account was just attacked when it was not.

    Every count in this case is scoped to this case's own member. The cases run in
    sequence against one database and the case above exercises reuse detection on
    a different member, so an unscoped count is asserting on another case's
    fixtures -- and would have passed while this case's own member was told
    nothing.
    """
    email = _loginable(db, "notify-reuse@example.ng")
    token = _open_session(db, email, "9a9a9a", device="laptop")
    _open_session(db, email, "9b9b9b", expires_in="30 days", device="phone")

    def outbox_count() -> str:
        return scalar(
            db,
            f"""SELECT count(*) FROM outbox_events
                 WHERE event_type = 'security.suspicious_token_reuse'
                   AND payload->>'user_id' = (SELECT id::text FROM users
                                               WHERE email = '{email}');""",
        )

    # Rollback first, because a rollback that leaked a notification would leave a
    # row behind that the committed test below would then collide with. The
    # replacement hash differs from the committed ones so a leak is visible as a
    # *second* event rather than hiding behind the dedupe index.
    must_succeed(
        db,
        "detect a replay without committing",
        as_role(
            db,
            "ajo_app",
            email,
            f"""SELECT app.claim_refresh_token(
                    decode('{token}', 'hex'), decode('9b0b0b', 'hex'),
                    now(), now() + interval '30 days');""",
        ),
    )
    if outbox_count() != "0":
        raise Failure(
            "a rolled-back token reuse left an outbox event behind; the alarm has "
            "to be in the same transaction as the revocation, or a crash between "
            "them loses a compromise warning -- and a surviving one tells a member "
            "they were attacked when they were not"
        )
    leaked = scalar(
        db,
        f"""SELECT count(*) FROM notifications n
             WHERE n.user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if leaked != "0":
        raise Failure(
            f"a rolled-back token reuse left {leaked} notification(s) behind, so a "
            "member would be told their account was attacked by a transaction that "
            "never happened"
        )

    # Now for real, and in the order the flow actually happens in: the rotation
    # commits first, then the *spent* token is presented. A single committed call
    # cannot demonstrate reuse, because the first presentation of a live token is
    # a rotation -- `rotated`, not `reused`. The spent-token ledger is what turns
    # the second presentation into `reused`, and it only exists if the first call
    # committed.
    rotated = scalar(
        db,
        as_role(
            db,
            "ajo_app",
            email,
            f"""SELECT coalesce((SELECT outcome FROM app.claim_refresh_token(
                    decode('{token}', 'hex'), decode('9c9c9c', 'hex'),
                    now(), now() + interval '30 days')), 'no-row');""",
            commit=True,
        ),
    )
    if rotated != "rotated":
        raise Failure(
            f"the setup rotation reported {rotated!r} where 'rotated' was expected, "
            "so there is no spent-token record and the reuse path cannot be reached"
        )

    outcome = scalar(
        db,
        as_role(
            db,
            "ajo_app",
            email,
            f"""SELECT coalesce((SELECT outcome FROM app.claim_refresh_token(
                    decode('{token}', 'hex'), decode('9d9d9d', 'hex'),
                    now(), now() + interval '30 days')), 'no-row');""",
            commit=True,
        ),
    )
    if outcome != "reused":
        raise Failure(
            f"the committed reuse reported {outcome!r} where 'reused' was expected; "
            "without the reuse branch firing there is no revocation and no alarm"
        )

    # The event reached the outbox, in the transaction that revoked the sessions.
    if outbox_count() != "1":
        raise Failure(
            f"a committed token reuse produced {outbox_count()} outbox events for "
            "this member where 1 was expected; the audit_logs trigger is the only "
            "thing putting it there"
        )

    # Drain first. Materialisation is the drain's job, not the trigger's: the
    # trigger writes one outbox row per event, and turning that into a row per
    # channel is what `app.drain_security_notifications` does. Asserting on
    # `notifications` before draining would be asserting on the wrong half, and
    # would read as "the trigger enqueued nothing" when the trigger enqueued
    # exactly what it should.
    must_succeed(
        db,
        "materialise the queued notifications",
        "SELECT count(*) FROM app.drain_security_notifications();",
    )

    # One notification per channel, and only for active security templates. Checked
    # per channel rather than as a total, because a total of 3 also matches "3
    # pushes, no email", which would leave the member with nothing readable.
    for channel in ("email", "sms", "push"):
        got = scalar(
            db,
            f"""SELECT count(*) FROM notifications
                 WHERE event_key = 'security.suspicious_token_reuse'
                   AND channel = '{channel}'
                   AND status = 'queued'
                   AND user_id = (SELECT id FROM users WHERE email = '{email}');""",
        )
        if got != "1":
            raise Failure(
                f"the reuse alarm queued {got} {channel} notification(s) where 1 was "
                "expected; every active security template has to be materialised"
            )

    # SMS is not optional, and the reason is in the schema rather than in this
    # migration: `app.assert_money_critical_has_sms` is a deferred constraint
    # trigger that refuses to commit any `is_security` template whose event has no
    # active SMS template. CANONICAL.md section 8 prints an em dash for
    # `security.login_new_device`, and the trigger has been contradicting that
    # cell since migration 000. Asserted because the day someone "fixes" the
    # catalogue by dropping the sms rows, the migration stops applying at all.
    sms_template = scalar(
        db,
        "SELECT count(*) FROM notification_templates "
        "WHERE event_key = 'security.suspicious_token_reuse' AND channel = 'sms' "
        "AND is_active;",
    )
    if sms_template != "1":
        raise Failure(
            "there is no active sms template for the reuse event, which "
            "app.assert_money_critical_has_sms refuses to let the migration commit "
            "without; this means the template was deactivated after the fact"
        )

    # And the recipient is a real address, resolved for the member rather than
    # hardcoded, because 12.4.2 says "every registered contact".
    recipient = scalar(
        db,
        f"SELECT app.member_email((SELECT id FROM users WHERE email = '{email}'));",
    )
    if recipient.strip() != email:
        raise Failure(
            f"member_email returned {recipient.strip()!r} where {email!r} was "
            "expected; the alarm would be delivered to nobody"
        )

    # Preference suppression. A member who has switched off every channel must
    # still be told, because section 6 says security events "cannot be switched
    # off" -- and because a preference that silences this particular alarm means an
    # attacker holding live sessions against an account that asked not to be
    # disturbed. Set explicitly rather than relying on defaults, and with quiet
    # hours set to cover a 3am breach, because quiet hours are the subtler half:
    # deferring a breach detected at 3am to 7am is how the attacker finishes.
    must_succeed(
        db,
        "a member who has switched off every channel",
        f"""
        INSERT INTO notification_preferences
          (user_id, push_enabled, email_enabled, sms_enabled, money_sms_opt_in,
           quiet_hours_start, quiet_hours_end)
        VALUES ((SELECT id FROM users WHERE email = '{email}'),
                false, false, false, false, '23:00', '06:00')
        ON CONFLICT (user_id) DO UPDATE
          SET push_enabled = false, email_enabled = false, sms_enabled = false, money_sms_opt_in = false;
        """,
    )
    suppressed = scalar(
        db,
        f"""SELECT count(*) FROM notifications
             WHERE event_key = 'security.suspicious_token_reuse'
               AND status = 'queued'
               AND user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if suppressed != "3":
        raise Failure(
            f"a member with every channel disabled and quiet hours set still has "
            f"{suppressed} queued reuse notification(s) where 3 was expected; a "
            "security alarm cannot be switched off, and quiet hours must not defer "
            "a breach detected at 3am to 7am"
        )

    return (
        "a replayed token queues a push, an email and an SMS for every registered "
        "contact in the same transaction that revoked the sessions; a rolled-back "
        "reuse queues nothing; and a member who has disabled every channel and set "
        "quiet hours is told anyway"
    )


@case("a new device is recognised once, and only when it is new")
def _new_device_notification(db: str) -> str:
    """
    US-04 and US-05 pull in opposite directions and the naive implementation
    loses to both.

    US-05 wants an alert when a session appears from a device the member does not
    recognise. US-04 says revoking a session must not raise one. Read literally
    with "a session exists" as the test, the second is unreachable -- revoking
    creates and removes sessions -- so the question is which rows count as
    evidence, and the answer that satisfies both is *all of them*.

    Every session row the member has ever had, revoked ones included. Revocation
    is not deletion: 103 revoked a row specifically so that a revoked session
    used afterwards is evidence rather than a lookup miss. Those same rows are
    also the record that this member has used this device before, so the history
    that makes theft detectable is the history that stops false alarms.

    The failure this prevents is quiet and cumulative. Sign out and back in on
    the same phone -- the common case, and people sign out constantly -- and a
    live-only check finds no prior session and sends "we have not seen this
    device before". Do that a few times and the member learns the alert is noise,
    which is precisely the state in which it cannot report the one time it
    mattered.
    """
    email = _loginable(db, "notify-device@example.ng")
    _loginable(db, "notify-device-2@example.ng")
    uid_sql = f"(SELECT id FROM users WHERE email = '{email}')"

    def check(platform, device_label) -> str:
        """Runs the detection and returns its verdict, on a fresh session id."""
        platform_sql = "'%s'" % platform if platform is not None else "NULL"
        label_sql = "'%s'" % device_label if device_label is not None else "NULL"
        return scalar(
            db,
            f"""SELECT app.record_login_new_device(
                    {uid_sql}, gen_random_uuid(), {platform_sql}, {label_sql},
                    '198.51.100.7', 'TestAgent/1.0');""",
        )

    # The first use of a device is new, and says so.
    if check("web", "Work laptop") != "t":
        raise Failure(
            "the first login from a device reported it as already known, so the "
            "alert for a genuinely new device is never sent"
        )

    # And the audit row it wrote is the thing the trigger turns into an outbox
    # event. Asserted through the outbox, because that is the delivery path and
    # an audit row nobody drains is not an alert.
    alerted = scalar(
        db,
        "SELECT count(*) FROM outbox_events WHERE event_type = "
        "'security.login_new_device';",
    )
    if alerted != "1":
        raise Failure(
            f"a new device produced {alerted} outbox event(s) where 1 was expected; "
            "FR-SEC-002 requires the alert and only the trigger enqueues it"
        )

    # The payload carries what the templates render. The device label in
    # particular, because a notification saying "new sign-in from an unknown
    # device" with no device on it is not much of a warning -- the member cannot
    # act on what they cannot compare against the device in their hand.
    # Asked of the database rather than read into Python, because `scalar` returns
    # one line and these bodies are multi-line -- reading the first line of an
    # email template and concluding it has no placeholder in it would pass for
    # exactly the templates it is supposed to catch.
    mentions_device = scalar(
        db,
        """SELECT count(*) FROM notification_templates t
            WHERE t.event_key = 'security.login_new_device'
              AND t.channel = 'email'
              AND t.body LIKE '%{{device_label}}%';""",
    )
    if mentions_device != "1":
        raise Failure(
            "the login_new_device email template does not reference the device "
            "label; a notification saying 'new sign-in from an unknown device' "
            "with no device on it is not much of a warning, because the member "
            f"cannot compare it against the device in their hand (count {mentions_device})"
        )

    # Now the half that needs a real session row rather than just the function.
    # The detection is called before the INSERT in the real flow, so a fixture
    # that inserts first and then asks is asking a different question -- which is
    # why the row below is inserted *after* the first check, standing in for a
    # session that has since been signed out.
    must_succeed(
        db,
        "a session on the same device, then signed out",
        f"""
        INSERT INTO sessions (user_id, refresh_token_hash, device_label, platform,
                              refresh_expires_at)
        SELECT id, decode('ab1ab1', 'hex'), 'Work laptop', 'web',
               now() + interval '30 days'
          FROM users WHERE email = '{email}';
        UPDATE sessions AS s SET revoked_at = now(), revoked_reason = 'signed_out'
          FROM users u WHERE u.id = s.user_id AND u.email = '{email}';
        """,
    )
    if check("web", "Work laptop") != "f":
        raise Failure(
            "a device the member had signed out of was reported as new, so every "
            "sign-out and sign-in sends a 'we have not seen this device' alert; "
            "training people to ignore the alert is how it stops working"
        )

    # A genuinely different device on the same member still alerts, which is the
    # half that breaks first if the function returns a constant or matches on the
    # member rather than the device.
    if check("android", "Pixel 8") != "t":
        raise Failure(
            "a second device on the same member was not reported as new, so the "
            "lookup is matching the member rather than the device"
        )

    # US-04: revoking a session must not raise an alert. Revoke the phone session
    # the previous check stood in for, then ask about that device again. The
    # outbox count is compared before and after, because the function returning
    # "not new" and the function returning "new but failing to enqueue" are the
    # same failure seen from two sides, and only the count separates them.
    must_succeed(
        db,
        "revoke the phone session",
        f"""
        INSERT INTO sessions (user_id, refresh_token_hash, device_label, platform,
                              refresh_expires_at)
        SELECT id, decode('ab2ab2', 'hex'), 'Pixel 8', 'android',
               now() + interval '30 days'
          FROM users WHERE email = '{email}';
        UPDATE sessions AS s SET revoked_at = now(), revoked_reason = 'revoked_by_member'
          FROM users u WHERE u.id = s.user_id AND u.email = '{email}'
          AND s.device_label = 'Pixel 8';
        """,
    )
    before = scalar(
        db,
        "SELECT count(*) FROM outbox_events WHERE event_type = 'security.login_new_device';",
    )
    if check("android", "Pixel 8") != "f":
        raise Failure(
            "US-04 is explicit that revoking a session must not send a "
            "security.login_new_device alert, but the revoked device was reported "
            "as new"
        )
    after = scalar(
        db,
        "SELECT count(*) FROM outbox_events WHERE event_type = 'security.login_new_device';",
    )
    if before != after:
        raise Failure(
            f"US-04 is explicit that revoking a session must not send a "
            f"security.login_new_device alert, but the outbox went from {before} "
            f"to {after} events"
        )

    # The NULL case, which decides how many alerts a browser client sends.
    # `sessions.device_label` is nullable and a client that sends nothing produces
    # a row of NULLs; under plain `=` every such client collides with every other
    # one, because NULL = NULL is unknown. That would mean the sixth silent login
    # alerts and the first five do not -- an ordering no user can explain and no
    # support answer can give.
    #
    # The fixture row matters: `record_login_new_device` reads `sessions`, and in
    # the real flow it is called *before* the INSERT. Calling it twice with no row
    # in between asserts that a function which inserts nothing can distinguish two
    # consecutive calls, which it cannot and should not -- so the row is written
    # here too, standing in for the session the first call would have been
    # followed by.
    if check(None, None) != "t":
        raise Failure(
            "a client's very first sign-in with no device label and no platform "
            "was not reported as new"
        )
    must_succeed(
        db,
        "a session with no device label and no platform",
        f"""
        INSERT INTO sessions (user_id, refresh_token_hash, device_label, platform,
                              refresh_expires_at)
        SELECT id, decode('ac1ac1', 'hex'), NULL, NULL, now() + interval '30 days'
          FROM users WHERE email = '{email}';
        """,
    )
    if check(None, None) != "f":
        raise Failure(
            "a second sign-in with no device label was reported as new, so the "
            "NULL comparison is not matching NULLs to each other; every member on "
            "an older client build gets an alert on every login after the first"
        )

    # And one member's devices never alert for another. Without this the whole
    # case could pass on a query that matched any session anywhere in the table,
    # which is the failure mode a member-scoping assertion exists to catch.
    stranger = scalar(
        db,
        """SELECT app.record_login_new_device(
                (SELECT id FROM users WHERE email = 'notify-device-2@example.ng'),
                gen_random_uuid(), 'web', 'Work laptop', '198.51.100.9', 'Other/1.0');""",
    )
    if stranger != "t":
        raise Failure(
            "a device belonging to a different member was treated as already "
            "known, so the lookup is not scoped to the member"
        )

    return (
        "a first device alerts, a signed-out device does not, a second device on "
        "the same member does, revocation never alerts, NULL device labels match "
        "each other, and one member's devices are invisible to another"
    )


@case("notifications are queued once, leased once, and delivered")
def _notification_delivery(db: str) -> str:
    """
    The queue semantics, which are the difference between a working alarm and a
    plausible-looking one.

    Materialisation is exactly-once per channel: `notifications_dedupe_unique` is
    UNIQUE on (dedupe_key, channel), so a replayed event cannot produce a second
    email. Delivery is at-least-once, because `notification_status` has no
    in-flight value and `app.claim_queued_notifications` leases a row by pushing
    `scheduled_for` forward rather than by marking it sent.

    That asymmetry is deliberate and it is the right way round for these two
    events specifically. A member who receives "we signed you out, was this you?"
    twice has been frightened twice and has lost nothing. A member who receives it
    zero times has been robbed. The two failures are not equivalent, so a queue
    that quietly drops a row when a worker dies -- which is what exactly-once
    delivery would buy -- is the wrong side of that trade.

    Which is only defensible if the lease actually expires. If it did not, a worker
    crash would strand the row forever and the alarm would be lost silently, which
    is the failure at-least-once delivery exists to avoid.

    Scoped to this case's own member and event throughout, for the reason the case
    above gives: the cases share a database and earlier ones leave pending outbox
    rows behind.
    """
    email = _loginable(db, "notify-drain@example.ng")
    token = _open_session(db, email, "9e9e9e", device="laptop")

    must_succeed(
        db,
        "rotate, then detect the reuse",
        as_role(
            db,
            "ajo_app",
            email,
            f"""SELECT app.claim_refresh_token(
                    decode('{token}', 'hex'), decode('9f0f0f', 'hex'),
                    now(), now() + interval '30 days');
                SELECT app.claim_refresh_token(
                    decode('{token}', 'hex'), decode('9f1f1f', 'hex'),
                    now(), now() + interval '30 days');""",
            commit=True,
        ),
    )

    mine = f"(payload->>'user_id' = (SELECT id::text FROM users WHERE email = '{email}'))"

    # The outbox row is still pending: nothing has drained it.
    pending = scalar(
        db,
        f"SELECT count(*) FROM outbox_events WHERE event_type = "
        f"'security.suspicious_token_reuse' AND {mine};",
    )
    if pending != "1":
        raise Failure(
            f"{pending} outbox event(s) are pending for this member where 1 was "
            "expected; the event should sit in the outbox until a worker drains it"
        )

    # The drain is global by design -- it is a worker's job to empty the queue, not
    # to pick an event -- and it takes a batch limit. The cases above share a
    # database and left their own pending events behind, so the queue is emptied
    # in a loop before this case asserts on its own member. Otherwise the batch
    # limit fills with another case's rows and this one concludes its alarm was
    # never materialised.
    while scalar(db, "SELECT count(*) FROM app.drain_security_notifications();") != "0":
        pass

    drained = scalar(
        db,
        f"""SELECT count(*) FROM notifications
             WHERE event_key = 'security.suspicious_token_reuse'
               AND user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if drained != "3":
        raise Failure(
            f"draining produced {drained} notification(s) for this member where 3 "
            "was expected (push, email and sms); a channel silently missing from "
            "the drain is a channel the member is never told on"
        )

    published = scalar(
        db,
        f"SELECT count(*) FROM outbox_events WHERE event_type = "
        f"'security.suspicious_token_reuse' AND status = 'published' AND {mine};",
    )
    if published != "1":
        raise Failure(
            f"{published} outbox event(s) are published where 1 was expected; the "
            "event and its notifications have to move together or a crash between "
            "them loses the alarm"
        )

    # A second drain finds nothing. Idempotence is what makes a retrying worker
    # safe, and without it every retry would email the member again.
    # Counting what the *second drain returns*, which is the only thing that shows
    # whether it did any work. Counting rows that exist instead would be 3 by
    # design -- the first drain created them -- and would fail for the right
    # behaviour having been the right behaviour.
    #
    # Scoped to this member, like everything else in this case. An earlier case's
    # event can become eligible between the drain loop above and this call -- a
    # lease expiring, a deferred row coming due -- and a global count then reports
    # another case's work as this one re-sending its alarm. That is a real
    # dependency on wall-clock time, and it fails on a fast machine more often
    # than a slow one.
    again = scalar(
        db,
        f"""SELECT count(*) FROM app.drain_security_notifications()
             WHERE user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if again != "0":
        raise Failure(
            f"a second drain produced {again} notification(s) for this member where "
            "0 was expected; draining has to be idempotent or a retrying worker "
            "spams the member with the same alarm"
        )

    # Claiming leases the rows rather than consuming them, so they come back. Only
    # this member's rows are counted, because other cases have queued theirs.
    claimed = scalar(
        db,
        f"""SELECT count(*) FROM app.claim_queued_notifications(500)
             WHERE user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if claimed != "3":
        raise Failure(
            f"claiming returned {claimed} notification(s) for this member where 3 "
            "was expected"
        )
    still_queued = scalar(
        db,
        f"""SELECT count(*) FROM notifications
             WHERE event_key = 'security.suspicious_token_reuse'
               AND status = 'queued'
               AND user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if still_queued != "3":
        raise Failure(
            f"claiming consumed {3 - still_queued} of 3 rows; a lease must not mark "
            "a row sent, because a worker that dies mid-send would then drop the "
            "alarm silently"
        )

    # Within the lease they are invisible, which is what stops two API replicas
    # from sending the same alarm twice.
    reentrant = scalar(
        db,
        f"""SELECT count(*) FROM app.claim_queued_notifications(500)
             WHERE user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if reentrant != "0":
        raise Failure(
            f"a second claim inside the lease window returned {reentrant} rows where "
            "0 was expected; two API replicas would send the same alarm twice"
        )

    # Recipients resolve per channel. push has none, and saying so is better than a
    # function that returns NULL for every real member and looks like it works.
    push_rows = scalar(
        db,
        f"""SELECT count(*) FROM app.claim_queued_notifications(1, 1)
             WHERE channel = 'push'
               AND user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if push_rows != "0":
        raise Failure(
            "a leased push row was offered again with a one-second lease, so the "
            "lease length is not being applied; the claimed set here should be "
            "another member's, not this one's"
        )

    # Sent and failed both land, with a bounded failure_detail.
    note_id = scalar(
        db,
        f"""SELECT id::text FROM notifications
             WHERE event_key = 'security.suspicious_token_reuse' AND channel = 'email'
               AND user_id = (SELECT id FROM users WHERE email = '{email}')
             LIMIT 1;""",
    )
    must_succeed(
        db,
        "mark one sent and one failed",
        f"""
        SELECT app.mark_notification_sent('{note_id}');
        SELECT app.mark_notification_failed(
          (SELECT id FROM notifications
            WHERE event_key = 'security.suspicious_token_reuse' AND channel = 'sms'
              AND user_id = (SELECT id FROM users WHERE email = '{email}')),
          repeat('x', 900));
        """,
    )
    final = scalar(
        db,
        f"""SELECT status::text FROM notifications WHERE id = '{note_id}'::uuid;""",
    )
    if final.strip() != "sent":
        raise Failure(
            f"mark_notification_sent did not land: status is {final.strip()!r}"
        )

    bounded = scalar(
        db,
        f"""SELECT length(failure_detail) FROM notifications
             WHERE event_key = 'security.suspicious_token_reuse' AND channel = 'sms'
               AND user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if bounded.strip() != "500":
        raise Failure(
            f"failure_detail came back {bounded.strip()} characters where 500 was "
            "expected; a provider error body can be megabytes and this column is "
            "free text"
        )

    # The lease expires, so a crashed worker's rows return. `scheduled_for` is
    # pushed back rather than waiting out the five-minute default.
    must_succeed(
        db,
        "expire this member's leases",
        f"""UPDATE notifications SET scheduled_for = now() - interval '1 second'
              WHERE status = 'queued'
                AND user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    recovered = scalar(
        db,
        f"""SELECT count(*) FROM app.claim_queued_notifications(500)
             WHERE user_id = (SELECT id FROM users WHERE email = '{email}');""",
    )
    if recovered != "1":
        raise Failure(
            f"{recovered} row(s) came back after the lease expired where 1 was "
            "expected; a worker crash would otherwise strand the alarm forever, "
            "which is the failure at-least-once delivery is supposed to prevent"
        )

    return (
        "draining materialises push, email and sms and publishes the event in one "
        "call; a second drain and a second claim inside the lease both return "
        "nothing; an expired lease returns the row; sent and failed both land with "
        "a bounded failure detail"
    )


@case("the delivery functions are not open to the whole cluster")
def _notification_grants(db: str) -> str:
    """
    `bootstrap_roles.sql` runs before any migration, so its
    `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO ajo_app` covers the functions
    that existed when it ran and nothing created afterwards. The functions in 103
    are reachable only because PostgreSQL's default is EXECUTE TO PUBLIC and that
    bootstrap's REVOKE had already happened by the time they were created.

    That default is too loose for these. `app.drain_security_notifications` and
    `app.claim_queued_notifications` take a user id from their caller and write
    real rows that a real relay sends mail from, so any role holding EXECUTE can
    address an alarm to an arbitrary member -- and PUBLIC includes every role in
    the cluster, including ones nobody has added yet.

    A phishing-shaped use: an attacker with any database foothold writes
    "your account was compromised, email this link to reclaim it" into a real
    member's notification stream, from the system's own sender, timed to a real
    event. It needs nothing but EXECUTE on one function.
    """
    # PUBLIC must be gone. Asserted via `has_function_privilege` with the
    # `public` pseudo-role, because checking `proacl` directly requires knowing
    # the grant order and the null case is ambiguous.
    for fn, args in (
        ("app.drain_security_notifications", "integer"),
        ("app.claim_queued_notifications", "integer, integer"),
        ("app.mark_notification_sent", "uuid"),
        ("app.mark_notification_failed", "uuid, text"),
    ):
        open_to_public = scalar(
            db,
            f"""SELECT has_function_privilege('public', '{fn}({args})', 'EXECUTE');""",
        )
        if open_to_public.strip() == "t":
            raise Failure(
                f"{fn} is still executable by PUBLIC; any role in the cluster can "
                "address a security alarm to an arbitrary member"
            )

    # And the login path must still work, or the migration has broken the thing
    # it was written for. `app.record_login_new_device` is called from the API's
    # login handler as `ajo_app`, so it has to be reachable -- asserted as the
    # role the worker connects as, which is `ajo_api`, a member of `ajo_app`.
    for fn, args in (
        ("app.record_login_new_device", "uuid, uuid, text, text, inet, text"),
        ("app.enqueue_security_notification", "text, uuid, uuid, jsonb"),
        ("app.member_email", "uuid"),
        ("app.drain_security_notifications", "integer"),
    ):
        reachable = scalar(
            db,
            f"""SELECT has_function_privilege('ajo_api', '{fn}({args})', 'EXECUTE');""",
        )
        if reachable.strip() != "t":
            raise Failure(
                f"{fn} is not executable by ajo_api, so either the login path or "
                "the delivery worker cannot call it; the REVOKE went one step too "
                "far"
            )

    # `ajo_analytics` is the reporting role and gets no DML anywhere in this
    # repository. It must not be able to send.
    for fn, args in (
        ("app.drain_security_notifications", "integer"),
        ("app.claim_queued_notifications", "integer, integer"),
    ):
        analytics = scalar(
            db,
            f"""SELECT has_function_privilege('ajo_analytics', '{fn}({args})', 'EXECUTE');""",
        )
        if analytics.strip() == "t":
            raise Failure(
                f"ajo_analytics can call {fn}; a reporting role that can write "
                "notification rows can send mail from the system sender"
            )

    return (
        "the four delivery functions are closed to PUBLIC and to analytics, and "
        "the login path and worker functions are still reachable as ajo_api"
    )


@case("templates render from the payload, and a missing key is not a failure")
def _template_rendering(db: str) -> str:
    """
    `{{key}}` substitution, tested on its own because the interesting failures are
    all in the edges.

    Three decisions, and the last one is the one worth arguing about.

    A key the payload did not supply substitutes to empty, because the alternative
    is failing to deliver a compromise alarm over an optional field. The body
    should be slightly odd -- "at  from android" -- not absent. That reads like a
    typo to the member, which is survivable; silence is not.

    A placeholder nobody supplied is left alone, so the caller can strip it. That
    split is what lets the drain be one pass: substitute everything the payload
    has, then remove whatever is left. A template typo therefore produces a
    visibly wrong message that a human notices, rather than a silently truncated
    one that nobody does.

    And substitution is not recursive. A device label is attacker-influenced text
    -- it comes from the client that is logging in -- so if the implementation
    re-scanned its own output, a member whose device is named `{{platform}}` would
    have the platform substituted into their notification, and a label naming a
    template key could pull arbitrary payload values into the message. Small, but it
    is our own mail rendering untrusted input twice, and the fix is one `replace`
    call rather than a loop.

    The NULL cases are asserted because a raise inside the drain takes the whole
    batch with it: one malformed row would stop every security alarm in flight.
    """
    # The ordinary case. The unsupplied `{{ip_address}}` deliberately stays put,
    # because `record_login_new_device` writes that key as a JSON null rather than
    # omitting it, and the empty substitution is what produces "at  from".
    got = scalar(
        db,
        """SELECT app.render_notification_body(
                 'Device: {{device_label}} at {{ip_address}} from {{platform}}',
                 '{"device_label": "Pixel 8", "platform": "android"}'::jsonb);""",
    )
    expected = "Device: Pixel 8 at {{ip_address}} from android"
    if got.strip() != expected:
        raise Failure(
            "substitution should replace supplied keys and leave unsupplied "
            f"placeholders for the caller to strip; expected {expected!r} and got "
            f"{got.strip()[:200]!r}"
        )

    # An explicitly null value, which is not the same as an absent key and is the
    # case this function actually sees in production: `record_login_new_device`
    # puts a real JSON null in the payload for a client that sent no device label.
    # `jsonb_each_text` yields SQL NULL for it, so without a coalesce the whole
    # `replace` returns NULL and the drain raises on a real login.
    null_value = scalar(
        db,
        """SELECT coalesce(
                 app.render_notification_body('Device: {{device_label}}',
                   '{"device_label": null}'::jsonb), '<null>');""",
    )
    if null_value.strip() != "Device:":
        raise Failure(
            "an explicitly null payload value should render as empty, not NULL and "
            f"not the text 'null'; got {null_value.strip()[:120]!r}"
        )

    # Not recursive: a substituted value that looks like a placeholder is inert.
    not_recursive = scalar(
        db,
        """SELECT app.render_notification_body(
                 'Device: {{device_label}}',
                 '{"device_label": "{{platform}}"}'::jsonb);""",
    )
    if not_recursive.strip() != "Device: {{platform}}":
        raise Failure(
            "substitution recursed into a substituted value; a device label of "
            f"'{{{{platform}}}}' was rendered as the platform: "
            f"{not_recursive.strip()[:200]!r}"
        )

    # NULL in, template out. Returning the template unchanged rather than NULL is
    # deliberate: a NULL body would violate `notifications.body NOT NULL` and the
    # insert would fail.
    null_template = scalar(
        db,
        """SELECT coalesce(app.render_notification_body(NULL, '{}'::jsonb), '<null>');""",
    )
    if null_template.strip() != "<null>":
        raise Failure(
            f"a NULL template should render to NULL, not raise; got "
            f"{null_template.strip()[:120]!r}"
        )
    null_payload = scalar(
        db,
        """SELECT app.render_notification_body('body', NULL);""",
    )
    if null_payload.strip() != "body":
        raise Failure(
            "a NULL payload should leave the template unchanged rather than raise "
            f"or blank it; got {null_payload.strip()[:120]!r}"
        )

    # The rows that actually ship. The two cases above leave queued rows behind,
    # and this one reads `notifications`, so the queue is materialised first --
    # otherwise there is nothing here to inspect and the count is zero by
    # accident.
    while scalar(db, "SELECT count(*) FROM app.drain_security_notifications();") != "0":
        pass

    # No placeholder left in any shipped body, on any channel. Checked across the
    # whole table rather than for one event, because the two templates differ in
    # exactly the place a leftover would hide: the reuse bodies have no
    # `{{device_label}}` at all, so a strip that only worked for keys the template
    # happened to use would leave the SMS ones clean by luck.
    leftovers = scalar(
        db,
        "SELECT count(*) FROM notifications WHERE body LIKE '%{{%' OR body LIKE '%}}%';",
    )
    if leftovers != "0":
        raise Failure(
            f"{leftovers} queued notification(s) still contain a placeholder; the "
            "drain strips them, and a leftover in a security email erodes trust in "
            "the one message that has to be believed"
        )

    # The rendered reuse email actually says what happened, on the channel a
    # member is most likely to read carefully. Asked of the database in one
    # expression because `scalar` returns a single line and these bodies are
    # multi-line, so reading the first line into Python would pass for exactly the
    # templates it is meant to catch.
    # Counted as "how many reuse emails *fail* the test", because the cases above
    # share a database and have queued this event for several members -- an
    # equality check against 1 would be asserting on how many fixtures ran.
    silent = scalar(
        db,
        """SELECT count(*) FROM notifications
             WHERE event_key = 'security.suspicious_token_reuse'
               AND channel = 'email'
               AND (body NOT LIKE '%already been used%'
                 OR body NOT LIKE '%signed out%'
                 OR body NOT LIKE '%password%');""",
    )
    if silent != "0":
        raise Failure(
            f"{silent} reuse email(s) do not say what happened and what to do -- a "
            "member who does not know to change their password cannot respond to "
            "the alarm, so the notification exists and communicates nothing"
        )

    return (
        "supplied keys substitute and unsupplied ones survive for the caller to "
        "strip, a JSON null renders as empty, substitution is not recursive so a "
        "device label cannot inject into the template, NULL renders without "
        "raising, and the shipped notifications retain no placeholder"
    )

# The ids are fixed rather than generated so a failing case can be re-run by hand
# against the same rows, and so two cases in this file can talk about the same Ajo
# without passing it around.
MONEY_AJO = "01b00000-0000-7000-8000-000000000001"
MONEY_ROUND = "01b00000-0000-7000-8000-000000000010"


def _money_ajo(db: str) -> str:
    """
    One member, one Ajo, one round, one contribution, one confirmed payment.

    A fixture, and an unusually complete one, because the capture function reads
    `contributions`, `rounds`, `payments` and `fees` and writes to all four plus
    two ledger tables. Any of them missing turns a real failure into a fixture
    error, and a fixture error looks exactly like a broken money path.

    Everything is in one transaction because `assert_organizer_is_member` is
    deferred and fires at COMMIT: the Ajo, its positions and the organizer's
    membership have to land together or the Ajo is refused. That is the schema
    stating the creator occupies one of the seats, and it is why the positions are
    inserted here rather than left to whoever needs them.

    The payment is `success`. That is not a shortcut around the provider -- it is
    the boundary this migration is drawn at. Something else, later, sets that
    status, and only from a signature-verified webhook. What is being tested here
    is what happens once the provider has said yes.
    """
    must_succeed(
        db,
        "a member, an Ajo, a round and a confirmed payment",
        "\n".join(
            [
                "BEGIN;",
                f"INSERT INTO users (auth_subject_id, email, status) "
                f"VALUES ('money-1', 'money-a@example.ng', 'active') "
                f"ON CONFLICT DO NOTHING;",
                f"""INSERT INTO ajos (
                      id, name, organizer_user_id, contribution_amount_kobo,
                      frequency_id, enrollment_opens_at, enrollment_closes_at,
                      total_rounds, currency, status, position_count
                    ) SELECT '{MONEY_AJO}', 'Test savings group', u.id, 1000000,
                      f.id, now() - interval '1 day', now() + interval '4 days',
                      3, 'NGN', 'draft', 5
                      FROM users u, contribution_frequencies f
                     WHERE u.email = 'money-a@example.ng' AND f.code = 'weekly'
                    ON CONFLICT DO NOTHING;""",
                # Five, because the Ajo says it has five seats and
                # `materialize_organizer_membership` binds the organizer to the
                # lowest free one as a side effect of this insert.
                f"""INSERT INTO ajo_positions (ajo_id, position_number)
                    SELECT a.id, n FROM ajos a, generate_series(1, 5) AS n
                     WHERE a.id = '{MONEY_AJO}'
                    ON CONFLICT DO NOTHING;""",
                f"""INSERT INTO rounds (
                      id, ajo_id, round_number, status, due_date, opens_at,
                      closes_at, target_amount_kobo
                    ) SELECT '{MONEY_ROUND}', a.id, 1, 'in_progress', current_date,
                      now(), now() + interval '3 days', 1000000
                      FROM ajos a WHERE a.id = '{MONEY_AJO}'
                    ON CONFLICT DO NOTHING;""",
                f"""INSERT INTO contribution_schedules (
                      round_id, ajo_id, due_date, expected_amount_kobo,
                      expected_member_count, late_cutoff_at
                    ) SELECT r.id, r.ajo_id, r.due_date, 1000000, 5,
                      now() + interval '5 days'
                      FROM rounds r WHERE r.id = '{MONEY_ROUND}'
                    ON CONFLICT DO NOTHING;""",
                f"""INSERT INTO contributions (
                      schedule_id, member_id, position_id, ajo_id, round_id,
                      user_id, amount_kobo, due_date
                    ) SELECT s.id, m.id, m.position_id, s.ajo_id, s.round_id,
                      m.user_id, 1000000, s.due_date
                      FROM contribution_schedules s
                      JOIN ajo_members m ON m.ajo_id = s.ajo_id
                        AND m.user_id = (SELECT id FROM users
                                          WHERE email = 'money-a@example.ng')
                     WHERE s.round_id = '{MONEY_ROUND}'
                    ON CONFLICT DO NOTHING;""",
                # `charged_amount_kobo` and `fee_kobo` are generated. Writing
                # either here would be an error, which is the point: the fee is
                # derived by the schema and cannot be supplied by a caller.
                """INSERT INTO payments (
                      contribution_id, channel_id, idempotency_key, provider,
                      provider_reference, contribution_amount_kobo, status,
                      provider_completed_at
                    ) SELECT c.id, ch.id, 'idem-money-1', 'mock', 'mock-ref-1',
                      1000000, 'success', now()
                      FROM contributions c, payment_channels ch
                     WHERE c.round_id = '%s' AND ch.code = 'bank_transfer'
                    ON CONFLICT DO NOTHING;""" % MONEY_ROUND,
                "COMMIT;",
            ]
        ),
    )
    return "money-a@example.ng"


def _capture(db: str, idempotency: str = "idem-money-1") -> str:
    """Recognises a capture, returning the two ledger transaction ids."""
    return scalar(
        db,
        f"""SELECT array_to_string(
                  app.post_collection_capture(
                    (SELECT id FROM payments WHERE idempotency_key = '{idempotency}'),
                    (SELECT id FROM users WHERE email = 'money-a@example.ng')),
                  ',') AS joined;""",
    )


def _postings_for(db: str, kind: str, ids: str | None = None) -> list[tuple[str, str, int]]:
    """
    The postings of every entry of one kind, as (account, side, amount).

    `psql` runs with `-tAF "|"`, so `scalar` treats any line containing a pipe
    as multi-column noise and skips it. Emitting `a|b|1` here therefore reads as
    zero rows, which is a silent pass rather than a failure -- the shape of the
    assertions below had to stop using `scalar` for that reason.

    `ids` narrows to the entries a particular capture produced. Every case shares
    one database and the rows are real, so "the postings of every
    `contribution.received` in the table" is a moving target: the case that proves
    a balanced entry can be written writes one, and the case after it then counts
    its own two plus that one. Each case has to be about its own entries.
    """
    only = f"AND t.id = ANY(string_to_array('{ids}', ',')::uuid[])" if ids else ""
    rows = []
    for line in psql(
        db,
        f"""SELECT p.account_kind::text || '|' || p.side::text || '|'
                   || p.amount_kobo::text
              FROM ledger_transactions t
              JOIN ledger_postings p ON p.transaction_id = t.id
             WHERE t.kind = '{kind}' {only}
             ORDER BY t.occurred_at, p.account_kind;""",
    ).splitlines():
        if "|" not in line:
            continue
        account, side, amount = line.strip().split("|")
        rows.append((account, side, int(amount)))
    return rows


@case("a confirmed collection is recognised exactly once, and only once")
def _collection_capture(db: str) -> str:
    """
    The first money this system has ever moved.

    The claim is narrow and load-bearing: given a payment the provider has
    confirmed, the books come out right, the fee is itemised, and doing it again
    changes nothing. Everything a member would later dispute -- what was collected,
    what the platform earned, what the group is owed -- is decided by this one
    function, and none of it was previously possible because there was no writer.
    """
    _money_ajo(db)

    first = _capture(db)
    if first.count(",") != 1:
        raise Failure(
            f"a capture produced {first!r} rather than two ledger transactions; "
            "BR-021 splits the contribution and the fee so each is answerable alone"
        )

    # Exactly two entries, in the order BR-021 fixes, each balanced on its own.
    #
    # Compared as sorted tuples because `_postings_for` orders by `account_kind`,
    # and that is an enum: it sorts by declaration order, so `escrow_cash` comes
    # first and `contributions_receivable` second, regardless of the alphabet.
    # Writing the expectation in that order would be an assertion about the enum
    # that happens to sit next to an assertion about the postings.
    if sorted(_postings_for(db, "contribution.received", first)) != sorted([
        ("contributions_receivable", "credit", 1000000),
        ("escrow_cash", "debit", 1000000),
    ]):
        raise Failure(
            "contribution.received is not debit escrow / credit receivable for the "
            "contribution amount: "
            f"{_postings_for(db, 'contribution.received', first)}"
        )

    # 2% of 1,000,000 kobo is 20,000, and it is on its own entry rather than
    # folded into the one above. A reader who finds the fee missing has no way to
    # tell "no fee was taken" from "the fee was recorded as contribution".
    if sorted(_postings_for(db, "fee.recognised", first)) != sorted([
        ("escrow_cash", "debit", 20000),
        ("fees_income", "credit", 20000),
    ]):
        raise Failure(
            "fee.recognised is not debit escrow / credit fees_income for exactly "
            f"2%: {_postings_for(db, 'fee.recognised', first)}"
        )

    # The order. Same instant, so this cannot be asserted on a timestamp and is
    # asserted on the ordinal instead -- BR-021 says the sequence is mandatory and
    # ordered, and two entries stamped now() carry no order of their own.
    order = scalar(
        db,
        f"""SELECT string_agg(kind::text, '+' ORDER BY ordinal)
               FROM (SELECT kind, row_number() OVER (ORDER BY ctid) AS ordinal
                       FROM ledger_transactions
                      WHERE id = ANY(string_to_array('{first}', ',')::uuid[])) s;""",
    )
    if order != "contribution.received+fee.recognised":
        raise Failure(
            f"the entries were posted in the order {order}; BR-021 fixes "
            "contribution.received before fee.recognised"
        )

    # The obligation is discharged and the round's stored aggregates agree.
    status = scalar(
        db,
        f"SELECT c.status::text FROM contributions c WHERE c.round_id = '{MONEY_ROUND}';",
    )
    if status != "paid":
        raise Failure(f"the contribution is {status}, not paid")

    pool = scalar(
        db,
        f"SELECT base_pool_kobo || '/' || fee_collected_kobo FROM rounds "
        f"WHERE id = '{MONEY_ROUND}';",
    )
    if pool != "1000000/20000":
        raise Failure(
            f"the round records pool/fees as {pool}, expected 1000000/20000; these "
            "are stored aggregates and must be restated with the contribution"
        )

    # The fee is a row of its own, pointing at the entry that recognised it.
    link = scalar(
        db,
        """SELECT f.contribution_amount_kobo || '/' || f.fee_kobo || '/'
                  || f.status::text || '/'
                  || (f.ledger_transaction_id = t.id)::text
             FROM fees f JOIN ledger_transactions t ON t.id = f.ledger_transaction_id
            WHERE t.kind = 'fee.recognised';""",
    )
    if link != "1000000/20000/accrued/true":
        raise Failure(
            f"the fee row reads {link}, expected base/fee/status/linked-to-the-fee-"
            "entry; BR-010 says the fee is itemised, never a hidden line"
        )

    # And nothing was created twice.
    before = scalar(db, "SELECT count(*) FROM ledger_transactions;")
    again = _capture(db)
    after = scalar(db, "SELECT count(*) FROM ledger_transactions;")

    if before != after:
        raise Failure(
            f"capturing the same payment again added {after} - {before} entries; a "
            "replayed webhook is normal traffic and must move no money"
        )
    if again != first:
        raise Failure(
            "the replay returned different transaction ids; idempotency has to "
            "return the original, not post again under a second identity"
        )

    return (
        "a confirmed capture posts contribution.received then fee.recognised, each "
        "balanced, the 2% itemised, the contribution paid, the round's aggregates "
        "restated; and replaying it returns the same two entries and adds nothing"
    )


@case("the ledger refuses an entry that does not balance")
def _ledger_writer_refuses(db: str) -> str:
    """
    BR-021's "a one-sided entry is rejected rather than posted", tested through
    the writer rather than through the trigger.

    The deferred constraint trigger already refuses an unbalanced transaction at
    COMMIT, and the `_ledger` case proves it. This proves something the trigger
    cannot: that the writer refuses *before writing*. A one-sided insert that only
    fails at COMMIT leaves rows that exist for the duration of the transaction and
    are rolled back afterwards, so the caller is told about a transaction that no
    longer exists -- and, in a batch that catches the error and carries on, leaves
    the error message pointing at rows a reader cannot find.
    """
    one_sided = (
        """[{"account_kind": "escrow_cash", "side": "debit", "amount_kobo": 100}]"""
    )
    must_fail(
        db,
        "a one-sided entry",
        f"""SELECT app.post_ledger_transaction(
              'contribution.received', '{one_sided}'::jsonb);""",
        expect="at least two postings",
    )

    mismatched = (
        """[{"account_kind": "escrow_cash", "side": "debit", "amount_kobo": 100},
            {"account_kind": "fees_income", "side": "credit", "amount_kobo": 99}]"""
    )
    must_fail(
        db,
        "an entry that is out by one kobo",
        f"""SELECT app.post_ledger_transaction(
              'contribution.received', '{mismatched}'::jsonb);""",
        expect="do not balance",
    )

    # A negative amount is the same mistake wearing a different hat: it is a
    # double negative, and accepting it would let a caller post +100 debit and
    # +100 credit and have the sum check pass on a transaction that moves nothing.
    must_fail(
        db,
        "a negative amount",
        """SELECT app.post_ledger_transaction(
              'contribution.received',
              '[{"account_kind": "escrow_cash", "side": "debit",
                 "amount_kobo": -100},
                {"account_kind": "fees_income", "side": "credit",
                 "amount_kobo": -100}]'::jsonb);""",
        expect="amounts must be positive",
    )

    # Nothing was written by any of the three, which is the property that makes
    # this test worth more than the trigger's. Counted as a delta rather than as
    # zero: this case runs against a database that other cases have committed to,
    # and an absolute count of zero would be an assertion about case ordering
    # dressed up as an assertion about the writer.
    before = scalar(db, "SELECT count(*) FROM ledger_transactions;")
    for label, body in (
        ("a one-sided entry", f"SELECT app.post_ledger_transaction('contribution.received', '{one_sided}'::jsonb);"),
        ("an entry out by one kobo", f"SELECT app.post_ledger_transaction('contribution.received', '{mismatched}'::jsonb);"),
        ("a negative amount", """SELECT app.post_ledger_transaction(
              'contribution.received',
              '[{"account_kind": "escrow_cash", "side": "debit",
                 "amount_kobo": -100},
                {"account_kind": "fees_income", "side": "credit",
                 "amount_kobo": -100}]'::jsonb);"""),
    ):
        must_fail(db, f"{label}, again", body)
    after = scalar(db, "SELECT count(*) FROM ledger_transactions;")

    if before != after:
        raise Failure(
            f"a refused entry left rows behind: {before} entries before, {after} "
            "after; the writer has to validate before it inserts, not leave a "
            "rollback to undo it"
        )

    # Reversals are one level deep (CR-21), and the writer says so by name rather
    # than leaving it to a foreign key that cannot find.
    balanced = (
        """[{"account_kind": "escrow_cash", "side": "credit", "amount_kobo": 500},
            {"account_kind": "contributions_receivable", "side": "debit",
             "amount_kobo": 500}]"""
    )
    # Two failures, not one. A reversal that names nothing, and a reversal that
    # names something that is not there, are different mistakes and the writer
    # distinguishes them -- asserting only the first would have passed against a
    # version that let a dangling reference through to the foreign key.
    must_fail(
        db,
        "a reversal of nothing",
        f"""SELECT app.post_ledger_transaction(
              'reversal', '{balanced}'::jsonb);""",
        expect="must name the transaction it reverses",
    )

    must_fail(
        db,
        "a reversal of a transaction that does not exist",
        f"""SELECT app.post_ledger_transaction(
              'reversal', '{balanced}'::jsonb,
              p_reverses_transaction_id => gen_random_uuid());""",
        expect="which does not exist",
    )

    must_succeed(
        db,
        "a balanced entry",
        """SELECT app.post_ledger_transaction(
              'contribution.received',
              '[{"account_kind": "escrow_cash", "side": "debit",
                 "amount_kobo": 500},
                {"account_kind": "contributions_receivable", "side": "credit",
                 "amount_kobo": 500}]'::jsonb);""",
    )
    # A real reversal has to exist before it can be reversed, and this one has to
    # be committed rather than attempted: the guard reads the referenced row, so
    # a reversal rolled back by a failed attempt is not there to find and the
    # next call fails as "must name the transaction it reverses" instead, which
    # would be the wrong reason and would pass for the wrong reason if the
    # expectation were loose.
    must_succeed(
        db,
        "a reversal",
        f"""SELECT app.post_ledger_transaction(
              'reversal', '{balanced}'::jsonb,
              p_reverses_transaction_id => (
                SELECT id FROM ledger_transactions
                 WHERE kind = 'contribution.received'
                   AND payment_id IS NULL LIMIT 1),
              p_memo => 'correction');""",
    )

    must_fail(
        db,
        "a reversal of a reversal",
        f"""SELECT app.post_ledger_transaction(
              'reversal', '{balanced}'::jsonb,
              p_reverses_transaction_id => (
                SELECT id FROM ledger_transactions
                 WHERE kind = 'reversal' LIMIT 1));""",
        expect="reversing a reversal is not a correction",
    )

    return (
        "a one-sided entry, an entry out by one kobo, a negative amount and a "
        "reversal of nothing are all refused before anything is written; a balanced "
        "entry commits; and a reversal of a reversal is refused by name"
    )


@case("only a provider-confirmed payment is recognised")
def _capture_requires_confirmation(db: str) -> str:
    """
    The line between this system and the provider.

    `payments.status = 'success'` is somebody else's decision. This case is the
    assertion that we never make it ourselves: every status that means "we asked
    and have no answer" is refused, including `unknown`, which is the one most
    likely to be mistaken for a yes.
    """
    _money_ajo(db)
    before = scalar(db, "SELECT count(*) FROM ledger_transactions;")

    for status in ("initiated", "pending", "unknown", "failed", "cancelled"):
        must_succeed(
            db,
            f"a {status} payment to try to capture",
            f"""INSERT INTO payments (
                  contribution_id, channel_id, idempotency_key, provider,
                  contribution_amount_kobo, status
                ) SELECT c.id, ch.id, 'idem-{status}', 'mock', 1000000, '{status}'
                  FROM contributions c, payment_channels ch
                 WHERE c.round_id = '{MONEY_ROUND}' AND ch.code = 'card'
                ON CONFLICT DO NOTHING;""",
        )
        must_fail(
            db,
            f"capturing a {status} payment",
            f"""SELECT app.post_collection_capture(
                  (SELECT id FROM payments WHERE idempotency_key = 'idem-{status}'),
                  (SELECT id FROM users WHERE email = 'money-a@example.ng'));""",
            expect="only a provider-confirmed success is recognised",
        )

    after = scalar(db, "SELECT count(*) FROM ledger_transactions;")
    if before != after:
        raise Failure(
            "recognising an unconfirmed payment left entries behind; the status "
            "check has to happen before the first posting"
        )

    return (
        "initiated, pending, unknown, failed and cancelled payments are all "
        "refused, and unknown is refused specifically because it means we could "
        "not find out rather than that nothing happened"
    )


@case("the API can recognise a capture and cannot post a ledger entry")
def _ledger_write_grants(db: str) -> str:
    """
    Who may write the books.

    `ajo_app` gets `post_collection_capture` and nothing else. The primitive stays
    closed, because a grant on the primitive makes the entry shape a suggestion:
    the first code path that wanted a slightly different entry would invent one,
    and the only guarantee left would be that the numbers added up somewhere.

    The signature is read out of `pg_proc` rather than written out here. Hand-
    written, it is a string that has to be edited by hand the next time an
    argument is added, and when it drifts it drifts to a name that does not exist
    -- and `has_function_privilege` on a non-existent function raises rather than
    returning false, so the test would fail loudly. Loud is survivable. The
    version of this test that was worse is one that named `ajo_api` instead of
    `ajo_app`: `ajo_api` inherits nothing, so every assertion passed and none of
    them described the role that runs the API.
    """
    primitive = scalar(
        db,
        """SELECT p.oid::regprocedure::text
             FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'app' AND p.proname = 'post_ledger_transaction';""",
    )
    if not primitive:
        raise Failure("app.post_ledger_transaction is missing")

    capture = scalar(
        db,
        """SELECT p.oid::regprocedure::text
             FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'app' AND p.proname = 'post_collection_capture';""",
    )
    if not capture:
        raise Failure("app.post_collection_capture is missing")

    for role in ("ajo_app", "ajo_analytics"):
        if scalar(db, f"SELECT has_function_privilege('{role}', '{primitive}', 'EXECUTE');") != "f":
            raise Failure(
                f"{role} can call the ledger primitive; a role that can post "
                "entries directly is a role that can invent revenue"
            )

    # PUBLIC is not a role, so `has_function_privilege('public', ...)` would be a
    # name that does not exist. In the ACL it is the grantee 0.
    for function in (primitive, capture):
        if scalar(
            db,
            f"""SELECT EXISTS (SELECT 1 FROM pg_proc p, aclexplode(p.proacl) x
                     WHERE p.oid::regprocedure::text = '{function}' AND x.grantee = 0);""",
        ) != "f":
            raise Failure(f"{function} is executable by PUBLIC")

    if scalar(db, f"SELECT has_function_privilege('ajo_app', '{capture}', 'EXECUTE');") != "t":
        raise Failure(
            "ajo_app cannot recognise a capture; nothing can move money until it can"
        )

    # Privileges on paper are not privileges in practice, and this is the only
    # assertion that runs as the role the API really assumes. It is also the
    # assertion that would have caught the bootstrap granting the primitive back
    # after migration 105 revoked it.
    _money_ajo(db)
    must_fail(
        db,
        "the API posting a ledger entry directly",
        as_role(
            db,
            "ajo_app",
            "money-a@example.ng",
            f"""SELECT app.post_ledger_transaction(
                  'contribution.received',
                  '[{{"account_kind": "escrow_cash", "side": "debit",
                     "amount_kobo": 100}},
                    {{"account_kind": "contributions_receivable",
                     "side": "credit", "amount_kobo": 100}}]'::jsonb);""",
        ),
        expect="permission denied for function post_ledger_transaction",
    )

    # Committed rather than rolled back, because a rolled-back call proves only
    # that permission was granted, not that the same guarantee holds for the role
    # the request actually arrives on. The payment was already captured earlier in
    # this database, so this is a replay: it has to add nothing. Idempotency that
    # only holds when the caller is the migration role is not idempotency.
    before = scalar(db, "SELECT count(*) FROM ledger_transactions;")
    must_succeed(
        db,
        "the API recognising a capture",
        as_role(
            db,
            "ajo_app",
            "money-a@example.ng",
            """SELECT app.post_collection_capture(
                  (SELECT id FROM payments WHERE idempotency_key = 'idem-money-1'),
                  (SELECT id FROM users WHERE email = 'money-a@example.ng'));""",
            commit=True,
        ),
    )
    after = scalar(db, "SELECT count(*) FROM ledger_transactions;")
    if before != after:
        raise Failure(
            f"a replayed capture from the API role added {after} - {before} entries; "
            "the idempotent path has to hold for the role that serves requests, not "
            "only for the role that owns the function"
        )

    return (
        "the primitive is closed to PUBLIC, to analytics and to the API -- checked "
        "against pg_proc's own signature and then by the API role being refused at "
        "call time -- while the API can recognise a capture, and doing so twice "
        "still leaves one set of books"
    )


@case("a round's fee total cannot drift from the fees booked")
def _round_fee_guard(db: str) -> str:
    """
    `rounds.fee_collected_kobo` had no enforcement at all.

    `assert_round_pool` guards the sibling column `base_pool_kobo`, and nothing
    guarded this one: a stored aggregate that nothing restates and nothing checks.
    The failure is a revenue report that disagrees with the ledger and nobody finds
    out until a human reconciles the accounts by hand.
    """
    _money_ajo(db)
    _capture(db)

    # Changing the contribution without restating the round, in either direction.
    must_fail(
        db,
        "a round whose fee total disagrees with its paid contributions",
        transaction(f"UPDATE rounds SET fee_collected_kobo = 1 WHERE id = '{MONEY_ROUND}';"),
        expect="records 1 kobo of fees collected",
    )

    # And the guard has to fire from the contribution side too, or a restatement
    # that also changed a contribution would be caught by one trigger and not the
    # other, which is not a distinction anyone should have to reason about.
    # Reopening a paid contribution is a real event -- a refund, a correction --
    # so it is not refused as an invalid transition. What must not happen is it
    # being accepted while the round still claims the money. `assert_round_pool`
    # fires first and names the column that is now wrong.
    must_fail(
        db,
        "a contribution reopened without restating the round",
        transaction(
            f"""UPDATE contributions SET status = 'pending'
                 WHERE round_id = '{MONEY_ROUND}';"""
        ),
        expect="base_pool_kobo is a stored aggregate",
    )

    must_succeed(
        db,
        "restating both aggregates together",
        transaction(
            f"""UPDATE rounds r SET
                  base_pool_kobo = (SELECT COALESCE(sum(c.amount_kobo), 0)
                                      FROM contributions c
                                     WHERE c.round_id = r.id AND c.status = 'paid'
                                       AND c.superseded_at IS NULL
                                       AND c.deleted_at IS NULL),
                  fee_collected_kobo = (SELECT COALESCE(sum(c.fee_kobo), 0)
                                          FROM contributions c
                                         WHERE c.round_id = r.id AND c.status = 'paid'
                                           AND c.superseded_at IS NULL
                                           AND c.deleted_at IS NULL)
                WHERE r.id = '{MONEY_ROUND}';"""
        ),
    )

    return (
        "a round that disagrees with its paid contributions is refused from either "
        "side, and restating both aggregates together is accepted"
    )


@case("applying 105 to a database with a stale fee total restates it")
def _fee_aggregate_backfill(db: str) -> str:
    """
    The one risk in migration 105 that the rest of this suite cannot see.

    Every other case runs against a database built from these files, where 105
    creates the guard over an empty ledger and its restatement statement is a
    no-op. The situation that actually matters is the opposite: the adopted
    production database, where a round already exists and already has a wrong
    `fee_collected_kobo`, because `096` created the column as a stored aggregate
    and nothing in the schema was able to write it.

    The guard is a deferred constraint trigger, so it does not evaluate rows
    that already exist. That is what makes 105 safe to apply to that database and
    it is also the trap: apply the guard without restating first and the round
    keeps its wrong number, then the first ordinary write to it fails naming a
    column the writer never touched.

    So this case reproduces the adoption for real: build a database through
    `104`, write a paid contribution, leave the fee total at zero the way `096`
    did, then apply `105` and require that the round comes out correct *and*
    writable. It builds its own database rather than using the shared one,
    because it is the only case that applies migrations at runtime, and it drops
    it again whether it passes or fails.

    It is slow, and it is here anyway.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    scratch = f"{db}_adopt"
    round_id = "01c00000-0000-7000-8000-000000000010"

    try:
        subprocess.run(pg.admin("dropdb", "--if-exists", scratch), check=True)
        subprocess.run(pg.admin("createdb", scratch), check=True)
        applied = subprocess.run(
            [sys.executable, os.path.join(here, "migrate.py"), "--db", scratch,
             "--through", "105"],
            capture_output=True, text=True,
        )
        if applied.returncode != 0:
            raise Failure(
                f"building {scratch} through 104 failed:\n"
                f"    {(applied.stdout + applied.stderr).strip()[:300]}"
            )

        # The shape 096 leaves behind: a round, a paid contribution, the base
        # pool restated because something wrote it, and the fee total never
        # written because nothing could. `paid_at` is set because the existing
        # check constraint requires it, which is itself a small proof that this
        # fixture is using the schema as adopted rather than a simplified one.
        must_succeed(
            scratch,
            "a round with a paid contribution and no fee total",
            "\n".join(
                [
                    "BEGIN;",
                    "INSERT INTO users (auth_subject_id, email, status) "
                    "VALUES ('adopt-1', 'adopt-a@example.ng', 'active');",
                    """INSERT INTO ajos (
                          id, name, organizer_user_id, contribution_amount_kobo,
                          frequency_id, enrollment_opens_at, enrollment_closes_at,
                          total_rounds, currency, status, position_count
                        ) SELECT '01c00000-0000-7000-8000-000000000001',
                          'Adopted group', u.id, 1000000, f.id,
                          now() - interval '1 day', now() + interval '4 days',
                          3, 'NGN', 'draft', 5
                          FROM users u, contribution_frequencies f
                         WHERE u.email = 'adopt-a@example.ng' AND f.code = 'weekly';""",
                    """INSERT INTO ajo_positions (ajo_id, position_number)
                        SELECT a.id, n FROM ajos a, generate_series(1, 5) AS n
                         WHERE a.id = '01c00000-0000-7000-8000-000000000001';""",
                    f"""INSERT INTO rounds (
                          id, ajo_id, round_number, status, due_date, opens_at,
                          closes_at, target_amount_kobo
                        ) SELECT '{round_id}', a.id, 1, 'in_progress', current_date,
                          now(), now() + interval '3 days', 1000000
                          FROM ajos a WHERE a.id = '01c00000-0000-7000-8000-000000000001';""",
                    """INSERT INTO contribution_schedules (
                          round_id, ajo_id, due_date, expected_amount_kobo,
                          expected_member_count, late_cutoff_at
                        ) SELECT r.id, r.ajo_id, r.due_date, 1000000, 5,
                          now() + interval '5 days'
                          FROM rounds r WHERE r.id = '%s';""" % round_id,
                    """INSERT INTO contributions (
                          schedule_id, member_id, position_id, ajo_id, round_id,
                          user_id, amount_kobo, due_date, status, paid_at
                        ) SELECT s.id, m.id, m.position_id, s.ajo_id, s.round_id,
                          m.user_id, 1000000, s.due_date, 'paid', now()
                          FROM contribution_schedules s
                          JOIN ajo_members m ON m.ajo_id = s.ajo_id
                            AND m.user_id = (SELECT id FROM users
                                              WHERE email = 'adopt-a@example.ng')
                         WHERE s.round_id = '%s';""" % round_id,
                    f"UPDATE rounds SET base_pool_kobo = 1000000 WHERE id = '{round_id}';",
                    "COMMIT;",
                ]
            ),
        )

        stale = scalar(
            scratch,
            f"SELECT fee_collected_kobo FROM rounds WHERE id = '{round_id}';",
        )
        if stale != "0":
            raise Failure(
                f"the fixture's fee total is {stale}, not 0; without a stale row "
                "this case proves nothing"
            )

        applied = subprocess.run(
            [sys.executable, os.path.join(here, "migrate.py"), "--db", scratch],
            capture_output=True, text=True,
        )
        if applied.returncode != 0:
            raise Failure(
                f"applying 105 to the adopted database failed:\n"
                f"    {(applied.stdout + applied.stderr).strip()[:300]}"
            )

        restated = scalar(
            scratch,
            f"SELECT base_pool_kobo || '|' || fee_collected_kobo FROM rounds "
            f"WHERE id = '{round_id}';",
        )
        if restated != "1000000|20000":
            raise Failure(
                f"after 105 the round reads {restated}, expected 1000000|20000; the "
                "restatement has to happen on apply, because the guard it precedes "
                "will refuse every future write to a round that is left wrong"
            )

        # Correct is not enough -- it has to be writable, or the guard is holding
        # a round hostage with the right number. The write exercised is the
        # aggregate restatement the guard's own HINT tells callers to perform, so
        # the advice the error message gives is proven to work on the row the
        # error message was written for. Restating to the values already stored
        # is deliberate: the round is already correct, so the only way this can
        # fail is the guard refusing a correct restatement.
        must_succeed(
            scratch,
            "restating the aggregates on the round 105 brought into agreement",
            transaction(
                f"""UPDATE rounds r SET
                      base_pool_kobo = (SELECT COALESCE(sum(c.amount_kobo), 0)
                                          FROM contributions c
                                         WHERE c.round_id = r.id AND c.status = 'paid'
                                           AND c.superseded_at IS NULL
                                           AND c.deleted_at IS NULL),
                      fee_collected_kobo = (SELECT COALESCE(sum(c.fee_kobo), 0)
                                              FROM contributions c
                                             WHERE c.round_id = r.id AND c.status = 'paid'
                                               AND c.superseded_at IS NULL
                                               AND c.deleted_at IS NULL)
                    WHERE r.id = '{round_id}';"""
            ),
        )

        return (
            "a database built through 104 with a round whose fee total was never "
            "written comes out of 105 correct at 2% and accepting writes, which is "
            "the adoption case the live database is in"
        )
    finally:
        subprocess.run(pg.admin("dropdb", "--if-exists", scratch), check=False,
                       capture_output=True)


# ---------------------------------------------------------------------------
# Provider event intake (spec 13.5).
# ---------------------------------------------------------------------------

@case("a redelivered provider event is stored once and is not a second event")
def _provider_event_dedupe(db: str) -> str:
    """
    Spec 13.5: "`provider_event_id` is uniquely indexed. A duplicate delivery is
    acknowledged and dropped, not reprocessed."

    The word doing the work is "delivery". Providers redeliver constantly -- a
    timeout on our side, a retry, an at-least-once queue between us. A
    redelivery is ordinary traffic, so it is neither an error nor a second
    event, and the return value has to say which one it is without the caller
    having to diff the table.
    """
    event = (
        "SELECT (e.event_id::text || '|' || e.is_new::text) AS joined "
        "FROM app.ingest_provider_event("
        "'mock', 'evt-dedupe-1', 'transfer.success', now(), "
        "'{\"reference\":\"MOCK-000001\"}'::jsonb) e;"
    )

    first = scalar(db, event)
    if "true" not in first:
        raise Failure(
            f"the first delivery returned {first!r}; the first sighting of an event "
            "is new, and a caller that thinks otherwise drops real money on the floor"
        )

    second = scalar(db, event)
    if "true" in second:
        raise Failure(
            "a redelivery was reported as new; the caller would then drive a second "
            "capture for one transfer"
        )

    # Same id both times: not merely "not new", but the same row, so the caller
    # can go and look at what happened to it.
    if first.split("|")[0] != second.split("|")[0]:
        raise Failure(
            f"the redelivery returned a different event id: {first} then {second}"
        )

    if scalar(db, "SELECT count(*) FROM webhook_events;") != "1":
        raise Failure("a redelivery created a second row")

    return (
        "the same provider event delivered twice yields one row and one id, the "
        "second reported as not new, which is what stops one transfer driving two "
        "captures"
    )


@case("a provider event older than the replay window is refused")
def _provider_event_replay_window(db: str) -> str:
    """
    Spec 13.5: "Reject any event whose timestamp is more than 5 minutes old."

    A signature does not expire. An attacker who captures one valid webhook can
    present it for as long as the key lives, and the only thing that stops a
    captured success being replayed forever is refusing it once it is old.

    The boundary is tested from both sides, because "more than five minutes" is
    easy to implement as "at least five minutes" and that rejects deliveries the
    specification allows.
    """
    must_succeed(
        db,
        "an event four minutes old",
        """SELECT app.ingest_provider_event(
              'mock', 'evt-replay-ok', 'transfer.success', now() - interval '4 minutes',
              '{"reference":"MOCK-000002"}'::jsonb);""",
    )

    must_succeed(
        db,
        "an event one second inside the window",
        """SELECT app.ingest_provider_event(
              'mock', 'evt-replay-edge', 'transfer.success', now() - interval '299 seconds',
              '{"reference":"MOCK-000002"}'::jsonb);""",
    )

    must_fail(
        db,
        "an event six minutes old",
        """SELECT app.ingest_provider_event(
              'mock', 'evt-replay-stale', 'transfer.success', now() - interval '6 minutes',
              '{"reference":"MOCK-000002"}'::jsonb);""",
        expect="past the five-minute replay window",
    )

    # Refused at the door, so nothing was stored -- a replay that is rejected
    # after being written is a replay that briefly existed.
    if scalar(db, "SELECT count(*) FROM webhook_events WHERE provider_event_id = 'evt-replay-stale';") != "0":
        raise Failure("a stale replay was stored before being refused")

    # A missing timestamp is not an escape hatch. If it is NULL the freshness
    # comparison is NULL, the test above would silently pass, and an event with no
    # timestamp would be accepted forever.
    must_fail(
        db,
        "an event with no timestamp",
        """SELECT app.ingest_provider_event(
              'mock', 'evt-replay-notime', 'transfer.success', NULL,
              '{"reference":"MOCK-000002"}'::jsonb);""",
        expect="must carry the time it occurred",
    )

    return (
        "an event four minutes old and one at 299 seconds are accepted, one at six "
        "minutes is refused and stored nowhere, and an event with no timestamp is "
        "refused rather than treated as fresh forever"
    )


@case("only a signature-verified provider event may be acted on")
def _provider_event_verification_gate(db: str) -> str:
    """
    Spec 13.5 requires parsing only after verification, and treating the webhook
    as hostile input. Nothing that moves money may read an event whose signature
    has not been checked.

    The design point is that verification is a separate call rather than a
    boolean argument. `ingest_provider_event` has no parameter that can set the
    flag, so an event cannot arrive already trusted -- the honest state is the
    only reachable one, and becoming trusted is an auditable act.
    """
    event_id = scalar(
        db,
        """SELECT (e.event_id::text) AS joined
             FROM app.ingest_provider_event(
               'mock', 'evt-verify-1', 'transfer.success', now(),
               '{"reference":"MOCK-000003"}'::jsonb) e;""",
    )

    if scalar(
        db, f"SELECT signature_verified::text FROM webhook_events WHERE id = '{event_id}';"
    ) != "false":
        raise Failure(
            "an ingested event is not unverified; the stored state has to be the "
            "honest one, or a caller could pass a boolean and be believed"
        )

    # Acting on it is refused, by name.
    must_fail(
        db,
        "acting on an unverified event",
        f"SELECT app.assert_provider_event_verified('{event_id}');",
        expect="has an unverified signature",
    )

    # And the other way: verification cannot be recorded without saying how, or
    # without the values settlement matches on. Each argument is checked
    # separately, because a function that only checks its first argument accepts
    # a verification it cannot act on.
    must_fail(
        db,
        "verifying without naming an algorithm",
        f"SELECT app.mark_provider_event_verified('{event_id}', NULL, 'ref-1', 100, 'NGN', 'success');",
        expect="must record which algorithm verified it",
    )

    must_fail(
        db,
        "verifying without the reference it names",
        f"SELECT app.mark_provider_event_verified('{event_id}', 'HMAC-SHA256', NULL, 100, 'NGN', 'success');",
        expect="must record the provider reference",
    )

    must_fail(
        db,
        "verifying without the amount reported",
        f"SELECT app.mark_provider_event_verified('{event_id}', 'HMAC-SHA256', 'ref-1', NULL, 'NGN', 'success');",
        expect="must record the amount",
    )

    must_fail(
        db,
        "verifying without the state reported",
        f"SELECT app.mark_provider_event_verified('{event_id}', 'HMAC-SHA256', 'ref-1', 100, 'NGN', NULL);",
        expect="must record the state",
    )

    must_succeed(
        db,
        "verifying with the algorithm that did it",
        f"SELECT app.mark_provider_event_verified('{event_id}', 'HMAC-SHA256', 'ref-1', 100, 'NGN', 'success');",
    )

    if scalar(
        db, f"SELECT signature_verified::text FROM webhook_events WHERE id = '{event_id}';"
    ) != "true":
        raise Failure("the event was not marked verified")

    must_succeed(
        db,
        "acting on a verified event",
        f"SELECT app.assert_provider_event_verified('{event_id}');",
    )

    # Redelivery is verified again rather than refused. A provider sending the
    # same good webhook twice must not look like an attack.
    must_succeed(
        db,
        "verifying an already-verified event",
        f"SELECT app.mark_provider_event_verified('{event_id}', 'HMAC-SHA256', 'ref-1', 100, 'NGN', 'success');",
    )

    # And an event the database has never heard of is not a verification.
    must_fail(
        db,
        "acting on an event that does not exist",
        "SELECT app.assert_provider_event_verified(gen_random_uuid());",
        expect="no provider event with id",
    )

    return (
        "an ingested event is unverified and cannot be acted on, verification is "
        "refused without an algorithm and is idempotent, a verified event passes the "
        "gate, and an unknown event id is not a pass"
    )


@case("an event type we do not implement is ignored, not refused")
def _provider_event_unknown_type(db: str) -> str:
    """
    Spec 13.5: "Unknown event types: Acknowledged, logged, and ignored -- never a
    4xx, and never a crash."

    The failure this prevents is a specific and embarrassing one: the provider
    adds an event type, starts sending it, our handler 4xx's or throws, and the
    provider retries the unhandleable event indefinitely -- turning a routine
    provider-side addition into an outage on our side.
    """
    event_id = scalar(
        db,
        """SELECT (e.event_id::text) AS joined
             FROM app.ingest_provider_event(
               'mock', 'evt-unknown-type', 'merchant.dispute.opened', now(),
               '{"reference":"MOCK-000004","reason":"fraud_review"}'::jsonb) e;""",
    )

    # Accepted on arrival, whatever it says. Ingest never inspects the type.
    must_succeed(
        db,
        "verifying an event type we do not implement",
        f"SELECT app.mark_provider_event_verified('{event_id}', 'HMAC-SHA256', 'MOCK-000004', 200000, 'NGN', 'unknown');",
    )

    must_succeed(
        db,
        "ignoring it with the reason recorded",
        f"""SELECT app.ignore_provider_event(
              '{event_id}', 'event type merchant.dispute.opened is not implemented');""",
    )

    # Parenthesised: `||` binds tighter than `<>`, so without them this compares
    # the concatenated string to '' and returns a bare boolean instead of the two
    # values being asserted on.
    outcome = scalar(
        db,
        f"SELECT status::text || '|' || (processed_at IS NOT NULL)::text "
        f"FROM webhook_events WHERE id = '{event_id}';",
    )
    if not outcome.startswith("ignored|true"):
        raise Failure(
            f"the ignored event reads {outcome}; an unexplained gap in a provider's "
            "events is undiagnosable six months later unless the ignore is recorded"
        )

    # Ignored is terminal for acting on it.
    must_fail(
        db,
        "acting on an event that was ignored",
        f"SELECT app.assert_provider_event_verified('{event_id}');",
        expect="cannot be acted on again",
    )

    return (
        "an unimplemented event type is accepted, verified, ignored with its reason "
        "and timestamp recorded, and refused for further action -- so a provider "
        "adding an event type cannot turn into a retry storm against us"
    )


@case("a settled payment is never unsettled by a later message")
def _terminal_state_resolution(db: str) -> str:
    """
    Spec 13.5: "Out-of-order delivery: A success arriving after a failure for the
    same reference is resolved by the terminal state, not by arrival order."

    Providers do not deliver in order. A `pending` and a `success` can arrive
    minutes apart in either order, and a webhook for a transfer that already
    settled can arrive after we have written ledger entries against it.

    The invariant is that a terminal payment state is never left. The member has
    been told something and the ledger has been written; a later message that
    disagrees cannot take that back.
    """
    checks = {
        # A settled transfer stays settled, whatever turns up afterwards.
        ("success", "pending"): "success",
        ("success", "unknown"): "success",
        ("success", "failed"): "success",
        ("failed", "success"): "failed",
        ("failed", "pending"): "failed",
        ("reversed", "success"): "reversed",
        ("cancelled", "success"): "cancelled",
        # An unsettled transfer is settled by a terminal arrival.
        ("pending", "success"): "success",
        ("initiated", "failed"): "failed",
        ("initiated", "success"): "success",
        # And two unsettled states progress normally, or nothing ever settles.
        ("initiated", "pending"): "pending",
        ("initiated", "unknown"): "initiated",
        ("pending", "unknown"): "pending",
        ("unknown", "success"): "success",
    }

    for (current, incoming), expected in checks.items():
        actual = scalar(
            db,
            "SELECT app.resolve_transfer_state("
            f"'{current}'::public.payment_status, '{incoming}'::public.payment_status)::text;",
        )
        if actual != expected:
            raise Failure(
                f"current {current} then {incoming} resolved to {actual}, expected "
                f"{expected}"
            )

    # The case that matters most in production: a transfer that has already been
    # captured cannot be walked back by a late webhook. This is asserted through
    # the whole path rather than the pure function alone, because the function
    # being right does not stop a caller asking the wrong question.
    _money_ajo(db)

    # Success, not failure. The contribution is already captured, so a second
    # call is a replay and idempotency means it returns the original entries. The
    # version of this case that asserted a failure here was asserting the wrong
    # thing: it would have passed if idempotency had been removed *and* if the
    # guard had rejected replays, which are opposite behaviours.
    # Success, not failure. The contribution is already captured, so a second
    # call is a replay and idempotency means it returns the original entries. The
    # version of this case that asserted a failure here was asserting the wrong
    # thing: it would have passed if idempotency had been removed *and* if the
    # guard had rejected replays, which are opposite behaviours.
    #
    # Compared against the ids the first capture returned rather than against a
    # count. Every case shares one database, so a global `count(*)` is a moving
    # target -- this case is about its own two entries, not about the table.
    first = _capture(db)

    before = int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;"))
    postings_before = int(scalar(db, "SELECT count(*)::text FROM ledger_postings;"))

    replayed = scalar(
        db,
        """SELECT array_to_string(
                  app.post_collection_capture(
                    (SELECT id FROM payments WHERE idempotency_key = 'idem-money-1'),
                    (SELECT id FROM users WHERE email = 'money-a@example.ng')),
                  ',') AS joined;""",
    )

    if replayed != first:
        raise Failure(
            f"replaying the capture returned {replayed} but the original returned "
            f"{first}; a settled contribution has to be answered by returning the "
            "entries already written for it"
        )

    # Nothing was written. Measured either side of the replay, so the cases that
    # share this database cannot move the number out from under the comparison.
    if int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;")) != before:
        raise Failure(
            "the ledger gained an entry when a settled contribution was replayed"
        )
    if int(scalar(db, "SELECT count(*)::text FROM ledger_postings;")) != postings_before:
        raise Failure(
            "the ledger postings gained entries when a settled contribution was "
            "replayed"
        )

    # And the contribution is still settled, not walked back to pending.
    if scalar(db, f"SELECT status::text FROM contributions WHERE round_id = '{MONEY_ROUND}';") != "paid":
        raise Failure(
            "a later message moved a settled contribution off paid; the ledger "
            "would then disagree with the contribution it was written for"
        )

    return (
        "every combination of settled and unsettled resolves to the terminal state "
        "in whichever order it arrived, unknown never overwrites a known state, and "
        "a settled contribution cannot be walked back"
    )


@case("provider event intake is reachable by the app and nobody else")
def _provider_event_grants(db: str) -> str:
    """
    Migration 105 taught this the hard way: a blanket grant in the role bootstrap
    silently reopened a primitive that the migration had closed, so the money path
    was callable by the application role and nobody noticed until the test read the
    grants back out of the catalogue.

    The grants are therefore asserted rather than assumed. And they are asserted
    with `has_function_privilege` rather than by calling the functions and watching
    them fail: this suite connects as the postgres superuser, and a superuser can
    execute any function regardless of its grants. A `must_fail` on a function the
    superuser is calling proves nothing at all -- the first version of this case
    did exactly that and passed a PUBLIC-exposed resolver on its way to the next
    assertion.
    """
    functions = (
        ("app.ingest_provider_event", "text, text, text, timestamptz, jsonb, timestamptz"),
        ("app.mark_provider_event_verified", "uuid, text, text, bigint, text, public.payment_status"),
        ("app.claim_provider_event", "integer, integer"),
        ("app.settle_provider_event", "uuid"),
        ("app.defer_provider_event", "uuid, text"),
        ("app.ignore_provider_event", "uuid, text"),
        ("app.assert_provider_event_verified", "uuid"),
        ("app.resolve_transfer_state", "public.payment_status, public.payment_status"),
    )

    # `ajo_api` is in the matrix as *allowed*, and that is not an oversight:
    # bootstrap_roles.sql makes it a member of `ajo_app`, so it inherits every
    # app privilege by design and is the role the HTTP server connects as. The
    # first version of this case asserted it could not call these functions, which
    # would have meant either dropping the webhook handler's role or removing the
    # inheritance the login path depends on.
    for fn, args in functions:
        for role, expected in (
            ("public", False),
            ("ajo_analytics", False),
            ("ajo_app", True),
            ("ajo_api", True),
        ):
            actual = scalar(
                db,
                f"""SELECT has_function_privilege(
                          '{role}', '{fn}({args})', 'EXECUTE');""",
            ).strip()
            if actual != ("t" if expected else "f"):
                allowed = "can" if actual == "t" else "cannot"
                should = "must be able to" if expected else "must not be able to"
                raise Failure(
                    f"{role} {allowed} call {fn}, but {role} {should} call it. "
                    "PUBLIC includes every role nobody has written down yet, so an "
                    "open function is open to roles that do not exist yet."
                )

    # The one place a bare `public` check is not enough: EXECUTE on a function is
    # granted to PUBLIC automatically when the function is created, so "the
    # migration did not mention PUBLIC" is not the same claim as "PUBLIC cannot
    # call it". The catalogue says this one is closed, which is the claim worth
    # making.
    if scalar(
        db,
        """SELECT has_function_privilege(
                  'public', 'app.resolve_transfer_state(public.payment_status, public.payment_status)',
                  'EXECUTE');""",
    ).strip() != "f":
        raise Failure(
            "PUBLIC can resolve a transfer state; bootstrap_roles.sql revokes it "
            "again on the next run, so who can reach it would depend on when roles "
            "were last bootstrapped"
        )

    # The migrator owns the table and has to reach every row regardless of the
    # impersonated user, because a webhook has no member behind it. Without the
    # policies the intake function fails as soon as the row is written, and that
    # failure looks like a webhook bug rather than a grant one.
    policies = int(
        scalar(
            db,
            # `pg_policies`, not an information_schema view -- there is no
            # `information_schema.row_security_policies` at all, so asking for one
            # raises rather than answering.
            "SELECT count(*)::text FROM pg_policies "
            "WHERE tablename = 'webhook_events';",
        )
    )
    if policies == 0:
        raise Failure(
            "webhook_events has no row policies; the migrator cannot reach the rows "
            "it is inserting"
        )

    return (
        "the application role and the API role that inherits it can call every one "
        "of these intake and settlement functions, PUBLIC and the analytics role "
        "can call none of them, the "
        "transfer-state resolver is closed to PUBLIC despite EXECUTE being granted "
        "there automatically at creation, and webhook_events carries the migrator "
        "policies the intake depends on"
    )


def _settle_ajo(group: int) -> str:
    """One Ajo per settlement case, and with it one round and one contribution.

    A shared Ajo does not work. `rounds_one_in_progress_per_ajo` is a unique index
    on (ajo_id) where status = 'in_progress', so a second round on the same Ajo is
    rejected -- and `ON CONFLICT DO NOTHING` reports success while inserting
    nothing, which left four cases matching no payment at all and deferring.
    """
    return f"01b00000-0000-7000-8000-{group + 19:012d}"


def _settle_round(group: int) -> str:
    return f"01b00000-0000-7000-8000-{group:012d}"


SETTLE_AJO = _settle_ajo(1)
SETTLE_ROUND = _settle_round(1)


def _pending_money_ajo(db: str, reference: str = "settle-ref-1", group: int = 1) -> str:
    """
    One member, one Ajo, one round, one contribution, and a payment that is
    `pending` with a provider reference.

    Separate from `_money_ajo` rather than a variation of it. That fixture's
    payment is already `success`, and a second payment on the same contribution
    would let a capture post a second `contribution.received` for one
    contribution -- the round aggregates are derived from paid contributions, not
    from payments, so the totals would double while the ledger looked internally
    consistent. Two independent fixtures keep "this capture belongs to that
    contribution" checkable.
    """
    ajo_id = _settle_ajo(group)
    round_id = _settle_round(group)
    # One member per group. The settlement cases commit real captures, and a capture
    # queues notifications for the member; a single shared member let those pile up
    # under a case of their own that counts what a drain owes one member.
    member = f"settle-{group}@example.ng"
    must_succeed(
        db,
        f"a pending payment on group {group} awaiting a webhook",
        "\n".join(
            [
                "BEGIN;",
                f"INSERT INTO users (auth_subject_id, email, status) "
                f"VALUES ('settle-{group}', '{member}', 'active') "
                "ON CONFLICT DO NOTHING;",
                f"""INSERT INTO ajos (
                      id, name, organizer_user_id, contribution_amount_kobo,
                      frequency_id, enrollment_opens_at, enrollment_closes_at,
                      total_rounds, currency, status, position_count
                    ) SELECT '{ajo_id}', 'Settlement group {group}', u.id, 1000000,
                      f.id, now() - interval '1 day', now() + interval '4 days',
                      12, 'NGN', 'draft', 5
                      FROM users u, contribution_frequencies f
                     WHERE u.email = '{member}' AND f.code = 'weekly'
                    ON CONFLICT DO NOTHING;""",
                f"""INSERT INTO ajo_positions (ajo_id, position_number)
                    SELECT a.id, n FROM ajos a, generate_series(1, 5) AS n
                     WHERE a.id = '{ajo_id}'
                    ON CONFLICT DO NOTHING;""",
                f"""INSERT INTO rounds (
                      id, ajo_id, round_number, status, due_date, opens_at,
                      closes_at, target_amount_kobo
                    ) SELECT '{round_id}', a.id, 1, 'in_progress', current_date,
                      now(), now() + interval '3 days', 1000000
                      FROM ajos a WHERE a.id = '{ajo_id}'
                    ON CONFLICT DO NOTHING;""",
                f"""INSERT INTO contribution_schedules (
                      round_id, ajo_id, due_date, expected_amount_kobo,
                      expected_member_count, late_cutoff_at
                    ) SELECT r.id, r.ajo_id, r.due_date, 1000000, 5,
                      now() + interval '5 days'
                      FROM rounds r WHERE r.id = '{round_id}'
                    ON CONFLICT DO NOTHING;""",
                f"""INSERT INTO contributions (
                      schedule_id, member_id, position_id, ajo_id, round_id,
                      user_id, amount_kobo, due_date
                    ) SELECT s.id, m.id, m.position_id, s.ajo_id, s.round_id,
                      m.user_id, 1000000, s.due_date
                      FROM contribution_schedules s
                      JOIN ajo_members m ON m.ajo_id = s.ajo_id
                        AND m.user_id = (SELECT id FROM users
                                          WHERE email = '{member}')
                     WHERE s.round_id = '{round_id}'
                    ON CONFLICT DO NOTHING;""",
                # `charged_amount_kobo` and `fee_kobo` are generated from the
                # contribution amount, so the amount the provider must confirm is
                # 1020000 and not 1000000. Writing either column here is an error
                # by design: the fee is derived, never supplied.
                #
                # The idempotency key is derived from the reference rather than
                # hard-coded. It was 'idem-settle-1' at first, and since that
                # column is unique a second call inserted nothing and reported
                # success -- so later cases went on asserting against a payment
                # that had never been created.
                f"""INSERT INTO payments (
                      contribution_id, channel_id, idempotency_key, provider,
                      provider_reference, contribution_amount_kobo, status
                    ) SELECT c.id, ch.id, 'idem-' || '{reference}', 'mock', '{reference}',
                      1000000, 'pending'
                      FROM contributions c, payment_channels ch
                     WHERE c.round_id = '{round_id}' AND ch.code = 'bank_transfer'
                    ON CONFLICT DO NOTHING;""",
                "COMMIT;",
            ]
        ),
    )
    return reference


# `app.claim_provider_event()` hands out a batch, oldest first, and its default is
# ten. A case that artificially expires a lease leaves the row it is about with a
# `next_retry_at` in the past, which sorts *after* every never-attempted event,
# whose NULL retry sorts first. On the one database the whole suite shares, rows
# committed by earlier cases can therefore fill the batch and leave the row a case
# cares about unclaimed. That is the flake that made
# `_settlement_that_raises_is_bounded` fail on some orderings and pass on others.
# A batch larger than any case creates makes the helper deterministic without
# touching the production ordering, which is deliberate.
_CLAIM_EVERYTHING = 100000


def _verified_event(
    db: str,
    reference: str,
    state: str = "success",
    amount: int = 1020000,
    currency: str = "NGN",
    event_id: str = "evt-settle-1",
    provider: str = "mock",
) -> str:
    """Ingest, verify and claim one provider event, returning its row id."""
    row_id = scalar(
        db,
        f"""SELECT (e.event_id::text) AS joined
              FROM app.ingest_provider_event(
                '{provider}', '{event_id}', 'transfer.{state}', now(),
                '{{"reference":"{reference}"}}'::jsonb) e;""",
    )
    must_succeed(
        db,
        f"verifying {event_id}",
        f"""SELECT app.mark_provider_event_verified(
              '{row_id}', 'HMAC-SHA256', '{reference}', {amount}, '{currency}',
              '{state}'::public.payment_status);""",
    )
    if scalar(
        db,
        f"SELECT count(*)::text FROM app.claim_provider_event({_CLAIM_EVERYTHING}) "
        f"WHERE id = '{row_id}';",
    ) != "1":
        raise Failure(
            f"{event_id} was not handed out by the claim, so the case cannot start "
            "from a claimed event; either it is not claimable or another case's rows "
            "filled an apparatus sized too small"
        )
    return row_id


@case("a verified, amount-matched webhook settles a pending payment")
def _settlement_captures(db: str) -> str:
    """
    The whole point of 107, end to end in one path: an event arrives unverified,
    its signature is checked by something that has the provider's secret, the
    values are recorded, a worker claims it, and the money moves.

    Asserted through the real functions rather than by writing the rows, because
    the claim being worth anything is exactly the claim that this path is the only
    way to reach the ledger from a webhook.
    """
    _pending_money_ajo(db)

    before = int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;"))
    event_id = _verified_event(db, "settle-ref-1")

    outcome = scalar(db, f"SELECT app.settle_provider_event('{event_id}');")
    if outcome != "captured":
        raise Failure(f"settling a verified, matched success returned {outcome!r}")

    # The payment is settled and linked to the event that settled it. The unique
    # index on `webhook_event_id` is what stops one event settling two payments.
    payment = scalar(
        db,
        f"""SELECT status::text || '|' || (webhook_event_id = '{event_id}')::text
              FROM payments WHERE provider_reference = 'settle-ref-1';""",
    )
    if payment != "success|true":
        raise Failure(f"the payment reads {payment}; expected success linked to the event")

    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{event_id}';") != "processed":
        raise Failure("the event was not marked processed after settling")

    # And the ledger moved by exactly the two entries a capture makes.
    added = int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;")) - before
    if added != 2:
        raise Failure(f"settling one capture added {added} ledger entries, expected 2")

    if scalar(db, f"SELECT status::text FROM contributions WHERE round_id = '{SETTLE_ROUND}';") != "paid":
        raise Failure("the contribution is not paid after a verified, matched success")

    # The event's own time is what gets stamped, not our arrival time: the column
    # 106 validated and threw away, and 107 exists partly to keep it.
    if scalar(
        db,
        f"SELECT (provider_completed_at IS NOT NULL)::text FROM payments "
        f"WHERE provider_reference = 'settle-ref-1';",
    ) != "true":
        raise Failure("the payment has no provider completion time")

    return (
        "a verified, amount-matched success claimed by a worker settles the pending "
        "payment, links the payment to the event, posts exactly the two ledger "
        "entries and marks the contribution paid"
    )


@case("a webhook that reports the wrong amount is escalated, never posted")
def _settlement_amount_must_match(db: str) -> str:
    """
    Spec §13.5: "The received amount, currency, and reference must match the
    pending contribution. A mismatch is escalated to reconciliation, not silently
    accepted."

    The number that matters is `charged_amount_kobo` -- contribution plus the 2%
    fee, 1020000 here -- not the contribution's own 1000000. Matching against the
    contribution alone would reject every correct webhook in the system.
    """
    _pending_money_ajo(db)

    before = int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;"))
    _pending_money_ajo(db, reference="settle-ref-amount", group=2)
    event_id = _verified_event(
        db, "settle-ref-amount", amount=1000000, event_id="evt-amount-wrong"
    )

    outcome = scalar(db, f"SELECT app.settle_provider_event('{event_id}');")
    if "amount mismatch" not in outcome:
        raise Failure(
            f"a webhook reporting 1000000 against a charge of 1020000 returned "
            f"{outcome!r} instead of escalating"
        )

    if int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;")) != before:
        raise Failure("a mismatched amount posted to the ledger")

    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{event_id}';") != "failed":
        raise Failure("a mismatched amount was not left in failed for reconciliation")

    # The escalation has to carry both figures, or reconciliation cannot act on it.
    detail = scalar(db, f"SELECT error_detail FROM webhook_events WHERE id = '{event_id}';")
    if "1000000" not in detail or "1020000" not in detail:
        raise Failure(f"the escalation does not carry both amounts: {detail!r}")

    # And the payment is untouched: still pending, still unpaid.
    if scalar(
        db, "SELECT status::text FROM payments WHERE provider_reference = 'settle-ref-amount';"
    ) != "pending":
        raise Failure("a mismatched webhook changed the payment's status")

    return (
        "a webhook reporting the contribution amount where the charge was the "
        "contribution plus fee is escalated with both figures on the row, posts "
        "nothing, and leaves the payment pending"
    )


@case("a currency the Ajo does not collect is escalated")
def _settlement_currency_must_match(db: str) -> str:
    """The second half of the same rule, and the half a Nigerian-only schema is
    most likely to skip because every row currently says NGN."""
    _pending_money_ajo(db)

    before = int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;"))
    _pending_money_ajo(db, reference="settle-ref-currency", group=3)
    event_id = _verified_event(
        db, "settle-ref-currency", currency="USD", event_id="evt-currency-wrong"
    )

    outcome = scalar(db, f"SELECT app.settle_provider_event('{event_id}');")
    if "currency mismatch" not in outcome:
        raise Failure(f"a webhook in USD returned {outcome!r} instead of escalating")

    if int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;")) != before:
        raise Failure("a webhook in the wrong currency posted to the ledger")

    if "USD" not in scalar(db, f"SELECT error_detail FROM webhook_events WHERE id = '{event_id}';"):
        raise Failure("the currency escalation does not name the currency reported")

    return (
        "a webhook reporting a currency the Ajo does not collect is escalated with "
        "both currencies named and posts nothing"
    )


@case("a webhook cannot settle before a worker has claimed it")
def _settlement_requires_the_claim(db: str) -> str:
    """
    The lease is the only thing stopping two API instances settling one event, so
    it has to be load-bearing: settling an event that nobody has claimed must be
    refused, not quietly allowed.

    Without this the claim is decoration -- a worker could call settle directly and
    the `FOR UPDATE SKIP LOCKED` in the claim would protect nothing.
    """
    _pending_money_ajo(db)

    row_id = scalar(
        db,
        """SELECT (e.event_id::text) AS joined
             FROM app.ingest_provider_event(
               'mock', 'evt-unclaimed', 'transfer.success', now(),
               '{"reference":"settle-ref-1"}'::jsonb) e;""",
    )
    must_succeed(
        db,
        "verifying an unclaimed event",
        f"""SELECT app.mark_provider_event_verified(
              '{row_id}', 'HMAC-SHA256', 'settle-ref-1', 1020000, 'NGN', 'success');""",
    )

    must_fail(
        db,
        "settling an event nobody claimed",
        f"SELECT app.settle_provider_event('{row_id}');",
        expect="is not claimed for processing",
    )

    # An unverified event is never claimable in the first place, so it never
    # reaches settle either.
    unverified = scalar(
        db,
        """SELECT (e.event_id::text) AS joined
             FROM app.ingest_provider_event(
               'mock', 'evt-unverified', 'transfer.success', now(),
               '{"reference":"settle-ref-1"}'::jsonb) e;""",
    )
    must_succeed(
        db,
        "claiming nothing while an unverified event waits",
        "SELECT count(*) FROM app.claim_provider_event() WHERE signature_verified;",
    )
    must_fail(
        db,
        "settling an unverified event",
        f"SELECT app.settle_provider_event('{unverified}');",
        expect="unverified signature",
    )

    return (
        "a verified but unclaimed event cannot be settled, and an unverified event "
        "is never handed out by the claim at all -- so the lease, not convention, is "
        "what serialises settlement"
    )


@case("a webhook for a reference we do not have waits instead of failing")
def _settlement_waits_for_the_payment(db: str) -> str:
    """
    The provider can confirm a transfer faster than we finish writing the pending
    payment that names it. Treating that race as a permanent failure drops a real
    payment on the floor, so the event goes back on the queue with a backoff.

    Bounded, though: unbounded retry on a reference that will never appear turns
    one bad webhook into a permanent row somebody has to notice and clear.
    """
    _pending_money_ajo(db)

    event_id = _verified_event(db, "settle-ref-never-arrives", event_id="evt-never-arrives")

    outcome = scalar(db, f"SELECT app.settle_provider_event('{event_id}');")
    if "no matching payment" not in outcome:
        raise Failure(f"an unmatched reference returned {outcome!r}")

    status = scalar(
        db,
        f"""SELECT status::text || '|' || (next_retry_at > now())::text || '|'
                  || (error_detail LIKE '%settle-ref-never-arrives%')::text
              FROM webhook_events WHERE id = '{event_id}';""",
    )
    if status != "received|true|true":
        raise Failure(
            f"an unmatched event reads {status}; it should go back on the queue "
            "with a backoff and the missing reference named"
        )

    # Backed off, so the claim does not hand it straight back out.
    must_succeed(
        db,
        "claiming after a deferral",
        f"SELECT count(*) FROM app.claim_provider_event() WHERE id = '{event_id}';",
    )
    if scalar(
        db, f"SELECT status::text FROM webhook_events WHERE id = '{event_id}';"
    ) != "received":
        raise Failure("a deferred event was claimed again before its retry was due")

    # Bounded in attempts as well as in time.
    must_succeed(
        db,
        "giving up after too many attempts",
        transaction(
            f"""UPDATE webhook_events SET attempts = 8 WHERE id = '{event_id}';
                SELECT app.defer_provider_event('{event_id}', 'still nothing');"""
        ).replace("ROLLBACK;", "COMMIT;"),
    )
    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{event_id}';") != "failed":
        raise Failure("an event retried eight times did not give up")

    return (
        "a reference with no matching payment goes back on the queue with an "
        "exponential backoff and is not handed out again until it is due, and gives "
        "up after eight attempts rather than retrying forever"
    )


@case("one provider's reference cannot settle another provider's payment")
def _settlement_is_scoped_to_the_provider(db: str) -> str:
    """
    Two providers can legitimately hand out the same reference. Matching on the
    reference alone would let one provider's webhook settle a payment another
    provider was asked to collect -- which is the failure mode that makes a
    multi-provider system unsafe rather than merely redundant.
    """
    _pending_money_ajo(db, reference="settle-ref-scope", group=4)

    # A second provider's payment, same reference, different contribution.
    must_succeed(
        db,
        "a second provider holding the same reference",
        """INSERT INTO payments (
             contribution_id, channel_id, idempotency_key, provider,
             provider_reference, contribution_amount_kobo, status
           )
           SELECT c.id, ch.id, 'idem-settle-other', 'other_provider', 'settle-ref-scope',
             500000, 'pending'
             FROM contributions c, payment_channels ch
            WHERE c.round_id = (SELECT c2.round_id FROM payments p
                                   JOIN contributions c2 ON c2.id = p.contribution_id
                                  WHERE p.provider = 'mock'
                                    AND p.provider_reference = 'settle-ref-scope')
              AND ch.code = 'bank_transfer';""",
    )

    # Scoped to mock's payment and measured either side of this case. Counting the
    # ledger as a whole reads the first case's capture and reports it as this
    # case's doing -- the same shared-database trap as before, in a test written
    # specifically to check that nothing else moved.
    def _mock_entries() -> int:
        return int(
            scalar(
                db,
                """SELECT count(*)::text FROM ledger_transactions t
                     JOIN payments p ON p.id = t.payment_id
                    WHERE p.provider = 'mock' AND p.provider_reference = 'settle-ref-scope';""",
            )
        )

    before = _mock_entries()
    event_id = _verified_event(
        db, "settle-ref-scope", provider="other_provider", amount=510000,
        event_id="evt-other-provider",
    )

    # This one is amount-matched for its own payment, so the scope test has to be
    # about which row moves, not about the amount check catching it first.
    outcome = scalar(db, f"SELECT app.settle_provider_event('{event_id}');")
    if _mock_entries() != before:
        raise Failure("another provider's webhook settled a payment belonging to mock")

    if scalar(
        db,
        "SELECT status::text FROM payments WHERE provider = 'mock' "
        "AND provider_reference = 'settle-ref-scope';",
    ) != "pending":
        raise Failure("another provider's webhook settled mock's payment")

    return (
        "a webhook scoped to one provider leaves the same reference under another "
        "provider unsettled, so a shared reference cannot cross providers"
    )


@case("a settled payment is not walked back by a later contradictory webhook")
def _settlement_records_contradictions(db: str) -> str:
    """
    Spec §13.5 resolves out-of-order delivery by the terminal state. But "resolved"
    is not the same as "not worth recording": the provider saying `failed` for a
    transfer we have captured is a discrepancy a human has to look at, and if it is
    filed as routine no-change it disappears.

    So the state stands, the ledger is untouched, and the event carries both
    figures for E3-08. This case exists because the first version of 107 checked
    for the contradiction *after* the no-change branch, where
    `resolve_transfer_state` had already guaranteed it could never be reached.
    """
    _pending_money_ajo(db, reference="settle-ref-contradiction", group=5)

    first = _verified_event(
        db, "settle-ref-contradiction", event_id="evt-settle-success"
    )
    must_succeed(db, "capturing the first success", f"SELECT app.settle_provider_event('{first}');")

    before = int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;"))
    second = _verified_event(
        db, "settle-ref-contradiction", state="failed", event_id="evt-settle-failed-later"
    )
    outcome = scalar(db, f"SELECT app.settle_provider_event('{second}');")

    if "contradiction" not in outcome:
        raise Failure(
            f"a failure arriving after a captured success returned {outcome!r}; "
            "the state stands, but the contradiction has to be recorded"
        )

    if int(scalar(db, "SELECT count(*)::text FROM ledger_transactions;")) != before:
        raise Failure("a later contradictory webhook moved the ledger")

    if scalar(
        db, "SELECT status::text FROM payments WHERE provider_reference = 'settle-ref-contradiction';"
    ) != "success":
        raise Failure("a later failure walked back a captured payment")

    detail = scalar(db, f"SELECT error_detail FROM webhook_events WHERE id = '{second}';")
    if "success" not in detail or "failed" not in detail:
        raise Failure(f"the contradiction does not record both states: {detail!r}")

    # Processed, not failed: a third delivery would not resolve it, and retrying
    # would re-report it forever.
    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{second}';") != "processed":
        raise Failure("the contradictory event was left retryable")

    return (
        "a failure arriving after a captured success leaves the payment and the "
        "ledger exactly as they were, records both states on the event, and files it "
        "as processed rather than retrying a contradiction forever"
    )


@case("a capture from a webhook is audited as a webhook")
def _settlement_audits_the_actor(db: str) -> str:
    """
    `audit_logs.actor_type` has always allowed `webhook` and nothing could ever
    write it: `app.audit_row()` mapped the GUC's two values onto two of the four
    and sent everything else to `service`. So the first money this system posts
    from a provider confirmation would have been filed as indistinguishable from a
    cron job -- on the one table where the distinction is the whole point.
    """
    _pending_money_ajo(db, reference="settle-ref-untyped", group=6)
    event_id = _verified_event(db, "settle-ref-untyped", event_id="evt-no-actor-type")

    # Without the GUC set, the default path applies and this must NOT claim a
    # webhook did it.
    must_succeed(
        db,
        "settling without an actor type",
        transaction(f"SELECT app.settle_provider_event('{event_id}');"),
    )
    default_actor = scalar(
        db,
        """SELECT COALESCE((
             SELECT actor_type::text FROM audit_logs a
               JOIN ledger_transactions t ON t.id = a.subject_id
              WHERE a.subject_type = 'ledger_transaction'
              ORDER BY a.created_at DESC LIMIT 1), 'none');""",
    )
    if default_actor == "webhook":
        raise Failure("a settlement with no actor type was audited as a webhook")

    _pending_money_ajo(db, reference="settle-ref-audited", group=7)
    actor_event = _verified_event(db, "settle-ref-audited", event_id="evt-audited")
    must_succeed(
        db,
        "settling as a webhook",
        transaction(
            f"""SELECT set_config('app.actor_type', 'webhook', false);
                SELECT app.settle_provider_event('{actor_event}');"""
        ).replace("ROLLBACK;", "COMMIT;"),
    )

    if scalar(
        db,
        """SELECT count(*)::text FROM audit_logs WHERE actor_type = 'webhook';""",
    ) == "0":
        raise Failure(
            "nothing was audited as a webhook; the provider confirmation and the "
            "settlement are indistinguishable from a background job in the trail"
        )

    return (
        "a capture driven by a verified provider event is audited with "
        "actor_type 'webhook', and one with no actor type set is not"
    )


@case("an event whose settlement raises is given up on, not retried forever")
def _settlement_that_raises_is_bounded(db: str) -> str:
    """
    Retry bounds live in `app.defer_provider_event`, which only runs on the paths
    that reach it. An event whose settlement *raises* never gets there: the caller's
    transaction rolls back, the event is still `processing`, and the next drain
    reclaims it.

    The trigger is real rather than contrived. Two pending payments on one
    contribution, both confirmed, is exactly what a double transfer produces, and
    the second capture violates `payments_one_success_per_contribution` forever.
    Nothing about attempt nine resolves it, so the ceiling belongs in the claim
    and the exhausted row has to end up somewhere a person will find it.
    """
    _pending_money_ajo(db, reference="exhaust-first", group=8)

    # A second pending payment on the same contribution, same provider, different
    # reference. The fixture derives its idempotency key from the reference, so
    # this is a real row and not a silent no-op.
    must_succeed(
        db,
        "a second pending payment on the same contribution",
        f"""INSERT INTO payments (
             contribution_id, channel_id, idempotency_key, provider,
             provider_reference, contribution_amount_kobo, status
           )
           SELECT c.id, ch.id, 'idem-exhaust-second', 'mock', 'exhaust-second',
             1000000, 'pending'
             FROM contributions c, payment_channels ch
            WHERE c.round_id = '{_settle_round(8)}' AND ch.code = 'bank_transfer';""",
    )

    first = _verified_event(db, "exhaust-first", event_id="evt-exhaust-first")
    must_succeed(
        db,
        "the first capture on that contribution",
        # Committed, not rolled back like `transaction()` does by default: the
        # whole case depends on the contribution being paid afterwards, and an
        # unpaid contribution lets the second capture succeed where it must raise.
        transaction(f"SELECT app.settle_provider_event('{first}');").replace(
            "ROLLBACK;", "COMMIT;"
        ),
    )

    # `_verified_event` ingests, verifies and claims, so the event starts claimed.
    second = _verified_event(db, "exhaust-second", event_id="evt-exhaust-raises")

    def _reclaim() -> str:
        return scalar(
            db,
            f"SELECT count(*)::text FROM app.claim_provider_event({_CLAIM_EVERYTHING}) "
            f"WHERE id = '{second}';",
        )

    # Every attempt raises the same way, and nothing about it is retried forever.
    raised = 0
    for _ in range(12):
        outcome = scalar(db, f"SELECT app.settle_provider_event('{second}');")
        if "payments_one_success_per_contribution" in outcome:
            raised += 1

        # The claim leased the event five minutes out, so the reclaim skips it --
        # correct, and why this loop would otherwise stop after one attempt. The
        # lease is fast-forwarded instead of slept through, which is the state a
        # worker that died mid-settlement leaves behind.
        must_succeed(
            db,
            "letting the lease expire",
            f"""UPDATE webhook_events
                   SET next_retry_at = now() - interval '1 second'
                 WHERE id = '{second}';""",
        )
        if _reclaim() == "0":
            break

    if raised == 0:
        raise Failure("the duplicate capture did not raise; nothing was bounded")

    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{second}';") != "failed":
        raise Failure(
            "an event whose settlement kept raising was still claimable after "
            f"{raised} attempts, so the queue would run it forever"
        )

    if "gave up" not in scalar(
        db, f"SELECT error_detail FROM webhook_events WHERE id = '{second}';"
    ):
        raise Failure("the exhausted event did not say why it stopped")

    return (
        "a settlement that raises every time is claimed eight times and then filed "
        "as failed with the reason, rather than staying processing forever"
    )


@case("an event type we do not act on is acknowledged and recorded, not refused")
def _unknown_event_type_is_discarded(db: str) -> str:
    """
    Spec §13.5: "Unknown event types: Acknowledged, logged, and ignored -- never a
    4xx, and never a crash."

    The two functions `106` wrote for this cannot reach each other. Ignoring an
    event asserts it is signature-verified, and the only function that records a
    verification insists on the reference, amount and state that settlement
    matches on -- which an event type we do not act on is most likely not to
    carry at all. `account.updated` has no `provider_reference` in it.

    So this case sends exactly that: a verified event with no reference, no amount
    and no state, and asserts it ends up `ignored` with a reason rather than as a
    verification failure or a stuck row.
    """
    row_id = scalar(
        db,
        f"""SELECT (e.event_id::text) AS joined
              FROM app.ingest_provider_event(
                'mock', 'evt-account-updated', 'account.updated', now(),
                '{{"accountId":"acct-1","status":"ACTIVE"}}'::jsonb) e;""",
    )
    must_fail(
        db,
        "verifying it without the values settlement needs",
        f"SELECT app.mark_provider_event_verified('{row_id}', 'HMAC-SHA256', NULL, NULL, NULL, NULL);",
        expect="must record the provider reference",
    )

    must_succeed(
        db,
        "discarding the event type we do not act on",
        f"""SELECT app.discard_provider_event(
                '{row_id}', 'HMAC-SHA256',
                'event type account.updated is not acted on', 'acct-1');""",
    )

    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{row_id}';") != "ignored":
        raise Failure("an unrecognised event type did not end up ignored")

    if scalar(db, f"SELECT provider_reference FROM webhook_events WHERE id = '{row_id}';") != "acct-1":
        raise Failure(
            "the discarded event did not record the reference it was about; a "
            "reconciliation query by reference would not find it"
        )

    if "account.updated" not in scalar(
        db, f"SELECT error_detail FROM webhook_events WHERE id = '{row_id}';"
    ):
        raise Failure("the discarded event did not record which event type it was")

    # The important half. An ignored event is signature-verified, so anything that
    # checked only that flag would find it actionable; what has to stop it is its
    # status. Both gates are asserted, because either one alone is enough to hold
    # today and neither is obviously load-bearing.
    if scalar(db, f"SELECT signature_verified FROM webhook_events WHERE id = '{row_id}';") != "t":
        raise Failure("the discarded event was not recorded as verified; the queue would claim it")

    claimed = scalar(
        db,
        f"SELECT count(*)::text FROM app.claim_provider_event() WHERE id = '{row_id}';",
    )
    if claimed != "0":
        raise Failure("a discarded event was handed out by the claim; it must be unreachable")

    must_fail(
        db,
        "settling a discarded event",
        f"SELECT app.settle_provider_event('{row_id}');",
        expect="not claimed for processing",
    )

    return (
        "an unrecognised event type is recorded as verified, marked ignored with its "
        "reason, findable by reference, and is neither claimable nor settleable"
    )


@case("a redelivered event can be discarded without being an error")
def _discard_is_idempotent(db: str) -> str:
    """
    Providers retry, and a retry of a good event must not look like an attack. The
    same rule the verify path follows: an event already processed is not an error.
    """
    row_id = scalar(
        db,
        f"""SELECT (e.event_id::text) AS joined
              FROM app.ingest_provider_event(
                'mock', 'evt-discarded-twice', 'account.updated', now(),
                '{{"accountId":"acct-2"}}'::jsonb) e;""",
    )
    for attempt in ("first", "second"):
        must_succeed(
            db,
            f"discarding the {attempt} delivery",
            f"SELECT app.discard_provider_event('{row_id}', 'HMAC-SHA256', 'not acted on');",
        )

    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{row_id}';") != "ignored":
        raise Failure("the redelivery changed the outcome of a discarded event")

    must_fail(
        db,
        "discarding an event without saying how it was verified",
        f"SELECT app.discard_provider_event('{row_id}', NULL, 'no algorithm');",
        expect="must record which algorithm verified it",
    )

    return "a second delivery of a discarded event is absorbed, and the algorithm is still required"


@case("a replay re-queues only what stopped, and never a settled event")
def _replay_requeues_only_what_stopped(db: str) -> str:
    """
    §13.5 asks for replay so an outage is recoverable. The failure worth spending
    a case on is not "does the row come back" -- it is "does anything come back
    that should not".

    Three things must survive this migration's write. A settled event is the one
    that matters: re-queueing it is the only irreversible mistake available here,
    because the settlement path would then meet `payments_one_success_per_contribution`
    and stop -- leaving a row that says received and an audit trail that says
    replayed, for an event that was captured weeks ago. A `received` event is
    quieter but equally wrong, because a worker is on its way to it and a replay
    would reset the attempt counter underneath one. `ignored` is a decision
    somebody made on purpose.

    The rest of the case is the thing an operator actually wants to know: that a
    replay followed by a re-settle captures a payment whose earlier failure has
    been fixed. Without that, this function is only ever a way to fail the same
    way twice.
    """
    # Three separate contributions, on purpose. The earlier version of this case
    # put all three events on one payment, which cannot work: the settled event
    # captures the contribution, and then the stopped event -- the one this case
    # exists to recover -- is refused by `payments_one_success_per_contribution`
    # no matter what the replay does. The three events have to be independent for
    # the last assertion to mean anything.
    _pending_money_ajo(db, reference="replay-stops", group=21)
    _pending_money_ajo(db, reference="replay-paid", group=22)
    _pending_money_ajo(db, reference="replay-queued", group=23)

    # The event that must stop. Matching payment, wrong amount, so the settlement
    # path escalates rather than defers -- one call instead of eight attempts.
    stopped = _verified_event(
        db, "replay-stops", event_id="evt-replay-stops", amount=999999999,
    )
    if "amount mismatch" not in scalar(
        db, f"SELECT app.settle_provider_event('{stopped}');"
    ):
        raise Failure(
            "the fixture did not escalate on the amount mismatch, so this case is "
            "not testing a replay of a stopped event at all"
        )
    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{stopped}';") != "failed":
        raise Failure(
            "the fixture did not fail, so this case is not testing a replay of a "
            "stopped event at all"
        )
    if scalar(db, f"SELECT attempts::text FROM webhook_events WHERE id = '{stopped}';") != "1":
        raise Failure("the fixture did not burn an attempt, so the reset proves nothing")

    # The window this case replays. The whole point of the production call is a
    # window, and this case has to use one: every other case in this file has left
    # `failed` rows behind, so a NULL window would re-queue the lot and the count
    # would be measuring the suite rather than the replay. Pinning both ends to the
    # instant this event stopped isolates it -- timestamps here are microsecond
    # `now()` values, so nothing else shares it.
    stopped_at = scalar(
        db, f"SELECT processed_at::text FROM webhook_events WHERE id = '{stopped}';"
    )

    # The event that must not come back, because it is already captured. A
    # different payment now, so this one can settle without consuming the
    # contribution the stopped event needs.
    paid = _verified_event(
        db, "replay-paid", event_id="evt-replay-already-paid", amount=1020000,
    )
    must_succeed(
        db,
        "settling the event that is already captured",
        transaction(f"SELECT app.settle_provider_event('{paid}');").replace(
            "ROLLBACK;", "COMMIT;"
        ),
    )
    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{paid}';") != "processed":
        raise Failure("the fixture did not settle, so this case cannot prove it was left alone")

    # And one still on the queue, which a worker has not reached.
    queued = _verified_event(
        db, "replay-queued", event_id="evt-replay-still-queued", amount=1020000,
    )

    # The reason is not a formality. A hundred events re-queued with nothing
    # recorded about why is an audit trail that cannot answer the only question
    # anybody will have. Whitespace is not a reason either -- `btrim` is what makes
    # `--reason ""` on a command line a refusal rather than an empty audit field.
    must_fail(
        db,
        "replaying with no reason",
        "SELECT app.replay_provider_event(NULL, NULL, 100, NULL);",
        expect="must record why",
    )
    must_fail(
        db,
        "replaying with a blank reason",
        "SELECT app.replay_provider_event(NULL, NULL, 100, '   ');",
        expect="must record why",
    )

    must_fail(
        db,
        "replaying with a limit of zero",
        "SELECT app.replay_provider_event(NULL, NULL, 0, 'a limit of nothing');",
        expect="p_limit must be between 1 and 10000",
    )

    must_fail(
        db,
        "replaying a window that runs backwards",
        "SELECT app.replay_provider_event(now(), now() - interval '1 day', 10, 'backwards');",
        expect="window runs backwards",
    )

    replayed = scalar(
        db,
        f"SELECT app.replay_provider_event('{stopped_at}', '{stopped_at}', 100, "
        "  'the settlement database was unreachable for two hours');",
    )
    if replayed != "1":
        raise Failure(
            f"expected exactly one event in the window to be re-queued, got {replayed}. "
            "Anything more means a settled or still-queued event was replayed; anything "
            "less means the stopped one was not found."
        )

    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{paid}';") != "processed":
        raise Failure("the replay re-queued a settled event; that is the irreversible one")
    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{queued}';") != "processing":
        raise Failure("the replay re-queued an event that was already on the queue")
    if scalar(db, f"SELECT status::text FROM webhook_events WHERE id = '{stopped}';") != "received":
        raise Failure("the replay did not put the stopped event back on the queue")

    # A fresh budget, and no trace of having stopped. A queued event that still
    # carries its stop time answers "when did this stop" with a date for something
    # that is running now.
    if scalar(db, f"SELECT attempts::text FROM webhook_events WHERE id = '{stopped}';") != "0":
        raise Failure("the replay did not reset the attempt counter; the old budget was left spent")
    if scalar(
        db, f"SELECT count(*)::text FROM webhook_events WHERE id = '{stopped}' AND processed_at IS NULL;"
    ) != "1":
        raise Failure("the replay left the stop time on an event that is now queued again")

    # Why it was replayed, and what it was before, have to survive the overwrite.
    # After the update there is nowhere else to recover either.
    audit = scalar(
        db,
        f"""SELECT (a.after_state ->> 'reason') || '|' || a.action || '|'
                  || a.subject_type::text || '|' || (a.before_state IS NULL)::text
              FROM audit_logs a
             WHERE a.subject_id = '{stopped}' AND a.action = 'webhook.replay';""",
    )
    if audit != "the settlement database was unreachable for two hours|webhook.replay|webhook_event|true":
        raise Failure(
            f"the replay was not audited in a way a later reader could use: {audit!r}"
        )
    if "amount" not in scalar(
        db,
        f"""SELECT a.after_state ->> 'previous_error' FROM audit_logs a
             WHERE a.subject_id = '{stopped}' AND a.action = 'webhook.replay';""",
    ):
        raise Failure("the audit row did not record what the event had failed on")

    # Running it again must be a no-op, not a second re-queue. "Replay everything
    # that failed since the outage" is a command an operator runs more than once
    # when they are not sure whether the first one worked.
    if scalar(
        db,
        f"SELECT app.replay_provider_event('{stopped_at}', '{stopped_at}', 100, "
        "  'checking whether the first replay took');",
    ) != "0":
        raise Failure("a second replay re-queued the same event; it is no longer failed")

    # The reason an operator runs this at all. The earlier failure was an amount
    # that did not match; fix the underlying record and the replayed event settles
    # on the strength of the current state, not of anything it remembered.
    must_succeed(
        db,
        "correcting the payment the stopped event referred to",
        """UPDATE payments
              SET contribution_amount_kobo = 999999999 / 1.02
            WHERE provider_reference = 'replay-stops';""",
    )
    must_succeed(
        db,
        "reclaiming the replayed event",
        f"""SELECT count(*) FROM app.claim_provider_event() WHERE id = '{stopped}';""",
    )
    outcome = scalar(db, f"SELECT app.settle_provider_event('{stopped}');")
    if outcome != "captured":
        raise Failure(
            f"the replayed event did not capture after its underlying problem was "
            f"fixed, it said {outcome!r}. Replay is only recovery if it can still succeed."
        )

    return (
        "one stopped event was re-queued with a fresh budget, an audit row naming "
        "the reason, and a settled or still-queued event left untouched; a second "
        "replay was a no-op, and the replayed event captured once its underlying "
        "failure was fixed"
    )


@case("a replay records who asked for it, not the raw actor GUC")
def _replay_records_who_asked(db: str) -> str:
    """
    The audit row's `actor_type` has a CHECK constraint with its own vocabulary
    (`user|system|service|webhook`) while `app.actor_type` is the GUC vocabulary
    (`anon|member|...`). `app.audit_row()` maps between them; a function that wrote
    the GUC value straight into the column would be refused by the CHECK -- and
    refused only in production, where the API sets 'member' and a developer's ad
    hoc call does not. This is the case that catches a missing mapping, and it also
    pins the default: no actor at all is an unattended recovery job, which is
    'system' rather than the 'service' an HTTP request would be.
    """
    _pending_money_ajo(db, reference="replay-actor", group=24)
    stopped = _verified_event(
        db, "replay-actor", event_id="evt-replay-actor", amount=999999999,
    )
    if "amount mismatch" not in scalar(
        db, f"SELECT app.settle_provider_event('{stopped}');"
    ):
        raise Failure("the fixture did not escalate, so there is nothing to replay")

    # The uncontrolled case, asserted because it is what a cron job gets: no actor
    # set at all. It must not depend on a developer having exported a GUC.
    if scalar(
        db,
        f"SELECT app.replay_provider_event("
        f"  (SELECT processed_at FROM webhook_events WHERE id='{stopped}'),"
        f"  (SELECT processed_at FROM webhook_events WHERE id='{stopped}'),"
        f"  10, 'the settlement worker was unreachable');",
    ) != "1":
        raise Failure("the unattributed replay did not re-queue the stopped event")
    if scalar(
        db,
        f"""SELECT a.actor_type || '|' || (a.actor_user_id IS NULL)::text
              FROM audit_logs a WHERE a.subject_id = '{stopped}'
               AND a.action = 'webhook.replay';""",
    ) != "system|true":
        raise Failure("an unattributed replay was not recorded as a system actor")

    # The controlled case: the API's own vocabulary. 'member' is a person acting as
    # themselves and has to arrive in the column as 'user', or the CHECK refuses it.
    _pending_money_ajo(db, reference="replay-actor-2", group=25)
    second = _verified_event(
        db, "replay-actor-2", event_id="evt-replay-actor-2", amount=999999999,
    )
    if "amount mismatch" not in scalar(
        db, f"SELECT app.settle_provider_event('{second}');"
    ):
        raise Failure("the second fixture did not escalate")

    actor = scalar(db, "SELECT id FROM users WHERE email LIKE 'settle-24@%' LIMIT 1;")
    if not actor:
        raise Failure("the fixture did not create the user this case attributes the replay to")

    must_succeed(
        db,
        "replaying as a member",
        f"""SELECT set_config('app.actor_user_id', '{actor}', false),
                   set_config('app.actor_type', 'member', false),
                   app.replay_provider_event(
                     (SELECT processed_at FROM webhook_events WHERE id='{second}'),
                     (SELECT processed_at FROM webhook_events WHERE id='{second}'),
                     10, 'a person asked for this one');""",
    )
    attributed = scalar(
        db,
        f"""SELECT a.actor_type || '|' || a.actor_user_id
              FROM audit_logs a WHERE a.subject_id = '{second}'
               AND a.action = 'webhook.replay';""",
    )
    if attributed != f"user|{actor}":
        raise Failure(
            f"'member' was not mapped to 'user' with the acting user recorded: {attributed!r}"
        )

    return (
        "an unattributed replay is recorded as 'system' with no user, and a replay "
        "run as a member is mapped to 'user' with the acting user id"
    )


@case("creating an Ajo writes it, its seats, and the organizer's seat in one transaction")
def _create_ajo(db: str) -> str:
    """
    `app.create_ajo` (migration 110) is the only write path for a new Ajo, and
    the schema makes it all-or-nothing: `ajos_organizer_is_member` is a
    DEFERRABLE INITIALLY DEFERRED constraint trigger, so the Ajo row, its
    positions and the organizer's membership have to land together or the commit
    is refused.

    `SET CONSTRAINTS ALL IMMEDIATE` is placed *after* the call and before the
    rollback, which is what makes the deferred check actually run here. Without
    it the case would pass against a transaction that a real COMMIT would have
    rejected -- `_organizer`'s `transaction()` helper does the same thing for the
    same reason.
    """
    email = "create-ajo@example.ng"
    body = f"""
INSERT INTO users (auth_subject_id, email, status, is_email_verified)
VALUES ('t-create-ajo', '{email}', 'active', true);
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{email}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.create_ajo('E5-01 Ajo', 'the test', 100000, 'NGN', 'fortnightly', 10, 'friday', DATE '2026-11-01');
SET CONSTRAINTS ALL IMMEDIATE;
SELECT 'seats=' || count(*) || '/' || count(*) FILTER (WHERE p.status = 'claimed')
  FROM ajo_positions p JOIN ajos a ON a.id = p.ajo_id WHERE a.name = 'E5-01 Ajo';
SELECT 'org=' || m.status || '/' || p.position_number
  FROM ajo_members m
  JOIN ajos a ON a.id = m.ajo_id
  JOIN ajo_positions p ON p.id = m.position_id
 WHERE a.name = 'E5-01 Ajo';
SELECT 'ajo=' || total_rounds || '/' || position_count || '/' || collection_day || '/' || status
  FROM ajos WHERE name = 'E5-01 Ajo';
"""
    out = must_succeed(db, "create_ajo as a verified member", f"BEGIN;\n{body}\nROLLBACK;")
    for expected in ("seats=10/1", "org=active/1", "ajo=10/10/friday/draft"):
        if expected not in out:
            raise Failure(
                f"create_ajo did not produce {expected!r}:\n    {out.strip()[:400]}"
            )

    # Rejections, each in its own transaction so one failure does not abort the
    # next, and each asserted on its own message rather than only on the failure:
    # the SQLSTATE alone would not tell "unverified" from "bad amount".
    verified = f"""
INSERT INTO users (auth_subject_id, email, status, is_email_verified)
VALUES ('t-create-bad', 'create-bad@example.ng', 'active', true);
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = 'create-bad@example.ng'), true);
SET LOCAL ROLE ajo_app;
"""
    must_fail(
        db,
        "three members",
        f"BEGIN;{verified}SELECT app.create_ajo('Too Small', null, 100000, 'NGN', 'weekly', 3, 'friday', DATE '2026-11-01');ROLLBACK;",
        expect="between 5 and 20",
    )
    must_fail(
        db,
        "999 naira",
        f"BEGIN;{verified}SELECT app.create_ajo('Too Cheap', null, 99900, 'NGN', 'weekly', 10, 'friday', DATE '2026-11-01');ROLLBACK;",
        expect="between 1000 and 5000000",
    )
    must_fail(
        db,
        "an unknown cadence",
        f"BEGIN;{verified}SELECT app.create_ajo('Bad Freq', null, 100000, 'NGN', 'daily', 10, 'friday', DATE '2026-11-01');ROLLBACK;",
        expect="unknown or inactive frequency",
    )
    must_fail(
        db,
        "an unverified caller",
        "BEGIN;"
        "INSERT INTO users (auth_subject_id, email, status, is_email_verified) "
        "VALUES ('t-create-unver', 'create-unver@example.ng', 'active', false);"
        "SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = 'create-unver@example.ng'), true);"
        "SET LOCAL ROLE ajo_app;"
        "SELECT app.create_ajo('Unverified', null, 100000, 'NGN', 'weekly', 10, 'friday', DATE '2026-11-01');"
        "ROLLBACK;",
        expect="email-verified active member",
    )

    # The grant is read out of pg_proc rather than proved by calling: the suite
    # connects as the superuser, which can execute anything, so a call would say
    # nothing about who else may. 106's README note is the reason this assertion
    # exists at all.
    if scalar(
        db,
        "SELECT has_function_privilege('public', "
        "'app.create_ajo(text,text,bigint,text,text,integer,text,date)', 'EXECUTE')::text;",
    ) != "false":
        raise Failure("PUBLIC can still execute app.create_ajo after the bootstrap")
    if scalar(
        db,
        "SELECT has_function_privilege('ajo_app', "
        "'app.create_ajo(text,text,bigint,text,text,integer,text,date)', 'EXECUTE')::text;",
    ) != "true":
        raise Failure("ajo_app cannot execute app.create_ajo")

    return (
        "creates the Ajo, 10 seats and the organizer's claimed seat 1; rejects a "
        "bad size, amount, cadence and unverified caller; EXECUTE stays ajo_app-only"
    )


@case("inviting a member mints one pending token and previews without the roster")
def _create_invitation(db: str) -> str:
    """
    `app.create_invitation` (migration 111) is the only write path for an
    invitation, because there is deliberately no INSERT policy on
    `public.invitations`. This case pins two things that are easy to get
    backwards: the inviter is derived from the session and never accepted as an
    argument (so an organizer cannot invite into somebody else's Ajo), and the
    anonymous preview is a curated projection rather than the row (FR-INV-003:
    no member roster, no pot value).

    The preview assertion that matters is the negative one. It would be easy to
    "fix" `preview_invitation` into `SELECT to_jsonb(i)` some later day and have
    every positive assertion still pass; the check that no invited address and no
    `organizer_user_id` appear in the output is what fails when that happens.
    """
    org = "invite-org@example.ng"
    other = "invite-other@example.ng"
    ajo = "E5B Invite"
    setup = f"""
INSERT INTO users (auth_subject_id, email, status, is_email_verified)
VALUES ('t-invite-org', '{org}', 'active', true);
INSERT INTO profiles (user_id, display_name)
SELECT id, 'Ada Organizer' FROM users WHERE email = '{org}';
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{org}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.create_ajo('{ajo}', 'the test', 100000, 'NGN', 'weekly', 10, 'friday', DATE '2026-11-01');
"""
    body = setup + f"""
SELECT 'inv=' || (app.create_invitation(
  (SELECT id FROM ajos WHERE name = '{ajo}'),
  'invitee1@example.ng', decode('01', 'hex'), now() + interval '72 hours', 'join us'
)).status;
SELECT 'preview=' || app.preview_invitation(decode('01', 'hex'))::text;
SELECT 'seats=' || (SELECT count(*) FROM ajo_positions p
   WHERE p.ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}') AND p.status = 'open');
"""
    out = must_succeed(
        db, "create_invitation as the organizer", transaction(body)
    )
    for expected in ("inv=pending", "seats=9"):
        if expected not in out:
            raise Failure(
                f"create_invitation did not produce {expected!r}:\n    {out.strip()[:400]}"
            )
    preview = ""
    for line in out.splitlines():
        if line.startswith("preview="):
            preview = line
    for expected in (
        '"name": "E5B Invite"',
        '"contributionKobo": 100000',
        '"frequencyCode": "weekly"',
        '"maxMembers": 10',
        '"membersCount": 1',
        '"name": "Ada Organizer"',
        '"positionOptions": [2',
    ):
        if expected not in preview:
            raise Failure(
                f"preview is missing {expected!r}:\n    {preview[:500]}"
            )
    if "@example.ng" in preview:
        raise Failure(
            f"preview leaked an email address:\n    {preview[:500]}"
        )
    if "organizer_user_id" in preview:
        raise Failure(
            f"preview leaked the organizer's id:\n    {preview[:500]}"
        )

    # Rejections, each in its own transaction and each asserted on its own
    # message rather than the SQLSTATE alone -- "not yours" and "already a
    # member" must not be the same outcome.
    # The non-organizer is made a *member* on purpose. A stranger cannot even see
    # the Ajo through RLS, so the argument subquery would resolve to NULL and the
    # function would answer "no Ajo to invite to" -- which is true, but tests the
    # wrong line. A member can see the Ajo, so the call reaches the explicit
    # `organizer_user_id <> v_user_id` branch and is refused for the reason that
    # matters: being in the Ajo is not the same as owning it.
    must_fail(
        db,
        "a member who is not the organizer",
        f"BEGIN;{setup}RESET ROLE;"
        f"INSERT INTO users (auth_subject_id, email, status, is_email_verified) "
        f"VALUES ('t-invite-other', '{other}', 'active', true);"
        f"UPDATE ajo_positions SET status = 'claimed' "
        f" WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}') AND position_number = 2;"
        f"INSERT INTO ajo_members (ajo_id, user_id, position_id, status, joined_at) "
        f"SELECT a.id, u.id, p.id, 'active', now() "
        f"  FROM ajos a, users u, ajo_positions p "
        f" WHERE a.name = '{ajo}' AND u.email = '{other}' "
        f"   AND p.ajo_id = a.id AND p.position_number = 2;"
        f"SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{other}'), true);"
        f"SET LOCAL ROLE ajo_app;"
        f"SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'), "
        f"'x@example.ng', decode('02', 'hex'), now() + interval '1 hour', null);ROLLBACK;",
        expect="only the organizer",
    )
    # And a stranger, who cannot see the Ajo at all, gets the same non-disclosing
    # "not yours" answer rather than a distinguishable "no such Ajo".
    must_fail(
        db,
        "a stranger",
        f"BEGIN;{setup}RESET ROLE;"
        f"INSERT INTO users (auth_subject_id, email, status, is_email_verified) "
        f"VALUES ('t-invite-stranger', 'invite-stranger@example.ng', 'active', true);"
        f"SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = 'invite-stranger@example.ng'), true);"
        f"SET LOCAL ROLE ajo_app;"
        f"SELECT app.create_invitation(("
        f"  SELECT id FROM ajos WHERE name = '{ajo}'"
        f"), 'x@example.ng', decode('02', 'hex'), now() + interval '1 hour', null);ROLLBACK;",
        expect="does not own it",
    )
    must_fail(
        db,
        "an address already in the Ajo",
        f"BEGIN;{setup}"
        f"SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'), "
        f"'{org}', decode('02', 'hex'), now() + interval '1 hour', null);ROLLBACK;",
        expect="already a member",
    )
    must_fail(
        db,
        "an address without an @",
        f"BEGIN;{setup}"
        f"SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'), "
        f"'nope', decode('02', 'hex'), now() + interval '1 hour', null);ROLLBACK;",
        expect="needs an email address",
    )
    must_fail(
        db,
        "an expiry in the past",
        f"BEGIN;{setup}"
        f"SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'), "
        f"'invitee2@example.ng', decode('02', 'hex'), now() - interval '1 hour', null);ROLLBACK;",
        expect="must expire in the future",
    )
    must_fail(
        db,
        "a full Ajo",
        f"BEGIN;{setup}RESET ROLE;"
        f"UPDATE ajo_positions SET status = 'claimed' "
        f" WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}');"
        f"SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{org}'), true);"
        f"SET LOCAL ROLE ajo_app;"
        f"SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'), "
        f"'invitee2@example.ng', decode('02', 'hex'), now() + interval '1 hour', null);ROLLBACK;",
        expect="no free positions",
    )
    # Two pending invitations to the same address collide on
    # `invitations_one_pending_per_ajo_email`, so a duplicate is refused by the
    # database rather than by the function remembering to check.
    must_fail(
        db,
        "a duplicate pending invitation",
        f"BEGIN;{setup}"
        f"SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'), "
        f"'invitee1@example.ng', decode('02', 'hex'), now() + interval '1 hour', null);"
        f"SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'), "
        f"'invitee1@example.ng', decode('03', 'hex'), now() + interval '1 hour', null);ROLLBACK;",
        expect="invitations_one_pending_per_ajo_email",
    )

    # The grants again read from pg_proc: the suite connects as the superuser, so
    # a successful call proves nothing about who else may call. `ajo_api` is the
    # one that matters for the anonymous preview route -- it is not a superuser
    # and does not bypass RLS, so EXECUTE has to come from its membership in
    # `ajo_app`.
    for role, fn, want, label in (
        ("public", "app.create_invitation(uuid,text,bytea,timestamptz,text)", "false", "PUBLIC"),
        ("ajo_app", "app.create_invitation(uuid,text,bytea,timestamptz,text)", "true", "ajo_app"),
        ("public", "app.preview_invitation(bytea)", "false", "PUBLIC"),
        ("ajo_api", "app.preview_invitation(bytea)", "true", "ajo_api"),
    ):
        got = scalar(
            db, f"SELECT has_function_privilege('{role}', '{fn}', 'EXECUTE')::text;"
        )
        if got != want:
            raise Failure(
                f"{label} EXECUTE on {fn.split('(')[0]} should be {want}, got {got!r}"
            )

    return (
        "mints a pending invitation for the organizer only, previews it without "
        "the roster or pot, rejects a stranger, a member, a bad address, a stale "
        "expiry, a full Ajo and a duplicate; EXECUTE stays ajo_app/ajo_api"
    )


@case("redeeming an invitation claims one seat, spends the token, and records the rules version")
def _join_ajo(db: str) -> str:
    """
    `app.join_ajo` (migration 112) is the only path from a token to a membership,
    and it exists because that write cannot be done honestly in the application:
    there is no INSERT policy on `ajo_members`, and a claim-then-insert route
    would leave a member with no seat whenever the process died between the two
    statements. Three claims are pinned here that an ordinary happy-path test
    cannot see.

    The first is *one* claim. `SELECT (app.join_ajo(...)).*` looks like a single
    call followed by a column expansion and is not: PostgreSQL rewrites it into
    one `(app.join_ajo(...)).<column>` per column, and a PL/pgSQL function is
    VOLATILE by default, so it runs once per column and claims a seat each time.
    The same mistake made `app.create_ajo` write 27 Ajos per request. The
    assertion is on the number of claimed seats, not on the call succeeding: a
    caller that only checked the final status would never have known.

    The second is that the acknowledgement is *recorded*. BR-004 is consent to a
    version of the rules, and a boolean cannot say which version.

    The third is that the refusals are distinguishable. 23514 covers "wrong
    version", "expired", "already accepted" and "no seats", and the API maps them
    to different status codes, so each is asserted on its own message.
    """
    org = "join-org@example.ng"
    first = "join-first@example.ng"
    second = "join-second@example.ng"
    stranger = "join-stranger@example.ng"
    ajo = "E5B Join"
    setup = f"""
INSERT INTO users (auth_subject_id, email, status, is_email_verified)
VALUES ('t-join-org', '{org}', 'active', true),
       ('t-join-first', '{first}', 'active', true),
       ('t-join-second', '{second}', 'active', true),
       ('t-join-stranger', '{stranger}', 'active', true);
INSERT INTO profiles (user_id, display_name)
SELECT id, 'Member ' || left(email, 4) FROM users WHERE email LIKE 'join-%@example.ng';
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{org}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.create_ajo('E5B Join', 'the test', 100000, 'NGN', 'weekly', 10,
                      'friday', DATE '2026-11-06');
SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'),
  '{first}', decode('11', 'hex'), now() + interval '72 hours', null);
SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'),
  '{second}', decode('22', 'hex'), now() + interval '72 hours', null);
RESET ROLE;
"""
    body = f"""{setup}
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{first}'), true);
SET LOCAL ROLE ajo_app;
SELECT 'joined=' || (app.join_ajo(decode('11', 'hex'), '{first}', app.ajo_rules_version()))::text;
SELECT 'claimed=' || (SELECT count(*) FROM ajo_positions
                       WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}')
                         AND status = 'claimed')::text;
SELECT 'acknowledged=' || (SELECT count(*) FROM ajo_members
                             WHERE invitation_id IS NOT NULL
                               AND rules_acknowledged_version = app.ajo_rules_version())::text;
SELECT 'status=' || (SELECT status FROM invitations WHERE token_hash = decode('11', 'hex'));
RESET ROLE;
"""
    out = must_succeed(db, "join_ajo as the invited member", transaction(body))
    # Two claimed seats: the organizer's own, and the invitee's. Three would mean
    # the function was evaluated once per output column.
    for expected in ("joined=(", "claimed=2", "acknowledged=1", "status=accepted"):
        if expected not in out:
            raise Failure(
                f"join_ajo did not produce {expected!r}:\n    {out.strip()[:400]}"
            )

    for label, sql, expect in (
        (
            "an invitation redeemed by a different address",
            f"""
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{stranger}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.join_ajo(decode('11', 'hex'), '{stranger}', app.ajo_rules_version());
""",
            "sent to a different address",
        ),
        (
            "an acknowledgement of a stale rules version",
            f"""
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{first}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.join_ajo(decode('11', 'hex'), '{first}',
                    (app.ajo_rules_version() + 1)::smallint);
""",
            "rules have changed",
        ),
        (
            "an expired invitation",
            f"""
UPDATE invitations SET expires_at = now() - interval '1 minute'
 WHERE token_hash = decode('11', 'hex');
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{first}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.join_ajo(decode('11', 'hex'), '{first}', app.ajo_rules_version());
""",
            "has expired",
        ),
        (
            "a replayed redemption",
            f"""
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{first}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.join_ajo(decode('11', 'hex'), '{first}', app.ajo_rules_version());
SELECT app.join_ajo(decode('11', 'hex'), '{first}', app.ajo_rules_version());
""",
            "already accepted",
        ),
        (
            "an unknown token",
            f"""
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{first}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.join_ajo(decode('99', 'hex'), '{first}', app.ajo_rules_version());
""",
            "not valid",
        ),
        # Already a member. Not reachable through the API, which refuses to mint
        # an invitation for somebody who already holds a seat. This is the race
        # the check exists for: invited, then joined by some other route, then
        # the token presented -- and it must not cost a second seat.
        (
            "somebody who is already a member",
            f"""
UPDATE ajo_positions SET status = 'claimed'
 WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}') AND position_number = 3;
INSERT INTO ajo_members (ajo_id, user_id, position_id, status, joined_at)
SELECT a.id, u.id, p.id, 'active', now()
  FROM ajos a, users u, ajo_positions p
 WHERE a.name = '{ajo}' AND u.email = '{first}'
   AND p.ajo_id = a.id AND p.position_number = 3;
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{first}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.join_ajo(decode('11', 'hex'), '{first}', app.ajo_rules_version());
""",
            "already a member",
        ),
    ):
        must_fail(db, label, transaction(setup + sql), expect)

    # A full Ajo: the tenth seat taken by somebody else before the token is
    # redeemed. The invitation is not spent, so it is still usable if a seat frees.
    must_fail(
        db,
        "an Ajo with no seat left",
        transaction(
            setup
            + f"""
UPDATE ajo_positions SET status = 'claimed'
 WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}')
   AND position_number <> 1;
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{second}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.join_ajo(decode('22', 'hex'), '{second}', app.ajo_rules_version());
"""
        ),
        "no free positions",
    )

    declined = must_succeed(
        db,
        "decline_invitation",
        transaction(
            setup
            + f"""
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{second}'), true);
SET LOCAL ROLE ajo_app;
SELECT 'declined=' || app.decline_invitation(decode('22', 'hex'), '{second}')::text;
SELECT 'members=' || (SELECT count(*) FROM ajo_members
                       WHERE invitation_id IS NOT NULL)::text;
SELECT 'status=' || (SELECT status FROM invitations WHERE token_hash = decode('22', 'hex'));
RESET ROLE;
"""
        ),
    )
    for expected in ("declined=true", "members=0", "status=declined"):
        if expected not in declined:
            raise Failure(
                f"decline_invitation did not produce {expected!r}:\n"
                f"    {declined.strip()[:400]}"
            )
    must_fail(
        db,
        "a replayed decline",
        transaction(
            setup
            + f"""
SELECT set_config('app.user_id', (SELECT id::text FROM users WHERE email = '{second}'), true);
SET LOCAL ROLE ajo_app;
SELECT app.decline_invitation(decode('22', 'hex'), '{second}');
SELECT app.decline_invitation(decode('22', 'hex'), '{second}');
"""
        ),
        "already declined",
    )

    for role, fn, want, label in (
        ("public", "app.join_ajo(bytea,text,smallint)", "false", "PUBLIC"),
        ("ajo_app", "app.join_ajo(bytea,text,smallint)", "true", "ajo_app"),
        ("public", "app.decline_invitation(bytea,text)", "false", "PUBLIC"),
        ("ajo_api", "app.decline_invitation(bytea,text)", "true", "ajo_api"),
    ):
        got = scalar(
            db, f"SELECT has_function_privilege('{role}', '{fn}', 'EXECUTE')::text;"
        )
        if got != want:
            raise Failure(
                f"{label} EXECUTE on {fn.split('(')[0]} should be {want}, got {got!r}"
            )
    return (
        "claims exactly one seat under SKIP LOCKED, records the acknowledged rules "
        "version on the membership, spends the token once; refuses a wrong address, "
        "a stale acknowledgement, an expired link, a replay, a non-member, an "
        "unknown token and a full Ajo without spending the token; declining writes "
        "no membership and cannot be replayed; EXECUTE stays ajo_app-only"
    )


@case("a draft has no enrollment clock, and opening enrollment starts one")
def _enrollment_clock(db: str) -> str:
    """
    EC-061: a draft has no clock running on it. `app.create_ajo` (110) stamps
    `enrollment_opens_at` and `enrollment_closes_at` at creation because the
    columns are NOT NULL, and migration 113 does not change that -- it makes the
    placeholder unreadable instead. Nothing sweeps a `draft`, and
    `app.assert_joinable` only consults the window for an Ajo already in
    `enrollment`, so an abandoned draft cancels nothing and collects nothing.

    The claim worth testing is that the placeholder is *replaced*, not merely
    ignored. The fixture is aged past the end of its own placeholder window, and
    the assertion is that the window which comes back is a full five days from
    now. A draft that sat for six days gets five days of enrollment, not zero.
    """
    org = "clock-org@example.ng"
    ajo = "E5C Clock"
    _seed_users(db, "an organizer", [("t-clock-org", org)])
    must_succeed(
        db,
        "a draft",
        as_role(
            db,
            "ajo_app",
            org,
            f"""SELECT app.create_ajo('{ajo}', 'the test', 100000, 'NGN', 'weekly', 5,
                      'friday', DATE '2026-11-06');""",
            commit=True,
        ),
    )

    # Age the draft so its creation-time placeholder window has already closed,
    # the way a draft abandoned for a week actually looks.
    must_succeed(
        db,
        "ageing the draft past its placeholder window",
        commit(
            f"""
UPDATE ajos SET created_at = now() - interval '6 days',
                enrollment_opens_at = now() - interval '6 days',
                enrollment_closes_at = now() - interval '1 day'
 WHERE name = '{ajo}';
"""
        ),
    )

    out = must_succeed(
        db,
        "opening enrollment on an aged draft",
        as_role(
            db,
            "ajo_app",
            org,
            f"""
SELECT 'window=' || (app.open_enrollment(
  (SELECT id FROM ajos WHERE name = '{ajo}')))::text;
SELECT 'status=' || (SELECT status FROM ajos WHERE name = '{ajo}');
SELECT 'days=' || round(EXTRACT(epoch FROM (
  enrollment_closes_at - enrollment_opens_at)) / 86400.0, 4)::text
  FROM ajos WHERE name = '{ajo}';
SELECT 'left=' || round(EXTRACT(epoch FROM (
  enrollment_closes_at - now())) / 86400.0, 4)::text
  FROM ajos WHERE name = '{ajo}';
""",
            commit=True,
        ),
    )
    if "status=enrollment" not in out:
        raise Failure(f"the Ajo did not enter enrollment:\n    {out.strip()[:400]}")
    if "days=5.0000" not in out:
        raise Failure(
            "the window is not exactly five days:\n" f"    {out.strip()[:400]}"
        )
    # The placeholder closed a day ago, so a window carried over from creation
    # would report a negative remainder here.
    if "left=5.0000" not in out and "left=4.9999" not in out:
        raise Failure(
            "the clock did not restart: the remainder is not a full five days, so "
            "the placeholder leaked into the window\n"
            f"    {out.strip()[:400]}"
        )

    # A second open, an unknown Ajo and an anonymous caller. Each impersonates a
    # real caller: `app.open_enrollment` reads the identity GUC before it looks at
    # the Ajo, so a missing GUC reports "requires an authenticated caller" and the
    # assertion would pass for the wrong reason on all three.
    must_fail(
        db,
        "opening enrollment a second time",
        as_role(
            db,
            "ajo_app",
            org,
            f"""SELECT app.open_enrollment((SELECT id FROM ajos WHERE name = '{ajo}'));""",
        ),
        expect="already open",
    )
    must_fail(
        db,
        "an unknown Ajo",
        as_role(
            db,
            "ajo_app",
            org,
            """SELECT app.open_enrollment('00000000-0000-7000-8000-000000000001');""",
        ),
        expect="no such Ajo",
    )
    must_fail(
        db,
        "an unauthenticated caller",
        "BEGIN;\nSELECT set_config('app.user_id', '', false);\nSET LOCAL ROLE ajo_app;\n"
        f"""SELECT app.open_enrollment((SELECT id FROM ajos WHERE name = '{ajo}'));\nROLLBACK;""",
        expect="requires an authenticated caller",
    )

    for role, fn, want, label in (
        ("public", "app.open_enrollment(uuid)", "false", "PUBLIC"),
        ("ajo_app", "app.open_enrollment(uuid)", "true", "ajo_app"),
        ("public", "app.close_expired_enrollment()", "false", "PUBLIC"),
        ("ajo_app", "app.close_expired_enrollment()", "false", "ajo_app"),
    ):
        got = scalar(db, f"SELECT has_function_privilege('{role}', '{fn}', 'EXECUTE')::text;")
        if got != want:
            raise Failure(f"{label} EXECUTE on {fn} should be {want}, got {got!r}")

    return (
        "an aged draft gets a fresh five days rather than its expired placeholder; "
        "a second open, an unknown Ajo and an anonymous caller are all refused; "
        "open_enrollment is ajo_app-only and the sweep is nobody's but the owner's"
    )


@case("the enrollment window cannot be extended")
def _no_extension(db: str) -> str:
    """
    EC-053 and CANONICAL section 3: the window is *exactly* five days and the
    organizer cannot move it. The invitees were told when this closes, so moving
    that date is not a configuration change -- it is a change to a promise already
    made to them.

    `app.open_enrollment` computes the window itself, so any movement is only
    reachable with a bare `UPDATE`, which is what `app.assert_enrollment_window`
    exists to refuse. Both directions are asserted. Shortening was considered and
    rejected: CANONICAL says the window is exactly five days, so a three-day
    window is not a shorter version of the rule, it is a different rule.
    """
    org = "extend-org@example.ng"
    ajo = "E5D Extend"
    _seed_users(db, "an organizer", [("t-extend-org", org)])
    must_succeed(
        db,
        "an Ajo in enrollment",
        as_role(
            db,
            "ajo_app",
            org,
            f"""
SELECT app.create_ajo('{ajo}', 'the test', 100000, 'NGN', 'weekly', 5,
                      'friday', DATE '2026-11-06');
SELECT app.open_enrollment((SELECT id FROM ajos WHERE name = '{ajo}'));
""",
            commit=True,
        ),
    )

    must_fail(
        db,
        "extending by two days",
        commit(f"UPDATE ajos SET enrollment_closes_at = enrollment_closes_at + interval '2 days' WHERE name = '{ajo}';"),
        expect="cannot move its enrollment window",
    )
    must_fail(
        db,
        "extending by a single second",
        commit(f"UPDATE ajos SET enrollment_closes_at = enrollment_closes_at + interval '1 second' WHERE name = '{ajo}';"),
        expect="cannot move its enrollment window",
    )
    must_fail(
        db,
        "shortening the window by one day",
        commit(f"UPDATE ajos SET enrollment_closes_at = enrollment_closes_at - interval '1 day' WHERE name = '{ajo}';"),
        expect="cannot move its enrollment window",
    )
    must_fail(
        db,
        "moving the open date",
        commit(f"UPDATE ajos SET enrollment_opens_at = enrollment_opens_at - interval '1 day' WHERE name = '{ajo}';"),
        expect="cannot move its enrollment window",
    )
    # A bare UPDATE straight into `enrollment` is the other half of EC-061. It is
    # accepted, and the window it lands with is a fresh five days rather than
    # whatever placeholder the draft was carrying -- the trigger stamps the
    # transition, so a draft aged past its own placeholder still gets a full
    # window.
    later = "E5D Later"
    _seed_users(db, "a second organizer", [("t-extend-later", "extend-later@example.ng")])
    must_succeed(
        db,
        "a second draft",
        as_role(
            db,
            "ajo_app",
            "extend-later@example.ng",
            f"""SELECT app.create_ajo('{later}', 'the test', 100000, 'NGN', 'weekly', 5,
                      'friday', DATE '2026-11-06');""",
            commit=True,
        ),
    )
    must_succeed(
        db,
        "ageing the second draft past its placeholder",
        commit(
            f"""
UPDATE ajos SET created_at = now() - interval '9 days',
                enrollment_opens_at = now() - interval '9 days',
                enrollment_closes_at = now() - interval '4 days'
 WHERE name = '{later}';
"""
        ),
    )
    out = must_succeed(
        db,
        "entering enrollment with a bare UPDATE",
        commit(
            f"""
UPDATE ajos SET status = 'enrollment' WHERE name = '{later}';
SELECT 'days=' || round(EXTRACT(epoch FROM (
  enrollment_closes_at - enrollment_opens_at)) / 86400.0, 4)::text
  FROM ajos WHERE name = '{later}';
SELECT 'left=' || round(EXTRACT(epoch FROM (
  enrollment_closes_at - now())) / 86400.0, 4)::text
  FROM ajos WHERE name = '{later}';
"""
        ),
    )
    if "days=5.0000" not in out:
        raise Failure(
            "a bare UPDATE into enrollment did not start a five-day window:\n"
            f"    {out.strip()[:300]}"
        )
    # The draft is nine days old and its placeholder closed four days ago, so a
    # window inherited from creation reports a *negative* remainder here. Anything
    # near five proves the trigger stamped the transition.
    if "left=4.999" not in out and "left=5.000" not in out:
        raise Failure(
            "the bare UPDATE kept the stale placeholder: a nine-day-old draft got "
            f"a window that had already closed:\n    {out.strip()[:300]}"
        )
    return (
        "one second past the close is refused as firmly as two days, and so is "
        "shortening or moving the open date; a bare UPDATE into enrollment is "
        "accepted but restamps a fresh five days rather than inheriting a stale "
        "placeholder"
    )


@case("the last seat claimed activates the Ajo, and locks its positions")
def _activate_on_fill(db: str) -> str:
    """
    EC-051: "Enrollment fills every position on day 4, so the Ajo activates early
    rather than waiting for day 5. Activation proceeds on the fill event, not on a
    calendar event."

    The claim is therefore not that activation is possible on the fill, but that it
    *happens* on the fill -- here, with four and a half days left on the clock.
    Nothing in this case advances time. If activation were wired to the expiry
    sweep instead, this Ajo would still be sitting in `enrollment` and the
    assertion would fail.

    The trigger is on `ajo_members` rather than inside `app.join_ajo` so that it is
    the only way in: a seat claimed through any other path has to activate the Ajo
    too, or a full Ajo waits until day five and cancels a rotation every member
    joined correctly.

    Position locking is the second half of E5-06 and is already enforced by
    `app.assert_positions_locked`, which reads this status -- so it is pinned here
    against the state the trigger just wrote rather than tested on its own.
    """
    org = "fill-org@example.ng"
    ajo = "E5E Fill"
    members = [f"fill-{i}@example.ng" for i in range(1, 5)]
    _seed_users(db, "an organizer and four invitees",
                [("t-fill-org", org)]
                + [(f"t-fill-{i}", m) for i, m in enumerate(members, start=1)])
    must_succeed(
        db,
        "a draft, opened and invited",
        as_role(
            db,
            "ajo_app",
            org,
            f"""SELECT app.create_ajo('{ajo}', 'the test', 100000, 'NGN', 'weekly', 5,
                      'friday', DATE '2026-11-06');
SELECT app.open_enrollment((SELECT id FROM ajos WHERE name = '{ajo}'));
"""
            + "".join(
                f"""SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'),
  '{m}', decode('{i:02x}', 'hex'), now() + interval '72 hours', null);
"""
                for i, m in enumerate(members, start=1)
            ),
            commit=True,
        ),
    )
    # The tokens must actually be in the table. `create_invitation` reports
    # success by returning the row even when nothing was inserted -- that was
    # migration 112's own bug with a hard-coded idempotency key -- so the count is
    # asserted rather than the exit status.
    minted = scalar(
        db,
        f"SELECT count(*)::text FROM invitations WHERE ajo_id ="
        f" (SELECT id FROM ajos WHERE name = '{ajo}');",
    )
    if minted != "4":
        raise Failure(
            f"expected 4 pending invitations, found {minted}; the join assertions "
            "below would fail with 'link is not valid' for the wrong reason"
        )

    # Four joins for five seats: the organizer took seat 1 when the Ajo was
    # created, so the fourth join fills the Ajo and none before it may activate it.
    #
    # One round trip per invitee for the join, one scalar read either side of it.
    #
    # The status is read outside the joining transaction rather than as a SELECT
    # alongside it, for two reasons. One statement cannot observe a change it
    # makes: in `... || app.join_ajo(...) || (SELECT status ...) || ...` there is
    # no evaluation order that puts the join before the re-read, so "after" would
    # equal "before" every time. And `psql -c` with several statements prints only
    # the last result set, so a labelled SELECT beside the join is silently not in
    # the output at all -- the label never appears and the assertion reads an empty
    # list rather than a wrong value.
    before: list[str] = []
    after: list[str] = []
    for i, m in enumerate(members, start=1):
        before.append(scalar(db, f"SELECT status::text FROM ajos WHERE name = '{ajo}';"))
        must_succeed(
            db,
            f"invitee {i} joining",
            as_role(
                db,
                "ajo_app",
                m,
                f"""SELECT app.join_ajo(decode('{i:02x}', 'hex'), '{m}',
                    app.ajo_rules_version());""",
                commit=True,
            ),
        )
        after.append(scalar(db, f"SELECT status::text FROM ajos WHERE name = '{ajo}';"))

    if before != ["enrollment"] * 4:
        raise Failure(
            f"the Ajo was not in enrollment for each of the four joins: {before}"
        )
    if after != ["enrollment"] * 3 + ["active"]:
        raise Failure(f"the Ajo did not activate on the fill event: {after}")

    must_fail(
        db,
        "reordering a position after activation",
        commit(
            f"""
UPDATE ajo_positions SET position_number = 5
 WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}')
   AND position_number = 2;
"""
        ),
        expect="the turn order is locked at activation",
    )
    _seed_users(db, "a late invitee", [("t-fill-late", "fill-late@example.ng")])
    must_fail(
        db,
        "an invitation redeemed after activation",
        as_role(
            db,
            "ajo_app",
            org,
            f"""SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'),
  'fill-late@example.ng', decode('ee', 'hex'), now() + interval '72 hours', null);""",
        ),
        expect="invitations are closed once an Ajo is active",
    )
    return (
        "activates with 4.5 days left on the clock, not on day 5; the first three "
        "joins leave it in enrollment; positions and invitations are both closed "
        "once it is active"
    )


@case("the five-day close cancels an unfilled Ajo and refuses a late join")
def _day_five_close(db: str) -> str:
    """
    BR-001 and EC-050: the window is five days, positions cannot be extended, and
    an unfilled Ajo at the close is cancelled with its collected contributions
    refunded in full.

    Two independent mechanisms are tested, because only one of them exists in the
    code and the other is what makes the rule real without it. `app.close_expired_
    enrollment` is the sweep that would run from a scheduler, and there is no
    scheduler in this codebase -- no pg_cron, no job runner. So the refusal a
    member would hit at day six is asserted through `app.assert_joinable` instead,
    which derives expiry from the clock and therefore does not care whether the
    sweep has been called. The sweep is asserted separately for the transition and
    the reason it records.

    The exact boundary is pinned at five days and one second: the window closed,
    the status was never swept, and the join must still be refused. A `<` where
    `>=` belongs would let that member in.
    """
    org = "close-org@example.ng"
    late = "close-late@example.ng"
    last = "close-last@example.ng"
    ajo = "E5F Close"
    _seed_users(db, "an organizer and two late invitees",
                [("t-close-org", org), ("t-close-late", late),
                 ("t-close-last", last)])
    # The Ajo is inserted already in `enrollment` with a window that closed a
    # second ago. It cannot be *aged* into that state: the transition into
    # enrollment restamps the window, and every later update is refused. That is
    # the immutability guarantee working, and it leaves the expired state
    # reachable only by constructing the row directly -- which is exactly what an
    # Ajo looks like on day six before any sweep has run.
    #
    # The organizer's membership is written with `assert_joinable` disabled,
    # because that trigger would otherwise refuse the organizer's own seat on an
    # Ajo whose window has closed. Disabling it on `ajos` is not an option: that
    # table carries the deferred constraint triggers, and PostgreSQL refuses
    # `ALTER TABLE ... DISABLE TRIGGER` while any are pending.
    must_succeed(
        db,
        "an Ajo whose window closed a second ago and was never swept",
        commit(
            f"""
INSERT INTO ajos (name, organizer_user_id, contribution_amount_kobo, frequency_id,
                  enrollment_opens_at, enrollment_closes_at, total_rounds, currency,
                  status, position_count)
SELECT '{ajo}', u.id, 100000, f.id, now() - interval '5 days' - interval '1 second',
       now() - interval '1 second', 5, 'NGN', 'enrollment', 5
  FROM users u, contribution_frequencies f
 WHERE u.email = '{org}' AND f.code = 'weekly';
-- The organizer's own membership arrives through `materialize_organizer_membership`
-- when the first position is inserted, and `assert_joinable` would refuse it on an
-- Ajo whose window has already closed. So the trigger is off for that one insert.
-- It is not disabled on `ajos`, whose deferred constraint triggers forbid
-- `ALTER TABLE ... DISABLE TRIGGER` outright while any are pending.
ALTER TABLE public.ajo_members DISABLE TRIGGER ajo_members_joinable;
INSERT INTO ajo_positions (ajo_id, position_number)
SELECT a.id, n FROM ajos a, generate_series(1, 5) AS n WHERE a.name = '{ajo}';
ALTER TABLE public.ajo_members ENABLE TRIGGER ajo_members_joinable;
"""
        ),
    )
    if scalar(
        db,
        f"SELECT count(*)::text FROM ajos a JOIN users u ON u.id = a.organizer_user_id"
        f" WHERE a.name = '{ajo}'"
        f" AND EXISTS (SELECT 1 FROM ajo_members m WHERE m.ajo_id = a.id);",
    ) != "1":
        raise Failure(
            "the organizer did not get a membership; the fixture this case sweeps "
            "is not shaped like a real Ajo"
        )
    # Two pending invitations, so the late attempt has a live token. A member
    # cannot redeem twice and a token is spent on use, so one invitee is not
    # enough for "join before the close" followed by "refused after it".
    must_succeed(
        db,
        "inviting two members before the window closed",
        as_role(
            db,
            "ajo_app",
            org,
            f"""SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'),
  '{late}', decode('a1', 'hex'), now() + interval '30 days', null);
SELECT app.create_invitation((SELECT id FROM ajos WHERE name = '{ajo}'),
  '{last}', decode('a2', 'hex'), now() + interval '30 days', null);""",
            commit=True,
        ),
    )
    if scalar(db, f"SELECT status::text FROM ajos WHERE name = '{ajo}';") != "enrollment":
        raise Failure(
            "the Ajo's status changed without the sweep; the unswept case this "
            "case depends on no longer exists"
        )
    must_fail(
        db,
        "a join one second after the window closed",
        as_role(
            db,
            "ajo_app",
            last,
            f"""
SELECT app.join_ajo(decode('a2', 'hex'), '{last}', app.ajo_rules_version());
""",
        ),
        expect="5-day enrollment window for this Ajo closed",
    )
    # The refusal must also be enforced on the membership write itself, so a path
    # that bypasses `app.join_ajo` cannot seat a member in an expired Ajo.
    #
    # `last` rather than the organizer: the organizer already holds a seat, and the
    # unique constraint would report "already exists" before the trigger got a
    # word in. The assertion is on the trigger, so the row has to be otherwise
    # insertable.
    must_fail(
        db,
        "a membership written directly into an expired Ajo",
        commit(
            f"""
INSERT INTO ajo_members (ajo_id, user_id, position_id, status, joined_at)
SELECT a.id, u.id, p.id, 'active', now()
  FROM ajos a, users u, ajo_positions p
 WHERE a.name = '{ajo}' AND u.email = '{last}'
   AND p.ajo_id = a.id AND p.status = 'open';
"""
        ),
        expect="5-day enrollment window for this Ajo closed",
    )

    # The sweep, and the transition it records. The sweep covers the whole table
    # and other cases have left Ajos of their own in it, so every count here is
    # filtered to this Ajo -- `swept=1` would be an assertion about the rest of
    # the suite as much as about this case.
    out = must_succeed(
        db,
        "the expiry sweep",
        f"""
BEGIN;
SELECT 'swept=' || count(*)::text FROM app.close_expired_enrollment()
 WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}');
SELECT 'status=' || status::text FROM ajos WHERE name = '{ajo}';
SELECT 'reason=' || coalesce(cancellation_reason, 'none') FROM ajos WHERE name = '{ajo}';
SELECT 'cancelled_at=' || (cancelled_at IS NOT NULL)::text FROM ajos WHERE name = '{ajo}';
COMMIT;
""",
    )
    if "swept=1" not in out:
        raise Failure(f"the sweep did not find the expired Ajo:\n    {out.strip()[:400]}")
    if "status=cancelled" not in out:
        raise Failure(f"the sweep did not cancel the expired Ajo:\n    {out.strip()[:400]}")
    if "BR-001" not in out:
        raise Failure(f"the cancellation did not record the rule that caused it:\n    {out.strip()[:400]}")
    if "cancelled_at=true" not in out:
        raise Failure(f"cancelled_at was not stamped:\n    {out.strip()[:400]}")

    # Idempotent: a second sweep finds nothing, because `cancelled` is terminal.
    again = must_succeed(
        db,
        "the sweep a second time",
        f"""SELECT 'again=' || count(*)::text FROM app.close_expired_enrollment()
 WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}');""",
    )
    if "again=0" not in again:
        raise Failure(f"the sweep is not idempotent:\n    {again.strip()[:300]}")
    return (
        "a join one second after the window closed is refused from the clock "
        "rather than from a swept status, and the membership write is refused "
        "too; the sweep cancels the unfilled Ajo, records BR-001 and the fill "
        "count, and is idempotent"
    )


@case("a full Ajo still in enrollment is activated by the sweep, not cancelled")
def _sweep_heals_a_full_ajo(db: str) -> str:
    """
    The fill trigger activates on the fill, so a full Ajo in `enrollment` should be
    unreachable. It is reachable in one way that matters: a seat claimed by some
    path that does not insert a membership -- a support tool, a future replacement
    flow, a backfill.

    That is the worst outcome available to a member who did everything right, so
    `app.close_expired_enrollment` re-evaluates fullness instead of trusting the
    status. It is built here by claiming positions directly, with no membership
    rows, which is precisely the state that would otherwise reach day five as a
    full rotation about to be cancelled.
    """
    org = "heal-org@example.ng"
    ajo = "E5G Heal"
    _seed_users(db, "an organizer", [("t-heal-org", org)])
    must_succeed(
        db,
        "a draft, opened",
        as_role(
            db,
            "ajo_app",
            org,
            f"""SELECT app.create_ajo('{ajo}', 'the test', 100000, 'NGN', 'weekly', 5,
                      'friday', DATE '2026-11-06');
SELECT app.open_enrollment((SELECT id FROM ajos WHERE name = '{ajo}'));""",
            commit=True,
        ),
    )
    # Claim every seat without writing a membership, so no trigger can fire.
    must_succeed(
        db,
        "claiming every seat without a membership",
        commit(
            f"""
UPDATE ajo_positions SET status = 'claimed'
 WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}') AND deleted_at IS NULL;
"""
        ),
    )
    out = must_succeed(
        db,
        "the sweep over a full Ajo",
        f"""
BEGIN;
SELECT 'swept=' || count(*)::text FROM app.close_expired_enrollment()
 WHERE ajo_id = (SELECT id FROM ajos WHERE name = '{ajo}');
SELECT 'status=' || status::text FROM ajos WHERE name = '{ajo}';
SELECT 'activated_at=' || (activated_at IS NOT NULL)::text FROM ajos WHERE name = '{ajo}';
COMMIT;
""",
    )
    if "status=active" not in out or "activated_at=true" not in out:
        raise Failure(
            "the sweep cancelled a full Ajo instead of activating it:\n"
            f"    {out.strip()[:400]}"
        )
    return (
        "a full Ajo whose seats were claimed without memberships is activated "
        "rather than cancelled, so no claim path can reach day five as a full "
        "rotation"
    )


@case("a cancelled Ajo records what it owes, and does not pretend it paid")
def _unpaid_vs_owed(db: str) -> str:
    """
    BR-001 promises a refund in full when an unfilled Ajo closes. A refund needs a
    provider call this codebase cannot make yet -- ProvidusUnity has supplied no
    sandbox specifications and no credentials.

    The Ajo is therefore cancelled, which is CANONICAL section 3's only automatic
    edge out of ENROLLMENT, and the amount owed is recorded on the cancellation.
    Nothing is faked: the sweep writes no refund, flips no contribution status and
    calls no provider, so the obligation stays visible and payable rather than
    being marked done. E5-09 settles it.

    The two arms are the ones that must differ. A `pending` contribution is an
    intention, and refunding it would invent a transaction that never happened;
    a `paid` one is money somebody gave us, and the kobo has to be named so that
    whoever performs the refund is not guessing.
    """
    org = "owed-org@example.ng"
    member = "owed-member@example.ng"
    # Two Ajos rather than one rewritten twice: the sweep refuses to touch a
    # terminal status, so the `paid` arm needs an Ajo of its own rather than a
    # second pass over the first one's cancellation.
    ids = {
        "pending": ("00000000-0000-4000-8000-0000000000c5",
                    "00000000-0000-4000-8000-0000000000c6",
                    "00000000-0000-4000-8000-0000000000c7"),
        "paid": ("00000000-0000-4000-8000-0000000000d5",
                 "00000000-0000-4000-8000-0000000000d6",
                 "00000000-0000-4000-8000-0000000000d7"),
    }
    _seed_users(db, "an organizer and a member",
                [("t-owed-org", org), ("t-owed-member", member)])
    # `{{status}}` survives the f-string so `.format()` can fill it in: the SQL is
    # built once and stamped twice, and an unescaped `{status}` would be
    # interpolated while `status` is still unbound.
    setup = f"""
-- Positions, and through them the organizer's membership, are inserted with the
-- membership trigger off. `app.assert_joinable` would otherwise refuse the
-- organizer's own seat on an Ajo whose window has already closed -- which is
-- correct behaviour, and makes the fixture impossible to build through the
-- normal path.
--
-- No trigger is disabled on `ajos` itself: that table carries the deferred
-- constraint triggers for every Ajo invariant, and `ALTER TABLE ... DISABLE
-- TRIGGER` is refused with "cannot ALTER TABLE ajos because it has pending
-- trigger events" while any are queued. Which is the database telling us that
-- disabling triggers mid-transaction is not a thing you do.
--
-- The Ajo is therefore inserted directly into `enrollment` with the expired
-- window it would have six hours after opening. That is the only way to write the
-- state at all, and it is correct that no other way exists.
INSERT INTO ajos (id, name, organizer_user_id, contribution_amount_kobo,
                  frequency_id, enrollment_opens_at, enrollment_closes_at,
                  total_rounds, currency, status, position_count)
SELECT '{{ajo_id}}', '{{name}}', u.id, 1000000, f.id,
       now() - interval '5 days' - interval '1 second',
       now() - interval '1 second', 5, 'NGN', 'enrollment', 5
  FROM users u, contribution_frequencies f
 WHERE u.email = '{org}' AND f.code = 'weekly';
ALTER TABLE public.ajo_members DISABLE TRIGGER ajo_members_joinable;
INSERT INTO ajo_positions (ajo_id, position_number)
SELECT '{{ajo_id}}', n FROM generate_series(1, 5) AS n;
ALTER TABLE public.ajo_members ENABLE TRIGGER ajo_members_joinable;
INSERT INTO rounds (id, ajo_id, round_number, status, due_date, opens_at,
                    closes_at, target_amount_kobo)
SELECT '{{round_id}}', '{{ajo_id}}', 1, 'in_progress', current_date, now(),
       now() + interval '3 days', 1000000;
INSERT INTO contribution_schedules (id, round_id, ajo_id, due_date,
                                    expected_amount_kobo, expected_member_count,
                                    late_cutoff_at)
SELECT '{{schedule_id}}', '{{round_id}}', '{{ajo_id}}', current_date, 1000000, 5,
       now() + interval '5 days';
-- `paid_at`, and nothing else. `contributions_paid_has_timestamp` requires it,
-- and `fee_kobo` / `charged_amount_kobo` are GENERATED ALWAYS, so writing them
-- is refused outright rather than ignored -- the provider confirms the charged
-- amount, the database derives the fee, and a caller may supply neither.
INSERT INTO contributions (schedule_id, member_id, position_id, ajo_id, round_id,
                           user_id, amount_kobo, due_date, status, paid_at)
SELECT '{{schedule_id}}', m.id, m.position_id, m.ajo_id, '{{round_id}}', m.user_id,
       1000000, current_date, '{{status}}',
       CASE WHEN '{{status}}' = 'paid' THEN now() ELSE NULL END
  FROM ajo_members m WHERE m.ajo_id = '{{ajo_id}}';
-- The round aggregates are stored, and a deferred trigger checks them at COMMIT
-- against the contributions. A fixture that writes contributions without
-- restating `fee_collected_kobo` fails on the same COMMIT that inserted them, so
-- it is restated here in the same transaction. This is the trigger's own HINT.
UPDATE rounds r
   SET fee_collected_kobo = COALESCE((
         SELECT sum(c.fee_kobo) FROM contributions c
          WHERE c.round_id = r.id AND c.status = 'paid'
            AND c.superseded_at IS NULL AND c.deleted_at IS NULL), 0),
       base_pool_kobo = COALESCE((
         SELECT sum(c.amount_kobo) FROM contributions c
          WHERE c.round_id = r.id AND c.status = 'paid'
            AND c.superseded_at IS NULL AND c.deleted_at IS NULL), 0)
 WHERE r.id = '{{round_id}}';
"""
    for status, want in (("pending", "cancelled"), ("paid", "cancelled")):
        ajo_id, round_id, schedule_id = ids[status]
        must_succeed(
            db,
            f"a {status} contribution on an expired unfilled Ajo",
            commit(setup.format(ajo_id=ajo_id, round_id=round_id,
                                schedule_id=schedule_id, status=status,
                                name=f"E5H Owed {status}")),
        )
        out = must_succeed(
            db,
            f"the sweep over the {status} Ajo",
            f"""
BEGIN;
SELECT 'swept=' || count(*)::text FROM app.close_expired_enrollment()
 WHERE ajo_id = '{ajo_id}';
SELECT 'status=' || status::text FROM ajos WHERE id = '{ajo_id}';
SELECT 'reason=' || coalesce(cancellation_reason, 'none') FROM ajos WHERE id = '{ajo_id}';
COMMIT;
""",
        )
        if f"status={want}" not in out:
            raise Failure(
                f"a {status} contribution gave {want!r} rather than the expected status:\n"
                f"    {out.strip()[:400]}"
            )
        # The obligation is reported by the sweep's return value, so it is read
        # before the row is committed: after the cancel the Ajo is terminal and a
        # second sweep finds nothing, which is the idempotence asserted elsewhere.
        if status == "paid" and "owed in refunds" not in out:
            raise Failure(
                "the cancellation did not say how much is owed, so whoever performs "
                f"the refund would be guessing:\n    {out.strip()[:400]}"
            )
        if status == "pending" and "owed in refunds" in out:
            raise Failure(
                "a pending contribution was treated as money owed; refunding an "
                f"intention would invent a transaction:\n    {out.strip()[:400]}"
            )
        # And the contribution is untouched: the sweep records an obligation, it
        # does not discharge one.
        left = scalar(
            db,
            f"SELECT status::text FROM contributions WHERE schedule_id = '{schedule_id}';",
        )
        if left != status:
            raise Failure(
                f"the sweep changed the contribution to {left!r}; it must leave the "
                "money alone until E5-09 performs the refund"
            )
    return (
        "an expired unfilled Ajo cancels with nothing owed when it holds only a "
        "pending contribution, and with a paid one it names the kobo owed in the "
        "cancellation reason and leaves the contribution untouched for E5-09"
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

    # The role cases below assert that a non-owner role is bound by RLS. Against
    # the superuser that just applied the migrations they would all pass
    # vacuously, so ownership has to move first.
    bootstrapped = subprocess.run(
        pg.psql(args.db, "-q", "-v", "ON_ERROR_STOP=1", "-f",
                os.path.join(here, "bootstrap_roles.sql")),
        capture_output=True,
        text=True,
    )
    if bootstrapped.returncode != 0:
        print("role bootstrap failed:\n" + bootstrapped.stdout + bootstrapped.stderr)
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
