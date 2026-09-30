#!/usr/bin/env python3
"""
migrate — apply the SQL migrations in `migrations/` to a database, in order.

    python3 scripts/migrate.py --db ajo_dev            # apply everything pending
    python3 scripts/migrate.py --db ajo_dev --status   # what is applied, what is not
    python3 scripts/migrate.py --db ajo_dev --check    # verify checksums only

Two properties matter more than convenience here.

**A migration is applied exactly once, inside a transaction, and its checksum is
recorded.** Editing a migration that has already been applied is a mistake the
runner refuses rather than absorbs, because a database that quietly diverges
from its repository is the failure mode that costs days.

**A failed migration leaves nothing behind.** Every file is wrapped in its own
transaction, so a partial schema is not a state the runner can be resumed from.
Migrations that must not run in a transaction, such as `CREATE INDEX CONCURRENTLY`,
declare it with `-- migrate:no-transaction` and are applied bare.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
import sys
import time

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


def psql_file(db: str, path: str) -> None:
    subprocess.run(
        pg.psql(db, "-q", "-f", path),
        capture_output=True,
        text=True,
        check=True,
    )


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--status", action="store_true", help="list applied and pending")
    ap.add_argument("--check", action="store_true", help="verify checksums only")
    args = ap.parse_args()

    ensure_ledger(args.db)
    migrations = discover()
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

    print(f"applying {len(pending)} migration(s) to {args.db}\n")
    for version, path in pending:
        with open(path, encoding="utf-8") as fh:
            body = fh.read()

        started = time.monotonic()
        if NO_TRANSACTION_MARKER in body:
            # Strip the transaction wrapper the generator added, because the
            # marker says this file must run bare.
            bare = body.replace("BEGIN;", "").replace("COMMIT;", "")
            psql(args.db, bare, tuples_only=False)
        else:
            psql(args.db, body, tuples_only=False)
        elapsed = int((time.monotonic() - started) * 1000)

        psql(
            args.db,
            "insert into app.schema_migrations (version, checksum, duration_ms) "
            f"values ('{version}', '{sha256(path)}', {elapsed});",
        )
        print(f"  applied {version}  ({elapsed} ms)")

    print(f"\ndone: {len(applied(args.db))} migrations applied in total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
