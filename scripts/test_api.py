#!/usr/bin/env python3
"""
test_api — build a database from the migrations, then run the API's integration
tests against it as the real application role.

    python3 scripts/test_api.py               # build, test, tear down
    python3 scripts/test_api.py --keep        # leave the database behind
    python3 scripts/test_api.py --no-redis    # skip the rate-limit cases

Why a separate harness rather than a fixture inside the TypeScript tests. The
central claim of the API is that the database constrains it, and that claim is
only meaningful against a database that was built the way production builds one:
from the migration files, then bootstrapped so the roles exist. A test that
connects to whatever happens to be on port 5432 is testing the wrong database if
it is the wrong one, and would still pass.

`--no-redis` exists because the rate limit is the only thing bounding the signup
write path, and a test that quietly skipped the cases covering it would leave the
most load-bearing part of the endpoint unverified. So the skip is explicit and
loud, and CI never passes it.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DB = "ajo_api_test"
# A fixed password, and the one the migration suite's role bootstrap creates the
# login role with. It is a test database that is dropped on exit, and the role
# is NOSUPERUSER NOBYPASSRLS, so a leak of this string buys nothing on a real
# server.
TEST_ROLE_PASSWORD = "local-dev-only"

# A second login, used by the tests to look at rows the application role cannot
# see -- to confirm a password hash was written, or to expire a token, neither of
# which the API is supposed to be able to do.
#
# It is a superuser because reading a table with FORCE ROW LEVEL SECURITY needs
# one, and that is the entire point of it: the tests need the view the API is
# denied. It exists only inside a database that this script drops on exit, and
# its password buys nothing anywhere else.
TEST_ADMIN_ROLE = "ajo_api_test_admin"
TEST_ADMIN_PASSWORD = "local-dev-only-admin"


def build_database(db: str) -> bool:
    print(f"building {db} from the migration files only")
    subprocess.run(pg.admin("dropdb", "--if-exists", db), check=True)
    subprocess.run(pg.admin("createdb", db), check=True)

    applied = subprocess.run(
        [sys.executable, os.path.join(HERE, "migrate.py"), "--db", db],
        capture_output=True,
        text=True,
    )
    if applied.returncode != 0:
        print("migrations failed to apply:\n" + applied.stdout + applied.stderr)
        return False

    # The role bootstrap has to run before anything else: the tests connect as
    # `ajo_api`, which does not exist until this has been run, and the whole
    # point of using that role is that it is NOT the superuser that just applied
    # the migrations. Against a superuser every RLS assertion below would pass
    # vacuously.
    bootstrapped = subprocess.run(
        pg.psql(db, "-f", os.path.join(HERE, "bootstrap_roles.sql")),
        capture_output=True,
        text=True,
    )
    if bootstrapped.returncode != 0:
        print("role bootstrap failed:\n" + bootstrapped.stdout + bootstrapped.stderr)
        return False

    # A login the Node tests can use to read what the application role cannot.
    # Created here rather than by the bootstrap, because it has no business in a
    # production role list, and the database it lives in is dropped on exit.
    admin = subprocess.run(
        pg.psql(
            db,
            "-c",
            f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles "
            f"WHERE rolname = '{TEST_ADMIN_ROLE}') THEN "
            f"CREATE ROLE {TEST_ADMIN_ROLE} LOGIN SUPERUSER "
            f"PASSWORD '{TEST_ADMIN_PASSWORD}'; END IF; END $$;",
        ),
        capture_output=True,
        text=True,
    )
    if admin.returncode != 0:
        print("could not create the test admin role:\n" + admin.stdout + admin.stderr)
        return False
    return True


def redis_available(url: str) -> bool:
    """
    True when the configured Redis answers PING.

    Done with a bare socket speaking RESP rather than the `redis` package, so
    that running this suite needs nothing installed beyond what the rest of the
    repository already needs. An availability probe is not worth a dependency
    that only exists here.

    The request is a real RESP array rather than Redis's old telnet-style inline
    command, because inline commands were removed in Redis 2.0 and answering
    such a request with an error would have read as "Redis is down".
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 6379
    try:
        with socket.create_connection((host, port), timeout=2) as sock:
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            reply = sock.recv(64)
        return reply.startswith(b"+PONG")
    except OSError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument(
        "--no-redis",
        action="store_true",
        help="run without Redis; the rate-limit cases will be reported as skipped",
    )
    args = ap.parse_args()

    pg.require_tools()

    if not build_database(args.db):
        return 1

    redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")
    have_redis = False if args.no_redis else redis_available(redis_url)
    if args.no_redis:
        print("redis: skipped at the caller's request")
    elif not have_redis:
        print(
            f"redis: not reachable at {redis_url}.\n"
            "       The registration rate limit is the only thing bounding the\n"
            "       signup write path, so its cases will not run. Start Redis, or\n"
            "       pass --no-redis to accept the gap deliberately."
        )
    else:
        print(f"redis: reachable at {redis_url}")

    # `--force`, and before the API's own compile, because the API tests import
    # `@ajo/domain` as a *built* package. Building only the API leaves domain's
    # `dist/` at whatever it was, so a change to the provider seam can sit on disk
    # unbuilt and every case below passes against the old code -- which is how a
    # test for an adapter behaviour passed against an adapter that did not have it.
    built = subprocess.run(
        ["npx", "tsc", "--build", "--force"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if built.returncode != 0:
        print("the packages do not build:\n" + built.stdout + built.stderr)
        return 1

    compiled = subprocess.run(
        ["npx", "tsc", "-p", "packages/api/tsconfig.test.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if compiled.returncode != 0:
        print("the API does not compile:\n" + compiled.stdout + compiled.stderr)
        return 1

    env = dict(os.environ)
    # The API's own configuration names are used here rather than new ones, so
    # the tests exercise the same path `loadConfig` takes at startup. Pointed at
    # the throwaway database, not at whatever is on the developer's port.
    env["PGHOST"] = env.get("PGHOST", "127.0.0.1")
    env["PGPORT"] = env.get("PGPORT", "5432")
    env["PGDATABASE"] = args.db
    env["PGUSER"] = "ajo_api"
    env["PGPASSWORD"] = TEST_ROLE_PASSWORD
    # The tests also need to see what the application role is denied. Kept in
    # separate variables so the application role and the observer are never
    # confused for one another.
    env["PGADMINUSER"] = TEST_ADMIN_ROLE
    env["PGADMINPASSWORD"] = TEST_ADMIN_PASSWORD
    env["REDIS_URL"] = redis_url
    env["REDIS_AVAILABLE"] = "1" if have_redis else "0"
    env["NODE_ENV"] = "test"

    tested = subprocess.run(
        [
            "node",
            "--test",
            "--test-reporter=spec",
            "packages/api/build-test/test/",
        ],
        cwd=ROOT,
        env=env,
    )

    if not args.keep:
        subprocess.run(pg.admin("dropdb", "--if-exists", args.db), check=False)
        # Roles are cluster-level, so dropping the database does not drop the
        # observer. Left behind, it turns up in `\du` on every later run and
        # eventually collides with a real role of the same name. Dropping it also
        # means the next run's "create it" branch actually runs, so the creation
        # path is exercised every time rather than only on a first run.
        subprocess.run(
            pg.psql("postgres", "-c", f"DROP ROLE IF EXISTS {TEST_ADMIN_ROLE};"),
            check=False,
        )

    if not have_redis and not args.no_redis:
        print()
        print("NOTE: rate-limit cases did not run (no Redis). Not a pass.")
    return tested.returncode


if __name__ == "__main__":
    raise SystemExit(main())
