/**
 * The authenticated-request path: bearer token in, `Identity` out.
 *
 * This module is deliberately small and does exactly three things -- verify the
 * token, refuse it if it does not verify, and hand the caller a `users.id`. It
 * does not check the account state, load permissions, or decide whether the
 * caller may do the thing they asked for, and the reasons are worth stating
 * because each one is a decision a reviewer might otherwise expect to find here:
 *
 *   * **No state check.** 12.2's warning is that no state may prevent a member
 *     from receiving money owed to them, and a member who cannot authenticate
 *     cannot be paid. The state is enforced where it is expressed -- the RLS
 *     policies and the money features -- not at the door.
 *   * **No session lookup.** A token issued before a revocation stays valid
 *     until it expires. That is the 15 minutes from 12.4.1, and it is a
 *     deliberate trade: checking the session on every request would make every API
 *     call a database round trip to close a window that is already bounded. A
 *     caller who needs immediate revocation has refresh -- and a reused refresh
 *     token revokes everything, which is 12.4.2's actual control.
 *   * **No permissions.** There are none to check. 12.1's "two independent
 *     layers" means the second layer is the database, and a JWT is not a place to
 *     put it.
 */
import type { FastifyReply, FastifyRequest } from 'fastify';

import { AccessTokenError, type AccessTokenVerifier } from './access-token.js';
import type { Identity } from './db.js';

/**
 * Thrown by the hook when a request has no usable access token.
 *
 * A class, thrown, rather than a status code the hook sends itself. The
 * difference matters: a preHandler that calls `reply.send()` and then returns
 * lets the *handler run anyway*, so the route is entered with no identity and
 * fails somewhere deeper, where the error says something about a null id rather
 * than about the missing token. Throwing stops the chain, and the error handler
 * turns exactly this one class into a 401.
 */
export class UnauthenticatedError extends Error {
  constructor() {
    super('the request carried no valid access token');
    this.name = 'UnauthenticatedError';
  }
}

/**
 * Runs before the handler. Refuses rather than answering, so no route has to
 * remember to check.
 */
export function requireAuthentication(verifier: AccessTokenVerifier) {
  return async (request: FastifyRequest): Promise<void> => {
    const token = bearerToken(request);
    if (token === undefined) {
      throw new UnauthenticatedError();
    }

    try {
      const claims = await verifier.verify(token);
      request.identity = {
        userId: claims.userId,
        actorType: 'member',
      };
      // Kept beside the identity rather than inside it, because it is a different
      // fact: `identity` is who the member is and is what every RLS policy wants,
      // while the session id is which of possibly five sessions this request came
      // from. Folding it in would give every caller a `userId` that could be
      // accidentally overridden with the session id -- the kind of bug that
      // produces a member reading somebody else's rows because the fields were
      // interchangeable.
      request.sessionId = claims.sessionId;
    } catch (error) {
      if (error instanceof AccessTokenError) {
        throw new UnauthenticatedError();
      }
      throw error;
    }
  };
}

declare module 'fastify' {
  interface FastifyRequest {
    identity?: Identity;
    sessionId?: string;
  }
}

/**
 * The request's identity, once `requireAuthentication` has run.
 *
 * Throws rather than returning `undefined`, because a route behind the hook that
 * reads this has a bug -- it is not handling an anonymous request. Failing loudly
 * at that point beats a `?.` that silently produces a query with no member id.
 */
export function requireIdentity(request: FastifyRequest): Identity {
  const identity = request.identity;
  if (identity === undefined) {
    throw new Error('the route requires an identity but none was resolved');
  }
  return identity;
}

/**
 * The session this request's token belongs to.
 *
 * Needed by logout, and by anything else that is about *this* session rather than
 * about the member. It comes from the token's `sid`, which was signed, so it
 * cannot be swapped for another member's session id -- which is what makes
 * "log out" mean this device rather than whichever session the client named.
 */
export function currentSessionId(request: FastifyRequest): string {
  const sessionId = request.sessionId;
  if (sessionId === undefined) {
    throw new Error('the route requires a session id but none was resolved');
  }
  return sessionId;
}

function bearerToken(request: FastifyRequest): string | undefined {
  const header = request.headers.authorization;
  if (header === undefined) {
    return undefined;
  }
  // `Bearer ` exactly, and case-sensitively per RFC 6750. A lenient match here
  // would accept `bearer`, which is harmless in itself, and would also be the
  // natural place to start accepting a second scheme -- and a token in a query
  // string, which must never happen because query strings end up in logs.
  const match = /^Bearer (\S+)$/.exec(header);
  return match?.[1];
}

export function unauthenticated(reply: FastifyReply): FastifyReply {
  // `WWW-Authenticate` is required by RFC 6750 and is what a client uses to know
  // it should refresh rather than re-prompt for a password.
  return reply
    .code(401)
    .header('WWW-Authenticate', 'Bearer error="invalid_token"')
    .send({ error: 'unauthenticated' });
}
