/**
 * Refresh: the one endpoint that can end a session, and the one that has to be
 * right about races.
 *
 * `app.claim_refresh_token` is the whole of the correctness argument, and it is in
 * the database rather than here for a specific reason. Rotation is a read, a
 * decision, and a write, and doing it in the application means two concurrent
 * requests both read "this token is live" and both mint successors -- two valid
 * tokens from one, which is precisely the ambiguity 12.4.2 exists to detect. The
 * function takes `FOR UPDATE` on the session row, so the second transaction
 * blocks, wakes up, and finds the first one's spent-token row.
 *
 * That makes the theft case and the legitimate double-tap indistinguishable, and
 * the spec accepts this: 12.4.2 explicitly calls the concurrent case "a real
 * device and an attacker now hold the same lineage". So both are answered the same
 * way -- everything is revoked -- and the client is sent to log in again. The
 * alternative, trying to tell a race from a theft by timing, is not something that
 * can be made reliable, and being wrong in the other direction means a stolen
 * token keeps working.
 *
 * Every failure here is one error. `reused`, an unknown token, an expired one and
 * an idle one all produce the same 401, because a client that could tell "this
 * token was already used" from "this token is not real" learns whether a stolen
 * token is still in circulation.
 */
import type pg from 'pg';

import { hashToken, generateToken } from './identity.js';
import type { AccessTokenSigner } from './access-token.js';
import { REFRESH_TOKEN_TTL_DAYS } from './login.js';

export class RefreshFailedError extends Error {
  constructor() {
    super('the refresh token is not valid');
    this.name = 'RefreshFailedError';
  }
}

export interface RefreshResult {
  readonly userId: string;
  readonly sessionId: string;
  readonly refreshToken: string;
  readonly accessToken: string;
}

type ClaimOutcome = 'rotated' | 'reused' | 'unknown';

interface ClaimRow {
  readonly user_id: string;
  readonly session_id: string;
  readonly outcome: ClaimOutcome;
}

/**
 * Claims the presented token and mints its successor.
 *
 * The replacement token is generated *before* the claim rather than after, and
 * that is a security decision rather than a convenience. The hash the claim
 * stores has to be the hash of a token that will be issued, and it has to be
 * generated in this process. Generating it afterwards would mean either a second
 * UPDATE outside the locked transaction -- reopening the window the function just
 * closed -- or claiming with a token the caller has not yet committed to sending.
 */
export async function refresh(
  pool: pg.Pool,
  signer: AccessTokenSigner,
  presentedToken: string,
  now: Date = new Date(),
): Promise<RefreshResult> {
  const replacement = generateToken();
  const replacementHash = hashToken(replacement);
  const presentedHash = hashToken(presentedToken);

  const client = await pool.connect();
  let began = false;
  try {
    await client.query('BEGIN');
    began = true;

    // No identity and no role switch: this is an unauthenticated caller whose
    // credential is the cookie, and the function decides what it is. Running as
    // `ajo_app` here would be wrong -- there is no member to assume yet, and
    // `sessions` is not readable without one.
    const claimed = await client.query<ClaimRow>(
      `SELECT user_id::text, session_id::text, outcome
         FROM app.claim_refresh_token($1, $2, $3::timestamptz, $3::timestamptz + make_interval(days => $4))`,
      [presentedHash, replacementHash, now, REFRESH_TOKEN_TTL_DAYS],
    );

    const row = claimed.rows[0];

    if (row === undefined || row.outcome === 'unknown') {
      throw new RefreshFailedError();
    }

    if (row.outcome === 'reused') {
      // The theft response has already been written by the function: every
      // session the member holds is revoked and the audit row is there. So this
      // transaction is *committed*, not rolled back, and that is the whole point
      // of the branch. Rolling back would leave the member's other sessions
      // open and the audit row unwritten -- the failure mode the feature exists
      // to prevent, caused by the error handling.
      //
      // It is committed and then reported as a failure, which looks contradictory
      // and is not: the commit persists the *consequence*, and the exception
      // stops the client from receiving a token.
      await client.query('COMMIT');
      began = false;
      throw new RefreshFailedError();
    }

    await client.query('COMMIT');
    began = false;

    // After the commit, for the same reason as login: a token signed for a
    // rotation that then failed to commit would verify and have no record behind
    // it.
    const accessToken = await signer.issue({ userId: row.user_id, sessionId: row.session_id });

    return {
      userId: row.user_id,
      sessionId: row.session_id,
      refreshToken: replacement,
      accessToken,
    };
  } catch (error) {
    if (began) {
      try {
        await client.query('ROLLBACK');
      } catch {
        /* the connection is poisoned; release() will not hand it out again */
      }
    }
    throw error;
  } finally {
    client.release();
  }
}
