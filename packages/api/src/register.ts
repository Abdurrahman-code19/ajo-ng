/**
 * Registration, as section 12.3 states it.
 *
 * The whole thing is one transaction and one identity, and both facts are load
 * bearing. Every row written belongs to the member being created, and every
 * policy in section 9.6 decides by comparing the row against `app.user_id`. So
 * the transaction's identity is the id of the row that does not exist yet, which
 * is why the id is generated before the transaction opens rather than by the
 * column default.
 *
 * That is the seam this file exists to resolve. `users_insert_own` is
 * `WITH CHECK (id = app.request_user_id())`, which is the right rule for an
 * authenticated write and the wrong one for a signup, because at signup there is
 * no user to authenticate. Two shapes solve it:
 *
 *   1. Mint the id first, then act as it. What this does. No policy changes, and
 *      the insert still proves the caller wrote their own row rather than
 *      anybody's -- the policy is not relaxed, it is satisfied.
 *   2. Add a policy keyed on `auth_subject_id` so an insert needs no identity.
 *      This is worse for a reason that is not obvious: `auth_subject_id` is
 *      attacker-supplied at this point, since it is whatever the caller sent, so
 *      the policy would check a value against itself and authorise the insert of
 *      a row for any subject the caller names.
 *
 * The cost of (1) is that a caller with no session can reach `users` at all, so
 * the rate limit in front of this is not defence in depth -- it is the only
 * thing standing between the signup endpoint and an unbounded write path into the
 * identity table. That is why the limit lives on the route and not in this
 * function: a limit in one place is a limit the next caller can forget.
 */
import type { Pool } from 'pg';
import { withIdentity } from './db.js';
import {
  ValidationError,
  generateToken,
  hashPassword,
  hashToken,
  normaliseNigerianPhone,
} from './identity.js';
import { uuidv7 } from './uuid.js';

/** 12.3: 24-hour expiry, single use. Enforced by the columns. */
export const VERIFICATION_TTL_MS = 24 * 60 * 60 * 1000;

/**
 * The document versions being consented to.
 *
 * They are constants rather than a database lookup because a consent record is
 * only evidence if it names the *exact* text that was accepted. When the terms
 * change these change with them, and the change is a new version in the audit
 * trail rather than a silent reinterpretation of the old one.
 */
export const TERMS_VERSION = '2026-01-01';
export const PRIVACY_VERSION = '2026-01-01';

/** Postgres unique-violation. Matched on the code, never on the message. */
const UNIQUE_VIOLATION = '23505';

export class RegistrationConflict extends Error {
  readonly field: 'email' | 'phone';

  constructor(field: 'email' | 'phone') {
    super(
      field === 'email'
        ? 'an account with that email already exists'
        : 'an account with that phone number already exists',
    );
    this.name = 'RegistrationConflict';
    this.field = field;
  }
}

export interface RegisterInput {
  readonly email: string;
  readonly password: string;
  readonly fullName: string;
  readonly phone: string;
  readonly acceptedTerms: boolean;
  readonly acceptedPrivacy: boolean;
  readonly preferredLocale?: string | undefined;
}

export interface RegisterResult {
  readonly userId: string;
  readonly email: string;
  readonly status: 'pending_verification';
  /**
   * The plaintext token, returned to the caller so the composition root can
   * email it. It is the one value in this module that must not reach a log line
   * or an HTTP response body, and the only thing done with it is the mailer call
   * in `app.ts`.
   */
  readonly verificationToken: string;
}

function assertConsent(input: RegisterInput): void {
  // 12.3: "must be explicitly true". Not "must be present" -- a client that sends
  // `acceptedTerms: false`, or omits it, has not consented, and the difference
  // between those two is the difference between a record and a non-record.
  if (input.acceptedTerms !== true) {
    throw new ValidationError('acceptedTerms', 'the terms must be accepted');
  }
  if (input.acceptedPrivacy !== true) {
    throw new ValidationError('acceptedPrivacy', 'the privacy notice must be accepted');
  }
}

function assertPassword(password: string): void {
  // A length floor rather than a composition rule. Composition rules push people
  // toward `Password1!`, and NIST SP 800-63B is explicit that length is the
  // property that matters.
  if (password.length < 12) {
    throw new ValidationError('password', 'a password must be at least 12 characters');
  }
  if (password.length > 200) {
    // Argon2id is deliberately slow, so an unbounded password is a way to spend
    // this process's CPU. 200 is well past any real passphrase.
    throw new ValidationError('password', 'a password may not exceed 200 characters');
  }
}

export async function register(pool: Pool, input: RegisterInput): Promise<RegisterResult> {
  assertConsent(input);
  assertPassword(input.password);

  const email = input.email.trim().toLowerCase();
  if (email === '' || !email.includes('@')) {
    throw new ValidationError('email', 'a valid email address is required');
  }

  const fullName = input.fullName.trim();
  if (fullName === '') {
    throw new ValidationError('fullName', 'a full name is required');
  }

  // Normalised before anything is written, so the uniqueness check below and the
  // stored value are the same comparison. See normaliseNigerianPhone.
  const phone = normaliseNigerianPhone(input.phone);

  // Hashed before the transaction, not inside it. Argon2id takes tens of
  // milliseconds by design, and holding a transaction open across it keeps a
  // connection and a snapshot pinned for the duration -- under a burst of
  // signups that is the difference between a queue and an outage.
  const passwordHash = await hashPassword(input.password);

  const userId = uuidv7();
  const verificationToken = generateToken();

  // One transaction, so a failure at any point leaves nothing behind.
  // `withIdentity` rolls back, and the audit rows the consent function wrote roll
  // back with it -- which is the correct behaviour here and worth being explicit
  // about, because "we recorded consent and then the insert failed" is the
  // opposite of what an evidence trail should say.
  return withIdentity(pool, { userId, actorType: 'member' }, async (client) => {
    // 23505 on either unique index is the same answer to the caller, but the two
    // are distinguished internally so the right field is reported. Which of the
    // two is *not* disclosed beyond the field name, and the field name is what
    // the client sent.
    try {
      await client.query(
        `INSERT INTO users (id, auth_subject_id, email, phone_e164, status)
         VALUES ($1, NULL, $2, $3, 'pending_verification')`,
        [userId, email, phone],
      );
    } catch (error) {
      if ((error as { code?: string }).code === UNIQUE_VIOLATION) {
        throw new RegistrationConflict(
          (error as { constraint?: string }).constraint?.includes('phone') ? 'phone' : 'email',
        );
      }
      throw error;
    }

    await client.query(
      `INSERT INTO profiles (user_id, display_name, preferred_locale)
       VALUES ($1, $2, $3)`,
      [userId, fullName, input.preferredLocale ?? 'en-NG'],
    );

    // The hash goes in as a parameter and is never logged, echoed, or returned.
    // `user_credentials` has no SELECT policy at all, so it cannot be read back
    // out through this role even by a bug in this file.
    await client.query(
      `INSERT INTO user_credentials (user_id, argon2_hash) VALUES ($1, $2)`,
      [userId, passwordHash],
    );

    // The token is stored hashed, so the row is useless if the table is disclosed.
    // The plaintext exists in this scope and in the email, and leaves in neither
    // a log line nor an API response body.
    await client.query(
      `INSERT INTO email_verification_tokens (user_id, token_hash, expires_at)
       VALUES ($1, $2, now() + interval '24 hours')`,
      [userId, hashToken(verificationToken)],
    );

    // Two rows, not one boolean. The requirement in 12.3 is that the boolean
    // *and* a timestamp are recorded with the document version, and one row per
    // document is what makes "accepted the privacy notice" independently
    // checkable from "accepted the terms".
    //
    // This is a SECURITY DEFINER function, because `audit_logs` grants INSERT to
    // no application role and the alternative -- granting it -- would make forged
    // audit rows possible. It takes no subject id, so it can only ever record
    // for the caller.
    await client.query(
      `SELECT app.record_consent('terms', $1, true),
              app.record_consent('privacy', $2, true)`,
      [TERMS_VERSION, PRIVACY_VERSION],
    );

    return {
      userId,
      email,
      status: 'pending_verification' as const,
      verificationToken,
    };
  });
}
