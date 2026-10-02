/**
 * POST /api/v1/webhooks/payments/:provider
 *
 * The public face of the provider seam. It does four things and delegates the
 * rest: resolve the provider, limit the caller, hand the bytes to the adapter to
 * verify, and record the result. Whether the money moved is settled later by a
 * worker, so a slow database cannot make a provider retry a delivery that has
 * already succeeded.
 *
 * Note what the route does *not* do: it never parses the body itself, and it
 * never decides what an event means. Both belong to the adapter and the
 * database, respectively, and a route that parsed JSON before calling
 * `parseWebhook` would have violated §13.5's "parse only after verification"
 * while looking perfectly reasonable.
 */
import type { FastifyInstance, FastifyReply, FastifyRequest } from 'fastify';
import {
  ProviderError,
  WebhookSignatureError,
  type FinancialProvider,
  type ProviderId,
} from '@ajo/domain';
import type { Pool } from 'pg';
import type { Config } from './config.js';
import type { RateLimiter } from './rate-limit.js';
import type { RequestWithRawBody } from './raw-body.js';
import { StaleProviderEventError, receiveProviderWebhook } from './webhooks.js';

export interface WebhookRouteDependencies {
  readonly config: Config;
  readonly pool: Pool;
  readonly limiter: RateLimiter;
  /**
   * Resolves a provider id to an adapter.
   *
   * A function rather than a map because the answer is not always the same: a
   * provider whose secret is not configured is not a provider, and the
   * composition root is where that is known.
   */
  readonly resolveProvider: (id: string) => FinancialProvider | undefined;
}

/**
 * Header carrying the signature, per provider.
 *
 * `x-signature` is the only name in the seam's contract today because `mock` is
 * the only provider with a published format. A provider that signs into a
 * different header gets its own name here, and nothing else has to change --
 * which is the arrangement worth preserving while there is only one provider to
 * preserve it for.
 */
const SIGNATURE_HEADER = 'x-signature';

export function registerWebhookRoutes(
  app: FastifyInstance,
  deps: WebhookRouteDependencies,
): void {
  app.post<{ Params: { provider: string } }>(
    '/api/v1/webhooks/payments/:provider',
    async (request, reply) => handle(app, deps, request, reply),
  );

  async function handle(
    fastify: FastifyInstance,
    routeDeps: WebhookRouteDependencies,
    request: FastifyRequest<{ Params: { provider: string } }>,
    reply: FastifyReply,
  ): Promise<FastifyReply> {
    const providerId = request.params.provider;

    // Refused before the signature is examined, because without the provider
    // there is no secret to examine it against, and because a caller should not
    // be able to learn which provider ids exist by watching which ones 401.
    const provider = routeDeps.resolveProvider(providerId);
    if (provider === undefined) {
      // 404, not 400: an unroutable provider is indistinguishable from an
      // unrouted path, and this URL is not part of the API's vocabulary.
      return reply.code(404).send({
        error: 'not_found',
        message: 'No such resource.',
      });
    }

    if (!(await rateLimited(fastify, routeDeps, request, providerId))) {
      return reply.code(429).send({
        error: 'rate_limited',
        message: 'Too many deliveries. Try again shortly.',
      });
    }

    const rawBody = (request as RequestWithRawBody).rawBody;
    if (rawBody === undefined) {
      // A webhook with no body cannot be signed over, and refusing it here is
      // clearer than letting the adapter compare an HMAC against an empty
      // string.
      return reply.code(400).send({
        error: 'bad_request',
        message: 'The request did not match the expected shape.',
      });
    }

    const signature = request.headers[SIGNATURE_HEADER];
    if (typeof signature !== 'string' || signature.length === 0) {
      return reply.code(401).send({
        error: 'invalid_signature',
        message: 'The signature header is required.',
      });
    }

    try {
      const outcome = await receiveProviderWebhook(routeDeps.pool, {
        provider,
        rawBody,
        signatureHeader: signature,
        receivedAt: new Date(),
      });

      if (outcome.kind === 'stale') {
        return reply.code(422).send({
          error: 'stale_event',
          message: 'The event timestamp is outside the accepted window.',
        });
      }

      if (outcome.kind === 'ignored') {
        // Acknowledged on purpose. §13.5 asks for an unknown event type to be
        // logged and ignored, never a 4xx: a provider that retries a delivery
        // this system will never understand sends it forever, and a log line is
        // the record the spec actually wants.
        fastify.log.info(
          { provider: providerId, eventType: outcome.eventId, reason: outcome.reason },
          'provider event ignored',
        );
        return reply.code(202).send({ received: true, acted_on: false });
      }

      // `202` rather than `200`: the delivery is recorded and the transfer is not
      // settled. Telling a provider "processed" here would invite it to believe
      // the member's contribution is paid when nothing has been checked yet.
      return reply.code(202).send({
        received: true,
        acted_on: true,
        duplicate: outcome.kind === 'duplicate',
      });
    } catch (error) {
      if (error instanceof WebhookSignatureError) {
        // 401 with nothing else in it. The reason the signature failed is not
        // disclosed, because telling a caller which of the three possibilities
        // it was -- unknown reference, wrong amount, wrong secret -- is free
        // information for whoever is guessing.
        fastify.log.warn(
          { provider: providerId },
          'provider webhook signature did not verify',
        );
        return reply.code(401).send({
          error: 'invalid_signature',
          message: 'The signature did not verify.',
        });
      }

      if (error instanceof StaleProviderEventError) {
        return reply.code(422).send({
          error: 'stale_event',
          message: 'The event timestamp is outside the accepted window.',
        });
      }

      if (error instanceof ProviderError) {
        // Signed correctly, unreadable. Spec §13.5's answer to a body we cannot
        // parse is to log it and carry on, and a 5xx would make the provider
        // retry a delivery whose bytes will never become parseable.
        fastify.log.error(
          { err: error, provider: providerId, retryable: error.retryable },
          'provider webhook body could not be read',
        );
        return reply.code(202).send({ received: true, acted_on: false });
      }

      throw error;
    }
  }
}

async function rateLimited(
  app: FastifyInstance,
  deps: WebhookRouteDependencies,
  request: FastifyRequest<{ Params: { provider: string } }>,
  providerId: string,
): Promise<boolean> {
  const allowed = await deps.limiter.consume(`${providerId}:${request.ip}`);
  if (!allowed) {
    app.log.warn(
      { provider: providerId, limit: deps.config.webhooks.rateLimit },
      'webhook rate limit exceeded',
    );
  }
  return allowed;
}

export type { ProviderId };