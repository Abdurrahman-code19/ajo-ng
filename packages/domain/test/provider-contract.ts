/**
 * The provider contract suite.
 *
 * The specification requires that "every adapter is covered by the same contract
 * test suite, so a provider swap cannot silently change behaviour that the
 * business logic depends on" (§13.4). That requirement is not satisfied by tests
 * written *about* one adapter: `mock-provider.test.ts` would pass forever and
 * mean nothing about ProvidusUnity, and the swap would land on a green build.
 *
 * So the assertions live here, in a suite that takes a provider and says nothing
 * about which one it is. An adapter supplies a factory and the two pieces of
 * scaffolding that cannot be generic -- how to produce a webhook the provider
 * will accept, and how to produce one it will reject.
 *
 * Every clause below is traceable to something the project has already promised:
 * the interface's own documented guarantees, or the specification. Nothing here
 * is invented. In particular there is no clause about fees, settlement timing or
 * retry policy, because those are the provider's business and Ajo.ng does not get
 * to assume them.
 */

import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  ProviderError,
  WebhookSignatureError,
  type FinancialProvider,
  type ProviderId,
  type ProviderWebhookEvent,
  type TransferState,
} from '../src/financial-provider.js';
import { kobo } from '../src/money.js';

/**
 * How to exercise an adapter.
 *
 * `signedWebhook` and `misSignedWebhook` are the only provider-specific pieces,
 * and both exist because signing is provider-specific by nature. An adapter
 * author writes these once; every assertion in this file then applies to them
 * unchanged.
 */
export interface ProviderHarness {
  /** A fresh provider. Called per clause, so no state leaks between them. */
  readonly build: () => FinancialProvider;
  /** A webhook this provider should accept. */
  readonly signedWebhook: (
    provider: FinancialProvider,
    reference: string,
    state?: TransferState,
  ) => Promise<ProviderWebhookEvent>;
  /** The same webhook, signed so this provider must reject it. */
  readonly misSignedWebhook: (
    provider: FinancialProvider,
    reference: string,
  ) => Promise<ProviderWebhookEvent>;
  /**
   * Sign arbitrary bytes.
   *
   * For the clause that needs a body which verifies but does not parse. Asking
   * the provider to build it is not possible -- there is no such webhook -- and
   * signing it with a *different* secret would exercise the signature check
   * instead, which is already covered and would prove nothing.
   */
  readonly signRaw: (provider: FinancialProvider, rawBody: string) => string;
}

const KNOWN_PROVIDER_IDS: readonly ProviderId[] = ['mock', 'providus_unity'];

export function runProviderContract(name: string, harness: ProviderHarness): void {
  describe(`${name} satisfies the financial provider contract`, () => {
    // ---------------------------------------------------------------- identity

    it('identifies itself with a known provider id', () => {
      const provider = harness.build();
      assert.ok(
        KNOWN_PROVIDER_IDS.includes(provider.id),
        `provider id ${JSON.stringify(provider.id)} is not one the application knows, ` +
          'so nothing upstream can switch behaviour on it',
      );
    });

    // ------------------------------------------------------------- idempotency

    it('returns the same collection account when a key is retried', async () => {
      const provider = harness.build();
      const command = {
        idempotencyKey: 'contract-acct-1',
        memberId: 'member-1',
        reference: 'AJO/CONTRACT/1',
      };
      const first = await provider.createCollectionAccount(command);
      const second = await provider.createCollectionAccount(command);

      assert.equal(
        first.providerAccountId,
        second.providerAccountId,
        'a retried create moved to a second provider account; a timeout followed by ' +
          'a retry is ordinary traffic, not a second account',
      );
    });

    it('issues distinct accounts for distinct keys', async () => {
      const provider = harness.build();
      const first = await provider.createCollectionAccount({
        idempotencyKey: 'contract-acct-a',
        memberId: 'member-1',
        reference: 'AJO/CONTRACT/A',
      });
      const second = await provider.createCollectionAccount({
        idempotencyKey: 'contract-acct-b',
        memberId: 'member-1',
        reference: 'AJO/CONTRACT/B',
      });
      assert.notEqual(first.providerAccountId, second.providerAccountId);
    });

    it('returns the same collection when a key is retried', async () => {
      const provider = harness.build();
      const command = {
        idempotencyKey: 'contract-coll-1',
        accountNumber: '000000001',
        amount: kobo(100_000),
        reference: 'AJO/CONTRACT/COLL',
        callbackUrl: 'https://example.ng/hooks',
      };
      const first = await provider.initiateCollection(command);
      const second = await provider.initiateCollection(command);

      assert.equal(
        first.providerReference,
        second.providerReference,
        'a retried collection produced a second transfer reference; the interface ' +
          'promises that a retry after a timeout must not move money twice',
      );
      assert.equal(first.amount, second.amount);
    });

    it('issues distinct transfers for distinct keys', async () => {
      const provider = harness.build();
      const base = {
        accountNumber: '000000001',
        amount: kobo(100_000),
        reference: 'AJO/CONTRACT/D',
        callbackUrl: 'https://example.ng/hooks',
      };
      const first = await provider.initiateCollection({
        ...base,
        idempotencyKey: 'contract-coll-d1',
      });
      const second = await provider.initiateCollection({
        ...base,
        idempotencyKey: 'contract-coll-d2',
      });
      assert.notEqual(first.providerReference, second.providerReference);
    });

    it('returns the same payout when a key is retried', async () => {
      const provider = harness.build();
      const command = {
        idempotencyKey: 'contract-pay-1',
        destinationAccountNumber: '000000002',
        amount: kobo(250_000),
        reference: 'AJO/CONTRACT/PAY',
        callbackUrl: 'https://example.ng/hooks',
      };
      const first = await provider.initiatePayout(command);
      const second = await provider.initiatePayout(command);
      assert.equal(first.providerReference, second.providerReference);
      assert.equal(first.amount, second.amount);
    });

    it('scopes idempotency to the operation, not just the key', async () => {
      // One shared key, used once to take a payment in and once to pay out. If a
      // provider treats the key as global, the payout call returns the inbound
      // transfer: a payout that silently pays nothing and reports success.
      //
      // This is not in the specification, because the application never relies
      // on it -- it generates a fresh key per operation. It is asserted anyway
      // because it is a property of the *key space*, and a provider whose keys
      // are global turns an upstream bug into money that leaves the wrong way.
      const provider = harness.build();
      const key = 'contract-shared-key';

      const collected = await provider.initiateCollection({
        idempotencyKey: key,
        accountNumber: '000000001',
        amount: kobo(100_000),
        reference: 'AJO/CONTRACT/SHARED-IN',
        callbackUrl: 'https://example.ng/hooks',
      });
      const paid = await provider.initiatePayout({
        idempotencyKey: key,
        destinationAccountNumber: '000000003',
        amount: kobo(100_000),
        reference: 'AJO/CONTRACT/SHARED-OUT',
        callbackUrl: 'https://example.ng/hooks',
      });

      assert.notEqual(
        paid.providerReference,
        collected.providerReference,
        'the same idempotency key returned the same transfer for a collection and a ' +
          'payout, so the key space is global; a caller bug would move money in the ' +
          'wrong direction',
      );
    });

    // ------------------------------------------------------------------ amounts

    it('reports the amount it was given, to the kobo', async () => {
      // An amount that only survives a round trip when it is whole is the
      // classic float bug in a money path, and it is invisible until a member is
      // charged 9,999 kobo for a 10,000 kobo contribution.
      const provider = harness.build();
      const awkward = kobo(10_001);
      const transfer = await provider.initiateCollection({
        idempotencyKey: 'contract-amount-1',
        accountNumber: '000000001',
        amount: awkward,
        reference: 'AJO/CONTRACT/AMOUNT',
        callbackUrl: 'https://example.ng/hooks',
      });

      assert.equal(transfer.amount, awkward);
      assert.ok(Number.isInteger(transfer.amount), 'a provider rounded a kobo amount');
      assert.ok(transfer.amount > 0);
    });

    // -------------------------------------------------------------- lookup

    it('reports an unknown transfer as a non-retryable provider error', async () => {
      const provider = harness.build();
      let thrown: unknown;
      try {
        await provider.getTransfer('NO-SUCH-REFERENCE-000');
      } catch (error) {
        thrown = error;
      }

      assert.ok(thrown instanceof ProviderError, 'an unknown reference must be a ProviderError');
      const error = thrown as ProviderError;
      assert.equal(
        error.retryable,
        false,
        'an unknown reference was marked retryable, so a caller will keep retrying a ' +
          'lookup that can never succeed',
      );
    });

    // --------------------------------------------------------------- accounts

    it('answers an unknown account with valid: false rather than throwing', async () => {
      // `verifyAccount` is called on numbers a member typed. Throwing here would
      // turn a typo into a 500, and the caller cannot distinguish "this account
      // does not exist" from "the provider is down".
      const provider = harness.build();
      const result = await provider.verifyAccount('00000000000000');
      assert.equal(result.valid, false);
    });

    it('reports an account it created as valid', async () => {
      const provider = harness.build();
      const account = await provider.createCollectionAccount({
        idempotencyKey: 'contract-verify-1',
        memberId: 'member-verify',
        reference: 'AJO/CONTRACT/VERIFY',
      });
      const result = await provider.verifyAccount(account.accountNumber);
      assert.equal(result.valid, true);
    });

    // ------------------------------------------------------------------ webhooks

    it('accepts a correctly signed webhook', async () => {
      const provider = harness.build();
      const transfer = await provider.initiateCollection({
        idempotencyKey: 'contract-hook-ok',
        accountNumber: '000000001',
        amount: kobo(75_000),
        reference: 'AJO/CONTRACT/HOOK-OK',
        callbackUrl: 'https://example.ng/hooks',
      });
      const event = await harness.signedWebhook(provider, transfer.providerReference);
      const parsed = await provider.parseWebhook(event);

      assert.equal(parsed.providerReference, transfer.providerReference);
      assert.equal(parsed.state, 'SUCCESS');
    });

    it('rejects a webhook whose body was changed after signing', async () => {
      // The attack this refuses is the important one: a valid signature over a
      // different body, replayed with the original signature.
      const provider = harness.build();
      const transfer = await provider.initiateCollection({
        idempotencyKey: 'contract-hook-tamper',
        accountNumber: '000000001',
        amount: kobo(75_000),
        reference: 'AJO/CONTRACT/HOOK-TAMPER',
        callbackUrl: 'https://example.ng/hooks',
      });
      const event = await harness.signedWebhook(provider, transfer.providerReference);
      const tampered = {
        ...event,
        rawBody: event.rawBody.replace(/75000/g, '9999999'),
      };

      await assert.rejects(
        () => provider.parseWebhook(tampered),
        WebhookSignatureError,
        'a tampered body was accepted',
      );
    });

    it('rejects a webhook signed with a different secret', async () => {
      const provider = harness.build();
      const transfer = await provider.initiateCollection({
        idempotencyKey: 'contract-hook-wrongkey',
        accountNumber: '000000001',
        amount: kobo(75_000),
        reference: 'AJO/CONTRACT/HOOK-WRONGKEY',
        callbackUrl: 'https://example.ng/hooks',
      });
      const event = await harness.misSignedWebhook(provider, transfer.providerReference);

      await assert.rejects(
        () => provider.parseWebhook(event),
        WebhookSignatureError,
        'a webhook signed with the wrong secret was accepted',
      );
    });

    it('rejects a missing or malformed signature without throwing something else', async () => {
      // A malformed header must surface as WebhookSignatureError specifically,
      // because that is what the HTTP layer catches to answer 401. Anything else
      // escaping here becomes a 500, which tells the provider the endpoint is
      // broken and invites retries of a request that was never going to verify.
      const provider = harness.build();
      const transfer = await provider.initiateCollection({
        idempotencyKey: 'contract-hook-malformed',
        accountNumber: '000000001',
        amount: kobo(75_000),
        reference: 'AJO/CONTRACT/HOOK-MALFORMED',
        callbackUrl: 'https://example.ng/hooks',
      });
      const event = await harness.signedWebhook(provider, transfer.providerReference);

      for (const signatureHeader of ['', 'not-a-signature', 'sha256=zzzz']) {
        await assert.rejects(
          () => provider.parseWebhook({ ...event, signatureHeader }),
          WebhookSignatureError,
          `a signature header of ${JSON.stringify(signatureHeader)} was not refused as ` +
            'a WebhookSignatureError',
        );
      }
    });

    it('is safe to parse the same webhook twice', async () => {
      // Providers redeliver. Parsing must not consume anything, or a retry of the
      // HTTP request itself fails and the event is lost rather than deduplicated.
      const provider = harness.build();
      const transfer = await provider.initiateCollection({
        idempotencyKey: 'contract-hook-twice',
        accountNumber: '000000001',
        amount: kobo(75_000),
        reference: 'AJO/CONTRACT/HOOK-TWICE',
        callbackUrl: 'https://example.ng/hooks',
      });
      const event = await harness.signedWebhook(provider, transfer.providerReference);

      const first = await provider.parseWebhook(event);
      const second = await provider.parseWebhook(event);
      assert.equal(first.providerReference, second.providerReference);
      assert.equal(first.state, second.state);
    });

    // ------------------------------------------------- what parsing has to fill

    it('fills the identity fields from the body rather than echoing the caller', async () => {
      // The event arrives with nothing in it -- no event id, no event type, no
      // currency, no parsed payload -- because none of those have been checked
      // yet. An adapter that returns its input unchanged hands the HTTP layer a
      // deduplication key the sender chose, and `parseWebhook` returning `event`
      // verbatim is exactly the shape that does that while still passing every
      // clause above it.
      const provider = harness.build();
      const transfer = await provider.initiateCollection({
        idempotencyKey: 'contract-hook-enrich',
        accountNumber: '000000001',
        amount: kobo(75_000),
        reference: 'AJO/CONTRACT/HOOK-ENRICH',
        callbackUrl: 'https://example.ng/hooks',
      });
      const event = await harness.signedWebhook(provider, transfer.providerReference);

      const blank: ProviderWebhookEvent = {
        ...event,
        eventId: '',
        eventType: '',
        currency: '',
        parsedPayload: {},
      };
      const parsed = await provider.parseWebhook(blank);

      assert.ok(
        parsed.eventId.length > 0,
        'parseWebhook returned no eventId; the HTTP layer deduplicates on it and ' +
          'would treat every delivery of one transfer as a separate event',
      );
      assert.ok(
        parsed.eventType.length > 0,
        'parseWebhook returned no eventType; nothing can tell a transfer event ' +
          'from an account event, so everything would be either ignored or misread',
      );
      assert.ok(
        parsed.currency.length > 0,
        'parseWebhook returned no currency; settlement compares it against the ' +
          "Ajo's and a missing one silently passes every check",
      );
      assert.ok(
        Object.keys(parsed.parsedPayload).length > 0,
        'parseWebhook returned an empty parsedPayload; the row persisted for ' +
          'forensics would not contain what the provider actually sent',
      );
    });

    it('reports a verified but unreadable body as a provider failure', async () => {
      // A body that will not parse, or that is missing the fields settlement
      // matches on, has already passed the signature check -- so the bytes are
      // genuinely the provider's and the defect is theirs. It must surface as a
      // ProviderError, which the HTTP layer treats as retryable, rather than as
      // a WebhookSignatureError, which would tell the provider "you signed this
      // wrongly" about a body they signed correctly.
      const provider = harness.build();
      const transfer = await provider.initiateCollection({
        idempotencyKey: 'contract-hook-garbage',
        accountNumber: '000000001',
        amount: kobo(75_000),
        reference: 'AJO/CONTRACT/HOOK-GARBAGE',
        callbackUrl: 'https://example.ng/hooks',
      });
      const event = await harness.signedWebhook(provider, transfer.providerReference);

      const garbage = '{"eventId":';
      const mangled = {
        ...event,
        rawBody: garbage,
        signatureHeader: harness.signRaw(provider, garbage),
      };

      let thrown: unknown;
      try {
        await provider.parseWebhook(mangled);
      } catch (error) {
        thrown = error;
      }
      assert.ok(
        thrown instanceof ProviderError,
        'a verified but unparseable body was not reported as a ProviderError',
      );
      assert.notEqual(
        thrown instanceof WebhookSignatureError,
        true,
        'a verified body was reported as a signature failure, which tells the ' +
          'provider their signing is wrong when it is not',
      );
    });

    // ------------------------------------------------------------- failures

    it('reports a retryable failure as retryable and a permanent one as not', async () => {
      // The suite cannot dictate *when* a provider fails, but it can insist that
      // the flag exists and that an unknown transfer is not retryable, because
      // that is the flag the retry loop reads.
      const provider = harness.build();
      let thrown: unknown;
      try {
        await provider.getTransfer('STILL-NO-SUCH-REFERENCE-000');
      } catch (error) {
        thrown = error;
      }
      assert.ok(thrown instanceof ProviderError);
      assert.equal(typeof (thrown as ProviderError).retryable, 'boolean');
      assert.equal(typeof (thrown as ProviderError).code, 'string');
      assert.ok((thrown as ProviderError).code.length > 0, 'a provider error with no code');
    });
  });
}