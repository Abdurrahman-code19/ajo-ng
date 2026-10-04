/**
 * Inviting members to an Ajo, and redeeming an invitation -- spec section 11.5.
 *
 * Three endpoints live here, and the split is not cosmetic:
 *
 *   * `POST /api/v1/invitations` mints. The caller must be the *organizer*, and
 *     the write goes through `app.create_invitation` (migration 111), because
 *     `invitations` has no INSERT policy and should not: a policy that let
 *     `ajo_app` insert directly would let any caller name any `ajo_id` and any
 *     `invited_by_user_id`, minting invitations into somebody else's Ajo.
 *   * `GET /api/v1/invitations/:token` previews, and is *anonymous*. An invitee
 *     who has not signed up yet still has to read what they are being asked to
 *     commit to, so this route has no bearer token and calls a SECURITY DEFINER
 *     projection that returns no roster and no pot (FR-INV-003).
 *   * `POST /api/v1/invitations/accept` redeems, and requires a signed-in,
 *     verified member whose own address is the one that was invited.
 *
 * Two spec conflicts are resolved here rather than guessed at, both recorded in
 * migration 111 and in `TODO`:
 *
 *   * Section 11.5's request shape carries a `phoneNumber` and an SMS channel.
 *     The schema addresses an invitation by email and has no phone column, and
 *     there is no SMS provider until `E7-05`. So this is email-only, and a
 *     contact with no addressable email is a 422 naming the field rather than a
 *     silently ignored entry.
 *   * Nothing is sent. `deliverySummary` reports the tokens as delivered-to-
 *     the-caller with a note saying why, instead of pretending an email went
 *     out. Extending `VerificationSender` for one message type is `E7`'s job.
 */
import type pg from 'pg';
import {
  AJO_RULES_VERSION,
  INVITATION_TTL_HOURS,
  ajoRules,
  assertInvitableEmail,
  feeDisclosure,
  isInvitationStatus,
  kobo,
  type AjoRules,
  type FeeDisclosure,
  type InvitationRejection,
  type InvitationStatus,
} from '@ajo/domain';

import { withIdentity, type Identity } from './db.js';
import { generateToken, hashToken, ValidationError } from './identity.js';

/** The raw JSON body, before validation. Every field is unknown on purpose. */
export interface CreateInvitationInput {
  readonly ajoId?: unknown;
  readonly contacts?: unknown;
  readonly personalMessage?: unknown;
  readonly expiresInHours?: unknown;
}

export interface AcceptInvitationInput {
  readonly token?: unknown;
  readonly accept?: unknown;
  readonly rulesAcknowledged?: unknown;
}

export interface InvitationToken {
  readonly id: string;
  readonly token: string;
  readonly channel: 'email';
  readonly status: 'pending';
  readonly expiresAt: string;
}

export interface CreateInvitationResult {
  readonly invitations: readonly InvitationToken[];
  readonly deliverySummary: {
    readonly delivered: readonly string[];
    readonly failed: readonly string[];
    readonly note: string;
  };
}

/** The caller authenticated but may not invite to that Ajo. */
export class InvitationNotAllowedError extends Error {
  constructor() {
    super('only the organizer of this Ajo may invite members to it');
    this.name = 'InvitationNotAllowedError';
  }
}

/** The invitation exists but cannot be acted on in this state. */
export class InvitationConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'InvitationConflictError';
  }
}

/** The token has been accepted, declined, revoked or has expired. */
export class InvitationGoneError extends Error {
  constructor(reason: InvitationRejection) {
    super(reason);
    this.name = 'InvitationGoneError';
  }
}

/** The token matches no invitation at all. */
export class InvitationNotFoundError extends Error {
  constructor() {
    super('that invitation link is not valid');
    this.name = 'InvitationNotFoundError';
  }
}

interface MintedRow {
  id: string;
  expires_at: Date;
}

interface ListedRow {
  id: string;
  status: string;
  email: string;
  expires_at: Date;
  created_at: Date;
}

/** Longest message an organizer may attach, matching `ajos.description`. */
const MAX_MESSAGE = 2000;

/** The ceiling on a requested lifetime, so a token cannot outlive its usefulness. */
const MAX_TTL_HOURS = 30 * 24;

const DELIVERY_NOTE =
  'no message was sent: outbound email is E7. The tokens in this response are the invitation.';

function asEmail(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined;
  try {
    assertInvitableEmail(value);
  } catch {
    return undefined;
  }
  return value.trim();
}

/**
 * The requested lifetime, clamped to something defensible.
 *
 * An absent or nonsensical `expiresInHours` falls back to the spec's 72 hours
 * rather than being an error: the field is a preference, and the default is the
 * documented behaviour. A negative or absurd value is clamped rather than
 * refused for the same reason -- the caller asked for a token, and the safe
 * answer is a shorter one, not an error page.
 */
function expiryFor(hours: unknown, now: Date): Date {
  const requested = typeof hours === 'number' && Number.isFinite(hours) ? Math.trunc(hours) : INVITATION_TTL_HOURS;
  const clamped = Math.min(Math.max(requested, 1), MAX_TTL_HOURS);
  return new Date(now.getTime() + clamped * 60 * 60 * 1000);
}

function sqlState(error: unknown): string | undefined {
  if (error !== null && typeof error === 'object' && 'code' in error) {
    const { code } = error as { code?: unknown };
    if (typeof code === 'string') return code;
  }
  return undefined;
}

function messageOf(error: unknown): string {
  if (error !== null && typeof error === 'object' && 'message' in error) {
    return String((error as { message: unknown }).message);
  }
  return '';
}

/**
 * Turn the function's refusals into the codes the spec names.
 *
 * Asserted on the message as well as the SQLSTATE, because several of these
 * share a code: 42501 means both "not the organizer" and "no such Ajo", and the
 * two must not collapse into one answer that lets a caller probe which ids
 * exist.
 */
function translate(error: unknown, email: string): never {
  switch (sqlState(error)) {
    case '42501':
      throw new InvitationNotAllowedError();
    case '28000':
      throw new InvitationNotAllowedError();
    case '23505': {
      const message = messageOf(error);
      if (message.includes('already a member')) {
        throw new InvitationConflictError(`${email} is already a member of this Ajo`);
      }
      throw new InvitationConflictError(`an invitation to ${email} is already pending`);
    }
    case '23514': {
      const message = messageOf(error);
      if (message.includes('free positions')) {
        throw new InvitationConflictError('this Ajo has no free positions left');
      }
      if (message.includes('closed once')) {
        throw new InvitationConflictError('this Ajo is no longer accepting members');
      }
      throw new InvitationConflictError('that invitation cannot be created');
    }
    default:
      throw error;
  }
}

/**
 * The redemption refusals, as the codes section 11.5 names them.
 *
 * Separate from `translate` because the two paths refuse different things: the
 * mint path refuses who may invite, this one refuses what a token can still do.
 * The distinction that matters most is 410 against 409 -- a link that has been
 * spent is gone (410, and the invitee should stop retrying), while an Ajo with
 * no seats left is a conflict (409, and the invitee may be told to try another
 * Ajo). Both arrive from PL/pgSQL as 23514, so the message is what separates
 * them.
 */
function translateRedemption(error: unknown): never {
  const message = messageOf(error);
  switch (sqlState(error)) {
    case 'P0002':
      throw new InvitationNotFoundError();
    case '28000':
      throw new InvitationNotAllowedError();
    case '42501':
      // "sent to a different address", or a preview the caller may not see.
      throw new InvitationNotAllowedError();
    case '23505':
      throw new InvitationConflictError('you are already a member of this Ajo');
    case '23514': {
      if (message.includes('has expired')) {
        throw new InvitationGoneError('expired');
      }
      if (message.startsWith('this invitation is already')) {
        // The status word is the rejection. Narrowed rather than cast: the
        // database says `already %`, and the words it can say here are exactly
        // the spent states. Anything else is a message I have not taught this
        // function to read, and guessing there would turn a contract question
        // into a wrong status code.
        const spent: InvitationRejection[] = ['accepted', 'declined', 'revoked'];
        const word = message.slice('this invitation is already '.length);
        throw new InvitationGoneError(spent.find((state) => state === word) ?? 'revoked');
      }
      if (message.includes('rules have changed')) {
        throw new InvitationConflictError('the Ajo rules have changed; read them again before joining');
      }
      if (message.includes('no free positions')) {
        throw new InvitationConflictError('this Ajo has no free positions left');
      }
      if (message.includes('no longer taking members') || message.includes('no longer exists')) {
        throw new InvitationConflictError('this Ajo is no longer taking members');
      }
      throw new InvitationConflictError('that invitation cannot be acted on');
    }
    default:
      throw error;
  }
}

/**
 * The verified-and-active gate, read under the caller's own identity.
 *
 * Same shape as `createAjo`'s: reading it here gives a specific 403 rather than
 * catching whichever SQLSTATE the write happened to fail with, and it keeps
 * "your account may not do this" distinguishable from "the database said no".
 */
async function assertVerifiedActive(client: pg.PoolClient, identity: Identity): Promise<void> {
  const gate = await client.query<{ is_email_verified: boolean; status: string }>(
    `SELECT is_email_verified, status::text AS status
       FROM public.users
      WHERE id = $1::uuid
        AND deleted_at IS NULL`,
    [identity.userId],
  );
  const me = gate.rows[0];
  if (me === undefined || !me.is_email_verified || me.status !== 'active') {
    throw new InvitationNotAllowedError();
  }
}

export async function createInvitations(
  pool: pg.Pool,
  identity: Identity,
  input: CreateInvitationInput,
): Promise<CreateInvitationResult> {
  const ajoId = typeof input.ajoId === 'string' && input.ajoId.trim() !== '' ? input.ajoId.trim() : null;
  if (ajoId === null) {
    throw new ValidationError('ajoId', 'ajoId is required');
  }
  if (!Array.isArray(input.contacts) || input.contacts.length === 0) {
    throw new ValidationError('contacts', 'at least one contact is required');
  }

  // Every contact is validated before anything is written, so a request with one
  // bad entry mints nothing. Partial success on a batch of invitations is a
  // state the caller cannot represent and the spec does not ask for.
  const addresses: string[] = [];
  for (const [index, entry] of input.contacts.entries()) {
    const contact = entry !== null && typeof entry === 'object' ? (entry as { email?: unknown }) : {};
    const email = asEmail(contact.email);
    if (email === undefined) {
      throw new ValidationError(`contacts.${index}.email`, 'a valid email address is required');
    }
    addresses.push(email);
  }

  let message: string | null = null;
  if (input.personalMessage !== undefined && input.personalMessage !== null) {
    const trimmed = String(input.personalMessage).trim();
    if (trimmed.length > MAX_MESSAGE) {
      throw new ValidationError(
        'personalMessage',
        `a personal message may not exceed ${MAX_MESSAGE} characters`,
      );
    }
    message = trimmed === '' ? null : trimmed;
  }

  const expiresAt = expiryFor(input.expiresInHours, new Date());

  return withIdentity(pool, identity, async (client) => {
    await assertVerifiedActive(client, identity);

    const minted: InvitationToken[] = [];
    for (const email of addresses) {
      // The plaintext token exists only here, in this loop, on its way out of
      // the response. The database only ever sees `hashToken(token)`, so a
      // leaked `invitations` table cannot be replayed as a set of working links.
      const token = generateToken();
      try {
        const row = await client.query<MintedRow>(
          // `MATERIALIZED` because `SELECT (f(...)).*` calls `f` once per column
          // of the composite it returns -- `invitations` has 17 -- so a plain
          // expansion minted 16 invitations and then collided with the pending
          // unique index, which surfaced to the caller as a 409 saying the
          // address already had one. See the note in `createAjo`.
          `WITH minted AS MATERIALIZED (
             SELECT * FROM app.create_invitation($1, $2, $3, $4, $5) AS i
           )
           SELECT i.id, i.expires_at FROM minted i`,
          [ajoId, email, hashToken(token), expiresAt, message],
        );
        const created = row.rows[0];
        if (created === undefined) {
          throw new Error('create_invitation returned no row');
        }
        minted.push({
          id: created.id,
          token,
          channel: 'email',
          status: 'pending',
          expiresAt: created.expires_at.toISOString(),
        });
      } catch (error) {
        translate(error, email);
      }
    }

    return {
      invitations: minted,
      deliverySummary: {
        delivered: addresses,
        failed: [],
        note: DELIVERY_NOTE,
      },
    };
  });
}

export interface AjoPreview {
  readonly id: string;
  readonly name: string;
  readonly status: string;
  readonly contributionKobo: number;
  readonly currency: string;
  readonly frequencyCode: string;
  readonly collectionDay: string | null;
  readonly durationRounds: number;
  readonly maxMembers: number;
  readonly membersCount: number;
  readonly endsAt: string | null;
}

export interface InvitationPreview {
  readonly ajo: AjoPreview;
  readonly organizer: { readonly name: string };
  readonly positionOptions: readonly number[];
  readonly feeDisclosure: FeeDisclosure;
  readonly rules: AjoRules;
}

interface PreviewProjection {
  readonly status: string;
  readonly expiresAt: string | null;
  readonly ajo: AjoPreview;
  readonly organizer: { readonly name: string };
  readonly positionOptions: readonly number[];
}

/**
 * The anonymous preview.
 *
 * The two things computed here rather than read from the projection -- the fee
 * and the rules -- are computed from the *domain* helpers the charge itself
 * uses, so the number an invitee is shown cannot drift from the number they are
 * later charged. A disclosure that came from a second, independently written
 * formula would be a disclosure that eventually lies.
 */
export async function previewInvitation(pool: pg.Pool, token: string): Promise<InvitationPreview> {
  const row = await pool.query<{ preview: PreviewProjection | null }>(
    'SELECT app.preview_invitation($1) AS preview',
    [hashToken(token)],
  );
  const projection = row.rows[0]?.preview;
  if (projection === null || projection === undefined) {
    throw new InvitationNotFoundError();
  }
  if (!isInvitationStatus(projection.status)) {
    throw new InvitationGoneError('revoked');
  }
  if (projection.status !== 'pending') {
    throw new InvitationGoneError(projection.status as InvitationRejection);
  }
  // The stored status can still be `pending` after the moment it lapsed --
  // nothing sweeps the table on a timer -- so the instant is checked here too.
  const expiresAt = projection.expiresAt === null ? null : Date.parse(projection.expiresAt);
  if (expiresAt === null || Number.isNaN(expiresAt) || expiresAt <= Date.now()) {
    throw new InvitationGoneError('expired');
  }

  const contribution = kobo(projection.ajo.contributionKobo);
  return {
    ajo: projection.ajo,
    organizer: projection.organizer,
    positionOptions: projection.positionOptions,
    feeDisclosure: feeDisclosure(contribution),
    rules: ajoRules(),
  };
}

export interface InvitationSummary {
  readonly id: string;
  readonly status: InvitationStatus;
  readonly email: string;
  readonly expiresAt: string;
  readonly createdAt: string;
}

/**
 * The invitations sent for one Ajo, newest first.
 *
 * No SQLSTATE translation: the read is filtered by the `invitations_select`
 * policy, so an Ajo the caller has no business seeing returns no rows rather
 * than an error, and there is nothing to translate.
 */
export async function listInvitations(
  pool: pg.Pool,
  identity: Identity,
  ajoId: string,
): Promise<readonly InvitationSummary[]> {
  return withIdentity(pool, identity, async (client) => {
    const rows = await client.query<ListedRow>(
      `SELECT id, status::text AS status, email, expires_at, created_at
         FROM public.invitations
        WHERE ajo_id = $1::uuid
          AND deleted_at IS NULL
        ORDER BY created_at DESC`,
      [ajoId],
    );
    return rows.rows.map((row) => ({
      id: row.id,
      status: isInvitationStatus(row.status) ? row.status : 'revoked',
      email: row.email,
      expiresAt: row.expires_at.toISOString(),
      createdAt: row.created_at.toISOString(),
    }));
  });
}

export interface AcceptInvitationResult {
  readonly accepted: true;
  readonly ajoId: string;
  readonly positionNumber: number;
  readonly rulesVersion: number;
}

/**
 * Redeem an invitation: claim a seat, become a member, spend the token.
 *
 * One transaction, because the three writes are one fact. A member row with no
 * claimed seat, or a spent token with no member, is the state where FR-INV-005
 * ("never duplicate a membership") is satisfied by accident rather than by
 * design.
 *
 * `FOR UPDATE` on the invitation and `SKIP LOCKED` on the seat are what make
 * concurrent accepts safe: two invitees racing for one remaining seat cannot
 * both win, because the second statement finds nothing open and is refused
 * rather than handed a seat that is already gone.
 *
 * `ajo_members` has no INSERT policy either, and for the same reason
 * `invitations` has none, so this is a definer function too -- `app.join_ajo`.
 * The email check is *also* done here rather than only in the function: it is
 * the rule that stops one member redeeming another member's link, and it is
 * stated where the route can answer it with a clear 409.
 */
export async function acceptInvitation(
  pool: pg.Pool,
  identity: Identity,
  input: AcceptInvitationInput,
): Promise<AcceptInvitationResult> {
  const token = typeof input.token === 'string' && input.token.trim() !== '' ? input.token.trim() : null;
  if (token === null) {
    throw new ValidationError('token', 'token is required');
  }
  if (input.accept !== true) {
    throw new ValidationError('accept', 'accept must be true to join an Ajo');
  }
  // The acknowledgement is required *before* anything is written, not recorded
  // afterwards: BR-004 is a commitment, and a commitment that can be assumed is
  // not one.
  if (input.rulesAcknowledged !== true) {
    throw new ValidationError(
      'rulesAcknowledged',
      'the Ajo rules must be acknowledged before joining',
    );
  }

  return withIdentity(pool, identity, async (client) => {
    await assertVerifiedActive(client, identity);

    const me = await client.query<{ email: string }>(
      'SELECT email::text AS email FROM public.users WHERE id = $1::uuid',
      [identity.userId],
    );
    const address = me.rows[0]?.email;
    if (address === undefined) {
      throw new InvitationNotAllowedError();
    }

    let row: { ajo_id: string; position_number: number; rules_version: number } | undefined;
    try {
      const joined = await client.query<{
        ajo_id: string;
        position_number: number;
        rules_version: number;
      }>(
        // Materialized for the same reason as `create_invitation` above: a bare
        // `(app.join_ajo(...)).*` would claim a seat three times over.
        `WITH joined AS MATERIALIZED (
           SELECT * FROM app.join_ajo($1, $2, $3) AS j
         )
         SELECT j.ajo_id, j.position_number, j.rules_version FROM joined j`,
        [hashToken(token), address, AJO_RULES_VERSION],
      );
      row = joined.rows[0];
    } catch (error) {
      // Translated inside the transaction, deliberately: throwing from here
      // rolls the claim back, and the caller is told why in the same breath.
      translateRedemption(error);
    }
    if (row === undefined) {
      throw new Error('join_ajo returned no row');
    }

    return {
      accepted: true,
      ajoId: row.ajo_id,
      positionNumber: row.position_number,
      rulesVersion: row.rules_version,
    };
  });
}

export interface DeclineInvitationResult {
  readonly declined: true;
}

/**
 * Decline, which is not the same as ignoring.
 *
 * Declining frees the unique index slot, so the organizer may invite the same
 * address again, and it records that a person was asked and said no -- which is
 * the difference between a pending invite and a silent one.
 */
export async function declineInvitation(
  pool: pg.Pool,
  identity: Identity,
  token: string,
): Promise<DeclineInvitationResult> {
  return withIdentity(pool, identity, async (client) => {
    await assertVerifiedActive(client, identity);

    const me = await client.query<{ email: string }>(
      'SELECT email::text AS email FROM public.users WHERE id = $1::uuid',
      [identity.userId],
    );
    const address = me.rows[0]?.email;
    if (address === undefined) {
      throw new InvitationNotAllowedError();
    }

    try {
      const declined = await client.query<{ ok: boolean }>(
        'SELECT app.decline_invitation($1, $2) AS ok',
        [hashToken(token), address],
      );
      if (declined.rows[0]?.ok !== true) {
        throw new InvitationConflictError('that invitation could not be declined');
      }
    } catch (error) {
      translateRedemption(error);
    }
    return { declined: true };
  });
}