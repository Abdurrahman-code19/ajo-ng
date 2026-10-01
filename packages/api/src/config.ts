/**
 * Configuration, read once at startup and validated there.
 *
 * Failing at startup rather than on the first request is the whole point: a
 * missing `DATABASE_URL` discovered while somebody is registering is an outage,
 * and discovered at boot is a log line.
 *
 * There is deliberately no default for the credentials. `createPool`'s role is
 * NOSUPERUSER and holds only `ajo_app`, so a wrong guess is a connection refusal
 * and not a privilege escalation -- but it is still better to say so at boot.
 */
import { generateEphemeralSigningKey } from './access-token.js';
import type { MailRelayConfig } from './mailer.js';

export interface Config {
  readonly host: string;
  readonly port: number;
  readonly logLevel: string;
  /**
   * `NODE_ENV`, defaulted rather than required.
   *
   * It is the one place a decision about "is this production" is made. The
   * mailer gate reads it; nothing else branches on it, so there is exactly one
   * definition of production in the process.
   */
  readonly environment: string;
  readonly database: {
    readonly host: string;
    readonly port: number;
    readonly database: string;
    readonly user: string;
    readonly password: string;
    readonly max: number;
  };
  readonly redis: {
    readonly url: string;
  };
  /**
   * The mail relay, or `undefined` when none is configured.
   *
   * Optional rather than required because development does not use one. It is
   * all-or-nothing: three variables set to two is a misconfiguration, and it is
   * caught here at boot instead of at the first signup.
   */
  readonly mail: MailRelayConfig | undefined;
  readonly registration: {
    /** Attempts allowed per window, per client address. */
    readonly rateLimit: number;
    readonly windowMs: number;
  };
  readonly login: {
    /**
     * Attempts allowed per window, per client address and per account.
     *
     * Two budgets rather than one, because they defend against different things.
     * The per-address limit bounds one host spraying many addresses, which is a
     * credential-stuffing list. The per-account limit bounds a distributed spray
     * at one member, which no single-address limit can see -- 12.8 calls this out
     * as "failed logins from multiple IPs/ASNs".
     */
    readonly rateLimit: number;
    readonly windowMs: number;
    /** 12.4.3: five sessions, oldest evicted. */
    readonly maxSessions: number;
  };
  /**
   * The access-token signing key, and how it was obtained.
   *
   * `source` is not decoration. A key generated at boot is fine for development
   * and catastrophic for production, where it means every restart invalidates
   * every session and -- worse -- every instance generates a *different* one, so
   * a member's token is only accepted by the instance that minted it and a load
   * balancer silently logs people out. The composition root branches on this
   * field rather than on `environment`, so there is one place that knows.
   */
  readonly signingKey: {
    readonly privateKeyPem: string;
    readonly publicKeyPem: string;
    readonly source: 'configured' | 'ephemeral';
  };
}

function required(env: NodeJS.ProcessEnv, name: string): string {
  const value = env[name];
  if (value === undefined || value === '') {
    throw new Error(
      `${name} is not set. The API refuses to start without it rather than ` +
        'falling back to a default, because a default credential is a guess.',
    );
  }
  return value;
}

function integer(value: string, name: string): number {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    throw new Error(`${name} must be a positive integer, got ${JSON.stringify(value)}`);
  }
  return parsed;
}

/**
 * The mail relay, or undefined.
 *
 * Half-configured is the interesting case and the reason this is a function: an
 * operator who set `MAIL_RELAY_URL` and forgot the token would otherwise boot
 * into a sender that authenticates as nobody and fails on the first signup, in
 * production, discovered by a member. Failing at boot says which variable is
 * missing instead.
 */
const MAIL_VARIABLES = ['MAIL_RELAY_URL', 'MAIL_RELAY_TOKEN', 'MAIL_FROM'] as const;

function loadMail(env: NodeJS.ProcessEnv): MailRelayConfig | undefined {
  const set = MAIL_VARIABLES.filter((name) => {
    const value = env[name];
    return value !== undefined && value !== '';
  });

  if (set.length === 0) {
    return undefined;
  }

  if (set.length < MAIL_VARIABLES.length) {
    const missing = MAIL_VARIABLES.filter((name) => !set.includes(name));
    throw new Error(
      `the mail relay is half configured: ${missing.join(' and ')} not set. ` +
        'Set all three of MAIL_RELAY_URL, MAIL_RELAY_TOKEN and MAIL_FROM, or none.',
    );
  }

  return {
    url: env['MAIL_RELAY_URL'] as string,
    token: env['MAIL_RELAY_TOKEN'] as string,
    from: env['MAIL_FROM'] as string,
  };
}

/**
 * The signing key, and the rule about which one is allowed.
 *
 * Three states, all of them decided here so the rest of the process never asks
 * whether the key is trustworthy:
 *
 *   * both set -- `configured`, the only state production accepts;
 *   * neither set -- `ephemeral`, refused outright when `NODE_ENV=production`;
 *   * one set -- a mistake, caught here.
 *
 * The half-configured case is the same argument as the mailer. An operator who
 * set the private key and forgot the public one would otherwise boot, and the
 * failure would surface as "the verifier rejects every token this process just
 * signed", which is a confusing way to learn about a missing variable.
 *
 * The production refusal is the important one, and it is a refusal rather than a
 * warning because an ephemeral key in a multi-instance deployment produces
 * intermittent logouts that no log line explains. See
 * `generateEphemeralSigningKey` for the mechanism; the gate belongs here so that
 * "is this production" is decided in exactly one place.
 */
const SIGNING_VARIABLES = ['ACCESS_TOKEN_PRIVATE_KEY', 'ACCESS_TOKEN_PUBLIC_KEY'] as const;

function loadSigningKey(
  env: NodeJS.ProcessEnv,
  environment: string,
): Config['signingKey'] {
  const set = SIGNING_VARIABLES.filter((name) => {
    const value = env[name];
    return value !== undefined && value !== '';
  });

  if (set.length === 1) {
    const missing = SIGNING_VARIABLES.filter((name) => !set.includes(name));
    throw new Error(
      `the access-token key is half configured: ${missing.join(' and ')} not set. ` +
        'Set both ACCESS_TOKEN_PRIVATE_KEY and ACCESS_TOKEN_PUBLIC_KEY, or neither.',
    );
  }

  if (set.length === 2) {
    return {
      privateKeyPem: env['ACCESS_TOKEN_PRIVATE_KEY'] as string,
      publicKeyPem: env['ACCESS_TOKEN_PUBLIC_KEY'] as string,
      source: 'configured',
    };
  }

  if (environment === 'production') {
    throw new Error(
      'ACCESS_TOKEN_PRIVATE_KEY and ACCESS_TOKEN_PUBLIC_KEY are not set, and ' +
        'NODE_ENV is production. The API refuses to generate its own key here: ' +
        'every instance would sign with a different one and members would be ' +
        'logged out at random. Generate an Ed25519 pair and set both variables.',
    );
  }

  return { ...generateEphemeralSigningKey(), source: 'ephemeral' };
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  const environment = env['NODE_ENV'] ?? 'development';

  return {
    host: env['HOST'] ?? '0.0.0.0',
    port: env['PORT'] === undefined ? 3000 : integer(env['PORT'], 'PORT'),
    logLevel: env['LOG_LEVEL'] ?? 'info',
    environment,
    database: {
      host: env['PGHOST'] ?? '127.0.0.1',
      port: env['PGPORT'] === undefined ? 5432 : integer(env['PGPORT'], 'PGPORT'),
      database: env['PGDATABASE'] ?? 'ajo',
      user: required(env, 'PGUSER'),
      password: required(env, 'PGPASSWORD'),
      max: env['PGPOOL_MAX'] === undefined ? 10 : integer(env['PGPOOL_MAX'], 'PGPOOL_MAX'),
    },
    redis: {
      url: required(env, 'REDIS_URL'),
    },
    mail: loadMail(env),
    registration: {
      rateLimit:
        env['REGISTRATION_RATE_LIMIT'] === undefined
          ? 5
          : integer(env['REGISTRATION_RATE_LIMIT'], 'REGISTRATION_RATE_LIMIT'),
      windowMs:
        env['REGISTRATION_WINDOW_MS'] === undefined
          ? 60 * 60 * 1000
          : integer(env['REGISTRATION_WINDOW_MS'], 'REGISTRATION_WINDOW_MS'),
    },
    login: {
      rateLimit:
        env['LOGIN_RATE_LIMIT'] === undefined ? 10 : integer(env['LOGIN_RATE_LIMIT'], 'LOGIN_RATE_LIMIT'),
      windowMs:
        env['LOGIN_WINDOW_MS'] === undefined
          ? 15 * 60 * 1000
          : integer(env['LOGIN_WINDOW_MS'], 'LOGIN_WINDOW_MS'),
      maxSessions:
        env['MAX_SESSIONS'] === undefined ? 5 : integer(env['MAX_SESSIONS'], 'MAX_SESSIONS'),
    },
    signingKey: loadSigningKey(env, environment),
  };
}
