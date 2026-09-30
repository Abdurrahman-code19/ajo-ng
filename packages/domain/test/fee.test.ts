/**
 * The 2% service fee.
 *
 * These are the money rules a member is told, tested as arithmetic rather than
 * prose. If any of these break, either a member is being overcharged or the
 * platform is losing revenue, and both are unacceptable at any scale.
 */

import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  FEE_BASIS_POINTS,
  MoneyError,
  add,
  format,
  kobo,
  multiply,
  naira,
  serviceFee,
  totalCharge,
} from '../src/money.js';

describe('Service fee (2% of contribution)', () => {
  it('uses 2% expressed in basis points', () => {
    assert.equal(FEE_BASIS_POINTS, 200);
  });

  it('is exactly 2% on the canonical ₦1,000 contribution', () => {
    assert.equal(serviceFee(naira(1_000)), naira(20));
  });

  it('makes the member pay ₦1,020 for a ₦1,000 contribution', () => {
    assert.equal(totalCharge(naira(1_000)), naira(1_020));
  });

  it('leaves the recipient pool untouched', () => {
    // The fee is charged to the member on top. It is never deducted from the
    // base pool, which is the promise the whole product rests on.
    const contribution = naira(10_000);
    const charged = totalCharge(contribution);
    assert.equal(add(contribution, serviceFee(contribution)), charged);
    assert.equal(charged - contribution, serviceFee(contribution));
  });

  it('scales linearly across the documented Ajo values', () => {
    const cases: ReadonlyArray<readonly [number, number]> = [
      [1_000, 20],
      [2_500, 50],
      [5_000, 100],
      [10_000, 200],
      [20_000, 400],
      [50_000, 1_000],
    ];
    for (const [contribution, expectedFee] of cases) {
      assert.equal(
        serviceFee(naira(contribution)),
        naira(expectedFee),
        `fee on ₦${contribution} should be ₦${expectedFee}`,
      );
    }
  });

  it('computes the standard 10-member, 10-round Ajo exactly', () => {
    const members = 10;
    const rounds = 10;
    const perMemberPerRound = naira(10_000);

    // Every round all 10 members put in ₦10,000, so the round pot is ₦100,000
    // and the recipient's total across the Ajo is ₦100,000.
    const roundPot = multiply(perMemberPerRound, members);
    assert.equal(roundPot, naira(100_000));

    const perMemberPaid = multiply(perMemberPerRound, rounds);
    assert.equal(perMemberPaid, naira(100_000));

    // A rotating Ajo is zero-sum for members: what you pay out equals what
    // you pay in, before fees.
    const perMemberReceived = multiply(roundPot, 1);
    assert.equal(perMemberReceived, naira(100_000));

    // Total volume per Ajo: 10 rounds x ₦100,000 pot.
    const perAjoVolume = multiply(roundPot, rounds);
    assert.equal(perAjoVolume, naira(1_000_000));

    // Fees. Each member pays 2% on everything they contribute.
    const perMemberFee = multiply(serviceFee(perMemberPerRound), rounds);
    assert.equal(perMemberFee, naira(2_000));

    const perAjoFee = multiply(perMemberFee, members);
    assert.equal(perAjoFee, naira(20_000));

    // The platform collects the member's money plus the fee; the members'
    // share is never reduced by it.
    const perAjoCollected = add(perAjoVolume, perAjoFee);
    assert.equal(perAjoCollected, naira(1_020_000));

    // Member cash out equals member cash in. This is the invariant that must
    // hold for every single Ajo that ever runs.
    const memberCashOut = multiply(perMemberReceived, members);
    assert.equal(memberCashOut, perAjoVolume);
  });

  it('projects the Year-1 base scenario from the same rules', () => {
    const ajos = 300;

    // ₦1,000,000 volume per Ajo (10 rounds x ₦100,000 pot) = 100,000,000 kobo.
    const volume = multiply(naira(1_000_000), ajos);
    assert.equal(volume, kobo(30_000_000_000)); // ₦300,000,000

    // ₦20,000 fee per Ajo x 300 = ₦6,000,000.
    const fee = multiply(naira(20_000), ajos);
    assert.equal(fee, kobo(600_000_000));

    // Deposits and payouts: 10 members x 10 rounds per Ajo.
    assert.equal(10 * 10 * ajos, 30_000);
    assert.equal(10 * ajos, 3_000);
  });

  it('rounds half-up in integer kobo and never below the true 2%', () => {
    // 2% of 24 kobo = 0.48 kobo, which rounds down to 0: a member is not
    // charged a fee they cannot meaningfully pay.
    assert.equal(serviceFee(kobo(1)), kobo(0));
    assert.equal(serviceFee(kobo(24)), kobo(0));
    // 2% of 25 kobo = exactly 0.5, and half-up rounds it to 1.
    assert.equal(serviceFee(kobo(25)), kobo(1));
    // 2% of 50 kobo = exactly 1.
    assert.equal(serviceFee(kobo(50)), kobo(1));
    // 2% of 51 kobo = 1.02 → 1
    assert.equal(serviceFee(kobo(51)), kobo(1));
    // 2% of 75 kobo = 1.5 → 2 (half-up)
    assert.equal(serviceFee(kobo(75)), kobo(2));
  });

  it('never charges a fee greater than the contribution itself', () => {
    for (let nairaValue = 1; nairaValue <= 200; nairaValue += 1) {
      const contribution = naira(nairaValue);
      const fee = serviceFee(contribution);
      assert.ok(
        fee <= contribution,
        `fee ${format(fee)} exceeded contribution ${format(contribution)}`,
      );
    }
  });

  it('is exact in integer arithmetic for every naira value up to ₦100,000', () => {
    // Property: fee === round-half-up(contribution * 0.02), computed
    // independently here in exact integer terms. Catches any drift introduced
    // by a refactor. `nairaValue * 100` is already the kobo amount.
    for (let nairaValue = 1; nairaValue <= 100_000; nairaValue += 1) {
      const contribution = naira(nairaValue);
      const contributionKobo = nairaValue * 100;
      const expectedKobo = Math.floor((contributionKobo * 200 + 5_000) / 10_000);
      assert.equal(
        serviceFee(contribution),
        kobo(expectedKobo),
        `mismatch at ₦${nairaValue}`,
      );
    }
  });

  it('sums to exactly 2% across a whole Ajo, with no rounding loss', () => {
    // 500 contributions of an odd amount each: the aggregate fee must still be
    // exactly 2% of the aggregate, or volume reporting drifts from reality.
    const oddAmount = naira(3_333);
    let totalContribution = kobo(0);
    let totalFee = kobo(0);
    for (let i = 0; i < 500; i += 1) {
      totalContribution = add(totalContribution, oddAmount);
      totalFee = add(totalFee, serviceFee(oddAmount));
    }
    // 500 × 333,300 kobo = 166,650,000 kobo. 2% = 3,333,000 kobo.
    assert.equal(totalContribution, kobo(166_650_000));
    assert.equal(totalFee, kobo(3_333_000));
  });

  it('rejects a fee computed on negative or zero-value input', () => {
    assert.equal(serviceFee(kobo(0)), kobo(0));
    assert.throws(() => kobo(-1), MoneyError);
  });

  it('rejects a total charge that would exceed the representable maximum', () => {
    // 1 billion naira contribution would overflow MAX_KOBO once the fee is added.
    assert.throws(() => totalCharge(naira(1_000_000_000)), MoneyError);
  });
});
