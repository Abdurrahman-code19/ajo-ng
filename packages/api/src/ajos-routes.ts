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
import {
  AjoNotFoundError,
  getAjo,
  listAjos,
} from './ajos-read.js';
import {
  EnrollmentConflictError,
  EnrollmentNotAllowedError,
  EnrollmentNotFoundError,
  openEnrollment,
  type OpenEnrollmentInput,
} from './enrollment.js';

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

  /**
   * `GET /api/v1/ajos` -- the Ajos the caller belongs to.
   *
   * Spec section 11. The read path does its own authorisation, in the database:
   * `ajos_select` only returns rows the caller organises or is a member of, so
   * this handler never sees a row it should not show and cannot leak one by
   * forgetting a check. See `ajos-read.ts`.
   */
  app.get(
    '/api/v1/ajos',
    {
      preHandler: requireAuthentication(verifier),
      schema: {
      querystring: {
        type: 'object',
        properties: {
          status: { type: 'string' },
        },
        // Unknown keys are refused rather than ignored: `?page=2` on a list
        // that has no paging answers with a 400 the caller can correct, instead
        // of a 200 that quietly returned page 1 again.
        additionalProperties: false,
      },
      },
    },
    async (request, reply) => {
      const identity = requireIdentity(request);
      const { status } = request.query as { status?: string };
      try {
        const result = await listAjos(pool, identity, status);
        return reply.code(200).send(result);
      } catch (error) {
        app.log.error({ err: error }, 'listing Ajos failed');
        return reply.code(500).send({
          error: 'internal_error',
          message: 'Your Ajos could not be loaded.',
        });
      }
    },
  );

  /**
   * `GET /api/v1/ajos/:id` -- one Ajo with its seat board and roster.
   *
   * The 404 for an invisible Ajo is deliberate (see `ajos-read.ts`): an id the
   * caller has no relationship with is not theirs to be told exists.
   */
  app.get(
    '/api/v1/ajos/:id',
    {
      preHandler: requireAuthentication(verifier),
      schema: {
        params: {
          type: 'object',
          required: ['id'],
          properties: { id: { type: 'string', format: 'uuid' } },
        },
      },
    },
    async (request, reply) => {
      const identity = requireIdentity(request);
      const { id } = request.params as { id: string };
      try {
        const result = await getAjo(pool, identity, id);
        return reply.code(200).send(result);
      } catch (error) {
        if (error instanceof AjoNotFoundError) {
          return reply.code(404).send({ error: 'not_found', message: error.message });
        }
        app.log.error({ err: error }, 'reading an Ajo failed');
        return reply.code(500).send({
          error: 'internal_error',
          message: 'That Ajo could not be loaded.',
        });
      }
    },
  );

  /**
   * `POST /api/v1/ajos/:id/activate` -- open the five-day enrollment window.
   *
   * The path is canonical and the semantics are pinned by user-flows section
   * 2.0.2: this is DRAFT to ENROLLMENT. Nothing here activates an Ajo, and the
   * name is kept only because renaming a canonical path is a decision for the
   * API owner, not something to do silently in a route handler.
   */
  app.post(
    '/api/v1/ajos/:id/activate',
    {
      preHandler: requireAuthentication(verifier),
      schema: {
        // 404 rather than 400 for a body-less request: a malformed id cannot be
        // told apart from a missing one without naming a UUID that is not there.
        params: {
          type: 'object',
          required: ['id'],
          properties: { id: { type: 'string', format: 'uuid' } },
        },
        body: {
          type: 'object',
          required: ['confirm'],
          additionalProperties: false,
          // `const: true` rather than `type: 'boolean'`. A boolean `false` is a
          // well-formed body that must still be refused -- the caller is saying
          // "do not confirm", which is a refusal to do the thing, not an intent
          // to open enrollment -- and only `const` expresses that here without a
          // custom validator that would have to be re-implemented per route.
          properties: { confirm: { type: 'boolean', const: true } },
        },
      },
    },
    async (request, reply) => {
      const identity = requireIdentity(request);
      const { id } = request.params as { id: string };
      try {
        const result = await openEnrollment(pool, identity, id, (request.body ?? {}) as OpenEnrollmentInput);
        return reply.code(200).send(result);
      } catch (error) {
        if (error instanceof EnrollmentNotFoundError) {
          return reply.code(404).send({ error: 'not_found', message: error.message });
        }
        if (error instanceof EnrollmentNotAllowedError) {
          return reply.code(403).send({ error: 'forbidden', message: error.message });
        }
        if (error instanceof EnrollmentConflictError) {
          return reply.code(409).send({ error: 'conflict', message: error.message });
        }
        if (error instanceof ValidationError) {
          return reply.code(422).send({
            error: 'validation_failed',
            field: error.field,
            message: error.message,
          });
        }
        app.log.error({ err: error }, 'opening enrollment failed');
        return reply.code(500).send({
          error: 'internal_error',
          message: 'Enrollment could not be opened.',
        });
      }
    },
  );
}
