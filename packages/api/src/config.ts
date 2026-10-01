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

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  return {
    host: env['HOST'] ?? '0.0.0.0',
    port: env['PORT'] === undefined ? 3000 : integer(env['PORT'], 'PORT'),
    logLevel: env['LOG_LEVEL'] ?? 'info',
    environment: env['NODE_ENV'] ?? 'development',
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
  };
}
