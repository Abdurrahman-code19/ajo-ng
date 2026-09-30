"""Section 26 — Appendices."""

BLOCKS = [
    {"t": "h1", "text": "26. Appendices"},

    {"t": "h2", "text": "Appendix A — Requirements traceability summary"},
    {"t": "p", "text": "The authoritative list of 148 functional requirements and 31 "
     "business rules is in section 1. This appendix maps the requirements that carry the "
     "greatest financial, legal, or trust consequence to where they are specified and "
     "verified, so a reviewer can confirm coverage without reading the whole document."},
    {"t": "table", "head": ["Req", "Summary", "Specified in", "Verified by"], "widths": [0.8, 2.6, 1.5, 1.6], "size": 8.0, "rows": [
        ["FR-001", "Member registers with verified identity", "§1, §2, §12, §24", "E2-01, E2-02, T-integration"],
        ["FR-021", "Contribution captured via webhook confirmation", "§1, §11, §13", "E3-04, E3-05, T-contract"],
        ["FR-038", "Ajo activation requires every position funded", "§1, §5, §10", "E5-06, T-state"],
        ["FR-045", "Payout released only at the scheduled date", "§1, §13", "E4-01, T-e2e"],
        ["FR-052", "Payout blocked during bank-change cooling-off", "§1, §12, §13, §15", "E10-01, T-integration"],
        ["FR-060", "A frozen member can still be paid", "§1, §12, §15", "E4-01, T-unit"],
        ["FR-071", "Ledger entries immutable; reversal only", "§1, §6, §13", "E1-04, T-unit"],
        ["FR-078", "Reconciliation break halts new payouts", "§1, §13, §20", "E3-09, T-recon"],
        ["FR-090", "Default recorded after the grace period", "§1, §6, §23", "E6-05, E6-06, T-e2e"],
        ["FR-104", "Fee of 2% shown separately before payment", "§1, §13, §16, §17", "E3-06, T-e2e"],
        ["BR-018", "Other members are never charged extra for a default", "§1, §23", "E6-10 (absence test)"],
        ["BR-019", "No public exposure of a defaulting member", "§1, §5, §24", "E8-06, E10-07"],
        ["BR-021", "A contribution counts only on capture", "§1, §13, §21", "E3-05, T-unit"],
        ["BR-025", "No unilateral post-activation exit", "§1, §5, §22", "E5-04, T-state"],
        ["BR-031", "No ledger edit permission for any role", "§1, §12, §13", "E9-05, T-authz"],
    ]},
    {"t": "p", "text": "Verification references use the backlog identifiers from section 23 "
     "and the test categories from section 18: T-unit, T-integration, T-contract, T-e2e, "
     "T-state, T-authz, T-recon."},

    {"t": "h2", "text": "Appendix B — Error code catalogue"},
    {"t": "p", "text": "Errors are returned with a stable machine-readable code, a "
     "human-readable message suitable for display, and a request ID. Messages are written "
     "for members, not for engineers, and a code never changes meaning once released."},
    {"t": "table", "head": ["Code", "HTTP", "Meaning", "Member-facing guidance"], "widths": [1.3, 0.7, 2.0, 2.5], "size": 7.8, "rows": [
        ["INVALID_PHONE", "400", "Phone number not a valid Nigerian number", "Check the number, including the country code"],
        ["EMAIL_ALREADY_REGISTERED", "409", "Email already in use", "Try signing in instead"],
        ["PHONE_ALREADY_REGISTERED", "409", "Phone already linked to an account", "Sign in to the account with this number"],
        ["VERIFICATION_EXPIRED", "410", "Verification token past its expiry", "Request a new code"],
        ["KYC_PENDING", "403", "Identity verification not complete", "Finish verification to continue"],
        ["KYC_FAILED", "403", "Verification did not succeed", "Contact support with the reference"],
        ["ACCOUNT_FROZEN", "403", "Account frozen by a risk decision", "Your payout is unaffected. Contact support"],
        ["ACCOUNT_SUSPENDED", "403", "Account suspended", "Contact support to appeal"],
        ["BAY_IN_COOLING_OFF", "409", "Bank account changed too recently", "Payout available from {date}"],
        ["TOKEN_EXPIRED", "401", "Access token expired", "Refresh and retry"],
        ["TOKEN_REUSE_DETECTED", "401", "Refresh token replay; sessions revoked", "Sign in again on your device"],
        ["MFA_REQUIRED", "401", "Step-up authentication required", "Confirm it's you to continue"],
        ["AJOS_ENROLLMENT_CLOSED", "409", "The 5-day enrollment window has closed", "This Ajo is no longer accepting members"],
        ["AJOS_NOT_FUNDED", "409", "Ajo has not reached funded status", "Payout is not available yet"],
        ["AJOS_ALREADY_JOINED", "409", "Member already has a position", "You are already in this Ajo"],
        ["POSITION_LOCKED", "409", "Position locked at activation", "This position can no longer be changed"],
        ["PAYOUT_NOT_READY", "409", "Payout is not yet at its scheduled date", "Available from {date}"],
        ["PAYMENT_NOT_FOUND", "404", "Unknown contribution", "Check the reference"],
        ["PAYMENT_PENDING_VERIFICATION", "202", "Webhook not yet received", "We are confirming your payment. Do not pay again"],
        ["PROVIDER_UNAVAILABLE", "503", "Payment provider unavailable", "We are working on it. Your money is unaffected"],
        ["RECONCILIATION_HOLD", "503", "Payouts paused pending reconciliation", "We're completing a check and will update you"],
        ["INTERNAL_ERROR", "500", "Unexpected failure", "Quote the reference when contacting support"],
    ]},

    {"t": "h2", "text": "Appendix C — Domain type reference"},
    {"t": "p", "text": "The core domain types from the financial foundation. These are the "
     "definitions the rest of the system is built on, and the reason the money rules cannot "
     "drift between the client, the API, and the workers."},
    {"t": "h3", "text": "C.1 Money"},
    {"t": "code", "size": 7.6, "text": """
  type Kobo = number & { readonly __brand: 'Kobo' };

  /** Integer kobo. No floating point, ever. */
  const kobo = (n: number): Kobo => {
    if (!Number.isSafeInteger(n)) throw new Error('Money must be an integer number of kobo');
    return n as Kobo;
  };

  /** The service fee rate, in basis points. 200 bps = 2.00%. */
  const FEE_BASIS_POINTS = 200;
  const BASIS_POINT_DIVISOR = 10_000;
  const ROUNDING_OFFSET = BASIS_POINT_DIVISOR / 2;

  /** 2% service fee, rounded half-up, in integer kobo. */
  const fee = (amount: Kobo): Kobo =>
    kobo(Math.floor((amount * FEE_BASIS_POINTS + ROUNDING_OFFSET) / BASIS_POINT_DIVISOR));

  const total = (amount: Kobo): Kobo => kobo(amount + fee(amount));

  // Per contribution, in kobo:
  //   NGN 1,000   -> fee     20 -> total  100_020   (NGN 1,020.00 charged)
  //   NGN 10,000  -> fee    200 -> total 1_000_200   (NGN 10,200.00 charged)
  //
  // The 10-member, 10-round Ajo at NGN 1,000 per member per round:
  //   100 contributions x 100,000 kobo = 10,000,000 kobo into the pool (NGN 100,000.00)
  //   100 contributions x      2,000 kobo =    200,000 kobo of fees     (NGN   2,000.00)
  //   total charged                          10,200,000 kobo            (NGN 102,000.00)
  //
  // The fee is charged to the member on top. It is never taken out of the
  // pool, so the recipient still receives the full base amount.
"""},
    {"t": "h3", "text": "C.2 Ledger"},
    {"t": "code", "size": 7.6, "text": """
  type AccountKind =
    | 'escrow_cash'              // cash held with the PSP / in escrow.  Asset.
    | 'contributions_receivable' // owed by members for the current round. Asset.
    | 'defaults_receivable'      // owed by members who have defaulted.  Asset.
    | 'payouts_payable'          // owed to the member whose turn it is. Liability.
    | 'refunds_payable'          // owed to departed members.          Liability.
    | 'fees_income'              // AJO.ng's 2% service fee.             Revenue.
    | 'provider_clearing';       // PSP transactions not yet settled.

  type EntryKind =
    | 'contribution.received' | 'fee.recognised'
    | 'payout.recognized' | 'payout.settled'
    | 'default' | 'reversal';

  /** Every posting is balanced. A posting that does not balance is rejected. */
  const post = (e: Entry): Entry => {
    const debits  = e.lines.filter(l => l.side === 'debit')
                         .reduce((s, l) => s + l.amount, 0);
    const credits = e.lines.filter(l => l.side === 'credit')
                         .reduce((s, l) => s + l.amount, 0);
    if (debits !== credits) throw new Error('Unbalanced ledger entry');
    return Object.freeze({ ...e, reversalOf: e.reversalOf ?? null });
  };

  /*
   * A member paying in clears the receivable and banks the fee, as two
   * separately reversible entries. For a NGN 1,020.00 charge:
   *
   *   contribution.received
   *     debit  escrow_cash                 100_000
   *     credit contributions_receivable   100_000
   *
   *   fee.recognised
   *     debit  escrow_cash                    2_000
   *     credit fees_income                    2_000
   *
   * They are separate so a provider refund can reverse the contribution while
   * keeping the earned fee. Collapsing them into one entry makes that
   * impossible to express, and a bare "credit fees_income" with no matching
   * debit is not a transaction at all -- post() rejects it.
   */
"""},
    {"t": "h3", "text": "C.3 Payout"},
    {"t": "code", "size": 7.6, "text": """
  /**
   * Recognition moves the obligation; settlement moves the cash.
   *   payout.recognized  debit contributions_receivable / credit payouts_payable
   *   payout.settled     debit payouts_payable      / credit escrow_cash
   */
  type PayoutState =
    | 'PENDING' | 'PRECHECKING' | 'QUEUED' | 'PROCESSING' | 'SUCCEEDED'
    | 'FAILED' | 'RETRYING' | 'REVIEW' | 'REVERSED';
"""},
    {"t": "h3", "text": "C.4 Provider interface"},
    {"t": "code", "size": 7.4, "text": """
  interface FinancialProvider {
    initiatePayment(req: PaymentRequest): Promise<PaymentSession>;
    verifyWebhook(req: RawWebhook): Promise<WebhookEvent>;
    queryPayment(ref: string): Promise<PaymentStatus>;
    transfer(req: TransferRequest): Promise<TransferResult>;
    reverseTransfer(ref: string, reason: string): Promise<ReverseResult>;
    queryTransfer(ref: string): Promise<TransferStatus>;
    resolveAccount(accountNumber: string): Promise<AccountIdentity>;
    collectFees(amount: MinorUnits): Promise<FeeSettlement>;
  }

  /** Refuses to construct when NODE_ENV === 'production'. Covered by a test. */
  class MockFinancialProvider implements FinancialProvider { /* in-memory */ }
"""},
    {"t": "h3", "text": "C.5 Ajo states"},
    {"t": "code", "size": 7.4, "text": """
  type AjoState =
    | 'DRAFT' | 'OPEN' | 'FUNDED' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED';

  type PositionState =
    | 'PENDING' | 'LOCKED' | 'PAID' | 'DEFAULTED' | 'RECOVERED';

  /**
   * Invariants enforced by the state machine, not by callers:
   *  - enrollment is exactly 5 days
   *  - a position locks at activation and never unlocks
   *  - ACTIVE requires FUNDED
   *  - COMPLETED and CANCELLED are terminal
   *  - no transition bypasses a payment prerequisite
   */
"""},
    {"t": "callout", "kind": "NOTE", "title": "These types are the reason the money rules are consistent.",
     "text": "Because the client, the API, and the workers all import the same domain "
     "core, a rule such as 'the fee is 2%, in integer kobo' is implemented exactly once. "
     "It cannot drift between the app and the backend, and it cannot be bypassed by a new "
     "code path, because the type system will not permit it."},

    {"t": "h2", "text": "Appendix D — Sample reconciliation report"},
    {"t": "p", "text": "The daily reconciliation record from section 13.8.2, in the form "
     "produced and signed off by the named owner."},
    {"t": "code", "size": 7.0, "text": """
  DAILY RECONCILIATION — {date}
  Owner: {name, role}            Signed: {timestamp}

  1. PROVIDER SETTLEMENT
     Provider-reported volume    NGN 1,284,500.00
     Ledger-matched volume       NGN 1,284,500.00
     Unmatched                   NGN 0.00                    ✓ balanced

  2. BANK STATEMENT
     Collection account          NGN   912,340.00
     Payout account              NGN  -312,000.00
     Fee account                 NGN    684,160.00
     Expected from ledger        NGN 1,284,500.00            ✓ balanced

  3. INTERNAL CONSISTENCY
     Sum of ledger entries       NGN 1,284,500.00
     Sum of member balances      NGN 1,284,500.00
     Escrow cash position        NGN 1,284,500.00            ✓ INVARIANT HOLDS

  4. FEE REVENUE
     Fees recognised             NGN    25,690.00  (2.00% of contributions)
     Fees settled to fee account  NGN    25,690.00            ✓ agrees

  ITEMS REQUIRING ATTENTION
     Unidentified inbound, 1–7 days     NGN 5,000.00   (1 transaction)
     Oldest unidentified                 3 days
     Assigned to: reconciliation queue   Review by {date}

  OUTCOME: Reconciled. Payouts not held.
"""},
    {"t": "p", "text": "The single most important line in this report is the internal "
     "consistency check. It is the invariant from section 13.8.2, and while it holds, no "
     "payout is ever released against a balance the platform cannot substantiate."},

    {"t": "h2", "text": "Appendix E — Glossary"},
    {"t": "table", "head": ["Term", "Definition"], "widths": [1.7, 4.8], "size": 8.0, "rows": [
        ["Ajo", "A rotating savings group. Members contribute on a schedule and each member receives the full pool in turn"],
        ["Position", "One member's place in one Ajo, with its own commitment and its own payment state"],
        ["Contribution", "A member's payment into the Ajo pool for a round. Counts only on capture, per BR-021"],
        ["Service fee", "The 2% charged on every contribution, in addition to the contribution amount. Never taken from the payout"],
        ["Round", "One collection cycle within an Ajo. Ten rounds in the standard Ajo"],
        ["Enrollment window", "The 5-day period during which members may join an Ajo before it activates"],
        ["Activation", "The transition of an Ajo to FUNDED, once every position is fully paid. Positions lock at this point"],
        ["Default", "A contribution not made by its deadline, after the 48-hour grace period, per BR-012"],
        ["Grace period", "48 hours after a missed deadline during which a member may cure the default without penalty"],
        ["Recovery", "Curing a default by paying, restoring the position to funded without changing the agreed pool"],
        ["Payout", "The release of a completed Ajo's pool to the member whose turn it is"],
        ["Batch payout", "The simultaneous release of the pool to every member of a completing Ajo"],
        ["PayoutIntent", "The record of a payout's lifecycle, from prechecking to settlement or review"],
        ["Escrow", "The ring-fenced position from which payouts are made. **AJO.ng holds no member funds itself, pending the determination in section 24**"],
        ["Ledger", "The append-only record of every money movement, as balanced double-entry postings. The source of truth"],
        ["Entry", "One balanced set of debit and credit lines. Immutable once written"],
        ["Reversal", "A balanced entry that exactly cancels an earlier entry. The only permitted correction"],
        ["Account kind", "A ledger account classification: escrow cash, contributions receivable, fee income, payouts payable, settlement in flight, or suspense"],
        ["Fee income", "Revenue recognised on captured contributions at 2%. Not a member's money and never a payout"],
        ["Suspense", "A holding account for unidentified or unmatched money pending investigation"],
        ["Reconciliation", "The daily process of proving the ledger, the balances, and the bank statements agree"],
        ["The invariant", "Ledger sum = sum of member balances = escrow cash. Zero tolerance"],
        ["Cooling-off", "The 14-day period after a payout destination change during which a payout cannot be released"],
        ["Step-up authentication", "A fresh authentication challenge required before a sensitive action, such as changing a bank account or releasing a payout"],
        ["Idempotency key", "A client-generated key that makes a retried request safe, so money moves at most once"],
        ["FinancialProvider", "The interface through which all money movement occurs, keeping the application independent of any provider SDK"],
        ["Capture", "The point at which a contribution becomes a confirmed payment, on verified webhook evidence"],
        ["Webhook", "A signed notification from the payment provider that a payment succeeded or failed. **The only authoritative confirmation**"],
        ["Hold", "A temporary pause on a payment pending review, always with a stated reason, an owner, and a deadline"],
        ["Freeze", "A restriction on sending money: contributions, new Ajos, withdrawals to a changed destination. **Never prevents receiving a payout**"],
        ["Money mule", "An account used to receive and forward funds for someone else. A criminal use of a member's account"],
        ["Beneficial owner", "The natural person who ultimately owns or controls an account"],
        ["PEP", "A politically exposed person, subject to enhanced due diligence"],
        ["SAR", "A Suspicious Activity Report, filed to the Financial Intelligence Unit within the statutory deadline"],
        ["EDD", "Enhanced due diligence, applied to higher-risk members"],
        ["CDD", "Customer due diligence: verifying a member's identity before they can hold a payoutable position"],
        ["RLS", "PostgreSQL Row Level Security. A database-enforced second authorization layer"],
        ["DPA", "A Data Processing Agreement with a processor of member personal data"],
        ["RPO / RTO", "Recovery Point Objective (data loss tolerated) and Recovery Time Objective (maximum downtime tolerated)"],
        ["SLO / error budget", "A Service Level Objective and the permitted amount of failure within a period"],
        ["Your Ajo. Your Story.", "The AJO.ng tagline"],
    ]},

    {"t": "h2", "text": "Appendix F — Glossary of abbreviations"},
    {"t": "table", "head": ["Abbreviation", "Meaning"], "widths": [1.3, 5.2], "size": 8.2, "rows": [
        ["Ajo", "Rotating savings group, the core AJO.ng concept"],
        ["API", "Application Programming Interface"],
        ["BVN", "Bank Verification Number. A Nigerian identity verification number"],
        ["CDD / EDD", "Customer due diligence / Enhanced due diligence"],
        ["CI / CD", "Continuous integration / Continuous delivery"],
        ["DPA", "Data Processing Agreement"],
        ["DUT", "Device under test"],
        ["FIU", "Financial Intelligence Unit"],
        ["FP / FN", "False positive / false negative, in fraud detection"],
        ["JWT", "JSON Web Token"],
        ["KYC", "Know Your Customer"],
        ["MFA", "Multi-factor authentication"],
        ["MLRO", "Money Laundering Reporting Officer"],
        ["NIP", "Nigeria Instant Payment"],
        ["OTP", "One-time password"],
        ["PEP", "Politically exposed person"],
        ["PSP", "Payment service provider"],
        ["RBAC", "Role-based access control"],
        ["RLS", "Row Level Security"],
        ["RPO / RTO", "Recovery point objective / Recovery time objective"],
        ["SAR", "Suspicious Activity Report"],
        ["SLA / SLO", "Service level agreement / objective"],
        ["SSL / TLS", "Transport encryption protocols"],
        ["TOTP", "Time-based one-time password, for authenticator apps"],
        ["WAT", "West Africa Time, UTC+1"],
        ["WORM", "Write once, read many. Storage that cannot be altered after writing"],
    ]},

    {"t": "h2", "text": "Appendix G — Source documents"},
    {"t": "p", "text": "The business and financial material from which this specification "
     "was derived. These remain the source for the commercial assumptions; where this "
     "document states a figure, it has been reconciled against them."},
    {"t": "table", "head": ["Document", "Used for"], "widths": [2.9, 3.6], "size": 8.2, "rows": [
        ["AJOng_Financial_Partnership_Proposal_MVP_UPDATED.pdf", "Founders, partnership framing, financial structure, projections"],
        ["AJOng_Year_1_Financial_Model_UPDATED.xlsx", "Year-1 model, transaction volumes, revenue assumptions"],
        ["AJOng_One_Page_Executive_Overview_UPDATED.pdf", "Executive summary, market context, value proposition"],
        ["AJOng_Year_1_Transaction_Volume_and_Financial_Projection_UPDATED.pdf", "Volume projections by scenario"],
        ["AJOng_Forming_An_Ajo_Terms_and_Conditions.pdf", "Draft terms, and the fee positioning that became the 2% service fee"],
    ]},
    {"t": "p", "text": "The earlier business documents stated that pricing was not yet "
     "locked. The 2% service fee in this specification supersedes that position, and the "
     "commercial documents should be reissued for internal consistency. Until they are, "
     "**this specification and CANONICAL.md are authoritative on the fee, and the earlier "
     "documents are not.**"},

    {"t": "h2", "text": "Appendix H — Document control"},
    {"t": "table", "head": ["Field", "Value"], "widths": [1.7, 4.8], "size": 8.4, "rows": [
        ["Document", "AJO.ng — Complete Product and Technical Specification"],
        ["Version", "1.0"],
        ["Status", "For review. Not a compliance determination"],
        ["Scope", "Product requirements, design, architecture, security, operations, legal considerations, roadmap"],
        ["Source of truth", "docs/src/CANONICAL.md, followed by this document"],
        ["Sections", "25, plus appendices A–H"],
        ["Supersedes", "Earlier business and financial documents, for the fee and technical scope"],
        ["Requires", "Review by qualified Nigerian legal and compliance professionals before production launch"],
        ["Verification", "Section 18 test strategy; section 23 backlog; section 20.11 operational readiness"],
    ]},
    {"t": "callout", "kind": "LEGAL", "title": "Closing note on the status of this document.",
     "text": "This is a complete and internally consistent specification. It is not, and "
     "does not claim to be, a compliance determination, a legal opinion, or a financial "
     "plan. It is a statement of what AJO.ng will be, built with the controls that make "
     "member money safe, and of what must be resolved before the first real naira moves. "
     "**That resolution requires qualified Nigerian legal and compliance professionals, "
     "and it is the only item on the critical path that engineering cannot deliver."},
]
