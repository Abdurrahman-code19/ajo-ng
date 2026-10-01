# Deployment

How to get this running somewhere that is not a laptop, and what has to be true
before it is allowed to.

Nothing here is provider-specific. Where a choice had to be made it is written
as a choice, with the reasoning, rather than hard-coded.

## Order of operations

The sequence is not interchangeable.

1. **Migrate the database.** `scripts/migrate.py` then `scripts/bootstrap_roles.sql`.
2. **Set the environment.** Every variable in the table below. No defaults for
   credentials.
3. **Start the API.** It refuses to start if the database is unreachable, so a
   bad migration surfaces as a failed deploy rather than 500s under traffic.
4. **Point the proxy at it.**

Migrations first, because the API version being deployed expects a schema that
the previous version also understands. Rolling back the API after a migration is
safe; the reverse is not.

```sh
python3 scripts/migrate.py --db "$PGDATABASE"
psql -d "$PGDATABASE" -v ON_ERROR_STOP=1 -f scripts/bootstrap_roles.sql
```

`bootstrap_roles.sql` is idempotent and must run after every migration, not once.
Migrations create functions owned by the migration role; the bootstrap moves that
ownership to `ajo_migrator` and grants execution, which is what makes a
`SECURITY DEFINER` function work for a non-superuser caller.

## Environment

| Variable | Required | Notes |
| --- | --- | --- |
| `NODE_ENV` | in production | `production` selects the mail relay and enables the gate that refuses to log tokens |
| `PGHOST` `PGPORT` `PGDATABASE` | defaults to localhost/5432/ajo | |
| `PGUSER` `PGPASSWORD` | **required** | The `ajo_api` login, not the migration role. No default: a guessed credential is a guess |
| `REDIS_URL` | **required** | The rate limiter fails closed if Redis is unreachable |
| `MAIL_RELAY_URL` `MAIL_RELAY_TOKEN` `MAIL_FROM` | in production | All three or none; half-configured is refused at boot |
| `PORT` `HOST` `LOG_LEVEL` | optional | Default `3000`, `0.0.0.0`, `info` |
| `REGISTRATION_RATE_LIMIT` `REGISTRATION_WINDOW_MS` | optional | Default 5 per hour per address |
| `PGPOOL_MAX` | optional | Default 10 |

Copy `.env.example` and fill it in. Keep the real `.env` out of version control;
`.dockerignore` excludes it so it cannot be baked into a layer, where it would
survive in the image history.

## The three database roles

The split is the point of the schema, and deploying it wrong quietly undoes it.

- `ajo_migrator` — owns the schema and every `SECURITY DEFINER` function. Never
  used by the application.
- `ajo_app` — `NOLOGIN`. The bundle of privilege the application actually runs
  with. Every RLS policy in section 9.6 is written for this role.
- `ajo_api` — the login the pool connects as. `NOSUPERUSER NOBYPASSRLS`, holds
  only `ajo_app`, and reaches it with `SET LOCAL ROLE` inside a transaction.

If the application connects as `ajo_migrator` or any superuser, every policy is
decorative and the tests that would have caught it pass vacuously against a
superuser. Set `PGUSER=ajo_api`.

`scripts/bootstrap_roles.sql` creates `ajo_api` with the placeholder password
`local-dev-only`, which is a development convenience and indefensible in
production. On a real deployment, provision the role with a secret from the
platform and do not rely on the bootstrap's `CREATE ROLE`:

```sql
CREATE ROLE ajo_api LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE
  NOREPLICATION PASSWORD :'api_password';
GRANT ajo_app TO ajo_api;
```

The membership is what does the work, and it is one-way: `ajo_app` gains nothing
from knowing this role exists.

## The mail relay

There is no vendor integration, and that is deliberate. Every hosted provider has
a different payload and SDK, and choosing one in a file that has no business
choosing it would be a decision made by accident.

What the API does is one authenticated HTTP POST per verification email, with a
10-second timeout. A relay service receives:

```json
{
  "from": "no-reply@example.ng",
  "to": "member@example.ng",
  "subject": "Confirm your email address for Ajo",
  "text": "Confirm your email address\n\nAccount: <uuid>\nToken: <token>\n\n..."
}
```

with `Authorization: Bearer <MAIL_RELAY_TOKEN>`. Any 2xx is success; anything else
throws, and the registration returns 500 with the HTTP status in the log. The
token never appears in the error, because error strings reach logs and sometimes
error trackers.

In production with no relay configured, **the process will not start**. The
alternative is the development sender, which writes every verification link to
stdout. Not booting is the better failure.

The token is in the message body, not a URL query string, so it does not land in
relay logs, mailbox list views, or a `Referer` header.

## The proxy, TLS, and the rate limit

The rate limiter keys on `request.ip`, and `trustProxy` is deliberately off. With
it off, `request.ip` is the socket peer — which is the only value a client cannot
choose.

Turn it on only when a reverse proxy in front of the API sets `X-Forwarded-For`
and overwrites any client-supplied value. Trusting the header from a client that
can set it yourself lets an attacker pick their own rate-limit key by inventing a
header, which removes the limit entirely. This is the single easiest way to
disable the only bound on the unauthenticated signup path.

TLS terminates at the proxy. The API speaks plain HTTP and should stay behind
something that does the terminating.

## Probes

- `/healthz` — liveness. Touches nothing. Use it for restart decisions.
- `/readyz` — readiness. Checks Postgres and Redis, reports which is down, and
  returns 503 if either is. Use it for traffic routing.

Do not point a restart policy at `/readyz`. A slow database would then restart
healthy processes, which does not fix the database and turns a degradation into
an outage.

## The image

```sh
docker build -t ajo-api .
docker run --rm -p 3000:3000 --env-file .env ajo-api
```

Three stages: build with the toolchain, `npm prune --omit=dev`, then a runtime
stage with the compiled output and production dependencies only. `dumb-init` is
the entrypoint so `SIGTERM` reaches node — without it the graceful shutdown in
`index.ts` is skipped and every deploy is a hard kill.

Runs as `node`, not root. The `HEALTHCHECK` uses `/healthz` for the same reason
as above.

The database is not in the image. A schema change and a code change need to ship
independently and in a known order, which means migrations are a release step,
not a startup step.

## What is still missing

Honest list, so nobody discovers these in production:

- **No vendor mail integration.** The relay contract above is the seam; an
  adapter for a specific provider is a thin function over it.
- **No session or login endpoint.** Registration and verification exist; there is
  no way to authenticate afterwards, and `user_credentials` is currently
  write-only by policy.
- **No application Dockerfile in `docker-compose.yml`.** The compose file is
  Postgres and Redis for local development; the API runs on the host.
- **No deployment manifests.** No Kubernetes, systemd, or platform-specific
  config. The image and the environment are the contract.
- **Rate-limit counters live in Redis with no persistence.** A Redis restart
  resets them, so a client gets a fresh budget. Acceptable for a signup limit;
  would not be for anything financial.
- **The specification still differs from the schema** in column counts on some
  tables. The migrations are the source of truth for what exists.
