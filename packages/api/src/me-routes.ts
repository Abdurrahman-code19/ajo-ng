/**
 * `GET /api/v1/me` -- the member behind the access token.
 *
 * The spec's path is `GET /me` (section 25); every route in this application is
 * mounted under `/api/v1`, so the faithful mapping is `/api/v1/me`.
 *
 * Deliberately a separate file from `session-routes.ts`. That file exists because
 * every line touching the refresh cookie belongs in one place, and this route
 * touches no cookie at all -- it reads a bearer token and answers with the member.
 * Folding it in would dilute the reason `session-routes.ts` is one file.
 */
import type { FastifyInstance } from 'fastify';

import type { AccessTokenVerifier } from './access-token.js';
import type { Pool } from 'pg';
import { loadMe } from './me.js';
import { requireAuthentication, requireIdentity } from './auth.js';

export interface MeRouteDependencies {
  readonly pool: Pool;
  readonly verifier: AccessTokenVerifier;
}

export function registerMeRoutes(app: FastifyInstance, deps: MeRouteDependencies): void {
  const { pool, verifier } = deps;

  /**
   * GET /api/v1/me
   *
   * `Cache-Control: private` because the response is one member's data and must
   * never be held by a shared cache; a short `max-age` because section 25 has the
   * app calling this on every launch, and a profile that is a minute stale is
   * worth the saved round trip. A verification or status change is visible within
   * that minute rather than immediately, which is the deliberate trade.
   */
  app.get(
    '/api/v1/me',
    { preHandler: requireAuthentication(verifier) },
    async (request, reply) => {
      const identity = requireIdentity(request);
      try {
        const me = await loadMe(pool, identity);
        if (me === undefined) {
          // The token verified, so the caller is not anonymous; the account row
          // is simply gone (deleted between the token being minted and now). 404
          // says that, whereas 401 would invite a refresh that cannot help.
          return reply.code(404).send({ error: 'not_found' });
        }
        void reply.header('Cache-Control', 'private, max-age=60');
        return reply.code(200).send(me);
      } catch (error) {
        app.log.error({ err: error }, 'loading the current member failed');
        return reply.code(500).send({
          error: 'internal_error',
          message: 'Your account details could not be loaded.',
        });
      }
    },
  );
}
