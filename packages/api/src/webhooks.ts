/**
 * Receiving a provider webhook.
 *
 * The HTTP half of spec §13.5, and deliberately small: verify, persist, return.
 * Everything that acts on the money is in the database and happens later, so a
 * slow handler cannot cause the provider retries and duplicate deliveries the
 * spec is trying to prevent.
 *
 * The order of operations is the interesting part, and it is the one the
 * specification asks for rather than the one the migrations were written around.
 *
 * §13.5 says to compute the HMAC over the raw body and parse JSON only after.
 * `app.ingest_provider_event` takes a `jsonb`, so it cannot be called first: to
 * hand it a payload the body has already been parsed, and parsing before
 * verification means parsing attacker-controlled input. So the signature is
 * checked first, over the bytes, by the adapter -- which is also the only party
 * that holds the secret.
 *
 * That leaves `app.ingest_provider_event`'s "recorded before it is known to be
 * genuine" design with a narrower job than §13.5's wording suggests, and the
 * narrower one is the useful one: it is the state this process is in between the
 * two calls below. If it dies in between, the row is unverified and unclaimable,
 * and the provider's retry arrives to find it already there.
 */
import type { Pool } from 'pg';
import {
  ProviderError,
  WebhookSignatureError,
  type FinancialProvider,
  type Kobo,
  type ProviderId,
  type TransferState,
} from '@ajo/domain';

/**
 * The event types this system acts on.
 *
 * `ProviderWebhookEvent.eventType` is provider-shaped on purpose, so this table
 * is where a provider's vocabulary becomes ours. It is the only place, which is
 * the point: an adapter that quietly renamed its own event types would make the
 * table below a list of lies.
 *
 * A closed set, and an unrecognised name is ignored rather than guessed at. A
 * new provider event that nobody has decided about must not reach the settlement
 * path on the strength of a name that merely looks right. Adding a provider
 * therefore means adding its names here, and knowing what they are is part of
 * E3-01 -- which is why `mock` is the only contributor so far.
 */
export const SETTLEMENT_EVENT_TYPES: ReadonlySet<string> = new Set([
  'transfer.pending',
  'transfer.success',
  'transfer.failed',
  'transfer.reversed',
]);

/**
 * `TransferState` to the `payment_status` the ledger reasons about.
 *
 * Exhaustive on purpose, and the record is declared over `TransferState` rather
 * than indexed afterwards: a new state in the seam must fail to compile here,
 * rather than arrive at the database as a string nobody has decided what it
 * means. The `undefined` branch below is therefore unreachable while that record
 * is complete, and is present only because a hand-edited record is not a thing
 * the compiler knows about.
 */
const STATE_TO_STATUS: Readonly<Record<TransferState, string>> = {
  PENDING: 'pending',
  SUCCESS: 'success',
  FAILED: 'failed',
  REVERSED: 'reversed',
  UNKNOWN: 'unknown',
};

function stateToStatus(state: TransferState): string {
  const mapped = STATE_TO_STATUS[state];
  if (mapped === undefined) {
    // Unreachable while the record above is complete; present because a
    // hand-edited record is not a thing the compiler knows about.
    throw new ProviderError(
      `no payment status for provider state ${JSON.stringify(state)}`,
      'UNMAPPED_STATE',
      false,
    );
  }
  return mapped;
}

/** The PostgreSQL error code `app.ingest_provider_event` raises for a stale event. */
const REPLAY_WINDOW_VIOLATION = '22023';

export type WebhookOutcome =
  /** Verified, recorded, and queued for a worker to settle. */
  | { readonly kind: 'queued'; readonly eventId: string; readonly isNew: boolean }
  /** A delivery of an event already recorded. Recorded, not reprocessed. */
  | { readonly kind: 'duplicate'; readonly eventId: string; readonly isNew: boolean }
  /** A verified event type this system does not act on. */
  | { readonly kind: 'ignored'; readonly eventId: string; readonly reason: string }
  /** Verified, but outside the replay window. Recorded, never processed. */
  | { readonly kind: 'stale'; readonly eventId: string; readonly reason: string };

export interface ProviderDelivery {
  readonly provider: FinancialProvider;
  /** The bytes as received. Never a re-serialised object. */
  readonly rawBody: string;
  readonly signatureHeader: string;
  readonly receivedAt: Date;
}

/**
 * Take one delivery from a provider and put it in the queue.
 *
 * Throws `WebhookSignatureError` when the signature does not verify, which the
 * route turns into a 401, and `ProviderError` when the body is signed correctly
 * but unreadable. Both are the caller telling us something is wrong with what we
 * sent; neither is an acknowledgement, so neither records an event.
 */
export async function receiveProviderWebhook(
  pool: Pool,
  delivery: ProviderDelivery,
): Promise<WebhookOutcome> {
  const { provider } = delivery;

  // Everything except the bytes and the signature is deliberately blank. The
  // adapter fills these in *after* verifying, and an event object pre-filled by
  // the caller is an event whose deduplication key and amount have not been
  // checked against anything.
  const parsed = await provider.parseWebhook({
    eventId: '',
    eventType: '',
    providerReference: '',
    idempotencyKey: '',
    state: 'UNKNOWN',
    amount: 0 as Kobo,
    currency: '',
    occurredAt: new Date(0),
    rawBody: delivery.rawBody,
    signatureHeader: delivery.signatureHeader,
    parsedPayload: {},
  });

  const actsOnIt = SETTLEMENT_EVENT_TYPES.has(parsed.eventType);

  /*
   * Resolved before the row is written, which is the whole reason it is here.
   *
   * `TransferState` is a compile-time union, so a state we cannot represent can
   * only arrive from a body -- and a signed body is allowed to say anything. If the
   * mapping failed after the row existed, the delivery would leave an unverified
   * row that no worker can claim and nobody can explain: a bad delivery recorded
   * as though it were an outage. Failing here records nothing, which is the honest
   * state for a body we cannot represent.
   */
  const status = actsOnIt ? stateToStatus(parsed.state) : undefined;

  const ingested = await ingest(pool, provider.id, parsed, delivery.receivedAt);
  const rowId = ingested.eventId;

  if (status === undefined) {
    await pool.query(
      `SELECT app.discard_provider_event($1, $2, $3, $4)`,
      [
        rowId,
        // The adapter verified it; asking it which algorithm is not part of the
        // seam, so this is recorded as what the seam guarantees. An adapter that
        // does use something else says so here.
        'HMAC-SHA256',
        `event type ${parsed.eventType} is not acted on`,
        // Recorded because an ignored event nobody can find by reference is not
        // the record the spec is asking for.
        parsed.providerReference,
      ],
    );
    return {
      kind: 'ignored',
      eventId: rowId,
      reason: `event type ${parsed.eventType} is not acted on`,
    };
  }

  await pool.query(
    `SELECT app.mark_provider_event_verified($1, $2, $3, $4, $5, $6::public.payment_status)`,
    [
      rowId,
      'HMAC-SHA256',
      parsed.providerReference,
      parsed.amount,
      parsed.currency,
      status,
    ],
  );

  return ingested.isNew
    ? { kind: 'queued', eventId: rowId, isNew: true }
    : { kind: 'duplicate', eventId: rowId, isNew: false };
}

interface Ingested {
  readonly eventId: string;
  readonly isNew: boolean;
}

async function ingest(
  pool: Pool,
  providerId: ProviderId,
  parsed: { readonly eventId: string; readonly eventType: string; readonly occurredAt: Date; readonly parsedPayload: Readonly<Record<string, unknown>> },
  receivedAt: Date,
): Promise<Ingested> {
  try {
    const result = await pool.query<{ event_id: string; is_new: boolean }>(
      `SELECT (e.event_id::text) AS event_id, e.is_new
         FROM app.ingest_provider_event($1, $2, $3, $4, $5::jsonb, $6) e`,
      [
        providerId,
        parsed.eventId,
        parsed.eventType,
        parsed.occurredAt,
        JSON.stringify(parsed.parsedPayload),
        receivedAt,
      ],
    );
    const row = result.rows[0];
    if (row === undefined) {
      throw new ProviderError(
        'app.ingest_provider_event returned no row',
        'INGEST_RETURNED_NOTHING',
        true,
      );
    }
    return { eventId: row.event_id, isNew: row.is_new };
  } catch (error) {
    if (isReplayWindowViolation(error)) {
      throw new StaleProviderEventError(
        `event ${parsed.eventId} is outside the five-minute replay window`,
      );
    }
    throw error;
  }
}

/**
 * A verified event that arrived too late to be trusted.
 *
 * Its own type rather than a `ProviderError` code, because the route answers it
 * differently from every other failure: this is the one case that is not
 * acknowledged, because §13.5 says to reject it.
 */
export class StaleProviderEventError extends Error {
  override readonly name = 'StaleProviderEventError';
}

function isReplayWindowViolation(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    (error as { code?: unknown }).code === REPLAY_WINDOW_VIOLATION
  );
}

export { ProviderError, WebhookSignatureError };