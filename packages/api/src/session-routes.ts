/**
 * The session routes: login, refresh, logout, and the session list.
 *
 * They live in their own file for one reason that only becomes visible when they
 * are together: the refresh cookie is the platform's most sensitive string, and
 * every line that touches it belongs in one place. 12.4.1's storage rule --
 * `httpOnly`, `Secure`, `SameSite=Strict` -- is enforced by one helper
 * (`setRefreshCookie`) that both `login` and `refresh` call. Written twice, the
 * second copy is where one attribute is missed, and the symptom is a token
 * readable by JavaScript on a page nobody thought was running scripts.
 */
import type { FastifyInstance, FastifyReply, FastifyRequest } from 'fastify';
import type { Pool } from 'pg';

import type { Config } from './config.js';
import type { RateLimiter } from './rate-limit.js';
import type { AccessTokenSigner, AccessTokenVerifier } from './access-token.js';
import { login, AuthenticationFailedError, REFRESH_TOKEN_TTL_DAYS } from './login.js';
import { refresh, RefreshFailedError } from './refresh.js';
import { listSessions, revokeSession, logout } from './session.js';
import { requireAuthentication, requireIdentity, currentSessionId, unauthenticated } from './auth.js';

export const REFRESH_COOKIE = 'ajo_refresh';

const CREDENTIAL_BODY = {
  type: 'object',
  required: ['email', 'password'],
  additionalProperties: false,
  properties: {
    email: { type: 'string', minLength: 3, maxLength: 320 },
    password: { type: 'string', minLength: 1, maxLength: 200 },
    deviceLabel: { type: 'string', maxLength: 200 },
    platform: { type: 'string', enum: ['web', 'ios', 'android'] },
  },
} as const;

export interface SessionRouteDependencies {
  readonly config: Config;
  readonly pool: Pool;
  /**
   * The limiter that enforces `config.login`, not registration.
   *
   * The two are separate instances in the composition root (`index.ts`), for the
   * reason given on `AppDependencies.loginLimiter`: one limiter carries one limit
   * and one window, and login and registration do not share either.
   */
  readonly loginLimiter: RateLimiter;
  readonly signer: AccessTokenSigner;
  readonly verifier: AccessTokenVerifier;
}

/**
 * Writes the refresh cookie, and clears it.
 *
 * All of 12.4.1's attributes, and each one earns its place:
 *
 *   * `httpOnly` -- the token is unreadable by JavaScript, which is what makes
 *     "never in localStorage" hold for the refresh token as well as the access
 *     one. An XSS bug on any page of the origin cannot exfiltrate it.
 *   * `secure` -- HTTPS only. Without it the cookie is sent over cleartext and a
 *     passive observer on the same network takes it.
 *   * `sameSite: 'strict'` -- not sent on any cross-site request, which is the
 *     part that makes 12.4.2's theft detection reachable: a cross-site caller
 *     holding a copied cookie cannot even present it.
 *   * `path` is pinned to the auth routes. The token then never accompanies an
 *     ordinary API call, so an ordinary request that is logged, cached or
 *     forwarded by something in the path does not carry it.
 *
 * `maxAge` is `REFRESH_TOKEN_TTL_DAYS`, the same constant the database uses for
 * `sessions.refresh_expires_at` -- imported, not written out. Two literals of
 * "30 days" in two files is a cookie that outlives its row, or a row that
 * outlives its cookie, and neither failure is visible until a member cannot
 * refresh.
 */
const REFRESH_COOKIE_ATTRIBUTES =
  'Path=/api/v1/auth; HttpOnly; Secure; SameSite=Strict';

function setRefreshCookie(reply: FastifyReply, token: string): void {
  void reply.header(
    'Set-Cookie',
    `${REFRESH_COOKIE}=${token}; ${REFRESH_COOKIE_ATTRIBUTES}; Max-Age=${
      REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60
    }`,
  );
}

function clearRefreshCookie(reply: FastifyReply): void {
  // An empty value with the same attributes, because a browser only replaces a
  // cookie when path and attributes match. Clearing with a different path leaves
  // the original in place, and the member's next refresh succeeds with a token
  // they never see.
  void reply.header(
    'Set-Cookie',
    `${REFRESH_COOKIE}=; ${REFRESH_COOKIE_ATTRIBUTES}; Max-Age=0`,
  );
}

function readRefreshCookie(request: FastifyRequest): string | undefined {
  const header = request.headers.cookie;
  if (header === undefined) {
    return undefined;
  }
  for (const part of header.split(';')) {
    const separator = part.indexOf('=');
    if (separator === -1) {
      continue;
    }
    if (part.slice(0, separator).trim() === REFRESH_COOKIE) {
      return part.slice(separator + 1).trim();
    }
  }
  return undefined;
}

/**
 * 12.4.3 caps a member at five sessions, which is a property of the *list*, not
 * of the flow. So the keys are separate: the address budget bounds one host
 * spraying many addresses, and the address budget alone cannot see a distributed
 * spray at one member.
 *
 * Both are consumed before either is checked, which is the part that is easy to
 * get wrong. If the per-address budget were checked first and the per-account
 * budget only reached when it passed, an attacker could burn the address budget
 * and the account budget would never move -- so a member under attack would have
 * their account budget untouched, protected, and the per-account limit would be
 * the one limit that never fires.
 */
function loginRateLimitKeys(input: { email: string }, clientIp: string): string[] {
  // Keyed on the *normalised* address. If it were keyed on the raw string then
  // `A@x.ng` and `a@x.ng` would be two budgets, and case-insensitivity -- which
  // is why `user_credentials.email` is `citext` -- would hand every attacker two
  // budgets per account for free.
  //
  // No `login:` prefix on the key: the limiter these are consumed by is created
  // with `namespace: 'login'`, which already separates them from the registration
  // counter. A prefix here would produce `...:login:login:addr` and suggest the
  // namespace is not doing its job.
  const normalised = input.email.trim().toLowerCase();
  return [`addr:${clientIp}`, `account:${normalised}`];
}

export function registerSessionRoutes(app: FastifyInstance, deps: SessionRouteDependencies): void {
  const { config, pool, loginLimiter, signer, verifier } = deps;

  /**
   * POST /api/v1/auth/login
   */
  app.post('/api/v1/auth/login', { schema: { body: CREDENTIAL_BODY } }, async (request, reply) => {
    const body = request.body as {
      email: string;
      password: string;
      deviceLabel?: string;
      platform?: string;
    };

    const keys = loginRateLimitKeys(body, request.ip);
    let allowed = true;
    try {
      for (const key of keys) {
        // Not short-circuited: see `loginRateLimitKeys`.
        const result = await loginLimiter.consume(key);
        allowed = allowed && result;
      }
    } catch (error) {
      app.log.error({ err: error }, 'rate limiter unavailable; refusing login');
      return reply.code(503).send({
        error: 'temporarily_unavailable',
        message: 'Sign in is unavailable. Please try again shortly.',
      });
    }

    if (!allowed) {
      const retryAfterSeconds = Math.ceil(config.login.windowMs / 1000);
      void reply.header('Retry-After', String(retryAfterSeconds));
      return reply.code(429).send({
        error: 'rate_limited',
        message: 'Too many sign-in attempts. Please try again later.',
      });
    }

    try {
      const result = await login(pool, signer, { maxSessions: config.login.maxSessions }, {
        email: body.email,
        password: body.password,
        deviceLabel: body.deviceLabel,
        platform: body.platform,
        clientIp: request.ip,
        userAgent: request.headers['user-agent'],
      });

      setRefreshCookie(reply, result.refreshToken);
      return reply.code(200).send({
        // The access token goes in the body because 12.4.1 says "memory only",
        // and a body is the only place a browser client can hold it in memory.
        accessToken: result.accessToken,
        tokenType: 'Bearer',
        expiresIn: 15 * 60,
        userId: result.userId,
        sessionId: result.sessionId,
        accountStatus: result.accountStatus,
        isEmailVerified: result.isEmailVerified,
      });
    } catch (error) {
      if (error instanceof AuthenticationFailedError) {
        // The same body and the same status for an unknown address and a wrong
        // password, which is what keeps the endpoint from being an account
        // enumeration oracle. The distinguishing detail goes to the log, where it
        // is useful, and not to the caller, where it is a tool.
        return reply.code(401).send({ error: 'invalid_credentials' });
      }
      app.log.error({ err: error }, 'login failed');
      return reply.code(500).send({
        error: 'internal_error',
        message: 'Sign in could not be completed.',
      });
    }
  });

  /**
   * POST /api/v1/auth/refresh
   *
   * No body and no rate limit, both deliberately. The token is 256 bits of
   * entropy, so there is nothing to guess; a rate limit here would only make the
   * legitimate client pay for an attacker's requests, and 12.4.2's reuse
   * detection is the control that actually matters. Rate limiting this endpoint
   * is one of the classic ways to turn a working theft control into a denial of
   * service.
   */
  app.post('/api/v1/auth/refresh', async (request, reply) => {
    const presented = readRefreshCookie(request);
    if (presented === undefined) {
      clearRefreshCookie(reply);
      return reply.code(401).send({ error: 'unauthenticated' });
    }

    try {
      const result = await refresh(pool, signer, presented);
      setRefreshCookie(reply, result.refreshToken);
      return reply.code(200).send({
        accessToken: result.accessToken,
        tokenType: 'Bearer',
        expiresIn: 15 * 60,
        userId: result.userId,
        sessionId: result.sessionId,
      });
    } catch (error) {
      if (error instanceof RefreshFailedError) {
        // The cookie is cleared on every refresh failure, including a reuse
        // detection -- the client is going to the login screen either way, and
        // leaving a known-bad token in the browser invites a retry loop that
        // would trip the theft path again.
        clearRefreshCookie(reply);
        return unauthenticated(reply);
      }
      app.log.error({ err: error }, 'refresh failed');
      return reply.code(500).send({
        error: 'internal_error',
        message: 'The session could not be renewed.',
      });
    }
  });

  /**
   * POST /api/v1/auth/logout
   *
   * Requires the access token as well as the cookie, and that is a choice worth
   * naming. The cookie alone would be enough to identify the session, but the
   * access token is what carries a signed `sid`, so requiring both means the
   * session being ended is named by something the server issued and signed
   * rather than by a value the browser holds. A stolen cookie on its own cannot
   * end a session -- it can only be replayed to refresh, which 12.4.2 handles.
   */
  app.post(
    '/api/v1/auth/logout',
    { preHandler: requireAuthentication(verifier) },
    async (request, reply) => {
      const identity = requireIdentity(request);
      try {
        await logout(pool, identity, currentSessionId(request));
      } catch (error) {
        app.log.error({ err: error }, 'logout failed');
        return reply.code(500).send({
          error: 'internal_error',
          message: 'Sign out could not be completed.',
        });
      }
      // The cookie is cleared whether or not the row was revoked, because a
      // member pressing "sign out" wants the browser to forget the token either
      // way, and leaving it would make the next sign-in on this device fail in a
      // confusing way.
      clearRefreshCookie(reply);
      return reply.code(204).send();
    },
  );

  /**
   * GET /api/v1/auth/sessions -- 12.4.3's "see and revoke your active sessions".
   */
  app.get(
    '/api/v1/auth/sessions',
    { preHandler: requireAuthentication(verifier) },
    async (request, reply) => {
      const identity = requireIdentity(request);
      try {
        const sessions = await listSessions(pool, identity, currentSessionId(request));
        return reply.code(200).send({ sessions });
      } catch (error) {
        app.log.error({ err: error }, 'listing sessions failed');
        return reply.code(500).send({
          error: 'internal_error',
          message: 'The session list could not be loaded.',
        });
      }
    },
  );

  /**
   * DELETE /api/v1/auth/sessions/:id
   *
   * Answers 204 whether or not the row was the caller's. See `session.ts` for
   * why that is the correct behaviour rather than a missing 404: a 404 for the
   * caller's own absent id and a 204 for a foreign one would tell an attacker
   * which session ids exist.
   */
  app.delete(
    '/api/v1/auth/sessions/:id',
    {
      preHandler: requireAuthentication(verifier),
      schema: {
        params: {
          type: 'object',
          required: ['id'],
          additionalProperties: false,
          properties: { id: { type: 'string', format: 'uuid' } },
        },
      },
    },
    async (request, reply) => {
      const identity = requireIdentity(request);
      const { id } = request.params as { id: string };
      try {
        const changed = await revokeSession(pool, identity, id);
        if (changed && id === currentSessionId(request)) {
          // Revoking the session this request came from means the client no
          // longer holds a usable refresh cookie, so it is cleared here too.
          // Otherwise the next silent refresh would succeed and the member would
          // find they were still signed in.
          clearRefreshCookie(reply);
        }
        return reply.code(204).send();
      } catch (error) {
        app.log.error({ err: error }, 'session revocation failed');
        return reply.code(500).send({
          error: 'internal_error',
          message: 'The session could not be signed out.',
        });
      }
    },
  );
}
