import type pg from 'pg';
import {
  INVITATION_TTL_HOURS,
  ajoRules,
  assertInvitableEmail,
  feeDisclosure,
  type AjoRules,
  type FeeDisclosure,
  type InvitationRejection,
} from '@ajo/domain';
import { kobo, type Kobo } from '@ajo/domain';
import { ValidationError, generateToken, hashToken } from './identity.js';
import { withIdentity, type Identity } from './db.js';

export interface InvitationContact {
  readonly email?: unknown;
}

export interface CreateInvitationInput {
  readonly ajoId?: unknown;
  readonly contacts?: unknown;
  readonly personalMessage?: unknown;
  readonly expiresInHours?: unknown;
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
  readonly deliverySummary: { readonly delivered: readonly string[]; readonly failed: readonly string[]; readonly note: string };
}

export class InvitationNotAllowedError extends Error {
  constructor() {
    super('only an Ajo organizer may invite members');
    this.name = 'InvitationNotAllowedError';
  }
}

export class InvitationConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'InvitationConflictError';
  }
}

/** The invitation token has been consumed, declined or has expired. */
export class InvitationGoneError extends Error {
  constructor(reason: InvitationRejection) {
    super(`invitation is ${reason}`);
    this.name = 'InvitationGoneError';
  }
}

/** The token does not match any existing invitation. */
export class InvitationNotFoundError extends Error {
  constructor() {
    super('invitation not found');
    this.name = 'InvitationNotFoundError';
  }
}

interface RawInvitation {
  id: string;
  status: string;
  expires_at: Date;
  email: string;
  token_hash: Buffer;
}

interface CreateDbResult {
  id: string;
  email: string;
  expires_at: Date;
}

const EMAIL_CHANNEL: 'email' = 'email';

function isEmailString(value: unknown): value is string {
  if (typeof value !== 'string') return false;
  try {
    assertInvitableEmail(value);
    return true;
  } catch {
    return false;
  }
}

function clampExpiry(hours: number, now: Date): Date {
  const h = Math.max(1, Math.min(720, Number.isFinite(hours) ? Math.trunc(hours) : INVITATION_TTL_HOURS));
  return new Date(now.getTime() + h * 60 * 60 * 1000);
}

function toIso(d: Date): string {
  return d.toISOString();
}

function sqlState(error: unknown): string | undefined {
  if (error && typeof error === 'object') {
    const e = error as { code?: string };
    return e.code;
  }
  return undefined;
}

export async function createInvitations(
  pool: pg.Pool,
  identity: Identity,
  input: CreateInvitationInput,
): Promise<CreateInvitationResult> {
  if ((identity as any).type !== 'member' || !(identity as any).verified) {
    throw new InvitationNotAllowedError();
  }

  const ajoId = typeof input.ajoId === 'string' && input.ajoId.length > 0 ? input.ajoId : null;
  if (ajoId === null) {
    throw new ValidationError('ajoId', 'ajoId is required');
  }
  const contacts = Array.isArray(input.contacts) ? input.contacts : null;
  if (contacts === null || contacts.length === 0) {
    throw new ValidationError('contacts', 'at least one contact is required');
  }

  let personalMessage: string | null = null;
  if (input.personalMessage !== undefined && input.personalMessage !== null) {
    const m = String(input.personalMessage).trim();
    if (m.length > 2000) {
      throw new ValidationError('personalMessage', 'personal message may not exceed 2000 characters');
    }
    personalMessage = m.length === 0 ? null : m;
  }

  const now = new Date();
  const expiresAt = clampExpiry(Number(input.expiresInHours), now);

  const valid: Array<{ email: string }> = [];
  for (const [i, c] of contacts.entries()) {
    const cobj = c && typeof c === 'object' ? (c as Record<string, unknown>) : {};
    const email = cobj['email'];
    if (!isEmailString(email)) {
      throw new ValidationError(`contacts.${i}.email`, 'a valid email is required');
    }
    valid.push({ email: String(email).trim().toLowerCase() });
  }

  const delivered: string[] = [];
  const tokens: InvitationToken[] = [];
  const client = await pool.connect();
  try {
    for (const v of valid) {
      const token = generateToken();
      const tokenHash = hashToken(token);
      try {
        const row = await client.query<CreateDbResult>(
          'SELECT * FROM app.create_invitation($1, $2, $3, $4, $5)',
          [ajoId, v.email, tokenHash, expiresAt, personalMessage],
        );
        const r = row.rows[0];
        if (r) {
          tokens.push({
            id: r.id,
            token,
            channel: EMAIL_CHANNEL,
            status: 'pending',
            expiresAt: toIso(r.expires_at),
          });
          delivered.push(v.email);
        } else {
          throw new InvitationConflictError('could not create invitation');
        }
      } catch (e) {
        const code = sqlState(e);
        if (code === '42501') {
          throw new InvitationNotAllowedError();
        }
        if (code === '23514') {
          const msg = e && typeof e === 'object' && 'message' in e ? String((e as any).message) : 'invalid invitation';
          if (msg.includes('full') || msg.includes('no free') || msg.includes('positions')) {
            throw new InvitationConflictError('Ajo has no free positions');
          }
          if (msg.includes('status') || msg.includes('enrollment') || msg.includes('collecting')) {
            throw new InvitationConflictError('Ajo is not open for enrollment');
          }
          throw new ValidationError('ajoId', 'cannot invite to this Ajo');
        }
        if (code === '23505') {
          const msg = e && typeof e === 'object' && 'message' in e ? String((e as any).message) : '';
          if (msg.includes('one_pending_per_ajo_email')) {
            throw new InvitationConflictError(`an invitation to ${v.email} is already pending`);
          }
          if (msg.includes('already a member')) {
            throw new InvitationConflictError(`${v.email} is already a member of this Ajo`);
          }
          throw new InvitationConflictError('invitation already exists');
        }
        if (e instanceof InvitationNotAllowedError || e instanceof InvitationConflictError) {
          throw e;
        }
        throw new InvitationConflictError('failed to create invitation');
      }
    }
  } finally {
    client.release();
  }

  return {
    invitations: tokens,
    deliverySummary: {
      delivered,
      failed: [],
      note: 'delivery is deferred (E7). Tokens are returned for testing and manual handoff.',
    },
  };
}

export async function listInvitations(_pool: pg.Pool, identity: Identity, ajoId: string): Promise<readonly RawInvitation[]> {
  if ((identity as any).type !== 'member') {
    throw new InvitationNotAllowedError();
  }
  const res = await withIdentity(_pool, identity, async (client: any) => {
    const r = await client.query(
      `SELECT id, status, expires_at, email, token_hash
         FROM invitations
        WHERE ajo_id = $1 AND deleted_at IS NULL
        ORDER BY created_at DESC`,
      [ajoId],
    );
    return r;
  });
  return res.rows;
}

export interface AjoPreview {
  id: string;
  name: string;
  status: string;
  contributionKobo: number;
  currency: string;
  frequencyCode: string;
  collectionDay: string | null;
  durationRounds: number;
  maxMembers: number;
  membersCount: number;
  endsAt: string | null;
}

export interface InvitationPreview {
  ajo: AjoPreview;
  organizer: { name: string };
  positionOptions: readonly number[];
  feeDisclosure: FeeDisclosure;
  rules: AjoRules;
}

interface PreviewJson {
  status: string;
  expiresAt: string | null;
  ajo: {
    id: string;
    name: string;
    status: string;
    contributionKobo: number;
    currency: string;
    frequencyCode: string;
    collectionDay: string | null;
    durationRounds: number;
    maxMembers: number;
    membersCount: number;
    endsAt: string | null;
  };
  organizer: { name: string };
  positionOptions: readonly number[];
}

export async function previewInvitationByToken(_pool: pg.Pool, token: string): Promise<InvitationPreview> {
  const tokenHash = hashToken(token);
  const res = await _pool.query<{ preview: unknown }>(
    'SELECT app.preview_invitation($1) AS preview',
    [tokenHash],
  );
  const preview = res.rows[0]?.preview;
  if (!preview || typeof preview !== 'object') {
    throw new InvitationNotFoundError();
  }
  const p = preview as PreviewJson;
  if (p.status !== 'pending') {
    throw new InvitationGoneError(p.status as InvitationRejection);
  }
  const expires = p.expiresAt ? new Date(p.expiresAt) : null;
  if (expires === null) {
    throw new InvitationGoneError('expired');
  }
  if (expires.getTime() <= Date.now()) {
    throw new InvitationGoneError('expired');
  }
  const contribution = Number(p.ajo.contributionKobo);
  return {
    ajo: {
      ...p.ajo,
      contributionKobo: contribution,
    },
    organizer: p.organizer,
    positionOptions: p.positionOptions,
    feeDisclosure: feeDisclosure(kobo(contribution) as Kobo),
    rules: ajoRules(),
  };
}
