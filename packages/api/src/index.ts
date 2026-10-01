/**
 * The composition root: the one file that reads the environment, and the one
 * place where a shutdown is ordered correctly.
 *
 * Nothing else in this package touches `process.env` or listens on a port, so
 * every test runs the real application without a real network listener and
 * without mutating global state.
 */
import { buildApp } from './app.js';
import { loadConfig } from './config.js';
import { createPool } from './db.js';
import { createVerificationSender } from './mailer.js';
import { createFixedWindowLimiter } from './rate-limit.js';

async function main(): Promise<void> {
  const config = loadConfig();
  const pool = createPool(config.database);
  const limiter = createFixedWindowLimiter({
    url: config.redis.url,
    limit: config.registration.rateLimit,
    windowMs: config.registration.windowMs,
  });

  const app = await buildApp({
    config,
    pool,
    limiter,
    // Refuses to construct in production until a real transport exists, so a
    // deploy cannot log verification tokens by accident. See `mailer.ts`.
    mailer: createVerificationSender(config.environment, devLogger),
  });

  // Registering the shutdown hooks before `listen` means a process that is
  // interrupted during startup still gets them, which is the window where an
  // aborted deploy otherwise leaves a connection open.
  let closing = false;

  const shutdown = async (signal: string): Promise<void> => {
    if (closing) {
      return;
    }
    closing = true;
    app.log.info({ signal }, 'shutting down');

    // In this order: stop accepting work, then close the things the work used.
    // Closing the pool first would let an in-flight request fail on a released
    // connection, and the 10-second grace period exists so those requests get
    // to finish first.
    await app.close();
    await limiter.close();
    await pool.end();

    // Exit explicitly. `app.close()` resolves once the server has stopped, but
    // ioredis keeps a socket open until it is closed, and a lingering handle is
    // the usual reason a "stopped" container takes the full grace period to die.
    process.exit(0);
  };

  process.on('SIGTERM', () => void shutdown('SIGTERM'));
  process.on('SIGINT', () => void shutdown('SIGINT'));

  await app.listen({ host: config.host, port: config.port });
  app.log.info(
    { host: config.host, port: config.port, databaseRole: config.database.user },
    'listening',
  );
}

/**
 * The development sender's log sink.
 *
 * `buildApp` creates the real logger, so the sender cannot be given one -- it is
 * constructed from what `buildApp` is about to build. console.info is the honest
 * choice: it goes to stdout, where a local developer is already looking, and it
 * keeps the sender's dependence on process state visible instead of hidden behind
 * a logger that does not exist yet. A production composition replaces this with
 * the real transport, and then the token must not be logged at all.
 */
const devLogger = {
  info: (fields: object, message: string): void => {
    console.info(JSON.stringify(fields), message);
  },
};
main().catch((error: unknown) => {
  // A startup failure must be loud and must be a non-zero exit. Fastify's logger
  // is not available yet, so this goes to stderr directly.
  console.error('failed to start:', error);
  process.exit(1);
});
