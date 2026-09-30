"""
Section 19 — Error and Edge-Case Specification.

Source of truth: docs/src/CANONICAL.md
Authoring contract: docs/src/AUTHORING.md
Cross-references: section 1 (business-rule register BR-001 to BR-032, risks
R1 to R14, assumptions A-01 to A-14, dependencies DEP-01 to DEP-15),
section 2 (user flows 2.1 to 2.17), section 4 (wireframes), section 6 (API),
section 7 (schema).

This is the register of everything that can go wrong. Each case is classified,
given a stable ID of the form EC-nnn, and specified across six dimensions: the
trigger, the system behaviour, the user experience, the recovery mechanism, and
the logging requirement. A case with no recovery mechanism is a specification
gap and is called out as such rather than dressed up.

Money in every example is stated in the canonical form: a member owing
NGN 1,000.00 is charged NGN 1,020.00, of which NGN 20.00 is the 2% platform
fee recorded as fees_income; the recipient of a ten-member round receives the
base pool NGN 10,000.00 and never NGN 10,200.00. The tagline is
"Your Ajo. Your Story."
"""

BLOCKS = [
    {"t": "h1", "text": "19. Error and Edge-Case Specification"},

    {"t": "lead",
     "text": (
        "A savings product that works perfectly in a test environment and fails on a "
        "Tuesday evening in a Lagos market has failed. This section is the register of "
        "every way that can happen: the payment that succeeds while the phone is dead, "
        "the webhook that arrives twice, the member who pays twice, the organiser who "
        "disappears, the account takeover, the round that completes before anyone has "
        "been told. One hundred and fifty-one cases are specified across ten classes, each "
        "with a "
        "trigger, a system behaviour, a user experience, a recovery mechanism and a "
        "logging requirement."
    )},
    {"t": "p",
     "text": (
        "**Three rules govern every case in this section.** First, no role, including "
        "`super_admin`, may edit or delete a ledger entry; corrections are reversing "
        "entries only, and every transaction must balance to zero or be rejected (BR-013, "
        "BR-021, BR-025, G6). Second, a payout is released only when the round's funds "
        "are fully available; it is never reduced and corporate funds are never used to "
        "cover a shortfall (BR-018, BR-020, G4). Third, a defaulting member is never "
        "named or exposed to any other member, and no other member is ever charged "
        "extra without their explicit consent (BR-014, BR-015, G5). Any behaviour below "
        "that would breach one of these is stated as prohibited, not offered as an option."
    )},
    {"t": "p",
     "text": (
        "**Severity** is assigned per case using the matrix in 19.12: S1 is money at risk "
        "or trust destroyed, S2 is a member blocked from a correct outcome, S3 is "
        "degraded experience with no money impact, S4 is cosmetic or internal. The "
        "`EC-nnn` identifiers in this section are referenced from the flow tables in "
        "section 2 and are stable: an identifier is never reused for a different case."
    )},
    {"t": "callout",
     "kind": "NOTE",
     "title": "The single most important line in this section",
     "text": (
        "There is no case in this register in which the platform pays a member less than "
        "the base pool they were promised, in which a member is charged twice for the "
        "same contribution, in which a defaulting member is exposed, in which a financial "
        "record is edited rather than reversed, or in which a shortfall is quietly covered "
        "with corporate funds. Those five are not edge cases to be handled. They are the "
        "product, and a design that permits any of them is a different product."
    )},

    # ------------------------------------------------------------------ 19.1
    {"t": "h2", "text": "19.1 Payment edge cases"},
    {"t": "p",
     "text": (
        "The payment class covers everything from the member's bank declining to the "
        "member deliberately paying twice. These are the highest-volume cases in the "
        "register and the ones most likely to be designed badly under time pressure, "
        "because a payment flow that 'looks fine' in a demo is precisely a payment flow "
        "that double-charges a real person."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-001",
         "The member loses internet connectivity partway through authorising a payment, "
         "so the provider's result never reaches the app.",
         "The payment stays `PENDING` with an expected confirmation time. The contribution "
         "stays PENDING and is never shown as in arrears. The member is not prompted to "
         "pay again. A late-arriving webhook is still accepted and still credits the "
         "contribution exactly once.",
         "*We are still confirming this payment. Do not pay again - we will tell you the "
         "moment it clears.* The dashboard shows the payment as pending with a spinner "
         "that is honest about what is known.",
         "Reconciliation against provider settlement, on the interval agreed with the "
         "provider under D-03. The interval is not fixed here because settlement timing is "
         "an open decision; what is fixed is that the member is contacted proactively "
         "rather than left waiting.",
         "Payment attempt with state, timestamp, last client heartbeat and the resolution "
         "path. Alert if any payment remains PENDING beyond the interval set under D-03, "
         "so the threshold is a decision rather than an assumption."],
        ["EC-002",
         "The payment succeeds at the provider but the HTTP response to the client is "
         "lost, so the app never learns the outcome.",
         "The webhook, not the client response, is the source of truth. The payment is "
         "resolved to SUCCESS, the ledger posts `contribution.received` then "
         "`fee.recognised`, and the contribution moves to PAID. The client reconciles on "
         "next open and sees PAID with a receipt.",
         "Nothing is asked of the member. On reopening the app the contribution simply "
         "reads PAID, with the receipt available.",
         "None required. The member's next app open resolves the display; if it does not, "
         "`GET /payments/:id` is authoritative.",
         "Log the webhook arrival and the client poll as two separate events, so that a "
         "'client thought it failed' report can be distinguished from a real failure."],
        ["EC-003",
         "The provider delivers the same webhook twice, or delivers the retry of a webhook "
         "it already delivered.",
         "The webhook event is deduplicated on provider event id. The second delivery "
         "returns 200 and changes nothing. No second ledger entry, no second fee, no "
         "second contribution credit.",
         "None. The member sees exactly one payment and one receipt.",
         "Automatic. The idempotency key for a webhook is the provider event id, stored "
         "uniquely.",
         "Log the duplicate with the original event id, so that a provider that "
         "double-delivers systematically is visible before it becomes a support load."],
        ["EC-004",
         "The member pays twice: either by deliberate action, or because a retry used a "
         "different idempotency key after a client crash regenerated it.",
         "The second success is recorded as an overpayment against the same contribution, "
         "never as a second contribution and never silently absorbed. Escrow holds the "
         "amount. The contribution obligation is discharged by the first payment alone.",
         "*You have paid this round twice. We are holding the extra NGN 1,020.00 and will "
         "refund it - nothing more is owed.*",
         "Refund on request, or consented application to a future round. The member must "
         "choose; silent application is prohibited (BR-032).",
         "Overpayment record linked to both payment ids, the contribution id, the "
         "reversal or application event, and the member's decision. Any overpayment "
         "unresolved after 7 days escalates."],
        ["EC-005",
         "The member pays a partial amount, for example NGN 500.00 against an obligation "
         "of NGN 1,000.00 plus the 2% fee.",
         "Refused. The amount owed is fixed by the schedule and the fee is a function of "
         "that amount, so a partial payment has no coherent fee. AJO.ng does not define "
         "partial contribution as a valid state at MVP.",
         "*Contributions are a fixed amount. This round is NGN 1,000.00 plus a NGN 20.00 "
         "fee, NGN 1,020.00 in total.*",
         "None required; the member pays the full amount. If partial payment is wanted "
         "later it is a scope change, not a bug fix.",
         "Rejected attempt logged with the attempted amount and the required amount, so a "
         "pattern of attempted partial payments is visible to risk."],
        ["EC-006",
         "The member pays more than the scheduled amount, for example NGN 5,000.00.",
         "The amount is fixed at initiation from the schedule and the client cannot "
         "override it. An overpayment arrives only through EC-004, and is handled there.",
         "*The amount for this round is fixed at NGN 1,020.00.*",
         "None; the request is refused before any provider call is made.",
         "Refusal logged with actor, role and the mismatch between requested and required "
         "amount."],
        ["EC-007",
         "A zero-value contribution is submitted, or the fee computes to zero kobo.",
         "Refused at validation. A zero contribution would create a ledger entry with no "
         "economic content and would corrupt round funding arithmetic. The minimum "
         "contribution is a configured value, not a hard-coded literal.",
         "*This amount is below the minimum contribution AJO.ng allows.*",
         "None required.",
         "Refusal logged. A run of near-zero or sub-minimum attempts is a risk signal "
         "(see EC-078, EC-081)."],
        ["EC-008",
         "The fee rounding lands on a half-kobo boundary, for example an amount whose kobo "
         "value times 200 ends in exactly 5000.",
         "Rounding is half-up and applied exactly once, at the single defined point: "
         "`fee_kobo = (amount_kobo * 200 + 5000) / 10000` using integer division. The "
         "computed fee is stored and the total charged is `amount_kobo + fee_kobo`; the "
         "total is never recomputed by re-rounding the sum.",
         "None. The member sees the same three numbers that were charged.",
         "Property-based tests over large random amounts and every boundary value, plus a "
         "fixture that must render identically in the app, the receipt export and the "
         "ledger (A-08).",
         "Store `amount_kobo`, `fee_kobo` and `total_kobo` on every payment. If a "
         "recomputation ever disagrees with the stored values, that is a Sev-2 and is "
         "reported as K-16."],
        ["EC-009",
         "A database transaction fails midway, after one posting of a multi-posting "
         "ledger transaction has been written but before the transaction commits.",
         "The whole ledger transaction rolls back atomically. No partial posting survives. "
         "The business record is left in its prior state with a `POST_INCOMPLETE` marker "
         "and is resolved by reconciliation, never by hand-editing.",
         "*We are resolving a records issue on this payment. You have not been charged "
         "twice and nothing is lost.*",
         "Automated reconciliation, then a risk event if unresolved. The solvency assertion "
         "prevents any disbursement while the exception is open (BR-020).",
         "Sev-1 alert on any partial ledger write. Log transaction id, the postings that "
         "were attempted, the rollback, and the resolution. K-16 is zero tolerance."],
        ["EC-010",
         "A reversal or refund is requested for a payment whose funds have already left "
         "the approved financial arrangement, for example because a payout was made from "
         "the same pool.",
         "The simple reversal path is unavailable. The case is escalated to `risk_officer` "
         "and to the provider relationship. AJO.ng does not claw back from a member, and "
         "does not absorb a loss silently.",
         "*Your refund is with our payment partner. We will update you every 48 hours until "
         "it is done.*",
         "Manual case with a named contact at ProvidusUnity, a recorded risk decision, and "
         "proactive member updates on a fixed cadence until resolution.",
         "Case record with the trigger, the evidence, the decision, the rationale and the "
         "officer. Every member update logged so the cadence commitment is auditable."],
        ["EC-011",
         "A refund is claimed twice for the same payment, or two agents initiate the same "
         "refund concurrently.",
         "One reversal per payment, enforced by a uniqueness constraint on the reversal "
         "reference. The second request is rejected and the attempt is recorded.",
         "*This payment has already been refunded. Here is your refund receipt.*",
         "Automatic.",
         "Rejected attempt logged with actor and role. A support agent repeatedly hitting "
         "this is a training signal, not a system fault."],
        ["EC-012",
         "The member pays after the due time but before the 48-hour grace has elapsed.",
         "Accepted as a late payment, not a default. The contribution returns to PAID, the "
         "organiser is not notified that a default occurred, and the late arrival is "
         "visible only in the member's own record and in aggregate reporting.",
         "*Paid, late. Nothing more is needed.*",
         "None required.",
         "Late-payment metric K-03 tracks on-time rate; individual lateness is retained but "
         "never surfaced to other members (BR-014)."],
        ["EC-013",
         "A payment is initiated for a contribution that has already been settled, "
         "because the client showed a stale screen.",
         "The server, not the client, is authoritative. The request is rejected as a "
         "conflict. No provider call is made and no money moves.",
         "*You have already paid this round. Here is your receipt.*",
         "Automatic. The client refetches the contribution and shows PAID.",
         "Rejected attempt logged. A high rate of these is a client-cache defect and is "
         "tracked as an S3 engineering defect, not a member error."],
        ["EC-014",
         "The member pays after the Ajo has been CANCELLED or has COMPLETED.",
         "The Ajo is in a terminal state and accepts no further events. The payment is "
         "refused before any provider call (BR-009).",
         "*This Ajo has ended, so it cannot take another payment. If you believe you are "
         "owed something from it, contact us and we will check the record.*",
         "Support reviews the ledger; if a genuine obligation exists it is settled as a "
         "payout or refund, never as a contribution.",
         "Refusal logged with the Ajo's terminal state and the timestamp at which it was "
         "reached."],
        ["EC-015",
         "The member pays after their contribution has been recorded as DEFAULTED.",
         "Accepted through the recovery path. The contribution transitions DEFAULTED back "
         "to PAID. The historical default record is retained and never deleted; only the "
         "state advances (BR-016, FR-DEF-007).",
         "*Thank you. Your payment is recorded and your Ajo is back on track.*",
         "None required. This is the recovery path working.",
         "Full state transition chain retained with actor, role, timestamp, prior state and "
         "new state (NFR-AUD-001)."],
        ["EC-016",
         "A contribution arrives after the 48-hour grace has fully elapsed, by which point "
         "a default has already been recorded and the organiser has been notified.",
         "Same as EC-015: the contribution returns to PAID. The organiser is not sent a "
         "correction notification containing member-visible default language; they see the "
         "current state, which is PAID.",
         "*Your payment is in and your round is covered.*",
         "None required.",
         "State chain retained. The default-to-recovered transition is a required field in "
         "default-rate reporting (K-05) so that recoveries are visible to risk."],
        ["EC-017",
         "A refund or reversal takes longer than the stated window, or the provider never "
         "confirms it.",
         "The case is swept on a schedule. The provider is asked for a reason. The member "
         "receives a proactive update at a fixed interval until it resolves. No window is "
         "publicised until ProvidusUnity confirms it in writing.",
         "*Still waiting on the payment partner. Next update by DATE.*",
         "Support sweep plus provider escalation. D-07 (refund SLA) must be answered before "
         "any window is promised to a member.",
         "Every update logged with its timestamp so the cadence commitment is auditable and "
         "so that a promise made in one channel and missed in another is detectable."],
        ["EC-018",
         "The provider is unreachable at payment initiation, before any charge is possible.",
         "Initiation fails fast. No payment record is left dangling in an ambiguous state "
         "and no obligation is altered. The client retries with the same idempotency key.",
         "*We could not reach the payment provider. Nothing was taken. Try again in a "
         "minute.*",
         "Automatic client retry, then manual retry. Nothing is lost because nothing "
         "happened.",
         "Initiation failures logged with provider, latency and error class. Availability "
         "on the money path is measured separately (NFR-AVL-002)."],
        ["EC-019",
         "The provider declines for insufficient funds, or the issuer refuses.",
         "Payment state FAILED with a machine-readable reason. No ledger entry is written, "
         "because no money moved. The contribution stays PENDING and the due date is "
         "unchanged.",
         "*Not enough in the account. Nothing was taken. Top up and try again.*",
         "`POST /contributions/:id/retry` with a new idempotency key against the same "
         "obligation.",
         "Failure reason class and provider reference retained. No provider text is exposed "
         "raw to members (enumeration and information-leak control)."],
        ["EC-020",
         "The provider's client page loads slowly or fails to load, so the member cannot "
         "authorise at all.",
         "The payment stays PENDING or is CANCELLED. The contribution is untouched. The "
         "member can retry or choose another supported method.",
         "*The payment page is not loading. Nothing has been taken. Try again, or try a "
         "different method.*",
         "Retry, alternative method, or support-assisted path that still does not involve "
         "AJO.ng handling credentials (NFR-SEC-007).",
         "Provider page load failures are not visible to us directly; provider-side "
         "telemetry is requested in the SLA and the gap is logged as a known blind spot."],
        ["EC-021",
         "A contribution amount falls outside the configured minimum or "
         "above the contribution cap.",
         "Refused before any provider call. The bounds are configured, "
         "not hard-coded, and the cap exists as a fraud control (D-08). "
         "AJO.ng publishes the range, so no member discovers it by "
         "failing.",
         "*This amount is outside the range AJO.ng allows for one "
         "contribution.*",
         "Choose an amount inside the range. The bounds are changed only "
         "by `super_admin`, with a versioned and audited change.",
         "Refusal with the attempted amount and the range in force. A "
         "population of attempts just above the cap is a risk signal "
         "(R4)."],
        ["EC-022",
         "The identical request arrives twice, from a retry, a double "
         "tap or a client retry storm.",
         "The `Idempotency-Key` returns the original result rather than "
         "creating a second one. No second obligation, no second "
         "payment, no second ledger entry. The replayed request is "
         "recorded, not served as new.",
         "*You already paid this one. Here is your receipt.*",
         "None needed; this is the guarantee working (BR-024).",
         "Replayed request with the key and the original result. A rise "
         "in replays from one client is a client defect and an S3 "
         "engineering item."],
        ["EC-023",
         "The member abandons the provider's authorisation page without "
         "completing or cancelling it.",
         "The payment is left in a non-terminal state until the "
         "provider's own timeout resolves it, and the contribution stays "
         "PENDING and not overdue. AJO.ng does not assume abandonment "
         "means failure, because a provider may still complete it.",
         "*Nothing was taken. You can pay this round whenever you are "
         "ready.*",
         "The provider timeout, then the same payment surface again, or "
         "support-assisted.",
         "Abandonment with the elapsed time before the provider resolved "
         "it. A pattern of abandonment at one provider screen is a "
         "provider-usability finding."],
        ["EC-024",
         "The same member retries the same contribution more than three "
         "times, each attempt failing.",
         "Further retries are rate-limited for that contribution and the "
         "member is routed to a different method or to support. This "
         "prevents a retry loop from becoming a payment incident, and it "
         "does not change the obligation or the due date.",
         "*That is several attempts. Let us sort this out together - "
         "nothing has been taken.*",
         "Support-assisted payment, which still does not involve AJO.ng "
         "handling credentials.",
         "Retry count per contribution with the failure class on each "
         "attempt. A member stuck at three failures is a conversion "
         "problem and is reviewed as one."],
        ["EC-025",
         "One member fails payments across several Ajos at once, for "
         "example because a phone is shared across accounts.",
         "Treated as a signal about the account, not as dishonesty. No "
         "default is accelerated, no obligation is altered, and the "
         "pattern is routed to `risk_officer` for review rather than to "
         "automatic punishment.",
         "*It looks like something is wrong with the account rather than "
         "with you. Let us fix it.*",
         "Verification-assisted resolution; a single verified account is "
         "preferred to several that all fail.",
         "Cross-Ajo failure pattern with the accounts and devices "
         "involved. This is the pattern that would otherwise be mistaken "
         "for fraud (R4)."],
        ["EC-026",
         "A member believes a charge happened and cannot find it in "
         "their own history.",
         "Treated as a possible money-at-risk report, not a "
         "misunderstanding. The member's full payment history is "
         "readable by them, support can reconcile against the provider "
         "by reference, and the case is worked to a definite answer "
         "either way.",
         "*We will find it. If a charge went through, you will see it "
         "here, and if it did not, we will tell you that too.*",
         "Support reconciliation by provider reference, ending in either "
         "a located payment or a confirmed absence.",
         "The member's report, the reconciliation evidence, and the "
         "conclusion. An unlocated charge is escalated to "
         "`risk_officer`, because 'we cannot find it' and 'it did not "
         "happen' must never be the answer given."],
        ["EC-027",
         "A member asks for the 2% fee to be refunded as well as their "
         "contribution.",
         "The contribution is refunded in full. The fee treatment "
         "depends on D-05 at Ajo cancellation and D-06 on whether the "
         "fee is tax-inclusive, so the fee answer is either given from a "
         "decision or explicitly held as open. AJO.ng does not quietly "
         "decide it in the member's favour or against them.",
         "*Your contribution is being returned in full. The fee question "
         "is a policy one and we will answer it as soon as it is settled "
         "- we are not going to guess with your money.*",
         "Refund of the contribution; fee refund on the answer to D-05, "
         "applied consistently to every member affected.",
         "Fee-refund requests with the decision applied. A fee refunded "
         "to some members and not others would be a discrimination "
         "finding, so the population is tracked."],
        ["EC-028",
         "A contribution falls due while the member's account is frozen "
         "or under risk review.",
         "The obligation stands and the due date does not move, because "
         "a platform-imposed pause is not a member default. The state is "
         "HELD rather than OVERDUE, no default is recorded against the "
         "member, and no other member is charged for it.",
         "*Your round is still yours. While we review your account the "
         "payment is paused, and you are not overdue and nobody else is "
         "being asked to cover it.*",
         "Unfreeze after review, then the normal contribution window. "
         "Support can act for the member if the review outlasts the "
         "window.",
         "Due date, HELD event with its reason, and the notification to "
         "the affected member. Prolonged holds on the same account are "
         "reviewed, because they accumulate into a real loss."],
        ["EC-029",
         "A payment failure was actually the provider's fault and the "
         "member is treated as though it were theirs.",
         "Corrected wherever it is recorded. Attribution is determined "
         "by provider evidence, not by the fact that a failure occurred "
         "on our member's schedule, and a member's record is amended "
         "rather than left carrying a fault that was not theirs.",
         "*That was our provider's problem, not yours. It is corrected "
         "on your record.*",
         "Record correction with the provider evidence attached.",
         "Attribution with the evidence, and any correction made to a "
         "member's record. Misattributed failures accumulate into false "
         "risk profiles, so this is a quality metric, not a nicety."]
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.2
    {"t": "h2", "text": "19.2 Connectivity and client edge cases"},
    {"t": "p",
     "text": (
        "The target user is on a mid-range Android device over 3G, in a market, at the end "
        "of a trading day (G7, C-14, A-07). Connectivity is therefore the normal condition, "
        "not the exception, and the flows in section 2 are written for that reality. This "
        "class covers what happens when the network, the device clock or the device itself "
        "misbehaves."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-030",
         "The client loses connectivity entirely, for example the phone is out of signal "
         "for hours while a contribution is due.",
         "Nothing is queued locally to be 'sent later' for a money movement. The server "
         "remains the sole authority on state. Cached reads are served with an explicit "
         "'last updated' timestamp so a stale screen can never be mistaken for a live one.",
         "The app opens to cached data clearly marked as such, plus the outstanding amount "
         "and due date. The next action is always available when signal returns.",
         "Automatic on reconnect. No offline money movement exists by design, because an "
         "offline payment queue is an unbounded double-charge risk.",
         "Client-side connectivity and cache-age events with device class. This data is how "
         "we prove the low-bandwidth requirement in NFR-PERF-004 rather than assuming it."],
        ["EC-031",
         "The client clock is wrong by hours or days, so the app believes a due date has "
         "passed when it has not, or the reverse.",
         "All state transitions, deadlines and grace windows are computed server-side from "
         "recorded UTC timestamps. A skewed client can neither accelerate nor postpone a "
         "default, a grace expiry or an enrollment deadline.",
         "*Your phone time is out by more than a day. Your payment status is correct "
         "regardless.*",
         "The app resynchronises time on detection. The member's status is unaffected in "
         "the meantime, which is the point.",
         "Client clock offset logged per session with device id. A population of skewed "
         "devices is an S3 usability defect and is prioritised as such, precisely because "
         "it makes an honest member believe they are in arrears when they are not."],
        ["EC-032",
         "A member travels to a different Nigerian time zone, or the country changes its "
         "time rules, during an active Ajo.",
         "All timestamps are stored in UTC and rendered in the user's configured zone, with "
         "the zone shown explicitly whenever a deadline matters. Deadlines themselves are "
         "evaluated in a single declared Ajo time zone, not in the viewer's local zone.",
         "The due date always displays with its zone, for example *Tue 12 May, 18:00 "
         "WAT*. A traveller sees the deadline in the Ajo's terms, not in theirs, so nobody "
         "is surprised by a silent 7-hour shift.",
         "None needed; this is a rendering rule. NFR-LOC-003.",
         "Rendered zone recorded on any dispute about a missed deadline, so support can "
         "reconstruct exactly what the member saw."],
        ["EC-033",
         "Daylight-saving or a government time change moves a local clock forward by an "
         "hour in the middle of a collection window.",
         "The Ajo's deadlines are anchored to UTC instants, not to wall-clock local time, so "
         "a clock change cannot create or destroy a due date. The Ajo time zone is declared "
         "once and stored with the Ajo.",
         "Any affected member is notified in advance if the change moves a deadline, so the "
         "shift is explained rather than discovered.",
         "System rule plus proactive notification. Nigeria has not observed daylight saving "
         "for many years, so this is a robustness requirement against a change, not a "
         "prediction.",
         "The declared Ajo time zone and any change to it are configuration events, "
         "versioned and audited (FR-ADM-010)."],
        ["EC-034",
         "A member's account is frozen or placed under risk review at the moment their "
         "payout is due.",
         "The payout is not lost, not redirected, and not paid to anyone else. It enters "
         "HELD with a recorded reason, and both the recipient and the organiser are notified "
         "on push, email and SMS. No default clock runs against the member for a "
         "platform-imposed hold.",
         "*Your payout is on hold while we confirm your account. It is yours, it is safe, "
         "and we will tell you the moment it is released.*",
         "Risk review, then release. Support can lift the freeze after verified identity.",
         "Payout HOLD event with the reason code, the deciding officer and the timestamps "
         "of both notifications. BR-017 requires the notification, so its absence is an "
         "alertable condition in itself."],
        ["EC-035",
         "The app is force-quit or the device is lost or wiped between a payment initiation "
         "and its confirmation, and the idempotency key is lost with local storage.",
         "The key is derived deterministically from the contribution, the attempt number "
         "and the device id, so a regenerated key still matches the original attempt. The "
         "server returns the original result and no second payment is created.",
         "Nothing. The member is never asked to pay twice because the app was closed.",
         "Automatic. BR-024.",
         "Attempt-number reuse is logged. A rise in it indicates a client defect and is an "
         "S3 engineering item, not a member complaint."],
        ["EC-036",
         "The device is too old, too low on storage, or lacks the capability the payment "
         "provider surface requires.",
         "The app detects this before the member reaches the payment step and says so, "
         "rather than failing inside a third-party page. The member can still view, verify, "
         "join and pay through any supported browser.",
         "*This phone cannot run the fastest version of the app. Everything still works, and "
         "here is how.*",
         "Browser fallback for the whole core flow: join, pay, view position (G7, "
         "NFR-PERF-004, C-14).",
         "Device class and capability failures are logged so the supported-device floor is "
         "maintained from evidence rather than from a marketing claim."],
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.3
    {"t": "h2", "text": "19.3 Provider and webhook edge cases"},
    {"t": "p",
     "text": (
        "ProvidusUnity is a dependency, not a component we control, and the only durable "
        "position on that is the one in section 1: its exact collection percentage, payout "
        "flat fee and settlement timing are open decision **D-03**, and its holding model "
        "is open decision **D-02**. Nothing in this class asserts a provider behaviour we "
        "have not been shown. What is specified here is how AJO.ng behaves when a provider "
        "behaves unexpectedly, which is a design obligation regardless of the answer to "
        "D-02 and D-03."
    )},
    {"t": "callout",
     "kind": "WARN",
     "title": "Design rule, not a provider promise",
     "text": (
        "`POST /webhooks/payments` is unauthenticated by necessity and therefore "
        "signature-verified by necessity. A webhook is treated as a claim, never as "
        "authority: it can move AJO.ng from UNKNOWN or PENDING to a resolved state, and "
        "it can never create a contribution, choose an amount, or name a beneficiary. "
        "Those are read from our own record, which the webhook is matched against."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-037",
         "A provider callback arrives for a payment that AJO.ng has not yet recorded, "
         "because the callback outran the response to our own initiation call.",
         "The unmatched callback is written to `webhook_events` and held, not applied. No "
         "contribution is credited on an unmatched reference. Once our initiation response "
         "lands, the held event is replayed and applied in arrival order.",
         "*We are confirming your payment. It is not lost and you do not need to pay "
         "again.*",
         "Automatic replay within a bounded window. An unmatched event unresolved after "
         "24 hours becomes a reconciliation item and a risk event.",
         "The held event, its provider event id, the payment it claimed, the delay "
         "between our initiation and its arrival, and the eventual resolution."],
        ["EC-038",
         "A callback arrives with a missing, malformed or invalid signature.",
         "Rejected with 401 and nothing is written except the rejection. Repeated "
         "signature failures from a single source are treated as a probable attack, not "
         "as noise.",
         "None. The member's legitimate callback is unaffected because it is verified "
         "correctly.",
         "None needed for the member; automatic alerting for us.",
         "Full rejection detail with the reason and source. A rate threshold raises a "
         "security alert to `risk_officer` (NFR-SEC-003)."],
        ["EC-039",
         "A callback references a payment id that does not exist in our ledger at all, "
         "for example one belonging to another merchant or another environment.",
         "Rejected and recorded as an unknown reference. AJO.ng never creates a payment "
         "row from an inbound callback, so an unknown reference cannot become money.",
         "None.",
         "None needed; investigation only.",
         "Unknown-reference rejections retained indefinitely, because a sustained pattern "
         "means our environment or credentials are wrong."],
        ["EC-040",
         "A replayed callback arrives far outside any plausible replay window, for "
         "example weeks after the payment settled.",
         "Rejected by timestamp freshness. The original settled payment is untouched. "
         "Late delivery is not treated as a new event; a settlement-state payment cannot "
         "be re-resolved by a callback.",
         "None.",
         "None needed.",
         "Rejected replay retained with the original event id, so a provider that "
         "misunderstands replay semantics is identified before it becomes a dispute."],
        ["EC-041",
         "The provider sends two contradictory callbacks for the same payment, for example "
         "SUCCESS and then FAILED.",
         "Resolved by a single, declared precedence rule: the first terminal state reached "
         "through a verified channel wins, and any later contradiction is escalated rather "
         "than applied. A contradiction involving an already-posted ledger entry is never "
         "resolved by editing the entry; it goes to `risk_officer` and, if funds have moved, "
         "to the provider as a formal dispute.",
         "The member is told the confirmed outcome once, and is never shown two different "
         "states for the same payment.",
         "Risk review, then provider dispute, then a correcting provider event if one "
         "exists. If money has already moved, a reversing entry is the only correction "
         "(BR-025).",
         "Both events, the precedence decision, the officer, and the final resolution. This "
         "is a Sev-1 class of incident and is never closed by an automatic rule alone."],
        ["EC-042",
         "A payout appears successful at the provider but is later reversed or recalled by "
         "the provider after settlement.",
         "A provider-side recall of a settled payout is an S1 incident, not a routine "
         "failure. The payout record is retained as historical truth; the recall is "
         "recorded as a new event. AJO.ng does not claw the money back from the member, "
         "does not silently reduce future payouts, and does not present the loss as the "
         "member's fault.",
         "*Your payout was recalled by our payment partner, not by you. We are resolving "
         "it and you will hear from us by DATE, even if there is nothing new to report.*",
         "Provider escalation with a named contact, a recorded risk decision, and proactive "
         "member updates on a fixed cadence. The member's own record is never rewritten.",
         "Full chain retained: payout settlement, recall notice, officer, decision, "
         "rationale, and every member communication. This is the case most likely to "
         "damage trust, so the audit trail is treated as the primary artefact."],
        ["EC-043",
         "A callback arrives long after the payment's expected confirmation, beyond the "
         "interval the member was told to expect.",
         "The payment resolves normally, but the delay is measured. Where the delay is "
         "caused by the provider, the member is not blamed and not asked to do anything; "
         "where it is caused by our own reconciliation, that is our Sev-2.",
         "Nothing is asked of the member. An apology-level message is sent when the "
         "confirmed time passes the promised time, because silence is what makes people "
         "pay twice.",
         "Automated reconciliation plus, after the interval, the payment-exception queue.",
         "Delay duration, the point at which the member was notified, and the resolved "
         "time. The distribution of this delay is the only honest way to hold a provider "
         "to D-03."],
        ["EC-044",
         "The provider credits the same bank account twice for one payout, or issues two "
         "settlement references for one instruction.",
         "One payout is settled and the duplicate is detected at settlement reconciliation "
         "and returned through the provider's reversal or recovery process. The second "
         "credit is never absorbed into escrow, because absorbing it would silently "
         "inflate the pool that other members are owed.",
         "None. The member's amount and their position are unaffected.",
         "Provider recovery, with the duplicate held in a suspense account and never "
         "recognised as fees_income or as contributions receivable.",
         "Suspense entry with both provider references. Suspense balance is reported "
         "daily and must not be allowed to become a place where money disappears."],
        ["EC-045",
         "A callback reports a different amount, or a currency other than NGN, from what "
         "we initiated.",
         "Rejected. Amount and currency are read from our own initiation record and are "
         "never taken from the callback. A currency other than NGN is refused at "
         "initiation (BR-031).",
         "None.",
         "None needed for the member; investigation for us.",
         "Rejected mismatch with both values. A provider that alters amounts is a "
         "contract-level escalation."],
        ["EC-046",
         "The provider changes its API contract, webhook schema or authentication scheme "
         "without notice.",
         "The integration is version-pinned and the contract is asserted on every call, so "
         "a breaking change surfaces as a loud failure rather than a silent "
         "misinterpretation. Contract tests run against recorded fixtures on every deploy.",
         "Payments may pause rather than fail wrongly. If initiation is unavailable, the "
         "member is told clearly that nothing has been taken.",
         "Provider liaison, contract tests, and a documented rollback path.",
         "Contract-test failures as deploy-blocking, and provider error-class distribution "
         "over time, so a silent semantic shift is visible in trends as well as in "
         "failures."],
        ["EC-047",
         "The provider rate-limits our reconciliation or status calls.",
         "Calls are queued with exponential backoff and jitter, never retried in a tight "
         "loop. Reconciliation is prioritised over read-only status calls, because an "
         "unresolved payment blocks a member while a stale status only delays a screen.",
         "Nothing visible unless reconciliation is affected, in which case the honest "
         "*we are still confirming this payment* state is shown rather than a failure.",
         "Automatic backoff, then manual sweep.",
         "Rate-limit responses and queue depth. Sustained queue depth is a provider "
         "capacity conversation, tracked under D-03."],
        ["EC-048",
         "The provider enters a maintenance window or returns an ambiguous error such as "
         "a timeout on a request that may or may not have been received.",
         "Ambiguous errors produce a state of UNKNOWN, never a guessed FAILED. An "
         "initiation that may have been received is reconciled by reference before any "
         "retry with a new key, because a blind retry is how a member is charged twice.",
         "*We could not reach the payment provider. Nothing was taken. Try again shortly.*",
         "Reconciliation first, then retry. Support can trigger a status refresh at any "
         "time.",
         "Every ambiguous call with its reference, its state and how it resolved. These are "
         "the calls that later become disputes, so the trail is mandatory."],
        ["EC-049",
         "The provider rejects or fails a disbursement: wrong "
         "destination, name mismatch, limit exceeded or a bank-side "
         "decline.",
         "The payout is FAILED and retried; it is never redirected, "
         "never split and never reduced to fit. A destination belonging "
         "to someone other than the recipient is refused outright rather "
         "than retried. The failure is visible to recipient and "
         "organizer immediately (BR-017).",
         "*Your payout did not go through. Your money is safe and it is "
         "still yours. Here is what we need to fix it.*",
         "Retry with a corrected destination the recipient controls, or "
         "an alternative supported method.",
         "Failure reason, the reference, the retry count and the "
         "destination state. Repeated failures on one payout are worked "
         "until they succeed; a failed payout is never left to resolve "
         "itself."]
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.4
    {"t": "h2", "text": "19.4 Scheduling and lifecycle edge cases"},
    {"t": "p",
     "text": (
        "The Ajo lifecycle is the part of AJO.ng with the least room for interpretation: "
        "`DRAFT → ENROLLMENT → ACTIVE ⇄ ROUND_IN_PROGRESS → COMPLETED` with `CANCELLED`, "
        "`CANCELLING` and `FROZEN` as branches, an enrollment window of exactly 5 days, and "
        "positions that lock on activation. This class is where time, rather than money or "
        "code, breaks the product."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-050",
         "Enrollment reaches day 5 with positions unfilled.",
         "The Ajo cancels automatically and every contribution already collected is "
         "refunded in full. The refund depends on D-05, which decides who bears the fee at "
         "cancellation, so the fee treatment is displayed before the day-5 deadline "
         "arrives, not discovered afterwards.",
         "*This Ajo did not fill, so it has closed and your contribution is being returned "
         "in full.* The member is told before day 5 that this is the outcome, so day 5 is "
         "not a surprise.",
         "Automatic cancellation and full refund. Support can trigger the refund earlier "
         "if the organiser cancels.",
         "Day-5 evaluation with the position fill count at that moment, the refund "
         "instructions issued, and the reason recorded against the Ajo (BR-001)."],
        ["EC-051",
         "Enrollment fills every position on day 4, so the Ajo activates early rather than "
         "waiting for day 5.",
         "Activation proceeds on the fill event, not on a calendar event. The organizer is "
         "notified that positions locked and that terms are now immutable (BR-002, BR-005).",
         "*Your Ajo is full and active. The schedule is locked from now on.*",
         "None needed; this is the design working.",
         "Activation event with the fill state, the locking of positions, and the immutable "
         "terms snapshot. This snapshot is what makes every later dispute answerable."],
        ["EC-052",
         "A member tries to claim a position after activation.",
         "Refused. Position order and membership are fixed at activation; a change requires "
         "a formal replacement or transfer request, and a unilateral exit after activation is "
         "refused (BR-002, BR-003).",
         "*Positions are locked when the Ajo became active. Request a replacement to "
         "transfer your position, and the organiser will review it.*",
         "`POST /ajos/:id/members/:memberId/replace`, which is an organiser-reviewed "
         "request, not a self-service exit.",
         "Rejected attempt logged with actor, role and the reason the state forbade it. "
         "Repeated attempts are a risk signal (R4)."],
        ["EC-053",
         "A member who joined during enrollment is removed on day 4, leaving a position "
         "unfilled with no time to refill it.",
         "Pre-activation removal is permitted, and the position reopens within the "
         "remaining window. If the window then closes unfilled, the Ajo cancels under "
         "EC-050. We do not extend the window silently.",
         "*A position is open again with less than a day to fill. Closing this Ajo early is "
         "possible if it fills.*",
         "Re-invitation, or a replacement claim by an existing member with organiser "
         "approval.",
         "Removal event with actor, role and timestamp, plus the position re-opening, and "
         "the day-5 evaluation that followed."],
        ["EC-054",
         "The organiser edits the contribution amount, frequency or payout order after the "
         "Ajo is ACTIVE.",
         "Refused. The terms are immutable once active; changing them would change what "
         "every member consented to, and silently changing a fee is separately prohibited "
         "(BR-005, BR-026).",
         "*The terms of an active Ajo cannot be changed. Start a new Ajo instead, with the "
         "new terms shown to everyone up front.*",
         "A new Ajo. There is no override, including for `super_admin`, because a consent "
         "that can be rewritten after the fact is not consent.",
         "Rejected edit logged with the attempted field change and the actor's role. A "
         "successful edit attempt on an active Ajo would be a Sev-1 integrity failure."],
        ["EC-055",
         "A round completes while a dispute concerning that round is still open.",
         "The dispute is not ignored and the money is not distributed through the "
         "ambiguity. The payout enters HELD with the dispute as the recorded reason, and "
         "both recipient and organizer are notified (BR-017, BR-018). Disbursement resumes "
         "or is resolved by the dispute outcome.",
         "*Your payout is on hold while a question about this round is being answered. It is "
         "yours and it is safe.*",
         "Dispute resolution, then release. The hold is visible to support and to the "
         "member as a reason, never as an unexplained delay.",
         "HOLD event naming the dispute id, the notification timestamps, and the release "
         "event with its cause."],
        ["EC-056",
         "The provider or our own scheduler is down at the exact moment a round was due to "
         "start, so a payout is discovered late rather than on time.",
         "A missed payout is treated as a Sev-1 and is communicated as soon as it is "
         "detected, before it becomes a member complaint. The payout is not skipped, "
         "rescheduled silently, or reported as on time.",
         "*Your payout was delayed. It is being processed now and here is when to expect "
         "it.* We do not let a member discover a missed payout by noticing an absent "
         "notification.",
         "Immediate execution on recovery, with a proactive notice to recipient and "
         "organizer.",
         "Detected-versus-scheduled delta in seconds, the notification timestamps, and the "
         "cause. On-time payout rate is a trust metric, not a technical one."],
        ["EC-057",
         "A round's collection window is configured so short that the 48-hour grace period "
         "extends past the next round's start.",
         "Rejected at schedule creation. Overlapping windows are a configuration error that "
         "would otherwise force a member into overlapping obligations, which is exactly the "
         "kind of coercion the product is meant to remove.",
         "*This schedule gives members less than 48 hours to pay, which cannot overlap the "
         "next round.*",
         "None; the schedule is corrected before it can be created.",
         "Rejected schedule with the conflicting windows. A valid but very tight schedule is "
         "flagged for review rather than rejected."],
        ["EC-058",
         "An Ajo is CANCELLED while a round is in progress and contributions have already "
         "been collected.",
         "The Ajo moves to CANCELLING, not straight to CANCELLED. All collected funds are "
         "refunded in full, each member's fees are handled per D-05, and only then does the "
         "Ajo reach CANCELLED. No round is ever completed against a cancelling Ajo.",
         "*This Ajo is closing, so every contribution collected is being returned to the "
         "member it came from.*",
         "Automatic full refund, with the same notification discipline as a successful "
         "payout.",
         "CANCELLING entry, refund instructions per member, fee treatment per D-05, and the "
         "final terminal transition with its timestamp."],
        ["EC-059",
         "A FROZEN Ajo is frozen for longer than a member's tolerance, with a round due in "
         "the meantime.",
         "Freeze halts the Ajo's timers and the members are told the reason and that their "
         "obligations are suspended, rather than being allowed to accrue an apparent debt "
         "during a platform-imposed pause. Unfreeze resumes the schedule with its remaining "
         "time intact where possible.",
         "*This Ajo is paused by us while we sort something out. Your round is not overdue "
         "and you are not being charged.*",
         "Unfreeze by `risk_officer` or `super_admin` with a recorded reason; the member may "
         "escalate to support if the pause exceeds the communicated window.",
         "Freeze and unfreeze with actor, role, reason and duration. Prolonged freezes are "
         "reviewed for pattern, because a freeze that always lands on the same organizers "
         "is an inequity."],
        ["EC-060",
         "The organiser configures fewer than two positions.",
         "The `OPEN_ENROLLMENT` guard fails and the Ajo stays in "
         "`DRAFT`. The rule is a floor, not a preference: an Ajo of one "
         "is a savings account, and pretending otherwise produces a "
         "product that does not mean what it says.",
         "*An Ajo needs at least two members. One member is a savings "
         "account, not an Ajo.*",
         "Raise the member count and re-submit.",
         "Rejected configuration with the count attempted. The guard is "
         "asserted in a test, so it cannot be lost in a refactor."],
        ["EC-061",
         "The organiser abandons the wizard and returns days later.",
         "The Ajo is still in `DRAFT`, and a draft has no clock running "
         "on it, so an abandoned draft cancels nothing and collects "
         "nothing. The draft is restored exactly as it was left, "
         "including every fee figure shown at the time.",
         "*Your Ajo is saved as a draft. Nothing has started and nothing "
         "is owed.*",
         "Resume the wizard, or delete the draft.",
         "Draft creation, last-touched timestamp and resumption. A draft "
         "that is never resumed is not a failure, so it is measured as "
         "abandonment and not as a cancellation."],
        ["EC-062",
         "An invitation is accepted by nobody, so the position stays "
         "unfilled through the enrollment window.",
         "Enrollment is unaffected mechanically and does not wait: the "
         "window is exactly 5 days. Reminders go to the organiser about "
         "the unfilled position, and the Ajo cancels under EC-050 if the "
         "seat is still empty at the end.",
         "To the organiser: *This Ajo needs one more member to start. "
         "You have until DAY to invite someone.*",
         "Re-invite, or a replacement claim by an existing member, or "
         "cancellation with a full refund.",
         "Invitation sent, accepted or not, and the seat's fill state at "
         "the day-5 evaluation."],
        ["EC-063",
         "The round's funds are short, for example NGN 90,000.00 "
         "available against NGN 100,000.00 due.",
         "The payout enters HELD with the shortfall recorded. The payout "
         "is never silently reduced, and corporate funds are never used "
         "to close the gap (BR-018). The solvency assertion halts "
         "disbursement independently. No other member is charged extra "
         "(BR-015), and the defaulting member is never named (BR-014).",
         "To the recipient: *Your payout is on hold because the round is "
         "short by NGN 10,000.00. It is yours and it is safe - here is "
         "what is happening next.* To the organizer: the same shortfall "
         "figure and the recovery steps.",
         "The recovery process: reminders, a retry window, then "
         "write-off of the defaulting position and the funding decision "
         "for the remaining members, taken explicitly and recorded "
         "rather than absorbed silently.",
         "HELD event with the shortfall, the notification timestamps to "
         "both parties, and the eventual resolution. Counted as K-01, "
         "and the single most trust-sensitive number in the product."],
        ["EC-064",
         "A completed Ajo is opened again months later to check its "
         "history.",
         "Terminal is terminal: `COMPLETED` accepts no events. The Ajo "
         "is fully readable and completely frozen, so history can be "
         "checked and a statement produced, but nothing about it can "
         "change (BR-009).",
         "*This Ajo is complete. Its history is here, and it cannot be "
         "changed.*",
         "None needed; read-only history is the correct behaviour.",
         "Attempted writes against a terminal Ajo, which should be rare "
         "and are watched. A successful write to a terminal Ajo is a "
         "Sev-1."],
        ["EC-065",
         "A replacement is requested but no suitable candidate can be "
         "found.",
         "The replacement request stays open and visible, and the "
         "position is not silently filled by anyone. A replacement "
         "requires a real consenting member who passes verification; an "
         "unfilled seat remains unfilled rather than being filled to "
         "make a record look tidy.",
         "*We are still looking for someone to take this position. It "
         "stays reserved meanwhile.*",
         "The organiser continues recruiting; support can assist. The "
         "window is set by the round, not by the request.",
         "Open replacement requests with their age. Ageing requests are "
         "a recruitment signal for the product, and are reported rather "
         "than timed out silently."],

        ["EC-066",
         "An invitation is accepted after the Ajo has already become ACTIVE.",
         "Refused. Activation locks the roster: positions and membership are fixed at that moment, and membership is by invitation only (BR-002, BR-006). Nothing is consumed and no partial membership is created.",
         "*Enrollment for this Ajo has closed, so new members cannot join. Talk to the "
         "organiser about a replacement position.*",
         "The organiser raises a formal replacement request, which is a different act from "
         "joining and is reviewed rather than automatic.",
         "Refused attempt with the Ajo's activation timestamp. Acceptance after activation is "
         "either a stale link or an attempt to backfill a circle, and the two are told apart "
         "by the reason recorded."],
        ["EC-067",
         "An invitation is accepted when every position in the Ajo is already filled.",
         "Refused, because there is no seat to take. The refusal does not disclose who holds "
         "the positions, so an invitee cannot use it to enumerate a roster.",
         "*Every position in this Ajo is taken. Ask the organiser whether a position is "
         "opening up.*",
         "The organiser frees a position before activation, or invites into the next Ajo.",
         "Refusal with the fill state at the time. A run of acceptance attempts against a "
         "full Ajo is an organiser-side invitation-hygiene problem, reported as such."],        ["EC-068",
         "A replacement is requested for a member who has already "
         "received their own turn.",
         "Refused as a request to move money that has already been paid. "
         "The position history, the payment and the receipt are all "
         "immutable, and a replacement is only possible for a position "
         "that has not yet paid out.",
         "*This turn has already been paid, so it cannot be handed to "
         "someone else. Your receipt is here.*",
         "None. Any remaining obligation is settled or written off "
         "through the normal path.",
         "Refused request with the settlement reference. A replacement "
         "attempted after settlement is a fraud signal as well as a "
         "refusal (R4)."]
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.5
    {"t": "h2", "text": "19.5 Notification edge cases"},
    {"t": "p",
     "text": (
        "The notification catalogue in section 8 is canonical, and so is the one rule that "
        "governs how far it may be bent: *SMS reserved for money-critical and security "
        "events. Push and email for the rest.* Every case in this class asks the same "
        "question, which is how AJO.ng behaves when the cheapest channel fails for the "
        "people who can least afford to be missed."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-069",
         "Push delivery fails because the member has revoked notification permission, or "
         "has no app installed at all.",
         "The event is not lost. It is recorded as undelivered on push and the fallback "
         "chain for that event's class is used, so a money-critical event such as "
         "`contribution.overdue` or `payout.succeeded` still reaches the member by SMS, "
         "and everything else still reaches them by email.",
         "The member still finds out, on a channel they actually receive. Silence is never "
         "the design.",
         "Automatic channel fallback, then a support sweep for anything undelivered after "
         "24 hours.",
         "Delivery status per channel per event, with the fallback that was used. Undelivered "
         "money-critical events are a daily review item, not a metric to be averaged away."],
        ["EC-070",
         "SMS delivery fails: the number is unreachable, the gateway rejects, or the "
         "country prefix is not Nigerian.",
         "The SMS is recorded as failed and the in-app and email copies stand. A member "
         "whose number has repeatedly failed is asked in-app to update it, and the "
         "outreach sequence does not keep sending to a dead number.",
         "*We could not reach the number on your profile. Update it so you do not miss "
         "payment reminders.*",
         "In-app prompt, profile update, then a new attempt on the next event.",
         "Gateway responses retained with the provider reference. A sustained SMS failure "
         "rate is a gateway problem, not a member problem, and is escalated as such."],
        ["EC-071",
         "Email bounces permanently because the address is invalid or full.",
         "The bounce marks the address unusable, the event is retried on the fallback "
         "channel, and the member is prompted in-app to correct the address. Nothing is "
         "silently retried against a dead address.",
         "*We could not reach your email. Fix it here so your receipts keep arriving.*",
         "In-app prompt and profile update.",
         "Bounce classification retained. A member whose email and push both fail and whose "
         "SMS also fails is effectively unreachable, and that combination is alerted "
         "separately because it precedes a missed payment."],
        ["EC-072",
         "A member has switched off every optional channel, leaving only the mandatory "
         "ones.",
         "Money-critical and security events are not suppressible, because a preference "
         "setting must not be able to make a member unreachable for the events that "
         "protect their money. The preference screen states this in the member's own terms "
         "before they change it.",
         "*Turn off marketing updates any time. Payment and security alerts always reach "
         "you, because they protect your money.*",
         "None required; this is the intended behaviour.",
         "Preference changes retained with before and after values. An attempt to suppress a "
         "non-suppressible event is logged as rejected."],
        ["EC-073",
         "The same event is delivered twice, for example after a worker retry while the "
         "first attempt is still in flight.",
         "Deduplicated on the event, recipient and channel, so a member receives one "
         "message, not two. For money-critical events a duplicate is worse than a late "
         "one, because it reads as two separate obligations.",
         "One message. A member never receives two payment reminders for one due date.",
         "Automatic.",
         "Suppressed duplicates retained with both delivery attempts, so a broken worker "
         "retry is visible before members notice it."],
        ["EC-074",
         "A notification would expose one member's private information to another, for "
         "example naming a defaulting member to the whole membership.",
         "Notifications are addressed to named recipients from the catalogue, and payloads "
         "are built from a per-recipient view. A default is communicated to the organizer "
         "as a financial state, not as a story about a named person, and defaulting is "
         "never public (BR-014).",
         "Members are told what they need to act on and nothing about anyone else. An "
         "organizer sees that a round is short, not who stopped paying.",
         "Payload review before any template is added; a new event type requires an "
         "explicit disclosure review.",
         "Every notification records its recipient, its template, and the exact payload "
         "sent. This log is the evidence that no cross-member disclosure occurred, and it "
         "is the artefact a regulator or a complainant would ask for."],
        ["EC-075",
         "The notification queue backs up, so `contribution.due` at T-24h is delivered at "
         "T-3h and the T-2h reminder is late too.",
         "The event is delivered late rather than dropped, and lateness is recorded. A late "
         "reminder is still useful; a dropped one is indistinguishable from a system that "
         "forgot the member.",
         "*Your round is due at 18:00 today.* The message is simply late, and the message "
         "is still true.",
         "Queue drain, then support outreach for members whose due window has closed with "
         "no delivered reminder.",
         "Queue depth and per-event delivery lag. A recurring lag on money-critical events is "
         "an S3 that becomes an S2 the first time a member misses a deadline because of "
         "it."],
        ["EC-076",
         "A member's contact details are updated at the same moment an event is being sent, "
         "so a message goes to an address the member has just abandoned.",
         "The send uses the address held at dispatch time, and the new address is used for "
         "subsequent events. If the message contains a money-critical instruction, the "
         "member is alerted to the change from the new channel too, because a payment link "
         "sent to a compromised mailbox is a real attack path.",
         "*The email or phone on your account was changed. If this was not you, tell us "
         "immediately.*",
         "Automatic security notice, then support or `risk_officer` review.",
         "Contact-detail change with before and after values, actor, IP and device. Combined "
         "with a payment, this pairing is a high-signal fraud indicator."],
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.6
    {"t": "h2", "text": "19.6 Authorization and role edge cases"},
    {"t": "p",
     "text": (
        "There are exactly six roles, and the interesting failures are not the ones where "
        "an attacker guesses an endpoint. They are the ones where a legitimate person with "
        "a real role tries something that is forbidden to that role, and the system has to "
        "refuse them cleanly and leave a record."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-077",
         "A member requests an Ajo, contribution, payment or dispute belonging to another "
         "member, either by editing an id or by replaying a captured request.",
         "Ownership is enforced server-side on every object access, not only in the client. "
         "The response reveals nothing about whether the object exists, so a probe cannot "
         "enumerate members, Ajos or payments.",
         "*You do not have access to that record.* The member is not told who does.",
         "None needed; the request never reaches the object.",
         "Denied attempts with actor, role, target and reason. A pattern of cross-account "
         "probes from one account is a security event (R4)."],
        ["EC-078",
         "An organizer requests a payout release while the round's funds are not fully "
         "collected or not yet available.",
         "The release is refused. A payout is released only when the required funds are "
         "fully collected and available; it is never reduced, and corporate funds are never "
         "used to cover a gap (BR-018, BR-020). The organizer sees the funding position, "
         "which is their own information, and the recovery process continues.",
         "*The round is short by NGN 4,000.00, so the payout cannot be released yet. Here is "
         "what is happening next.*",
         "The normal recovery process, with the short position and its cause visible to the "
         "organizer.",
         "Refused release with the funding position at that instant. Repeated organizer "
         "pressure to release an unfunded payout is retained, because it is a pressure "
         "pattern we would rather see than infer."],
        ["EC-079",
         "A support agent attempts to move money: refund a payment, adjust a balance, or "
         "release a payout.",
         "Not possible. Support never moves money (BR-023) and the organiser never handles "
         "the money either (BR-022). Support can see, explain, escalate and trigger "
         "processes, but every money movement belongs to the two permitted events "
         "(BR-032).",
         "*I can see exactly what happened and get it moving, but the movement itself is "
         "done by the system, not by me.* The member is told the truth about who did what.",
         "Escalation to `risk_officer` where judgement is needed.",
         "Denied attempts with actor and role. This is one of the highest-value audit "
         "trails in the product, and a pattern of attempts is a personnel issue that the "
         "log is designed to surface."],
        ["EC-080",
         "A `risk_officer` attempts to decide a member dispute, or a `support` agent "
         "attempts to close a risk case.",
         "Refused. The two functions are separated: disputes are decided on evidence by the "
         "role entitled to decide them, and risk decisions are recorded as risk decisions "
         "with a distinct reason code. A role that owns a case cannot also be the role that "
         "clears it.",
         "The dispute proceeds with the correct decision-maker. A member never receives a "
         "decision that was later found to be made by the wrong role.",
         "Correct reassignment; the case history records the rejection and the reassignment.",
         "Denied attempts and the resulting reassignment, with actor and role on both."],
        ["EC-081",
         "A `super_admin` attempts to edit or delete a ledger entry, or to correct a "
         "transaction by changing it in place.",
         "Not possible, for any role, at any privilege level, through any interface. The "
         "ledger is append-only with no `updated_at` and no `deleted_at` (BR-025). "
         "Corrections are made only by posting a reversing entry, which is itself a full, "
         "balanced, auditable transaction.",
         "*The system does not allow that. What we can do is post a correcting entry so the "
         "record shows exactly what happened and why.*",
         "Reversing entry, always.",
         "Denied attempts with actor, role, target transaction and the entry that was "
         "requested. The absence of an `UPDATE` or `DELETE` path in the ledger is asserted "
         "by a test, so the guarantee is enforced rather than remembered."],
        ["EC-082",
         "An authenticated account with no active role assignment attempts any privileged "
         "action.",
         "Refused with a distinct 'no role assigned' reason, which is different from 'not "
         "authorised'. An account without a role is an incomplete setup, and it is visible "
         "in the admin console as such rather than as a suspicious actor.",
         "Not applicable; the account has no product surface of its own.",
         "Role assignment, then normal access.",
         "Recorded as an administrative gap, not a security incident, so that it is fixed "
         "rather than investigated."],
        ["EC-083",
         "A role is revoked while the holder's session is still live.",
         "The change takes effect immediately. Authorization is evaluated per request "
         "against current role assignments, not captured into a session at login, so "
         "revocation does not wait for an expiry.",
         "The next action fails cleanly and the user is told their access changed, with the "
         "route to request it back.",
         "Re-assignment, which creates a new audit event rather than resurrecting the old "
         "one.",
         "Revocation with actor, target, reason and the exact time it took effect, plus the "
         "first denied request afterwards as proof it was not merely theoretical."],
        ["EC-084",
         "An invitation token is forwarded and accepted by someone other than the "
         "invitee, or the same token is used twice.",
         "Membership is by invitation only (BR-006, BR-029). A token is single-use and bound "
         "to the invited contact details; acceptance by a different person requires identity "
         "verification, which is the anti-pyramid control. A second acceptance is rejected.",
         "*This invitation was already used, or it was issued to a different number. Ask your "
         "organiser for a new one.*",
         "A new invitation from the organizer, and a risk event for the mismatch.",
         "Token use with the verified identity that used it, the mismatch where one exists, "
         "and reuse attempts. Pyramid recruitment attempts are detected here first."],
        ["EC-085",
         "An organizer's account is deactivated while their Ajo is ACTIVE.",
         "The Ajo is not orphaned. It is frozen with a recorded reason and the members are "
         "told, because a half-run Ajo is worse than a paused one. Frozen, not cancelled: "
         "the members' positions and money are preserved.",
         "*Your organiser is no longer reachable, so we have paused this Ajo to protect your "
         "money. Nothing is lost and support is on the case.*",
         "Transfer of organiser role to a co-organiser or a member with consent, then "
         "unfreeze; failing that, the cancellation and refund path under EC-058.",
         "Freeze with reason, the member notification timestamps, and the transfer or "
         "cancellation that followed. Orphaned-Ajo detection is a standing dashboard, "
         "because an organiser who simply stops answering is the expected failure."],
        ["EC-086",
         "The organiser tries to remove a member after activation.",
         "Refused. Removal is a pre-activation action only (BR-007), and "
         "a member cannot be expelled after activation; the position "
         "must change through a formal replacement or transfer request, "
         "and no one may exit unilaterally (BR-003).",
         "*Members cannot be removed once an Ajo is active. You can "
         "request a replacement instead, and the member has to agree to "
         "it.*",
         "A replacement request, which the departing member and the "
         "replacement must both consent to.",
         "Refused attempt with actor and role. Repeated attempts to "
         "remove members post-activation are reviewed as conduct."],
        ["EC-087",
         "A member disputes that they were ever frozen.",
         "The freeze and its actor, role, reason and duration are read "
         "back to them from the audit log. A freeze that cannot be "
         "evidenced is treated as a support error and reversed, not "
         "defended.",
         "*Here is exactly when this was applied, by whom, and why. If "
         "it was not you, we will lift it now.*",
         "Reversal on evidence, or confirmation on evidence. Either way "
         "the member is told which it is.",
         "The audit trail is the mechanism here, which is why "
         "`risk_officer` freezes carry a mandatory reason: an "
         "unevidenced freeze is a decision nobody can defend afterwards."],
        ["EC-088",
         "A password reset is requested on a frozen account.",
         "Permitted, because locking someone out of their own recovery "
         "path is a denial of service, not a control. The reset "
         "completes, all sessions are revoked, and the freeze itself "
         "remains. Recovery of access and resolution of the risk are "
         "separate decisions.",
         "*Your password has been reset and your other devices are "
         "signed out. The review of your account continues separately.*",
         "Identity verification to complete recovery where the member "
         "cannot prove ownership.",
         "Reset on a frozen account, which is also a signal: someone "
         "attempting recovery on a risk-flagged account is worth a look."],
        ["EC-089",
         "A risk rule fires on an honest member, for example a shared "
         "family phone or a shared bank account.",
         "The member is told a review is happening and why, in plain "
         "terms, and is not left guessing at a freeze. A false positive "
         "never becomes a silent restriction, and the outcome of every "
         "review is recorded as a hit or a miss so the rules are "
         "measured against reality.",
         "*We are checking one detail on your account. Nothing is wrong "
         "with your money and you can keep using your Ajos.*",
         "Review outcome, normally a release, and a correction of the "
         "pattern data that caused the false positive.",
         "Every rule hit with its outcome. Rule precision is a measured "
         "product metric: a rule that fires mostly on honest members is "
         "a rule that needs retuning, not a member base that needs "
         "suspicion."],
        ["EC-090",
         "A dispute is raised and the counterparty never responds.",
         "The response window passes and the case is decided on the "
         "evidence available, with the absence of a response recorded as "
         "a fact rather than as an admission. The decision states what "
         "was considered and what was not received.",
         "To the member who raised it: *We asked the other party to "
         "respond and did not hear back, so we have decided on the "
         "evidence we have.*",
         "Decision on the record, appealable, with the non-response "
         "disclosed to both parties.",
         "Case with the window, the notifications sent, and the decision "
         "basis. Unanswered cases are reported by counterparty, because "
         "a party who never answers is a pattern, not an accident."],
        ["EC-091",
         "Dispute evidence is malicious, oversized or of a type we will "
         "not accept.",
         "Rejected at upload with a stated reason, and the case "
         "continues with the evidence that was accepted. A file that "
         "will not be scanned is never stored, and an oversized file is "
         "never buffered into a memory problem.",
         "*That file could not be accepted. Send a photo or a PDF under "
         "10 MB and your case continues.*",
         "Re-upload, or submission through support for a member who "
         "cannot meet the constraint.",
         "Rejected upload with reason and size. A repeated pattern of "
         "rejected uploads on one case is a conduct signal."],
        ["EC-092",
         "A dispute alleges money that reached the provider and was "
         "never credited to the member.",
         "Treated as a reconciliation matter first and a disagreement "
         "second. The provider's records are the evidence, the member's "
         "account is corrected if the member is right, and a confirmed "
         "loss is recorded as a loss rather than argued about.",
         "*We are checking this against the payment partner's records. "
         "If money left your account and did not reach us, that is ours "
         "to fix.*",
         "Reconciliation by reference, then a correction entry, and "
         "recovery from the provider where applicable.",
         "The dispute, the provider evidence, the conclusion and any "
         "correcting entry. 'It went to the provider' is a claim AJO.ng "
         "must be able to test, not a claim it has to accept."],
        ["EC-093",
         "A member raises many disputes, or disputes almost everything.",
         "Rate-limited and reviewed. Nothing about a legitimate dispute "
         "is weakened by volume, but a member cannot use the dispute "
         "path to stall payouts indefinitely: a dispute is not a reason "
         "to hold money once its basis is answered (BR-017).",
         "To the member: *You can raise a dispute on this Ajo. Repeated "
         "disputes on the same facts will not change the answer, and the "
         "payout will not wait for them.*",
         "The decision on the merits, and the payout proceeding once the "
         "merits are answered.",
         "Dispute counts per member with outcomes. A high-volume filer "
         "is a support cost and a signal, and is handled as a process "
         "question, not as a member being silenced."],
        ["EC-094",
         "A phone number that is already an active member of the same "
         "Ajo is entered as a new member.",
         "Refused. One identity takes one account (BR-030) and one "
         "position per Ajo, so the same person cannot occupy two seats "
         "in a circle that pays out on rotation. The check is on "
         "verified identity, not on the number alone.",
         "*This number is already in this Ajo. One person takes one "
         "position.*",
         "None; the second position is not available to the same person.",
         "Refused attempt with both records. Repetition is a "
         "pyramid-scheme signal (R4) and is reviewed."],
        ["EC-095",
         "A default is recorded and the member later disputes that it "
         "should have been.",
         "The dispute is decided on the record: the due time, the "
         "reminders sent, the grace period and the timestamps, all of "
         "which are computed server-side and cannot be moved by a device "
         "clock. If the default was wrong, the state is corrected and "
         "the recovery is applied as though it had never happened.",
         "*Here is what happened and when, including the reminders you "
         "were sent. If it was wrong, we will correct it and your Ajo "
         "continues.*",
         "Correction with the audit evidence, and re-instatement of the "
         "contribution.",
         "The full default chain and the dispute outcome. A reversed "
         "default is reported as a rule or timing fault, not as a "
         "member's problem."],
        ["EC-096",
         "An organiser asks AJO.ng to deduct a defaulting member's "
         "shortfall from the other members.",
         "Refused, without exception and without partial fulfilment. "
         "Other members are never charged extra without their explicit "
         "consent, and the platform does not do it on their behalf "
         "either (BR-015). The organizer is told what the actual options "
         "are.",
         "*We cannot take one member's shortfall from the others. Here "
         "is what the recovery process does instead.*",
         "The recovery process, and a recorded funding decision for the "
         "round.",
         "The request itself, the refusal, and what was offered instead. "
         "A large volume of these requests is an indicator about how the "
         "product is being explained on the ground."],
        ["EC-097",
         "A defaulting member cannot be reached at all on any channel.",
         "The recovery process is exhausted and recorded as exhausted. "
         "The position is written off only through that recorded path, "
         "never silently, and the shortfall then faces the funding "
         "question in EC-063 rather than being spread.",
         "To the organiser: *We could not reach this member on any "
         "channel. Here is where this stands and what you can do about "
         "it.*",
         "Support outreach where an address exists, then the written-off "
         "path, then the round's funding decision.",
         "Contact attempts per channel with their outcomes. A member who "
         "is genuinely unreachable is a support gap, so the exhaustion "
         "is reported to a human rather than closed by the system."],
        ["EC-098",
         "An organiser asks AJO.ng to tell the other members who has not "
         "paid.",
         "Refused. Defaulting is private between the member, the "
         "organizer and platform risk, and no notification payload ever "
         "names a defaulter (BR-014). The organizer is given the funding "
         "position, which is the information they need to act.",
         "*We can tell you whether the round is covered. We will not "
         "tell the group who has not paid, and neither will the app.*",
         "The funding position and the recovery process for the member "
         "in question, handled privately.",
         "The request and the refusal. The distinction between a "
         "financial state and a person's behaviour is the thing being "
         "protected, so the log records which was served."],
        ["EC-099",
         "A platform-wide emergency stop of all money movement is executed during a "
         "security or solvency incident.",
         "All new authorisation attempts, disbursements and refunds stop at once. Ajo "
         "state is untouched, no money is moved by AJO.ng itself, and in-flight "
         "authorisations are either allowed to settle or reversed by the provider rather "
         "than silently dropped. The stop is scoped, timestamped, ordered by `super_admin` "
         "with a `risk_officer` countersign, and time-boxed, because an open-ended stop is "
         "itself a loss.",
         "*We have paused payments and payouts while we fix a problem. Nothing has been "
         "taken from you, your Ajo has not changed, and we will tell you the moment it is "
         "safe to move money again.*",
         "A documented incident runbook with a named owner, a fixed review interval, and a "
         "pre-agreed resume or wind-down plan. Resumption is a separate recorded order, "
         "never the automatic expiry of the stop.",
         "Order, countersign, scope, affected flows, the in-flight transactions caught at "
         "the moment of the stop, and the resume order. A platform-wide stop is a Sev-1 "
         "event and its duration is reported as an incident metric."]
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.7
    {"t": "h2", "text": "19.7 Data integrity edge cases"},
    {"t": "p",
     "text": (
        "This class is the arithmetic of the product. Money columns are always `bigint` "
        "kobo, never `float` or `numeric` (BR-031); business tables are versioned for "
        "optimistic concurrency; ledger tables are append-only. Those three rules are what "
        "make the rest of the system auditable, and this class is where they are tested "
        "against reality."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-100",
         "Two requests modify the same record concurrently, for example the organizer edits "
         "the schedule while a member is claiming a position.",
         "Detected by the version column. The second writer is rejected with a conflict, "
         "and the client refetches and shows the member what actually happened. No silent "
         "last-write-wins, because last-write-wins on money is how a member loses a "
         "contribution without being told.",
         "*Someone just updated this Ajo. Here is the current version - your change was not "
         "saved.*",
         "Refetch and re-apply deliberately.",
         "Rejected conflict with both versions and actors. A high conflict rate on one record "
         "is a concurrency design smell and is reviewed."],
        ["EC-101",
         "The solvency assertion fails: escrow cash no longer equals the sum of what is owed "
         "to members.",
         "Disbursement halts immediately and automatically. This is the control the whole "
         "ledger depends on: skipping the payout recognition step drains escrow against a "
         "liability that was never raised, and the assertion is designed to catch exactly "
         "that (BR-020, BR-021). A halt is never overridden to make a payout succeed on "
         "time.",
         "Nothing is said about internal assertions. Affected members receive a truthful "
         "delay message: the payout is pending, it is safe, and here is when we will "
         "update you.",
         "Engineering investigation, then a correcting reversing entry, then an assertion "
         "harness replay before disbursement resumes.",
         "Sev-1 alert with the assertion, the escrow balance, the outstanding obligation and "
         "the transaction that breached it. K-01 under-funded payouts counts these, so a "
         "halt is a visible trust event, not a hidden engineering nuisance."],
        ["EC-102",
         "A ledger posting is attempted against a round that has already settled and paid "
         "out.",
         "Rejected. A settled round accepts no further postings, and no entry is ever added "
         "to a closed period. A correction, if genuinely needed, is a reversing entry in a "
         "current period with an explicit link to the original.",
         "None; this should never be visible to a member.",
         "None required; the rejection is the control.",
         "Rejected posting with actor, role and target. Any successful posting into a "
         "settled period is a Sev-1 and a test failure."],
        ["EC-103",
         "A soft-deleted record is referenced by a new transaction, for example a "
         "contribution whose member row was deleted out of band.",
         "Rejected. Money-moving records are not deletable at all, and a soft delete is "
         "never treated as absence by the money path. A contribution in any non-terminal "
         "state must resolve to a real member.",
         "*We hit a records problem on this Ajo. Your money is accounted for and support is "
         "looking into it now.*",
         "Restore the record; the reference proves the deletion was illegitimate.",
         "Rejected reference plus the originating soft delete with actor and reason. A "
         "soft delete touching a money record is alerted the moment it happens."],
        ["EC-104",
         "A report or aggregate spans a timezone boundary, so a contribution lands in the "
         "wrong day or month bucket.",
         "Reporting is computed in UTC and labelled in the Ajo's declared zone, and the "
         "figure shown always carries the zone it was computed in. Money totals are never "
         "bucketed by client-supplied local time.",
         "*Your Ajo runs on WAT, so the deadline you see is in WAT wherever you are.*",
         "Recompute the affected period; historical reports are versioned so the correction "
         "is visible.",
         "Zone and period boundary recorded with every aggregate. An unexplained movement "
         "between periods is almost always this, and the label is what resolves it in "
         "minutes instead of days."],
        ["EC-105",
         "An export, statement or report renders kobo as naira, or divides by a hundred "
         "twice.",
         "The internal representation is a kobo integer, and formatting happens once at the "
         "boundary. A statement shows the same numbers as the receipt and the ledger for "
         "the same transaction, and a mismatch is a Sev-2 that blocks the export until "
         "fixed.",
         "The member's statement reconciles exactly with their receipts, line for line. "
         "Where it does not, we withdraw the export rather than let them act on it.",
         "Regenerate after the fix; a withdrawn export is retracted, not quietly replaced.",
         "Export job, template version and a checksum of the rendered figures per statement, "
         "so a formatting change is detectable after the fact."],
        ["EC-106",
         "A schema migration runs while writes are in flight, and a transaction fails "
         "mid-migration.",
         "Migrations are expand-and-contract: additive first, backfill second, enforcement "
         "last, with the old path live throughout. A failed migration rolls back without "
         "partial state, and the solvency assertion keeps running as a guard.",
         "No member is affected by a migration. If something is unavailable, it is "
         "degraded and says so.",
         "Rollback and retry; the payment path is never the last thing switched over.",
         "Migration id, phase, row counts, and assertion results before and after. An "
         "unrecorded migration is treated as an incident."],
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.8
    {"t": "h2", "text": "19.8 Security and privacy edge cases"},
    {"t": "p",
     "text": (
        "Ajo holds real money belonging to people who have often never held a formal bank "
        "account before, so the security model has to protect someone who does not yet know "
        "what a breach looks like. That is why several cases here are about explaining a "
        "security event in plain language to a member who may be alarmed, rather than only "
        "about blocking an attacker."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-107",
         "An attacker resets a member's password using the member's own email account.",
         "The reset link is single-use and short-lived, and completing a reset revokes every "
         "other session and notifies the member on a separate channel with the device and "
         "location of the new sign-in. A password reset is treated as a security event, not "
         "as account maintenance.",
         "*Your password was changed and we have signed out your other devices. If this was "
         "not you, tell us now and we will secure the account and your Ajos.*",
         "The member reclaims the account, and `risk_officer` reviews the Ajos the account "
         "touched while it was under hostile control.",
         "Reset request and completion with source, IP, device and time; sessions revoked; "
         "the review of everything the account did in the exposure window. A reset followed "
         "by a payout change is a high-signal sequence."],
        ["EC-108",
         "The member's phone number is re-issued to someone else after a SIM swap, so one-time "
         "codes arrive at the wrong person.",
         "One-time codes are bound to the session and the device that requested them, are "
         "single-use, and expire quickly. A code that arrives at a new number for a new "
         "device is a signal: the account is put into a monitored state and the member is "
         "not silently logged out of a payment they were in the middle of.",
         "*Your number was changed at your network. We noticed. Confirm it was you to keep "
         "paying, or tell us and we will help you get back in.*",
         "Alternative verification, or in-person support with identity verification.",
         "New-number detection with the change source, the affected flows, and the resolution. "
         "SIM swap is a known Nigerian fraud pattern, so it is modelled rather than assumed "
         "away."],
        ["EC-109",
         "Credential stuffing or brute force against a member account.",
         "Rate-limited by account and by network, with progressive backoff, and no "
         "distinction between failure messages that would reveal whether an account exists. "
         "A sustained attack triggers an account-protection step that does not lock a "
         "legitimate member out of their own money.",
         "*We are protecting your account. We have asked you to confirm it is you.*",
         "Identity verification to restore access; support can assist a member who is locked "
         "out of funds they can see.",
         "Failed attempts with source and pattern. A blocked account that holds funds is "
         "always reviewed by a human, because an overzealous lock that strands someone's "
         "money is its own harm."],
        ["EC-110",
         "A session token is stolen and replayed after the member has logged out.",
         "Logout revokes the session server-side, so a stolen token is dead immediately "
         "rather than until natural expiry. Refresh tokens are rotated on use, and reuse of a "
         "rotated token revokes the whole family as a probable theft.",
         "The member's logout actually works, which is the entire point of having one.",
         "Re-authentication.",
         "Token family reuse detections with the session chain. This is a standard control "
         "with a non-standard consequence here, because the session holds access to real "
         "money."],
        ["EC-111",
         "An identity document is uploaded that belongs to someone else, or is a "
         "photograph of a photograph, or is unreadable.",
         "The check is failed closed and the case goes to a human reviewer. Verification is "
         "not a formality that can be passed by a convincing image, and mandatory versus "
         "threshold-based verification remains open decision **D-04** so the policy is "
         "stated as pending, not as settled.",
         "*We could not confirm your identity from that document. Try again, or we will "
         "review it another way - here is what we need.*",
         "Resubmission with clearer guidance, or manual review, or an alternative route so a "
         "member is never permanently stuck without a way to participate.",
         "Document hash, check result, reviewer, decision and reason. Documents are retained "
         "for a defined period and then deleted; that period is a stated policy, not an "
         "unbounded archive."],
        ["EC-112",
         "An organizer uses the members view to harvest phone numbers or identity documents "
         "for unrelated purposes.",
         "Organizers see what they need to run the Ajo and no more. Identity documents are "
         "never exposed to organizers at all, and member contact details are shown only "
         "where the Ajo genuinely requires coordination.",
         "*Your number is shared with the organiser of this Ajo so the round can run, and "
         "with nobody else.*",
         "Report and revoke, with a recorded case.",
         "Access to member data logged per request with purpose, and an unusual-volume alert "
         "on the members endpoints. Organizer access to a large member list is a standard "
         "abuse pattern."],
        ["EC-113",
         "An admin browses user records without a legitimate purpose, or exports them in "
         "bulk.",
         "Admin access is role-scoped and purpose-scoped, with bulk export disabled by "
         "default and enabled only by `super_admin` with a recorded reason. Support sees "
         "what is needed to answer the question in front of them.",
         "Not applicable; this is an internal control.",
         "Revocation of the access and review of what was read.",
         "Every administrative read and export retained with actor, role, scope and reason. "
         "Admin logs are readable by all admin roles and writable by none, so the trail "
         "cannot be edited by the person it describes."],
        ["EC-114",
         "An unauthenticated or incorrectly scoped endpoint exposes member or financial "
         "data, for example a receipt endpoint that trusts an id alone.",
         "Every endpoint is authenticated and object-scoped, and receipts are served to the "
         "payment's owner and to authorised staff only. Unauthenticated surfaces exist "
         "exactly where the canonical API says they do, and that is the payment webhook.",
         "A member's receipt is not something a stranger with a guessed id can read.",
         "Revocation of the exposure, notification if data was accessed, and a fix plus a "
         "regression test.",
         "Access-denied and 4xx/5xx patterns by endpoint retained. A public exposure of "
         "financial data is a Sev-1 with a notification obligation, and that obligation is "
         "assessed immediately rather than at legal review."],
        ["EC-115",
         "Sensitive data lands in application logs: a full phone number, an identity "
         "document, a token or a provider secret.",
         "Redaction at the logging layer, not at each call site, with a denylist that fails "
         "the build when a new sensitive field is added without redaction. Logs are not a "
         "convenient place to keep a copy of a member's data.",
         "Not applicable; this is an internal control.",
         "Rotation of anything exposed, and log scrubbing where retention allows.",
         "Log content is itself audited, and any occurrence of a denylisted field in a log "
         "is an alert rather than a curiosity."],
        ["EC-116",
         "A member hands their unlocked phone to another person, who views their Ajos or "
         "initiates a payment.",
         "Sensitive actions require re-authentication, and payment initiation always shows "
         "the amount, the fee and the total before anything is charged, so a second pair of "
         "hands on the phone cannot commit an invisible amount. Biometric or PIN "
         "confirmation guards payment initiation.",
         "Even with someone's phone in their hands, the amount is shown, confirmed and "
         "recorded before money moves.",
         "Reversal through the normal refund path, and instant revocation of the other "
         "device's session.",
         "New-device and re-authentication events. Shared-device use is common and not "
         "inherently malicious, so the control is friction at the money moment rather than a "
         "refusal to let anyone use the phone."],
        ["EC-117",
         "A member and an organizer collude, for example to claim a position and collect a "
         "payout that the rest of the group expected someone else to receive.",
         "Pattern detection rather than proof: linked accounts, repeated invitation flows "
         "between the same people, position claims that contradict typical behaviour. A "
         "flagged case may be frozen with a recorded reason and a member-facing "
         "notification, never silently delayed.",
         "*This Ajo is paused while we confirm a detail. Your position and your money are "
         "intact.*",
         "`risk_officer` decision with a reason code, appealable through a dispute.",
         "Risk events with the signals that fired, the decision, the rationale and the "
         "outcome. A freeze imposed without notifying the members would breach the "
         "no-hidden-payout-failure rule, so the notification is part of the control."],
        ["EC-118",
         "A member requests deletion of their account and data while they hold money in an "
         "active Ajo, or outstanding obligations.",
         "Deletion is refused while any obligation, held payout or open dispute exists, and "
         "the member is told exactly what stands in the way and what would release it. "
         "Financial records are retained for the period the law and the provider arrangement "
         "require; the retention rule is a stated policy, not a permanent archive by "
         "default.",
         "*You cannot close your account while you are in an active Ajo. Finish the round, or "
         "ask us about replacing your position, and we will help.*",
         "Position replacement, then deletion once nothing is outstanding.",
         "Deletion requests, refusals with the blocking reason, and the retention clock. A "
         "refusal to delete is a decision we owe the member an explanation for."],
        ["EC-119",
         "A registration is attempted with an email or phone number that "
         "already belongs to an account.",
         "Refused with a single message that does not reveal whether it "
         "was the email or the phone that matched. One identity takes "
         "one account (BR-030); AJO.ng does not run a second account on "
         "the same person, and does not offer to take over the existing "
         "one by email, which is the standard account-takeover path.",
         "*That number or email is already registered. Try signing in, "
         "or contact us if it is not you.*",
         "Sign in, or support-assisted recovery with verification.",
         "The refusal, the source, and any attempt count against the "
         "address. Probing for whether an identity is registered is "
         "itself recorded."],
        ["EC-120",
         "Registration is completed on a public or shared device, such "
         "as a cyber cafe or a borrowed phone.",
         "The account is usable, but the session is treated as "
         "untrusted: sensitive actions require re-authentication, and "
         "the device is not silently trusted for later money movement. "
         "The member is told the device is remembered and how to remove "
         "it.",
         "*You signed in on a shared device. You can sign out of it here "
         "at any time.*",
         "Session revocation from the security screen, which the member "
         "can reach without support.",
         "Device fingerprint and trust state with each session. "
         "Shared-device use is common and not malicious, so the control "
         "is friction at the money moment."],
        ["EC-121",
         "The email verification link is not clicked within its validity "
         "window.",
         "The link expires and a new one is issued on request. No "
         "account is created by an unverified address, and the member is "
         "not left with a half-state they cannot see; the app tells them "
         "what is outstanding and what to do.",
         "*That link has expired. We have sent you a new one - check "
         "your email.*",
         "Resend, then an alternative verification route if email is not "
         "usable.",
         "Issue, expiry and resend counts. A member repeatedly unable to "
         "complete verification is an onboarding defect and is measured "
         "as one."],
        ["EC-122",
         "The user abandons onboarding part-way through, after an "
         "account exists but verification is incomplete.",
         "The account exists but cannot join an Ajo or hold a position, "
         "because membership requires verification. It is not deleted, "
         "and it is not counted as a member. The user can return to the "
         "same point and continue.",
         "*Your account is saved. Finish verifying and you can join an "
         "Ajo.*",
         "Resume, or account deletion through the same path a fully "
         "verified member would use.",
         "Incomplete accounts with their age. A large number of accounts "
         "stuck at one step is a design problem with that step, not a "
         "user problem."],
        ["EC-123",
         "The user is identified as a minor, or as acting on someone "
         "else's behalf.",
         "The account is not used to open or hold a position. A minor's "
         "account is treated as a supervised account with no financial "
         "commitments of its own, and someone acting for another person "
         "is routed through the invitation path, because AJO.ng has no "
         "power of attorney and will not pretend to.",
         "*AJO.ng is for adults acting for themselves. If this is for "
         "someone else, ask their organiser for an invitation.*",
         "The invitation path, or a supervised account with an adult.",
         "The determination and the route taken. Age verification "
         "thresholds are part of D-04 and are not invented here."],
        ["EC-124",
         "An invitation token has expired.",
         "Acceptance is refused and the invitation itself is not "
         "consumed, so the organiser still holds the seat. The message "
         "says expired and says who can renew it, because a member "
         "should not have to guess whether to chase the organiser or the "
         "platform.",
         "*This invitation has expired. Ask the organiser to send a new "
         "one.*",
         "The organiser resends. A resend never creates a second "
         "membership or a second position.",
         "Token issue, expiry and resend. Resend volume per organiser is "
         "a recruitment-health signal."],
        ["EC-125",
         "An invitation token is revoked by the organiser before it is "
         "used.",
         "Refused immediately, with no indication of whether the seat is "
         "still free. Revocation is a legitimate pre-activation "
         "organiser action, and the response reveals nothing that would "
         "let a revoked recipient probe the roster.",
         "*This invitation is no longer valid.*",
         "Contact the organiser. A member who believes a revocation was "
         "not authorised is an account-takeover signal, and support "
         "handles it as one.",
         "Revocation with actor, role and time, and the refused attempt "
         "from the token's holder."],
        ["EC-126",
         "The invitee declines the invitation.",
         "The seat reopens within the enrollment window and the decline "
         "is recorded without a reason being demanded. The organiser is "
         "told the position is open, not why it is open, because a "
         "decline is private.",
         "To the invitee: *No problem - you are not joining. Nothing "
         "further is needed.* To the organiser: *One position is open "
         "again.*",
         "Re-invite if the relationship allows, or the Ajo proceeds "
         "without that position.",
         "Decline with a timestamp and no stored reason. A seat that "
         "reopens is the signal the organiser needs; the reason is not "
         "the platform's to keep."],
        ["EC-127",
         "The invitee is not verified when they try to accept the "
         "invitation.",
         "Refused with the specific missing step named. Acceptance "
         "requires a verified email and a verified phone, and identity "
         "verification above the configured threshold, which is open "
         "decision D-04 and therefore stated as pending rather than "
         "assumed either way.",
         "*Verify your email and phone number and you can accept. Here "
         "is exactly what is left to do.*",
         "Complete verification, then accept. The invitation is not "
         "consumed by the attempt.",
         "Refusal with the missing steps. Repeated refusals at this "
         "point are an onboarding-friction signal worth more than the "
         "individual refusal."],
        ["EC-128",
         "A payout is requested to a destination that is not in the "
         "recipient's own name.",
         "Refused. AJO.ng does not pay third parties, does not pay a "
         "business account for an individual, and does not accept a "
         "changed destination on a phone call. The recipient's own "
         "verified account is the only destination.",
         "*We can only send this to an account in your own name. Add "
         "your own account and we will release it there.*",
         "The recipient adds and verifies their own destination, then "
         "the payout proceeds.",
         "Refused destination with the name on the account. A "
         "third-party destination request is a fraud pattern (R4) and is "
         "reviewed, not just refused."],
        ["EC-129",
         "Reset requests are spammed across a list of email addresses.",
         "Rate-limited per requester and per address, with responses "
         "that do not reveal whether an address has an account. A list "
         "of resets is an enumeration attempt, so it is throttled, "
         "recorded and alerted rather than served.",
         "Nothing; the requester gets a generic response either way.",
         "None needed for the member; the enumeration attempt is "
         "escalated.",
         "Volume, source and pattern, with an alert threshold. A "
         "sustained run is a security event even though no single "
         "request is remarkable."],
        ["EC-130",
         "A reset token is older than its validity window.",
         "Refused, and the token is consumed on use so it cannot be "
         "retried. A new token is issued only on a new request, which is "
         "why a long-expired link never becomes a working one later.",
         "*That reset link has expired. Request a new one and we will "
         "send it.*",
         "A new request.",
         "Token issue, use, expiry and the number of stale attempts. A "
         "stale-token attempt on an account with money in it is "
         "reviewed."],
        ["EC-131",
         "The chosen new password appears on a breached-password list.",
         "Refused at the point of choosing, not after it is set. The "
         "message says the password is too common rather than where it "
         "was found, and AJO.ng does not send a member's new password "
         "anywhere, including to itself.",
         "*That password has appeared in a data breach. Choose something "
         "no one else would.*",
         "Choose another password.",
         "The rejection, without the candidate value. Rejected "
         "candidates are never logged in full, because a log of "
         "attempted passwords is a log of secrets."],
        ["EC-132",
         "The reset email cannot be delivered, or the member cannot see "
         "it.",
         "Detected from the bounce, and recovery does not stop there. A "
         "member locked out of an account holding money is offered a "
         "verified alternative route rather than being told to check "
         "their inbox again.",
         "*We could not reach that email. We will get you back in "
         "another way - here is what we need from you.*",
         "Verification-assisted recovery through support.",
         "Bounce plus the alternative route offered. A member who cannot "
         "complete recovery is an S2, because the consequence is access "
         "to their own money."],
        ["EC-133",
         "The member has lost access to both email and phone.",
         "Recovered through in-person identity verification, never "
         "through a channel that assumes possession of a lost inbox. "
         "Support cannot bypass identity checks to be helpful, and a "
         "request for an exception is escalated to `risk_officer` rather "
         "than granted.",
         "*We will need to verify you in person before we restore "
         "access. Here is where and what to bring.*",
         "In-person verification, then restoration and revocation of "
         "everything that was accessible before.",
         "The recovery with its evidence and the officer who approved "
         "it. This path is the most abused in the industry, so it is the "
         "most heavily evidenced."],
        ["EC-134",
         "Fraud is suspected on a member who has already been paid out.",
         "Investigated as an investigation, not as a clawback. AJO.ng "
         "does not recover a paid-out sum from a member on suspicion, "
         "and does not reverse a settled payout to make a case look "
         "better. Any action against an innocent member would be a worse "
         "failure than the fraud.",
         "To the member: nothing is said until there is something to "
         "say, and if action is ever taken it comes with its basis and a "
         "route to contest it.",
         "`risk_officer` investigation, with escalation to the provider "
         "or law enforcement where appropriate.",
         "The risk event, the investigation, the evidence, and the "
         "outcome. 'Suspected' and 'confirmed' are never conflated in "
         "the record, because a suspicion that reads as a finding "
         "destroys trust on its own."],
        ["EC-135",
         "A member reaches the verification attempt limit.",
         "Further automated attempts are refused, and the member is "
         "routed to manual review rather than into a loop. The limit "
         "exists to stop someone guessing at verification, and a member "
         "who has genuinely failed repeatedly is a documentation "
         "problem, not a criminal one.",
         "*You have reached the limit for automatic checks. We will "
         "review this by hand - nothing further is needed from you "
         "today.*",
         "Manual review, then a decision with a stated reason.",
         "Attempts per verification with the failure reason. Members "
         "reaching the limit with clean intent are reported as a process "
         "failure of the verifier."],
        ["EC-136",
         "The member disputes a verification failure as an error in the "
         "provider's data.",
         "Treated as a data question about a third party, not as a "
         "member being difficult. The provider is asked to correct its "
         "record, the member is told what is being asked and when they "
         "will hear, and the member is not left unable to participate "
         "indefinitely while a third party's database is argued about.",
         "*We are asking the verification provider to correct their "
         "record. We will tell you the outcome, and you will not lose "
         "your place while we do it.*",
         "Provider correction, then resubmission, with manual review as "
         "the parallel route.",
         "The dispute, the request to the provider, and the outcome. "
         "Verification data quality is a dependency metric, because "
         "AJO.ng does not own the records being judged against."]
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.9
    {"t": "h2", "text": "19.9 Third-party dependency edge cases"},
    {"t": "p",
     "text": (
        "Section 1 records fifteen dependencies and fourteen risks, and the honest reading "
        "of that list is that AJO.ng depends on parties it does not control: a payment "
        "provider whose economics are still open decision **D-03**, verification services "
        "whose own availability is not ours, messaging gateways, push infrastructure, and "
        "hosting. This class is about our behaviour when one of them is down, and about the "
        "case that is worse: when one of them is up and we still cannot see the problem."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-137",
         "The identity verification service is unavailable, rate-limits us, or changes its "
         "response contract.",
         "Verification degrades to manual review rather than to automatic approval. Failing "
         "closed is mandatory: an unavailable verifier must never be read as a pass. The "
         "member's other rights are unaffected, so someone already verified can keep "
         "participating.",
         "*Verification is taking longer than usual. You can keep using the Ajos you are "
         "already in, and we will finish this.*",
         "Manual review queue, with a target turnaround communicated and a proactive update "
         "if it slips.",
         "Verifier errors by class, queue depth, and manual-review outcomes. A silent "
         "contract change is detected by response validation, not by a member complaint."],
        ["EC-138",
         "The push service is unavailable, so no app notification is delivered platform-wide.",
         "Money-critical and security events fall back to SMS, and everything else falls back "
         "to email. Volume is shaped so that a push outage cannot become an SMS bill "
         "outage, because SMS is the expensive channel and the one we least want to burn "
         "indiscriminately.",
         "The member is still reached by the channel that matters for the event they need "
         "to know about.",
         "Automatic fallback, then a review of whether a bulk channel switch is warranted.",
         "Fallback usage per event class. A sustained shift to SMS is both a resilience "
         "signal and a unit-economics signal, and it is reported as both."],
        ["EC-139",
         "A failure occurs that our monitoring does not detect, so the first signal is a "
         "member report rather than an alert.",
         "Member-reported money issues are treated as potential Sev-1 until disproved. The "
         "support queue is monitored for that specific pattern, because a burst of reports "
         "about the same screen is the only detector we have in that scenario.",
         "The member who reports it is answered quickly and told what is happening, rather "
         "than asked to wait for a system that has not noticed.",
         "Immediate investigation, plus a retrospective on why the alert did not fire.",
         "Support cases tagged by affected flow and clustered by time window. Clusters are "
         "escalated automatically above a threshold, precisely because absence of an alert "
         "must not delay the response."],
        ["EC-140",
         "The hosting platform has a regional outage, so the API is unavailable for all "
         "members at once.",
         "The service fails over, and the invariant that survives the outage is the honest "
         "one: a member who was told their payment was pending is still told it is pending, "
         "and no state is advanced on the assumption that it succeeded. Reconciliation runs "
         "before any resumed state is shown.",
         "*We are having problems and we are fixing them. Nothing you have done is lost, and "
         "we will not ask you to pay twice.*",
         "Automatic failover, then reconciliation of anything in flight at the time.",
         "Outage start and end, affected surface, and the reconciliation results. The "
         "in-flight set at failover is the interesting part and is retained explicitly."],
        ["EC-141",
         "DNS, a certificate or an edge component fails, so the app cannot reach the API or "
         "cannot be reached.",
         "Infrastructure-level, and handled with multi-region DNS, automated certificate "
         "renewal and a known-good fallback endpoint. Certificate expiry is prevented by "
         "monitoring with a long lead time, because an expired certificate is the most "
         "avoidable outage in this document.",
         "The app reports it cannot reach AJO.ng, and does not display a misleading error "
         "that looks like a payment problem.",
         "Infrastructure automation; a member never has to be told to reinstall anything.",
         "Certificate and DNS monitoring with lead-time alerts, and the incident record if "
         "renewal ever fails."],
        ["EC-142",
         "The provider's settlement or bank-credit file is unavailable, so reconciliation "
         "cannot confirm that funds actually arrived.",
         "Unconfirmed funds are not treated as available. A payout is released only when "
         "funds are fully collected and available, so an unavailable settlement feed becomes "
         "HELD rather than a guess. Unconfirmed amounts sit in suspense and are never "
         "recognised as income or as contributions receivable.",
         "*We are confirming that funds have reached us before releasing your payout. It is "
         "on track and it is yours.*",
         "Reconciliation when the feed returns, with a proactive update cadence if it does "
         "not.",
         "Suspense age and value, with a hard limit on how long an amount may sit "
         "unconfirmed. Ageing suspense is a risk item in its own right, not a bookkeeping "
         "detail."],
        ["EC-143",
         "The provider changes its pricing, so the 2% gross fee no longer covers collection "
         "and payout costs.",
         "This is a business risk, not a runtime fault, and it is answered by never changing "
         "the member-facing fee silently. The fee may not be raised without notice, and the "
         "notice period is a commitment to members (BR-026, BR-011).",
         "*We are telling you early, with the real numbers, before anything changes.* No "
         "member learns about a fee change from a payment receipt.",
         "Re-pricing with communicated notice, or absorbing the cost. Reducing the fee to "
         "zero without notice is not on that list.",
         "Unit economics tracked as R3, with fee revenue against provider cost per "
         "successful transaction, reviewed before any pricing decision is taken."],
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.10
    {"t": "h2", "text": "19.10 User-expectation and trust edge cases"},
    {"t": "p",
     "text": (
        "The last class is not a technical failure at all, and it is the one most likely to "
        "cost the product its reputation. Ajo carries a dense cultural meaning that the "
        "software inherits: it is a promise between people who know each other. Every case "
        "here is a place where the software's honest behaviour and the member's expectation "
        "of a traditional Ajo come apart, and where the product has to say plainly what it "
        "is and is not."
    )},
    {"t": "table",
     "head": ["ID", "Trigger", "System behaviour", "User experience", "Recovery mechanism",
              "Logging requirement"],
     "widths": [0.45, 1.15, 1.45, 1.2, 1.1, 1.15],
     "size": 7.0,
     "rows": [
        ["EC-144",
         "A member believes joining an Ajo guarantees a return, or expects the platform to "
         "cover a loss the way a guarantor would.",
         "The product never implies a return or a guarantee, and never claims to. Terms, "
         "disclosures and the interface state that the organiser is not a guarantor and that "
         "AJO.ng provides no yield, no lending and no guarantee (BR-008, BR-027, BR-028).",
         "*AJO.ng holds and tracks your Ajo. It is not an investment, and if a member does "
         "not pay, the platform does not cover it.* Said once, clearly, at the moment of "
         "joining rather than buried in terms.",
         "None needed; this is the intended framing.",
         "Disclosure acknowledgement at enrollment, so the point was actually made to each "
         "member rather than merely published."],
        ["EC-145",
         "A member believes a larger Ajo means a larger personal payout, or that more "
         "members means more money for them.",
         "The position order and the base pool are explicit before joining, and the member's "
         "own position is shown with its amount. A ten-member Ajo at NGN 1,000.00 per "
         "member pays a base pool of NGN 10,000.00, never NGN 10,200.00, because the 2% fee "
         "never reduces or inflates a payout.",
         "*Ten members at NGN 1,000.00 each means NGN 10,000.00 for the recipient. The "
         "platform fee does not come out of that.*",
         "None; the numbers are shown before commitment (BR-011).",
         "Fee disclosure acknowledgement, retained per member."],
        ["EC-146",
         "A member believes the 2% fee is deducted from their NGN 1,000.00 contribution, "
         "so that the Ajo receives NGN 980.00.",
         "The fee is added on top and always shown as three figures: contribution, fee, "
         "total. The member owes NGN 1,020.00, the escrow receives the net NGN 1,000.00, and "
         "the fee is recognised separately as fees_income (BR-010, BR-021).",
         "*You pay NGN 1,000.00 plus a 2% fee of NGN 20.00, so NGN 1,020.00 in total. The "
         "Ajo receives the full NGN 1,000.00 of your contribution.*",
         "The receipt repeats the same three figures, so a misunderstanding is corrected by "
         "the artefact rather than by an argument.",
         "Disclosure acknowledgement, and any support contact about the fee, which is a "
         "signal that the wording is not yet clear enough."],
        ["EC-147",
         "A member requests an early payout before their round completes, or asks to be "
         "skipped to the front of the order.",
         "Refused, and explained rather than merely rejected. A payout arises from a "
         "completed round with fully available funds; positions and the schedule are locked "
         "on activation (BR-002, BR-004, BR-018).",
         "*Payouts follow the round order that everyone agreed to when the Ajo started, and "
         "yours is third. Changing it needs a replacement request from the organiser.*",
         "A formal replacement or transfer request, which the organizer reviews.",
         "Requests logged with their reason. A cluster of early-payout requests is feedback "
         "on the product, not a queue of exceptions to process faster."],
        ["EC-148",
         "A member assumes the organiser can see their individual payment activity in detail, "
         "or that the platform shares payment data with them.",
         "Organizers see the funding position they need, not member-level payment telemetry. "
         "The organiser never handles the money, and support never moves it (BR-022, "
         "BR-023). What an organizer can see is stated plainly, so nobody is surprised in "
         "either direction.",
         "*Your organiser can see whether the round is covered, and they get reminders. Your "
         "individual payment history is yours.*",
         "None needed.",
         "Members-endpoint access logs, so a claim that an organiser saw more than they "
         "should have can be answered with evidence."],
        ["EC-149",
         "A member disputes the outcome of a completed Ajo and asks for their money back "
         "because the pool is smaller than they expected.",
         "Explained with the actual figures and the position order that was agreed at "
         "activation. A return is never implied and a shortfall is never quietly absorbed, "
         "because an implied return is exactly the belief the product must not create "
         "(BR-027, BR-018).",
         "*Here is the round: ten members at NGN 1,000.00, a base pool of NGN 10,000.00, and "
         "your position in the agreed order. If you think that order is wrong, you can raise "
         "a dispute.*",
         "Dispute, with evidence and a decision on the record.",
         "Dispute opened, resolved or not, with the figures quoted to the member. A dispute "
         "citing pool size is a comprehension signal, not just a service request."],
        ["EC-150",
         "An organiser pressures members in a group chat, or shares member details and "
         "payment status in a WhatsApp group outside the platform.",
         "The platform does not participate in that pressure and does not expose individual "
         "defaults to any member, including through its own notifications (BR-014). Members "
         "are given the route to raise a concern with support, and organiser conduct that "
         "crosses into coercion is a risk matter, not a feature request.",
         "*The organiser cannot see who paid and who did not. If you are being pressured, "
         "tell us - that is not how this should work.*",
         "Report, then `risk_officer` review; repeated coercion can lead to the organiser "
         "being removed from future Ajos.",
         "Reports with outcome, and the distinction maintained between a financial default "
         "and a conduct concern, because conflating them is how a platform ends up punishing "
         "a member for a member's behaviour."],
        ["EC-151",
         "A member concludes the 2% fee means AJO.ng is a scam, or that the app is taking a "
         "cut of the savings itself.",
         "Fees are disclosed before commitment and shown on every receipt, and the fee is "
         "never taken from the pool. The 2% is the whole business model, stated plainly: a "
         "fee on the deposit, added on top, never taken from anyone's savings.",
         "*We charge 2% of each contribution, NGN 20.00 on NGN 1,000.00, as our fee. The "
         "recipient still receives the full base pool.*",
         "Direct answer, then a referral to the fee and trust pages; unresolved suspicion is "
         "escalated, because a member who believes they are being defrauded will not wait "
         "for an email.",
         "Fee-related contacts and abandonment after the fee disclosure step. A high drop-off "
         "at that exact step is a comprehension problem in our own wording, and is treated "
         "as a design defect rather than a pricing decision."],
     ]},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.11
    {"t": "h2", "text": "19.11 Coverage map"},
    {"t": "p",
     "text": (
        "One hundred and fifty-one cases across ten classes. The map below states what each "
        "class is protecting, so that a reader can see the shape of the risk surface rather "
        "than only the volume of the table. The ordering of severity within a class is the "
        "ordering used by the on-call runbook in 19.13."
    )},
    {"t": "table",
     "head": ["Class", "Cases", "ID range", "Money at risk", "Trust exposure",
              "Worst severity"],
     "widths": [1.9, 0.5, 1.05, 0.9, 1.35, 0.8],
     "size": 8.5,
     "rows": [
        ["19.1 Payment", "29", "EC-001 to EC-029", "High", "High", "S1"],
        ["19.2 Connectivity and client", "7", "EC-030 to EC-036", "Low", "Medium", "S2"],
        ["19.3 Provider and webhook", "13", "EC-037 to EC-049", "High", "High", "S1"],
        ["19.4 Scheduling and lifecycle", "19", "EC-050 to EC-068", "High", "High", "S1"],
        ["19.5 Notification", "8", "EC-069 to EC-076", "None", "High", "S2"],
        ["19.6 Authorization and role", "23", "EC-077 to EC-099", "High", "High", "S1"],
        ["19.7 Data integrity", "7", "EC-100 to EC-106", "High", "Medium", "S1"],
        ["19.8 Security and privacy", "30", "EC-107 to EC-136", "High", "High", "S1"],
        ["19.9 Third-party dependency", "7", "EC-137 to EC-143", "Medium", "High", "S1"],
        ["19.10 Expectation and trust", "8", "EC-144 to EC-151", "None", "Severe", "S2"],
     ]},
    {"t": "p",
     "text": (
        "One hundred and two of these cases are cited directly by a branch or step in "
        "section 2, so a reviewer reading the flows can follow the reference to the case. "
        "The remaining forty-nine are register-only: they are risks our own systems and "
        "our own staff create rather than risks a member walks into, so no user journey "
        "reaches them and forcing a citation would be fiction. They are specified here "
        "because the register is the control, not the journey."
     )},
    {"t": "p",
     "text": (
        "Read that last column honestly. The classes with the highest case counts are not "
        "the classes with the worst outcomes; they are the classes with the most surface. "
        "The worst outcomes concentrate in 19.3, 19.7 and 19.8, because those are the "
        "classes where our own systems make assertions about money and identity, and an "
        "assertion that is wrong is worse than a service that is merely unavailable."
    )},

    # ------------------------------------------------------------------ 19.12
    {"t": "h2", "text": "19.12 Severity classification matrix"},
    {"t": "p",
     "text": (
        "Severity describes the consequence of the case going unhandled, not how often it "
        "happens. A once-in-a-year case that pays a member the wrong amount is an S1; a "
        "daily case that misplaces an icon is an S4. Three rules settle the remaining "
        "argument: a case that involves money at risk is at least S1; a case that is both "
        "S1 and S2 is treated as S1; and when genuinely uncertain, classify upwards and "
        "downgrade later with a recorded reason. Downgrading an incident is a decision "
        "someone makes on the record, not something the clock does to it."
    )},
    {"t": "table",
     "head": ["Severity", "Definition", "Representative cases", "Detected by",
              "First response target", "Escalation owner"],
     "widths": [0.56, 1.86, 1.39, 1.02, 0.88, 0.79],
     "size": 8.5,
     "rows": [
        ["S1 - Critical",
         "Money at risk, a member told something untrue about their money, a public data "
         "exposure, or an integrity assertion that has failed. Includes any case where a "
         "member may have been over- or under-charged.",
         "EC-004, EC-009, EC-041, EC-042, EC-044, EC-056, EC-101, EC-102, EC-111, EC-114",
         "Automated assertion, reconciliation, or clustered member reports",
         "Immediate, 24x7",
         "`super_admin`, with `risk_officer` on the case"],
        ["S2 - Major",
         "A member is blocked from a correct outcome they are entitled to, or a money-critical "
         "notification has failed and the fallback has not yet restored reach.",
         "EC-001, EC-010, EC-017, EC-034, EC-075, EC-078, EC-082, EC-151",
         "Support contact, failed-delivery report, anomaly",
         "Same business day",
         "`support` lead, escalating to engineering"],
        ["S3 - Moderate",
         "Degraded experience with no money at risk and no loss of entitlement: a stale "
         "screen, a slow channel, a queue that recovered on its own.",
         "EC-013, EC-020, EC-031, EC-036, EC-047, EC-104, EC-138",
         "Metric threshold",
         "Two business days",
         "Engineering owner"],
        ["S4 - Minor",
         "Cosmetic, copy or internal inconsistency with no member-visible consequence worth "
         "an interruption.",
         "EC-033, EC-053, EC-057, EC-071",
         "Manual observation",
         "Normal backlog",
         "Product"],
     ]},
    {"t": "callout",
     "kind": "NOTE",
     "title": "Two severities that are never downgraded",
     "text": (
        "An under-funded payout (K-01) and a leaked member record are both S1 regardless of "
        "how few members are affected, because both attack the specific promise the product "
        "is built on: that a member's money arrives intact, and that their information does "
        "not leave their control. A single under-funded payout of NGN 10,000.00 is the same "
        "kind of news as a systemic one, because the story does not distinguish."
    )},

    # ------------------------------------------------------------------ 19.13
    {"t": "h2", "text": "19.13 On-call runbook"},
    {"t": "p",
     "text": (
        "The runbook exists so that a tired person at 2am with one member's money at stake "
        "does not have to decide from first principles. It states what to do first, what may "
        "be delegated, and - more importantly - what nobody is permitted to do while under "
        "pressure, because the shortcuts available during an incident are exactly the ones "
        "that violate the product's core rules."
    )},
    {"t": "h3", "text": "19.13.1 First fifteen minutes"},
    {"t": "code",
     "size": 8.0,
     "text": """
   ALERT FIRES
       |
       v
   1. Is any member's money wrong, missing, or duplicated?
       |                                    |
       | yes                                | no
       v                                    v
   2. HALT disbursement                3. Is a member blocked
      (never reverse a payout              from a correct outcome?
       to make a number look                  |              |
       right)                                yes            no
       |                                     v               v
       v                                  4. Support lead   6. S3/S4
   5. Page the risk officer;              owns it;         backlog
      open a case per member,                  |
      not per alert                        5. Same ladder
                                              one rung down
   Every step writes to the case record. The first
   member message goes out before the root cause is
   known, because a member who has been paid wrongly
   and then told nothing is the failure we care about.
   """.strip("\n")},
    {"t": "h3", "text": "19.13.2 Alert handling"},
    {"t": "table",
     "head": ["Alert", "Likely case", "First 15 minutes", "15 to 60 minutes",
              "Beyond 1 hour", "Owner"],
     "widths": [1.25, 0.79, 1.33, 1.29, 1.17, 0.67],
     "size": 8.0,
     "rows": [
        ["Solvency assertion failed",
         "EC-101",
         "Halt all disbursement. Do not release any payout, for any Ajo, until the "
         "assertion passes again.",
         "Locate the breaching transaction, reconcile escrow against obligations, and "
         "identify every payout that would have been released on bad data.",
         "Engineering incident with a named incident lead; `risk_officer` informed if any "
         "member is affected.",
         "Engineering"],
        ["A payout is past its due time",
         "EC-056",
         "Confirm the funds and the funding position. Execute immediately if funds are "
         "available; do not wait for the root cause.",
         "Notify recipient and organizer with a real expected time, even if that time is "
         "an estimate.",
         "Escalate if the cause is systemic or if more than a handful of payouts are late.",
         "Support lead"],
        ["Possible double charge detected",
         "EC-004, EC-116",
         "Stop the affected payment path. Confirm with the provider before telling the "
         "member anything definitive.",
         "Refund the duplicate through the normal reversal path, and confirm the member's "
         "original payment is unaffected.",
         "Treat as S1 for as long as any member believes they were charged twice, even after "
         "the money is corrected.",
         "`risk_officer`"],
        ["Webhook signature failures spiking",
         "EC-038",
         "Do not disable verification to stop the noise. Confirm the alert source.",
         "Determine whether it is an attack, a provider contract change, or a replay. "
         "Preserve the evidence.",
         "Security incident with a response to the exposure, not only to the alert volume.",
         "`risk_officer`"],
        ["Provider unreachable",
         "EC-018, EC-048, EC-139",
         "Confirm nothing is in an ambiguous state. Reassure members that nothing has been "
         "taken and nothing needs to be repeated.",
         "Reconcile any ambiguous initiations by reference before permitting a single retry "
         "with a new key.",
         "Provider liaison. Do not build a workaround that bypasses the payment path.",
         "Engineering"],
        ["Money-critical notifications undelivered",
         "EC-075, EC-138, EC-069",
         "Switch money-critical events to the fallback channel. Do not wait to understand "
         "the cause.",
         "Confirm reach per member, and contact anyone unreachable by every channel before "
         "their deadline passes.",
         "Review channel budgets: a sustained fallback is a resilience and cost event.",
         "Support lead"],
        ["Denials or 5xx spiking on member endpoints",
         "EC-077, EC-114",
         "Assume a possible exposure until proven otherwise. Check whether any response is "
         "returning another member's data.",
         "If data may have been read by the wrong person, begin the notification assessment "
         "immediately.",
         "Sev-1 disclosure process if exposure is confirmed, including regulators as required "
         "by counsel.",
         "`super_admin`"],
        ["Member reports spike, no alert",
         "EC-139",
         "Treat the reports as the signal. Cluster them by flow and start the investigation "
         "without waiting for a metric to confirm.",
         "Establish scope from the reports themselves: how many members, which flow, which "
         "money.",
         "Retrospective on the missing detector, added to the monitoring set.",
         "Support lead"],
     ]},
    {"t": "h3", "text": "19.13.3 Authority during an incident"},
    {"t": "p",
     "text": (
        "These limits exist because every one of them has a plausible justification at 2am "
        "and none of them is a good idea."
    )},
    {"t": "table",
     "head": ["Permitted during an incident", "Not permitted, at any severity"],
     "widths": [3.25, 3.25],
     "size": 9.0,
     "rows": [
        ["Halt disbursement entirely, including for unaffected Ajos.",
         "Editing, deleting or amending a ledger entry. Corrections are reversing entries "
         "only, and this holds for `super_admin` (BR-025)."],
        ["Place an Ajo, payment or payout in HELD with a recorded reason, and notify the "
         "affected members.",
         "Reducing a payout to make it affordable, or using corporate funds to cover a "
         "shortfall (BR-018, BR-020)."],
        ["Freeze an account or Ajo pending review, with the reason recorded and the member "
         "notified.",
         "Silently delaying a payout, or delaying one without telling the recipient and the "
         "organizer (BR-017)."],
        ["Issue a full refund of a cancelled Ajo, and a reversal of a genuine overpayment.",
         "Absorbing a provider error quietly, or telling a member a refund will arrive by a "
         "date the provider has not confirmed (D-07)."],
        ["Proactively message affected members with what is known, what is not, and when the "
         "next update will be.",
         "Telling a member who defaulted to anyone else, or exposing default status through "
         "a notification payload (BR-014)."],
        ["Disable a money-moving endpoint entirely.",
         "Disabling webhook signature verification to reduce alert noise, or accepting an "
         "amount from a provider callback."],
        ["Re-run reconciliation, and post a correcting reversing entry once the facts are "
         "established.",
         "Writing a correction directly, or asking another member to cover a shortfall "
         "without their explicit consent (BR-015)."],
     ]},
    {"t": "callout",
     "kind": "WARN",
     "title": "The one-line version of this runbook",
     "text": (
        "Stop the money from moving, tell the member the truth immediately, and fix the "
        "record with a reversing entry. Everything else can wait for the root cause; those "
        "three things cannot."
    )},
    {"t": "pagebreak"},

    # ------------------------------------------------------------------ 19.14
    {"t": "h2", "text": "19.14 Specification gaps and open decisions"},
    {"t": "p",
     "text": (
        "A specification that hides its gaps is worse than one that names them. The cases "
        "below cannot be fully closed until the open item in the second column is answered, "
        "and they are listed here so that nobody discovers the dependency while a member is "
        "waiting. None of these is answered by invention in this document."
    )},
    {"t": "table",
     "head": ["Open item", "Question", "Cases affected", "Blocked until answered", "Owner"],
     "widths": [0.65, 2.18, 1.07, 1.58, 1.02],
     "size": 8.0,
     "rows": [
        ["D-02",
         "Does ProvidusUnity hold funds as principal, or must AJO.ng hold them? This "
         "determines the licensing path.",
         "EC-010, EC-042, EC-142",
         "The custody and recovery language in every member-facing document, and whether a "
         "provider failure is our loss or theirs.",
         "Legal and Providus"],
        ["D-03",
         "Exact Providus collection percentage, payout flat fee, and settlement timing.",
         "EC-001, EC-017, EC-043, EC-047, EC-143",
         "Any published timing promise, the margin warning in the revenue material, and the "
         "reconciliation interval. Required before the fee is publicised.",
         "Providus"],
        ["D-05",
         "Who bears the 2% fee when an Ajo cancels in the 5-day window - is it refunded?",
         "EC-050, EC-058",
         "The exact refund figure shown to a member at cancellation, which they must see "
         "before day 5 arrives.",
         "Founders and Legal"],
        ["D-06",
         "Is the 2% fee tax-inclusive, and who remits VAT or WHT?",
         "EC-010, EC-142, EC-143",
         "The fee line on receipts and the fee figure in every worked example.",
         "Tax adviser"],
        ["D-07",
         "Refund SLA after Providus approves a reversal.",
         "EC-010, EC-017",
         "Every date we might put in a member message about a refund. Until answered, no "
         "window is promised.",
         "Providus and Legal"],
        ["D-08",
         "Maximum Ajo size and maximum contribution cap as a fraud limit.",
         "EC-007, EC-008, EC-117",
         "The validation limits themselves, and therefore the correct behaviour for EC-007, "
         "which is currently specified against a configured minimum rather than a fixed "
         "figure.",
         "Risk"],
        ["D-04",
         "Is BVN or CAC verification mandatory for all members, or only above a threshold?",
         "EC-111, EC-137",
         "Whether an unverified member may occupy a position at all, and what EC-111 fails "
         "closed against in the automated path.",
         "Risk and Legal"],
        ["A-08",
         "Rounding basis for the 2% fee, in kobo integers.",
         "EC-008, EC-105",
         "Nothing structural. The rule in EC-008 is a design decision, and it becomes a "
         "canonical fact only once this assumption is confirmed.",
         "Engineering and Finance"],
     ]},
    {"t": "p",
     "text": (
        "Two further gaps are ours rather than a dependency's, and both are recorded here "
        "because the register is only useful if it can say so. First, a member on a shared or "
        "low-capability device is served by browser fallback, and we have no measured "
        "figure for how many members that represents; the low-bandwidth requirement is "
        "currently a design intention rather than a measured property (C-14, NFR-PERF-004). "
        "Second, the provider's client page sits outside our telemetry, so a failure inside "
        "it is visible to us only as an unfinished payment; that blind spot is why EC-020 "
        "can specify the message but not the detection."
    )},
    {"t": "callout",
     "kind": "NOTE",
     "title": "Closing position",
     "text": (
        "One hundred and fifty-one cases, each with a trigger, a system behaviour, a user "
        "experience, a "
        "recovery mechanism and a logging requirement. Where a recovery mechanism does not "
        "exist, the case says so rather than inventing one. Where the answer depends on a "
        "decision we have not made, the case is filed against that decision in 19.14. And "
        "through all of it, five things never change: no member is paid less than the base "
        "pool, no member is charged twice, no defaulter is exposed, no financial record is "
        "edited, and no shortfall is covered with corporate funds. AJO.ng. Your Ajo. Your "
        "Story."
    )},
]
