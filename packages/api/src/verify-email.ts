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
import { withIdentity } from './db.js';
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

export async function verifyEmailToken(
  pool: Pool,
  token: string,
): Promise<VerifyResult> {
  const tokenHash = hashToken(token);
  const now = new Date().toISOString();

  /**
   * The token's user is the identity for the transaction, which is read out of
   * the token row by the schema owner.
   *
   * There is no session to authenticate here -- a user who has not yet verified
   * their email has no session -- so the token is the credential, and the row it
   * points at is what the caller is acting as. The `SECURITY DEFINER` function
   * is the only way to read `email_verification_tokens` at all, because the
   * table has no `SELECT` policy for the application role: the token is a
   * bearer secret, and a policy that let a session read its own tokens would
   * let a script on an authenticated page collect them all.
   */
  const claimed = await pool.query<{ user_id: string; already_verified: boolean }>(
    `SELECT user_id, already_verified
       FROM app.claim_email_verification_token($1::bytea, $2::timestamptz)`,
    [tokenHash, now],
  );

  const claim = claimed.rows[0];
  if (claim === undefined) {
    // One message for every reason. See the module comment.
    throw new VerificationError('This verification link is not valid.');
  }

  const { user_id: userId, already_verified: alreadyVerified } = claim;

  if (alreadyVerified) {
    return { userId, alreadyVerified: true };
  }

  // Now acting as the user the token names, so the UPDATE is checked against
  // the same `users_update_own` policy that governs every other member write.
  await withIdentity(pool, { userId, actorType: 'member' }, async (client) => {
    const updated = await client.query(
      `UPDATE users
          SET status = 'active', is_email_verified = true
        WHERE id = $1`,
      [userId],
    );
    if (updated.rowCount === 0) {
      throw new VerificationError('This verification link is not valid.');
    }
  });

  return { userId, alreadyVerified: false };
}
