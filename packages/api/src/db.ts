/**
 * The database connection, and the one thing that must never be got wrong about it.
 *
 * The pool connects as `ajo_api`, which is NOSUPERUSER, NOBYPASSRLS, and holds
 * `ajo_app` as a member. Every statement that touches member data therefore runs
 * inside `withIdentity`, which sets the identity GUCs and then does
 * `SET LOCAL ROLE ajo_app` inside a transaction.
 *
 * The order of those two operations is not a style preference. It was found by
 * the migration test suite, which had to discover it twice: the GUC belongs to
 * the session, and the role change resets the session's privilege context, so a
 * GUC set after `SET ROLE` is not what the policy then reads. See
 * `as_role` in `scripts/test_migrations.py`, which does it the other way round
 * and is the reason this file is written this way.
 *
 * `SET LOCAL ROLE` rather than `SET ROLE` because the whole thing is inside an
 * explicit transaction. If the callback throws, `ROLLBACK` releases the role
 * change along with the work, so a connection returned to the pool is not still
 * acting as somebody.
 */
import pg from 'pg';

const { Pool } = pg;
export type { PoolClient, QueryResult, QueryResultRow } from 'pg';

export interface DatabaseConfig {
  readonly host: string;
  readonly port: number;
  readonly database: string;
  readonly user: string;
  readonly password: string;
  readonly max: number;
}

/** The role member data is read and written as. Not configurable on purpose. */
export const APP_ROLE = 'ajo_app';

/**
 * `audit_logs.actor_type`, which is a CHECK constraint, not a free-text field.
 *
 * The allowed values are `user`, `system`, `service` and `webhook` -- the
 * database's vocabulary, which is the only one that matters here because the
 * constraint rejects anything else. This is the *kind* of actor, not their
 * permissions: a platform support agent acting through the API is still a `user`
 * as far as the audit trail is concerned, and the fact that they hold the
 * `support` role is recorded separately in `actor_role_code` by the trigger,
 * which derives it from the database rather than being told.
 *
 * The first version of this type said `member | staff`, which was wrong and was
 * caught by the integration test rather than by the type checker -- the
 * constraint is on a value that only meets a string at runtime.
 */
/**
 * `app.actor_type`, which the schema calls `app.request_actor_type()`.
 *
 * This is the *policy* vocabulary, and it is not the same as
 * `audit_logs.actor_type`. The two are easy to conflate and the confusion is
 * silent on one side and a 500 on the other:
 *
 *   * the GUC is `'anon' | 'member'`, and it is what `users_update_own` and
 *     `profiles_update_own` compare against, so a member update is authorised
 *     only when this is exactly `'member'`
 *   * the `audit_logs.actor_type` column is a CHECK constraint allowing
 *     `user | system | service | webhook`, where the human equivalent of
 *     `'member'` is `'user'`
 *
 * So the value written here is `'member'`, and the mapping to the column's
 * vocabulary happens inside the SECURITY DEFINER function that writes the audit
 * row -- not here, because nothing else in the API writes audit rows.
 */
export type ActorType = 'anon' | 'member';

export interface Identity {
  /**
   * The `users.id` every policy compares the row against.
   *
   * There is no "no identity" option. A statement that needs to touch member
   * data without a caller to attribute it to is the thing this layer exists to
   * prevent, and representing that as `null` would put it one careless call site
   * away. Service work belongs in a SECURITY DEFINER function, which states its
   * own privilege explicitly instead of arriving through this door.
   */
  readonly userId: string;
  readonly actorType: ActorType;
}

export function createPool(config: DatabaseConfig): pg.Pool {
  return new Pool({
    host: config.host,
    port: config.port,
    database: config.database,
    user: config.user,
    password: config.password,
    max: config.max,
    // A connection that has been sitting in the pool across a database restart
    // fails on first use, and the error that surfaces is "terminating
    // connection due to administrator command" -- which reads like a database
    // problem rather than a stale socket. Reconnecting hides that entirely.
    idleTimeoutMillis: 30_000,
  });
}

/**
 * Thrown when a transaction's identity could not be resolved from the credential
 * it was given -- currently only a rejected email-verification token. It exists
 * so `withResolvedIdentity` can roll back and tell the caller "no identity",
 * without the caller having to distinguish that from a database error.
 */
export class IdentityNotResolvedError extends Error {
  constructor() {
    super('no identity could be resolved for this transaction');
    this.name = 'IdentityNotResolvedError';
  }
}

/**
 * Sets the transaction's identity and steps into the application role.
 *
 * The order is the point and must not be rearranged: the GUC is set first, then
 * `SET LOCAL ROLE`. See the module comment -- a GUC set after the role change is
 * not what the policy reads. Exported so a caller that has to discover its
 * identity mid-transaction (verification) uses the same ordering as everybody
 * else rather than reproducing it.
 */
export async function assumeIdentity(
  client: pg.PoolClient,
  identity: Identity,
): Promise<void> {
  // `true` for is_local: the identity is scoped to this transaction, so a
  // pooled connection can never carry one caller's identity into the next
  // request's. That is the failure this whole layer is guarding against, and
  // a session-scoped GUC would reintroduce it silently.
  //
  // `app.actor_user_id` is set as well as `app.user_id` because they are not
  // the same GUC. The policies read `app.user_id`; `app.audit_row()` reads
  // `app.actor_user_id`. Setting only the first produces audit rows with a
  // null actor, which is a correct record of a system action and a useless
  // record of a person.
  await client.query(
    `SELECT set_config('app.user_id', $1, true),
            set_config('app.actor_user_id', $1, true),
            set_config('app.actor_type', $2, true)`,
    [identity.userId, identity.actorType],
  );

  await client.query(`SET LOCAL ROLE ${APP_ROLE}`);
}

export async function withIdentity<T>(
  pool: pg.Pool,
  identity: Identity,
  work: (client: pg.PoolClient) => Promise<T>,
): Promise<T> {
  return withResolvedIdentity(
    pool,
    async () => identity,
    (client) => work(client),
  );
}

/**
 * Like `withIdentity`, for the one flow whose identity is not known until the
 * transaction has already started.
 *
 * Email verification is that flow: the token is the credential, and the user it
 * names can only be read by a `SECURITY DEFINER` function -- so the identity
 * arrives from inside the transaction, after that function has run.
 *
 * It exists as a separate entry point rather than as more code in
 * `verify-email.ts` for one reason: the claim and the activation must be the
 * same transaction. Consuming the token and activating the account are two
 * writes that are only correct together, and doing the first in its own
 * autocommitted statement is what left a failed activation with a spent token
 * and an unverified account -- a dead end for the user, with no way forward but
 * re-registering.
 *
 * `resolve` returning `undefined` means the credential was rejected; the caller
 * gets `IdentityNotResolvedError` after a rollback, and should translate it to
 * whatever it tells an unauthenticated caller, which must not distinguish the
 * rejection reasons.
 */
export async function withResolvedIdentity<T>(
  pool: pg.Pool,
  resolve: (client: pg.PoolClient) => Promise<Identity | undefined>,
  work: (client: pg.PoolClient, identity: Identity) => Promise<T>,
): Promise<T> {
  const client = await pool.connect();
  let began = false;
  try {
    await client.query('BEGIN');
    began = true;

    const identity = await resolve(client);
    if (identity === undefined) {
      throw new IdentityNotResolvedError();
    }

    await assumeIdentity(client, identity);

    const result = await work(client, identity);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    if (began) {
      // Best effort, and deliberately not awaited-then-rethrown: the original
      // error is the one worth reporting, and a connection whose rollback also
      // fails is already being discarded by `release`.
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
