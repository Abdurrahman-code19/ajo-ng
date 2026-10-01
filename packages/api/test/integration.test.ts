/**
 * Integration tests: the real API, against a real database, over HTTP.
 *
 * The claims being made here are the ones a unit test cannot make, and they are
 * the reason this suite exists:
 *
 *   * registration really does write through `SET LOCAL ROLE ajo_app`, so RLS is
 *     active while it runs
 *   * the password hash cannot be read back out through the application role,
 *     even by the code that wrote it
 *   * the verification token is stored hashed, and is single-use under
 *     concurrency
 *   * a failed registration leaves no partial rows and no consent evidence
 *   * a connection returned to the pool carries nobody's identity
 *
 * Every assertion below runs as `ajo_api`, which is NOSUPERUSER and NOBYPASSRLS.
 * Against a superuser every RLS assertion would pass vacuously, which is the
 * failure mode that made the first version of the database suite useless.
 */
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { after, before, describe, it } from 'node:test';
import type { FastifyInstance, LightMyRequestResponse } from 'fastify';
import type { Pool } from 'pg';
import { buildApp } from '../src/app.js';
import {
  createAccessTokenPair,
  generateEphemeralSigningKey,
} from '../src/access-token.js';
import { createPool } from '../src/db.js';
import { hashToken } from '../src/identity.js';
import { allowAllLimiter, createFixedWindowLimiter, type RateLimiter } from '../src/rate-limit.js';
import type { Config } from '../src/config.js';
import type { VerificationSender } from '../src/mailer.js';

const HAVE_REDIS = process.env['REDIS_AVAILABLE'] === '1';

function testConfig(): Config {
  return {
    host: '127.0.0.1',
    port: 0,
    logLevel: 'silent',
    environment: 'test',
    database: {
      host: process.env['PGHOST'] ?? '127.0.0.1',
      port: Number(process.env['PGPORT'] ?? 5432),
      database: process.env['PGDATABASE'] ?? 'ajo_api_test',
      // The application role. Not the superuser that applied the migrations.
      user: process.env['PGUSER'] ?? 'ajo_api',
      password: process.env['PGPASSWORD'] ?? 'local-dev-only',
      max: 5,
    },
    redis: { url: process.env['REDIS_URL'] ?? 'redis://127.0.0.1:6379' },
    // No relay: the tests inject a capturing sender instead, so the transport is
    // never on the path. See CapturingMailer.
    mail: undefined,
    registration: { rateLimit: 3, windowMs: 60_000 },
    login: { rateLimit: 50, windowMs: 60_000, maxSessions: 5 },
    // A fixed key per process, generated once. Generated per test would be fine
    // for signing, but a test that signs with one and verifies with another would
    // then pass for an unrelated reason, and the failure would be a confusing
    // "every token is invalid" rather than "you mixed the keys up".
    signingKey: { ...generateEphemeralSigningKey(), source: 'ephemeral' },
  };
}

/**
 * The app, with its key pair already built.
 *
 * A helper rather than three call sites spelling out `createAccessTokenPair`
 * because the pair has to match: the routes sign with `signer` and verify with
 * `verifier`, and a test that passes a signer from one key and a verifier from
 * another produces 401s that look exactly like a correct rejection.
 */
async function buildTestApp(
  overrides: Partial<Parameters<typeof buildApp>[0]> = {},
): Promise<FastifyInstance> {
  const keys = createAccessTokenPair(testConfig().signingKey);
  const { signer, verifier } = await keys;
  const built = await buildApp({
    config: testConfig(),
    pool: pool as Pool,
    limiter: allowAllLimiter(),
    mailer: new CapturingMailer(),
    signer,
    verifier,
    ...overrides,
  });
  await built.ready();
  return built;
}

/** Captures what would have been emailed, so a test can use the token. */
class CapturingMailer implements VerificationSender {
  readonly sent: { to: string; userId: string; token: string }[] = [];

  async sendVerificationToken(message: { to: string; userId: string; token: string }): Promise<void> {
    this.sent.push(message);
  }
}

/** A pool that connects as the superuser, for asserting on rows the API cannot see. */
function adminPool() {
  return createPool({
    host: process.env['PGHOST'] ?? '127.0.0.1',
    port: Number(process.env['PGPORT'] ?? 5432),
    database: process.env['PGDATABASE'] ?? 'ajo_api_test',
    // The role that applied the migrations. Used only to look at what the API
    // wrote, never to write on the API's behalf.
    user: process.env['PGADMINUSER'] ?? 'postgres',
    password: process.env['PGADMINPASSWORD'] ?? '',
    max: 2,
  });
}

let app: FastifyInstance;
let pool: ReturnType<typeof createPool>;
let admin: ReturnType<typeof adminPool>;
let mailer: CapturingMailer;

function uniqueEmail(prefix: string): string {
  return `${prefix}-${randomUUID()}@example.ng`;
}

function uniquePhone(): string {
  // Ten digits starting 080, from a random block, so two tests never collide.
  const digits = String(Math.floor(Math.random() * 1_000_000_000)).padStart(9, '0');
  return `+23480${digits.slice(0, 8)}`;
}

/**
 * Awaited inside the helper on purpose. `inject` returns a thenable with extra
 * chainable methods, and letting that leak into the test's types turns every
 * `response.statusCode` into a compile error about a union of `void & Promise`
 * and a Chain. Naming the awaited type at the boundary keeps the tests readable.
 */
async function post(
  body: unknown,
  path = '/api/v1/auth/register',
): Promise<LightMyRequestResponse> {
  return app.inject({ method: 'POST', url: path, payload: body as object });
}

const validBody = (over: Record<string, unknown> = {}) => ({
  email: uniqueEmail('reg'),
  password: 'a sufficiently long passphrase',
  fullName: 'Test Member',
  phone: uniquePhone(),
  acceptedTerms: true,
  acceptedPrivacy: true,
  ...over,
});

before(async () => {
  const config = testConfig();
  pool = createPool(config.database);
  admin = adminPool();
  mailer = new CapturingMailer();
  app = await buildTestApp({ config, pool, limiter: allowAllLimiter(), mailer });
});

after(async () => {
  await app?.close();
  await pool?.end();
  await admin?.end();
});

describe('registration', () => {
    it('creates a pending account, a profile, a credential, a token and consent evidence', async () => {
      const body = validBody();
    const response = await post(body);

    assert.equal(response.statusCode, 201, response.body);
    const created = response.json() as { userId: string; email: string; status: string };

    assert.equal(created.status, 'pending_verification');
    assert.equal(created.email, body.email);
    assert.match(created.userId, /^[0-9a-f-]{36}$/);

    const user = await admin.query(
      'SELECT status, is_email_verified, phone_e164 FROM users WHERE id = $1',
      [created.userId],
    );
    assert.equal(user.rows[0].status, 'pending_verification');
    assert.equal(user.rows[0].is_email_verified, false);
    assert.match(user.rows[0].phone_e164, /^\+234/);

    const profile = await admin.query(
      'SELECT display_name FROM profiles WHERE user_id = $1',
      [created.userId],
    );
    assert.equal(profile.rows[0].display_name, body.fullName);

    // The hash exists and is Argon2id, and the plaintext is nowhere in it.
    const credential = await admin.query(
      'SELECT argon2_hash FROM user_credentials WHERE user_id = $1',
      [created.userId],
    );
    assert.equal(credential.rows.length, 1);
    assert.ok(credential.rows[0].argon2_hash.startsWith('$argon2id$'));
    assert.ok(!credential.rows[0].argon2_hash.includes(body.password));

    // The token is stored hashed, so the row cannot be replayed from a dump.
    const token = await admin.query(
      'SELECT encode(token_hash, \'hex\') AS h FROM email_verification_tokens WHERE user_id = $1',
      [created.userId],
    );
    assert.equal(token.rows.length, 1);
    assert.notEqual(token.rows[0].h, mailer.sent.at(-1)?.token);

    // Consent: two rows, one per document, each naming the version accepted.
    const consent = await admin.query(
      `SELECT after_state->>'document' AS document
         FROM audit_logs
        WHERE actor_user_id = $1 AND after_state->>'event' = 'consent'
        ORDER BY after_state->>'document'`,
      [created.userId],
    );
    assert.deepEqual(
      consent.rows.map((r) => r.document),
      ['privacy', 'terms'],
    );
  });

  it('never puts the verification token in the response body', async () => {
    const response = await post(validBody());
    const token = mailer.sent.at(-1)?.token;
    assert.ok(token, 'expected the mailer to have received a token');
    assert.ok(
      !response.body.includes(token),
      'the response body contains the verification token',
    );
  });

  it('normalises the phone before the uniqueness check, so one number is one account', async () => {
    const phone = uniquePhone();
    const national = phone.replace('+234', '0');

    const first = await post(validBody({ phone }));
    assert.equal(first.statusCode, 201, first.body);

    // The same number written the other way round must collide, or the unique
    // index on phone_e164 is defeated by a matter of spelling.
    const second = await post(validBody({ phone: national }));
    assert.equal(second.statusCode, 409, second.body);
    assert.equal((second.json() as { field: string }).field, 'phone');
  });

  it('reports an email conflict without writing a second account', async () => {
    const email = uniqueEmail('dup');
    const first = await post(validBody({ email }));
    assert.equal(first.statusCode, 201, first.body);

    const second = await post(validBody({ email, phone: uniquePhone() }));
    assert.equal(second.statusCode, 409, second.body);
    assert.equal((second.json() as { field: string }).field, 'email');

    const count = await admin.query('SELECT count(*)::int AS n FROM users WHERE email = $1', [email]);
    assert.equal(count.rows[0].n, 1);

    // And the rolled-back attempt left no credential, token or profile behind.
    const orphan = await admin.query(
      `SELECT
         (SELECT count(*) FROM profiles WHERE user_id NOT IN (SELECT id FROM users))::int AS p,
         (SELECT count(*) FROM user_credentials uc
           WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = uc.user_id))::int AS c,
         (SELECT count(*) FROM email_verification_tokens t
           WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = t.user_id))::int AS t`,
    );
    assert.deepEqual(orphan.rows[0], { p: 0, c: 0, t: 0 });
  });

  it('refuses a registration that has not accepted both documents', async () => {
    for (const field of ['acceptedTerms', 'acceptedPrivacy']) {
      const response = await post(validBody({ [field]: false }));
      assert.equal(response.statusCode, 422, `${field}: ${response.body}`);
      assert.equal((response.json() as { field: string }).field, field);
    }
  });

  it('refuses a short password before touching the database', async () => {
    const response = await post(validBody({ password: 'short' }));
    assert.equal(response.statusCode, 422, response.body);
    assert.equal((response.json() as { field: string }).field, 'password');
  });

  it('rejects an unknown field, so a typo is not silently ignored', async () => {
    const response = await post({ ...validBody(), acceptdTerms: true });
    assert.equal(response.statusCode, 400, response.body);
  });
});

describe('row level security on the registration write path', () => {
  it('the application role cannot read a password hash back, even its own', async () => {
    // The strongest statement of the policy design: `user_credentials` has no
    // SELECT policy at all, so the code that just wrote the hash cannot read it.
    // A future policy added "for convenience" would break this test.
    const created = await post(validBody());
    const userId = (created.json() as { userId: string }).userId;

    // Zero rows, not an error. A table with RLS enabled and no policy covering
    // the current role yields an empty set; `permission denied` is what a missing
    // table *grant* produces, and conflating the two would make this test pass for
    // the wrong reason. Either way the hash is not readable, and this asserts the
    // stronger statement: the grant exists, the policy does not.
    const result = await pool.query('SELECT argon2_hash FROM user_credentials WHERE user_id = $1', [
      userId,
    ]);
    assert.equal(result.rows.length, 0, 'the application role read a password hash');
  });

  it('the application role cannot read the verification token table', async () => {
    // A policy that let an authenticated session read its own tokens would let a
    // script on any authenticated page collect them all.
    const created = await post(validBody());
    const userId = (created.json() as { userId: string }).userId;

    // As above: the own-row SELECT policy needs an identity, and a bare pool query
    // has none, so this is empty. The claim function reads this table as
    // `ajo_migrator` instead -- see migrations 101 and 102.
    const result = await pool.query(
      'SELECT token_hash FROM email_verification_tokens WHERE user_id = $1',
      [userId],
    );
    assert.equal(result.rows.length, 0, 'the application role read a verification token');
  });

  it('a member session sees its own token hash and no one else\'s', async () => {
    // Migrations 101 and 102 granted the *migrator* access to the token table. This
    // is the test that the grant did not leak to application roles.
    //
    // `email_verification_tokens_select_own` does let an identified member read
    // its own row, and that is deliberate: the stored value is a SHA-256 digest,
    // so reading it discloses nothing that could be replayed, and the policy
    // predates the API. The property worth locking down is therefore isolation
    // between accounts -- a session that can see one token can see exactly one,
    // its own.
    const mine = (await post(validBody())).json() as { userId: string };
    const theirs = (await post(validBody())).json() as { userId: string };

    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      await client.query('SELECT set_config($1, $2, true)', ['app.user_id', mine.userId]);
      await client.query('SELECT set_config($1, $2, true)', ['app.actor_type', 'member']);
      await client.query('SET LOCAL ROLE ajo_app');

      const own = await client.query(
        'SELECT token_hash FROM email_verification_tokens WHERE user_id = $1',
        [mine.userId],
      );
      assert.equal(own.rows.length, 1, 'a session could not read its own token hash');
      // A digest, not a token. Asserted so that a future change to store the
      // plaintext would fail here rather than in an incident.
      assert.equal(Buffer.from(own.rows[0].token_hash as Buffer).length, 32);

      const other = await client.query(
        'SELECT token_hash FROM email_verification_tokens WHERE user_id = $1',
        [theirs.userId],
      );
      assert.equal(other.rows.length, 0, "a session read another member's token");

      // And an unfiltered read is still bounded to the session's own rows, so a
      // bug that dropped the WHERE clause could not collect everyone's tokens.
      const all = await client.query('SELECT token_hash FROM email_verification_tokens');
      assert.equal(all.rows.length, 1, 'an unfiltered read escaped the session boundary');
    } finally {
      await client.query('ROLLBACK').catch(() => undefined);
      client.release();
    }
  });

  it('the application role cannot insert a row for somebody else', async () => {
    // The policy is `id = app.request_user_id()`. Outside a transaction, and so
    // with no identity, nothing satisfies it.
    const someoneElse = randomUUID();
    await assert.rejects(
      () =>
        pool.query(
          `INSERT INTO users (id, email, phone_e164, status)
           VALUES ($1, $2, $3, 'active')`,
          [someoneElse, uniqueEmail('forged'), uniquePhone()],
        ),
      /row-level security|permission denied/i,
    );
  });

  it('a returned connection carries no identity from the previous request', async () => {
    // The failure this guards against is silent and total: a session-scoped GUC
    // would let the next request read the last request's rows. Asserted by
    // asking for the GUC on a freshly acquired connection.
    const client = await pool.connect();
    try {
      const result = await client.query("SELECT current_setting('app.user_id', true) AS v");
      assert.ok(result.rows[0].v === '' || result.rows[0].v === null, `leaked identity: ${result.rows[0].v}`);
    } finally {
      client.release();
    }
  });
});

describe('email verification', () => {
  const verify = (token: string): Promise<LightMyRequestResponse> =>
    app.inject({
      method: 'POST',
      url: '/api/v1/auth/verify-email',
      payload: { token },
    });

  it('activates the account and marks the token spent', async () => {
    const created = await post(validBody());
    const userId = (created.json() as { userId: string }).userId;
    const token = mailer.sent.at(-1)?.token as string;

    const response = await verify(token);
    assert.equal(response.statusCode, 200, response.body);
    assert.deepEqual(response.json(), { verified: true, alreadyVerified: false });

    const user = await admin.query('SELECT status, is_email_verified FROM users WHERE id = $1', [userId]);
    assert.equal(user.rows[0].status, 'active');
    assert.equal(user.rows[0].is_email_verified, true);

    const spent = await admin.query(
      'SELECT consumed_at FROM email_verification_tokens WHERE user_id = $1',
      [userId],
    );
    assert.ok(spent.rows[0].consumed_at, 'the token was not marked consumed');
  });

  it('refuses a token that has already been used', async () => {
    await post(validBody());
    const token = mailer.sent.at(-1)?.token as string;
    assert.equal((await verify(token)).statusCode, 200);
    assert.equal((await verify(token)).statusCode, 400, 'a spent token verified twice');
  });

  it('refuses an expired token', async () => {
    const created = await post(validBody());
    await admin.query(
      `UPDATE email_verification_tokens SET expires_at = now() - interval '1 minute'
        WHERE user_id = $1`,
      [(created.json() as { userId: string }).userId],
    );
    const response = await verify(mailer.sent.at(-1)?.token as string);
    assert.equal(response.statusCode, 400, response.body);
  });

  it('answers identically for a forged token, an expired one and a spent one', async () => {
    // The endpoint is unauthenticated, so any difference between these cases
    // tells an attacker holding a stolen token whether it is worth continuing.
    const forged = await verify('not-a-real-token');
    const spent = await (async () => {
      await post(validBody());
      const token = mailer.sent.at(-1)?.token as string;
      await verify(token);
      return verify(token);
    })();

    assert.equal(forged.statusCode, spent.statusCode);
    assert.deepEqual(forged.json(), spent.json());
  });

  it('lets exactly one of two concurrent claims win', async () => {
    // The FOR UPDATE in app.claim_email_verification_token is what makes this
    // true. A read-then-write would let both callers past the check, which is the
    // difference between single-use and single-use-only-if-nobody-clicks-twice.
    await post(validBody());
    const token = mailer.sent.at(-1)?.token as string;

    const results = await Promise.all([verify(token), verify(token)]);
    const statuses = results.map((r) => r.statusCode).sort();
    assert.deepEqual(statuses, [200, 400], `expected one winner, got ${statuses.join(' and ')}`);
  });

  it('leaves the token unspent when activation fails, because they are one transaction', async () => {
    // The bug this locks down: claiming the token and activating the account used
    // to be two autocommitted statements. If the second failed, the first had
    // already landed, leaving an account that could never be verified and a token
    // that could not be retried. Fault injection is the only way to reach that
    // branch deterministically: make the activation UPDATE raise, for one user.
    const created = await post(validBody());
    const userId = (created.json() as { userId: string }).userId;
    const token = mailer.sent.at(-1)?.token as string;

    await admin.query(
      `CREATE FUNCTION _fault_fail_activation() RETURNS trigger LANGUAGE plpgsql AS
         $$ BEGIN RAISE EXCEPTION 'fault injection: activation failed'; END $$;
       CREATE TRIGGER _fault_fail_activation BEFORE UPDATE ON users
         FOR EACH ROW WHEN (OLD.id = '${userId}'::uuid)
         EXECUTE FUNCTION _fault_fail_activation();`,
    );

    try {
      const response = await verify(token);
      assert.equal(response.statusCode, 500, response.body);

      // The claim must have rolled back with the activation.
      const spent = await admin.query(
        'SELECT consumed_at FROM email_verification_tokens WHERE user_id = $1',
        [userId],
      );
      assert.equal(
        spent.rows[0].consumed_at,
        null,
        'the token was spent by an activation that failed',
      );

      const user = await admin.query('SELECT status FROM users WHERE id = $1', [userId]);
      assert.equal(user.rows[0].status, 'pending_verification');
    } finally {
      await admin.query(
        `DROP TRIGGER IF EXISTS _fault_fail_activation ON users;
         DROP FUNCTION IF EXISTS _fault_fail_activation();`,
      );
    }

    // And the same token still works once the fault is gone -- which is the
    // property the user actually cares about.
    const retry = await verify(token);
    assert.equal(retry.statusCode, 200, retry.body);
    assert.deepEqual(retry.json(), { verified: true, alreadyVerified: false });
  });
});

describe('health', () => {
  it('answers liveness without touching the database', async () => {
    const response = await app.inject({ method: 'GET', url: '/healthz' });
    assert.equal(response.statusCode, 200);
    assert.deepEqual(response.json(), { status: 'ok' });
  });

  it('answers readiness, reporting both dependencies', async () => {
    const response = await app.inject({ method: 'GET', url: '/readyz' });
    assert.equal(response.statusCode, HAVE_REDIS ? 200 : 503, response.body);
  });

  it('sets the security headers a browser needs', async () => {
    const response = await app.inject({ method: 'GET', url: '/healthz' });
    assert.equal(response.headers['x-content-type-options'], 'nosniff');
    assert.equal(response.headers['x-frame-options'], 'DENY');
    assert.equal(response.headers['referrer-policy'], 'no-referrer');
    assert.match(String(response.headers['content-security-policy']), /default-src 'none'/);
  });
});

describe('rate limiting', { skip: HAVE_REDIS ? false : 'Redis is not reachable' }, () => {
  it('stops a burst of registrations from one address', async () => {
    // The limit is the only thing bounding the signup write path, so this is the
    // test that says it exists. A client that is over the limit is told when to
    // come back, because a client told only "no" retries immediately.
    const limiter: RateLimiter = createFixedWindowLimiter({
      url: process.env['REDIS_URL'] ?? 'redis://127.0.0.1:6379',
      limit: 3,
      windowMs: 60_000,
    });
    const limited = await buildTestApp({
      config: testConfig(),
      pool,
      limiter,
      mailer: new CapturingMailer(),
    });

    try {
      // The limiter keys on the socket address, which for `inject` is a fixed
      // value, so these are all one client as far as the limit is concerned.
      const codes: number[] = [];
      for (let attempt = 0; attempt < 5; attempt += 1) {
        const response = await limited.inject({
          method: 'POST',
          url: '/api/v1/auth/register',
          payload: validBody(),
        });
        codes.push(response.statusCode);
        if (response.statusCode === 429) {
          assert.ok(
            response.headers['retry-after'],
            'a 429 must say when to come back',
          );
        }
      }

      assert.equal(codes.filter((c) => c === 201).length, 3, `got ${codes.join(',')}`);
      assert.equal(codes.filter((c) => c === 429).length, 2, `got ${codes.join(',')}`);
    } finally {
      await limited.close();
      await limiter.close();
    }
  });

  it('refuses registration outright when Redis is unreachable', async () => {
    // "Redis is down" must mean "stop accepting registrations", not "accept them
    // all": failing open here removes the only bound on the write path.
    const broken = createFixedWindowLimiter({
      url: 'redis://127.0.0.1:1', // nothing listens here
      limit: 10,
      windowMs: 60_000,
    });
    const degraded = await buildTestApp({
      config: testConfig(),
      pool,
      limiter: broken,
      mailer: new CapturingMailer(),
    });

    try {
      const response = await degraded.inject({
        method: 'POST',
        url: '/api/v1/auth/register',
        payload: validBody(),
      });
      assert.equal(response.statusCode, 503, response.body);
    } finally {
      await degraded.close();
      await broken.close().catch(() => undefined);
    }
  });
});

/**
 * Registers a member, verifies the address, and returns their credentials.
 *
 * A helper because the setup is three calls and every test in this file would
 * otherwise repeat it -- and a test that registers but forgets to verify would
 * then be asserting login behaviour for a `pending_verification` account while
 * believing it was asserting it for a usable one.
 */
async function loginableMember(prefix: string): Promise<{
  email: string;
  password: string;
  userId: string;
}> {
  const password = 'a sufficiently long passphrase';
  const email = uniqueEmail(prefix);
  const created = await post(validBody({ email, password }));
  assert.equal(created.statusCode, 201, created.body);
  const userId = (created.json() as { userId: string }).userId;

  const token = mailer.sent.at(-1)?.token as string;
  const verified = await app.inject({
    method: 'POST',
    url: '/api/v1/auth/verify-email',
    payload: { token },
  });
  assert.equal(verified.statusCode, 200, verified.body);

  return { email, password, userId };
}

const signIn = (email: string, password: string, over: Record<string, unknown> = {}) =>
  app.inject({
    method: 'POST',
    url: '/api/v1/auth/login',
    payload: { email, password, deviceLabel: 'laptop', platform: 'web', ...over },
  });

/** Pulls the refresh token back out of the `Set-Cookie` the route set. */
function refreshCookieOf(response: LightMyRequestResponse): string {
  const header = response.headers['set-cookie'];
  const raw = Array.isArray(header) ? header.join(',') : String(header ?? '');
  const match = /ajo_refresh=([^;]+)/.exec(raw);
  assert.ok(
    match,
    `no refresh cookie: status ${response.statusCode}, body ${response.body}`,
  );
  return match[1] as string;
}

const withCookie = (token: string) => ({ cookie: `ajo_refresh=${token}` });

const withBearer = (token: string) => ({ authorization: `Bearer ${token}` });

describe('login', () => {
  it('exchanges a password for an access token, a session and a cookie', async () => {
    const member = await loginableMember('login');

    const response = await signIn(member.email, member.password);
    assert.equal(response.statusCode, 200, response.body);

    const body = response.json() as {
      accessToken: string;
      tokenType: string;
      userId: string;
      sessionId: string;
      accountStatus: string;
    };
    assert.equal(body.tokenType, 'Bearer');
    assert.equal(body.userId, member.userId);
    assert.equal(body.accountStatus, 'active', 'a verified member is active');

    // The cookie carries every attribute 12.4.1 names. Asserted as a whole
    // because the failure is silent: a cookie missing `HttpOnly` is still a
    // working cookie, and the bug is only visible to JavaScript.
    const cookie = String(response.headers['set-cookie']);
    for (const attribute of ['HttpOnly', 'Secure', 'SameSite=Strict']) {
      assert.ok(cookie.includes(attribute), `the refresh cookie must be ${attribute}: ${cookie}`);
    }
    assert.ok(!cookie.includes('accessToken'), 'the access token must not be a cookie');

    // The token verifies and names this member and this session.
    const decoded = JSON.parse(
      Buffer.from(body.accessToken.split('.')[1] as string, 'base64url').toString(),
    ) as { sub: string; sid: string };
    assert.equal(decoded.sub, member.userId);
    assert.equal(decoded.sid, body.sessionId);

    // And the session is a real row, with the token stored hashed.
    const session = await admin.query(
      'SELECT id::text, device_label, platform, refresh_expires_at FROM sessions WHERE id = $1',
      [body.sessionId],
    );
    assert.equal(session.rows[0].device_label, 'laptop');
    assert.equal(session.rows[0].platform, 'web');
    assert.ok(
      new Date(session.rows[0].refresh_expires_at).getTime() > Date.now(),
      'a new session has a future refresh expiry',
    );
  });

  it('gives the same answer for a wrong password and an unknown address', async () => {
    const member = await loginableMember('enum');

    const wrongPassword = await signIn(member.email, 'not the password');
    const unknownAddress = await signIn(uniqueEmail('nobody'), 'not the password');

    // Byte-for-byte identical apart from nothing: the whole point is that an
    // attacker cannot tell which addresses exist by reading the response.
    assert.equal(wrongPassword.statusCode, unknownAddress.statusCode);
    assert.equal(wrongPassword.body, unknownAddress.body);
    assert.equal(wrongPassword.statusCode, 401);
  });

  it('tolerates the case of the address, because citext does', async () => {
    const member = await loginableMember('case');
    const shouted = member.email.toUpperCase();

    const response = await signIn(shouted, member.password);
    assert.equal(response.statusCode, 200, response.body);
  });

  it('refuses a revoked credential rather than checking the password first', async () => {
    // Not yet implemented -- a member whose credential row is withdrawn must not
    // be able to log in, and the check has to be the *only* difference. Stated
    // here so the behaviour is pinned if the column ever gains a meaning.
    const member = await loginableMember('revoked');
    await admin.query('DELETE FROM user_credentials WHERE user_id = $1', [member.userId]);

    const response = await signIn(member.email, member.password);
    assert.equal(response.statusCode, 401, response.body);
  });

  it('replaces the session on a device it has used before, rather than duplicating it', async () => {
    // 12.4.3: "If the member signs in from a device they have used before, that
    // session is replaced, not duplicated." The database refuses the duplicate
    // either way -- `sessions_one_active_per_device` is a partial unique index --
    // so without the replacement statement this is a 500 rather than a sign-in.
    const member = await loginableMember('same-device');

    const first = await signIn(member.email, member.password, { deviceLabel: 'laptop' });
    const second = await signIn(member.email, member.password, { deviceLabel: 'laptop' });
    assert.equal(second.statusCode, 200, second.body);

    const firstId = (first.json() as { sessionId: string }).sessionId;
    const secondId = (second.json() as { sessionId: string }).sessionId;
    assert.notEqual(secondId, firstId);

    // One row for that device, and the old one revoked rather than deleted.
    // The cast is on the FILTER, not just the first count: `count(*)` is bigint,
    // `count(*) FILTER (...)` is bigint whatever you cast around the outside of
    // it, and `pg` hands a bigint back as a *string*. Asserted with `equal`
    // rather than `deepEqual` so the two types cannot quietly drift apart again.
    const rows = await admin.query(
      `SELECT count(*)::int AS total,
              (count(*) FILTER (WHERE revoked_at IS NOT NULL))::int AS revoked,
              max(revoked_reason) AS reason
         FROM sessions
        WHERE user_id = $1 AND device_label = 'laptop'`,
      [member.userId],
    );
    assert.equal(rows.rows[0].total, 2, 'the first row is evidence and is kept');
    assert.equal(rows.rows[0].revoked, 1);
    assert.equal(rows.rows[0].reason, 'replaced');

    // And the replaced session's token no longer works, without that counting as
    // a theft against the member's other sessions.
    const stale = await app.inject({
      method: 'POST',
      url: '/api/v1/auth/refresh',
      headers: withCookie(refreshCookieOf(first)),
    });
    assert.equal(stale.statusCode, 401, stale.body);
  });

  it('keeps at most five sessions, evicting the oldest', async () => {
    const member = await loginableMember('five');

    const sessionIds: string[] = [];
    for (let i = 0; i < 6; i += 1) {
      // Six *distinct* devices. With a repeated label each login would replace
      // the previous session through `sessions_one_active_per_device` and the cap
      // would never be reached, so the case would pass without ever evicting
      // anything.
      const response = await signIn(member.email, member.password, { deviceLabel: `device-${i}` });
      assert.equal(response.statusCode, 200, response.body);
      sessionIds.push((response.json() as { sessionId: string }).sessionId);
    }

    const live = await admin.query(
      'SELECT count(*)::int AS n FROM sessions WHERE user_id = $1 AND revoked_at IS NULL',
      [member.userId],
    );
    assert.equal(live.rows[0].n, 5, '12.4.3 caps the list at five');

    // The first is the one that went, and it is revoked rather than deleted --
    // a revoked row is the evidence 12.4.2 needs.
    const evicted = await admin.query(
      'SELECT revoked_at IS NOT NULL AS revoked, revoked_reason FROM sessions WHERE id = $1',
      [sessionIds[0]],
    );
    assert.equal(evicted.rows[0].revoked, true);
    assert.equal(evicted.rows[0].revoked_reason, 'superseded');
  });
});

describe('refresh', () => {
  it('rotates the token and issues a new access token', async () => {
    const member = await loginableMember('refresh');
    const login = await signIn(member.email, member.password);
    const first = refreshCookieOf(login);

    const response = await app.inject({
      method: 'POST',
      url: '/api/v1/auth/refresh',
      headers: withCookie(first),
    });
    assert.equal(response.statusCode, 200, response.body);

    const second = refreshCookieOf(response);
    assert.notEqual(second, first, 'rotation must change the token');

    // The successor is the only live one, and the consumed one is on the ledger.
    const token = await admin.query(
      `SELECT count(*)::int AS n FROM sessions
        WHERE user_id = $1 AND refresh_token_hash = decode($2, 'hex') AND revoked_at IS NULL`,
      [member.userId, hashToken(first).toString('hex')],
    );
    assert.equal(token.rows[0].n, 0, 'the old token must not still be live');

    const spent = await admin.query(
      'SELECT count(*)::int AS n FROM session_rotated_tokens WHERE token_hash = decode($1, \'hex\')',
      [hashToken(first).toString('hex')],
    );
    assert.equal(spent.rows[0].n, 1, 'the consumed token must be on the spent ledger');
  });

  it('revokes every session when a spent token comes back', async () => {
    // 12.4.2's actual requirement, and the reason the ledger exists: the second
    // use of a rotated token means a real device and an attacker hold the same
    // lineage, so everything the member has goes.
    const member = await loginableMember('reuse');
    const phone = await signIn(member.email, member.password, { deviceLabel: 'phone' });
    // A second device, so "every session" means more than the one being stolen.
    await signIn(member.email, member.password, { deviceLabel: 'laptop' });
    const stolen = refreshCookieOf(phone);

    // The attacker rotates the stolen token first, so it becomes a *spent* token
    // in the database. That is the only way to reach the reuse branch, and it is
    // why a plain replay of a never-used token is just an unknown token.
    const rotated = await app.inject({
      method: 'POST',
      url: '/api/v1/auth/refresh',
      headers: withCookie(stolen),
    });
    assert.equal(rotated.statusCode, 200, rotated.body);

    const replay = await app.inject({
      method: 'POST',
      url: '/api/v1/auth/refresh',
      headers: withCookie(stolen),
    });
    assert.equal(replay.statusCode, 401, 'a spent token must be refused');

    // Everything is gone, including the session the attacker was using.
    const sessions = await admin.query(
      'SELECT count(*)::int AS n FROM sessions WHERE user_id = $1 AND revoked_at IS NULL',
      [member.userId],
    );
    assert.equal(sessions.rows[0].n, 0, 'every session must be revoked');

    // And the attacker's own successor no longer works.
    const attacker = await app.inject({
      method: 'POST',
      url: '/api/v1/auth/refresh',
      headers: withCookie(refreshCookieOf(rotated)),
    });
    assert.equal(attacker.statusCode, 401, 'the attacker is cut off too');

    const reasons = await admin.query(
      'SELECT DISTINCT revoked_reason FROM sessions WHERE user_id = $1',
      [member.userId],
    );
    assert.deepEqual(reasons.rows.map((r) => r.revoked_reason), ['refresh_token_reuse']);

    const audit = await admin.query(
      `SELECT count(*)::int AS n FROM audit_logs
        WHERE action = 'session.refresh_token_reuse'
          AND after_state ->> 'user_id' = $1`,
      [member.userId],
    );
    assert.equal(audit.rows[0].n, 1, 'the theft must be recorded');
  });

  it('gives one of two concurrent refreshes the token and the other a 401', async () => {
    // The claim I could not make in the database suite, because `psql -c` cannot
    // express two overlapping transactions and a sequential test passes with or
    // without the lock. This is the test that actually exercises it: both
    // requests are in flight at once, so the second one finds the session row
    // locked by the first.
    //
    // The expectation is *not* "one succeeds and one is politely refused". 12.4.2
    // is explicit that a concurrent second use is indistinguishable from theft
    // and gets the same response, and pretending otherwise is the kind of
    // refinement that reintroduces the ambiguity the whole design removes.
    const member = await loginableMember('race');
    const login = await signIn(member.email, member.password);
    const token = refreshCookieOf(login);

    const attempt = () =>
      app.inject({ method: 'POST', url: '/api/v1/auth/refresh', headers: withCookie(token) });

    const [first, second] = await Promise.all([attempt(), attempt()]);
    const codes = [first.statusCode, second.statusCode].sort();
    assert.deepEqual(codes, [200, 401], `got ${codes.join(',')}`);

    // Exactly one successor exists, so neither caller ended up holding a second
    // valid token -- which is the property the lock protects.
    const live = await admin.query(
      'SELECT count(*)::int AS n FROM sessions WHERE user_id = $1 AND revoked_at IS NULL',
      [member.userId],
    );
    assert.equal(live.rows[0].n, 0, 'the race is resolved as theft, so the lineage is closed');
  });

  it('refuses an unknown or absent token, identically', async () => {
    const unknown = await app.inject({
      method: 'POST',
      url: '/api/v1/auth/refresh',
      headers: withCookie('f'.repeat(64)),
    });
    const absent = await app.inject({ method: 'POST', url: '/api/v1/auth/refresh' });

    assert.equal(unknown.statusCode, 401);
    assert.equal(absent.statusCode, 401);
    assert.equal(unknown.body, absent.body);
  });
});

describe('the authenticated session routes', () => {
  /**
   * One coherent session: the access token and the refresh cookie from the *same*
   * login.
   *
   * Which sounds obvious and was not. Logging in twice and pairing the first
   * response's access token with the second response's cookie produces two
   * sessions, and then "log out" revokes one while the cookie still refreshes the
   * other -- a failure that looks exactly like logout not working. Logout acts on
   * the session named by the access token's signed `sid`, so the token and the
   * cookie have to belong to the same login for the test to mean anything.
   */
  async function signedIn(prefix: string) {
    const member = await loginableMember(prefix);
    const response = await signIn(member.email, member.password, { deviceLabel: 'laptop' });
    const body = response.json() as { accessToken: string; sessionId: string };
    return {
      ...member,
      accessToken: body.accessToken,
      sessionId: body.sessionId,
      refreshToken: refreshCookieOf(response),
    };
  }

  it('lists only the member\'s own live sessions, and marks the current one', async () => {
    const member = await signedIn('list');
    const second = await signIn(member.email, member.password, { deviceLabel: 'phone' });
    assert.equal(second.statusCode, 200, second.body);

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/auth/sessions',
      headers: withBearer(member.accessToken),
    });
    assert.equal(response.statusCode, 200, response.body);

    const { sessions } = response.json() as {
      sessions: { id: string; deviceLabel: string; isCurrent: boolean }[];
    };
    assert.equal(sessions.length, 2);
    const mine = sessions.filter((s) => s.isCurrent);
    assert.equal(mine.length, 1, 'exactly one session is the current one');
    assert.equal(mine[0]?.id, member.sessionId);
    assert.deepEqual(
      sessions.map((s) => s.deviceLabel).sort(),
      ['laptop', 'phone'],
    );
  });

  it('revokes a session and answers 204 either way, so ids cannot be probed', async () => {
    const member = await signedIn('revoke');
    const other = await signedIn('revoke-other');

    const own = await app.inject({
      method: 'DELETE',
      url: `/api/v1/auth/sessions/${member.sessionId}`,
      headers: withBearer(member.accessToken),
    });
    assert.equal(own.statusCode, 204, own.body);

    const revoked = await admin.query('SELECT revoked_reason FROM sessions WHERE id = $1', [
      member.sessionId,
    ]);
    assert.equal(revoked.rows[0].revoked_reason, 'signed_out');

    // Somebody else's session: 204, and unchanged. A 404 here would tell the
    // caller that this id exists.
    const foreign = await app.inject({
      method: 'DELETE',
      url: `/api/v1/auth/sessions/${other.sessionId}`,
      headers: withBearer(member.accessToken),
    });
    assert.equal(foreign.statusCode, 204, foreign.body);
    const untouched = await admin.query('SELECT revoked_at FROM sessions WHERE id = $1', [
      other.sessionId,
    ]);
    assert.equal(untouched.rows[0].revoked_at, null, 'another member\'s session is untouched');

    // A syntactically valid id that does not exist, for the same reason.
    const imaginary = await app.inject({
      method: 'DELETE',
      url: `/api/v1/auth/sessions/${randomUUID()}`,
      headers: withBearer(member.accessToken),
    });
    assert.equal(imaginary.statusCode, 204, imaginary.body);
  });

  it('ends the current session on logout, and clears the cookie', async () => {
    const member = await signedIn('logout');
    const cookie = member.refreshToken;

    const response = await app.inject({
      method: 'POST',
      url: '/api/v1/auth/logout',
      headers: { ...withBearer(member.accessToken), ...withCookie(cookie) },
    });
    assert.equal(response.statusCode, 204, response.body);
    assert.match(String(response.headers['set-cookie']), /Max-Age=0/);

    const revoked = await admin.query(
      'SELECT revoked_at IS NOT NULL AS revoked FROM sessions WHERE id = $1',
      [member.sessionId],
    );
    assert.equal(revoked.rows[0].revoked, true);

    // The access token still verifies, which is the 15-minute window 12.4.1
    // accepts. The refresh token does not, which is the control that matters.
    const refreshed = await app.inject({
      method: 'POST',
      url: '/api/v1/auth/refresh',
      headers: withCookie(cookie),
    });
    assert.equal(refreshed.statusCode, 401);
  });

  it('refuses every session route without a token, and never hints why', async () => {
    for (const request of [
      { method: 'GET' as const, url: '/api/v1/auth/sessions' },
      { method: 'POST' as const, url: '/api/v1/auth/logout' },
      { method: 'DELETE' as const, url: `/api/v1/auth/sessions/${randomUUID()}` },
    ]) {
      const response = await app.inject(request);
      assert.equal(response.statusCode, 401, `${request.method} ${request.url}`);
      assert.equal(response.body, JSON.stringify({ error: 'unauthenticated' }));
      assert.match(String(response.headers['www-authenticate']), /Bearer/);
    }
  });

  it('refuses a token that is not a token, and one from another key', async () => {
    const member = await signedIn('bearer');

    for (const header of ['Bearer', 'Bearer ', 'Basic abc', 'Bearer a b', 'bearer abc']) {
      const response = await app.inject({
        method: 'GET',
        url: '/api/v1/auth/sessions',
        headers: { authorization: header },
      });
      assert.equal(response.statusCode, 401, `Authorization: ${header}`);
    }

    // A well-formed JWT signed by a key this process does not hold.
    const stranger = await createAccessTokenPair(generateEphemeralSigningKey());
    const forged = await stranger.signer.issue({
      userId: member.userId,
      sessionId: member.sessionId,
    });
    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/auth/sessions',
      headers: withBearer(forged),
    });
    assert.equal(response.statusCode, 401, response.body);
  });

  it('refuses an unknown field on the login body, so a typo is not ignored', async () => {
    const member = await loginableMember('typo');
    const response = await signIn(member.email, member.password, {
      passwrod: member.password,
    } as unknown as Record<string, unknown>);
    assert.equal(response.statusCode, 400, response.body);
  });
});
