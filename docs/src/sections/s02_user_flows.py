"""
Section 2 — User Flow Specification.

Source of truth: docs/src/CANONICAL.md
Authoring contract: docs/src/AUTHORING.md
Cross-references: section 1 (product requirements, business-rule register BR-001
to BR-032, user stories US-01 to US-38, risks R1 to R14, dependencies DEP-01
to DEP-15), section 19 (error and edge-case register EC-001 onwards).

Every flow in this section is written against the six canonical roles
(`user`, `ajo_organizer`, `ajo_member`, `support`, `risk_officer`,
`super_admin`) and against the canonical state machines. The 2% platform fee
is quoted exactly as CANONICAL.md defines it: a member owing NGN 1,000.00 is
charged NGN 1,020.00; the recipient of a ten-member round receives the base
pool NGN 10,000.00, never NGN 10,200.00. The tagline is "Your Ajo. Your
Story."
"""

BLOCKS = [
    {"t": "h1", "text": "2. User Flow Specification"},

    # =================================================================== 2.0
    {
        "t": "lead",
        "text": (
            "This section specifies, step by step, what every actor does and what the "
            "platform does in response, across sixteen end-to-end flows. Each flow is "
            "written to be testable: a diagram, a step table with a rule reference on "
            "every step, the happy path in prose, and a branch table covering every "
            "alternate and failure path. Flow 2.17 traces every flow back to the "
            "functional requirements it satisfies, the screens it touches and the API "
            "endpoints it calls."
        )
    },
    {
        "t": "p",
        "text": (
            "**Reading convention.** Every step in every table carries a rule reference. "
            "`BR-nnn` refers to the business-rule register in section 1.21. `FR-*` refers "
            "to a functional requirement in section 1.17. `US-nn` refers to a user story in "
            "section 1.20. `NFR-*` refers to a non-functional requirement in section 1.18. "
            "`R-n` refers to a risk and `DEP-nn` to a dependency in sections 1.25 and 1.23. "
            "`D-nn` refers to an open decision in section 9 of CANONICAL.md. `A-nn` refers "
            "to an assumption in section 1.22. `EC-nnn` refers to an edge case in section "
            "19. `SCR-*` refers to a screen in the screen-ID key below. Where a step depends "
            "on something not yet decided, the reference carries the open decision or the "
            "assumption rather than a fabricated answer."
        )
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "What a flow is and is not",
        "text": (
            "A flow is a sequence of user intents and system obligations, not a page map. "
            "Where a flow crosses a payment provider, the provider's behaviour is modelled "
            "as a state, not as an assumption about capability. **No flow in this section "
            "asserts that ProvidusUnity can do anything that has not been confirmed in "
            "writing.** Every provider-dependent step is written so that it remains correct "
            "if the provider's behaviour differs, and every place where that matters carries "
            "an `ASSUMPTION` or a `DECISION` callout."
        )
    },
    {"t": "h2", "text": "2.0 How to read this section"},
    {"t": "p",
     "text": (
        "Three things are settled before the flows begin, because every flow below depends "
        "on them: how screens are identified, what the create and activate endpoints "
        "actually do, and how money is written in the worked examples."
     )},
    {"t": "h3", "text": "2.0.1 Screen-ID key"},
    {
        "t": "p",
        "text": (
            "The screen inventory in section 7 of CANONICAL.md is given stable identifiers "
            "here so that the flow tables, the section 4 wireframes and the section 19 edge "
            "cases can all refer to the same screen unambiguously. No screen is added to or "
            "removed from the canonical inventory by this section; the identifiers are an "
            "index over it."
        )
    },
    {
        "t": "table",
        "head": ["ID", "Screen", "Group"],
        "rows": [
            ["SCR-MKT-01", "Home", "Marketing"],
            ["SCR-MKT-02", "How It Works", "Marketing"],
            ["SCR-MKT-03", "Features", "Marketing"],
            ["SCR-MKT-04", "Safety & Trust", "Marketing"],
            ["SCR-MKT-05", "Fees", "Marketing"],
            ["SCR-MKT-06", "About", "Marketing"],
            ["SCR-MKT-07", "FAQ", "Marketing"],
            ["SCR-MKT-08", "Contact", "Marketing"],
            ["SCR-MKT-09", "Login", "Marketing"],
            ["SCR-MKT-10", "Register", "Marketing"],
            ["SCR-MKT-11", "Terms & Conditions", "Marketing"],
            ["SCR-MKT-12", "Privacy", "Marketing"],
            ["SCR-APP-01", "Dashboard", "App"],
            ["SCR-APP-02", "My Ajos", "App"],
            ["SCR-APP-03", "Create Ajo wizard (7 steps)", "App"],
            ["SCR-APP-04", "Join Ajo", "App"],
            ["SCR-APP-05", "Ajo Detail", "App"],
            ["SCR-APP-06", "Members", "App"],
            ["SCR-APP-07", "Schedule", "App"],
            ["SCR-APP-08", "Contributions", "App"],
            ["SCR-APP-09", "Payments", "App"],
            ["SCR-APP-10", "Payouts", "App"],
            ["SCR-APP-11", "Transactions", "App"],
            ["SCR-APP-12", "Notifications", "App"],
            ["SCR-APP-13", "Support", "App"],
            ["SCR-APP-14", "Disputes", "App"],
            ["SCR-APP-15", "Profile", "App"],
            ["SCR-APP-16", "Settings", "App"],
            ["SCR-APP-17", "Security", "App"],
            ["SCR-APP-18", "Help", "App"],
            ["SCR-APP-19", "KYC / identity verification", "App"],
            ["SCR-ADM-01", "Overview", "Admin"],
            ["SCR-ADM-02", "Users", "Admin"],
            ["SCR-ADM-03", "Ajos", "Admin"],
            ["SCR-ADM-04", "Disputes", "Admin"],
            ["SCR-ADM-05", "Risk / Fraud", "Admin"],
            ["SCR-ADM-06", "Verification", "Admin"],
            ["SCR-ADM-07", "Reports", "Admin"],
            ["SCR-ADM-08", "Audit Logs", "Admin"],
            ["SCR-ADM-09", "Settings", "Admin"],
        ],
        "widths": [1.23, 4.09, 1.18],
        "size": 8.0,
    },
    {
        "t": "callout",
        "kind": "ASSUMPTION",
        "title": "Screen identifiers are an indexing convention introduced here",
        "text": (
            "CANONICAL.md section 7 names the screens but does not number them. The "
            "`SCR-*` scheme is introduced by this specification so that flows, wireframes and "
            "the edge-case register can be cross-referenced. The screen list itself is "
            "unchanged. Where a flow requires a surface that is not in the canonical "
            "inventory, this is stated explicitly as an addition rather than assumed."
        )
    },
    {"t": "h3", "text": "2.0.2 Endpoint reconciliation for the create and activate transitions"},
    {
        "t": "p",
        "text": (
            "Two places in the canonical surface need an explicit reading before the flows "
            "can be written. Both are recorded here rather than resolved silently, because "
            "getting either wrong would corrupt the Ajo state machine in flow 2.2."
        )
    },
    {
        "t": "table",
        "head": ["Canonical text", "Apparent conflict", "Reading adopted in this section"],
        "rows": [
            [
                "`POST /ajos/:id/activate` (CAN §6) against the transition `ENROLLMENT → "
                "ACTIVE` on the guard *every position filled, or day 5 reached* (CAN §3).",
                "The endpoint name suggests an organiser action, but the guard is a system "
                "condition, so an endpoint of that name would let an organiser activate a "
                "half-filled Ajo.",
                "**`POST /ajos/:id/activate` performs `OPEN_ENROLLMENT`, the DRAFT to "
                "ENROLLMENT transition, and requires a recorded reason.** The name is "
                "retained because the endpoint path is canonical; its semantics are pinned "
                "here. The ENROLLMENT to ACTIVE transition is system-driven and is never "
                "reachable through this endpoint. EC-050 and EC-051 depend on this reading.",
            ],
            [
                "`POST /ajos/:id/members` (CAN §6) against BR-006, *membership is by "
                "invitation only; at MVP no member may be added to an Ajo without their own "
                "acceptance of an invitation*.",
                "A direct member-creation endpoint appears to permit the platform to add a "
                "member who never accepted anything.",
                "**`POST /ajos/:id/members` creates an invitation-bound membership from a "
                "token already accepted by the invitee, or from an invitation issued and "
                "accepted out of band.** It is never a path by which a member is added "
                "without their own acceptance, and it is the path used to attach a member who "
                "accepted an invitation on a device that has since been reset. A separate "
                "organiser-initiated invitation creation belongs to `POST /invitations`.",
            ],
        ],
        "widths": [2.06, 1.9, 2.54],
        "size": 7.6,
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Two naming decisions that the engineering team must confirm before build",
        "text": (
            "The two readings above are correct as specifications but ugly as API design. "
            "The recommended change is to keep `POST /ajos/:id/activate` for the DRAFT to "
            "ENROLLMENT transition for backward compatibility with the canonical path list, "
            "add `POST /ajos/:id/open-enrollment` as the clear name, and deprecate the "
            "ambiguous one. **Owner: Engineering and Founders. Decision required before the "
            "build starts, not during it.** The behaviour is safe either way; only the name "
            "is in question."
        )
    },
    {
        "t": "h3",
        "text": "2.0.3 Money values used in every worked example in this section",
    },
    {
        "t": "p",
        "text": (
            "Every flow that moves or explains money uses the same canonical example, so "
            "that a member reading a receipt, an organiser reading a wizard review step and "
            "an engineer reading a ledger posting are all looking at the same numbers."
        )
    },
    {
        "t": "table",
        "head": ["Item", "Value"],
        "rows": [
            ["Members", "10"],
            ["Contribution per member per round", "NGN 1,000.00"],
            ["Platform fee (2%), recorded as `fees_income`", "NGN 20.00"],
            ["**Total charged to the member per round**", "**NGN 1,020.00**"],
            ["**Base pool paid to the recipient at their turn**", "**NGN 10,000.00**"],
            ["Total collected in the round", "NGN 10,200.00"],
            ["Platform fee retained in the round", "NGN 200.00"],
            ["Rounds", "10"],
            ["Total paid in by one member across the Ajo", "NGN 10,200.00"],
            ["**Total received by the recipient at their turn**", "**NGN 10,000.00**"],
            ["Platform fee over the full Ajo", "NGN 2,000.00"],
            ["Total collected across the Ajo", "NGN 102,000.00"],
        ],
        "widths": [4.29, 2.21],
        "size": 8.5,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Read the difference twice",
        "text": (
            "The member pays NGN 1,020.00. The member receives NGN 10,000.00. Those are not "
            "the same transaction, and the gap between them is the entire reason the fee can "
            "be charged without ever reducing a promise. NGN 10,200.00 is collected in the "
            "round. NGN 200.00 of it is `fees_income`. NGN 10,000.00 is the pot. The pot is "
            "what the member was promised, so the pot is what the member gets (BR-010, "
            "BR-012, C-02)."
        )
    },
    {"t": "pagebreak"},

    # =================================================================== 2.1
    {"t": "h2", "text": "2.1 New user: landing to first dashboard"},
    {"t": "h3", "text": "2.1.1 Purpose"},
    {
        "t": "p",
        "text": (
            "A person who has never heard of AJO.ng arrives, understands what an Ajo is and "
            "what the 2% fee is, creates an account, verifies that the account is theirs, "
            "completes a profile, and lands on a dashboard that shows them one thing to do "
            "rather than an empty screen. The flow exists to reach a state where the person "
            "can be trusted with a payment: an account that is theirs, at an address they "
            "control, under a name that can be verified. Nothing in this flow can move money, "
            "and nothing in it can begin without the person's own action."
        )
    },
    {"t": "h3", "text": "2.1.2 Swimlane"},
    {
        "t": "code",
        "text": """
VISITOR        AJO.ng  (API)        PROVIDER        EMAIL / SMS
   |               |                   |                |
   |  Home         |                   |                |
   |-- GET / ------>|  marketing only  |                |
   |  "How it      |  no account, no    |                |
   |   works"      |  tracking that    |                |
   |  "Fees"       |  identifies a      |                |
   |               |  person            |                |
   |  Register     |                   |                |
   |-------------->|  POST /auth/      |                |
   |               |   register        |                |
   |               |  account created  |                |
   |               |  UNVERIFIED  -----+--------------->|  account.
   |               |                   |                |  registered
   |<--------------|  generic result  |                |
   |               |  (no enumeration) |                |
   |  Verify email |                   |                |
   |--------------.  GET /auth/       |                |
   |               |   verify-email    |                |
   |               |  EMAIL_VERIFIED   |                |
   |  Verify phone |                   |                |
   |-------------->|  POST /auth/otp/  |                |
   |               |   request  -------+--------------->|  OTP
   |  Enter OTP    |  POST /auth/otp/  |                |
   |-------------->|   verify  (max 5) |                |
   |               |  PHONE_VERIFIED   |                |
   |  Profile      |                   |                |
   |-------------->|  PATCH /profile  |                |
   |               |  POST /profile/   |                |
   |               |   avatar         |                |
   |  Identity     |  POST /verification/identity      |
   |-------------->|  POST /verification/bvn           |
   |               |  VERIFICATION_REVIEW or APPROVED  |
   |               |  (or FAILED -> 2.14) -----+------->|  verification.
   |               |                   |                |  approved
   |  Dashboard    |                   |                |
   |-------------->|  GET /ajos        |                |
   |               |  GET /contributions  (empty)     |
   |               |  GET /payouts      (empty)       |
   |               |  GET /notifications               |
   |<--------------|  role = `user`    |                |
   |  "Create an Ajo" or "I have an invitation"        |
""",
    },
    {"t": "h3", "text": "2.1.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.1.1", "Visitor", "SCR-MKT-01",
                "Lands on Home. Reads *Your Ajo. Your Story.*",
                "No account exists and none is created. Analytics record page views with no "
                "personal identifier. Marketing surfaces carry no imperative to enter a "
                "payment detail.",
                "NFR-AVL-001; section 1.1",
            ],
            [
                "2.1.2", "Visitor", "SCR-MKT-02 / 03 / 05",
                "Reads How It Works, Features and Fees to understand the model.",
                "Fees page states the 2% fee in the canonical form: contribution NGN "
                "1,000.00, fee NGN 20.00, total charged NGN 1,020.00, base pool received "
                "NGN 10,000.00. It states that an Ajo earns no interest and that no return "
                "is implied.",
                "BR-010, BR-012, BR-027, G3",
            ],
            [
                "2.1.3", "Visitor", "SCR-MKT-10",
                "Opens Register and submits full name, email, phone in E.164 form, password "
                "of at least 10 characters, and state of residence.",
                "`POST /auth/register`. Account created with status `unverified` and the "
                "single default role `user` assigned. Raw identifiers are not stored beyond "
                "what the account requires. Response is byte-identical whether or not the "
                "email or phone already exists.",
                "FR-AUTH-001, FR-AUTH-002, BR-030, US-01, US-03, NFR-SEC-002, NFR-SEC-003",
            ],
            [
                "2.1.4", "AJO.ng", "—",
                "Dispatches `account.registered`.",
                "Push and email dispatched within 60 seconds at p99. No SMS, because this is "
                "not a money-critical or security event. Dispatch failure does not block "
                "registration.",
                "CAN §8, FR-NOTIF-001, NFR-PERF-002, FR-NOTIF-003",
            ],
            [
                "2.1.5", "New user", "SCR-APP-15",
                "Opens the verification prompt the app shows as its single next action and "
                "clicks the link in the email.",
                "`GET /auth/verify-email` with a single-use, expiring token. Email moves to "
                "`verified`. A replayed link returns the same success page and changes "
                "nothing.",
                "FR-AUTH-003, US-01, NFR-SEC-008",
            ],
            [
                "2.1.6", "New user", "SCR-APP-15",
                "Requests and enters the phone OTP.",
                "`POST /auth/otp/request` then `POST /auth/otp/verify`. OTP is 6 digits, "
                "expires after 5 minutes, is limited to 5 attempts, and the endpoint is rate "
                "limited with exponential backoff. Phone moves to `verified`.",
                "FR-AUTH-004, FR-AUTH-005, NFR-SEC-004, US-01",
            ],
            [
                "2.1.7", "New user", "SCR-APP-15",
                "Completes the profile: display name, occupation, city, and an optional "
                "avatar.",
                "`PATCH /profile` and `POST /profile/avatar`. Avatar is validated for type, "
                "size and content server-side and re-encoded before storage. Profile is not "
                "public to other members; members see only what the Ajo terms require.",
                "FR-PROF-001 to FR-PROF-003, NFR-SEC-006",
            ],
            [
                "2.1.8", "New user", "SCR-APP-19",
                "Starts identity verification. Submits the BVN check, and a CAC check where "
                "the member is a business.",
                "`POST /verification/identity` and `POST /verification/bvn`, then "
                "`GET /verification/:id`. Only the result, the timestamp and the provider "
                "reference are stored. The raw BVN is never persisted, never logged and never "
                "returned.",
                "FR-KYC-001, FR-KYC-002, US-06, R10, NFR-AUD-002",
            ],
            [
                "2.1.9", "New user", "SCR-APP-19",
                "Receives the outcome and completes KYC.",
                "On approval, `verification.approved` is sent on push and email. On failure "
                "the flow branches to 2.14. KYC rejection never leaves the user on a blank "
                "screen; it always names the next action.",
                "CAN §8, US-02, K-21",
            ],
            [
                "2.1.10", "New user", "SCR-APP-01",
                "Lands on the dashboard.",
                "`GET /ajos`, `GET /contributions`, `GET /payouts`, `GET /notifications`. "
                "With no Ajos the dashboard shows a single primary action and, if an "
                "invitation link brought the user here, a pending invitation card. An "
                "unverified user sees no Ajo content at all and is given the reason.",
                "US-02, US-03, G2, FR-CON-001",
            ],
            [
                "2.1.11", "New user", "SCR-APP-01",
                "Chooses a next step: create an Ajo (2.2) or open an invitation (2.3).",
                "Role assignment is derived from what the user does next, not from what they "
                "register. `ajo_organizer` attaches on creating an Ajo; `ajo_member` attaches "
                "on joining one. A user can hold both across different Ajos.",
                "CAN §2, FR-MEM-001",
            ],
        ],
        "widths": [0.49, 0.78, 0.78, 1.46, 2.0, 0.99],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.1.4 Happy path"},
    {
        "t": "p",
        "text": (
            "The visitor reads the Fees page, sees the 2% stated as a separate number from "
            "the contribution, and registers. The account is created `unverified`. The "
            "verification email arrives within a minute and the OTP SMS shortly after. The "
            "user verifies both, completes a profile with a name and an occupation, "
            "submits the identity check, and is approved. The dashboard loads with no Ajos, "
            "no contributions, no payouts and no unread notifications, and offers exactly "
            "two things: *Create an Ajo* and *Open an invitation*. The user's role is "
            "`user`. No money has moved. No ledger entry exists. The system holds an "
            "account, a verified email, a verified phone, a profile and a verification "
            "result, and nothing else."
        )
    },
    {"t": "h3", "text": "2.1.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The email or phone is already registered",
                "No second account is created. The response is byte-identical to the "
                "success path and does not reveal that the account exists.",
                "SCR-MKT-10",
                "*If that email or number is already registered, sign in or reset your "
                "password.* No difference in wording, status code or timing.",
                         "Sign in, or `POST /auth/password/forgot`. Enumeration is blocked in "
         "body, status and timing. NFR-S, US-03, EC-119.",
            ],
            [
                "Registration is submitted from a public or shared device",
                "A new session is created and the device is recorded as unrecognised. No "
                "money capability is attached until verification completes.",
                "SCR-MKT-10",
                "*We will ask you to confirm your phone before you can do anything with "
                "money.*",
                         "Complete steps 2.1.5 and 2.1.6. Sessions can be revoked from "
         "SCR-APP-17, EC-120.",
            ],
            [
                "The email link is not clicked within its validity window",
                "The token expires. The account stays `unverified`; nothing is lost.",
                "SCR-APP-15",
                "*This link has expired. Send a new one.*",
                                  "Re-request a verification link. Re-requesting is rate limited, EC-121.",
            ],
            [
                "The OTP request is spammed or the OTP is guessed",
                "The endpoint rate limits with exponential backoff; the account is "
                "temporarily locked for that verification route after 5 failed attempts. No "
                "lockout of the whole account, because a lockout is a denial-of-service "
                "against the member.",
                "SCR-APP-15",
                "*Too many attempts. Try again in N minutes.*",
                         "Wait out the backoff, or request a new OTP which invalidates the "
         "previous one, EC-109.",
            ],
            [
                "Email dispatch fails at the provider",
                "Registration stands. The dispatch job retries with backoff and opens a "
                "delivery-exception record if it still fails. The user is not blocked from "
                "continuing.",
                "SCR-APP-15",
                "*We could not send the email just now. Use resend, or call us on the number "
                "on the Help screen.*",
                         "Resend, or contact support. Dispatch failures are monitored; see. "
         "NFR-AVL-003 requires that no registration be lost to a mail outage, "
         "EC-071.",
            ],
            [
                "The user abandons onboarding at any step",
                "The account persists in `unverified` with a resumable onboarding state. No "
                "Ajo content is visible.",
                "SCR-APP-01",
                "*Finish setting up your account.* One clear next action, never a blank "
                "screen.",
                         "Resume at the incomplete step. US-02, EC-122.",
            ],
            [
                "The phone number is a Nigerian number that is later reassigned to a new "
                "subscriber",
                "At verification time the number is bound to the account as a single verified "
                "phone. If the provider later reports the number as reassigned, a risk event "
                "is raised for review; the account is not silently migrated.",
                "SCR-APP-19 / SCR-ADM-05",
                "The member is asked to confirm the number. The officer sees the reassignment "
                "signal in the Risk screen.",
                                  "Risk review decides: continue, require re-verification, or freeze, "
         "EC-108.",
            ],
            [
                "The user is identified as a minor or as acting for someone else",
                "Onboarding is paused and a risk event is raised. No Ajo may be created or "
                "joined in that state.",
                "SCR-APP-19",
                "*We need to confirm who this account belongs to before you can continue.*",
                         "Verified identity by a human at `risk_officer`, EC-123.",
            ],
        ],
        "widths": [1.25, 1.44, 0.72, 1.35, 1.74],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =================================================================== 2.2
    {"t": "h2", "text": "2.2 Create Ajo: seven-step wizard to invitations issued"},
    {"t": "h3", "text": "2.2.1 Purpose"},
    {
        "t": "p",
        "text": (
            "An organiser turns an intention into a set of locked terms and a list of named "
            "people. The flow must be completable on a mid-range Android over 3G in a few "
            "minutes, because the organiser is unpaid and every minute of friction is a "
            "chance for them to stop (R8, G9, A-03). It must end with the organiser "
            "understanding exactly what each member will pay, what the recipient will "
            "receive, and what happens if the group does not fill, and it must never require "
            "the organiser to handle money at any point (BR-022)."
        )
    },
    {"t": "h3", "text": "2.2.2 Swimlane"},
    {
        "t": "code",
        "text": """
ORGANISER         WIZARD             AJO.ng API              INVITEE
   |  Dashboard     |                  |                       |
   |  "Create"      |                  |                       |
   |--------------->|  step 1 Configure|                       |
   |  name, size,   |----------------->| POST /ajos            |
   |  currency,     |                  |  201 ajo id, DRAFT     |
   |  frequency     |                  |  role: ajo_organizer  |
   |  step 2 Amount |                  |                       |
   |  contribution  |----------------->| PATCH /ajos/:id       |
   |  = NGN 1,000.00|  fee preview:    |                       |
   |  step 3 Freq   |  NGN 20.00       |                       |
   |  step 4 Dur.   |  charged         |                       |
   |  = 10 rounds   |  NGN 1,020.00    |                       |
   |  step 5 Members|----------------->| POST /invitations     |
   |  names/numbers |  tokens minted,  |  invitation.received->|  SMS + email
   |                |  single-use,     |---------------------->|  (brings 2.3)
   |                |  expiring,       |                       |
   |                |  fee disclosed   |                       |
   |  step 6 Order  |  proposer/       |                       |
   |  drag to order |  proposer/claim |--------------------->|  claim a slot
   |  step 7 Review |----------------->| GET /ajos/:id         |
   |  base pool     |  summary         |                       |
   |  NGN 10,000.00 |                  |                       |
   |  total         |                  |                       |
   |  NGN 102,000.00|                  |                       |
   |  [Acknowledge] |                  |                       |
   |  Create        |----------------->| POST /ajos/:id/       |
   |                |                  |   activate            |
   |                |                  |  DRAFT -> ENROLLMENT  |
   |                |                  |  5-day clock starts   |
   |  Invite more   |----------------->| POST /invitations     |
   |  Track         |                  | GET /ajos/:id/members |
   |                |                  | GET /invitations      |
""",
    },
    {"t": "h3", "text": "2.2.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.2.1", "User as `ajo_organizer`", "SCR-APP-01",
                "Taps *Create an Ajo* from the dashboard.",
                "Wizard opens at step 1. The wizard is resumable: a partially configured DRAFT "
                "Ajo is restored exactly as it was left, and the draft is visible in My Ajos "
                "labelled *Draft*.",
                "FR-AJO-001, US-07, F1",
            ],
            [
                "2.2.2", "Organiser", "SCR-APP-03 step 1",
                "Names the Ajo, sets the member count, the currency (NGN only at MVP) and the "
                "start date.",
                "`POST /ajos` creates the Ajo in `DRAFT` with `version = 1` and assigns the "
                "organiser scope. Currency other than NGN is refused with a stated reason. "
                "Maximum size is capped by a configurable limit.",
                "FR-AJO-002, C-07, D-08, BR-031",
            ],
            [
                "2.2.3", "Organiser", "SCR-APP-03 step 2",
                "Enters the contribution, NGN 1,000.00.",
                "`PATCH /ajos/:id`. The screen shows, live and before any commitment: "
                "contribution NGN 1,000.00, platform fee 2% NGN 20.00, total charged NGN "
                "1,020.00. Fee is computed in kobo as `(amount_kobo * 200 + 5000) / 10000`, "
                "half-up, and is final at this point.",
                "BR-010, BR-011, BR-031, FR-AJO-005, US-08",
            ],
            [
                "2.2.4", "Organiser", "SCR-APP-03 step 3",
                "Chooses the collection frequency: weekly or monthly at MVP.",
                "Frequency sets the due-date generator for every round. Frequency is "
                "immutable after activation; the screen says so before the organiser can "
                "wonder later.",
                "FR-SCH-001, BR-005, FR-AJO-011",
            ],
            [
                "2.2.5", "Organiser", "SCR-APP-03 step 4",
                "Confirms the duration, which equals the member count: 10 members implies 10 "
                "rounds.",
                "The screen shows the total across the Ajo: each member pays NGN 10,200.00 "
                "over 10 rounds; the recipient receives NGN 10,000.00; AJO.ng retains NGN "
                "2,000.00; total collected across the Ajo is NGN 102,000.00.",
                "FR-AJO-005, BR-010, BR-012, US-09",
            ],
            [
                "2.2.6", "Organiser", "SCR-APP-03 step 5",
                "Names the people to invite, by phone number or by an existing AJO.ng contact.",
                "`POST /invitations` mints one single-use, expiring, revocable token per "
                "invitee. Each invitation discloses the organiser's name, the member count, "
                "the contribution, the fee, the frequency, the total duration, the total the "
                "invitee will pay and what happens on a missed payment. It reveals nothing "
                "about other members and nothing about the pot value.",
                "FR-INV-001, FR-INV-002, FR-INV-004, BR-004, BR-006, NFR-SEC-008, US-09, "
                "US-10",
            ],
            [
                "2.2.7", "Invitee", "—",
                "Receives `invitation.received`.",
                "Push, email and SMS, immediately. This is a money-critical event, so SMS is "
                "permitted here. The link resolves to the invitation, not to a login wall.",
                "CAN §8, FR-NOTIF-001, FR-NOTIF-003",
            ],
            [
                "2.2.8", "Members", "SCR-APP-03 step 6",
                "Proposes and settles the payout order.",
                "`POST /ajos/:id/positions/claim` lets a member claim an unclaimed position. "
                "`POST /ajos/:id/positions/reorder` records the organiser's proposal. Until "
                "activation every position is mutable, and the screen states that the order "
                "is provisional in exactly those words.",
                "FR-POS-003, FR-POS-004, BR-002 (pre-activation only), US-18",
            ],
            [
                "2.2.9", "Organiser", "SCR-APP-03 step 7",
                "Reviews the complete economics and acknowledges the terms.",
                "The review shows the whole table from 2.0.3, the fee as a separate line, the "
                "organiser's non-guarantor role (BR-008), the complete-cycle commitment "
                "(BR-004), the 5-day enrollment window and its cancellation consequence, and "
                "the position-lock rule. A commit action that does not display the fee is "
                "prohibited by design, not by copy.",
                "BR-011, BR-004, BR-008, BR-001, BR-002, G3, R9",
            ],
            [
                "2.2.10", "Organiser", "SCR-APP-03 step 7",
                "Taps *Create Ajo and open enrollment*.",
                "`POST /ajos/:id/activate` performs `OPEN_ENROLLMENT`: DRAFT to ENROLLMENT, "
                "guarded by at least 2 positions, contribution set and frequency set. The "
                "5-day window starts counting from this instant in UTC and the countdown is "
                "shown to the organiser and to every member in Africa/Lagos time with the "
                "zone stated explicitly.",
                         "CAN §3, BR-001, NFR-LOC-003, EC-050, EC-069"
            ],
            [
                "2.2.11", "Organiser", "SCR-APP-06",
                "Monitors members who have not joined, resends invitations and sees who has "
                "claimed a position.",
                "`GET /invitations`, `POST /invitations/resend`, `GET /ajos/:id/members`, "
                "`GET /ajos/:id/positions`. Resend is rate limited and never duplicates a "
                "membership. The organiser can send reminders but cannot collect, hold or "
                "reconcile money.",
                "FR-INV-005, FR-MEM-004, BR-022, FR-ADM-012",
            ],
            [
                "2.2.12", "Organiser", "SCR-APP-05",
                "Sees the funding progress and the Ajo economics read-only.",
                "`GET /ajos/:id/summary` shows positions claimed, contributions collected, "
                "fee retained and the base pool target. The pot figure shown to members is "
                "the base pool, never the collected total.",
                "FR-AJO-017, FR-POS-002, BR-012",
            ],
        ],
        "widths": [0.49, 0.84, 0.78, 1.41, 1.95, 1.03],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.2.4 Happy path"},
    {
        "t": "p",
        "text": (
            "The organiser opens the wizard, names the Ajo *Lagos Market Monthly 2026*, sets "
            "10 members at NGN 1,000.00 monthly, and works through seven steps. At step 2 the "
            "screen already shows the fee as a separate line: NGN 20.00, charged on top, "
            "total NGN 1,020.00. At step 5 the organiser sees the whole picture: every "
            "member will pay NGN 10,200.00 across the Ajo, the person whose turn it is will "
            "receive NGN 10,000.00, AJO.ng keeps NGN 2,000.00, and NGN 102,000.00 will pass "
            "through the arrangement in total. At step 6 the organiser proposes an order and "
            "members claim positions. At step 7 the organiser reads that they are a "
            "facilitator and not a guarantor, that joining commits a member to every "
            "remaining round, that the order locks on activation, and that if the group is "
            "not full in five days everything is cancelled and refunded. The organiser "
            "taps create. The Ajo moves to ENROLLMENT, a five-day countdown appears, and ten "
            "invitations have already gone out by SMS, email and push. No money has moved. "
            "The organiser's next job is to wait, and the software sends the reminders."
        )
    },
    {"t": "h3", "text": "2.2.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "Contribution amount is below the configured minimum or above the "
                "contribution cap",
                "The step cannot be committed. The cap and its rationale are shown before the "
                "attempt, not after the error.",
                "SCR-APP-03 step 2",
                "*This amount is outside the range AJO.ng allows for one contribution.*",
                         "Choose an amount inside the range. The cap is a fraud control and is "
         "configurable only by `super_admin` with a versioned, audited change. "
         "D-08, EC-021.",
            ],
            [
                "The organiser sets fewer than 2 positions",
                "`OPEN_ENROLLMENT` guard fails. The Ajo stays in DRAFT.",
                "SCR-APP-03 step 4",
                "*An Ajo needs at least two members. One member is a savings account, not an "
                "Ajo.*",
                         "Raise the member count. CAN §3 guard, EC-060."
            ],
            [
                "The organiser abandons the wizard and returns days later",
                "The Ajo is still in DRAFT. A draft has no clock running on it, so an "
                "abandoned draft does not silently cancel anything.",
                "SCR-APP-02 / SCR-APP-03",
                "*Your Ajo is saved as a draft. Nothing has started yet.*",
                         "Resume the wizard, or delete the draft. US-07, EC-061.",
            ],
            [
                "Day 5 arrives with positions unfilled",
                "The system transitions the Ajo to CANCELLED with a recorded reason, "
                "automatically. The organiser cannot extend the window.",
                "SCR-APP-05 / SCR-APP-12",
                "To the organiser: *Enrollment closed after 5 days with 7 of 10 positions "
                "filled. Nothing was collected and nothing is owed.*",
                         "Start again with better recruitment. Any prepayment is refunded in "
         "full. BR-001, EC-050.",
            ],
            [
                "The organiser tries to change contribution, frequency, size or order after "
                "activation",
                "Refused at the API and recorded as a refused attempt. The screen explains the "
                "only legal alternative.",
                "SCR-APP-05",
                "*These terms are locked when the Ajo activates. The only change available "
                "after activation is a formal replacement request.*",
                         "Cancel and create a new Ajo, or raise a replacement request. BR-002, "
         "BR-005, US-12, EC-054.",
            ],
            [
                "The organiser tries to remove a member after activation",
                "Refused for every role, including `super_admin`. Removal is pre-activation "
                "only.",
                "SCR-APP-06",
                "*Members cannot be removed once the Ajo is active. A replacement must take "
                "the position.*",
                         "Raise a replacement or transfer request. BR-007, EC-086.",
            ],
            [
                "A phone number is entered that is already an active member of the same Ajo",
                "No second membership is created; the existing member is offered to open their "
                "existing position instead.",
                "SCR-APP-03 step 5",
                "*This number is already in the Ajo. Send them their invitation again.*",
                         "Resend the invitation. One identity, one membership. BR-030, EC-094.",
            ],
            [
                "An invitation is sent to someone who will never accept it",
                "The organiser sees the unfilled position with the days remaining. No "
                "escalation, no pressure list, no automatic bulk messaging.",
                "SCR-APP-06",
                "*7 of 10 positions filled. Enrollment closes in 3 days.*",
                         "Invite someone else. BR-029, R12, EC-062.",
            ],
            [
                "The organiser attempts an action on a CANCELLED or COMPLETED Ajo",
                "Rejected as a terminal-state event, and the attempt is recorded.",
                "SCR-APP-05",
                "*This Ajo has finished. It cannot be changed.*",
                         "Read the archived record and the statement. BR-009, EC-064.",
            ],
        ],
        "widths": [1.25, 1.44, 0.72, 1.35, 1.74],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =================================================================== 2.3
    {"t": "h2", "text": "2.3 Join Ajo: invitation to membership"},
    {"t": "h3", "text": "2.3.1 Purpose"},
    {
        "t": "p",
        "text": (
            "An invited person becomes a member without being surprised. The flow must let "
            "someone read the entire commercial and legal shape of the commitment in plain "
            "language before they accept, must show the 2% fee as its own number rather than "
            "folding it into the amount, must make the complete-cycle commitment and the "
            "consequence of a missed payment explicit, and must produce a membership record "
            "that the member and the organiser both believe is the same one."
        )
    },
    {"t": "h3", "text": "2.3.2 Swimlane"},
    {
        "t": "code",
        "text": """
INVITEE         AJO.ng            ORGANISER          AJO API
   |  opens        |                  |                 |
   |  token link   |                  |                 |
   |--------------->|  GET            |                 |
   |                |  /invitations/  |                 |
   |                |   :token        |                 |
   |  Is the token  |  organiser name, |                 |
   |  valid?        |  member count,   |                 |
   |                |  contribution    |                 |
   |                |  NGN 1,000.00    |                 |
   |                |  fee NGN 20.00   |                 |
   |                |  charged         |                 |
   |                |  NGN 1,020.00   |                 |
   |                |  my total        |                 |
   |                |  NGN 10,200.00  |                 |
   |                |  base pool       |                 |
   |                |  NGN 10,000.00  |                 |
   |                |  my position     |                 |
   |  not signed in |                  |                 |
   |--------------->|  SCR-MKT-09 /   |                 |
   |                |  SCR-MKT-10      |                 |
   |  Register or   |  (flow 2.1)      |                 |
   |  log in        |                  |                 |
   |  Verify email, |                  |                 |
   |  phone, KYC    |                  |                 |
   |  [ ] I accept  |                  |                 |
   |  the full      |                  |                 |
   |  cycle         |                  |                 |
   |  [ ] I have     |                  |                 |
   |  read the fee   |                  |                 |
   |-------------->|  POST            |                 |
   |                |  /invitations/   |                 |
   |                |   :token/accept |                 |
   |                |  token consumed  |                 |
   |                |  membership     |                 |
   |                |  created  ------|---- member.joined ->|  push + email
   |                |  role:          |                 |
   |                |  ajo_member     |                 |
   |  Dashboard     |                  |                 |
   |--------------->|  GET /ajos      |                 |
   |                |  GET /contributions                 |
   |                |  GET /payouts (position visible)     |
""",
    },
    {"t": "h3", "text": "2.3.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.3.1", "Invitee", "SCR-MKT-01 / SCR-APP-04",
                "Opens the invitation link from SMS, email, push or a forwarded message.",
                "`GET /invitations/:token`. The token is single-use, expiring, revocable and "
                "non-enumerable. The response discloses the Ajo's terms and nothing else. No "
                "account is created by opening it.",
                         "FR-INV-001, FR-INV-003, NFR-S, US-18, EC-124, EC-084",
            ],
            [
                "2.3.2", "Invitee", "SCR-APP-04",
                "Reads the plain-language summary: organiser, member count, contribution, "
                "fee, frequency, total duration, total they will pay, and what happens if "
                "they miss a payment.",
                "All figures are itemised. The fee is a separate line with its own label. The "
                "complete-cycle commitment and the position-lock rule are stated in the same "
                "block, not behind a link.",
                "FR-JOIN-001, FR-JOIN-002, FR-INV-002, BR-004, BR-011, G3, US-15, N15",
            ],
            [
                "2.3.3", "Invitee", "SCR-APP-04",
                "Checks which turn is theirs and what the order's status is.",
                "`GET /ajos/:id/positions`. The screen shows the position number, the "
                "expected round and the expected payout date. If the order is still "
                "provisional it says so in those words and shows the date on which it locks.",
                "FR-POS-003, FR-POS-005, BR-002, US-18",
            ],
            [
                "2.3.4", "Invitee", "SCR-MKT-09 / SCR-MKT-10",
                "Registers or logs in, then completes verification.",
                "Flow 2.1 in full. A user who is not verified is refused acceptance with a "
                "specific reason, never a blank screen. Joining requires a verified email and "
                "a verified phone; identity verification is required above the configured "
                "threshold, which is open decision D-04.",
                         "US-02, US-19, FR-KYC-001, D-04, EC-127",
            ],
            [
                "2.3.5", "Invitee", "SCR-APP-04",
                "Ticks the two acknowledgements: the full-cycle commitment, and the fee "
                "breakdown.",
                "Neither box is pre-ticked. The accept control is inert until both are ticked. "
                "The acknowledgement is stored with the terms version and the timestamp, so "
                "what was agreed can be proved later.",
                "FR-JOIN-003, FR-JOIN-004, BR-004, BR-011, US-16, US-17",
            ],
            [
                "2.3.6", "Invitee", "SCR-APP-04",
                "Taps *Join this Ajo*.",
                "`POST /invitations/:token/accept` with an `Idempotency-Key`. The token is "
                "consumed atomically; a second use is rejected. A membership is created, the "
                "role `ajo_member` attaches, and the position is held or confirmed.",
                "BR-006, BR-024, FR-JOIN-005, FR-MEM-001",
            ],
            [
                "2.3.7", "AJO.ng", "—",
                "Notifies the organiser.",
                "`member.joined` to the organiser on push and email, immediately. It names "
                "the member, the position and the terms version, and nothing more.",
                "CAN §8, FR-NOTIF-001",
            ],
            [
                "2.3.8", "Invitee now `ajo_member`", "SCR-APP-01",
                "Lands on the dashboard and sees the Ajo with its position, its first due "
                "date and its total remaining commitment.",
                "`GET /ajos`, `GET /contributions`, `GET /ajos/:id/schedule`, "
                "`GET /payouts`. The member can now see everything they owe without asking "
                "anyone, which is the entire point of the product.",
                "FR-CON-001 to FR-CON-004, FR-SCH-002, G2, N1, N2",
            ],
        ],
        "widths": [0.49, 0.92, 0.84, 1.39, 1.95, 0.91],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.3.4 Happy path"},
    {
        "t": "p",
        "text": (
            "Bisi receives an SMS and an email from an organiser she knows. The link opens a "
            "page that names the organiser, says 10 members, NGN 1,000.00 per month, shows "
            "the fee as NGN 20.00 and the total charged as NGN 1,020.00, and tells her that "
            "she will pay NGN 10,200.00 across the whole Ajo and that whoever's turn it is "
            "receives NGN 10,000.00. It tells her she is in position 6, that the order is "
            "still provisional, and that it locks when the Ajo activates. It tells her what "
            "happens if she misses a payment: a reminder, a 48-hour grace, then the organiser "
            "is told, privately, and nobody else. She does not have an account, so she "
            "registers, verifies her email and phone, and passes the identity check. She "
            "ticks both acknowledgements and joins. The organiser is told immediately. Bisi's "
            "dashboard shows her position, her first due date, and everything she owes for "
            "the next ten months without having to ask a single person."
        )
    },
    {"t": "h3", "text": "2.3.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The token has expired",
                "Acceptance is refused. The invitation itself is not consumed, and the "
                "organiser still holds a seat.",
                "SCR-APP-04",
                "*This invitation has expired. Ask the organiser to send a new one.*",
                                  "The organiser resends. Resend never creates a second membership, "
         "EC-124.",
            ],
            [
                "The token has already been used",
                "Refused. No state change. The attempt is recorded.",
                "SCR-APP-04",
                "*This invitation has already been used. Sign in to see your Ajo.*",
                                  "Sign in. If the member believes the first use was not them, this is an "
         "account-takeover signal, not a UX problem, flow 2.15, EC-084.",
            ],
            [
                "The token was revoked by the organiser",
                "Refused immediately, with no indication of whether the seat is still free to "
                "a different person.",
                "SCR-APP-04",
                "*This invitation is no longer valid.*",
                         "Contact the organiser. Revocation is a legitimate organiser action "
         "pre-activation. FR-INV-005, EC-125.",
            ],
            [
                "The Ajo is already ACTIVE",
                "Acceptance is refused. Membership by invitation is closed once activation "
                "locks the roster.",
                "SCR-APP-04",
                "*Enrollment for this Ajo has closed, so new members cannot join. Talk to the "
                "organiser about a replacement position.*",
                         "The organiser raises a formal replacement request. BR-002, BR-006, "
         "US-19, EC-066.",
            ],
            [
                "The Ajo is full",
                "Refused. No overbooking, no waitlist that silently changes the pot value, no "
                "partial join.",
                "SCR-APP-04",
                "*This Ajo is full. There is no room without a member leaving formally.*",
                         "The organiser may request a replacement, EC-067.",
            ],
            [
                "The invitee declines",
                "`POST /invitations/:token/decline`. No account is created, the token is "
                "invalidated, and the seat is released back to the organiser.",
                "SCR-APP-04",
                "*Invitation declined.* The organiser sees the seat return to unfilled.",
                         "None needed. US-18, EC-126.",
            ],
            [
                "The invitee is unverified when they try to accept",
                "Refused with a specific reason and a route to fix it. The token is not "
                "consumed, so the invitation survives the detour.",
                "SCR-MKT-09 / SCR-APP-19",
                "*Confirm your email and phone number first. Your invitation is saved.*",
                         "Complete 2.1.5 to 2.1.8, then return. US-02, EC-127.",
            ],
            [
                "The invitee has no smartphone or no data",
                "The invitation link is a web link, not an app-only deep link. The join "
                "confirmation is available on a low-bandwidth page and the full terms are "
                "reachable without a login.",
                "SCR-APP-04 (web)",
                "*You can read everything and agree on any phone with a browser.*",
                         "Join from any browser. Core flows must complete on the lowest "
         "supported device class over 3G. G7, NFR-PERF-004, C-14, EC-036.",
            ],
            [
                "The invitation is forwarded and the forwarder accepts",
                "Acceptance is refused unless the account's verified phone matches the "
                "invitee's number. The attempt is recorded as a risk signal on the "
                "invitation.",
                "SCR-APP-04",
                "*This invitation was sent to a different phone number. Ask to be added "
                "personally.*",
                         "The organiser revokes and reissues to the correct number. The "
         "forwarded attempt is visible to `risk_officer`, R4, EC-084.",
            ],
        ],
        "widths": [1.25, 1.44, 0.72, 1.35, 1.74],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =================================================================== 2.4
    {"t": "h2", "text": "2.4 Contribution: from dashboard to receipt"},
    {"t": "h3", "text": "2.4.1 Purpose"},
    {
        "t": "p",
        "text": (
            "This is the flow that decides whether the product is trusted. A member opens the "
            "app, sees exactly what is owed and exactly what will be charged, pays through a "
            "provider without ever handing AJO.ng a card, and receives a receipt that shows "
            "the contribution and the fee as separate lines. Every one of those steps is "
            "mandatory. The flow must survive a dropped connection, a duplicated request and "
            "a delayed provider response without ever charging a member twice or leaving a "
            "member in doubt about whether they paid (BR-024, NFR-AVL-003, P4)."
        )
    },
    {"t": "h3", "text": "2.4.2 Swimlane"},
    {
        "t": "code",
        "text": """
MEMBER (ajo_member)     AJO.ng            PROVIDER       LEDGER (append-only)
   |  Dashboard          |                  |                 |
   |-- GET /contributions>|                |                 |
   |<-- PENDING, due Tue  |                |                 |
   |  contribution.due   |                |                 |
   |  T-24h, T-2h (push, |                |                 |
   |  email; SMS optional)|                |                 |
   |  Upcoming           |                |                 |
   |--------------->|    |                |                 |
   |  "Pay now"        |    |                |                 |
   |                  |  Shows owed        |                 |
   |                  |  contribution      |                 |
   |                  |  NGN 1,000.00      |                 |
   |                  |  fee 2%            |                 |
   |                  |  NGN 20.00         |                 |
   |                  |  TOTAL             |                 |
   |                  |  NGN 1,020.00      |                 |
   |                  |  [ ] I understand  |                 |
   |--------------->|  POST /payments    |                 |
   |                  |  Idempotency-Key   |                 |
   |                  |  amount fixed ---->|  INITIATED     |
   |                  |  payment: PENDING  |---------------->|  (nothing yet)
   |  <provider page: authorise>                |                 |
   |----------------------------------------->|  SUCCESS        |
   |                  |  POST /payments/:id/verify (poll + reconcile)
   |                  |<--------------------------------------|  webhook
   |                  |  POST /webhooks/payments              |
   |                  |  signature verified, replay-checked   |
    |                  |  1. contribution.received   debit escrow_cash
    |                  |                          credit contribs_recd
    |                  |                          (net NGN 1,000.00)
    |                  |  2. fee.recognised        debit escrow_cash
    |                  |                          credit fees_income
    |                  |                          (NGN 20.00)
   |                  |  payment SUCCESS         |
   |                  |  contribution PENDING -> PAID
   |                  |  balance to zero or rejected
   |  Receipt         |                  |                 |
   |--------------->|  GET /payments/:id/receipt                 |
   |                  |  contribution NGN 1,000.00                |
   |                  |  fee         NGN   20.00                 |
   |                  |  charged     NGN 1,020.00                 |
   |                  |  provider ref, timestamp, state PAID     |
   |  contribution.received (push, email)                    |
   |  Round funding progress updates for every member         |
""",
    },
    {"t": "h3", "text": "2.4.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.4.1", "System", "SCR-APP-12",
                "Sends `contribution.due` at T-24h and T-2h before the due time.",
                "Push and email to the member, SMS only if the member has opted into the "
                "optional SMS for this category. Two notifications per round is a deliberate "
                "ceiling, not an accident.",
                "CAN §8, FR-NOTIF-002, FR-NOTIF-006, A-14",
            ],
            [
                "2.4.2", "Member", "SCR-APP-01",
                "Opens the dashboard and taps the upcoming contribution.",
                "`GET /contributions` returns the member-scoped list with each contribution's "
                "state, due date in the member's configured zone with the zone named, and the "
                "amount outstanding. The view is self-service and needs no organiser input.",
                "FR-CON-001, FR-CON-002, NFR-LOC-003, G2, N1, US-20",
            ],
            [
                "2.4.3", "Member", "SCR-APP-08",
                "Opens the contribution detail.",
                "Shows: round number, due date, contribution NGN 1,000.00, platform fee 2% "
                "NGN 20.00, total to charge NGN 1,020.00, amount already paid, and the state "
                "sequence PENDING, PAID, settled. State is carried as a text label and an "
                "icon, never by colour alone.",
                "FR-CON-003, FR-CON-004, BR-011, NFR-ACC-003, US-21, US-22",
            ],
            [
                "2.4.4", "Member", "SCR-APP-08",
                "Taps *Pay now* and acknowledges the amount.",
                "The amount is final at initiation and cannot change afterwards. A single "
                "acknowledgement records that the member saw the split between contribution "
                "and fee before authorising the charge.",
                "FR-PAY-002, FR-PAY-007, BR-011, US-22",
            ],
            [
                "2.4.5", "Member", "SCR-APP-09",
                "Authorises payment on the provider's own surface.",
                "`POST /contributions/:id/pay` then `POST /payments`, both requiring an "
                "`Idempotency-Key`. AJO.ng stores no card credentials at any layer; the "
                "provider tokenises. The payment record is created `INITIATED` then "
                "`PENDING` with the amount fixed.",
                "FR-PAY-001, FR-PAY-004, BR-024, NFR-SEC-007, CAN §4",
            ],
            [
                "2.4.6", "AJO.ng", "—",
                "Acknowledges initiation within 2 seconds.",
                "NFR-PERF-003 target. The member is told *we are confirming your payment* and "
                "is not asked to pay again. A payment in `PENDING` is never displayed as in "
                "arrears.",
                "NFR-PERF-003, US-24, US-25",
            ],
            [
                "2.4.7", "Provider", "SCR-APP-09",
                "Charges the member and returns a result; the webhook arrives out of band.",
                "`POST /webhooks/payments` is unauthenticated but signature-verified, "
                "replay-protected and idempotent before any credit is posted. The client also "
                "polls `POST /payments/:id/verify`. Either path may win; the loser is absorbed.",
                         "NFR-S, FR-PAY-005, CAN §6, EC-002, EC-003"
            ],
            [
                "2.4.8", "AJO.ng", "—",
                "Posts the ledger, in the mandatory order.",
                "Step 1 `contribution.received`: debit escrow_cash, credit "
                "contributions_receivable for the net contribution of NGN 1,000.00. Step 2 "
                "`fee.recognised`: debit escrow_cash, credit fees_income NGN 20.00. Each entry must "
                "balance to zero individually or be rejected at the data layer.",
                "BR-021, BR-013, BR-010, NFR-AUD-006, CAN §4",
            ],
            [
                "2.4.9", "AJO.ng", "SCR-APP-08",
                "Moves the contribution from PENDING to PAID and closes the round's funding "
                "progress.",
                "State transition recorded with actor, role, timestamp, prior state and new "
                "state. Round funding progress, and therefore the pot figure every member "
                "sees, updates immediately.",
                "FR-CON-005, NFR-AUD-001, FR-POS-002",
            ],
            [
                "2.4.10", "Member", "SCR-APP-09",
                "Opens the receipt.",
                "`GET /payments/:id/receipt` shows contribution NGN 1,000.00, fee NGN 20.00, "
                "total charged NGN 1,020.00, the provider reference, the timestamp and the "
                "resulting contribution state, as separate lines. The naira glyph is never "
                "used in an export.",
                "FR-PAY-007, NFR-LOC-002, NFR-LOC-004, N4, US-23",
            ],
            [
                "2.4.11", "System", "SCR-APP-12",
                "Sends `contribution.received` to the member immediately.",
                "Push and email, SMS only on the optional opt-in. The event is idempotent per "
                "event instance, so a retried delivery never produces a second message.",
                "CAN §8, FR-NOTIF-001, FR-NOTIF-004",
            ],
        ],
        "widths": [0.49, 0.87, 0.78, 1.41, 1.95, 1.0],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.4.4 Happy path"},
    {
        "t": "p",
        "text": (
            "The member receives a reminder on Monday evening and again on Tuesday morning. "
            "They open the app, tap the upcoming contribution, and see the round, the due "
            "date, and three numbers: NGN 1,000.00 contribution, NGN 20.00 platform fee, "
            "NGN 1,020.00 total. They acknowledge the amount and tap pay. The provider page "
            "opens, they authorise, and within two seconds AJO.ng has acknowledged the "
            "initiation and told them it is confirming. The webhook arrives, the signature "
            "is verified, the ledger posts two entries in order: NGN 1,000.00 into escrow and "
            "NGN 20.00 into fees_income, balancing to zero. The contribution moves to PAID, "
            "the round's funding progress advances for every member, the receipt is available "
            "with all four lines separate, and a confirmation notification arrives. The "
            "member never saw a card number, was never charged a second time, and can prove "
            "the payment to anyone who asks."
        )
    },
    {"t": "h3", "text": "2.4.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The member's connection drops during authorisation",
                "The payment stays `PENDING` with an expected confirmation time. The member is "
                "not shown as in arrears and is not prompted to pay again.",
                "SCR-APP-09",
                "*We are still confirming this payment. Do not pay again — we will tell you "
                "the moment it clears.*",
                         "Wait for the webhook or the poll. If nothing arrives, the "
         "reconciliation job resolves it within 24 hours. NFR-AVL-003, US-24, "
         "US-25, EC-001.",
            ],
            [
                "The payment succeeds at the provider but the response never reaches the app",
                "The webhook is the source of truth, not the client response. The app "
                "reconciles on next open and shows PAID.",
                "SCR-APP-09 / SCR-APP-08",
                "*Your payment went through. Your receipt is ready.*",
                         "None. The receipt is the recovery, NFR-AVL-003, EC-002.",
            ],
            [
                "The same request arrives twice, from a retry or a double tap",
                "The `Idempotency-Key` returns the original result. No second obligation, no "
                "second payment, no second ledger entry.",
                "SCR-APP-09",
                "*You already paid this one. Here is your receipt.*",
                         "None. BR-024, US-23, EC-022.",
            ],
            [
                "The provider returns FAILED (insufficient funds, declined, timeout)",
                "The payment is `FAILED`. No ledger posting occurs at all: there is no "
                "contribution, no fee, nothing to reverse. `contribution.failed` is sent and "
                "the retry control appears.",
                "SCR-APP-08",
                "*That payment did not go through. Nothing has been taken from you. Try "
                "again.*",
                         "`POST /contributions/:id/retry` with a new idempotency key. Flow 2.7, "
         "EC-019.",
            ],
            [
                "The member abandons the provider page",
                "The payment is `CANCELLED`. The obligation is untouched and remains PENDING. "
                "No fee is charged, because no money moved.",
                "SCR-APP-09",
                "*Payment cancelled. You still owe NGN 1,020.00 for this round.*",
                         "Pay again from the contribution detail. Flow 2.8, EC-023.",
            ],
            [
                "The provider returns UNKNOWN, meaning neither success nor failure",
                "The payment is held in `UNKNOWN` and the contribution stays PENDING. A "
                "reconciliation against provider settlement is run. The member is not "
                "prompted to pay again while the state is unresolved.",
                "SCR-APP-09",
                "*We are checking with the payment provider. You do not need to pay again.*",
                                  "Reconciliation resolves to SUCCESS or FAILED, then normal handling, "
         "EC-048, EC-035.",
            ],
            [
                "The member pays a second time by deliberate choice",
                "The second payment is treated as an overpayment, not a second contribution. "
                "It is recorded, held and offered back as a refund. It is never applied "
                "silently to a future round.",
                "SCR-APP-09",
                "*You have paid this round twice. We are holding the extra NGN 1,020.00 and "
                "will refund it — nothing more is owed.*",
                                  "Refund on request, or apply to a future round with explicit consent, "
         "flow 2.9, BR-032, EC-004.",
            ],
            [
                "The member pays a different amount from the amount shown",
                "Refused. The amount is fixed at initiation from the schedule; the client may "
                "not override it.",
                "SCR-APP-08",
                "*The amount for this round is fixed at NGN 1,020.00.*",
                         "Pay the scheduled amount, or raise a dispute, BR-005, EC-005, EC-006.",
            ],
            [
                "A webhook arrives for a payment record that does not exist",
                "Rejected as a signature or reference failure and recorded. No credit is "
                "posted against an unknown reference.",
                "—",
                "The member is unaffected. The event appears in the admin log as an anomaly.",
                         "Reconciliation identifies the unmatched item, NFR-S, EC-039.",
            ],
            [
                "The escrow balance or the ledger does not balance after posting",
                "The transaction is rejected at the data layer. The payment record is left in "
                "PENDING for investigation, not marked paid.",
                "SCR-APP-08",
                "*We are resolving a records issue on this payment. You have not been charged "
                "twice and nothing is lost.*",
                         "Engineering investigation; the solvency assertion prevents "
         "disbursement. BR-013, BR-020, K-16, EC-101.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =================================================================== 2.5
    {"t": "h2", "text": "2.5 Payout: from cycle complete to record"},
    {"t": "h3", "text": "2.5.1 Purpose"},
    {
        "t": "p",
        "text": (
            "The flow that ends an Ajo's trust or confirms it. A member whose turn it is has "
            "been promised the base pool, NGN 10,000.00 in the canonical example, and the "
            "platform either pays that in full or pays nothing at all. There is no reduced "
            "payout, there is no corporate money used to make one look better, and there is "
            "no silence. If the funds are not there, the round goes to HELD, the recipient and "
            "the organiser are told immediately in plain language, and the recovery process "
            "begins (BR-018, BR-012, BR-017, G4)."
        )
    },
    {"t": "h3", "text": "2.5.2 Swimlane"},
    {
        "t": "code",
        "text": """
RECIPIENT         AJO.ng            ORGANISER        PROVIDER        LEDGER
   |  payout.       |                  |               |              |
   |  upcoming      |                  |               |              |
   |  (T-24h,       |                  |               |              |
   |   push/email/  |                  |               |              |
   |   SMS)         |                  |               |              |
   |  Round funding |                  |               |              |
   |  = 10 x        |                  |               |              |
   |  NGN 1,000.00  |                  |               |              |
   |  collected     |                  |               |              |
   |           Eligibility check      |               |              |
   |                |  verified + in-name payout destination
   |                |  recipient not frozen, not under review
   |                |  payout SCHEDULED -> FUNDING
   |                |  escrow solvency assertion:
   |                |  available >= due (NGN 10,000.00)?     |
   |                |  YES:                                |
   |                |  3. payout.recognized                 |
   |                |     debit contributions_receivable    |
   |                |     credit payouts_payable            |---------->|
   |                |  organizer may REQUEST release:       |              |
   |  released      |  POST /payouts/:id/release ------------>|              |
   |                |  organizer CANNOT release, control,    |              |
   |                |  modify or cancel it                   |              |
   |  payout.released  |------------->| push/email/SMS   |              |
   |                |  payout RELEASED -> provider disburses  |              |
   |                |<--------------------------------------|  SUCCESS     |
   |                |  4. payout.settled                     |              |
   |                |     debit payouts_payable              |---------->|
   |                |     credit escrow_cash                  |
   |                |  balance to zero or rejected            |              |
   |  payout.succeeded                  |               |              |
   |  GET /payouts/:id  receipt: base pool NGN 10,000.00   |              |
   |                   fee retained   NGN    200.00         |              |
   |                   provider reference, timestamp        |              |
   |  Round closes, next position opens                      |              |
""",
    },
    {"t": "h3", "text": "2.5.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.5.1", "System", "SCR-APP-12",
                "Detects that a round has fully collected its required funds.",
                "Round funding progress is derived from the ledger, never from a count of "
                "who says they paid. Full collection is a necessary condition, not the "
                "sufficient one.",
                "FR-POS-002, FR-POUT-001, BR-013",
            ],
            [
                "2.5.2", "System", "SCR-APP-12",
                "Sends `payout.upcoming` to the recipient at T-24h.",
                "Push, email and SMS, because this is money-critical. The notification names "
                "the date, the amount and the destination so the recipient can sanity-check "
                "them.",
                "CAN §8, FR-NOTIF-001, FR-POUT-008",
            ],
            [
                "2.5.3", "Recipient", "SCR-APP-10",
                "Reviews the payout before it is released.",
                "`GET /payouts/:id`. The amount shown is the base pool, NGN 10,000.00, with "
                "the retained fee for the round, NGN 200.00, shown separately. The collected "
                "total of NGN 10,200.00 is never presented as what they will receive.",
                "BR-012, FR-POUT-003, FR-POUT-008, US-27",
            ],
            [
                "2.5.4", "System", "—",
                "Runs eligibility.",
                "Recipient is identity-verified, the account is not frozen and not under risk "
                "review, the payout destination is verified and in the recipient's own name, "
                "and the round funds are fully collected. Any failed check stops the release "
                "with a recorded reason rather than proceeding.",
                "NFR-SEC-010, FR-POUT-004, FR-ADM-005, D-04",
            ],
            [
                "2.5.5", "System", "—",
                "Runs the escrow solvency assertion.",
                "Before every disbursement the platform asserts that escrow covers the "
                "liability being settled. This is not bypassable by any role, including "
                "`super_admin`. If NGN 100,000.00 is due and NGN 90,000.00 is available, the "
                "assertion fails and the payout cannot be released.",
                         "BR-020, BR-018, NFR-AUD-006, EC-101, EC-063",
            ],
            [
                "2.5.6", "System", "SCR-APP-10",
                "Moves the payout SCHEDULED to FUNDING and posts recognition.",
                "Step 3 `payout.recognized`: debit contributions_receivable, credit "
                "payouts_payable for NGN 10,000.00. Skipping this step drains escrow against "
                "a liability that was never raised, and the assertion correctly halts "
                "disbursement.",
                "BR-021, BR-020, CAN §4",
            ],
            [
                "2.5.7", "Organiser", "SCR-APP-05",
                "May request release of the payout.",
                "`POST /payouts/:id/release` records a request. The organiser may not "
                "release, control, modify or cancel the payout, and may not authorise a "
                "payout at all. A request by an organiser is never a precondition the "
                "platform waits on indefinitely.",
                "FR-POUT-005, CAN §2, BR-008",
            ],
            [
                "2.5.8", "System", "SCR-APP-12",
                "Sends `payout.released` to the recipient on release.",
                "Push, email and SMS. Silence about a released payout is not permitted for "
                "any role.",
                "CAN §8, BR-017",
            ],
            [
                "2.5.9", "Provider", "—",
                "Disburses to the verified destination.",
                "The provider webhook moves the payout to SUCCESS or FAILED. Retries are "
                "bounded and every attempt is recorded. Failure is retried automatically a "
                "bounded number of times before member action is required.",
                         "FR-POUT-007, CAN §4, EC-128"
            ],
            [
                "2.5.10", "System", "—",
                "Posts settlement and closes the round.",
                "Step 4 `payout.settled`: debit payouts_payable, credit escrow_cash. Balance "
                "to zero or reject. The round closes, the next position opens, and "
                "`ajo.completed` goes to all members when the final round settles.",
                "BR-021, BR-013, CAN §8",
            ],
            [
                "2.5.11", "Recipient", "SCR-APP-10",
                "Receives the payout receipt and the record.",
                "`GET /payouts/:id` and `GET /statements` produce a receipt showing the base "
                "pool NGN 10,000.00, the fee retained NGN 200.00 and the provider reference "
                "as separate lines, and a downloadable statement itemised by round. "
                "`payout.succeeded` is sent on push, email and SMS.",
                "FR-POUT-008, FR-TXN-003, CAN §8, N4, US-26",
            ],
        ],
        "widths": [0.49, 0.78, 0.84, 1.41, 2.0, 0.98],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.5.4 Happy path"},
    {
        "t": "p",
        "text": (
            "Twenty-four hours before the round, Ada receives `payout.upcoming` on push, "
            "email and SMS with the date, the amount and the destination. She opens the "
            "payout screen and sees NGN 10,000.00 as the amount she will receive, with the "
            "round's retained fee of NGN 200.00 shown on a separate line, and a clear note "
            "that NGN 10,000.00 is the base pool and not the NGN 10,200.00 collected. The "
            "system confirms she is verified, that her account is clean, that the "
            "destination account is in her own name, and that all ten contributions of NGN "
            "1,000.00 have been collected into the round. The escrow solvency assertion "
            "passes. The payout moves to FUNDING, the recognition entry posts, the organiser's "
            "release request is recorded but confers no authority, the payout is released, and "
            "Ada is told immediately that it is on its way. The provider settles, the "
            "settlement entry posts, the round closes, the next member's turn opens, and Ada "
            "has a receipt that shows the base pool, the retained fee and the provider "
            "reference as three separate lines. The next Ajo she joins starts from that "
            "receipt, not from a notebook."
        )
    },
    {"t": "h3", "text": "2.5.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The round funds are short, for example NGN 90,000.00 available against "
                "NGN 100,000.00 due",
                "The release is refused. The payout enters HELD. No reduced amount is ever "
                "paid and corporate funds are never used.",
                "SCR-APP-10",
                "To the recipient: *Your payout of NGN 100,000.00 is on hold because the "
                "round has not been fully funded. We will not pay you part of it. You will "
                "receive the whole amount or we will tell you exactly what is missing.* To "
                "the organiser: the same fact, with the shortfall.",
                         "The recovery process begins: chase the defaulting member through the "
         "documented sequence, or place the Ajo under formal recovery. BR-018, "
         "BR-017, G4, US-29, K-14, EC-063.",
            ],
            [
                "The payout destination is not in the recipient's own name",
                "Release is blocked until a verified, own-name destination is nominated. No "
                "third-party payout is permitted at MVP.",
                "SCR-APP-10",
                "*Payouts can only go to an account in your own name. Add one to continue.*",
                         "Nominate a verified own-name account. NFR-S, FR-POUT-004, US-30, "
         "EC-128.",
            ],
            [
                "The provider rejects or fails the disbursement",
                "Payout moves to FAILED and enters bounded automatic retry. Every attempt is "
                "recorded with its reason.",
                "SCR-APP-10",
                "*Your payout did not complete. We are retrying automatically. Nothing is lost "
                "and no action is needed from you yet.*",
                         "Automatic retry, then member action: re-nominate a destination or "
         "contact support. `payout.failed` goes to recipient and organiser on "
         "push, email and SMS. FR-POUT-007, BR-017, EC-049.",
            ],
            [
                "The recipient's account is frozen or under risk review when their turn "
                "arrives",
                "The payout does not silently vanish. The round goes to HELD with a recorded "
                "reason, and the recipient and organiser are both told.",
                "SCR-APP-10 / SCR-ADM-05",
                "*Your payout is on hold while we confirm your account. Contact support to "
                "resolve it.*",
                                  "Risk review clears the account, or the freeze is lifted. The hold is "
         "not a default and no default clock runs against the member for it, "
         "flow 2.15, EC-034.",
            ],
            [
                "The organiser demands an early release, or a partial release, or a change of "
                "destination",
                "Refused and recorded. The organiser holds no authority over disbursement.",
                "SCR-APP-05",
                "*You can ask for a release, but AJO.ng decides when money moves, and only in "
                "full.*",
                         "None needed. The refusal is the correct behaviour. BR-008, "
         "FR-POUT-005, CAN §2, EC-078, EC-147, EC-128."
            ],
            [
                "The recipient is overseas or the account cannot receive a local "
                "disbursement",
                "The payout is HELD rather than sent to a third party or a different account. "
                "Diaspora participation is out of MVP scope by design.",
                "SCR-APP-10",
                "*We cannot pay this destination yet. Your position is safe and your money is "
                "held for you.*",
                         "Provide a supported own-name destination, or wait. C-07, A-11, EC-049.",
            ],
            [
                "The round completes but some members have not yet seen the notification",
                "The financial record is written by the system, not by the notification. "
                "Notifications are idempotent per event instance and are re-driven until "
                "confirmed or exhausted.",
                "SCR-APP-12",
                "The member sees the payout in the app and in the statement even if every "
                "push, email and SMS was lost.",
                         "Notification re-drive and a support-swept list, FR-NOTIF-004, EC-069.",
            ],
            [
                "A completed Ajo is opened again months later",
                "Terminal states are terminal for events, but not for reading. The full round "
                "history, all receipts and the downloadable statement remain available for "
                "the whole retention period.",
                "SCR-APP-05 / SCR-APP-11",
                "*This Ajo completed on DATE. Here is everything that happened.*",
                         "Download the statement. BR-009, FR-TXN-004, G10, US-38, EC-064.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =================================================================== 2.6
    {"t": "h2", "text": "2.6 Default: due date to recovery"},
    {"t": "h3", "text": "2.6.1 Purpose"},
    {
        "t": "p",
        "text": (
            "A missed payment is the most common failure in an Ajo and the one most likely "
            "to destroy the product if handled badly. This flow implements the fixed sequence "
            "from CANONICAL.md and nothing else: reminder, retry if supported, 48-hour grace, "
            "organiser notified, member contacted, payment or default recorded, recovery "
            "process. No step is skipped, no default is recorded before the grace elapses, no "
            "other member is charged extra, and no member other than the three parties ever "
            "learns that a default happened (BR-014, BR-015, BR-016, G5)."
        )
    },
    {"t": "h3", "text": "2.6.2 Swimlane"},
    {
        "t": "code",
        "text": """
CLOCK          MEMBER                ORGANISER           RISK        LEDGER
   |             |                      |                  |            |
   |  due time   |                      |                  |            |
   |------------>| contribution.overdue |                  |            |
   |             |  (push, email, SMS)  |                  |            |
   |             |  PENDING -> OVERDUE  |                  |            |
   |  +0h        |  "Pay now" is the    |                  |            |
   |             |  primary action;     |                  |            |
   |             |  the full sequence,  |                  |            |
   |             |  the 48h clock and   |                  |            |
   |             |  "others are NOT     |                  |            |
   |             |   charged extra"     |                  |            |
   |             |  are shown BEFORE    |                  |            |
   |             |  the due date        |                  |            |
   |  +48h       |  OVERDUE -> GRACE    |                  |            |
   |             |  contribution.grace_ended (push, email)|
   |             |                      |  "This member is  |            |
   |             |                      |   in default on   |            |
   |             |                      |   round R. Your   |            |
   |             |                      |   options are    |            |
   |             |                      |   below."        |            |
   |  +48h and   |  member contacted    |  member contacted |            |
   |  still unpaid|  (support outreach) |  by support      |            |
   |             |  OVERDUE/GRACE ->    |                  |            |
   |             |  DEFAULTED          |  member.defaulted|            |
   |             |  (push, email)      |  (push, email)   |            |
   |             |  risk_events row    |  risk_events row |            |
   |             |                      |                  |            |
   |  recovery   |  pay later -> RECOVERED -> PAID                     |
   |             |  POST /contributions/:id/retry                      |
   |             |  OR formal replacement request (flow 2.10)         |
   |             |  OR risk officer writes off with recorded approver  |
   |             |                      |                  | -> WRITTEN_OFF
   |  NO other member is charged extra. NO member-visible feed names
   |  the defaulting member. Ever.                                    |
""",
    },
    {"t": "h3", "text": "2.6.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.6.1", "Member", "SCR-APP-08",
                "Reads, before the due date, exactly what will happen if they cannot pay.",
                "The contribution detail shows the state sequence, the 48-hour grace, the "
                "recovery options, and the explicit statement that other members will not be "
                "charged extra because of them. This is shown proactively, not after the "
                "fact.",
                "FR-DEF-002, US-32, N9, G5",
            ],
            [
                "2.6.2", "System", "SCR-APP-12",
                "At the due time, marks the contribution OVERDUE and sends "
                "`contribution.overdue`.",
                "Push, email and SMS to the member, because an overdue money event is "
                "money-critical. State transition recorded with actor, role, timestamp and "
                "both states.",
                "CAN §8, BR-016, NFR-AUD-001",
            ],
            [
                "2.6.3", "System", "—",
                "Offers retry where the provider supports it.",
                "`POST /contributions/:id/retry` is offered inside the grace window and must "
                "not create a second obligation. The member is not re-charged without a "
                "fresh authorisation.",
                "FR-DEF-003, FR-PAY-008, BR-016",
            ],
            [
                "2.6.4", "Member", "SCR-APP-08",
                "Attempts to pay during the grace window.",
                "The payment flow in 2.4 runs normally. On success the contribution returns "
                "to PAID, the organiser is never told a default occurred, and the round's "
                "funding progress recovers with no visible scar.",
                "FR-DEF-007, CAN §4",
            ],
            [
                "2.6.5", "System", "—",
                "At 48 hours, moves the contribution to GRACE and ends grace.",
                "No default may be recorded before the grace period elapses. The clock is "
                "computed in UTC from the recorded due timestamp, never from a client-supplied "
                "time.",
                         "BR-016, NFR-LOC-003, EC-012, EC-031",
            ],
            [
                "2.6.6", "System", "SCR-APP-12",
                "Sends `contribution.grace_ended` to the organiser after 48 hours.",
                "Push and email, not SMS, because this is a money event for a third party "
                "rather than for the member. The notification names the round, the amount and "
                "the organiser's options.",
                "CAN §8, FR-DEF-004, US-34",
            ],
            [
                "2.6.7", "Support", "SCR-APP-13",
                "Contacts the member privately.",
                "The member is contacted directly, not through the group. Support can read "
                "everything and assist; support cannot move money, change a balance or "
                "override a risk decision.",
                "CAN §2, BR-023, FR-ADM-004, BR-016",
            ],
            [
                "2.6.8", "System", "—",
                "If payment or an agreed arrangement is not made, records the contribution as "
                "DEFAULTED and raises a `risk_events` row.",
                "`contribution` moves to DEFAULTED. `member.defaulted` goes to the organiser "
                "on push and email. The risk event carries the rule, the evidence and the "
                "amount. No member-visible surface contains the default.",
                "FR-DEF-005, BR-014, BR-016, US-32, US-33, NFR-AUD-003",
            ],
            [
                "2.6.9", "Organiser", "SCR-APP-05",
                "Sees the default, the member's remaining balance and the recovery options.",
                "The organiser console shows outstanding amounts and the documented options: "
                "await payment, agree a formal replacement, or escalate to platform risk. The "
                "organiser cannot write the debt off, cannot charge other members, and cannot "
                "remove a member from an active Ajo.",
                "FR-MEM-004, BR-008, BR-015, CAN §2",
            ],
            [
                "2.6.10", "Risk officer", "SCR-ADM-05",
                "Reviews defaults that breach a configurable threshold.",
                "Default rate per Ajo, per organiser and per member is measurable in admin "
                "reporting and triggers risk review at a configured threshold. An organiser "
                "running an abnormal pattern is a risk signal, not a member-facing event.",
                "FR-DEF-009, FR-ADM-005, R4, R12, D-08",
            ],
            [
                "2.6.11", "Member", "SCR-APP-08",
                "Recovers: pays later, or requests a formal replacement, or the obligation is "
                "written off by a risk officer.",
                "Recovery returns the contribution to PAID. A write-off moves it to "
                "WRITTEN_OFF with a recorded decision and approver. Both are recorded, and "
                "neither is a member-visible judgement.",
                "FR-DEF-007, FR-DEF-008, CAN §4, CAN §2, flow 2.10",
            ],
        ],
        "widths": [0.49, 0.78, 0.84, 1.41, 2.0, 0.98],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.6.4 Happy path"},
    {
        "t": "p",
        "text": (
            "Tunde's phone is down on the due date. The platform marks the contribution "
            "OVERDUE at the due time and sends `contribution.overdue` on push, email and SMS. "
            "He already read, three days earlier, exactly what would happen: the sequence, "
            "the 48-hour grace, and the fact that nobody else would be charged for his "
            "miss. Within the grace window his phone comes back, he taps pay, the payment "
            "succeeds for NGN 1,020.00, the ledger posts NGN 1,000.00 to escrow and NGN "
            "20.00 to fees_income, and the contribution returns to PAID. The organiser is "
            "never notified, because nothing was recorded as a default. The round closes on "
            "time and every other member is entirely unaware that anything happened. That is "
            "the design: the default flow is a safety net that is invisible when it is not "
            "needed."
        )
    },
    {"t": "h3", "text": "2.6.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The member pays after the grace period has elapsed but before a default is "
                "recorded",
                "The payment is accepted, the contribution returns to PAID, and no default is "
                "recorded. The record shows the late payment, not a default.",
                "SCR-APP-08",
                "*Paid, late. Nothing more is needed.*",
                         "None, EC-012.",
            ],
            [
                "The member pays after DEFAULTED has been recorded",
                "The contribution returns from DEFAULTED to PAID through the recovery path. "
                "The historical default record is retained; it is never deleted, only "
                "transitioned.",
                "SCR-APP-08",
                "*Thank you. Your payment is recorded and your Ajo is back on track.*",
                         "None. FR-DEF-007, EC-015.",
            ],
            [
                "A member defaults and the round can no longer be fully funded",
                "The round does not pay a reduced pot. The payout goes to HELD, the shortfall "
                "is visible, and the recovery process engages.",
                "SCR-APP-10 / SCR-APP-05",
                "*This round is NGN 1,000.00 short. We will not pay part of the pot. Here is "
                "what we are doing about it.*",
                         "Documented, consent-based recovery. No automatic top-up of other "
         "members, ever. BR-015, BR-018, EC-063.",
            ],
            [
                "The defaulting member cannot be reached at all",
                "The obligation stands. The organiser and platform risk continue the documented "
                "process. A replacement request becomes the realistic route.",
                "SCR-APP-05",
                "To the organiser: *We have tried SMS and phone. The documented options are a "
                "formal replacement or a risk decision.*",
                         "Replacement under flow 2.10, or a risk-officer decision with a "
         "recorded rationale. FR-DEF-008, EC-097.",
            ],
            [
                "An organiser asks AJO.ng to tell other members who has not paid",
                "Refused. There is no member-visible feed, ranking or leaderboard that "
                "identifies a defaulting member.",
                "SCR-APP-05",
                "*AJO.ng will not name a member who has not paid to the other members. What "
                "we will do is tell you the amount outstanding and run the recovery "
                "process.*",
                         "None needed. The refusal is the product. BR-014, FR-NOTIF-007, G5, "
         "C-10, EC-098.",
            ],
            [
                "An organiser asks AJO.ng to deduct the shortfall from other members",
                "Refused. Any recovery that requires other members to contribute more must be "
                "explicit and consent-based, and must never happen silently.",
                "SCR-APP-05",
                "*We cannot take more from anyone else without their agreement. If the group "
                "wants a different arrangement, it has to be agreed openly.*",
                         "A formal, documented and consented arrangement, if the group chooses "
         "one. BR-015, FR-DEF-006, C-06, EC-096.",
            ],
            [
                "The client device clock is wrong and reports the due date as past",
                "The state machine runs on the server's recorded UTC timestamps. A skewed "
                "client can never advance or postpone a default.",
                "SCR-APP-08",
                "*Your phone time is out by more than a day. Your payment status is correct "
                "regardless.*",
                         "Client clock is corrected or the app resynchronises, NFR-LOC-003, "
         "EC-031.",
            ],
            [
                "A default is recorded, and later the member disputes that it should have "
                "been",
                "The dispute thread is created against the contribution with the full state "
                "history as evidence. A dispute does not block unrelated contributions.",
                "SCR-APP-14",
                "*Your dispute is open. Your other payments and the Ajo continue as normal "
                "while we look at it.*",
                         "Flow 2.11. FR-DISP-001, FR-DISP-007, EC-095.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =================================================================== 2.7
    {"t": "h2", "text": "2.7 Failed payment"},
    {"t": "h3", "text": "2.7.1 Purpose"},
    {
        "t": "p",
        "text": (
            "A failed payment is a normal commercial event, not a disciplinary one. The flow "
            "must make three things true simultaneously: the member knows nothing was taken "
            "from them, the obligation remains open and visible, and the retry is safe to "
            "perform as many times as the member needs. It must never produce a ledger entry "
            "for a payment that did not happen, because an entry for a non-event is a false "
            "record that no role can later remove (BR-025, BR-013)."
        )
    },
    {"t": "h3", "text": "2.7.2 Swimlane"},
    {
        "t": "code",
        "text": """
MEMBER          AJO.ng            PROVIDER          LEDGER
   |  Pay now      |                  |                 |
   |--------------->| POST /payments  |                 |
   |               |  key: idem-1     |                 |
   |               |  PENDING  ------>|                 |
   |  <provider>    |                  |  DECLINED       |
   |----------------------------------------->|  (insufficient funds)
   |               |<-----------------|                 |
   |               |  payment FAILED  |                 |
   |               |  NOTHING POSTED TO THE LEDGER      |
   |               |  obligation still PENDING         |
   |  contribution.failed  |           |                 |
   |  (push, email, SMS opt-in)          |                 |
   |  "Nothing was taken. You can try    |                 |
   |   again or use another method."     |                 |
   |  Retry        |                  |                 |
   |--------------->| POST /contributions/:id/retry      |
   |               |  NEW idem key -> idem-2             |
   |               |  same obligation, no second one     |
   |               |  PENDING ------>|                 |
   |               |                  |  SUCCESS        |
   |               |<-----------------|                 |
   |               |  SUCCESS -> 2.4 steps 8 to 11       |
   |               |  PAID, receipt, confirmation        |
   |  If the due time passes instead, the flow continues in 2.6.
""",
    },
    {"t": "h3", "text": "2.7.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.7.1", "Member", "SCR-APP-08",
                "Taps *Pay now* on a PENDING contribution.",
                "The amount shown is NGN 1,020.00, split as NGN 1,000.00 contribution and "
                "NGN 20.00 fee. Acknowledgement is captured.",
                "FR-PAY-002, BR-011, BR-010",
            ],
            [
                "2.7.2", "AJO.ng", "SCR-APP-09",
                "Creates the payment record and calls the provider.",
                "`POST /payments` with an `Idempotency-Key`. Payment moves INITIATED to "
                "PENDING. The amount is fixed at initiation.",
                "BR-024, FR-PAY-004, CAN §4",
            ],
            [
                "2.7.3", "Provider", "—",
                "Declines, or times out, or the issuer refuses.",
                "The provider status is mapped to `FAILED` with a machine-readable reason "
                "code retained. No provider text is shown raw to the member.",
                "CAN §4, NFR-SEC-003",
            ],
            [
                "2.7.4", "AJO.ng", "—",
                "Marks the payment FAILED and posts nothing to the ledger.",
                "No `contribution.received`, no `fee.recognised`, no escrow movement, no "
                "fee. There is nothing to reverse because nothing was written. The "
                "contribution remains PENDING with the full amount outstanding.",
                "BR-021, BR-013, BR-025",
            ],
            [
                "2.7.5", "System", "SCR-APP-12",
                "Sends `contribution.failed` immediately.",
                "Push and email, SMS on the optional opt-in. The message says the payment "
                "did not go through and that nothing has been taken.",
                "CAN §8, FR-NOTIF-001",
            ],
            [
                "2.7.6", "Member", "SCR-APP-08",
                "Sees the failure with a retry control and a plain-language reason.",
                "Reason is expressed as a category the member can act on, for example "
                "*not enough in the account* or *the bank refused it*, with the provider "
                "reference available in the detail view.",
                "FR-PAY-006, NFR-ACC-003",
            ],
            [
                "2.7.7", "Member", "SCR-APP-08",
                "Retries.",
                "`POST /contributions/:id/retry` creates a new payment against the *same* "
                "obligation with a new `Idempotency-Key`. It does not create a second "
                "obligation and does not change the amount.",
                "FR-DEF-003, FR-PAY-008, BR-024",
            ],
            [
                "2.7.8", "System", "—",
                "If retries are not made before the due time, the contribution continues into "
                "the default flow.",
                "The due date is not extended by a failure. The 48-hour grace runs from the "
                "recorded due time exactly as it would have, and a member who is actively "
                "retrying is treated identically to one who is not.",
                "BR-016, NFR-LOC-003, flow 2.6",
            ],
        ],
        "widths": [0.49, 0.78, 0.84, 1.41, 2.0, 0.98],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.7.4 Happy path"},
    {
        "t": "p",
        "text": (
            "The member's bank declines the charge. The payment is marked FAILED with the "
            "provider's reference, nothing is written to the ledger, the contribution is "
            "still PENDING and still shows NGN 1,020.00 outstanding. The member is told "
            "immediately that nothing was taken, and is offered a retry. They top up and "
            "retry; the second attempt carries a new idempotency key against the same "
            "obligation, succeeds, and the flow rejoins 2.4 at step 8: two ledger entries, a "
            "PAID contribution, a receipt and a confirmation. From the Ajo's point of view, "
            "one member paid one round on time. The failure never became an event in the "
            "Ajo's history beyond a payment record with two attempts."
        )
    },
    {"t": "h3", "text": "2.7.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The provider declines for insufficient funds",
                "FAILED with reason `insufficient_funds`. The member may top up and retry. No "
                "fee is charged for a failed attempt.",
                "SCR-APP-08",
                "*Not enough in the account. Nothing was taken. Top up and try again.*",
                         "Retry from the contribution, EC-019.",
            ],
            [
                "The provider is unreachable at initiation",
                "Initiation fails before any charge is possible. The member is told to try "
                "again; nothing is pending and nothing is owed differently.",
                "SCR-APP-09",
                "*We could not reach the payment provider. Nothing was taken. Try again in a "
                "minute.*",
                         "Automatic client retry, then manual. No payment record is left "
         "dangling, EC-018.",
            ],
            [
                "The provider times out after the charge was made",
                "The payment is `UNKNOWN`, not FAILED. The contribution stays PENDING and the "
                "member is not prompted to pay again.",
                "SCR-APP-09",
                "*We are confirming with the payment provider. Please do not pay again.*",
                         "Reconciliation against provider settlement, NFR-AVL-003, EC-048.",
            ],
            [
                "The member retries repeatedly, more than three times",
                "Each attempt is a separate payment record. The obligation is unchanged. After "
                "a configurable attempt threshold the app suggests a different method or "
                "contacting support, and the risk engine may flag velocity.",
                "SCR-APP-08",
                "*Several attempts have failed. Try a different account, or contact us and we "
                "will help.*",
                                  "Support assists; support does not move money or change a balance, "
         "BR-023, EC-024.",
            ],
            [
                "A member fails on many Ajos at once, for example a phone shared across "
                "accounts",
                "Risk velocity rules raise a `risk_events` row for human review. Accounts are "
                "not frozen automatically on velocity alone at launch.",
                "SCR-ADM-05",
                "The member sees nothing; the officer sees the pattern.",
                         "`risk_officer` reviews, approves or rejects the override, with the "
         "decision recorded. Flow 2.15, FR-ADM-006, EC-025.",
            ],
            [
                "The failure is actually the provider's fault and the member is penalised for "
                "it",
                "Reconciliation attributes the failure to the provider where the evidence "
                "shows it, and the grace window is not treated as consumed by a platform "
                "error.",
                "SCR-APP-08",
                "*This one was on us, not you. Your deadline has been moved to DATE.*",
                         "Due-date correction with a recorded reason. Requires this to be a "
         "deliberate policy, not an accident, EC-029.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =================================================================== 2.8
    {"t": "h2", "text": "2.8 Cancelled payment: the member abandons the provider page"},
    {"t": "h3", "text": "2.8.1 Purpose"},
    {
        "t": "p",
        "text": (
            "The most common payment failure in Nigeria is not a decline; it is a person "
            "closing the page because they found the money in the wrong place, or because "
            "they were interrupted. This flow makes abandonment safe and boring: the "
            "obligation is untouched, no fee is charged, nothing is written to the ledger, "
            "the member is told exactly what is still owed, and returning to pay later is one "
            "tap rather than a re-entry exercise."
        )
    },
    {"t": "h3", "text": "2.8.2 Swimlane"},
    {
        "t": "code",
        "text": """
MEMBER          AJO.ng            PROVIDER          LEDGER
   |  Pay now      |                  |                 |
   |--------------->| POST /payments  |                 |
   |               |  key: idem-1     |                 |
   |  <provider page opens>               |                 |
   |  closes the tab / presses back /      |                 |
   |  the network drops                    |                 |
   |               |<-----------------|  CANCELLED      |
   |               |  payment CANCELLED (or UNKNOWN if no  |
   |               |  provider confirmation ever arrives)   |
   |               |  NOTHING POSTED                        |
   |               |  contribution still PENDING            |
   |               |  still owes NGN 1,020.00               |
   |  "You still owe this round. Pay any time|
   |   before the due date."               |                 |
   |  Pay again    |                  |                 |
   |--------------->| POST /payments  |                 |
   |               |  key: idem-2     |                 |
   |               |  same obligation |                 |
   |               |  SUCCESS ----->|                 |
   |               |<-----------------|                 |
   |               |  PAID, receipt (2.4 steps 8 to 11)    |
   |  If the due date passes, the flow continues in 2.6.
   |  The idempotency key of the abandoned attempt is retained so a
   |  late-arriving provider result can still be matched correctly.
""",
    },
    {"t": "h3", "text": "2.8.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.8.1", "Member", "SCR-APP-09",
                "Opens the provider surface and then abandons it.",
                "AJO.ng holds no state that requires the member to return to a specific "
                "step. The client persists the idempotency key locally so a retry after a "
                "crash or a reinstall is still safe.",
                "BR-024, NFR-PERF-004",
            ],
            [
                "2.8.2", "Provider", "—",
                "Reports CANCELLED, or reports nothing at all.",
                "A confirmed CANCELLED is mapped directly. An absent confirmation becomes "
                "UNKNOWN after the provider's agreed timeout, never a silent FAILED and never "
                "a silent SUCCESS.",
                         "CAN §4, NFR-PERF-003, EC-035, EC-048"
            ],
            [
                "2.8.3", "AJO.ng", "—",
                "Leaves the obligation exactly as it was.",
                "Contribution remains PENDING with the full NGN 1,020.00 outstanding. No "
                "ledger entry, no fee, no state regression. The due date is unchanged.",
                "BR-021, BR-005",
            ],
            [
                "2.8.4", "Member", "SCR-APP-08",
                "Returns to the contribution later.",
                "The screen shows the outstanding amount, the due date and a single *Pay now* "
                "control. The abandoned attempt is visible in the payment history as "
                "*cancelled* so the member is never confused about their own record.",
                "FR-PAY-006, FR-CON-002, P1",
            ],
            [
                "2.8.5", "Member", "SCR-APP-08",
                "Pays again, before or after the due date.",
                "A new payment against the same obligation with a new key. A payment after "
                "the due date is a late payment, not a default, and the default clock is "
                "governed by the recorded due timestamp.",
                         "FR-DEF-003, BR-016, EC-012",
            ],
        ],
        "widths": [0.49, 0.78, 0.84, 1.41, 2.0, 0.98],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.8.4 Happy path"},
    {
        "t": "p",
        "text": (
            "The member opens the provider page, realises the money is in the other account, "
            "and closes the tab. The provider reports CANCELLED. The payment record shows "
            "cancelled, the contribution still shows NGN 1,020.00 outstanding with the "
            "original due date, and nothing has been charged. Two days later the member moves "
            "the money and taps *Pay now* once. The new attempt succeeds, the ledger posts "
            "the contribution and the fee, the contribution becomes PAID, and the receipt "
            "lists both attempts so the member's own record is complete and honest. No fee "
            "was collected for the abandoned attempt, because no money moved."
        )
    },
    {"t": "h3", "text": "2.8.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The member abandons and the provider never confirms anything",
                "The payment becomes UNKNOWN after the timeout and is held for "
                "reconciliation. The contribution is not shown as failed and the member is "
                "not asked to pay again.",
                "SCR-APP-09",
                "*We are still checking this payment with the provider. Do not pay again.*",
                         "Reconciliation within 24 hours. NFR-AVL-003, EC-001, EC-048.",
            ],
            [
                "The member abandons and then pays, and the first attempt later turns out to "
                "have succeeded",
                "The late success is detected by reconciliation and handled as an overpayment, "
                "not as a second contribution and not as a silent absorption.",
                "SCR-APP-09",
                "*You have paid this round twice. We are holding the extra NGN 1,020.00 and "
                "will refund it.*",
                                  "Refund on request, or consented application to a future round, flow "
         "2.9, EC-004.",
            ],
            [
                "The member abandons repeatedly on every round",
                "Pattern is visible to the member as a personal record and to risk as a "
                "velocity signal, but the obligation is not escalated faster than the fixed "
                "sequence allows.",
                "SCR-APP-08 / SCR-ADM-05",
                "*You have started three payments and not finished any. Your money is not at "
                "risk and nothing extra is owed.*",
                         "Risk review. No member-visible shaming. BR-014, EC-024.",
            ],
            [
                "The member abandons and never returns, and the due time passes",
                "The default flow in 2.6 runs from the recorded due timestamp exactly as it "
                "would have for a member who never started.",
                "SCR-APP-08",
                "The default sequence messages, unchanged.",
                         "BR-016, flow 2.6, EC-016.",
            ],
            [
                "The client crashes after the charge but before the response is stored "
                "locally",
                "The idempotency key is derived deterministically from the contribution, the "
                "attempt number and the device, so a regenerated key still matches the "
                "original attempt.",
                "SCR-APP-09",
                "*We found your last payment attempt. Nothing was charged twice.*",
                         "Automatic. BR-024, EC-035.",
            ],
            [
                "The member believes a charge happened and cannot find it",
                "The payment history shows every attempt with its state and provider "
                "reference, so the member can answer the question themselves before contacting "
                "support.",
                "SCR-APP-09 / SCR-APP-11",
                "*Here is every payment you have made and every attempt, including the ones "
                "that did not go through.*",
                         "Support can read this. Support cannot alter it. BR-023, P1, EC-026.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =================================================================== 2.9
    {"t": "h2", "text": "2.9 Refund"},
    {"t": "h3", "text": "2.9.1 Purpose"},
    {
        "t": "p",
        "text": (
            "A refund returns money that was collected and should not have been kept. There "
            "are exactly four triggers in this specification, and only two of them occur in "
            "normal operation. Because a refund is itself a money movement, it is governed by "
            "the same rules as a contribution: an idempotency key, a reversing entry rather "
            "than an edit, a balance that must reach zero, and a receipt. The 2% fee on a "
            "refunded contribution is open decision D-05 and is not invented here."
        )
    },
    {"t": "h3", "text": "2.9.2 Swimlane"},
    {
        "t": "code",
        "text": """
TRIGGER            AJO.ng            PROVIDER          LEDGER        MEMBER
   |                  |                  |                 |            |
   |  A. Enrollment    |                  |                 |            |
   |  closes at day 5 |  CANCELLED with a recorded reason      |            |
   |  positions unfull|  refund every collected contribution  |            |
   |                  |  in full; no position is filled by a  |            |
   |                  |  substitute, no debt survives         |            |
   |                  |----------------->| REVERSED        |            |
   |                  |  reversal entry   |                 |            |
   |                  |  (never an edit)  |                 |            |
   |                  |----------------------------------------->|  receipt
   |                  |                  |                 |            |
   |  B. Provider      |  REVERSED -> payment REVERSED         |            |
   |  reversal         |  contribution returns to PENDING     |            |
   |                  |  or is settled out by reversal        |            |
   |                  |----------------->| REVERSED        |            |
   |                  |----------------------------------------->|  receipt
   |                  |                  |                 |            |
   |  C. Ajo CANCELLED |  no disbursement has occurred, so   |            |
   |  before round 1   |  no payout recognition exists       |            |
   |  disburses        |  reversal only, liability unwound   |            |
   |                  |----------------------------------------->|  receipt
   |                  |                  |                 |            |
   |  D. Risk decision |  risk_officer records trigger,       |            |
   |  or dispute       |  evidence, decision, rationale,      |            |
   |  resolution       |  identity. Reversal only.            |            |
   |                  |----------------------------------------->|  receipt
   |                  |                  |                 |            |
   |  NEVER: an edit, a delete, or a silent absorption into a later round.
""",
    },
    {"t": "h3", "text": "2.9.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.9.1", "System", "SCR-APP-05",
                "Enrollment closes at day 5 with positions unfilled.",
                "The Ajo transitions to CANCELLED with the reason recorded. Every collected "
                "contribution is refunded in full. In the normal case there is nothing to "
                "refund, because contributions are only collected from an ACTIVE Ajo; the "
                "rule exists so that a prepaid edge case cannot leave money stranded.",
                         "BR-001, CAN §3, EC-051"
            ],
            [
                "2.9.2", "AJO.ng", "SCR-APP-10",
                "Initiates the refund to the original payment instrument.",
                "The refund is a money movement and therefore requires an `Idempotency-Key`, "
                "a recorded trigger and a receipt. The member is told the expected credit "
                "window, which cannot be stated as a firm date until ProvidusUnity confirms "
                "it in writing.",
                         "BR-024, D-07, DEP-02, EC-017",
            ],
            [
                "2.9.3", "AJO.ng", "—",
                "Posts the reversal in the ledger.",
                "A reversal entry is posted; no existing entry is edited or deleted by any "
                "role, including `super_admin`. The reversal transaction must balance to zero "
                "or be rejected.",
                "BR-025, BR-013, C-05, G6",
            ],
            [
                "2.9.4", "Provider", "—",
                "Credits the member.",
                "Payment state becomes REVERSED on provider confirmation. The refund SLA is "
                "open decision D-07 and must not be publicised as a promise until it is "
                "answered in writing.",
                         "CAN §4, D-07, EC-011"
            ],
            [
                "2.9.5", "Member", "SCR-APP-11",
                "Receives the refund receipt and sees the corrected balance.",
                "The receipt shows the original charge, the reversal, the net position and "
                "the resulting state, each on its own line. The original payment record is "
                "retained and marked reversed, never removed, so the member's history is "
                "complete.",
                "FR-PAY-007, FR-TXN-001, NFR-AUD-004",
            ],
            [
                "2.9.6", "Risk officer or support", "SCR-ADM-05 / SCR-ADM-04",
                "Approves a refund outside the automatic triggers.",
                "The decision is recorded with trigger, evidence, decision, rationale and "
                "officer identity, and is visible in the Risk screen and the audit log. "
                "Support may propose but may never execute a refund.",
                "FR-ADM-006, BR-023, NFR-AUD-003, NFR-AUD-004",
            ],
        ],
        "widths": [0.49, 0.92, 0.87, 1.39, 1.95, 0.88],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.9.4 Happy path"},
    {
        "t": "p",
        "text": (
            "An Ajo opens enrollment, three members join, and day 5 arrives with seven "
            "positions unfilled. The system cancels the Ajo automatically with a recorded "
            "reason, tells the organiser and the three members what happened and why, and "
            "refunds anything that was collected, in full. Because contributions are only "
            "collected from an ACTIVE Ajo, in practice nothing was collected and there is "
            "nothing to unwind; had a member prepaid, the reversal entry would post, balance "
            "to zero, and the member's receipt would show the original charge and its "
            "reversal as two separate lines. No member is left with a residual obligation, no "
            "fee is quietly kept or quietly refunded, and the organiser is free to try again "
            "with a group that fills."
        )
    },
    {"t": "h3", "text": "2.9.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The provider has already moved the money out of the approved arrangement",
                "A refund is no longer a simple reversal. The Ajo cannot disburse and the "
                "member's money is behind an external round trip, so the case goes to risk "
                "and to ProvidusUnity, not to a silent workaround.",
                "SCR-APP-10",
                "*Your refund is with our payment partner. We will tell you what is happening "
                "every 48 hours until it is done.*",
                         "Manual case with `risk_officer`, a recorded decision and a named "
         "contact at ProvidusUnity, EC-010.",
            ],
            [
                "The member asks for the 2% fee to be refunded as well",
                "Not answered by the system. D-05 is open and the treatment of the fee at "
                "cancellation is owned by the founders and legal.",
                "SCR-APP-13",
                "*We are confirming how the platform fee is handled on a refund. You will get "
                "a definite answer, not an estimate.*",
                         "Decision D-05, then a versioned and audited policy change. D-05, "
         "BR-026, EC-027.",
            ],
            [
                "A refund is claimed twice for the same payment",
                "The second request is rejected by the idempotency key and the uniqueness of "
                "one reversal per payment. The rejection is recorded.",
                "SCR-APP-13",
                "*This payment has already been refunded. Here is the refund receipt.*",
                         "None, EC-011.",
            ],
            [
                "The refund takes longer than the stated window",
                "The member is not left guessing. The case is swept, the reason is asked of "
                "the provider, and the member receives a proactive update at a fixed interval "
                "until it resolves.",
                "SCR-APP-10 / SCR-APP-12",
                "*Still waiting on the payment partner. Next update by DATE.*",
                         "Support sweep. D-07 must be answered in writing before any window is "
         "promised, EC-017.",
            ],
            [
                "An overpaid amount is offered back against a future round",
                "Only with explicit, recorded member consent. Silent absorption is prohibited: "
                "money returned is money returned.",
                "SCR-APP-09",
                "*You have NGN 1,020.00 in credit. Refund it, or apply it to a future round "
                "with your agreement?*",
                         "Member chooses. BR-032, EC-004.",
            ],
            [
                "A payout has already been recognised and then must be clawed back",
                "Not possible under normal operation: recognition happens only when a payout "
                "is released, and a released payout is paid to the member's own verified "
                "account. Clawback from a member is not a product capability and is not "
                "proposed.",
                "—",
                "The screen that would offer it does not exist.",
                         "None. The Ajo is placed under formal recovery instead. BR-018, BR-032, "
         "EC-010, EC-042.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Open decision D-05 — who bears the fee on a cancellation refund",
        "text": (
            "CANONICAL.md records D-05 as open: *is the fee at Ajo cancellation refunded?* "
            "Three positions are defensible. Refund the fee in full, which is the most "
            "trust-preserving and the most expensive. Retain the fee, on the basis that the "
            "member used the platform's record-keeping. Or split it, which is the most "
            "commercially defensible and the hardest to explain to a member whose Ajo "
            "cancelled before it started. **Recommendation: refund the fee in full whenever a "
            "contribution is refunded, and state this plainly on the fee screen. Owner: "
            "Founders and Legal. Must be decided before launch, not after the first "
            "cancellation.** The flow above is written so that the answer is a configuration "
            "value applied at the reversal, not a code fork in the refund path."
        )
    },
    {"t": "pagebreak"},

    # ================================================================== 2.10
    {"t": "h2", "text": "2.10 Leaving an Ajo: before activation and after activation"},
    {"t": "h3", "text": "2.10.1 Purpose"},
    {
        "t": "p",
        "text": (
            "Leaving is the hardest thing in an Ajo to get right, because a member's genuine "
            "financial difficulty and a member's indifference look identical from the "
            "outside. Before activation, leaving is easy and cheap: an invitation can be "
            "declined, an organiser can remove a pre-activation member, a position is simply "
            "released. After activation, leaving is not unilateral for anybody. The position "
            "belongs to the Ajo, not to the member, because the pot is calculated on that "
            "position existing. So the only path is a formal replacement or transfer request "
            "that is recorded, reviewed and approved, and in which the incoming member "
            "assumes the outgoing member's position and all remaining obligations (BR-002, "
            "BR-003, BR-004, BR-007, C-06)."
        )
    },
    {"t": "h3", "text": "2.10.2 Swimlane"},
    {
        "t": "code",
        "text": """
BEFORE ACTIVATION (DRAFT / ENROLLMENT)
   member declines invitation --> token invalidated, seat released, no account
   member withdraws           --> membership released, position freed
   organizer removes member   --> DELETE /ajos/:id/members/:memberId
   remaining members are unaffected. No obligation ever existed.

AFTER ACTIVATION (ACTIVE / ROUND_IN_PROGRESS)
   member asks to leave
        |
        v
   "You cannot leave this Ajo on your own. What you
    can do is ask for a replacement. Here is what
    that involves."
        |
        v
   POST /ajos/:id/members/:memberId/replace
   reason recorded, request created, timestamped
        |
        v
   risk_officer review: is the request genuine?      organizer: does the
   is there a candidate? does the Ajo stay funded?    group consent?
        |
        +-- rejected --> reason recorded, member told, Ajo unchanged
        |
        v
   candidate invited, KYC'd, accepts the position
   and explicitly assumes the REMAINING obligations
        |
        v
   outgoing member's membership ends, both parties
   recorded in the ledger, settled history retained
        |
        v
   position occupied. Round continues. No other member
   pays more. No member's turn moves.
        |
   no candidate found --> position vacant, round funding
   shortfall tracked, HELD if the pot cannot be funded,
   recovery process begins. Never a reduced payout.
""",
    },
    {"t": "h3", "text": "2.10.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.10.1", "Invitee", "SCR-APP-04",
                "Declines the invitation before joining.",
                "`POST /invitations/:token/decline`. No account is created, the token is "
                "invalidated, and the seat returns to the organiser as unfilled.",
                         "FR-INV-006, US-18, EC-126",
            ],
            [
                "2.10.2", "Member", "SCR-APP-05",
                "Withdraws while the Ajo is in DRAFT or ENROLLMENT.",
                "Membership is released and the position is freed. Because no obligation has "
                "ever crystallised, nothing is owed, nothing is reversed and no other member "
                "is affected.",
                         "BR-007, BR-005",
            ],
            [
                "2.10.3", "Organiser", "SCR-APP-06",
                "Removes a member while the Ajo is in DRAFT or ENROLLMENT.",
                "`DELETE /ajos/:id/members/:memberId` is permitted only pre-activation. The "
                "removal is recorded with actor, role, timestamp and both states. After "
                "activation the same call is rejected for every role.",
                         "BR-007, FR-MEM-003, CAN §2"
            ],
            [
                "2.10.4", "Member", "SCR-APP-08",
                "Asks, after activation, what happens if they cannot continue.",
                "The screen states, in advance and in plain language: the complete-cycle "
                "commitment, the position lock, the 48-hour grace, and the fact that there is "
                "no unilateral exit but there is a formal route that is designed to be fast "
                "and not punitive.",
                "FR-DEF-002, BR-003, C-06, US-35",
            ],
            [
                "2.10.5", "Member", "SCR-APP-08",
                "Submits a formal replacement or transfer request.",
                "`POST /ajos/:id/members/:memberId/replace` with a reason and, where "
                "available, a proposed successor. The request is timestamped and attributed. "
                "The member remains bound until the request is resolved; the request is a "
                "process, not an exit.",
                "FR-MEM-006, FR-DEF-008, BR-003, flow 2.6 step 11",
            ],
            [
                "2.10.6", "Organiser", "SCR-APP-05",
                "Is notified and may comment.",
                "The organiser may support, oppose or propose a candidate, and may not "
                "approve. The organiser cannot remove the member, cannot absorb the debt, and "
                "cannot guarantee the departing member's position on the platform.",
                "BR-008, CAN §2, FR-POUT-005",
            ],
            [
                "2.10.7", "Risk officer", "SCR-ADM-05",
                "Reviews the request.",
                "The officer assesses whether the request is genuine, whether the round stays "
                "fundable, whether fraud is involved, and whether the candidate is suitable. "
                "The decision records trigger, evidence, decision, rationale and identity.",
                "FR-ADM-005, FR-ADM-006, R4, NFR-AUD-003",
            ],
            [
                "2.10.8", "Candidate", "SCR-APP-04",
                "Accepts the position and its obligations.",
                "The candidate is invited, completes identity verification, and on acceptance "
                "explicitly assumes the position, the round that is due and every remaining "
                "obligation. The assumption is recorded with the terms version.",
                "FR-MEM-007, BR-004, BR-030, flow 2.3",
            ],
            [
                "2.10.9", "AJO.ng", "SCR-APP-05",
                "Completes the transfer.",
                "Both parties are recorded in the ledger. The outgoing member's settled "
                "contributions and receipts are retained and remain visible to them. The "
                "outgoing member is not refunded for contributions already made, because "
                "those funds are in the pot that funded other members' turns.",
                "BR-003, FR-MEM-007, BR-025, BR-032",
            ],
            [
                "2.10.10", "AJO.ng", "SCR-APP-10",
                "If no candidate is found, tracks the shortfall.",
                "The position is vacant, the round cannot be fully funded, and the payout goes "
                "to HELD rather than paying a reduced pot. The recovery process runs. No "
                "other member is charged extra.",
                         "BR-018, BR-015, G4, EC-065, EC-063",
            ],
        ],
        "widths": [0.49, 0.78, 0.84, 1.41, 2.0, 0.98],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.10.4 Happy path"},
    {
        "t": "p",
        "text": (
            "A member's income changes and they cannot sustain the commitment. They read, "
            "before they ask, that leaving alone is not possible and that the route is a "
            "replacement. They submit a request with a reason. The organiser is told and may "
            "propose a colleague from the same workplace, who is invited, passes identity "
            "verification and, on accepting, sees exactly what they are taking on: position 4, "
            "round 4, NGN 1,000.00 per month plus the 2% fee, and the remaining obligations "
            "in full. They accept. Both parties are recorded, the position is occupied, the "
            "round continues, no other member pays one naira more, and the outgoing member "
            "keeps every receipt from the rounds they did pay. The Ajo did not break. That is "
            "the entire design intent of the flow."
        )
    },
    {"t": "h3", "text": "2.10.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The member simply stops paying after activation",
                "The default flow in 2.6 runs in full. The member remains a member. No "
                "unilateral exit exists, and no role may create one.",
                "SCR-APP-08",
                "*Your position is still yours. A replacement is the way out, and you can ask "
                "for one today.*",
                         "Replacement request, or risk decision. BR-003, EC-016.",
            ],
            [
                "The member asks to be removed by the organiser after activation",
                "Refused. Removal is pre-activation only, for every role, with no exception "
                "path.",
                "SCR-APP-06",
                "*Members cannot be removed from an active Ajo. A replacement has to take the "
                "position.*",
                         "Replacement request. BR-007, EC-086.",
            ],
            [
                "No suitable candidate can be found",
                "The position stays vacant. The round's funding shortfall is tracked and, if "
                "the pot cannot be fully funded, the payout is HELD and recovery begins.",
                "SCR-APP-10",
                "*This Ajo is one member short of funding a full round. We are not paying a "
                "partial pot. Here is what we are doing.*",
                         "Organiser recruitment within the Ajo, or formal recovery. BR-018, "
         "BR-015, EC-065.",
            ],
            [
                "The departing member had already received their own turn",
                "Nothing is clawed back. The payout was paid in full when it was due. A member "
                "who leaves after collecting has still paid every round they owed, and the "
                "product has no mechanism to take money back from a member.",
                "SCR-APP-11",
                "*Your completed rounds stay on your record. Your remaining obligations are "
                "what the replacement takes on.*",
                         "None needed. BR-032, BR-012, EC-068.",
            ],
            [
                "The departing member is in DEFAULTED at the time of the request",
                "The request does not erase the default. The default record is retained, the "
                "replacement assumes the position, and the outstanding amount follows the "
                "position into the recovery process.",
                "SCR-APP-05",
                "To the organiser: *The position has a replacement. The outstanding amount "
                "attached to that position is still outstanding.*",
                         "Recovery, or a risk-officer decision. FR-DEF-007, EC-086, EC-095.",
            ],
            [
                "A member is removed by a fraudster who has compromised an organiser account",
                "Removal is refused post-activation, so the impersonation cannot remove "
                "members. A compromised organiser can still issue invitations, so "
                "invitation-graph anomalies are a risk signal and the audit log is the "
                "evidence.",
                "SCR-ADM-05 / SCR-ADM-08",
                "The officer sees the organiser's activity graph and the refused removal "
                "attempt.",
                         "Risk review, session revocation, freeze. Flow 2.15, NFR-AUD-004, "
         "EC-110.",
            ],
            [
                "The member asks to leave a CANCELLED Ajo",
                "Terminal states are terminal. There is nothing to leave, and nothing owed. "
                "The membership is simply closed out read-only.",
                "SCR-APP-05",
                "*This Ajo ended. Your record stays available to you.*",
                         "Read the statement. BR-009, EC-064.",
            ],
            [
                "A member in a frozen account requests a replacement",
                "The request is accepted and queued, but the outgoing member's frozen state "
                "is a separate matter. Freezing stops money movement; it does not create or "
                "destroy membership obligations.",
                "SCR-APP-13",
                "*Your request is recorded. Your account restriction is separate and we will "
                "explain it.*",
                         "Flow 2.12 and 2.15, EC-034.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # ================================================================== 2.11
    {"t": "h2", "text": "2.11 Dispute"},
    {"t": "h3", "text": "2.11.1 Purpose"},
    {
        "t": "p",
        "text": (
            "Money disputes in a traditional Ajo are settled by memory, volume and "
            "relationships. The digital dispute exists to replace all three with a "
            "timestamped, permanent, exportable thread attached to a specific round or "
            "contribution, with every action attributed. It must be usable by a member with a "
            "poor connection, it must not be a pretext for freezing a member's money without "
            "a recorded risk reason, and it must be resolved by a role whose decision and "
            "rationale are permanent."
        )
    },
    {"t": "h3", "text": "2.11.2 Swimlane"},
    {
        "t": "code",
        "text": """
MEMBER          AJO.ng           ORGANISER        SUPPORT      RISK
   |              |                  |                |                |
   |  I paid and   |                  |                 |                |
   |  it is not    |                  |                 |                |
   |  showing      |                  |                 |                |
   |--------------->| POST /disputes |                |                |
   |              |  scoped to the   |                 |                |
   |              |  round and the   |                 |                |
   |              |  contribution    |                 |                |
   |              |  dispute.opened -> counterparty,
   |              |  + organiser      |                |                |
   |--------------->| POST /disputes/:id/evidence   |                |
   |              |  docs validated,  |                |                |
   |              |  re-encoded,     |                |                |
   |              |  permanent       |                |                |
   |              |  open + a response window          |              |
   |              |----------------->| responds        |                |
   |              |                  |--------------->| reads all, contacts
   |              |                  |                 | both, assists,
   |              |                  |                 | PROPOSES a fix
   |              |                  |                 | CANNOT move money
   |              |                  |                 |------------->
   |              |                  |                |     decides if a
   |              |                  |                |     a risk reason
   |              |  outcome + reason + evidence + deciding role
   |              |  (permanent)      |                |                |
   |<-------------|  dispute.resolved |                |                |
   |  Other contributions, other rounds and the Ajo are unaffected.
""",
    },
    {"t": "h3", "text": "2.11.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.11.1", "Member", "SCR-APP-08 / SCR-APP-11",
                "Sees a discrepancy: a payment that shows as uncredited, a position that "
                "looks wrong, a duplicate charge, or a receipt that does not match the "
                "statement.",
                "Every screen that can generate a dispute carries the entry point, and the "
                "entry point carries the object it disputes. A member is never asked to "
                "describe their dispute in the abstract.",
                "FR-DISP-001, N8, P5",
            ],
            [
                "2.11.2", "Member", "SCR-APP-14",
                "Opens the dispute with a category, a description and the object in question.",
                "`POST /disputes` creates a dispute with a timestamp, a state and a permanent "
                "thread. The ledger, the payment records and the state history are "
                "automatically attached as the platform's own evidence.",
                "FR-DISP-001, NFR-AUD-001, N8",
            ],
            [
                "2.11.3", "AJO.ng", "SCR-APP-12",
                "Notifies the counterparty and the organiser.",
                "`dispute.opened` on push and email, immediately. The notification states that "
                "a dispute exists and where to respond, without editorialising on the merits.",
                "CAN §8, FR-DISP-006",
            ],
            [
                "2.11.4", "Both parties", "SCR-APP-14",
                "Attach evidence and exchange messages.",
                "`POST /disputes/:id/evidence` and `POST /disputes/:id/messages`. Uploads are "
                "validated for type, size and content server-side and re-encoded. The thread "
                "is append-only and exportable.",
                "FR-DISP-002, NFR-SEC-006, FR-DISP-004",
            ],
            [
                "2.11.5", "Support", "SCR-ADM-04",
                "Reads, contacts both parties and assists.",
                "`support` may read all disputes, contact members, assist and propose a "
                "resolution. It may not initiate or moderate a payout, change a balance or "
                "override a risk decision. Every attempt is rejected and recorded.",
                "BR-023, FR-DISP-003, FR-ADM-004, FR-ADM-012, US-37",
            ],
            [
                "2.11.6", "Risk officer", "SCR-ADM-05",
                "Decides whether a risk reason exists to freeze or hold.",
                "A payout may be frozen only with a recorded risk reason. A dispute on its own "
                "is never sufficient, because a dispute is a process, not a verdict.",
                "FR-DISP-007, FR-ADM-005, BR-018",
            ],
            [
                "2.11.7", "Decision maker", "SCR-ADM-04",
                "Resolves the dispute.",
                "The outcome is recorded with the reason, the evidence relied on and the role "
                "that decided, permanently. `dispute.resolved` is sent to the parties on push "
                "and email.",
                "FR-DISP-005, FR-DISP-006, NFR-AUD-003",
            ],
            [
                "2.11.8", "AJO.ng", "SCR-APP-05",
                "Keeps the rest of the Ajo running throughout.",
                "A dispute does not block a member's unrelated contributions, does not pause "
                "their notifications, and does not freeze their payout absent a recorded risk "
                "reason. Disposing of the dispute is never allowed to become a way of "
                "stopping the Ajo.",
                "FR-DISP-007, G2",
            ],
        ],
        "widths": [0.49, 0.84, 0.87, 1.39, 1.95, 0.96],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.11.4 Happy path"},
    {
        "t": "p",
        "text": (
            "A member notices that a payment they made on the 12th is not showing as credited "
            "on their statement. They open the contribution, tap *Something is wrong*, and the "
            "dispute is created already scoped to that contribution and that round, with the "
            "platform's own payment record and state history attached as evidence. The "
            "organiser is notified, sees the same thread, and posts a reply. A support agent "
            "reads the whole thing, contacts both parties, and finds that the payment settled "
            "at the provider but the webhook was delayed, so the ledger caught up forty "
            "minutes later. The dispute is resolved with the reason, the evidence relied on "
            "and the deciding role recorded permanently. Meanwhile the member paid their next "
            "contribution on time, their notifications kept arriving, their position did not "
            "move, and no money was frozen while an administrative question was being asked. "
            "The dispute resolved in under the 72-hour target because nobody had to argue from "
            "memory."
        )
    },
    {"t": "h3", "text": "2.11.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The member raises a dispute to delay a payout",
                "The dispute does not block the payout. A dispute may freeze a payout only "
                "with a recorded risk reason, and a risk reason is a risk-officer judgement, "
                "not a member's request.",
                "SCR-APP-10",
                "*Your dispute is open and being worked. Your payout is not affected by it "
                "unless our risk team records a specific reason, and if they do, you will be "
                "told why.*",
                         "Risk review if a reason exists. FR-DISP-007, EC-055.",
            ],
            [
                "The counterparty never responds",
                "The dispute does not stall forever. A response window is set, the thread "
                "records the non-response, and support proposes a resolution on the evidence "
                "available.",
                "SCR-APP-14",
                "*We asked the other party to respond by DATE. If we do not hear back, we "
                "will decide on what we have.*",
                         "Support resolution with the non-response recorded. K-13, EC-090.",
            ],
            [
                "Evidence is uploaded that is malicious or oversized",
                "Rejected at validation. The upload is never stored uninspected, and the "
                "attempt is recorded.",
                "SCR-APP-14",
                "*That file could not be accepted. Accepted types and maximum size are "
                "listed.*",
                         "Re-upload. NFR-S, EC-091.",
            ],
            [
                "The dispute is about a real loss, for example money that reached the provider "
                "and was never credited",
                "It is simultaneously a dispute and a reconciliation exception. The "
                "reconciliation run creates a `risk_events` row that cannot be silently "
                "closed, and the member is told the case is with the payments team.",
                "SCR-APP-14 / SCR-ADM-05",
                "*Your money is not in dispute with the other member. It is unaccounted for at "
                "our payment partner, and we own that.*",
                         "Reconciliation, provider escalation, risk-officer decision with a "
         "recorded rationale. NFR-AUD-005, FR-ADM-011, EC-092.",
            ],
            [
                "A support agent tries to resolve the dispute by moving money",
                "Rejected by role, and the attempt is recorded in the audit log as an "
                "authorisation failure. Support's proposed resolution is advisory.",
                "SCR-ADM-04",
                "*Your role cannot move money. You can propose a resolution and escalate.*",
                         "Escalation to `risk_officer` or `super_admin` within their authority. "
         "BR-023, US-37, NFR-AUD-004, EC-079.",
            ],
            [
                "The dispute concerns a member who is no longer reachable",
                "The dispute proceeds on the evidence. A default may be recorded separately "
                "through the flow in 2.6; the two processes are independent and neither "
                "blocks the other.",
                "SCR-APP-14",
                "*We are proceeding on the record. The other member has not responded.*",
                         "Support decision, risk-officer decision, or both, with the reasoning "
         "recorded, EC-097.",
            ],
            [
                "A member raises many disputes, or disputes everything",
                "Velocity and abuse rules raise a `risk_events` row. Dispute rights are not "
                "removed; the pattern is reviewed by a human and the decision is recorded.",
                "SCR-ADM-05",
                "The member is not shown a warning about their dispute usage.",
                         "Risk review, R4, EC-093.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # ================================================================== 2.12
    {"t": "h2", "text": "2.12 Account suspension and freeze"},
    {"t": "h3", "text": "2.12.1 Purpose"},
    {
        "t": "p",
        "text": (
            "A freeze stops money movement for an account or a platform without deleting "
            "anything, without rewriting history and without disappearing. It is available "
            "three ways: a member freezing their own account when they suspect compromise, a "
            "`risk_officer` freezing on a risk trigger, and a `super_admin` executing an "
            "emergency platform-wide freeze. In all three cases the same four things are true: "
            "money movement stops immediately, the account holder is told, the reason and the "
            "decider are recorded, and only an action after verified identity can lift it."
        )
    },
    {"t": "h3", "text": "2.12.2 Swimlane"},
    {
        "t": "code",
        "text": """
TRIGGER        MEMBER              RISK OFFICER       SUPER ADMIN      LEDGER
   |              |                    |                   |              |
   |  I think my  |                    |                   |              |
   |  account was  |                    |                   |              |
   |  taken over   |                    |                   |              |
   |------------->| self-freeze        |                   |              |
   |              |  all money movement|                   |              |
   |              |  stops immediately |                   |              |
   |              |  account.frozen -> push, email, SMS     |              |
   |              |  sessions revoked |                   |              |
   |  Support verifies my identity, then lifts the freeze.  |              |
   |              |                    |                   |              |
   |              |        RISK TRIGGER (duplicate identity, |
   |              |        fraud pattern, account takeover) |
   |              |                    |  risk_events row  |              |
   |              |                    |  place UNDER REVIEW
   |              |                    |  -> freeze        |              |
   |              |  account.frozen <-|                   |              |
   |              |  member told the reason in plain words  |              |
   |              |                    |  decision: trigger, evidence,
   |              |                    |  rationale, officer identity
   |              |                    |                   |              |
   |              |                    |                   | EMERGENCY:   |
   |              |                    |                   | freeze all  |
   |              |                    |                   | money movement
   |              |                    |                   | platform-wide
   |              |                    |                   | reason recorded
   |  Contributions, positions and receipts stay READABLE throughout.
   |  Nothing is deleted. No role edits the ledger to make a freeze tidy.
""",
    },
    {"t": "h3", "text": "2.12.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.12.1", "User", "SCR-APP-17",
                "Requests a self-freeze because they suspect account takeover.",
                "All money movement stops immediately: no new payment initiation, no payout "
                "release, no withdrawal-equivalent. Existing sessions are revoked. "
                "`account.frozen` is sent on push, email and SMS because this is a "
                "security event.",
                "US-36, CAN §8, FR-SEC-001 to FR-SEC-009",
            ],
            [
                "2.12.2", "Risk officer", "SCR-ADM-05",
                "Places an account or an Ajo under review, then freezes.",
                "`risk_events` records the trigger and the evidence. A freeze is a reversible "
                "state, not a deletion, and it creates a `risk_events` row that cannot be "
                "silently closed.",
                "FR-ADM-005, FR-ADM-011, NFR-AUD-005, R4",
            ],
            [
                "2.12.3", "Super admin", "SCR-ADM-09",
                "Executes an emergency platform-wide freeze.",
                "All money movement halts platform-wide with the reason recorded. This is a "
                "stop-the-bleeding control for an incident, not a routine operating tool, and "
                "its use is itself audited.",
                         "FR-ADM-007, CAN §2, EC-099"
            ],
            [
                "2.12.4", "AJO.ng", "SCR-APP-12 / SCR-APP-10",
                "Notifies the member and the affected organiser.",
                "`account.frozen` goes to the member on push, email and SMS in plain language. "
                "Where an Ajo is frozen, the organiser and the members see a clear statement "
                "that the Ajo is paused and why, without any implication of member fault.",
                "CAN §8, FR-NOTIF-001, BR-014",
            ],
            [
                "2.12.5", "AJO.ng", "SCR-APP-11 / SCR-APP-05",
                "Preserves the member's financial history in full.",
                "The member keeps read access to their contributions, receipts, statements, "
                "positions and completed Ajos. A freeze restricts movement; it does not erase "
                "the record that the money ever existed.",
                "FR-TXN-001, FR-TXN-004, G6, N11",
            ],
            [
                "2.12.6", "AJO.ng", "SCR-APP-10",
                "Handles a payout that falls due while the recipient is frozen.",
                "The payout does not silently vanish. It is HELD with a recorded reason, and "
                "both the recipient and the organiser are told. The HELD state is not a "
                "default and no default clock runs against the member for it.",
                         "BR-018, BR-017, K-14, EC-034",
            ],
            [
                "2.12.7", "Support", "SCR-APP-13 / SCR-ADM-02",
                "Lifts the freeze after verifying the member's identity.",
                "Unfreeze is permitted only after verified identity. The unfreeze is "
                "recorded with actor, role, timestamp, evidence of identity verification and "
                "rationale. The member's own request is not sufficient, which is precisely "
                "what makes the control work against an attacker who has the password.",
                         "FR-S, US-36, BR-023, NFR-AUD-003, EC-079, EC-087",
            ],
            [
                "2.12.8", "Risk officer", "SCR-ADM-05",
                "Records the final decision on the underlying risk event.",
                "The decision records trigger, evidence considered, decision, rationale and "
                "officer identity, and is visible in the Risk screen to every admin role "
                "including `super_admin`.",
                "FR-ADM-006, US-38, NFR-AUD-004",
            ],
        ],
        "widths": [0.49, 0.87, 0.84, 1.41, 1.95, 0.94],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.12.4 Happy path"},
    {
        "t": "p",
        "text": (
            "A member notices a `security.login_new_device` alert from a location they have "
            "never used. They open the Security screen, see three unfamiliar sessions, and "
            "tap *Freeze my account*. Money movement stops immediately: no payment can be "
            "initiated, no payout can be released to them, and the other sessions are revoked. "
            "They receive `account.frozen` on push, email and SMS. They contact support, "
            "prove their identity, and the freeze is lifted with the verification recorded. "
            "Meanwhile the risk officer sees the same pattern as a `risk_events` row with the "
            "device, the location and the timing, and places the account under review. Nothing "
            "was deleted. The member can still read every receipt they have ever received. "
            "When the risk officer closes the review, the decision, the evidence and the "
            "rationale are on the record permanently, visible in the audit log to every admin "
            "role including `super_admin`."
        )
    },
    {"t": "h3", "text": "2.12.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "An attacker with valid credentials asks support to lift the freeze",
                "Unfreeze requires verified identity, not credentials. The request is "
                "refused and the attempted unfreeze is itself recorded as a risk event.",
                "SCR-ADM-02",
                "To the attacker: *We cannot unfreeze the account without verified identity.*",
                         "The legitimate member completes identity verification through a "
         "channel the attacker does not control, EC-079.",
            ],
            [
                "A frozen member's contribution falls due",
                "The obligation continues to exist and the default clock is paused, because a "
                "platform-imposed freeze is not the member's failure. The due date is "
                "adjusted or the clock is suspended, and this is visible to the organiser as "
                "*paused by platform review*, never as a member default.",
                "SCR-APP-08 / SCR-APP-05",
                "To the organiser: *This member is paused by a platform review. It is not a "
                "default and the clock is not running.*",
                         "Unfreeze, then the member pays, BR-014, G5, EC-028.",
            ],
            [
                "A frozen member is the recipient of a due payout",
                "The payout is HELD with a recorded reason, and the member is told. They are "
                "not paid to a different account and no third party receives the money.",
                "SCR-APP-10",
                "*Your payout is on hold until your account review is closed. It is safe and it "
                "is yours.*",
                         "Unfreeze, then the payout releases in full. BR-018, EC-034.",
            ],
            [
                "A whole Ajo is frozen mid-round because of one member",
                "The Ajo goes to FROZEN with a reason recorded, and only the activity "
                "dependent on the risk decision stops. Other members' contributions already "
                "collected are safe and are not clawed back.",
                "SCR-APP-05",
                "*This Ajo is paused while we review an account involved in it. Your money is "
                "intact and your position is unchanged.*",
                         "Risk decision, then UNFREEZE back to ACTIVE, or CANCEL with a recorded "
         "reason. CAN §3, EC-059."
            ],
            [
                "An emergency platform-wide freeze is executed",
                "All money movement halts. Open payment states are not force-resolved; they "
                "remain PENDING and are reconciled on unfreeze, so a mid-flight payment is "
                "never lost or double-counted.",
                "SCR-ADM-09 / SCR-APP-09",
                "*AJO.ng is temporarily paused while we resolve an issue. Anything you have "
                "already paid is safe.*",
                         "Unfreeze, then reconciliation. NFR-AVL-003, EC-099.",
            ],
            [
                "The member disputes that they were ever frozen",
                "The audit log is the answer: it records who froze, when, on what trigger and "
                "with what rationale, and is readable by every admin role and writable by "
                "none.",
                "SCR-ADM-08",
                "*Here is the complete history of every action on this account, including the "
                "freeze and who made it.*",
                         "None needed. NFR-AUD-004, FR-ADM-008, EC-087.",
            ],
            [
                "A frozen account is a duplicate of an existing identity",
                "Freeze persists; both accounts are reviewed together. Merging accounts is not "
                "a capability at MVP: the append-only ledger has no delete, and an identity "
                "merge that removed a record would violate G6.",
                "SCR-ADM-05",
                "*We have found a possible duplicate. Both accounts are under review and "
                "nothing has been deleted.*",
                         "Risk-officer decision, with a documented outcome. BR-030, BR-025, "
         "EC-119.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # ================================================================== 2.13
    {"t": "h2", "text": "2.13 Password reset"},
    {"t": "h3", "text": "2.13.1 Purpose"},
    {
        "t": "p",
        "text": (
            "Password reset is the flow most often used by an attacker and least often "
            "exercised honestly, which makes it the flow where design discipline matters "
            "most. The response to a reset request must be identical whether or not the "
            "account exists, the token must be single-use and short-lived, a successful reset "
            "must invalidate every existing session including the attacker's, and the member "
            "must be told that a reset happened so they can react if they did not request one."
        )
    },
    {"t": "h3", "text": "2.13.2 Swimlane"},
    {
        "t": "code",
        "text": """
MEMBER                    AJO.ng                 EMAIL / SMS        SESSIONS
   |  Forgot password         |                       |                 |
   |------------------------->| POST /auth/password/  |                 |
   |                          |   forgot              |                 |
   |                          |                       |                 |
   |                          |  IF account exists:   |                 |
   |                          |    token (single-use,  |                 |
   |                          |    15 min, hashed at  |                 |
   |                          |    rest)          --->|                 |
   |                          |                       |                 |
   |                          |  IF account does NOT exist:            |
   |                          |    same status, same body,            |
   |                          |    same timing class, no mail          |
   |                          |                       |                 |
   |  "If that account exists,|                       |                 |
   |   we have sent a link."  |                       |                 |
   |                          |                       |                 |
   |  clicks link  ---------->| POST /auth/password/  |                 |
   |                          |   reset               |                 |
   |                          |  new password: min 10 |                 |
   |                          |  chars, breached-password
   |                          |  blocklist enforced   |                 |
   |                          |  token destroyed      |                 |
   |                          |  ALL sessions revoked ---------> revoked
   |                          |  refresh token family |
   |                          |  rotated, never reused|
   |                          |  security alert sent --->|            |
   |<-------------------------| signed out everywhere, sign in again|
""",
    },
    {"t": "h3", "text": "2.13.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.13.1", "User", "SCR-MKT-09 / SCR-APP-17",
                "Requests a password reset.",
                "`POST /auth/password/forgot`. The endpoint is rate limited with exponential "
                "backoff. The response is byte-identical for known and unknown accounts, and "
                "the response time is not materially different.",
                         "NFR-S, NFR-S, US-03, EC-129",
            ],
            [
                "2.13.2", "AJO.ng", "—",
                "Issues a reset token if the account exists.",
                "Token is single-use, short-lived, stored hashed, and the delivery is "
                "idempotent per event instance so a spammed reset does not produce a token "
                "storm. No token is issued and no mail is sent for an unknown account.",
                         "FR-AUTH-006, NFR-S, FR-NOTIF-004, EC-130, EC-132",
            ],
            [
                "2.13.3", "Member", "SCR-APP-17",
                "Clicks the link and sets a new password.",
                "`POST /auth/password/reset`. Minimum 10 characters, breached-password "
                "blocklist enforced, no password reuse beyond policy, and no password or "
                "hash ever logged.",
                "FR-AUTH-007, NFR-SEC-001, NFR-SEC-002",
            ],
            [
                "2.13.4", "AJO.ng", "—",
                "Destroys the token and revokes every session.",
                "All sessions are revoked, including any session an attacker holds. Refresh "
                "tokens are single-use and rotating; reuse of a rotated token revokes the "
                "entire token family.",
                         "FR-S, NFR-S, US-04, EC-107",
            ],
            [
                "2.13.5", "AJO.ng", "SCR-APP-12",
                "Alerts the member that the password changed.",
                "A security notification is sent to the existing verified channels so that a "
                "reset the member did not request is visible to them immediately rather than "
                "discovered later.",
                         "FR-S, NFR-S, EC-069",
            ],
            [
                "2.13.6", "Member", "SCR-MKT-09",
                "Signs in again.",
                "The new password works. A failed attempt after a reset triggers the "
                "backoff ladder, because a reset is a known account-takeover moment and is "
                "the moment to be strict.",
                         "NFR-S",
            ],
        ],
        "widths": [0.49, 0.78, 0.97, 1.39, 1.95, 0.92],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.13.4 Happy path"},
    {
        "t": "p",
        "text": (
            "A member cannot remember their password. They tap *Forgot password*, enter "
            "their email, and are told, whether or not the account exists, that if it does, a "
            "link is on its way. The link opens a single-use, fifteen-minute page. They "
            "choose a twelve-character passphrase, the token is destroyed, and every session "
            "on every device is revoked, including the one on a phone they no longer own. They "
            "receive a security alert telling them the password changed, and they sign in "
            "again. The whole thing took under two minutes and told an attacker nothing, "
            "because a request for a non-existent account is indistinguishable from a request "
            "for a real one."
        )
    },
    {"t": "h3", "text": "2.13.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "An attacker spams reset requests for a list of emails",
                "Rate limiting with exponential backoff per identifier and per source. No "
                "enumeration through the presence or absence of an email.",
                "SCR-APP-17",
                "*Too many requests. Try again in N minutes.*",
                         "Wait out the backoff. NFR-S, EC-129.",
            ],
            [
                "The reset token is older than its validity",
                "Refused. The token is single-use, so a second attempt with an expired token "
                "also fails.",
                "SCR-APP-17",
                "*This reset link has expired. Request a new one.*",
                         "Request a new token, EC-130.",
            ],
            [
                "An attacker who already has a session requests a reset to lock the member "
                "out",
                "The reset succeeds, which is correct: the member is locked out but every "
                "attacker session is revoked too. The member is alerted, so the lockout is "
                "visible rather than silent.",
                "SCR-APP-12",
                "*Your password was changed and all devices were signed out. If this was not "
                "you, freeze your account now.*",
                         "Self-freeze from the notification. Flow 2.12, EC-107.",
            ],
            [
                "The new password appears on a breached-password list",
                "Refused with a specific message naming the problem without echoing the "
                "password.",
                "SCR-APP-17",
                "*That password has appeared in a data breach. Choose something nobody has "
                "used before.*",
                         "Choose another. NFR-S, EC-131.",
            ],
            [
                "The member is already signed in on another device and cannot receive the "
                "reset email",
                "The reset flow does not depend on the existing session. The member uses SMS "
                "recovery, which is offered because SMS is a security channel in the "
                "canonical catalogue even though it is reserved for money-critical and "
                "security events.",
                "SCR-APP-17",
                "*We sent a code to the number ending 4321.*",
                         "Enter the code. DEP-05 is an open dependency: the SMS gateway and "
         "short-code registration are not yet selected and cannot be compressed, "
         "EC-132.",
            ],
            [
                "The member has lost both email and phone access",
                "Recovery requires verified identity through support. It is slow by design "
                "and no agent may skip the identity check, because that check is the whole "
                "control.",
                "SCR-APP-13",
                "*To restore access we need to verify who you are. This is deliberately not "
                "a quick process.*",
                         "Support-assisted identity verification. FR-ADM-004, US-37, EC-133.",
            ],
            [
                "A reset is requested on an account that is frozen",
                "The reset proceeds, because a frozen account must never be a locked-out "
                "account. The freeze is unaffected by the credential change.",
                "SCR-APP-17",
                "*Your password is updated. Your account is still frozen for review.*",
                         "Complete the underlying review. Flow 2.12, EC-088.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # ================================================================== 2.14
    {"t": "h2", "text": "2.14 Identity verification failure and resubmission"},
    {"t": "h3", "text": "2.14.1 Purpose"},
    {
        "t": "p",
        "text": (
            "Identity verification is where the product decides whether it can pay a stranger. "
            "A failure must therefore be legible: the member must be told what failed, what "
            "they should do about it, how many attempts they have left, and what the "
            "consequence of not resolving it is. It must not be a dead end, and it must not "
            "be an interrogation. The raw identifier is never stored, only the result, the "
            "timestamp and the provider reference."
        )
    },
    {"t": "h3", "text": "2.14.2 Swimlane"},
    {
        "t": "code",
        "text": """
MEMBER            AJO.ng          VERIFICATION PROVIDER     RISK
   |  Submit BVN    |                  |                     |
   |--------------->| POST            |                     |
   |                | /verification/bvn|                     |
   |                |  raw BVN passed  |                     |
   |                |  straight through|                     |
   |                |  NEVER STORED --->| check               |
   |                |<-----------------| result + ref        |
   |                | verification_checks row                  |
   |                |  outcome, timestamp, provider ref      |
   |                |  (no raw identifier, no raw document)   |
   |                |                   |                     |
   |   +-----------+-----------+-----------+                     |
   |   |                       |           |                     |
   | APPROVED            MISMATCH        NOT FOUND              |
   |   |                       |           |                     |
   |   |            "This name does       "We could not     manual |
   |   |             not match the        find that record   review |
   |   |             records"                  |                     |
   |   |                       |           |                     |
   |   |            member corrects the      member may          |
   |   |            name and resubmits       retry a bounded     |
   |   |            (bounded attempts)       number of times     |
   |   |                       |           |                     |
   |   |                       +-----------+                     |
   |   |                                 |                        |
   |   |                    verification.failed -> push + email   |
   |   |                                 |                        |
   |   |                    risk_events row where the failure     |
   |   |                    pattern suggests abuse, not error     |
   |   v                                                         |
   |  verification.approved -> push + email                         |
   |                                                                 |
   |  CANNOT: create an Ajo, join one, take a payout position, or   |
   |  be paid out.  CAN still: read, ask for help, fix the record.  |
""",
    },
    {"t": "h3", "text": "2.14.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.14.1", "Member", "SCR-APP-19",
                "Submits the identity check.",
                "`POST /verification/identity` and `POST /verification/bvn`. Only the result, "
                "the timestamp and the provider reference are persisted. Raw identifiers and "
                "raw documents are never stored, never logged and never returned.",
                "FR-KYC-001, FR-KYC-002, US-06, R10, NFR-AUD-002",
            ],
            [
                "2.14.2", "Provider", "—",
                "Returns the outcome.",
                "`GET /verification/:id` returns `PENDING`, `APPROVED` or `FAILED` with a "
                "machine-readable failure category. Provider text is never rendered raw.",
                "CAN §6, FR-KYC-003, NFR-SEC-003",
            ],
            [
                "2.14.3", "AJO.ng", "SCR-APP-19",
                "Handles a mismatch or a not-found result.",
                "The screen names the category, states what to do, and shows the attempts "
                "remaining. Nothing is deleted, nothing is penalised silently, and a "
                "verification failure is not a default.",
                "FR-KYC-003, FR-KYC-004, K-21, US-02",
            ],
            [
                "2.14.4", "Member", "SCR-APP-19",
                "Resubmits with corrected details.",
                "Resubmission is bounded, rate limited, and fully recorded including "
                "failures. Each attempt is a new `verification_checks` row with its own "
                "outcome and provider reference.",
                         "FR-KYC-004, NFR-AUD-002, EC-111, EC-135",
            ],
            [
                "2.14.5", "AJO.ng", "SCR-APP-12",
                "Notifies the outcome.",
                "`verification.approved` or `verification.failed` on push and email, "
                "immediately, in both cases.",
                "CAN §8, FR-NOTIF-001",
            ],
            [
                "2.14.6", "AJO.ng", "SCR-APP-19",
                "Explains the consequence of staying unverified.",
                "The screen states exactly which things are blocked: creating an Ajo, joining "
                "an Ajo, taking a payout position, and being paid. It also states what is "
                "not blocked: reading, contacting support, and fixing the record.",
                "US-02, US-03, D-04, US-19",
            ],
            [
                "2.14.7", "Risk officer", "SCR-ADM-06 / SCR-ADM-05",
                "Reviews the failure when the pattern looks adversarial.",
                "Repeated failures, mismatches across accounts, or a duplicate identity raise "
                "a `risk_events` row. The review is human, recorded, and separate from the "
                "member's right to keep trying within the attempt limit.",
                         "FR-ADM-005, FR-KYC-005, EC-135, EC-089",
            ],
        ],
        "widths": [0.49, 0.84, 0.87, 1.39, 1.95, 0.96],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.14.4 Happy path"},
    {
        "t": "p",
        "text": (
                "A member's name does not match the records exactly, because they shortened "
                "their middle name. The screen says so in plain words, tells them what to do, "
                "and shows that they have four attempts left. They correct the name and "
                "resubmit. The check is approved, `verification.approved` arrives, and the "
                "member can now create or join an Ajo. Throughout, the platform held only the "
                "result, the timestamp and the provider reference. The BVN number itself was "
                "passed to the provider and then gone. The member's failed attempt is still on "
                "the record, because a verification history that only shows successes is "
                "worthless to risk."
            )
    },
    {"t": "h3", "text": "2.14.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "The member's name genuinely does not match the records",
                "The member is told the category and the remedy, and may resubmit within the "
                "attempt limit. The failure is not a dead end and is not a silent block.",
                "SCR-APP-19",
                "*The name on the records is different from the name you gave us. Check the "
                "spelling and try again.*",
                         "Resubmit. Support can assist with a documents-based route. FR-KYC-004, "
         "EC-111.",
            ],
            [
                "The verification provider is down or slow",
                "The check is `PENDING`, not failed. The member is not shown an error that "
                "implies their documents are wrong, and no attempt is consumed.",
                "SCR-APP-19",
                "*We are waiting for the verification service. Nothing is wrong with your "
                "details.*",
                         "Automatic retry, then support if it persists, EC-137.",
            ],
            [
                "The member reaches the attempt limit",
                "Further automatic resubmission is blocked and the case moves to human review "
                "with a recorded reason, rather than leaving the member stuck.",
                "SCR-APP-19 / SCR-ADM-06",
                "*You have used all your automatic attempts. Our team will review this "
                "manually and contact you.*",
                         "`support` assists with identity; only `risk_officer` or `super_admin` "
         "can record a final outcome, US-37, EC-135.",
            ],
            [
                "A duplicate account is registered with the same BVN",
                "A `risk_events` row is raised, the second account is prevented from taking a "
                "payout position until review, and no financial record is ever merged or "
                "deleted.",
                "SCR-ADM-05 / SCR-ADM-06",
                "To the officer: *Duplicate identity across two accounts. Freeze the second; "
                "the first is untouched.*",
                         "Risk review. BR-030, BR-025, EC-119, EC-094.",
            ],
            [
                "The member is verified, then a payout arrives for a different name",
                "Release is blocked. The payout destination must be verified and in the "
                "recipient's own name; a mismatch stops the money rather than sending it to "
                "the wrong person.",
                "SCR-APP-10",
                "*We cannot pay that account because it is not in your name. Add an account "
                "in your own name and we will release it immediately.*",
                         "Nominate a verified own-name destination. NFR-S, US-30, EC-128.",
            ],
            [
                "The member disputes a verification failure as a data error at the provider",
                "It becomes a dispute with a category, an evidence thread and a recorded "
                "decision. Support may escalate to the provider; support may not simply "
                "override the result, because the result is the control.",
                "SCR-APP-14 / SCR-ADM-04",
                "*We have escalated this to our verification provider. Here is your case "
                "reference.*",
                         "Dispute resolution with a recorded outcome. FR-DISP-001 to "
         "FR-DISP-005, EC-136.",
            ],
            [
                "D-04 is not yet resolved, so the verification threshold is unknown",
                "The policy is a configuration value with a safe default, not a hard-coded "
                "rule, and the default is stated in the interface so a member is never "
                "blocked by a policy they cannot see.",
                "SCR-APP-19",
                "*Identity verification is required before you can be paid out. It takes about "
                "a minute.*",
                "Resolve D-04, then change the threshold as a versioned, audited setting. "
                "D-04, FR-ADM-010, BR-026.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "callout",
        "kind": "DECISION",
        "title": "Where identity verification is required at launch",
        "text": (
            "CANONICAL.md records D-04 as open: *is BVN/CAC verification mandatory for all "
            "members, or only above a threshold?* This specification adopts the following "
            "launch position, which is a decision and not a finding: a verified email and a "
            "verified phone are required to create or join an Ajo, and BVN-level identity "
            "verification is required **before a member can occupy a payout position and "
            "before their first disbursement**. The rationale is asymmetric risk: the cost of "
            "asking an honest member for a BVN once is a small onboarding friction, while the "
            "cost of paying a pot to a fabricated identity is the entire trust of the product. "
            "**Owner: Risk and Legal, with Engineering. Must be resolved before launch.** The "
            "threshold is implemented as a versioned, audited setting so that changing it "
            "later is a configuration change, not a redeploy."
        )
    },
    {"t": "pagebreak"},

    # ================================================================== 2.15
    {"t": "h2", "text": "2.15 Fraud detection"},
    {"t": "h3", "text": "2.15.1 Purpose"},
    {
        "t": "p",
        "text": (
            "The fraud the product is actually exposed to is not a random attacker; it is a "
            "member who joins with a false identity, takes a position, collects the pot and "
            "disappears, or an organiser who uses the platform to run schemes that are not "
            "what they appear to be. Detection produces signals and evidence, not verdicts. "
            "At launch the platform holds accounts for review and freezes; it does not "
            "silently decline a legitimate member's payment because a rule fired, because a "
            "false positive in a savings product is indistinguishable to the member from the "
            "platform stealing their money."
        )
    },
    {"t": "h3", "text": "2.15.2 Swimlane"},
    {
        "t": "code",
        "text": """
SIGNAL SOURCE      RULES              AJO.ng                RISK OFFICER
   |                 |                   |                        |
   | new account,    |                   |                        |
   | new device,     |                   |                        |
   | new payout      |-- rule set ----->| risk_events row       |
   | destination     |  (versioned,      |  (never auto-closed)  |
   | duplicate BVN   |   auditable)      |                        |
   | velocity of     |                   |                        |
   | contributions   |                   |                        |
   | invitation      |                   |                        |
   | graph shape     |                   |                        |
   | organiser       |                   |                        |
   | concentration   |                   |                        |
   |                   |                   |                        |
   |                   |  UNDER REVIEW -->| reads evidence         |
   |                   |  (pause only the   | decides: dismiss,     |
   |                   |   activity that    | monitor, freeze,      |
   |                   |   depends on it)   | reject override,      |
   |                   |                   | escalate               |
   |                   |                   |                        |
   |                   |                   |  decision recorded:   |
   |                   |                   |  trigger, evidence,   |
   |                   |                   |  decision, rationale, |
   |                   |                   |  officer identity     |
   |                   |                   |                        |
   |  A member is never told they were "scored". They are told one of:
   |  approved, paused for review with a reason, or frozen. Nothing more.
""",
    },
    {"t": "h3", "text": "2.15.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.15.1", "AJO.ng", "—",
                "Collects signals on account creation, device, IP, funding pattern, "
                "invitation graph, organiser concentration and duplicate identity.",
                "Signals are recorded as `risk_events` with the rule that fired and the "
                "evidence considered. A rule set is a versioned, effective-dated, audited "
                "configuration change, exactly like any other platform setting.",
                "FR-ADM-010, FR-ADM-011, CAN §5, D-08",
            ],
            [
                "2.15.2", "AJO.ng", "—",
                "Scores and routes, with a documented rule set.",
                "A score alone never freezes an account at launch. The output of a rule that "
                "fires is a `risk_events` row for a human, and the row cannot be silently "
                "closed.",
                "FR-ADM-005, NFR-AUD-005, R13",
            ],
            [
                "2.15.3", "Risk officer", "SCR-ADM-05",
                "Reviews the event with its evidence.",
                "The officer sees the rule, the evidence, the account's history, the Ajo's "
                "history and the organiser's history. Every privileged action requires "
                "re-authentication and is recorded with before and after values.",
                "FR-ADM-006, NFR-AUD-003, US-38",
            ],
            [
                "2.15.4", "Risk officer", "SCR-ADM-05",
                "Places the account or Ajo under review.",
                "Under review pauses only the activity that depends on the decision. Existing "
                "credits, receipts, positions and completed Ajos stay readable. A payout due "
                "during review is HELD with a recorded reason and the member is told.",
                         "FR-ADM-005, BR-017, BR-018, EC-089, EC-059",
            ],
            [
                "2.15.5", "Risk officer", "SCR-ADM-05",
                "Approves, rejects or overrides, and records limits.",
                "Approve or reject overrides, and manage limits. The risk officer may not "
                "delete records, edit the ledger, or change fee configuration.",
                "CAN §2, FR-ADM-005, BR-025, R4",
            ],
            [
                "2.15.6", "Member", "SCR-APP-19 / SCR-APP-10 / SCR-APP-13",
                "Is told one of three things: approved, paused for review with a reason, or "
                "frozen.",
                "No score, no risk language, no accusation. A paused member is told what to "
                "do and how long to expect. A frozen member is told that support can lift the "
                "freeze after verified identity.",
                         "FR-ADM-005, US-36, EC-089, EC-087",
            ],
            [
                "2.15.7", "Support", "SCR-ADM-02",
                "Communicates the outcome without adjudicating.",
                "Support reads everything and contacts members. Support cannot override a "
                "risk decision, cannot move money, and cannot change a balance.",
                "BR-023, FR-ADM-004, US-37",
            ],
            [
                "2.15.8", "Platform", "SCR-ADM-07",
                "Monitors the pattern across Ajos.",
                "Default rate per Ajo, per organiser and per member is measurable and "
                "triggers review at a configurable threshold. Organiser concentration and "
                "volume limits are monitored, because a commercial organiser running many "
                "Ajos is a real and specific risk.",
                "FR-DEF-009, R12, D-08, FR-ADM-009",
            ],
        ],
        "widths": [0.49, 0.84, 0.89, 1.39, 1.95, 0.94],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.15.4 Happy path"},
    {
        "t": "p",
        "text": (
            "A risk officer reviewing the Risk screen notices that one organiser has issued "
            "forty invitations in an hour, twenty-three of them to numbers that have never "
            "had an account, and that four of those numbers share a device fingerprint. The "
            "rule that fired is recorded on a `risk_events` row with the evidence. The officer "
            "places the Ajo under review, which pauses only the invitations and the next "
            "activation; the contributions already collected stay exactly where they are and "
            "the members keep reading their receipts. The organiser receives a clear message "
            "that the Ajo is paused for review and what to do. Twenty-four hours later the "
            "officer finds a market association using one shared device, closes the event as "
            "*legitimate shared device*, and the decision is recorded with the trigger, the "
            "evidence, the decision, the rationale and their own identity. Nobody was "
            "accused of anything, and the record is complete enough to be reviewed by "
            "somebody else in a year."
        )
    },
    {"t": "h3", "text": "2.15.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "A rule fires on an honest member, for example a shared family phone",
                "The account goes to review, not to automatic freeze. The member is told it is "
                "paused for review and why. A false positive must never be silent and must "
                "never be permanent.",
                "SCR-APP-19 / SCR-APP-10",
                "*We are doing a quick check on this account before the next step. Nothing is "
                "wrong with your money.*",
                         "Officer dismisses the event and the activity resumes, K-21, EC-089.",
            ],
            [
                "A member is paid out to an account that is not theirs",
                "Blocked before release. The payout destination must be verified and in the "
                "recipient's own name; this is the control that stops the most damaging "
                "fraud in a rotating savings scheme.",
                "SCR-APP-10",
                "*We can only pay an account in your own name. Add one and we will release "
                "your money straight away.*",
                         "Nominate a verified own-name account. NFR-S, FR-POUT-004, EC-128.",
            ],
            [
                "A duplicate account is created with the same BVN to take a second position",
                "A `risk_events` row is raised and the second account is prevented from "
                "taking a payout position until reviewed. No record is merged, because "
                "merging would require deleting a financial history.",
                "SCR-ADM-05 / SCR-ADM-06",
                "To the officer: *Duplicate identity. Second account blocked from a position.*",
                         "Risk-officer decision. BR-030, BR-025, G6, EC-119, EC-094.",
            ],
            [
                "An organiser is running a scheme that charges members more than the "
                "disclosed fee",
                "The organiser's disclosed terms are immutable and versioned, so an attempt "
                "to change them is refused and recorded. Off-platform solicitation is outside "
                "the platform's technical control and is handled through the terms, "
                "monitoring and reporting.",
                "SCR-ADM-05 / SCR-ADM-08",
                "To the officer: *Attempt to alter active terms, and solicitation volume "
                "above threshold.*",
                         "Risk review, then freeze of the organiser's Ajo activity if warranted. "
         "BR-005, R12, EC-150.",
            ],
            [
                "The risk team is not staffed, which is the current state of the "
                "dependency",
                "This is the single most dangerous operational gap in the specification, "
                "because an unstaffed risk role is worse than no risk role: events queue, "
                "nobody triages them, and the review state silently becomes a permanent "
                "hold.",
                "SCR-ADM-05",
                "The Risk screen shows the queue depth and the age of the oldest unhandled "
                "event, so the gap is visible rather than assumed away.",
                "Staff the function before launch. DEP-11, R13, gate G-A. This cannot be "
                "closed by software.",
            ],
            [
                "A member is in review when their contribution falls due",
                "The default clock is paused. A platform review is not a member failure and "
                "must not be recorded as one.",
                "SCR-APP-08 / SCR-APP-05",
                "To the organiser: *Paused by platform review. Not a default, clock not "
                "running.*",
                         "Clear the review, then the member pays, BR-014, G5, EC-028.",
            ],
            [
                "Fraud is suspected on a member who has already been paid out",
                "A `risk_events` row and a freeze are raised. There is no clawing back from a "
                "member: money returned to a member is a documented refund, not an "
                "involuntary deduction, and the capability does not exist.",
                "SCR-ADM-05",
                "To the officer: *Post-payout fraud indicator. Account frozen. No clawback "
                "capability exists by design.*",
                         "Freeze, review, and if there is a shortfall the Ajo goes to HELD and "
         "the recovery process runs. BR-032, EC-134.",
            ],
            [
                "A replayed or forged provider webhook attempts to credit a fake payment",
                "Rejected on signature or replay protection before any credit is posted, and "
                "recorded as an anomaly for review.",
                "SCR-ADM-05",
                "No member is affected. The attempt appears in the Risk screen.",
                         "Signature and replay verification. NFR-S, EC-038, EC-040.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # ================================================================== 2.16
    {"t": "h2", "text": "2.16 Admin intervention"},
    {"t": "h3", "text": "2.16.1 Purpose"},
    {
        "t": "p",
        "text": (
            "Administration is where the product's promises are either kept or quietly "
            "broken. The separation of roles in CANONICAL.md is not bureaucracy: `support` "
            "sees everything and changes nothing, `risk_officer` judges and freezes but "
            "cannot move money or edit the ledger, `super_admin` configures the platform and "
            "can halt everything but cannot bypass the append-only ledger or delete "
            "financial history. Every intervention is recorded with actor, role, timestamp, "
            "before and after values, and it is readable by every admin role and writable by "
            "none."
        )
    },
    {"t": "h3", "text": "2.16.2 Swimlane"},
    {
        "t": "code",
        "text": """
INCIDENT          SUPPORT        RISK OFFICER     SUPER ADMIN
   |                 |               |               |
   | organizer has   |  reads all    |  places the   |
   | disappeared     |  records,     |  Ajo under    |
   | for 3 weeks     |  contacts     |  review, or   |
   |                 |  organizer    |  delegates    |
   |                 |  and members  |  FR-AJO-012   |
   |                 |               |               |
   | Ajo stalled,    |  explains the |  agrees the   |
   | round unfunded  |  recovery     |  recovery     |
   |                 |  options to   |  path; payout |
   |                 |  every        |  HELD until   |
   |                 |  member       |  funded       |
   |                 |               |               |
   | member dispute  |  assists and  |  judges only  |
   | escalated       |  proposes;    |  if a risk    |
   |                 |  CANNOT move  |  reason       |
   |                 |  money        |  exists       |
   |                 |               |               |
   | provider outage |  tells the    |               |  emergency
   | or incident     |  members the  |               |  platform-wide
   |                 |  truth        |               |  freeze with
   |                 |               |               |  a reason
   |                 |               |               |  recorded
   |                 |               |               |
   | correction to a financial record, by ANY role including super_admin:
   |                 NO. A reversing entry is the only correction. BR-025.
   |
   | Every intervention above lands in audit_logs with actor, role,
   | timestamp, before value, after value and reason. Append-only:
   | readable by every admin role, writable by none. NFR-AUD-004.
""",
    },
    {"t": "h3", "text": "2.16.3 Step detail"},
    {
        "t": "table",
        "head": ["Step", "Actor", "Screen", "Action", "System response", "Rule ref"],
        "rows": [
            [
                "2.16.1", "Support", "SCR-ADM-02",
                "Investigates: organiser unavailable, member unreachable, Ajo stalled, "
                "question about a receipt.",
                "Support searches and reads users, Ajos, contributions, payments, payouts, "
                "disputes and audit logs. Every mutation control is absent from the interface "
                "and every mutation endpoint rejects the role with a recorded attempt.",
                "FR-ADM-004, US-37, BR-023, FR-ADM-001",
            ],
            [
                "2.16.2", "Support", "SCR-APP-13",
                "Contacts the parties and explains the options.",
                "Support may assist and propose. It may not initiate or moderate a payout, "
                "change a balance, or override a risk decision. The member-visible outcome is "
                "always an explanation, never a number that has been moved.",
                "CAN §2, FR-ADM-012, BR-023",
            ],
            [
                "2.16.3", "Risk officer", "SCR-ADM-05",
                "Places an account or Ajo under review, freezes, approves or rejects "
                "overrides, manages limits.",
                "Every risk decision records trigger, evidence, decision, rationale and "
                "officer identity, and is visible in the Risk screen. An exception from "
                "reconciliation creates a `risk_events` row that cannot be silently closed.",
                "FR-ADM-005, FR-ADM-006, FR-ADM-011, NFR-AUD-003, NFR-AUD-005",
            ],
            [
                "2.16.4", "Risk officer", "SCR-ADM-03",
                "Handles the organiser-disappears case.",
                "The Ajo is placed under review, the members are told the truth in plain "
                "language, the organiser delegation path is offered, and the round's funding "
                "position is stated exactly. The Ajo is never allowed to fail silently, "
                "because silent failure is the failure mode with no complaints and no "
                "returns.",
                         "FR-AJO-012, N12, NFR-AVL-003, EC-085",
            ],
            [
                "2.16.5", "Risk officer", "SCR-ADM-03",
                "Handles a stalled or unfundable round.",
                "The payout is HELD with the shortfall stated. The recovery process runs. No "
                "reduced payout, no corporate funds, and no other member is charged extra.",
                "BR-018, BR-015, BR-017, G4, K-14",
            ],
            [
                "2.16.6", "Super admin", "SCR-ADM-09",
                "Configures platform settings and executes an emergency freeze.",
                "Settings changes, including fee configuration, limits and thresholds, are "
                "versioned, effective-dated and audited, and never alter historical ledger "
                "entries. An emergency freeze halts all money movement with the reason "
                "recorded.",
                "FR-ADM-007, FR-ADM-010, BR-026, C-01",
            ],
            [
                "2.16.7", "Super admin or risk officer", "SCR-ADM-08",
                "Corrects a financial record.",
                "**No role, including `super_admin`, may edit or delete a ledger entry.** The "
                "only correction is a reversing entry, posted through the same balanced, "
                "audited path as any other transaction. This is the single hardest "
                "constraint in the product and it is enforced at the data layer, not in the "
                "user interface.",
                "BR-025, BR-013, G6, C-05, FR-ADM-002",
            ],
            [
                "2.16.8", "All admin roles", "SCR-ADM-08",
                "Reads the audit log.",
                "Filterable by actor, role, entity, action and date range, and read-only to "
                "every role including `super_admin`. There is no write path, by construction.",
                "FR-ADM-008, NFR-AUD-004, FR-ADM-003",
            ],
            [
                "2.16.9", "Platform", "SCR-ADM-07",
                "Reports on the intervention itself.",
                "Admin reporting covers deposits, volume, fee revenue, active Ajos, defaults, "
                "disputes, frozen accounts and reconciliation exceptions, so the health of the "
                "operation is measurable rather than anecdotal.",
                "FR-ADM-009, K-01 to K-21, FR-PAY-009",
            ],
        ],
        "widths": [0.49, 0.92, 0.84, 1.39, 1.95, 0.91],
        "size": 7.3,
    },
    {"t": "h3", "text": "2.16.4 Happy path"},
    {
        "t": "p",
        "text": (
            "An organiser is hospitalised and unreachable for three weeks. A member contacts "
            "support. The agent, whose role can read everything and change nothing, sees the "
            "Ajo, its round, its funding progress, its members' contribution states and the "
            "full audit history, and calls the members to tell them what is true: the Ajo is "
            "running, the contributions are recorded, the round is short by NGN 1,000.00, and "
            "nothing has been lost. The risk officer places the Ajo under review with a "
            "recorded reason, and the organiser delegation path is offered to a verified member "
            "who is willing to take it. The missing contribution arrives. The round funds, "
            "the payout is released in full, and the Ajo completes three weeks late instead of "
            "dying quietly. Every action taken along the way is in the audit log with an actor, "
            "a role, a timestamp and a reason, and the one thing nobody did was edit a "
            "financial record."
        )
    },
    {"t": "h3", "text": "2.16.5 Alternates and failure branches"},
    {
        "t": "table",
        "head": ["Condition", "Branch", "Screen", "Message", "Recovery"],
        "rows": [
            [
                "A support agent is asked to release a payout for a member",
                "Refused by role, and the attempt is recorded in the audit log as an "
                "authorisation failure.",
                "SCR-ADM-04",
                "*Your role cannot initiate or moderate a payout. I can escalate this to the "
                "risk team.*",
                         "Escalation. BR-023, FR-ADM-012, EC-079.",
            ],
            [
                "A super admin is asked to fix a wrong ledger entry by editing it",
                "Refused at the data layer, not in the interface. The only path is a reversing "
                "entry, which is visible as a separate, balanced, attributed transaction.",
                "SCR-ADM-08",
                "*Ledger entries cannot be edited or deleted by any role. I can post a "
                "reversing entry, which will show as its own transaction.*",
                         "Reversing entry. BR-025, C-05, G6, EC-081.",
            ],
            [
                "The organiser is permanently unreachable",
                "The Ajo does not silently stall. It goes under review, members are told, "
                "delegation is offered, and if the round cannot be funded the payout is HELD "
                "and recovery runs. The Ajo is eventually cancelled with a recorded reason, "
                "not abandoned.",
                "SCR-APP-05 / SCR-ADM-03",
                "*Your organiser is unreachable. Your money is recorded and safe. Here is what "
                "happens next.*",
                         "Delegation, then formal cancellation. FR-AJO-012, G1, EC-085.",
            ],
            [
                "A risk officer is asked to change the fee to resolve a margin problem",
                "Refused. The fee is locked at 2%, may not be raised silently, and any change "
                "is a versioned, effective-dated, audited change disclosed to every existing "
                "member in advance and never applied retrospectively.",
                "SCR-ADM-09",
                "*The 2% fee cannot be changed silently or retrospectively. If it ever changes, "
                "every member is told before it applies.*",
                         "Founders and Legal. BR-026, C-01, R3, D-03, D-06, EC-143.",
            ],
            [
                "Support and risk are unstaffed, which is the current dependency state",
                "The system still enforces every rule, so nothing becomes unsafe, but the "
                "queues grow and cases do not resolve. This is an operational failure, not a "
                "technical one, and it is one of the launch gates.",
                "SCR-ADM-05 / SCR-ADM-04",
                "The admin overview shows queue depth and the age of the oldest unhandled "
                "case, so the gap is visible to leadership rather than discovered later.",
                "Staff both functions before launch. DEP-11, DEP-12, R13, gate G-A, section "
                "19 runbook.",
            ],
            [
                "A member asks an admin to delete their account",
                "Not available for any role, and not something the member should be able to "
                "obtain. The financial record is retained; a personal-data export is a "
                "different thing and is handled under the data-protection process.",
                "SCR-ADM-02",
                "*We cannot delete financial records, and that is deliberate. We can give you "
                "everything we hold about you.*",
                         "Personal-data export, subject to legal review of retention and lawful "
         "basis. BR-025, R10, C-05, EC-118.",
            ],
            [
                "A platform-wide incident requires all money movement to stop",
                "`super_admin` executes an emergency freeze. In-flight payments are not "
                "force-resolved; they stay PENDING and are reconciled on unfreeze, so nothing "
                "is lost and nothing is counted twice.",
                "SCR-ADM-09",
                "*AJO.ng is temporarily paused while we resolve an issue. Anything already "
                "paid is safe and will be confirmed.*",
                         "Unfreeze, then reconciliation. FR-ADM-007, NFR-AVL-003, EC-099, "
         "EC-101.",
            ],
        ],
        "widths": [1.21, 1.49, 0.72, 1.35, 1.73],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # ================================================================== 2.17
    {"t": "h2", "text": "2.17 Flow-to-requirement traceability matrix"},
    {"t": "h3", "text": "2.17.1 How to read this matrix"},
    {
        "t": "p",
        "text": (
            "Each row maps one flow to the functional requirements it discharges, the "
            "screens it touches and the API endpoints it calls. Requirement IDs are the "
            "register in section 1.17; user-story IDs are section 1.20; business-rule IDs "
            "are section 1.21; edge-case IDs are section 19. Any requirement that appears in "
            "no row of this matrix is a requirement with no specified user flow, and must be "
            "treated as a specification gap. Any flow row with no requirement would be a "
            "feature nobody asked for, and must be justified deliberately."
        )
    },
    {
        "t": "p",
        "text": (
            "Endpoints are given as paths under `/api/v1` exactly as they appear in section 6 "
            "of CANONICAL.md. Where this section depends on a reading of an endpoint that is "
            "not explicit in the canonical surface, the row names the interpretation adopted "
            "in 2.0.2 and the callout there. Two endpoints referenced in this section are "
            "proposed additions rather than canonical ones, and are marked as such: "
            "`POST /contributions/:id/refund` and `POST /ajos/:id/members/:memberId/replace`."
        )
    },
    {
        "t": "table",
        "head": ["Flow", "Requirement IDs", "Screen IDs", "API endpoints"],
        "rows": [
            [
                "**2.1** New user",
                "FR-AUTH-001 to FR-AUTH-005, FR-AUTH-011, FR-AUTH-012, FR-PROF-001 to "
                "FR-PROF-003, FR-KYC-001 to FR-KYC-003, FR-NOTIF-001, FR-TXN-005, "
                "FR-TXN-006; US-01, US-02, US-03; BR-030, BR-031; NFR-SEC-002, NFR-SEC-003, "
                "NFR-SEC-004, NFR-PERF-002, NFR-LOC-001",
                "SCR-MKT-01, SCR-MKT-02, SCR-MKT-03, SCR-MKT-05, SCR-MKT-10, SCR-APP-01, "
                "SCR-APP-15, SCR-APP-19",
                "`POST /auth/register`, `POST /auth/otp/request`, `POST /auth/otp/verify`, "
                "`GET /auth/verify-email`, `POST /auth/login`, `PATCH /profile`, "
                "`POST /profile/avatar`, `POST /verification/identity`, "
                "`POST /verification/bvn`, `GET /verification/:id`, `GET /ajos`, "
                "`GET /contributions`, `GET /payouts`, `GET /notifications`",
            ],
            [
                "**2.2** Create Ajo",
                "FR-AJO-001 to FR-AJO-011, FR-AJO-015, FR-INV-001, FR-INV-002, FR-INV-004, "
                "FR-INV-005, FR-POS-003, FR-POS-004, FR-SCH-001, FR-MEM-002, FR-MEM-004; "
                "US-07 to US-13; BR-001, BR-002, BR-004, BR-005, BR-006, BR-008, BR-009, "
                "BR-010, BR-011, BR-012, BR-026, BR-029; NFR-LOC-002, NFR-LOC-003",
                "SCR-APP-01, SCR-APP-02, SCR-APP-03, SCR-APP-04, SCR-APP-05, SCR-APP-06, "
                "SCR-APP-12",
                "`POST /ajos`, `PATCH /ajos/:id`, `POST /ajos/:id/positions/claim`, "
                "`POST /ajos/:id/positions/reorder`, `POST /invitations`, `GET /invitations`, "
                "`POST /invitations/resend`, `POST /ajos/:id/activate` (per 2.0.2: this is "
                "`OPEN_ENROLLMENT`), `GET /ajos/:id/positions`, `GET /ajos/:id/members`, "
                "`GET /ajos/:id/summary`",
            ],
            [
                "**2.3** Join Ajo",
                "FR-JOIN-001 to FR-JOIN-006, FR-INV-003, FR-INV-006, FR-POS-003, FR-POS-005, "
                "FR-MEM-001, FR-CON-001; US-14 to US-19; BR-004, BR-006, BR-011, BR-030; "
                "NFR-SEC-008, NFR-PERF-004, NFR-ACC-005, G3, G7",
                "SCR-APP-04, SCR-APP-01, SCR-MKT-09, SCR-MKT-10, SCR-APP-19, SCR-APP-11",
                "`GET /invitations/:token`, `POST /auth/login`, `POST /auth/register`, "
                "`POST /invitations/:token/accept`, `POST /invitations/:token/decline`, "
                "`GET /ajos/:id`, `GET /ajos/:id/positions`, `GET /ajos/:id/schedule`, "
                "`GET /contributions`, `GET /payouts`",
            ],
            [
                "**2.4** Contribution",
                "FR-PAY-001 to FR-PAY-009, FR-CON-001 to FR-CON-007, FR-NOTIF-001, "
                "FR-NOTIF-002, FR-TXN-001; US-20 to US-25; BR-010, BR-013, BR-021, BR-022, "
                "BR-024, BR-031; NFR-SEC-007, NFR-SEC-009, NFR-PERF-003, NFR-AVL-003, "
                "NFR-LOC-002, NFR-LOC-004, NFR-AUD-006, NFR-ACC-003",
                "SCR-APP-01, SCR-APP-08, SCR-APP-09, SCR-APP-12, SCR-APP-11",
                "`GET /contributions`, `GET /contributions/:id`, "
                "`POST /contributions/:id/pay`, `POST /payments`, `POST /payments/:id/verify`, "
                "`GET /payments/:id`, `GET /payments/:id/receipt`, `POST /webhooks/payments`",
            ],
            [
                "**2.5** Payout",
                "FR-POUT-001 to FR-POUT-008, FR-POS-001, FR-POS-002, FR-TXN-003, "
                "FR-NOTIF-001; US-26 to US-30; BR-008, BR-012, BR-013, BR-017, BR-018, "
                "BR-020, BR-021; NFR-SEC-010, NFR-AUD-006; G4",
                "SCR-APP-10, SCR-APP-12, SCR-APP-11, SCR-APP-05",
                "`GET /payouts`, `GET /payouts/:id`, `GET /ajos/:id/payouts`, "
                "`POST /payouts/:id/release` (organizer request only), "
                "`GET /statements`, `POST /webhooks/payments`",
            ],
            [
                "**2.6** Default",
                "FR-DEF-001 to FR-DEF-009, FR-NOTIF-002, FR-NOTIF-004, FR-NOTIF-007, "
                "FR-MEM-004, FR-ADM-005, FR-ADM-006, FR-DISP-001; US-31 to US-34; BR-014, "
                "BR-015, BR-016; NFR-LOC-003; G5, C-10",
                "SCR-APP-08, SCR-APP-12, SCR-APP-13, SCR-APP-05, SCR-ADM-05",
                "`GET /contributions`, `GET /contributions/:id`, "
                "`POST /contributions/:id/retry`, `GET /ajos/:id/members`, "
                "`POST /ajos/:id/members/:memberId/replace` (proposed, 2.0.2), "
                "`POST /admin/risk/:id/decision`, `GET /admin/risk`",
            ],
            [
                "**2.7** Failed payment",
                "FR-PAY-004, FR-PAY-006, FR-PAY-008, FR-DEF-003, FR-NOTIF-001, FR-ADM-005; "
                "BR-024, BR-021, BR-025; NFR-SEC-003, NFR-ACC-003, K-17",
                "SCR-APP-08, SCR-APP-09, SCR-APP-11, SCR-ADM-05",
                "`POST /payments`, `POST /payments/:id/verify`, `GET /payments/:id`, "
                "`POST /contributions/:id/retry`, `POST /webhooks/payments`",
            ],
            [
                "**2.8** Cancelled payment",
                "FR-PAY-004, FR-PAY-006, FR-CON-002, FR-DEF-003; BR-024, BR-005, BR-016; "
                "NFR-PERF-003, NFR-PERF-004, NFR-AVL-003",
                "SCR-APP-08, SCR-APP-09, SCR-APP-11",
                "`POST /payments`, `GET /payments/:id`, `POST /payments/:id/verify`, "
                "`POST /contributions/:id/retry`, `POST /webhooks/payments`",
            ],
            [
                "**2.9** Refund",
                "FR-PAY-007, FR-TXN-001, FR-TXN-004, FR-ADM-006, FR-ADM-011, FR-AJO-007, "
                "FR-AJO-008; BR-001, BR-013, BR-023, BR-024, BR-025, BR-032; NFR-AUD-003, "
                "NFR-AUD-004, NFR-AUD-006; D-05, D-07",
                "SCR-APP-05, SCR-APP-10, SCR-APP-11, SCR-APP-13, SCR-ADM-04, SCR-ADM-05",
                "`POST /contributions/:id/refund` (**proposed**), `GET /payments/:id`, "
                "`GET /payments/:id/receipt`, `GET /transactions`, "
                "`POST /admin/risk/:id/decision`",
            ],
            [
                "**2.10** Leaving an Ajo",
                "FR-MEM-003, FR-MEM-006, FR-MEM-007, FR-MEM-008, FR-JOIN-006, FR-DEF-008, "
                "FR-AJO-011, FR-POUT-005; US-35; BR-002, BR-003, BR-004, BR-005, BR-007, "
                "BR-008, BR-015, BR-018, BR-032; C-06, G4",
                "SCR-APP-04, SCR-APP-05, SCR-APP-06, SCR-APP-08, SCR-APP-10, SCR-APP-11",
                "`POST /invitations/:token/decline`, `DELETE /ajos/:id/members/:memberId` "
                "(pre-activation only), `POST /ajos/:id/members/:memberId/replace` "
                "(**proposed**), `GET /ajos/:id/members`, `PATCH /ajos/:id/members/:memberId`",
            ],
            [
                "**2.11** Dispute",
                "FR-DISP-001 to FR-DISP-007, FR-ADM-004, FR-ADM-006, FR-NOTIF-001; US-30, "
                "US-31, US-37; BR-014, BR-018, BR-023; NFR-SEC-006, NFR-AUD-001, NFR-AUD-003, "
                "NFR-AUD-004; N8, P5, K-13",
                "SCR-APP-08, SCR-APP-11, SCR-APP-14, SCR-APP-13, SCR-ADM-04, SCR-ADM-05",
                "`POST /disputes`, `GET /disputes`, `GET /disputes/:id`, "
                "`POST /disputes/:id/evidence`, `POST /disputes/:id/messages`",
            ],
            [
                "**2.12** Suspension",
                "FR-SEC-001 to FR-SEC-009, FR-ADM-005, FR-ADM-006, FR-ADM-007, FR-TXN-001, "
                "FR-TXN-004, FR-NOTIF-001; US-04, US-05, US-35, US-36, US-38; BR-014, "
                "BR-017, BR-018, BR-025, BR-030; NFR-SEC-005, NFR-AUD-003, NFR-AUD-004, "
                "G6",
                "SCR-APP-12, SCR-APP-13, SCR-APP-17, SCR-APP-10, SCR-ADM-02, SCR-ADM-05, "
                "SCR-ADM-08",
                "`POST /admin/users/:id/freeze`, `POST /admin/risk/:id/decision`, "
                "`GET /admin/users`, `GET /admin/audit-logs`, `GET /auth/sessions`, "
                "`DELETE /auth/sessions/:id`",
            ],
            [
                "**2.13** Password reset",
                "FR-AUTH-006 to FR-AUTH-010, FR-SEC-001 to FR-SEC-005, FR-NOTIF-001, "
                "FR-ADM-004; US-03, US-04, US-05, US-13; BR-030, BR-023; NFR-SEC-001, "
                "NFR-SEC-002, NFR-SEC-003, NFR-SEC-004, NFR-SEC-005, NFR-SEC-008",
                "SCR-MKT-09, SCR-APP-17, SCR-APP-13, SCR-APP-12",
                "`POST /auth/password/forgot`, `POST /auth/password/reset`, `POST /auth/otp/"
                "request`, `POST /auth/otp/verify`, `GET /auth/sessions`, `DELETE /auth/"
                "sessions/:id`",
            ],
            [
                "**2.14** Verification failure",
                "FR-KYC-001 to FR-KYC-007, FR-NOTIF-001, FR-ADM-005, FR-ADM-006, "
                "FR-POUT-004, FR-JOIN-005; US-06, US-19; BR-025, BR-030; NFR-AUD-002, "
                "NFR-SEC-010, NFR-SEC-003; D-04, R10, K-21",
                "SCR-APP-19, SCR-APP-10, SCR-APP-14, SCR-ADM-05, SCR-ADM-06",
                "`POST /verification/identity`, `POST /verification/bvn`, "
                "`GET /verification/:id`, `GET /admin/verification` (**proposed**; the "
                "canonical surface exposes `GET /admin/users` and `GET /admin/risk`, and the "
                "Verification screen is in the canonical inventory without a listed path)",
            ],
            [
                "**2.15** Fraud detection",
                "FR-ADM-005, FR-ADM-006, FR-ADM-010, FR-ADM-011, FR-KYC-001, FR-KYC-005, "
                "FR-SEC-001 to FR-SEC-007, FR-POUT-004, FR-DEF-009, FR-MEM-002; US-36, "
                "US-37, US-38; BR-025, BR-030; NFR-AUD-003, NFR-AUD-005, NFR-SEC-009, "
                "NFR-SEC-010; D-08, R4, R12, R13, DEP-11",
                "SCR-APP-19, SCR-APP-10, SCR-APP-13, SCR-ADM-05, SCR-ADM-06, SCR-ADM-08",
                "`GET /admin/risk`, `POST /admin/risk/:id/decision`, "
                "`POST /admin/users/:id/freeze`, `GET /admin/audit-logs`, "
                "`GET /admin/reports/*`",
            ],
            [
                "**2.16** Admin intervention",
                "FR-ADM-001 to FR-ADM-012, FR-AJO-012, FR-MEM-007, FR-DEF-009, "
                "FR-PAY-009, FR-DISP-003, FR-DISP-005; US-12, US-13, US-37, US-38; BR-008, "
                "BR-013, BR-015, BR-017, BR-018, BR-021, BR-023, BR-025, BR-026; NFR-AUD-001, "
                "NFR-AUD-003, NFR-AUD-004, NFR-AUD-005, NFR-AUD-006, NFR-AVL-003; G1, G4, "
                "G6, D-03, D-06, DEP-11, DEP-12, DEP-15",
                "SCR-ADM-01, SCR-ADM-02, SCR-ADM-03, SCR-ADM-04, SCR-ADM-05, SCR-ADM-07, "
                "SCR-ADM-08, SCR-ADM-09, SCR-APP-05, SCR-APP-13",
                "`GET /admin/overview`, `GET /admin/users`, `GET /admin/ajos`, "
                "`GET /admin/disputes`, `GET /admin/risk`, `POST /admin/risk/:id/decision`, "
                "`POST /admin/users/:id/freeze`, `GET /admin/audit-logs`, "
                "`GET /admin/reports/*`",
            ],
        ],
        "widths": [0.84, 2.08, 1.25, 2.33],
        "size": 7.0,
    },
    {"t": "h3", "text": "2.17.2 Coverage gaps and open items this matrix exposes"},
    {
        "t": "p",
        "text": (
            "A traceability matrix earns its place by admitting what it cannot cover. The "
            "following are the gaps it exposes, stated plainly rather than smoothed over."
        )
    },
    {
        "t": "table",
        "head": ["Gap", "Why it exists", "What is required"],
        "rows": [
            [
                "**2.9** Refund has no canonical endpoint",
                "Section 6 of CANONICAL.md lists no refund route, and BR-032 forbids refunds "
                "outside the documented cancellation and reversal paths. The refund flow "
                "therefore depends on a proposed endpoint that does not yet exist in the "
                "canonical surface.",
                "Add `POST /contributions/:id/refund` to the canonical API surface with an "
                "`Idempotency-Key` requirement, or specify refunds as an operations-only "
                "action with no member-facing trigger. **Owner: Engineering and Founders. "
                "Before build.**",
            ],
            [
                "**2.10** Replacement has no canonical endpoint",
                "`POST /ajos/:id/members/:memberId/replace` appears in the canonical member "
                "surface, but the replacement and transfer flow is specified here as a "
                "multi-party, risk-reviewed process, and the canonical path suggests a single "
                "call.",
                "Specify replacement as a request-and-decision resource with explicit states, "
                "or document the single endpoint as the request-creation call only, with the "
                "decision recorded elsewhere. **Owner: Engineering and Risk. Before build.**",
            ],
            [
                "**2.14** The Verification admin screen has no canonical endpoint",
                "The Verification screen is in the canonical screen inventory but no "
                "`/admin/verification` path is listed in section 6, while the screen needs a "
                "data source for `verification_checks`.",
                "Add a read path for `verification_checks` to the admin surface. **Owner: "
                "Engineering. Before build.**",
            ],
            [
                "**2.12** and **2.16** depend on human roles that are not staffed",
                "DEP-11 (risk) and DEP-12 (support) are both recorded as not established. "
                "Every freeze, review, dispute resolution and unfreeze in this section "
                "requires a human being to execute it.",
                "Staff both functions before launch, or the flows exist on paper only. "
                "**Owner: Operations. Gates launch.** R13, gate G-A.",
            ],
            [
                "**2.4**, **2.5**, **2.7**, **2.8** depend on unconfirmed provider behaviour",
                "Collection percentage, payout flat fee, settlement timing, reversal SLA and "
                "the exact cancellation semantics are all unknown. D-02, D-03 and D-07 are "
                "open and no written provider pricing has been obtained.",
                "Obtain written pricing and SLA from ProvidusUnity before the fee is "
                "publicised and before these flows are built to a fixed timeline. "
                "**Owner: Founders. Gates launch.** A-05, DEP-01, DEP-02, DEP-03.",
            ],
            [
                "**2.5** and **2.6** depend on the D-04 verification threshold",
                "The set of members who must be BVN-verified before taking a position is not "
                "decided, and the flows encode a launch position rather than a settled one.",
                "Resolve D-04, then implement the threshold as a versioned, audited setting so "
                "a later change is configuration rather than a code change. **Owner: Risk and "
                "Legal. Gates launch.**",
            ],
            [
                "**2.6**, **2.9** and **2.16** depend on the D-05 fee-on-refund policy",
                "Whether the 2% is returned with a refunded contribution is undecided, and "
                "the answer changes what a member is told at three different screens.",
                "Decide D-05 before launch and reflect it in the fee screen, not only in the "
                "refund path. **Owner: Founders and Legal. Gates launch.**",
            ],
        ],
        "widths": [1.68, 2.55, 2.27],
        "size": 7.6,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Closing note on the flows",
        "text": (
            "Sixteen flows, and in every one of them the same three sentences hold. The member "
            "is told the fee as its own number before they commit. The member's money is "
            "either the full base pool or it has not moved. And the record of what happened is "
            "written once, by the system, in a place no role can quietly change. Everything "
            "else in this specification is an implementation of those three sentences. "
            "*Your Ajo. Your Story.*"
        )
    },
]
