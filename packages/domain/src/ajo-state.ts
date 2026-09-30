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

export function createAjo(totalRounds: number, now: Date = new Date()): AjoState {
  if (!Number.isSafeInteger(totalRounds) || totalRounds < 2) {
    throw new AjoRuleError(`an Ajo needs at least 2 rounds, received ${totalRounds}`);
  }
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
  } catch (error: unknown) {
    if (error instanceof MoneyError) {
      throw new AjoRuleError('invalid contribution amount');
    }
    throw error;
  }
}

export { MoneyError };
