/**
 * The security notification worker.
 *
 * Migration 104 makes the events durable and makes them queue; this is the part
 * that talks to the outside world. It does three things in a loop, in this order,
 * and the order is the design:
 *
 *   1. `app.drain_security_notifications()` turns outbox events into one row per
 *      channel. Idempotent, and safe to call when there is nothing to do.
 *   2. `app.claim_queued_notifications()` leases rows and returns them with a
 *      resolved recipient. The lease, not a status change -- see the note at the
 *      bottom of the migration for why.
 *   3. Each row is sent, and then marked sent or failed.
 *
 * Why draining and claiming are separate is worth being explicit about, because
 * the obvious refactor is to merge them and it is wrong. Draining is where an
 * event becomes a message; claiming is where a message becomes *this worker's*
 * job. Merged, a slow mail relay would hold the outbox rows locked for the
 * duration of every send, so a queue backlog would stop events being enqueued at
 * all -- and the enqueue is the part that has to be in the session's transaction
 * to be worth anything. The two steps are separate so that the fast,
 * transaction-bound half never waits on the slow, network-bound half.
 *
 * ## At-least-once, and why that is right here
 *
 * `app.claim_queued_notifications` leases by pushing `scheduled_for` forward.
 * There is no 'sending' status in `notification_status`, and adding one to an
 * adopted enum is not this worker's business. So a worker that dies between the
 * lease and the send leaves the row 'queued' with a future `scheduled_for`, and
 * the next pass picks it up once the lease expires.
 *
 * That means a member may receive the same alarm twice. For these two events that
 * is the correct trade and not a compromise: "someone used your refresh token
 * twice, we signed you out" delivered twice frightens someone twice and costs one
 * text message. Delivered zero times it means the member is robbed and never told.
 * The two failures are not equivalent, and a queue that drops rows on crash
 * resolves the less important one.
 *
 * ## Push and SMS are queued, not sent
 *
 * `app.claim_queued_notifications` returns `recipient: NULL` for push, and may
 * return NULL for sms on a member who registered without a phone number. Both
 * rows are counted, logged and left alone rather than marked failed, because
 * "failed" means a provider rejected it and calling a missing provider a failure
 * makes the same row look like a bug in the relay. There is no push provider in
 * this repository and no SMS provider either; TODO.md records both.
 *
 * A row with no recipient is left 'queued' and will be re-leased every pass
 * forever, which is a slow leak in the queue index. The lease interval keeps it
 * cheap -- one row, re-leased every five minutes -- and marking it 'suppressed'
 * would be wrong, because a provider added tomorrow should deliver the backlog
 * that accumulated today.
 *
 * ## What this worker deliberately does not do
 *
 * It does not check notification preferences or quiet hours, and it does not need
 * to. Materialisation happens in `app.drain_security_notifications`, which selects
 * templates by `is_security` alone, so a member who has muted every channel is
 * still queued for all three. Preferences are a way for a member to choose what
 * they hear about; they are not a control on being told that someone else is
 * using their refresh token. Honouring a mute here would let anyone silence a
 * compromise alarm by opening a settings page once, which is the exact outcome
 * these notifications exist to prevent.
 */
import type pg from 'pg';

/** What the API needs to hand over for a notification to actually be sent. */
export interface NotificationTransport {
  sendEmail(message: {
    readonly to: string;
    readonly subject: string;
    readonly body: string;
  }): Promise<void>;
}

export interface NotificationLog {
  info(fields: object, message: string): void;
  warn(fields: object, message: string): void;
}

export interface DrainResult {
  /** Outbox events materialised into queued notifications by this pass. */
  readonly materialised: number;
  /** Rows successfully sent or definitively failed by this pass. */
  readonly attempted: number;
  /** Rows with no transport yet: push, or sms with no phone on file. */
  readonly undeliverable: number;
}

interface ClaimedRow {
  readonly id: string;
  readonly user_id: string;
  readonly event_key: string;
  readonly channel: string;
  readonly subject: string | null;
  readonly body: string;
  readonly recipient: string | null;
}

/**
 * One pass of the worker.
 *
 * Returns counts rather than logging each row, so a caller can build a health
 * signal on "alarms queued but not sent", which is the number that matters: a
 * growing gap means a member is not being told, and the audit trail would look
 * entirely healthy while it happened.
 *
 * Every database call is `pool.query` rather than a held client, and none of them
 * are wrapped in an explicit transaction. Each of the three functions is a single
 * atomic statement inside its own transaction -- which is why each is safe to call
 * alone, and why holding one connection across all three would only add a way for
 * the worker to hold a pool slot while a relay is slow.
 */
export async function drainOnce(
  pool: pg.Pool,
  transport: NotificationTransport,
  log: NotificationLog,
  batchSize = 20,
): Promise<DrainResult> {
  // 1. Outbox -> queued notifications. Call even when empty: it is cheap and it is
  // the call that keeps the enqueue path honest, so a pass that skipped it when
  // idle would need a second code path for "first pass after a deploy".
  const materialised = await countDrain(pool, batchSize);

  // 2. Lease a batch. The limit is generous relative to the default because
  // earlier cases and other members' rows share the queue, and a tight limit here
  // would make throughput depend on how much unrelated work is pending.
  const claimed = await claim(pool, Math.max(batchSize, 100));

  let attempted = 0;
  let undeliverable = 0;

  for (const row of claimed) {
    if (row.channel !== 'email') {
      // Counted and left queued. See the module note: push and sms have no
      // transport in this repository, and marking them failed would be a lie about
      // what happened to them.
      undeliverable += 1;
      continue;
    }

    if (row.recipient === null || row.recipient === '') {
      // `users.email` is NOT NULL, so this should be unreachable. It is handled
      // anyway because the alternative is a crash in the worker loop, and a worker
      // that dies on one malformed row stops delivering *every* alarm behind it.
      undeliverable += 1;
      log.warn(
        { notificationId: row.id, eventKey: row.event_key, userId: row.user_id },
        'skipping an email notification with no recipient; users.email is NOT NULL, so this is a bug',
      );
      continue;
    }

    // `subject` is nullable in the schema because an sms row has no subject, and
    // the email templates all set one. The fallback is a constant rather than an
    // empty string because an email with a blank subject line renders as a very
    // spammy-looking message, and a member deciding whether to trust an alert
    // about their savings group is exactly the person who would read a blank
    // subject as suspicious.
    const subject = row.subject ?? 'A security alert about your Ajo account';

    try {
      await transport.sendEmail({
        to: row.recipient,
        subject,
        body: row.body,
      });
      await markSent(pool, row.id);
      attempted += 1;
    } catch (error) {
      // Marked failed, not retried. A relay that rejects a security email will
      // keep rejecting it, and retrying only buries the events that can be
      // delivered. `failure_detail` carries the message and is bounded to 500
      // characters by the function.
      await markFailed(pool, row.id, describe(error));
      log.warn(
        {
          notificationId: row.id,
          eventKey: row.event_key,
          userId: row.user_id,
          error: describe(error),
        },
        'a security notification could not be delivered',
      );
    }
  }

  if (materialised > 0 || attempted > 0 || undeliverable > 0) {
    log.info(
      { materialised, attempted, undeliverable },
      'security notification pass complete',
    );
  }

  return { materialised, attempted, undeliverable };
}

/**
 * The error message, and nothing else.
 *
 * `error.message` is deliberately the only field taken. The transport's own errors
 * are written to never quote a token, but that is a convention, and a worker that
 * dumps `JSON.stringify(error)` will eventually surface a provider response body
 * containing a recipient address into the logs. The message alone is enough to
 * diagnose a relay timeout or a 4xx.
 */
function describe(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return 'an unknown transport error';
}

/**
 * Drains in a loop until the queue is empty, then reports how many rows it made.
 *
 * A single call takes a batch limit, so a busy outbox needs several passes. It
 * loops because leaving a backlog for the next tick is fine, but leaving it
 * because this pass gave up early is not -- and the difference is invisible from
 * the outside.
 *
 * Bounded by `maxPasses` anyway, because an unbounded loop over a queue that
 * something else keeps refilling is a way to never return. On the last pass the
 * limit is ignored deliberately: the alternative is exiting with rows still
 * pending and no record that they were.
 */
async function countDrain(pool: pg.Pool, batchSize: number): Promise<number> {
  let total = 0;
  for (let pass = 0; pass < 20; pass += 1) {
    const result = await pool.query<{ n: string }>(
      'SELECT count(*)::text AS n FROM app.drain_security_notifications($1);',
      [batchSize],
    );
    const made = Number(result.rows[0]?.n ?? '0');
    total += made;
    if (made === 0) {
      break;
    }
  }
  return total;
}

async function claim(pool: pg.Pool, limit: number): Promise<ClaimedRow[]> {
  const result = await pool.query<ClaimedRow>(
    `SELECT id::text, user_id::text, event_key, channel::text,
            subject, body, recipient
       FROM app.claim_queued_notifications($1);`,
    [limit],
  );
  return result.rows;
}

async function markSent(pool: pg.Pool, id: string): Promise<void> {
  await pool.query('SELECT app.mark_notification_sent($1::uuid);', [id]);
}

async function markFailed(pool: pg.Pool, id: string, detail: string): Promise<void> {
  await pool.query('SELECT app.mark_notification_failed($1::uuid, $2);', [id, detail]);
}

/**
 * The interval between passes.
 *
 * Five seconds when a pass found work, longer when idle. The shape matters more
 * than the numbers: a fixed 5-second tick on an idle system is a query every 5
 * seconds forever across every replica, and the adaptive version is idle-silent.
 * The floor is there so a burst does not spin -- `claim` returns nothing when
 * there is nothing to do, and a loop that immediately retries would be a busy
 * wait against the database.
 */
export interface PollInterval {
  readonly whenBusyMs: number;
  readonly whenIdleMs: number;
}

export const DEFAULT_POLL_INTERVAL: PollInterval = {
  whenBusyMs: 5_000,
  whenIdleMs: 30_000,
};

export function nextDelay(result: DrainResult, interval = DEFAULT_POLL_INTERVAL): number {
  return result.attempted > 0 || result.materialised > 0
    ? interval.whenBusyMs
    : interval.whenIdleMs;
}

/**
 * Runs the worker until `stop` resolves.
 *
 * Written as a loop with an `await` at the top rather than as a recursive timer,
 * because a recursive timer cannot be interrupted mid-sleep -- which means a
 * SIGTERM during a 30-second idle wait would hold the process open for the rest of
 * the interval. Awaiting `stop` between passes means shutdown is observed within
 * one pass, and a pass is bounded by the relay's own 10s timeout.
 */
export async function runWorker(
  pool: pg.Pool,
  transport: NotificationTransport,
  log: NotificationLog,
  stop: Promise<void>,
  interval = DEFAULT_POLL_INTERVAL,
): Promise<void> {
  let stopped = false;
  void stop.then(() => {
    stopped = true;
  });

  while (!stopped) {
    const result = await drainOnce(pool, transport, log);
    await sleep(nextDelay(result, interval));
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}