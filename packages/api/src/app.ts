/**
 * The Fastify application.
 *
 * `buildApp` takes its collaborators as arguments and returns the app without
 * listening, so a test can drive it over an ephemeral port and the composition
 * root in `index.ts` is the only file that knows about the environment. The
 * alternative -- a module that reads `process.env` on import -- makes every test
 * that touches it a test that mutates global state.
 */
import Fastify, { type FastifyInstance } from 'fastify';
import type { Pool } from 'pg';
import type { Config } from './config.js';
import type { RateLimiter } from './rate-limit.js';
import { ValidationError } from './identity.js';
import { RegistrationConflict, register } from './register.js';
import { VerificationError, verifyEmailToken } from './verify-email.js';
import type { VerificationSender } from './mailer.js';

export interface AppDependencies {
  readonly config: Config;
  readonly pool: Pool;
  readonly limiter: RateLimiter;
  /** Where the verification token goes. Never into the HTTP response. */
  readonly mailer: VerificationSender;
}

export async function buildApp(deps: AppDependencies): Promise<FastifyInstance> {
  const { config, pool, limiter, mailer } = deps;
  const app = Fastify({
    logger: { level: config.logLevel },
    ajv: {
      customOptions: {
        // Fastify's default is `removeAdditional: true`, which deletes any
        // property not named in the schema rather than rejecting the request. For
        // a public API that is the wrong default: a client sending
        // `acceptdTerms` gets a cheerful 201 for an account that accepted nothing,
        // and the bug surfaces later as a consent dispute. The schemas below set
        // `additionalProperties: false` on every body for the same reason -- this
        // option is what makes that setting mean anything.
        removeAdditional: false,
        // Report the whole set of schema violations, not the first, so a client
        // fixing one field at a time is not led through six round trips.
        allErrors: true,
      },
    },
  });

  // Security headers. Not a substitute for a reverse proxy that sets them too,
  // but the API is a JSON endpoint that a browser may be pointed at, and the
  // defaults are wrong for that case.
  app.addHook('onSend', async (_request, reply) => {
    void reply
      .header('X-Content-Type-Options', 'nosniff')
      .header('X-Frame-Options', 'DENY')
      .header('Referrer-Policy', 'no-referrer')
      // An API returns JSON and nothing else, so the strictest possible policy
      // is also the correct one. `default-src 'none'` means even a successful
      // HTML injection has nothing to load.
      .header(
        'Content-Security-Policy',
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
      );
  });

  /**
   * Liveness and readiness, kept separate on purpose.
   *
   * `/healthz` answers "is this process running" and must not touch the
   * database, because a liveness probe that fails when Postgres is slow will
   * restart a process that is perfectly healthy. `/readyz` answers "can this
   * process serve a request" and does check both dependencies, so an orchestrator
   * stops sending traffic to an instance that cannot serve it.
   */
  app.get('/healthz', async () => ({ status: 'ok' }));

  app.get('/readyz', async (_request, reply) => {
    try {
      await pool.query('SELECT 1');
    } catch (error) {
      app.log.error({ err: error }, 'readiness check failed');
      return reply.code(503).send({ status: 'unavailable', database: 'down' });
    }
    // Checked and reported separately rather than short-circuited, so an
    // operator can tell which dependency is the problem from the response.
    if (!(await limiter.ping())) {
      return reply.code(503).send({ status: 'unavailable', rateLimiter: 'down' });
    }
    return { status: 'ok', database: 'up', rateLimiter: 'up' };
  });

  registerAuthRoutes(app, pool, limiter, mailer, config);
  registerVerifyEmailRoute(app, pool, limiter, config);
  return app;
}

function registerAuthRoutes(
  app: FastifyInstance,
  pool: Pool,
  limiter: RateLimiter,
  mailer: VerificationSender,
  config: Config,
): void {
  /**
   * POST /api/v1/auth/register
   *
   * The rate limit is here, on the route, rather than inside `register`, so that
   * a limit has exactly one home. A limit inside the service function is one
   * call site away from being bypassed by the next caller added.
   */
  app.post(
    '/api/v1/auth/register',
    {
      schema: {
        body: {
          type: 'object',
          required: ['email', 'password', 'fullName', 'phone', 'acceptedTerms', 'acceptedPrivacy'],
          additionalProperties: false,
          properties: {
            email: { type: 'string', minLength: 3, maxLength: 320 },
            password: { type: 'string', minLength: 1, maxLength: 200 },
            fullName: { type: 'string', minLength: 1, maxLength: 200 },
            phone: { type: 'string', minLength: 1, maxLength: 32 },
            acceptedTerms: { type: 'boolean' },
            acceptedPrivacy: { type: 'boolean' },
            preferredLocale: { type: 'string', maxLength: 32 },
          },
        },
      },
    },
    async (request, reply) => {
      // `trustProxy` is not enabled, so `request.ip` is the socket peer. That is
      // the correct input for a limit whose job is to bound one source of signup
      // traffic, and it is the *only* correct input: trusting an `X-Forwarded-For`
      // from an unverified client would let a caller pick its own rate-limit key
      // by inventing a header, which removes the limit entirely.
      const key = request.ip;

      let allowed: boolean;
      try {
        allowed = await limiter.consume(key);
      } catch (error) {
        app.log.error({ err: error }, 'rate limiter unavailable; refusing registration');
        return reply.code(503).send({
          error: 'temporarily_unavailable',
          message: 'Registration is unavailable. Please try again shortly.',
        });
      }

      if (!allowed) {
        // 429 with Retry-After, because a client that is told only "no" will
        // retry immediately and make the situation worse.
        const retryAfterSeconds = Math.ceil(config.registration.windowMs / 1000);
        void reply.header('Retry-After', String(retryAfterSeconds));
        return reply.code(429).send({
          error: 'rate_limited',
          message: 'Too many registration attempts. Please try again later.',
        });
      }

      try {
        const result = await register(pool, request.body as never);

        // The token leaves by email and nowhere else. It is not in this
        // response, not in a header, and not in a log line. `result` holds it
        // because `register` had to mint it; the one thing done with it is this
        // call.
        await mailer.sendVerificationToken({
          to: result.email,
          userId: result.userId,
          token: result.verificationToken,
        });

        // 201, and a Location header, because a registration creates a resource
        // at a URL the caller can now address.
        void reply.header('Location', `/api/v1/users/${result.userId}`);
        return reply.code(201).send({
          userId: result.userId,
          email: result.email,
          status: result.status,
        });
      } catch (error) {
        if (error instanceof ValidationError) {
          return reply.code(422).send({
            error: 'validation_failed',
            field: error.field,
            message: error.message,
          });
        }
        if (error instanceof RegistrationConflict) {
          return reply.code(409).send({
            error: 'conflict',
            field: error.field,
            message: error.message,
          });
        }
        // A password hash is never part of an error, and this is the only place
        // an unexpected one is logged -- so nothing reaches the log that a
        // credential could be reconstructed from.
        app.log.error({ err: error }, 'registration failed');
        return reply.code(500).send({
          error: 'internal_error',
          message: 'Registration could not be completed.',
        });
      }
    },
  );
}

/**
 * POST /api/v1/auth/verify-email
 *
 * Unauthenticated, because the account this verifies has no session yet, and
 * that is exactly why it is rate limited like registration is: the token is 256
 * bits of entropy so it cannot be brute-forced, but the *account status* behind
 * it is observable, and an unbounded endpoint that flips account state is worth
 * bounding anyway.
 *
 * Separate from `registerAuthRoutes` because it is not an auth-route concern in
 * the sense that route is -- it has no body validation beyond the token and no
 * identity to establish. Keeping it separate also keeps `config` an explicit
 * parameter rather than something reaching for a module-level value.
 */
export function registerVerifyEmailRoute(
  app: FastifyInstance,
  pool: Pool,
  limiter: RateLimiter,
  config: Config,
): void {
  app.post(
    '/api/v1/auth/verify-email',
    {
      schema: {
        body: {
          type: 'object',
          required: ['token'],
          additionalProperties: false,
          properties: { token: { type: 'string', minLength: 1, maxLength: 512 } },
        },
      },
    },
    async (request, reply) => {
      // The key is namespaced with the action, so registrations and
      // verifications from one address do not share a budget. They are different
      // endpoints with different costs and a client legitimately doing both
      // should not be throttled for the other.
      let allowed: boolean;
      try {
        allowed = await limiter.consume(`verify:${request.ip}`);
      } catch (error) {
        app.log.error({ err: error }, 'rate limiter unavailable; refusing verification');
        return reply.code(503).send({
          error: 'temporarily_unavailable',
          message: 'Verification is unavailable. Please try again shortly.',
        });
      }

      if (!allowed) {
        void reply.header(
          'Retry-After',
          String(Math.ceil(config.registration.windowMs / 1000)),
        );
        return reply
          .code(429)
          .send({ error: 'rate_limited', message: 'Too many attempts. Please try again later.' });
      }

      try {
        const result = await verifyEmailToken(pool, (request.body as { token: string }).token);
        return reply.code(200).send({
          verified: true,
          // Reported so a double-clicked link is a success rather than an error,
          // while the single-use guarantee is still enforced underneath.
          alreadyVerified: result.alreadyVerified,
        });
      } catch (error) {
        if (error instanceof VerificationError) {
          // 400, one message for every rejection reason. See verify-email.ts.
          return reply.code(400).send({ error: 'invalid_token', message: error.message });
        }
        app.log.error({ err: error }, 'email verification failed');
        return reply
          .code(500)
          .send({ error: 'internal_error', message: 'Verification could not be completed.' });
      }
    },
  );
}
