"""Section 22 — Delivery Roadmap and Milestones."""

BLOCKS = [
    {"t": "h1", "text": "22. Delivery Roadmap and Milestones"},

    {"t": "lead", "text": "The roadmap is organised around a single commitment: get a "
     "small number of real people safely through a complete Ajo cycle, and prove that the "
     "money works. Everything that does not serve that goal is deferred, regardless of how "
     "attractive it looks."},

    {"t": "h2", "text": "22.1 Guiding constraints"},
    {"t": "bullets", "items": [
        "**No real money before the legal and compliance position is established.** This is a hard gate, not a phase that can be compressed.",
        "**No money before the ledger, reconciliation, and reconciliation alerting work and are tested.**",
        "**No member funds in platform operating accounts, ever**, pending a determination on the custody question.",
        "**At least one payment rail proven end to end** before any member is asked to pay.",
        "**No launch without the fraud controls that protect a payout**, principally the cooling-off on bank-account change and the multi-channel notification.",
        "Every phase ends with something demonstrable. A phase with only code behind it is not finished.",
    ]},
    {"t": "callout", "kind": "WARNING", "title": "The temptation to launch before the boring parts are done.",
     "text": "The reconciliation job, the alert that halts payouts, the reverse-entry "
     "path, the cooling-off period — none of these are visible in a demo, and all of them "
     "are what stand between the platform and a catastrophic mistake. They are the "
     "difference between a fintech and a group-chat app with a payment button, and they are "
     "where a rushed launch always loses."},

    {"t": "h2", "text": "22.2 Phase 0 — Foundation (complete)"},
    {"t": "p", "text": "The financial core, established before any product surface exists. "
     "Building this first is the single most consequential decision in the project."},
    {"t": "table", "head": ["Deliverable", "Status", "Note"], "widths": [2.6, 1.1, 2.8], "size": 8.4, "rows": [
        ["Canonical business and financial specification", "Complete", "Single source of truth for terms, rules, states, and entities"],
        ["Money primitive", "Complete", "Branded integer-kobo type; exact arithmetic; no floating point"],
        ["Append-only double-entry ledger", "Complete", "Balanced entries, reversal-only correction, computed balances"],
        ["Ajo lifecycle state machine", "Complete", "All transitions, the 5-day enrollment window, position lock"],
        ["FinancialProvider abstraction", "Complete", "Interface plus a production-guarded mock"],
        ["Adversarial domain tests", "Complete", "61 tests covering the money, ledger, fee arithmetic, and state machine"],
        ["Technical specification document", "Complete", "26 sections; the generated DOCX is committed alongside this table"],
    ]},

    {"t": "h2", "text": "22.3 Phase 1 — Hardened core and legal position"},
    {"t": "table", "head": ["Deliverable", "Exit criteria"], "widths": [2.8, 3.7], "size": 8.4, "rows": [
        ["Balanced fee posting in the ledger", "Contribution and fee capture post correctly and balance; reversal is exact; covered by tests"],
        ["Ledger reconciliation service", "The invariant is checked continuously, and a deliberately injected break is detected and alerts"],
        ["ProvidusUnity technical due diligence", "A verified sandbox specification, published fee schedule, and settlement behaviour — **or a documented decision to proceed with a different provider**"],
        ["Legal and compliance engagement", "Written advice on licensing, the treatment of member funds, data protection, and consumer protection"],
        ["Data protection programme", "Privacy notice, retention schedule, and data subject request process drafted and approved"],
        ["Payments partner agreement", "A signed agreement on terms, fees, settlement, and the handling of member funds"],
    ]},
    {"t": "callout", "kind": "LEGAL", "title": "Phase 1 has a legal exit criterion, not just an engineering one.",
     "text": "The advice obtained in this phase determines whether AJO.ng may operate at all, "
     "and in what form. It must come from **qualified Nigerian legal and compliance "
     "professionals**. Nothing in this document should be read as establishing that a "
     "particular structure is permissible, and no engineering milestone substitutes for "
     "that determination."},

    {"t": "h2", "text": "22.4 Phase 2 — Payments spine"},
    {"t": "table", "head": ["Deliverable", "Exit criteria"], "widths": [2.8, 3.7], "size": 8.4, "rows": [
        ["ProvidusFinancialProvider adapter", "Passes the full contract test suite against the provider sandbox"],
        ["Collection flow", "A member pays end to end, and the contribution is confirmed by webhook"],
        ["Webhook handling", "Signature verification, replay protection, idempotent processing, and out-of-order handling all proven by test"],
        ["Escrow and settlement accounts", "Opened and configured, with a documented daily reconciliation owner"],
        ["Payout flow", "A single-member payout completes to a real bank account, with a reconciled result"],
        ["Reconciliation procedures", "All three run daily in staging against the sandbox and produce a clean result"],
        ["Reversals and refunds", "A duplicate capture and an over-contribution are both reversed correctly"],
    ]},

    {"t": "h2", "text": "22.5 Phase 3 — Member experience"},
    {"t": "table", "head": ["Deliverable", "Exit criteria"], "widths": [2.8, 3.7], "size": 8.4, "rows": [
        ["Registration and verification", "A new member registers, verifies identity, and consents, with the audit record complete"],
        ["Create and join an Ajo", "The 5-day enrollment, invitation, and position assignment all work and are tested at the boundary"],
        ["Contribute", "The fee is shown as a separate line, the total is correct, and failure states are handled"],
        ["Notifications", "Money events reach every enabled channel; the reminder schedule escalates correctly"],
        ["Payout experience", "The full cycle completes and the member sees a receipt and a statement"],
        ["Profiles, bank accounts, settings", "Members manage their own details, with cooling-off enforced on bank changes"],
        ["Help and support", "In-app help, a support channel, and a documented escalation path"],
    ]},

    {"t": "h2", "text": "22.6 Phase 4 — Organizer and admin"},
    {"t": "table", "head": ["Deliverable", "Exit criteria"], "widths": [2.8, 3.7], "size": 8.4, "rows": [
        ["Organizer tools", "Create, invite, monitor, and acknowledge, scoped strictly to their own Ajos"],
        ["Organizer reporting", "A structured default report that respects BR-019: no public exposure of a defaulting member"],
        ["Admin console", "Ajo oversight, member support lookup, dispute queue, and audit trail"],
        ["Risk console", "The alert queue, holds with reasons and deadlines, and the investigation record"],
        ["Finance console", "Reconciliation dashboards, manual operations with dual authorisation, and month-end reporting"],
        ["Dispute resolution", "Raise, respond, resolve, and notify, with a complete timeline"],
    ]},

    {"t": "h2", "text": "22.7 Phase 5 — Controlled pilot"},
    {"t": "p", "text": "A small, invited, closely supervised group. The purpose is to find the "
     "problems that only appear with real money and real people."},
    {"t": "table", "head": ["Deliverable", "Exit criteria"], "widths": [2.8, 3.7], "size": 8.4, "rows": [
        ["Pilot cohort", "10–20 trusted members, recruited personally, with real money"],
        ["Complete Ajo cycles", "At least three full cycles complete to a real bank account, reconciled"],
        ["Daily operations", "The runbook in section 13.13 is followed for the full pilot without improvisation"],
        ["Default handling", "At least one real default is processed end to end through recovery or formal default"],
        ["Member feedback", "Structured interviews with every pilot member, and every complaint logged and answered"],
        ["Defect resolution", "All critical and high defects closed"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "The pilot is the real test, and it should be treated as such.",
     "text": "A pilot exists to discover the assumptions that were wrong. If a pilot of "
     "fifteen people across three complete cycles produces no surprises, the pilot was not "
     "run properly — either the cohort was too safe, or the team was not watching. The "
     "questions to ask are: did anyone default unexpectedly, did anyone fail "
     "verification, did any reconciliation break occur, and did any member ask a question "
     "the product could not answer clearly?"},

    {"t": "h2", "text": "22.8 Phase 6 — Public launch"},
    {"t": "table", "head": ["Deliverable", "Exit criteria"], "widths": [2.8, 3.7], "size": 8.4, "rows": [
        ["Public availability", "Open registration, with onboarding and verification proven at volume"],
        ["Localisation", "Professional translation of all financial and instructional content, reviewed by native speakers"],
        ["Security certification", "Independent penetration test passed, with all critical and high findings closed"],
        ["Observability and on-call", "Dashboards live, alerting routing to a real rota, runbooks written"],
        ["Operations staffed", "Reconciliation, support, and risk roles filled and trained"],
        ["Support readiness", "Pre-approved incident templates, and a documented member communication process"],
    ]},

    {"t": "h2", "text": "22.9 Phase 7 — Growth"},
    {"t": "bullets", "items": [
        "Scale onboarding, marketing, and referral with real unit economics in view.",
        "Deepen member value: savings goals, Ajo recommendations sized to a member's demonstrated capacity, and portfolio-style views.",
        "Strengthen the community layer: verified Ajo organizers, member trust signals, and a transparent track record.",
        "Explore additional payment rails and partners to improve success rates and reduce per-transaction cost.",
        "Build the data platform properly once the volume justifies it.",
    ]},
    {"t": "p", "text": "Growth decisions in this phase are constrained by measured net "
     "revenue per member, not by gross volume. A member acquired at a cost the 2% fee cannot "
     "recover is not growth."},

    {"t": "h2", "text": "22.10 What is explicitly out of scope for MVP"},
    {"t": "bullets", "items": [
        "Corporate or institutional Ajos, employee-contribution schemes, or employer partnerships.",
        "Multiple partial payouts or graduated payouts. A full payout or no payout, per CANONICAL.md.",
        "Late-payment penalties, and any mechanism that charges other members extra for a default (BR-018).",
        "Public defaulters lists, shaming, or any reputational consequence for defaulting (BR-019).",
        "Open social features: public profiles, a member directory, follower graphs, or a public feed.",
        "Unilateral post-activation exit from an Ajo. There is no mechanism for one, by design.",
        "Escrow in the legal sense. AJO.ng holds no member funds itself, pending the determination in Phase 1.",
        "Cryptocurrency, investment products, or any return on savings. AJO.ng is a rotating savings group, not an investment scheme, and must not be presented as one.",
        "Multi-currency support.",
        "A native Android-only build.",
        "An independent escrow agent as a launch dependency. It is a strong future feature and an expensive one; it is not required to launch.",
    ]},
    {"t": "callout", "kind": "LEGAL", "title": "The boundary between a savings group and an investment product.",
     "text": "AJO.ng is a rotating savings group: members contribute in turn and receive what "
     "they saved, with no return beyond their own money. Presenting that as an investment, "
     "or describing it in language that implies one, would be misleading and would change "
     "the regulatory characterisation entirely. All marketing and product language must stay "
     "on the right side of that line, and the wording should be reviewed by counsel."},

    {"t": "h2", "text": "22.11 Dependencies and risks to the roadmap"},
    {"t": "table", "head": ["Dependency or risk", "Impact if it fails", "Mitigation"], "widths": [1.7, 2.2, 2.6], "size": 8.0, "rows": [
        ["ProvidusUnity does not support a required rail", "Launch is blocked or a different provider is needed", "Complete the technical due diligence in Phase 1. The adapter boundary means the cost of switching is engineering, not redesign"],
        ["Provider fees erode the 2% margin", "The business case weakens materially", "Model net revenue with real rates before scaling. Negotiate on volume. Consider rail mix"],
        ["Legal determination requires a different structure", "Significant additional work, or a different model", "Establish this in Phase 1, before building on an assumption"],
        ["Default rates higher than modelled", "Members are disappointed and reputational damage follows", "Build the recovery process properly. Track the default rate from the first cycle. Do not launch with an untested recovery path"],
        ["KYC or verification friction", "Onboarding abandonment", "Test verification early and often with real providers. Simplify the flow, not the verification"],
        ["Team capacity", "Phases slip", "Sequencing already assumes a small team. Cut scope, not control"],
    ]},
]
