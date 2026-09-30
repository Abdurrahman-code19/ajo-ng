"""Section 23 — Epics, Backlog and Prioritisation."""

BLOCKS = [
    {"t": "h1", "text": "23. Epics, Backlog and Prioritisation"},

    {"t": "lead", "text": "A backlog is a set of decisions, not a list of wishes. The "
     "entries below are written so that the reason for each is visible, because a backlog "
     "item whose purpose has been forgotten is either built for the wrong reason or "
     "deleted for no reason."},

    {"t": "h2", "text": "23.1 Prioritisation method"},
    {"t": "p", "text": "Effort and impact are estimated relative to each other rather than "
     "in absolute days, because absolute estimates from a team that has not yet built the "
     "product are fiction. Risk reduction is treated as a first-class dimension: a task "
     "that removes a catastrophic outcome outranks a task that adds a modest convenience, "
     "even at equal effort."},
    {"t": "table", "head": ["Factor", "Question asked"], "widths": [1.5, 5.0], "size": 8.4, "rows": [
        ["Member impact", "Does a real member get to save, or keep their money, or understand what happened?"],
        ["Risk reduction", "Does this remove a way to lose money, lose data, or violate a control?"],
        ["Blocking", "Does something else physically depend on this?"],
        ["Trust and clarity", "Does this prevent a member from being confused or feeling misled?"],
        ["Effort", "How large is it, honestly?"],
    ]},
    {"t": "p", "text": "The ordering rule, in plain terms: **safety before money movement, "
     "money movement before convenience, convenience before polish.** A beautiful interface "
     "on an incorrect ledger is a liability."},

    {"t": "h2", "text": "23.2 Epics"},
    {"t": "table", "head": ["Epic", "Contains", "Depends on"], "widths": [1.4, 3.1, 2.0], "size": 8.0, "rows": [
        ["E1 — Financial core", "Money type, ledger, state machine, provider interface, adversarial tests", "Nothing"],
        ["E2 — Identity and compliance", "Registration, verification, consent records, data protection", "E1"],
        ["E3 — Payments spine", "Collection, webhooks, escrow, reconciliation, reversals", "E1, E2"],
        ["E4 — Payouts", "Preconditions, batches, settlement, receipts, statements", "E3"],
        ["E5 — Ajo lifecycle", "Create, configure, invite, join, enroll, activate, complete, cancel", "E2, E3"],
        ["E6 — Contributions", "Scheduling, collection, defaults, grace periods, recovery", "E3, E5"],
        ["E7 — Notifications", "Templates, channels, preferences, reminders, escalation", "E3, E5"],
        ["E8 — Organizer tools", "Scoped configuration, invites, monitoring, acknowledgements", "E5"],
        ["E9 — Operations console", "Admin, risk, finance, reconciliation, manual operations", "E3, E4"],
        ["E10 — Trust and safety", "Fraud signals, holds, disputes, reporting, appeals", "E3, E9"],
        ["E11 — Platform", "Infrastructure, CI/CD, observability, environments, runbooks", "E1"],
        ["E12 — Growth", "Referrals, marketing, community, experiments", "Everything shipped"],
    ]},

    {"t": "h2", "text": "23.3 Detailed backlog — Epic 1, financial core (foundation, complete)"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Status"], "widths": [0.8, 3.2, 1.1, 0.9, 0.9], "size": 8.2, "rows": [
        ["E1-01", "Money type in integer kobo, branded, no floating point", "P0", "S", "Done"],
        ["E1-02", "Formatting and parsing for NGN across all magnitudes", "P0", "S", "Done"],
        ["E1-03", "Double-entry ledger with balanced postings", "P0", "M", "Done"],
        ["E1-04", "Reversal-only correction; no update or delete path", "P0", "S", "Done"],
        ["E1-05", "Computed balances from entries, not mutable columns", "P0", "M", "Done"],
        ["E1-06", "Ajo lifecycle state machine with all transitions", "P0", "M", "Done"],
        ["E1-07", "5-day enrollment window and position lock", "P0", "M", "Done"],
        ["E1-08", "FinancialProvider interface", "P0", "S", "Done"],
        ["E1-09", "MockFinancialProvider with a production guard", "P0", "S", "Done"],
        ["E1-10", "Adversarial test suite", "P0", "M", "Done"],
        ["E1-11", "Balanced 2% fee posting for contribution capture", "P0", "M", "**To do**"],
        ["E1-12", "Fee reversal preserving recognised revenue", "P0", "S", "**To do**"],
        ["E1-13", "Payout recognition and settlement entries", "P0", "M", "**To do**"],
        ["E1-14", "Continuous invariant check: ledger = balances = escrow", "P0", "M", "**To do**"],
    ]},

    {"t": "h2", "text": "23.4 Detailed backlog — Epic 2, identity and compliance"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E2-01", "Registration with email verification and consent capture", "P0", "M", "Consent record must include document version"],
        ["E2-02", "BVN verification and liveness flow", "P0", "L", "Provider-dependent"],
        ["E2-03", "Phone normalisation to E.164 and uniqueness", "P0", "S", "Blocks account farming"],
        ["E2-04", "Account states: pending, active, frozen, suspended, dormant, closed", "P0", "M", "Payout must remain possible in every state"],
        ["E2-05", "Profile management and self-service data export", "P0", "M", "Data subject request"],
        ["E2-06", "Login, refresh rotation, and reuse detection", "P0", "M", "Token family revocation"],
        ["E2-07", "MFA: SMS OTP for sensitive actions, TOTP for staff", "P0", "M", "Mandatory for bank changes"],
        ["E2-08", "Step-up authentication framework", "P0", "M", "Required for payout release"],
        ["E2-09", "Device management and revocation", "P1", "M", "New-device alerts"],
        ["E2-10", "Role and permission enforcement, with RLS", "P0", "L", "Both layers, not either"],
        ["E2-11", "Staff access review tooling", "P1", "M", "Quarterly requirement"],
    ]},

    {"t": "h2", "text": "23.5 Detailed backlog — Epic 3, payments spine"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E3-01", "ProvidusUnity technical due diligence", "P0", "L", "**Blocks E3-05 onward**"],
        ["E3-02", "ProvidusFinancialProvider adapter", "P0", "L", "Against a verified sandbox spec"],
        ["E3-03", "Provider contract test suite", "P0", "M", "Runs against mock and sandbox"],
        ["E3-04", "Webhook verification, replay protection, idempotency", "P0", "M", "Raw body, constant-time compare"],
        ["E3-05", "Collection initiation and the pending contribution flow", "P0", "L", "Idempotency key required"],
        ["E3-06", "Fee calculation and capture posting", "P0", "M", "2%, integer kobo, balanced"],
        ["E3-07", "Escrow and settlement account setup", "P0", "M", "Separate account for fees"],
        ["E3-08", "Daily reconciliation service and reporting", "P0", "L", "Three reconciliations"],
        ["E3-09", "Reconciliation alerting, with payouts halted on a break", "P0", "M", "The safety net"],
        ["E3-10", "Refunds and reversals, including duplicate capture", "P0", "M", "Reversal entries only"],
        ["E3-11", "Unmatched inbound payment handling and aging", "P0", "M", "Return to source after 30 days"],
        ["E3-12", "Provider status polling as a webhook backstop", "P1", "M", "Covers webhook gaps"],
        ["E3-13", "Payment status query for members", "P1", "S", "Answers 'is my money safe'"],
        ["E3-14", "USSD or feature-phone fallback", "P2", "L", "Inclusion, not launch-critical"],
    ]},

    {"t": "h2", "text": "23.6 Detailed backlog — Epic 4, payouts"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E4-01", "Payout preconditions engine", "P0", "M", "All six conditions, including the frozen-member exception"],
        ["E4-02", "PayoutIntent state machine", "P0", "M", "Prechecking, queued, processing, retrying, review"],
        ["E4-03", "Single payout with ledger recognition and settlement", "P0", "M", "Two entries, not one"],
        ["E4-04", "Batch dispatch for a completing Ajo", "P0", "L", "Partial failure per item"],
        ["E4-05", "Retry with exponential backoff, then human review", "P0", "M", "Max 3 attempts, then escalate"],
        ["E4-06", "Payout held state, with a bounded automatic release", "P0", "M", "Never a silent hold"],
        ["E4-07", "Receipt and payout notification", "P0", "S", "The most monitored notification"],
        ["E4-08", "Member-initiated payout request", "P1", "M", "Within the policy window"],
        ["E4-09", "Monthly and annual statements", "P1", "M", "Itemising fees"],
        ["E4-10", "Payout reconciliation against bank statements", "P0", "M", "Part of the daily close"],
    ]},

    {"t": "h2", "text": "23.7 Detailed backlog — Epic 5, Ajo lifecycle"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E5-01", "Create an Ajo with all parameters and validation", "P0", "M", "Defaults locked at activation"],
        ["E5-02", "Ajo rules and acknowledgement record", "P0", "S", "Every member acknowledges"],
        ["E5-03", "Invitation generation and single-use validation", "P0", "M", "No unilateral invitation"],
        ["E5-04", "Join and position assignment", "P0", "M", "Position locked on activation"],
        ["E5-05", "5-day enrollment window, with boundary tests", "P0", "M", "Server-enforced, not client-side"],
        ["E5-06", "Activation to FUNDED", "P0", "M", "Requires every position paid"],
        ["E5-07", "Round scheduling and advance", "P0", "M", "Timezone-correct"],
        ["E5-08", "Completion and Ajo closure", "P0", "M", "All positions paid"],
        ["E5-09", "Cancellation before activation, with full refunds", "P0", "M", "Fee treatment needs counsel"],
        ["E5-10", "Ajo detail and history view", "P0", "M", "Member-visible states"],
        ["E5-11", "Ajo completion certificate or record", "P2", "S", "A member-value nicety"],
    ]},

    {"t": "h2", "text": "23.8 Detailed backlog — Epic 6, contributions and defaults"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E6-01", "Contribution schedule and due dates", "P0", "M", "Ajo timezone with local alongside"],
        ["E6-02", "Contribution collection flow with itemised fee", "P0", "M", "Fee on a separate line, always"],
        ["E6-03", "Position status: unpaid, pending, funded", "P0", "S", "Pending is distinct from paid"],
        ["E6-04", "Reminder escalation schedule", "P0", "M", "T−7, T−3, T−1, T−0, close"],
        ["E6-05", "Default recording, per BR-012", "P0", "M", "No shaming, no public exposure"],
        ["E6-06", "48-hour grace period with recovery offer", "P0", "M", "Structural, not punitive"],
        ["E6-07", "Organizer acknowledgement of a default", "P0", "M", "With member consent"],
        ["E6-08", "Recovery payment flow", "P0", "M", "Position returns to funded"],
        ["E6-09", "Replacement member with debt assumption", "P2", "L", "Not a default, requires consent"],
        ["E6-10", "No extra charge to other members, per BR-018", "—", "—", "**Enforced by absence. A test asserts no such path exists**"],
    ]},

    {"t": "h2", "text": "23.9 Detailed backlog — Epic 7, notifications"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E7-01", "Notification event model and taxonomy", "P0", "M", "Money events not opt-out"],
        ["E7-02", "In-app notification centre and history", "P0", "M", "The source of truth"],
        ["E7-03", "Push delivery with APNs and FCM", "P0", "M", "Deep links to the right screen"],
        ["E7-04", "Email templates and delivery", "P0", "M", "Transactional, not marketing"],
        ["E7-05", "SMS fallback for critical events", "P0", "M", "The inclusion channel"],
        ["E7-06", "Money event templates, complete set", "P0", "M", "Per section 16.4"],
        ["E7-07", "Reminder scheduler with quiet hours and daily caps", "P0", "M", "No reminder fatigue"],
        ["E7-08", "Preference centre, per channel and category", "P0", "M", "Money and security locked on"],
        ["E7-09", "Delivery logging, bounce handling, dead letters", "P0", "M", "Alerts on dead-letter depth"],
        ["E7-10", "WhatsApp Business integration", "P2", "L", "Requires provider approval"],
        ["E7-11", "Localisation of templates", "P1", "M", "**Professional translation required**"],
    ]},

    {"t": "h2", "text": "23.10 Detailed backlog — Epic 8, organizer tools"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E8-01", "Organizer dashboard for their Ajos", "P0", "M", "Scoped to their own Ajos"],
        ["E8-02", "Invitation management", "P0", "S", "Consent required from the invitee"],
        ["E8-03", "Contribution status monitoring", "P0", "S", "Status, not identity documents"],
        ["E8-04", "Member removal before activation", "P0", "S", "Impossible after activation"],
        ["E8-05", "Send reminders, as AJO.ng messages", "P0", "S", "Never as impersonation"],
        ["E8-06", "Default acknowledgement, per BR-020", "P0", "M", "With the defaulting member's consent"],
        ["E8-07", "Ajo completion reporting", "P1", "S", "What every member contributed and received"],
        ["E8-08", "Organizer Ajo history and reputation signals", "P2", "M", "Careful with ranking and fairness"],
        ["E8-09", "Organizer messaging within the Ajo", "P1", "M", "Recorded, moderated, rate-limited"],
    ]},

    {"t": "h2", "text": "23.11 Detailed backlog — Epic 9, operations console"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E9-01", "Admin: Ajo and member oversight", "P0", "M", "Read-only by default"],
        ["E9-02", "Support lookup by transaction or member", "P0", "M", "Must not need engineering"],
        ["E9-03", "Reconciliation dashboard with break alerts", "P0", "M", "The daily tool"],
        ["E9-04", "Manual payout retry and destination reassignment", "P0", "M", "Step-up auth, dual authorisation"],
        ["E9-05", "Manual ledger correction, reversal only", "P0", "M", "Dual authorisation, mandatory reason"],
        ["E9-06", "Risk queue with holds, reasons, and deadlines", "P0", "M", "Auto-release on deadline"],
        ["E9-07", "Audit log viewer", "P0", "M", "Append-only, searchable"],
        ["E9-08", "Dispute management", "P0", "L", "Raise, respond, resolve, notify"],
        ["E9-09", "Finance reporting and month-end close tooling", "P1", "L", "Gross and net revenue separate"],
        ["E9-10", "Role assignment administration", "P0", "M", "Every assignment audited"],
    ]},

    {"t": "h2", "text": "23.12 Detailed backlog — Epic 10, trust and safety"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E10-01", "Bank-account change cooling-off, 14 days", "P0", "M", "The highest-value single control"],
        ["E10-02", "Multi-channel notification of every sensitive change", "P0", "M", "Push, email, and SMS"],
        ["E10-03", "Risk engine v1 with interpretable scores and reasons", "P0", "L", "Not a black box"],
        ["E10-04", "Velocity limits: contribution, Ajo count, payout count", "P0", "M", "Configurable, not hard-coded"],
        ["E10-05", "Device, phone, and bank graph analysis", "P1", "L", "Catches what per-transaction limits miss"],
        ["E10-06", "Sanctions and PEP screening", "P0", "M", "**Requires a licensed provider and a legal determination**"],
        ["E10-07", "Member reporting of organizers and messages", "P0", "M", "Reviewed by a human"],
        ["E10-08", "Freeze that blocks sending but never receiving", "P0", "M", "The rule that prevents confiscation by software"],
        ["E10-09", "SAR workflow and filing", "P0", "L", "**Statutory deadline applies; confirm with counsel**"],
        ["E10-10", "Fraud metrics, including false positive rate", "P1", "M", "Controls must earn their cost"],
        ["E10-11", "Anti-phishing messaging throughout the product", "P0", "S", "Cheap and extremely effective"],
    ]},

    {"t": "h2", "text": "23.13 Detailed backlog — Epic 11, platform"},
    {"t": "table", "head": ["ID", "Item", "Priority", "Effort", "Note"], "widths": [0.8, 3.2, 1.1, 0.9, 1.5], "size": 8.2, "rows": [
        ["E11-01", "Repository, CI pipeline, and quality gates", "P0", "M", "Blocks merge on anything"],
        ["E11-02", "Environments: local, CI, staging, pre-prod, production", "P0", "M", "Identical in shape"],
        ["E11-03", "Structured logging with PII redaction at source", "P0", "M", "Not filtered later"],
        ["E11-04", "Metrics, dashboards, and alerting with runbooks", "P0", "L", "Actionable alerts only"],
        ["E11-05", "Distributed tracing across the async boundary", "P1", "M", "Correlates payment journeys"],
        ["E11-06", "Backups with a rehearsed restore", "P0", "M", "Quarterly drill, timed against the RTO"],
        ["E11-07", "Database migration strategy, expand then contract", "P0", "M", "No destructive migration in a code deploy"],
        ["E11-08", "Secret management and rotation", "P0", "M", "Per environment, never in source"],
        ["E11-09", "API versioning and backward compatibility", "P0", "M", "Old app versions stay live for weeks"],
        ["E11-10", "Feature flags with an audit trail", "P1", "M", "With removal dates"],
        ["E11-11", "Mobile build pipeline, signing, and staged rollout", "P0", "L", "App store distribution"],
    ]},

    {"t": "h2", "text": "23.14 Deferred items and why"},
    {"t": "table", "head": ["Item", "Deferred because", "Revisit when"], "widths": [2.0, 2.5, 1.9], "size": 8.2, "rows": [
        ["Independent escrow agent", "Expensive, and not required to launch. A real trust differentiator later", "After demonstrated scale, or on investor demand"],
        ["Yield on pooled funds", "Changes the product from a savings group to an investment product. A different business entirely", "**Only with a completely separate legal and regulatory basis. Never as a feature**"],
        ["Corporate and employer Ajos", "Different onboarding, compliance, and support model", "After consumer product-market fit"],
        ["Native Android build", "React Native covers the requirement. A rebuild is a large effort", "If a specific native requirement is proven"],
        ["Open social features", "Trust and safety risk, and contrary to the private design", "Never, in the current model"],
        ["Automated credit scoring", "Exclusion risk, and a regulatory exposure", "Not planned"],
        ["Multi-currency", "No requirement, and a large surface area", "Not planned"],
        ["Android-only USSD interface", "Inclusion is valuable, but a web and SMS path exists", "If feature-phone usage proves material"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "The most important deferred item is the one nobody argues for.",
     "text": "The genuinely hard questions — reconciliation, fraud controls, defaults, and the "
     "cold-start problem — get little attention compared to features. The backlog above is "
     "weighted deliberately towards the boring, unglamorous work that determines whether "
     "members' money is safe. That weighting is the difference between a fintech and a "
     "payment wrapper."},

    {"t": "h2", "text": "23.15 Definition of done"},
    {"t": "p", "text": "An item is done only when all of the following are true. This "
     "definition exists because a partial financial feature is worse than no financial "
     "feature."},
    {"t": "bullets", "items": [
        "The acceptance criteria in the specification are met, and demonstrated.",
        "Unit tests cover the domain logic, including the failure paths.",
        "Integration tests cover the persistence and the authorisation.",
        "The permission check is implemented and tested, with RLS where the data is sensitive.",
        "Audit logging is in place for any privileged or money-touching action.",
        "Empty, loading, and error states are designed and built — not left to the implementer.",
        "Accessible: screen reader, contrast, and scaling checked.",
        "Copy is written, and it is correct about money. No placeholder text in a payment flow.",
        "Monitoring exists for the new code path, and an alert would fire if it broke.",
        "Documentation and the runbook are updated where relevant.",
        "Reviewed by someone other than the author, and for money paths, by two people.",
    ]},
]
