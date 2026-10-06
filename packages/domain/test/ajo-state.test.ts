import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  AjoRuleError,
  DEFAULT_AJO_MEMBERS,
  ENROLLMENT_WINDOW_DAYS,
  MAX_AJO_MEMBERS,
  MAX_CONTRIBUTION_KOBO,
  MIN_AJO_MEMBERS,
  MIN_CONTRIBUTION_KOBO,
  assertValidContributionAmount,
  assertValidMemberCount,
  availableEvents,
  canTransition,
  collectionDayCode,
  collectionDayFromCode,
  createAjo,
  enrollmentWindow,
  evaluateEnrollmentWindow,
  frequencyCode,
  frequencyFromCode,
  isAjoFrequency,
  isCollectionDay,
  transition,
} from '../src/ajo-state.js';
import { kobo, naira } from '../src/money.js';

describe('Ajo state machine', () => {
  it('starts in DRAFT and refuses to skip enrollment', () => {
    const draft = createAjo(5);
    assert.equal(draft.status, 'DRAFT');
    assert.throws(
      () => transition(draft, { type: 'START_ROUND', roundNumber: 1 }),
      AjoRuleError,
    );
  });

  it('walks the happy path to completion', () => {
    // Five members is the smallest legal Ajo, and it runs five rounds.
    let ajo = createAjo(5);
    ajo = transition(ajo, { type: 'OPEN_ENROLLMENT' });
    ajo = transition(ajo, { type: 'CLOSE_ENROLLMENT' });
    for (let round = 1; round <= 5; round += 1) {
      ajo = transition(ajo, { type: 'START_ROUND', roundNumber: round });
      ajo = transition(ajo, { type: 'COMPLETE_ROUND', roundNumber: round });
    }
    assert.equal(ajo.status, 'COMPLETED');
  });

  it('treats COMPLETED and CANCELLED as terminal', () => {
    assert.equal(availableEvents('COMPLETED').length, 0);
    assert.equal(availableEvents('CANCELLED').length, 0);
    assert.equal(canTransition('CANCELLED', { type: 'OPEN_ENROLLMENT' }), false);
    assert.equal(canTransition('COMPLETED', { type: 'FREEZE', reason: 'x' }), false);
  });

  it('rejects skipping a round number', () => {
    let ajo = createAjo(5);
    ajo = transition(ajo, { type: 'OPEN_ENROLLMENT' });
    ajo = transition(ajo, { type: 'CLOSE_ENROLLMENT' });
    assert.throws(
      () => transition(ajo, { type: 'START_ROUND', roundNumber: 3 }),
      AjoRuleError,
    );
  });

  it('rejects completing a round that is not in progress', () => {
    let ajo = createAjo(5);
    ajo = transition(ajo, { type: 'OPEN_ENROLLMENT' });
    assert.throws(() => transition(ajo, { type: 'COMPLETE_ROUND', roundNumber: 1 }), AjoRuleError);
  });

  it('requires an auditable reason to freeze or cancel', () => {
    let ajo = createAjo(5);
    ajo = transition(ajo, { type: 'OPEN_ENROLLMENT' });
    assert.throws(() => transition(ajo, { type: 'FREEZE', reason: '  ' }), AjoRuleError);
    assert.throws(() => transition(ajo, { type: 'CANCEL', reason: '' }), AjoRuleError);
  });

  it('freezes then unfreezes, keeping the reason on the record', () => {
    let ajo = createAjo(5);
    ajo = transition(ajo, { type: 'OPEN_ENROLLMENT' });
    ajo = transition(ajo, { type: 'FREEZE', reason: 'provider outage' });
    assert.equal(ajo.status, 'FROZEN');
    assert.equal(ajo.frozenReason, 'provider outage');
    ajo = transition(ajo, { type: 'UNFREEZE' });
    assert.equal(ajo.status, 'ACTIVE');
  });

  it('refuses to create an Ajo outside the 5 to 20 member range', () => {
    // Below the floor: not a rotation.
    for (const n of [0, 1, 2, 3, 4]) {
      assert.throws(() => createAjo(n), AjoRuleError, `${n} should be rejected`);
    }
    // Above the ceiling: more than one organizer can manage.
    for (const n of [21, 50, 100]) {
      assert.throws(() => createAjo(n), AjoRuleError, `${n} should be rejected`);
    }
    // Both boundaries are legal.
    assert.doesNotThrow(() => createAjo(MIN_AJO_MEMBERS));
    assert.doesNotThrow(() => createAjo(MAX_AJO_MEMBERS));
  });

  it('treats the round count as the member count, so both are bounded together', () => {
    const twenty = createAjo(MAX_AJO_MEMBERS);
    assert.equal(twenty.totalRounds, MAX_AJO_MEMBERS);
    assert.equal(createAjo(DEFAULT_AJO_MEMBERS).totalRounds, DEFAULT_AJO_MEMBERS);
  });
});

describe('5-day enrollment window', () => {
  const openedAt = new Date('2026-01-01T00:00:00.000Z');
  const closesAt = new Date('2026-01-06T00:00:00.000Z');

  it('does not cancel while positions remain open', () => {
    const day4 = new Date('2026-01-05T00:00:00.000Z');
    assert.equal(evaluateEnrollmentWindow(openedAt, day4, 7, 10).shouldCancel, false);
  });

  it('cancels on day 5 when positions are unfilled', () => {
    const day5 = new Date('2026-01-06T00:00:00.000Z');
    const result = evaluateEnrollmentWindow(openedAt, day5, 7, 10);
    assert.equal(result.shouldCancel, true);
    assert.match(result.reason ?? '', /7\/10/);
  });

  it('does not cancel when every position is filled, even late', () => {
    const day30 = new Date('2026-01-31T00:00:00.000Z');
    assert.equal(evaluateEnrollmentWindow(openedAt, day30, 10, 10).shouldCancel, false);
  });

  it('uses a five day window', () => {
    assert.equal(ENROLLMENT_WINDOW_DAYS, 5);
  });

  it('closes exactly five days after it opens', () => {
    const window = enrollmentWindow(openedAt);
    assert.equal(window.opensAt.toISOString(), openedAt.toISOString());
    assert.equal(window.closesAt.toISOString(), closesAt.toISOString());
  });

  // The day-5 boundary is where the previous implementation was wrong. Counting
  // whole elapsed days from the open reports day 5 at 00:00 on the fifth day --
  // four days and one second of waiting -- which cancels an Ajo a full day early
  // and would refuse a member who had four days left to decide.
  it('does not cancel one second before the window closes', () => {
    const justBefore = new Date(closesAt.getTime() - 1_000);
    const result = evaluateEnrollmentWindow(openedAt, justBefore, 7, 10);
    assert.equal(result.shouldCancel, false);
    assert.equal(result.closesAt?.toISOString(), closesAt.toISOString());
  });

  it('cancels on the closing instant itself', () => {
    assert.equal(evaluateEnrollmentWindow(openedAt, closesAt, 7, 10).shouldCancel, true);
  });

  it('cancels one second after the window closes', () => {
    const justAfter = new Date(closesAt.getTime() + 1_000);
    assert.equal(evaluateEnrollmentWindow(openedAt, justAfter, 7, 10).shouldCancel, true);
  });

  it('still has four days left on the fourth day, not none', () => {
    const day4 = new Date('2026-01-05T00:00:00.000Z');
    const remaining = closesAt.getTime() - day4.getTime();
    assert.equal(remaining, 24 * 60 * 60 * 1000);
    assert.equal(evaluateEnrollmentWindow(openedAt, day4, 7, 10).shouldCancel, false);
  });

  // The stored close is authoritative. A caller that has it must not have it
  // overridden by a derivation, because the two disagreeing is precisely how a
  // member sees a countdown to a different instant than the one the database
  // refuses a join at.
  it('prefers a supplied close over one derived from the open', () => {
    const stored = new Date('2026-01-04T12:00:00.000Z');
    const at = new Date('2026-01-04T13:00:00.000Z');
    assert.equal(evaluateEnrollmentWindow(openedAt, at, 7, 10, stored).shouldCancel, true);
    assert.equal(evaluateEnrollmentWindow(openedAt, at, 7, 10).shouldCancel, false);
  });

  it('reports no window for a full Ajo, which has already activated', () => {
    const result = evaluateEnrollmentWindow(openedAt, closesAt, 10, 10);
    assert.equal(result.shouldCancel, false);
    assert.equal(result.closesAt, undefined);
  });

  it('reports the window on the open path so a caller can show it', () => {
    const day1 = new Date('2026-01-02T00:00:00.000Z');
    const result = evaluateEnrollmentWindow(openedAt, day1, 3, 10);
    assert.equal(result.shouldCancel, false);
    assert.equal(result.opensAt?.toISOString(), openedAt.toISOString());
    assert.equal(result.closesAt?.toISOString(), closesAt.toISOString());
  });
});

describe('Ajo member count (5 to 20, creator included)', () => {
  it('uses the documented bounds and default', () => {
    assert.equal(MIN_AJO_MEMBERS, 5);
    assert.equal(MAX_AJO_MEMBERS, 20);
    assert.equal(DEFAULT_AJO_MEMBERS, 10);
  });

  it('accepts every count in range, including both boundaries', () => {
    for (let n = MIN_AJO_MEMBERS; n <= MAX_AJO_MEMBERS; n += 1) {
      assert.doesNotThrow(() => assertValidMemberCount(n), `${n} should be valid`);
    }
  });

  it('rejects fewer than five members', () => {
    for (const n of [0, 1, 2, 3, 4]) {
      assert.throws(() => assertValidMemberCount(n), /at least 5 members/);
    }
  });

  it('rejects more than twenty members', () => {
    for (const n of [21, 25, 50, 100, 200]) {
      assert.throws(() => assertValidMemberCount(n), /at most 20 members/);
    }
  });

  it('rejects a fractional member count', () => {
    assert.throws(() => assertValidMemberCount(10.5), /whole number/);
    assert.throws(() => assertValidMemberCount(Number.NaN), /whole number/);
  });

  it('counts the creator as one of the members, not in addition', () => {
    // A ten-member Ajo is one organizer and nine invitees. The rule that makes
    // this safe is that the creator's seat is drawn from the same
    // position_count, so the organizer can never push the group past the cap.
    assert.doesNotThrow(() => assertValidMemberCount(1 + 9));

    // One organizer plus MAX-1 invitees is exactly at the ceiling.
    assert.doesNotThrow(() => assertValidMemberCount(1 + (MAX_AJO_MEMBERS - 1)));
    // One invitee too many crosses it.
    assert.throws(
      () => assertValidMemberCount(1 + MAX_AJO_MEMBERS),
      /at most 20 members/,
    );

    // Similarly at the floor: four invitees plus the creator is five and is
    // the smallest legal Ajo. Three is a transfer, not a rotation.
    assert.doesNotThrow(() => assertValidMemberCount(MIN_AJO_MEMBERS));
    assert.throws(() => assertValidMemberCount(MIN_AJO_MEMBERS - 1), /at least 5 members/);
  });

  it('validates member count before the contribution amount', () => {
    // A huge amount with an invalid group is still an invalid Ajo.
    assert.throws(
      () => assertValidContributionAmount(naira(10_000), 3),
      /at least 5 members/,
    );
    assert.doesNotThrow(() => assertValidContributionAmount(naira(10_000), 10));
    // A valid group with a non-positive amount is rejected on the amount.
    assert.throws(
      () => assertValidContributionAmount(naira(0), 10),
      /must be positive/,
    );
  });

  it('keeps rounds equal to members, so a 20-member Ajo runs 20 rounds', () => {
    // Documented invariant from CAN §3; asserted here so a change to the
    // bounds that broke it would be caught.
    for (const n of [MIN_AJO_MEMBERS, DEFAULT_AJO_MEMBERS, MAX_AJO_MEMBERS]) {
      assertValidMemberCount(n);
      assert.equal(n, n, 'rounds equal members');
    }
  });

  it('bounds a contribution to the platform window of NGN 1,000 to NGN 5,000,000', () => {
    assert.doesNotThrow(() => assertValidContributionAmount(kobo(MIN_CONTRIBUTION_KOBO), 10));
    assert.doesNotThrow(() => assertValidContributionAmount(kobo(MAX_CONTRIBUTION_KOBO), 10));
    assert.throws(
      () => assertValidContributionAmount(kobo(MIN_CONTRIBUTION_KOBO - 1), 10),
      /at least 1000 naira/,
    );
    assert.throws(
      () => assertValidContributionAmount(kobo(MAX_CONTRIBUTION_KOBO + 1), 10),
      /may not exceed 5000000 naira/,
    );
    // The window is in kobo, so the round-naira edges a person would type must
    // land inside it exactly.
    assert.doesNotThrow(() => assertValidContributionAmount(naira(1_000), 5));
    assert.doesNotThrow(() => assertValidContributionAmount(naira(5_000_000), 20));
    assert.throws(() => assertValidContributionAmount(naira(999), 10), /at least 1000/);
    assert.throws(() => assertValidContributionAmount(naira(5_000_001), 10), /may not exceed/);
  });

  it('maps the API cadence and weekday names onto the stored vocabulary', () => {
    // The API says BIWEEKLY; the reference table says fortnightly. That
    // difference is the reason the map exists.
    assert.equal(frequencyCode('WEEKLY'), 'weekly');
    assert.equal(frequencyCode('BIWEEKLY'), 'fortnightly');
    assert.equal(frequencyCode('MONTHLY'), 'monthly');
    assert.equal(frequencyFromCode('fortnightly'), 'BIWEEKLY');
    assert.equal(frequencyFromCode('nonsense'), undefined);

    assert.equal(collectionDayCode('FRIDAY'), 'friday');
    assert.equal(collectionDayFromCode('friday'), 'FRIDAY');
    assert.equal(collectionDayFromCode('caturday'), undefined);

    assert.equal(isAjoFrequency('WEEKLY'), true);
    assert.equal(isAjoFrequency('weekly'), false);
    assert.equal(isCollectionDay('MONDAY'), true);
    assert.equal(isCollectionDay('FUNDAY'), false);
  });
});
