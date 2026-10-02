/**
 * The settlement worker.
 *
 * Spec §13.5 requires business processing to happen after the acknowledgement, and
 * this is the half that does it. The split exists for one reason: a webhook
 * handler that settles a contribution before replying is a webhook handler whose
 * latency the provider controls, and a provider that retries a slow response
 * sends the same confirmation twice. The route therefore verifies and records,
 * and everything about money happens here.
 *
 * The queue itself is a database table with a lease, not Redis. That is a
 * deliberate trade: the work being done is a ledger posting, which is a
 * transactional write to Postgres, and a queue that can lose a job between Redis
 * and Postgres is a queue that can lose a capture. The lease gives the same
 * multi-process safety -- `FOR UPDATE SKIP LOCKED` means two workers never hold
 * the same event -- with one fewer thing that can be down.
 *
 * The loop shape is borrowed from the notification worker deliberately: a promise
 * for stopping rather than a boolean flag, because a flag checked above a
 * 30-second sleep ignores SIGTERM for up to 30 seconds and this process has 10.
 */
import type { Pool } from 'pg';

/** How long to wait after a pass that found nothing. */
const IDLE_INTERVAL_MS = 2_000;
/** How long to wait after a pass that did something. */
const BUSY_INTERVAL_MS = 0;
/** Events claimed per pass. */
const BATCH_SIZE = 10;
/**
 * Longer than a capture takes, short enough that a worker killed mid-event does
 * not hold the event for long. A capture is a handful of statements in one
 * transaction; five minutes is generous by an order of magnitude, and the cost of
 * being generous is only latency in the case where a worker died.
 */
const LEASE_SECONDS = 300;

export interface SettlementLog {
  info(fields: object, message: string): void;
  error(fields: object, message: string): void;
  warn(fields: object, message: string): void;
}

export interface SettlementWorkerOptions {
  readonly batchSize?: number;
  readonly leaseSeconds?: number;
  readonly idleIntervalMs?: number;
}

export interface PassResult {
  readonly claimed: number;
  /**
   * Events `settle_provider_event` returned a verdict for.
   *
   * Not called "settled" because a verdict is often *not* a capture: a reference
   * matching no payment is a verdict too, and counting those as settled would
   * make a queue that is quietly failing look like one that is working.
   */
  readonly handled: number;
  /** Events whose settlement raised. Bounded by the migration's attempt ceiling. */
  readonly raised: number;
}

/**
 * One pass over the queue.
 *
 * Exported so a test can drive the loop deterministically. Everything that can go
 * wrong in a pass is caught per event, never around the whole batch: an exception
 * that escaped here would stop the worker and strand every later event in the
 * table, which is the failure this file exists to make impossible.
 */
export async function drainOnce(
  pool: Pool,
  log: SettlementLog,
  options: SettlementWorkerOptions = {},
): Promise<PassResult> {
  const batchSize = options.batchSize ?? BATCH_SIZE;
  const leaseSeconds = options.leaseSeconds ?? LEASE_SECONDS;

  const claimed = await pool.query<{ id: string }>(
    'SELECT id::text FROM app.claim_provider_event($1, $2)',
    [batchSize, leaseSeconds],
  );

  let handled = 0;
  let raised = 0;

  for (const event of claimed.rows) {
    try {
      // `settle_provider_event` captures, defers, escalates or fails the event, or
      // raises -- and the migration already bounds what a raise costs: eight
      // attempts, then filed as failed with the reason. So this catch is not about
      // the event, it is about the *other* events in the batch.
      const outcome = await pool.query<{ outcome: string }>(
        'SELECT app.settle_provider_event($1::uuid) AS outcome',
        [event.id],
      );
      const result = outcome.rows[0]?.outcome ?? 'unknown';
      handled += 1;
      log.info({ event: event.id, outcome: result }, 'provider event settled');
    } catch (error) {
      raised += 1;
      log.error({ err: error, event: event.id }, 'provider event settlement raised');
    }
  }

  return { claimed: claimed.rowCount ?? 0, handled, raised };
}

export async function runSettlementWorker(
  pool: Pool,
  log: SettlementLog,
  stop: Promise<void>,
  options: SettlementWorkerOptions = {},
): Promise<void> {
  const idleIntervalMs = options.idleIntervalMs ?? IDLE_INTERVAL_MS;
  let stopped = false;
  void stop.then(() => {
    stopped = true;
  });

  while (!stopped) {
    let result: PassResult;
    try {
      result = await drainOnce(pool, log, options);
    } catch (error) {
      // The database is unreachable, or the claim failed. Retrying immediately in a
      // tight loop would turn one outage into a busy one, so this waits like an
      // idle pass.
      log.error({ err: error }, 'the settlement queue could not be read');
      result = { claimed: 0, handled: 0, raised: 0 };
    }
    await sleep(result.claimed === 0 ? idleIntervalMs : BUSY_INTERVAL_MS);
  }
}

function sleep(ms: number): Promise<void> {
  if (ms <= 0) {
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}