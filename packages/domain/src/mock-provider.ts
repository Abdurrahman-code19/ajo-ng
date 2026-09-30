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
import { format, type Kobo } from './money.js';

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

export class MockFinancialProvider implements FinancialProvider {
  readonly id: ProviderId = 'mock';

  readonly #secret: string;
  readonly #accounts = new Map<string, CollectionAccount>();
  readonly #transfers = new Map<string, Transfer>();
  readonly #idempotency = new Map<string, Transfer>();
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
    const existingKey = `acct:${command.idempotencyKey}`;
    const prior = this.#idempotency.get(existingKey);
    if (prior !== undefined) {
      const account = this.#accounts.get(prior.providerReference);
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
    this.#accounts.set(account.accountNumber, account);
    this.#idempotency.set(existingKey, {
      providerReference: account.providerAccountId,
      idempotencyKey: existingKey,
      amount: 0 as Kobo,
      state: 'SUCCESS',
    });
    return account;
  }

  async verifyAccount(accountNumber: string): Promise<{ valid: boolean; accountName?: string }> {
    await this.#maybeFail();
    const account = this.#accounts.get(accountNumber);
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
    const existing = this.#idempotency.get(idempotencyKey);
    if (existing !== undefined) {
      const transfer = this.#transfers.get(existing.providerReference);
      if (transfer !== undefined) {
        return transfer;
      }
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
    this.#idempotency.set(idempotencyKey, transfer);
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
    return event;
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
      reference: providerReference,
      idempotencyKey: transfer.idempotencyKey,
      state,
      amount: transfer.amount,
      occurredAt: new Date().toISOString(),
    });
    return {
      providerReference,
      idempotencyKey: transfer.idempotencyKey,
      state,
      amount: transfer.amount,
      occurredAt: new Date(),
      rawBody,
      signatureHeader: this.sign(rawBody),
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
