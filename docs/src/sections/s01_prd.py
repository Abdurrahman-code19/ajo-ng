"""
Section 1 — Product Requirements Document (PRD).

Source of truth: docs/src/CANONICAL.md
Authoring contract: docs/src/AUTHORING.md

The 2% platform fee is quoted exactly as CANONICAL.md defines it:
a member owing NGN 1,000.00 is charged NGN 1,020.00; the recipient of a
10-member round receives the base pool NGN 10,000.00, never NGN 10,200.00.
"""

BLOCKS = [
    {"t": "h1", "text": "1. Product Requirements Document"},
    {
        "t": "lead",
        "text": (
            "This section defines what AJO.ng is, for whom, what it promises, and exactly "
            "what it will and will not do at launch. It is a product document, not a "
            "licensing opinion, not a tax opinion and not a statement of regulatory "
            "compliance. Every claim about Nigerian financial regulation, data protection or "
            "payment-provider capability in this document is marked for verification by "
            "qualified Nigerian professionals and by the appointed payment partner."
        )
    },
    {
        "t": "kv",
        "pairs": [
            ("Product", "AJO.ng"),
            ("Tagline", "*Your Ajo. Your Story.*"),
            ("Category", "Savings / rotating-savings fintech"),
            ("Founders", "Abdurrahman Lawal and Abdurrahman Oriolowo"),
            ("Stage", "Pre-launch. No live transaction volume. No customer data."),
            ("Revenue model", "2% platform fee on every contribution deposit (locked)"),
            ("This section covers", "Sections 1.1 to 1.28"),
        ],
    },

    # ------------------------------------------------------------------ 1.1
    {"t": "h2", "text": "1.1 Executive summary"},
    {
        "t": "p",
        "text": (
            "AJO.ng digitises the Nigerian *Ajo* (also called *esusu*): a rotating savings "
            "scheme in which a fixed group of people pays a fixed amount into a common pot on "
            "a fixed schedule, and each member in turn receives the entire pot. The Ajo has "
            "existed for generations in markets, mosques, associations, workplaces and "
            "families. It works because the members trust each other. It fails for a narrow "
            "and specific set of reasons that have nothing to do with trust and everything to "
            "do with record-keeping."
        )
    },
    {
        "t": "p",
        "text": (
            "AJO.ng keeps the trust. It removes the notebook. Every contribution, every "
            "position, every payout and every default is written to an append-only ledger the "
            "organiser cannot edit, the platform cannot quietly amend, and no role including "
            "`super_admin` can delete. The organiser stops being a cashier and becomes a "
            "facilitator. The member stops carrying a risk they cannot see and gains a "
            "commitment they can hold someone to."
        )
    },
    {"t": "h3", "text": "1.1.1 The problem in one paragraph"},
    {
        "t": "p",
        "text": (
            "A 10-member Ajo with a NGN 10,000.00 monthly contribution moves NGN 1,000,000.00 "
            "over ten months. Every naira of that depends on a single person's honesty, "
            "availability and memory. The organiser is simultaneously the collector, the "
            "recorder, the only auditor and the guarantor. If the organiser falls ill, "
            "travels, dies, loses the notebook or is tempted, the scheme stops. There is no "
            "second copy, no counterparty the members can check against, and no way to settle "
            "a disagreement other than memory versus memory."
        )
    },
    {"t": "h3", "text": "1.1.2 What AJO.ng does"},
    {
        "t": "p",
        "text": (
            "AJO.ng provides four things and refuses to pretend it provides a fifth."
        )
    },
    {
        "t": "table",
        "head": ["Capability", "What it actually does"],
        "rows": [
            [
                "A shared, verifiable record",
                "Every position, contribution, fee, payout, default and dispute is written to "
                "an append-only ledger with a full audit trail. Any member can see the same "
                "truth the organiser sees.",
            ],
            [
                "Enforcement without shaming",
                "Reminders, grace windows, private default handling and a documented recovery "
                "process. The platform never automatically charges other members extra and "
                "never publicly exposes a defaulting member.",
            ],
            [
                "Money movement that balances",
                "Contributions, the 2% platform fee and payouts move through a documented "
                "ledger recognition sequence in a mandatory order. Every transaction balances "
                "to zero or is rejected. Payouts are released only when funds are actually "
                "available.",
            ],
            [
                "A commitment people can rely on",
                "A 5-day enrollment window, positions that lock on activation, and a "
                "complete-cycle commitment with a formal replacement mechanism instead of "
                "quiet unilateral exit.",
            ],
            [
                "What it does not do",
                "It does not lend, it does not invest, it does not insure, it does not take "
                "deposits on AJO.ng's own account, and it does not replace the organiser's "
                "social commitment. It makes the organiser's commitment checkable.",
            ],
        ],
        "widths": [1.85, 4.65],
    },
    {"t": "h3", "text": "1.1.3 The commercial position"},
    {
        "t": "p",
        "text": (
            "AJO.ng earns a **2% platform fee on every contribution deposit**. The fee is "
            "added on top of the contribution, shown separately on every receipt, in every "
            "Ajo details screen, and in the invitation and join confirmation before the "
            "member commits. It is never deducted from a contribution and it never reduces a "
            "payout. On the base-case Year-1 model this is 300 Ajos, 30,000 deposits, "
            "NGN 300,000,000 of contribution volume and NGN 6,000,000 of gross fee revenue."
        )
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "Margin warning",
        "text": (
            "Gross fee revenue is not net revenue. Payment-partner charges for collection and "
            "for payout are **unknown** and must be obtained in writing from ProvidusUnity "
            "before the fee is publicised. At 2% gross, a 1% collection charge plus per-payout "
            "fees could consume most or all of the margin. This must be modelled before the fee "
            "is communicated to members, because the fee cannot be raised later without "
            "renegotiating trust that took a year to build."
        )
    },
    {
        "t": "callout",
        "kind": "LEGAL",
        "title": "Regulatory status",
        "text": (
            "This document does not assert that AJO.ng is licensed, approved, exempt or "
            "compliant with any Nigerian financial regulator, statute or guideline. The "
            "licensing path depends on open decision D-02 (whether ProvidusUnity holds funds "
            "as principal or whether AJO.ng must hold them). That question must be resolved by "
            "qualified Nigerian counsel before any customer funds are accepted. Nothing in "
            "this PRD may be read as legal advice."
        )
    },

    # ------------------------------------------------------------------ 1.2
    {"t": "h2", "text": "1.2 Product vision"},
    {
        "t": "p",
        "text": (
            "**Ten years from now, the Nigerian Ajo will be run on infrastructure.** The "
            "rotating savings group will no longer be defined by who happens to know whom in "
            "one market, one office or one family compound. It will be defined by an "
            "invitation, a schedule, a ledger and a promise that is enforced by software. The "
            "notebook will survive only as a cultural object, the way the passbook survived "
            "the mobile money account."
        )
    },
    {"t": "h3", "text": "1.2.1 Vision statement"},
    {
        "t": "p",
        "text": (
            "To make the rotating savings group a first-class financial instrument — as safe "
            "to run with a stranger you have met once as with a cousin you have known for "
            "twenty years — by giving every Nigerian Ajo a shared, verifiable, tamper-evident "
            "record and by making the platform's obligations smaller and clearer than the "
            "platform's ambitions."
        )
    },
    {"t": "h3", "text": "1.2.2 The three futures the vision commits to"},
    {
        "t": "table",
        "head": ["Horizon", "What is true if the vision is realised"],
        "rows": [
            [
                "Near term",
                "An organiser in a Lagos market runs three Ajos from a phone. All three are "
                "activated, all positions are locked, all contributions are landing, and the "
                "notebook is in a drawer. The organiser is no longer the single point of "
                "failure.",
            ],
            [
                "Medium term",
                "Ajo is no longer a purely local practice. A member in Abuja, a member in "
                "Ibadan and a member in London can run the same Ajo on the same terms, with "
                "the same receipt, the same schedule and the same recourse. Diaspora "
                "participation becomes ordinary rather than a special accommodation.",
            ],
            [
                "Long term",
                "The Ajo becomes a genuine on-ramp to formal savings behaviour: regular "
                "payment discipline, a visible transaction history, a record that helps a "
                "member qualify for ordinary credit later. The Ajo becomes the first financial "
                "product a person ever keeps, rather than the one they hide.",
            ],
        ],
        "widths": [1.0, 5.5],
    },
    {"t": "h3", "text": "1.2.3 Vision boundaries"},
    {
        "t": "p",
        "text": (
            "The vision is about **trustworthy record-keeping and reliable money movement "
            "inside a savings group**. It is deliberately not a vision of AJO.ng becoming a "
            "lender, a bank, an insurer, an investment platform or a marketplace. Every "
            "product decision in section 1.16 is a consequence of that boundary."
        )
    },

    # ------------------------------------------------------------------ 1.3
    {"t": "h2", "text": "1.3 Product mission"},
    {
        "t": "p",
        "text": (
            "Our mission is to remove the failure modes of the traditional Ajo without "
            "removing the thing that makes it work. Concretely, for every AJO.ng group:"
        )
    },
    {
        "t": "numbers",
        "items": [
            "Make the record complete, shared and tamper-evident, so that the scheme survives "
            "the absence of any single member including the organiser.",
            "Make the commitment enforceable through process — locked positions, a 5-day "
            "enrollment window, a complete-cycle commitment — rather than through pressure, "
            "embarrassment or threat.",
            "Make every naira legible: what each member owes, what each member paid, what the "
            "pool contains, what the platform retains and what the recipient receives.",
            "Make the platform's obligations smaller than its promises, and publish them "
            "plainly before the member commits, not afterwards.",
            "Make it possible for a person who is not trusted yet to be *checked* rather than "
            "trusted blindly — which is the only honest way to widen access.",
        ],
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Mission test",
        "text": (
            "If a proposed feature would make the Ajo feel more trustworthy by making people "
            "compete, expose or be shamed, it is out of scope. If it makes the Ajo more "
            "legible, more recoverable or more available to a member who is absent or "
            "distressed, it is in scope. This test is applied to every feature request."
        )
    },

    # ------------------------------------------------------------------ 1.4
    {"t": "h2", "text": "1.4 Problem statement"},
    {"t": "h3", "text": "1.4.1 The structural problem"},
    {
        "t": "p",
        "text": (
            "The traditional Ajo concentrates four critical functions in one unpaid person: "
            "**collection, recording, adjudication and custody.** That person is the scheme's "
            "greatest strength when the group is small and everyone knows each other. It is "
            "also the scheme's only point of failure, and the concentration is total."
        )
    },
    {
        "t": "table",
        "head": ["Function", "Who performs it today", "What happens if they stop"],
        "rows": [
            [
                "Collection",
                "The organiser, on market day, in cash",
                "The round does not collect. There is no substitute cashier and no way to "
                "collect without the organiser present.",
            ],
            [
                "Recording",
                "One paper notebook, or a WhatsApp group message",
                "Every member's personal record is lost. The group falls back to memory, and "
                "memory is not evidence.",
            ],
            [
                "Adjudication",
                "The organiser, informally, from memory",
                "Disputes become opinion versus opinion. There is no neutral record to point "
                "at, so the loudest member usually wins.",
            ],
            [
                "Custody",
                "The organiser, in cash or a personal account",
                "If the money is gone, it is gone. There is no segregation, no statement, no "
                "counterparty statement to reconcile against.",
            ],
        ],
        "widths": [1.15, 2.15, 3.2],
    },
    {"t": "h3", "text": "1.4.2 The problems that are NOT the problem"},
    {
        "t": "p",
        "text": (
            "Stating this plainly matters, because a product that attacks these would be "
            "building on a false premise:"
        )
    },
    {
        "t": "table",
        "head": ["Common claim", "AJO.ng's position"],
        "rows": [
            [
                "Nigerians do not save",
                "False. Nigerians save heavily and consistently, in groups, every week, in "
                "cash. The Ajo is a savings product with near-perfect retention. The problem "
                "is record-keeping, not the saving instinct.",
            ],
            [
                "Nigerians do not trust technology",
                "False. Mobile money is used more widely than bank accounts. Members are "
                "willing to trust a system. They are unwilling to trust a system they cannot "
                "inspect — which is a design requirement, not a barrier.",
            ],
            [
                "The Ajo is a poverty product",
                "Misleading. Ajos are used by traders, professionals, students, market women "
                "and diaspora families. Many participants could easily save alone and choose "
                "not to, because the social commitment is the product.",
            ],
            [
                "Organisers are dishonest",
                "Mostly false. Organisers are usually honest under observation. The scheme "
                "fails when an honest person is absent, unavailable or unreachable, and there "
                "is no process that survives their absence.",
            ],
        ],
        "widths": [1.9, 4.6],
    },
    {"t": "h3", "text": "1.4.3 The failure we are actually building against"},
    {
        "t": "p",
        "text": (
            "The dominant failure is **organiser unavailability**, not organiser dishonesty. "
            "The organiser travels, falls ill, loses interest, changes business, is bereaved, "
            "or simply stops answering the group. The Ajo does not fail loudly. It fails by "
            "not being discussed again. Weeks pass. The notebook is lost. Nobody can say who "
            "paid what, so the remaining members disperse, and each takes a small silent loss."
        )
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Why this matters commercially",
        "text": (
            "Silent failure is the worst possible failure for a savings product, because "
            "nobody complains and nobody returns. AJO.ng's ability to detect a stalled Ajo and "
            "to surface it to members and to support is therefore a retention feature, not a "
            "nice-to-have."
        )
    },
    {"t": "h3", "text": "1.4.4 Problem statement, one sentence"},
    {
        "t": "p",
        "text": (
            "Nigerians run rotating savings groups in the hundreds of thousands and have "
            "done so for generations, but the record of who paid, who is owed what, and who "
            "holds the pot lives in one person's notebook and one person's memory — so a "
            "single absence, error or dispute can end a scheme that members have already "
            "committed months of savings to, with no recourse and no evidence."
        )
    },

    # ------------------------------------------------------------------ 1.5
    {"t": "h2", "text": "1.5 The traditional Ajo process"},
    {
        "t": "p",
        "text": (
            "This subsection describes how a real Lagos market Ajo operates today. It is "
            "written from observation of the practice, not from a design preference, and it "
            "is the baseline against which every AJO.ng requirement in this document is "
            "justified."
        )
    },
    {"t": "h3", "text": "1.5.1 Step-by-step: how it actually works"},
    {
        "t": "table",
        "head": ["Step", "What happens", "What is recorded, and where"],
        "rows": [
            [
                "1. Formation",
                "A trader or market leader needs working capital for stock. They propose an "
                "Ajo to people they already know: relatives, fellow traders, market "
                "neighbours, an association or a work cohort. Usually verbal.",
                "Nothing. Possibly a WhatsApp message announcing it. No terms document exists.",
            ],
            [
                "2. Terms agreed",
                "Members agree out loud on the number of people, the contribution amount, "
                "the collection day, the payout order and the duration. The organiser "
                "repeats it. Everyone nods.",
                "A list of names, in the organiser's handwriting, often with the amount "
                "beside each name, in the same notebook used for everything else.",
            ],
            [
                "3. Position order set",
                "The order in which the pot is paid out is agreed verbally — often by "
                "seniority, sometimes by luck, sometimes by whoever needs it most urgently. "
                "It is not usually written down as an *order*.",
                "A rough list in the notebook. Frequently the *only* record of whose turn it "
                "is, and the first thing lost or disputed.",
            ],
            [
                "4. Weekly collection",
                "On the agreed market day, the organiser goes round physically. Each member "
                "hands over cash. For members who cannot attend, the money is often sent by "
                "transfer to the organiser's personal account.",
                "A tick or a figure next to the member's name. Sometimes a WhatsApp message "
                "in the group: *Madu, paid. Okoye, not yet.* Sometimes a transfer receipt "
                "screenshotted into the chat and then scrolled away.",
            ],
            [
                "5. Counting and banking",
                "The organiser counts the cash, usually in a back room or a car, then keeps it "
                "— sometimes in a drawer, sometimes in a pouch, sometimes deposited into a "
                "personal account.",
                "The notebook shows the total. The pot is not held in any account that belongs "
                "to the Ajo, and no statement is ever produced.",
            ],
            [
                "6. Payout on the turn",
                "When a member's turn arrives, the pot is handed over. Often in cash at the "
                "market in front of witnesses. Increasingly by bank transfer, sometimes to a "
                "different bank than the one used to collect.",
                "A line in the notebook, sometimes a photograph of the cash, sometimes "
                "nothing at all. The member usually has no receipt.",
            ],
            [
                "7. Next round",
                "The cycle repeats. The notebook is carried forward. The only formal marker "
                "of progress is a calendar and the organiser's memory.",
                "Cumulative totals in the notebook, rarely added up correctly, rarely checked "
                "by anyone but the organiser.",
            ],
            [
                "8. Close or dissolution",
                "After the last member has been paid, the Ajo is simply over. There is no "
                "closing statement, no confirmation, no archive, no record that this group "
                "ever ran.",
                "Nothing. The notebook is put in a drawer, reused for something else, or "
                "thrown away.",
            ],
        ],
        "widths": [1.15, 2.7, 2.65],
        "size": 8.2,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Note on scale in this example",
        "text": (
            "The worked example below uses a NGN 10,000.00 monthly contribution because that "
            "is realistic for a market-based Ajo. The canonical fee worked example used "
            "elsewhere in this specification uses NGN 1,000.00 contributions (10 members, 10 "
            "rounds, base pool NGN 10,000.00). The two examples are deliberately different "
            "scales and must not be conflated."
        )
    },
    {"t": "h3", "text": "1.5.2 Worked example — 10 members, NGN 10,000.00, Friday"},
    {
        "t": "p",
        "text": (
            "Ten market traders form an Ajo in Lagos. Each contributes NGN 10,000.00 per "
            "month. Collection happens every **Friday**, the market day, split into four "
            "weekly collections of NGN 2,500.00 each. The pot is NGN 100,000.00 per month, "
            "handed in full to one member per month, in the agreed order, for ten months."
        )
    },
    {
        "t": "table",
        "head": ["Item", "Value"],
        "rows": [
            ["Members", "10"],
            ["Contribution per member per month", "NGN 10,000.00"],
            ["Collection day", "Friday (market day)"],
            ["Collections per month", "4"],
            ["Amount collected per member per Friday", "NGN 2,500.00"],
            ["Total collected per member per month", "NGN 10,000.00"],
            ["Pot paid out each month", "NGN 100,000.00"],
            ["Rounds (one payout per member)", "10"],
            ["Duration of the Ajo", "10 months"],
            ["Total paid in by one member across the Ajo", "NGN 100,000.00"],
            ["Total received by one member at their turn", "NGN 100,000.00"],
            ["Total circulated by the Ajo", "NGN 1,000,000.00"],
            ["Platform fee (there is no platform)", "NGN 0.00"],
            ["Interest or yield (none is offered or implied)", "NGN 0.00"],
            ["Records kept", "One paper notebook, held by the organiser"],
            ["Receipts given to members", "None, in the large majority of cases"],
            ["Time the organiser spends per Friday", "Approximately 2 to 3 hours"],
        ],
        "widths": [3.5, 3.0],
    },
    {
        "t": "p",
        "text": (
            "Note what the member actually buys with that two or three hours: the member pays "
            "NGN 10,000.00 and receives NGN 10,000.00. The return is **exactly zero in cash "
            "terms**. The entire value of the Ajo is the enforcement of the schedule and the "
            "social commitment. This is the single most important insight for product design: "
            "AJO.ng is not competing with a bank on yield, and any suggestion that it pays a "
            "return would be both false and dangerous."
        )
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "Zero cash return",
        "text": (
            "An Ajo pays no interest. A member who joins a 10-member Ajo at NGN 10,000.00 per "
            "month pays NGN 100,000.00 in total and receives NGN 100,000.00. Marketing "
            "material must never imply, allow or invite the inference that AJO.ng generates a "
            "return, an investment, or a financial gain. The product sold is **forced "
            "savings discipline plus accountability**, and nothing else."
        )
    },
    {"t": "h3", "text": "1.5.3 What the organiser's Friday actually looks like"},
    {
        "t": "code",
        "text": """
MARKET DAY - FRIDAY                      THE POT
----------------------------------------   --------------------
  07:20  Arrive early, open the stall        Target: NGN 100,000.00
  08:00  Begin walking the row               Notebook: one, yours
  08:40  Remind Chidi (still owes)           ...
  09:15  Collect from 6 members
          = NGN 15,000.00
  11:30  Count it in the back room
          = NGN 22,500.00 for today
  12:00  Send "paid update" in the group
  16:00  Carry NGN 22,500.00 home
          in a bag, in a bus, in traffic

  Zero of this is written by software.
  All of it is written by you, by hand.
  None of it can be checked by anybody else.
""",
    },

    # ------------------------------------------------------------------ 1.6
    {"t": "h2", "text": "1.6 Problems with the traditional Ajo"},
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Read this first",
        "text": (
            "**The social trust in a traditional Ajo is a strength, not only a weakness.** It "
            "is why NGN 1,000,000.00 can move through ten people who have never signed "
            "anything, in a country where formal credit is expensive and largely unavailable. "
            "Any product that replaces trust with surveillance will be worse, not better. "
            "AJO.ng's job is to keep the trust and remove the paper. The problems below are "
            "listed honestly, and the strengths are listed just as honestly."
        )
    },
    {"t": "h3", "text": "1.6.1 The genuine strengths of the traditional Ajo"},
    {
        "t": "table",
        "head": ["Strength", "Why it matters", "How AJO.ng preserves it"],
        "rows": [
            [
                "Social enforcement",
                "The strongest enforcement mechanism in low-cost finance is a person who will "
                "be embarrassed in front of you. It works at no cost and needs no software.",
                "Preserved. Defaulting is handled privately between the member, the "
                "organiser and platform risk. AJO.ng never publicly shames or exposes a "
                "defaulting member.",
            ],
            [
                "Known counterparty",
                "Members join because they know and trust the organiser. That trust is the "
                "product's distribution channel and its acquisition cost of zero.",
                "Preserved and extended. MVP is private and invitation-only. Ajo.ng Ajos are "
                "invitation-only in launch, so the group is always somebody's group.",
            ],
            [
                "Zero onboarding cost",
                "A new member can join in under two minutes at the market, with no documents, "
                "no forms and no account.",
                "Improved, not replaced. Joining requires registration, but the flow is "
                "designed so that an invited member can be paying within a few minutes.",
            ],
            [
                "Physical immediacy",
                "Cash handed over face to face, in the same minute, cannot be forgotten or "
                "reversed later.",
                "Replicated digitally through immediate receipts, idempotent payments and a "
                "confirming webhook within seconds of provider settlement.",
            ],
            [
                "No paperwork, no literacy barrier",
                "The scheme runs in a language the participants actually speak, with no forms "
                "to read.",
                "Replicated. Onboarding supports voice-first notification, low-bandwidth "
                "flows, and no English-literacy requirement for core tasks.",
            ],
            [
                "Fits irregular income",
                "Small daily or weekly amounts, no minimum balance, no application. It works "
                "for a trader whose income arrives in irregular lumps.",
                "Replicated. Contributions are small and frequent by design; there is no "
                "minimum balance and no application burden.",
            ],
        ],
        "widths": [1.3, 2.5, 2.7],
        "size": 8.2,
    },
    {"t": "h3", "text": "1.6.2 The real problems"},
    {
        "t": "table",
        "head": ["#", "Problem", "What it looks like in practice", "Severity"],
        "rows": [
            [
                "P1",
                "Records live in WhatsApp and notebooks",
                "The authoritative record is a paper exercise book, a set of voice notes, and a "
                "WhatsApp group where *paid* and *not paid* are asserted by the organiser. "
                "Scroll-back is not an audit trail. A message can be deleted. There is no "
                "second copy and no timestamp that survives a screenshot.",
                "Critical",
            ],
            [
                "P2",
                "No enforcement beyond memory and pressure",
                "The only consequences for not paying are a phone call and a public naming in "
                "a group chat. There is no defined due date, no grace period, no default "
                "state, no consequence schedule and no record that any of it happened. The "
                "same member can be overdue for six months because nobody had a rule to "
                "apply.",
                "Critical",
            ],
            [
                "P3",
                "The organiser disappears",
                "Illness, travel, bereavement, business loss, a new job, or simply losing "
                "interest. The notebook is personal. The cash is personal. There is no "
                "succession, no deputy, no escrow, no way for the other nine members to "
                "continue without the tenth. The Ajo ends silently and no one is told.",
                "Critical",
            ],
            [
                "P4",
                "No receipts",
                "Most members never receive a receipt for a single naira they paid in or "
                "received. The contributor cannot prove they paid. The recipient cannot prove "
                "they were paid the full pot. Neither can produce anything to a bank, an "
                "employer, a family member or a court.",
                "Critical",
            ],
            [
                "P5",
                "Disputes are unresolvable",
                "If a member claims they paid and the organiser says they did not, the only "
                "evidence is two memories. The strongest argument wins. There is no "
                "timestamped record, no bank statement, no third-party copy. A dispute about "
                "money with no evidence is a coin toss, and the loser usually leaves the group "
                "rather than escalate.",
                "Critical",
            ],
            [
                "P6",
                "No audit trail and no accountability",
                "There is no way to establish, after the fact, what the Ajo was supposed to "
                "do, what it actually did, who authorised anything, or how much money passed "
                "through. If a dispute ever needed to be settled by a third party, the Ajo "
                "has nothing to offer.",
                "High",
            ],
            [
                "P7",
                "The organiser is an unguarded guarantor",
                "In practice the organiser is treated as personally liable for the pot, "
                "whether or not anyone said so. The group believes their money is safe because "
                "the organiser is known. If the organiser cannot cover a shortfall, the "
                "members' belief is simply wrong and they find out on payday.",
                "High",
            ],
            [
                "P8",
                "Cash handling risk",
                "Large sums in cash, carried on public transport, counted in a back room, "
                "stored in a home. Robbery, loss and theft are real and uninsurable in "
                "practice. Transferring to a personal account instead mixes Ajo money with "
                "personal money and makes reconciliation impossible.",
                "High",
            ],
            [
                "P9",
                "No way to check on the scheme without asking the organiser",
                "A member who has been away for two months has no way to see what they owe, "
                "what they paid, when their turn is or what the pot contains. They must ask "
                "the organiser, which means their information is only as good as the "
                "organiser's day.",
                "High",
            ],
            [
                "P10",
                "Frequency limits participation",
                "Ajo is a weekly or monthly commitment. Someone whose income is lumpy, or who "
                "travels for work, or who is paid quarterly, cannot participate in a scheme "
                "that demands a fixed Friday. The group loses good members and the potential "
                "demands of better-off members.",
                "Medium",
            ],
            [
                "P11",
                "It does not scale past the personal network",
                "An Ajo cannot exceed the organiser's phone book. A trader who wants to run "
                "three Ajos with thirty people must maintain three notebooks and three sets "
                "of records, and is strongly discouraged from delegating any of it.",
                "Medium",
            ],
            [
                "P12",
                "No record of the Ajo after it ends",
                "Nothing is archived. The member has no statement, no total paid, no total "
                "received, no completion certificate. The entire financial history of the "
                "scheme is a piece of paper in a drawer that is eventually thrown away.",
                "Medium",
            ],
        ],
        "widths": [0.4, 1.6, 3.85, 0.7],
        "size": 8.0,
    },
    {"t": "h3", "text": "1.6.3 Why these problems are worth software"},
    {
        "t": "p",
        "text": (
            "Problems P1 through P6 are all the same problem seen from six angles: **the "
            "record does not exist in a form that can survive its creator.** AJO.ng's entire "
            "MVP is an answer to that one sentence. Problems P7 and P8 are answered by "
            "changing the money path, not the record. Problems P10 to P12 are growth "
            "constraints rather than correctness problems, and are addressed by schedule "
            "flexibility, scale and archiving respectively."
        )
    },

    # ------------------------------------------------------------------ 1.7
    {"t": "h2", "text": "1.7 Proposed digital solution"},
    {
        "t": "p",
        "text": (
            "AJO.ng is a private, invitation-only platform on which a group runs the same Ajo "
            "it runs today, with the ledger, the receipts, the schedule and the enforcement "
            "handled by software. The organiser keeps the social role. The software keeps the "
            "books."
        )
    },
    {"t": "h3", "text": "1.7.1 The AJO.ng model, end to end"},
    {
        "t": "code",
        "text": """
  ORGANISER                AJO.ng                MEMBER
  ---------                ------                ------
  Create the Ajo   ---->  Positions defined
  Set amount,              Enrollment opens
  frequency, order  ---->  5-day window runs
                                 |
  Invite people    ---->  Invitations issued
                                 |
                        Members join  <----  Accept invite,
                                 |           see full terms
                        Activation
                        POSITIONS LOCK
                                 |
                        Round 1 opens
                                 |
  Remind, nudge    ---->  Member pays ---->  Charged
                                     |        NGN 1,020.00
                                     |          = NGN 1,000.00
                                     |            + NGN 20.00 fee
                                     v
                        Fee recorded as
                        fees_income
                                     |
                        Pool reaches
                        base pool
                                     |
  Request release  ---->  Payout released ---> Recipient gets
                                     |          NGN 10,000.00
                                     |          (base pool only)
                        Round closes
                        Next position
""",
    },
    {"t": "h3", "text": "1.7.2 The five design decisions that define the product"},
    {
        "t": "table",
        "head": ["Decision", "What it means", "Why"],
        "rows": [
            [
                "Invitation-only at launch",
                "An Ajo can only be created and joined by people the organiser has invited. "
                "There is no public directory, no searchable marketplace and no open "
                "browsing.",
                "It preserves the one thing that makes the traditional Ajo work — a known "
                "group — while adding the record. Opening to strangers is a post-MVP decision "
                "with a different risk profile.",
            ],
            [
                "Money is not the organiser's",
                "Contributions are collected by the payment provider into the approved "
                "financial arrangement, not into the organiser's personal account, drawer or "
                "pouch.",
                "Removes P7 and P8 at once. The organiser can no longer be a custodian, so "
                "the organiser can no longer be a single point of failure.",
            ],
            [
                "Positions lock on activation",
                "The payout order is fixed when the Ajo becomes ACTIVE. Reordering afterwards "
                "requires a formal replacement or transfer request, not a phone call.",
                "Ajo.ng's promise is that a member's turn is a fact, not a favour. Locking is "
                "what makes the promise checkable.",
            ],
            [
                "The fee is added, never taken",
                "A member owing NGN 1,000.00 is charged NGN 1,020.00. The contribution of "
                "NGN 1,000.00 goes to the pool. The NGN 20.00 is recorded as fees_income. "
                "The recipient receives NGN 10,000.00.",
                "If the fee were deducted from the pool, members would discover at payout "
                "that the pot was smaller than promised. That single design choice would "
                "destroy more trust than any competitor could win.",
            ],
            [
                "No unilateral exit after activation",
                "A member who needs to leave must request a replacement and a re-ordering, and "
                "the commitment to the complete cycle is explicit at join time.",
                "Without it, Ajo.ng reproduces the exact failure it was built to remove: the "
                "quiet departure that strands the remaining members.",
            ],
        ],
        "widths": [1.35, 2.55, 2.6],
        "size": 8.2,
    },
    {"t": "h3", "text": "1.7.3 The complete-cycle commitment, stated plainly"},
    {
        "t": "p",
        "text": (
            "Joining an Ajo after activation is a commitment to pay every remaining round "
            "until the Ajo completes, or until a formal replacement is accepted. This is "
            "stated in plain language on the join confirmation screen, in the invitation, and "
            "in the terms. The member acknowledges it explicitly. It is the digital equivalent "
            "of the thing the group already says to itself on day one — that you are in for "
            "the whole cycle, not just your turn."
        )
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Open decision — replacement mechanics",
        "text": (
            "The exact replacement mechanism (a queue of approved replacements, a per-Ajo "
            "waitlist, or an organizer-nominated substitute) is specified at product level in "
            "section 1.17 and in the state-machine section, but the commercial question of "
            "**whether a replacement candidate pays a premium, and how that premium is "
            "handled**, is not yet decided. Owner: Founders. This must be settled before "
            "launch because it is a money-in question and money-in questions cannot be "
            "ambiguous."
        )
    },
    {"t": "h3", "text": "1.7.4 How AJO.ng differs from a WhatsApp group"},
    {
        "t": "table",
        "head": ["Dimension", "WhatsApp group", "AJO.ng"],
        "rows": [
            [
                "Record",
                "Mutable, deletable, scrolled away, asserted by one person",
                "Append-only ledger, versioned, no role can edit or delete",
            ],
            [
                "Identity",
                "A display name and a phone number, easily borrowed",
                "Verified account with optional BVN or CAC verification, one identity to one "
                "account",
            ],
            [
                "Money",
                "Manual transfers to a personal account, unreconciled",
                "Provider-collected, provider-receipted, reconciled daily by automation",
            ],
            [
                "Schedule",
                "Remembered, restated, drifting",
                "Generated schedule, locked at activation, visible to every member",
            ],
            [
                "Enforcement",
                "Social pressure, applied unevenly and inconsistently",
                "Documented default sequence with grace, private handling and recovery",
            ],
            [
                "Dispute",
                "Argument, decided by whoever argues better or louder",
                "Evidence thread against a timestamped record, escalated to a role that "
                "cannot move money",
            ],
            [
                "After the fact",
                "No record survives",
                "Statements, receipts and audit logs are retained and exportable",
            ],
        ],
        "widths": [0.95, 2.35, 3.2],
        "size": 8.2,
    },

    # ------------------------------------------------------------------ 1.8
    {"t": "h2", "text": "1.8 Product goals"},
    {
        "t": "p",
        "text": (
            "Product goals are what the product must *be*. Business objectives (section 1.9) "
            "are what the company must *achieve*. Where they conflict, this table is the "
            "tie-breaker in favour of the product goal, because a business objective "
            "achieved by breaking a product goal is not an objective achieved."
        )
    },
    {
        "t": "table",
        "head": ["ID", "Product goal", "Why it matters", "Measured by"],
        "rows": [
            [
                "G1",
                "Make the Ajo survive the loss of any single member",
                "The traditional Ajo's only point of failure is the organiser. Removing that "
                "dependency is the core of the product's value.",
                "Percentage of Ajos that continue correctly after an organiser becomes "
                "unavailable for 14 days",
            ],
            [
                "G2",
                "Give every member a complete, self-service view of their own position",
                "A member should never need to ask the organiser to know what they owe, what "
                "they paid, or when their turn is.",
                "Share of contribution views served without contacting the organiser",
            ],
            [
                "G3",
                "Make the fee completely transparent before commitment",
                "The single most likely cause of a trust-ending discovery is a fee the member "
                "did not know about.",
                "Fee disclosure present and acknowledged on 100% of invitations, join "
                "confirmations and receipts",
            ],
            [
                "G4",
                "Never release a payout the funds cannot cover",
                "The failure that ends a product is a failed payout. Holding a round is "
                "extremely bad; under-paying one is fatal and irreversible.",
                "Zero under-funded or short-paid payouts in the lifetime of the platform",
            ],
            [
                "G5",
                "Keep default handling private and process-driven",
                "Public shaming destroys the social mechanism the product depends on, and it "
                "is also simply cruel.",
                "Zero public exposure of defaulting members; 100% of defaults handled through "
                "the documented sequence",
            ],
            [
                "G6",
                "Keep the ledger beyond the reach of every role",
                "If any role can amend financial history, no other requirement in this document "
                "is worth anything.",
                "Zero edits or deletes to ledger tables; corrections only by reversing entry",
            ],
            [
                "G7",
                "Be usable on a low-end Android phone on a poor connection",
                "This is the actual device and network the target users have. Designing for "
                "the flagship phone would design for nobody.",
                "Core flows (join, pay, view) completed on the lowest supported device class "
                "over 3G",
            ],
            [
                "G8",
                "Never imply a return on savings",
                "An Ajo pays zero interest. Any suggestion otherwise is misleading and "
                "dangerous.",
                "Zero marketing or product copy implying yield, interest, investment or "
                "financial gain",
            ],
            [
                "G9",
                "Make the organiser's job take minutes, not hours",
                "The organiser is unpaid. If AJO.ng adds work, organisers will leave.",
                "Median organiser time per round on AJO.ng, compared with the traditional "
                "2 to 3 hours per Friday",
            ],
            [
                "G10",
                "Make a completed Ajo produce a lasting record",
                "A member who has kept every receipt and every statement has acquired a "
                "financial history, which is itself the retention hook.",
                "Percentage of completed Ajos with a full, exportable member statement",
            ],
        ],
        "widths": [0.35, 1.85, 2.55, 1.75],
        "size": 8.0,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Explicitly not a goal",
        "text": (
            "Maximising transaction volume is **not** a product goal. Volume at the expense of "
            "a funded payout, a legible record or a private default is a negative outcome. "
            "Volume is a business measure, listed in section 1.9."
        )
    },

    # ------------------------------------------------------------------ 1.9
    {"t": "h2", "text": "1.9 Business objectives"},
    {
        "t": "p",
        "text": (
            "AJO.ng's revenue model is locked: a **2% platform fee on every contribution "
            "deposit**. This supersedes the earlier *fee model not locked* note in the "
            "existing Year-1 financial model documents, which must be reissued."
        )
    },
    {"t": "h3", "text": "1.9.1 The 2% fee mechanic"},
    {
        "t": "table",
        "head": ["Element", "Definition"],
        "rows": [
            ["Fee rate", "2% of the contribution amount, charged in addition to it"],
            [
                "Computed as",
                "fee = (amount_kobo * 200 + 5000) / 10000, integer half-up rounding",
            ],
            ["Ledger account", "Fees are recorded as fees_income, separately from contributions"],
            [
                "Deducted from the contribution?",
                "**Never.** The contribution is never reduced to make room for the fee.",
            ],
            [
                "Deducted from the payout?",
                "**Never.** The payout the member was promised is exactly the base pool.",
            ],
            [
                "Who can change it?",
                "Configuration only, by a role that cannot edit the ledger. `risk_officer` "
                "**cannot** change fee configuration (see section 1.12).",
            ],
            [
                "Disclosure",
                "Shown separately from the contribution on every receipt, in every Ajo details "
                "screen, and in the invitation and join confirmation, before the member "
                "commits.",
            ],
        ],
        "widths": [1.55, 4.95],
    },
    {"t": "h3", "text": "1.9.2 Canonical worked example — must be quoted identically everywhere"},
    {
        "t": "table",
        "head": ["Item", "Value"],
        "rows": [
            ["Members", "10"],
            ["Contribution per member per round", "NGN 1,000.00"],
            ["Platform fee (2%)", "NGN 20.00"],
            ["Total charged per member", "NGN 1,020.00"],
            ["Base pool paid to recipient", "NGN 10,000.00"],
            ["Total collected in the round", "NGN 10,200.00"],
            ["Platform fee retained in the round", "NGN 200.00"],
            ["Rounds", "10"],
            ["Total paid in by one member", "NGN 10,200.00"],
            ["Total received by recipient at their turn", "NGN 10,000.00"],
            ["Platform fee over the full Ajo", "NGN 2,000.00"],
            ["Total collected across the Ajo", "NGN 102,000.00"],
        ],
        "widths": [3.5, 3.0],
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "The two numbers that must never be confused",
        "text": (
            "The recipient receives **NGN 10,000.00**. They do not receive NGN 10,200.00. The "
            "difference, NGN 200.00, is the platform's fee for that round and belongs to "
            "AJO.ng. Any interface, statement, receipt or marketing asset that shows the "
            "recipient receiving the collected total rather than the base pool is a "
            "misrepresentation of the product and a breach of the promise the fee model is "
            "built to protect."
        )
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "D-01 — resolved in this specification",
        "text": (
            "CANONICAL.md D-01 asked whether the recipient receives the base pool "
            "(NGN 10,000.00) or the full collected pool (NGN 10,200.00). **This "
            "specification assumes the base pool.** That assumption must be confirmed "
            "formally by the Founders and reflected in the terms, the interface and the "
            "marketing copy before launch. If it is ever changed, the change is a "
            "material change to the product promise and requires reissue of this document, "
            "the terms of service and all fee disclosures."
        )
    },
    {"t": "h3", "text": "1.9.3 Year-1 scenarios"},
    {
        "t": "p",
        "text": (
            "The three scenarios below are aligned to the existing financial model "
            "spreadsheet. They are **projections, not forecasts or commitments**, and no "
            "customer or transaction data exists to validate them. The model is a planning "
            "artefact whose purpose is to size the operation, not to promise investors."
        )
    },
    {
        "t": "table",
        "head": [
            "Scenario",
            "Ajos",
            "Members",
            "Contribution",
            "Rounds",
            "Deposits",
            "Volume",
            "Fee revenue at 2%",
            "Fee per Ajo",
        ],
        "rows": [
            [
                "Conservative",
                "150",
                "8",
                "NGN 7,500",
                "10",
                "12,000",
                "NGN 90,000,000",
                "NGN 1,800,000",
                "NGN 12,000",
            ],
            [
                "Base Case",
                "300",
                "10",
                "NGN 10,000",
                "10",
                "30,000",
                "NGN 300,000,000",
                "NGN 6,000,000",
                "NGN 20,000",
            ],
            [
                "Growth Case",
                "600",
                "12",
                "NGN 12,000",
                "10",
                "72,000",
                "NGN 864,000,000",
                "NGN 17,280,000",
                "NGN 28,800",
            ],
        ],
        "widths": [0.85, 0.5, 0.6, 0.85, 0.5, 0.7, 1.15, 0.85, 0.5],
        "size": 7.6,
    },
    {
        "t": "table",
        "head": ["Base-case derived measure", "Value"],
        "rows": [
            ["Core payment events", "33,000 (30,000 contributions + 3,000 payouts)"],
            ["Monthly average contribution volume", "NGN 25,000,000"],
            ["Monthly average fee revenue at 2%", "NGN 500,000"],
            ["Gross fee revenue over the year", "NGN 6,000,000"],
            [
                "Net revenue",
                "Unknown. Dependent on ProvidusUnity collection and payout charges, which are "
                "not yet known. See open decision D-03.",
            ],
        ],
        "widths": [2.6, 3.9],
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "Margin warning — must appear in all financial material",
        "text": (
            "Gross fee revenue is not net revenue. Payment-partner charges for collection and "
            "payout are **unknown and must be obtained in writing from ProvidusUnity**. At 2% "
            "gross, a 1% collection charge plus per-payout fees could consume most or all of "
            "the margin. This must be modelled before the fee is communicated to members, "
            "because the fee cannot be raised later without renegotiating trust."
        )
    },
    {"t": "h3", "text": "1.9.4 Business objectives"},
    {
        "t": "table",
        "head": ["ID", "Business objective", "Target (Year 1)", "Dependency"],
        "rows": [
            [
                "BO1",
                "Reach a self-sustaining set of Ajos across a small number of dense market "
                "clusters",
                "150 to 600 Ajos depending on scenario; 2 to 3 city clusters",
                "Organiser recruitment and local trust. This is a people problem, not a "
                "marketing problem.",
            ],
            [
                "BO2",
                "Generate gross fee revenue at the locked 2%",
                "NGN 1,800,000 to NGN 17,280,000 depending on scenario",
                "BO1 plus payment collection succeeding at the assumed rate.",
            ],
            [
                "BO3",
                "Establish positive net contribution margin per Ajo",
                "Positive by month 12 — **unverified, dependent on D-03**",
                "Written pricing from ProvidusUnity. This objective cannot be validated "
                "before that pricing exists.",
            ],
            [
                "BO4",
                "Achieve zero failed or under-funded payouts",
                "Zero, without exception",
                "The payout funding principle in BR-018. This is a constraint, not a target.",
            ],
            [
                "BO5",
                "Reach a default rate that does not strand Ajos",
                "Below 3% of contributions defaulted at 60 days — **projection**",
                "A stable member base and a functioning private recovery process.",
            ],
            [
                "BO6",
                "Prove the licence and custody path before scale",
                "Written legal opinion and written provider confirmation before the first live "
                "contribution",
                "D-02, D-03, D-04, D-06. **This gates launch, not growth.**",
            ],
            [
                "BO7",
                "Build a per-member financial history that retains members into a second Ajo",
                "At least 40% of completing members start or join a further Ajo within 90 days "
                "— **projection**",
                "Statements, receipts and a completion experience that feels like an "
                "achievement rather than an expiry.",
            ],
        ],
        "widths": [0.4, 1.9, 1.9, 2.3],
        "size": 8.0,
    },
    {
        "t": "callout",
        "kind": "LEGAL",
        "title": "Fee, tax and licensing treatment",
        "text": (
            "Whether the 2% fee is tax-inclusive, and who remits VAT or withholding tax, is "
            "open decision **D-06** and must be settled by a qualified Nigerian tax adviser. "
            "Whether AJO.ng's activities require a licence, a registration or an exemption is "
            "open decision **D-02** and must be settled by qualified Nigerian counsel. Nothing "
            "in this PRD states or implies that any such requirement has been met."
        )
    },

    # ----------------------------------------------------------------- 1.10
    {"t": "h2", "text": "1.10 Target users"},
    {
        "t": "table",
        "head": ["Segment", "Who", "Size and shape", "Why they are the target"],
        "rows": [
            [
                "Primary — market traders and micro-entrepreneurs",
                "Market women and men, shop owners, traders in markets such as Balogun, "
                "Oniru, Mile 2, Sabon Gari",
                "The historical heart of the Ajo. Already save weekly. Already have a group. "
                "Cash-heavy, mobile-first, low tolerance for paperwork.",
                "Highest willingness to switch for a receipt. Lowest need for a return. The "
                "fee of NGN 20.00 per NGN 1,000.00 is the smallest possible toll for the "
                "largest possible gain in control.",
            ],
            [
                "Primary — young urban professionals",
                "Ages roughly 24 to 35, employed, in Lagos, Abuja, Port Harcourt, Ibadan",
                "Join an Ajo that a parent or older relative runs. Want the record more than "
                "they want the pot. Comfortable with apps, disciplined with notifications.",
                "The segment most likely to complete a cycle, most likely to start a second "
                "Ajo, and most likely to bring a partner into a new one. They are the growth "
                "engine.",
            ],
            [
                "Primary — students and young adults",
                "Ages roughly 18 to 23, university and polytechnic, often with irregular "
                "income",
                "Small contributions, high sensitivity to the fee, need a fixed schedule they "
                "can meet around lectures and holidays.",
                "Cheapest to acquire, most price-sensitive, most likely to churn on the first "
                "missed payment. Their retention tests the grace-period design.",
            ],
            [
                "Secondary — small business owners",
                "Owner-operators with real cash flow, inventory to finance, and a need for a "
                "predictable lump sum",
                "Run Ajos themselves, sometimes several. Think in terms of working capital and "
                "inventory, not savings.",
                "Highest lifetime value and highest Ajo count per user. They are also the "
                "segment most likely to attempt to game position order, which is a design "
                "pressure that must be anticipated.",
            ],
            [
                "Secondary — diaspora members",
                "Nigerians living outside Nigeria who want to participate in a family Ajo and "
                "cannot be present on collection day",
                "Contribute remotely, in their own currency's worth, from abroad. Often the "
                "organiser of a family Ajo spread across two or three countries.",
                "Expands the total addressable market substantially and solves the single "
                "biggest structural complaint about traditional Ajos (P10). Also the "
                "segment with the highest per-member willingness to pay and the highest "
                "support cost.",
            ],
            [
                "Not targeted at launch",
                "Institutional and corporate scheme participants, government programmes, "
                "large associations, non-Nigerian users",
                "—",
                "None of the required controls, limits, legal analysis or support model exist "
                "for these segments at launch. They are out of scope, not merely unpromoted.",
            ],
        ],
        "widths": [1.25, 1.6, 1.85, 1.8],
        "size": 7.8,
    },
    {
        "t": "callout",
        "kind": "ASSUMPTION",
        "title": "Segment sizing",
        "text": (
            "The segment definitions above are a working segmentation derived from founder "
            "knowledge of the practice. They are **not** derived from a documented market "
            "study, and no third-party market sizing has been commissioned as at the date of "
            "this document. Validation path: primary research with 20 to 30 target users and "
            "5 to 10 organisers across 2 cities before the growth plan is committed. Owner: "
            "Founders."
        )
    },

    # ----------------------------------------------------------------- 1.11
    {"t": "h2", "text": "1.11 User personas"},
    {
        "t": "p",
        "text": (
            "Six personas. Five are the target segments from section 1.10. The sixth, Chidi, "
            "represents the largest and least-served group in every Ajo: the member who simply "
            "wants to pay and be left alone. Designing for him is what stops AJO.ng from "
            "becoming a job."
        )
    },

    {"t": "h3", "text": "1.11.1 Alhaji Musa — the market organiser"},
    {
        "t": "kv",
        "pairs": [
            ("Age / location", "47. Balogun Market, Lagos. Runs a provisions stall, employs two."),
            ("Context", "Has organised Ajos for eleven years, usually eight to twelve people, always from his own network. Runs two at the moment. Holds NGN 100,000.00 to NGN 200,000.00 of members' money at any time, in a bag."),
            ("Goals", "Stop being the cashier. Be sure the money he is responsible for is provably safe. Prove to members that he is honest without having to argue it. Retire from collecting without ending the Ajo."),
            ("Frustrations", "Loses the notebook constantly. Cannot answer 'who paid in round four' from memory. Fears a member claiming he never paid and having no way to settle it. Spends two to three hours every Friday. Felt embarrassed refusing to pay someone who was short."),
            ("Tech comfort", "Comfortable with WhatsApp, mobile money and a smartphone. Will not use a system that takes more than ten minutes to learn. Will not do data entry beyond his name and a number."),
            ("What success looks like", "He opens AJO.ng on a Friday, sees that round six is fully funded, presses one button, and closes the app. He can show any member a receipt at any time. He never touches cash."),
            ("Will not tolerate", "Being asked to verify balances manually. Being asked to chase members. Any wording that implies he is suspected of dishonesty. Any interface that makes him look like a clerk."),
        ],
    },
    {"t": "h3", "text": "1.11.2 Ada — the young professional"},
    {
        "t": "kv",
        "pairs": [
            ("Age / location", "29. Lekki, Lagos. Product manager, fintech employer, pays rent monthly."),
            ("Context", "Joined her mother's Ajo two years ago and now organises one herself with six colleagues. Comfortable with apps, uses three financial apps already, expects a good interface and will abandon a bad one without sentiment."),
            ("Goals", "Know her exact position at any moment. Get a proper statement at the end. See the fee clearly and not feel nickel-and-dimed. Eventually use the record to qualify for something better."),
            ("Frustrations", "Hates asking her mother whether she paid round three. Has no idea what the pot is currently worth. Finds the 2% fee annoying but tolerable if it is stated up front. Finds the invitation flow long."),
            ("Tech comfort", "High. Expects push notifications, dark mode, fast navigation, no surprises. Will read a receipt. Will compare AJO.ng against her other savings apps and expect it to be presentable."),
            ("What success looks like", "A dashboard that tells her, without being asked, what she owes next, when her turn is, and what she has received. A statement she would be willing to attach to a loan application."),
            ("Will not tolerate", "Hidden fees. A slow app. Being forced to call anyone. Losing her position because of a UI error."),
        ],
    },
    {"t": "h3", "text": "1.11.3 Tunde — the student"},
    {
        "t": "kv",
        "pairs": [
            ("Age / location", "21. Ibadan. Undergraduate, irregular income from odd jobs and family support."),
            ("Context", "Wants to be in an Ajo for the discipline but finds a fixed Friday hard. A missed payment would be genuinely stressful rather than merely embarrassing."),
            ("Goals", "Start small. Build the habit of paying regularly. Not lose face if he misses one. Understand exactly what he owes at any time without doing arithmetic."),
            ("Frustrations", "Fees feel large relative to NGN 500.00. Does not want to read terms. Wants SMS because push notifications get cleared. Worried about what happens if he is short one week."),
            ("Tech comfort", "Moderate. Heavy Android user, low-end device, limited data, uses SMS and WhatsApp far more than apps. Will delete an app he does not use weekly."),
            ("What success looks like", "An SMS on Thursday telling him what is due on Friday. A one-tap payment that works on a weak network. A clear statement that he did the right thing, not a lecture when he did not."),
            ("Will not tolerate", "Public exposure of a missed payment. A complicated sign-up. Being charged more than he expected."),
        ],
    },
    {"t": "h3", "text": "1.11.4 Bisi Okonkwo — the small business owner"},
    {
        "t": "kv",
        "pairs": [
            ("Age / location", "39. Aba, Rivers State. Runs aProvision and provisions store, plus a small bakery."),
            ("Context", "Uses the Ajo to finance inventory at specific points in her business year. Thinks in terms of cash flow timing, not savings. May run an Ajo among her staff and a second among her siblings."),
            ("Goals", "Predictable lump sums at predictable dates. Ability to hand an Ajo to a manager if she travels. Assurance that the money is in a system, not a handbag."),
            ("Frustrations", "Has lost money twice when an organiser moved abroad. Cannot get a record of the payments she made, which her accountant asked for. Worried about initiating a payout on a day she is not present."),
            ("Tech comfort", "High for her own business — she already uses a POS and a bank app. Time-poor. Delegates aggressively to staff, which creates an access-control problem AJO.ng must solve."),
            ("What success looks like", "A statement her accountant accepts. An ability to nominate a trusted deputy. Predictable payout dates she can plan stock purchases around."),
            ("Will not tolerate", "Having to be present. Needing to explain the Ajo to her accountant. Any ambiguity about who can trigger a payout."),
        ],
    },
    {"t": "h3", "text": "1.11.5 Kemi Adeyemi — the diaspora member"},
    {
        "t": "kv",
        "pairs": [
            ("Age / location", "35. Manchester, United Kingdom. Consultant, visits Nigeria twice a year."),
            ("Context", "Organises a family Ajo across Nigeria and the UK. Cannot be present on collection day in Lagos. Currently pays by transfer to a relative who then hands over cash, and cannot see anything."),
            ("Goals", "Pay her own contribution from abroad without an intermediary. See the Ajo's status without asking anyone. Know her turn is coming months in advance. Get a record that satisfies her bank and her family."),
            ("Frustrations", "Total opacity. A 2021 round where her money was collected and she never received confirmation. Being unable to prove she contributed. Not knowing whether the Ajo is still running."),
            ("Tech comfort", "High, but with genuine friction: international card and transfer fees, time-zone confusion, and a real fear about a site she has never heard of taking an international payment."),
            ("What success looks like", "A local-currency receipt she can store. A visible countdown to her turn. A statement in a format her UK bank will accept as evidence of source of funds."),
            ("Will not tolerate", "Unexplained currency conversion. Unclear refund terms if an Ajo cancels. Being asked to send money to a personal account again."),
        ],
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Diaspora participation and open decision D-02",
        "text": (
            "Kemi is in the persona set because her need is real and well evidenced, but "
            "**international participation is explicitly out of scope for MVP** (section "
            "1.16). Whether AJO.ng can accept funds from non-Nigerian residents at all, and "
            "under what arrangement, is unresolved and depends on D-02. Her persona exists to "
            "keep that requirement visible, not to imply it is solved."
        )
    },
    {"t": "h3", "text": "1.11.6 Chidi — the joiner, the silent majority"},
    {
        "t": "kv",
        "pairs": [
            ("Age / location", "33. Agege, Lagos. Works in a logistics company, lives with family."),
            ("Context", "One of ten members in an Ajo run by someone he respects. Has never organised anything. Pays his NGN 1,000.00 every Friday with his phone and thinks about it for roughly ten seconds."),
            ("Goals", "Pay on time without it becoming a task. Know his turn has not been moved. Be able to see his own position. Nothing else."),
            ("Frustrations", "Being sent nine notifications a week about an Ajo he is already handling correctly. Having to open an app to confirm what a message already said. Any attempt to make him an organiser."),
            ("Tech comfort", "Adequate. Uses mobile money daily, does not use budgeting apps, will not maintain a schedule. Notices good design, tolerates average design."),
            ("What success looks like", "Two notifications per round: one before, one after. A screen that answers 'what is my position' in one tap. Silence."),
            ("Will not tolerate", "Notification fatigue. Being upsold. Being treated as a potential organiser."),
        ],
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Design consequence",
        "text": (
            "Chidi outnumbers every other persona. He represents the majority of members in "
            "every Ajo. Any notification policy that treats him as an active user will cause "
            "the uninstall. This is why the notification catalogue in CANONICAL.md reserves "
            "SMS for money-critical and security events only, and why notification preferences "
            "are a first-class feature rather than a setting."
        )
    },

    # ----------------------------------------------------------------- 1.12
    {"t": "h2", "text": "1.12 User roles"},
    {
        "t": "p",
        "text": (
            "AJO.ng has **exactly six roles**, per CANONICAL.md. Roles are additive and "
            "explicitly granted; there is no implicit inheritance and no wildcard role. A user "
            "may hold several roles simultaneously, and a person may be `ajo_organizer` in one "
            "Ajo and an ordinary `user` in every other."
        )
    },
    {
        "t": "table",
        "head": ["Role", "Scope", "Can", "Cannot"],
        "rows": [
            [
                "`user`",
                "Own account",
                "Create Ajos, join Ajos, pay, view own records",
                "See others' Ajos, alter financial records",
            ],
            [
                "`ajo_organizer`",
                "One Ajo",
                "Invite or remove pre-activation members, send reminders, propose position "
                "order, request payout release",
                "Withdraw member funds, control payouts, change settled records, guarantee "
                "another member's debt, act after the Ajo completes",
            ],
            [
                "`ajo_member`",
                "One Ajo",
                "Pay contributions, see own commitment, raise a dispute, request replacement "
                "exit",
                "Change payout order post-activation, unilaterally exit after activation",
            ],
            [
                "`support`",
                "Platform",
                "Read all records, contact members, assist disputes",
                "Move money or alter financial records. **Cannot** initiate or moderate "
                "payouts, change balances, or override risk decisions",
            ],
            [
                "`risk_officer`",
                "Platform",
                "View risk events, place accounts or Ajos under review, freeze, approve or "
                "reject overrides, manage limits",
                "Delete records, edit the ledger, change fee configuration",
            ],
            [
                "`super_admin`",
                "Platform",
                "Manage roles, configure platform settings, emergency freeze",
                "Bypass the append-only ledger or delete financial history",
            ],
        ],
        "widths": [1.05, 0.9, 2.35, 2.2],
        "size": 8.0,
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "Hard rule — the ledger is outside every role",
        "text": (
            "**No role, including `super_admin`, may edit or delete a ledger entry.** "
            "Corrections are made only by posting a reversing entry. This single rule is what "
            "makes the audit trail meaningful, and it is enforced at the data layer, not at "
            "the application layer. Any implementation that permits a privileged UPDATE or "
            "DELETE against ledger tables is non-conforming, regardless of how the permission "
            "is described."
        )
    },
    {"t": "h3", "text": "1.12.1 Role design notes"},
    {
        "t": "table",
        "head": ["Principle", "How it is applied"],
        "rows": [
            [
                "Least privilege, enforced at the data layer",
                "A role's reach is enforced by database permissions, not by hiding buttons. "
                "Hiding a control is not an authorisation control.",
            ],
            [
                "Money-moving is separated from money-reading",
                "`support` can read everything and move nothing. This is deliberate: support "
                "is the most-exposed role to social pressure and to social engineering.",
            ],
            [
                "Risk cannot change the economics",
                "`risk_officer` can freeze and can limit, but cannot change the fee "
                "configuration. Risk decisions constrain activity; they do not define it.",
            ],
            [
                "Administration cannot rewrite history",
                "`super_admin` configures platform settings and manages role assignments. It "
                "cannot touch a ledger row. Configuration changes are themselves audited.",
            ],
            [
                "Ajo scope is enforced, not assumed",
                "`ajo_organizer` and `ajo_member` are scoped to one Ajo. Being an organiser "
                "grants nothing in any other Ajo, including ones the person is a member of.",
            ],
            [
                "Actions end with the scheme",
                "`ajo_organizer` cannot act after the Ajo reaches COMPLETED. Organiser "
                "authority is temporary by design and the expiry is enforced in the state "
                "machine.",
            ],
            [
                "No implicit elevation",
                "There is no inheritance between roles and no default-superuser. Every grant is "
                "an explicit, audited `role_assignments` record with a named granter.",
            ],
        ],
        "widths": [1.9, 4.6],
    },
    {"t": "h3", "text": "1.12.2 What the organiser is, and is not"},
    {
        "t": "p",
        "text": (
            "Because this is the most misunderstood role in the product, it is stated "
            "explicitly. The `ajo_organizer` is a **facilitator, not a custodian and not a "
            "guarantor.** The organiser does not hold member funds, does not authorise "
            "payouts, cannot guarantee another member's debt, and cannot be pursued for a "
            "shortfall. AJO.ng is explicit on this in the organiser onboarding, in the Ajo "
            "terms, and in the join confirmation shown to every member. If a member believes "
            "otherwise, the product has failed at communication, not at enforcement."
        )
    },
    {
        "t": "callout",
        "kind": "LEGAL",
        "title": "Organiser liability wording",
        "text": (
            "Any wording describing organiser responsibilities is drafted to be reviewed by "
            "qualified Nigerian counsel before launch. In particular, nothing in the product "
            "should be read as creating a guarantee, a fiduciary relationship, a partnership "
            "or an agency between AJO.ng, the organiser and the members, and the terms must "
            "say so clearly."
        )
    },

    # ----------------------------------------------------------------- 1.13
    {"t": "h2", "text": "1.13 User needs"},
    {
        "t": "table",
        "head": ["#", "Need", "Whose need", "Why it is not met today", "Requirement"],
        "rows": [
            ["N1", "Know exactly what I owe and when", "Member (Chidi, Tunde)", "Depends entirely on the organiser remembering or checking the notebook", "FR-CON-001 to FR-CON-004"],
            ["N2", "Know what the pot is worth right now", "Member, organiser", "Never stated; the pot is a physical pile of cash", "FR-POS-002"],
            ["N3", "Know when my turn is, and be certain it cannot move", "Member (Ada, Kemi)", "The order is verbal and is the first thing forgotten", "FR-AJO-009, FR-AJO-010"],
            ["N4", "Get a receipt for everything I pay and receive", "All members", "No receipt exists in the large majority of Ajos", "FR-PAY-007, FR-POUT-006"],
            ["N5", "Pay without arranging a physical meeting", "Kemi, Tunde, Bisi", "Requires being physically present or an intermediary", "FR-PAY-001, FR-PAY-002"],
            ["N6", "Be reminded before I am late, not after", "Member", "Reminders are ad hoc and inconsistent", "FR-NOTIF-002"],
            ["N7", "Get the pot on my turn, in full, on time", "Member", "Depends on everyone else paying and the organiser having cash", "FR-POUT-001, FR-POUT-003"],
            ["N8", "Resolve a disagreement about money with evidence", "Member, organiser", "Memory versus memory; the louder party wins", "FR-DISP-001 to FR-DISP-005"],
            ["N9", "Know what happens if I cannot pay this week, before it happens", "Member (Tunde)", "Nobody knows; there is no defined process", "FR-DEF-001, FR-DEF-002"],
            ["N10", "Collect the Ajo without collecting the money", "Organiser (Musa)", "Today the two are the same job", "FR-PAY-003, FR-MEM-004"],
            ["N11", "Prove to a third party what happened in my Ajo", "All members, Bisi", "No audit trail, no statement, no archive", "FR-TXN-003, FR-TXN-004"],
            ["N12", "Keep an Ajo running when I am not available", "Bisi, Kemi", "The Ajo ends when the organiser is absent", "FR-AJO-012, FR-MEM-007"],
            ["N13", "Leave an Ajo without stranding the people I leave behind", "Member", "People simply disappear, and others absorb the loss", "FR-MEM-006, FR-MEM-007"],
            ["N14", "See the fee clearly before I commit", "All members", "Non-existent today; this is the new product's own requirement", "FR-AJO-005, FR-INV-002, FR-JOIN-003"],
            ["N15", "Understand the Ajo without reading a contract", "Tunde, Chidi", "Terms are verbal and inconsistent between groups", "FR-JOIN-002, FR-AJO-004"],
            ["N16", "See a complete history of my own savings", "Ada, Bisi", "No record survives the notebook", "FR-TXN-001, FR-TXN-006"],
        ],
        "widths": [0.35, 1.65, 1.15, 1.75, 1.6],
        "size": 7.8,
    },

    # ----------------------------------------------------------------- 1.14
    {"t": "h2", "text": "1.14 User pain points"},
    {
        "t": "table",
        "head": ["#", "Pain point", "Who feels it", "Current workaround", "Cost of the pain"],
        "rows": [
            ["PP1", "I do not know if I paid", "Every member", "Asking the organiser, or scrolling back through WhatsApp", "Constant low-grade anxiety; members often pay twice or not at all"],
            ["PP2", "I do not know when my turn is", "Every member", "Asking, or assuming", "Members miss their own payout; the most damaging failure in an Ajo"],
            ["PP3", "The organiser is not answering", "Every member", "Waiting, phoning around, escalating in the group", "The Ajo stalls; members quietly give up and lose the round"],
            ["PP4", "Somebody claims they paid and the organiser says they did not", "Both parties", "Argument, pressure, sometimes splitting the difference", "Unresolvable; often ends with one member losing real money"],
            ["PP5", "I missed a payment and I do not know what happens now", "Tunde, Chidi", "Pay quietly twice next week, or disappear", "A single miss cascades; one default can strand a whole round"],
            ["PP6", "I have no receipt for anything", "Bisi, Kemi", "Photographing a paper note, keeping a mental record", "No proof for an accountant, a bank, a visa application or a dispute"],
            ["PP7", "I was short-paid and cannot prove it", "Member", "Nothing", "Irrecoverable loss"],
            ["PP8", "The organiser used the pot and I only found out later", "All members", "Nothing", "Total loss, and the end of trust in the entire group"],
            ["PP9", "I want to leave but I am scared of what that does to the others", "Member", "Simply stops paying, which is worse", "Silent default; exactly the behaviour the group resents most"],
            ["PP10", "I cannot see the Ajo unless I ask someone", "Ada, Kemi", "Weekly WhatsApp questions", "The group is a black box; nobody is in control"],
            ["PP11", "I have to be in Lagos to participate in a family Ajo", "Kemi", "Sending money to a relative", "Diaspora members are excluded or dependent on a third party"],
            ["PP12", "I do not know what the fee is until after I have paid", "Tunde", "None", "The discovery that ends trust; the reason AJO.ng discloses first"],
        ],
        "widths": [0.4, 1.7, 1.05, 1.75, 1.6],
        "size": 7.8,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The common root",
        "text": (
            "Eleven of these twelve pain points reduce to one sentence: **nobody can see the "
            "same truth.** When the record is shared, complete and immutable, PP1, PP2, PP4, "
            "PP6, PP7, PP10 and PP12 are not mitigated but eliminated. PP3, PP5, PP8 and PP9 "
            "are reduced by process rather than visibility, and are handled by the default "
            "sequence and the payout funding principle."
        )
    },

    # ----------------------------------------------------------------- 1.15
    {"t": "h2", "text": "1.15 Value proposition"},
    {"t": "h3", "text": "1.15.1 Positioning"},
    {
        "t": "p",
        "text": (
            "**Your Ajo. Your Story.** The Ajo you already trust, with a record that cannot "
            "be lost, a receipt for every naira, and a promise that is enforced by software "
            "instead of by your temper."
        )
    },
    {
        "t": "table",
        "head": ["For", "The value", "Proved by"],
        "rows": [
            [
                "The member",
                "Certainty. You know what you owe, what you have paid, when your turn is, and "
                "that nobody can quietly move it. You get a receipt for everything and a "
                "record you keep for life.",
                "Schedule, receipts, statements, locked positions",
            ],
            [
                "The organiser",
                "Time and cover. You stop handling cash, you stop being the only record, and "
                "you can point at a receipt instead of defending a memory.",
                "Provider collection, immutable ledger, one-button round closure",
            ],
            [
                "The family or group",
                "Continuity. The Ajo survives illness, travel, bereavement and change. It no "
                "longer depends on one person being available on one day.",
                "Role separation, escrow arrangement, succession design",
            ],
            [
                "AJO.ng",
                "A fee that scales with real savings activity, earned by making a previously "
                "informal financial habit legible, without taking any cut of the pot.",
                "2% on every contribution deposit",
            ],
        ],
        "widths": [1.05, 3.45, 2.0],
    },
    {"t": "h3", "text": "1.15.2 The three claims we make, and how each is kept"},
    {
        "t": "table",
        "head": ["Claim", "What it must be true for it to hold", "Mechanism"],
        "rows": [
            [
                "You always get what you were promised",
                "A payout equals the base pool exactly, is never reduced by fees, and is "
                "released only when funded.",
                "Payout funding principle (BR-018), fee never reduces a payout (BR-012), "
                "escrow solvency assertion (BR-020)",
            ],
            [
                "You always know where you stand",
                "Every position, payment, fee and default is visible to the member, in real "
                "time, and is written once and never changed.",
                "Append-only ledger, member-scoped read model, audit trail (G6)",
            ],
            [
                "Nobody is exposed for struggling",
                "Default handling is private between the member, the organiser and platform "
                "risk, and never broadcast.",
                "Default sequence (BR-016), no shaming (BR-014), "
                "`member.defaulted` notification goes to the organiser only",
            ],
        ],
        "widths": [1.5, 2.55, 2.45],
        "size": 8.2,
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "Claims discipline",
        "text": (
            "These three claims are the whole brand. Any marketing material that adds a "
            "fourth claim — returns, insurance, protection, credit, guarantees — is outside "
            "what the product can deliver and must be rejected at review. AJO.ng does not "
            "insure pots, does not guarantee pots, does not lend and does not invest."
        )
    },
    {"t": "h3", "text": "1.15.3 Differentiation summary"},
    {
        "t": "table",
        "head": ["Alternative", "What the member gets", "Where AJO.ng is different"],
        "rows": [
            ["Traditional Ajo", "Zero cash return, enforced by trust, recorded by hand", "Same group, same trust, plus a record that survives the organiser"],
            ["WhatsApp group", "Free, familiar, no structure", "Same immediacy, plus a ledger, receipts, a schedule and recourse"],
            ["Bank savings account", "Interest, safety, a statement", "No interest; the point is forced regular saving plus peer enforcement"],
            ["Mobile money", "Transfer and store value", "Not a store of value; a rotating commitment with a defined payout position"],
            ["A formal credit cooperative", "Interest, governance, a place to leave money", "No membership fee, no minimum balance, no interest, works in a day, invitation-only"],
            ["Ajo.ng", "Zero cash return, enforced by process, recorded immutably, fee of 2% disclosed up front", "—"],
        ],
        "widths": [1.35, 2.45, 2.7],
        "size": 8.0,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Honest positioning",
        "text": (
            "AJO.ng sits in an unusual place: it offers **no financial return at all**. Its "
            "value is behavioural, not financial. This should be said plainly in onboarding "
            "and in marketing rather than glossed over, because a member who joins expecting "
            "a return will feel cheated at cycle ten when they receive exactly what they paid. "
            "Telling them on day one turns a disappointment into an expectation."
        )
    },

    # ----------------------------------------------------------------- 1.16
    {"t": "h2", "text": "1.16 Product scope"},
    {"t": "h3", "text": "1.16.1 MVP scope — in"},
    {
        "t": "p",
        "text": (
            "MVP is **private and invitation-only**. An Ajo exists only because a named "
            "person created it and named the people they want in it. This preserves the social "
            "trust the product depends on and limits the platform's exposure to strangers "
            "trading each other's participation, which is a different product with a "
            "different risk profile."
        )
    },
    {
        "t": "table",
        "head": ["Area", "In scope for MVP", "Note"],
        "rows": [
            ["Registration and login", "Email and phone registration, email verification, OTP, password plus refresh sessions, session listing and revocation", "No social login in MVP unless it is free of data-sharing risk; see DEC-04"],
            ["Profile", "Name, phone, email, avatar, notification preferences, financial summary", "Minimal data collection, deliberately"],
            ["Identity verification", "Email mandatory; phone OTP mandatory; BVN or CAC verification available and, if D-04 is decided, required above a threshold", "Threshold is open decision D-04"],
            ["Ajo creation", "7-step wizard: terms, contribution, frequency, size, positions, invitations, review", "Contribution, frequency and size configurable at creation"],
            ["Ajo settings", "Reminder cadence, reminder channels, payout destination per member, freeze, cancel, unfreeze, summary", "Terms are not editable after activation"],
            ["Invitations", "Issue, list, view by token, accept, decline, resend, expire", "Token-based, expiring, single use"],
            ["Joining", "Accept invitation, review full terms and fee, acknowledge complete-cycle commitment, claim or be assigned a position", "Fee shown before commit (BR-011)"],
            ["Member management", "List, view, add, remove pre-activation, update member details, request replacement, accept replacement, delegate organiser", "Removal permitted **only** pre-activation"],
            ["Contribution schedule", "Generated schedule for all rounds, per-member, with due dates, states and totals", "Derived, never hand-entered"],
            ["Payment collection", "Provider-initiated collection, verification, retry, receipt, idempotency", "Idempotency-Key required on every money-moving POST"],
            ["Contribution tracking", "Per-member and per-round status, outstanding balances, progress, statements", "Reads the ledger, never a cached counter"],
            ["Payout scheduling", "Schedule the next payout, show the pot position, hold on under-funding, notify recipient T-24h", "Never silently reduce (BR-018)"],
            ["Payout processing", "Funding, release request by organiser, release, settlement, failure and retry, held state", "Escrow solvency assertion runs before every release (BR-020)"],
            ["Transaction history", "Full member-scoped history, single transaction view, downloadable statements", "Exportable and retained"],
            ["Notifications", "The canonical catalogue in section 8 of CANONICAL.md, with per-channel preferences", "SMS reserved for money-critical and security events"],
            ["Disputes", "Open, attach evidence, message thread, escalate, resolve, record outcome", "Support may assist but may not move money"],
            ["Defaults", "The canonical default sequence, private handling, recovery tracking", "No automatic top-up of other members (BR-015)"],
            ["Admin management", "Overview, users, Ajos, disputes, risk, verification, reports, audit logs, settings, emergency freeze", "No role can edit the ledger"],
            ["Account security", "Device sessions, password change, new-device alerts, account freeze request, deletion request", "Freeze is a user-visible right"],
        ],
        "widths": [1.15, 3.1, 2.25],
        "size": 7.6,
    },
    {"t": "h3", "text": "1.16.2 Post-MVP scope — considered, not committed"},
    {
        "t": "table",
        "head": ["Candidate", "Why it is attractive", "What must be true first", "Status"],
        "rows": [
            ["Referred members (invite-only referral link)", "Cheapest possible acquisition in a trust-driven product", "Anti-abuse controls and a fraud limit (D-08)", "Candidate, not committed"],
            ["Organiser succession and delegation as a first-class feature", "Directly addresses P3 and N12", "Legal wording on delegation reviewed; role model proven", "Candidate, not committed"],
            ["Scheduled-frequency expansion (daily, weekly, fortnightly, monthly)", "Expands TAM beyond monthly market Ajos", "Ledger and round model generalised; tested against the existing state machine", "Candidate, not committed"],
            ["Statement formats suitable for banks and third parties", "Retains Ada and Bisi; aids Kemi", "Legal review of what a statement asserts", "Candidate, not committed"],
            ["Native mobile applications", "Better retention for Tunde and Chidi", "PWA validated as insufficient; or organiser demand justifies it", "Candidate, not committed"],
            ["Ajo templates from real market practice", "Reduces creation friction for Alhaji Musa", "Enough completed Ajos to identify genuine patterns", "Candidate, not committed"],
            ["Standalone public marketing and referral content", "Growth at scale", "Unit economics proven positive (BO3)", "Candidate, not committed"],
        ],
        "widths": [1.75, 1.6, 1.9, 1.25],
        "size": 7.8,
    },
    {"t": "h3", "text": "1.16.3 Out of scope — explicitly excluded"},
    {
        "t": "table",
        "head": ["Excluded", "Rationale", "Boundary that still applies"],
        "rows": [
            [
                "A public Ajo marketplace or directory",
                "An open market for participation in schemes involving other people's money is "
                "a materially different product with materially different fraud, consumer "
                "protection and regulatory questions. Not a launch feature.",
                "Every Ajo at launch requires a named organiser who invited every member.",
            ],
            [
                "Any credit or lending product",
                "Ajo.ng must never be a route by which a member's future receipts are "
                "pledged, assigned or lent against. This is both a risk decision and a "
                "regulatory one.",
                "No assignment of expected payouts, no pre-payout advances, no "
                "payout-against-collateral of any kind.",
            ],
            [
                "Cryptocurrency or stablecoins",
                "Adds a regulatory surface, a volatility surface and a fraud surface to a "
                "product whose entire value proposition is that it is boring and "
                "trustworthy.",
                "All amounts are NGN. Money columns are always bigint kobo, never float or "
                "numeric.",
            ],
            [
                "International participation and foreign currency",
                "Kemi's need is real, but accepting funds from non-residents raises unresolved "
                "questions about the custody arrangement (D-02), sanctions screening and "
                "exchange-rate treatment.",
                "MVP members are Nigerian residents transacting in NGN. Foreign participation "
                "is not offered, not marketed and not supported.",
            ],
            [
                "Yield, interest or investment",
                "An Ajo pays zero return. Presenting anything else would be misleading.",
                "No copy anywhere implies interest, yield, ROI, investment or financial gain.",
            ],
            [
                "Insurance or protection products",
                "Selling cover on a pot AJO.ng does not control and cannot guarantee creates "
                "an obligation the product cannot meet.",
                "No insurance, warranty, protection plan or guarantee is offered or implied.",
            ],
            [
                "Loan origination, credit scoring and bureau reporting",
                "Requires data sharing, consent architecture and regulatory analysis that do not "
                "exist at launch.",
                "Member data is used to operate the Ajo and for nothing else.",
            ],
            [
                "Money transfers between members, top-ups and gifts",
                "Out of scope. Funds move only as contributions into a round and as a payout "
                "out of it.",
                "The only money flows are contribution, fee, and base-pool payout.",
            ],
            [
                "Organiser-to-member advances or bridging loans",
                "Would make the organiser a lender and would undo the elimination of P7.",
                "The organiser is never a guarantor and never a creditor of a member.",
            ],
        ],
        "widths": [1.5, 2.75, 2.25],
        "size": 7.8,
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Scope-change discipline",
        "text": (
            "Anything in the out-of-scope table that is proposed for a later release must be "
            "brought back through this document as a numbered change, with the regulatory "
            "position, the fraud model and the trust consequences written out. It cannot be "
            "added as a feature ticket. Specifically, **public marketplace access, any credit "
            "product and any international participation each require a full re-review of "
            "this section before engineering begins.**"
        )
    },

    # ----------------------------------------------------------------- 1.17
    {"t": "h2", "text": "1.17 Functional requirements"},
    {
        "t": "p",
        "text": (
            "Requirements are grouped into five families. Each carries a unique ID, a "
            "testable statement, a MoSCoW priority and a reference to the business rule or "
            "section that justifies it. **Must** items are launch-blocking. **Should** items "
            "may be deferred to the first post-MVP release with sign-off. **Could** items are "
            "explicitly optional and may be dropped entirely without violating this "
            "specification."
        )
    },
    {
        "t": "table",
        "head": ["Priority", "Definition", "Launch effect"],
        "rows": [
            ["Must", "The product is unsafe, untrustworthy or unlawful without it", "Blocks launch"],
            ["Should", "The product works without it, but materially worse", "May be deferred with written sign-off"],
            ["Could", "A convenience, an optimisation, or a nicety", "May be dropped without consequence"],
        ],
        "widths": [0.7, 3.5, 2.3],
    },

    {"t": "h3", "text": "1.17.1 Identity, profile and account security"},
    {
        "t": "table",
        "head": ["ID", "Requirement", "Priority", "Section ref"],
        "rows": [
            ["FR-AUTH-001", "A visitor may register with email address and phone number; neither may be omitted.", "Must", "1.11.6, 1.16.1"],
            ["FR-AUTH-002", "Registration must reject an email address or phone number already registered to an account.", "Must", "BR-030"],
            ["FR-AUTH-003", "A newly registered account is created in an unverified state and cannot join an Ajo until both email and phone are verified.", "Must", "1.16.1"],
            ["FR-AUTH-004", "An email verification link must be sent within 60 seconds of registration and must expire after 24 hours.", "Must", "1.18 (NFR-PERF-002)"],
            ["FR-AUTH-005", "A phone OTP of 6 digits must be sent for verification and must expire after 5 minutes with a maximum of 5 attempts.", "Must", "1.11.3"],
            ["FR-AUTH-006", "A user may log in with email or phone plus password; the same account is reachable either way.", "Must", "1.16.1"],
            ["FR-AUTH-007", "Passwords must be stored as a salted adaptive hash; plaintext passwords must never be logged, emailed or returned by any endpoint.", "Must", "1.18 (NFR-SEC-001)"],
            ["FR-AUTH-008", "Password policy must require at least 10 characters and block the most common breached passwords. Length must be the dominant factor, not symbol classes.", "Must", "1.18 (NFR-SEC-002)"],
            ["FR-AUTH-009", "Login responses must not reveal whether an account exists; the same message and comparable timing must be returned for unknown accounts.", "Must", "1.18 (NFR-SEC-003)"],
            ["FR-AUTH-010", "Failed logins must be rate limited per account and per source address, with exponential backoff and a lockout that requires a reset rather than a bypass.", "Must", "1.18 (NFR-SEC-004)"],
            ["FR-AUTH-011", "Sessions use a short-lived access token and a rotating refresh token; a refresh token may be used once and reuse must revoke the whole family.", "Must", "1.18 (NFR-SEC-005)"],
            ["FR-AUTH-012", "A user may list all active sessions with device, location and last-seen time, and may revoke any single session or all sessions.", "Must", "FR-SEC-001"],
            ["FR-PROF-001", "A user may view and update their own profile: full name, phone number, email address and avatar.", "Must", "1.16.1"],
            ["FR-PROF-002", "A user may upload one avatar image; the client must enforce type and size limits and the server must re-validate both.", "Must", "1.18 (NFR-SEC-006)"],
            ["FR-PROF-003", "A user must be able to view a financial summary: total contributed, total received, fees paid, active Ajo count and outstanding balance.", "Must", "FR-TXN-002"],
            ["FR-PROF-004", "A user may view and update notification preferences per channel per event category, subject to the mandatory minimum in FR-NOTIF-006.", "Must", "1.18 (NFR-LOC-001)"],
            ["FR-PROF-005", "A user may export a complete personal data archive covering profile, Ajo memberships, transactions and statements.", "Should", "1.23"],
            ["FR-PROF-006", "A user may request deletion of their account. Deletion must be a reversible soft delete with a stated retention window for financial records.", "Must", "1.23, LEGAL below"],
            ["FR-KYC-001", "A user may submit a BVN verification request; the platform must never store the raw BVN, only the verification result and the provider reference.", "Must", "D-04, LEGAL below"],
            ["FR-KYC-002", "A user may submit a CAC (company) verification request for business membership, with the same non-storage rule as FR-KYC-001.", "Should", "1.11.4"],
            ["FR-KYC-003", "Verification results must be stored with the check outcome, timestamp, provider reference and reason codes where available.", "Must", "1.18 (NFR-AUD-002)"],
            ["FR-KYC-004", "A failed verification must state the reason in plain language and state what the user can do next. It must not state a suspicion of fraud.", "Must", "1.11.3"],
            ["FR-KYC-005", "Whether BVN or CAC verification is mandatory for all members or only above a contribution threshold is governed by open decision D-04 and must be configurable without code change.", "Must", "D-04"],
            ["FR-KYC-006", "Identity verification must be re-checkable by risk_officer and the result must be visible in the admin Verification screen.", "Must", "1.16.1"],
            ["FR-KYC-007", "The platform must not use verification data for any purpose other than verification, risk screening and legally required record-keeping.", "Must", "LEGAL below"],
            ["FR-SEC-001", "A user must be able to see every active device session and revoke it.", "Must", "FR-AUTH-012"],
            ["FR-SEC-002", "A `security.login_new_device` notification must be sent when a session is created from an unrecognised device or location.", "Must", "CAN §8"],
            ["FR-SEC-003", "A user may change their password, which must revoke all other sessions and require re-authentication.", "Must", "1.18 (NFR-SEC-005)"],
            ["FR-SEC-004", "A user may request a self-freeze, which must immediately block money-moving and must be reversible only by support after identity confirmation.", "Must", "1.25 R4"],
            ["FR-SEC-005", "Account unlock after a security freeze must require verified identity and a support action, never an automated rule alone.", "Must", "1.12 (support cannot move money)"],
            ["FR-SEC-006", "A user may reset a forgotten password via a verified email or phone channel; the reset token must be single-use and expire after 30 minutes.", "Must", "FR-AUTH-005"],
            ["FR-SEC-007", "All privileged administrative actions must require re-authentication within a short window and must be recorded in the audit log with actor, target, before and after.", "Must", "1.18 (NFR-AUD-003)"],
            ["FR-SEC-008", "The platform must not log or store full payment credentials at any layer. Tokenised provider references are the only permitted representation.", "Must", "1.18 (NFR-SEC-007)"],
            ["FR-SEC-009", "A user may view, acknowledge and download the current terms and privacy notice from within the app.", "Should", "1.16.1"],
        ],
        "widths": [0.95, 3.35, 0.6, 1.6],
        "size": 7.6,
    },
    {
        "t": "callout",
        "kind": "LEGAL",
        "title": "Personal data and verification data",
        "text": (
            "The data collected, retained and shared under FR-KYC-001 to FR-KYC-007, FR-PROF-005 "
            "and FR-PROF-006 must be reviewed by qualified Nigerian counsel against the "
            "applicable data protection regime in force at the time of launch. This document "
            "does **not** assert that AJO.ng's data practices are compliant with any statute, "
            "regulator's rules or industry guideline. Specific items requiring review include: "
            "the lawful basis for processing identity data, the retention period for financial "
            "records after account closure, whether BVN data may lawfully be transmitted to "
            "the chosen verification providers, the consent and notice content, and any "
            "cross-border transfer of member data to non-Nigerian processors. These must be "
            "settled before the first live member."
        )
    },

    {"t": "h3", "text": "1.17.2 Ajo lifecycle, invitations and membership"},
    {
        "t": "table",
        "head": ["ID", "Requirement", "Priority", "Section ref"],
        "rows": [
            ["FR-AJO-001", "A registered, email-verified user may create an Ajo via a 7-step wizard and may save a draft and return to it.", "Must", "1.16.1, CAN §7"],
            ["FR-AJO-002", "Creation must set: Ajo name, contribution amount, contribution frequency, maximum member count, enrollment window, round duration and organizer.", "Must", "CAN §3"],
            ["FR-AJO-003", "The wizard must validate contribution amount and member count against the configured platform limits before submission.", "Must", "D-08, FR-DEF-006"],
            ["FR-AJO-004", "Before activation the organizer must review and explicitly accept the Ajo terms, including the complete-cycle commitment and the statement that the organizer is not a guarantor.", "Must", "BR-004, BR-008"],
            ["FR-AJO-005", "The 2% fee must be shown in the wizard, in real money terms, with a worked example, before the Ajo can be created.", "Must", "BR-011"],
            ["FR-AJO-006", "Opening enrollment requires at least 2 positions filled, and contribution and frequency set; otherwise the transition is refused.", "Must", "CAN §3"],
            ["FR-AJO-007", "The enrollment window runs for exactly 5 days from opening, is displayed with an absolute end timestamp, and cannot be extended by the organizer.", "Must", "BR-001"],
            ["FR-AJO-008", "If every position is not filled when the window closes, the Ajo transitions to CANCELLED and all collected contributions are refunded in full.", "Must", "BR-001, D-05"],
            ["FR-AJO-009", "Activation locks every payout position. No member may change position after activation except by an approved replacement or transfer request.", "Must", "BR-002"],
            ["FR-AJO-010", "The organizer may propose position order; the proposal is advisory until activation, after which it is fixed.", "Must", "CAN §2, §3"],
            ["FR-AJO-011", "Contribution amount, frequency, member count and position order must be immutable once the Ajo is ACTIVE.", "Must", "BR-002, BR-004"],
            ["FR-AJO-012", "The organizer may request that `ajo_organizer` be delegated to another verified member; the delegate must accept, and the grant is recorded and revocable.", "Should", "N12, 1.11.4"],
            ["FR-AJO-013", "A member or organizer may freeze an Ajo with a recorded reason, and unfreeze returns it to ACTIVE with a full audit record of the interval.", "Must", "CAN §3"],
            ["FR-AJO-014", "A cancellation must record a reason, the acting role, the timestamp, and the disposition of every member balance.", "Must", "CAN §3"],
            ["FR-AJO-015", "An Ajo in COMPLETED or CANCELLED is terminal and must reject all further events, including organizer actions.", "Must", "CAN §3, CAN §2"],
            ["FR-AJO-016", "The Ajo detail screen must display the current state, the schedule, the current pot position, all members, and the fee disclosure.", "Must", "BR-011"],
            ["FR-AJO-017", "A user must see the Ajo summary: rounds completed, current round, amounts collected against target, next payout date and open defaults or disputes.", "Must", "FR-POS-002"],
            ["FR-INV-001", "An organizer may issue an invitation to a phone number or email address for a specific Ajo and position.", "Must", "1.7.1"],
            ["FR-INV-002", "An invitation must state the contribution amount, the 2% fee and the total charged, the frequency, the payout order, the 5-day enrollment window and the complete-cycle commitment.", "Must", "BR-011, BR-004"],
            ["FR-INV-003", "An invitation token must be single-use, time-limited, revocable by the organizer, and must not disclose the Ajo's other members or the pot value.", "Must", "1.18 (NFR-SEC-008)"],
            ["FR-INV-004", "An invitee may accept or decline an invitation, and may do so without an account, being asked to register only at acceptance.", "Should", "1.11.3"],
            ["FR-INV-005", "An organizer may resend an invitation, and must be prevented from sending more than a configured number of invitations to one destination in a period.", "Must", "FR-DEF-006"],
            ["FR-INV-006", "The recipient of an `invitation.received` notification must be the invitee across push, email and SMS.", "Must", "CAN §8"],
            ["FR-INV-007", "An expired or revoked invitation must produce a clear, non-technical explanation rather than a generic error.", "Should", "1.16.1"],
            ["FR-JOIN-001", "An invitee who accepts becomes a member of the Ajo in ENROLLMENT and is assigned a position.", "Must", "CAN §3"],
            ["FR-JOIN-002", "Before joining, the member must be shown a plain-language summary of the Ajo: who organizes it, size, amount, frequency, total duration, total payable, and what happens on default.", "Must", "1.11.6, N15"],
            ["FR-JOIN-003", "The join confirmation must display the contribution, the 2% fee and the total charged as three separate amounts, and require an explicit acknowledgement.", "Must", "BR-011"],
            ["FR-JOIN-004", "The member must acknowledge the complete-cycle commitment before the join is recorded.", "Must", "BR-005"],
            ["FR-JOIN-005", "A member may claim an unassigned position, or the organizer may assign one, with the assignment recorded either way.", "Must", "FR-AJO-010"],
            ["FR-JOIN-006", "A join attempt after activation, against a full Ajo, or without a valid invitation must be refused with a specific reason.", "Must", "FR-AJO-006"],
            ["FR-MEM-001", "An organizer may list all members of an Ajo with position, payment state, outstanding balance and contact details.", "Must", "1.16.1"],
            ["FR-MEM-002", "An organizer may add a member by invitation only; adding without the member's own acceptance is prohibited.", "Must", "1.16.1 (private)"],
            ["FR-MEM-003", "An organizer may remove a member **only while the Ajo is in DRAFT or ENROLLMENT**, and the removal must be recorded with a reason.", "Must", "CAN §2"],
            ["FR-MEM-004", "An organizer may send reminders, individually or to all outstanding members, at configured times, and each reminder must be logged.", "Must", "CAN §8, G9"],
            ["FR-MEM-005", "An organizer may view a member's contribution status but must not see the member's financial summary, other Ajos, or any record outside the Ajo.", "Must", "1.12, CAN §2"],
            ["FR-MEM-006", "A member may request a replacement exit; the request, the reason and the outcome are recorded, and no exit is unilateral after activation.", "Must", "BR-003, BR-004"],
            ["FR-MEM-007", "A replacement candidate, once approved, assumes all remaining obligations and the same position; the ledger records both the outgoing and incoming member.", "Must", "BR-003, N13"],
            ["FR-MEM-008", "Member and position records must be versioned for optimistic concurrency, and a conflicting update must be rejected rather than merged silently.", "Must", "CAN §5"],
        ],
        "widths": [0.95, 3.35, 0.6, 1.6],
        "size": 7.6,
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Open — replacement and removal economics",
        "text": (
            "FR-MEM-006 and FR-MEM-007 define the *mechanism*. Three commercial questions "
            "remain open and must be answered by the Founders and reviewed by counsel before "
            "launch: (1) whether a replacement candidate pays a premium, and where that "
            "premium is recorded; (2) who approves a replacement where the Ajo has no other "
            "position holder, given that `support` cannot move money; (3) what happens to a "
            "member who fails to pay and is then replaced mid-cycle. Until these are settled, "
            "the replacement flow may be built and tested but must not be enabled in "
            "production."
        )
    },

    {"t": "h3", "text": "1.17.3 Money: schedules, collection, tracking, payouts, history"},
    {
        "t": "table",
        "head": ["ID", "Requirement", "Priority", "Section ref"],
        "rows": [
            ["FR-SCH-001", "On activation, a contribution schedule must be generated for every round and every member, with due dates derived from the configured frequency.", "Must", "CAN §4, CAN §7"],
            ["FR-SCH-002", "The schedule must be stored as a derived record and must be re-derivable from the Ajo definition, so a generation failure is recoverable.", "Must", "1.18 (NFR-AVL-004)"],
            ["FR-SCH-003", "A member must see their complete schedule: every round, due date, amount owed, amount paid, fee, state and total remaining.", "Must", "N1, PP1"],
            ["FR-SCH-004", "The organizer must see the round-level view: who is paid, who is outstanding, and the amount still required to fund the round.", "Must", "N2, N7"],
            ["FR-SCH-005", "The schedule must display the total the member will pay across the whole Ajo, fee included, at join time and thereafter.", "Must", "1.9.2"],
            ["FR-SCH-006", "Schedule dates must be stored as timestamps in a single canonical time zone and rendered in the user's configured zone.", "Must", "1.18 (NFR-LOC-003)"],
            ["FR-PAY-001", "A member may initiate payment of a due contribution from the schedule or the contribution screen, in whole or in part where partial payment is enabled.", "Must", "1.16.1"],
            ["FR-PAY-002", "The amount charged must be the contribution plus the 2% fee, itemised before confirmation, and must be final at the moment of initiation.", "Must", "BR-011, BR-012"],
            ["FR-PAY-003", "Payment must be collected by the payment provider into the approved financial arrangement, never into an organizer's personal account.", "Must", "1.7.2, D-02"],
            ["FR-PAY-004", "Every money-moving POST must require an `Idempotency-Key` header; a repeated key must return the original result and must not move money twice.", "Must", "CAN §6"],
            ["FR-PAY-005", "The platform must reconcile a payment by provider webhook, signature-verified, and must not credit a contribution on the strength of a client-side success message alone.", "Must", "1.7.1, NFR-SEC-009"],
            ["FR-PAY-006", "The payment state machine must be INITIATED to PENDING to SUCCESS or FAILED, with CANCELLED, REVERSED and UNKNOWN states supported and UNKNOWN treated as not-yet-settled.", "Must", "CAN §4"],
            ["FR-PAY-007", "Every successful payment must produce a retrievable receipt showing contribution, fee, total charged, provider reference and timestamp as separate lines.", "Must", "N4, BR-011"],
            ["FR-PAY-008", "A failed payment must be retryable by the member without a new obligation being created, and a reversal must post a reversing entry rather than a mutation.", "Must", "FR-DEF-003, BR-024"],
            ["FR-PAY-009", "The platform must reconcile provider settlements against the ledger on a scheduled run, and must raise a risk event on any unmatched item.", "Must", "1.18 (NFR-AUD-005)"],
            ["FR-CON-001", "A member must see their own contribution state for every round: PENDING, PAID, OVERDUE, GRACE, DEFAULTED, RECOVERED or WRITTEN_OFF.", "Must", "CAN §4"],
            ["FR-CON-002", "An organizer must see the contribution state of every member in their Ajo, and no member may see another member's state outside their own.", "Must", "CAN §2"],
            ["FR-CON-003", "Outstanding balance must be computed from the ledger, never from a denormalised counter, and the two must be reconciled daily.", "Must", "G6, NFR-AUD-005"],
            ["FR-CON-004", "A contribution must move to OVERDUE automatically at its due time without any human action.", "Must", "CAN §4"],
            ["FR-CON-005", "A contribution must move to GRACE on entering OVERDUE and must issue the documented reminder sequence before any default is recorded.", "Must", "BR-016"],
            ["FR-CON-006", "The platform must never automatically increase another member's obligation when one member defaults.", "Must", "BR-015"],
            ["FR-CON-007", "Every state transition on a contribution must be written to the audit trail with actor, timestamp, prior state and new state.", "Must", "1.18 (NFR-AUD-001)"],
            ["FR-POS-001", "At the start of each round, the platform must compute the scheduled recipient and the required funding target as base pool, and must display both.", "Must", "1.7.1"],
            ["FR-POS-002", "The Ajo summary must show the current pot position: collected, required, remaining, and the percentage funded.", "Must", "N2, FR-AJO-017"],
            ["FR-POS-003", "The recipient must receive a `payout.upcoming` notification 24 hours before the scheduled payout date.", "Must", "CAN §8"],
            ["FR-POS-004", "A payout must be SCHEDULED, FUNDING, RELEASED, then SUCCESS or FAILED, with a HELD state reachable at any pre-settlement point.", "Must", "CAN §4"],
            ["FR-POS-005", "The scheduled payout date must be derived from the frequency and the Ajo start date, and must be visible to every member at join time.", "Must", "FR-SCH-005"],
            ["FR-POUT-001", "A payout must be released only when the full round funds are collected and available under the approved financial arrangement.", "Must", "BR-018"],
            ["FR-POUT-002", "If the required funds are not available, the payout must move to HELD. The platform must not reduce the payout and must not use corporate funds.", "Must", "BR-018, G4"],
            ["FR-POUT-003", "The payout amount must equal the base pool exactly. The platform fee must never be deducted from it under any circumstance.", "Must", "BR-012"],
            ["FR-POUT-004", "Only the recipient may nominate a payout destination, and the destination must be verified and in the recipient's own name.", "Must", "1.18 (NFR-SEC-010)"],
            ["FR-POUT-005", "An organizer may request release of a payout but may not release, control, modify or cancel it.", "Must", "CAN §2"],
            ["FR-POUT-006", "A released payout must post the ledger recognition sequence in the mandatory order, and any transaction that does not balance must be rejected.", "Must", "CAN §4, BR-020"],
            ["FR-POUT-007", "A failed payout must be retried by the platform automatically a bounded number of times before requiring member action, and every attempt must be recorded.", "Must", "CAN §4"],
            ["FR-POUT-008", "The recipient must receive a receipt for the payout showing the base pool, the fee retained separately, and the provider reference.", "Must", "1.9.2, N4"],
            ["FR-TXN-001", "A user must see a complete, filterable, member-scoped transaction history across all their Ajos, showing both contributions and payouts.", "Must", "FR-PROF-003"],
            ["FR-TXN-002", "The financial summary must be derivable entirely from the transaction history, with no separate balance store.", "Must", "G6"],
            ["FR-TXN-003", "A user must be able to generate and download a statement for any completed or in-progress Ajo, itemised by round.", "Must", "N11, 1.11.2"],
            ["FR-TXN-004", "A completed Ajo must remain fully readable and its statements must remain downloadable for the whole retention period.", "Must", "1.11.4, LEGAL below"],
            ["FR-TXN-005", "All list endpoints must use cursor pagination with a bounded limit, and must be stable under concurrent insertion.", "Must", "CAN §6"],
            ["FR-TXN-006", "Every response must echo an `X-Request-Id` and every error must be RFC-7807 shaped with a stable, documented error code.", "Must", "CAN §6"],
        ],
        "widths": [0.95, 3.35, 0.6, 1.6],
        "size": 7.6,
    },
    {
        "t": "callout",
        "kind": "LEGAL",
        "title": "Financial record retention",
        "text": (
            "The retention period asserted in FR-TXN-004 is a placeholder pending advice. The "
            "applicable period for financial records, identity verification records and "
            "communications in Nigeria must be confirmed by qualified Nigerian counsel, and "
            "the interaction between that period, the data protection position and the "
            "deletion right in FR-PROF-006 must be settled before launch. This document does "
            "not state what that period is."
        )
    },

    {"t": "h3", "text": "1.17.4 Notifications, disputes and defaults"},
    {
        "t": "table",
        "head": ["ID", "Requirement", "Priority", "Section ref"],
        "rows": [
            ["FR-NOTIF-001", "The platform must implement exactly the notification catalogue in section 8 of CANONICAL.md, with the stated recipients, channels and timings.", "Must", "CAN §8"],
            ["FR-NOTIF-002", "`contribution.due` must be delivered at T-24h and T-2h before the due time to the member.", "Must", "CAN §8"],
            ["FR-NOTIF-003", "SMS must be reserved for money-critical and security events. Every other event must default to push and email only.", "Must", "CAN §8, 1.11.6"],
            ["FR-NOTIF-004", "Notifications must be idempotent per event instance; a retried delivery must not produce a second message.", "Must", "FR-PAY-004"],
            ["FR-NOTIF-005", "A user may read, mark read, and mark all read, and must see an unread count per Ajo.", "Must", "CAN §6"],
            ["FR-NOTIF-006", "Users may opt out of push and email by category, but a money-critical and security minimum may not be disabled.", "Must", "FR-PROF-004, G5"],
            ["FR-NOTIF-007", "A defaulting member must never be named or identified in any notification, message or feed visible to other members.", "Must", "BR-014"],
            ["FR-DISP-001", "A member may raise a dispute against an Ajo, scoped to a specific round or contribution, with a category and a description.", "Must", "CAN §6"],
            ["FR-DISP-002", "A dispute must create a structured evidence thread to which the counterparty, the organizer and support may attach documents and messages.", "Must", "N8"],
            ["FR-DISP-003", "`support` may read all disputes, contact parties, assist and propose a resolution, but may not move money or alter financial records.", "Must", "CAN §2"],
            ["FR-DISP-004", "Every dispute action must be timestamped and attributed, and the full thread must be exportable.", "Must", "1.18 (NFR-AUD-001)"],
            ["FR-DISP-005", "Resolution outcomes must be recorded with the reason, the evidence relied on and the role that decided; the deciding role is recorded permanently.", "Must", "1.25 R1"],
            ["FR-DISP-006", "A member must be notified of a dispute opened against them and of every resolution, across push and email.", "Must", "CAN §8"],
            ["FR-DISP-007", "Disputes must not block a member's unrelated contributions or notifications, and must not freeze a payout without a recorded risk reason.", "Should", "BR-018"],
            ["FR-DEF-001", "On OVERDUE the platform must issue the documented sequence: reminder, retry if supported, 48-hour grace, organizer notification.", "Must", "CAN §4, BR-016"],
            ["FR-DEF-002", "A member must be able to see, before a due date, what will happen if they cannot pay: the states, the grace window and the consequences.", "Must", "N9, PP5"],
            ["FR-DEF-003", "Retry of a failed payment must be offered within the grace window and must not create a second obligation.", "Must", "FR-PAY-008"],
            ["FR-DEF-004", "`contribution.grace_ended` and `member.defaulted` must be sent to the organizer after the 48-hour grace elapses.", "Must", "CAN §8"],
            ["FR-DEF-005", "Default handling must be private between the member, the organizer and platform risk. No public or member-visible exposure is permitted.", "Must", "BR-014, G5"],
            ["FR-DEF-006", "The platform must not automatically charge other members extra. Any recovery must follow a documented, consent-based path.", "Must", "BR-015"],
            ["FR-DEF-007", "A defaulted contribution must be recoverable and must return to PAID on recovery, or to WRITTEN_OFF with a recorded decision and approver.", "Must", "CAN §4, CAN §2"],
            ["FR-DEF-008", "A member in default must have a documented route to request a replacement exit, which is a formal process and not a unilateral departure.", "Must", "FR-MEM-006, BR-003"],
            ["FR-DEF-009", "Default rates per Ajo, per organizer and per member must be measurable in admin reporting and trigger risk review at a configurable threshold.", "Must", "1.25 R4, D-08"],
        ],
        "widths": [0.95, 3.35, 0.6, 1.6],
        "size": 7.6,
    },

    {"t": "h3", "text": "1.17.5 Platform administration"},
    {
        "t": "table",
        "head": ["ID", "Requirement", "Priority", "Section ref"],
        "rows": [
            ["FR-ADM-001", "Admin screens must be reachable only by the role that owns them, with no page visible to a role that cannot act on it.", "Must", "1.12"],
            ["FR-ADM-002", "No role may edit or delete a ledger entry. Corrections are possible only by posting a reversing entry.", "Must", "CAN §2, G6"],
            ["FR-ADM-003", "`super_admin` may manage role assignments, and every grant and revocation must be recorded with granter, grantee, role, scope and timestamp.", "Must", "CAN §2"],
            ["FR-ADM-004", "`support` must be able to search and read users, Ajos, contributions, payments, payouts and disputes, and must be unable to mutate any of them.", "Must", "CAN §2, FR-DISP-003"],
            ["FR-ADM-005", "`risk_officer` may place an account or an Ajo under review, freeze it, and approve or reject overrides, and must be unable to edit the ledger or change fee configuration.", "Must", "CAN §2"],
            ["FR-ADM-006", "Every risk decision must record the trigger, the evidence considered, the decision, the rationale and the officer, and must be visible in the Risk screen.", "Must", "1.18 (NFR-AUD-003)"],
            ["FR-ADM-007", "`super_admin` may execute an emergency freeze that halts all money movement platform-wide, with the reason recorded.", "Must", "CAN §2"],
            ["FR-ADM-008", "The audit log screen must support filtering by actor, role, entity, action and date range, and must be read-only to every role including `super_admin`.", "Must", "CAN §6"],
            ["FR-ADM-009", "Admin reporting must cover deposits, volume, fee revenue, active Ajos, defaults, disputes, frozen accounts and reconciliation exceptions.", "Must", "1.27"],
            ["FR-ADM-010", "Platform settings changes, including fee configuration, limits and thresholds, must be versioned, effective-dated and audited, and must never alter historical ledger entries.", "Must", "CAN §5, FR-PAY-002"],
            ["FR-ADM-011", "Reconciliation runs must be executable and their results inspectable, with any exception creating a risk event that cannot be silently closed.", "Must", "FR-PAY-009, 1.18 (NFR-AUD-005)"],
            ["FR-ADM-012", "A support agent must never be able to perform any action that would result in money leaving the approved financial arrangement.", "Must", "1.12, G4"],
        ],
        "widths": [0.95, 3.35, 0.6, 1.6],
        "size": 7.6,
    },
    {
        "t": "table",
        "head": ["Requirement family", "Count", "Must", "Should", "Could"],
        "rows": [
            ["Identity, profile and account security", "34", "31", "3", "0"],
            ["Ajo lifecycle, invitations and membership", "38", "35", "3", "0"],
            ["Money: schedules, collection, payouts, history", "41", "41", "0", "0"],
            ["Notifications, disputes and defaults", "23", "22", "1", "0"],
            ["Platform administration", "12", "12", "0", "0"],
            ["Total", "148", "141", "7", "0"],
        ],
        "widths": [3.37, 0.8, 0.8, 0.8, 0.8],
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Why there are no Coulds",
        "text": (
            "No requirement in this specification is classified **Could**. A requirement that "
            "the product can live without but that is not yet built is a **Should** with a "
            "deferral date. The Could column is left empty deliberately: an empty Could "
            "column means nothing has been quietly assigned a low priority to make a date."
        )
    },

    # ----------------------------------------------------------------- 1.18
    {"t": "h2", "text": "1.18 Non-functional requirements"},
    {
        "t": "p",
        "text": (
            "Every target below is **measurable and testable**, and each has a named "
            "verification method. Where a target depends on an unresolved decision or an "
            "unconfirmed provider capability, the dependency is stated in the row. No provider "
            "capability is asserted as fact."
        )
    },
    {
        "t": "table",
        "head": ["ID", "Category", "Target", "Verified by"],
        "rows": [
            ["NFR-SEC-001", "Security", "Passwords stored only as salted adaptive hashes. Plaintext never persisted, logged or returned.", "Code review; static analysis; log inspection"],
            ["NFR-SEC-002", "Security", "Minimum 10-character password; breached-password blocklist enforced.", "Automated test suite; credential-stuffing simulation"],
            ["NFR-SEC-003", "Security", "No user enumeration via response body, status code or materially different timing.", "Automated enumeration test on login, reset and invitation"],
            ["NFR-SEC-004", "Security", "Rate limiting on all authentication and OTP endpoints with exponential backoff.", "Load and abuse test"],
            ["NFR-SEC-005", "Security", "Short-lived access tokens; rotating single-use refresh tokens; reuse revokes the token family.", "Token lifecycle test; server-side session revocation test"],
            ["NFR-SEC-006", "Security", "File uploads validated for type, size and content server-side; images re-encoded before storage.", "Upload abuse test with mismatched type and extension"],
            ["NFR-SEC-007", "Security", "No payment credentials stored at any layer; provider tokenisation only.", "Code review; data-store inspection"],
            ["NFR-SEC-008", "Security", "Invitation tokens single-use, expiring, revocable, and non-enumerable.", "Token entropy and expiry test"],
            ["NFR-SEC-009", "Security", "All provider webhooks signature-verified, replay-protected and idempotent before any credit is posted.", "Signature-failure and replay test suite"],
            ["NFR-SEC-010", "Security", "Payout destinations must be verified and in the recipient's own name before any release.", "Negative test with a mismatched account name"],
            ["NFR-PERF-001", "Performance", "Server-side API p95 under 300 ms and p99 under 800 ms for read endpoints at expected load.", "Load test at 1,000 concurrent sessions"],
            ["NFR-PERF-002", "Performance", "Verification email and OTP dispatched within 60 seconds of request, 99% of the time.", "Synthetic monitoring"],
            ["NFR-PERF-003", "Performance", "Payment initiation acknowledged by the platform within 2 seconds; final state within provider-agreed settlement time.", "Load test; provider SLA confirmation required"],
            ["NFR-PERF-004", "Performance", "Largest mobile screen fully interactive within 3 seconds on a mid-range Android device over 3G.", "Device testing on the lowest supported device class"],
            ["NFR-PERF-005", "Performance", "Statement generation for a completed 10-round Ajo within 10 seconds.", "Timing test"],
            ["NFR-AVL-001", "Availability", "99.5% monthly availability of the member-facing application, measured monthly.", "External synthetic monitoring"],
            ["NFR-AVL-002", "Availability", "99.0% availability of payment initiation and payout release paths, measured separately because they are the money paths.", "External monitoring with alert routing"],
            ["NFR-AVL-003", "Availability", "A provider webhook outage must not lose a payment. State must be recoverable by reconciliation within 24 hours.", "Chaos test with provider endpoint blocked"],
            ["NFR-AVL-004", "Availability", "No single point of failure in the payment initiation path; documented failover to a second provider is a post-MVP objective, not a launch claim.", "Architecture review"],
            ["NFR-AVL-005", "Availability", "Maintenance windows must never exceed 4 hours and must never fall inside a collection window.", "Release policy"],
            ["NFR-SCL-001", "Scalability", "Design to 10,000 concurrent members and 100 simultaneous payment initiations per second without architectural change.", "Load test"],
            ["NFR-SCL-002", "Scalability", "A single Ajo must support the maximum configured size without degrading any other Ajo's performance.", "Isolation test"],
            ["NFR-SCL-003", "Scalability", "The ledger must remain queryable at 100 million postings; partitioning and archival strategy documented before scale.", "Data volume test"],
            ["NFR-SCL-004", "Scalability", "Notification dispatch must absorb a 10x spike in a single event type without delaying other event types.", "Spike test"],
            ["NFR-SCL-005", "Scalability", "An organizer may manage at least 20 concurrent Ajos with no per-Ajo degradation.", "Load test with a synthetic heavy organizer"],
            ["NFR-ACC-001", "Accessibility", "WCAG 2.1 Level AA conformance for all member-facing web screens, verified per release.", "Automated scan plus manual keyboard and screen-reader pass"],
            ["NFR-ACC-002", "Accessibility", "Every interactive element reachable and operable by keyboard alone, with a visible focus indicator.", "Manual keyboard traversal"],
            ["NFR-ACC-003", "Accessibility", "No information conveyed by colour alone. Contribution, default and payout states must carry a text label and an icon.", "Design review; contrast audit"],
            ["NFR-ACC-004", "Accessibility", "Minimum text contrast ratio of 4.5 to 1 for body text against the brand palette.", "Automated contrast test on the theme tokens"],
            ["NFR-ACC-005", "Accessibility", "Core flows (join, pay, view position) completable without a mouse, including on the low-bandwidth path.", "Keyboard-only end-to-end test"],
            ["NFR-AUD-001", "Auditability", "Every state transition on every business entity records actor, role, timestamp, prior state and new state, and is immutable.", "Schema inspection plus query test"],
            ["NFR-AUD-002", "Auditability", "Every verification attempt, including failures, is recorded with outcome and provider reference.", "Query test"],
            ["NFR-AUD-003", "Auditability", "Every privileged action requires re-authentication and is recorded with before and after values.", "Admin action test with audit log inspection"],
            ["NFR-AUD-004", "Auditability", "The audit log is append-only and readable by every admin role, writable by none.", "Permission test proving no write path exists"],
            ["NFR-AUD-005", "Auditability", "Daily automated reconciliation between provider settlements, the ledger and balances, with any exception creating a risk event.", "Scheduled job with an exception injection test"],
            ["NFR-AUD-006", "Auditability", "Every transaction in the ledger must balance to zero or be rejected. An unbalanced transaction cannot be committed.", "Automated invariant check on every write path"],
            ["NFR-LOC-001", "Localisation", "English and Nigerian Pidgin are supported for member-facing copy in MVP; every string is externalised, none hard-coded.", "String extraction check"],
            ["NFR-LOC-002", "Localisation", "All money is displayed in NGN with two decimal places and thousands separators, using kobo integers internally with no floating point.", "Unit and rendering tests"],
            ["NFR-LOC-003", "Localisation", "All timestamps stored in UTC and rendered in the user's configured time zone, with an explicit zone shown whenever a deadline matters.", "Cross-zone test"],
            ["NFR-LOC-004", "Localisation", "Naira amounts must never be represented using the naira glyph in exports, statements or API payloads, due to known encoding failures in downstream tools.", "Export fixture test"],
        ],
        "widths": [1.0, 0.85, 3.15, 1.5],
        "size": 7.5,
    },
    {
        "t": "callout",
        "kind": "ASSUMPTION",
        "title": "NFR targets are engineering targets, not measured facts",
        "text": (
            "The performance, availability and scalability targets above are **engineering "
            "targets set at specification time**. No system exists, nothing has been measured, "
            "and no provider SLA has been obtained. They are the acceptance thresholds the "
            "build will be tested against. Several of them, notably NFR-PERF-003, cannot be "
            "validated until ProvidusUnity provides written settlement timing (D-03)."
        )
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The Naira glyph",
        "text": (
            "NFR-LOC-004 exists because the naira glyph renders unreliably in PDF, DOCX and "
            "some downstream accounting tools. Throughout this specification, **NGN** is used "
            "in tables, exports, API payloads and code, and the glyph is used only in prose. "
            "This is a rendering decision, not a currency decision; the currency is the "
            "Nigerian naira throughout."
        )
    },

    # ----------------------------------------------------------------- 1.19
    {"t": "h2", "text": "1.19 Core features"},
    {
        "t": "p",
        "text": (
            "The features below are the product. Everything not listed here is either a "
            "supporting enabler or out of scope per section 1.16.3. Priority follows the "
            "same Must/Should/Could convention as section 1.17."
        )
    },
    {
        "t": "table",
        "head": ["#", "Feature", "What the user does with it", "Priority", "Requirements"],
        "rows": [
            ["F1", "Create an Ajo", "Sets contribution, frequency, size, positions and terms in a 7-step wizard, then invites named people.", "Must", "FR-AJO-001 to FR-AJO-011"],
            ["F2", "Invite to an Ajo", "Issues a tokenised, expiring invitation that discloses the full terms and the 2% fee before acceptance.", "Must", "FR-INV-001 to FR-INV-007"],
            ["F3", "Join an Ajo", "Reads a plain-language summary, sees the fee itemised, acknowledges the complete-cycle commitment, takes a position.", "Must", "FR-JOIN-001 to FR-JOIN-006"],
            ["F4", "Automatic schedule", "Receives a generated, locked, per-round schedule with due dates, amounts owed and totals.", "Must", "FR-SCH-001 to FR-SCH-006"],
            ["F5", "Pay a contribution", "Pays the contribution plus the 2% fee in one action, with a receipt, verified by webhook and idempotent.", "Must", "FR-PAY-001 to FR-PAY-009"],
            ["F6", "See exactly where you stand", "Views contribution state, outstanding balance, position, payout date and the pot's funding progress at any time.", "Must", "FR-CON-001 to FR-CON-007, FR-POS-002"],
            ["F7", "Payout to the member on turn", "Receives the base pool in full, released only when funded, with a receipt.", "Must", "FR-POS-001 to FR-POS-005, FR-POUT-001 to FR-POUT-008"],
            ["F8", "Held payouts with explanation", "When funds are short, sees a clear held state and an explanation, never a silently reduced amount.", "Must", "FR-POUT-002, BR-018"],
            ["F9", "Reminders and notifications", "Receives T-24h and T-2h due reminders, receipts, payout notices and security alerts on the right channel.", "Must", "FR-NOTIF-001 to FR-NOTIF-007"],
            ["F10", "Receipts and statements", "Gets a receipt for every payment and payout, and a downloadable statement for every Ajo.", "Must", "FR-PAY-007, FR-POUT-008, FR-TXN-003"],
            ["F11", "Disputes with evidence", "Raises a dispute, attaches evidence, and reads a permanent, timestamped thread.", "Must", "FR-DISP-001 to FR-DISP-007"],
            ["F12", "Private default handling and recovery", "Gets a 48-hour grace, a private process, a recovery path and a formal replacement route, with no public exposure.", "Must", "FR-DEF-001 to FR-DEF-009"],
            ["F13", "Replacement and transfer", "Requests a replacement exit and hands over to an approved successor, with both parties recorded in the ledger.", "Should", "FR-MEM-006, FR-MEM-007"],
            ["F14", "Organiser delegation", "Hands organiser duties to a trusted verified member, so the Ajo survives absence.", "Should", "FR-AJO-012"],
            ["F15", "Account security centre", "Views sessions, revokes devices, changes password, self-freezes and exports personal data.", "Must", "FR-SEC-001 to FR-SEC-009"],
            ["F16", "Identity verification", "Verifies BVN or CAC where required, with results stored but raw identifiers never retained.", "Must", "FR-KYC-001 to FR-KYC-007"],
            ["F17", "Admin risk and fraud console", "Reviews risk events, freezes, approves overrides, manages limits and inspects reconciliation exceptions.", "Must", "FR-ADM-005, FR-ADM-006, FR-ADM-011"],
            ["F18", "Audit log", "Inspects every privileged and state-changing action, read-only, filterable, permanent.", "Must", "FR-ADM-008, NFR-AUD-001 to NFR-AUD-006"],
            ["F19", "Financial reporting", "Reports deposits, volume, fee revenue, defaults, disputes and exceptions for business and risk use.", "Must", "FR-ADM-009, 1.27"],
            ["F20", "Organiser console", "One view of every Ajo the organizer runs: funding progress, outstanding members, defaults, disputes, release requests.", "Must", "FR-AJO-017, FR-MEM-004"],
            ["F21", "Low-bandwidth and SMS path", "Receives SMS for money-critical events and can complete the core flows on a weak connection.", "Must", "NFR-LOC-001, NFR-PERF-004"],
            ["F22", "Notification preferences", "Chooses channels and categories, with a non-optional money and security minimum.", "Must", "FR-PROF-004, FR-NOTIF-006"],
        ],
        "widths": [0.35, 1.4, 2.85, 0.6, 1.3],
        "size": 7.6,
    },

    # ----------------------------------------------------------------- 1.20
    {"t": "h2", "text": "1.20 User stories and acceptance criteria"},
    {
        "t": "p",
        "text": (
            "Thirty-six stories, each written as a role, a need and a benefit, with Given / "
            "When / Then acceptance criteria that a test engineer can execute without further "
            "interpretation. The canonical fee example is used in US-21."
        )
    },

    {"t": "h3", "text": "1.20.1 Onboarding and identity"},
    {
        "t": "table",
        "head": ["ID", "User story", "Acceptance criteria (Given / When / Then)"],
        "rows": [
            ["US-01", "As a new user, I want to register with my phone and email so that I can be reached where I actually am.", "**Given** no account exists for the phone or email, **when** I submit valid details, **then** an account is created unverified, a verification email is sent within 60 seconds and an OTP is sent, and the OTP expires after 5 minutes with no more than 5 attempts."],
            ["US-02", "As a new user, I want the app to tell me plainly what to do next, so that I do not get stuck before I have seen the product.", "**Given** I am unverified, **when** I open the app, **then** I am shown one clear next action, and I cannot see any Ajo content, and joining is refused with a specific reason rather than a blank screen."],
            ["US-03", "As a new user, I want to know the app will not tell anyone I have an account, so that I feel safe registering.", "**Given** I register with an unknown email, **when** I read the response, **then** it is byte-identical to the response for a known email, and the response time is not materially different, and no enumeration is possible from the status code."],
            ["US-04", "As a user, I want to see every device I am signed in on and kill the ones I do not recognise.", "**Given** I have three active sessions, **when** I revoke one, **then** its access token stops working on the next request, its refresh token is revoked, and the other two are unaffected, and a `security.login_new_device` alert is not sent."],
            ["US-05", "As a user, I want to be warned when a new device signs in, so that I find out before someone else uses my account.", "**Given** I am signed in on one device, **when** a session is created from an unrecognised device, **then** a `security.login_new_device` notification is sent to push and email, and the session list shows the device, location and time."],
            ["US-06", "As a business member, I want to verify my business without handing over my raw identifiers.", "**Given** I submit a CAC verification, **when** the check completes, **then** only the result, timestamp and provider reference are stored, the raw identifier is not retained, and I can see the outcome and what to do next."],
        ],
        "widths": [0.5, 2.4, 3.6],
        "size": 7.6,
    },
    {"t": "h3", "text": "1.20.2 Creating and running an Ajo"},
    {
        "t": "table",
        "head": ["ID", "User story", "Acceptance criteria (Given / When / Then)"],
        "rows": [
            ["US-07", "As an organizer, I want to define an Ajo in a few clear steps, so that creating one does not feel like paperwork.", "**Given** I am verified, **when** I complete the 7-step wizard with valid terms, **then** the Ajo is created in DRAFT, the wizard is resumable, and every step shows the fee that will apply."],
            ["US-08", "As an organizer, I want to see exactly what the 2% fee will cost, so that I can explain it to my members honestly.", "**Given** a contribution of NGN 1,000.00 for 10 members over 10 rounds, **when** I reach the review step, **then** I see the contribution NGN 1,000.00, the fee NGN 20.00, the total charged NGN 1,020.00, the base pool paid to the recipient NGN 10,000.00, and the total across the Ajo NGN 102,000.00."],
            ["US-09", "As an organizer, I want to invite specific people by name or number, so that my Ajo stays my group.", "**Given** my Ajo is in ENROLLMENT, **when** I issue invitations, **then** each is single-use, expiring and revocable, discloses the full terms and the fee, and reveals nothing about other members or the pot value."],
            ["US-10", "As an organizer, I want the enrollment window to close on time, so that I am not left holding an incomplete Ajo.", "**Given** enrollment opened 5 days ago and not every position is filled, **when** the window closes, **then** the Ajo transitions to CANCELLED automatically, a reason is recorded, and every collected contribution is refunded in full."],
            ["US-11", "As an organizer, I want positions to lock when the Ajo activates, so that I cannot be accused of moving someone's turn.", "**Given** my Ajo is ACTIVE, **when** I attempt to reorder positions directly, **then** the attempt is refused, and the only available path is a formal replacement or transfer request, and the refusal is recorded."],
            ["US-12", "As an organizer, I want one view of every Ajo I run, so that I am not maintaining three notebooks.", "**Given** I organize three Ajos, **when** I open my console, **then** I see funding progress, outstanding members, open defaults, open disputes and release requests for all three, and no financial record of any member outside those Ajos."],
            ["US-13", "As an organizer, I want to hand over to a deputy when I travel, so that the Ajo survives my absence.", "**Given** I am the organizer, **when** I nominate a verified member and they accept, **then** the grant is recorded with both identities and a timestamp, is revocable, and my own organizer rights end immediately on acceptance."],
        ],
        "widths": [0.5, 2.4, 3.6],
        "size": 7.6,
    },
    {"t": "h3", "text": "1.20.3 Joining"},
    {
        "t": "table",
        "head": ["ID", "User story", "Acceptance criteria (Given / When / Then)"],
        "rows": [
            ["US-14", "As an invitee, I want to see what I am agreeing to before I join, in plain language.", "**Given** I open an invitation, **when** the detail page loads, **then** I see the organizer's name, the member count, the contribution, the frequency, the total duration, the total I will pay, and what happens if I miss a payment, without reading a contract."],
            ["US-15", "As an invitee, I want to see the fee as a separate number, not buried in the amount.", "**Given** the contribution is NGN 1,000.00, **when** I view the join confirmation, **then** I see three separate lines: contribution NGN 1,000.00, platform fee 2% NGN 20.00, and total charged NGN 1,020.00, and I must acknowledge before joining."],
            ["US-16", "As an invitee, I want to know I am committing to the whole cycle, not just my turn.", "**Given** the Ajo has 10 rounds, **when** I review the terms, **then** I see that I am committing to all remaining rounds, that my position is fixed at activation, and that leaving requires a formal replacement request, and I must acknowledge this separately."],
            ["US-17", "As an invitee, I want to know my turn before I join, not after.", "**Given** I am viewing an Ajo before activation, **when** I load the join screen, **then** my position number and expected round are shown, and if the order is still provisional this is stated in those words."],
            ["US-18", "As an invitee, I want to decline without creating an account.", "**Given** I have not registered, **when** I decline the invitation, **then** no account is created, the organizer is notified, and the token is invalidated."],
            ["US-19", "As a member, I want to know why I cannot join, so that I do not think the app is broken.", "**Given** the Ajo is already ACTIVE or full, **when** I attempt to accept, **then** I am told in plain language that enrollment has closed and who to contact, and no partial membership is created."],
        ],
        "widths": [0.5, 2.4, 3.6],
        "size": 7.6,
    },
    {"t": "h3", "text": "1.20.4 Paying and tracking"},
    {
        "t": "table",
        "head": ["ID", "User story", "Acceptance criteria (Given / When / Then)"],
        "rows": [
            ["US-20", "As a member, I want to see what I owe and when, so that I never have to ask.", "**Given** my Ajo is ACTIVE, **when** I open my schedule, **then** I see every round, due date, contribution, fee, total charged, amount paid, state and remaining total, and this view needs no organiser input."],
            ["US-21", "As a member, I want to know exactly what I will be charged, so that I am never surprised.", "**Given** I owe NGN 1,000.00, **when** I open the payment screen, **then** I see contribution NGN 1,000.00, platform fee 2% NGN 20.00, total NGN 1,020.00, and the amount is final at initiation and cannot change afterwards."],
            ["US-22", "As a member, I want to pay once and never be charged twice, so that I can retry safely.", "**Given** I submitted a payment, **when** the client retries the same request with the same Idempotency-Key, **then** the original result is returned, no second obligation is created and no second ledger entry is posted."],
            ["US-23", "As a member, I want a receipt for every payment, so that I can prove I paid.", "**Given** my payment settled, **when** I open the receipt, **then** I see contribution, fee, total charged, provider reference, timestamp and the resulting contribution state as separate lines."],
            ["US-24", "As a member, I want to know I have paid before I worry, so that a delayed confirmation does not cause a panic.", "**Given** a payment has been initiated but the provider has not confirmed, **when** I open the app, **then** the state reads PENDING with an explanation, and I am not shown as in arrears, and I am not prompted to pay again."],
            ["US-25", "As a member, I want the app to work on a poor connection, so that I can pay from the market.", "**Given** a 3G connection on a mid-range Android device, **when** I complete the core flows of joining, paying and viewing my position, **then** each completes without exceeding 3 seconds to interactive and without a duplicated payment."],
        ],
        "widths": [0.5, 2.4, 3.6],
        "size": 7.6,
    },
    {"t": "h3", "text": "1.20.5 Payouts"},
    {
        "t": "table",
        "head": ["ID", "User story", "Acceptance criteria (Given / When / Then)"],
        "rows": [
            ["US-26", "As a recipient, I want to receive exactly what was promised, in full.", "**Given** a 10-member round with NGN 1,000.00 contributions, **when** the payout is released and settles, **then** I receive NGN 10,000.00, the retained platform fee for that round is NGN 200.00, and my receipt shows the base pool and the retained fee as separate lines."],
            ["US-27", "As a recipient, I want to know my payout is coming before it arrives, so that I can plan.", "**Given** my turn is 24 hours away, **when** the notification window opens, **then** I receive `payout.upcoming` on push, email and SMS, and I see the date, the amount and the destination."],
            ["US-28", "As a recipient, I would rather wait than be paid short, so that the promise is not broken.", "**Given** NGN 100,000.00 is due and only NGN 90,000.00 is available, **when** release is attempted, **then** the release is refused, the payout enters HELD, I am notified on push, email and SMS, the organizer is notified, and no reduced amount is ever paid and no corporate funds are used."],
            ["US-29", "As a recipient, I want to control where my money goes, so that it reaches my own account.", "**Given** I nominate a payout destination, **when** the name on the destination account does not match my verified name, **then** the nomination is rejected with a specific reason and no payout can be released to it."],
        ],
        "widths": [0.5, 2.4, 3.6],
        "size": 7.6,
    },
    {"t": "h3", "text": "1.20.6 Disputes, defaults and trust"},
    {
        "t": "table",
        "head": ["ID", "User story", "Acceptance criteria (Given / When / Then)"],
        "rows": [
            ["US-30", "As a member, I want to raise a dispute about a specific payment with evidence, so that it can be settled on facts.", "**Given** I believe a contribution was not credited, **when** I raise a dispute against that round, **then** a dispute is created with a timestamp, the counterparty and the organizer are notified, and I can attach evidence to a permanent thread that all parties can see."],
            ["US-31", "As a member, I want to know what will happen if I cannot pay this week, before it happens.", "**Given** a contribution is due in 3 days, **when** I open the contribution detail, **then** I see the state sequence, the 48-hour grace, what my options are, and that other members will not be charged extra because of me."],
            ["US-32", "As a member, I want my missed payment handled privately, so that I am not exposed.", "**Given** I have defaulted, **when** the default is recorded, **then** only I, the organizer and platform risk are notified, no other member sees my name or state, and no public or member-visible feed contains the default."],
            ["US-33", "As an organizer, I want to be told when grace has ended, so that I know when to act.", "**Given** a member's contribution is overdue, **when** 48 hours elapse without payment, **then** I receive `contribution.grace_ended` and then `member.defaulted`, and the member's remaining balance and recovery options are shown to me."],
            ["US-34", "As a member, I want to leave without stranding the others, so that I am not forced to stay in something I cannot afford.", "**Given** I am in an ACTIVE Ajo, **when** I request a replacement exit, **then** a formal request is created with a reason, no unilateral exit is possible, an approved replacement assumes my position and my remaining obligations, and both members are recorded in the ledger."],
        ],
        "widths": [0.5, 2.4, 3.6],
        "size": 7.6,
    },
    {"t": "h3", "text": "1.20.7 Security and administration"},
    {
        "t": "table",
        "head": ["ID", "User story", "Acceptance criteria (Given / When / Then)"],
        "rows": [
            ["US-35", "As a user, I want to freeze my own account instantly, so that I can stop a problem before I understand it.", "**Given** I suspect fraud on my account, **when** I request a self-freeze, **then** all money movement stops immediately, I receive `account.frozen` on push, email and SMS, and only a support action after verified identity can unfreeze it."],
            ["US-36", "As a support agent, I want to see everything and change nothing, so that I can help without becoming a risk.", "**Given** I am signed in as support, **when** I open any admin screen, **then** I can read users, Ajos, contributions, payments, payouts, disputes and audit logs, and every mutation control is absent and every mutation endpoint rejects my role with a recorded attempt."],
            ["US-37", "As a risk officer, I want every decision I make to be explained and permanent, so that my judgement can be reviewed.", "**Given** I place an Ajo under review, **when** I record the decision, **then** the trigger, evidence, decision, rationale and my identity are stored, the decision appears in the Risk screen, and it is visible in the audit log to every admin role including super_admin."],
            ["US-38", "As a member, I want to keep a record of my completed Ajos, so that my savings history outlives the scheme.", "**Given** an Ajo has reached COMPLETED, **when** I open the completed Ajo, **then** the full round history, all receipts and a downloadable statement remain readable and downloadable for the whole retention period."],
        ],
        "widths": [0.5, 2.4, 3.6],
        "size": 7.6,
    },

    # ----------------------------------------------------------------- 1.21
    {"t": "h2", "text": "1.21 Business rules"},
    {
        "t": "p",
        "text": (
            "Business rules are the **fixed, non-negotiable constraints** on the product. They "
            "are numbered BR-001 onwards and referenced from the requirements in section 1.17. "
            "A change to any of these is a change to the product promise and requires "
            "reissue of this document."
        )
    },
    {"t": "h3", "text": "1.21.1 Enrollment, commitment and membership"},
    {
        "t": "table",
        "head": ["ID", "Rule", "Detail", "Enforced by"],
        "rows": [
            ["BR-001", "Five-day enrollment window", "An Ajo may remain in ENROLLMENT for exactly 5 days. If every position is not filled when the window closes, the Ajo transitions to CANCELLED and all collected contributions are refunded in full. The window cannot be extended by the organizer.", "State machine, FR-AJO-007, FR-AJO-008"],
            ["BR-002", "Positions lock on activation", "When an Ajo transitions to ACTIVE, every payout position is fixed. No member may change position afterwards except by a formal, approved replacement or transfer request. Reordering is not permitted by any role for any reason.", "State machine, FR-AJO-009, FR-AJO-010, FR-AJO-011"],
            ["BR-003", "No unilateral exit after activation", "A member who has joined an ACTIVE Ajo may not leave on their own initiative. Exiting requires a replacement or transfer request that is recorded, and the incoming member assumes the outgoing member's position and all remaining obligations.", "FR-MEM-006, FR-MEM-007, FR-DEF-008"],
            ["BR-004", "Complete-cycle commitment", "Joining an Ajo is a commitment to pay every remaining round until the Ajo completes, or until an approved replacement takes the position. The commitment is disclosed on the invitation, on the join confirmation, and must be explicitly acknowledged before the join is recorded.", "FR-INV-002, FR-JOIN-003, FR-JOIN-004"],
            ["BR-005", "Terms are immutable once active", "Contribution amount, frequency, member count and position order cannot be changed after activation. Administrative changes require cancellation and a new Ajo.", "FR-AJO-011"],
            ["BR-006", "Membership is by invitation only", "At MVP, no member may be added to an Ajo without their own acceptance of an invitation. There is no public directory, no open marketplace and no way to add a member directly.", "FR-MEM-002, 1.16.1"],
            ["BR-007", "Removal is pre-activation only", "An organizer may remove a member only while the Ajo is in DRAFT or ENROLLMENT. Removal after activation is prohibited for every role.", "FR-MEM-003, CAN §2"],
            ["BR-008", "The organizer is not a guarantor", "The organizer is a facilitator. They do not hold member funds, do not authorize payouts, and do not guarantee any member's debt or the pot. A shortfall is the platform's and the Ajo's problem to solve through the recovery process, never the organizer's personal liability. This must be stated in the terms, in organizer onboarding and in the join confirmation.", "FR-AJO-004, 1.12.2, LEGAL"],
            ["BR-009", "Terminal states are terminal", "An Ajo in COMPLETED or CANCELLED accepts no further events, including any organizer action. Attempting one is rejected and recorded.", "FR-AJO-015"],
        ],
        "widths": [0.5, 1.35, 3.55, 1.1],
        "size": 7.5,
    },
    {"t": "h3", "text": "1.21.2 Money, fee and payout"},
    {
        "t": "table",
        "head": ["ID", "Rule", "Detail", "Enforced by"],
        "rows": [
            ["BR-010", "The fee is 2% of the contribution, added on top", "A member owing NGN 1,000.00 is charged NGN 1,020.00. The contribution is NGN 1,000.00 and the fee is NGN 20.00, recorded as fees_income. Fee is computed in kobo as (amount_kobo * 200 + 5000) / 10000, half-up.", "FR-PAY-002, 1.9.1"],
            ["BR-011", "Fee disclosure is mandatory and pre-commitment", "The fee must be shown separately from the contribution on every receipt, in every Ajo details screen, and in the invitation and join confirmation, before the member commits. A commit action that does not display the fee is prohibited.", "FR-INV-002, FR-JOIN-003, FR-PAY-002, FR-PAY-007"],
            ["BR-012", "The 2% fee never reduces a payout", "The fee is never deducted from a member's contribution and never reduces a payout. The recipient receives the base pool exactly: NGN 10,000.00 for a 10-member round of NGN 1,000.00 contributions, never NGN 10,200.00.", "FR-POUT-003, FR-POUT-008, 1.9.2"],
            ["BR-013", "Every transaction balances to zero or is rejected", "No ledger transaction may be committed unless its debits equal its credits. An unbalanced transaction is rejected at the data layer, not logged and corrected afterwards.", "NFR-AUD-006, CAN §4"],
            ["BR-018", "Payout funding principle", "A payout is released only when the required round funds are fully collected and available under the approved financial arrangement. If NGN 100,000.00 is due and only NGN 90,000.00 is available, AJO.ng must not silently reduce the payout and must not use corporate funds. The round enters HELD or pending-funding and the recovery process begins.", "FR-POUT-001, FR-POUT-002, G4"],
            ["BR-020", "Escrow solvency assertion", "Before every disbursement the platform asserts that the escrow balance is sufficient for the liability being settled. Skipping the payout recognition step drains escrow against a liability that was never raised, and the assertion correctly halts disbursement. The assertion runs on every release and is not bypassable by any role.", "FR-POUT-006, NFR-AUD-006, CAN §4"],
            ["BR-021", "Ledger recognition sequence is mandatory and ordered", "Entries post in this order, each balanced on its own: 1. contribution.received, debit escrow cash and credit contributions receivable for the contribution. 2. fee.recognised, debit escrow cash and credit fees income for the 2%. 3. payout.recognized, debit contributions_receivable and credit payouts_payable. 4. payout.settled, debit payouts_payable and credit escrow_cash. Steps must not be skipped or reordered, and a one-sided entry is rejected rather than posted.", "FR-POUT-006, CAN §4"],
            ["BR-022", "The organizer never handles the money", "Contributions are collected by the payment provider into the approved financial arrangement. The organizer does not receive, hold, forward or reconcile member funds at any point.", "FR-PAY-003, 1.7.2"],
            ["BR-023", "Support never moves money", "The support role can read all records and cannot initiate or moderate payouts, change balances or override risk decisions. Any attempt is rejected and recorded.", "FR-ADM-004, FR-ADM-012, CAN §2"],
            ["BR-024", "Idempotency on every money movement", "Every POST that moves money requires an Idempotency-Key. A repeated key returns the original result and never moves money twice.", "FR-PAY-004, CAN §6"],
        ],
        "widths": [0.5, 1.35, 3.55, 1.1],
        "size": 7.5,
    },
    {"t": "h3", "text": "1.21.3 Default, trust and governance"},
    {
        "t": "table",
        "head": ["ID", "Rule", "Detail", "Enforced by"],
        "rows": [
            ["BR-014", "No shaming of defaulters", "AJO.ng does not publicly shame or expose a defaulting member. Defaulting is private between the member, the organizer and platform risk. No member-visible feed, notification, ranking, leaderboard or report may identify a defaulting member to other members.", "FR-NOTIF-007, FR-DEF-005, G5"],
            ["BR-015", "No automatic top-up of other members", "AJO.ng does not automatically charge other members extra when one member defaults. Any recovery requiring other members to contribute more must be a documented, explicit, consent-based process and must never happen silently.", "FR-CON-006, FR-DEF-006, CAN §4"],
            ["BR-016", "The default sequence is fixed", "The sequence is: reminder, retry if supported, 48-hour grace, organizer notified, member contacted, payment or default recorded, recovery process. No step may be skipped, and no default may be recorded before the grace period elapses.", "FR-DEF-001, FR-DEF-003, FR-DEF-004, CAN §4"],
            ["BR-017", "A payout failure is never hidden", "A failed or held payout must be notified to the recipient and the organizer across push, email and SMS, with a plain-language reason and the next step. Silence on a failed payout is prohibited for every role.", "FR-POUT-002, FR-POUT-007, CAN §8"],
            ["BR-025", "No role edits the ledger", "No role, including super_admin, may edit or delete a ledger entry. Corrections are made only by posting a reversing entry. This is enforced at the data layer.", "FR-ADM-002, G6, CAN §2"],
            ["BR-026", "The fee may not be raised silently", "The 2% fee is locked. Any change is a versioned, effective-dated, audited configuration change, disclosed to every existing member in advance, and never applied retrospectively to a completed or in-flight round.", "FR-ADM-010, 1.9.1"],
            ["BR-027", "No return is ever implied", "An Ajo pays no interest. No product surface, document, notification or marketing asset may state or imply a return, yield, interest, investment or financial gain.", "1.5.2, G8"],
            ["BR-028", "No yield, no lending, no guarantee", "AJO.ng does not lend, does not invest, does not insure and does not guarantee a pot. Expected payouts may not be pledged, assigned or advanced against.", "1.16.3"],
            ["BR-029", "Invitation-only at MVP", "Every Ajo at MVP exists because a named organizer created it and every member accepted an invitation. There is no public marketplace, directory or open participation at launch.", "FR-MEM-002, 1.16.3"],
            ["BR-030", "One identity, one account", "An account is bound to a single verified email and a single verified phone number. Duplicate accounts, duplicate identities and account sharing are prohibited and are grounds for freeze.", "FR-AUTH-002, FR-KYC-001"],
            ["BR-031", "All money is NGN, all values are kobo integers", "Money columns are always bigint kobo, never float or numeric. Amounts are never derived by dividing a total by a count, and rounding is half-up, applied once, at a single defined point.", "NFR-LOC-002, CAN §5"],
            ["BR-032", "Money is only ever moved by two events", "The only money movements are a contribution deposit and a base-pool payout. There is no transfer between members, no top-up, no withdrawal and no refund outside the documented cancellation and reversal paths.", "1.16.3"],
        ],
        "widths": [0.5, 1.35, 3.55, 1.1],
        "size": 7.5,
    },
    {
        "t": "table",
        "head": ["Family", "Count", "Hard product rules", "Governance rules"],
        "rows": [
            ["Enrollment, commitment and membership", "9", "BR-001 to BR-007", "BR-008, BR-009"],
            ["Money, fee and payout", "10", "BR-010 to BR-013, BR-018, BR-020 to BR-024", "—"],
            ["Default, trust and governance", "12", "BR-014 to BR-017", "BR-025 to BR-032"],
            ["Total business rules", "31", "—", "—"],
        ],
        "widths": [2.6, 0.6, 1.9, 1.4],
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Rule numbering",
        "text": (
            "Rule IDs are **stable identifiers assigned by theme** and are intentionally "
            "non-contiguous. A rule that is withdrawn leaves a gap; it does not cause the "
            "remaining rules to be renumbered, because BR- references are already embedded in "
            "148 functional requirements, 38 user stories and the ledger specification. "
            "Renumbering would silently break every cross-reference in the document."
        )
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Two rules that are not yet decided",
        "text": (
            "**Who bears the fee when an Ajo cancels during the 5-day enrollment window.** "
            "BR-001 requires a full refund of contributions, but it does not state whether the "
            "2% fee already collected is also refunded. This is open decision **D-05**, owned "
            "by the Founders and Legal, and it must be resolved before launch because it is a "
            "refund of money already taken. **The interaction between BR-001 and BR-026** (a "
            "cancellation that falls after a fee change takes effect) is also unresolved."
        )
    },

    # ----------------------------------------------------------------- 1.22
    {"t": "h2", "text": "1.22 Assumptions"},
    {
        "t": "p",
        "text": (
            "Every assumption relied on by this document is listed here with the reason it "
            "is believed, the path by which it will be validated, an owner and a point at "
            "which it must be resolved. **An assumption that is not listed here does not "
            "exist.** If the build depends on something not in this table, that is a defect "
            "in this document."
        )
    },
    {
        "t": "table",
        "head": ["ID", "Assumption", "Why we believe it", "Validation path", "Owner", "Resolve by"],
        "rows": [
            [
                "A-01",
                "The recipient of a round receives the base pool (NGN 10,000.00), not the collected total (NGN 10,200.00).",
                "CANONICAL.md D-01 lists the base pool as the assumption used in this specification.",
                "Founder decision, reflected in the terms, the interface and the fee disclosures, tested against the worked example in the user stories.",
                "Founders",
                "Pre-launch",
            ],
            [
                "A-02",
                "A 2% fee is small enough that members will accept it in exchange for a real receipt and a real record.",
                "At a NGN 1,000.00 contribution the fee is NGN 20.00, which is below the cost of one market taxi fare, while the traditional alternative costs a member their entire time and their certainty.",
                "Structured user testing with 20 to 30 target users before launch; monitored through a controlled pilot in month 1.",
                "Founders",
                "Pre-launch and re-tested at 90 days",
            ],
            [
                "A-03",
                "Organisers will adopt if the software takes work off them, not add to it.",
                "The organiser is unpaid and already spends two to three hours per Friday; removing cash handling is unambiguously attractive.",
                "Pilot with 10 to 15 real organisers measuring time per round before and after, not self-reported satisfaction.",
                "Founders",
                "Pilot",
            ],
            [
                "A-04",
                "Members will pay on time at least as often as they do in a traditional Ajo, because the record is visible to everyone.",
                "Social enforcement is stronger when the evidence is shared. This is the core behavioural hypothesis of the product and it is not yet tested.",
                "Controlled pilot measuring on-time payment rate against the members' own prior traditional Ajo, and against a non-observable control where feasible.",
                "Founders",
                "Pilot",
            ],
            [
                "A-05",
                "ProvidusUnity will provide collection and payout services on terms that leave a positive margin at 2% gross.",
                "Completely unverified. No written pricing has been obtained. D-03 is open.",
                "Obtain written pricing; build the full unit economics model; walk away from the fee model entirely if the margin does not survive.",
                "Founders",
                "Pre-launch. **This gates launch.**",
            ],
            [
                "A-06",
                "A compliant and defensible custody path exists that does not require AJO.ng to hold funds as principal.",
                "Assumed to favour the faster path. It is an assumption, not a finding. D-02 is open.",
                "Written opinion from qualified Nigerian counsel, and written confirmation from ProvidusUnity of the arrangement.",
                "Legal and Founders",
                "Pre-launch. **This gates launch.**",
            ],
            [
                "A-07",
                "Target users have or will obtain a smartphone capable of running the app and a means of paying digitally.",
                "Mobile money penetration in Nigeria is high and the target segments are mobile-first by income and occupation.",
                "Device-census onboarding question in the pilot; the low-bandwidth path in NFR-PERF-004 is the mitigation if this proves partly false.",
                "Product",
                "Pilot",
            ],
            [
                "A-08",
                "Naira amounts can be represented in kobo integers with half-up rounding applied once, with no divergence between the ledger, the receipt and the statement.",
                "Standard integer arithmetic; rounding rules are unambiguous if applied at exactly one defined point.",
                "Automated property-based tests over large random amounts and boundary values, plus a fixture that must render identically in export, receipt and statement.",
                "Engineering",
                "Pre-launch",
            ],
            [
                "A-09",
                "The three Year-1 scenarios in section 1.9.3 are a reasonable planning envelope.",
                "They are derived from founder judgement aligned to an existing spreadsheet. They are **not** derived from market research, funnel data or any operating history, because none exists.",
                "Replace with actual cohort data as soon as the first 50 Ajos complete. Treat every figure as a projection until then.",
                "Founders",
                "Reviewed every quarter from first 50 completed Ajos",
            ],
            [
                "A-10",
                "Default rates will stay low enough that no Ajo is routinely stranded by a single default.",
                "Untested. The default rate is unknown for both traditional and digital Ajos because it has never been measured.",
                "Instrument default rate from the first live contribution; revisit the recovery design and the risk thresholds (D-08) as data arrives.",
                "Risk",
                "Reviewed at 30, 60 and 90 days",
            ],
            [
                "A-11",
                "Diaspora demand is real, urgent and large enough to matter, but it is not required for the Year-1 case.",
                "The need is evidenced by the persona work and by the frequency of the complaint in the founder's networks, but it is anecdotal.",
                "Structured interviews with diaspora users. Until then, international participation stays out of scope and the segmentation is not claimed as sized.",
                "Founders",
                "Post-MVP review",
            ],
            [
                "A-12",
                "Ajo.ng is a facilitator and record-keeper, not a party to the savings arrangement between members.",
                "This is the only structure that keeps the product's obligations smaller than its promises. It also avoids implying a guarantee.",
                "Legal review of the terms and of the organizer and member onboarding copy before launch.",
                "Legal and Founders",
                "Pre-launch",
            ],
            [
                "A-13",
                "Members will accept a 5-day enrollment window as reasonable.",
                "The window is short but finite, and it prevents an organizer from holding an incomplete Ajo indefinitely. No user has yet tested the boundary.",
                "Usability test of the countdown and the cancellation-and-refund explanation with 10 users; revise the window only via a versioned business rule change.",
                "Product",
                "Pre-launch",
            ],
            [
                "A-14",
                "Two notifications per round is the right volume for the silent majority member.",
                "Derived from the Chidi persona and from the notification catalogue in CANONICAL.md, not from behavioural data.",
                "Notification opt-out and uninstall rate monitoring during the pilot, segmented by member activity.",
                "Product",
                "Pilot",
            ],
        ],
        "widths": [0.35, 1.65, 1.65, 1.6, 0.55, 0.72],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "Two assumptions gate launch",
        "text": (
            "**A-05 and A-06 gate launch, not growth.** If the 2% fee does not leave a "
            "sustainable margin after provider charges, or if no defensible custody path exists, "
            "then the fee model or the product model must change, and that is a decision to "
            "take deliberately and early rather than to discover after members have been "
            "onboarded. Both are open decisions **D-02** and **D-03** in CANONICAL.md."
        )
    },

    # ----------------------------------------------------------------- 1.23
    {"t": "h2", "text": "1.23 Dependencies"},
    {
        "t": "p",
        "text": (
            "Dependencies are things outside the product's control that the product cannot "
            "work without, or works worse without. A dependency with no owner is a risk, not "
            "a dependency."
        )
    },
    {
        "t": "table",
        "head": ["ID", "Dependency", "Type", "Needed for", "Owner", "Status"],
        "rows": [
            ["DEP-01", "ProvidusUnity, as payment and collection partner", "External, commercial", "Collection, payout, reconciliation, the entire money path", "Founders", "Not contracted. **This is the largest single dependency in the product.**"],
            ["DEP-02", "ProvidusUnity written pricing and SLA", "External, commercial", "Unit economics (BO3), publicising the 2% fee, NFR-PERF-003", "Founders", "Not obtained. Open decision D-03."],
            ["DEP-03", "ProvidusUnity confirmation of the custody arrangement", "External, regulatory", "Licensing path, BR-022, whether AJO.ng ever holds funds", "Legal and Founders", "Unresolved. Open decision D-02. **Gates launch.**"],
            ["DEP-04", "Identity verification providers for BVN and CAC", "External, technical", "FR-KYC-001, FR-KYC-002, D-04", "Engineering and Risk", "Not selected"],
            ["DEP-05", "SMS gateway and short-code registration", "External, technical", "The SMS channel for money-critical and security events, which is the only channel some members will reliably receive", "Engineering", "Not selected. Short-code registration in Nigeria requires regulatory process and cannot be compressed."],
            ["DEP-06", "Push notification service", "External, technical", "FR-NOTIF-001 across push", "Engineering", "Not selected"],
            ["DEP-07", "Email delivery service with domain authentication", "External, technical", "Verification, receipts, statements, security alerts", "Engineering", "Not selected"],
            ["DEP-08", "Qualified Nigerian legal counsel", "External, professional", "Terms, role descriptions, organizer liability wording, data protection, licensing", "Founders", "Not engaged. **Gates launch.**"],
            ["DEP-09", "Qualified Nigerian tax adviser", "External, professional", "Whether the 2% fee is tax-inclusive and who remits VAT or WHT", "Founders", "Not engaged. Open decision D-06."],
            ["DEP-10", "Cloud hosting, database and object storage", "External, technical", "Everything. Includes the immutability guarantee for the ledger and backups.", "Engineering", "Not selected"],
            ["DEP-11", "Internal fraud and risk operations capacity", "Internal, people", "FR-ADM-005, FR-ADM-006, the review of every risk decision", "Operations", "Not established. A `risk_officer` role with no human behind it is worse than no role."],
            ["DEP-12", "Internal support capacity", "Internal, people", "FR-ADM-004, dispute assistance, FR-SEC-005 account unlock", "Operations", "Not established. A support function that cannot act is a queue, not a service."],
            ["DEP-13", "Organiser recruitment in the first market cluster", "Internal, people", "Distribution. Ajo.ng has no marketing channel that works as well as one organiser with fifty members.", "Founders", "Not started"],
            ["DEP-14", "Brand and design system", "Internal", "Consistency, accessibility (NFR-ACC-001 to 005), and the fee disclosure being unmistakable on every surface", "Product", "Brand palette fixed in CANONICAL.md; system not built"],
            ["DEP-15", "Reconciliation and ledger invariant tooling", "Internal", "NFR-AUD-005, NFR-AUD-006, BR-013, BR-020. Without it the solvency assertion is an aspiration.", "Engineering", "Not built. This is a build dependency, not a vendor one, and it is on the critical path."],
        ],
        "widths": [0.5, 1.6, 0.85, 1.65, 0.65, 1.25],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The dependency shape",
        "text": (
            "Four of the fifteen dependencies (**DEP-03, DEP-08, DEP-09 and DEP-11**) are "
            "people, not platforms, and three of those gate launch. The common failure mode for "
            "a pre-launch product of this kind is to complete the engineering on schedule "
            "while the counsel, the tax position and the risk operations capacity are still "
            "unresolved, and then to discover that the product cannot legally or safely launch "
            "as built. These are not the boring dependencies. They are the critical path."
        )
    },

    # ----------------------------------------------------------------- 1.24
    {"t": "h2", "text": "1.24 Constraints"},
    {
        "t": "table",
        "head": ["ID", "Constraint", "Type", "Consequence", "Can it be relaxed?"],
        "rows": [
            ["C-01", "The 2% fee is locked and may not be raised without renegotiating trust", "Commercial", "Revenue is capped at 2% of contribution volume. If costs rise, margin falls. There is no pricing lever.", "No, not for Year 1. BR-026 governs any future change."],
            ["C-02", "The recipient receives the base pool and the fee never reduces a payout", "Product", "Gross revenue is capped at 2% and cannot be increased by taking a cut of the pot, which is the obvious pricing alternative.", "No. This is the product's central promise."],
            ["C-03", "An Ajo pays zero interest and no return is ever implied", "Product", "There is no financial return to offer a member. Growth must come from discipline, record and convenience, never from yield.", "No"],
            ["C-04", "Invitation-only at MVP", "Product", "Growth is bounded by organiser invitation networks. No marketplace flywheel. Acquisition is slower and harder to scale.", "Yes, by a formal scope change (section 1.16.3) with a full re-review"],
            ["C-05", "No role may edit or delete a ledger entry, including super_admin", "Technical and governance", "Corrections require reversing entries, which is more expensive to build and more expensive to operate than an update.", "No. G6 and BR-025."],
            ["C-06", "Complete-cycle commitment and no unilateral exit", "Product", "A member in genuine financial difficulty cannot simply leave. A formal, moderated replacement process is required and must be humane.", "No, but the process must be designed to be fast and non-punitive"],
            ["C-07", "MVP members are Nigerian residents transacting in NGN", "Regulatory and commercial", "Excludes Kemi and the entire diaspora market, which is a large part of the addressable opportunity.", "No, until D-02 is resolved and a full scope re-review is completed"],
            ["C-08", "ProvidusUnity is the sole payment partner at launch", "Technical", "Single point of failure. No failover provider exists, and switching cost rises with volume.", "Not at launch. A second provider is a post-MVP objective (NFR-AVL-004)"],
            ["C-09", "Money is always bigint kobo; never float or numeric", "Technical", "Legacy migration from any float-based system would require a conversion and reconciliation exercise.", "No. BR-031."],
            ["C-10", "Defaulting is private and members are never publicly exposed", "Product and ethical", "Social pressure cannot be used as a platform mechanism, which removes a powerful but unacceptable lever.", "No. BR-014 and G5"],
            ["C-11", "The platform must never use corporate funds to cover a shortfall", "Financial", "A margin-diluting event becomes a reputational catastrophe. There is no cushion.", "No. BR-018"],
            ["C-12", "Provider costs are unknown until written pricing is obtained", "Financial", "The financial model cannot be finalised and the fee cannot responsibly be publicised.", "Resolvable. D-03. **Gates launch.**"],
            ["C-13", "The Ajo is a monthly or market-cycle product, and participation is periodic", "Product", "Engagement is inherently intermittent, which makes daily-active metrics the wrong measure and makes notification fatigue the primary UX risk.", "Partially. Frequency flexibility is a post-MVP candidate"],
            ["C-14", "Core flows must work on low-end Android over 3G", "Technical", "Constrains component choice, media strategy and interaction design throughout.", "No. G7. It is the device the users actually have."],
            ["C-15", "No return, guarantee, insurance or investment may be offered or implied", "Regulatory and ethical", "Removes every high-margin adjacent revenue line. Monetisation is limited to the 2% fee at MVP.", "No. BR-027, BR-028"],
        ],
        "widths": [0.45, 1.75, 0.85, 2.05, 1.4],
        "size": 7.3,
    },

    # ----------------------------------------------------------------- 1.25
    {"t": "h2", "text": "1.25 Risks"},
    {
        "t": "p",
        "text": (
            "Likelihood and impact are assessed on a High / Medium / Low scale before any "
            "operating data exists, and are **judgements, not measurements**. They must be "
            "re-scored after the first 50 completed Ajos. The scale is deliberately blunt: a "
            "risk rated High in either column requires a named owner and a review at every "
            "monthly product review until it falls."
        )
    },
    {
        "t": "table",
        "head": ["ID", "Risk", "Likelihood", "Impact", "Mitigation", "Owner"],
        "rows": [
            [
                "R1",
                "Trust collapse from a failed or under-funded payout. A member is owed NGN 10,000.00 and does not receive it, or receives it late, and the story spreads through every WhatsApp group in the market.",
                "Medium",
                "Severe",
                "Payout funding principle (BR-018) forbids under-payment absolutely; escrow solvency assertion (BR-020) runs before every release; HELD state with mandatory notification to recipient and organizer (BR-017); a defined recovery process rather than improvisation; pilot gates on completing 10 Ajos end to end before any scale-up. Frequency of held payouts is a monitored metric (1.27).",
                "Founders",
            ],
            [
                "R2",
                "Regulatory misclassification. The activity is treated as an unlicensed deposit-taking or money-transfer operation, or a licensing requirement is discovered after launch.",
                "Medium",
                "Severe",
                "D-02 resolved in writing by qualified Nigerian counsel **before** the first live contribution; the architecture keeps AJO.ng's custody exposure as low as the arrangement permits; the product contains no lending, no yield, no guarantee and no member-to-member transfer, which materially narrows the surface; a documented legal review gate in the launch checklist.",
                "Legal and Founders",
            ],
            [
                "R3",
                "Unit economics fail. Provider collection and payout charges consume most or all of the 2% gross fee, so the business is loss-making at scale.",
                "Medium",
                "High",
                "Written pricing obtained before the fee is publicised (D-03); a full cost model built before launch; the decision to abandon the fee model taken deliberately and early rather than discovered late; monthly gross-to-net reporting; the fee never being raised on existing members (BR-026), so the model must work at 2% or not at all.",
                "Founders",
            ],
            [
                "R4",
                "Fraud and default. A member joins with false identity, takes a position, collects the pot and disappears, or enlises accomplices to farm invited Ajos.",
                "Medium",
                "High",
                "BVN or CAC verification above a configurable threshold (D-04); contribution and Ajo size caps (D-08); position and reordering controls; risk event monitoring; freeze capability for `risk_officer`; default detection at the grace boundary; the append-only ledger making concealment materially harder; limits reviewed at 30, 60 and 90 days.",
                "Risk",
            ],
            [
                "R5",
                "Provider dependency. ProvidusUnity raises prices, changes terms, degrades, fails, or exits, and there is no second provider.",
                "Medium",
                "High",
                "All provider interaction behind a documented adapter interface; webhook idempotency and replay protection; reconciliation runs that recover state from any outage; the escrow solvency assertion independent of the provider; a second provider treated as a post-MVP objective rather than claimed as existing (NFR-AVL-004); no provider capability asserted as fact anywhere in this document.",
                "Engineering and Founders",
            ],
            [
                "R6",
                "Low frequency kills retention. An Ajo is a monthly or market-cycle event, so the product is opened rarely, and Chidi uninstalls because he is notified about something he has already handled.",
                "High",
                "High",
                "Notification policy: two notifications per round, SMS reserved for money-critical and security events only (BR-014 family, FR-NOTIF-003); notification preferences as a first-class feature with an unsubscribe; success measured on completed cycles and repeat participation, not on daily actives; retention measured as second-Ajo participation (KPI K-09).",
                "Product",
            ],
            [
                "R7",
                "Competition from WhatsApp. Members conclude that the free group they already have is good enough and the 2% fee is not worth paying.",
                "High",
                "Medium",
                "Positioning on the things WhatsApp structurally cannot do: an immutable ledger, receipts, a locked schedule, escrow solvency, evidence-based disputes and a durable statement. Organisers onboarded with the time saved made explicit. The pilot must produce a measurable before-and-after on organiser time, because that is the argument that converts, not the feature list.",
                "Founders and Product",
            ],
            [
                "R8",
                "Organiser abandonment. Organisers stop because the product makes their job harder, not easier, and Ajos die with them.",
                "Medium",
                "High",
                "Organiser console as a first-class surface (F20); reminders handled by software rather than by hand (FR-MEM-004); organiser delegation (FR-AJO-012); the time-saved hypothesis tested directly in the pilot (A-03) before scale; Ajo dormancy detection and outreach as a retention feature.",
                "Product",
            ],
            [
                "R9",
                "Fee shock at scale. A member discovers the 2% at the moment of payment despite disclosure, and reacts as though AJO.ng stole from the pool.",
                "Low",
                "High",
                "Mandatory pre-commitment disclosure on the invitation, the join confirmation and the Ajo details screen (BR-011, FR-INV-002, FR-JOIN-003); itemised receipts; the base pool stated explicitly in the worked example; a UI test that fails if the fee is not rendered as a separate line on any money screen.",
                "Product",
            ],
            [
                "R10",
                "Data protection breach or unlawful processing of identity data.",
                "Low",
                "Severe",
                "Raw BVN and CAC identifiers never stored (FR-KYC-001, FR-KYC-002); data minimisation; explicit lawful-basis and retention review by counsel before launch; a user-facing data export and deletion mechanism; audit of every privileged data access; incident response plan owned and rehearsed.",
                "Engineering and Legal",
            ],
            [
                "R11",
                "Key-person dependency on the founders. Product, relationships and domain knowledge sit with two people, and a disruption stops the company.",
                "Medium",
                "High",
                "This specification document is itself a mitigation: the rules, states, fee model and constraints are written down rather than held in memory. Documented decision records. Successor organisers and operators trained during the pilot rather than after it.",
                "Founders",
            ],
            [
                "R12",
                "Organisers misuse the platform. A commercial organiser runs many Ajos, solicits participation for a fee, or becomes a de facto sub-platform.",
                "Medium",
                "Medium",
                "Per-organizer Ajo and volume limits (D-08); monitoring of organiser concentration and default rates; terms prohibiting solicitation for gain, reviewed by counsel; freeze capability; rate limits on invitations (FR-INV-005).",
                "Risk",
            ],
            [
                "R13",
                "Support and risk roles are staffed on paper only, so a freeze, an unlock or a dispute cannot actually be actioned by a human.",
                "Medium",
                "High",
                "Role definitions that separate reading from moving money are worthless without staffed humans; staffing and runbook requirements stated as launch gates in DEP-11 and DEP-12; escalation paths defined before launch; measured response-time targets once live.",
                "Operations",
            ],
            [
                "R14",
                "Ledger or solvency defects. A bug, a race or a partial failure produces an unbalanced ledger, a false balance, or a disbursement against an unraised liability.",
                "Low",
                "Severe",
                "Every transaction balances to zero or is rejected (BR-013); the recognition sequence is mandatory and ordered (BR-021); the solvency assertion is not bypassable by any role (BR-020); ledger tables are append-only with no update or delete path (BR-025); daily reconciliation against provider settlements (NFR-AUD-005); automated invariant checks on every write path, with any exception raising a risk event that cannot be silently closed.",
                "Engineering",
            ],
        ],
        "widths": [0.35, 1.6, 0.6, 0.55, 2.5, 0.6],
        "size": 7.0,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The compounding risk",
        "text": (
            "R1, R3, R7 and R8 are the same failure seen from four sides: a member is not "
            "paid on time, the margin does not cover the recovery, the group concludes WhatsApp "
            "was right all along, and the organiser quietly stops using the product. They are "
            "sequenced deliberately. R1 is managed first, without exception, because it is the "
            "only one that can end the business in a single event rather than degrade it "
            "gradually."
        )
    },

    # ----------------------------------------------------------------- 1.26
    {"t": "h2", "text": "1.26 Success metrics"},
    {
        "t": "p",
        "text": (
            "Success for AJO.ng is not transaction volume. It is **Ajos that complete "
            "correctly and members who come back**. The metrics below are chosen so that the "
            "easiest thing to inflate is the thing that matters least."
        )
    },
    {"t": "h3", "text": "1.26.1 What success means, in order of importance"},
    {
        "t": "numbers",
        "items": [
            "Zero under-funded, reduced or fabricated payouts. A single one is a reputational "
            "event that outweighs a year of good numbers.",
            "Ajo completion rate. An Ajo that reaches COMPLETED with every position filled is "
            "the unit of value. Anything else is unfinished work.",
            "On-time payment rate. The product's behavioural claim is that visibility improves "
            "payment discipline. If it does not, the core hypothesis has failed.",
            "Repeat participation. A member who starts or joins a second Ajo within 90 days "
            "has demonstrated that the product is worth keeping, which is the only durable "
            "signal available.",
            "Organiser retention. An organiser still running Ajos at 90 days has proven the "
            "product saves them time rather than adding to their week.",
            "Dispute rate and resolution time. Low disputes and fast resolution mean the record "
            "is doing its job.",
            "Fee revenue. Real, and deliberately last.",
        ],
    },
    {"t": "h3", "text": "1.26.2 Staged success gates"},
    {
        "t": "table",
        "head": ["Gate", "When", "Criteria to pass", "Consequence of failure"],
        "rows": [
            [
                "G-A. Ready",
                "Pre-launch",
                "D-02, D-03, D-04, D-06 and D-08 resolved. Written legal opinion obtained. Provider contracted with written pricing and SLA. Support and risk staffed with runbooks. Ledger invariants automated and passing. No failed payout in 10 consecutive end-to-end pilot Ajos.",
                "Do not launch. No amount of engineering readiness substitutes for this gate.",
            ],
            [
                "G-B. First 10 Ajos",
                "Month 1",
                "10 Ajos complete end to end with zero reduced payouts, zero unreconciled ledger exceptions, and a receipt issued for every movement.",
                "Halt onboarding. Diagnose before adding any further Ajos.",
            ],
            [
                "G-C. First 50 Ajos",
                "Month 3",
                "Completion rate at or above the target in 1.27, on-time payment at or above target, dispute rate below target, at least 20% of completing members engaged with a second Ajo.",
                "Reassess the behavioural hypothesis (A-04) and the recovery design before scaling acquisition.",
            ],
            [
                "G-D. Unit economics proven",
                "Month 6",
                "Actual provider charges received and modelled. Gross-to-net margin per Ajo positive on real data. The Year-1 model replaced by actuals.",
                "Change the model deliberately, or stop. Do not continue acquiring volume on a negative margin.",
            ],
            [
                "G-E. Scale ready",
                "Month 12",
                "300 Ajos at base case, organiser retention at or above target, support load within staffing capacity, no unresolved Sev-1 incidents.",
                "Extend the timeline. Do not take growth capital to solve an operational problem.",
            ],
        ],
        "widths": [1.05, 0.65, 2.85, 2.0],
        "size": 7.5,
    },

    # ----------------------------------------------------------------- 1.27
    {"t": "h2", "text": "1.27 Key performance indicators"},
    {
        "t": "p",
        "text": (
            "Every target below is labelled as either a **Gate** (a condition that must hold), a "
            "**Projection** (a modelled expectation with no data behind it), or a "
            "**Direction** (a metric that must move the right way, with no number attached "
            "until data exists). No figure in this table is a measurement. **The platform has "
            "no live transactions and no customers.**"
        )
    },
    {
        "t": "table",
        "head": ["ID", "Metric", "Definition", "Target", "Measurement source"],
        "rows": [
            ["K-01", "Under-funded payouts", "Count of payouts released for less than the base pool, or released without sufficient escrow", "Zero. Absolute. No tolerance.", "Ledger; payout records; escrow solvency assertion log"],
            ["K-02", "Ajo completion rate", "Ajos reaching COMPLETED with every position filled, divided by Ajos activated", "Gate: 90% by month 6, 95% by month 12", "Ajo state machine records"],
            ["K-03", "On-time payment rate", "Contributions marked PAID on or before the due time, divided by contributions due", "Projection: 85% at month 3, 90% by month 12", "contributions table, states vs due dates"],
            ["K-04", "Cancellations during enrollment", "Ajos cancelling in the 5-day window, divided by Ajos that opened enrollment", "Direction: falling over time as organiser quality improves. No numeric target until month 3.", "Ajo state transitions with reason recorded"],
            ["K-05", "Default rate", "Contributions reaching DEFAULTED, divided by contributions due, at 30, 60 and 90 days", "Projection: below 3% at 60 days", "contributions and risk_events"],
            ["K-06", "Fee revenue", "Sum of fees_income posted, by period", "Projection, from 1.9.3: NGN 1,800,000 to NGN 17,280,000 in Year 1 depending on scenario", "fees table and the financial report in FR-ADM-009"],
            ["K-07", "Contribution volume", "Sum of net contributions received, by period", "Projection, from 1.9.3: NGN 90,000,000 to NGN 864,000,000 in Year 1", "ledger, contribution.received postings"],
            ["K-08", "Gross-to-net margin", "Fee revenue less provider collection and payout charges, divided by fee revenue", "Gate: positive by month 6 on real provider pricing. Currently **uncomputable**: D-03 is open.", "Provider settlement reports against the ledger (FR-PAY-009)"],
            ["K-09", "Repeat participation", "Members who start or join a further Ajo within 90 days of completing one, divided by completing members", "Projection: at least 40%", "user and ajo_members records"],
            ["K-10", "Organiser retention", "Organizers who run at least one Ajo in the three months after their first, divided by organisers active in the first month", "Projection: 60% at 90 days", "ajos grouped by organizer"],
            ["K-11", "Organiser time per round", "Median self-reported or measured minutes an organizer spends per round", "Direction: materially below the 2 to 3 hours of a traditional Friday. Measured directly in the pilot (A-03).", "Pilot time study, then organizer survey"],
            ["K-12", "Dispute rate", "Disputes raised per 100 Ajos per month", "Projection: below 5 per 100 Ajos per month by month 6", "disputes table"],
            ["K-13", "Dispute resolution time", "Median hours from dispute opened to resolved, excluding member-response time", "Target: under 72 hours, once support is staffed", "disputes table with timestamps"],
            ["K-14", "Held payout rate", "Payouts entering HELD for insufficient funding, divided by payouts due", "Gate: zero at month 3, sustained", "payouts table state transitions"],
            ["K-15", "Reconciliation exceptions", "Unmatched items found by scheduled reconciliation runs, divided by transactions", "Gate: zero unexplained at month 1, zero total by month 3", "reconciliation_runs (FR-ADM-011)"],
            ["K-16", "Ledger balance invariant", "Transactions failing to balance to zero, across all write paths", "Zero. Absolute. Any non-zero value is a Sev-1.", "Automated invariant check on every write path (NFR-AUD-006)"],
            ["K-17", "Contribution success rate", "Payments reaching SUCCESS on first attempt, divided by payment initiations", "Projection: above 90%", "payments table state transitions"],
            ["K-18", "P95 API latency", "95th percentile server response time on read endpoints", "Target: under 300 ms (NFR-PERF-001)", "Application monitoring"],
            ["K-19", "Availability", "Monthly uptime of the member-facing application and of the money paths, measured separately", "Target: 99.5% and 99.0% (NFR-AVL-001, NFR-AVL-002)", "External synthetic monitoring"],
            ["K-20", "Notification opt-out rate", "Users who disable push or email for a non-mandatory category", "Direction: monitored, no target until month 3. A high rate indicates notification fatigue (R6).", "notification_preferences"],
            ["K-21", "Verification failure rate", "Identity verifications failing, by check type", "Direction: monitored, with the failure reason distribution reviewed as an onboarding quality signal", "verification_checks (FR-KYC-003)"],
            ["K-22", "Ajo sizes and mix", "Distribution of Ajos by size and by contribution band", "No target. Diagnostic metric used to test whether the segmentation in 1.10 holds.", "ajos table"],
            ["K-23", "Acquisition source", "Where new members and new organisers came from", "No target. The hypothesis under test is that organiser referral dominates, and WhatsApp sharing is the mechanism (R7).", "Invitation records and referral attribution"],
            ["K-24", "Support contact rate", "Support contacts per 100 active members per month", "No target until staffing is measured. Used to size the support function (DEP-12).", "Support ticketing"],
        ],
        "widths": [0.45, 1.35, 1.85, 1.65, 1.2],
        "size": 7.2,
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "On the projections",
        "text": (
            "The Year-1 figures in 1.9.3 and every target marked **Projection** above are derived "
            "from founder judgement and a spreadsheet, not from a funnel, a cohort or an "
            "operating history. They exist to size the operation and to make the assumptions "
            "explicit and arguable. **They must be presented to any investor as projections, "
            "and must be replaced with actuals as soon as the first 50 Ajos complete.** "
            "Presenting a projection as a forecast would be a misrepresentation of the kind "
            "this product exists to eliminate."
        )
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The metric that matters most is the one that cannot be faked",
        "text": (
            "K-01 and K-16 have absolute zero targets and cannot be improved, only maintained. "
            "Every other metric can be made to look better by growing faster. A platform that "
            "reports volume prominently and these two quietly is reporting the wrong product. "
            "Both should appear on the first slide of any internal or external reporting, "
            "whatever else is included."
        )
    },

    # ----------------------------------------------------------------- 1.28
    {"t": "h2", "text": "1.28 Future roadmap"},
    {
        "t": "p",
        "text": (
            "The roadmap below is a **direction of travel, not a commitment**. No dates are "
            "given, because no date can honestly be given for anything downstream of D-02, "
            "D-03 and the engagement of counsel. Items are gated on evidence, not on dates."
        )
    },
    {
        "t": "table",
        "head": ["Phase", "Focus", "What is built", "Exit criterion to move on"],
        "rows": [
            [
                "Phase 0. Foundational",
                "Make it lawful and make it solvent",
                "ProvidusUnity contracted with written pricing and a custody arrangement. Counsel and tax adviser engaged and D-02, D-03, D-04, D-05, D-06, D-07 and D-08 resolved. Support and risk staffed with runbooks. Ledger invariants automated and green.",
                "All open decisions closed in writing. 10 end-to-end pilot Ajos complete with zero reduced payouts.",
            ],
            [
                "Phase 1. MVP launch",
                "The product in section 1.17, invitation-only",
                "Registration, profile, verification, Ajo creation and settings, invitations, joining, membership, schedules, collection, tracking, payouts, history, notifications, disputes, defaults, admin. The full 2% fee model with complete disclosure.",
                "Gate G-B passed: 10 Ajos complete, zero unreconciled exceptions, a receipt for every movement.",
            ],
            [
                "Phase 2. Prove it works",
                "Behaviour and economics, not features",
                "No new features. Instrument everything. Complete 50 Ajos. Replace the Year-1 model with actuals. Build the dispute and recovery playbook from real cases. Test frequency and retention assumptions.",
                "Gates G-C and G-D passed: completion and on-time payment at target, and a positive gross-to-net margin on real provider pricing.",
            ],
            [
                "Phase 3. Density",
                "Own a small number of clusters completely",
                "Organiser onboarding programme. Referred invitations. Statements fit for banks and third parties. Organiser console deepened. SMS and low-bandwidth paths hardened. Ajo templates drawn from real market practice.",
                "300 Ajos at base case, organiser retention at target, support load inside staffing capacity.",
            ],
            [
                "Phase 4. Reach",
                "Widen who can participate",
                "Referred membership beyond personal networks. Second payment provider for failover. Frequency expansion. Native apps if and only if the progressive web app is genuinely insufficient. Full re-review of section 1.16.3 before any of it.",
                "Provider failover proven in a chaos test, and the scope re-review completed and signed off.",
            ],
            [
                "Phase 5. Adjacent, subject to full review",
                "Only if the core is proven and lawful",
                "Diaspora and international participation, subject to D-02 and a licensing review. Credit or lending is **not** on this line and is not anticipated; it is excluded in section 1.16.3. Possible: richer financial history, integration with formal savings products, organisation-level arrangements.",
                "Each item independently reviewed against section 1.16.3, the risk table in 1.25 and the business rules in 1.21. Nothing on this line is a commitment.",
            ],
        ],
        "widths": [0.95, 1.1, 2.6, 1.85],
        "size": 7.4,
    },
    {"t": "h3", "text": "1.28.1 What is deliberately not on this roadmap"},
    {
        "t": "bullets",
        "items": [
            "A public Ajo marketplace. It is the most requested and the most dangerous item, and it stays out until the core is proven and the fraud model is understood.",
            "Any credit or lending product, in any form, including a softer variant such as a payout advance. Excluded permanently unless the position is consciously revisited, and BR-028 governs until then.",
            "Yield, interest, savings returns or any investment product. An Ajo pays zero return and always will.",
            "Insurance, protection or guarantee products. AJO.ng cannot underwrite a risk it does not control.",
            "Cryptocurrency and stablecoins of any kind.",
        ],
    },
    {
        "t": "h3", "text": "1.28.2 The one-line version"},
    {
        "t": "p",
        "text": (
            "**Make it lawful, make it solvent, then make it work, then make it dense, then "
            "widen it, and never build a lending company on top of it.** Every phase above is "
            "gated on evidence rather than on a date, and the first phase is the one that "
            "decides whether there is a second phase."
        )
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Traceability",
        "text": (
            "This document is the product baseline for AJO.ng. Section 1 defines what the "
            "product is and the rules it obeys; the state-machine, entity, API, security, data, "
            "financial and operational sections that follow define how it is built. Where any "
            "later section conflicts with this one, **CANONICAL.md wins, and this section is "
            "wrong and must be corrected rather than reconciled.**"
        )
    },
]
