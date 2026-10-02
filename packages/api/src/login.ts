/**
 * Login: the password exchange that mints a session and an access token.
 *
 * The structure here is decided by one property of the flow that is easy to miss:
 * **a failed login must be indistinguishable from a login for an address that does
 * not exist.** Not in its status code, not in its body, not in its timing. An
 * endpoint that answers 401 for a real address and 404 for an unknown one is a
 * free account-enumeration oracle, and it will be used to build the list of
 * members before any password is guessed. So `verifyLoginCredential` and
 * `burnPasswordVerification` exist as a pair: the first does real work for a
 * real address, and for a fake one the second does the same amount of work, and
 * both land in the same `401` with the same body.
 *
 * 12.2 and the "may log in" question
 * ----------------------------------
 * Every account state is allowed to authenticate here, deliberately, including
 * `frozen`, `suspended`, `dormant` and `closed`. The reason is in the spec's own
 * warning: *"No state ever prevents a member from receiving money already owed to
 * them."* A member who cannot authenticate cannot be paid out, so gating login on
 * state would manufacture the exact custody problem the spec refuses to have --
 * and it would do it to the members in the worst states, who are the ones most
 * likely to be owed something.
 *
 * The state is therefore *not* an authentication decision. It is an
 * authorisation one, and it stays that way: the login response reports the state so
 * the client can route, and 12.2's table -- may contribute, may receive payout,
 * may join, may withdraw -- is enforced by RLS and by the money features. One
 * rule at the door is better than five, and the five would be wrong.
 *
 * `pending_verification` is the case that looks like an exception and is not. A
 * member in that state cannot have contributed, so cannot be owed anything, but
 * they do need a session to read their own state and to ask for the verification
 * mail to be resent. Refusing them would be a state machine decision made in the
 * wrong layer.
 */
import type pg from 'pg';

import { generateToken, hashToken, verifyPassword, burnPasswordVerification } from './identity.js';
import type { AccessTokenSigner } from './access-token.js';

export const REFRESH_TOKEN_TTL_DAYS = 30;

export type AccountStatus = 'pending_verification' | 'active' | 'frozen' | 'closed';

export interface LoginInput {
  readonly email: string;
  readonly password: string;
  /** Free text from the client, e.g. "iPhone 15". Used for 12.4.3's session list. */
  readonly deviceLabel: string | undefined;
  /** `web`, `ios` or `android`; the schema's CHECK allows exactly these. */
  readonly platform: string | undefined;
  readonly clientIp: string | undefined;
  readonly userAgent: string | undefined;
}

export interface LoginResult {
  readonly userId: string;
  readonly sessionId: string;
  /** The opaque token, returned once and stored only as a hash by the database. */
  readonly refreshToken: string;
  readonly accessToken: string;
  readonly accountStatus: AccountStatus;
  readonly isEmailVerified: boolean;
}

/**
 * Thrown for every authentication failure a caller is allowed to learn about.
 *
 * One class, not four, and the constructor takes no argument: an internal call
 * site cannot accidentally leak which of the four reasons applied, because there
 * is nowhere to put it. The distinction between "no such member", "wrong
 * password" and "unverified" is available to the *logs*, which is where it
 * belongs, and not to the client.
 */
export class AuthenticationFailedError extends Error {
  constructor() {
    super('the email or password is incorrect');
    this.name = 'AuthenticationFailedError';
  }
}

interface CredentialRow {
  readonly user_id: string;
  readonly argon2_hash: string;
  readonly status: AccountStatus;
  readonly is_email_verified: boolean;
}

/**
 * Reads the hash and state for one address, or nothing.
 *
 * Returns `undefined` rather than throwing so the caller can run the dummy
 * verification and produce the same failure path. The `LIMIT 1` is not
 * defensive noise: `citext` is case-insensitive by construction, so two rows
 * differing only in case would both match, and a login that picked one
 * non-deterministically would be a real authentication bug.
 */
async function readCredential(client: pg.PoolClient, email: string): Promise<CredentialRow | undefined> {
  const result = await client.query<CredentialRow>(
    `SELECT user_id::text, argon2_hash, status, is_email_verified
       FROM app.verify_login_credential($1)`,
    [email],
  );
  return result.rows[0];
}

/**
 * Replaces the member's active session on the same device.
 *
 * 12.4.3: "If the member signs in from a device they have used before, that
 * session is replaced, not duplicated." The database already refuses the
 * duplicate -- `sessions_one_active_per_device` is a partial unique index over
 * `(user_id, platform, device_label)` -- so without this statement a second login
 * on the same device is a unique violation, which surfaces as a 500. The index
 * makes the rule true; this makes it *produce the right outcome* rather than an
 * error.
 *
 * `=` rather than `IS NOT DISTINCT FROM`, deliberately. A client that sends no
 * device label leaves `device_label` NULL, and the index treats those as distinct
 * -- so it permits several such sessions, and replacing them here would be
 * stricter than the invariant the database enforces. They are still bounded: the
 * cap below evicts the oldest at five.
 *
 * Revoked, not deleted, for the reason given in `EVICT_PAST_CAP`: a revoked row
 * presenting its token later is evidence, and evidence is the whole reason
 * `session_rotated_tokens` exists.
 */
const REPLACE_SAME_DEVICE = `
  UPDATE public.sessions
     SET revoked_at = now(),
         revoked_reason = 'replaced'
   WHERE user_id = $1
     AND platform IS NOT DISTINCT FROM $2::text
     AND device_label IS NOT DISTINCT FROM $3::text
     AND revoked_at IS NULL
     AND deleted_at IS NULL`;

/**
 * Evicts sessions until the member is at or under the cap, newest kept.
 *
 * 12.4.3 caps the list at five. Three things make the obvious implementation
 * wrong, and each was a bug here before it was a comment:
 *
 *   * It has to run *after* the new session is inserted. Evicting first means the
 *     new row is not in the count, so the sixth login revokes nothing and leaves
 *     six live sessions -- which is exactly what the test caught.
 *   * It has to count only *live* sessions. A revoked row is evidence, not a
 *     session -- that is why 070's DELETE sets `revoked_at` instead of removing
 *     the row -- so counting them would make a member who has logged in and out
 *     ten times unable to log in again.
 *   * The ordering needs a tiebreaker. `created_at` is `now()`, which is the
 *     *transaction* start time, so two logins can share it, and "the oldest" is
 *     then whichever row the planner returned first. `id` breaks the tie because
 *     it is uuidv7 and therefore time-ordered in the same direction.
 *
 * Revocation is not deletion, here either. The evicted row is exactly the row
 * whose continued use is the theft signal in 12.4.2, so it is revoked with a
 * reason a reader can interpret.
 */
const EVICT_PAST_CAP = `
  UPDATE public.sessions
     SET revoked_at = now(),
         revoked_reason = 'superseded'
   WHERE id IN (
     SELECT id
       FROM public.sessions
      WHERE user_id = $1
        AND revoked_at IS NULL
        AND deleted_at IS NULL
      ORDER BY created_at DESC, id DESC
      OFFSET $2
   )`;

/**
 * Verifies a password, opens a session, and mints an access token.
 *
 * The transaction is opened here rather than through `withIdentity` because the
 * identity is not known at the start -- it is whatever `app.verify_login_credential`
 * returns -- and it is not a `withResolvedIdentity` case either: that helper runs
 * `assumeIdentity` before the work, which needs the `users.id` this call has not
 * read yet. So the two `set_config` calls are spelled out. That is the one place in
 * the API where the GUC-then-role order is written by hand, and the comment at
 * each step says why.
 */
export async function login(
  pool: pg.Pool,
  signer: AccessTokenSigner,
  config: { readonly maxSessions: number },
  input: LoginInput,
): Promise<LoginResult> {
  const refreshToken = generateToken();
  const refreshHash = hashToken(refreshToken);

  // One transaction for the credential read, the password check, the session
  // insert and the eviction. They are only correct together: a session row without
  // a verified password is a usable session, and a verified password without a
  // session is a login that appeared to succeed.
  return loginOnce(pool, signer, config, input, refreshToken, refreshHash);
}

async function loginOnce(
  pool: pg.Pool,
  signer: AccessTokenSigner,
  config: { readonly maxSessions: number },
  input: LoginInput,
  refreshToken: string,
  refreshHash: Buffer,
): Promise<LoginResult> {
  const client = await pool.connect();
  let began = false;
  try {
    await client.query('BEGIN');
    began = true;

    // The credential read happens before the role switch: the function is
    // SECURITY DEFINER and reads `user_credentials` as its owner, and `ajo_app`
    // has no policy allowing it to read that table at all. Running it as
    // `ajo_app` is what migration 101 got wrong.
    const credential = await readCredential(client, input.email);

    let ok: boolean;
    if (credential === undefined) {
      // Same cost as a real verification, so the response time for an unknown
      // address matches the response time for a known one. Skipping this is how
      // enumeration tools work: send one request, read the timing.
      await burnPasswordVerification(input.password);
      ok = false;
    } else {
      // Hash first, plaintext second -- `verifyPassword`'s order, which is
      // `argon2.verify`'s. Passing them the other way round fails closed rather
      // than loudly: argon2 throws on a malformed hash, the catch returns false,
      // and every login on the platform reports a wrong password. The two
      // arguments are both strings, so nothing catches it at compile time.
      ok = await verifyPassword(credential.argon2_hash, input.password);
    }

    if (credential === undefined || !ok) {
      // Rolled back by the catch. No audit row, no rate-limit increment here --
      // those are the route's job, and 12.8 counts attempts, not successes.
      throw new AuthenticationFailedError();
    }

    // Step into the application role as this member before writing the session.
    // The INSERT is authorised by `sessions_insert_own`, which compares
    // `app.user_id` to the row's `user_id`; the database decides the session
    // belongs to the member whose password was just verified. Doing the check in
    // TypeScript and writing as the migrator would duplicate a policy that
    // already exists, and the copy would be the one that drifts.
    await client.query(
      `SELECT set_config('app.user_id', $1, true),
              set_config('app.actor_user_id', $1, true),
              set_config('app.actor_type', 'member', true)`,
      [credential.user_id],
    );
    await client.query('SET LOCAL ROLE ajo_app');

    // Before the insert: `sessions_one_active_per_device` forbids the two
    // coexisting, so the old one has to go first. See `REPLACE_SAME_DEVICE`.
    await client.query(REPLACE_SAME_DEVICE, [
      credential.user_id,
      input.platform ?? null,
      input.deviceLabel ?? null,
    ]);

    const inserted = await client.query<{ id: string }>(
      `INSERT INTO public.sessions (
         user_id, refresh_token_hash, refresh_expires_at,
         device_label, platform, ip_address, user_agent
       ) VALUES ($1, $2, now() + make_interval(days => $3), $4, $5, $6::inet, $7)
       RETURNING id::text`,
      [
        credential.user_id,
        refreshHash,
        REFRESH_TOKEN_TTL_DAYS,
        input.deviceLabel ?? null,
        input.platform ?? null,
        input.clientIp ?? null,
        input.userAgent ?? null,
      ],
    );
    const sessionId = inserted.rows[0]?.id;
    if (sessionId === undefined) {
      throw new Error('the session insert returned no id');
    }

    // After the insert, and passed the real session id rather than a generated
    // one. The function answers "have we seen this device before?" by looking at
    // `sessions` history and excluding the session it is told about, so calling it
    // here means the audit row names a session that exists -- which is what
    // `outbox_events_dedupe_unique` needs, since it is UNIQUE on
    // (event_type, aggregate_id) and an id that matches no session cannot dedupe
    // against anything.
    //
    // Called before the insert instead, with a random id, the two problems are
    // inverse and equally bad: the lookup would not see the new row at all, so
    // every login looks new, and the alert would fire on every single one.
    //
    // It writes an audit row rather than inserting a notification directly, and
    // that indirection is not ceremony. The audit row is inside this transaction,
    // and migration 104's trigger turns it into an outbox event in the same
    // commit -- so the alert cannot be lost between the login committing and a
    // worker noticing, which is the same reason the reuse alarm is enqueued from
    // a trigger rather than from `refresh.ts`.
    await client.query(
      `SELECT app.record_login_new_device($1, $2::uuid, $3, $4, $5::inet, $6)`,
      [
        credential.user_id,
        sessionId,
        input.platform ?? null,
        input.deviceLabel ?? null,
        input.clientIp ?? null,
        input.userAgent ?? null,
      ],
    );

    // After the insert, so the new session is one of the rows being counted. See
    // `EVICT_PAST_CAP`.
    await client.query(EVICT_PAST_CAP, [credential.user_id, config.maxSessions]);

    await client.query('COMMIT');
    began = false;

    // Minted after the commit, and that ordering is not cosmetic. A token signed
    // for a session that then failed to commit is a token the database has no
    // record of -- it would verify, it would pass RLS, and 12.4.2's theft
    // detection would have nothing to compare it against.
    const accessToken = await signer.issue({ userId: credential.user_id, sessionId });

    return {
      userId: credential.user_id,
      sessionId,
      refreshToken,
      accessToken,
      accountStatus: credential.status,
      isEmailVerified: credential.is_email_verified,
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
