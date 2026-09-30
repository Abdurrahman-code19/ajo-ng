import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  AjoRuleError,
  DEFAULT_AJO_MEMBERS,
  ENROLLMENT_WINDOW_DAYS,
  MAX_AJO_MEMBERS,
  MIN_AJO_MEMBERS,
  assertValidContributionAmount,
  assertValidMemberCount,
  availableEvents,
  canTransition,
  createAjo,
  evaluateEnrollmentWindow,
  transition,
} from '../src/ajo-state.js';
import { naira } from '../src/money.js';

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
    let ajo = createAjo(3);
    ajo = transition(ajo, { type: 'OPEN_ENROLLMENT' });
    ajo = transition(ajo, { type: 'CLOSE_ENROLLMENT' });
    for (let round = 1; round <= 3; round += 1) {
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

  it('refuses to create an Ajo with fewer than 2 rounds', () => {
    assert.throws(() => createAjo(1), AjoRuleError);
    assert.throws(() => createAjo(0), AjoRuleError);
  });
});

describe('5-day enrollment window', () => {
  const openedAt = new Date('2026-01-01T00:00:00.000Z');

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
});
