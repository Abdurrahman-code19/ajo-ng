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
import { createAccessTokenPair } from './access-token.js';
import { createPool } from './db.js';
import { createNotificationTransport, createVerificationSender } from './mailer.js';
import { runWorker } from './notifications.js';
import { createFixedWindowLimiter } from './rate-limit.js';
import { createProviderRegistry } from './providers.js';
import { runSettlementWorker } from './settlement-worker.js';

async function main(): Promise<void> {
  const config = loadConfig();
  const pool = createPool(config.database);
  const limiter = createFixedWindowLimiter({
    url: config.redis.url,
    limit: config.registration.rateLimit,
    windowMs: config.registration.windowMs,
  });
  // Login's budget is its own. Sharing the registration limiter enforced the
  // registration number against sign-in and reported the login window in
  // `Retry-After`; see `AppDependencies.loginLimiter`.
  const loginLimiter = createFixedWindowLimiter({
    url: config.redis.url,
    limit: config.login.rateLimit,
    windowMs: config.login.windowMs,
    namespace: 'login',
  });
  const webhookLimiter = createFixedWindowLimiter({
    url: config.redis.url,
    limit: config.webhooks.rateLimit,
    windowMs: config.webhooks.windowMs,
    namespace: 'webhook',
  });

  const providers = createProviderRegistry({ secrets: config.webhooks.secrets });

  // Built before the app, and awaited, so a malformed key fails the boot instead
  // of the first login. `jose`'s imports are async, which is the reason this is
  // a promise and not a constructor call.
  const { signer, verifier } = await createAccessTokenPair(config.signingKey);

  const app = await buildApp({
    config,
    pool,
    limiter,
    loginLimiter,
    webhookLimiter,
    resolveProvider: providers.resolve,
    // Returns the HTTP relay in production and refuses to construct at all if one
    // is not configured, so a deploy cannot log verification tokens by accident.
    // See `mailer.ts`.
    mailer: createVerificationSender(config.environment, devLogger, config.mail),
    signer,
    verifier,
  });

  // The security notification worker, started after the app so it can log through
  // the real logger. Started before `listen` rather than after, and that is
  // deliberate in the direction it looks wrong: the alarms are already in the
  // queue from the previous process's login traffic, and a deploy that serves
  // logins before anyone is draining the outbox makes that window longer on every
  // release.
  //
  // The signal is a promise rather than a flag because the worker awaits it
  // between passes. A boolean checked at the top of a loop with a 30-second sleep
  // inside it would ignore SIGTERM for up to 30 seconds, and this process has 10
  // seconds of grace before it is killed -- so the flag version would be shut down
  // by the platform every single time. See `runWorker`.
  let signalWorkerStop: (() => void) | undefined;
  const workerStopped = new Promise<void>((resolve) => {
    signalWorkerStop = resolve;
  });

  void runWorker(
    pool,
    createNotificationTransport(config.environment, app.log, config.mail),
    app.log,
    workerStopped,
  ).catch((error: unknown) => {
    // Without this the worker is a floating promise and a failure -- an
    // unreachable database, say -- stops delivery with nothing in the logs but a
    // generic unhandled rejection. Better a loud line and no delivery than a
    // silently drained queue.
    app.log.error({ err: error }, 'the security notification worker stopped unexpectedly');
  });

  // The settlement worker, for the same reason and with the same failure mode: a
  // queue that is never drained is a queue of payments nobody has been told about.
  void runSettlementWorker(pool, app.log, workerStopped).catch((error: unknown) => {
    app.log.error({ err: error }, 'the settlement worker stopped unexpectedly');
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

    // Then the worker, and before the pool. A worker still mid-pass when the pool
    // closes fails on a released connection, which turns an orderly shutdown into a
    // 'could not deliver' on an alarm the member was owed. The signal is
    // synchronous and the worker's own pass is bounded by the relay's 15s timeout,
    // so this resolves promptly; it is not awaited to completion because the grace
    // period, not this function, is what guarantees the process exits.
    signalWorkerStop?.();

    await Promise.all([limiter.close(), loginLimiter.close(), webhookLimiter.close()]);
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
