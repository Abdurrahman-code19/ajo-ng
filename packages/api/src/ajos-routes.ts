/**
 * `POST /api/v1/ajos` -- create a draft Ajo.
 *
 * Spec section 11. Behind an access token, because an Ajo belongs to its
 * organizer and there is nothing anonymous about it; the route then hands the
 * identity to `createAjo`, which applies the email-verified precondition and
 * performs the write.
 *
 * A separate file from `session-routes.ts` and `me-routes.ts` for the same
 * reason those are separate from each other: this route is about an Ajo, and
 * the collection of Ajo routes will grow here -- this is the first of them, not
 * an auth concern that happens to touch an Ajo.
 */
import type { FastifyInstance } from 'fastify';
import type { Pool } from 'pg';

import type { AccessTokenVerifier } from './access-token.js';
import { requireAuthentication, requireIdentity } from './auth.js';
import { ValidationError } from './identity.js';
import { AjoNotAllowedError, createAjo, type CreateAjoInput } from './ajos.js';

export interface AjoRouteDependencies {
  readonly pool: Pool;
  readonly verifier: AccessTokenVerifier;
}

export function registerAjoRoutes(app: FastifyInstance, deps: AjoRouteDependencies): void {
  const { pool, verifier } = deps;

  /**
   * The body schema checks shape, not policy.
   *
   * Types and required fields are here so a malformed body is refused before it
   * reaches a database transaction; the *rules* -- the contribution window, the
   * 5-to-20 member count, rounds equalling members, the cadence and weekday
   * vocabularies -- are checked in `validateCreateAjo` and answered as 422,
   * because they are the product's configuration rules rather than JSON syntax.
   */
  app.post(
    '/api/v1/ajos',
    {
      preHandler: requireAuthentication(verifier),
      schema: {
        body: {
          type: 'object',
          required: [
            'name',
            'contributionKobo',
            'currency',
            'frequency',
            'collectionDay',
            'durationRounds',
            'maxMembers',
            'startDate',
          ],
          additionalProperties: false,
          properties: {
            name: { type: 'string', minLength: 1, maxLength: 80 },
            description: { type: 'string', maxLength: 2000 },
            contributionKobo: { type: 'integer', minimum: 0 },
            currency: { type: 'string' },
            frequency: { type: 'string' },
            collectionDay: { type: 'string' },
            durationRounds: { type: 'integer', minimum: 1 },
            maxMembers: { type: 'integer', minimum: 1 },
            startDate: { type: 'string' },
          },
        },
      },
    },
    async (request, reply) => {
      const identity = requireIdentity(request);
      try {
        const result = await createAjo(pool, identity, (request.body ?? {}) as CreateAjoInput);
        // 201 with a Location, because the caller can now address the Ajo they
        // created. The positions come back with it so the client does not have
        // to make a second request to render the roster it just asked for.
        void reply.header('Location', `/api/v1/ajos/${result.ajo.id}`);
        return reply.code(201).send(result);
      } catch (error) {
        if (error instanceof ValidationError) {
          return reply.code(422).send({
            error: 'validation_failed',
            field: error.field,
            message: error.message,
          });
        }
        if (error instanceof AjoNotAllowedError) {
          return reply.code(403).send({ error: 'forbidden', message: error.message });
        }
        app.log.error({ err: error }, 'creating an Ajo failed');
        return reply.code(500).send({
          error: 'internal_error',
          message: 'The Ajo could not be created.',
        });
      }
    },
  );
}
