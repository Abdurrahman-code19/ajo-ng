"""Section 13 — Payments, Reconciliations and Operations."""

BLOCKS = [
    {"t": "h1", "text": "13. Payments, Reconciliation and Operations"},

    {"t": "lead", "text": "This is the section that determines whether AJO.ng is a "
     "fintech or a group-chat app with a payment button. Every rule here is written on "
     "the assumption that money may fail in transit, arrive late, arrive twice, or "
     "arrive from someone we cannot identify. The system must be correct in all of those "
     "cases, not merely in the happy path."},

    {"t": "h2", "text": "13.1 Principles"},
    {"t": "numbers", "items": [
        "**Money movement is not a side effect of a business rule; it is the business rule.** No payout is considered issued until the ledger records it, regardless of what a provider API returned.",
        "**The ledger is the source of truth.** Provider balances, bank statements and internal balances are reconciled against it, never the other way round.",
        "**Every kobo has an owner.** Segregated client-money accounts only. A member's balance is a claim on a ring-fenced ledger position, not a number in a database column that can drift.",
        "**Idempotency is mandatory.** Every money-mutating endpoint accepts a client-generated idempotency key. A retry must never move money twice.",
        "**Reversal, not correction.** A mistake is fixed by posting a reversing entry. No ledger row is ever updated or deleted.",
        "**Reconciliation is a first-class, continuous, automated process** with a named human owner and a hard daily deadline.",
    ]},

    {"t": "h2", "text": "13.2 Account and money structure"},
    {"t": "p", "text": "AJO.ng must be structured as an agent or partner arrangement "
     "with the payment provider or licensed partner, with collection accounts and payout "
     "accounts clearly distinct. Whether that constitutes custody of client funds is a "
     "**legal question that must be resolved before launch, and this document does not "
     "resolve it.** What follows describes the operational shape, subject to that "
     "determination."},
    {"t": "bullets", "items": [
        "**Collection accounts** — receive member contributions. One or more, with a separate account for the 2% fee so fee revenue is never commingled with client money.",
        "**Payout account** — the single account from which member payouts are sent.",
        "**Operating account** — platform costs, refunds, and revenue. Never debited for client obligations.",
        "**Reconciliation account** — holds unidentified or unmatched inbound payments pending investigation.",
        "Every account has a named purpose, a documented daily reconciliation owner, and a documented escalation path.",
    ]},
    {"t": "callout", "kind": "WARNING", "title": "No account may be used for two purposes.",
     "text": "The most common cause of a reconciliation failure in a young fintech is a "
     "single account that receives both contributions and something else — a top-up, a "
     "refund, a transfer between Ajos. Once that happens, attributing an inbound payment "
     "to a specific Ajo member becomes guesswork, and the platform's own numbers become "
     "unreliable. Separate accounts by purpose from day one, even if it means more "
     "statements to reconcile."},

    {"t": "h2", "text": "13.3 The contribution flow"},
    {"t": "h3", "text": "13.3.1 Sequence"},
    {"t": "p", "text": "Two different things are happening here and they must not be "
     "confused. The **payment provider** has a genuine two-phase lifecycle — an "
     "initiation that is *pending* and a capture that is *confirmed by webhook*. "
     "The **ledger**, by contrast, records only money that has actually arrived. "
     "A pending authorization is not a receipt, so it produces no balanced entry; "
     "it produces a payment record in `PENDING` state and nothing else."},
    {"t": "code", "size": 7.6, "text": """
  member            API              payment record    PSP
    │                 │                  │              │
    │ choose Ajo      │                  │              │
    │────────────────▶│                  │              │
    │                 │ confirm amount   │              │
    │                 │ = base + 2% fee  │              │
    │                 │ + idempotency key│              │
    │◀─ amount shown ──│                  │              │
    │                 │                  │              │
    │ payment sheet / │ create record    │              │
    │ transfer        │ status PENDING   │              │
    │────────────────▶│─────────────────▶│ initiate      │
    │                 │                  │─────────────▶│
    │                 │◀─ redirect or transfer instructions ────│
    │                 │                  │              │
    │   (member pays) │                  │              │
    │─────────────────────────── webhook: success or failure
    │                 │                  │◀─────────────│
    │                 │ verify signature │              │
    │                 │ match reference   │              │
    │                 │ and amount       │              │
    │                 │                  │              │
    │                 │   ┌──────────────────────────────────┐
    │                 │   │ LEDGER — only on confirmed capture │
    │                 │   │                                  │
    │                 │   │ contribution.received             │
    │                 │   │   debit  escrow_cash            100_000
    │                 │   │   credit contributions_receivable 100_000
    │                 │   │                                  │
    │                 │   │ fee.recognised                   │
    │                 │   │   debit  escrow_cash                2_000
    │                 │   │   credit fees_income                2_000
    │                 │   │                                  │
    │                 │   │ position in the Ajo is now funded  │
    │                 │   └──────────────────────────────────┘
    │◀─ confirmation ──│ notify member, update position    │
"""},
    {"t": "p", "text": "The two entries are each balanced on their own, which is what the "
     "ledger requires. They are posted separately, rather than as one entry with two "
     "credit lines, so that a provider refund can reverse the member's contribution "
     "while leaving the earned fee intact. Collapsing them into a single posting makes "
     "that outcome impossible to express."},
    {"t": "p", "text": "Only after capture is a member's position in the Ajo considered "
     "funded. A member who abandons the payment sheet leaves a record in `PENDING`, not "
     "a position in `PAID`, and a webhook that never arrives leaves the same state "
     "until the reconciliation job resolves it — which is why an unmatched payment is "
     "an operational alert in section 13.8 rather than a silent timeout."},

    {"t": "h3", "text": "13.3.2 Fee calculation"},
    {"t": "code", "size": 7.6, "text": """
  contribution_kobo = 100_000            // NGN 1,000
  fee_kobo          = 2_000              // 2% = NGN 20
  amount_charged   = 102_000            // NGN 1,020
  recipient receives the base pool only: 1,000,000 kobo for NGN 10,000

  Integer arithmetic only. fee_kobo = contribution_kobo * 2 / 100,
  computed in kobo as a rounded integer, never in floating point.
"""},
    {"t": "table", "head": ["Base contribution", "Fee (2%)", "Total charged", "Recipient pool (base)", "Platform margin"], "widths": [1.6, 1.2, 1.4, 1.9, 1.5], "size": 8.4, "rows": [
        ["NGN 1,000", "NGN 20", "NGN 1,020", "NGN 10,000", "0.20%"],
        ["NGN 2,500", "NGN 50", "NGN 2,550", "NGN 10,000", "0.50%"],
        ["NGN 5,000", "NGN 100", "NGN 5,100", "NGN 10,000", "1.00%"],
        ["NGN 10,000", "NGN 200", "NGN 10,200", "NGN 10,000", "2.00%"],
        ["NGN 20,000", "NGN 400", "NGN 20,400", "NGN 10,000", "4.00%"],
        ["NGN 50,000", "NGN 1,000", "NGN 51,000", "NGN 10,000", "10.00%"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "The margin rises steeply on small contributions.",
     "text": "At a NGN 1,000 contribution AJO.ng earns 20% of the *contribution* as "
     "margin. At NGN 50,000 it earns 2%. This is a deliberate product constraint: AJO "
     "groups are cash-flow products for people who save in small amounts, and the fee is "
     "readable and predictable at that scale — NGN 20, not 0.4% of something. It also "
     "means **the fee must never be described as a percentage of what the member "
     "receives**, because that framing inverts the relationship and confuses members badly."},

    {"t": "h3", "text": "13.3.3 Payment initiation, by rail"},
    {"t": "table", "head": ["Rail", "Instruments", "Typical use", "Settlement", "Considerations"], "widths": [1.2, 1.7, 1.6, 1.2, 1.8], "size": 8.0, "rows": [
        ["Card (via provider)", "Verve, Mastercard, Visa", "Members without a funded bank account", "Instant to T+1", "3-D Secure on desktop; 3DS exemptions and friction are a real conversion risk"],
        ["Bank transfer", "Transfer by NIP, USSD, bank app", "Primary rail; members already trust their own bank", "Typically same-day", "Requires the member to leave the app; transfer-reference matching must be reliable"],
        ["Mobile money", "MTN MoMo, Airtel Money", "Widely used; valuable for unbanked and unbanked-adjacent members", "Instant", "Wallet limits vary by provider and by regulation; must be handled and displayed"],
        ["USSD", "Provider-driven code", "Feature-phone fallback", "Instant", "No app required — a deliberate inclusion decision, not an afterthought"],
        ["Card funded via bank (Pay by Bank)", "Card linked to a bank account", "Card-unavailable members", "T+1", "Adds a network call; failure modes must be reported plainly"],
    ]},
    {"t": "p", "text": "The exact instrument set supported at launch depends entirely on "
     "the **ProvidusUnity** capabilities that can be verified during technical due "
     "diligence. That verification has not been performed, so this table states "
     "requirements, not commitments. What is non-negotiable is that at least one rail "
     "works end to end before any member is asked to pay."},

    {"t": "h2", "text": "13.4 Provider abstraction and adapters"},
    {"t": "p", "text": "AJO.ng integrates with money movement exclusively through the "
     "`FinancialProvider` interface defined in CANONICAL.md §5.7. No application code "
     "imports a provider SDK directly. This is what allows the platform to add or replace "
     "a provider, and to run the entire test suite with no network at all."},
    {"t": "code", "size": 7.6, "text": """
  interface FinancialProvider {
    // inbound
    initiatePayment(req: PaymentRequest): Promise<PaymentSession>
    verifyWebhook(req: RawWebhook): Promise<WebhookEvent>   // signature + schema
    queryPayment(ref: string): Promise<PaymentStatus>        // reconciliation aid

    // outbound
    transfer(req: TransferRequest): Promise<TransferResult>  // idempotent, by mandate
    reverseTransfer(ref: string, reason: string): Promise<ReverseResult>
    queryTransfer(ref: string): Promise<TransferStatus>

    // account
    resolveAccount(accountNumber: string): Promise<AccountIdentity>
    collectFees(amount: MinorUnits): Promise<FeeSettlement>
  }
"""},
    {"t": "h3", "text": "13.4.1 Adapter implementations"},
    {"t": "bullets", "items": [
        "`MockFinancialProvider` — in-memory, deterministic, and **refuses to construct in a production environment**. It is the only provider permitted in automated tests.",
        "`ProvidusFinancialProvider` — a future adapter, to be written after a verified sandbox specification. It is not written in this document because an adapter written against a guessed API is worse than no adapter at all.",
        "Every adapter is covered by the **same contract test suite**, so a provider swap cannot silently change behaviour that the business logic depends on.",
    ]},

    {"t": "h2", "text": "13.5 Webhooks: the primary channel of truth"},
    {"t": "p", "text": "For card, transfer and wallet payments, the provider's webhook is "
     "the event that tells AJO.ng money arrived. It must be treated as hostile input."},
    {"t": "table", "head": ["Requirement", "Rule"], "widths": [1.7, 4.8], "size": 8.4, "rows": [
        ["Signature verification", "HMAC-SHA256 over the **raw** request body using a per-environment secret, compared with a constant-time function. Parse JSON only after verification"],
        ["Replay protection", "Reject any event whose timestamp is more than 5 minutes old, and any `event_id` already processed"],
        ["Idempotent handling", "`provider_event_id` is uniquely indexed. A duplicate delivery is acknowledged and dropped, not reprocessed"],
        ["Fast acknowledgement", "Verify, persist to a queue, return 2xx. Business processing happens asynchronously. A slow webhook handler causes provider retries and duplicate risk"],
        ["Unknown event types", "Acknowledged, logged, and ignored — never a 4xx, and never a crash"],
        ["Amount and reference check", "The received amount, currency, and reference must match the pending contribution. A mismatch is escalated to reconciliation, not silently accepted"],
        ["Out-of-order delivery", "A success arriving after a failure for the same reference is resolved by the terminal state, not by arrival order"],
        ["Durability", "Unprocessed webhooks are retained for 90 days and replayable, so a processing outage is recoverable"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "Never trust a redirect.",
     "text": "A browser returning from a payment page is a hint, not evidence. It may be "
     "forged, replayed, or simply never happen if the member closes the tab. Only the "
     "verified webhook, or a server-side status query, may mark a contribution paid. The "
     "UI must be able to show *pending verification* indefinitely without ever telling a "
     "member their money is safe when it is not."},

    {"t": "h2", "text": "13.6 Payouts"},
    {"t": "h3", "text": "13.6.1 Preconditions — all must hold"},
    {"t": "numbers", "items": [
        "The Ajo is `FUNDED` — every active position is fully paid up to the current round.",
        "The Ajo's `ready_at` has arrived. A payout is never available early, even by a minute, even for the organizer.",
        "The recipient is `ACTIVE` or in a non-blocking state. Per CANONICAL.md §2.6, a `FROZEN`, `SUSPENDED` or `DORMANT` member **can still be paid**. This is not negotiable and must be implemented as an explicit exception to the freeze check, with the reason recorded.",
        "The recipient's bank account has been verified by the provider and has not changed inside the standing cooling-off period (14 days; see 12.8).",
        "The escrow account holds the full amount, as verified against the ledger — not against an internal cache.",
        "No open fraud investigation on the payout itself. A member-level freeze does not block their own payout.",
    ]},
    {"t": "h3", "text": "13.6.2 Sequence"},
    {"t": "code", "size": 7.6, "text": """
  organizer (or automatic, at ready_at)
        │
        ▼
  PayoutIntent created ──▶ PRECHECKING ──funds verified──▶ QUEUED
                                                            │
                             ┌──────────────────────────────┘
                             ▼
                          PROCESSING ──▶ provider transfer initiated
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
    SUCCEEDED             FAILED              (timeout → UNKNOWN → query)
        │                    │
        │                    ▼
        │             RETRYING (exponential backoff, then HUMAN_REVIEW)
        │
        ▼
  payout.recognized  debit contributions_receivable / credit payouts_payable
  payout.settled     debit payouts_payable      / credit escrow_cash
  position → PAID
  member notified
  Ajo → COMPLETED when all positions are PAID
"""},
    {"t": "p", "text": "The two ledger entries in the success path are the whole "
     "accounting of a payout. Recognising it moves the obligation from *what the member "
     "is owed* to *what the platform owes the member*; settling it moves the cash. "
     "Splitting the two is what makes it possible to answer, at any moment, the question "
     "the regulator or an auditor will ask: *how much do you owe your members right now?*"},

    {"t": "h3", "text": "13.6.3 Batch payouts"},
    {"t": "p", "text": "A mature Ajo completes in a single event affecting every member, "
     "so payouts are released as one batch rather than member by member. The batch is the "
     "atomicity boundary: either the batch is authorised and dispatched, or it is not. "
     "Per-item outcomes are recorded individually, because a batch of 10 will sometimes "
     "succeed 10 times, 9 times, or 8 times, and each of those is a distinct state that a "
     "member and a reconciler both need to see."},
    {"t": "table", "head": ["Batch field", "Value"], "widths": [1.9, 4.6], "size": 8.4, "rows": [
        ["Batch reference", "AJO-{ajoId}-R{round}-{payoutId}, unique and human-readable"],
        ["Settlement account", "The single payout account; one batch, one debit, many credits"],
        ["Per-item status", "Each payout carries its own state, provider reference, and failure reason"],
        ["Partial failure handling", "Successful items are settled and notified immediately. Failed items move to retry or human review. No retry is ever automatic after 3 attempts"],
        ["Cut-off", "Batch dispatch is rate-limited and capped per day to stay within provider and bank limits — the cap must be configurable, not hard-coded"],
        ["Reconciliation", "The batch debit is matched to the sum of successful items on the same day. Any difference is an exception, same-day"],
    ]},

    {"t": "h2", "text": "13.7 Refunds and reversals"},
    {"t": "table", "head": ["Scenario", "Action", "Ledger treatment"], "widths": [1.7, 2.3, 2.5], "size": 8.4, "rows": [
        ["Duplicate contribution capture", "Full refund of one instance", "Reverse the original capture entry. The valid contribution is untouched"],
        ["Contributed to the wrong Ajo", "Refund after confirmation, or transfer if the member chooses", "Reverse and re-record against the correct Ajo; the two entries reference each other"],
        ["Captured, then position removed pre-activation", "Refund + the 2% fee is not refunded, as it is a completed service", "Reverse gross contribution; retain fee as realised revenue"],
        ["Payout failed at the bank", "Retry, then reverse the settlement if permanently failed", "Reverse payout.settled; the obligation returns to contributions_receivable"],
        ["Ajo cancelled before activation", "Refund every contribution in full", "Each contribution reversed individually; the fee is retained as revenue for a service never delivered — **this must be reviewed by counsel**"],
        ["Fraudulent contribution", "Recovery action, not a customer refund", "Write off via a documented loss-provision entry, not by deleting the capture"],
        ["Member over-contributed in error", "Refund the excess, or offer an Ajo credit", "Member's choice. Never silently retain or silently absorb it"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Refund is a product capability, not an exception.",
     "text": "AJO.ng must be able to refund a member quickly and without escalation for the "
     "ordinary mistakes. A platform that makes a member open a ticket to recover their own "
     "money has already lost their trust, and refunds are cheap while the money is small. "
     "The right posture is: automatic for small amounts, fast human review for large ones, "
     "and a published maximum SLA."},

    {"t": "h2", "text": "13.8 Reconciliation"},
    {"t": "h3", "text": "13.8.1 Why it is non-negotiable"},
    {"t": "p", "text": "Reconciliation is the discipline that makes the platform's numbers "
     "true. Without it, AJO.ng is a business whose financial position is a guess — and in "
     "a regulated-adjacent product that is a governance failure, not an accounting "
     "detail. Three reconciliations run every day, and all three have a named owner and a "
     "completion deadline."},

    {"t": "h3", "text": "13.8.2 Daily procedures"},
    {"t": "table", "head": ["Procedure", "Compares", "Deadline", "On mismatch"], "widths": [1.6, 2.3, 0.9, 1.7], "size": 8.0, "rows": [
        ["Provider settlement", "Provider's settlement report ↔ ledger entries with provider references", "10:00 WAT", "Auto-ticket to reconciliation; investigate before 14:00"],
        ["Bank statement", "Collection + payout bank accounts ↔ ledger", "10:00 WAT", "Same-day investigation"],
        ["Internal consistency", "Sum of ledger ↔ member balances ↔ Ajo positions ↔ escrow balance", "On every deploy and nightly", "Halt new payouts automatically. Never reconcile by adjusting a balance column"],
        ["Fee revenue", "Sum of fee entries ↔ revenue recognised in the management accounts", "Monthly close", "Finance escalation"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "The invariant: ledger sum = sum of member balances = escrow cash.",
     "text": "This identity must hold at all times, and it is checked automatically and "
     "continuously, not at month end. If it ever fails, the platform **stops releasing new "
     "payouts** and a P1 incident is raised. Payouts continuing while the books do not "
     "balance converts an accounting problem into a solvency problem."},

    {"t": "h3", "text": "13.8.4 Unmatched and unidentified money"},
    {"t": "table", "head": ["Age", "Action", "Owner"], "widths": [1.2, 3.6, 1.7], "size": 8.4, "rows": [
        ["< 24 hours", "Automatic attempt to match by reference, amount and time. Expected during outages", "System"],
        ["1–7 days", "Manual review. Possible causes: member used a stale reference, or a bank transfer description was edited", "Reconciliation officer"],
        ["8–30 days", "Escalated. Attempt contact with the payer. Considered for return to source", "Reconciliation + support"],
        ["> 30 days", "Escalated to risk and finance. Return to source, or recognise as unclaimed funds only with counsel's approval", "Finance lead"],
    ]},

    {"t": "h2", "text": "13.9 Reversals and corrections"},
    {"t": "p", "text": "The rule is absolute: **no ledger entry is ever updated or "
     "deleted.** A mistake is corrected by posting a reversing entry that references the "
     "original. The original stays, because the audit trail is more valuable than a clean "
     "looking table — and because a system that can silently edit history can silently "
     "hide a fraud."},
    {"t": "code", "size": 7.6, "text": """
  Posted when the capture is confirmed. Two balanced entries:

    contribution.received    debit  escrow_cash                100_000
                            credit contributions_receivable   100_000

    fee.recognised           debit  escrow_cash                  2_000
                            credit fees_income                  2_000

  Now suppose the member is refunded. Two reversing entries, each the exact
  mirror of its original:

    reversal of contribution.received
                            debit  contributions_receivable   100_000
                            credit escrow_cash                100_000

    reversal of fee.recognised
                            debit  fees_income                  2_000
                            credit escrow_cash                  2_000

  All four rows remain in the ledger, each linked to the entry it reverses.
  Escrow and the receivable are back to zero. Only the member's contribution
  was actually returned; the fee is retained as earned, and the reason both
  reversals were necessary is permanent.
"""},
    {"t": "p", "text": "A reversing entry may be posted by the system automatically for "
     "mechanical errors, or by a super admin with a mandatory written reason and a "
     "mandatory review by a second person. Manual reversal is one of the highest-risk "
     "operations in the platform and is treated as such."},

    {"t": "h2", "text": "13.10 Provider outages and degradation"},
    {"t": "table", "head": ["Failure", "Member-facing behaviour", "Internal action"], "widths": [1.6, 2.4, 2.5], "size": 8.2, "rows": [
        ["Collection rail unavailable", "Show the outage on the payment screen, before the member starts. Allow contribution for a *different* rail if one is available", "Feature-flag the rail; alert on error rate"],
        ["Webhook delivery stops", "Contributions show 'pending verification'. **Never** tell the member they have paid", "Queue inbound; poll provider status on a schedule as a backstop; raise P1 if the gap exceeds 2 hours"],
        ["Payout rail unavailable at ready_at", "Delay the payout and notify every affected member with a new expected date, before they notice", "Queue the batch; retry with backoff; never issue a partial batch silently"],
        ["Bank credit slow (T+1 expected, T+3 actual)", "Show 'sent, awaiting bank credit' with the last check time", "Reconcile; do not reverse automatically — the money is usually in flight"],
        ["Provider returns an unknown error", "Generic failure with a support reference", "Alert immediately; never auto-retry a non-idempotent operation without a reference check"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Honesty is the outage strategy.",
     "text": "A member whose payout is delayed by two days and told so in advance is a "
     "retained member. A member whose payout is delayed silently, and who discovers it by "
     "checking their bank statement, is a lost member and a public review. Every delay in "
     "this system produces a proactive notification, even when the fix is in progress."},

    {"t": "h2", "text": "13.11 Financial controls"},
    {"t": "bullets", "items": [
        "**Segregation of duties** — the person who initiates a payout is not the person who approves a large manual intervention.",
        "**Dual authorisation** — any manual ledger correction, any refund above a set threshold, and any bank-account change on a frozen account require two people.",
        "**Four-eyes on bank detail** — no change to the settlement account or payout account is possible without two independent authorisers, plus a cooling-off period and an out-of-band notification.",
        "**Daily and monthly limits** — per member, per Ajo, and platform-wide payout caps, configurable without a deploy.",
        "**Immutable provider credentials** — secrets live in a managed secret store, rotate on a schedule and on any personnel change, and are never in an environment variable committed to source.",
        "**Audit of every privileged money action** — actor, target, amount, reason, and outcome, retained per section 24.",
    ]},

    {"t": "h2", "text": "13.12 Manual and assisted operations"},
    {"t": "p", "text": "Some situations genuinely require a person: a payout the provider "
     "cannot resolve, a bank account that was closed mid-cycle, a member who has moved. "
     "AJO.ng provides a controlled console for these, not a spreadsheet and not a direct "
     "database edit."},
    {"t": "table", "head": ["Operation", "Who", "Controls"], "widths": [1.9, 1.3, 3.3], "size": 8.4, "rows": [
        ["Retry a failed payout", "Support", "Up to 3 automatic attempts first. Manual retry records the reason"],
        ["Reassign a payout destination", "Risk officer", "Step-up auth, 14-day cooling-off, notify all registered channels, dual authorisation"],
        ["Post a manual ledger correction", "Super admin", "Reversing entry only, mandatory reason, dual authorisation, automatic alert to the board"],
        ["Waive a late fee", "Finance", "Value capped. Logged, reported monthly"],
        ["Return unidentified funds", "Finance + risk", "Evidence-based; never to a destination supplied by the payer without independent verification"],
        ["Close an Ajo with a structural default", "Risk + organizer", "Structured, documented, member-notified. Never a silent write-off"],
    ]},

    {"t": "h2", "text": "13.13 Operational runbook — daily"},
    {"t": "table", "head": ["Time (WAT)", "Task", "Owner", "Output"], "widths": [1.1, 2.7, 1.3, 1.4], "size": 8.4, "rows": [
        ["08:00", "Review overnight alerts: webhook gaps, failed batches, reconciliation alarms", "On-call", "Incident log"],
        ["09:00", "Review the previous day's unmatched payments and pursue identification", "Reconciliation officer", "Aging report"],
        ["10:00", "Run and sign off the three reconciliations (13.8.2)", "Reconciliation officer", "Signed reconciliation record"],
        ["11:00", "Review the payout queue: preconditions, cooling-off holds, bank-account flags", "Payments ops", "Approved batches"],
        ["14:00", "Escalate anything from 10:00 still unmatched", "Finance lead", "Escalation"],
        ["16:00", "Review provider health, error rates, and latency against SLOs", "Engineering on-call", "SLO report"],
        ["17:00", "Publish member-impacting status: what is delayed, what is fixed, what is next", "Support + eng", "Status update"],
    ]},

    {"t": "h2", "text": "13.14 Payment-related KPIs"},
    {"t": "table", "head": ["Metric", "Definition", "Target", "Why it matters"], "widths": [1.6, 2.4, 1.1, 1.4], "size": 8.2, "rows": [
        ["Collection success rate", "Captured ÷ initiated", "≥ 97%", "The single most visible number for a member"],
        ["Time to capture", "Initiation → webhook confirmation", "< 60s for card/wallet; same day for transfer", "Determines whether the Ajo feels alive"],
        ["Transfer-reference match rate", "Automatically matched ÷ transfer payments received", "≥ 98%", "Unmatched transfer is the top reconciliation cost"],
        ["Payout success rate", "Succeeded ÷ released", "≥ 99%", "A failed payout is a broken promise"],
        ["Payout cycle time", "ready_at → bank credit", "< 30 min; T+1 acceptable for transfer rails", "The moment the whole product exists for"],
        ["Unmatched money as % of volume", "Unmatched ÷ total inbound", "< 0.5%", "Above this, reconciliation stops scaling"],
        ["Reconciliation break rate", "Sessions with a mismatch ÷ sessions", "Zero tolerance", "The ledger must be true"],
        ["Manual intervention rate", "Manual money ops ÷ total money ops", "Declining trend", "Automation maturity"],
    ]},
]
