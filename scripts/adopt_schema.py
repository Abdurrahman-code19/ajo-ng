#!/usr/bin/env python3
"""
adopt_schema — generate the initial migration set from a live database.

    python3 scripts/adopt_schema.py --from-db ajo --out migrations

This exists because of a specific situation: a 40-table schema existed in a
Postgres database on the build machine with no SQL source anywhere, and
`TODO.md` still described the tables as unbuilt. Work that exists only in a
database is one `DROP DATABASE` away from being gone, so it was dumped,
verified, and turned into the migrations that become the source of truth from
here on.

The dump is split on pg_dump's own `-- Name: X; Type: Y` markers rather than
with a hand-maintained object list, so every one of the 557 dumped objects
lands in exactly one file and none are silently dropped. Objects are then
assigned to a group by the table they belong to, with a table-less object
falling into the foundation group. The group order is a real dependency order:
`ajos` is referenced by nearly everything, and the ledger references `rounds`,
so the files apply top to bottom and nothing references a table that does not
exist yet.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
import sys

# Objects that must exist before any table, in application order.
FOUNDATION = {"SCHEMA", "EXTENSION", "COMMENT", "TYPE"}

#  is handled specially: it names the object it annotates.

# Object types that reference other tables and therefore cannot be emitted
# alongside the table they belong to: a foreign key may point at a table in a
# later group (`profiles.avatar_document_id` references `documents`, which is
# in the last table group), and triggers and policies call `app.*` helpers
# against a table that may not exist yet. All of them are emitted once every
# table is in place, in a single trailing migration.
DEFERRED = {"FK CONSTRAINT", "INDEX", "TRIGGER", "POLICY", "ROW SECURITY", "VIEW"}

# (directory, [tables], heading) in creation order. The last group holds the
# tables that nothing else depends on.
GROUPS = [
    (
        "000_foundation",
        [],
        "Extensions, the app schema, enums, and the three roles",
    ),
    (
        "010_identity",
        [
            "users",
            "profiles",
            "admins",
            "sessions",
            "device_tokens",
            "roles",
            "role_assignments",
        ],
        "Identity and access",
    ),
    (
        "020_ajo_core",
        [
            "contribution_frequencies",
            "payment_channels",
            "ajos",
            "ajo_positions",
            "ajo_members",
            "rounds",
            "contribution_schedules",
        ],
        "The Ajo lifecycle",
    ),
    (
        "030_money",
        ["contributions", "payments", "fees", "payouts"],
        "Contributions, payments, fees and payouts",
    ),
    (
        "040_ledger",
        ["ledger_transactions", "ledger_postings"],
        "The append-only double-entry ledger",
    ),
    (
        "050_disputes_ops",
        [
            "dispute_reasons",
            "disputes",
            "dispute_messages",
            "dispute_evidence",
            "risk_events",
            "reconciliation_runs",
            "support_tickets",
            "audit_logs",
            "platform_settings",
        ],
        "Disputes, risk, operations and the audit log",
    ),
    (
        "060_notifications_infra",
        [
            "notification_templates",
            "notification_preferences",
            "notifications",
            "idempotency_keys",
            "webhook_events",
            "outbox_events",
            "document_types",
            "documents",
            "invitations",
            "verification_check_types",
            "verification_checks",
        ],
        "Notifications, infrastructure, documents and verification",
    ),
    (
        "070_constraints_and_policies",
        [],
        "Foreign keys, indexes, triggers, and row-level security",
    ),
]

SECTION_RE = re.compile(r"^-- Name: (?P<name>.*?); Type: (?P<type>[A-Za-z ]+); Schema:")

# Objects deliberately not adopted.
#
# `_t1_decode(uuid)` is a leftover helper from an earlier UUIDv7 test that
# decoded the embedded millisecond timestamp. Nothing references it, and §9.2
# requires that functions live in `app` and never in `public`, so adopting it
# would import a real spec violation. It is listed here rather than silently
# dropped so the exclusion is visible in review.
EXCLUDE = {"_t1_decode"}


def _comment_group(name: str, group_of: dict[str, str], table_set: set[str]) -> str:
    """
    The group a COMMENT belongs to, following the object it annotates.

    pg_dump names a column comment "TABLE public.users.email", so the second
    field is the table in every case.
    """
    # pg_dump names a column comment "TABLE public.users.email" and a table
    # comment "TABLE public.users", so the table is the first dotted component
    # after the leading keyword in both cases.
    parts = name.split()
    # "CONSTRAINT <name> ON <table>" documents a constraint, which is only
    # created in the deferred phase.
    if len(parts) >= 4 and parts[0] == "CONSTRAINT" and parts[2] == "ON":
        object_name = parts[3].removeprefix("public.").split(".")[0]
        if object_name in table_set:
            return "070_constraints_and_policies"
    # "TRIGGER <name> ON <table>" documents a trigger, which is created in
    # the deferred phase alongside every other trigger.
    if len(parts) >= 4 and parts[0] == "TRIGGER" and parts[2] == "ON":
        return "070_constraints_and_policies"
    if parts and parts[0] in ("TABLE", "COLUMN"):
        for token in parts[1:]:
            object_name = token.removeprefix("public.").split(".")[0]
            if object_name in table_set:
                return group_of[object_name]
    if parts and parts[0] == "VIEW":
        return "070_constraints_and_policies"
    # Extension and schema comments have nothing to be created after.
    return "000_foundation"


def _excluded(name: str) -> bool:
    return any(name == e or name.startswith(f"{e}(") for e in EXCLUDE)


def psql_scalar(db: str, sql: str) -> str:
    out = subprocess.run(
        pg.psql(db, "-tAc", sql),
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def dump(db: str) -> str:
    out = subprocess.run(
        pg.admin("pg_dump", "--schema-only", "--no-owner", "--no-privileges", db),
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout


def split_sections(schema: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Return (preamble, [(name, type, sql), ...]) in dump order."""
    lines = schema.splitlines()

    preamble: list[str] = []
    sections: list[tuple[str, str, list[str]]] = []
    current: tuple[str, str, list[str]] | None = None

    for line in lines:
        # pg_dump >= 16.10 emits \restrict/\unrestrict tokens tied to the
        # server version. They are a dump-runner guard, not schema.
        if line.startswith("\\restrict") or line.startswith("\\unrestrict"):
            continue

        match = SECTION_RE.match(line)
        if match:
            if current is not None:
                sections.append(current)
            current = (match.group("name"), match.group("type").strip(), [])
            continue

        if current is None:
            preamble.append(line)
        else:
            current[2].append(line)

    if current is not None:
        sections.append(current)

    return preamble, sections


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-db", default="ajo")
    ap.add_argument("--out", default="migrations")
    ap.add_argument(
        "--tables",
        default="users,profiles,admins,sessions,device_tokens,roles,role_assignments,"
        "contribution_frequencies,payment_channels,ajos,ajo_positions,ajo_members,rounds,"
        "contribution_schedules,contributions,payments,fees,payouts,ledger_transactions,"
        "ledger_postings,dispute_reasons,disputes,dispute_messages,dispute_evidence,"
        "risk_events,reconciliation_runs,support_tickets,audit_logs,platform_settings,"
        "notification_templates,notification_preferences,notifications,idempotency_keys,"
        "webhook_events,outbox_events,document_types,documents,invitations,"
        "verification_check_types,verification_checks",
        help="comma-separated public tables that must all be accounted for",
    )
    args = ap.parse_args()

    schema = dump(args.from_db)
    preamble, sections = split_sections(schema)

    table_set = {t.strip() for t in args.tables.split(",") if t.strip()}
    group_of: dict[str, str] = {}
    for directory, tables, _heading in GROUPS:
        for table in tables:
            if table not in table_set:
                raise SystemExit(f"group {directory} lists unknown table {table!r}")
            if table in group_of:
                raise SystemExit(f"table {table!r} appears in two groups")
            group_of[table] = directory

    missing = table_set - set(group_of)
    if missing:
        raise SystemExit(f"tables not assigned to any group: {sorted(missing)}")

    buckets: dict[str, list[tuple[str, str, str]]] = {g[0]: [] for g in GROUPS}
    unassigned: list[str] = []

    excluded = 0
    for name, obj_type, body in sections:
        sql = "\n".join(body).strip()
        if not sql:
            continue
        if _excluded(name):
            excluded += 1
            continue

        target = None
        if obj_type == "COMMENT":
            # A COMMENT names the object it annotates, e.g.
            # "COMMENT ON TABLE public.users" or
            # "COMMENT ON VIEW app.policy_coverage", so it has to be emitted
            # with that object rather than with every other comment. These
            # comments are the schema's documentation and dropping them would
            # quietly lose the reasoning behind the DDL.
            target = _comment_group(name, group_of, table_set)
        elif obj_type in FOUNDATION:
            target = "000_foundation"
        elif obj_type in DEFERRED:
            target = "070_constraints_and_policies"
        elif obj_type == "VIEW":
            # The policy_coverage view in §9.6 makes RLS coverage checkable
            # rather than asserted, and it enumerates every table, so it has
            # to be created after they all exist.
            target = "070_constraints_and_policies"
        elif name in group_of:
            # ROW SECURITY, POLICY and TABLE objects are named after the bare
            # table, with no prefix.
            target = group_of[name]
        elif obj_type == "FUNCTION" and re.match(r"^[a-z_][a-z_0-9]*\(", name):
            # Every app.* helper is SECURITY DEFINER and is called by policies
            # and triggers, so all of them must exist before the tables that
            # use them. `_t1_decode` is a leftover probe function from the
            # testcontainers encoding probe and is dropped below.
            target = "000_foundation"
        else:
            for table in sorted(table_set, key=len, reverse=True):
                if name.startswith(f"{table}_") or name.startswith(f"{table} "):
                    target = group_of[table]
                    break
        if target is None:
            unassigned.append(f"{name} ({obj_type})")
            continue
        buckets[target].append((name, obj_type, sql))

    if unassigned:
        raise SystemExit(
            "could not attribute these objects to a group:\n  "
            + "\n  ".join(unassigned)
        )

    os.makedirs(args.out, exist_ok=True)
    total_objects = 0

    for directory, tables, heading in GROUPS:
        entries = buckets[directory]
        if not entries and directory != "000_foundation":
            continue

        path = os.path.join(args.out, directory, "001_adopt.sql")
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Within the deferred phase the order is load-bearing: RLS is enabled
        # before any policy is attached to it, and both come after the
        # tables exist.
        ORDER = {
            "FK CONSTRAINT": 0,
            "CONSTRAINT": 1,
            "INDEX": 2,
            "ROW SECURITY": 3,
            "TRIGGER": 4,
            "POLICY": 5,
            "VIEW": 6,
        }
        if directory == "070_constraints_and_policies":
            entries.sort(key=lambda e: (ORDER.get(e[1], 99), e[0]))

        body = [
            f"-- {heading}",
            "--",
            f"-- Adopted from the `{args.from_db}` database, which held this schema with no",
            "-- SQL source in version control. Generated by scripts/adopt_schema.py;",
            "-- do not hand-edit, re-run the generator and commit the result.",
            "--",
            f"-- {len(entries)} object(s)."
            + (f" Tables: {', '.join(tables)}." if tables else ""),
            "",
            "SET check_function_bodies = false;",
            "",
        ]
        for _name, _type, sql in entries:
            # The migration ledger creates `app` before anything else runs, so
            # the dump's plain CREATE SCHEMA would collide on a second apply.
            sql = sql.replace("CREATE SCHEMA app;", "CREATE SCHEMA IF NOT EXISTS app;")
            body.append(sql)
            body.append("")

        content = "\n".join(body)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

        total_objects += len(entries)
        digest = hashlib.sha256(content.encode()).hexdigest()[:12]
        print(
            f"wrote {path}  ({len(entries):>3} objects, "
            f"{len(tables):>2} tables, sha {digest})"
        )

    print()
    print(f"adopted  {total_objects} objects across {len(GROUPS)} migrations")
    print(f"dumped   {len(sections)} objects")
    if excluded:
        print(f"excluded {excluded} object(s): {', '.join(sorted(EXCLUDE))}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
