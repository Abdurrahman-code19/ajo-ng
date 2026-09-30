"""Section 15 — Fraud, Risk and Financial Crime."""

BLOCKS = [
    {"t": "h1", "text": "15. Fraud, Risk and Financial Crime"},

    {"t": "lead", "text": "AJO.ng moves money between people who know each other, in "
     "small amounts, on a schedule, in a market where fraud is a daily commercial "
     "activity. The platform's job is not to eliminate fraud — no platform can — but to "
     "make it visible early, make it recoverable where possible, and never make a member "
     "pay twice for someone else's crime."},

    {"t": "h2", "text": "15.1 Risk philosophy"},
    {"t": "numbers", "items": [
        "**Fraud is an expected operating cost, not an exceptional event.** It is modelled in the financials and staffed for, rather than treated as something that will not happen.",
        "**Protect the member first.** A member who is a victim of fraud should be believed, compensated where the platform is at fault, and supported through the process.",
        "**Never lose a member's money to fraud prevention.** A false positive that freezes a legitimate payout is a real cost to a real person, and it damages trust more than a single missed fraud.",
        "**No single signal convicts.** Risk scoring informs human decisions; it never autonomously confiscates money or closes an account without a reviewable record.",
        "**Speed matters.** Most fraud is recoverable in the first hours. Controls that add friction to legitimate members, in order to catch a rare case, are a bad trade.",
        "**Every action is explainable.** When a payment is held, the reason is recorded in plain language, and a member can ask and get an answer.",
    ]},
    {"t": "callout", "kind": "NOTE", "title": "The uncomfortable truth about false positives.",
     "text": "Every fraud control has a cost paid by honest members. A cooling-off "
     "period annoys someone who legitimately changed banks. A payout hold angers someone "
     "who did nothing wrong. The discipline is to keep the total friction proportionate to "
     "the actual fraud rate, to measure the false-positive rate, and to remove controls "
     "that are not earning their cost."},

    {"t": "h2", "text": "15.2 Fraud typology relevant to AJO.ng"},
    {"t": "table", "head": ["Type", "Mechanism", "AJO-specific angle", "Primary defence"], "widths": [1.5, 1.9, 1.9, 1.6], "size": 7.6, "rows": [
        ["Payout redirection / BEC", "Account takeover, then a bank-account change before the next payout", "**The highest-value attack.** A predictable, dated payout is a standing target", "Cooling-off on destination change, multi-channel notification, step-up auth"],
        ["First-party abuse", "Member makes a genuine contribution, then disputes it as unauthorised", "Ajo membership makes a plausible story easy to construct", "Strong webhook evidence, transaction history, dispute analysis"],
        ["Duplicate / replay payment", "Replaying a captured webhook or a transfer reference", "Recurring payments make a valid reference reusable", "Unique provider event IDs, unique reference constraints, idempotency keys"],
        ["Fake support / social engineering", "Impersonating AJO.ng staff on WhatsApp or by phone to move a member's money or BVN", "Members are primed to trust group authority", "AJO.ng will never move money or request BVN by chat. Staff identity is verifiable in-app"],
        ["Organizer abuse", "Misleading members, using the group to solicit off-platform payments, or excluding members", "The organizer is a trusted human with real influence", "Scoped permissions, no custody, member complaints channel, audit trail"],
        ["Money mule recruitment", "Using member accounts to receive and forward funds, often for a 'fee'", "Savings accounts plus transfers make a mule account look normal", "Behavioural signals, velocity limits, off-platform solicitation detection, SAR escalation"],
        ["Structuring / smurfing", "Many small contributions to keep below a reporting threshold", "Small, regular contributions are the product's core behaviour", "Aggregate transaction monitoring across accounts, not just per-transaction"],
        ["Account farming", "Bulk creation of accounts with disposable numbers to farm cashback, inflate Ajo counts, or stage fraud", "Invitation-only onboarding raises the cost of this", "Device and phone uniqueness, invite-code validity, behavioural scoring"],
        ["Identity theft", "Using another person's identity to open an account or pass KYC", "BVN-based KYC raises both detection and harm", "BVN verification, liveness where required, device fingerprinting, manual review on mismatch"],
        ["Chargeback abuse", "Legitimate contribution disputed at the card issuer as fraud", "Contributions recur, which looks like a subscription to issuers", "Clear descriptors, evidence packs for issuers, velocity limits"],
        ["Referral / reward manipulation", "Self-referral chains to inflate bonuses", "Referral bonuses are a natural target", "KYC-gated rewards, graph analysis, no reward until the referred member completes a cycle"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "The predictable-payout problem.",
     "text": "Ajo.ng knows the amount, the date, the recipient, and the destination account "
     "weeks before the money moves. That predictability is what makes AJO.ng structurally "
     "more attackable than a normal wallet, and it is the single most important fact in "
     "this section. Every control that protects the payout window is worth more than a "
     "generic anti-fraud rule."},

    {"t": "h2", "text": "15.3 Risk engine"},
    {"t": "p", "text": "The risk engine scores a transaction or an account at decision "
     "points. It is deliberately interpretable: a score with a stated reason is auditable "
     "and can be explained to a member, and a black-box score cannot be defended to a "
     "regulator or a customer."},
    {"t": "h3", "text": "15.3.1 Signals"},
    {"t": "table", "head": ["Signal", "Example", "Direction"], "widths": [1.5, 3.6, 1.4], "size": 8.2, "rows": [
        ["Account age", "Account younger than 30 days making a large first contribution", "↑ risk"],
        ["Velocity", "Many contributions in a short window; many new Ajos per day", "↑ risk"],
        ["Amount anomaly", "Contribution far above the member's own history or the Ajo's agreed amount", "↑ risk"],
        ["Device", "Emulator, rooted device, new device, many accounts per device", "↑ risk"],
        ["Network", "IP reputation, VPN or data-centre IP, many accounts per IP", "↑ risk"],
        ["Phone", "Disposable number, recently changed, virtual number, reused across accounts", "↑ risk"],
        ["Graph", "Two accounts sharing a device, bank account, BVN, or address", "↑ risk"],
        ["Behavioural", "Payout immediately after a bank-account change; login then immediate payout", "↑ risk"],
        ["Tenure", "Long history, no incidents, verified identity, consistent behaviour", "↓ risk"],
        ["Relationship", "Member of a long-running Ajo with an established pattern", "↓ risk"],
    ]},
    {"t": "h3", "text": "15.3.2 Decision bands"},
    {"t": "table", "head": ["Score", "Band", "Action"], "widths": [1.1, 1.2, 4.2], "size": 8.4, "rows": [
        ["0–29", "Low", "Approve automatically. No friction"],
        ["30–59", "Medium", "Approve, but log. Step-up auth if the action is a bank change or payout release"],
        ["60–79", "Elevated", "Apply the specific control matched to the reason: velocity cap, cooling-off, or a short delay with proactive notification"],
        ["80–100", "High", "Hold for human review by a risk officer. The member is told the payment is being reviewed, with a timeframe. Never a silent hold"],
    ]},
    {"t": "p", "text": "A high score is a request for a human decision, not a verdict. Every "
     "hold has an owner, a reason, a review deadline, and an outcome — and a hold that "
     "expires without a decision releases automatically, so a queue can never quietly "
     "strand a member's money."},

    {"t": "h2", "text": "15.4 Preventative controls"},
    {"t": "table", "head": ["Control", "Rule", "Friction cost"], "widths": [1.6, 3.6, 1.3], "size": 8.2, "rows": [
        ["Identity verification", "BVN verification and liveness check for payout-capable accounts", "One-time"],
        ["Destination cooling-off", "14 days between changing a bank account and a payout, shortened only by risk review", "Rare, and communicated"],
        ["Step-up authentication", "Required to change a bank account, release a payout, or resolve a dispute", "Seconds"],
        ["Multi-channel change notification", "Every bank, phone, or email change notified to all registered channels", "None"],
        ["Velocity limits", "Daily and monthly caps on contribution volume, Ajo count, and payout count", "Low, if set generously"],
        ["First-payout ramp", "Payout amount capped for the first cycle of a new account, rising with tenure", "Moderate; transparent"],
        ["Device and graph binding", "Limit accounts per device, phone, bank account, and BVN", "None for honest users"],
        ["Off-platform solicitation report", "Members and organizers can report payment requests outside AJO.ng; rapid review", "None"],
        ["Contributor identity consistency", "Contributions must come from the contributing member's own verified account", "Moderate, and correct"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "AJO.ng never asks for a BVN on WhatsApp, SMS, or a phone call.",
     "text": "This should be a permanent, prominent product statement — in the app, in "
     "the terms, in the footer of every email, and in the FAQ. Organizers should be "
     "explicitly bound by it. The most effective anti-fraud control available to a "
     "savings platform is a rule its members can remember, and this is the one."},

    {"t": "h2", "text": "15.5 Detection controls"},
    {"t": "bullets", "items": [
        "**Post-transaction monitoring** — every contribution, payout, bank change, and login is scored, not only those crossing a threshold at the time.",
        "**Aggregation across accounts** — a single account's behaviour may look normal while the aggregate across a device, a bank account, or an organizer looks like fraud. Per-transaction thresholds alone will miss this.",
        "**Graph analysis** — shared devices, phone numbers, addresses, and bank accounts across nominally separate accounts.",
        "**Sequence detection** — the specific ordering of events that predicts a redirected payout: bank change, then payout request, then a new-device login.",
        " **Sanctions and PEP screening** — against the current Nigerian sanctions lists and any applicable international lists, at onboarding, on payout, and periodically thereafter. This requires a licensed screening provider and is a legal obligation to verify.",
        "**Reconciliation-driven detection** — a payout that does not appear in the bank statement is an alert, not an accounting footnote.",
        "**Member reports** — a simple, in-app report button on any transaction, a message, or an organizer. Reports are triaged, not dismissed.",
    ]},

    {"t": "h2", "text": "15.6 Response controls"},
    {"t": "h3", "text": "15.6.1 Actions and their limits"},
    {"t": "table", "head": ["Action", "Trigger", "Effect on the member", "Guardrail"], "widths": [1.5, 1.7, 1.8, 1.8], "size": 7.8, "rows": [
        ["Step-up auth", "Medium risk on a sensitive action", "Must re-authenticate", "Cannot be used to deny a payout outright"],
        ["Delay with notification", "Elevated risk, no fraud indicator", "Informed, with a date", "Delay is bounded and expires automatically"],
        ["Cooling-off", "Bank-account change", "Payout available after 14 days", "Shortened on verified evidence"],
        ["Payout hold", "High risk, or an open investigation on the payout", "Informed with a timeframe", "Human decision required. Never automatic beyond a short bounded window"],
        ["Account freeze", "Confirmed or strongly suspected fraud", "Cannot contribute or withdraw. **Can still be paid out**", "Risk officer decision, reviewed, expiring"],
        ["Ajo freeze", "Fraud inside an Ajo, or an organiser acting in bad faith", "All activity paused", "Risk officer plus super admin; members notified"],
        ["Full suspension", "Confirmed fraud or repeated serious breach", "Read-only. Payouts continue", "Super admin, documented, appealable"],
        ["Termination", "Fraud with no legitimate basis", "Account closed, funds settled per the terms", "Super admin plus legal review. Always a written, reasoned decision"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "A freeze must never trap money a member has earned.",
     "text": "Freeze blocks *sending* money: contributions, new Ajos, and withdrawals to a "
     "changed destination. It does not block *receiving* a payout already owed. A member "
     "under investigation is still entitled to their Ajo money. Getting this wrong in the "
     "favour of safety would turn a fraud control into a means of confiscating a member's "
     "savings without authority, which is both a legal exposure and a moral failure."},

    {"t": "h3", "text": "15.6.2 Investigation"},
    {"t": "p", "text": "An investigation is a documented, time-boxed process. The officer "
     "gathers evidence, records each step, and reaches one of a small number of conclusions."},
    {"t": "table", "head": ["Conclusion", "Meaning", "Action"], "widths": [1.3, 2.6, 2.6], "size": 8.4, "rows": [
        ["No concern", "Legitimate activity", "Release all holds. Record the outcome so the pattern is visible next time"],
        ["Suspicious, resolved", "Concern explained by circumstance", "Release, and tune the signal if it was a false positive"],
        ["Confirmed fraud", "Deliberate abuse", "Recover funds where possible; suspend; consider referral; decide on restitution"],
        ["Money mule", "Account used to move third-party funds", "Freeze, restrict, and refer to law enforcement and the FIU"],
        ["Organizer abuse", "Misconduct by an Ajo organizer", "Remove organizer role, audit the Ajo, notify members, review the cycle"],
    ]},
    {"t": "p", "text": "Suspicious Activity Reports are filed where legally required, by a "
     "nominated officer, in the format and to the authority the law specifies, within the "
     "statutory deadline. Whether AJO.ng is a reporting entity under Nigerian law is a "
     "**legal determination that must be confirmed before launch**; the platform should be "
     "built as though it is, because retrofitting a reporting obligation under regulatory "
     "pressure is far harder than having it in place."},

    {"t": "h2", "text": "15.7 Fraud and the member experience"},
    {"t": "p", "text": "Fraud controls fail in two directions: too little, which costs "
     "money, and too much, which costs members. The product must be designed for the "
     "second case as carefully as the engineering is for the first."},
    {"t": "bullets", "items": [
        "Every hold, delay, and review is explained in plain language, with what is happening, why, and when it will be resolved. 'Your payment is being reviewed' is acceptable; silence is not.",
        "A member can see the status of their own payout at all times, including when it is held, and why.",
        "A member can dispute a risk decision, and the dispute is answered. A system with no appeal route will accumulate grievances that surface publicly.",
        "The cooling-off period is stated up front, at the moment of the bank change, not discovered two weeks later at the payout.",
        "False positives are measured as a first-class metric (15.10), and controls are retired when their false-positive cost exceeds their fraud benefit.",
    ]},

    {"t": "h2", "text": "15.8 Organizer risk"},
    {"t": "p", "text": "The organizer is the one participant the platform cannot verify "
     "away. They are a real person with real influence over real money, and the controls "
     "here are behavioural and social rather than technical."},
    {"t": "bullets", "items": [
        "**Off-platform solicitation is prohibited** — an organizer may not collect money, request BVN, or arrange payment outside AJO.ng. Contributions are made only in-app, always to the platform.",
        "**The member-facing fee is fixed** — an organizer may not add a fee, levy, or 'handling charge'. The 2% is the whole cost to the member.",
        "**No private messaging for financial matters** — organizer communication about money happens through AJO.ng, where it is recorded. A private channel is where fraud and coercion thrive.",
        "**No exclusion after activation** — an organizer who dislikes a member cannot remove them, because their committed contributions are already in the pool.",
        "**Member reporting** — any member may report an organizer, and reports are reviewed by a risk officer, not by the organizer.",
        "**Pattern monitoring** — repeated Ajo creation and abandonment, unusually rapid default rates, and organiser behaviour that correlates with member complaints all raise the risk level.",
    ]},

    {"t": "h2", "text": "15.9 Fraud operations"},
    {"t": "table", "head": ["Function", "Responsibility", "Coverage"], "widths": [1.7, 3.3, 1.5], "size": 8.4, "rows": [
        ["Automated triage", "Scoring, queueing, alerting", "24/7"],
        ["L1 analyst", "First-line review of alerts and disputes, standard playbook decisions", "Business hours, extended for payout cycles"],
        ["L2 risk officer", "Complex cases, freezes, Ajo freezes, recovery strategies", "Business hours + on-call"],
        ["Money recovery", "Bank liaison, chargeback, recall attempts, law enforcement liaison", "As required"],
        ["Data protection officer", "Breach assessment, regulatory notification, SAR oversight", "Named individual"],
        ["SAR / reporting officer", "Filing to the FIU and other authorities within statutory deadlines", "Named individual"],
        ["Money laundering reporting officer", "Overall MLRO accountability", "**Role must be confirmed as legally required**"],
    ]},
    {"t": "p", "text": "The organisational separation between the L1 analyst who triages and "
     "the L2 officer who freezes is deliberate: the person who reviews the alert should "
     "not also be the person who decides what happens to a member."},

    {"t": "h2", "text": "15.10 Risk metrics"},
    {"t": "table", "head": ["Metric", "Definition", "Target", "Note"], "widths": [1.7, 2.1, 1.1, 1.6], "size": 8.0, "rows": [
        ["Gross fraud loss", "Confirmed fraud loss ÷ payment volume", "Declining trend", "The number the board sees"],
        ["Fraud basis points", "Basis points of volume lost to fraud", "< 5 bps", "Comfortably below the 2% fee — the fee is not a fraud budget"],
        ["Detection rate", "Confirmed fraud caught before loss ÷ total confirmed fraud", "> 70%", "The rest is recovered or written off"],
        ["False positive rate", "False holds ÷ total holds", "< 10%", "Member-experience metric. Reviewed monthly"],
        ["Time to detection", "Onset to alert", "< 1 hour for payout redirection", "Recoverability decays sharply after this"],
        ["Time to decision", "Alert to human decision", "< 24 hours", "Bounded automatically to prevent stranding"],
        ["Recovery rate", "Recovered ÷ attempted recovery", "> 30%", "Depends on how fast we move"],
        ["SAR filing timeliness", "Filed within the statutory deadline", "100%", "Zero tolerance"],
        ["Sanctions hit rate", "True matches ÷ alerts", "Investigate all", "Also a false-positive concern — a blocked innocent is a serious harm"],
        ["Organizer complaint rate", "Reports per 100 active organizers", "Declining trend", "A leading indicator of community health"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Fraud cost is a fraction of the fee — but not of trust.",
     "text": "At 5 basis points, fraud consumes a quarter of the 2% fee. That is "
     "sustainable. What is not sustainable is a member whose money was taken and who was "
     "then told it was their own fault. The financial case for good fraud controls is "
     "comfortable; the reason to do them well is the member."},
]
