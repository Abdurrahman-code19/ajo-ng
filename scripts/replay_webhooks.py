#!/usr/bin/env python3
"""
replay_webhooks — put provider webhooks that stopped back on the queue.

    python3 scripts/replay_webhooks.py --db ajo --since 2026-10-01
    python3 scripts/replay_webhooks.py --db ajo --since 2026-10-01 \
        --actor ops@example.ng --reason "settlement was down for two hours" --apply

Why this exists, and why it is a script rather than an endpoint. Spec §13.5 says
unprocessed webhooks are replayable so a processing outage is recoverable. The
queue already retries a working system; what it cannot do is notice that a broken
one has been fixed. When settlement was unreachable for two hours, the worker spent
its attempt budget against a database that was down and marked each event `failed`.
Those rows are now permanent, and nothing in the API will look at them again. A
person has to decide that the reason they stopped is gone and say so.

**The default is a dry run.** Running this with no `--apply` prints what would be
re-queued and changes nothing, because the command is short and the wrong window is
easy to type. Re-queuing is not destructive -- `app.settle_provider_event`
re-validates every event against the payment when it runs, so an event that still
does not match simply fails again -- but a replay is still an operator asserting
that a set of failed payments deserve a second look, and that assertion should be
read before it is made.

**`--apply` requires `--reason` and `--actor`.** The reason is recorded on every
audit row, and the actor is resolved to a real user so the trail says who decided
this. There is no anonymous replay from this tool; an unattended recovery job calls
the function directly, where it is recorded as a `system` actor.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def lit(value: str) -> str:
    """A SQL string literal. Doubling the quote is the whole of the escaping."""
    return "'" + value.replace("'", "''") + "'"


def timestamp(raw: str, label: str) -> str:
    """
    Validate an operator's `--since`/`--before` and return a SQL literal.

    Parsed rather than trusted. The values end up in a query, and a date typed by
    hand is the one part of this command that is not a fixed keyword or a resolved
    id; `datetime` is stricter about what a date looks like than the SQL parser is
    about where it can appear.
    """
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        raise SystemExit(
            f"--{label} is not an ISO-8601 date or timestamp: {raw!r}. "
            "Use 2026-10-01 or 2026-10-01T14:30:00+01:00."
        )
    return lit(parsed.isoformat())


def one(db: str, sql: str) -> str:
    out = subprocess.run(
        pg.psql(db, "-tAc", sql), capture_output=True, text=True
    )
    return out.stdout.strip()


def rows(db: str, sql: str) -> list[list[str]]:
    out = subprocess.run(
        pg.psql(db, "-tAF", "|", "-c", sql), capture_output=True, text=True
    )
    if out.returncode != 0:
        raise SystemExit(out.stderr.strip() or "query failed")
    return [line.split("|") for line in out.stdout.strip().splitlines() if line]


def window(since: str | None, before: str | None) -> str:
    clauses = []
    if since:
        clauses.append(f"processed_at >= {since}")
    if before:
        clauses.append(f"processed_at <= {before}")
    return (" AND " + " AND ".join(clauses)) if clauses else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--db", required=True, help="database to act on")
    ap.add_argument("--since", help="only events that stopped at or after this time")
    ap.add_argument("--before", help="only events that stopped at or before this time")
    ap.add_argument("--limit", type=int, default=100, help="at most this many (1-10000)")
    ap.add_argument("--reason", help="why they are being retried; required with --apply")
    ap.add_argument("--actor", help="email or user id to attribute the replay to")
    ap.add_argument("--apply", action="store_true", help="actually re-queue them")
    args = ap.parse_args()
    db = args.db

    if not 1 <= args.limit <= 10000:
        raise SystemExit(f"--limit must be between 1 and 10000, got {args.limit}")

    since = timestamp(args.since, "since") if args.since else None
    before = timestamp(args.before, "before") if args.before else None

    where = (
        "status = 'failed' AND deleted_at IS NULL AND processed_at IS NOT NULL"
        + window(since, before)
    )

    eligible = one(db, f"SELECT count(*) FROM public.webhook_events WHERE {where};")
    if eligible == "0":
        print("No provider events stopped in that window. Nothing to replay.")
        return 0

    candidates = rows(
        db,
        f"""SELECT id, provider, coalesce(provider_reference, '-'),
                   processed_at::text, coalesce(error_detail, '-')
              FROM public.webhook_events
             WHERE {where}
             ORDER BY processed_at, id
             LIMIT {args.limit};""",
    )

    print(f"{eligible} provider event(s) stopped in this window.\n")
    width = max(len(r[1]) for r in candidates)
    for event_id, provider, reference, stopped_at, error in candidates:
        print(f"  {stopped_at[:19]}  {provider:<{width}}  {reference:<20}  {error}")

    if str(args.limit) != eligible:
        print(f"\nShowing {len(candidates)} of {eligible}; raise --limit to see the rest.")

    if not args.apply:
        print(
            "\nDry run. Nothing was changed."
            "\nRe-run with --apply, --actor <email> and --reason \"...\" to re-queue these."
            "\nEvery one is re-validated against its payment when the worker settles it,"
            "\nso an event that still does not match fails again rather than being forced."
        )
        return 0

    if not args.reason or not args.reason.strip():
        raise SystemExit("--apply needs --reason: the audit row has to say why.")
    if not args.actor:
        raise SystemExit("--apply needs --actor: a replay is attributed to a person.")
    if len(args.reason) > 200:
        raise SystemExit("--reason is recorded truncated at 200 characters; shorten it.")

    actor_raw = args.actor.strip()
    if UUID_RE.match(actor_raw):
        actor_id = one(db, f"SELECT id FROM users WHERE id = {lit(actor_raw)};")
    else:
        actor_id = one(
            db,
            f"SELECT id FROM users WHERE email = {lit(actor_raw)} LIMIT 1;",
        )
    if not actor_id:
        raise SystemExit(
            f"--actor {args.actor!r} is not a user in this database. A replay has to be "
            "attributable to somebody; an unattended job calls "
            "app.replay_provider_event directly and is recorded as 'system'."
        )

    # One session, because the GUCs the function reads are session state. The
    # function is granted to ajo_app; whoever runs this needs to be able to read
    # `webhook_events` as well, which for the dry run above is a stronger
    # requirement than the function itself.
    session = "\n".join(
        [
            "SELECT set_config('app.actor_user_id', %s, false);" % lit(actor_id),
            "SELECT set_config('app.actor_type', 'member', false);",
            "SELECT app.replay_provider_event("
            f"{since or 'NULL'}, {before or 'NULL'}, {args.limit}, {lit(args.reason)});",
        ]
    )
    out = subprocess.run(
        pg.psql(args.db, "-tA"), input=session, capture_output=True, text=True
    )
    if out.returncode != 0:
        raise SystemExit(out.stderr.strip() or "the replay failed")

    replayed = out.stdout.strip().splitlines()[-1].strip()
    print(f"\nRe-queued {replayed} event(s) as user {actor_id}.")
    print(
        "The worker will pick them up on its next pass. To see what was done:\n"
        "  SELECT subject_id, after_state->>'reason' AS reason, actor_type\n"
        "    FROM audit_logs WHERE action = 'webhook.replay'\n"
        "   ORDER BY created_at DESC LIMIT 20;"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
