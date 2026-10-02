/**
 * In-memory financial provider for development and tests.
 *
 * IMPORTANT: this is a development tool. It does not move money. It exists so
 * the Ajo engine, ledger and full end-to-end flows can be exercised before
 * ProvidusUnity is approved, and so the failure paths that matter most
 * (duplicate webhooks, out-of-order delivery, timeouts, reversals) can be
 * tested deliberately rather than waited for in production.
 *
 * Two safeguards keep it from being mistaken for a real integration:
 *  - `assertNotProduction` throws if it is ever constructed with production
 *    config.
 *  - Every transfer it creates is tagged MOCK and its reference says so.
 *
 * If you find yourself adding business logic here, it belongs in the Ajo engine.
 */

import { timingSafeEqual, createHmac } from 'node:crypto';
import {
  ProviderError,
  WebhookSignatureError,
  type CollectionAccount,
  type CreateCollectionAccountCommand,
  type FinancialProvider,
  type InitiateCollectionCommand,
  type InitiatePayoutCommand,
  type ProviderId,
  type ProviderWebhookEvent,
  type Transfer,
  type TransferState,
} from './financial-provider.js';
import { format, kobo, type Kobo } from './money.js';

export interface MockProviderOptions {
  readonly secret?: string;
  /** Simulate latency and failure for testing retry and timeout paths. */
  readonly failNext?: number;
  readonly latencyMs?: number;
}

export class ProductionGuardError extends Error {
  override readonly name = 'ProductionGuardError';
}

function constantTimeEquals(a: string, b: string): boolean {
  const bufA = Buffer.from(a, 'utf8');
  const bufB = Buffer.from(b, 'utf8');
  if (bufA.length !== bufB.length) {
    // Still perform a comparison to avoid leaking length via timing.
    timingSafeEqual(bufA, bufA);
    return false;
  }
  return timingSafeEqual(bufA, bufB);
}

/**
 * Read a string field, treating a wrong type as absent.
 *
 * `undefined` rather than a throw, because the caller decides what a missing
 * field means: `currency` and `idempotencyKey` have sensible defaults, while a
 * missing `eventId` is fatal and gets its own error. Collapsing "absent" and
 * "wrong type" into one value here is what lets that distinction be made.
 */
function readString(
  payload: Record<string, unknown>,
  key: string,
): string | undefined {
  const value = payload[key];
  return typeof value === 'string' ? value : undefined;
}

export class MockFinancialProvider implements FinancialProvider {
  readonly id: ProviderId = 'mock';

  readonly #secret: string;
  readonly #accounts = new Map<string, CollectionAccount>();
  readonly #accountNumbers = new Map<string, string>();
  readonly #transfers = new Map<string, Transfer>();
  // Two stores rather than one, and this is not tidiness.
  //
  // A single map keyed only by the caller's idempotency key is a global key
  // space: `initiateCollection({idempotencyKey: 'k'})` followed by
  // `initiatePayout({idempotencyKey: 'k'})` returns the *inbound* transfer for the
  // payout. A payout that reports success and moves no money is the worst
  // possible failure for this system to have, and it is reachable from an
  // upstream bug that reuses a key. Transfers are therefore stored under a
  // per-operation key, so a collection and a payout can never alias.
  readonly #accountIdempotency = new Map<string, string>();
  readonly #transferIdempotency = new Map<string, Transfer>();
  #failuresRemaining: number;
  #counter = 1;
  readonly #latencyMs: number;

  constructor(options: MockProviderOptions = {}) {
    this.#secret = options.secret ?? 'mock-secret-do-not-use-in-production';
    this.#failuresRemaining = options.failNext ?? 0;
    this.#latencyMs = options.latencyMs ?? 0;
  }

  /**
   * Refuse to operate under production environment configuration.
   *
   * A mock provider silently handling real payouts would mean customers believe
   * they were paid when no money moved. That is a reportable incident, not a
   * bug, so it is prevented structurally rather than by convention.
   */
  static assertNotProduction(env: string = process.env['NODE_ENV'] ?? 'development'): void {
    if (env === 'production') {
      throw new ProductionGuardError(
        'MockFinancialProvider cannot run with NODE_ENV=production. ' +
          'Wire the approved ProvidusUnity provider instead.',
      );
    }
  }

  static create(options?: MockProviderOptions): MockFinancialProvider {
    MockFinancialProvider.assertNotProduction();
    return new MockFinancialProvider(options);
  }

  #nextReference(prefix: string): string {
    return `MOCK-${prefix}-${String(this.#counter++).padStart(6, '0')}`;
  }

  async #maybeFail(): Promise<void> {
    if (this.#latencyMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, this.#latencyMs));
    }
    if (this.#failuresRemaining > 0) {
      this.#failuresRemaining -= 1;
      throw new ProviderError('simulated provider failure', 'SIMULATED', true);
    }
  }

  async createCollectionAccount(
    command: CreateCollectionAccountCommand,
  ): Promise<CollectionAccount> {
    await this.#maybeFail();
    const prior = this.#accountIdempotency.get(command.idempotencyKey);
    if (prior !== undefined) {
      // Indexed by providerAccountId, not accountNumber. It used to be indexed
      // by accountNumber and looked up by providerAccountId, so this branch
      // never found anything and every retry quietly opened a second account --
      // the exact opposite of what an idempotency key is for. The contract suite
      // found it; the previous tests never retried a create.
      const account = this.#accounts.get(prior);
      if (account !== undefined) {
        return account;
      }
    }

    const account: CollectionAccount = {
      providerAccountId: this.#nextReference('ACCT'),
      memberId: command.memberId,
      accountNumber: `0000${String(this.#counter).padStart(6, '0')}`,
      bankName: 'Mock Bank',
      status: 'PENDING_VERIFICATION',
    };
    this.#accounts.set(account.providerAccountId, account);
    this.#accountNumbers.set(account.accountNumber, account.providerAccountId);
    this.#accountIdempotency.set(command.idempotencyKey, account.providerAccountId);
    return account;
  }

  async verifyAccount(accountNumber: string): Promise<{ valid: boolean; accountName?: string }> {
    await this.#maybeFail();
    const providerAccountId = this.#accountNumbers.get(accountNumber);
    const account =
      providerAccountId === undefined ? undefined : this.#accounts.get(providerAccountId);
    if (account === undefined) {
      return { valid: false };
    }
    return { valid: true, accountName: `MOCK MEMBER ${account.memberId}` };
  }

  async initiateCollection(command: InitiateCollectionCommand): Promise<Transfer> {
    return this.#transfer(command.idempotencyKey, command.amount, 'COLL');
  }

  async initiatePayout(command: InitiatePayoutCommand): Promise<Transfer> {
    return this.#transfer(command.idempotencyKey, command.amount, 'PAY');
  }

  async #transfer(idempotencyKey: string, amount: Kobo, prefix: string): Promise<Transfer> {
    // Scoped by operation. See the note on `#transferIdempotency`: a key that
    // means "this collection" must not also mean "this payout".
    const scopedKey = `${prefix}:${idempotencyKey}`;
    const existing = this.#transferIdempotency.get(scopedKey);
    if (existing !== undefined) {
      return existing;
    }
    await this.#maybeFail();

    const transfer: Transfer = {
      providerReference: this.#nextReference(prefix),
      idempotencyKey,
      amount,
      state: 'SUCCESS' satisfies TransferState,
      settledAt: new Date(),
    };
    this.#transfers.set(transfer.providerReference, transfer);
    this.#transferIdempotency.set(scopedKey, transfer);
    return transfer;
  }

  async getTransfer(providerReference: string): Promise<Transfer> {
    await this.#maybeFail();
    const transfer = this.#transfers.get(providerReference);
    if (transfer === undefined) {
      throw new ProviderError(
        `unknown transfer ${providerReference}`,
        'NOT_FOUND',
        false,
      );
    }
    return transfer;
  }

  /** HMAC-SHA256 over the raw body, the shape most PSPs use. */
  sign(rawBody: string): string {
    return createHmac('sha256', this.#secret).update(rawBody, 'utf8').digest('hex');
  }

  async parseWebhook(event: ProviderWebhookEvent): Promise<ProviderWebhookEvent> {
    const expected = this.sign(event.rawBody);
    if (!constantTimeEquals(expected, event.signatureHeader)) {
      throw new WebhookSignatureError('webhook signature verification failed');
    }

    // Parsing happens *after* the comparison above, on purpose. A signature is
    // computed over bytes, so there is nothing to trust in the body until the
    // bytes are known to be the ones that were signed -- and a parser that runs
    // first is a parser running on attacker-controlled input.
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(event.rawBody) as Record<string, unknown>;
    } catch {
      // A verified body that will not parse is a provider defect, not a forgery:
      // the signature already proved the bytes are theirs. ProviderError is
      // retryable here, because the next delivery may well be well-formed, and a
      // 4xx that reads "malformed request" would be a lie.
      throw new ProviderError(
        'verified webhook body is not JSON',
        'MALFORMED_WEBHOOK',
        true,
      );
    }

    const reference = readString(parsed, 'reference');
    const state = readString(parsed, 'state');
    const amount = parsed['amount'];
    const occurredAt = readString(parsed, 'occurredAt');
    const eventId = readString(parsed, 'eventId');
    const eventType = readString(parsed, 'eventType');
    const currency = readString(parsed, 'currency');

    if (reference === undefined || eventId === undefined || eventType === undefined) {
      throw new ProviderError(
        'verified webhook is missing the fields settlement matches on',
        'MALFORMED_WEBHOOK',
        true,
      );
    }

    // Reported as a provider defect rather than allowed to throw whatever the
    // money type throws. The seam has two ways to fail a delivery -- the signature
    // did not verify, or the body was signed and cannot be used -- and an adapter
    // that raised a third kind of error for a signed body would leave the caller
    // with no way to tell "this provider is broken" from "this code is broken".
    // A negative or fractional amount is a real possibility in a body that
    // verified, and `kobo()` would reject it.
    if (amount !== undefined && (typeof amount !== 'number' || !Number.isInteger(amount) || amount < 0)) {
      throw new ProviderError(
        'verified webhook carries an amount that is not a whole number of kobo',
        'MALFORMED_WEBHOOK',
        true,
      );
    }

    const when = occurredAt === undefined ? new Date() : new Date(occurredAt);
    if (Number.isNaN(when.getTime())) {
      throw new ProviderError(
        'verified webhook carries an unparseable occurredAt',
        'MALFORMED_WEBHOOK',
        true,
      );
    }

    return {
      eventId,
      eventType,
      providerReference: reference,
      idempotencyKey: readString(parsed, 'idempotencyKey') ?? '',
      state: (state ?? 'UNKNOWN') as TransferState,
      amount: typeof amount === 'number' ? kobo(amount) : (0 as Kobo),
      currency: currency ?? 'NGN',
      occurredAt: when,
      rawBody: event.rawBody,
      signatureHeader: event.signatureHeader,
      parsedPayload: parsed,
    };
  }

  /**
   * Build a signed webhook for a transfer. Test helper: lets tests drive
   * out-of-order and duplicate delivery without hand-rolling HMAC.
   */
  buildWebhook(
    providerReference: string,
    state: TransferState = 'SUCCESS',
  ): ProviderWebhookEvent {
    const transfer = this.#transfers.get(providerReference);
    if (transfer === undefined) {
      throw new ProviderError(`unknown transfer ${providerReference}`, 'NOT_FOUND', false);
    }
    const rawBody = JSON.stringify({
      // These two are what settlement deduplicates on and dispatches by, so the
      // mock has to send them for real rather than let the parser invent them:
      // a fixture that cannot produce a redelivery cannot test that a redelivery
      // is harmless.
      eventId: `mock-evt-${providerReference}-${state}`,
      eventType: `transfer.${state.toLowerCase()}`,
      reference: providerReference,
      idempotencyKey: transfer.idempotencyKey,
      state,
      amount: transfer.amount,
      currency: 'NGN',
      occurredAt: new Date().toISOString(),
    });
    return {
      eventId: `mock-evt-${providerReference}-${state}`,
      eventType: `transfer.${state.toLowerCase()}`,
      providerReference,
      idempotencyKey: transfer.idempotencyKey,
      state,
      amount: transfer.amount,
      currency: 'NGN',
      occurredAt: new Date(),
      rawBody,
      signatureHeader: this.sign(rawBody),
      // What the *sender* believes it sent. Deliberately not the parsed values:
      // the whole point of the round trip is that these arrive as empty and come
      // back filled in from the body.
      parsedPayload: {},
    };
  }

  /** Description of what the mock did, for the audit log. */
  describe(): string {
    return (
      `MockFinancialProvider: ${this.#transfers.size} simulated transfers, ` +
      `NGN ${format(
        [...this.#transfers.values()].reduce<number>((acc, t) => acc + t.amount, 0) as Kobo,
      )}. NO REAL MONEY WAS MOVED.`
    );
  }
}
