import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  MoneyError,
  add,
  format,
  fromDecimalString,
  kobo,
  multiply,
  naira,
  subtract,
  sum,
} from '../src/money.js';

describe('Money', () => {
  it('represents kobo exactly, with no floating point', () => {
    assert.equal(naira(10_000), 1_000_000);
    assert.equal(format(naira(10_000)), '10000.00');
  });

  it('parses decimal strings without float error', () => {
    // 0.1 + 0.2 in floats is the classic bug; string parsing must be exact.
    assert.equal(fromDecimalString('1000.50'), 100_050);
    assert.equal(fromDecimalString('0.01'), 1);
    assert.equal(add(fromDecimalString('0.10'), fromDecimalString('0.20')), 30);
  });

  it('rejects malformed decimal input rather than coercing it', () => {
    for (const bad of ['', 'abc', '10.999', '-5', '1e5', '10.', '.5', '1,000']) {
      assert.throws(() => fromDecimalString(bad), MoneyError, `should reject: "${bad}"`);
    }
  });

  it('rejects negative and non-integer money', () => {
    assert.throws(() => kobo(-1), MoneyError);
    assert.throws(() => kobo(10.5), MoneyError);
    assert.throws(() => naira(10.5), MoneyError);
    assert.throws(() => multiply(kobo(100), 1.5), MoneyError);
  });

  it('refuses to underflow below zero', () => {
    assert.throws(() => subtract(kobo(100), kobo(101)), MoneyError);
  });

  it('detects overflow beyond safe integers', () => {
    assert.throws(() => add(kobo(Number.MAX_SAFE_INTEGER), kobo(1)), MoneyError);
  });

  it('sums a list of contributions without drift', () => {
    const contributions = Array.from({ length: 1000 }, () => naira(10_000));
    // 1000 x NGN 10,000.00 = NGN 10,000,000.00
    assert.equal(sum(contributions), 1_000_000_000);
    assert.equal(format(sum(contributions)), '10000000.00');
  });

  it('computes a 10-member pot at 10,000 naira each', () => {
    assert.equal(format(multiply(naira(10_000), 10)), '100000.00');
  });
});
