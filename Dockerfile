# syntax=docker/dockerfile:1
#
# The API image.
#
# Three stages, because the one thing that must not ship is the toolchain. The
# build stage has TypeScript and every devDependency; the runtime stage has the
# compiled output and production dependencies only, so a compromised build step
# does not leave `tsc` on the box, and the image is small enough to pull on a
# deploy.
#
#   docker build -t ajo-api .
#   docker run --rm -p 3000:3000 --env-file .env ajo-api
#
# The database is NOT part of this image. It is a separate concern with its own
# release step (`scripts/migrate.py` plus `scripts/bootstrap_roles.sql`), because
# a schema change and a code change must be able to ship independently and in a
# known order. See docs/deployment.md.

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
FROM node:20.20.2-bookworm-slim AS build

WORKDIR /app

# Dependencies first, as their own layer, so a source-only change does not
# re-download the tree. `npm ci` is not `npm install`: it installs exactly the
# lockfile, so the image cannot drift from what CI verified.
COPY package.json package-lock.json ./
COPY packages/api/package.json packages/api/
COPY packages/domain/package.json packages/domain/

# `--ignore-scripts` because the root package's `prepare` hook installs git
# hooks, which needs a .git directory this stage does not have and is
# meaningless in an image. The native module @node-rs/argon2 ships prebuilt
# binaries and needs no install step.
RUN npm ci --ignore-scripts

COPY tsconfig.base.json tsconfig.json ./
COPY packages/api/tsconfig.json packages/api/
COPY packages/domain/tsconfig.json packages/domain/
COPY packages/api/src packages/api/src
COPY packages/domain/src packages/domain/src

RUN npm run build

# Prune to production dependencies. Done here rather than in a fresh `npm ci
# --omit=dev` so the second install cannot resolve anything differently from the
# one that was just built and tested against.
RUN npm prune --omit=dev

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
FROM node:20.20.2-bookworm-slim AS runtime

# dumb-init reaps zombies and, more importantly, forwards SIGTERM to node. Node
# is PID 1 without it and does not run signal handlers reliably, so the graceful
# shutdown in index.ts -- close the server, close Redis, end the pool -- would be
# skipped and every deploy would be a hard kill.
RUN apt-get update \
 && apt-get install --no-install-recommends -y dumb-init \
 && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000

WORKDIR /app

# node (uid 1000) ships with the base image. Running as root inside a container
# that has a database password in its environment is a privilege nobody needs.
USER node

COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/package.json ./package.json
COPY --from=build --chown=node:node /app/packages/api/package.json ./packages/api/package.json
COPY --from=build --chown=node:node /app/packages/api/dist ./packages/api/dist
COPY --from=build --chown=node:node /app/packages/domain/dist ./packages/domain/dist
COPY --from=build --chown=node:node /app/packages/domain/package.json ./packages/domain/package.json

EXPOSE 3000

# Liveness only, deliberately. /readyz checks Postgres and Redis, and a
# container that is up but cannot reach its dependencies is not "unhealthy" --
# it is correctly running and correctly refusing traffic, and restarting it would
# not fix the database. The orchestrator's readiness probe is the one that
# should use /readyz.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||3000)+'/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "packages/api/dist/index.js"]
