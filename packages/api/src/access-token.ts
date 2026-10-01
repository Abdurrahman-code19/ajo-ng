/**
 * Access tokens: a short-lived EdDSA JWT, as section 12.4.1 asks for.
 *
 * 15 minutes, in memory only, never localStorage -- the spec is explicit about
 * both the lifetime and the storage, and both matter for a different reason. The
 * short lifetime is what bounds the damage of a stolen access token, since 12.4.3
 * makes server-side revocation the real control and this is the window in which a
 * revoke cannot be observed. The storage rule is about a class of bug that no
 * amount of expiry fixes: a token in localStorage survives XSS on any page of the
 * origin, so a single injected script reads it and exfiltrates it.
 *
 * Why `jose` and not `node:crypto` directly, since Ed25519 JWS is three lines
 * with a standard library:
 *
 *   * Algorithm confusion is the documented top JWT vulnerability, and the whole
 *     class of it comes from *reading* the `alg` header and choosing a verifier
 *     from it. `jose` takes the allowlist as configuration
 *     (`algorithms: ['EdDSA']`) and structurally cannot be talked into RS256 or
 *     `none`. A hand-rolled verifier has to remember, and forgetting is a
 *     vulnerability rather than a bug report.
 *   * The claim checks are the second thing. `exp` is not a formatting concern: a
 *     verifier that does not read it accepts a token forever, which is silent and
 *     total.
 *
 * For a financial platform's authentication this is the one place where the
 * default answer is "use the audited implementation" and deviating needs a
 * reason stronger than "the dependency felt heavy". `jose` has no runtime
 * dependencies of its own, so the cost of that default is one package.
 *
 * What this module does *not* do, deliberately:
 *
 *   * Authorisation. A valid token proves who the caller is; whether they may do
 *     what they asked for is decided by the RLS policies, which is 12.1's
 *     "two independent layers". Nothing in a JWT is a permission.
 *   * Session state. A token issued before a revocation stays valid until it
 *     expires. That is the 15 minutes, accepted deliberately: the alternative --
 *     a database read on every request -- turns every API call into a round trip
 *     to close a window that is already bounded.
 */
import { generateKeyPairSync, randomUUID } from 'node:crypto';
import { SignJWT, importPKCS8, importSPKI, jwtVerify, errors as joseErrors } from 'jose';

/** 12.4.1: 15 minutes. The one number the spec fixes, and the one that bounds a stolen token. */
export const ACCESS_TOKEN_TTL_SECONDS = 15 * 60;

export const ACCESS_TOKEN_ISSUER = 'ajo-api';
export const ACCESS_TOKEN_AUDIENCE = 'ajo-app';

/**
 * What the token carries.
 *
 * Three claims and no more. `sub` is the member's `users.id`, which is what every
 * RLS policy compares against. `sid` is the session, and it is the one that is not
 * obvious: a member may hold five sessions (12.4.3), and "log out" is meaningless
 * without knowing which one. `jti` is a random id so two tokens minted in the
 * same second for the same session are distinguishable in a log.
 *
 * The things a token is *not* carrying are worth stating because putting them in
 * a token is the standard mistake: no role, no `email`, no `status`. Roles change
 * and are scoped; a role baked into a 15-minute token would outlive the decision
 * to revoke it, and `status` in particular would let a frozen member keep acting
 * for the length of the token. The database holds all of it and is read fresh.
 */
export interface AccessTokenClaims {
  readonly userId: string;
  readonly sessionId: string;
}

export interface AccessTokenSigner {
  /**
   * Mints a token.
   *
   * `now` is injected so a test can assert on a boundary rather than on a race
   * with the clock.
   */
  issue(claims: AccessTokenClaims, now?: Date): Promise<string>;
}

export interface AccessTokenVerifier {
  /**
   * Resolves the claims, or throws `AccessTokenError`.
   *
   * Every failure -- bad signature, expired, wrong audience, malformed -- is the
   * same error on purpose. A verifier that distinguishes them hands an attacker a
   * oracle: "expired" says the token was genuine, which is a free validity check
   * on a stolen one.
   */
  verify(token: string, now?: Date): Promise<AccessTokenClaims>;
}

export class AccessTokenError extends Error {
  constructor() {
    super('the access token is not valid');
    this.name = 'AccessTokenError';
  }
}

export interface SigningKeys {
  /** PEM, PKCS#8 (`-----BEGIN PRIVATE KEY-----`). */
  readonly privateKeyPem: string;
  /** PEM, SPKI (`-----BEGIN PUBLIC KEY-----`). */
  readonly publicKeyPem: string;
}

/**
 * Builds the signer and verifier from one key pair.
 *
 * Async because `jose` imports keys asynchronously, and that is worth surfacing
 * rather than hiding: an un-awaited import is a signer that is a `Promise` where
 * an `AccessTokenSigner` was expected, and the first symptom is a `TypeError` on
 * the first login in production rather than at boot. Awaiting here means the
 * composition root cannot construct a half-ready signer.
 */
export async function createAccessTokenPair(keys: SigningKeys): Promise<{
  readonly signer: AccessTokenSigner;
  readonly verifier: AccessTokenVerifier;
}> {
  // Both imports in one `Promise.all` rather than in sequence: they are
  // independent, and a signer that is ready before the verifier buys nothing.
  const [signer, verifier] = await Promise.all([
    createSigner(keys.privateKeyPem),
    // Deliberately built from the *public* key rather than reusing the private
    // one. An API process that can only verify cannot mint, so a bug that reaches
    // the verifier cannot hand anybody a token. Node derives the public half from
    // a private key, and using it would quietly undo that.
    createVerifier(keys.publicKeyPem),
  ]);
  return { signer, verifier };
}

/**
 * A key pair for development, generated at boot.
 *
 * Exists so that `npm run dev` and the integration suite work with no setup, and
 * it is a foot-gun with a deliberate shape: it is only reachable when
 * `ACCESS_TOKEN_PRIVATE_KEY` is unset, and the configuration loader refuses to
 * take this path in production. Two things go wrong with an ephemeral key in
 * production, and they are different failures:
 *
 *   1. A restart invalidates every issued access token, and with no refresh-token
 *      check at boot the platform logs everybody out on every deploy.
 *   2. Two instances generate two *different* keys. A member who logs in through
 *      one is rejected by the other, so a load balancer produces intermittent
 *      logouts that no single log line explains.
 *
 * (2) is the reason the gate is on the loader and not merely a warning in the
 * docs: an ephemeral key is safe only while there is exactly one process, and
 * nothing else in the codebase knows whether that is true.
 */
export function generateEphemeralSigningKey(): SigningKeys {
  const { privateKey, publicKey } = generateKeyPairSync('ed25519');
  return {
    privateKeyPem: privateKey.export({ type: 'pkcs8', format: 'pem' }).toString(),
    publicKeyPem: publicKey.export({ type: 'spki', format: 'pem' }).toString(),
  };
}

async function createSigner(privateKeyPem: string): Promise<AccessTokenSigner> {
  // A malformed key must fail here, at construction, rather than on the first
  // login -- and the composition root starts once at boot, so this is a startup
  // error and not a request error.
  const key = await importPKCS8(privateKeyPem, 'EdDSA');

  return {
    async issue(claims: AccessTokenClaims, now: Date = new Date()): Promise<string> {
      const issuedAt = Math.floor(now.getTime() / 1000);
      return new SignJWT({
        sid: claims.sessionId,
        jti: randomUUID(),
      })
        .setProtectedHeader({ alg: 'EdDSA', typ: 'JWT' })
        .setSubject(claims.userId)
        .setIssuer(ACCESS_TOKEN_ISSUER)
        .setAudience(ACCESS_TOKEN_AUDIENCE)
        .setIssuedAt(issuedAt)
        .setExpirationTime(issuedAt + ACCESS_TOKEN_TTL_SECONDS)
        .sign(key);
    },
  };
}

async function createVerifier(publicKeyPem: string): Promise<AccessTokenVerifier> {
  const key = await importSPKI(publicKeyPem, 'EdDSA');

  return {
    async verify(token: string, now: Date = new Date()): Promise<AccessTokenClaims> {
      try {
        const { payload } = await jwtVerify(token, key, {
          // The allowlist is the protection, and it is configuration rather than a
          // comparison I have to remember to write. Anything not EdDSA is refused
          // without the verifier looking at the token's own `alg`.
          algorithms: ['EdDSA'],
          issuer: ACCESS_TOKEN_ISSUER,
          audience: ACCESS_TOKEN_AUDIENCE,
          // No tolerance. A token one second past its life is expired, and a
          // clock-tolerance window is a way to make "expired" not true.
          clockTolerance: 0,
          currentDate: now,
        });

        // `sub` is what every RLS policy compares against, so a token without one
        // has to be refused rather than verified with an undefined identity --
        // there is no valid state here where a member has no id.
        if (typeof payload.sub !== 'string' || payload.sub === '') {
          throw new AccessTokenError();
        }
        if (typeof payload['sid'] !== 'string' || payload['sid'] === '') {
          throw new AccessTokenError();
        }

        return { userId: payload.sub, sessionId: payload['sid'] };
      } catch (error) {
        // `AccessTokenError` thrown from inside the try is re-wrapped here, which
        // is fine and intentional: the caller must not be able to tell a
        // structurally invalid token from a badly signed one either.
        if (error instanceof AccessTokenError) {
          throw error;
        }
        if (error instanceof joseErrors.JOSEError) {
          throw new AccessTokenError();
        }
        throw error;
      }
    },
  };
}
