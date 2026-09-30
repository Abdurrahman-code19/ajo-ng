#!/usr/bin/env python3
"""
seed_reference_data — generate the reference-data migration from a live database.

    python3 scripts/seed_reference_data.py --from-db ajo --out migrations

Reference data is the one category of database content that is genuinely part of
the source. Frequencies, roles, payment channels, document types, dispute reasons
and notification templates are not user data and not derived data: they are
decisions, and a database that disagrees with the repository about them is a
deployment that behaves differently in production than in development.

The adopted schema arrived with all of these tables empty, because schema-only
dumps carry no rows. Without this migration an Ajo cannot even be created,
because `ajos.frequency_id` is NOT NULL and there is no frequency to point at.
That is the failure this file prevents.

Ids are emitted as explicit literals rather than relying on sequence defaults,
because a fixture that depends on a sequence's current value is a fixture that
breaks the next time a row is inserted out of band.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
import sys

# Columns never seeded: they are timestamps or optimistic-locking counters whose
# values are the database's business, not a decision recorded in a migration.
SKIP_COLUMNS = {
    "created_at",
    "updated_at",
    "deleted_at",
    "version",
    "last_modified_at",
}

# (table, comment). Columns are derived from the table, minus SKIP_COLUMNS and
# anything generated, so a column added upstream is picked up automatically
# rather than silently missing from the seed.
TABLES = [
    (
        "contribution_frequencies",
        "How often contributions fall due. Rounds always equal members, so a "
        "frequency sets the gap between rounds rather than the number of them.",
    ),
    (
        "roles",
        "Role codes. Roles are reference data added by migration rather than a "
        "hard-coded enum, so a new role is a row and not an ALTER TYPE.",
    ),
    (
        "payment_channels",
        "Card, bank transfer and the rest, with what each requires of a member.",
    ),
    (
        "document_types",
        "The document vocabulary: what a member can be asked to upload, and what "
        "it is used for.",
    ),
    (
        "verification_check_types",
        "Which kinds of identity check exist, and whether a check must pass "
        "before an Ajo can activate.",
    ),
    (
        "dispute_reasons",
        "The vocabulary support scripts off. A free-text dispute reason produces "
        "a report nobody can group by.",
    ),
    (
        "platform_settings",
        "Platform-wide configuration. Readable by members, writable only by "
        "migration.",
    ),
]


def psql_rows(db: str, sql: str) -> list[list[str]]:
    # -P null= marks an unset field with a token that is checked on the way out,
    # so a NULL stays a NULL instead of collapsing into an empty string.
    out = subprocess.run(
        pg.psql(db, "-tAF", US, "-P", "null=" + NULL_MARK, "-c", sql),
        capture_output=True,
        text=True,
        check=True,
    )
    rows = []
    for line in out.stdout.splitlines():
        if not line.strip():
            continue
        rows.append(line.split(US))
    return rows


def columns_of(db: str, table: str) -> list[str]:
    """Seedable columns for a table, in declaration order."""
    rows = psql_rows(
        db,
        "select column_name from information_schema.columns "
        f"where table_schema='public' and table_name='{table}' "
        "and is_generated = 'NEVER' "
        "and column_name not in (" + ", ".join(quote(c) for c in sorted(SKIP_COLUMNS)) + ") "
        "order by ordinal_position;",
    )
    return [r[0] for r in rows]


# Field separator and null marker.
#
# A NUL byte would be the natural choice for the psql null marker, but an argv
# cannot contain one, so these are printable sentinels instead. US (unit
# separator, \x1f) is used as the field separator because it cannot occur in any
# of this data, and the null marker is a token that is checked against every
# value on the way out, so a row that genuinely contained the literal text
# would be detected rather than silently turned into a NULL.
US = "\x1f"
NULL_MARK = "<<AJO_NULL>>"


def quote(value: str) -> str:
    """
    Render one value as SQL.

    A NULL is distinguishable from an empty string only if psql is told not to
    collapse them, which `-t` does: an unset field arrives as an empty string
    exactly like a genuine ''. Emitting `''` for a NULL bigint is a type error
    and emitting `''` for a NULL text is a silent data corruption, so the
    separator is a control character that cannot occur in the data and NULL is
    emitted as the keyword.
    """
    if value == NULL_MARK:
        return "NULL"
    if value == "":
        return "''"
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-db", default="ajo")
    ap.add_argument("--out", default="migrations/090_reference_data/001_seed.sql")
    args = ap.parse_args()

    body = [
        "-- Reference data.",
        "--",
        f"-- Adopted from the `{args.from_db}` database by",
        "-- scripts/seed_reference_data.py. Do not hand-edit.",
        "--",
        "-- These rows are decisions, not data. They are emitted with explicit ids",
        "-- so a fixture does not depend on a sequence's current value, and",
        "-- `ON CONFLICT DO NOTHING` so the migration is safe to re-run against a",
        "-- database that was seeded by hand during development.",
        "",
        "BEGIN;",
        "",
    ]

    total = 0
    for table, comment in TABLES:
        cols = columns_of(args.from_db, table)
        if not cols:
            raise SystemExit(f"no columns found for {table}")

        select = ", ".join(cols)
        rows = psql_rows(
            args.from_db, f"select {select} from public.{table} order by 1;"
        )
        if not rows:
            print(f"  {table}: 0 rows, skipped")
            continue

        body.append(f"-- {table}: {len(rows)} row(s)")
        body.append(f"-- {comment}")
        values = ",\n  ".join(
            "(" + ", ".join(quote(c) for c in row) + ")" for row in rows
        )
        body.append(
            f"INSERT INTO public.{table} ({select})\n  VALUES\n  {values}\n"
            "ON CONFLICT DO NOTHING;"
        )
        body.append("")
        total += len(rows)
        print(f"  {table}: {len(rows)} rows")

    body.append("COMMIT;")
    body.append("")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(body))

    print(f"\nwrote {args.out} ({total} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
