"""
pg — one way to reach Postgres from these scripts.

The first version of these scripts hardcoded `sudo -n -u postgres psql`, which
works on a developer laptop and nowhere else. It cannot work in CI, where
Postgres is a service container reached over TCP with a password, and it cannot
work on a managed instance where there is no local `postgres` account to
escalate to at all.

So the connection is described by the standard libpq environment variables, and
the local-sudo path is only the fallback for when they are absent. Nothing in
these scripts needs to know which of the two it got.
"""

from __future__ import annotations

import os
import shutil
import subprocess

# Present only when libpq variables are unset, which is the case for a developer
# with a local Postgres and the wrong default credentials.
LOCAL_SUDO = ["sudo", "-n", "-u", "postgres"]


def has_remote_config() -> bool:
    """True when the environment describes a connection we should use as-is."""
    return any(os.environ.get(v) for v in ("PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE"))


def psql(db: str, *args: str) -> list[str]:
    """The argument vector for invoking psql against `db`."""
    if has_remote_config():
        return ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", db, *args]
    return [*LOCAL_SUDO, "psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", db, *args]


def admin(tool: str, *args: str) -> list[str]:
    """The argument vector for createdb/dropdb against the default server."""
    if has_remote_config():
        return [tool, *args]
    return [*LOCAL_SUDO, tool, *args]


def run(argv: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, check=check)


def require_tools() -> None:
    for tool in ("psql",):
        if shutil.which(tool) is None:
            raise SystemExit(
                f"{tool} is not on PATH. Install the PostgreSQL client tools."
            )
