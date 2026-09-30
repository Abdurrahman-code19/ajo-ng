"""Section 21 — Analytics, Metrics and Reporting."""

BLOCKS = [
    {"t": "h1", "text": "21. Analytics, Metrics and Reporting"},

    {"t": "lead", "text": "Analytics serves three audiences with three different needs, and "
     "confusing them is how dashboards become useless. The member needs to understand their "
     "own savings. Operations needs to know the platform is healthy. The business needs to "
     "know whether the model works. All three are served by the same ledger — which is one "
     "of the strongest arguments for building the ledger first."},

    {"t": "h2", "text": "21.1 Principles"},
    {"t": "numbers", "items": [
        "**The ledger is the only source of financial truth.** No analytics figure is computed from a cache, a client log, or a provider report alone.",
        "**One definition per metric, written down.** 'Active member' means one thing across every dashboard, report, and conversation. This is enforced by a metrics catalogue, not by goodwill.",
        "**Pseudonymous by default.** Analytics carry opaque identifiers. Names, phone numbers, emails, and bank details never enter an analytics system.",
        "**Derived data is disposable and rebuildable.** If a transformation is wrong, it is fixed and re-run. The ledger is never rebuilt to fix a report.",
        "**Metrics that cannot change a decision do not belong on a dashboard.** Every chart answers a question somebody actually asks.",
    ]},

    {"t": "h2", "text": "21.2 Data flow"},
    {"t": "code", "size": 7.6, "text": """
  domain events ──▶ event stream ──▶ warehouse (aggregated, pseudonymised)
  (ledger, positions,                     │
   notifications)                          ├──▶ product dashboards
                                          ├──▶ operational dashboards
  PostgreSQL ──▶ nightly ETL ─────────────┤
  (authoritative, immutable)              ├──▶ finance reporting
                                          ├──▶ member statements
                                          └──▶ regulatory / audit packs
"""},
    {"t": "p", "text": "A warehouse or a set of materialized aggregates is what makes "
     "reporting possible without loading the transactional database. It is a read replica "
     "of the truth, and it is safe to rebuild from the ledger at any time."},

    {"t": "h2", "text": "21.3 Metrics catalogue"},
    {"t": "p", "text": "The following definitions are binding across product, engineering, "
     "and finance. A metric used in a board deck but defined differently in an engineering "
     "dashboard is two metrics, and the disagreement will surface at the worst moment."},
    {"t": "table", "head": ["Metric", "Definition", "Notes"], "widths": [1.5, 3.1, 1.9], "size": 7.8, "rows": [
        ["Registered member", "An account created, regardless of verification", "Not a useful success metric on its own"],
        ["Verified member", "Identity verification completed successfully", "The first meaningful funnel step"],
        ["Active member", "Verified member with a contribution or a login in the last 30 days", "The headline retention metric"],
        ["Active Ajo", "Ajo in an active lifecycle state with at least one funded position", "Excludes draft, cancelled, and completed"],
        ["Funded Ajo", "Ajo that has reached FUNDED and not yet completed", "The conversion event that matters"],
        ["Ajo completion rate", "Completed ÷ funded Ajos", "The core product success metric"],
        ["Contribution", "A contribution captured successfully, per BR-021", "Never counted at initiation"],
        ["Contribution success rate", "Captured ÷ initiated payments", "Operationally critical"],
        ["Default", "A contribution not made by the deadline, per BR-012", "A structural product signal, not merely a member failure"],
        ["Default rate", "Defaulted positions ÷ positions in funded Ajos", "The single best leading indicator of product health"],
        ["Recovery rate", "Defaults cured within the grace period ÷ defaults", "Measures how fair the recovery process is"],
        ["Gross contribution volume", "Sum of captured contribution amounts, excluding fees", "The volume the 2% applies to"],
        ["Gross fee revenue", "Sum of fee entries, 2% of contributions", "Gross. Not profit, and not net of provider costs"],
        ["Net revenue", "Gross fee revenue minus provider fees and delivery costs", "Requires real provider rates, which are not yet confirmed"],
        ["Payout volume", "Sum of settled payouts", "Should equal gross contribution volume over time"],
        ["Payout success rate", "Succeeded ÷ released payouts", "The promise the product makes"],
        ["Payout cycle time", "ready_at to bank credit", "The member-experience metric"],
        ["Repeat Ajo rate", "Members who have completed or joined more than one Ajo", "The stickiness metric"],
        ["Time to first Ajo", "Registration to first join", "Onboarding effectiveness"],
        ["Cost per acquisition", "Marketing spend ÷ new verified members", "Requires marketing spend data"],
        ["Payback period", "Months of net revenue to recover CAC", "Cannot be computed until net revenue is real"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Gross fee revenue is not profit, and should never be reported as profit.",
     "text": "At a 2% fee, provider transaction costs are a large fraction of revenue, and "
     "the margin is thin enough that presenting 2% as profitability would be misleading to "
     "anyone reading the number. Gross revenue, net revenue, and contribution margin are "
     "three different lines, and only the last one describes whether the business works."},

    {"t": "h2", "text": "21.4 Member-facing analytics"},
    {"t": "p", "text": "This is the analytics that changes behaviour rather than "
     "informing it, and it is the part members actually value."},
    {"t": "h3", "text": "21.4.1 Personal savings dashboard"},
    {"t": "bullets", "items": [
        "**Total saved to date** across every completed and active Ajo — the single most motivating figure.",
        "**Ajos completed**, and the count of members helped.",
        "**Total fees paid**, stated plainly. Hiding it is a trust problem when the member sees it on a bank statement.",
        "**Next contribution** and its due date, prominently.",
        "**Savings trajectory** — a simple line over time, showing the pattern of steady accumulation. This is the emotional payoff of the product.",
        "**Historical round view** — what was paid in, what was received, when.",
    ]},
    {"t": "h3", "text": "21.4.2 Personal insights"},
    {"t": "bullets", "items": [
        "Average contribution per cycle, and how that compares with the previous Ajo.",
        "Contribution consistency — paid on time every round, or a pattern of near-misses. Framed supportively.",
        "Time to goal, if the member has set a savings target.",
        "Largest single payout received, with the Ajo and date.",
    ]},
    {"t": "p", "text": "Insights are computed for the member and shown only to them. No "
     "member ever sees another member's financial data, and no derived insight is used for "
     "scoring without a documented, lawful basis."},

    {"t": "h2", "text": "21.5 Operational dashboards"},
    {"t": "table", "head": ["Dashboard", "Audience", "Content", "Refresh"], "widths": [1.5, 1.3, 2.9, 0.8], "size": 8.2, "rows": [
        ["Money movement", "Operations", "Contributions and payouts per hour, success rates, cycle times, escrow balance", "5 min"],
        ["Reconciliation", "Finance", "Invariants, unmatched payments, breaks, the ledger-to-bank position", "15 min"],
        ["Queue health", "Engineering", "Depth, age, retries, dead letters, per queue", "1 min"],
        ["Provider health", "Engineering", "Latency, error rate, webhook lag, per endpoint", "1 min"],
        ["Ajo lifecycle", "Product", "Created, funded, active, completed, cancelled, with a funnel", "1 hour"],
        ["Risk", "Risk team", "Open alerts, holds, false positives, cases by type", "5 min"],
        ["Member health", "Product and support", "Default rate, recovery, complaints, NPS", "Daily"],
    ]},

    {"t": "h2", "text": "21.6 Financial reporting"},
    {"t": "h3", "text": "21.6.1 Monthly close"},
    {"t": "numbers", "items": [
        "Reconcile all accounts and the ledger; sign off with a named owner.",
        "Accrue fee revenue properly, and reconcile accrued fees to cash received. A 2% accrual on a contribution that has not settled is still a liability to be tracked.",
        "Report gross contribution volume, gross fee revenue, provider costs, and net margin separately.",
        "Report the escrow obligation as a liability, and the fee receivable as an asset. The obligation to members is not revenue and must never appear as such.",
        "Reconcile the reporting layer to the ledger. Any difference is investigated before the pack is issued.",
        "Issue the pack with a written commentary on variances, not just numbers.",
    ]},
    {"t": "h3", "text": "21.6.2 Compliance and audit reporting"},
    {"t": "bullets", "items": [
        "**Transaction reporting** — per-provider and regulator-facing reports, in the format the provider or authority specifies, generated from the ledger.",
        "**Suspicious Activity Reports**, filed within the statutory deadline, with a complete internal case file behind each one.",
        "**Audit packs** — for a financial audit or a regulatory examination: the ledger, the reconciliation records, the access logs, and the policy documents in force at the time.",
        "**Member statements** — monthly and annual, itemising contributions, fees, and payouts.",
    ]},
    {"t": "callout", "kind": "LEGAL", "title": "Reporting obligations must be established before launch, not after.",
     "text": "The specific reports required of AJO.ng — to the payment provider, to the bank, "
     "to the FIU, to any supervisory authority, and to tax authorities — depend on the "
     "business structure and the agreements in place, and none of that has been confirmed. "
     "**Qualified Nigerian legal and compliance professionals must establish these "
     "obligations before launch.** The architecture in this section is designed to support "
     "whatever they turn out to require, which is a reason to build it now and a reason not "
     "to assume its contents."},

    {"t": "h2", "text": "21.7 Product analytics"},
    {"t": "p", "text": "Funnel and behavioural analysis for improving the product, built on "
     "pseudonymous identifiers only."},
    {"t": "code", "size": 7.4, "text": """
  install → onboarding → verified → first Ajo viewed → first Ajo joined
          → first contribution → first round funded → first payout received
          → second Ajo

  Diagnose the drop at each step. The most common and most expensive leaks in a
  savings product are: verification abandonment, first-contribution failure, and
  the long wait for a first payout. Each of those is a fixable product problem,
  and each one costs a member.
"""},
    {"t": "bullets", "items": [
        "**Cohorts by join month**, because Ajo behaviour is inherently seasonal and a blended average hides it.",
        "**Event tracking** on the journeys that matter: onboarding steps, payment attempts and failures, notification interactions, and support contacts.",
        "**Error analysis by app version and device**, so a defect affecting a specific Android population is visible rather than anecdotal.",
        "**Qualitative input** — support tickets, app reviews, and member interviews. The numbers tell you where; the conversations tell you why.",
    ]},

    {"t": "h2", "text": "21.8 Data quality"},
    {"t": "p", "text": "A report built on unverified data is worse than no report, because "
     "it is acted upon. Data quality is measured, not assumed."},
    {"t": "table", "head": ["Check", "Frequency", "Threshold", "On failure"], "widths": [1.7, 1.1, 1.3, 2.4], "size": 8.4, "rows": [
        ["Ledger to warehouse", "Daily", "Zero difference", "Block the reporting layer; investigate"],
        ["Event completeness", "Daily", "< 0.1% loss", "Investigate the pipeline"],
        ["Metric definition drift", "Per release", "No undocumented change", "Reject the release"],
        ["Referential integrity in aggregates", "Daily", "Zero orphans", "Rebuild the aggregate"],
        ["Backfill verification", "Per backfill", "Matches the source exactly", "Discard and retry"],
        ["Dashboard freshness", "Continuous", "Within the stated refresh", "Alert; do not present stale figures as current"],
    ]},

    {"t": "h2", "text": "21.9 Analytics and privacy"},
    {"t": "bullets", "items": [
        "Analytics systems hold pseudonymous identifiers and financial aggregates, never names, phone numbers, emails, BVN, or bank details.",
        "Access to member-level analytics is restricted and logged. Aggregate reporting needs no member-level access at all, which is the default.",
        "Retention limits apply to analytics data per section 14.8. Aggregates are made irreversible or deleted on schedule; raw event data is not kept indefinitely.",
        "No third-party advertising or tracking SDKs. Analytics is first-party and proportionate.",
        "A member can request their data, and an analytics export must be able to identify which events belong to them, without exposing other members' data in the process.",
        "**Analytics never influence eligibility.** A member's savings behaviour may inform a *product recommendation* such as a better-suited Ajo size. It may not be used to deny a payout, change a fee, or exclude them from a product — that is discrimination, and it is prohibited.",
    ]},

    {"t": "h2", "text": "21.10 Governance"},
    {"t": "bullets", "items": [
        "**One owner per metric**, named, responsible for the definition and for answering questions about it.",
        "**Definition changes are versioned and announced**, with a note on whether historical figures are restated. Silent restatement of a metric destroys trust in every number on the dashboard.",
        "**A written definition accompanies every number** presented to the board, in the appendix rather than the headline.",
        "**A metrics review each quarter**: which metrics led to a decision, and which were simply interesting. The second category is where most of the clutter comes from, and removing it is a discipline.",
    ]},
    {"t": "callout", "kind": "NOTE", "title": "The metric the board will actually ask about.",
     "text": "It will not be contribution volume. It will be the completion rate and the "
     "default rate, because those two numbers decide whether people keep using AJO.ng. A "
     "platform can show impressive volume and still be failing, if members keep failing to "
     "receive what they saved for. Those two metrics deserve a place on the first slide of "
     "every business review."},
]
