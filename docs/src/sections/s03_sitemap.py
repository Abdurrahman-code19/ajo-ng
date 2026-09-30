"""
Section 3 — Sitemap and Information Architecture.

Source of truth: docs/src/CANONICAL.md
Authoring contract: docs/src/AUTHORING.md
Cross-references: section 1 (business rules BR-001 to BR-032), section 2
(user flows and the screen-ID key `SCR-MKT`/`SCR-APP`/`SCR-ADM`), section 5
(information architecture traceability), section 6 (wireframes), section 7
(high-fidelity UI), section 13 (security), section 18 (analytics).

The three tiers used throughout this section are the same three tiers as the
canonical screen inventory in CANONICAL.md section 7: **public marketing
website**, **authenticated application**, **admin console**. The screen
identifiers used here are `SCR-WEB-nn` (tier 1), `SCR-MOB-nn` (tier 2) and
`SCR-ADM-nn` (tier 3). Section 2.0.1 publishes a parallel key built on
`SCR-MKT-nn` / `SCR-APP-nn` / `SCR-ADM-nn`; the reconciliation table in 3.6.4
maps one to the other so that the two sections can be read together without
either being wrong.

The 2% platform fee is quoted exactly as CANONICAL.md defines it: a member
owing NGN 1,000.00 is charged NGN 1,020.00; the fee is NGN 20.00; the
recipient of a ten-member round receives the base pool NGN 10,000.00, never
NGN 10,200.00. Every route in this section that can commit a member to a
payment is marked as a fee-disclosure surface.

The tagline is "Your Ajo. Your Story."
"""

BLOCKS = [
    {"t": "h1", "text": "3. Sitemap and Information Architecture"},

    {
        "t": "lead",
        "text": (
            "This section fixes the shape of AJO.ng: what pages exist, which of them a "
            "person may see, how they are reached, how they are named, and where the line "
            "between public and private is drawn in the URL. It is the contract between "
            "the product design in sections 6 and 7, the flows in section 2, the API in "
            "CANONICAL.md section 6 and the routes that will actually be registered in the "
            "router. Nothing here is a suggestion. A route that does not appear in the "
            "inventory in 3.6 does not exist, and a screen that is not reachable from one "
            "of the entry points in 3.9 is dead code."
        )
    },
    {
        "t": "p",
        "text": (
            "**Reading convention.** `SCR-WEB-nn` is a tier-1 public marketing screen, "
            "`SCR-MOB-nn` is a tier-2 authenticated application screen, `SCR-ADM-nn` is a "
            "tier-3 admin console screen. `BR-nnn` is a business rule in section 1. "
            "`C-nn` is a constraint in CANONICAL.md. `D-nn` is an open decision in "
            "CANONICAL.md section 9. `A-nn` is an assumption in section 1.22. `NFR-*` is a "
            "non-functional requirement in section 1.18. Money is written `NGN 1,000.00` "
            "in tables, never with a naira glyph."
        )
    },

    # =================================================================== 3.1
    {"t": "h2", "text": "3.1 Principles"},
    {
        "t": "p",
        "text": (
            "Five principles decide every structural question in this section. Where two "
            "of them pull against each other, the order below is the tie-break order."
        )
    },
    {
        "t": "numbers",
        "items": [
            "**Three tiers, no fourth.** Public marketing, authenticated application, "
            "admin console. Each tier has its own host path, its own authentication "
            "posture, its own navigation model, its own indexability policy and its own "
            "support story. A fourth tier (a partner or B2B surface) is out of scope for "
            "MVP and is deliberately not reserved for.",
            "**The tier boundary is also the trust boundary.** Tier 1 makes no claim about "
            "any individual. Tier 2 makes claims about the signed-in member only. Tier 3 "
            "reads across all Ajos under role control. No screen in tier 2 may read "
            "another member's data; no screen in tier 1 may require an account to be "
            "useful; no screen in tier 3 may move money (CANONICAL.md section 2, role "
            "`support` cannot move money; `risk_officer` cannot move money; only "
            "`super_admin` can initiate a payout and even then not by editing the ledger).",
            "**Authenticate at the edge, not per screen.** Tier 2 and tier 3 route guards "
            "run before render. An unauthenticated request to `/app/**` redirects to "
            "`/login?returnTo=<encoded path>`; an authenticated request for which the "
            "role is insufficient returns the role-denied screen (SCR-ADM-13), never the "
            "not-found screen, so that a person is not misled about their own access.",
            "**Depth is capped at three levels.** Tier 2 is `/app/<resource>/<resource>`. "
            "Beyond that the user navigates by filter, tab and in-page state rather than "
            "by path. This keeps every URL copyable, every breadcrumb two items deep, and "
            "every deep link survivable across a redesign.",
            "**One primary action per screen.** Every screen has at most one element that "
            "is styled as a primary action. Where a screen has two real actions, one of "
            "them is a navigation link, not a button. This is the structural expression of "
            "the no-dark-pattern rule in 7.1 and it is a hard constraint, not a style "
            "preference.",
        ],
    },
    {"t": "h3", "text": "3.1.1 Tier characteristics"},
    {
        "t": "table",
        "head": [
            "Attribute",
            "Tier 1 — Public website",
            "Tier 2 — Authenticated app",
            "Tier 3 — Admin console",
        ],
        "rows": [
            ["Path root", "`/`", "`/app`", "`/admin`"],
            [
                "Authentication",
                "None. A session, if present, is ignored for content selection.",
                "Required. Bearer/cookie session with refresh.",
                "Required **plus** an admin role assertion. Re-authentication within a "
                "15-minute window for destructive actions.",
            ],
            [
                "Roles served",
                "Anonymous",
                "`user`, `ajo_organizer`, `ajo_member`",
                "`support`, `risk_officer`, `super_admin`",
            ],
            [
                "Indexing",
                "Indexed. Listed in `sitemap.xml`.",
                "`noindex, nofollow` on every route, enforced by response header.",
                "`noindex, nofollow`, plus `robots.txt` disallow and edge-IP allowlist.",
            ],
            [
                "Navigation model",
                "Horizontal top nav, 8 items maximum, footer sitemap.",
                "Desktop: left rail plus top bar. Mobile: 5-tab bottom bar.",
                "Fixed left rail, 9 items, no bottom bar, no marketing chrome.",
            ],
            [
                "Session lifetime",
                "None",
                "Sliding 30-day refresh, absolute 12-month",
                "30-minute idle timeout, absolute 12-hour",
            ],
            [
                "Data in URLs",
                "None",
                "Opaque ULIDs and enums only. **Never** a name, phone, email, BVN or "
                "amount.",
                "Opaque ULIDs only. Search filters travel in the query string.",
            ],
            [
                "Fee disclosure duty",
                "Static explanation on `/fees` and `/how-it-works`",
                "Mandatory, itemised, on every money-moving screen (BR-010, BR-011)",
                "Read-only mirror of `fees_income`; no configuration (D-06 open)",
            ],
            [
                "Error treatment",
                "404 with a link home",
                "In-app error boundary (SCR-MOB-26) with retry and reference ID",
                "Role-denied (SCR-ADM-13) or 404; never a bare 500",
            ],
            [
                "Analytics",
                "Page views, section engagement, signup funnel",
                "Product events, **no** PII in event properties (NFR-SEC-020)",
                "Audit event only; admin sessions are themselves audited",
            ],
        ],
        "widths": [0.9, 1.85, 1.95, 1.8],
        "size": 7.4,
    },
    {"t": "h3", "text": "3.1.2 Navigation model per tier"},
    {
        "t": "p",
        "text": (
            "**Tier 1** uses a single horizontal top navigation. It is not a mega-menu "
            "site. The top nav carries at most eight items and every item in it is a page "
            "in the table in 3.2, never a category that needs a second click. The footer "
            "carries the full sitemap, the legal pages and the contact route. Mobile "
            "collapses the tier-1 top nav to a logo, a single *Sign in* affordance and a "
            "hamburger; the marketing site does not get a bottom bar, because the marketing "
            "site is not a task surface."
        )
    },
    {
        "t": "p",
        "text": (
            "**Tier 2** uses a persistent left rail on desktop and a fixed five-item "
            "bottom bar on mobile. The rail is the primary orientation device: it is the "
            "answer to *where am I* in a product where a person belongs to many Ajos at "
            "once. The bottom bar is the answer to *what can I do right now*, and it is "
            "deliberately short (3.8). Tier 2 has no hamburger. On mobile, a hamburger in "
            "a financial application hides the two things a nervous member checks first: "
            "what I owe and what I am owed."
        )
    },
    {
        "t": "p",
        "text": (
            "**Tier 3** uses a fixed left rail only. There is no top nav, no bottom nav "
            "and no marketing chrome. An admin console is a work surface and it should look "
            "like one. The admin rail collapses to icons with a hover label below 1024 px "
            "and the admin console is explicitly not supported on screens narrower than "
            "360 px — an administrator uses a desktop."
        )
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "The admin console is not a member of the app",
        "text": (
            "Keeping `/admin` on the same origin as `/app` is a deployment convenience, not "
            "a security control. `super_admin` cannot edit or delete a ledger entry "
            "(CANONICAL.md section 2, hard rule), and no admin screen in 3.4 exposes a "
            "write affordance against a ledger table. Splitting the admin console onto a "
            "separate origin behind a separate edge control is a recommended hardening "
            "step; it is not in MVP scope and it does not substitute for authorisation on "
            "every request. **Owner: Founders and Engineering. Decision required before "
            "production.**"
        )
    },

    # =================================================================== 3.2
    {"t": "h2", "text": "3.2 Public website sitemap"},
    {
        "t": "p",
        "text": (
            "Twelve content pages plus six authentication pages make up tier 1. The content "
            "pages exist to answer the questions that block a signup, in the order a "
            "sceptical Nigerian saver actually asks them: what is this, how does it work, "
            "what does it cost, what happens if someone does not pay, who are you. The "
            "authentication pages are the only tier-1 routes that a person arrives at with "
            "an intent already formed, and they are deliberately unbranded in their title "
            "so that they do not compete with the content pages in search."
        )
    },
    {
        "t": "table",
        "head": ["Path", "Page", "Purpose", "Audience", "CTA"],
        "rows": [
            [
                "`/`",
                "Home — SCR-WEB-01",
                "State the offer in one sentence, show the rotating mechanic, disclose the "
                "2% fee above the fold, and route to signup.",
                "All, first visit",
                "Create free account",
            ],
            [
                "`/how-it-works`",
                "How It Works — SCR-WEB-02",
                "Explain the cycle in six numbered steps with the canonical worked example: "
                "10 members at NGN 1,000.00, each charged NGN 1,020.00, recipient receives "
                "NGN 10,000.00. Name the Ajo/esusu context.",
                "All, evaluation",
                "See what you would pay",
            ],
            [
                "`/features`",
                "Features — SCR-WEB-03",
                "Organiser tools, member tools, schedule and reminder features, statements "
                "and receipts. No performance claims.",
                "Prospective members and organisers",
                "Create an Ajo",
            ],
            [
                "`/safety-and-trust`",
                "Safety & Trust — SCR-WEB-04",
                "Position lock, the 5-day enrollment rule, what happens on a default, who "
                "can see what, and the append-only ledger statement. States that the "
                "custody and licensing position is open (D-02).",
                "Sceptical savers, existing referrers",
                "Read the safeguards",
            ],
            [
                "`/fees`",
                "Fees — SCR-WEB-05",
                "The single canonical fee page. One worked example, one table, one number: "
                "2% on every contribution deposit, charged on top, never deducted from the "
                "contribution, never reducing a payout.",
                "All, pre-commitment",
                "Accept and continue",
            ],
            [
                "`/about`",
                "About — SCR-WEB-06",
                "Founders, why the product exists, the Nigerian context, contact routes. No "
                "funding or traction claims — the company is pre-launch.",
                "All, trust-building",
                "Talk to us",
            ],
            [
                "`/faq`",
                "FAQ — SCR-WEB-07",
                "Ranked questions on default, cancellation, refunds, what happens if the "
                "Ajo does not fill, privacy, and who can see member names.",
                "All, late-stage",
                "Still unsure? Contact us",
            ],
            [
                "`/contact`",
                "Contact — SCR-WEB-08",
                "Form plus direct channels, published response expectation, and a separate "
                "press route.",
                "All, support",
                "Send a message",
            ],
            [
                "`/login`",
                "Login — SCR-WEB-09",
                "Email or phone plus password. Carries `returnTo`. No registration pitch "
                "above the fold.",
                "Returning",
                "Sign in",
            ],
            [
                "`/register`",
                "Register — SCR-WEB-10",
                "Create an account. States that an Ajo cannot be created or joined until "
                "the email and phone are both verified.",
                "New",
                "Create account",
            ],
            [
                "`/verify-email`",
                "Verify email — SCR-WEB-11",
                "Consume the emailed token, report the result, offer resend with cooldown.",
                "New, post-signup",
                "Resend email",
            ],
            [
                "`/verify-phone`",
                "Verify phone — SCR-WEB-12",
                "Six-digit OTP. Five-attempt limit, sixty-second resend cooldown, rate "
                "limit, no account-existence disclosure on failure.",
                "New, post-signup",
                "Verify phone",
            ],
            [
                "`/forgot-password`",
                "Forgot password — SCR-WEB-13",
                "Always returns the same neutral response, whether or not the account "
                "exists.",
                "Locked out",
                "Email a reset link",
            ],
            [
                "`/reset-password`",
                "Reset password — SCR-WEB-14",
                "Consume a single-use token, set a password, revoke all other sessions, "
                "confirm out of band.",
                "Locked out",
                "Set new password",
            ],
            [
                "`/terms`",
                "Terms & Conditions — SCR-WEB-15",
                "The contract. Includes the non-guarantor role of the organiser (BR-008), "
                "the complete-cycle commitment (BR-004), fee and tax language pending D-05 "
                "and D-06, and the complaint route.",
                "Legal, registrants",
                "Accept and continue",
            ],
            [
                "`/privacy`",
                "Privacy Policy — SCR-WEB-16",
                "What is collected, why, retention, the member-visibility rules, and the "
                "rights mechanism. **Requires review by qualified Nigerian counsel** "
                "(NDPA alignment to be confirmed).",
                "Legal, registrants",
                "Download",
            ],
            [
                "`/status`",
                "Account status notice — SCR-WEB-17",
                "Shown when an account is frozen or under risk review. States what the "
                "person can still do, who to contact, and the reference ID.",
                "Restricted members",
                "Contact support",
            ],
            [
                "`/invite/:token`",
                "Invitation — SCR-MOB-24",
                "The bridge into tier 2. Publicly addressable but never indexed, never "
                "pre-cached, and it discloses the organiser name, member count, "
                "contribution, fee, frequency, total duration and the invitee's total "
                "commitment — and nothing about other members.",
                "Invited people",
                "Join this Ajo",
            ],
        ],
        "widths": [1.06, 1.28, 2.5, 0.9, 0.76],
        "size": 7.0,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The fee page is not optional and is not the pricing page",
        "text": (
            "`/fees` is the only place on tier 1 where the 2% fee is quantified, and it is "
            "quantified with the same numbers that appear in the receipt, the wizard and "
            "the statement. There is no tier-1 page that shows a contribution amount "
            "without showing the fee beside it. A design that puts NGN 1,000.00 in large "
            "type and NGN 20.00 in eight-point grey is a dark pattern (7.17) and is "
            "rejected at design review."
        )
    },

    # =================================================================== 3.3
    {"t": "h2", "text": "3.3 Authenticated web app sitemap"},
    {
        "t": "p",
        "text": (
            "Tier 2 is a single application served responsively at `/app`. It has one "
            "dashboard, one collection resource (the Ajo), and a set of member-scoped "
            "records that hang off either the member or the Ajo. The organising principle "
            "is that **the Ajo is the organising object**: almost every tier-2 screen is "
            "reached through an Ajo, and the screens that are not (payments, payouts, "
            "transactions, disputes, profile) are member-scoped ledgers that a member "
            "consults to answer the two questions they actually have — *what have I "
            "paid, and what am I owed*."
        )
    },
    {
        "t": "table",
        "head": ["Path", "Screen", "Purpose", "Role", "Key states"],
        "rows": [
            [
                "`/app`",
                "Dashboard — SCR-MOB-01",
                "The single landing surface after login. Greeting, *needs your action* "
                "block, next due contribution, Ajo progress, recent activity.",
                "All tier-2",
                "First-run (no Ajos), enrolled, active, frozen",
            ],
            [
                "`/app/ajos`",
                "My Ajos — SCR-MOB-02",
                "Every Ajo the person organises or belongs to, with lifecycle badge, next "
                "due date, my commitment, my position.",
                "All tier-2",
                "Empty, 1 item, long list, cancelled/completed collapsed",
            ],
            [
                "`/app/ajos/new`",
                "Create Ajo wizard — SCR-MOB-05.1 to 05.7",
                "Seven steps from name to acknowledgement. Resumable; a partial DRAFT is "
                "persisted from step 1.",
                "`user` (becomes `ajo_organizer`)",
                "Step-level validation, expiry, resumable",
            ],
            [
                "`/app/join`",
                "Join Ajo — SCR-MOB-04",
                "Enter an invitation code. Route of last resort when the deep link was "
                "lost.",
                "`user`",
                "Invalid code, expired, already used, enrollment closed",
            ],
            [
                "`/app/join/:token`",
                "Invitation accept — SCR-MOB-24",
                "Full fee-disclosure surface. The invitee sees exactly what they will pay in "
                "total and what the recipient receives, before committing.",
                "`user`",
                "Valid, expired, used, revoked, Ajo full, window closing",
            ],
            [
                "`/app/ajos/:id`",
                "Ajo Detail — SCR-MOB-03",
                "The Ajo's home. Status, positions, funding progress this round, base pool "
                "target, my position and my commitment, organizer actions.",
                "All tier-2 (scoped)",
                "By lifecycle: DRAFT, ENROLLMENT (with countdown), ACTIVE, ROUND_IN_PROGRESS, "
                "COMPLETED, FROZEN, CANCELLED, CANCELLING",
            ],
            [
                "`/app/ajos/:id/members`",
                "Members — SCR-MOB-06",
                "Roster with position, payment status for the current round, and — for the "
                "organiser only — invite, remove (pre-activation), replace and remind.",
                "All see roster; organiser acts",
                "Invited-not-joined, active, defaulting (organiser only)",
            ],
            [
                "`/app/ajos/:id/schedule`",
                "Contribution Schedule — SCR-MOB-07",
                "The full round calendar: who pays what on which date, and what I owe next. "
                "Frequency and duration read-only after activation.",
                "All tier-2 (scoped)",
                "Not yet active (provisional), active, past, frozen",
            ],
            [
                "`/app/ajos/:id/contributions`",
                "Contributions — SCR-MOB-08",
                "Contribution obligations for the member, filterable by round and state "
                "(`PENDING`, `PAID`, `OVERDUE`, `GRACE`, `DEFAULTED`, `RECOVERED`, "
                "`WRITTEN_OFF`).",
                "All tier-2 (scoped)",
                "Empty (no Ajo), all paid, mixed, defaulted",
            ],
            [
                "`/app/contributions/:id/pay`",
                "Pay Contribution — SCR-MOB-09",
                "**Fee-disclosure surface.** Itemised: contribution NGN 1,000.00, platform "
                "fee NGN 20.00, total charged NGN 1,020.00. Method selection, then commit.",
                "`ajo_member`",
                "Due, overdue, in grace, already paid, expired authorisation",
            ],
            [
                "`/app/contributions/:id/processing`",
                "Payment processing — SCR-MOB-10",
                "Terminal handoff to the provider. Non-dismissable, shows the provider "
                "reference, survives refresh, polls until the webhook or the verify call "
                "resolves it.",
                "`ajo_member`",
                "`INITIATED`, `PENDING`, `UNKNOWN`, `FAILED`, `CANCELLED`, `REVERSED`",
            ],
            [
                "`/app/contributions/:id/receipt`",
                "Payment receipt — SCR-MOB-11",
                "**Fee-disclosure surface.** Contribution, fee and total as three separate "
                "lines. Downloadable. Never mutated; a correction is a reversing entry and "
                "appears as a second receipt (BR-024, hard rule).",
                "`ajo_member`",
                "Success, reversed, refunded",
            ],
            [
                "`/app/ajos/:id/payouts`",
                "`/app/payouts` — SCR-MOB-12",
                "Payout schedule and history. Who is due, when, from which round, and the "
                "base pool they will receive — never the collected total.",
                "All tier-2 (scoped)",
                "`SCHEDULED`, `FUNDING`, `RELEASED`, `SUCCESS`, `FAILED`, `HELD`",
            ],
            [
                "`/app/payouts/:id`",
                "Payout detail — SCR-MOB-13",
                "One payout: base pool, funding progress, provider reference, and — if "
                "`HELD` — the plain statement that the round is short and no other member "
                "will be charged extra (C: payout funding principle).",
                "`ajo_member`",
                "As above, plus retry-pending",
            ],
            [
                "`/app/transactions`",
                "Transactions / Statement — SCR-MOB-14",
                "The member's complete financial record, chronological, with statement "
                "period export. The screen a member screenshots to their own records.",
                "All tier-2",
                "Empty, single period, cross-Ajo, long range",
            ],
            [
                "`/app/notifications`",
                "Notifications centre — SCR-MOB-15",
                "The canonical catalogue from CANONICAL.md section 8, grouped by Ajo, "
                "with per-event read state and a per-category preference control.",
                "All tier-2",
                "Empty, unread-only, many Ajos, long history",
            ],
            [
                "`/app/disputes`",
                "Disputes list — SCR-MOB-16",
                "Raised and open disputes with state and last activity. Default handling "
                "is not a dispute by default — the member is offered a dispute only after "
                "the recovery path is engaged.",
                "`ajo_member`",
                "Empty, open, resolved, escalated",
            ],
            [
                "`/app/disputes/new`",
                "New dispute — SCR-MOB-17",
                "Category, amount, narrative, evidence upload. Warns that a dispute does "
                "not stop a payout that is already funded, and does not stop the recovery "
                "process.",
                "`ajo_member`",
                "Draft, validation, evidence too large, upload failed",
            ],
            [
                "`/app/disputes/:id`",
                "Dispute thread — SCR-MOB-18",
                "The conversation and evidence timeline, with the decision and its "
                "reasoning when resolved.",
                "Parties + `support`",
                "Open, awaiting member, awaiting platform, resolved, escalated",
            ],
            [
                "`/app/profile`",
                "Profile — SCR-MOB-19",
                "Name, avatar, contact channels, and a read-only financial summary: paid "
                "to date, received to date, fees paid, active Ajos.",
                "All tier-2",
                "Complete, incomplete, verification pending",
            ],
            [
                "`/app/settings`",
                "Settings — SCR-MOB-20",
                "Notification channel matrix from CANONICAL.md section 8, language, "
                "timezone (stated, default `Africa/Lagos`), and data rights.",
                "All tier-2",
                "Default, modified, SMS not permitted",
            ],
            [
                "`/app/settings/security`",
                "Security — SCR-MOB-21",
                "Password change, active sessions with device and last-seen, revoke one, "
                "revoke all, and new-device alerts.",
                "All tier-2",
                "One session, many sessions, forced revoke after password reset",
            ],
            [
                "`/app/verification`",
                "KYC / Verification — SCR-MOB-22",
                "Identity submission: NIN and BVN, liveness, address. States what is "
                "verified, by whom, and how long it is retained. Whether this is "
                "mandatory or threshold-based is D-04, open.",
                "All tier-2",
                "Not started, in review, approved, failed with reason, resubmittable",
            ],
            [
                "`/app/exit-request`",
                "Replacement / exit request — SCR-MOB-25",
                "The only sanctioned route out of an activated Ajo. Replacement member "
                "nomination, handover of the position, and a clear statement that the "
                "member remains liable until the replacement completes.",
                "`ajo_member`",
                "Pre-activation (plain leave), post-activation (replacement), refused",
            ],
            [
                "`/app/support`",
                "Support — SCR-MOB-23",
                "Help centre entries, a ticket form, and the direct route to a human. "
                "Attachments flow to the same evidence store as disputes.",
                "All tier-2",
                "No ticket, open ticket, closed ticket, attachment failed",
            ],
            [
                "`/app/*`",
                "Error boundary — SCR-MOB-26",
                "In-app not-found and unexpected-error boundary with retry, a support "
                "reference, and a link home.",
                "All tier-2",
                "404, 403, 5xx, offline",
            ],
        ],
        "widths": [1.28, 1.36, 2.28, 0.9, 1.18],
        "size": 6.9,
    },

    # =================================================================== 3.4
    {"t": "h2", "text": "3.4 Admin dashboard sitemap"},
    {
        "t": "p",
        "text": (
            "Tier 3 is a single read-and-decide console. The canonical inventory has nine "
            "admin areas; they are expressed here as nine rail destinations and twelve "
            "screens. Two of them — the risk queue and the dispute workspace — are the "
            "places where an administrator can actually affect a member's life, and both "
            "are written with the same restraint: **show the record, show the reason, show "
            "who decided, never offer a delete.**"
        )
    },
    {
        "t": "table",
        "head": ["Rail item", "Route", "Screen", "Purpose", "Role"],
        "rows": [
            [
                "Overview",
                "`/admin`",
                "Overview — SCR-ADM-01",
                "Operational health: Ajos by lifecycle, round funding status, disputes "
                "open, risk queue depth, verification backlog, fee income for the period, "
                "reconciliation run status.",
                "All admin",
            ],
            [
                "Users",
                "`/admin/users`",
                "Users — SCR-ADM-02",
                "Searchable member list with verification state, Ajo count, account state, "
                "last activity. Bulk export is off by default and requires `super_admin`.",
                "All admin",
            ],
            [
                "Users",
                "`/admin/users/:id`",
                "User detail — SCR-ADM-03",
                "One member across every Ajo they touch, with their contribution history, "
                "dispute history and risk events. **No balance editing, ever.**",
                "All admin",
            ],
            [
                "Ajos",
                "`/admin/ajos`",
                "Ajos — SCR-ADM-04",
                "Every Ajo with lifecycle, funding gap, organizer, member count, fee "
                "retained, and flags.",
                "All admin",
            ],
            [
                "Ajos",
                "`/admin/ajos/:id`",
                "Ajo detail — SCR-ADM-05",
                "Read-only mirror of the tier-2 Ajo Detail plus the platform-only columns: "
                "escrow balance, reconciliation state, risk events.",
                "All admin",
            ],
            [
                "Disputes",
                "`/admin/disputes`",
                "Disputes — SCR-ADM-06",
                "Queue by state, category, age and Ajo. SLA ageing is visible. This is the "
                "screen `support` works from.",
                "`support`, `risk_officer`, `super_admin`",
            ],
            [
                "Disputes",
                "`/admin/disputes/:id`",
                "Dispute workspace — SCR-ADM-07",
                "Facts, evidence, both narratives, the money involved, and the decision "
                "form. Resolution posts a ledger entry; it does not adjust one silently.",
                "`support` drafts, `risk_officer`/`super_admin` decide",
            ],
            [
                "Risk",
                "`/admin/risk`",
                "Risk queue — SCR-ADM-08",
                "Risk events ranked by score: funding shortfalls, repeated payment failure, "
                "identity mismatch, velocity breaches. Actions are *place under review*, "
                "*freeze*, *release*, and *approve or reject an override*.",
                "`risk_officer`, `super_admin`",
            ],
            [
                "Verification",
                "`/admin/verification`",
                "Verification queue — SCR-ADM-09",
                "Pending NIN/BVN submissions with the checker's outcome and reason. BVN is "
                "never displayed beyond the last four digits, in any view, for anyone.",
                "`support`, `risk_officer`",
            ],
            [
                "Reports",
                "`/admin/reports`",
                "Reports — SCR-ADM-10",
                "Volume, fee income, contribution and payout counts against the three "
                "Year-1 scenarios, default rate, and the reconciliation run log.",
                "`support`, `super_admin`",
            ],
            [
                "Audit Logs",
                "`/admin/audit-logs`",
                "Audit Logs — SCR-ADM-11",
                "Append-only. Every privileged action: who, what, which record, before and "
                "after, from which session, at which `X-Request-Id`. Filterable, exportable, "
                "**not deletable, including by `super_admin`**.",
                "All admin",
            ],
            [
                "Settings",
                "`/admin/settings`",
                "Settings — SCR-ADM-12",
                "Limits, notification template overrides, contribution cap, max Ajo size, "
                "feature flags. The fee rate is **read-only here** — changing it is a code "
                "and legal change, not a settings change (D-06 open).",
                "`super_admin` only",
            ],
            [
                "(none)",
                "`/admin/denied`",
                "Access denied — SCR-ADM-13",
                "Shown when an authenticated user holds a tier-1 or tier-2 session and "
                "requests `/admin/**`, or holds an admin role without the specific "
                "permission. States the role held and the role required, without "
                "enumerating the admin surface.",
                "Any",
            ],
        ],
        "widths": [0.78, 1.06, 1.1, 2.62, 0.94],
        "size": 7.0,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "What an admin screen may never contain",
        "text": (
            "A control that edits or deletes a ledger entry, a control that changes a "
            "member's obligation, a control that releases a payout without a funded round, "
            "and a control that alters the 2% fee. If an admin screen appears to need one "
            "of these, the correct mechanism is a reversing ledger entry, a risk decision "
            "recorded against the Ajo, or a code change reviewed by the founders. This is "
            "CANONICAL.md's hard rule and it is a UI constraint as much as a data one."
        )
    },

    # =================================================================== 3.5
    {"t": "h2", "text": "3.5 Full navigation tree"},
    {
        "t": "p",
        "text": (
            "The complete tree, with the screen identifier for every leaf and the role "
            "gate in brackets. `[A]` is any tier-2 role, `[O]` adds the organiser "
            "capability, `[S]` is `support`, `[R]` is `risk_officer`, `[*]` is "
            "`super_admin`."
        )
    },
    {
        "t": "code",
        "text": """
ajo.ng
|
+-- TIER 1  PUBLIC WEBSITE ........... no account, indexable
|   |
|   +-- /                      SCR-WEB-01  Home
|   +-- /how-it-works          SCR-WEB-02
|   +-- /features              SCR-WEB-03
|   +-- /safety-and-trust      SCR-WEB-04
|   +-- /fees                  SCR-WEB-05
|   +-- /about                 SCR-WEB-06
|   +-- /faq                   SCR-WEB-07
|   +-- /contact               SCR-WEB-08
|   +-- /terms                 SCR-WEB-15
|   +-- /privacy               SCR-WEB-16
|   |
|   +-- /login                 SCR-WEB-09
|   +-- /register              SCR-WEB-10
|   +-- /verify-email          SCR-WEB-11
|   +-- /verify-phone          SCR-WEB-12
|   +-- /forgot-password       SCR-WEB-13
|   +-- /reset-password        SCR-WEB-14
|   +-- /status                SCR-WEB-17   frozen / under review
|   +-- /invite/:token         SCR-MOB-24   bridge into tier 2
|
+-- TIER 2  AUTHENTICATED APP ...... /app, [A] [O]
|   |
|   +-- /app                   SCR-MOB-01  Dashboard
|   +-- /app/ajos              SCR-MOB-02  My Ajos
|   |   +-- new                SCR-MOB-05  Create Ajo wizard
|   |   |   +-- 1  configure   05.1   name, size, NGN, start
|   |   |   +-- 2  amount      05.2   NGN 1,000.00 + NGN 20.00 fee
|   |   |   +-- 3  frequency   05.3   weekly | monthly
|   |   |   +-- 4  duration    05.4   10 rounds = 10 members
|   |   |   +-- 5  invite      05.5   members + invitations
|   |   |   +-- 6  order       05.6   payout positions [O]
|   |   |   +-- 7  review      05.7   acknowledge + open window
|   |   +-- :id                SCR-MOB-03  Ajo Detail  [A] [O]
|   |       +-- members        SCR-MOB-06  roster, act [O] only
|   |       +-- schedule       SCR-MOB-07  round calendar
|   |       +-- contributions  SCR-MOB-08  obligations
|   |       +-- economics      anchor    base pool NGN 10,000.00
|   |       +-- payouts        SCR-MOB-12  round payouts
|   +-- /app/join              SCR-MOB-04  by code
|   +-- /app/join/:token       SCR-MOB-24  by link
|   |
|   +-- /app/contributions/:id
|   |   +-- pay                SCR-MOB-09  fee broken out
|   |   +-- processing         SCR-MOB-10  provider terminal
|   |   +-- receipt            SCR-MOB-11  fee broken out
|   +-- /app/payments/:id      SCR-MOB-10  deep link
|   +-- /app/payments/:id/receipt  SCR-MOB-11
|   +-- /app/payouts           SCR-MOB-12
|   +-- /app/payouts/:id       SCR-MOB-13  base pool, never collected
|   +-- /app/transactions      SCR-MOB-14  statement + export
|   +-- /app/notifications     SCR-MOB-15  canonical catalogue
|   |
|   +-- /app/disputes          SCR-MOB-16
|   |   +-- new                SCR-MOB-17
|   |   +-- :id                SCR-MOB-18  thread + evidence
|   |
|   +-- /app/profile           SCR-MOB-19
|   +-- /app/settings          SCR-MOB-20
|   |   +-- security           SCR-MOB-21
|   |   +-- sessions           SCR-MOB-21
|   +-- /app/verification      SCR-MOB-22  NIN / BVN / liveness
|   +-- /app/exit-request      SCR-MOB-25  replacement only
|   +-- /app/support           SCR-MOB-23
|   +-- /app/*                 SCR-MOB-26  in-app error boundary
|
+-- TIER 3  ADMIN CONSOLE ......... /admin, [S] [R] [*]
    |
    +-- /admin                  SCR-ADM-01  Overview
    +-- /admin/users            SCR-ADM-02
    |   +-- :id                SCR-ADM-03  read-only
    +-- /admin/ajos             SCR-ADM-04
    |   +-- :id                SCR-ADM-05  read-only
    +-- /admin/disputes         SCR-ADM-06
    |   +-- :id                SCR-ADM-07  decision workspace
    +-- /admin/risk             SCR-ADM-08  queue + freeze/release
    +-- /admin/verification    SCR-ADM-09
    +-- /admin/reports          SCR-ADM-10
    +-- /admin/audit-logs       SCR-ADM-11  append-only
    +-- /admin/settings         SCR-ADM-12  [*] only, fee read-only
    +-- /admin/denied           SCR-ADM-13
""",
    },
    {
        "t": "callout",
        "kind": "ASSUMPTION",
        "title": "Why tier 2 is served at /app and not at the root",
        "text": (
            "Serving tier 2 at the root (`/dashboard`, `/ajos`) would give tier-1 content "
            "the shortest, most linkable URLs and would make the marketing site and the "
            "product indistinguishable to a crawler and to a person reading a shared "
            "link. The cost of `/app` is one extra segment on roughly forty internal "
            "links, and the benefit is an unambiguous, mechanically enforceable public/"
            "private boundary at the path prefix. **Owner: Founders and Engineering.**"
        )
    },

    # =================================================================== 3.6
    {"t": "h2", "text": "3.6 Route inventory and screen identifiers"},
    {
        "t": "p",
        "text": (
            "Every route registered by the web application, its screen, whether a session "
            "is required, which role may see it, whether it may be linked to from outside "
            "the application, and the notes that a router implementer needs. If a route is "
            "not in this table it is not in the product."
        )
    },
    {"t": "h3", "text": "3.6.1 Tier 1 and authentication routes"},
    {
        "t": "table",
        "head": ["Route", "Screen ID", "Auth", "Role", "Deep-link", "Notes"],
        "rows": [
            ["`/`", "SCR-WEB-01", "No", "—", "Yes", "Canonical home. Redirects `/index.html`."],
            ["`/how-it-works`", "SCR-WEB-02", "No", "—", "Yes", "Carries the worked example."],
            ["`/features`", "SCR-WEB-03", "No", "—", "Yes", "No performance claims."],
            ["`/safety-and-trust`", "SCR-WEB-04", "No", "—", "Yes", "Must name D-02 as open."],
            ["`/fees`", "SCR-WEB-05", "No", "—", "Yes", "Canonical fee statement. Single source."],
            ["`/about`", "SCR-WEB-06", "No", "—", "Yes", "Pre-launch: no traction claims."],
            ["`/faq`", "SCR-WEB-07", "No", "—", "Yes", "Ranked; default and cancellation first."],
            ["`/contact`", "SCR-WEB-08", "No", "—", "Yes", "Form posts to a support queue."],
            ["`/login`", "SCR-WEB-09", "No", "—", "Yes", "`?returnTo=` allowlisted to `/app` only."],
            ["`/register`", "SCR-WEB-10", "No", "—", "Yes", "Accepts `/terms` acceptance token."],
            ["`/verify-email`", "SCR-WEB-11", "Token", "—", "Yes", "Single-use, 24 h expiry."],
            ["`/verify-phone`", "SCR-WEB-12", "Token", "—", "Yes", "5 attempts, 60 s resend."],
            ["`/forgot-password`", "SCR-WEB-13", "No", "—", "Yes", "Neutral response always."],
            ["`/reset-password`", "SCR-WEB-14", "Token", "—", "Yes", "Revokes all other sessions."],
            ["`/terms`", "SCR-WEB-15", "No", "—", "Yes", "Versioned; acceptance is timestamped."],
            ["`/privacy`", "SCR-WEB-16", "No", "—", "Yes", "Counsel review required before launch."],
            ["`/status`", "SCR-WEB-17", "No", "—", "No", "Reached by state, not linked. `noindex`."],
            ["`/404`", "SCR-WEB-18", "No", "—", "No", "Wildcard handler for tier 1."],
            ["`/invite/:token`", "SCR-MOB-24", "Optional", "Any signed-in", "Yes", "`noindex, nofollow`, `no-store`."],
        ],
        "widths": [1.28, 0.98, 0.5, 0.72, 0.56, 2.46],
        "size": 7.1,
    },
    {"t": "h3", "text": "3.6.2 Tier 2 application routes"},
    {
        "t": "table",
        "head": ["Route", "Screen ID", "Auth", "Role", "Deep-link", "Notes"],
        "rows": [
            ["`/app`", "SCR-MOB-01", "Yes", "All tier-2", "Yes", "Post-login landing. `noindex`."],
            ["`/app/aios` → `/app/ajos`", "—", "—", "—", "—", "Reserved typo redirect only; see 3.12."],
            ["`/app/ajos`", "SCR-MOB-02", "Yes", "All tier-2", "Yes", "Cursor-paginated list."],
            ["`/app/ajos/new`", "SCR-MOB-05.1", "Yes", "`user`", "No", "Resumable. Creates DRAFT."],
            ["`/app/ajos/new/amount`", "SCR-MOB-05.2", "Yes", "`user`", "No", "Live fee preview. BR-010."],
            ["`/app/ajos/new/frequency`", "SCR-MOB-05.3", "Yes", "`user`", "No", "Immutable post-activation."],
            ["`/app/ajos/new/duration`", "SCR-MOB-05.4", "Yes", "`user`", "No", "Rounds = member count."],
            ["`/app/ajos/new/invite`", "SCR-MOB-05.5", "Yes", "`user`", "No", "Mints single-use tokens."],
            ["`/app/ajos/new/order`", "SCR-MOB-05.6", "Yes", "`user`, members", "No", "Provisional until activation."],
            ["`/app/ajos/new/review`", "SCR-MOB-05.7", "Yes", "`user`", "No", "Acknowledgement gate. No fee line, no commit action."],
            ["`/app/join`", "SCR-MOB-04", "Yes", "All tier-2", "Yes", "Code entry. Rate limited."],
            ["`/app/join/:token`", "SCR-MOB-24", "Yes", "All tier-2", "Yes", "Fee disclosure before commit."],
            ["`/app/ajos/:id`", "SCR-MOB-03", "Yes", "Member/organizer of that Ajo", "Yes", "404 if not a participant. No existence oracle."],
            ["`/app/ajos/:id/members`", "SCR-MOB-06", "Yes", "Member/organizer of that Ajo", "Yes", "Write actions gated to `[O]`."],
            ["`/app/ajos/:id/schedule`", "SCR-MOB-07", "Yes", "Member/organizer of that Ajo", "Yes", "Provisional pre-activation."],
            ["`/app/ajos/:id/contributions`", "SCR-MOB-08", "Yes", "Member/organizer of that Ajo", "Yes", "Default handling is private (C §4)."],
            ["`/app/ajos/:id/economics`", "SCR-MOB-03", "Yes", "Member/organizer of that Ajo", "Yes", "Fee-disclosure surface. Base pool, not collected."],
            ["`/app/ajos/:id/payouts`", "SCR-MOB-12", "Yes", "Member/organizer of that Ajo", "Yes", "Scoped view of `/app/payouts`."],
            ["`/app/contributions`", "SCR-MOB-08", "Yes", "All tier-2", "Yes", "Cross-Ajo obligation list."],
            ["`/app/contributions/:id`", "SCR-MOB-08", "Yes", "Owner", "Yes", "Detail. 404 if not the owner."],
            ["`/app/contributions/:id/pay`", "SCR-MOB-09", "Yes", "Owner, `ajo_member`", "Yes", "**Fee disclosure required**."],
            ["`/app/contributions/:id/processing`", "SCR-MOB-10", "Yes", "Owner", "Yes", "Non-dismissable while `PENDING`."],
            ["`/app/contributions/:id/receipt`", "SCR-MOB-11", "Yes", "Owner", "Yes", "**Fee disclosure required.** Immutable."],
            ["`/app/payments`", "SCR-MOB-10", "Yes", "All tier-2", "Yes", "Attempt history, not receipts."],
            ["`/app/payments/:id`", "SCR-MOB-10", "Yes", "Owner", "Yes", "State machine view."],
            ["`/app/payments/:id/receipt`", "SCR-MOB-11", "Yes", "Owner", "Yes", "**Fee disclosure required.**"],
            ["`/app/payouts`", "SCR-MOB-12", "Yes", "All tier-2", "Yes", "Cross-Ajo payout list."],
            ["`/app/payouts/:id`", "SCR-MOB-13", "Yes", "Recipient/organizer", "Yes", "Base pool only. `HELD` explained."],
            ["`/app/transactions`", "SCR-MOB-14", "Yes", "All tier-2", "Yes", "Statement export. PII-free."],
            ["`/app/statements`", "SCR-MOB-14", "Yes", "All tier-2", "Yes", "Period selector for the same view."],
            ["`/app/notifications`", "SCR-MOB-15", "Yes", "All tier-2", "Yes", "Grouped by Ajo."],
            ["`/app/disputes`", "SCR-MOB-16", "Yes", "Party to the dispute", "Yes", "No platform-wide list for members."],
            ["`/app/disputes/new`", "SCR-MOB-17", "Yes", "`ajo_member`", "No", "Optional `:contributionId`."],
            ["`/app/disputes/:id`", "SCR-MOB-18", "Yes", "Party to the dispute", "Yes", "Evidence timeline."],
            ["`/app/profile`", "SCR-MOB-19", "Yes", "All tier-2", "Yes", "Read-only financial summary."],
            ["`/app/settings`", "SCR-MOB-20", "Yes", "All tier-2", "Yes", "Channel matrix from CAN §8."],
            ["`/app/settings/security`", "SCR-MOB-21", "Yes", "All tier-2", "Yes", "Password and sessions."],
            ["`/app/settings/sessions`", "SCR-MOB-21", "Yes", "All tier-2", "Yes", "Revoke one or all."],
            ["`/app/verification`", "SCR-MOB-22", "Yes", "All tier-2", "Yes", "Submission and status. D-04 open."],
            ["`/app/verification/:id`", "SCR-MOB-22", "Yes", "Owner", "Yes", "Never displays full BVN."],
            ["`/app/exit-request`", "SCR-MOB-25", "Yes", "`ajo_member`", "No", "Replacement path only post-activation."],
            ["`/app/support`", "SCR-MOB-23", "Yes", "All tier-2", "Yes", "Help centre and ticket form."],
            ["`/app/support/:id`", "SCR-MOB-23", "Yes", "Owner", "Yes", "Ticket thread."],
            ["`/app/*`", "SCR-MOB-26", "Yes", "All tier-2", "No", "In-app error boundary."],
        ],
        "widths": [1.5, 0.94, 0.42, 1.18, 0.5, 1.96],
        "size": 6.9,
    },
    {"t": "h3", "text": "3.6.3 Tier 3 admin routes"},
    {
        "t": "table",
        "head": ["Route", "Screen ID", "Auth", "Role", "Deep-link", "Notes"],
        "rows": [
            ["`/admin`", "SCR-ADM-01", "Yes", "All admin", "Yes", "Redirect `/admin/` to `/admin`."],
            ["`/admin/users`", "SCR-ADM-02", "Yes", "All admin", "Yes", "BVN never rendered."],
            ["`/admin/users/:id`", "SCR-ADM-03", "Yes", "All admin", "Yes", "Read-only. No balance edit."],
            ["`/admin/ajos`", "SCR-ADM-04", "Yes", "All admin", "Yes", "Escrow and reconciliation columns."],
            ["`/admin/ajos/:id`", "SCR-ADM-05", "Yes", "All admin", "Yes", "Read-only mirror + platform columns."],
            ["`/admin/disputes`", "SCR-ADM-06", "Yes", "`support`, `risk_officer`, `super_admin`", "Yes", "SLA ageing visible."],
            ["`/admin/disputes/:id`", "SCR-ADM-07", "Yes", "As above", "Yes", "Decision posts a ledger entry."],
            ["`/admin/risk`", "SCR-ADM-08", "Yes", "`risk_officer`, `super_admin`", "Yes", "Freeze and release; no delete."],
            ["`/admin/risk/:id/decision`", "SCR-ADM-08", "Yes", "`risk_officer`, `super_admin`", "No", "Reason mandatory. Audited."],
            ["`/admin/verification`", "SCR-ADM-09", "Yes", "`support`, `risk_officer`", "Yes", "Approve/reject with reason."],
            ["`/admin/reports`", "SCR-ADM-10", "Yes", "`support`, `super_admin`", "Yes", "Scenario comparison."],
            ["`/admin/audit-logs`", "SCR-ADM-11", "Yes", "All admin", "Yes", "Append-only. Export gated."],
            ["`/admin/settings`", "SCR-ADM-12", "Yes", "`super_admin`", "Yes", "Fee rate read-only (D-06)."],
            ["`/admin/denied`", "SCR-ADM-13", "Yes", "Any", "No", "Reached by redirect, not linked."],
        ],
        "widths": [1.5, 0.98, 0.42, 1.42, 0.5, 1.68],
        "size": 6.9,
    },
    {"t": "h3", "text": "3.6.4 Screen identifier key and reconciliation with section 2"},
    {
        "t": "p",
        "text": (
            "Section 2.0.1 published a screen-ID key built on `SCR-MKT-nn`, `SCR-APP-nn` and "
            "`SCR-ADM-nn`. This section uses `SCR-WEB-nn`, `SCR-MOB-nn` and `SCR-ADM-nn`, "
            "because the three tiers in 3.1 are the right granularity and because `SCR-MOB` "
            "distinguishes the responsive application surface from the marketing site more "
            "honestly than `SCR-MKT` implies. **Both keys are correct indexes over the same "
            "canonical screen inventory in CANONICAL.md section 7. Neither adds a screen "
            "nor removes one.** The mapping is below and should be applied mechanically when "
            "cross-references are built."
        )
    },
    {
        "t": "table",
        "head": ["This section", "Section 2", "Screen", "Tier"],
        "rows": [
            ["SCR-WEB-01 … 08", "SCR-MKT-01 … 08", "Home … Contact", "1"],
            ["SCR-WEB-09", "SCR-MKT-09", "Login", "1"],
            ["SCR-WEB-10", "SCR-MKT-10", "Register", "1"],
            ["SCR-WEB-11", "— (in 2.1 only)", "Email verification", "1"],
            ["SCR-WEB-12", "— (in 2.1 only)", "Phone OTP verification", "1"],
            ["SCR-WEB-13", "— (in 2.1 only)", "Forgot password", "1"],
            ["SCR-WEB-14", "— (in 2.1 only)", "Reset password", "1"],
            ["SCR-WEB-15", "SCR-MKT-11", "Terms & Conditions", "1"],
            ["SCR-WEB-16", "SCR-MKT-12", "Privacy", "1"],
            ["SCR-WEB-17", "—", "Account status notice", "1"],
            ["SCR-WEB-18", "—", "Tier-1 404", "1"],
            ["SCR-MOB-01", "SCR-APP-01", "Dashboard", "2"],
            ["SCR-MOB-02", "SCR-APP-02", "My Ajos", "2"],
            ["SCR-MOB-03", "SCR-APP-05", "Ajo Detail", "2"],
            ["SCR-MOB-04", "SCR-APP-04", "Join Ajo (by code)", "2"],
            ["SCR-MOB-05.1 … 05.7", "SCR-APP-03 step 1 … 7", "Create Ajo wizard", "2"],
            ["SCR-MOB-06", "SCR-APP-06", "Members", "2"],
            ["SCR-MOB-07", "SCR-APP-07", "Contribution Schedule", "2"],
            ["SCR-MOB-08", "SCR-APP-08", "Contributions", "2"],
            ["SCR-MOB-09", "SCR-APP-09", "Pay Contribution", "2"],
            ["SCR-MOB-10", "SCR-APP-09 / 09 b", "Payment processing", "2"],
            ["SCR-MOB-11", "— (in 2.6 only)", "Payment receipt", "2"],
            ["SCR-MOB-12", "SCR-APP-10", "Payouts", "2"],
            ["SCR-MOB-13", "— (in 2.9 only)", "Payout detail", "2"],
            ["SCR-MOB-14", "SCR-APP-11", "Transactions / Statement", "2"],
            ["SCR-MOB-15", "SCR-APP-12", "Notifications centre", "2"],
            ["SCR-MOB-16", "SCR-APP-14", "Disputes list", "2"],
            ["SCR-MOB-17", "— (in 2.11 only)", "New dispute", "2"],
            ["SCR-MOB-18", "— (in 2.11 only)", "Dispute thread", "2"],
            ["SCR-MOB-19", "SCR-APP-15", "Profile", "2"],
            ["SCR-MOB-20", "SCR-APP-16", "Settings", "2"],
            ["SCR-MOB-21", "SCR-APP-17", "Security", "2"],
            ["SCR-MOB-22", "SCR-APP-19", "KYC / Verification", "2"],
            ["SCR-MOB-23", "SCR-APP-13 / 18", "Support / Help", "2"],
            ["SCR-MOB-24", "SCR-APP-04", "Invitation accept", "2"],
            ["SCR-MOB-25", "SCR-APP-05 b", "Replacement / exit request", "2"],
            ["SCR-MOB-26", "—", "In-app error boundary", "2"],
            ["SCR-ADM-01 … 12", "SCR-ADM-01 … 12", "Admin screens, same numbering", "3"],
            ["SCR-ADM-13", "—", "Access denied", "3"],
        ],
        "widths": [1.3, 1.4, 2.4, 0.4],
        "size": 7.3,
    },

    # =================================================================== 3.7
    {"t": "h2", "text": "3.7 Navigation patterns per surface"},
    {
        "t": "p",
        "text": (
            "Three levels of navigation exist in tier 2, and each answers a different "
            "question. Keeping them distinct is what stops a financial application from "
            "feeling like a website with buttons on it."
        )
    },
    {
        "t": "table",
        "head": ["Level", "Question it answers", "Where it lives", "Behaviour"],
        "rows": [
            [
                "**Primary**",
                "*Where am I in the product?*",
                "Left rail (desktop), bottom bar (mobile)",
                "Persistent, reflects the current top-level section, never more than 9 "
                "rail items or 5 tabs. Carries an unread count on Notifications and an "
                "action count on the Dashboard badge.",
            ],
            [
                "**Secondary**",
                "*Which part of this thing am I looking at?*",
                "Segmented control or in-page tab strip",
                "In-place, does not change the URL unless the tab is genuinely a separate "
                "resource. On Members/Schedule/Contributions inside an Ajo, the tab strip "
                "reflects and updates the URL so the tab is linkable.",
            ],
            [
                "**Contextual**",
                "*What can I do about the thing in front of me?*",
                "Card header actions and a row action",
                "Destructive actions are never icon-only. A row action opens a menu whose "
                "first item is always the safe, reversible one. The commit action for a "
                "payment is never in a dropdown.",
            ],
        ],
        "widths": [0.72, 1.5, 1.5, 2.78],
        "size": 7.2,
    },
    {"t": "h3", "text": "3.7.1 Desktop (1024 px and above)"},
    {
        "t": "p",
        "text": (
            "A fixed 240 px left rail carries the eight tier-2 destinations. A 64 px top "
            "bar carries the Ajo context switcher, the global search, the notification "
            "bell and the account menu. Content sits in a 1200 px maximum column, "
            "centre-aligned, with a 24 px gutter. On Ajo-scoped screens the Ajo name and "
            "lifecycle badge are pinned to the top bar so that a member scrolling a long "
            "member list never loses track of which Ajo they are in."
        )
    },
    {"t": "h3", "text": "3.7.2 Tablet (768–1023 px)"},
    {
        "t": "p",
        "text": (
            "The rail collapses to a 72 px icon rail with hover labels. The top bar "
            "becomes 56 px. Two-column card grids become one column. Tables keep all "
            "columns down to 768 px by reducing cell padding and truncating the longest "
            "free-text column; below 768 px a table becomes a card list (7.12)."
        )
    },
    {"t": "h3", "text": "3.7.3 Mobile (below 768 px)"},
    {
        "t": "p",
        "text": (
            "The rail is removed and replaced entirely by the bottom bar. The top bar "
            "becomes a 56 px contextual header showing the screen title and, on Ajo-scoped "
            "screens, the Ajo name. There is no hamburger in tier 2. The account menu, the "
            "notification list and the search all have their own reachable affordances, and "
            "the full destination list is reachable by scrolling the bottom bar's overflow "
            "into the More tab (3.8)."
        )
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Hamburger in tier 2 — rejected, with the trade-off stated",
        "text": (
            "A hamburger would give tier 2 a single component covering both primary and "
            "secondary navigation, which is simpler to build. It was rejected because in a "
            "product that handles someone's savings, hiding navigation raises the cost of "
            "the one behaviour that matters: checking what is owed. The cost of the "
            "decision is a second navigation component to design, test and localise, and a "
            "bottom bar that must be defended against feature creep (3.8). **Owner: "
            "Founders. Revisit only if user testing on a 360 px device shows the five tabs "
            "are not discoverable.**"
        )
    },

    # =================================================================== 3.8
    {"t": "h2", "text": "3.8 Mobile bottom navigation model"},
    {
        "t": "p",
        "text": (
            "Five tabs, fixed, in this order, with no reordering and no seventh tab:"
        )
    },
    {
        "t": "table",
        "head": ["#", "Tab", "Destination", "Why it earns its place", "Badge"],
        "rows": [
            [
                "1",
                "**Home**",
                "`/app` — SCR-MOB-01",
                "The *needs your action* block lives here and nowhere else. It is the answer "
                "to the question a saver opens the app to ask.",
                "Count of actions due, Gold, capped at `9+`",
            ],
            [
                "2",
                "**Ajos**",
                "`/app/ajos` — SCR-MOB-02",
                "The organising object. A member in four Ajos needs to switch between them "
                "faster than anything else in the product.",
                "Count of Ajos with an action due",
            ],
            [
                "3",
                "**Pay**",
                "`/app/contributions?filter=due` — SCR-MOB-08",
                "A direct route to the next thing payable. It is a *destination*, not a "
                "sheet: it lands on a real, linkable list of due contributions with their "
                "amounts, so a member can decide before committing.",
                "Count of due contributions",
            ],
            [
                "4",
                "**Alerts**",
                "`/app/notifications` — SCR-MOB-15",
                "Payout imminent, contribution due, invitation, default — the money-critical "
                "half of the canonical catalogue (CAN §8).",
                "Unread count",
            ],
            [
                "5",
                "**More**",
                "`/app/profile` + sheet — SCR-MOB-19/20",
                "Everything that is used weekly by some members and daily by none: profile, "
                "settings, security, verification, transactions, disputes, exit request, "
                "support. A sheet, not a screen, so that *More* always returns to where it "
                "was opened from.",
                "KYC incomplete or restricted state",
            ],
        ],
        "widths": [0.24, 0.62, 1.3, 2.72, 1.62],
        "size": 7.2,
    },
    {"t": "h3", "text": "3.8.1 Why five and why these five"},
    {
        "t": "p",
        "text": (
            "Five is the cap because the bottom bar sits in the natural reach zone of a "
            "one-handed grip. A sixth tab forces a target width of 62 px or less on a "
            "375 px screen, which is below the 44 px minimum touch target once label "
            "padding is accounted for (7.14). Beyond five, the honest options are a *More* "
            "sheet or a context-sensitive tab, and a context-sensitive bottom bar in a "
            "financial application is a dark pattern: the location of the pay action would "
            "move depending on state, and muscle memory would be trained on a layout that "
            "changes."
        )
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The Pay tab is a list, not a button",
        "text": (
            "Putting *Pay NGN 1,020.00* on a tab would be the most tempting design in this "
            "document and it is wrong. It would put a money-movement action one mis-tap "
            "from a money-movement destination, it would make the amount the navigation "
            "label, and it would hide the choice between two contributions that are both "
            "due. The tab opens a list of due contributions, each with its own amount, its "
            "due date and its own *Pay* action. The commitment screen is always a separate "
            "navigation step (SCR-MOB-09)."
        )
    },
    {"t": "h3", "text": "3.8.2 Bottom navigation behaviour"},
    {
        "t": "bullets",
        "items": [
            "**Height** 64 px plus the device safe-area inset, so a notched device does not "
            "clip the active indicator.",
            "**Scroll behaviour** the bar is fixed and always visible; the content column "
            "carries 64 px plus safe-area bottom padding so the last card is never hidden "
            "behind it.",
            "**Active state** a 2 px top rule in Primary plus a label weight change from "
            "400 to 600. Never colour alone (7.10, 7.14).",
            "**Badges** are capped at `9+`, are announced to assistive technology with a "
            "count and a noun, and are never used for anything other than an action or an "
            "unread count. No red badge on the Home tab under any circumstance.",
            "**No destructive action is reachable from the bar or from the More sheet** "
            "without a full navigation step. *Sign out* lives in Security, behind a "
            "confirmation.",
            "**Landscape** below 400 px of height the bar is replaced by a compact 48 px "
            "icon row with labels, because a 64 px bar plus a 44 px target is more than a "
            "third of a landscape phone's height.",
        ],
    },

    # =================================================================== 3.9
    {"t": "h2", "text": "3.9 Entry points and exit points"},
    {
        "t": "p",
        "text": (
            "An entry point is a route a person can arrive at from outside the "
            "application. There are seven. Everything else is reached by navigating, and "
            "a route that is not an entry point must not be reachable by a shared link "
            "without a session."
        )
    },
    {"t": "h3", "text": "3.9.1 Tier-1 entry points"},
    {
        "t": "table",
        "head": ["Source", "Landing route", "Conditions"],
        "rows": [
            [
                "Direct, search, social share",
                "`/` — SCR-WEB-01",
                "None. This is the only tier-1 route with no `returnTo`.",
            ],
            [
                "Campaign, referral, printed material",
                "`/` or `/how-it-works`",
                "UTM parameters are read, stored once against the anonymous visitor, and "
                "stripped from every subsequent internal link. Never forwarded to tier 2 "
                "or into an invitation URL.",
            ],
            [
                "Direct brand search for the login",
                "`/login` — SCR-WEB-09",
                "`?returnTo=` is accepted only from an allowlist of `/app` paths; anything "
                "else is discarded silently, which is a security control against open "
                "redirect.",
            ],
            [
                "SEO and marketing internal links",
                "Any tier-1 content page",
                "No `noindex` on tier-1 content. Authenticated links from tier 1 into "
                "tier 2 always pass through `/login` first.",
            ],
            [
                "Legal, footer, in-app support",
                "`/terms`, `/privacy`, `/contact` — SCR-WEB-15/16/08",
                "Reachable without a session, from every tier.",
            ],
        ],
        "widths": [1.36, 1.5, 3.64],
        "size": 7.3,
    },
    {"t": "h3", "text": "3.9.2 Tier-2 and tier-3 entry points"},
    {
        "t": "table",
        "head": ["Source", "Landing route", "Conditions"],
        "rows": [
            [
                "Successful login or registration",
                "`/app` — SCR-MOB-01",
                "The only successful-authentication landing. `returnTo` overrides it; "
                "otherwise a first-time member lands on the Dashboard with an empty-state "
                "that offers *Create an Ajo* and *Enter an invitation code* rather than a "
                "zero balance.",
            ],
            [
                "Email or SMS link",
                "`/verify-email`, `/verify-phone`, `/reset-password`, `/invite/:token`",
                "Consume the token, then land on the `returnTo` carried inside the signed "
                "token, never one supplied by the query string.",
            ],
            [
                "Deep link from a notification",
                "The screen the event concerns, per CAN §8",
                "`contribution.due` → the Pay Contribution screen. `payout.upcoming` → "
                "Payout detail. `member.defaulted` → the Contributions list, never a "
                "public-facing page. Notification deep links carry a signed, single-use "
                "token, not a bare AJO id.",
            ],
            [
                "Push notification tap, app installed",
                "The same destination as above",
                "Cold start to the correct route with the token validated in-app. If the "
                "token has expired the app opens the Notifications entry and shows the "
                "event, not an error.",
            ],
            [
                "Admin SSO or admin login",
                "`/admin` — SCR-ADM-01",
                "A separate session scope from tier 2. A tier-2 session never silently "
                "grants admin access and an admin session never silently grants member "
                "access.",
            ],
            [
                "Password reset from an active session",
                "`/app/settings/security` — SCR-MOB-21",
                "All other sessions are revoked and the current one is rotated. The member "
                "is returned to Security with a confirmation, not to the Dashboard.",
            ],
        ],
        "widths": [1.36, 1.66, 3.48],
        "size": 7.3,
    },
    {"t": "h3", "text": "3.9.3 Exit points"},
    {
        "t": "p",
        "text": (
            "There are only four ways out, and three of them are deliberate. A person "
            "must never be able to lose money by navigating away: a half-completed payment, "
            "a half-completed wizard and an open dispute each have an explicit exit that "
            "resolves the state rather than abandoning it."
        )
    },
    {
        "t": "table",
        "head": ["Exit", "From", "Behaviour"],
        "rows": [
            [
                "Sign out",
                "`/app/settings/security` — SCR-MOB-21",
                "Revokes the refresh token family, clears local state, returns to `/` with "
                "an explanatory note. An in-flight payment cannot be signed out of; the "
                "action is disabled while a payment is `PENDING`.",
            ],
            [
                "Session expired",
                "Any tier-2 route",
                "`/login?returnTo=<path>` with a neutral *Your session ended* note. The path "
                "is preserved only if it passes the allowlist in 3.9.1.",
            ],
            [
                "Account restricted",
                "Any tier-2 route",
                "`/status` — SCR-WEB-17. The member can read their records and contact "
                "support. They cannot pay, join, create or invite. A `FROZEN` Ajo shows its "
                "records read-only.",
            ],
            [
                "Wizard abandoned",
                "Wizard step 1–6 — SCR-MOB-05",
                "The DRAFT is persisted. Exiting is silent and lossless; the Dashboard shows "
                "it under *Continue setting up* with a resume link. A DRAFT older than 30 "
                "days is archived and the organiser is told once, by notification, before "
                "it happens.",
            ],
        ],
        "widths": [0.94, 1.5, 4.06],
        "size": 7.3,
    },

    # =================================================================== 3.10
    {"t": "h2", "text": "3.10 Breadcrumb strategy"},
    {
        "t": "p",
        "text": (
            "Breadcrumbs exist to answer *how do I get back to something bigger*. They are "
            "therefore shown only where there is genuinely something bigger, they are never "
            "the primary navigation, and they are never shown on tier 1, on the Dashboard, "
            "or on any screen that is itself a top-level destination."
        )
    },
    {
        "t": "table",
        "head": ["Screen", "Breadcrumb", "Rationale"],
        "rows": [
            [
                "Ajo Detail",
                "`My Ajos › Lagos Market Monthly 2026`",
                "The Ajo is inside the member's collection. The Ajo name is truncated to 24 "
                "characters with a full name in the accessible label.",
            ],
            [
                "Members, Schedule, Contributions, Payouts, Economics",
                "`My Ajos › {ajo} › {tab}`",
                "These are views of an Ajo, not pages in a hierarchy. The middle crumb is "
                "the Ajo and the last is the current tab.",
            ],
            [
                "Pay Contribution",
                "`{ajo} › {round} contribution › Pay`",
                "No *My Ajos* crumb. The member is one action from money and every extra "
                "crumb is a chance to leave. Back returns to the contribution, and the "
                "back gesture does not lose the selected method.",
            ],
            [
                "Payment processing",
                "**No breadcrumb.** Non-dismissable.",
                "There is nothing to go back to. Leaving does not cancel the payment.",
            ],
            [
                "Payment receipt",
                "`{ajo} › {round} contribution › Receipt`",
                "Reached from the contribution, not from the payment. The receipt is the "
                "member's record, and the record hangs off the obligation.",
            ],
            [
                "Payout detail",
                "`Payouts › {round} payout`",
                "Global payouts list, then the record. The Ajo name is in the header, not "
                "the trail, because a member consults payouts across Ajos.",
            ],
            [
                "Dispute thread",
                "`Disputes › {reference}`",
                "Disputes are cross-Ajo; the Ajo is a field in the record, not a parent in "
                "the trail.",
            ],
            [
                "Settings, Security, Support, Profile",
                "**No breadcrumb.**",
                "Top-level destinations reached from the More sheet or the account menu.",
            ],
            [
                "All tier-3 screens",
                "**No breadcrumbs.** Fixed left rail only.",
                "An admin console is a two-dimensional work surface. A trail implies a "
                "containment relationship that does not exist.",
            ],
        ],
        "widths": [1.36, 1.86, 3.28],
        "size": 7.2,
    },
    {
        "t": "bullets",
        "items": [
            "The last crumb is the current page and is not a link; it carries "
            "`aria-current=\"page\"`.",
            "The separator is a decorative glyph, not a character read by a screen reader; "
            "the trail is a `<nav>` with a label and an ordered list.",
            "On mobile below 768 px the trail collapses to *Back ‹ {Ajo name}* plus the "
            "standard system back, because three crumbs at 375 px truncate into uselessness.",
            "A trail never shows a crumb the member cannot reach. A removed member or a "
            "cancelled Ajo removes its crumb.",
        ],
    },

    # =================================================================== 3.11
    {"t": "h2", "text": "3.11 SEO and the public/private boundary"},
    {
        "t": "p",
        "text": (
            "The rule is short: **indexable content is content that is true for every "
            "visitor, and AJO.ng has almost none of it that is interesting.** The marketing "
            "site is the product's search surface and it is optimised as such. The "
            "application and the admin console are not indexed at all, and that is enforced "
            "in three independent places so that a single missing tag is not a data leak."
        )
    },
    {"t": "h3", "text": "3.11.1 Indexing policy by tier"},
    {
        "t": "table",
        "head": ["Tier", "`<meta robots>`", "`robots.txt`", "In `sitemap.xml`", "Cache"],
        "rows": [
            [
                "Tier 1 content",
                "`index, follow, max-image-preview:large`",
                "Allowed",
                "Yes — 10 content URLs, `lastmod`, no parameters",
                "Public CDN, short TTL",
            ],
            [
                "Tier 1 auth pages",
                "`noindex, follow`",
                "Disallowed",
                "No",
                "No-store",
            ],
            [
                "`/invite/:token`",
                "`noindex, nofollow, noarchive`",
                "Disallowed",
                "No",
                "`no-store, private, no-cache`",
            ],
            [
                "`/status`",
                "`noindex, nofollow`",
                "Disallowed",
                "No",
                "`no-store`",
            ],
            [
                "Tier 2 `/app/**`",
                "`noindex, nofollow, noarchive`",
                "Disallowed",
                "No",
                "`no-store, private`",
            ],
            [
                "Tier 3 `/admin/**`",
                "`noindex, nofollow, noarchive`",
                "Disallowed **and** edge allowlist",
                "No",
                "`no-store, private`",
            ],
        ],
        "widths": [1.1, 1.66, 1.06, 1.2, 1.48],
        "size": 7.2,
    },
    {"t": "h3", "text": "3.11.2 Private data must never appear in a URL"},
    {
        "t": "p",
        "text": (
            "A URL is the least protected part of any system. It is written in the browser "
            "history, in the `Referer` header on outbound navigation, in server access "
            "logs, in analytics, in screenshots and in bug reports. Therefore:"
        )
    },
    {
        "t": "bullets",
        "items": [
            "**Identifiers are opaque ULIDs**, sortable by creation time, never sequential "
            "integers. A guessable `?member=1024` is a data leak with a working URL bar.",
            "**No name, phone number, email address, BVN, NIN, bank account number, "
            "contribution amount or Ajo name in any path or query parameter**, on any tier. "
            "Filters are expressed as enum tokens (`?status=OVERDUE`), never as free text "
            "containing a person's data.",
            "**No search term in a query string** on tier 2 or tier 3. A member searching "
            "for another member's name would write that name into a log. Admin search uses "
            "POST with a `no-store` response, or a server-side encrypted session reference.",
            "**`Referer-Policy: no-referrer`** on tier 2 and tier 3, and the invitation "
            "route additionally sets `Referrer-Policy: no-referrer` so that an accepted "
            "invitation cannot leak a token to a third party through an outbound link.",
            "**Analytics and error reporting redact** route identifiers at the edge; the "
            "raw URL reaches only the append-only access log with a retention limit (13.9).",
        ],
    },
    {"t": "h3", "text": "3.11.3 Structured data and social previews"},
    {
        "t": "bullets",
        "items": [
            "**Only tier 1 emits structured data.** `Organization` on `/about`, "
            "`FAQPage` on `/faq`, `WebSite` on `/`. No `Product`, no `Offer`, no "
            "`AggregateRating`, no `Review` — there are no reviews and inventing them would "
            "be a fabricated claim.",
            "**No tier-2 or tier-3 URL may be pasted into a social card.** A share sheet "
            "on a payment receipt shares `/fees` or a public help article, never the "
            "receipt URL.",
            "**Open Graph images are static per tier-1 page.** There is no server-rendered "
            "OG image for an Ajo, a receipt or a dispute, because rendering a member's "
            "money into an image that any crawler can fetch is the exact failure this "
            "section exists to prevent.",
            "**Canonical URLs are absolute, `https`, and omit the query string and any "
            "trailing slash variant.** `/fees` and `/fees/` are one URL, served once, with "
            "a 301 from the other.",
        ],
    },
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "Client-side rendering is a boundary, not a defence",
        "text": (
            "A `noindex` meta tag in the served HTML is honoured by compliant crawlers, but "
            "it is not an access control and it is not a defence against a determined "
            "reader. The real boundary is the **server**: tier-2 and tier-3 routes render "
            "no member data for an unauthenticated request, they redirect or return 401, "
            "and the response carries `Cache-Control: no-store` so that no shared cache "
            "ever holds a page containing one member's money. The meta tag is the second "
            "line, not the first. **Owner: Engineering.**"
        )
    },

    # =================================================================== 3.12
    {"t": "h2", "text": "3.12 URL naming conventions and reserved routes"},
    {"t": "h3", "text": "3.12.1 Conventions"},
    {
        "t": "table",
        "head": ["Rule", "Applies to", "Example"],
        "rows": [
            ["Lowercase, hyphen-separated, ASCII", "All static segments", "`/safety-and-trust`"],
            ["Plural nouns for collections, singular for one record", "All resource paths", "`/app/ajos`, `/app/ajos/:id`"],
            ["No file extensions, ever", "All routes", "`/fees` not `/fees.html`"],
            ["No trailing slash; `/x/` 301s to `/x`", "All routes", "`/app/ajos/` → `/app/ajos`"],
            ["Opaque ULID for every record id", "All `:id` segments", "`01HQ8S3K7M2Z4P9R6T1V0YB3DE`"],
            ["Enum tokens in query filters, lowercase snake", "All query strings", "`?status=overdue&round=3`"],
            ["Cursor pagination only, no page numbers", "All list routes", "`?cursor=eyJpZCI6…&limit=25`"],
            ["No verbs in paths", "All routes", "`/app/verification`, not `/app/verify`"],
            ["Deep paths only where the child is meaningless alone", "All routes", "`/app/ajos/:id/members` yes; `/app/people` no"],
            ["Same path shape on every tier-3 record", "Admin routes", "`/admin/ajos/:id`, `/admin/users/:id`"],
        ],
        "widths": [2.24, 2.06, 2.2],
        "size": 7.2,
    },
    {"t": "h3", "text": "3.12.2 Reserved routes and namespaces"},
    {
        "t": "p",
        "text": (
            "The following prefixes and names are reserved by this product. A future "
            "marketing page, campaign or Ajo name may not take them, because the router, "
            "the edge, the link preview service and the mobile deep-link handler all "
            "already claim them."
        )
    },
    {
        "t": "table",
        "head": ["Reserved", "Claimed by", "Rule"],
        "rows": [
            ["`/api/**`", "The v1 REST surface (`/api/v1`, CAN §6)", "Never serves HTML. An unknown API path returns an RFC-7807 body, never a 404 page."],
            ["`/app/**`", "Tier 2", "No new first-level segment may be added under `/app` without updating 3.3 and 3.6.2."],
            ["`/admin/**`", "Tier 3", "As above for 3.4 and 3.6.3."],
            ["`/invite/**`", "Invitation deep links", "The only public route that renders anything resembling a tier-2 screen."],
            ["`/webhooks/**`", "Provider callbacks (`POST /api/v1/webhooks/payments`)", "Signature-verified, unauthenticated, JSON only, never browser-navigable."],
            ["`/.well-known/**`", "RFC 8615", "Security contact, and the OAuth/redirect URIs used by the auth provider."],
            ["`/health`, `/ready`, `/live`", "Platform probes", "No auth, no body detail beyond status, excluded from access-log retention."],
            ["`/status`", "Account status notice (SCR-WEB-17)", "Deliberately public, `noindex`, and reachable only by state — never linked from the navigation."],
            ["`/favicon.ico`, `/robots.txt`, `/sitemap.xml`, `/manifest.webmanifest`", "Crawler and PWA surfaces", "Static, CDN-cached, and the only tier-1 files served from a different origin."],
            ["`/_next/**`, `/static/**`, `/assets/**`", "Build output", "Content-hashed, immutable, one-year cache. Not part of the product IA."],
            ["Ajo names", "All three tiers", "An Ajo name is user data and is never a path segment. `/app/ajos/:id` only, always. **This also means no vanity Ajo URLs in MVP.**"],
        ],
        "widths": [1.66, 1.86, 2.98],
        "size": 7.0,
    },
    {"t": "h3", "text": "3.12.3 Redirects and URL evolution"},
    {
        "t": "bullets",
        "items": [
            "**A URL, once published, is permanent.** Tier-1 content URLs and any tier-2 "
            "URL that has appeared in an email, an SMS, a receipt or a statement are never "
            "renamed. If the IA must change, the old path is registered as a 301 and kept "
            "in the redirect table indefinitely.",
            "**`returnTo` is a vulnerability if it is a string.** It is validated against "
            "an allowlist of internal path patterns before it is stored in the session, "
            "and it is never rendered as a raw href without that validation. This is the "
            "single most common open-redirect defect in applications of this shape.",
            "**Link shortening is not used.** Every SMS and email link is the canonical "
            "path with a signed, single-use, expiring token in a fragment, not a query "
            "parameter, so that the token is never sent to a server that does not need it "
            "and never lands in a proxy log.",
            "**UTM parameters are consumed once and stripped.** The first landing stores "
            "them against the anonymous visitor; every internal link generated from that "
            "page omits them.",
        ],
    },
    {"t": "callout",
        "kind": "NOTE",
        "title": "One reservation that is easy to get wrong",
        "text": (
            "Ajo names are user data. A route such as `/app/ajos/lagos-market-2026` would "
            "be a vanity URL that leaks a user's chosen name into every log and every "
            "shared screenshot, would collide the moment two people create an Ajo with the "
            "same name, and would make the Ajo name unrenameable once shared. Tier 2 uses "
            "opaque ULIDs throughout. If vanity Ajo URLs are wanted later they must be a "
            "subdomain with a slug that is a hash, not a name — and that is a separate "
            "decision with its own reserved namespace. **Owner: Founders.**"
        )
    },
]
