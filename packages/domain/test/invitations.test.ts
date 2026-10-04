import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  AJO_RULES,
  AJO_RULES_VERSION,
  INVITATION_TTL_HOURS,
  ajoRules,
  assertInvitableEmail,
  feeDisclosure,
  invitationRejection,
  isInvitationStatus,
  isInvitationUsable,
} from '../src/invitations.js';
import { AjoRuleError } from '../src/ajo-state.js';
import { kobo, naira } from '../src/money.js';

describe('invitation usability', () => {
  const now = new Date('2026-10-03T12:00:00Z');

  it('accepts a pending invitation that has not expired', () => {
    const state = { status: 'pending' as const, expiresAt: new Date('2026-10-03T12:00:01Z') };
    assert.equal(invitationRejection(state, now), undefined);
    assert.equal(isInvitationUsable(state, now), true);
  });

  it('treats a pending invitation at its expiry instant as expired', () => {
    // Boundary: the instant it expires it is no longer usable, matching the
    // access-token rule that a token is good up to but not including expiry.
    const state = { status: 'pending' as const, expiresAt: now };
    assert.equal(invitationRejection(state, now), 'expired');
  });

  it('derives expiry for a pending row whose status has not been swept', () => {
    // Nothing sweeps the table on a timer, so a stale `pending` row past its
    // expiry must still read as expired -- that is the whole point of deriving
    // it rather than trusting the column.
    const state = { status: 'pending' as const, expiresAt: new Date('2026-10-01T00:00:00Z') };
    assert.equal(invitationRejection(state, now), 'expired');
  });

  it('reports each terminal status as its own reason', () => {
    const future = new Date('2027-01-01T00:00:00Z');
    for (const status of ['accepted', 'declined', 'revoked', 'expired'] as const) {
      assert.equal(invitationRejection({ status, expiresAt: future }, now), status);
    }
  });

  it('recognises only the schema\u2019s invitation statuses', () => {
    assert.equal(isInvitationStatus('pending'), true);
    assert.equal(isInvitationStatus('revoked'), true);
    assert.equal(isInvitationStatus('cancelled'), false);
    assert.equal(isInvitationStatus(undefined), false);
  });
});

describe('fee disclosure', () => {
  it('separates the contribution, the 2% fee and the total', () => {
    const disclosure = feeDisclosure(naira(1_000));
    assert.equal(disclosure.contributionKobo, 100_000);
    assert.equal(disclosure.feeKobo, 2_000);
    assert.equal(disclosure.totalChargeKobo, 102_000);
  });

  it('rounds the fee half-up on the kobo, like the ledger', () => {
    // 2% of 25 kobo is 0.5 kobo, which rounds up to 1. The disclosure must not
    // disagree with the charge by a kobo.
    assert.equal(feeDisclosure(kobo(25)).feeKobo, 1);
  });
});

describe('Ajo rules', () => {
  it('carries the five clauses the point of commitment must disclose', () => {
    assert.equal(AJO_RULES_VERSION, 1);
    const codes = AJO_RULES.map((rule) => rule.code);
    assert.deepEqual(codes, ['BR-004', 'BR-008', 'BR-002', 'BR-001', 'BR-011']);
    const rules = ajoRules();
    assert.equal(rules.version, AJO_RULES_VERSION);
    assert.equal(rules.clauses.length, AJO_RULES.length);
  });
});

describe('invitation lifetime', () => {
  it('is the spec\u2019s stated 72-hour default', () => {
    // Section 11.5 names 72 hours and marks it an open decision; this pins the
    // assumption so a change to it is a deliberate edit, not a drift.
    assert.equal(INVITATION_TTL_HOURS, 72);
  });
});

describe('invited email', () => {
  it('accepts a plainly-shaped address', () => {
    assert.doesNotThrow(() => assertInvitableEmail('invitee@example.com'));
    assert.doesNotThrow(() => assertInvitableEmail('  invitee@example.com  '));
  });

  it('rejects shapes that cannot be addressed', () => {
    for (const bad of ['', 'no-at-sign', '@example.com', 'invitee@', 'two@@example.com']) {
      assert.throws(() => assertInvitableEmail(bad), AjoRuleError, bad);
    }
  });
});
