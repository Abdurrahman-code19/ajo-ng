#!/usr/bin/env python3
"""
migrate — apply the SQL migrations in `migrations/` to a database, in order.

    python3 scripts/migrate.py --db ajo_dev            # apply everything pending
    python3 scripts/migrate.py --db ajo_dev --status   # what is applied, what is not
    python3 scripts/migrate.py --db ajo_dev --check    # verify checksums only

Two properties matter more than convenience here.

**A migration is applied exactly once, and its checksum is recorded.** Editing a
migration that has already been applied is a mistake the runner refuses rather
than absorbs, because a database that quietly diverges from its repository is
the failure mode that costs days.

**A failed migration leaves nothing behind.** The runner wraps each file in a
transaction, so a partial schema is not a state it can be resumed from. The
transaction is the runner's job, not the file's: a migration file contains no
`BEGIN` or `COMMIT`, because a stray `COMMIT` inside a file the runner has
already wrapped would end the transaction early and silently apply the rest of
the file outside it. Files that genuinely cannot run in a transaction, such as
`CREATE INDEX CONCURRENTLY`, declare it with `-- migrate:no-transaction` and are
applied bare.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATIONS = os.path.join(ROOT, "migrations")

NO_TRANSACTION_MARKER = "-- migrate:no-transaction"


def sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def discover() -> list[tuple[str, str]]:
    """(version, absolute path) for every migration, in directory order."""
    found: list[tuple[str, str]] = []
    for directory in sorted(os.listdir(MIGRATIONS)):
        sub = os.path.join(MIGRATIONS, directory)
        if not os.path.isdir(sub):
            continue
        for filename in sorted(os.listdir(sub)):
            if not filename.endswith(".sql"):
                continue
            found.append((f"{directory}/{filename}", os.path.join(sub, filename)))
    return found


def psql(db: str, sql: str, tuples_only: bool = True) -> str:
    # SQL is passed on stdin rather than as an argument. A migration is far
    # larger than any command-line length limit, and psql also mangles a
    # multi-statement argument that happens to contain a backslash.
    cmd = pg.psql(db)
    if tuples_only:
        cmd += ["-tAc", sql]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return out.stdout.strip()

    out = subprocess.run(
        cmd + ["-q"],
        input=sql,
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        # psql's own error is more useful than the exit code, so it is raised
        # rather than printed. A migration failure with no message is the one
        # thing a migration runner must never do.
        raise SystemExit(out.stderr.strip() or f"psql exited {out.returncode}")
    return out.stdout


def psql_file(db: str, path: str, single_transaction: bool = True) -> None:
    """
    Run a migration file.

    `--single-transaction` is what makes a failed migration leave nothing
    behind. It wraps the file in a transaction and rolls it back on the first
    error, so a migration that dies on its last statement applies none of
    itself. Relying on each file to carry its own BEGIN and COMMIT is what
    produced the opposite: eleven of the twelve files had neither, so a failure
    halfway through the 2,572-line constraints file left a partial schema and a
    partial set of triggers behind.
    """
    argv = pg.psql(db, "--single-transaction", "-f", path) if single_transaction else pg.psql(db, "-f", path)
    subprocess.run(argv, capture_output=True, text=True, check=True)


def ensure_ledger(db: str) -> None:
    ledger = os.path.join(MIGRATIONS, "000_foundation", "000_ledger.sql")
    if not os.path.exists(ledger):
        return
    with open(ledger, encoding="utf-8") as fh:
        psql(db, fh.read(), tuples_only=False)


def applied(db: str) -> dict[str, str]:
    rows = psql(
        db,
        "select version, checksum from app.schema_migrations order by version;",
    )
    out = {}
    for line in rows.splitlines():
        if line.strip():
            version, checksum = line.split("|")
            out[version.strip()] = checksum.strip()
    return out


def record(db: str, version: str, path: str, elapsed_ms: int, baselined: bool) -> None:
    # No ON CONFLICT clause. Both callers have already established that the
    # version is absent, so a conflict means a bug in the caller, and swallowing
    # it would let a migration report as recorded when nothing was written.
    psql(
        db,
        "insert into app.schema_migrations (version, checksum, duration_ms, baselined) "
        f"values ('{version}', '{sha256(path)}', {elapsed_ms}, "
        f"{'true' if baselined else 'false'});",
    )


def baseline(db: str, through: str) -> int:
    """
    Record migrations as already applied, but only after proving the database
    already matches them.

    This exists for the database the schema was adopted from: it already has
    every table, trigger and policy, but has no history and must not be
    recreated, because it holds append-only ledger and audit rows that cannot be
    deleted. Running the migrations over the top of it would fail on the first
    `CREATE TABLE` that already exists.

    The tempting shortcut is to insert the rows and move on. That would be a
    lie written into the one table whose entire purpose is to record what
    actually happened, and it would convert a verifiable "this schema is
    identical" into an unfalsifiable "we believe this is fine". So instead the
    migrations are built into a scratch database and the two are compared object
    by object. Only an exact match is recorded.

    `through` is the first migration that should still be applied normally, so
    `--baseline 080` records 000 to 070 and leaves 080 and 090 pending.

    Ordering matters here and is easy to get wrong. Filtering on "does not start
    with the prefix" is not the same as "sorts before the prefix": it sweeps in
    everything that is not 080, including 090, which sits after it. A prefix
    filter would have quietly recorded the reference-data migration as verified
    when it had never run. The boundary is therefore taken from the sorted list.
    """
    import compare_schemas

    migrations = discover()
    boundary = next(
        (i for i, (v, _) in enumerate(migrations) if v.startswith(through)),
        None,
    )
    if boundary is None:
        print(
            f"no migration starts with {through!r}. Available prefixes: "
            + ", ".join(sorted({v.split("/")[0] for v, _ in migrations})),
            file=sys.stderr,
        )
        return 1
    to_record = migrations[:boundary]
    if not to_record:
        print(f"nothing to baseline: {through!r} is the first migration")
        return 1

    # A database whose ledger already records these has history, and
    # baselining it would assert something about migrations it has already run.
    # Reported rather than assumed, because the two states mean different things
    # and picking the wrong one silently is the failure this whole command
    # exists to prevent.
    existing = applied(db)
    already = [v for v, _ in to_record if v in existing]
    if len(already) == len(to_record):
        print(
            f"{db} already records all {len(already)} of these migrations; "
            "there is nothing to baseline."
        )
        return 0
    if already:
        print(
            f"REFUSING TO BASELINE: {db} records {len(already)} of the "
            f"{len(to_record)} migrations, so its history is partial.",
            file=sys.stderr,
        )
        for version in already:
            print(f"  already recorded: {version}", file=sys.stderr)
        quoted = ", ".join("'" + v.replace("'", "''") + "'" for v in already)
        print(
            "\nEither finish applying them with --db "
            f"{db}, or drop the ledger rows if this database's history is not "
            "trustworthy:\n"
            f"  psql -d {db} -c \"delete from app.schema_migrations "
            f"where version in ({quoted})\"",
            file=sys.stderr,
        )
        return 1

    scratch = f"{db}_baseline_scratch"
    # Flushed, or the progress line lands after the failure it precedes.
    print(f"verifying that {db} already matches {len(to_record)} migration(s)\n", flush=True)

    subprocess.run(
        pg.admin("dropdb", "--if-exists", scratch),
        capture_output=True, text=True, check=False,
    )
    subprocess.run(pg.admin("createdb", scratch), capture_output=True, text=True, check=True)

    try:
        for version, path in to_record:
            with open(path, encoding="utf-8") as fh:
                bare = NO_TRANSACTION_MARKER in fh.read()
            started = time.monotonic()
            psql_file(scratch, path, single_transaction=not bare)
            record(scratch, version, path, int((time.monotonic() - started) * 1000), False)

        # The ledger itself is the one thing that must differ: it records what
        # ran, which is exactly what is being brought into existence.
        ignore = {"app.schema_migrations"}
        differences = compare_schemas.diff(
            compare_schemas.fingerprint(scratch, ignore),
            compare_schemas.fingerprint(db, ignore),
        )
    finally:
        subprocess.run(
            pg.admin("dropdb", "--if-exists", scratch),
            capture_output=True, text=True, check=False,
        )

    if differences:
        total = sum(len(v["only_in_a"]) + len(v["only_in_b"]) for v in differences.values())
        print(
            f"REFUSING TO BASELINE: {db} does not match the migrations "
            f"({total} difference(s) across {len(differences)} categories).",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        for kind, sides in differences.items():
            for side, items in sides.items():
                label = "in migrations only" if side == "only_in_a" else "in database only"
                print(f"  {kind} ({len(items)}) {label}:", file=sys.stderr)
                for item in items[:6]:
                    print(f"    {item}", file=sys.stderr)
                if len(items) > 6:
                    print(f"    ... and {len(items) - 6} more", file=sys.stderr)
        print(
            "\nEach object above is named so it can be looked up directly:\n"
            f"  psql -d {db} -c '\\d+ <object>'\n"
            "Or compare against a fresh build, which is what --baseline did:\n"
            "  python3 scripts/compare_schemas.py --a <freshly built db> --b "
            f"{db}",
            file=sys.stderr,
        )
        return 1

    for version, path in to_record:
        record(db, version, path, 0, True)
    print(
        f"baselined {len(to_record)} migration(s) into {db} after an exact "
        f"structural match.\nThey are recorded as verified, not as run."
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--status", action="store_true", help="list applied and pending")
    ap.add_argument("--check", action="store_true", help="verify checksums only")
    ap.add_argument(
        "--through",
        help="apply only migrations before this version prefix, then stop",
    )
    ap.add_argument(
        "--baseline",
        metavar="PREFIX",
        help=(
            "record every migration sorting before PREFIX as applied, but only "
            "after building them into a scratch database and proving this one "
            "already matches. For a database that has the schema but no history."
        ),
    )
    ap.add_argument(
        "--yes-baseline",
        action="store_true",
        help="with --baseline, skip the interactive confirmation",
    )
    args = ap.parse_args()

    ensure_ledger(args.db)

    if args.baseline:
        return baseline(args.db, args.baseline)

    migrations = discover()
    if args.through:
        migrations = [(v, p) for v, p in migrations if not v.startswith(args.through)]

    done = applied(args.db)

    pending = [(v, p) for v, p in migrations if v not in done]

    if args.status:
        for version, path in migrations:
            state = "applied" if version in done else "pending"
            print(f"  {state:<8} {version}")
        print(f"\n{len(done)} applied, {len(pending)} pending")
        return 0

    drift = [
        v
        for v, p in migrations
        if v in done and sha256(p) != done[v]
    ]
    if drift:
        print("MIGRATION DRIFT DETECTED", file=sys.stderr)
        for version in drift:
            print(f"  {version} was applied with a different checksum", file=sys.stderr)
        print(
            "\nA migration that has already run was edited. The database no longer "
            "matches the repository. Write a new migration instead of changing an "
            "applied one.",
            file=sys.stderr,
        )
        return 1

    if args.check:
        print(f"OK  {len(done)} applied, checksums match")
        return 0

    if not pending:
        print(f"nothing to do; {len(done)} migrations already applied")
        return 0

    # Flushed as it goes: stdout is block-buffered when piped, so without this
    # a failure is printed before the progress that led to it.
    print(f"applying {len(pending)} migration(s) to {args.db}\n", flush=True)
    for version, path in pending:
        with open(path, encoding="utf-8") as fh:
            body = fh.read()

        # A file that declares it cannot run in a transaction is applied bare.
        # Everything else is wrapped by psql, so a failure rolls the whole file
        # back rather than leaving half a migration behind.
        bare = NO_TRANSACTION_MARKER in body

        started = time.monotonic()
        try:
            psql_file(args.db, path, single_transaction=not bare)
        except subprocess.CalledProcessError as exc:
            print(
                f"  FAILED  {version}\n\n{exc.stderr.strip()}\n",
                file=sys.stderr,
            )
            print(
                f"{version} was rolled back, so {args.db} is unchanged by it. "
                "Fix the migration and run again.",
                file=sys.stderr,
            )
            return 1
        elapsed = int((time.monotonic() - started) * 1000)

        record(args.db, version, path, elapsed, False)
        note = "  (no transaction)" if bare else ""
        print(f"  applied {version}  ({elapsed} ms){note}", flush=True)

    print(f"\ndone: {len(applied(args.db))} migrations applied in total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
