import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { WebhookSignatureError } from '../src/financial-provider.js';
import { MockFinancialProvider, ProductionGuardError } from '../src/mock-provider.js';
import { naira } from '../src/money.js';

const AMOUNT = naira(200_000);

describe('MockFinancialProvider safety guards', () => {
  it('refuses to construct under NODE_ENV=production', () => {
    assert.throws(() => MockFinancialProvider.assertNotProduction('production'), ProductionGuardError);
    assert.doesNotThrow(() => MockFinancialProvider.assertNotProduction('development'));
    assert.doesNotThrow(() => MockFinancialProvider.assertNotProduction('test'));
  });

  it('labels its output so it can never be mistaken for real money', () => {
    const provider = MockFinancialProvider.create();
    assert.match(provider.describe(), /NO REAL MONEY WAS MOVED/);
    assert.match(provider.describe(), /MockFinancialProvider/);
  });

  it('is identified as mock, never as a live provider', () => {
    assert.equal(MockFinancialProvider.create().id, 'mock');
  });
});

describe('MockFinancialProvider idempotency', () => {
  it('returns the same payout reference on retry', async () => {
    const provider = MockFinancialProvider.create();
    const command = {
      idempotencyKey: 'payout:ajo1:1:m1',
      destinationAccountNumber: '0000001',
      amount: AMOUNT,
      reference: 'AJO-1',
      callbackUrl: 'https://example.test/hook',
    };

    const first = await provider.initiatePayout(command);
    const retry = await provider.initiatePayout(command);

    assert.equal(first.providerReference, retry.providerReference);
  });

  it('issues distinct references for distinct idempotency keys', async () => {
    const provider = MockFinancialProvider.create();
    const base = {
      destinationAccountNumber: '0000001',
      amount: AMOUNT,
      reference: 'AJO-1',
      callbackUrl: 'https://example.test/hook',
    };
    const a = await provider.initiatePayout({ ...base, idempotencyKey: 'payout:a' });
    const b = await provider.initiatePayout({ ...base, idempotencyKey: 'payout:b' });
    assert.notEqual(a.providerReference, b.providerReference);
  });

  it('surfaces retryable provider failures', async () => {
    const provider = MockFinancialProvider.create({ failNext: 1 });
    await assert.rejects(
      () =>
        provider.initiatePayout({
          idempotencyKey: 'payout:retry',
          destinationAccountNumber: '0000001',
          amount: AMOUNT,
          reference: 'AJO-1',
          callbackUrl: 'https://example.test/hook',
        }),
      /simulated provider failure/,
    );
  });
});

describe('Webhook signature verification', () => {
  it('accepts a correctly signed webhook', async () => {
    const provider = MockFinancialProvider.create({ secret: 'test-secret' });
    const transfer = await provider.initiatePayout({
      idempotencyKey: 'payout:ajo1:1:m1',
      destinationAccountNumber: '0000001',
      amount: AMOUNT,
      reference: 'AJO-1',
      callbackUrl: 'https://example.test/hook',
    });

    const event = provider.buildWebhook(transfer.providerReference, 'SUCCESS');
    await assert.doesNotReject(() => provider.parseWebhook(event));
  });

  it('rejects a tampered body', async () => {
    const provider = MockFinancialProvider.create({ secret: 'test-secret' });
    const transfer = await provider.initiatePayout({
      idempotencyKey: 'payout:ajo1:1:m1',
      destinationAccountNumber: '0000001',
      amount: AMOUNT,
      reference: 'AJO-1',
      callbackUrl: 'https://example.test/hook',
    });
    const event = provider.buildWebhook(transfer.providerReference, 'SUCCESS');

    const tampered = { ...event, rawBody: event.rawBody.replace('SUCCESS', 'FAILED') };
    await assert.rejects(() => provider.parseWebhook(tampered), WebhookSignatureError);
  });

  it('rejects an invalid signature', async () => {
    const provider = MockFinancialProvider.create({ secret: 'test-secret' });
    const transfer = await provider.initiatePayout({
      idempotencyKey: 'payout:ajo1:1:m1',
      destinationAccountNumber: '0000001',
      amount: AMOUNT,
      reference: 'AJO-1',
      callbackUrl: 'https://example.test/hook',
    });
    const event = provider.buildWebhook(transfer.providerReference, 'SUCCESS');

    await assert.rejects(
      () => provider.parseWebhook({ ...event, signatureHeader: 'deadbeef' }),
      WebhookSignatureError,
    );
  });

  it('rejects a webhook signed with the wrong secret', async () => {
    const honest = MockFinancialProvider.create({ secret: 'secret-a' });
    const attacker = MockFinancialProvider.create({ secret: 'secret-b' });
    const transfer = await honest.initiatePayout({
      idempotencyKey: 'payout:ajo1:1:m1',
      destinationAccountNumber: '0000001',
      amount: AMOUNT,
      reference: 'AJO-1',
      callbackUrl: 'https://example.test/hook',
    });
    const event = honest.buildWebhook(transfer.providerReference, 'SUCCESS');

    await assert.rejects(
      () => attacker.parseWebhook(event),
      WebhookSignatureError,
    );
  });
});
