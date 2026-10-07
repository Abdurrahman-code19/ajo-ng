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
import { loadConfig } from '../src/config.js';
import {
  AccessTokenError,
  createAccessTokenPair,
  generateEphemeralSigningKey,
} from '../src/access-token.js';
import { SignJWT, importPKCS8 } from 'jose';
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

  it('refuses to construct in production with no relay', () => {
    // The failure this prevents is silent and hands over accounts: the logging
    // sender writes the plaintext token to stdout, so a deploy with no transport
    // would publish every verification link. Refusing at construction means the
    // process does not start, which is loud.
    assert.throws(() => createVerificationSender('production', sink), /MAIL_RELAY_URL/);
  });

  it('uses the relay in production when one is configured', async () => {
    // The check that the production sender is not the logging sender: the
    // logging sender's only observable effect is the log line, so asserting the
    // line is absent is the assertion.
    const logged: object[] = [];
    const spy = { info: (fields: object): void => void logged.push(fields) };

    const sender = createVerificationSender('production', spy, {
      url: 'http://127.0.0.1:1/never-reached',
      token: 'relay-secret',
      from: 'no-reply@example.ng',
    });

    // Rejected because nothing listens there, which is the other property: a
    // relay failure is a failure rather than a silent success.
    await assert.rejects(() =>
      sender.sendVerificationToken({ to: 'a@b.ng', userId: 'x', token: 't' }),
    );
    assert.equal(logged.length, 0, 'the production sender logged the token');
  });

  it('gives the logging sender outside production', async () => {
    const logged: object[] = [];
    const sender = createVerificationSender('development', {
      info: (fields: object): void => void logged.push(fields),
    });
    await sender.sendVerificationToken({ to: 'a@b.ng', userId: 'x', token: 't' });
    assert.equal(logged.length, 1, 'the development sender did not log');
  });

  it('uses the relay in development when one is configured', async () => {
    // The demo runs development with a local relay stub so verification tokens
    // travel the production path (and land in the demo mailbox) instead of only
    // a log line. A configured relay must win over logging even outside prod.
    const logged: object[] = [];
    const sender = createVerificationSender(
      'development',
      { info: (fields: object): void => void logged.push(fields) },
      { url: 'http://127.0.0.1:1/never-reached', token: 'relay-secret', from: 'no-reply@example.ng' },
    );
    await assert.rejects(() =>
      sender.sendVerificationToken({ to: 'a@b.ng', userId: 'x', token: 't' }),
    );
    assert.equal(logged.length, 0, 'the development sender logged the token');
  });
});

describe('the mail relay configuration', () => {
  const base = { PGUSER: 'ajo_api', PGPASSWORD: 'p', REDIS_URL: 'redis://127.0.0.1:6379' };

  it('is absent when nothing is set, which is a valid development state', () => {
    assert.equal(loadConfig(base).mail, undefined);
  });

  it('is read when all three variables are set', () => {
    const config = loadConfig({
      ...base,
      MAIL_RELAY_URL: 'https://relay.example.ng/send',
      MAIL_RELAY_TOKEN: 'secret',
      MAIL_FROM: 'no-reply@example.ng',
    });
    assert.deepEqual(config.mail, {
      url: 'https://relay.example.ng/send',
      token: 'secret',
      from: 'no-reply@example.ng',
    });
  });

  it('refuses a half-configured relay, naming what is missing', () => {
    // Without this, an operator who set the URL and forgot the token would boot
    // into a sender that authenticates as nobody and fails on the first signup --
    // in production, discovered by a member.
    assert.throws(
      () => loadConfig({ ...base, MAIL_RELAY_URL: 'https://relay.example.ng/send' }),
      /MAIL_RELAY_TOKEN and MAIL_FROM/,
    );
    assert.throws(() => loadConfig({ ...base, MAIL_FROM: 'no-reply@example.ng' }), /MAIL_RELAY_URL/);
  });
});

// At module scope, not inside `describe`, because `describe`'s callback cannot be
// async and the key pair has to be built before any of the tests run. Top-level
// await is fine here: the test file is a module.
const tokenKeys = generateEphemeralSigningKey();
const { signer, verifier } = await createAccessTokenPair(tokenKeys);

describe('the access token', () => {
  const claims = { userId: '3f2504e0-4f89-41d3-9a0c-0305e82c3301', sessionId: '9c858901-8a57-4791-81fe-4c455b099bc9' };
  const now = new Date('2026-01-01T00:00:00Z');

  it('round-trips the member and the session it was minted for', async () => {
    const token = await signer.issue(claims, now);
    assert.deepEqual(await verifier.verify(token, now), claims);
  });

  it('is EdDSA over a compact JWT, which is what 12.4.1 asks for', async () => {
    // The header is not a secret and is not encrypted, so asserting on it is free
    // and pins the algorithm to the spec. `jose` will not emit anything else, and
    // the point of the assertion is that a future change to RS256 would fail here
    // rather than in a client's decoder.
    const token = await signer.issue(claims, now);
    const [rawHeader] = token.split('.');
    const header = JSON.parse(Buffer.from(rawHeader as string, 'base64url').toString()) as {
      alg: string;
      typ: string;
    };
    assert.equal(header.alg, 'EdDSA');
    assert.equal(header.typ, 'JWT');
  });

  it('carries the member and the session, and carries no authority', async () => {
    // Three claims only. A token that named a role or an account state would be a
    // decision recorded at login and obeyed for 15 minutes after the decision was
    // reversed, so the absence is the property -- there is nothing in here that
    // RLS could be argued out of.
    const token = await signer.issue(claims, now);
    const payload = JSON.parse(
      Buffer.from(token.split('.')[1] as string, 'base64url').toString(),
    ) as Record<string, unknown>;
    assert.equal(payload['sub'], claims.userId);
    assert.equal(payload['sid'], claims.sessionId);
    assert.ok('jti' in payload, 'a token needs an id so two minted in the same second differ');
    for (const forbidden of ['role', 'email', 'status', 'is_email_verified', 'permissions']) {
      assert.ok(!(forbidden in payload), `the token must not carry ${forbidden}`);
    }
  });

  it('is accepted right up to its last second and refused in the next one', async () => {
    const token = await signer.issue(claims, now);
    const lastGood = new Date(now.getTime() + (15 * 60 - 1) * 1000);
    await verifier.verify(token, lastGood);

    const firstBad = new Date(now.getTime() + 15 * 60 * 1000);
    await assert.rejects(verifier.verify(token, firstBad), AccessTokenError);
  });

  it('refuses a token signed by another key, without saying so', async () => {
    // The other half of `jose`'s value: a verifier built from a different key must
    // reject. The *same error* as an expired token is the part that matters -- a
    // caller that can distinguish "wrong signature" from "expired" has a free
    // validity check on a token they stole.
    const other = await createAccessTokenPair(generateEphemeralSigningKey());
    const forged = await other.signer.issue(claims, now);

    const fromOurs = assert.rejects(verifier.verify(forged, now), AccessTokenError);
    const fromExpired = assert.rejects(
      verifier.verify(await signer.issue(claims, now), new Date(now.getTime() + 3600_000)),
      AccessTokenError,
    );
    await Promise.all([fromOurs, fromExpired]);
  });

  it('refuses the alg-none and HS256 shapes a hand-rolled verifier can be talked into', async () => {
    // Constructed here rather than with `jose`, because `jose` will not mint them:
    // the point is what the *verifier* does when handed one. `alg: none` with the
    // signature segment removed, and an HS256 token signed with the public key --
    // the classic confusion attack, which works against any verifier that reads
    // `alg` and picks a verifier from it.
    const header = (alg: string) =>
      Buffer.from(JSON.stringify({ alg, typ: 'JWT' })).toString('base64url');
    const payload = Buffer.from(
      JSON.stringify({
        sub: claims.userId,
        sid: claims.sessionId,
        iss: 'ajo-api',
        aud: 'ajo-app',
        exp: Math.floor(now.getTime() / 1000) + 900,
      }),
    ).toString('base64url');

    const noneToken = `${header('none')}.${payload}.`;
    await assert.rejects(verifier.verify(noneToken, now), AccessTokenError);

    const hs256 = await new SignJWT({ sid: claims.sessionId })
      .setProtectedHeader({ alg: 'HS256' })
      .setSubject(claims.userId)
      .setIssuer('ajo-api')
      .setAudience('ajo-app')
      .setExpirationTime(Math.floor(now.getTime() / 1000) + 900)
      .sign(Buffer.from(tokenKeys.publicKeyPem));
    await assert.rejects(verifier.verify(hs256, now), AccessTokenError);
  });

  it('refuses a token with no session, because a member with no session is not a session', async () => {
    const noSession = await new SignJWT({})
      .setProtectedHeader({ alg: 'EdDSA' })
      .setSubject(claims.userId)
      .setIssuer('ajo-api')
      .setAudience('ajo-app')
      .setIssuedAt(Math.floor(now.getTime() / 1000))
      .setExpirationTime(Math.floor(now.getTime() / 1000) + 900)
      .sign(await importPKCS8(tokenKeys.privateKeyPem, 'EdDSA'));

    await assert.rejects(verifier.verify(noSession, now), AccessTokenError);
  });

  it('refuses a token minted for another audience', async () => {
    // A token this platform signed, for something else. Only the audience check
    // stands between it and acceptance, which is why the audience is configured
    // rather than assumed.
    const foreign = await new SignJWT({ sid: claims.sessionId })
      .setProtectedHeader({ alg: 'EdDSA' })
      .setSubject(claims.userId)
      .setIssuer('ajo-api')
      .setAudience('some-other-service')
      .setIssuedAt(Math.floor(now.getTime() / 1000))
      .setExpirationTime(Math.floor(now.getTime() / 1000) + 900)
      .sign(await importPKCS8(tokenKeys.privateKeyPem, 'EdDSA'));

    await assert.rejects(verifier.verify(foreign, now), AccessTokenError);
  });
});

describe('the signing key configuration', () => {
  const base = { PGUSER: 'ajo_api', PGPASSWORD: 'p', REDIS_URL: 'redis://127.0.0.1:6379' };
  const pair = generateEphemeralSigningKey();

  it('is read when both halves are set', () => {
    const config = loadConfig({
      ...base,
      ACCESS_TOKEN_PRIVATE_KEY: pair.privateKeyPem,
      ACCESS_TOKEN_PUBLIC_KEY: pair.publicKeyPem,
    });
    assert.equal(config.signingKey.source, 'configured');
    assert.equal(config.signingKey.privateKeyPem, pair.privateKeyPem);
  });

  it('is generated for development, and says that it was', () => {
    // The `source` field is what the composition root and the logs read, so an
    // operator can see a development key in a non-development log line.
    const config = loadConfig({ ...base, NODE_ENV: 'development' });
    assert.equal(config.signingKey.source, 'ephemeral');
    assert.match(config.signingKey.privateKeyPem, /^-----BEGIN PRIVATE KEY-----/);
    assert.match(config.signingKey.publicKeyPem, /^-----BEGIN PUBLIC KEY-----/);
  });

  it('is refused outright in production rather than generated', () => {
    // The failure this prevents is not theoretical: two instances would each
    // generate a different key, so a member's token would be accepted by one and
    // rejected by the other, and a load balancer would log people out at random.
    assert.throws(
      () => loadConfig({ ...base, NODE_ENV: 'production' }),
      /NODE_ENV is production/,
    );
  });

  it('is refused when half configured, naming the missing half', () => {
    assert.throws(
      () => loadConfig({ ...base, ACCESS_TOKEN_PRIVATE_KEY: pair.privateKeyPem }),
      /ACCESS_TOKEN_PUBLIC_KEY not set/,
    );
  });
});

describe('the login limits', () => {
  const base = { PGUSER: 'ajo_api', PGPASSWORD: 'p', REDIS_URL: 'redis://127.0.0.1:6379' };

  it('default to the five sessions 12.4.3 fixes', () => {
    assert.equal(loadConfig(base).login.maxSessions, 5);
  });

  it('are read from the environment', () => {
    const config = loadConfig({
      ...base,
      LOGIN_RATE_LIMIT: '4',
      LOGIN_WINDOW_MS: '60000',
      MAX_SESSIONS: '2',
    });
    assert.deepEqual(config.login, { rateLimit: 4, windowMs: 60_000, maxSessions: 2 });
  });
});
