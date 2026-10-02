import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { describe, it } from 'node:test';
import {
  MockFinancialProvider,
  ProductionGuardError,
} from '../src/mock-provider.js';
import { runProviderContract, type ProviderHarness } from './provider-contract.js';
import type { TransferState } from '../src/financial-provider.js';

/**
 * The mock adapter, held to the same contract as any real provider.
 *
 * Every assertion below runs through `runProviderContract`, which is the same
 * suite a ProvidusUnity adapter will be given. If that adapter later changes
 * behaviour the business logic depends on, it fails here rather than in
 * production.
 */
const harness: ProviderHarness = {
  build: () => MockFinancialProvider.create({ secret: 'contract-suite-secret' }),

  signedWebhook: async (provider, reference, state = 'SUCCESS') => {
    const mock = provider as MockFinancialProvider;
    return mock.buildWebhook(reference, state);
  },

  // Signed under a different key rather than corrupted, so this exercises the
  // failure a leaked or rotated secret produces -- which is the one an attacker
  // actually achieves -- rather than a malformed header.
  //
  // The signature is computed directly rather than by asking a second mock to
  // build the body: a second mock has never seen this transfer and would refuse.
  // An earlier version of this harness signed the body with the *live* provider's
  // own `sign`, which produced a perfectly valid signature and therefore tested
  // nothing while appearing to work.
  misSignedWebhook: async (provider, reference) => {
    const live = provider as MockFinancialProvider;
    const event = live.buildWebhook(reference, 'SUCCESS');
    return {
      ...event,
      signatureHeader: createHmac('sha256', 'a-different-secret')
        .update(event.rawBody, 'utf8')
        .digest('hex'),
    };
  },
};

runProviderContract('MockFinancialProvider', harness);

describe('MockFinancialProvider safety guards', () => {
  it('refuses to construct under NODE_ENV=production', () => {
    assert.throws(() => MockFinancialProvider.assertNotProduction('production'), ProductionGuardError);
  });

  it('constructs outside production', () => {
    MockFinancialProvider.assertNotProduction('test');
    assert.ok(MockFinancialProvider.create());
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

describe('MockFinancialProvider failure injection', () => {
  it('surfaces a simulated failure as retryable', async () => {
    // The contract suite cannot dictate when a provider fails, so the mock's
    // failure path is asserted here instead. This is the path the notification
    // worker's own retry loop depends on, and it is the reason the mock accepts
    // `failNext` at all.
    const provider = MockFinancialProvider.create({ failNext: 1 });
    await assert.rejects(
      () =>
        provider.initiateCollection({
          idempotencyKey: 'mock-fail-1',
          accountNumber: '000000001',
          amount: 1000 as never,
          reference: 'AJO/MOCK/FAIL',
          callbackUrl: 'https://example.ng/hooks',
        }),
      (error: unknown) => {
        assert.ok(error instanceof Error);
        assert.equal((error as { retryable?: boolean }).retryable, true);
        return true;
      },
    );

    // And the retry after the simulated outage succeeds, which is the whole
    // point of the flag being true.
    const transfer = await provider.initiateCollection({
      idempotencyKey: 'mock-fail-1',
      accountNumber: '000000001',
      amount: 1000 as never,
      reference: 'AJO/MOCK/FAIL',
      callbackUrl: 'https://example.ng/hooks',
    });
    assert.ok(transfer.providerReference.startsWith('MOCK-'));
  });
});

describe('MockFinancialProvider transfer states', () => {
  it('builds a webhook in a requested state, so out-of-order delivery is testable', async () => {
    // Spec §13.5 requires that "a success arriving after a failure for the same
    // reference is resolved by the terminal state, not by arrival order". That
    // rule is enforced above this seam, but it can only be exercised if the
    // provider can be made to say either thing -- so the mock must be able to.
    const provider = MockFinancialProvider.create();
    const transfer = await provider.initiateCollection({
      idempotencyKey: 'mock-states-1',
      accountNumber: '000000001',
      amount: 1000 as never,
      reference: 'AJO/MOCK/STATES',
      callbackUrl: 'https://example.ng/hooks',
    });

    for (const state of ['PENDING', 'SUCCESS', 'FAILED', 'REVERSED', 'UNKNOWN'] as TransferState[]) {
      const event = provider.buildWebhook(transfer.providerReference, state);
      const parsed = await provider.parseWebhook(event);
      assert.equal(parsed.state, state);
    }
  });
});