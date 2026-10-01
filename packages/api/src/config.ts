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
export interface Config {
  readonly host: string;
  readonly port: number;
  readonly logLevel: string;
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

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  return {
    host: env['HOST'] ?? '0.0.0.0',
    port: env['PORT'] === undefined ? 3000 : integer(env['PORT'], 'PORT'),
    logLevel: env['LOG_LEVEL'] ?? 'info',
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
