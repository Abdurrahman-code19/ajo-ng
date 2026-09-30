import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  AjoRuleError,
  ENROLLMENT_WINDOW_DAYS,
  availableEvents,
  canTransition,
  createAjo,
  evaluateEnrollmentWindow,
  transition,
} from '../src/ajo-state.js';

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
