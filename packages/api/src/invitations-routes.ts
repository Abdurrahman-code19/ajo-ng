import type { FastifyInstance } from 'fastify';
import type pg from 'pg';

import type { AccessTokenVerifier } from './access-token.js';
import { requireAuthentication, requireIdentity } from './auth.js';
import { ValidationError } from './identity.js';
import {
  acceptInvitation,
  createInvitations,
  declineInvitation,
  InvitationConflictError,
  InvitationGoneError,
  InvitationNotAllowedError,
  InvitationNotFoundError,
  listInvitations,
  previewInvitation,
  type CreateInvitationInput,
} from './invitations.js';

export interface InvitationRouteDeps {
  readonly pool: pg.Pool;
  readonly verifier: AccessTokenVerifier;
}

/**
 * Invitations -- spec section 11.5.
 *
 * Every handler here repeats the same five-branch mapping. That is deliberate:
 * the branch order *is* the contract, and a shared helper would let one route's
 * mistake (a 409 where the spec says 410, say) hide inside an abstraction that
 * reads as if it could not be wrong.
 */
export function registerInvitationRoutes(app: FastifyInstance, deps: InvitationRouteDeps) {
  const { pool, verifier } = deps;
  // Every route except the preview is behind this. It is attached per route
  // rather than app-wide because the preview is the one endpoint in this file
  // that must work for somebody with no account at all, and a hook that cannot
  // be exempted from would either break it or quietly make it authenticated.
  const authenticated = { preHandler: requireAuthentication(verifier) };

  app.post(
    '/api/v1/invitations',
    {
      ...authenticated,
      schema: {
        body: {
          type: 'object',
          required: ['ajoId', 'contacts'],
          additionalProperties: false,
          properties: {
            ajoId: { type: 'string', format: 'uuid' },
            contacts: {
              type: 'array',
              minItems: 1,
              maxItems: 50,
              items: {
                type: 'object',
                additionalProperties: false,
                properties: {
                  name: { type: 'string', maxLength: 200 },
                  email: { type: 'string', maxLength: 320 },
                  // Accepted here, refused by the service. This schema decides
                  // what is *syntactically* an invitation contact, and
                  // `phoneNumber` is one of those in section 11.4. Whether the
                  // Ajo can actually reach an address is policy, and policy
                  // lives in the service, which answers 422 with the field
                  // named. Closing it here instead would report a malformed
                  // request (400) for what is a well-formed request to
                  // something that cannot be sent.
                  phoneNumber: { type: 'string', maxLength: 32 },
                },
              },
            },
            personalMessage: { type: 'string', maxLength: 2000 },
            expiresInHours: { type: 'integer', minimum: 1, maximum: 720 },
          },
        },
      },
    },
    async (request, reply) => {
      const identity = requireIdentity(request);
      try {
        const result = await createInvitations(pool, identity, (request.body ?? {}) as CreateInvitationInput);
        // 202, not 201: the invitation exists, but the thing the caller actually
        // asked for -- the invitee learning about it -- has not happened yet.
        return reply.code(202).send(result);
      } catch (error) {
        if (error instanceof ValidationError) {
          return reply.code(422).send({
            error: 'validation_failed',
            field: error.field,
            message: error.message,
          });
        }
        if (error instanceof InvitationNotAllowedError) {
          return reply.code(403).send({ error: 'forbidden', message: error.message });
        }
        if (error instanceof InvitationConflictError) {
          return reply.code(409).send({ error: 'conflict', message: error.message });
        }
        app.log.error({ err: error }, 'creating an invitation failed');
        return reply.code(500).send({ error: 'internal_error', message: 'The invitation could not be created.' });
      }
    },
  );

  app.get(
    '/api/v1/invitations',
    {
      ...authenticated,
      schema: {
        querystring: {
          type: 'object',
          required: ['ajoId'],
          additionalProperties: false,
          properties: { ajoId: { type: 'string', format: 'uuid' } },
        },
      },
    },
    async (request, reply) => {
      const identity = requireIdentity(request);
      const { ajoId } = request.query as { ajoId: string };
      try {
        const invitations = await listInvitations(pool, identity, ajoId);
        return reply.code(200).send({ invitations });
      } catch (error) {
        if (error instanceof InvitationNotAllowedError) {
          return reply.code(403).send({ error: 'forbidden', message: error.message });
        }
        app.log.error({ err: error }, 'listing invitations failed');
        return reply.code(500).send({ error: 'internal_error', message: 'The invitations could not be listed.' });
      }
    },
  );

  /**
   * The anonymous preview. No `requireIdentity`, on purpose: the person holding
   * this link may have no account yet, and the disclosure of what they are
   * being asked to commit to is the last thing that should require one.
   */
  app.get(
    '/api/v1/invitations/:token',
    async (request, reply) => {
      const { token } = request.params as { token: string };
      try {
        const preview = await previewInvitation(pool, token);
        return reply.code(200).send(preview);
      } catch (error) {
        if (error instanceof InvitationNotFoundError) {
          return reply.code(404).send({ error: 'not_found', message: error.message });
        }
        if (error instanceof InvitationGoneError) {
          // 410 rather than 404: the link was real and is now spent. A 404 here
          // would tell an invitee their address was never invited, which is a
          // different and more confusing answer.
          return reply.code(410).send({ error: 'gone', reason: error.message });
        }
        app.log.error({ err: error }, 'previewing an invitation failed');
        return reply.code(500).send({ error: 'internal_error', message: 'The invitation could not be read.' });
      }
    },
  );

  app.post(
    '/api/v1/invitations/accept',
    {
      ...authenticated,
      schema: {
        body: {
          type: 'object',
          required: ['token', 'accept', 'rulesAcknowledged'],
          additionalProperties: false,
          properties: {
            token: { type: 'string', minLength: 1, maxLength: 512 },
            accept: { type: 'boolean' },
            rulesAcknowledged: { type: 'boolean' },
          },
        },
      },
    },
    async (request, reply) => {
      const identity = requireIdentity(request);
      try {
        const result = await acceptInvitation(pool, identity, request.body ?? {});
        return reply.code(200).send(result);
      } catch (error) {
        if (error instanceof ValidationError) {
          return reply.code(422).send({
            error: 'validation_failed',
            field: error.field,
            message: error.message,
          });
        }
        if (error instanceof InvitationNotAllowedError) {
          return reply.code(403).send({ error: 'forbidden', message: error.message });
        }
        if (error instanceof InvitationNotFoundError) {
          return reply.code(404).send({ error: 'not_found', message: error.message });
        }
        if (error instanceof InvitationGoneError) {
          return reply.code(410).send({ error: 'gone', reason: error.message });
        }
        if (error instanceof InvitationConflictError) {
          return reply.code(409).send({ error: 'conflict', message: error.message });
        }
        app.log.error({ err: error }, 'accepting an invitation failed');
        return reply.code(500).send({ error: 'internal_error', message: 'The invitation could not be accepted.' });
      }
    },
  );

  app.post(
    '/api/v1/invitations/:token/decline',
    authenticated,
    async (request, reply) => {
      const identity = requireIdentity(request);
      const { token } = request.params as { token: string };
      try {
        const result = await declineInvitation(pool, identity, token);
        return reply.code(200).send(result);
      } catch (error) {
        if (error instanceof InvitationNotAllowedError) {
          return reply.code(403).send({ error: 'forbidden', message: error.message });
        }
        if (error instanceof InvitationNotFoundError) {
          return reply.code(404).send({ error: 'not_found', message: error.message });
        }
        if (error instanceof InvitationGoneError) {
          return reply.code(410).send({ error: 'gone', reason: error.message });
        }
        if (error instanceof InvitationConflictError) {
          return reply.code(409).send({ error: 'conflict', message: error.message });
        }
        app.log.error({ err: error }, 'declining an invitation failed');
        return reply.code(500).send({ error: 'internal_error', message: 'The invitation could not be declined.' });
      }
    },
  );
}