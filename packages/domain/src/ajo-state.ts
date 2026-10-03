/**
 * Ajo lifecycle state machine.
 *
 * Modelled as a discriminated union so the compiler rejects code that handles a
 * state that cannot occur, plus an explicit transition table so an illegal
 * transition is a thrown error at runtime rather than a corrupted Ajo in
 * production.
 *
 * Every rule that affects money or a member's rights lives here, in the domain,
 * never in a route handler or a component. The frontend is a view; it is not
 * trusted to enforce this.
 */

import { MoneyError, type Kobo } from './money.js';

export type AjoStatus =
  | 'DRAFT'
  | 'ENROLLMENT'
  | 'ACTIVE'
  | 'ROUND_IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLING'
  | 'CANCELLED'
  | 'FROZEN';

export type AjoEvent =
  | { readonly type: 'OPEN_ENROLLMENT' }
  | { readonly type: 'CLOSE_ENROLLMENT' }
  | { readonly type: 'ACTIVATE' }
  | { readonly type: 'START_ROUND'; readonly roundNumber: number }
  | { readonly type: 'COMPLETE_ROUND'; readonly roundNumber: number }
  | { readonly type: 'FINISH' }
  | { readonly type: 'FREEZE'; readonly reason: string }
  | { readonly type: 'UNFREEZE' }
  | { readonly type: 'CANCEL'; readonly reason: string };

export interface AjoState {
  readonly status: AjoStatus;
  readonly roundNumber: number;
  readonly totalRounds: number;
  readonly frozenReason?: string;
  readonly cancellationReason?: string;
  readonly since: Date;
}

export type AjoStateEvent =
  | 'created'
  | 'opened_enrollment'
  | 'activated'
  | 'round_started'
  | 'round_completed'
  | 'completed'
  | 'frozen'
  | 'unfrozen'
  | 'cancelled';

export class AjoRuleError extends Error {
  override readonly name = 'AjoRuleError';
}

/** Transitions that are legal, expressed as an explicit allow-list. */
const ALLOWED: Record<AjoStatus, readonly AjoEvent['type'][]> = {
  DRAFT: ['OPEN_ENROLLMENT', 'CANCEL'],
  ENROLLMENT: ['CLOSE_ENROLLMENT', 'CANCEL', 'FREEZE'],
  ACTIVE: ['START_ROUND', 'FREEZE', 'CANCEL'],
  ROUND_IN_PROGRESS: ['COMPLETE_ROUND', 'FREEZE', 'CANCEL'],
  COMPLETED: [],
  CANCELLING: ['CANCEL', 'FREEZE'],
  CANCELLED: [],
  FROZEN: ['UNFREEZE', 'CANCEL'],
};

export function canTransition(status: AjoStatus, event: AjoEvent): boolean {
  return ALLOWED[status].includes(event.type);
}

export function availableEvents(status: AjoStatus): readonly AjoEvent['type'][] {
  return ALLOWED[status];
}

/**
 * Emit the domain event corresponding to a lifecycle change.
 *
 * Exported so the application layer can write these to the audit log and outbox
 * without re-deriving the mapping, which keeps the event stream and the state
 * machine from drifting apart.
 */
export function stateEvent(type: AjoStateEvent, at: Date = new Date()): { type: AjoStateEvent; at: Date } {
  return { type, at };
}

export function transition(
  current: AjoState,
  event: AjoEvent,
  now: Date = new Date(),
): AjoState {
  if (!canTransition(current.status, event)) {
    throw new AjoRuleError(
      `illegal transition: cannot apply ${event.type} while Ajo is ${current.status}. ` +
        `Allowed here: ${ALLOWED[current.status].join(', ') || 'none (terminal state)'}`,
    );
  }

  const base = { ...current, since: now };

  switch (event.type) {
    case 'OPEN_ENROLLMENT':
      return { ...base, status: 'ENROLLMENT' };
    case 'CLOSE_ENROLLMENT':
      return { ...base, status: 'ACTIVE' };
    case 'ACTIVATE':
      return { ...base, status: 'ACTIVE' };
    case 'START_ROUND':
      if (event.roundNumber !== current.roundNumber + 1) {
        throw new AjoRuleError(
          `rounds must advance by exactly one: expected ${current.roundNumber + 1}, received ${event.roundNumber}`,
        );
      }
      return { ...base, status: 'ROUND_IN_PROGRESS', roundNumber: event.roundNumber };
    case 'COMPLETE_ROUND':
      if (current.status !== 'ROUND_IN_PROGRESS') {
        throw new AjoRuleError('only a round in progress can be completed');
      }
      if (event.roundNumber !== current.roundNumber) {
        throw new AjoRuleError(
          `round mismatch: Ajo is on round ${current.roundNumber}, cannot complete ${event.roundNumber}`,
        );
      }
      if (current.roundNumber >= current.totalRounds) {
        return { ...base, status: 'COMPLETED' };
      }
      return { ...base, status: 'ACTIVE' };
    case 'FINISH':
      return { ...base, status: 'COMPLETED' };
    case 'FREEZE': {
      if (event.reason.trim() === '') {
        throw new AjoRuleError('a freeze requires a reason for the audit trail');
      }
      return { ...base, status: 'FROZEN', frozenReason: event.reason };
    }
    case 'UNFREEZE': {
      const { frozenReason: _dropped, ...rest } = base;
      return { ...rest, status: 'ACTIVE' };
    }
    case 'CANCEL': {
      if (event.reason.trim() === '') {
        throw new AjoRuleError('a cancellation requires a reason for the audit trail');
      }
      return { ...base, status: 'CANCELLED', cancellationReason: event.reason };
    }
  }
}

/**
 * Create an Ajo in `DRAFT`.
 *
 * `totalRounds` is the member count: rounds equal members, so a ten-member
 * Ajo runs ten rounds. It is validated as a member count rather than as an
 * arbitrary round count, which is what keeps the two from drifting apart.
 */
export function createAjo(totalRounds: number, now: Date = new Date()): AjoState {
  assertValidMemberCount(totalRounds);
  return { status: 'DRAFT', roundNumber: 0, totalRounds, since: now };
}

export function isTerminal(status: AjoStatus): boolean {
  return ALLOWED[status].length === 0;
}

/** Terminal states never accept further events. */
export function assertNotTerminal(current: AjoState): void {
  if (isTerminal(current.status)) {
    throw new AjoRuleError(`Ajo is ${current.status} and can no longer be modified`);
  }
}

/**
 * The 5-day enrollment rule.
 *
 * If every payout position is not filled within the window, the Ajo cancels
 * rather than running partially. This protects members from being collected
 * from for a rotation that can never complete.
 */
export const ENROLLMENT_WINDOW_DAYS = 5;

export function evaluateEnrollmentWindow(
  openedAt: Date,
  now: Date,
  positionsFilled: number,
  positionsTotal: number,
): { readonly shouldCancel: boolean; readonly reason?: string } {
  if (positionsFilled >= positionsTotal) {
    return { shouldCancel: false };
  }
  const elapsedMs = now.getTime() - openedAt.getTime();
  const elapsedDays = Math.floor(elapsedMs / 86_400_000);
  if (elapsedDays >= ENROLLMENT_WINDOW_DAYS) {
    return {
      shouldCancel: true,
      reason: `enrollment window of ${ENROLLMENT_WINDOW_DAYS} days closed with ${positionsFilled}/${positionsTotal} positions filled`,
    };
  }
  return { shouldCancel: false };
}

/** Ajo.ng charges the organizer, not the member. */
export interface FeeSchedule {
  readonly monthlySubscriptionKobo: Kobo;
}

/**
 * Product rule: an Ajo has between 5 and 20 members, ten being the default.
 *
 * The floor is what makes a group a rotation rather than a transfer between
 * two or three people. The ceiling bounds how many positions one organizer can
 * actually invite, monitor and default-handle inside a single Ajo.
 */
export const MIN_AJO_MEMBERS = 5;
export const MAX_AJO_MEMBERS = 20;
export const DEFAULT_AJO_MEMBERS = 10;

/**
 * The creation-time contribution window, in kobo: NGN 1,000 to NGN 5,000,000.
 *
 * Below the floor an Ajo collects less than it costs to move the money; above
 * the ceiling a single default is large enough to threaten the platform rather
 * than one group. Section 11 of the API spec fixes these as the bounds on
 * `POST /api/v1/ajos`, so they belong here with the other money-and-rights
 * rules rather than in the route.
 */
export const MIN_CONTRIBUTION_KOBO = 100_000;
export const MAX_CONTRIBUTION_KOBO = 500_000_000;

/** The contribution cadences the product offers, as the API names them. */
export type AjoFrequency = 'WEEKLY' | 'BIWEEKLY' | 'MONTHLY';

export const AJO_FREQUENCIES: readonly AjoFrequency[] = ['WEEKLY', 'BIWEEKLY', 'MONTHLY'];

/** The weekday a collection lands on, as the API names them. */
export type CollectionDay =
  | 'MONDAY'
  | 'TUESDAY'
  | 'WEDNESDAY'
  | 'THURSDAY'
  | 'FRIDAY'
  | 'SATURDAY'
  | 'SUNDAY';

export const COLLECTION_DAYS: readonly CollectionDay[] = [
  'MONDAY',
  'TUESDAY',
  'WEDNESDAY',
  'THURSDAY',
  'FRIDAY',
  'SATURDAY',
  'SUNDAY',
];

/**
 * The API's cadence name to the reference-data `contribution_frequencies.code`.
 *
 * The two vocabularies are not the same and must not be conflated: the API says
 * `BIWEEKLY` and the table says `fortnightly`. An explicit map means a fourth
 * frequency is a compile error here rather than a lookup that silently returns
 * no row at runtime.
 */
const FREQUENCY_CODES: Record<AjoFrequency, string> = {
  WEEKLY: 'weekly',
  BIWEEKLY: 'fortnightly',
  MONTHLY: 'monthly',
};

export function frequencyCode(frequency: AjoFrequency): string {
  return FREQUENCY_CODES[frequency];
}

/**
 * The API's weekday name to the stored form, lower-cased.
 *
 * The database's own vocabulary is lower-case throughout (`weekly`, `active`,
 * `draft`), and the day is no exception. Storing exactly what the API sent would
 * make this one column the only place a value's convention came from the wire.
 */
export function collectionDayCode(day: CollectionDay): string {
  return day.toLowerCase();
}

export function frequencyFromCode(code: string): AjoFrequency | undefined {
  return AJO_FREQUENCIES.find((frequency) => FREQUENCY_CODES[frequency] === code);
}

export function collectionDayFromCode(code: string): CollectionDay | undefined {
  return COLLECTION_DAYS.find((day) => day.toLowerCase() === code);
}

export function isAjoFrequency(value: unknown): value is AjoFrequency {
  return typeof value === 'string' && (AJO_FREQUENCIES as readonly string[]).includes(value);
}

export function isCollectionDay(value: unknown): value is CollectionDay {
  return typeof value === 'string' && (COLLECTION_DAYS as readonly string[]).includes(value);
}

/**
 * Validate an Ajo's member count.
 *
 * The creator occupies one of these positions rather than sitting outside
 * them, so a ten-member Ajo is one organizer and nine invitees. A caller that
 * passes an invitee count of 10 for a ten-member Ajo is asking for eleven
 * members, and must be rejected here rather than producing an Ajo whose
 * position count and roster disagree.
 */
export function assertValidMemberCount(memberCount: number): void {
  if (!Number.isSafeInteger(memberCount)) {
    throw new AjoRuleError(
      `member count must be a whole number, received ${String(memberCount)}`,
    );
  }
  if (memberCount < MIN_AJO_MEMBERS) {
    throw new AjoRuleError(
      `an Ajo needs at least ${MIN_AJO_MEMBERS} members to rotate, received ${memberCount}`,
    );
  }
  if (memberCount > MAX_AJO_MEMBERS) {
    throw new AjoRuleError(
      `an Ajo may have at most ${MAX_AJO_MEMBERS} members, received ${memberCount}`,
    );
  }
}

/**
 * Validate a contribution amount for an Ajo of a given size.
 *
 * Member count is validated first, because an amount is meaningless without a
 * valid group: NGN 10,000 across two people and NGN 10,000 across twenty are
 * different products, and only one of them is an Ajo.
 */
export function assertValidContributionAmount(amount: Kobo, memberCount: number): void {
  assertValidMemberCount(memberCount);
  try {
    if (amount <= 0) {
      throw new AjoRuleError('contribution amount must be positive');
    }
    // The platform window, not a per-group choice. The floor is what keeps an
    // Ajo from collecting less than it costs to move the money; the ceiling is
    // what bounds the loss from a single default.
    if (amount < MIN_CONTRIBUTION_KOBO) {
      throw new AjoRuleError(
        `a contribution must be at least ${MIN_CONTRIBUTION_KOBO / 100} naira`,
      );
    }
    if (amount > MAX_CONTRIBUTION_KOBO) {
      throw new AjoRuleError(
        `a contribution may not exceed ${MAX_CONTRIBUTION_KOBO / 100} naira`,
      );
    }
  } catch (error: unknown) {
    if (error instanceof MoneyError) {
      throw new AjoRuleError('invalid contribution amount');
    }
    throw error;
  }
}

export { MoneyError };
