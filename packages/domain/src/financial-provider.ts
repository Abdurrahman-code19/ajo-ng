/**
 * Financial provider abstraction.
 *
 * The single seam between Ajo.ng's business logic and regulated money movement.
 * Everything above this interface (Ajo engine, ledger, scheduling) must never
 * import a provider SDK or know a provider field name. When ProvidusUnity is
 * approved, a new implementation lands here and nothing upstream changes.
 *
 * Two properties matter more than anything else in this file:
 *
 *  1. Every mutating call takes an idempotency key. A retry after a timeout is
 *     normal and must not move money twice.
 *  2. Provider status is never treated as truth. Webhooks are untrusted input
 *     until signature-verified, and the ledger is the source of truth for what
 *     Ajo.ng believes. Disagreement is reconciled, not overwritten.
 */

import type { Kobo } from './money.js';

export type ProviderId = 'mock' | 'providus_unity';

export interface CreateCollectionAccountCommand {
  /** Stable, derived from the member + provider account, never random. */
  readonly idempotencyKey: string;
  readonly memberId: string;
  readonly reference: string;
  readonly bvn?: string;
  readonly phoneNumber?: string;
}

export interface CollectionAccount {
  readonly providerAccountId: string;
  readonly memberId: string;
  readonly accountNumber: string;
  readonly bankName: string;
  readonly status: 'ACTIVE' | 'PENDING_VERIFICATION' | 'FROZEN' | 'CLOSED';
}

export interface InitiateCollectionCommand {
  readonly idempotencyKey: string;
  readonly accountNumber: string;
  readonly amount: Kobo;
  readonly reference: string;
  readonly callbackUrl: string;
}

export type TransferState =
  | 'PENDING'
  | 'SUCCESS'
  | 'FAILED'
  | 'REVERSED'
  | 'UNKNOWN';

export interface Transfer {
  readonly providerReference: string;
  readonly idempotencyKey: string;
  readonly amount: Kobo;
  readonly state: TransferState;
  readonly providerMessage?: string;
  readonly settledAt?: Date;
}

export interface InitiatePayoutCommand {
  readonly idempotencyKey: string;
  readonly destinationAccountNumber: string;
  readonly amount: Kobo;
  readonly reference: string;
  readonly callbackUrl: string;
}

export interface ProviderWebhookEvent {
  /**
   * The provider's own identifier for this delivery.
   *
   * This is the deduplication key, and the only one that can be. A provider
   * redelivers, retries on a timer, and occasionally sends the same logical
   * event twice with different payload bytes; the reference alone cannot tell
   * those apart from two genuinely separate confirmations of one transfer.
   */
  readonly eventId: string;
  /**
   * The provider's own event name, e.g. `transfer.success`.
   *
   * Provider-shaped on purpose. The application matches on it to decide what an
   * event *is*, so a mapping to our vocabulary here would mean every adapter
   * could name things differently; the mapping is one table, one place.
   */
  readonly eventType: string;
  readonly providerReference: string;
  readonly idempotencyKey: string;
  readonly state: TransferState;
  readonly amount: Kobo;
  /** ISO 4217. The settlement compares it against the Ajo's currency. */
  readonly currency: string;
  readonly occurredAt: Date;
  /** Raw payload exactly as received, for signature verification before parsing. */
  readonly rawBody: string;
  readonly signatureHeader: string;
  /**
   * The body, parsed.
   *
   * Kept whole and provider-shaped rather than reduced to what we happen to use,
   * because this is what gets persisted for forensics: the row has to answer
   * "what did the provider actually send" months later, and a subset cannot.
   */
  readonly parsedPayload: Readonly<Record<string, unknown>>;
}

export class WebhookSignatureError extends Error {
  override readonly name = 'WebhookSignatureError';
}

export class ProviderError extends Error {
  override readonly name = 'ProviderError';
  constructor(
    message: string,
    readonly code: string,
    readonly retryable: boolean,
  ) {
    super(message);
  }
}

export interface FinancialProvider {
  readonly id: ProviderId;

  createCollectionAccount(
    command: CreateCollectionAccountCommand,
  ): Promise<CollectionAccount>;

  verifyAccount(
    accountNumber: string,
  ): Promise<{ readonly valid: boolean; readonly accountName?: string }>;

  /** Charge a member. Retrying with the same key is safe. */
  initiateCollection(command: InitiateCollectionCommand): Promise<Transfer>;

  /** Pay a member. Retrying with the same key is safe. */
  initiatePayout(command: InitiatePayoutCommand): Promise<Transfer>;

  getTransfer(providerReference: string): Promise<Transfer>;

  /**
   * Verify and parse a webhook.
   *
   * MUST throw WebhookSignatureError on a bad signature. Implementations must
   * verify over `rawBody` before any parsing, and must be constant-time in
   * their comparison.
   *
   * Returns an *enriched* copy, not the input: `eventId`, `eventType`,
   * `currency` and `parsedPayload` are read out of the body, so they are empty
   * on the way in and only trustworthy on the way out. A caller that reads them
   * off the unparsed event is reading whatever the sender put in a field this
   * process has not checked yet.
   */
  parseWebhook(event: ProviderWebhookEvent): Promise<ProviderWebhookEvent>;
}
