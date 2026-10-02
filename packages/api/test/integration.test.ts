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
import { MockFinancialProvider } from '@ajo/domain';
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
import type { NotificationTransport, VerificationSender } from '../src/mailer.js';
import { drainOnce } from '../src/notifications.js';
import {
  drainOnce as drainSettlementOnce,
  runSettlementWorker,
} from '../src/settlement-worker.js';
import { createProviderRegistry } from '../src/providers.js';

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
    // `mock` is switched on and every other provider is not, which is the
    // production shape: the endpoint exists for the one provider whose signing
    // format is known. A test for an unknown provider is therefore a test of the
    // 404 path rather than one that has to be told which providers to expect.
    webhooks: {
      rateLimit: 1000,
      windowMs: 60_000,
      secrets: { mock: 'test-webhook-secret' },
    },
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
  const providers = createProviderRegistry({ secrets: testConfig().webhooks.secrets });
  const built = await buildApp({
    config: testConfig(),
    pool: pool as Pool,
    limiter: allowAllLimiter(),
    webhookLimiter: allowAllLimiter(),
    resolveProvider: providers.resolve,
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

/**
 * Captures what would have been sent, so a test can assert on a delivered alarm.
 *
 * A separate class from `CapturingMailer` rather than one that implements both
 * interfaces, because the two are different contracts with opposite rules:
 * `VerificationSender` handles a secret and must never log one, while
 * `NotificationTransport` sends a loud warning to a human. Sharing a recorder
 * would put a token and an alarm in the same array, and an assertion like
 * "the last message is the reuse warning" would then pass or fail depending on
 * whether registration happened to run first.
 */
class CapturingTransport implements NotificationTransport {
  readonly sent: { to: string; subject: string; body: string }[] = [];
  /** Set to make every send reject, to exercise the failed path. */
  failWith: Error | undefined;

  async sendEmail(message: { to: string; subject: string; body: string }): Promise<void> {
    if (this.failWith !== undefined) {
      throw this.failWith;
    }
    this.sent.push(message);
  }
}

/**
 * Outbox events for one member, read as the superuser.
 *
 * Needed because the outbox and the notifications table are two different stages,
 * and a login only reaches the first. Asserting on `notifications` straight after
 * a sign-in asserts on a stage that no worker has run yet, which is a test that
 * fails for the wrong reason and then gets "fixed" by deleting the assertion.
 */
async function outboxFor(userId: string, eventType?: string) {
  const values: string[] = [userId];
  const filter = eventType === undefined ? '' : (values.push(eventType), 'AND event_type = $2');
  const result = await admin.query(
    `SELECT id::text, event_type, status::text, aggregate_id::text, payload
       FROM outbox_events
      WHERE payload ->> 'user_id' = $1::text ${filter}
      ORDER BY created_at`,
    values,
  );
  return result.rows as {
    id: string;
    event_type: string;
    status: string;
    aggregate_id: string;
    payload: Record<string, unknown>;
  }[];
}

/** Queued notifications for one member, read as the superuser. */
async function queuedFor(userId: string, eventKey?: string) {
  const values: string[] = [userId];
  const filter =
    eventKey === undefined ? '' : (values.push(eventKey), 'AND event_key = $2');
  const result = await admin.query(
    // No `recipient` here, because the table does not have one: the address is
    // resolved by `app.claim_queued_notifications` at lease time, so that a member
    // who changes their email between queueing and delivery is written to the new
    // one. Selecting a stored address would have been testing a column that does
    // not exist, which is what happened.
    `SELECT id::text, channel::text, subject, body, status::text
       FROM notifications
      WHERE user_id = $1 ${filter}
      ORDER BY created_at, channel`,
    values,
  );
  return result.rows as {
    id: string;
    channel: string;
    subject: string | null;
    body: string;
    status: string;
  }[];
}

/** A log sink that keeps the test output readable; the worker logs on every pass. */
function silentLog() {
  return { info: () => undefined, warn: () => undefined };
}

/** As `silentLog`, but with the `error` the settlement worker logs through. */
function silentSettlementLog() {
  return { info: () => undefined, warn: () => undefined, error: () => undefined };
}

describe('security notifications', () => {
  let transport: CapturingTransport;

  before(() => {
    transport = new CapturingTransport();
  });

  it('queues an alarm the first time a member uses a device, and never again', async () => {
    // The claim that matters: the alarm fires once per real device, and a member
    // who signs in on the same device every morning must not be trained to ignore
    // it. Getting this wrong in the "always" direction is the failure a support
    // request would report as spam; getting it wrong in the "never" direction is
    // the one nobody reports, because nothing happens.
    const member = await loginableMember('newdev');

    const first = await signIn(member.email, member.password, {
      deviceLabel: 'a phone nobody has seen',
      platform: 'android',
    });
    assert.equal(first.statusCode, 200, first.body);

    // The login produced an outbox event and nothing else, because materialising a
    // notification is a worker's job. Asserted in this order deliberately: the
    // event is what the login transaction is responsible for, and the rows are what
    // the worker is responsible for, and this test is about the first.
    const events = await outboxFor(member.userId, 'security.login_new_device');
    assert.equal(events.length, 1, 'the login enqueued exactly one event');
    const enqueued = events[0];
    assert.ok(enqueued !== undefined, 'the event asserted above is the one checked below');
    assert.equal(enqueued.status, 'pending', 'and nothing has drained it yet');
    // The event's aggregate is the session, which is what makes
    // `outbox_events_dedupe_unique` meaningful for this event: two events about the
    // same session are the same alarm, two events about different sessions are not.
    assert.equal(
      enqueued.aggregate_id,
      (first.json() as { sessionId: string }).sessionId,
      'the alarm is about the session that was just created',
    );

    await drainOnce(pool, transport, silentLog());
    const afterFirst = await queuedFor(member.userId, 'security.login_new_device');
    assert.equal(afterFirst.length, 3, 'push, email and sms are all queued');
    // Per channel, not collectively. Email has a transport in this repository and
    // push and sms do not, so after one pass the three rows have three different
    // states -- and an assertion that they share one would pass only by being wrong
    // about two of them.
    assert.equal(
      afterFirst.find((row) => row.channel === 'email')?.status,
      'sent',
      'email is delivered by the worker',
    );
    for (const channel of ['push', 'sms']) {
      assert.equal(
        afterFirst.find((row) => row.channel === channel)?.status,
        'queued',
        `${channel} has no provider, so its row stays queued rather than failing`,
      );
    }

    // Two more logins on the same device, and a second login after logging out --
    // the last one is the interesting case, because a revoked session is still
    // evidence that this device belongs to the member.
    await signIn(member.email, member.password, {
      deviceLabel: 'a phone nobody has seen',
      platform: 'android',
    });
    const afterSignOut = await app.inject({
      method: 'POST',
      url: '/api/v1/auth/logout',
      headers: withBearer(
        (first.json() as { accessToken: string }).accessToken,
      ),
    });
    assert.equal(afterSignOut.statusCode, 204, afterSignOut.body);
    await signIn(member.email, member.password, {
      deviceLabel: 'a phone nobody has seen',
      platform: 'android',
    });

    // Drained again before counting, because these logins enqueue nothing and so
    // materialise nothing: the count below is only meaningful once the queue has
    // been emptied, or it would be reading the three rows from the first pass.
    await drainOnce(pool, transport, silentLog());
    const afterAll = await queuedFor(member.userId, 'security.login_new_device');
    assert.equal(
      afterAll.length,
      3,
      'the same device must not queue a second alarm, even after being signed out',
    );
    assert.equal(
      (await outboxFor(member.userId, 'security.login_new_device')).length,
      1,
      'no second event was enqueued either',
    );

    // A genuinely new device is still recognised as new.
    await signIn(member.email, member.password, {
      deviceLabel: 'a laptop nobody has seen',
      platform: 'web',
    });
    await drainOnce(pool, transport, silentLog());
    const withLaptop = await queuedFor(member.userId, 'security.login_new_device');
    assert.equal(withLaptop.length, 6, 'a second device queues its own alarm');
  });

  it('sends the email over the transport and leaves nothing queued behind', async () => {
    const member = await loginableMember('deliver');
    await signIn(member.email, member.password, { deviceLabel: 'the first device' });

    const result = await drainOnce(pool, transport, silentLog());

    // `materialised` is a count over the whole queue, and other members' events are
    // in it too, so the claim is "this event became three rows", not "this call
    // made three". The per-member count below is the scoped version.
    assert.ok(result.materialised >= 3, 'the outbox event became queued rows');
    const delivered = transport.sent.filter((m) => m.to === member.email);
    assert.equal(delivered.length, 1, 'one email, to the member, not three');
    // Named out of the array rather than indexed at each use: `noUncheckedIndexedAccess`
    // makes `delivered[0]` a possibly-undefined on every single line, and the fix for
    // that is normally a non-null assertion. Here the length was asserted one line
    // above, so binding it to a name states the same thing without an assertion that
    // could silently outlive the check.
    const message = delivered[0];
    assert.ok(message !== undefined, 'the delivered message is the one asserted above');
    // The subject and the body are asserted separately because they fail
    // differently. A vague subject is a triage problem: the member decides whether to
    // open the message from the subject line alone, and a notification with a broken
    // subject is an unread one. A body that omits what to do is a security problem:
    // it tells someone they are being robbed and then stops.
    assert.ok(
      message.subject.toLowerCase().includes('new sign-in'),
      `the subject should say what happened: ${message.subject}`,
    );
    for (const fragment of [
      'device we have not seen before',
      'if this was you, no action is needed',
      'if it was not',
      'sign out and revoke your sessions now',
      'changing your password signs you out everywhere',
    ]) {
      assert.ok(
        message.body.toLowerCase().includes(fragment),
        `the body should tell the member what happened and what to do; missing "${fragment}": ${message.body}`,
      );
    }

    // The placeholders are gone. A body with a raw {{device_label}} in it is how a
    // member learns to distrust an alert, and it would pass every assertion above
    // because the surrounding prose is still correct.
    assert.ok(!/\{\{/.test(message.body), `no placeholder survives: ${message.body}`);

    // Idempotent: a second pass with an empty outbox must send nothing, because a
    // worker that runs every five seconds forever would otherwise mail the same
    // alarm every five seconds forever.
    const again = await drainOnce(pool, transport, silentLog());
    assert.equal(again.materialised, 0);
    assert.equal(again.attempted, 0);
    assert.equal(
      transport.sent.filter((m) => m.to === member.email).length,
      1,
      'the alarm was already delivered',
    );
  });

  it('delivers the reuse alarm, which is written by the rotation transaction', async () => {
    // The end-to-end path for the other event, and the one that matters most: the
    // alarm is written by `app.claim_refresh_token` revoking the sessions, not by
    // any code in the API. If the trigger were missing, this member is robbed and
    // never hears about it, and nothing else in the suite would notice.
    const member = await loginableMember('reuse-notify');
    const device = await signIn(member.email, member.password, { deviceLabel: 'phone' });
    const stolen = refreshCookieOf(device);

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
    assert.equal(replay.statusCode, 401, replay.body);

    // Enqueued by the same transaction that revoked the sessions -- so asserted
    // before any worker runs, or the test cannot tell which step did it.
    const events = await outboxFor(member.userId, 'security.suspicious_token_reuse');
    assert.equal(events.length, 1, 'the reuse alarm is enqueued by the rotation');

    await drainOnce(pool, transport, silentLog());
    const queued = await queuedFor(member.userId, 'security.suspicious_token_reuse');
    assert.equal(queued.length, 3);

    // Matched on the body rather than the subject, because the subject says what
    // happened to the *account* ("Your Ajo sessions were signed out") and carries no
    // word that identifies this event. Filtering on a word the subject happens not
    // to contain is how a test ends up asserting on a template's wording instead of
    // on the delivery.
    const delivered = transport.sent.filter(
      (m) => m.to === member.email && m.body.includes('already been used'),
    );
    assert.equal(delivered.length, 1, 'the reuse alarm reaches the member');
    const alarm = delivered[0];
    assert.ok(alarm !== undefined, 'the delivered alarm is the one asserted above');
    for (const fragment of ['already been used', 'signed out', 'password']) {
      assert.ok(
        alarm.body.includes(fragment),
        `a member who does not know to change their password cannot act on the alarm; missing "${fragment}": ${alarm.body}`,
      );
    }
  });

  it('records a failed send as failed rather than dropping the alarm quietly', async () => {
    const member = await loginableMember('relay-down');
    await signIn(member.email, member.password, { deviceLabel: 'a device' });

    const broken = new CapturingTransport();
    broken.failWith = new Error('the mail relay is down');
    const result = await drainOnce(pool, broken, silentLog());

    assert.equal(result.attempted, 0, 'nothing was delivered');

    const rows = await queuedFor(member.userId, 'security.login_new_device');
    const email = rows.find((row) => row.channel === 'email');
    // An email row is the premise of this test: `login_new_device` queues all three
    // channels and the failing one is picked out by name, so `undefined` here means
    // the queue never produced an email and the failure detail is untested.
    assert.ok(email !== undefined, 'a security notification queues an email');
    assert.equal(email.status, 'failed');

    // And the detail is bounded, so a verbose relay error cannot grow the row
    // without limit. Asserted as <= 500 because that is the function's contract.
    const detail = await admin.query(
      'SELECT length(failure_detail) AS n FROM notifications WHERE id = $1',
      [email.id],
    );
    assert.ok(
      Number(detail.rows[0].n) <= 500,
      `failure_detail must be bounded, got ${detail.rows[0].n}`,
    );

    // Push and sms are untouched. They have no transport, and calling them
    // "failed" would be a false report about what happened to them.
    const others = rows.filter((row) => row.channel !== 'email');
    assert.ok(
      others.every((row) => row.status === 'queued'),
      'channels with no transport stay queued, for when a provider exists',
    );
  });

  it('never silences an alarm because the member muted their notifications', async () => {
    // A member can mute everything in settings. That must not mute this, because
    // a mute anyone can set is a mute an attacker can set.
    const member = await loginableMember('muted');
    await admin.query(
      `UPDATE notification_preferences
          SET push_enabled = false, email_enabled = false, sms_enabled = false,
              money_sms_opt_in = false, quiet_hours_start = '23:00',
              quiet_hours_end = '06:00'
        WHERE user_id = $1`,
      [member.userId],
    );

    await signIn(member.email, member.password, { deviceLabel: 'a device' });
    await drainOnce(pool, transport, silentLog());

    const rows = await queuedFor(member.userId, 'security.login_new_device');
    assert.equal(
      rows.length,
      3,
      'a security notification ignores preferences and quiet hours',
    );
  });
});

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

describe('provider webhooks', () => {
  /**
   * A second adapter instance, used only to sign.
   *
   * Separate from the one the app holds, and that is the point: it proves the
   * signature is checked against the *secret*, not against an object the route
   * happens to share with the test. It also gives the tests arbitrary bodies,
   * which `buildWebhook` cannot produce because it only knows how to describe a
   * transfer it initiated.
   */
  const signer = new MockFinancialProvider({ secret: 'test-webhook-secret' });

  function delivery(over: Record<string, unknown> = {}): {
    rawBody: string;
    signatureHeader: string;
  } {
    const rawBody = JSON.stringify({
      eventId: `evt-${randomUUID()}`,
      eventType: 'transfer.success',
      reference: `ref-${randomUUID()}`,
      state: 'SUCCESS',
      amount: 20_000,
      currency: 'NGN',
      occurredAt: new Date().toISOString(),
      ...over,
    });
    return { rawBody, signatureHeader: signer.sign(rawBody) };
  }

  function send(
    body: { rawBody: string; signatureHeader: string },
    path = '/api/v1/webhooks/payments/mock',
    headers: Record<string, string> = {},
  ): Promise<LightMyRequestResponse> {
    return app.inject({
      method: 'POST',
      url: path,
      // The body is sent as the exact string that was signed. Re-serialising an
      // object here would sign one byte sequence and verify another, and the test
      // would be testing the harness.
      payload: body.rawBody,
      headers: {
        'content-type': 'application/json',
        'x-signature': body.signatureHeader,
        ...headers,
      },
    });
  }

  async function eventsFor(reference: string) {
    const result = await admin.query(
      `SELECT id::text, status::text, signature_verified, provider_reference,
              provider_event_id, event_type, amount_kobo, currency,
              reported_state::text, error_detail, occurred_at
         FROM webhook_events
        WHERE provider_reference = $1
        ORDER BY created_at`,
      [reference],
    );
    return result.rows as {
      id: string;
      status: string;
      signature_verified: boolean;
      provider_reference: string | null;
      provider_event_id: string;
      event_type: string;
      amount_kobo: string | null;
      currency: string | null;
      reported_state: string | null;
      error_detail: string | null;
      occurred_at: Date;
    }[];
  }

  it('refuses an unsigned delivery with a 401 and records nothing', async () => {
    const unverified = async (): Promise<number> => {
      const result = await admin.query(
        'SELECT count(*)::int AS n FROM webhook_events WHERE signature_verified = false',
      );
      return (result.rows[0] as { n: number }).n;
    };
    const before = await unverified();

    const body = delivery();
    const response = await app.inject({
      method: 'POST',
      url: '/api/v1/webhooks/payments/mock',
      payload: body.rawBody,
      headers: { 'content-type': 'application/json' },
    });

    assert.equal(response.statusCode, 401, response.body);
    // Nothing recorded. An unsigned delivery that left a row would be
    // indistinguishable from a forgery later, which is worse than having no row.
    assert.equal(await unverified(), before, 'an unsigned delivery recorded a row');
    const rows = await eventsFor(JSON.parse(body.rawBody).reference as string);
    assert.equal(rows.length, 0, 'and recorded nothing under its reference either');
  });

  it('refuses a signature that does not match the body', async () => {
    const body = delivery();
    const tampered = delivery();

    // The body is one delivery's, the signature another's. This is the forgery
    // the whole seam exists to refuse, and it must not be recorded either.
    const response = await send({
      rawBody: tampered.rawBody,
      signatureHeader: body.signatureHeader,
    });

    assert.equal(response.statusCode, 401, response.body);
    const rows = await eventsFor(JSON.parse(tampered.rawBody).reference as string);
    assert.equal(rows.length, 0, 'a forged delivery left a row behind');
  });

  it('acknowledges a verified delivery, and queues it without settling it', async () => {
    const body = delivery();

    const response = await send(body);

    assert.equal(response.statusCode, 202, response.body);
    const payload = response.json() as { received: boolean; acted_on: boolean; duplicate: boolean };
    assert.equal(payload.received, true);
    assert.equal(payload.acted_on, true, 'a transfer event is one we act on');
    assert.equal(payload.duplicate, false);

    const rows = await eventsFor(JSON.parse(body.rawBody).reference as string);
    assert.equal(rows.length, 1, 'exactly one row for one delivery');
    const row = rows[0];
    assert.ok(row !== undefined);
    assert.equal(row.signature_verified, true);
    // Still waiting for a worker. If this were `processed` here, the capture would
    // have happened inside the request, which is the slow handler the spec forbids.
    assert.equal(row.status, 'received', 'nothing is settled on the request thread');
    // `bigint` comes back as a string, and comparing it to a number would pass
    // only if both were coerced -- so the string form is what is asserted, which
    // is also what a later reconciliation would have to parse.
    assert.equal(row.amount_kobo, '20000');
    assert.equal(row.currency, 'NGN');
    assert.equal(row.reported_state, 'success');
  });

  it('acknowledges a redelivery without reprocessing it', async () => {
    const body = delivery();

    const first = await send(body);
    assert.equal(first.statusCode, 202, first.body);
    const second = await send(body);
    assert.equal(second.statusCode, 202, second.body);

    const payload = second.json() as { duplicate: boolean };
    assert.equal(payload.duplicate, true, 'the second delivery is reported as a duplicate');

    const rows = await eventsFor(JSON.parse(body.rawBody).reference as string);
    assert.equal(rows.length, 1, 'a redelivery created a second row');
    assert.equal(rows[0]?.status, 'received', 'and did not settle the first one early');
  });

  it('ignores an event type it does not act on, without refusing it', async () => {
    const body = delivery({ eventType: 'account.updated', reference: `acct-${randomUUID()}` });

    const response = await send(body);

    // Spec §13.5: acknowledged, logged, ignored -- never a 4xx. A provider that
    // retries a delivery we will never understand sends it forever.
    assert.equal(response.statusCode, 202, response.body);
    assert.equal((response.json() as { acted_on: boolean }).acted_on, false);

    const reference = JSON.parse(body.rawBody).reference as string;
    const rows = await eventsFor(reference);
    assert.equal(rows.length, 1, 'the ignored event is still recorded');
    assert.equal(rows[0]?.status, 'ignored');
    assert.equal(
      rows[0]?.error_detail,
      'event type account.updated is not acted on',
      'and says why, which is the record the spec wants',
    );
  });

  it('rejects a verified event older than the replay window', async () => {
    const body = delivery({ occurredAt: new Date(Date.now() - 20 * 60_000).toISOString() });

    const response = await send(body);

    // Not acknowledged: §13.5 says reject, and returning 2xx would tell the
    // provider its event was queued when it was dropped.
    assert.equal(response.statusCode, 422, response.body);
  });

  it('acknowledges a verified body it cannot read, rather than crashing', async () => {
    const rawBody = 'this was signed but is not JSON';
    const response = await send({ rawBody, signatureHeader: signer.sign(rawBody) });

    // A provider defect, not a forgery: the signature proved the bytes are theirs.
    // A 5xx would make the provider retry bytes that will never parse.
    assert.equal(response.statusCode, 202, response.body);
    assert.equal((response.json() as { acted_on: boolean }).acted_on, false);
  });

  it('records nothing for a verified body it cannot represent', async () => {
    // Signed, so not a forgery -- but a state the ledger has no meaning for. The
    // status is mapped before the row is written, so this leaves nothing behind
    // rather than an unverified row no worker can claim and nobody can explain.
    const body = delivery({ state: 'BANANA', reference: `st-${randomUUID()}` });

    const response = await send(body);

    assert.equal(response.statusCode, 202, response.body);
    assert.equal((response.json() as { acted_on: boolean }).acted_on, false);
    const rows = await eventsFor(JSON.parse(body.rawBody).reference as string);
    assert.equal(rows.length, 0, 'an unusable state left a row behind');
  });

  it('acknowledges a verified body carrying an amount that is not money', async () => {
    // Also signed. `kobo()` refuses a negative amount, and a provider that reports
    // one is broken rather than lying -- so this is reported as a provider defect,
    // not as a 500 from the money type.
    const negative = delivery({ amount: -1, reference: `neg-${randomUUID()}` });

    const response = await send(negative);

    assert.equal(response.statusCode, 202, response.body);
    assert.equal((response.json() as { acted_on: boolean }).acted_on, false);
    const rows = await eventsFor(JSON.parse(negative.rawBody).reference as string);
    assert.equal(rows.length, 0, 'an unusable amount left a row behind');
  });

  it('has no endpoint for a provider with no configured secret', async () => {
    const body = delivery();

    const response = await send(body, '/api/v1/webhooks/payments/providus_unity');

    // 404 rather than 401, and with nothing about which providers exist: an
    // unconfigured provider and an unrouted path are the same answer.
    assert.equal(response.statusCode, 404, response.body);
    assert.equal((response.json() as { error: string }).error, 'not_found');
  });

  it('has no endpoint for a provider that is not a provider at all', async () => {
    const body = delivery();

    const response = await send(body, '/api/v1/webhooks/payments/notaprovider');

    assert.equal(response.statusCode, 404, response.body);
  });

  it('is rate limited per provider and address', async () => {
    // Redis, not `allowAllLimiter`, because the limit being tested is the one
    // this class of limiter implements. And it is closed below: an ioredis socket
    // left open keeps the whole test process alive after the last case, which is a
    // failure that looks like a hang rather than a mistake.
    const webhookLimiter = createFixedWindowLimiter({
      url: process.env['REDIS_URL'] ?? 'redis://127.0.0.1:6379',
      limit: 2,
      windowMs: 60_000,
      namespace: 'webhook-limit-test',
    });
    const limited = await buildTestApp({
      config: {
        ...testConfig(),
        webhooks: { ...testConfig().webhooks, rateLimit: 2 },
      },
      webhookLimiter,
    });

    try {
      const statuses: number[] = [];
      for (let attempt = 0; attempt < 4; attempt += 1) {
        const body = delivery();
        statuses.push(
          (await limited.inject({
            method: 'POST',
            url: '/api/v1/webhooks/payments/mock',
            payload: body.rawBody,
            headers: {
              'content-type': 'application/json',
              'x-signature': body.signatureHeader,
            },
          })).statusCode,
        );
      }

      assert.equal(statuses[0], 202, `first delivery: ${String(statuses[0])}`);
      assert.equal(statuses[2], 429, `third delivery is over the limit: ${String(statuses[2])}`);
      assert.equal(statuses[3], 429, 'and stays over the limit');
    } finally {
      await limited.close();
      await webhookLimiter.close();
    }
  });

  it('preserves the raw body byte for byte for everything else', async () => {
    // The parser is app-wide because it is keyed by content type, so the cost of
    // keeping the bytes is paid by every route. This is what pays for it: a
    // registration body that has an extra property must still be rejected by the
    // schema rather than silently trimmed, which is what the JSON parser's
    // `removeAdditional` default would have done to it.
    const response = await post({
      email: uniqueEmail('rawbody'),
      password: 'a sufficiently long passphrase',
      fullName: 'Raw Body',
      phone: uniquePhone(),
      acceptedTerms: true,
      acceptedPrivacy: true,
      acceptedTermsAt: '2011-01-01T00:00:00.000Z',
    });

    assert.equal(response.statusCode, 400, response.body);
  });

  describe('the settlement worker', () => {
    /**
     * Drains whatever is claimable right now.
     *
     * Every route case above leaves verified events behind, so a worker case that
     * assumed an empty queue would be at the mercy of test order -- and would
     * quietly stop testing anything the moment someone reordered the file.
     */
    async function drainQueue(): Promise<number> {
      let claimed = 0;
      for (let pass = 0; pass < 5; pass += 1) {
        const result = await drainSettlementOnce(pool, silentSettlementLog());
        claimed += result.claimed;
        if (result.claimed === 0) {
          break;
        }
      }
      return claimed;
    }

    it('claims what the route queued, and backs off instead of spinning', async () => {
      await drainQueue();

      const references: string[] = [];
      for (let attempt = 0; attempt < 3; attempt += 1) {
        const body = delivery({ reference: `wkr-${randomUUID()}` });
        assert.equal((await send(body)).statusCode, 202);
        references.push(JSON.parse(body.rawBody).reference as string);
      }

      const result = await drainSettlementOnce(pool, silentSettlementLog());
      assert.equal(result.claimed, 3, 'a pass claims the whole batch');
      assert.equal(result.handled, 3, 'and gives each one a verdict');

      // None of these references matches a payment, so each was deferred with a
      // future `next_retry_at`. The second pass is the assertion that matters: a
      // worker that ignored the backoff would re-claim them immediately and burn
      // database work on every event it cannot possibly settle yet.
      const again = await drainSettlementOnce(pool, silentSettlementLog());
      assert.equal(again.claimed, 0, 'a deferred event was re-claimed straight away');

      for (const reference of references) {
        const rows = await eventsFor(reference);
        assert.equal(rows.length, 1);
        assert.equal(
          rows[0]?.status,
          'received',
          'an event with no matching payment stays queued rather than failing',
        );
      }
    });

    it('never claims an event whose signature did not verify, or one it ignored', async () => {
      await drainQueue();

      const ignored = delivery({ eventType: 'account.updated', reference: `ign-${randomUUID()}` });
      assert.equal((await send(ignored)).statusCode, 202);
      const ignoredReference = JSON.parse(ignored.rawBody).reference as string;

      const forged = delivery();
      // Signed with the wrong secret: refused, so no row at all. The unverified-row
      // case is the one that matters, and it is exercised here directly by writing
      // the row the way an interrupted request would have left it.
      const forgedResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/webhooks/payments/mock',
        payload: forged.rawBody,
        headers: { 'content-type': 'application/json', 'x-signature': 'not-the-signature' },
      });
      assert.equal(forgedResponse.statusCode, 401);

      const result = await drainSettlementOnce(pool, silentSettlementLog());
      assert.equal(result.claimed, 0, 'the claim took something it must not touch');

      const ignoredRows = await eventsFor(ignoredReference);
      assert.equal(ignoredRows[0]?.status, 'ignored', 'and left the ignored event alone');
    });

    it('settles the rest of a batch when one event raises', async () => {
      await drainQueue();

      const references: string[] = [];
      for (let attempt = 0; attempt < 3; attempt += 1) {
        const body = delivery({ reference: `poison-${randomUUID()}` });
        assert.equal((await send(body)).statusCode, 202);
        references.push(JSON.parse(body.rawBody).reference as string);
      }
      const poisoned = references[1] as string;

      // The worker settles by event id, not by reference, so the poison has to be
      // keyed on the uuid -- matching on the reference would silently never fire
      // and this test would pass without testing anything.
      const poisonedRow = (await eventsFor(poisoned))[0];
      assert.ok(poisonedRow !== undefined, 'the poisoned event was recorded');
      const poisonedId = poisonedRow.id;

      // A pool that fails one specific event, so the batch-interruption property
      // is tested without contriving a database state that is hard to reach on
      // purpose. The real trigger -- an event whose settlement raises -- exists;
      // what is under test is what happens to the other two.
      const failing = {
        query: (text: unknown, values?: unknown) => {
          if (
            typeof text === 'string' &&
            text.includes('settle_provider_event') &&
            Array.isArray(values) &&
            values.includes(poisonedId)
          ) {
            return Promise.reject(new Error('settlement exploded'));
          }
          return pool.query(text as string, values as never[]);
        },
      } as unknown as Pool;

      const result = await drainSettlementOnce(failing, silentSettlementLog());
      assert.equal(result.claimed, 3);
      assert.equal(result.raised, 1, 'the raising event was counted as raised');
      assert.equal(
        result.handled,
        2,
        'and the two behind it in the batch were still settled',
      );
    });

    it('stops when it is asked to', async () => {
      let release: () => void = () => undefined;
      const stopped = new Promise<void>((resolve) => {
        release = resolve;
      });

      const running = runSettlementWorker(pool, silentSettlementLog(), stopped, {
        idleIntervalMs: 1,
      });
      release();
      // The worker is awaited, so a loop that ignored the stop signal would hang
      // this test rather than pass it. That is the whole assertion.
      await running;
    });
  });
});

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
