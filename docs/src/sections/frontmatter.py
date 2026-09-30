"""Front matter: cover, document control, executive summary, product overview, contents."""

TITLE = "AJO.ng"
SUBTITLE = "Complete Product and Technical Specification"
VERSION = "Version 1.0"
STATUS = "For review — not a compliance determination"

COVER_NOTE = (
    "A complete blueprint for a private, invitation-only rotating savings platform, "
    "covering product requirements, user experience, architecture, data, payments, "
    "security, operations, testing, delivery, and the legal questions that must be "
    "resolved before the first naira moves."
)

COVER_META = [
    ("Product", "AJO.ng — a rotating savings platform for Nigeria"),
    ("Tagline", "Your Ajo. Your Story."),
    ("Version", "1.0"),
    ("Status", "For review. Requires review by qualified Nigerian legal and "
               "compliance professionals before production launch"),
    ("Source of truth", "docs/src/CANONICAL.md, followed by this specification"),
    ("Financial model", "2% service fee charged on every contribution, in addition to "
                        "the contribution amount. Never deducted from a payout"),
    ("Scope", "25 sections, plus appendices A–H"),
    ("Prepared for", "Founders, engineering, product, operations, legal, and investors"),
]

LEGAL_STATEMENT = (
    "This document is a technical and product specification. It is not legal advice, not a "
    "compliance determination, and not a financial plan. AJO.ng handles identity documents, "
    "bank details, and members' savings, and it operates in a regulated market. Before any "
    "real money is accepted or any member is onboarded, this specification and the operating "
    "model it describes require review by qualified Nigerian legal and compliance "
    "professionals — including on licensing, the treatment of member funds, data protection, "
    "consumer protection, and the obligations of the payment partner."
)

# Order matters: this is the sequence in the assembled document.
SECTIONS = [
    ("Executive Summary", "frontmatter"),
    ("Product Overview", "frontmatter"),
    ("1. Product Requirements Document", "s01_prd"),
    ("2. User Flows and Journeys", "s02_user_flows"),
    ("3. Sitemap and Screen Inventory", "s03_sitemap"),
    ("4. UX Specification", "s04_ux_spec"),
    ("5. Design System", "s05_design_system"),
    ("6. Wireframes", "s06_wireframes"),
    ("7. High-Fidelity UI Specification", "s07_hifi_ui"),
    ("8. Entity Relationship Model", "s08_erd"),
    ("9. Database Schema", "s09_schema"),
    ("10. Technical Architecture", "s10_architecture"),
    ("11. API Specification", "s11_api"),
    ("12. Authentication and Authorization", "s12_auth"),
    ("13. Payments, Reconciliation and Operations", "s13_payments"),
    ("14. Security, Privacy and Compliance", "s14_security"),
    ("15. Fraud, Risk and Financial Crime", "s15_fraud"),
    ("16. Notifications and Messaging", "s16_notifications"),
    ("17. Mobile Experience and Platform Strategy", "s17_mobile"),
    ("18. Test Strategy and Quality Assurance", "s18_testing"),
    ("19. Edge Cases and Failure Modes", "s19_edge_cases"),
    ("20. Infrastructure, DevOps and Environments", "s20_devops"),
    ("21. Analytics, Metrics and Reporting", "s21_analytics"),
    ("22. Delivery Roadmap and Milestones", "s22_roadmap"),
    ("23. Epics, Backlog and Prioritisation", "s23_backlog"),
    ("24. Legal, Regulatory and Compliance Considerations", "s24_legal"),
    ("25. Performance, Scalability and Financial Performance", "s25_performance"),
    ("26. Appendices", "s26_appendices"),
]

EXECUTIVE_SUMMARY = [
    {"t": "h1", "text": "Executive Summary"},

    {"t": "lead", "text": "AJO.ng is a private, invitation-only platform for rotating "
     "savings groups — Ajos — in Nigeria. Members of an Ajo contribute a fixed amount on a "
     "fixed schedule, and each member in turn receives the entire pool. It is not a bank, "
     "not an investment product, and it does not pay returns. It is the digital version of "
     "something Nigerian families and friend groups have done for decades, made reliable."},

    {"t": "h2", "text": "The product in one page"},
    {"t": "bullets", "items": [
        "**An Ajo has 2–20 members, a fixed contribution amount, a fixed frequency, and a fixed number of rounds.** Ten members, NGN 10,000 weekly, ten rounds is the standard Ajo, and it returns NGN 1,000,000 to each member in turn.",
        "**Enrollment lasts exactly five days.** After that the group is fixed, because a savings group that can still change membership after the first payment is not a savings group.",
        "**A member contributes NGN 1,000 and pays a NGN 20 service fee — 2% — for a total of NGN 1,020.** The fee is charged on the contribution and is never taken from what the member receives. The recipient always gets the full base pool.",
        "**The cycle is mechanical and fair.** Round ten, the member who joined last receives the pool. Everyone knows whose turn it is, and the schedule is fixed at activation.",
        "**Positions lock at activation.** A member cannot be removed after committing, and cannot leave without a default. Both rules protect the people already in the pool.",
        "**A missed contribution has a defined, humane path.** Reminders escalate over seven days, a 48-hour grace period follows, and a recovery payment restores the position. The defaulting member is never publicly exposed, and no other member is ever charged extra (BR-018, BR-019).",
        "**The platform never custodies member funds.** Contributions are held in a ring-fenced escrow position, segregated from operating accounts. Whether the chosen payment arrangement amounts to custody in the legal sense is one of the questions that must be answered by counsel before launch.",
        "**The organizer facilitates; they never touch money.** They create the Ajo, invite people, send reminders, and monitor contributions. They cannot collect funds, charge a fee, request a BVN, or remove an activated member.",
    ]},

    {"t": "h2", "text": "The business model"},
    {"t": "p", "text": "Revenue is a 2% service fee on every contribution. In the base "
     "scenario — 300 Ajos of 10 members contributing NGN 10,000 for 10 rounds — the platform "
     "collects NGN 300 million in contributions and earns NGN 6 million in fees, which is "
     "NGN 20,000 per Ajo."},
    {"t": "table", "head": ["Scenario", "Ajos", "Members", "Contribution", "Volume", "Gross fee (2%)"], "widths": [1.3, 0.8, 0.9, 1.3, 1.5, 1.4], "size": 8.2, "rows": [
        ["Conservative", "150", "8", "NGN 7,500", "NGN 90,000,000", "NGN 1,800,000"],
        ["Base", "300", "10", "NGN 10,000", "NGN 300,000,000", "NGN 6,000,000"],
        ["Growth", "600", "12", "NGN 12,000", "NGN 864,000,000", "NGN 17,280,000"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "2% is gross, not profit.",
     "text": "Payment provider transaction fees, message delivery, and operating costs all "
     "sit between the gross fee and the net margin, and the provider rates are unknown "
     "until the ProvidusUnity agreement is obtained. The 2% is the revenue model, and it is "
     "frequently confused with profitability. It should not be."},

    {"t": "h2", "text": "What makes this hard, and what the specification does about it"},
    {"t": "p", "text": "A savings platform looks like a simple app and behaves like a "
     "financial institution. The difficult parts are not the screens."},
    {"t": "table", "head": ["Problem", "Why it is hard", "How this specification handles it"], "widths": [1.5, 2.4, 2.6], "size": 8.0, "rows": [
        ["Money that arrives late, twice, or not at all", "Card, transfer, wallet, and USSD rails all fail in different ways, and a member's position depends on knowing the truth", "Webhook-only confirmation, idempotency keys, a two-phase ledger, and a contribution that shows *pending verification* until proven otherwise"],
        ["A ledger that must never be wrong", "Any error becomes a financial claim the platform cannot substantiate", "Append-only double-entry in integer kobo, reversal-only correction, computed balances, and a continuous invariant check that halts payouts on a break"],
        ["Payout redirection fraud", "AJO.ng knows the amount, date, and destination account weeks in advance, which makes a predictable payout a standing target", "A 14-day cooling-off on bank-account change, step-up authentication, and notification to every channel on every change"],
        ["A member freezing must not trap their money", "A risk control that blocks a payout is a confiscation by software", "Freeze blocks sending, never receiving. A frozen, suspended, or dormant member can always be paid"],
        ["Reconciling bank reality against the books", "Transfers can arrive with no reference, an edited description, or a stale one", "Three daily reconciliations with a named owner, aging of unmatched money, and a payout halt on any break"],
        ["Defaults without shaming", "A missed payment is a financial event, not a moral failure, and the group must keep working", "Seven-day reminder escalation, a 48-hour grace period, a recovery path, no public defaulters list, and no extra charge to other members"],
        ["Organizers are human and fallible", "The one unverified participant with real influence over real money", "Scoped permissions, no custody, no unilateral removal, a visible reporting channel, and organizer abuse as a first-class risk category"],
        ["Privacy of identity documents", "BVN and bank details are the most attractive data in the system", "Data minimisation, envelope encryption, log redaction at source, RLS as a second authorization layer, and retention limits"],
    ]},

    {"t": "h2", "text": "How the system is built"},
    {"t": "bullets", "items": [
        "**A pure TypeScript domain core** holds the money type, the ledger, the state machine, and the payment provider interface. It has no I/O, which is what makes it exhaustively testable — 44 adversarial tests, and it is the layer the whole system rests on.",
        "**A modular monolith** rather than microservices, because financial correctness is far easier to guarantee inside one deployable unit and one transaction boundary. The API is Node.js and Fastify; the client is React Native and Expo; the database is PostgreSQL.",
        "**All money movement goes through a `FinancialProvider` interface**, so the application never imports a provider SDK. A mock implementation that refuses to run in production lets the entire test suite run with no network at all, and makes a provider change an engineering task rather than a redesign.",
        "**Long-lived processes, not serverless, on the money path.** Ten thousand members completing an Ajo is ten thousand units of work with a deadline, and serverless time limits are the wrong shape for it.",
        "**Authorization in two independent layers** — application checks plus PostgreSQL Row Level Security — so a bug in one does not expose member data.",
    ]},

    {"t": "h2", "text": "The delivery sequence"},
    {"t": "p", "text": "The order of work is deliberate, and the boring parts come before the "
     "exciting ones. A savings platform that launches with a beautiful interface and an "
     "unreconciled ledger has launched the wrong product."},
    {"t": "table", "head": ["Phase", "Focus", "Exit criteria"], "widths": [1.3, 2.3, 2.9], "size": 8.2, "rows": [
        ["0 — Foundation", "Money type, ledger, state machine, provider interface, tests", "**Complete**"],
        ["1 — Hardened core and legal", "Balanced fee posting, reconciliation service, Providus due diligence, counsel's advice", "Written advice on licensing and the treatment of member funds"],
        ["2 — Payments spine", "Collection, webhooks, escrow, reconciliation, reversals", "A contribution confirmed by webhook, and a real payout reconciled"],
        ["3 — Member experience", "Registration, verification, Ajo lifecycle, contribute, payout, notifications", "A complete cycle works for a real member"],
        ["4 — Organizer and admin", "Organizer tooling, admin console, risk console, finance console, disputes", "Operations can run the business without engineering"],
        ["5 — Controlled pilot", "10–20 members, real money, at least three complete cycles", "Every real problem found and fixed while it is still cheap to fix"],
        ["6 — Public launch", "Localisation, penetration test, staffed operations, on-call", "Every control in section 14.15 verified live"],
        ["7 — Growth", "Scale, member value, community, additional rails", "Measured net revenue per member, not gross volume"],
    ]},

    {"t": "h2", "text": "What is not being built, and why"},
    {"t": "p", "text": "The excluded list is as much a part of the specification as the "
     "included one. Scope discipline is what makes a financial product deliverable by a "
     "small team."},
    {"t": "bullets", "items": [
        "**No investment features, no yield, no returns.** This is a savings group. Adding an apparent return would change the legal character of the product, mislead every member who read it, and breach the disclosure principles in section 24.8.",
        "**No partial payouts, no penalties, no extra charges on other members.** A payout is the full pool or nothing, and a default is a missed payment, not a debt the group must absorb.",
        "**No public defaulters list, no shaming, no reputational consequence.** A member in financial difficulty is the most vulnerable person in the transaction.",
        "**No unilateral exit after activation, and no open social features.** A savings group that can be disrupted after the money is in is not a savings group.",
        "**No custody by AJO.ng itself**, pending the legal determination. The platform moves money through a segregated payment arrangement and never holds it as principal.",
    ]},

    {"t": "h2", "text": "The open questions that matter"},
    {"t": "p", "text": "All fifteen items on the pre-launch legal checklist in "
     "section 24.14 are outstanding, and none of them is an engineering task."},
    {"t": "table", "head": ["Question", "Why it blocks launch"], "widths": [2.4, 4.1], "size": 8.4, "rows": [
        ["Does AJO.ng require regulatory registration or a licence, and which authority?", "It determines the business model, the capital requirements, and the timeline. Everything else follows from it"],
        ["Does holding member funds in a pooled account constitute custody?", "If yes, the account structure, segregation, reconciliation, and possibly the licensing all change materially"],
        ["What does the ProvidusUnity agreement permit?", "Some providers permit an agency arrangement and some do not permit pooled accounts at all. The technical due diligence has not been done"],
        ["What are the AML, KYC, and suspicious-activity-reporting obligations, and who discharges them?", "A money laundering reporting officer may be legally required, and the reporting deadline is statutory"],
        ["What is the tax treatment of the fee and of contributions?", "Affects the financial model and the member statements"],
        ["How is a default legally characterised — breach, debt, or loss?", "A foundational design question, not an edge case. It determines what happens to the Ajo"],
    ]},
    {"t": "callout", "kind": "LEGAL", "title": "This is the critical path, and it does not run through engineering.",
     "text": "The technology in this specification is buildable. The questions above are "
     "answerable only by **qualified Nigerian legal and compliance professionals**, and "
     "they should be opened now, in parallel with development, rather than treated as the "
     "last gate before launch. A fintech that builds for a year and then discovers its "
     "structure is wrong has wasted a year."},

    {"t": "h2", "text": "How to read this document"},
    {"t": "table", "head": ["If you are", "Read", "Why"], "widths": [1.6, 1.8, 3.1], "size": 8.4, "rows": [
        ["A member of the team joining the project", "§1, §5, §23", "The product rules, the vocabulary, and what is being built next"],
        ["A backend engineer", "§10, §11, §13, §16, §20", "Architecture, API, money movement, queues, and operations"],
        ["A frontend or mobile engineer", "§4–§7, §11, §17", "The screens, the design system, and the client obligations"],
        ["A product manager or founder", "§1–§3, §21, §22, §25", "Requirements, flows, metrics, roadmap, and economics"],
        ["A security reviewer", "§12, §14, §15, §18", "Authorization, controls, fraud, and how they are tested"],
        ["A lawyer or compliance adviser", "§1, §2, §5, §13, §24", "The business rules, the money flows, and the open questions"],
        ["An investor or advisor", "Executive summary, §21, §22, §25", "The model, the metrics, the plan, and the risks"],
    ]},
    {"t": "p", "text": "Terms are defined once in `CANONICAL.md` and used identically "
     "throughout. The glossary is Appendix E. Where this document and the earlier business "
     "documents disagree — and they do, on pricing — this document and `CANONICAL.md` are "
     "authoritative."},
]

PRODUCT_OVERVIEW = [
    {"t": "h1", "text": "Product Overview"},

    {"t": "lead", "text": "This overview exists for a reader who needs to understand what "
     "AJO.ng is, who it is for, and how it works, without reading twenty-five sections. It "
     "introduces the domain, the people, the money, and the shape of the product."},

    {"t": "h2", "text": "The problem"},
    {"t": "p", "text": "Rotating savings groups are one of the oldest and most reliable "
     "financial mechanisms in the world, and they are everywhere in Nigeria. Family members "
     "run them. Church groups run them. Market traders run them. They work because trust "
     "between the participants is high, and because a fixed schedule with a visible "
     "deadline is a discipline that individual savings rarely provide."},
    {"t": "p", "text": "They also break in predictable ways, and the failures are not about "
     "money being stolen by criminals."},
    {"t": "bullets", "items": [
        "**Trust is not enforced, only assumed.** The whole group depends on one person's honesty, and there is no mechanism when that assumption fails.",
        "**The record is somebody's notebook.** Contributions are tracked in a book, a WhatsApp group, or someone's memory. When there is a disagreement, there is no evidence.",
        "**Defaults are handled socially.** Missing a contribution is a matter of shame, embarrassment, or silent pressure, and the group has no process. So a single default can end the arrangement for everyone.",
        "**A default leaves the group short.** With no mechanism to cover a missing contribution, the remaining members either absorb the loss — which nobody agrees to — or the Ajo collapses.",
        "**Payout is slow and paper-based.** The money may exist but reaching the member takes a queue, a signature, and a bank trip.",
        "**The group cannot scale.** An Ajo lives inside one relationship network, and bringing in a stranger requires a level of trust that a group chat cannot offer.",
        "**Organizer burden.** Whoever runs the Ajo spends hours chasing, reconciling, and reminding, with no tools and no record.",
    ]},
    {"t": "p", "text": "AJO.ng addresses all seven. Not by replacing trust with technology, "
     "but by giving a trusted group the record, the reminders, the enforcement, and the "
     "rail that it currently lacks."},

    {"t": "h2", "text": "Who it is for"},
    {"t": "table", "head": ["Segment", "Profile", "What they get"], "widths": [1.6, 2.5, 2.4], "size": 8.0, "rows": [
        ["The disciplined saver", "Contributes regularly, already saves informally, wants the discipline without the admin", "A fixed schedule, automatic reminders, and a visible record of every naira"],
        ["The cash-flow participant", "Income arrives irregularly, or in a business with daily swings", "A structure that fits a variable income, with the payout as a buffer"],
        ["The migrant worker", "Sends money home, wants to save for family or for a return", "A fixed commitment to a person, not an account"],
        ["The group organiser", "Runs the Ajo today, spends hours on it, has no tools", "Automated reminders, a live contribution status, and no need to chase people"],
        ["The small trader or artisan", "Turns capital over quickly, values liquidity", "A rotating structure rather than a locked savings account"],
        ["The diaspora family", "Wants to support relatives transparently and safely", "Visibility and a formal record, without handling anyone's bank details"],
    ]},
    {"t": "p", "text": "Not the target at MVP: institutional or corporate participation, "
     "investment products, high-value savers, and anyone seeking returns. Those are "
     "different products with different obligations."},

    {"t": "h2", "text": "The domain, in plain language"},
    {"t": "table", "head": ["Concept", "What it means", "Example"], "widths": [1.4, 2.7, 2.4], "size": 8.0, "rows": [
        ["Ajo", "A group of members who rotate contributions on a fixed schedule", "10 members, weekly"],
        ["Round", "One collection cycle in the Ajo", "Round 3 of 10"],
        ["Contribution", "One member's payment for one round", "NGN 1,000"],
        ["Service fee", "2% charged on top of each contribution", "NGN 20"],
        ["Total charged", "Contribution plus fee", "NGN 1,020"],
        ["Pool", "The sum of all contributions in a round — what one member receives", "NGN 10,000"],
        ["Position", "One member's place in one Ajo", "Member 7, round 7"],
        ["Payout", "The release of the pool to the member whose turn it is", "NGN 10,000 to member 7"],
        ["Default", "A contribution not made by its deadline, after a 48-hour grace period", "Round 5 unpaid"],
        ["Recovery", "Curing a default, restoring the position without changing the pool", "Pays NGN 1,020 on day 2"],
        ["Enrollment window", "The 5 days in which members may join", "Opens at creation"],
        ["Activation", "The moment every position is fully paid, and positions lock", "Ajo becomes FUNDED"],
        ["Organizer", "The member who creates and runs the Ajo. Never touches money", "Amaka"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "One Ajo, worked through.",
     "text": "Ten members, NGN 10,000 weekly, ten rounds. Every member pays NGN 10,000 plus "
     "a NGN 200 fee, NGN 10,200, each week. The pool is NGN 100,000, and it goes to one "
     "member per round. In round 7 it goes to member 7. After ten rounds, every member has "
     "contributed NGN 102,000 in total — NGN 100,000 into the pool and NGN 2,000 in fees — "
     "and received NGN 1,000,000. The platform earned NGN 20,400."},

    {"t": "h2", "text": "The people and their roles"},
    {"t": "table", "head": ["Role", "What they do", "What they cannot do"], "widths": [1.4, 2.6, 2.5], "size": 8.0, "rows": [
        ["Member (user)", "Joins an Ajo, contributes on schedule, receives their payout, manages their own money", "Remove themselves after activation, or take money out before their turn"],
        ["Ajo organizer", "Creates the Ajo, invites members, monitors contributions, sends reminders, acknowledges a default", "Handle money, charge a fee, request a BVN, remove an activated member, or edit the ledger"],
        ["Support agent", "Helps members, investigates transactions and payout status, escalates problems", "Move money, alter the ledger, or decide a dispute outcome"],
        ["Risk officer", "Reviews fraud alerts, places holds, freezes, runs investigations, files reports where required", "Edit the ledger, or block a payout that is already owed without reason"],
        ["Finance / reconciliation", "Runs the daily reconciliations, month-end close, and manual money operations", "Move money without dual authorisation"],
        ["Super admin", "Platform administration, roles, escalations, and oversight", "**Edit or delete a ledger entry. No role can, and this is deliberate**"],
    ]},

    {"t": "h2", "text": "The Ajo lifecycle"},
    {"t": "code", "size": 7.8, "text": """
  DRAFT ──organizer configures──▶ OPEN ──5-day window closes, all paid──▶ FUNDED
   │                                │                                        │
   │                                └──cancelled, all refunded──▶ CANCELLED  │
   │                                                                          ▼
   └──abandoned──▶ CANCELLED                                          ACTIVE ──all rounds──▶ COMPLETED
                                                                              │
                                        HELD (shortfall) ◀──────────────────┘
"""},
    {"t": "p", "text": "`COMPLETED` and `CANCELLED` are terminal. The 5-day enrollment "
     "window is enforced server-side and tested at its boundary. A position locks at "
     "activation and can never be unlocked or removed. `HELD` is a structural shortfall — "
     "the pool is not fully funded — and it is resolved, never written off silently."},

    {"t": "h2", "text": "How money moves"},
    {"t": "numbers", "items": [
        "**The member initiates.** They choose a rail — card, bank transfer, mobile money, or USSD — and are shown the itemised breakdown: contribution, fee, total.",
        "**A pending entry is recorded**, holding a claim on escrow cash, before anything is attempted.",
        "**The provider confirms by webhook.** A verified webhook is the only thing that marks a contribution paid. A browser redirect is a hint, not evidence.",
        "**The capture entries post, each balanced:** debit escrow cash and credit contributions receivable for the contribution, then debit escrow cash and credit fee income for the 2%. The position becomes funded and the member is notified.",
        "**At the scheduled date, the Ajo completes** and a batch payout is released to every member whose turn has come.",
        "**Each payout posts two entries:** recognition moves the obligation, settlement moves the cash. The receipt is generated and the member is notified.",
        "**Daily, three reconciliations run** — against the provider, against the bank, and internally. Any break halts new payouts.",
    ]},
    {"t": "callout", "kind": "WARNING", "title": "The two-entry payout is not an implementation detail.",
     "text": "Splitting recognition from settlement is what makes it possible, at any moment, "
     "to answer the question an auditor will ask: how much do you owe your members right "
     "now? Collapsing the two entries would make that question unanswerable, and would make "
     "a failure mid-payout unrecoverable."},

    {"t": "h2", "text": "What the product refuses to do"},
    {"t": "p", "text": "The exclusions are design decisions, and several of them are the "
     "reason the product is defensible."},
    {"t": "table", "head": ["Refusal", "Reason"], "widths": [2.2, 4.3], "size": 8.2, "rows": [
        ["No yield, no interest, no returns", "It is a savings group, not an investment product. A return would change its legal character and mislead every member who read it"],
        ["No public defaulters list", "A member in financial difficulty is the most vulnerable person in the transaction. BR-019"],
        ["No extra charge on other members for a default", "Nobody agreed to cover someone else's commitment. BR-018"],
        ["No partial payouts", "A member receives the full pool or nothing. A reduced payout is a smaller loss of trust than a delayed one"],
        ["No unilateral post-activation exit", "An exit would break commitments already funded by others"],
        ["No organizer custody of money", "The organizer facilitates; the platform contracts and holds the funds. Ambiguity here is the platform's biggest unmanaged risk"],
        ["No money through chat", "Every money event happens in the product, where it is recorded"],
        ["No automated decisioning on a member's money", "Risk scoring informs a human decision. It never autonomously confiscates or denies a payout"],
        ["No public directory, no open social features", "Trust is the product. An open member directory is a fraud and harassment surface"],
    ]},

    {"t": "h2", "text": "The trust promise"},
    {"t": "p", "text": "Everything above reduces to a single promise a member can rely on, "
     "and it is worth stating plainly."},
    {"t": "callout", "kind": "NOTE", "title": "What AJO.ng promises its members.",
     "text": "Your contribution is recorded the moment it is confirmed, and not before. "
     "You always know what you owe, what you have paid, and what you will receive. You are "
     "told in advance when something is late, held, or under review — never after the fact. "
     "Nobody's money is ever released to a destination they did not authorise. A payment "
     "problem is never blamed on you before it is investigated. And no circumstance, "
     "including a security freeze, prevents you from receiving money you have already "
     "earned."},
]
