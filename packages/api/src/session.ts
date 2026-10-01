/**
 * Session listing and revocation -- 12.4.3's `GET /auth/sessions` and
 * `DELETE /auth/sessions/:id`.
 *
 * Both run as the member, through the `sessions` RLS policies, and neither one
 * checks ownership in TypeScript. That is the point of the arrangement: a
 * `WHERE user_id = $me` in application code is a security control that lives
 * somewhere other than the security controls, and it is the copy that drifts.
 * `sessions_select_own` and `sessions_update_own` already say what a member may
 * read and write, and this module cannot be used to bypass them.
 *
 * The consequence, and it is worth stating because it looks like a bug: revoking
 * a session that is not the caller's *succeeds* and changes nothing. `UPDATE`
 * under a `USING` clause that matches no visible row updates nothing and reports
 * success, which is the correct behaviour -- a member learns nothing about whether
 * a session id exists, so "not yours" and "does not exist" have to be the same
 * answer. Returning 404 for the caller's own missing id and 204 for a foreign one
 * would turn this endpoint into an existence oracle for session ids.
 */
import type pg from 'pg';

import { withIdentity, type Identity } from './db.js';

export interface SessionSummary {
  readonly id: string;
  readonly deviceLabel: string | null;
  readonly platform: string | null;
  readonly ipAddress: string | null;
  readonly createdAt: string;
  readonly lastActiveAt: string;
  readonly expiresAt: string;
  readonly isCurrent: boolean;
}

export async function listSessions(
  pool: pg.Pool,
  identity: Identity,
  currentSessionId: string,
): Promise<SessionSummary[]> {
  return withIdentity(pool, identity, async (client) => {
    // `revoked_at IS NULL` rather than relying on the policy: the policies select
    // a member's rows, not a member's *live* rows, and a revoked row is
    // deliberately still readable so the list can show what was signed out.
    // Excluding them here is the API's decision about which rows are sessions.
    const result = await client.query<{
      id: string;
      device_label: string | null;
      platform: string | null;
      ip_address: string | null;
      created_at: Date;
      last_active_at: Date;
      refresh_expires_at: Date;
    }>(
      `SELECT id::text, device_label, platform, ip_address::text,
              created_at, last_active_at, refresh_expires_at
         FROM public.sessions
        WHERE revoked_at IS NULL
          AND deleted_at IS NULL
        ORDER BY created_at DESC`,
    );

    return result.rows.map((row) => ({
      id: row.id,
      deviceLabel: row.device_label,
      platform: row.platform,
      ipAddress: row.ip_address,
      createdAt: row.created_at.toISOString(),
      lastActiveAt: row.last_active_at.toISOString(),
      expiresAt: row.refresh_expires_at.toISOString(),
      isCurrent: row.id === currentSessionId,
    }));
  });
}

/**
 * Revokes a session. Returns whether a row was actually changed.
 *
 * The boolean is for the *caller's* convenience and logging. It is never put in
 * the response body, for the reason in the module comment.
 */
export async function revokeSession(
  pool: pg.Pool,
  identity: Identity,
  sessionId: string,
): Promise<boolean> {
  return withIdentity(pool, identity, async (client) => {
    const result = await client.query(
      `UPDATE public.sessions
          SET revoked_at = now(),
              revoked_reason = 'signed_out'
        WHERE id = $1::uuid
          AND revoked_at IS NULL`,
      [sessionId],
    );

    return (result.rowCount ?? 0) > 0;
  });
}

/**
 * Revokes the caller's own current session, for `POST /auth/logout`.
 *
 * Takes the session id from the verified access token rather than from the route
 * or the body. A logout that revokes "the session id in the request" would let a
 * caller with a valid access token sign out *any* of their own sessions by naming
 * it -- harmless -- and, if the id ever came from a body field, something worse.
 * The token is the credential, so the token says which session this is.
 */
export async function logout(pool: pg.Pool, identity: Identity, sessionId: string): Promise<boolean> {
  return revokeSession(pool, identity, sessionId);
}
