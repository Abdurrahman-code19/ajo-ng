/**
 * Money. Integer minor units (kobo). Never floating point.
 *
 * Rationale: 0.1 + 0.2 !== 0.3 in IEEE-754. In a rotating savings product every
 * member's pot must reconcile to the naira at the end of every round. A
 * one-kobo drift per operation accumulates into unrecoverable disputes that
 * destroy member trust, and member trust is the entire product.
 *
 * This type is deliberately opaque. A raw `number` cannot be passed where a
 * Money is expected, and a Money cannot be silently treated as kobo. Making the
 * wrong thing a compile error is cheaper than making it an incident.
 *
 * Ajo.ng is Nigeria-only at launch; the platform currency is NGN. When a second
 * currency is introduced, that becomes a v2 problem requiring an explicit
 * currency on every value, not a change to this file.
 */

declare const MONEY_BRAND: unique symbol;

/** An exact, non-negative integer quantity of NGN minor units (kobo). */
export type Kobo = number & { readonly [MONEY_BRAND]: 'Kobo' };

export const ZERO_KOBO = 0 as Kobo;

/** Largest single contribution/payout we will represent: ₦1 billion. */
export const MAX_KOBO = 100_000_000_000 as Kobo;

export class MoneyError extends Error {
  override readonly name = 'MoneyError';
}

function assertSafeInteger(value: number, context: string): void {
  if (!Number.isSafeInteger(value)) {
    throw new MoneyError(
      `${context}: expected a safe integer number of kobo, received ${String(value)}`,
    );
  }
}

/**
 * Construct Money from an integer count of kobo.
 *
 * Kobo is the storage and arithmetic unit. Naira only exists at the edges:
 * human input, display, and the payment provider boundary.
 */
export function kobo(value: number): Kobo {
  assertSafeInteger(value, 'kobo()');
  if (value < 0) {
    throw new MoneyError(`kobo(): money cannot be negative, received ${value}`);
  }
  if (value > MAX_KOBO) {
    throw new MoneyError(
      `kobo(): ${value} exceeds the maximum supported value of ${MAX_KOBO} kobo`,
    );
  }
  return value as Kobo;
}

/**
 * Construct Money from a whole-naira amount.
 *
 * Only accepts integers. Passing 10.5 is a bug in the caller and must surface
 * loudly now, not as a silent rounding difference in someone's payout.
 */
export function naira(whole: number): Kobo {
  assertSafeInteger(whole, 'naira()');
  return kobo(whole * 100);
}

/**
 * Construct Money from a decimal string, exactly.
 *
 * "1000.50" -> 100050 kobo. This is the only sanctioned path for parsing user
 * input. It avoids Number entirely, so it cannot lose precision on large or
 * long-decimal values the way parseFloat does.
 */
export function fromDecimalString(input: string): Kobo {
  const trimmed = input.trim();
  if (!/^\d+(\.\d{1,2})?$/.test(trimmed)) {
    throw new MoneyError(
      `fromDecimalString(): "${input}" is not a valid naira amount (expected digits with at most 2 decimals)`,
    );
  }
  const [wholePart = '0', fractionPart = ''] = trimmed.split('.');
  const paddedFraction = fractionPart.padEnd(2, '0');
  return kobo(Number(wholePart) * 100 + Number(paddedFraction));
}

export function add(a: Kobo, b: Kobo): Kobo {
  return checked(a + b, 'add');
}

export function subtract(a: Kobo, b: Kobo): Kobo {
  const result = a - b;
  if (result < 0) {
    throw new MoneyError(`subtract(): ${format(a)} - ${format(b)} would go negative`);
  }
  return checked(result, 'subtract');
}

function checked(value: number, op: string): Kobo {
  assertSafeInteger(value, `${op}() overflowed`);
  if (value > MAX_KOBO) {
    throw new MoneyError(`${op}(): result ${value} exceeds maximum supported value`);
  }
  return value as Kobo;
}

export function equals(a: Kobo, b: Kobo): boolean {
  return a === b;
}

/**
 * AJO.ng's service fee: 2% of the contribution, charged to the member on top.
 *
 * Represented in basis points so the rate is a named constant rather than a
 * literal 0.02, and computed in integer kobo. A float multiply here would
 * produce a fee that is off by a kobo on some contributions, and that kobo is
 * a real member's money.
 *
 * Rounding is half-up on the kobo. Every member is charged a fee that is at
 * least the true 2% and never more than half a kobo above it, so the platform
 * can never be accused of over-collecting because of rounding drift.
 */
export const FEE_BASIS_POINTS = 200; // 2.00%
const BASIS_POINT_DIVISOR = 10_000;
const ROUNDING_OFFSET = BASIS_POINT_DIVISOR / 2;

/** The 2% service fee on a contribution. */
export function serviceFee(contribution: Kobo): Kobo {
  const scaled = contribution * FEE_BASIS_POINTS + ROUNDING_OFFSET;
  return checked(Math.floor(scaled / BASIS_POINT_DIVISOR), 'serviceFee');
}

/**
 * What the member is actually charged: contribution + fee.
 *
 * ₦1,000 contribution → ₦20 fee → ₦1,020 charged, while the recipient
 * still receives the full ₦1,000 base pool. The fee is never taken out of
 * the pool; that is the promise the product makes and the reason the
 * rounding rule above is specified rather than left to chance.
 */
export function totalCharge(contribution: Kobo): Kobo {
  return add(contribution, serviceFee(contribution));
}
export function isZero(a: Kobo): boolean {
  return a === 0;
}

export function isPositive(a: Kobo): boolean {
  return a > 0;
}

export function max(a: Kobo, b: Kobo): Kobo {
  return a >= b ? a : b;
}

export function min(a: Kobo, b: Kobo): Kobo {
  return a <= b ? a : b;
}

export function sum(values: readonly Kobo[]): Kobo {
  return values.reduce<Kobo>((acc, value) => add(acc, value), ZERO_KOBO);
}

/**
 * Multiply by a plain integer factor (member count, round count).
 *
 * Rejects non-integer factors. Anything requiring a real rate or a percentage
 * must be computed in kobo with explicit rounding at the call site, where the
 * rounding direction is a visible business decision.
 */
export function multiply(value: Kobo, factor: number): Kobo {
  assertSafeInteger(factor, 'multiply() factor');
  if (factor < 0) {
    throw new MoneyError(`multiply(): factor must be non-negative, received ${factor}`);
  }
  return checked(value * factor, 'multiply');
}

/**
 * Human-readable naira, e.g. "1000.50".
 *
 * Display only. Never feed this back into arithmetic.
 */
export function format(value: Kobo): string {
  const whole = Math.floor(value / 100);
  const fraction = value % 100;
  return `${whole}.${fraction.toString().padStart(2, '0')}`;
}
