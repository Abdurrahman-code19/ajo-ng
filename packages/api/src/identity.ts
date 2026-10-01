/**
 * Identifiers, phone numbers, and password hashing -- the three things
 * registration must get right before it touches the database.
 *
 * They live together because they are all pure, all fail in ways that need to
 * be distinguishable by the caller, and none of them belongs in `packages/domain`:
 * the domain core imports nothing from the outside world, and a Argon2id hash is
 * an infrastructure concern even though the rule that a password is never stored
 * in plaintext is a domain one.
 */
import { createHash, randomBytes } from 'node:crypto';
import * as argon2 from '@node-rs/argon2';
import { parsePhoneNumberFromString } from 'libphonenumber-js';

/**
 * Argon2id, as the numeric constant the library's `Algorithm` enum holds.
 *
 * Spelled out rather than imported because `Algorithm` is a `const enum`, and
 * `verbatimModuleSyntax` refuses to read one at runtime -- it is inlined by the
 * compiler or it does not exist. The number is not left to memory: a test
 * asserts the stored hash begins `$argon2id$`, which is the property that
 * actually matters, since that prefix is what makes the hash self-describing and
 * what a future `algorithm` change would silently break.
 */
const ARGON2ID = 2;

/**
 * The cost parameters, in one place, because they are a decision rather than a
 * constant. 19 MiB and two passes is the OWASP floor for Argon2id; a hardware
 * budget decides whether to go higher, and when it does the change is one edit
 * here rather than a search.
 *
 * Raising it does not invalidate existing hashes: the PHC string that
 * `user_credentials.argon2_hash` stores carries its own parameters, so a hash
 * written under these settings still verifies after they change.
 */
const ARGON2_OPTIONS = {
  algorithm: ARGON2ID,
  memoryCost: 19_456,
  timeCost: 2,
  parallelism: 1,
} as const;

export async function hashPassword(plaintext: string): Promise<string> {
  return argon2.hash(plaintext, ARGON2_OPTIONS);
}

export async function verifyPassword(
  hash: string,
  plaintext: string,
): Promise<boolean> {
  try {
    return await argon2.verify(hash, plaintext, ARGON2_OPTIONS);
  } catch {
    // A malformed stored hash is not a valid password. It returns false rather
    // than throwing, so a corrupt row denies access instead of turning every
    // login attempt into a 500 -- and, more importantly, so it cannot be used
    // to tell "wrong password" from "this account is broken" from the outside.
    return false;
  }
}

/**
 * A dummy hash, verified against when the user does not exist.
 *
 * Without it, login answers "no such user" measurably faster than "wrong
 * password", because the second case pays for an Argon2id verification and the
 * first does not. That difference is a user-enumeration oracle, and it is
 * measurable over a network. The cost is one hash per failed login for a
 * non-existent account, which is the cost the alternative implies anyway.
 */
let dummyHash: string | undefined;

export async function burnPasswordVerification(plaintext: string): Promise<void> {
  dummyHash ??= await argon2.hash('a password that no account has', ARGON2_OPTIONS);
  await verifyPassword(dummyHash, plaintext);
}

/** A 256-bit token, URL-safe. Used for email verification. */
export function generateToken(): string {
  return randomBytes(32).toString('base64url');
}

/**
 * The hash a token is stored as.
 *
 * SHA-256, not Argon2id, and the difference is deliberate. Argon2id exists to
 * slow down guessing a *low-entropy* secret; an email verification token is 256
 * random bits, so there is nothing to guess and the cost would only be paid on
 * the legitimate path. What the token table needs is that a database
 * disclosure does not yield working tokens, and a preimage-resistant digest over
 * a full-entropy random value provides exactly that. It also means verification
 * is one indexed lookup instead of a deliberately slow one.
 */
export function hashToken(token: string): Buffer {
  return createHash('sha256').update(token, 'utf8').digest();
}

export class ValidationError extends Error {
  readonly field: string;

  constructor(field: string, message: string) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}

/**
 * Nigerian numbers in E.164, which is what `users.phone_e164` stores.
 *
 * `BR-030` is one identity, one account, and this is the function that enforces
 * it: two spellings of the same number must not produce two accounts, so the
 * value is normalised to its canonical form *before* the uniqueness check rather
 * than compared as typed. A caller sending `0803 123 4567` and another sending
 * `+2348031234567` are the same person.
 */
export function normaliseNigerianPhone(input: string): string {
  const trimmed = input.trim();
  if (trimmed === '') {
    throw new ValidationError('phone', 'a phone number is required');
  }

  // Normalise to the country code, because a Nigerian number is written in
  // several ways and all of them are the same identity: `0803...` (national),
  // `+234803...` (international), `234803...` (bare code). Stripping whichever
  // of those the caller used and re-adding the code covers all three spellings
  // exactly, and without it the result would depend on how the number was typed.
  const national = trimmed.replace(/^\+?234/, '').replace(/^0+/, '');
  const significant = national.replace(/\D/g, '');

  // Length checked here rather than left to the library, because libphonenumber
  // reports `+234080312345678901` as a *valid* Nigerian number: with a country
  // code supplied it strips the leading zero and checks the result against a
  // general description that does not constrain the length. That is fine for
  // parsing a number somebody dialled and wrong for a column with a unique index
  // on it, where "valid" has to mean "this is exactly a Nigerian mobile number"
  // or junk gets in with a unique constraint to protect.
  //
  // Ten digits after the country code, starting 7, 8, or 9 -- the mobile ranges.
  // Landlines are deliberately not accepted: a member authenticates with a
  // device that receives SMS, and a number that cannot receive one is not a
  // verification channel.
  if (significant.length !== 10 || !/^[789]/.test(significant)) {
    throw new ValidationError(
      'phone',
      'that is not a valid Nigerian mobile number in international format',
    );
  }

  const parsed = parsePhoneNumberFromString(`+234${significant}`, 'NG');
  if (parsed === undefined || !parsed.isValid() || parsed.country !== 'NG') {
    throw new ValidationError('phone', 'that is not a valid Nigerian mobile number');
  }
  return parsed.number;
}
