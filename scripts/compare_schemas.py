#!/usr/bin/env python3
"""
compare_schemas — diff the structure of two databases.

    python3 scripts/compare_schemas.py --a <db> --b <db>
    python3 scripts/compare_schemas.py --a <db> --b <db> --json

Used by `migrate.py --baseline` to decide whether a database that already has
the schema is allowed to be recorded as migrated, and useful on its own for
answering "what actually differs between these two environments".

Only *structure* is compared, never rows, because baselining is about whether a
set of DDL has been applied. Two databases holding entirely different data but
the same shape are correctly considered equal here.

The comparison is a set of normalised catalog signatures, one per object. A
signature is a stable string, so the diff is a set difference and reports
exactly which objects are missing or extra rather than a count that tells you
nothing.

Object types deliberately excluded, and why:

  * `public._t1_decode` and other objects the adoption generator skipped are
    excluded by name, not by pattern, so nothing is hidden by accident.
  * Extensions are skipped: a server-level extension can legitimately exist in
    one database and not another without meaning the schema differs.
  * The `app` schema is compared only for functions. Its ledger tables are
    bookkeeping about which migrations ran, which is precisely the thing being
    brought into existence and cannot be expected to match.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

# Objects the adoption step knowingly left out of migrations/.
IGNORED = {"public._t1_decode"}

QUERIES = {
    "table": """
        select 'table ' || quote_ident(n.nspname) || '.' || quote_ident(c.relname)
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where c.relkind = 'r'
          and n.nspname not in ('pg_catalog', 'information_schema')
    """,
    "column": """
        select 'column ' || quote_ident(n.nspname) || '.' || quote_ident(c.relname)
               || '.' || quote_ident(a.attname) || ' ' || format_type(a.atttypid, a.atttypmod)
               || case when a.attnotnull then ' not null' else '' end
               || coalesce(' default ' || pg_get_expr(d.adbin, d.adrelid), '')
               || case when a.attidentity <> '' then ' identity' else '' end
        from pg_attribute a
        join pg_class c on c.oid = a.attrelid
        join pg_namespace n on n.oid = c.relnamespace
        left join pg_attrdef d on d.adrelid = a.attrelid and d.adnum = a.attnum
        where a.attnum > 0
          and not a.attisdropped
          and c.relkind in ('r', 'p')
          and n.nspname not in ('pg_catalog', 'information_schema')
    """,
    "constraint": """
        select 'constraint ' || quote_ident(n.nspname) || '.' || quote_ident(c.relname)
               || ' ' || con.conname || ' ' || pg_get_constraintdef(con.oid)
               -- pg_get_constraintdef does not render NOT VALID, so a
               -- grandfathered constraint would compare equal to a validated one.
               || ' validated=' || con.convalidated::text
               || ' deferrable=' || con.condeferrable::text
               || ' deferred=' || con.condeferred::text
        from pg_constraint con
        join pg_class c on c.oid = con.conrelid
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname not in ('pg_catalog', 'information_schema')
    """,
    "index": """
        select 'index ' || quote_ident(sn.nspname) || '.' || quote_ident(ic.relname)
               || '.' || quote_ident(ic.relname) || ' on '
               || quote_ident(n.nspname) || '.' || quote_ident(c.relname)
               || ' ' || pg_get_indexdef(i.indexrelid)
        from pg_index i
        join pg_class c on c.oid = i.indrelid
        join pg_namespace n on n.oid = c.relnamespace
        join pg_class ic on ic.oid = i.indexrelid
        join pg_namespace sn on sn.oid = ic.relnamespace
        where n.nspname not in ('pg_catalog', 'information_schema')
          and i.indisprimary = false
    """,
    "trigger": """
        select 'trigger ' || quote_ident(n.nspname) || '.' || quote_ident(c.relname)
               || ' ' || t.tgname || ' ' || pg_get_triggerdef(t.oid)
               -- Not in the rendered definition: a DISABLE'd trigger would
               -- otherwise be indistinguishable from an active one.
               || ' enabled=' || t.tgenabled::text
        from pg_trigger t
        join pg_class c on c.oid = t.tgrelid
        join pg_namespace n on n.oid = c.relnamespace
        where not t.tgisinternal
          and n.nspname not in ('pg_catalog', 'information_schema')
    """,
    "policy": """
        select 'policy ' || quote_ident(schemaname) || '.' || quote_ident(tablename)
               || ' ' || policyname || ' ' || cmd
               || ' roles=[' || roles::text || ']'
               || ' ' || coalesce(qual, '')
               || ' with check ' || coalesce(with_check, '')
        from pg_policies
        where schemaname not in ('pg_catalog', 'information_schema')
    """,
    "function": """
        -- The body is included, not just the signature. A signature-only
        -- fingerprint would call two functions with different logic identical,
        -- which is exactly the mistake this script exists to catch.
        --
        -- Extension members are excluded by extension membership rather than by
        -- schema name. Filtering on `nspname <> 'public'` looks equivalent and
        -- is not: it hides every public function, including ones an adopted
        -- database happens to have that the migrations never created.
        --
        -- Whitespace is not normalised. A cosmetic reformat is reported as a
        -- difference on purpose -- a false mismatch costs a human one look,
        -- while a false match silently baselines a wrong database.
        select 'function ' || quote_ident(n.nspname) || '.' || quote_ident(p.proname)
               || '(' || pg_get_function_identity_arguments(p.oid) || ') '
               || p.prokind::text || ' ' || p.prosrc
        from pg_proc p
        join pg_namespace n on n.oid = p.pronamespace
        where n.nspname not in ('pg_catalog', 'information_schema')
          and p.prokind in ('f', 'p')
          and not exists (
              select 1 from pg_depend d
              where d.classid = 'pg_proc'::regclass
                and d.objid = p.oid
                and d.deptype = 'e'
          )
    """,
    "enum": """
        select 'enum ' || quote_ident(n.nspname) || '.' || quote_ident(t.typname)
               || ' = ' || string_agg(e.enumlabel, ',' order by e.enumsortorder)
        from pg_type t
        join pg_enum e on e.enumtypid = t.oid
        join pg_namespace n on n.oid = t.typnamespace
        where n.nspname not in ('pg_catalog', 'information_schema')
        group by n.nspname, t.typname
    """,
    "extension": """
        select 'extension ' || e.extname || ' ' || e.extversion
        from pg_extension e
        where e.extname not in ('plpgsql')
    """,
    "rowsecurity": """
        select 'rowsecurity ' || quote_ident(n.nspname) || '.' || quote_ident(c.relname)
               || case when c.relrowsecurity then ' enabled' else ' disabled' end
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where c.relkind = 'r'
          and n.nspname not in ('pg_catalog', 'information_schema')
    """,
}


def _query(db: str, kind: str, sql: str) -> set[str]:
    """
    Run one fingerprint query and return its set of signatures.

    A query that fails raises. It does not return an empty set, because an empty
    set is indistinguishable from "these objects genuinely do not exist", and a
    comparator that reports a category it could not read as *identical* will
    happily certify a database as matching when it never looked. That failure
    mode is worse than the bug it hides: the whole point of this script is to
    stop something being recorded as true when it was never checked.
    """
    result = pg.run(pg.psql(db, "-tAF", "\x1f", "-c", sql), check=False)
    if result.returncode != 0:
        raise SystemExit(
            f"fingerprint query for {kind!r} failed against {db!r}. "
            "Refusing to compare: a category that could not be read must not "
            "look like one that matched.\n"
            + (result.stderr or "").strip()
        )
    return {ln.strip() for ln in (result.stdout or "").splitlines() if ln.strip()}


def fingerprint(db: str, ignore: set[str] | None = None) -> dict[str, set[str]]:
    """
    The catalog signature of a database.

    `ignore` holds identifiers to skip, matched as a substring. It exists for
    the migration ledger: the ledger is how one database records what it has
    run, so when comparing a baselined database against a freshly built one the
    ledger is necessarily different and says nothing about whether the schema
    matches.
    """
    skip = set(IGNORED) | set(ignore or ())
    out: dict[str, set[str]] = {}
    for kind, query in QUERIES.items():
        found = _query(db, kind, query)
        out[kind] = {s for s in found if not any(i in s for i in skip)}
    return out


def diff(a: dict[str, set[str]], b: dict[str, set[str]]) -> dict[str, dict[str, list[str]]]:
    return {
        kind: {
            "only_in_a": sorted(a.get(kind, set()) - b.get(kind, set())),
            "only_in_b": sorted(b.get(kind, set()) - a.get(kind, set())),
        }
        for kind in QUERIES
        if a.get(kind, set()) != b.get(kind, set())
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="the database you believe is correct")
    ap.add_argument("--b", required=True, help="the database you are checking")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-show", type=int, default=12)
    ap.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="identifier to skip, matched as a substring; repeatable",
    )
    args = ap.parse_args()

    ignore = set(args.ignore)
    fa, fb = fingerprint(args.a, ignore), fingerprint(args.b, ignore)
    d = diff(fa, fb)

    if args.json:
        print(json.dumps(d, indent=2))
        return 0 if not d else 1

    if not d:
        total = sum(len(v) for v in fa.values())
        print(f"identical: {total} schema objects match across {len(QUERIES)} categories")
        return 0

    for kind, sides in d.items():
        for side, items in sides.items():
            label = "only in A" if side == "only_in_a" else "only in B"
            print(f"\n{kind}: {len(items)} {label}")
            for item in items[: args.max_show]:
                # Fingerprints can span several lines -- a function body, most
                # often. Printed raw, each line looked like its own object and a
                # single leftover function was reported as three.
                shown = item if "\n" in item else "  " + item
                for line in shown.splitlines():
                    print(line if not line.strip() else "  " + line.lstrip())
            if len(items) > args.max_show:
                print(f"  ... and {len(items) - args.max_show} more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
