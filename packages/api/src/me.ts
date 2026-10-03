/**
 * The member behind the access token -- what `GET /me` answers.
 *
 * The app calls this on launch (section 25's performance table), so it is one
 * indexed primary-key lookup, not a graph. It is also the one read whose caller
 * is not choosing a subject: the subject is the token, and the token's `sub` is
 * the `users.id`. That is why there is no id parameter here and no ownership
 * check in TypeScript -- the RLS policies (`users_select_self_or_staff`,
 * `profiles_select_shared_ajo`) already confine the row to the caller, and a
 * second `WHERE user_id = $me` would be a security control living somewhere other
 * than the security controls.
 *
 * The fields are deliberately a subset. This is the member's own view of
 * themselves, which is exactly the place a field gets added "because it would be
 * useful" and quietly becomes part of every response the platform ever emits.
 * `bvn_hash` and `bvn_last4` are not here for that reason: identity data belongs
 * to the verification flow, not to a launch ping.
 */
import type pg from 'pg';

import { withIdentity, type Identity } from './db.js';

export interface Me {
  readonly userId: string;
  readonly email: string;
  readonly phoneE164: string | null;
  readonly status: string;
  readonly isEmailVerified: boolean;
  readonly isPhoneVerified: boolean;
  readonly displayName: string | null;
  readonly preferredLocale: string | null;
  readonly createdAt: string;
  readonly lastLoginAt: string | null;
}

interface MeRow {
  user_id: string;
  email: string;
  phone_e164: string | null;
  status: string;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  display_name: string | null;
  preferred_locale: string | null;
  created_at: Date;
  last_login_at: Date | null;
}

export async function loadMe(
  pool: pg.Pool,
  identity: Identity,
): Promise<Me | undefined> {
  return withIdentity(pool, identity, async (client) => {
    const result = await client.query<MeRow>(
      // The profile join is `LEFT`, and the policy on `profiles` lets a member see
      // their own row, so this is a nil row only for a member whose profile was
      // never created -- which the registration transaction prevents. Left rather
      // than inner so a data gap degrades to a null display name instead of
      // turning a valid session into a 404.
      `SELECT u.id::text        AS user_id,
              u.email::text     AS email,
              u.phone_e164::text AS phone_e164,
              u.status::text    AS status,
              u.is_email_verified,
              u.is_phone_verified,
              p.display_name,
              p.preferred_locale,
              u.created_at,
              u.last_login_at
         FROM public.users u
         LEFT JOIN public.profiles p
                ON p.user_id = u.id
               AND p.deleted_at IS NULL
        WHERE u.id = $1::uuid
          AND u.deleted_at IS NULL`,
      [identity.userId],
    );

    const row = result.rows[0];
    if (row === undefined) {
      return undefined;
    }

    return {
      userId: row.user_id,
      email: row.email,
      phoneE164: row.phone_e164,
      status: row.status,
      isEmailVerified: row.is_email_verified,
      isPhoneVerified: row.is_phone_verified,
      displayName: row.display_name,
      preferredLocale: row.preferred_locale,
      createdAt: row.created_at.toISOString(),
      lastLoginAt: row.last_login_at?.toISOString() ?? null,
    };
  });
}
