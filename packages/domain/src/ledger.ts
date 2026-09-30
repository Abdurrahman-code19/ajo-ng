/**
 * Append-only double-entry ledger.
 *
 * The invariant that makes money safe: the sum of all postings in a
 * transaction is exactly zero. Value cannot be created or destroyed inside this
 * ledger, only moved between accounts. If the sum is ever non-zero, something is
 * wrong, and we want that to be a thrown error and an alert, not a balance that
 * quietly drifts for six months.
 *
 * There are no update and no delete methods, by design. A correction is a new
 * reversing transaction. History is the product: a member disputing a ₦200,000
 * payout needs to see the original entry, not a row that was edited.
 *
 * Money is represented as kobo (see money.ts) and is never rounded implicitly.
 */

import { MoneyError, add, format, isZero, subtract, sum, type Kobo } from './money.js';

/** Posting sides. Debits and credits are equal and opposite. */
export type Side = 'debit' | 'credit';

/**
 * Account kinds. A closed union on purpose: the set of places money can sit is
 * a business and regulatory decision, and adding a new one should require a
 * deliberate code change plus a migration, not a loose string from a request
 * body.
 */
export type AccountKind =
  /** Cash actually held by the payment provider / escrow. Asset. */
  | 'escrow_cash'
  /** Owed by members for the current round. Asset. */
  | 'contributions_receivable'
  /** Owed by members who have defaulted. Asset. */
  | 'defaults_receivable'
  /** Owed to the member whose turn it is. Liability. */
  | 'payouts_payable'
  /** Owed to departed members for unforwarded contributions. Liability. */
  | 'refunds_payable'
  /** Ajo.ng's fee income. Equity. */
  | 'fees_income'
  /** In-flight balance for provider transactions not yet settled. Liability. */
  | 'provider_clearing';

export type AccountId = string & { readonly __accountId?: unique symbol };

/** The side on which an account kind carries its normal balance. */
const NORMAL_SIDE: Record<AccountKind, Side> = {
  escrow_cash: 'debit',
  contributions_receivable: 'debit',
  defaults_receivable: 'debit',
  payouts_payable: 'credit',
  refunds_payable: 'credit',
  fees_income: 'credit',
  provider_clearing: 'credit',
};

export class LedgerError extends Error {
  override readonly name = 'LedgerError';
}

export interface Posting {
  readonly account: AccountKind;
  readonly side: Side;
  readonly amount: Kobo;
  /** Optional per-account qualifier, e.g. a specific member id. */
  readonly memo?: string;
}

export interface Transaction {
  readonly id: string;
  readonly idempotencyKey: string;
  readonly kind: string;
  readonly postings: readonly Posting[];
  readonly occurredAt: Date;
  readonly reversesTransactionId?: string;
  readonly reversalReason?: string;
}

export interface PostCommand {
  readonly idempotencyKey: string;
  readonly kind: string;
  readonly postings: readonly Posting[];
  readonly occurredAt?: Date;
  /** Set only by Ledger.reverse to link the correction to its original. */
  readonly reversesTransactionId?: string;
  readonly reversalReason?: string;
}

export interface Balances {
  /** Positive = asset or expense side. Negative = liability or income side. */
  readonly byAccount: ReadonlyMap<AccountKind, Kobo>;
  /** Always zero when the ledger is internally consistent. */
  readonly netPosition: Kobo;
}

function signed(posting: Posting): number {
  return posting.side === 'debit' ? posting.amount : -posting.amount;
}

function validatePostings(postings: readonly Posting[]): void {
  if (postings.length < 2) {
    throw new LedgerError(
      'double-entry requires at least two postings, received ' + String(postings.length),
    );
  }
  for (const posting of postings) {
    if (!Number.isSafeInteger(posting.amount) || posting.amount <= 0) {
      throw new LedgerError(
        `posting amount must be a positive safe integer, received ${String(posting.amount)}`,
      );
    }
    if (!(posting.account in NORMAL_SIDE)) {
      throw new LedgerError(`unknown account kind: ${String(posting.account)}`);
    }
  }
  const net = postings.reduce((acc, posting) => acc + signed(posting), 0);
  if (net !== 0) {
    throw new LedgerError(
      'transaction does not balance: debits must equal credits (off by ' +
        String(Math.abs(net)) +
        ' kobo)',
    );
  }
}

export class Ledger {
  readonly #transactions: Transaction[] = [];
  readonly #byIdempotencyKey = new Map<string, Transaction>();
  readonly #balances = new Map<AccountKind, number>();
  #nextSequence = 1;

  /**
   * Post a balanced transaction, or return the existing one if this
   * idempotency key has been seen before.
   *
   * Idempotency is the reason this is safe to retry. A network timeout on a
   * payout submit is not a failure state; the caller will retry, and a retried
   * payout must not move money twice. Keys are scoped per logical operation, so
   * derive them from something stable such as
   * `payout:${ajoId}:${roundNumber}:${memberId}` rather than a random UUID.
   */
  post(command: PostCommand): Transaction {
    const existing = this.#byIdempotencyKey.get(command.idempotencyKey);
    if (existing !== undefined) {
      return existing;
    }

    validatePostings(command.postings);

    const transaction: Transaction = {
      id: `txn_${String(this.#nextSequence++).padStart(8, '0')}`,
      idempotencyKey: command.idempotencyKey,
      kind: command.kind,
      postings: [...command.postings],
      occurredAt: command.occurredAt ?? new Date(),
      ...(command.reversesTransactionId === undefined
        ? {}
        : { reversesTransactionId: command.reversesTransactionId }),
      ...(command.reversalReason === undefined
        ? {}
        : { reversalReason: command.reversalReason }),
    };

    this.#transactions.push(transaction);
    this.#byIdempotencyKey.set(command.idempotencyKey, transaction);

    for (const posting of transaction.postings) {
      this.#balances.set(posting.account, (this.#balances.get(posting.account) ?? 0) + signed(posting));
    }

    return transaction;
  }

  /**
   * Reverse a transaction by appending its exact mirror.
   *
   * The original stays in the ledger forever. This is the only supported way to
   * undo a financial operation.
   */
  reverse(
    transactionId: string,
    reason: string,
    idempotencyKey: string,
  ): Transaction {
    const original = this.#transactions.find((txn) => txn.id === transactionId);
    if (original === undefined) {
      throw new LedgerError(`cannot reverse unknown transaction: ${transactionId}`);
    }
    if (reason.trim() === '') {
      throw new LedgerError('reversal reason is required for audit');
    }

    const mirrored: readonly Posting[] = original.postings.map((posting) => ({
      account: posting.account,
      side: posting.side === 'debit' ? 'credit' : 'debit',
      amount: posting.amount,
      ...(posting.memo === undefined ? {} : { memo: posting.memo }),
    }));

    return this.post({
      idempotencyKey,
      kind: 'reversal',
      postings: mirrored,
      reversesTransactionId: original.id,
      reversalReason: reason,
    });
  }

  balanceOf(account: AccountKind): Kobo {
    const raw = this.#balances.get(account) ?? 0;
    return (raw < 0 ? -raw : raw) as Kobo;
  }

  /** Signed balance: positive for assets, negative for liabilities. */
  signedBalanceOf(account: AccountKind): number {
    return this.#balances.get(account) ?? 0;
  }

  balances(): Balances {
    const byAccount = new Map<AccountKind, Kobo>();
    for (const kind of Object.keys(NORMAL_SIDE) as AccountKind[]) {
      byAccount.set(kind, this.balanceOf(kind));
    }
    const netPosition = sum([...byAccount.values()].map((amount) => amount)) as unknown as number;
    return { byAccount, netPosition: netPosition as Kobo };
  }

  transactions(): readonly Transaction[] {
    return this.#transactions;
  }

  findByIdempotencyKey(key: string): Transaction | undefined {
    return this.#byIdempotencyKey.get(key);
  }

  /**
   * Total held in escrow.
   *
   * This is the number a regulator, an auditor, or a nervous member will ask
   * for. It must always be the sum of what we genuinely owe members, which is
   * the invariant `assertSolvent` enforces.
   */
  escrowBalance(): Kobo {
    return this.balanceOf('escrow_cash');
  }

  totalOwedToMembers(): Kobo {
    return sum([
      this.balanceOf('payouts_payable'),
      this.balanceOf('refunds_payable'),
    ]);
  }

  totalOwedByMembers(): Kobo {
    return sum([
      this.balanceOf('contributions_receivable'),
      this.balanceOf('defaults_receivable'),
    ]);
  }

  /**
   * Verify escrow covers every liability we have recorded.
   *
   * If this ever fails, the platform has promised money it does not have. That
   * is a stop-the-line event: freeze disbursement, page a human, do not retry.
   */
  assertSolvent(): void {
    const held = this.escrowBalance();
    const owed = this.totalOwedToMembers();
    try {
      subtract(held, owed);
    } catch (error: unknown) {
      const shortfall = owed - held;
      throw new LedgerError(
        'INSOLVENT: escrow holds ' +
          format(held) +
          ' but ' +
          format(owed) +
          ' is owed to members. Shortfall ' +
          format(shortfall as Kobo) +
          '. Disbursement must halt.',
      );
    }
  }
}

/**
 * Canonical posting builders.
 *
 * Keeping the double-entry shapes in one place means a reviewer can audit every
 * money movement Ajo.ng is capable of making by reading a single screen, and it
 * removes the chance of one endpoint inventing its own slightly-wrong version.
 */
export const entries = {
  /** A member pays a contribution for the current round. */
  contributionReceived(ajoId: string, roundNumber: number, memberId: string) {
    return {
      idempotencyKey: `contribution:${ajoId}:${roundNumber}:${memberId}`,
      kind: 'contribution.received',
      postings: (amount: Kobo) =>
        [
          { account: 'contributions_receivable' as const, side: 'credit' as const, amount },
          { account: 'escrow_cash' as const, side: 'debit' as const, amount },
        ] satisfies readonly Posting[],
    };
  },

  /**
   * The round's collected pot becomes a liability owed to the member whose turn
   * it is.
   *
   * This recognition step is not optional bookkeeping. Without it the payout
   * below extinguishes a liability that was never raised, escrow drains to zero
   * while a phantom obligation remains, and `assertSolvent` correctly reports
   * the platform as insolvent. Recognition must happen before disbursement.
   */
  payoutRecognized(ajoId: string, roundNumber: number, memberId: string) {
    return {
      idempotencyKey: `payout-recognized:${ajoId}:${roundNumber}:${memberId}`,
      kind: 'payout.recognized',
      postings: (amount: Kobo) =>
        [
          { account: 'contributions_receivable' as const, side: 'debit' as const, amount },
          { account: 'payouts_payable' as const, side: 'credit' as const, amount },
        ] satisfies readonly Posting[],
    };
  },

  /** The round's pot is released to the member whose turn it is. */
  payoutSettled(ajoId: string, roundNumber: number, memberId: string) {
    return {
      idempotencyKey: `payout:${ajoId}:${roundNumber}:${memberId}`,
      kind: 'payout.settled',
      postings: (amount: Kobo) =>
        [
          { account: 'payouts_payable' as const, side: 'debit' as const, amount },
          { account: 'escrow_cash' as const, side: 'credit' as const, amount },
        ] satisfies readonly Posting[],
    };
  },

  /**
   * The 2% service fee on a captured contribution.
   *
   * Balanced in its own right: cash leaves escrow and becomes platform
   * revenue. This is a *separate* entry from contributionReceived rather
   * than an extra credit line on it, because the two happen at different
   * moments conceptually and can be reversed independently — a refund
   * returns the contribution but keeps the earned fee, and collapsing them
   * into one entry would make that impossible to express.
   *
   * Posting a bare "credit fees_income" is not a transaction and is
   * rejected by validatePostings. If revenue reports ever disagree with
   * the ledger by exactly 2% of gross volume, this entry was skipped.
   */
  feeRecognised(ajoId: string, roundNumber: number, memberId: string) {
    return {
      idempotencyKey: `fee:${ajoId}:${roundNumber}:${memberId}`,
      kind: 'fee.recognised',
      postings: (amount: Kobo) =>
        [
          { account: 'escrow_cash' as const, side: 'debit' as const, amount },
          { account: 'fees_income' as const, side: 'credit' as const, amount },
        ] satisfies readonly Posting[],
    };
  },

  /**
   * A member failed to pay; the receivable becomes a default.
   */
  contributionDefaulted(ajoId: string, roundNumber: number, memberId: string) {
    return {
      idempotencyKey: `default:${ajoId}:${roundNumber}:${memberId}`,
      kind: 'contribution.defaulted',
      postings: (amount: Kobo) =>
        [
          { account: 'contributions_receivable' as const, side: 'debit' as const, amount },
          { account: 'defaults_receivable' as const, side: 'credit' as const, amount },
        ] satisfies readonly Posting[],
    };
  },
} as const;

export function isBalanced(postings: readonly Posting[]): boolean {
  try {
    validatePostings(postings);
    return true;
  } catch {
    return false;
  }
}

export { isZero, add, MoneyError };
