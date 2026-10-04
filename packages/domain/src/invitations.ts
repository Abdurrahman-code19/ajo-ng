/**
 * Invitations -- `POST /api/v1/invitations`, spec section 11.5.
 *
 * This module holds the parts of an invitation that must be the same for every
 * client and must be true without a database: what states an invitation can be
 * in, how long one stays usable, what the fee disclosure adds up to, and the
 * clauses the invitee is shown before they join.
 *
 * It deliberately does *not* mint the token. A token is 256 bits of randomness
 * and a hash, which is a property of the process that issues it, not of the
 * domain -- the same split `identity.ts` makes for the refresh and verification
 * tokens.
 *
 * The one number here the spec flags as unsettled is the invitation lifetime;
 * section 11.5 records it as an open decision and names 72 hours as the current
 * assumption. It lives in one constant so the decision, when it is made, is a
 * one-line change rather than a hunt.
 */
import { AjoRuleError } from './ajo-state.js';
import { serviceFee, totalCharge, type Kobo } from './money.js';

/** `invitation_status`, which the schema owns. Spelled to match the enum. */
export type InvitationStatus = 'pending' | 'accepted' | 'declined' | 'expired' | 'revoked';

export const INVITATION_STATUSES: readonly InvitationStatus[] = [
  'pending',
  'accepted',
  'declined',
  'expired',
  'revoked',
];

export function isInvitationStatus(value: unknown): value is InvitationStatus {
  return typeof value === 'string' && (INVITATION_STATUSES as readonly string[]).includes(value);
}

/**
 * How long an invitation stays usable, in hours.
 *
 * Section 11.5 states 72 hours and marks the value an open decision. It is here,
 * named, rather than inlined at the route, because the open decision is about
 * this number and a reader looking for it should find a constant and not a
 * literal buried in a handler.
 */
export const INVITATION_TTL_HOURS = 72;

/** The minimum an invitation needs to be judged usable. */
export interface InvitationState {
  readonly status: InvitationStatus;
  readonly expiresAt: Date;
}

/** Why an invitation cannot be used. `undefined` means it can. */
export type InvitationRejection = 'expired' | 'accepted' | 'declined' | 'revoked';

/**
 * Whether an invitation is still usable, and if not, why.
 *
 * `expired` is derived rather than stored: a `pending` row whose `expires_at`
 * has passed is expired even though its status column still says `pending`,
 * because nothing sweeps the table on a timer. Reading it this way means the
 * answer is right at the instant it is asked, not at the instant some job last
 * ran. The other four states are stored and authoritative.
 */
export function invitationRejection(
  state: InvitationState,
  now: Date = new Date(),
): InvitationRejection | undefined {
  if (state.status === 'pending') {
    return state.expiresAt.getTime() <= now.getTime() ? 'expired' : undefined;
  }
  // accepted, declined, expired, revoked -- every non-pending status is terminal
  // and is its own reason.
  return state.status;
}

export function isInvitationUsable(state: InvitationState, now: Date = new Date()): boolean {
  return invitationRejection(state, now) === undefined;
}

/**
 * The three amounts the invitee must see, as three separate figures.
 *
 * BR-011 requires the fee to be disclosed before consent, and FR-JOIN-003
 * requires the contribution, the fee and the total to be displayed as three
 * separate amounts. Returning them together, computed by the same functions the
 * ledger uses, is what keeps the disclosure from drifting away from the charge.
 */
export interface FeeDisclosure {
  readonly contributionKobo: Kobo;
  readonly feeKobo: Kobo;
  readonly totalChargeKobo: Kobo;
}

export function feeDisclosure(contribution: Kobo): FeeDisclosure {
  return {
    contributionKobo: contribution,
    feeKobo: serviceFee(contribution),
    totalChargeKobo: totalCharge(contribution),
  };
}

/**
 * One clause of the Ajo rules, tagged with the business rule it comes from.
 *
 * The tag is not decoration: it is what lets a later reading of the rules trace
 * a clause back to the requirement it discharges instead of to a paragraph
 * somebody liked. The wording is the domain's; the obligations are the spec's.
 */
export interface AjoRule {
  readonly code: string;
  readonly text: string;
}

/**
 * The version of the rules text. Bump it when a clause changes, because a member
 * consented to a version and not to "the rules" -- an acknowledgement that
 * cannot say what was agreed is not evidence of anything.
 */
export const AJO_RULES_VERSION = 1;

/**
 * The clauses an invitee is shown before joining, and acknowledges on accept.
 *
 * Kept short on purpose. These are the five things the spec says must be
 * disclosed at the point of commitment (BR-001, BR-002, BR-004, BR-008,
 * BR-011), in plain language, not the full terms of service.
 */
export const AJO_RULES: readonly AjoRule[] = [
  {
    code: 'BR-004',
    text: 'Joining commits you to pay every remaining round until the Ajo completes, or until an approved replacement takes your position.',
  },
  {
    code: 'BR-008',
    text: 'The organizer runs the Ajo but is not a guarantor: they are not responsible for paying anyone else\u2019s share.',
  },
  {
    code: 'BR-002',
    text: 'The payout order is provisional until the Ajo activates. After activation no position can be changed except by an approved replacement.',
  },
  {
    code: 'BR-001',
    text: 'Enrollment lasts five days. If every position is not filled when the window closes, the Ajo is cancelled and every contribution is refunded in full.',
  },
  {
    code: 'BR-011',
    text: 'A 2% service fee is charged on top of each contribution and is shown above before you join. It never reduces the amount paid out.',
  },
];

export interface AjoRules {
  readonly version: number;
  readonly clauses: readonly AjoRule[];
}

export function ajoRules(): AjoRules {
  return { version: AJO_RULES_VERSION, clauses: AJO_RULES };
}

/**
 * Validate an invited email address.
 *
 * Shape only, and deliberately loose: the database column is `citext`, so the
 * comparison is case-insensitive, but deciding whether an address is deliverable
 * by a stricter regex mostly decides wrongly. The one structural property worth
 * requiring is a single `@` with something on each side.
 */
export function assertInvitableEmail(email: string): void {
  const trimmed = email.trim();
  const at = trimmed.indexOf('@');
  if (at <= 0 || at !== trimmed.lastIndexOf('@') || at === trimmed.length - 1) {
    throw new AjoRuleError('an invitation needs a valid email address');
  }
}
