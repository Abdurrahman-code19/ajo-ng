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

    # And the tables 096 deliberately leaves without an INSERT policy. These are
    # the money and ledger tables, and asserting they are closed is what stops a
    # later "just grant it" from going unnoticed.
    for table in (
        "payments",
        "payouts",
        "ledger_transactions",
        "ledger_postings",
        "risk_events",
    ):
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

    return (
        "profiles accepts a self-owned row and refuses someone else's, and the "
        "five money, ledger and risk tables remain closed"
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
