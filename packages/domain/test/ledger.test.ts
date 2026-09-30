import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { Ledger, LedgerError, entries, isBalanced } from '../src/ledger.js';
import { add, kobo, naira, serviceFee, sum, type Kobo } from '../src/money.js';

const CONTRIBUTION = naira(10_000);
const MEMBERS = ['m1', 'm2', 'm3', 'm4', 'm5'] as const;

describe('Ledger invariants', () => {
  it('rejects an unbalanced transaction instead of accepting drift', () => {
    const ledger = new Ledger();
    assert.throws(
      () =>
        ledger.post({
          idempotencyKey: 'bad',
          kind: 'test.unbalanced',
          postings: [
            { account: 'escrow_cash', side: 'debit', amount: kobo(100) },
            { account: 'payouts_payable', side: 'credit', amount: kobo(99) },
          ],
        }),
      LedgerError,
    );
  });

  it('rejects a single-sided transaction', () => {
    const ledger = new Ledger();
    assert.throws(
      () =>
        ledger.post({
          idempotencyKey: 'bad',
          kind: 'test.one-sided',
          postings: [{ account: 'escrow_cash', side: 'debit', amount: kobo(100) }],
        }),
      LedgerError,
    );
  });

  it('rejects zero and negative posting amounts', () => {
    const ledger = new Ledger();
    assert.throws(
      () =>
        ledger.post({
          idempotencyKey: 'bad',
          kind: 'test.zero',
          postings: [
            { account: 'escrow_cash', side: 'debit', amount: kobo(0) },
            { account: 'payouts_payable', side: 'credit', amount: kobo(0) },
          ],
        }),
      LedgerError,
    );
  });

  it('rejects an unknown account kind', () => {
    const ledger = new Ledger();
    assert.throws(
      () =>
        ledger.post({
          idempotencyKey: 'bad',
          kind: 'test.unknown-account',
          postings: [
            { account: 'attacker_controlled' as never, side: 'debit', amount: kobo(100) },
            { account: 'escrow_cash', side: 'credit', amount: kobo(100) },
          ],
        }),
      LedgerError,
    );
  });
});

describe('Ledger idempotency', () => {
  it('returns the original transaction when a payout is retried', () => {
    const ledger = new Ledger();
    const spec = entries.payoutSettled('ajo1', 1, 'm1');

    const first = ledger.post({
      idempotencyKey: spec.idempotencyKey,
      kind: spec.kind,
      postings: spec.postings(CONTRIBUTION),
    });
    const second = ledger.post({
      idempotencyKey: spec.idempotencyKey,
      kind: spec.kind,
      postings: spec.postings(CONTRIBUTION),
    });

    assert.equal(first.id, second.id);
    assert.equal(ledger.transactions().length, 1, 'retry must not create a second entry');
  });

  it('does not double-count a retried collection', () => {
    const ledger = new Ledger();
    const spec = entries.contributionReceived('ajo1', 1, 'm1');

    for (let attempt = 0; attempt < 5; attempt += 1) {
      ledger.post({
        idempotencyKey: spec.idempotencyKey,
        kind: spec.kind,
        postings: spec.postings(CONTRIBUTION),
      });
    }

    assert.equal(ledger.escrowBalance(), CONTRIBUTION);
  });
});

describe('Ledger append-only history', () => {
  it('reverses rather than mutates, keeping both entries', () => {
    const ledger = new Ledger();
    const original = ledger.post({
      idempotencyKey: 'contribution:ajo1:1:m1',
      kind: 'contribution.received',
      postings: [
        { account: 'contributions_receivable', side: 'credit', amount: CONTRIBUTION },
        { account: 'escrow_cash', side: 'debit', amount: CONTRIBUTION },
      ],
    });

    const reversal = ledger.reverse(original.id, 'duplicate webhook', 'reversal:1');

    assert.equal(ledger.transactions().length, 2);
    assert.equal(ledger.escrowBalance(), 0, 'reversal must zero the balance');
    assert.equal(reversal.reversesTransactionId, original.id);
  });

  it('requires a reason for every reversal', () => {
    const ledger = new Ledger();
    const original = ledger.post({
      idempotencyKey: 'x:1',
      kind: 'contribution.received',
      postings: [
        { account: 'contributions_receivable', side: 'credit', amount: CONTRIBUTION },
        { account: 'escrow_cash', side: 'debit', amount: CONTRIBUTION },
      ],
    });
    assert.throws(() => ledger.reverse(original.id, '   ', 'reversal:2'), LedgerError);
  });

  it('exposes no update or delete method', () => {
    const ledger = new Ledger();
    const surface = Object.getOwnPropertyNames(Object.getPrototypeOf(ledger));
    for (const forbidden of ['update', 'delete', 'remove', 'set', 'patch', 'edit']) {
      assert.equal(surface.includes(forbidden), false, `Ledger must not expose ${forbidden}()`);
    }
  });
});

describe('Ledger solvency', () => {
  it('accepts a full round when escrow covers the payout', () => {
    const ledger = new Ledger();
    for (const memberId of MEMBERS) {
      const spec = entries.contributionReceived('ajo1', 1, memberId);
      ledger.post({
        idempotencyKey: spec.idempotencyKey,
        kind: spec.kind,
        postings: spec.postings(CONTRIBUTION),
      });
    }

    const pot = sum(MEMBERS.map(() => CONTRIBUTION));

    // 1. Recognise the liability owed to this round's recipient.
    const recognized = entries.payoutRecognized('ajo1', 1, 'm1');
    ledger.post({
      idempotencyKey: recognized.idempotencyKey,
      kind: recognized.kind,
      postings: recognized.postings(pot),
    });
    assert.equal(ledger.escrowBalance(), pot);
    assert.equal(ledger.totalOwedToMembers(), pot);
    assert.doesNotThrow(() => ledger.assertSolvent());

    // 2. Disburse it.
    const payout = entries.payoutSettled('ajo1', 1, 'm1');
    ledger.post({
      idempotencyKey: payout.idempotencyKey,
      kind: payout.kind,
      postings: payout.postings(pot),
    });

    assert.equal(ledger.escrowBalance(), 0);
    assert.equal(ledger.totalOwedToMembers(), 0);
    assert.doesNotThrow(() => ledger.assertSolvent());
  });

  it('halts disbursement if a payout is recognised without collected funds', () => {
    const ledger = new Ledger();
    const recognized = entries.payoutRecognized('ajo1', 1, 'm1');
    ledger.post({
      idempotencyKey: recognized.idempotencyKey,
      kind: recognized.kind,
      postings: recognized.postings(naira(200_000)),
    });

    assert.equal(ledger.escrowBalance(), 0);
    assert.throws(() => ledger.assertSolvent(), /INSOLVENT/);
  });

  it('detects an insolvent ledger and halts disbursement', () => {
    const ledger = new Ledger();
    // Record a liability without ever funding it.
    ledger.post({
      idempotencyKey: 'unfunded:1',
      kind: 'payout.settled',
      postings: [
        { account: 'payouts_payable', side: 'debit', amount: naira(200_000) },
        { account: 'escrow_cash', side: 'credit', amount: naira(200_000) },
      ],
    });
    // Drive escrow negative by collecting from nowhere.
    ledger.post({
      idempotencyKey: 'contribution:ajo1:1:m1',
      kind: 'contribution.received',
      postings: [
        { account: 'contributions_receivable', side: 'credit', amount: CONTRIBUTION },
        { account: 'escrow_cash', side: 'debit', amount: CONTRIBUTION },
      ],
    });

    assert.throws(() => ledger.assertSolvent(), /INSOLVENT/);
  });
});

describe('Ledger defaults', () => {
  it('moves a missed contribution from receivable to default', () => {
    const ledger = new Ledger();
    const spec = entries.contributionDefaulted('ajo1', 1, 'm3');
    ledger.post({
      idempotencyKey: spec.idempotencyKey,
      kind: spec.kind,
      postings: spec.postings(CONTRIBUTION),
    });

    assert.equal(ledger.balanceOf('contributions_receivable'), CONTRIBUTION);
    assert.equal(ledger.balanceOf('defaults_receivable'), CONTRIBUTION);
  });
});

describe('isBalanced', () => {
  it('accepts balanced and rejects unbalanced', () => {
    assert.equal(
      isBalanced([
        { account: 'escrow_cash', side: 'debit', amount: kobo(100) },
        { account: 'payouts_payable', side: 'credit', amount: kobo(100) },
      ]),
      true,
    );
    assert.equal(
      isBalanced([
        { account: 'escrow_cash', side: 'debit', amount: kobo(100) },
        { account: 'payouts_payable', side: 'credit', amount: kobo(101) },
      ]),
      false,
    );
  });
});

describe('Ledger fee recognition', () => {
  it('posts the 2% fee as a balanced entry of its own', () => {
    const ledger = new Ledger();
    const fee = serviceFee(CONTRIBUTION);

    const spec = entries.feeRecognised('ajo1', 1, 'm1');
    const txn = ledger.post({
      idempotencyKey: spec.idempotencyKey,
      kind: spec.kind,
      postings: spec.postings(fee),
    });

    // The entry balances on its own. A bare "credit fees_income" with no
    // matching debit would be rejected.
    const debits = txn.postings.filter((p) => p.side === 'debit');
    const credits = txn.postings.filter((p) => p.side === 'credit');
    assert.equal(debits.length, 1);
    assert.equal(credits.length, 1);
    assert.equal(debits[0]?.account, 'escrow_cash');
    assert.equal(credits[0]?.account, 'fees_income');
    assert.equal(fee, naira(200));
  });

  it('is idempotent so a retried webhook does not bank the fee twice', () => {
    const ledger = new Ledger();
    const spec = entries.feeRecognised('ajo1', 1, 'm1');

    ledger.post({ ...spec, postings: spec.postings(serviceFee(CONTRIBUTION)) });
    ledger.post({ ...spec, postings: spec.postings(serviceFee(CONTRIBUTION)) });

    assert.equal(ledger.balanceOf('fees_income'), serviceFee(CONTRIBUTION));
  });

  it('leaves member money and platform fee separable over a full round', () => {
    const ledger = new Ledger();
    const fee = serviceFee(CONTRIBUTION);
    const pot = sum(MEMBERS.map(() => CONTRIBUTION));

    // Every member pays in: their contribution clears the receivable, and
    // the fee is recognised separately so a refund can reverse one without
    // the other.
    for (const memberId of MEMBERS) {
      const contribution = entries.contributionReceived('ajo1', 1, memberId);
      ledger.post({ ...contribution, postings: contribution.postings(CONTRIBUTION) });

      const feeSpec = entries.feeRecognised('ajo1', 1, memberId);
      ledger.post({ ...feeSpec, postings: feeSpec.postings(fee) });
    }

    const totalFees = sum(MEMBERS.map(() => fee));
    const totalCharged = sum(
      MEMBERS.map((): Kobo => add(CONTRIBUTION, fee)),
    );

    // Escrow holds the pot plus every fee collected.
    assert.equal(ledger.escrowBalance(), pot + totalFees);
    assert.equal(totalCharged, pot + totalFees);

    // Revenue is banked separately from member money.
    assert.equal(ledger.balanceOf('fees_income'), totalFees);
    assert.equal(ledger.totalOwedByMembers(), pot);

    // Recognise and settle the payout: members get the pot, never less.
    const recognized = entries.payoutRecognized('ajo1', 1, 'm1');
    ledger.post({ ...recognized, postings: recognized.postings(pot) });
    assert.doesNotThrow(() => ledger.assertSolvent());

    const payout = entries.payoutSettled('ajo1', 1, 'm1');
    ledger.post({ ...payout, postings: payout.postings(pot) });

    // After the round, escrow holds only the platform's fees and no member
    // money remains owed.
    assert.equal(ledger.escrowBalance(), totalFees);
    assert.equal(ledger.totalOwedToMembers(), 0);
    assert.equal(ledger.balanceOf('fees_income'), totalFees);
    assert.doesNotThrow(() => ledger.assertSolvent());
  });

  it('reverses a fee without touching the member contribution', () => {
    const ledger = new Ledger();
    const fee = serviceFee(CONTRIBUTION);

    const contribution = entries.contributionReceived('ajo1', 1, 'm1');
    const contributionTxn = ledger.post({
      ...contribution,
      postings: contribution.postings(CONTRIBUTION),
    });

    const feeSpec = entries.feeRecognised('ajo1', 1, 'm1');
    const feeTxn = ledger.post({ ...feeSpec, postings: feeSpec.postings(fee) });

    ledger.reverse(feeTxn.id, 'Fee reversed after provider refund', 'rev:fee:1');

    assert.equal(ledger.balanceOf('fees_income'), 0);
    // The contribution is untouched: the member's money is not taken with it.
    assert.equal(ledger.balanceOf('escrow_cash'), CONTRIBUTION);
    assert.equal(ledger.escrowBalance(), CONTRIBUTION);
    assert.ok(contributionTxn.id !== feeTxn.id);
  });
});
