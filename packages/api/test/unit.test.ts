/**
 * Unit tests for the pure parts of registration.
 *
 * These need neither a database nor Redis, so they run in the `verify` job that
 * has no services. That is the point: the normalising and hashing rules are the
 * ones most likely to be "tested by hand" and quietly broken later, and they
 * are cheap enough to keep honest without a container.
 */
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  ValidationError,
  burnPasswordVerification,
  generateToken,
  hashPassword,
  hashToken,
  normaliseNigerianPhone,
  verifyPassword,
} from '../src/identity.js';
import { createVerificationSender } from '../src/mailer.js';
import { uuidv7 } from '../src/uuid.js';

describe('normaliseNigerianPhone', () => {
  // The property under test is that all of these are one identity. If any two of
  // them produced different strings, the same person would be able to create
  // two accounts and the unique index on users.phone_e164 would not stop them.
  const spellings = [
    '08031234567',
    '+2348031234567',
    '2348031234567',
    '0803 123 4567',
    '+234 803 123 4567',
    '  08031234567  ',
  ];

  it('collapses every spelling of one number to one E.164 value', () => {
    const results = spellings.map(normaliseNigerianPhone);
    assert.equal(new Set(results).size, 1, `expected one value, got ${results.join(', ')}`);
    assert.equal(results[0], '+2348031234567');
  });

  it('rejects a number that is not a Nigerian mobile', () => {
    // 0803 123 4567 is 11 digits, which is too long for the Nigerian scheme.
    assert.throws(() => normaliseNigerianPhone('080312345678901'), ValidationError);
  });

  it('rejects an empty value rather than normalising it to something', () => {
    assert.throws(() => normaliseNigerianPhone('   '), ValidationError);
  });

  it('reports which field was wrong', () => {
    // The handler maps this onto a 422 with the field name, so the field has to
    // survive the throw rather than being lost in the message.
    try {
      normaliseNigerianPhone('not a phone');
      assert.fail('should have thrown');
    } catch (error) {
      assert.ok(error instanceof ValidationError);
      assert.equal(error.field, 'phone');
    }
  });
});

describe('password hashing', () => {
  it('produces an Argon2id hash, not Argon2i or Argon2d', () => {
    // Asserted from the PHC prefix rather than from the enum passed in, because
    // the prefix is what makes the stored hash self-describing: it is what a
    // future parameter change has to preserve, and what a wrong enum value would
    // silently break while every other assertion still passed.
    return hashPassword('a long enough password').then((hash) => {
      assert.ok(hash.startsWith('$argon2id$'), `expected $argon2id$, got ${hash.slice(0, 12)}`);
    });
  });

  it('never stores the plaintext', () => {
    return hashPassword('correct horse battery staple').then((hash) => {
      assert.ok(!hash.includes('correct horse'));
    });
  });

  it('verifies the right password and refuses the wrong one', async () => {
    const hash = await hashPassword('correct horse battery staple');
    assert.equal(await verifyPassword(hash, 'correct horse battery staple'), true);
    assert.equal(await verifyPassword(hash, 'correct horse battery stapl'), false);
  });

  it('salts, so one password hashes differently every time', async () => {
    const [a, b] = await Promise.all([
      hashPassword('correct horse battery staple'),
      hashPassword('correct horse battery staple'),
    ]);
    assert.notEqual(a, b);
  });

  it('treats a corrupt stored hash as a refusal, not a crash', async () => {
    // Returning false keeps a damaged row a failed login instead of a 500, and
    // keeps "this account is broken" indistinguishable from "wrong password".
    assert.equal(await verifyPassword('not-a-phc-string', 'anything'), false);
  });

  it('burns comparable time for an account that does not exist', async () => {
    // The reason this exists: without it, "no such user" returns without ever
    // verifying a hash, and that difference is a user-enumeration oracle.
    const real = await hashPassword('correct horse battery staple');
    const absent = Date.now();
    await burnPasswordVerification('a password that no account has');
    const absentElapsed = Date.now() - absent;
    const presentStart = Date.now();
    await verifyPassword(real, 'wrong');
    const presentElapsed = Date.now() - presentStart;
    // Loose, because a timing assertion on a shared CI runner is a flaky test
    // wearing a disguise. The claim is only that the absent path is not free.
    assert.ok(presentElapsed > 5, `verification took ${presentElapsed}ms, which is suspiciously fast`);
    assert.ok(absentElapsed > 5, `dummy verification took ${absentElapsed}ms, which is suspiciously fast`);
  });
});

describe('token hashing', () => {
  it('is deterministic, so a presented token can be looked up', () => {
    assert.deepEqual(hashToken('abc'), hashToken('abc'));
  });

  it('differs between tokens', () => {
    assert.notDeepEqual(hashToken('abc'), hashToken('abd'));
  });

  it('is a 32-byte digest, not a hex string', () => {
    // bytea is what the column is, and a hex string would be stored as its
    // 64 characters -- which would still work but would be twice the size and
    // would compare correctly only by accident of encoding.
    assert.equal(hashToken('abc').length, 32);
  });

  it('generates distinct, URL-safe tokens', () => {
    const tokens = Array.from({ length: 200 }, () => generateToken());
    assert.equal(new Set(tokens).size, 200);
    for (const token of tokens) {
      assert.match(token, /^[A-Za-z0-9_-]+$/, `${token} is not URL-safe`);
    }
  });
});

describe('uuidv7', () => {
  it('is a well-formed v7 UUID', () => {
    assert.match(
      uuidv7(),
      /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
  });

  it('puts the timestamp in the high bits, so keys sort by creation time', () => {
    // This is the reason for v7 rather than v4: every table's primary key
    // defaults to app.uuidv7() so inserts land at the end of the index. A v4
    // would work and would quietly undo that.
    const early = uuidv7(1_700_000_000_000).replace(/-/g, '');
    const late = uuidv7(1_800_000_000_000).replace(/-/g, '');
    assert.ok(early < late, 'earlier timestamp did not sort first');
  });

  it('is unique across many calls in the same millisecond', () => {
    const ids = Array.from({ length: 5_000 }, () => uuidv7(1_700_000_000_000));
    assert.equal(new Set(ids).size, 5_000);
  });
});

describe('the verification sender guards production', () => {
  const sink = { info: (): void => undefined };

  it('refuses to hand back the logging sender in production', () => {
    // The failure this prevents is silent and hands over accounts: the logging
    // sender writes the plaintext token to stdout, so a deploy with no transport
    // would publish every verification link. Refusing at construction means the
    // process does not start, which is loud.
    assert.throws(() => createVerificationSender('production', sink), /email transport/i);
  });

  it('gives the logging sender everywhere else', async () => {
    const sender = createVerificationSender('development', sink);
    // Constructed, and usable enough to accept a message without throwing.
    await sender.sendVerificationToken({ to: 'a@b.ng', userId: 'x', token: 't' });
  });
});
