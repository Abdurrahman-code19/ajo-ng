/**
 * Consuming an email verification token.
 *
 * Two properties matter and neither is about the happy path.
 *
 * The first is that the lookup is single-use and atomic. `consumed_at` is updated
 * with a `WHERE consumed_at IS NULL` guard and the update's row count is what
 * decides success, so two concurrent requests carrying the same token produce
 * one winner rather than two activations. A read-then-write would let both pass.
 *
 * The second is that every failure mode looks identical from outside. A token
 * that does not exist, one that has already been used, one that has expired and
 * one belonging to an account that was never created all produce the same 400,
 * because distinguishing them would tell an attacker holding a stolen token
 * whether it was worth guessing, and telling a caller that their email is
 * already verified leaks account state on an unauthenticated endpoint.
 */
import type { Pool } from 'pg';
import { IdentityNotResolvedError, withResolvedIdentity } from './db.js';
import { hashToken } from './identity.js';

export class VerificationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'VerificationError';
  }
}

export interface VerifyResult {
  readonly userId: string;
  readonly alreadyVerified: boolean;
}

/** One row of `app.claim_email_verification_token`'s result. */
interface Claim {
  readonly user_id: string;
  readonly already_verified: boolean;
}

const INVALID = 'This verification link is not valid.';

export async function verifyEmailToken(pool: Pool, token: string): Promise<VerifyResult> {
  const tokenHash = hashToken(token);
  const now = new Date().toISOString();

  // The claim is written into the transaction by `resolve` and read by `work`.
  // `work` only runs when the claim exists, because that is what returned the
  // identity, so the definite assignment is real rather than an assumption.
  let claim: Claim | undefined;

  try {
    return await withResolvedIdentity(
      pool,
      async (client) => {
        /**
         * The token's user is the identity for the transaction, read out of the
         * token row by the schema owner.
         *
         * There is no session to authenticate here -- a user who has not yet
         * verified their email has no session -- so the token is the credential,
         * and the row it points at is what the caller is acting as. The
         * `SECURITY DEFINER` function is the only way to read
         * `email_verification_tokens` at all, because no `SELECT` policy lets the
         * application role read it: the token is a bearer secret, and a policy
         * that let a session read its own tokens would let a script on any
         * authenticated page collect them all.
         */
        const claimed = await client.query<Claim>(
          `SELECT user_id, already_verified
             FROM app.claim_email_verification_token($1::bytea, $2::timestamptz)`,
          [tokenHash, now],
        );
        claim = claimed.rows[0];
        if (claim === undefined) {
          return undefined;
        }
        return { userId: claim.user_id, actorType: 'member' as const };
      },
      async (client, identity) => {
        const current = claim as Claim;

        if (current.already_verified) {
          // The token was still valid and has now been spent, but the account was
          // already active. Reported as a success so a double-clicked link is not
          // an error, while the single-use guarantee is still kept underneath.
          return { userId: identity.userId, alreadyVerified: true };
        }

        // Acting as the user the token names, so the UPDATE is checked against
        // the same `users_update_own` policy that governs every other member
        // write. This is in the same transaction as the claim above: if it
        // throws, the token is not left spent. See `withResolvedIdentity`.
        const updated = await client.query(
          `UPDATE users
              SET status = 'active', is_email_verified = true
            WHERE id = $1`,
          [identity.userId],
        );
        if (updated.rowCount === 0) {
          throw new VerificationError(INVALID);
        }

        return { userId: identity.userId, alreadyVerified: false };
      },
    );
  } catch (error) {
    if (error instanceof IdentityNotResolvedError) {
      // One message for every reason. See the module comment.
      throw new VerificationError(INVALID);
    }
    throw error;
  }
}
