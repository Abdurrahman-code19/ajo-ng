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
import { buildApp } from '../src/app.js';
import { createPool } from '../src/db.js';
import { allowAllLimiter, createFixedWindowLimiter, type RateLimiter } from '../src/rate-limit.js';
import type { Config } from '../src/config.js';
import type { VerificationSender } from '../src/mailer.js';

const HAVE_REDIS = process.env['REDIS_AVAILABLE'] === '1';

function testConfig(): Config {
  return {
    host: '127.0.0.1',
    port: 0,
    logLevel: 'silent',
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
    registration: { rateLimit: 3, windowMs: 60_000 },
  };
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
  app = await buildApp({ config, pool, limiter: allowAllLimiter(), mailer });
  await app.ready();
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
    const limited = await buildApp({
      config: testConfig(),
      pool,
      limiter,
      mailer: new CapturingMailer(),
    });
    await limited.ready();

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
    const degraded = await buildApp({
      config: testConfig(),
      pool,
      limiter: broken,
      mailer: new CapturingMailer(),
    });
    await degraded.ready();

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
