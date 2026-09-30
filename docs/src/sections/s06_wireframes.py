"""
Section 6 — Wireframe Specification.

Source of truth: docs/src/CANONICAL.md
Authoring contract: docs/src/AUTHORING.md
Cross-references: section 2 (user flows 2.1 to 2.16), section 3 (sitemap,
screen identifiers SCR-WEB-nn / SCR-MOB-nn / SCR-ADM-nn, route inventory
3.6), section 1 (business rules BR-001 to BR-032, requirements FR-*),
section 7 (high-fidelity UI), section 13 (security), section 16 (payments
and ledger), section 19 (edge cases EC-001 onwards).

Screen identifiers are the ones published in section 3.6.4, so a wireframe, a
flow step, a route and a high-fidelity component all name the same thing.

The 2% platform fee is shown exactly as CANONICAL.md defines it on every
money-moving screen: a member owing NGN 1,000.00 is charged NGN 1,020.00, the
fee is NGN 20.00, and the recipient of a ten-member round receives the base
pool NGN 10,000.00. The tagline is "Your Ajo. Your Story."
"""

BLOCKS = [
    {"t": "h1", "text": '6. Wireframe Specification'},

    {
        "t": "lead",
        "text": "This section specifies every screen AJO.ng will have, at the level of structure rather than finish: which regions a screen contains, what each region is for, in what order they appear, what changes between a 375 px phone and a 1440 px desktop, and which regions are mandatory. It is the contract that lets a designer and an engineer work in parallel without either one inventing a region the other did not know about. A region that is not in a screen's region table does not get built. A screen that is not in this section does not get routed.",
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'What a wireframe is not',
        "text": 'These are not pictures and they are not mocks. They fix containment, order, hierarchy, and the presence or absence of a control. They do not fix type sizes, colours, radii or spacing — that is section 7, and a change there does not invalidate anything here. What they do fix, and what must not be changed without returning to this section, is the **fee disclosure on the money screens**, the **order of the amount relative to the commit action**, and the **presence of the base-pool figure on every payout surface**. Those are compliance requirements, not design choices.',
    },

    {"t": "h2", "text": '6.1 How to read the wireframes'},

    {
        "t": "p",
        "text": "Every diagram in this section uses the same notation. A box is a bounded region of the screen with a name; the name is the region's identifier in the region table that follows the diagram. Regions are numbered from the top of the screen down, in reading order, and the same number means the same region on the mobile and the desktop frame unless the region table says the region was replaced.",
    },

    {"t": "h3", "text": '6.1.1 Notation key'},

    {
        "t": "table",
        "head": ['Glyph', 'Meaning', 'Notes'],
        "rows": [
            ['`+---+`', 'Region boundary', 'Corners `+`, horizontal rules `-`, vertical rules `|`.'],
            ['`+-- (4) X --+`', 'Region boundary carrying its number and name', 'The number keys to the region table below the diagram.'],
            ['`# Heading`', 'Heading text region', 'Rendered per 7.4, not per this section.'],
            ['`[ value ]`', 'Text input, empty or filled', 'Drawn at a fixed width; the real width is 7.5.'],
            ['`[ value v ]`', 'Select or dropdown', 'The trailing `v` is the affordance, not a value.'],
            ['`{ Label }`', 'Button', 'A trailing `*` marks the **primary** action. At most one per screen.'],
            ['`{ Label }o`', 'Button, disabled', 'Non-interactive, and the reason is stated in text, never only by the grey.'],
            ['`< label >`', 'Text link', 'Never a destructive action.'],
            ['`o Name`', 'Identity row', 'Avatar or initials chip plus a display name.'],
            ['`^^^####-----`', 'Meter or progress bar', 'Cyan is filled, Cloud is the track. Always paired with a numeric label.'],
            ['`$$1,020.00`', 'Monetary value', 'Right-aligned in the real layout, never truncated.'],
            ['`@3`', 'Badge count', 'Unread or action count. Capped at `9+`.'],
            ['`! text`', 'Warning strip', 'Gold. Only for a genuine risk to the member.'],
            ['`x text`', 'Error strip', 'Danger. Always paired with what to do next.'],
            ['`+ ok`', 'Success strip', 'Always paired with a reference or a next step.'],
            ['`~`', 'Divider rule', 'Between rows of a group, never between a heading and its content.'],
            ['`...`', 'Collapsed remainder', 'Means *more rows exist and scroll*, not *loading*.'],
            ['`// note`', 'Annotation', 'Not rendered. A note to the designer or engineer.'],
        ],
        "widths": [0.73, 2.15, 3.62],
        "size": 7.2,
    },

    {"t": "h3", "text": '6.1.2 Box conventions'},

    {
        "t": "bullets",
        "items": [
            "**A region box is not a visible border.** The `+` and `-` characters describe a region's extent in the layout, not a stroke on screen. The only regions that render a visible boundary are cards, sheets, the non-dismissable processing screen and the receipt, and those are marked `card` in the region table.",
            "**The first line inside a box is the region's first line in reading order.** Where a region has a heading, the heading is its own line and is marked `#`.",
            '**Blank lines inside a box are spacing, not content.** They correspond to the vertical rhythm in 7.5 and carry no meaning beyond *there is a gap here*.',
            '**A control drawn on two frames is one control**, restyled for the frame. It never means the screen has two of them.',
            '**An ellipsis inside a value is a layout constraint, not a data value.** A display name truncates with an ellipsis and keeps its full text in the accessible label. An amount is never truncated.',
            '**Empty content is drawn as `[ none yet ]`**, never as a blank area. A blank area is an unresolved state; see 7.15.',
        ],
    },

    {"t": "h3", "text": '6.1.3 Priority values used in the region tables'},

    {
        "t": "table",
        "head": ['Priority', 'Meaning', 'Effect if omitted'],
        "rows": [
            ['`P1`', 'Required for the screen to be correct. Removing it breaks a canonical rule, a security control or the fee disclosure.', 'The screen does not ship. Not a judgement call.'],
            ['`P2`', 'Required for the screen to be usable and complete.', 'Ships with a filed gap and a named owner.'],
            ['`P3`', 'Required for the screen to be good. Deferrable to a named iteration.', 'Deferrable, recorded in the 6.35 handoff checklist.'],
        ],
        "widths": [0.42, 4.2, 1.88],
        "size": 7.4,
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '6.2 Frame sizes and how the three frames relate'},

    {
        "t": "p",
        "text": 'Every screen is drawn twice: once at mobile and once at desktop. The tablet frame appears only where the desktop layout has a genuinely intermediate form, that is, where a two-column form or table collapses at 768 px. Diagram width is proportional to real frame width so that relative column widths stay readable: the mobile frame is 38 characters for 375 px, the tablet frame 62 characters for 768 px, and the desktop frame 72 characters for 1440 px.',
    },

    {
        "t": "table",
        "head": ['Frame', 'CSS width', 'Content column', 'Diagram width', 'Where used'],
        "rows": [
            ['Mobile', '375 px', '343 px, 16 px gutters', '38 chars', 'Every screen in this section.'],
            ['Tablet', '768 px', '720 px, 24 px gutters', '62 chars', 'Only where a two-column form or table collapses.'],
            ['Desktop', '1440 px', '1200 px maximum, 24 px gutter', '72 chars', 'Every screen in this section.'],
        ],
        "widths": [0.43, 0.55, 1.78, 0.8, 2.94],
        "size": 7.4,
    },

    {"t": "h3", "text": '6.2.1 Admin console frames'},

    {
        "t": "callout",
        "kind": 'DECISION',
        "title": 'The admin console is not designed below 1024 px',
        "text": "The three admin screens in this section (6.30 to 6.33) are drawn at 768 px and 1440 px, and **no mobile frame is specified for them.** The reason is structural, not stylistic: a risk decision or a dispute decision is made by comparing a member's record against an Ajo's record and a ledger posting, and making that comparison on a 375 px screen is a safety problem rather than a layout problem. The console therefore renders a *device not supported* page below 1024 px, which is a `P1` region on every admin screen. **Owner: Founders. Revisit only if support is staffed from a phone-first region, which is a staffing decision, not a design one.**",
    },

    {
        "t": "table",
        "head": ['Breakpoint', 'Layout', 'Rule'],
        "rows": [
            ['Below 768 px', 'Single column; bottom bar in tier 2, stacked nav in tier 1', 'Baseline.'],
            ['768–1023 px', '72 px icon rail, single content column, reduced table padding', 'The tablet frame.'],
            ['1024–1439 px', '240 px rail, two-column content where shown', 'Desktop begins.'],
            ['1440 px and above', '1200 px content column, centred', 'The desktop frame.'],
        ],
        "widths": [1.15, 4.13, 1.22],
        "size": 7.4,
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '6.3 Home (marketing) — SCR-WEB-01'},

    {
        "t": "p",
        "text": "The page a first-time visitor sees, and the only page in the product that has to win a stranger's trust in about eight seconds. Its job is to explain the Ajo in plain Nigerian English, disclose the 2% fee above the fold in a form that cannot be skimmed past, and hand the visitor one obvious next step. It is also the only page with a real SEO job.",
    },

    {"t": "h3", "text": '6.3.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| AJO.ng           Sign in  [=]            |
+-- (2) HERO ------------------------------+
|      Your Ajo. Your Story.               |
|                                          |
| The rotating savings                     |
| scheme you already                       |
| understand, with the                     |
| admin done properly.                     |
|                                          |
| { Create free account }*                 |
|                                          |
| < See how it works >                     |
+-- (3) FEE CARD --------------------------+
| +------------------------------------+   |
| |  Every NGN 1,000.00 you pay        |   |
| |  carries a NGN 20.00 AJO.ng fee,   |   |
| |  so NGN 1,020.00 leaves your       |   |
| |  account. At your turn you         |   |
| |  receive NGN 10,000.00. The fee    |   |
| |  is never taken out of it.         |   |
| +------------------------------------+   |
+-- (4) HOW IT WORKS ----------------------+
| 1 Gather   2 Save   3 Take your turn     |
+-- (5) SAFETY BAND -----------------------+
|   ! Payout positions lock the day        |
|     the Ajo activates. AJO.ng never      |
|     charges other members for a          |
|     missed payment, and never names      |
|     a member who defaults.               |
+-- (6) CTA STRIP -------------------------+
| { Create free account }*                 |
| { Join with an invite code }             |
+-- (7) FOOTER ----------------------------+
| Fees  Safety  FAQ  About  Contact        |
| Terms  Privacy                           |
| Your Ajo. Your Story.                    |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) TOP NAV -----------------------------------------------------------+
| AJO.ng   How it works  Features  Safety and trust  Fees                  |
|          About  FAQ  Contact        [Sign in]  [Create account]          |
+-- (2) HERO AND FEE TABLE ------------------------------------------------+
| Your Ajo. Your Story.         +------------------------------------+     |
|                               |  What you pay, and what you get    |     |
| The rotating savings scheme   |  --------------------------------  |     |
| you already understand, with  |  NGN 1,000.00  your contribution   |     |
| the admin done properly.      |  NGN    20.00  AJO.ng fee, 2%      |     |
|                               |  NGN 1,020.00  total charged       |     |
| { Create free account }*      |  --------------------------------  |     |
|                               |  NGN 10,000.00  base pool at turn  |     |
| < See how it works >          |  --------------------------------  |     |
|                               |  The fee is charged on top. It is  |     |
| The numbers on the right are  |  never taken out of a              |     |
| the numbers you will see on   |  contribution and it never         |     |
| every receipt you ever get.   |  reduces a payout.                 |     |
|                               +------------------------------------+     |
+-- (3) HOW IT WORKS, THREE ACROSS ----------------------------------------+
| +--------------------------------------------------------------------+   |
| |  1  GATHER             2  SAVE               3  TAKE YOUR TURN     |   |
| |                                                                    |   |
| |  Ten people agree a    Each member pays on   When the round is     |   |
| |  contribution and a    the due date. The     fully collected,      |   |
| |  schedule. Everyone    fee is NGN 20.00 on   whoever it is due to  |   |
| |  sees the same plan.   top of NGN 1,000.00.  is paid the base      |   |
| |                                              pool, NGN 10,000.00.  |   |
| +--------------------------------------------------------------------+   |
+-- (4) SAFETY BAND -------------------------------------------------------+
| +--------------------------------------------------------------------+   |
| |  !  Safety is the product, not a feature we added. Payout          |   |
| |     positions lock the moment the Ajo activates. A member who      |   |
| |     misses a payment is handled privately between them, the        |   |
| |     organiser and AJO.ng risk. No member is ever charged extra,    |   |
| |     and a defaulting member is never named in the Ajo.             |   |
| |                                                                    |   |
| |  < Read how defaults are handled >                                 |   |
| +--------------------------------------------------------------------+   |
+-- (5) CTA AND FOOTER ----------------------------------------------------+
| Ready when your group is.  { Create free account }*                      |
| { Join with an invite code }                                             |
|                                                                          |
| Fees  Safety  FAQ  About  Contact  Terms  Privacy                        |
| Your Ajo. Your Story.                                                    |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.3.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Header', 'Wordmark, sign-in entry, links to the content pages.', 'P1', 'Sign in is a link, not a button. Register is the primary action of the page and lives in the hero.'],
            ['(2) Hero', 'Tagline, one-sentence explanation, the single primary CTA.', 'P1', 'Tagline is **Your Ajo. Your Story.** No other tagline appears anywhere in the product.'],
            ['(3) Fee card', 'The 2% fee quantified with the canonical example, above the fold.', 'P1', '**Contribution, fee and total are three separate lines**, and the card states that the fee never reduces the payout. Same disclosure as 6.17 and 6.19.'],
            ['(4) How it works', 'Three-step summary of the mechanic.', 'P2', 'Links to SCR-WEB-02. Three cards, not seven. The third card says *base pool* and gives the figure.'],
            ['(5) Safety band', 'Position lock, private default handling, no member charged extra.', 'P1', 'Carries the three canonical safety promises from CAN §4. Wording is fixed by section 1 and may not be softened for tone.'],
            ['(6) CTA strip', 'Repeat of the primary action lower on the page.', 'P2', 'Same target as the hero CTA. A second, *different* CTA would compete with the first and is prohibited.'],
            ['(7) Footer', 'Full sitemap, legal routes, tagline.', 'P1', 'Carries `/terms` and `/privacy` on every page of tier 1 (3.2).'],
            ['— Social proof', '**Deliberately absent.**', '—', 'The company is pre-launch with no customers. Testimonial, logo, download-count and user-count regions are prohibited until verifiable numbers exist. Adding them earlier would be a fabricated claim, which is a conduct issue, not a design one.'],
        ],
        "widths": [0.42, 1.28, 0.42, 4.38],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.4 How It Works — SCR-WEB-02'},

    {
        "t": "p",
        "text": 'The long-form explanation that resolves the questions the home page raises. It is written for someone who has run an Ajo in person and is checking whether the digital version is the same thing. That means it leads with the mechanic rather than the technology, and it states what happens when things go wrong before it states what happens when they go right.',
    },

    {"t": "h3", "text": '6.4.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| AJO.ng           Sign in  [=]            |
+-- (2) TITLE -----------------------------+
| # How an Ajo works                       |
| The same scheme, recorded properly.      |
+-- (3) THE SIX STEPS ---------------------+
| 1  You and nine others agree             |
|    NGN 1,000.00 each, every month.       |
|                                          |
| 2  Every position is set and             |
|    locked the day the Ajo starts.        |
|                                          |
| 3  Each round, everyone pays             |
|    by the due date.                      |
|                                          |
| 4  AJO.ng keeps NGN 20.00 as its         |
|    fee, charged on top.                  |
|                                          |
| 5  When the round is fully               |
|    collected, whoever it is due to       |
|    is paid NGN 10,000.00.                |
|                                          |
| 6  Round two begins. Ten rounds,         |
|    one payout each.                      |
+-- (4) WORKED EXAMPLE --------------------+
| +------------------------------------+   |
| |  10 members, NGN 1,000.00 each     |   |
| |  Charged to each member      NGN   |   |
| |  1,020.00                          |   |
| |  of which AJO.ng fee, 2%     NGN   |   |
| |  20.00                             |   |
| |  Contributed to the round    NGN   |   |
| |  1,000.00                          |   |
| |                                    |   |
| |  Base pool to the recipient  NGN   |   |
| |  10,000.00                         |   |
| |                                    |   |
| |  Total across the whole Ajo  NGN   |   |
| |  102,000.00                        |   |
| +------------------------------------+   |
+-- (5) WHEN THINGS GO WRONG --------------+
| ! If someone misses a payment:           |
|   48-hour grace, the organiser is        |
|   told privately, recovery begins.       |
|   You are never charged extra.           |
+-- (6) CTA -------------------------------+
| { Create free account }*                 |
| < Back to the top                        |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) TOP NAV -----------------------------------------------------------+
| AJO.ng   How it works  Features  Safety and trust  Fees                  |
|          About  FAQ  Contact        [Sign in]  [Create account]          |
+-- (2) TITLE AND SIX STEPS -----------------------------------------------+
| How an Ajo works                1  You and nine others agree             |
|                                    NGN 1,000.00 each, every month.       |
| The same scheme, recorded                                                |
| properly.                       2  Every position is set and             |
|                                    locked the day the Ajo starts.        |
| An Ajo is not a new idea. It                                             |
| is a habit people already       3  Each round, everyone pays             |
| have, with the record-keeping      by the due date.                      |
| done by a system instead of by                                           |
| memory.                         4  AJO.ng keeps NGN 20.00 as its         |
|                                    fee, charged on top.                  |
| Everything below is what                                                 |
| AJO.ng does differently. The    5  When the round is fully               |
| scheme itself is yours.            collected, whoever it is due to       |
|                                    is paid NGN 10,000.00.                |
|                                                                          |
|                                 6  Round two begins. Ten rounds,         |
|                                    one payout each.                      |
+-- (3) WORKED EXAMPLE ----------------------------------------------------+
| +------------------------------------------------------------+           |
| |  The whole scheme in one table, with the exact numbers     |           |
| |  you will see on every receipt you ever get.               |           |
| |  --------------------------------------------------------  |           |
| |  Members                                  10               |           |
| |  Contribution per member per round   NGN 1,000.00          |           |
| |  Platform fee, 2%                       NGN    20.00       |           |
| |  TOTAL CHARGED TO EACH MEMBER         NGN  1,020.00        |           |
| |  BASE POOL PAID TO THE RECIPIENT      NGN 10,000.00        |           |
| |  Collected in the round                NGN 10,200.00       |           |
| |  Retained by AJO.ng in the round       NGN    200.00       |           |
| |  Total paid in by one member          NGN 10,200.00        |           |
| |  TOTAL RECEIVED BY THE RECIPIENT      NGN 10,000.00        |           |
| |  AJO.ng fee over the full Ajo          NGN  2,000.00       |           |
| |  Total collected across the Ajo        NGN 102,000.00      |           |
| |  --------------------------------------------------------  |           |
| |  The fee is charged on top. It is never taken out of a     |           |
| |  contribution and it never reduces a payout.               |           |
| +------------------------------------------------------------+           |
+-- (4) WHEN THINGS GO WRONG ----------------------------------------------+
| +--------------------------------------------------------------------+   |
| |  !  If someone misses a payment: a reminder, then a retry where    |   |
| |     the payment partner supports it, then a 48-hour grace, then    |   |
| |     the organiser is told privately, then recovery. You are never  |   |
| |     charged extra to cover the gap, and the defaulting member is   |   |
| |     never named in the Ajo.                                        |   |
| |                                                                    |   |
| |  < Safety and trust >                                              |   |
| +--------------------------------------------------------------------+   |
+-- (5) CTA AND FOOTER ----------------------------------------------------+
| Ready when your group is.  { Create free account }*                      |
|                                                                          |
| Fees  Safety  FAQ  About  Contact  Terms  Privacy                        |
| Your Ajo. Your Story.                                                    |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.4.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Header', 'Same header component as 6.3.', 'P1', 'One header component serves all of tier 1.'],
            ['(2) Title and standfirst', 'What the page is, in one line.', 'P1', 'Standfirst is *the same scheme, recorded properly* — the positioning line, not a feature claim.'],
            ['(3) The six steps', 'The mechanic, in the order a member lives it.', 'P1', 'Step 4 names the fee and step 5 names the base pool. **The two money steps may not be merged or reordered.**'],
            ['(4) Worked example', 'The canonical table, identical to the one on the receipt.', 'P1', 'Same eleven rows, same values, same order as 6.19 and as section 1. This is the single canonical money table for the product and it is transcribed, never retyped per screen.'],
            ['(5) When things go wrong', 'Default handling, stated plainly, before the CTA.', 'P1', 'Mirrors CAN §4 in substance: reminder, retry, 48-hour grace, organiser notified, recovery. Must state that other members are not charged extra.'],
            ['(6) CTA', 'The single next step.', 'P2', 'One primary action only.'],
            ['— Email gate, quiz, calculator', '**Calculator permitted; gate prohibited.**', 'P2', 'A fee calculator that turns NGN 1,000.00 of input into NGN 1,020.00 is good, because it makes the fee concrete. An email capture before the fee is shown is a dark pattern (7.17) and is not permitted.'],
        ],
        "widths": [0.66, 1.26, 0.42, 4.16],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.5 Login — SCR-WEB-09'},

    {
        "t": "p",
        "text": 'The return path. Its only job is to get a known member back to their Dashboard with as few decisions as possible: one identifier, one password, one button. It carries no marketing, no carousel and no pitch, and it never tells a person whether an account exists.',
    },

    {"t": "h3", "text": '6.5.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| AJO.ng                   [=]             |
+-- (2) TITLE AND FORM --------------------+
| # Welcome back                           |
| Sign in to your account.                 |
|                                          |
| Email or phone                           |
| [                          ]             |
|                                          |
| Password                                 |
| [                          ]  (o)        |
|                                          |
| [x] Keep me signed in on this            |
|     device for 30 days                   |
|                                          |
| x  We could not sign you in with         |
|    those details. Check them and         |
|    try again, or reset your              |
|    password.                             |
|                                          |
| { Sign in }*                             |
| < Forgot password? >                     |
|                                          |
| New to AJO.ng?                           |
| < Create an account >                    |
| Terms  Privacy                           |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) SPLIT LAYOUT ------------------------------------------------------+
| +--------------------------+  +----------------------------------------+ |
| |                          |  |  Welcome back                          | |
| |  Your Ajo. Your Story.   |  |  Sign in to your account.              | |
| |                          |  |  ------------------------------------  | |
| |  An Ajo is not a new     |  |                                        | |
| |  idea. Ten people,       |  |  Email or phone                        | |
| |  NGN 1,000.00 each,      |  |  [                              ]      | |
| |  one payout each.        |  |                                        | |
| |                          |  |  Password                              | |
| |  Ten rounds. At your     |  |  [                             ]  (o)  | |
| |  turn, NGN 10,000.00.    |  |                                        | |
| |                          |  |  [x] Keep me signed in on this         | |
| |  NGN 20.00 per round,    |  |      device for 30 days                | |
| |  charged on top. That    |  |                                        | |
| |  is the whole cost.      |  |  ------------------------------------  | |
| |                          |  |                                        | |
| |  AJO.ng                  |  |  x  We could not sign you in with      | |
| +--------------------------+  |    those                               | |
|                               |     details. Try again, or reset your  | |
|                               |     password.                          | |
|                               |                                        | |
|                               |  ------------------------------------  | |
|                               |                                        | |
|                               |  {             Sign in             }*  | |
|                               |                                        | |
|                               |  < Forgot password? >                  | |
|                               |                                        | |
|                               |  ------------------------------------  | |
|                               |  New to AJO.ng?  < Create an account   | |
|                               |    >                                   | |
|                               |  Terms   Privacy                       | |
|                               +----------------------------------------+ |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.5.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Header', 'Wordmark linking home, minimal menu.', 'P1', 'On the desktop frame this is replaced by the brand panel, which carries the same wordmark.'],
            ['(2) Title', '*Welcome back* and one line of orientation.', 'P2', 'No marketing copy above the fold on an authentication screen.'],
            ['(3) Form', 'Identifier, password, show/hide toggle, keep-signed-in.', 'P1', 'One identifier field accepting email **or** phone, not a tab switch. A tab switch doubles the taps and breaks password managers.'],
            ['(4) Error strip', 'One generic message for every failure.', 'P1', 'Never distinguishes an unknown identifier from a wrong password and never confirms that an account exists. Always offers the recovery route.'],
            ['(5) Actions', 'Primary sign-in plus the password-reset link.', 'P1', 'The button is disabled until both fields have content, and the reason is discoverable rather than a silently dead control.'],
            ['(6) Consent links', 'Terms and Privacy inside the form card.', 'P1', 'Present above the fold on desktop, so the consent context is on screen at the moment of sign-in.'],
            ['(7) Brand panel', 'Restates the mechanic and the tagline on the split layout.', 'P3', 'Desktop only. Its fee figure is NGN 20.00 on top, matching `/fees`; a marketing panel that disagreed with the fee page would be a material defect.'],
            ['— Social sign-in', '**Deliberately absent.**', '—', 'CAN §6 defines no OAuth or social-login endpoint. Adding one would create an account verified by a foreign identity provider with a Nigerian phone number attached, which interacts badly with NIN/BVN verification (D-04). **Owner: Founders.** Revisit as an explicit decision if wanted.'],
            ['— Sign-up prompt', '**Deliberately absent.**', '—', "A *Sign up, it's free* panel beside the form interrupts a returning member in order to sell to a stranger. The footer link is sufficient."],
        ],
        "widths": [0.42, 1.03, 0.42, 4.63],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.6 Register — SCR-WEB-10'},

    {
        "t": "p",
        "text": 'The commitment screen of the whole product. It asks for four things — name, email, phone, password — and it is honest about what happens next: the account cannot be used for money until both the email and the phone are verified, and that is stated before the person submits rather than discovered afterwards.',
    },

    {"t": "h3", "text": '6.6.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| AJO.ng                   [=]             |
+-- (2) TITLE AND FORM --------------------+
| # Create your account                    |
| Free, and it takes about a minute.       |
|                                          |
| Full name                                |
| [                          ]             |
|                                          |
| Email address                            |
| [                          ]             |
|                                          |
| Phone number                             |
| [                          ]             |
| Used for the OTP and for money           |
| alerts. No marketing.                    |
|                                          |
| Password                                 |
| [                          ]  (o)        |
| [x] At least 10 characters, and          |
|     not a password you use               |
|     anywhere else                        |
|                                          |
| [x] I accept the Terms and the           |
|     Privacy Policy                       |
| < Read the Terms >  < Privacy >          |
|                                          |
| ! You will verify your email and         |
| ! your phone before you can pay          |
| ! or join an Ajo.                        |
|                                          |
| { Create account }*                      |
| Already registered?                      |
| < Sign in >                              |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) SPLIT LAYOUT ------------------------------------------------------+
| +--------------------------+  +----------------------------------------+ |
| |                          |  |  Create your account                   | |
| |  Your Ajo. Your Story.   |  |  Free, and it takes about a minute.    | |
| |                          |  |  ------------------------------------  | |
| |  Ten people.             |  |                                        | |
| |  NGN 1,000.00 each.      |  |  Full name                             | |
| |  One payout each.        |  |  [                              ]      | |
| |  Ten rounds.             |  |                                        | |
| |                          |  |  Email address                         | |
| |  Why we ask:             |  |  [                              ]      | |
| |                          |  |                                        | |
| |  Name    so your group   |  |  Phone number                          | |
| |          knows you       |  |  [                              ]      | |
| |                          |  |  Used for the OTP and for money        | |
| |  Email  so we can prove  |  |  alerts. No marketing.                 | |
| |          it is yours     |  |                                        | |
| |                          |  |  Password                              | |
| |  Phone  so we can reach  |  |  [                             ]  (o)  | |
| |          you re money    |  |  [x] At least 10 characters, and       | |
| |                          |  |      not used anywhere else            | |
| |  Password keeps it safe  |  |                                        | |
| |                          |  |  [x] I accept the Terms and the        | |
| |  Nothing else, and       |  |      Privacy Policy                    | |
| |  nothing for sale.       |  |                                        | |
| +--------------------------+  |  ! You will verify your email and      | |
|                               |  ! your phone before you can pay       | |
|                               |  ! or join an Ajo.                     | |
|                               |                                        | |
|                               |  ------------------------------------  | |
|                               |                                        | |
|                               |  {           Create account            | |
|                               |    }*                                  | |
|                               |                                        | |
|                               |  Already registered?  < Sign in >      | |
|                               +----------------------------------------+ |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.6.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Header', 'Wordmark linking home.', 'P1', 'Same component as 6.5.'],
            ['(2) Title', '*Create your account* with a time expectation.', 'P2', '*About a minute* is accurate and is the only claim made.'],
            ['(3) Form fields', 'Name, email, phone, password, in that order.', 'P1', 'Phone is not deferred to a later step, because the OTP gates every money action and deferring it produces a second interruption after the member has already invested effort.'],
            ['(4) Field help', 'Why the phone is needed, at the field.', 'P1', '*Used for the OTP and for money alerts. No marketing.* The last sentence is mandatory: a Nigerian member asked for a phone number by a savings product is entitled to know it is not a marketing list.'],
            ['(5) Password rule', 'Length and reuse, as persistent text plus a live state.', 'P1', 'A placeholder that disappears on focus is not an instruction, and neither is a checkbox that silently re-ticks itself.'],
            ['(6) Consent', 'Terms and Privacy acceptance.', 'P1', 'Unchecked by default, required, and the acceptance is timestamped and version-stamped. Must not be bundled with a marketing opt-in.'],
            ['(7) Verification notice', 'What happens before the account can be used.', 'P1', 'Stated before submit. Discovering it after submit is the largest single drop-off in a signup with a verification step.'],
            ['(8) Actions', 'Primary create plus the sign-in link.', 'P1', 'Disabled until the required fields are valid and consent is ticked.'],
            ['(9) Brand panel', "Explains each field's purpose in plain language.", 'P2', 'Desktop only. Resolves the most common objection at this step, which is *what is this phone number for*.'],
            ['— Referral code field', '**Deferred, not rejected.**', 'P3', 'A referral code at signup is a growth feature, not a trust feature. It lives in the More sheet after signup, and `/invite/:token` carries the referral without asking for a code.'],
        ],
        "widths": [0.53, 1.26, 0.42, 4.29],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.7 Email verification — SCR-WEB-11'},

    {
        "t": "p",
        "text": 'A single-purpose confirmation screen reached from an emailed link. It exists because an unverified email is an account nobody can prove is theirs, and because the failure path — expired link, wrong account, mail never arrived — is common enough to need its own design rather than a generic error page.',
    },

    {"t": "h3", "text": '6.7.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| AJO.ng                   [=]             |
+-- (2) CARD, PENDING WITH FAILED STRIP ---+
| +------------------------------------+   |
| |  # Verify your email               |   |
| |                                    |   |
| |  We have sent a link to            |   |
| |                                    |   |
| |    abd***@gmail.com                |   |
| |                                    |   |
| |  It expires in 23 h 41 m. Opening  |   |
| |  the link marks the address        |   |
| |  verified, and nothing else        |   |
| |  happens when you open it.         |   |
| |                                    |   |
| |  x  That link has expired, or it   |   |
| |     has already been used.         |   |
| |                                    |   |
| |  { Resend the email }*             |   |
| |    cooldown shown until it can     |   |
| |    be used                         |   |
| |                                    |   |
| |  < Use a different address >       |   |
| +------------------------------------+   |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) CENTRED CARD ------------------------------------------------------+
|                              +--------------------------------------+    |
| Three states, designed       |  Verify your email address           |    |
| rather than handled.         |  ----------------------------------  |    |
|                              |                                      |    |
| Sent. Verified. Not          |  + ok  Email verified                |    |
| working.                     |                                      |    |
|                              |    abd***@gmail.com                  |    |
| The third is the state most  |                                      |    |
| people will see, because     |  is now verified. You can            |    |
| links expire and mail is     |  pay and join once your              |    |
| unreliable. It gets a real   |  phone is verified too.              |    |
| design, not an error page.   |                                      |    |
|                              |  ----------------------------------  |    |
|                              |                                      |    |
|                              |  Links expire 24 hours after         |    |
|                              |  they are sent, and work             |    |
|                              |  only once.                          |    |
|                              |                                      |    |
|                              |  < Resend the email >                |    |
|                              |  < Use a different address >         |    |
|                              +--------------------------------------+    |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.7.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Header', 'Wordmark linking home.', 'P1', 'Present on the pending and failure states so nobody is stranded.'],
            ['(2) Result strip', 'Success, pending or failed, in the same position.', 'P1', 'One region, three states. Success is shown only after the token has been consumed server-side, never optimistically on load.'],
            ['(3) Masked address', 'Which address was targeted, masked.', 'P1', "Masked to two characters each side. Revealing the full address on a page reachable by an emailed link would defeat the screen's purpose."],
            ['(4) Expiry window', 'Countdown on the pending state.', 'P2', '24-hour window, stated. A bare *link expired* with no window generates support tickets.'],
            ['(5) Resend', 'Resend with a visible cooldown.', 'P1', 'The countdown appears on the button itself. A 60-second cooldown rendered as an unexplained dead control is a `P2` defect at best.'],
            ['(6) Change address', 'Route to replace the address on the account.', 'P1', 'Changing the address revokes outstanding links immediately. This is the most common real failure and it needs a first-class route, not a support ticket.'],
            ['(7) Next step', '*Continue to phone verification* on success.', 'P1', 'Sequential verification is deliberate: a person with two unverified channels is an account nobody can prove. Each screen names the next one.'],
            ['— State templating', '**Fixed.**', 'P1', 'The three states are fixed designs, not one template with a variable message. The copy differs per state and is written per state, because each state needs a different next action.'],
        ],
        "widths": [0.46, 1.25, 0.42, 4.37],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.8 Phone verification (OTP) — SCR-WEB-12'},

    {
        "t": "p",
        "text": 'The second of the two verification steps and the last gate before an account can hold a position in an Ajo. It is also the screen most likely to be attacked, so the countdown and the attempt counter are both visible at all times: a person being rate-limited should be able to see that they are, and why.',
    },

    {"t": "h3", "text": '6.8.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| AJO.ng                   [=]             |
+-- (2) -----------------------------------+
| +------------------------------------+   |
| |  # Verify your phone               |   |
| |                                    |   |
| |  Enter the 6-digit code we sent.   |   |
| |                                    |   |
| |  [ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]    |   |
| |                                    |   |
| |  Sent to +234 80* *** **41         |   |
| |  by SMS at 12:04. Expires in 10    |   |
| |    min.                            |   |
| |                                    |   |
| |  4 attempts left before the code   |   |
| |  must be replaced.                 |   |
| |  Resend available in  0:42         |   |
| |                                    |   |
| |  x  That code is not right.        |   |
| |     3 attempts left.               |   |
| |                                    |   |
| |  {          Verify phone           |   |
| |    }*                              |   |
| |  < Use a different number >        |   |
| +------------------------------------+   |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) CENTRED CARD ------------------------------------------------------+
|                              +--------------------------------------+    |
| The screen most likely       |  Verify your phone number            |    |
| to be attacked.              |  Enter the 6-digit code we sent.     |    |
|                              |  ----------------------------------  |    |
| So every control is on       |                                      |    |
| screen at once:              |  [ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]      |    |
|                              |                                      |    |
|   how many attempts left,    |  Sent to  +234 80* *** **41          |    |
|   when the code expires,     |  by SMS at 12:04. Expires in 10      |    |
|   when a resend is allowed.  |    min.                              |    |
|                              |                                      |    |
| A counter that appears       |  ----------------------------------  |    |
| only on failure reads as     |  4 attempts left before the code     |    |
| an accusation.               |  must be replaced.                   |    |
|                              |  Resend available in  0:42.          |    |
|                              |                                      |    |
|                              |  ----------------------------------  |    |
|                              |  x  That code is not right.  3       |    |
|                              |     attempts left.                   |    |
|                              |                                      |    |
|                              |  ----------------------------------  |    |
|                              |  {          Verify phone             |    |
|                              |    }*                                |    |
|                              |                                      |    |
|                              |  < Use a different number >          |    |
|                              |  < Resend the code (0:42) >          |    |
|                              +--------------------------------------+    |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.8.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Header', 'Wordmark linking home.', 'P1', 'Same component as 6.7.'],
            ['(2) Title and instruction', 'What to do, and that it was sent.', 'P1', 'Says *code*, not *verification*. Nigerian users are comfortable with SMS codes; *verification* is jargon.'],
            ['(3) OTP input', 'Six single-character fields, or one widely tracked field.', 'P1', 'Either form is acceptable. It must accept a pasted six-digit code, set `inputmode="numeric"` and `autocomplete="one-time-code"`, and support backspace across fields.'],
            ['(4) Masked number', 'Which number the code was sent to.', 'P1', 'Masked, because the page is reachable by a link from an email on a possibly shared device.'],
            ['(5) Attempt counter', 'Remaining attempts before invalidation.', 'P1', 'Five attempts, then the code is invalidated and a new one must be requested. **Always visible**, including before the first failure.'],
            ['(6) Resend cooldown', 'Sixty-second countdown on the resend control.', 'P1', 'Rendered on the control, not merely enforced. The cooldown starts on request, not on send, so a failed send does not lock a person out of their own account.'],
            ['(7) Error strip', 'Generic, with the remaining attempt count.', 'P1', 'Never says whether the number exists, whether a code was ever sent, or whether it was already used.'],
            ['(8) Actions', 'Verify, change number, resend.', 'P1', '*Use a different number* changes the phone on the account and invalidates the outstanding code.'],
            ['— Voice or WhatsApp fallback', '**Not specified.**', '—', 'If a voice fallback is offered later it is a `D-` decision covering cost, consent and abuse, and it needs its own screen. Not assumed here, and not implied by the omission.'],
        ],
        "widths": [0.69, 1.4, 0.42, 3.99],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.9 Forgot password — SCR-WEB-13'},

    {
        "t": "p",
        "text": 'A screen with one field and a hard information-security requirement attached: the response must be identical whether or not the account exists. The wireframe therefore shows the neutral response as a designed state rather than as an error branch, because a branch is a thing engineers optimise away.',
    },

    {"t": "h3", "text": '6.9.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| AJO.ng                   [=]             |
+-- (2) TITLE, FORM, NEUTRAL RESPONSE -----+
| +------------------------------------+   |
| |  # Reset your password             |   |
| |                                    |   |
| |  Tell us the email or phone on     |   |
| |  the account and we will send a    |   |
| |  reset link.                       |   |
| |                                    |   |
| |  Email or phone                    |   |
| |  [                          ]      |   |
| |                                    |   |
| |  +------------------------------+  |   |
| |  |  + ok  Check your inbox      |  |   |
| |  |                              |  |   |
| |  |  If that email or phone is   |  |   |
| |  |  on an AJO.ng account, a     |  |   |
| |  |  reset link is on its way.   |  |   |
| |  |  It expires in 30 minutes.   |  |   |
| |  +------------------------------+  |   |
| |                                    |   |
| |  { Send reset link }*              |   |
| |  < Back to sign in                 |   |
| +------------------------------------+   |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) CENTRED CARD ------------------------------------------------------+
| +------------------------------------------------------------+           |
| |  Reset your password                                       |           |
| |  Tell us the email or phone on the account                 |           |
| |  and we will send a reset link.                            |           |
| |  --------------------------------------------------------  |           |
| |                                                            |           |
| |  Email or phone                                            |           |
| |  [                                                         |           |
| |  ]                                                         |           |
| |                                                            |           |
| |  --------------------------------------------------------  |           |
| |                                                            |           |
| |  + ok  Check your inbox                                    |           |
| |                                                            |           |
| |  If that email or phone is on an AJO.ng account, a reset   |           |
| |  link is on its way. The link expires in 30 minutes and    |           |
| |  can be used once.                                         |           |
| |                                                            |           |
| |  It can take a minute to arrive. Check the spam folder     |           |
| |  before asking for another one.                            |           |
| |                                                            |           |
| |  --------------------------------------------------------  |           |
| |                                                            |           |
| |  {                 Send reset link                 }*      |           |
| |                                                            |           |
| |  < Back to sign in >                                       |           |
| +------------------------------------------------------------+           |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.9.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Header', 'Wordmark linking home.', 'P1', 'Same component as 6.7.'],
            ['(2) Title and explanation', 'States what will happen, before the person acts.', 'P1', '*We will send a reset link* is written in the future, so it is accurate for both outcomes.'],
            ['(3) Identifier field', 'Email or phone, one field.', 'P1', 'Same semantics as login, so the password manager that knows the sign-in form also knows this one.'],
            ['(4) Neutral response', 'The single response for both outcomes.', 'P1', '**The wording is fixed and may not be varied by outcome.** *If that email or phone is on an AJO.ng account* is the whole of the disclosure. Any variant such as *we could not find an account with those details* creates an account-existence oracle and is prohibited.'],
            ['(5) Realistic expectations', 'Delivery time and spam folder.', 'P2', "Prevents a second request within seconds, which would otherwise trip the per-identifier send limit and delay the first mail's sender reputation."],
            ['(6) Actions', 'Send, and back to sign in.', 'P1', 'Rate limited per identifier and per source address. If a person hits the limit, the limit and its reset time are shown.'],
            ['— Confirmation of account state', '**Prohibited.**', 'P1', 'The response may not reveal whether the account exists, is frozen, or is under review. A frozen-account hint here would leak risk status to an unauthenticated caller.'],
        ],
        "widths": [0.57, 0.89, 0.42, 4.62],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.10 Dashboard — SCR-MOB-01'},

    {
        "t": "p",
        "text": 'The first authenticated screen, and the answer to one question: what does this person owe, and what is owed to them. Everything else on it is either a summary of a figure that already appears on a detail screen or a route into one. The dashboard is a reading surface, so it is designed to be finished in about four seconds and to be scrolled only if the person wants to.',
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Why the dashboard has no chart',
        "text": "The dashboard carries three numbers and a list. It does not carry a chart, and that is a decision rather than an oversight: a chart of a member's own money tells them something they can already read, while costing them the four-second read. Charts are specified for the admin analytics surfaces in 6.30 and in detail in section 7.10, where the population is large enough for a shape to mean something.",
    },

    {"t": "h3", "text": '6.10.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column in priority order: next due, then the Ajos, then recent activity. The verification banner sits above the fold because nothing below it works until it is dealt with.',
    },

    {
        "t": "code",
        "text": """
+-- (1) TOP BAR ---------------------------+
| AJO.ng                [bell 3] [AV]      |
+-- (2) VERIFICATION BANNER ---------------+
| ! One step left before you can pay       |
| ! or join.  Verify your phone  >         |
+-- (3) NEXT DUE --------------------------+
| +------------------------------------+   |
| |  Next contribution                 |   |
| |                                    |   |
| |  Adaeze's Ajo      round 4 of 10   |   |
| |  Due  Fri 12 Sep                   |   |
| |                                    |   |
| |  Your share   NGN 1,000.00         |   |
| |  AJO.ng fee      NGN 20.00         |   |
| |  You will be charged               |   |
| |                  NGN 1,020.00      |   |
| |                                    |   |
| |  {              Pay now            |   |
| |    }*                              |   |
| +------------------------------------+   |
+-- (4) YOUR AJOS -------------------------+
| Adaeze's Ajo   round 4 of 10             |
| ###########-------  7 of 10              |
|                                          |
| Chima's Ajo    round 9 of 10             |
| #############-----  your turn            |
+-- (5) RECENT ----------------------------+
| 12 Sep  NGN 1,020.00  paid  >            |
| 12 Sep  NGN 20.00 fee  >                 |
| 05 Sep  payout NGN 10,000.00  >          |
+-- (6) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Three summary tiles, then a two-column body. The nearest due contribution is given its own column because it is the only element on the page that asks for a decision.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) SUMMARY TILES -----------------------------------------------------+
| +--------------------------------------------------------------------+   |
| |  OWED TO YOU           YOU OWE               THIS ROUND            |   |
| |  NGN 10,000.00         NGN 1,000.00          NGN 1,000.00          |   |
| |  across 1 Ajo          due Fri 12 Sep        of NGN 1,000.00       |   |
| |  at your turn          charged NGN 1,020.00  7 of 10 paid          |   |
| +--------------------------------------------------------------------+   |
+-- (3) NEXT DUE ----------------------------------------------------------+
| The one thing      +------------------------------------+                |
| on this page that  |  Next contribution                 |                |
| wants a decision.  |                                    |                |
|                    |  Adaeze's Ajo      round 4 of 10   |                |
| Everything else    |  Due  Fri 12 Sep                   |                |
| on the dashboard   |                                    |                |
| is information.    |  Your share   NGN 1,000.00         |                |
|                    |  AJO.ng fee      NGN 20.00         |                |
|                    |  You will be charged               |                |
|                    |                  NGN 1,020.00      |                |
|                    |                                    |                |
|                    |  {              Pay now            |                |
|                    |    }*                              |                |
|                    +------------------------------------+                |
+-- (4) YOUR AJOS ---------------------------------------------------------+
| AJO              ROUND  STATE     PROGRESS  YOUR POSITION                |
| Adaeze's Ajo       4  ACTIVE      7 of 10   9th                          |
| Chima's Ajo        9  ROUNDING     9 of 10   2nd, next                   |
| Fatima's Ajo      -  ENROLLMENT  2 of 10   1st                           |
+-- (5) RIGHT COLUMN ------------------------------------------------------+
| Alerts                                                                   |
| !  Round 5 opens Mon 15 Sep                                              |
| !  Your turn in Chima's Ajo                                              |
| !  is round 10. NGN 10,000.00                                            |
|                                                                          |
| Recent                                                                   |
| 12 Sep  NGN 1,020.00  paid                                               |
| 12 Sep  NGN 20.00  fee                                                   |
| 05 Sep  NGN 10,000.00  payout                                            |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.10.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Top bar', 'Wordmark, notification bell with unread count, avatar menu.', 'P1', 'The bell count is the sum of unread in-app notifications, and never includes SMS, which has no inbox.'],
            ['(2) Verification banner', 'Blocking precondition, shown until both email and phone are verified.', 'P1', '**Prohibited: hiding it behind the pay flow.** A member who reaches the pay screen unverified is bounced back to a screen that is now visible, or they will not know why. Dismissable only once verification is complete.'],
            ['(3) Next contribution', 'The single nearest due contribution, with the fee broken out.', 'P1', 'Contribution, fee and total are three separate lines. This is the first place a member sees the NGN 20.00, so it is stated plainly rather than as *1,000 plus 2%*. See the disclosure rule in CANONICAL.md section 1.'],
            ['(4) Your Ajos', 'Every Ajo the person is a member of, with round counter and progress.', 'P1', 'Progress is a filled bar **plus** a count such as *7 of 10*, never the bar alone, because the bar carries no number a screen reader can use.'],
            ['(5) Recent', "The last three ledger movements on the person's own account.", 'P2', 'Amounts are the amount **charged** on the way out and the amount **received** on the way in. Mixing the two on one line is the single most common way a fintech app misleads, and it is prohibited here.'],
            ['(6) Bottom navigation', 'The five-tab model from section 3.7.2.', 'P1', 'Home, Ajos, Pay, Alerts, More. The Pay tab is a tab, not a floating action button, so the five targets stay in one row at the same height.'],
            ['(7) Summary tiles', 'Owed to you, you owe, this round. Desktop only.', 'P2', 'Each tile states the basis of its number in the third line. A tile reading *NGN 10,000.00* with no label is not built.'],
            ['(8) Ajo table', 'The full membership list with round, state, progress and position.', 'P1', 'Sorts by nearest due date. The *your position* column answers the question people actually open the Ajo list to answer.'],
            ['(9) Right column', 'Alerts and recent activity, on wide screens only.', 'P2', 'Below 1280 px this column moves under the Ajo table rather than being hidden.'],
        ],
        "widths": [0.47, 1.41, 0.42, 4.2],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.11 My Ajos — SCR-MOB-02'},

    {
        "t": "p",
        "text": 'The membership list, and the screen people revisit most often because it is the only place every Ajo they belong to can be seen at once with its state. It is deliberately a list and not a dashboard: a person opening it has a specific Ajo in mind, and a summary of all of them is not what they asked for.',
    },

    {
        "t": "callout",
        "kind": 'DECISION',
        "title": 'Sorting the Ajo list by nearest due date',
        "text": 'The default sort is by nearest due date, then by Ajo name. Sorting by Ajo name is the alternative and it is the wrong default: the reason a person opens this list is almost always a payment they owe, not a group they are in. The trade-off is that the list reorders itself as dates pass, which is disorienting for a person trying to find a specific Ajo by muscle memory. The mitigation is that the state and position columns make each row identifiable on sight, and the sort key is visible in the filter bar so the ordering is never a surprise.',
    },

    {"t": "h3", "text": '6.11.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) SEGMENTED CONTROL -----------------+
| All(3)  Active(2)  Joined(1)  Past(0)    |
+-- (2) STATUS SUMMARY --------------------+
| 1 due this week                          |
| 1 awaiting you                           |
| 0 overdue                                |
+-- (3) AJO CARD --------------------------+
| +------------------------------------+   |
| |  Adaeze's Ajo                      |   |
| |  round 4 of 10   ACTIVE            |   |
| |  ###########-------                |   |
| |  7 of 10 members paid this round   |   |
| |                                    |   |
| |  You are position 9. You owe       |   |
| |  NGN 1,000.00 on Fri 12 Sep and    |   |
| |  will be charged NGN 1,020.00.     |   |
| |                                    |   |
| |  Your turn: round 9                |   |
| |  Payout: NGN 10,000.00 base pool   |   |
| |                                    |   |
| |  < View Ajo >    { Pay now }*      |   |
| +------------------------------------+   |
+-- (4) AJO CARD --------------------------+
| +------------------------------------+   |
| |  Chima's Ajo                       |   |
| |  round 9 of 10   ROUNDING          |   |
| |  #############-----                |   |
| |  9 of 10 members paid this round   |   |
| |                                    |   |
| |  Your turn: round 10, in 2 days    |   |
| |  Payout: NGN 10,000.00 base pool   |   |
| |                                    |   |
| |  < View Ajo >                      |   |
| +------------------------------------+   |
+-- (5) EMPTY STATE -----------------------+
| +------------------------------+         |
| |  You have not joined an Ajo   |        |
| |  yet.                        |         |
| |                              |         |
| |  { Create an Ajo }*          |         |
| |  { Join with a code }        |         |
| +------------------------------+         |
+-- (6) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) FILTER BAR --------------------------------------------------------+
| All 3   Active 2   Awaiting you 1   Overdue 0        [ New Ajo ]*        |
+-- (3) AJO TABLE ---------------------------------------------------------+
| AJO              STATE          ROUND  DUE       YOUR POS   TURNOVER     |
| Adaeze's Ajo     ACTIVE           4    12 Sep    9 of 10    round 9      |
| Chima's Ajo      ROUND_IN_PROG    9    19 Sep    10 of 10   round 10     |
| Fatima's Ajo     ENROLLMENT       -    14 Sep    awaiting    1 of 10     |
|                                                                          |
| Progress column carries a count, not only a bar.                         |
+-- (4) EMPTY STATE -------------------------------------------------------+
| You have not joined an Ajo yet.                                          |
|                                                                          |
| An Ajo needs at least two people, a contribution amount, a frequency,    |
| and a start date. Ten people at NGN 1,000.00 weekly for ten rounds is    |
| the arrangement this product is built around, but a group of five at     |
| NGN 2,000.00 is equally valid and the product does not assume otherwise. |
|                                                                          |
| { Create an Ajo }*        { Join with a code }                           |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.11.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Segmented control', 'All, Active, Joined, Past, with live counts.', 'P1', 'Counts are counts of Ajos, not of members or of amounts, and are labelled so the unit is unambiguous.'],
            ['(2) Status summary', 'What needs attention this week.', 'P1', '**Overdue is its own figure, never a negative colour on a due date.** Colour alone does not convey state, and the count must be reachable by a screen reader.'],
            ['(3) Ajo card', 'One card per Ajo: name, round, state, progress, position, due date, amount owed and amount charged.', 'P1', 'The card carries the fee line because this is the list a person screenshots or forwards to a group. The omitted detail is the members list, which has its own screen.'],
            ['(4) Pay action', 'Present only when a contribution is due and unpaid.', 'P1', 'Hidden, not disabled, when nothing is due. A greyed *Pay now* on every card trains people to ignore the primary action.'],
            ['(5) Empty state', 'Two ways in: create, or join with a code.', 'P1', 'The empty state states the minimum an Ajo needs, because the most common first-run failure is inventing a group that cannot satisfy the two-position guard.'],
            ['(6) Filter bar', 'Desktop filter bar with the create action.', 'P1', 'On desktop the filter is a row of counts rather than a segmented control, because four segments plus a page title plus a primary action does not fit one line at 1440 px with the left nav present.'],
            ['(7) Ajo table', 'Ajo, state, round, due, position, projected turnover round.', 'P1', 'State names are the CANONICAL.md state machine values, rendered in title case. The table shows the projected turnover round so a member can see how long they are in for without opening each Ajo.'],
        ],
        "widths": [0.42, 1.99, 0.42, 3.67],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.12 Create Ajo wizard — SCR-MOB-05'},

    {
        "t": "p",
        "text": 'Seven steps that turn an intention into an Ajo with a locked schedule. It is the longest flow in the product and the only one where a mistake is expensive, because an activated Ajo cannot be edited: positions are locked, the frequency is fixed, and the contribution amount is what every member will be charged. Every step therefore shows its consequence before the person commits, and the final step shows the whole arrangement in the same form a member will see it later.',
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'One desktop frame for all seven steps',
        "text": 'The desktop wizard chrome — progress rail, step body width, footer and its actions — is identical across the seven steps, so it is drawn once here rather than seven times. The step body is the only thing that changes, and the table below gives the step bodies, in wireframe body form, followed by the full region table. This is a drawing economy, not a specification economy: each of the seven steps is a distinct screen and each gets its own region table in 6.12.4.',
    },

    {"t": "h3", "text": '6.12.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** The step body sits between a fixed progress header and a fixed step navigation bar, so the body scrolls and the chrome does not. On a 375 px screen the body must fit in 375 minus 32 of gutters, which is the reason the step bodies below are single-column and short.',
    },

    {
        "t": "code",
        "text": """
+-- (1) PROGRESS --------------------------+
| Step 3 of 7                              |
|                                          |
| #########-----------------  43%          |
+-- (2) STEP BODY -------------------------+
| +------------------------------------+   |
| |  How often will you save?          |   |
| |                                    |   |
| |  (o) Weekly                        |   |
| |      Every Monday                  |   |
| |                                    |   |
| |  ( ) Monthly                       |   |
| |      Same day each month           |   |
| |                                    |   |
| |  Weekly rounds are the most        |   |
| |  common arrangement.               |   |
| +------------------------------------+   |
+-- (3) STEP NAV --------------------------+
| < Back                                   |
| { Continue }*                            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** The step body is capped at 720 px and left-aligned under the progress rail. It is deliberately narrow: a seven-step commitment form reads badly at full desktop width, and a wide form invites people to scan it.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV, INERT ---------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| The wizard is not in this nav.                                           |
| Save and close is in the footer.                                         |
+-- (2) PROGRESS RAIL -----------------------------------------------------+
| 1  Configure        done                                                 |
| 2  Amount           done                                                 |
| 3  Frequency        you are here                                         |
| 4  Duration                                                              |
| 5  Invite members                                                        |
| 6  Payout order                                                          |
| 7  Review                                                                |
|                                                                          |
| Completed steps are clickable.                                           |
| Steps ahead are inert.                                                   |
+-- (3) STEP BODY ---------------------------------------------------------+
| +----------------------------------------------------------------+       |
| |  How often will you save?                                      |       |
| |                                                                |       |
| |  (o) Weekly     Every Monday                                   |       |
| |  ( ) Monthly    Same day each month                            |       |
| |                                                                |       |
| |  Weekly rounds are the most common arrangement. A frequency    |       |
| |  cannot be changed after the Ajo is activated.                 |       |
| +----------------------------------------------------------------+       |
+-- (4) STEP NAV ----------------------------------------------------------+
| < Back                                                                   |
| Save and close                                                           |
| { Continue }*                                                            |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.12.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Progress', 'Step number, step name, and a progress bar.', 'P1', 'The bar is decorative and is duplicated by *Step 3 of 7* as text, so progress is never conveyed by a shape alone.'],
            ['(2) Step body', 'One decision per step. Never two.', 'P1', 'A step that needs a second decision is a second step. Combining amount and frequency is the specific temptation this structure refuses, because it produces a form people fill in wrong.'],
            ['(3) Consequence text', 'Plain-language effect of the choice, under the control.', 'P1', '*Weekly, every Monday* rather than *7-day period*. The person is deciding a day of their week, not a duration.'],
            ['(4) Step navigation', 'Back, and a Continue action labelled for the step.', 'P1', 'The label names the next step, not the action, so the button is *Continue* to *Duration* rather than *Next*. **Continue is disabled until the step is valid**, and disabled is a real disabled, not a greyed button that does nothing.'],
            ['(5) Progress rail', 'Desktop left rail listing all seven steps.', 'P1', 'Completed steps are clickable so a person can go back without pressing Back six times. Steps ahead are inert, because the wizard validates in order and a later step may depend on an earlier answer.'],
            ['(6) Inert app nav', 'Desktop left navigation present but disabled during the wizard.', 'P2', 'Leaving the wizard is allowed and the draft is kept. The nav is disabled so a person cannot lose an unsaved answer by a mis-click, and a **Save and close** action is offered in the footer instead.'],
        ],
        "widths": [0.42, 1.28, 0.42, 4.38],
        "size": 7.2,
    },

    {
        "t": "p",
        "text": 'The step list is fixed and comes from section 2, flow 2.6. Each step, its decision, its guard, and what it is allowed to change if the person presses Back are listed together, because a wizard is only safe when the reversibility of each step is as well understood as the step itself. The step bodies follow at 6.12.3 to 6.12.9, one heading per step.',
    },

    {
        "t": "table",
        "head": ['Step', 'Screen', 'Decision', 'Guard to continue', 'Editable after activation'],
        "rows": [
            ['1', 'Configure', 'Ajo name, number of positions, currency, start date', 'Name 3-60 chars, at least 2 positions, NGN only, start date not in the past', 'No. The Ajo is identified by this data and the schedule is derived from it.'],
            ['2', 'Amount', 'Contribution per member per round', 'NGN 100.00 to NGN 5,000,000, whole naira', 'No. This is the figure every member is charged.'],
            ['3', 'Frequency', 'Weekly or monthly', 'Exactly one selected', 'No. Changing it changes every due date.'],
            ['4', 'Duration', 'Rounds, defaulting to the position count', '1 to 52, and the derived end date is within 5 years', 'No.'],
            ['5', 'Invite members', 'Invite the people who will fill the positions', 'At least one pending invitation before the Ajo can open enrollment', 'Yes, while positions remain unfilled.'],
            ['6', 'Payout order', 'Propose the order positions are paid in', 'Every position assigned exactly once', '**No. Positions lock on activation.** Reordering afterwards needs a replacement request.'],
            ['7', 'Review', 'Read the whole arrangement, acknowledge, open enrollment', 'Every position filled **or** the person accepts the day-5 auto-cancel and refund', 'No. The review is the last point at which anything can be refused.'],
        ],
        "widths": [0.42, 0.42, 1.5, 2.15, 2.01],
        "size": 7.0,
    },

    {
        "t": "p",
        "text": 'Each step body below is the region content for the step body region of the two frames above, and each has its own annotated region table. The step numbers match the flow steps in section 2.6, so a reader holding both documents can move between them without translating.',
    },

    {"t": "h3", "text": '6.12.3 Step 1 — Configure'},

    {
        "t": "code",
        "text": """
+------------------------------+
|  Name this Ajo               |
|  It is what your members     |
|  will see.                   |
|  [ Adaeze's Ajo          ]   |
|                              |
|  Positions                   |
|  [  10                 ]    |
|  [ - ][ + ]                  |
|  2 to 50. Ten is the most    |
|  common.                     |
|                              |
|  Currency    NGN             |
|  Naira only at launch.       |
|                              |
|  Start date                  |
|  [ 15 Sep 2026           ]   |
|  First round opens on this   |
|  day. Cannot be in the past. |
""",
    },

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Name field', 'Free text shown to every member of the Ajo.', 'P1', '3 to 60 characters. The name is **not** the identifier: `POST /ajos` returns an `id` and a shareable invite link, and the name is display only. Renaming is allowed until activation because it changes no money.'],
            ['(2) Position count', 'Number of payout positions, i.e. the number of members the Ajo is for.', 'P1', 'The CANONICAL.md DRAFT to ENROLLMENT guard is at least 2 positions. The stepper stops at the D-08 cap, which is **not yet fixed** and is flagged as open rather than given a number here.'],
            ['(3) Currency', 'Read-only NGN.', 'P1', 'Single currency at v1. A currency selector with one option is a promise about the future, so it is not rendered.'],
            ['(4) Start date', 'Date the first round opens.', 'P1', 'Not in the past, within 90 days. **The five-day enrollment window starts here, not at creation**, so this date determines when the Ajo can cancel itself with a full refund.'],
        ],
        "widths": [0.42, 1.49, 0.42, 4.17],
        "size": 7.2,
    },

    {"t": "h3", "text": '6.12.4 Step 2 — Amount'},

    {
        "t": "code",
        "text": """
+------------------------------+
|  What does each member pay  |
|  each round?                 |
|  [ NGN 1,000.00         ]    |
|  [ - ][ + ]                  |
|                              |
|  With a 2% AJO.ng fee on    |
|  each payment, every member  |
|  is charged:                  |
|                              |
|  NGN 1,000.00  contribution  |
|  NGN    20.00  AJO.ng fee    |
|  NGN 1,020.00  charged       |
|                              |
|  x  Above the NGN 5,000,000  |
|   per-round cap. This limit  |
|   is set by risk, not by us. |
""",
    },

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Amount field', 'Contribution per member per round, in naira.', 'P1', 'Accepts naira and kobo, displays naira with two decimals, and rejects the thousand separator on entry so the value cannot be misparsed.'],
            ['(2) Stepper', 'Increment and decrement by NGN 100.00.', 'P2', 'A convenience, not the primary input. Typing is always available, because a stepper of 50 presses to reach NGN 5,000 is worse than typing.'],
            ['(3) Live fee preview', 'The three-line breakdown of what the member will actually be charged.', 'P1', '**This block is mandatory and may not be removed from the wizard.** CANONICAL.md requires the fee to be disclosed before the member commits, and the only moment a member commits is here and in the join confirmation. The total is labelled *charged* rather than *total* to distinguish it from the pool.'],
            ['(4) Cap message', 'The rejection when the amount exceeds the D-08 cap.', 'P1', 'Names the limit and its owner, because a limit with no stated owner becomes a support ticket.'],
        ],
        "widths": [0.42, 1.13, 0.42, 4.53],
        "size": 7.2,
    },

    {"t": "h3", "text": '6.12.5 Step 3 — Frequency'},

    {
        "t": "code",
        "text": """
+------------------------------+
|  How often will you save?     |
|                              |
|  (o) Weekly                  |
|      Every Monday             |
|                              |
|  ( ) Monthly                 |
|      Same day each month      |
|                              |
|  x  A frequency cannot be    |
|   changed once the Ajo is    |
|   active.                    |
""",
    },

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Radio pair', 'Weekly or monthly, exactly one.', 'P1', 'A radio group, not a segmented control. A segmented control implies both are visible states of one control; a frequency is an exclusive choice of one value, and the label for each value carries the day or date rule.'],
            ['(2) Day rule', "The derived rule, in the person's own terms.", 'P1', '*Every Monday* and *same day each month*, not *7-day cycle* and *30-day cycle*. The start date from step 1 supplies the day.'],
            ['(3) Irreversibility note', 'States that this cannot be changed after activation.', 'P1', 'Shown on the step rather than at review, because this is the step where a person decides. An irreversibility warning seven steps later is a warning nobody reads.'],
        ],
        "widths": [0.52, 1.13, 0.42, 4.43],
        "size": 7.2,
    },

    {"t": "h3", "text": '6.12.6 Step 4 — Duration'},

    {
        "t": "code",
        "text": """
+------------------------------+
|  How many rounds?             |
|  [ 10                    ]    |
|  [ - ][ + ]                  |
|                              |
|  = 10 members, 10 rounds,    |
|    everyone pays once and     |
|    everyone is paid once.     |
|                              |
|  Round    Due            Fee  |
|  1        15 Sep       NGN 20 |
|  2        22 Sep       NGN 20 |
|  3        29 Sep       NGN 20 |
|  4        05 Oct       NGN 20 |
|  ...                          |
|  10       10 Nov       NGN 20 |
|                              |
|  Ends 10 Nov 2026            |
""",
    },

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Rounds field', 'Number of rounds, defaulting to the position count from step 1.', 'P1', 'Rounds need not equal positions. A group of ten people who save for five rounds is a real arrangement, and the product does not force the equal case.'],
            ['(2) Relationship note', 'States the relationship between positions, rounds and payouts in one sentence.', 'P1', '*Everyone pays once and everyone is paid once* holds only when rounds equal positions. **When they differ, the note changes to describe the actual shape** and says plainly who is not paid, because the equal case is the one that reads as universal and is not.'],
            ['(3) Schedule preview', 'The first four and last round with due dates and the fee.', 'P1', 'Due dates are computed from the start date and the frequency, so a date change in step 1 is visible here as a consequence rather than discovered later. The fee column is per round, because that is how it is charged.'],
            ['(4) End date', 'The date the last round is due.', 'P1', 'Derived, not entered. A person who would rather enter an end date is expressing the same intent, and the derived value is less ambiguous.'],
        ],
        "widths": [0.42, 1.39, 0.42, 4.27],
        "size": 7.2,
    },

    {"t": "h3", "text": '6.12.7 Step 5 — Invite members'},

    {
        "t": "code",
        "text": """
+------------------------------+
|  Invite your members         |
|                              |
|  Positions 4 of 10 filled    |
|  ########---                 |
|                              |
|  1  Adaeze    joined         |
|  2  Chima     joined         |
|  3  Fatima    joined         |
|  4  Ibrahim   invited        |
|  5  -         add            |
|  6  -         add            |
|  ...                          |
|  10 -         add            |
|                              |
|  { Add by phone }*           |
|  { Copy invite link }        |
|                              |
|  ! 6 positions still open.   |
|   This Ajo cancels itself on  |
|   20 Sep if they are not     |
|   filled, and you are         |
|   refunded in full.          |
""",
    },

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Position roster', 'One row per position, in payout order.', 'P1', "The roster is editable here and nowhere else before activation. **A filled position may be cleared**, which removes the member and frees the position; an accepted member cannot be silently dropped, so a removal requires the member's own decline or an explicit removal action that is recorded."],
            ['(2) Add by phone', 'Invites a person by phone number.', 'P1', 'Creates an `invitations` row and sends `invitation.received` by push, email and SMS, because the recipient may not have an account yet.'],
            ['(3) Copy invite link', 'A shareable link for open group chats.', 'P1', 'The link resolves to `GET /invitations/:token` and then the join screen at 6.13. It is not the same URL as the Ajo, so a link posted publicly does not expose the Ajo.'],
            ['(4) Enrollment deadline warning', 'The day-5 auto-cancel and full-refund rule, with the actual date.', 'P1', '**Mandatory.** CANONICAL.md fixes the enrollment window at exactly 5 days with automatic cancellation and full refund. A rule with a financial consequence and a date attached belongs on the screen, not in a policy page.'],
        ],
        "widths": [0.51, 1.07, 0.42, 4.5],
        "size": 7.2,
    },

    {"t": "h3", "text": '6.12.8 Step 6 — Payout order'},

    {
        "t": "code",
        "text": """
+------------------------------+
|  Who is paid, and when?      |
|                              |
|  1  Adaeze    round 1        |
|  2  Chima     round 2        |
|  3  Fatima    round 3        |
|  4  Ibrahim   round 4        |
|  5  ...                       |
|  10 Ibrahim   round 10       |
|                              |
|  < Drag to reorder >          |
|                              |
|  !  This order locks when    |
|   the Ajo activates. Moving  |
|   someone afterwards needs a  |
|   replacement request, and   |
|   both people must agree.    |
""",
    },

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Ordered position list', 'Positions 1 to N in the order they will be paid.', 'P1', 'Ordering is by drag on mobile with keyboard support on desktop, and every row also has move-up and move-down controls. **Drag alone is not sufficient**: it is unusable with a keyboard and unusable with a screen reader, and reordering a payout order is a financial act.'],
            ['(2) Payout amount per position', 'The amount each position will receive.', 'P1', "The base pool, NGN 10,000.00 in the worked example, labelled as the base pool. It is never shown as the collected total, because that figure includes AJO.ng's fee and is not paid out."],
            ['(3) Lock warning', 'States the lock and the only post-activation route.', 'P1', 'CANONICAL.md: payout positions lock on activation, and reordering requires a formal replacement or transfer request. The warning names the route so the rule reads as a process rather than a prohibition.'],
        ],
        "widths": [0.55, 0.93, 0.42, 4.6],
        "size": 7.2,
    },

    {"t": "h3", "text": '6.12.9 Step 7 — Review'},

    {
        "t": "code",
        "text": """
+------------------------------+
|  Check this before you open  |
|  enrollment.                 |
|                              |
|  Adaeze's Ajo               |
|  10 members, 10 rounds,      |
|  weekly from 15 Sep 2026     |
|  ends 10 Nov 2026            |
|                              |
|  Each member owes            |
|    NGN 1,000.00 contribution |
|    NGN    20.00 AJO.ng fee   |
|    NGN 1,020.00 charged      |
|                              |
|  At their turn each member   |
|  receives NGN 10,000.00, the |
|  base pool.                  |
|                              |
|  Total across this Ajo:      |
|    charged   NGN 102,000.00  |
|    to AJO.ng NGN 2,000.00    |
|                              |
|  [x] I have told everyone    |
|      the order, the amount   |
|      and the fee.            |
|                              |
|  { Open enrollment }*        |
""",
    },

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Arrangement summary', 'Name, members, rounds, frequency, start, end.', 'P1', 'Reassembled from the answers, not from a draft field, so the summary cannot drift from what will be created.'],
            ['(2) Member charge block', 'Contribution, fee and charged, per member.', 'P1', '**Mandatory, third and final occurrence in the wizard.** Between the step-2 preview and this block the amount may have changed context, and the disclosure rule in CANONICAL.md requires the fee to be shown before the member commits. The charged figure is named *charged*, the pool figure is named *base pool*.'],
            ['(3) Ajo-level totals', 'Total charged across the Ajo and the fee AJO.ng retains.', 'P1', "NGN 102,000.00 charged and NGN 2,000.00 retained for the ten-member worked example. This is the organizer's number, and it is the reason the disclosure is on this screen as well as the member's."],
            ['(4) Acknowledgement', 'One required checkbox.', 'P1', 'The wording is *I have told everyone the order, the amount and the fee*. **The fee is in the acknowledgement because the most common dispute after launch will be a member who says nobody told them about the NGN 20.00.** This is an organiser attestation, not a platform warranty, and it is recorded as such.'],
            ['(5) Open enrollment', 'The commit action.', 'P1', 'Calls `POST /ajos/:id/activate`, which performs DRAFT to ENROLLMENT and requires a reason. The button is the last point at which anything can be refused, so the label names the state change rather than *Finish*.'],
        ],
        "widths": [0.42, 0.92, 0.42, 4.74],
        "size": 7.2,
    },

    {"t": "h3", "text": '6.12.10 Wizard states and guards'},

    {
        "t": "table",
        "head": ['State', 'When it applies', 'What the person sees', 'What is stored'],
        "rows": [
            ['Entry', 'First visit', 'Step 1, empty, with a **Save and close** action in the footer', 'Nothing. A draft is created on the first Continue, not on entry, so an abandoned first visit leaves no rows.'],
            ['Resumed', 'Return from Save and close', 'The step they reached, with answers intact', 'A DRAFT `ajos` row and its positions.'],
            ['Invalid', 'Continue pressed with an invalid step', 'A message beside the offending field, and focus moved to it', 'The draft, unchanged.'],
            ['Stale', 'The draft changed in another tab or by the organiser', 'A notice that the arrangement was updated and the step is reloaded', 'The draft, and the version that lost the race is discarded.'],
            ['Submitted', 'Open enrollment pressed', 'The Ajo detail screen in ENROLLMENT', 'An ACTIVE-eligible ENROLLMENT Ajo with locked positions.'],
        ],
        "widths": [0.42, 1.44, 1.83, 2.81],
        "size": 7.2,
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Why the draft is a real Ajo and not a client-side form',
        "text": 'A `DRAFT` Ajo is a server-side row from the moment the first step is completed, because the invite links in step 5, the position roster and the version counter all need somewhere to live, and because a person who closes the tab on a phone and finishes on a laptop must find the same draft. The five-day enrollment window does **not** start at draft creation: it starts at the transition to ENROLLMENT, so a draft abandoned for a month is not cancelled and creates no obligation.',
    },

    {"t": "h2", "text": '6.13 Join Ajo — SCR-MOB-04'},

    {
        "t": "p",
        "text": 'The acceptance path for an invited person, and the last point at which a member sees what they are agreeing to. It is two steps rather than one because the CANONICAL.md disclosure rule requires the fee to be shown before the member commits, and a single screen that both explains and accepts invites people past the explanation. Nothing is charged here: accepting creates the `ajo_members` row and the first contribution obligation, and payment happens on its own schedule.',
    },

    {
        "t": "callout",
        "kind": 'LEGAL',
        "title": 'Consent capture on the join and review acknowledgements',
        "text": "The acknowledgement checkbox and the surrounding disclosure are drafted as evidence that the member was told the contribution amount, the fee and the order before committing. They are not drafted as a contract, and no part of this specification asserts that a checkbox on a web screen satisfies any particular consent, formation or disclosure requirement under Nigerian law or under the payment partner's terms. **Requires review by qualified Nigerian legal counsel**, together with confirmation of what ProvidusUnity requires in its own onboarding flow. If counsel advises that a stronger form is needed, the acknowledgement becomes a separate document and the two acknowledgements here are replaced by links to it.",
    },

    {"t": "h3", "text": '6.13.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** Two steps rather than one long scroll. The confirm step repeats the fee block rather than referring back to step 1, because a scroll-and-remember flow is how a commitment gets made without being read.',
    },

    {
        "t": "code",
        "text": """
+-- (1) PROGRESS --------------------------+
| Join an Ajo                              |
|                                          |
| Step 1 of 2                              |
+-- (2) INVITE ----------------------------+
| +------------------------------------+   |
| |  You have been invited             |   |
| |                                    |   |
| |  to Adaeze's Ajo                   |   |
| |                                    |   |
| |  10 members, weekly,               |   |
| |  NGN 1,000.00 each,                |   |
| |  10 rounds from 15 Sep             |   |
| |                                    |   |
| |  { Continue }*                     |   |
| |  < Decline >                       |   |
| +------------------------------------+   |
+-- (3) STEP 2: CONFIRM -------------------+
| +------------------------------------+   |
| |  Before you join                   |   |
| |                                    |   |
| |  Adaeze's Ajo                      |   |
| |  round 1 of 10                     |   |
| |                                    |   |
| |  You owe each round                |   |
| |    NGN 1,000.00  contribution      |   |
| |    NGN    20.00  AJO.ng fee        |   |
| |    NGN 1,020.00  charged           |   |
| |                                    |   |
| |  You are position 9 of 10.         |   |
| |  You will be paid in round 9:      |   |
| |  NGN 10,000.00, the base pool.     |   |
| |                                    |   |
| |  Positions lock when the           |   |
| |  Ajo activates. You cannot         |   |
| |  leave after that without          |   |
| |  a replacement request.            |   |
| |                                    |   |
| |  [x] I understand the order,       |   |
| |      the amount and the fee.       |   |
| |                                    |   |
| |  {         Join Ajo         }*     |   |
| +------------------------------------+   |
+-- (4) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Step 2 is a two-column layout: the charge and payout figures on the left as a labelled list with rules, and the acknowledgement and action on the right. The figures are not in a card, because a card implies they are optional detail.',
    },

    {
        "t": "code",
        "text": """
+-- (1) STEP 1: INVITATION ------------------------------------------------+
| You have been invited to Adaeze's Ajo                                    |
|                                                                          |
| 10 members, weekly, NGN 1,000.00 each, 10 rounds from 15 Sep 2026.       |
| The organiser is Adaeze B. (0703 000 0001).                              |
|                                                                          |
| What the invitation does not do: it does not take your position, and it  |
| does not commit you to paying. You choose whether to accept, and         |
|   accepting                                                              |
| still lets you see the full arrangement first.                           |
|                                                                          |
| { Continue }*        < Decline >                                         |
+-- (2) STEP 2: CONFIRM ---------------------------------------------------+
| Before you join                                                          |
|                                                                          |
|   Contribution per round      NGN 1,000.00                               |
|   AJO.ng fee, 2%                  NGN 20.00                              |
|   Charged to you per round     NGN 1,020.00                              |
|   -----------------------------------------------------                  |
|   Your position                 9 of 10                                  |
|   You are paid in round 9                                                |
|   Base pool paid to you        NGN 10,000.00                             |
|   -----------------------------------------------------                  |
|   Total charged by you, 10 rounds                                        |
|                                 NGN 10,200.00                            |
|                                                                          |
| Positions lock when the Ajo activates. After that, leaving requires a    |
| replacement request that the person taking your place must also accept.  |
|                                                                          |
| [x] I understand the order, the amount and the fee.                      |
|                                                                          |
| {         Join Ajo         }*        < Back >                            |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.13.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Invitation summary', 'Who invited, which Ajo, and its shape.', 'P1', 'Taken from the invitation token, so a person who was invited to an Ajo that has since closed sees that fact rather than a broken join.'],
            ['(2) Decline', 'An explicit way to say no.', 'P1', 'Decline records a response so the organiser sees the position still open, and frees the position. **Decline never requires a reason**, because a required reason is a request to be persuaded.'],
            ['(3) Charge breakdown', 'Contribution, fee, and total charged, for the round and across the Ajo.', 'P1', '**Mandatory, per the disclosure rule.** The three figures are never merged into a single *NGN 1,020.00 per round with fee* line. Both the per-round and the across-the-Ajo totals are shown, because *10,200.00 total* is the number that surprises people at month three and it is far better to say it now.'],
            ['(4) Position and payout', 'The position offered and the base pool to be received.', 'P1', 'Says *base pool* explicitly, and gives the round number. A member who is told NGN 10,000.00 with no explanation will later compare it against NGN 10,200.00 collected and conclude the platform took a cut of their own money.'],
            ['(5) Lock warning', 'Positions lock on activation; leaving needs a replacement.', 'P1', 'Required because the person is about to give up the ability to leave unilaterally, which CANONICAL.md fixes as an `ajo_member` limitation.'],
            ['(6) Acknowledgement', 'One checkbox covering order, amount and fee.', 'P1', "Mirrors the wizard's review acknowledgement so the two flows use the same words."],
            ['(7) Join action', 'Commits the membership.', 'P1', 'POST /invitations/:token/accept. The action is idempotent, so a double tap produces one membership row and one contribution obligation rather than two.'],
        ],
        "widths": [0.42, 1.15, 0.42, 4.51],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.14 Ajo Detail — SCR-MOB-03'},

    {
        "t": "p",
        "text": 'The reference page for one Ajo. Everything a member needs in order to decide what they owe, when they will be paid, and how much they will receive is on this one screen, because the question that brings someone here — *is this right, and am I in the right place* — is answered by seeing the whole arrangement at once. It is a read surface: the only action that moves money on it is the payment for a contribution that is already due.',
    },

    {
        "t": "callout",
        "kind": 'WARNING',
        "title": 'The base-pool sentence is load-bearing',
        "text": "The line stating that the NGN 20.00 fee is not part of the pool is the most load-bearing sentence in the interface. A member who sees NGN 10,200.00 collected and NGN 10,000.00 received, with no explanation, will reasonably conclude AJO.ng took 2% of their own savings. That is not a cosmetic omission; it is the product failing to keep the trust the fee model depends on. The sentence appears on this screen, on the receipt at 6.19, on the payout screen at 6.20, in the marketing fee copy, and in the join confirmation at 6.13. Removing it from any of those is a change to the fee model's disclosure, not to a design.",
    },

    {"t": "h3", "text": '6.14.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| < My Ajos   Adaeze's Ajo   [more]        |
+-- (2) STATUS ----------------------------+
| ACTIVE                                   |
| round 4 of 10                            |
| 7 of 10 paid this round                  |
| ###########-------                       |
+-- (3) KEY FACTS -------------------------+
| Contribution   NGN 1,000.00              |
| AJO.ng fee        NGN 20.00              |
| Charged        NGN 1,020.00              |
| Frequency      weekly, Mondays           |
| Started        15 Sep 2026               |
| Ends           10 Nov 2026               |
+-- (4) YOUR POSITION ---------------------+
| +------------------------------------+   |
| |  You are position 9 of 10          |   |
| |                                    |   |
| |  Round    Due        Fee           |   |
| |    Status                          |   |
| |  1        15 Sep     NGN 20        |   |
| |    paid                            |   |
| |  2        22 Sep     NGN 20        |   |
| |    paid                            |   |
| |  3        29 Sep     NGN 20        |   |
| |    paid                            |   |
| |  4        05 Oct     NGN 20   due  |   |
| |  ...                               |   |
| |  9        09 Nov     NGN 20        |   |
| |    your turn                       |   |
| |                                    |   |
| |  You are paid NGN 10,000.00 in     |   |
| |  round 9. That is the base pool:   |   |
| |  10 members at NGN 1,000.00.       |   |
| +------------------------------------+   |
+-- (5) ACTIONS ---------------------------+
| { Pay round 4 }*                         |
| < Members >  < Schedule >                |
| < Raise a dispute >                      |
+-- (6) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) HEADER ------------------------------------------------------------+
| < My Ajos    Adaeze's Ajo    ACTIVE    round 4 of 10    [More]           |
+-- (3) SUMMARY -----------------------------------------------------------+
| CONTRIBUTION   NGN 1,000.00   FREQUENCY   weekly, Mondays                |
| AJO.ng FEE         NGN 20.00   STARTED     15 Sep 2026                   |
| CHARGED         NGN 1,020.00   ENDS        10 Nov 2026                   |
+-- (4) SCHEDULE TABLE ----------------------------------------------------+
| ROUND  DUE       YOUR FEE   YOUR STATUS   WHO IS PAID                    |
| 1       15 Sep    NGN 20.00  paid          Adaeze B.                     |
| 2       22 Sep    NGN 20.00  paid          Chima O.                      |
| 3       29 Sep    NGN 20.00  paid          Fatima S.                     |
| 4       05 Oct    NGN 20.00  DUE  NGN      Ibrahim D.                    |
|                      1,000.00                                            |
| 5       12 Oct    NGN 20.00  not due       Yeti A.                       |
| ...                                                                      |
| 9       09 Nov    NGN 20.00  not due       YOU                           |
| 10      16 Nov    NGN 20.00  not due       Segun B.                      |
+-- (5) RIGHT COLUMN ------------------------------------------------------+
| Your position                                                            |
| 9 of 10. Paid in round 9.                                                |
|                                                                          |
| Base pool at your turn                                                   |
| NGN 10,000.00                                                            |
| 10 members x NGN 1,000.00.                                               |
| The NGN 20.00 fee per member                                             |
| stays with AJO.ng and is not                                             |
| part of the pool.                                                        |
|                                                                          |
| Organiser                                                                |
| Adaeze B.  0703 000 0001                                                 |
+-- (6) ACTIONS -----------------------------------------------------------+
| { Pay round 4 }*   < Members >   < Schedule >   < Raise a dispute >      |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.14.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Header', 'Back to the list, Ajo name, and an overflow menu.', 'P1', 'The state appears in the header on mobile as well as the body, so it is visible before scrolling to anything.'],
            ['(2) Status', 'State, round counter, and round progress.', 'P1', 'State values are the CANONICAL.md lifecycle names. `ROUND_IN_PROGRESS` renders as *Rounding*, because the internal name is for engineers and the screen is for members.'],
            ['(3) Key facts', 'Contribution, fee, charged, frequency, start and end.', 'P1', '**The fee appears here even though no payment is being made**, because CANONICAL.md requires the fee to be shown in every Ajo details screen, not only on payment screens. A member checking the numbers before their turn has paid needs to see the same three figures they were charged.'],
            ['(4) Your position', 'Position number, and the round in which this member is paid.', 'P1', 'The projected payout is named *base pool* and shows the derivation *10 members x NGN 1,000.00*, plus one sentence saying the fee is not part of the pool. This is the sentence that prevents the NGN 10,200-versus-NGN 10,000 support ticket.'],
            ['(5) Schedule table', "Every round: due date, this member's fee, status, and who is paid.", 'P1', "Two columns, because they answer different questions and conflating them is how a member decides they are the wrong person for the round. *Who is paid* reveals other members' first names to members, which is in scope because names are what a group uses to recognise each other; phone numbers and amounts each member owes are not."],
            ['(6) Fee column', 'The fee the member will pay for that round.', 'P1', 'Per round, not a total, because rounds are billed individually and a total on a schedule implies a lump sum that does not exist.'],
            ['(7) Actions', 'Pay when due, and navigation to members, schedule and disputes.', 'P1', 'Pay appears only when a contribution is due and unpaid, for the same reason as 6.11: a permanently visible pay button trains people to ignore it.'],
            ['(8) Right column', 'Position, base pool derivation, and organiser contact.', 'P2', 'Organiser contact is available to members. A group that cannot reach its own organiser stops using the Ajo, and the platform is not a substitute for the relationship.'],
        ],
        "widths": [0.42, 1.02, 0.42, 4.64],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.15 Members — SCR-MOB-06'},

    {
        "t": "p",
        "text": "The roster, and the screen where the product's privacy position has to be practical rather than merely stated. Members need to know who else is in the Ajo and whose turn it is, because that is how a group confirms it has formed correctly. They do not need to know what anyone else owes, and the screen is designed so that the useful information is complete without that information being present.",
    },

    {
        "t": "callout",
        "kind": 'DECISION',
        "title": 'First name and initial only in the member roster',
        "text": 'Members see first name plus initial for other members, and organisers see the same plus their reminder and replacement columns. Showing full names would be marginally more useful for a group of people who already know each other; showing contact details would be a privacy exposure for a financial product. The trade-off is that a group whose members do not know each other by first name has to confirm its roster through its own channel, which is acceptable because such a group has no reason to trust a platform roster anyway. The alternative considered was hashed identifiers with no names at all, rejected because a group cannot verify its own formation without recognising its members.',
    },

    {"t": "h3", "text": '6.15.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| < Ajo   Members        10                |
+-- (2) FILTER ----------------------------+
| All 10                                   |
| Paid 7                                   |
| Due 1                                    |
| Late 1                                   |
+-- (3) MEMBER ROWS -----------------------+
| Pos  Name       Turn  R4                 |
| 1    Adaeze B.    1   paid               |
| 2    Chima O.     2   paid               |
| 3    Fatima S.    3   paid               |
| 4    Ibrahim D.   4   LATE               |
| 5    Yeti A.      5   paid               |
| ...                                      |
| 9    Segun A.     9   soon               |
| 10   Ngozi E.    10   soon               |
+-- (4) PRIVACY NOTE ----------------------+
| x  Ajo.ng does not show what             |
|    another member owes you, or           |
|    owes the group.                       |
+-- (5) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) HEADER ------------------------------------------------------------+
| < My Ajos    Adaeze's Ajo    Members                                     |
+-- (3) MEMBER TABLE ------------------------------------------------------+
| POS  NAME         TURN  ORG   ROUND 4   LAST PAID   SHOWN TO             |
| 1    Adaeze B.      1    yes   paid       29 Sep      n, t, s            |
| 2    Chima O.       2    no    paid       29 Sep      n, t, s            |
| 3    Fatima S.      3    no    paid       29 Sep      n, t, s            |
| 4    Ibrahim D.     4    no    OVERDUE 2d 29 Sep      n, t, s            |
| 5    Yeti A.        5    no    paid       29 Sep      n, t, s            |
| ...                                                                      |
| 9    Segun A.       9    no    not due    -           n, t, s            |
| 10   Ngozi E.      10    no    not due    -           n, t, s            |
|                                                                          |
| n = first name and initial, t = turn, s = round status.                  |
| No phone, no email, and no amount any member owes another member.        |
+-- (4) ORGANISER VIEW ----------------------------------------------------+
| Extra columns for ajo_organizer only:                                    |
|                                                                          |
|   last reminder sent      12 Sep 09:14                                   |
|   reminders this round    2 of 3                                         |
|   replace request         none                                           |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.15.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Header', 'Back to the Ajo, title, and the member count.', 'P1', 'The count is the filled position count, not the invitation count, because an unfilled position is not a member.'],
            ['(2) Filter', 'All, paid, due, late, with counts.', 'P1', '*Late* is a neutral word. The screen does not say *deadbeat* or *defaulted* about a person, and CANONICAL.md forbids publicly shaming or exposing defaulting members.'],
            ['(3) Position column', 'The payout position, 1 to N.', 'P1', "Shown as the *turn* in the person's own terms. The internal `ajo_positions` row number is not a user-facing concept and never appears."],
            ['(4) Name', 'First name and initial only.', 'P1', '**Full names and contact details of other members are not displayed to ordinary members.** A group recognises its own participants by first name; a full name, phone number or email of a third party is data the viewer has no need for.'],
            ['(5) Round status', "This round's contribution state per member.", 'P1', 'State names are the contribution state machine: paid, due, overdue, grace, defaulted, recovered, written off. A member in grace is shown as *in grace* rather than *late*, because grace is a designed period and not a fault.'],
            ['(6) Amounts withheld', 'What another member owes is never shown to a member.', 'P1', "**Prohibited in any member view.** If a member sees NGN 2,000.00 outstanding beside a colleague's name, the group starts charging each other, and AJO.ng's position that it never charges other members extra becomes a lie the interface is telling."],
            ['(7) Organiser columns', 'Reminder history and replacement status.', 'P1', 'Visible to `ajo_organizer` only. Reminders are capped per round and the count is shown, so the organiser can see they have exhausted the gentle options without leaving the app.'],
            ['(8) Last paid', 'The date the member last paid a contribution.', 'P2', "A date, not an amount. The date is enough to run a group down; the amount is nobody else's business."],
        ],
        "widths": [0.42, 1.04, 0.42, 4.62],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.16 Contribution Schedule — SCR-MOB-07'},

    {
        "t": "p",
        "text": "The schedule, on a phone and as a calendar on a desktop. It answers *when* and *how much*, and it is where the difference between what a round collects and what it pays out becomes visible in a form people can act on: the round shows NGN 10,200.00 collected, the recipient is paid NGN 10,000.00, and the NGN 200.00 gap is the platform's. The table is the single clearest place in the product to show that gap without embarrassment, because the arithmetic is right there.",
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Why the calendar is desktop-only',
        "text": 'A month grid is 7 by 5 cells and is unusable at 375 px, where each cell would be about 45 px across and the day numbers would be the only legible content. On mobile the equivalent information is the round list, which is a strictly better shape for a phone because it is ordered by round rather than by date. The calendar is not hidden behind a view switcher on mobile; adding a switcher would give a phone user two worse options instead of one good one.',
    },

    {"t": "h3", "text": '6.16.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| < Ajo   Schedule                         |
+-- (2) NEXT DUE --------------------------+
| +------------------------------------+   |
| |  Round 4                           |   |
| |  Due 05 Oct 2026                   |   |
| |                                    |   |
| |  You owe        NGN 1,000.00       |   |
| |  AJO.ng fee       NGN 20.00        |   |
| |  Charged        NGN 1,020.00       |   |
| |                                    |   |
| |  7 of 10 paid. 1 overdue.          |   |
| |                                    |   |
| |  { Pay now }*                      |   |
| +------------------------------------+   |
+-- (3) ROUND LIST ------------------------+
| 1  15 Sep  done     Adaeze               |
| 2  22 Sep  done     Chima                |
| 3  29 Sep  done     Fatima               |
| 4  05 Oct  collecting                    |
| 5  12 Oct  upcoming                      |
| ...                                      |
| 9  09 Nov  you                           |
| 10 16 Nov  Segun                         |
+-- (4) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) CALENDAR ----------------------------------------------------------+
| September 2026                 October 2026                              |
| Mo Tu We Th Fr Sa Su           Mo Tu We Th Fr Sa Su                      |
|         1  2  3  4  5  6           5  6  7  8  9 10                      |
|  7  8  9 10 11 12 13          12 13 14 15 16 17                          |
| 14 15 16 17 18 19 20          19 20 21 22 23 24                          |
| 21 22 23 24 25 26 27          26 27 28 29 30 31                          |
| 28 29 30                      1  2  3                                    |
|                                                                          |
| * 15 Sep  round 1  collected                                             |
| * 22 Sep  round 2  collected                                             |
| * 29 Sep  round 3  collected                                             |
| * 05 Oct  round 4  collecting  7 of 10                                   |
+-- (3) ROUND TABLE -------------------------------------------------------+
| ROUND  DUE       OPENS   CLOSES   COLLECTED   STATE                      |
| 1       15 Sep    14 Sep  16 Sep  NGN 10,200  COMPLETE                   |
| 2       22 Sep    21 Sep  23 Sep  NGN 10,200  COMPLETE                   |
| 3       29 Sep    28 Sep  30 Sep  NGN 10,200  COMPLETE                   |
| 4       05 Oct    04 Oct  06 Oct  NGN 7,140   COLLECTING                 |
| ...                                                                      |
| 9       09 Nov    08 Nov  10 Nov  -           SCHEDULED                  |
| 10      16 Nov    15 Nov  17 Nov  -           SCHEDULED                  |
|                                                                          |
| Collected includes the NGN 20.00 fee per member. The pool paid out is    |
| NGN 10,000.00. The difference is AJO.ng's, and is never paid out.        |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.16.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Next due card', "The nearest due round, with the member's own three figures.", 'P1', '**The fee is shown even when the round is not yet due**, because this is the screen a member checks before committing money, and the disclosure rule applies before the charge, not after it.'],
            ['(2) Round state', 'Collected, collecting, or upcoming.', 'P1', 'A round is *collecting* from the day it opens to the day it closes, and *collected* when fully funded. The states match the round and payout states in CANONICAL.md section 4.'],
            ['(3) Round list', 'One line per round: number, date, state, recipient.', 'P1', "The recipient's name is shown so a group can see whose turn it is without opening each round. The member's own turn is marked in the list rather than only in the detail."],
            ['(4) Calendar', 'Desktop month grid with rounds marked.', 'P2', "Rounds are marked on the date they are **due**, not the date they open, because a person's obligation is the due date. A round that opens a day earlier and is missed is still missed on the due date."],
            ['(5) Collected figure', 'What the round has actually collected, in total.', 'P1', '**Labelled as collected, including the fee, with the pool and the difference stated beneath.** The figure NGN 10,200.00 on its own is the number most likely to be read as *what the recipient gets*, so it is never shown alone.'],
            ['(6) Contribution count', 'How many of N members have paid the round.', 'P1', 'Count plus fraction, never a proportion bar on its own. A member deciding whether their group is on track needs a number.'],
            ['(7) Overdue count', 'How many members are past due in this round.', 'P1', 'A count, with no names attached on this screen, and no colour-only signal. The named version of this fact lives on the members screen for the organiser, and the member-facing one is a total.'],
        ],
        "widths": [0.46, 1.22, 0.42, 4.4],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.17 Pay Contribution — SCR-MOB-09'},

    {
        "t": "p",
        "text": "The screen that spends money, and the most consequential wireframe in the product. Its job is to be unambiguous: what the amount is, what the fee is, what will actually leave the account, and where the payment will happen. It does not take a card number, it does not show a spinner, and it does not offer a *remember this method* checkbox, because the payment is the provider's to take and AJO.ng's to record.",
    },

    {
        "t": "callout",
        "kind": 'LEGAL',
        "title": 'What this screen may and may not say about the payment partner',
        "text": 'The screen names ProvidusUnity as the party that takes the payment, because CANONICAL.md section 6 places the payment endpoints and the webhook there and because hiding it would be worse. It does **not** claim that AJO.ng is authorised, licensed, approved or regulated, that the payment is held in escrow, that funds are insured, or that any particular processing or settlement time will be met. Open decision D-02 — whether the partner holds funds as principal or AJO.ng must hold them — determines the licensing path and is unresolved, and D-03, the exact collection percentage, flat payout fee and settlement timing, must be obtained in writing before any of that wording is published. **Requires confirmation with ProvidusUnity and review by qualified Nigerian legal counsel.**',
    },

    {"t": "h3", "text": '6.17.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** Amount first, then method, then a single full-width commit action. The action is not sticky, because a sticky money button on a page whose content scrolls is how a member charges an amount they did not read.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| < Ajo   Round 4                          |
+-- (2) AMOUNT ----------------------------+
| +------------------------------------+   |
| |  What you will be charged          |   |
| |                                    |   |
| |  Contribution    NGN 1,000.00      |   |
| |  AJO.ng fee 2%      NGN 20.00      |   |
| |  --------------------------------  |   |
| |  Total charged    NGN 1,020.00     |   |
| |                                    |   |
| |  Into the round pool               |   |
| |                          NGN       |   |
| |    1,000.00                        |   |
| |                                    |   |
| |  This is round 4 of 10.            |   |
| |  You are paid in round 9,          |   |
| |  NGN 10,000.00, the base           |   |
| |  pool of 10 members.               |   |
| +------------------------------------+   |
+-- (3) METHOD ----------------------------+
| +------------------------------------+   |
| |  Pay from                          |   |
| |                                    |   |
| |  (o) Bank account                  |   |
| |      ProvidusUnity  0203 000 0003  |   |
| |                                    |   |
| |  ( ) Card                          |   |
| |      Visa, Mastercard, Verve       |   |
| |                                    |   |
| |  AJO.ng never stores your          |   |
| |  bank details. Payment is          |   |
| |  completed on ProvidusUnity's      |   |
| |  page.                             |   |
| +------------------------------------+   |
+-- (4) ACTIONS ---------------------------+
| { Continue to payment }*                 |
| x  This round closes 06 Oct.             |
+-- (5) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** A two-column body: the order summary with its figures on the left, the method and its explanation on the right, and one commit action beneath both. The action is never duplicated in a column header.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) ORDER SUMMARY -----------------------------------------------------+
| Adaeze's Ajo, round 4 of 10. Due 05 Oct 2026.                            |
| You are position 9 of 10 and paid in round 9.                            |
|                                                                          |
| +-----------------------------------------+                              |
| |  What you will be charged               |                              |
| |                                         |                              |
| |  Contribution               NGN 1,000.00|                              |
| |  AJO.ng fee, 2%                  NGN 20.00                             |
| |  --------------------------------------- |                             |
| |  Total charged                NGN 1,020.00                             |
| |                                         |                              |
| |  Of which into the round pool           |                              |
| |                            NGN 1,000.00 |                              |
| |                                         |                              |
| |  You are paid in round 9: NGN 10,000.00,|                              |
| |  the base pool of 10 members.           |                              |
| +-----------------------------------------+                              |
+-- (3) METHOD ------------------------------------------------------------+
| Pay from                                                                 |
|                                                                          |
| (o) Bank account   ProvidusUnity  0203 000 0003                          |
|     Transfer, or a debit to the collection account.                      |
|                                                                          |
| ( ) Card            Visa, Mastercard, Verve                              |
|                                                                          |
| AJO.ng never stores your bank details. The payment is completed on       |
| ProvidusUnity's page and AJO.ng is told the outcome by a                 |
| signature-verified webhook.                                              |
|                                                                          |
| Every payment request carries an Idempotency-Key so a double tap or a    |
| network retry cannot charge twice.                                       |
+-- (4) ACTIONS -----------------------------------------------------------+
| { Continue to payment }*                                                 |
| < Back                                                                   |
|                                                                          |
| This round closes 06 Oct 2026.                                           |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.17.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Amount block', 'Contribution, fee, total charged, and the pool amount.', 'P1', '**Mandatory and fixed: four figures, in this order, with a rule above the total.** CANONICAL.md requires the fee to be shown separately from the contribution on every payment surface. The rule above the total is not decoration; it is what stops the eye reading NGN 1,000.00 as the amount to be charged. The *of which into the round pool* line is what the contribution actually becomes, and it is the first thing a member checks when a receipt says NGN 1,020.00.'],
            ['(2) Round context', 'Which round, how many, and when the member is paid.', 'P1', '*You are paid in round 9, NGN 10,000.00, the base pool.* Stated on the payment screen, not only afterwards, so a member who feels misled has it in front of them at the moment they decide.'],
            ['(3) Method selection', 'Bank account or card, delegating to the provider.', 'P1', "**No card or account number is ever entered on an AJO.ng screen.** PAN, expiry, CVV and bank credentials are captured on ProvidusUnity's hosted page, and AJO.ng receives only a payment reference and an outcome. This is a security requirement, and it is also the only way the collection arrangement in D-02 and D-03 can be correct."],
            ['(4) Provider hand-off', "The transition to the provider's page.", 'P1', 'Announced to a screen reader as a navigation away from AJO.ng, because a silent jump to a differently-branded page is disorienting and looks like a redirect to a fraud site.'],
            ['(5) Idempotency', 'One charge per attempt, enforced by header.', 'P1', '`Idempotency-Key` on `POST /payments`. The button is not disabled on tap alone; the same key is reused for a retry of the same attempt, so a double tap or a reconnect produces one charge.'],
            ['(6) Round closing time', 'When this round stops accepting payment.', 'P1', 'Stated before the action, so a member is not surprised by a payment that lands after the round closed and lands in the next one. What happens in that case is in section 19.'],
            ['(7) No amount editing', 'The amount is not editable on the pay screen.', 'P1', '**Prohibited.** A partial payment or a changed amount on this screen would create a contribution that does not match the schedule every other member is following. Partial payment is not a v1 feature; a member who cannot pay in full is a default-handling case, not a payment-screen case.'],
        ],
        "widths": [0.42, 0.64, 0.42, 5.02],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.18 Payment Processing — SCR-MOB-10'},

    {
        "t": "p",
        "text": 'The waiting state, and the screen people remember worst when something goes wrong. A payment that takes eleven seconds produces an anxious user who taps again, so this screen is designed to make waiting feel like something the system is doing rather than something the person must supervise. It has three outcomes, not one: still working, cannot tell yet, and failed. The middle one is the one that gets skipped in most products and it is the one that matters most, because a payment whose outcome is genuinely unknown is exactly when a person needs to be told the truth rather than shown a spinner forever.',
    },

    {
        "t": "callout",
        "kind": 'WARNING',
        "title": 'Never resolve an UNKNOWN payment optimistically on the client',
        "text": "When a payment webhook has not arrived, the screen must not display a success state derived from the browser's own redirect parameters. CANONICAL.md models this as payment state `UNKNOWN`, and the only transitions out of it are a signed webhook from the provider, a provider status query, or reconciliation. **A client-side success screen for an unconfirmed payment creates a receipt for money that was never collected**, which is a financial record defect and not a display bug. The 6.19 receipt is reachable only from a confirmed `SUCCESS`, from a ledger entry, or from a reconciliation run that has matched the payment.",
    },

    {"t": "h3", "text": '6.18.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) FULL SCREEN -----------------------+
|                                          |
|         AJO.ng                           |
|                                          |
|         Processing payment               |
|                                          |
|         ......................           |
|         (indeterminate)                  |
|                                          |
|         Do not close this screen.        |
|                                          |
|         We will tell you the result      |
|         here and by SMS. You are         |
|         not charged twice if you         |
|         come back.                       |
+-- (2) LATE OUTCOME ----------------------+
|                                          |
|         AJO.ng                           |
|                                          |
|    !   We cannot tell yet                |
|                                          |
|    Your payment is still being           |
|    confirmed by the payment              |
|    partner. This is normal and           |
|    usually takes under a minute.         |
|                                          |
|    { Check again }*                      |
|    < Back to my Ajos                     |
|                                          |
|    Reference  pay_7QK2M9                 |
+-- (3) FAILED OUTCOME --------------------+
|                                          |
|         AJO.ng                           |
|                                          |
|    x   Payment not completed             |
|                                          |
|    Nothing was taken from your           |
|    account. The reason given             |
|    was: insufficient funds.              |
|                                          |
|    Round 4 still closes 06 Oct.          |
|                                          |
|    { Try again }*                        |
|    < Pay a different way                 |
|                                          |
|    Reference  pay_7QK2M9                 |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) FULL SCREEN -------------------------------------------------------+
|                                                                          |
| AJO.ng                                                                   |
|                                                                          |
| Processing payment                                                       |
|                                                                          |
| ....................................                                     |
|                                                                          |
| Do not close this window. We will tell you the result here, by push      |
| and by SMS. You are not charged twice if you come back.                  |
|                                                                          |
| Reference  pay_7QK2M9                                                    |
+-- (2) LATE OUTCOME ------------------------------------------------------+
|                                                                          |
| AJO.ng                                                                   |
|                                                                          |
| !  We cannot tell yet                                                    |
|                                                                          |
| Your payment is still being confirmed by the payment partner. This       |
| is normal and usually takes under a minute.                              |
|                                                                          |
| { Check again }*        < Back to my Ajos                                |
|                                                                          |
| Reference  pay_7QK2M9                                                    |
+-- (3) FAILED OUTCOME ----------------------------------------------------+
|                                                                          |
| AJO.ng                                                                   |
|                                                                          |
| x  Payment not completed                                                 |
|                                                                          |
| Nothing was taken from your account. The reason given was                |
| insufficient funds.                                                      |
|                                                                          |
| Round 4 still closes 06 Oct 2026.                                        |
|                                                                          |
| { Try again }*        < Pay a different way                              |
|                                                                          |
| Reference  pay_7QK2M9                                                    |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.18.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Progress', 'An indeterminate bar plus a sentence about what is happening.', 'P1', '**Indeterminate, and honest about it.** A determinate percentage for a provider hand-off would be invented, and a bar that fills to 100% and then fails is the single most damaging thing this screen could do.'],
            ['(2) Reassurance', 'Do not close; you will be told; you will not be charged twice.', 'P1', 'All three facts are shown before the wait, not after it. The double-charge reassurance is specific because it is the fear: the person is looking at a bank app showing a debited balance.'],
            ['(3) Reference', 'The payment reference, from the moment it exists.', 'P1', "Shown on every state, including the waiting one, because support's first question will be *what is the reference* and the answer should never be *I do not know*."],
            ['(4) Late outcome', 'Outcome genuinely unknown, with a retry.', 'P1', 'Mapped to payment state `UNKNOWN` in CANONICAL.md section 4. The screen says the payment is still being confirmed, **and does not say it succeeded**, and it does not ask the person to try again, because a retry against an unresolved payment is a second charge. Reconciliation closes these, and section 16 covers the timing.'],
            ['(5) Failed outcome', 'Failure with the reason, what was and was not taken, and the deadline.', 'P1', "**States plainly that nothing was taken.** A failure screen that leaves the person guessing about their balance is the fastest route to a bank call. The reason is the provider's reason, in the provider's words, not an AJO.ng paraphrase that could be wrong."],
            ['(6) Pay another way', 'A method switch after failure.', 'P1', 'Available because a failure is often a method problem, not a balance problem. The contribution stays due and the round deadline is restated, so switching methods is time-pressured and clear.'],
            ['(7) Return to the Ajo', 'A way out that is not a cancel.', 'P1', 'The contribution remains payable afterwards, so leaving this screen never leaves the member in a state where they believe they are done.'],
        ],
        "widths": [0.42, 1.08, 0.42, 4.58],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.19 Payment Receipt — SCR-MOB-11'},

    {
        "t": "p",
        "text": 'The proof. It is the document a member keeps, forwards to a group, or shows to an organiser who doubts the payment landed, and it is the artefact a dispute will be argued from, so it is rendered from the ledger postings rather than from the payment row. That is the single most important decision on this screen: a receipt reconstructed from the payment table can show a total that the ledger does not support, and when the two disagree the receipt is what the member trusts.',
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Immutable once issued',
        "text": 'A receipt is not edited. If a posting is found to be wrong, the correction is a reversing entry, which produces a second, correcting receipt that references the first. The original stays in place, which is what makes the history auditable and what CANONICAL.md requires of the ledger. The UI consequence is that there is no edit control on a receipt, and there is no delete control anywhere in the product that touches money.',
    },

    {"t": "h3", "text": '6.19.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| Receipt      pay_7QK2M9                  |
+-- (2) AMOUNT PAID -----------------------+
| +------------------------------------+   |
| |  You paid                          |   |
| |  NGN 1,020.00                      |   |
| |                                    |   |
| |  to AJO.ng, for Adaeze's Ajo,      |   |
| |  round 4 of 10, on 12 Sep 2026.    |   |
| +------------------------------------+   |
+-- (3) BREAKDOWN -------------------------+
| +------------------------------------+   |
| |  What that NGN 1,020.00 is         |   |
| |                                    |   |
| |  Contribution   NGN 1,000.00       |   |
| |                into the round      |   |
| |    pool                            |   |
| |  AJO.ng fee        NGN 20.00       |   |
| |                2% of the           |   |
| |    contribution                    |   |
| |  --------------------------------  |   |
| |  Total charged  NGN 1,020.00       |   |
| +------------------------------------+   |
+-- (4) POOL NOTE -------------------------+
| This round's pool will pay               |
| NGN 10,000.00 to Adaeze B.               |
| The NGN 20.00 stays with                 |
| AJO.ng and is not part of it.            |
+-- (5) ACTIONS ---------------------------+
| < Download PDF >                         |
| < Share >                                |
| < Done >                                 |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) RECEIPT -----------------------------------------------------------+
| RECEIPT                                            pay_7QK2M9            |
|                                                                          |
| Paid by    Segun A.        0703 000 0009                                 |
| Paid on    12 Sep 2026, 09:41 WAT                                        |
| For        Adaeze's Ajo, round 4 of 10                                   |
| Method     Bank transfer, ProvidusUnity  0203 000 0003                   |
|                                                                          |
| +----------------------------------------------------------------+       |
| |  You paid                                    NGN 1,020.00      |       |
| |                                                                |       |
| |  Contribution                     NGN 1,000.00  to the round pool      |
| |  AJO.ng fee, 2%                      NGN 20.00  platform fee    |      |
| |  --------------------------------------------                 |        |
| |  Total charged                      NGN 1,020.00                |      |
| +----------------------------------------------------------------+       |
|                                                                          |
| This round's pool pays NGN 10,000.00 to Adaeze B. The NGN 20.00 fee is   |
| retained by AJO.ng and is not part of that pool. Across the ten rounds   |
|   of                                                                     |
| this Ajo you will have paid NGN 10,200.00 and received NGN 10,000.00.    |
|                                                                          |
| { Download PDF }   { Share }   < Done                                    |
+-- (3) LEDGER LINES ------------------------------------------------------+
| The receipt is rendered from these two postings, not from the payment    |
|   row:                                                                   |
|                                                                          |
|   contribution.received   NGN 1,000.00   to the round pool               |
|   fee.recognised          NGN    20.00   to fees_income                  |
|   payment                 NGN 1,020.00   total charged                   |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.19.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Amount paid', "The total that left the member's account, as a headline.", 'P1', 'NGN 1,020.00, and it is the *paid* amount, not the contribution. Showing NGN 1,000.00 as the headline is the most common way a fee-charging product produces an angry support ticket.'],
            ['(2) Breakdown', 'Contribution, fee, total, each with its destination.', 'P1', '**Mandatory, per the disclosure rule, which names receipts explicitly.** Each of the three lines also states where the money went, so the fee is visibly a platform charge and the contribution is visibly a pool deposit.'],
            ['(3) Pool note', 'What the round pool pays, and that the fee is not in it.', 'P1', 'The round-pool sentence from 6.14, repeated. On a receipt it does different work: the member is looking at NGN 1,020.00 leaving their account, and this is what answers the question they will ask next month.'],
            ['(4) Ajo-level totals', 'What the member will pay across the whole Ajo, and receive.', 'P2', 'NGN 10,200.00 paid across ten rounds, NGN 10,000.00 received. The asymmetry is the product, stated rather than left for the member to discover.'],
            ['(5) Rendered from postings', "The receipt's figures come from the ledger.", 'P1', '**The receipt is a rendering of `ledger_postings`, not of the `payments` row.** A payment row can exist without a matching posting — that is a reconciliation defect — and a receipt that reads from it would show a confirmed payment the ledger has no record of. Where the two disagree, the receipt shows the posting and flags the discrepancy rather than showing the payment.'],
            ['(6) Reference', 'The payment reference, in the header and in the PDF.', 'P1', 'The one string support needs. Present in the shareable text as well, so a receipt pasted into a group chat is still traceable.'],
            ['(7) Download and share', 'PDF and a share sheet.', 'P1', 'The shared version is plain text plus the reference, because a group chat on a phone is where receipts actually go, and an image in a chat thread cannot be searched later.'],
        ],
        "widths": [0.42, 0.82, 0.42, 4.84],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.20 Payouts — SCR-MOB-12'},

    {
        "t": "p",
        "text": "The screen a member works towards, and the one where the fee model either reads as fair or does not. It shows what is coming, what has been received, and the reasoning behind every amount, including the one that separates what the round collected from what the recipient gets. The held state is designed as a first-class screen state rather than an error, because holding a payout is a decision the product makes on the member's behalf and a member who cannot see why will assume the worst.",
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Payout amounts are never computed in the client',
        "text": "A payout amount shown on this screen is read from the `payouts` row, which is written from the round's contribution postings. The client does not sum the round, does not apply the 2% fee, and does not round. The reason is not defensiveness about client bugs: a client that recomputes a payout can display a number the ledger has never agreed to, and the difference between what a member was shown and what they were paid is the definition of a dispute. The same rule applies to every other amount in the product: the client displays, the server decides.",
    },

    {"t": "h3", "text": '6.20.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| Payouts                                  |
+-- (2) UPCOMING --------------------------+
| +------------------------------------+   |
| |  Coming up                         |   |
| |                                    |   |
| |  Adaeze's Ajo, round 1             |   |
| |  Friday 19 Sep                     |   |
| |                                    |   |
| |  You receive                       |   |
| |  NGN 10,000.00                     |   |
| |                                    |   |
| |  The base pool: 10 members         |   |
| |  at NGN 1,000.00.                  |   |
| |                                    |   |
| |  Each member also paid             |   |
| |  NGN 20.00 to AJO.ng. That is      |   |
| |  not part of your payout.          |   |
| +------------------------------------+   |
+-- (3) HISTORY ---------------------------+
| Chima's Ajo, round 2                     |
| 12 Sep  NGN 10,000.00  released          |
| 12 Sep  received to 0203 000 0003        |
|                                          |
| Adaeze's Ajo, round 1                    |
| 19 Aug  NGN 10,000.00  released          |
+-- (4) HELD STATE ------------------------+
| +------------------------------+         |
| |  ! Payout on hold            |         |
| |                              |         |
| |  Chima's Ajo, round 4        |         |
| |                              |         |
| |  NGN 10,000.00 is owed to    |         |
| |  Segun A. but the round has  |         |
| |  not fully collected.        |         |
| |                              |         |
| |  AJO.ng will not reduce the  |         |
| |  amount and will not use its  |        |
| |  own funds to cover it.      |         |
| |                              |         |
| |  Recovery is in progress.    |         |
| |  We will tell you the result |         |
| |  either way.                 |         |
| |                              |         |
| |  { What happens next > }     |         |
| +------------------------------+         |
+-- (5) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) UPCOMING ----------------------------------------------------------+
| Adaeze's Ajo, round 1, due Friday 19 Sep 2026                            |
|                                                                          |
| You receive  NGN 10,000.00  the base pool, 10 members at NGN 1,000.00    |
|                                                                          |
| Each member has separately paid AJO.ng a NGN 20.00 fee. That fee is not  |
| part of the pool and is not deducted from your payout.                   |
+-- (3) PAYOUT TABLE ------------------------------------------------------+
| AJO              ROUND  DUE       AMOUNT         STATE      SETTLED      |
| Adaeze's Ajo     1      19 Sep    NGN 10,000.00  SCHEDULED  -            |
| Chima's Ajo      4      05 Oct    NGN 10,000.00  HELD       -            |
| Chima's Ajo      2      12 Sep    NGN 10,000.00  SUCCESS    12 Sep       |
| Adaeze's Ajo     1      19 Aug    NGN 10,000.00  SUCCESS    19 Aug       |
+-- (4) HELD EXPLANATION --------------------------------------------------+
| Why a payout is HELD                                                     |
|                                                                          |
| Chima's Ajo, round 4 owes Segun A. NGN 10,000.00. The round has not      |
| collected in full, so the payout is not released.                        |
|                                                                          |
| AJO.ng will not reduce the amount and will not use its own money to      |
| cover the gap. The round enters the recovery process and every member    |
| is told what is happening.                                               |
|                                                                          |
| The alternative, quietly paying a smaller amount, is the failure this    |
| product exists to avoid.                                                 |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.20.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Upcoming payout', 'The next round in which this member is paid, and the amount.', 'P1', 'The amount is named *the base pool* and the derivation *10 members at NGN 1,000.00* is shown beneath it, so the figure is never a bare number that has to be compared against something else later.'],
            ['(2) Fee-not-in-pool sentence', 'States that the per-member fee is not part of the payout.', 'P1', '**Mandatory, and repeated from 6.14 and 6.19.** A member seeing NGN 10,200.00 collected and NGN 10,000.00 paid is owed an explanation on the screen where the payout is, not in a help centre.'],
            ['(3) Payout state', 'SCHEDULED, FUNDING, RELEASED, SUCCESS, FAILED, HELD.', 'P1', 'The CANONICAL.md payout states, in title case. `FUNDING` and `RELEASED` are separated in the data because they are separated in the ledger, and collapsing them in the UI would make a released-but-unsettled payout look complete.'],
            ['(4) Settlement target', "When a SUCCESS payout reached the member's account.", 'P1', "Shown only once settled. Before settlement the column reads the provider's expected timing as an estimate, and **the estimate is attributed to the payment partner rather than promised by AJO.ng**, because D-03 is unresolved."],
            ['(5) Bank account', 'Where the money goes.', 'P1', 'Masked to the last four digits, as `0203 *** ***3`. The full account number is never shown after it has been saved, because the screens that display it are the screens most likely to be photographed.'],
            ['(6) Held state', 'An under-collected round and what happens instead.', 'P1', "**The held state says three things: the amount is not reduced, AJO.ng's own funds are not used, and the member will be told the outcome.** CANONICAL.md is explicit that a payout must not be silently reduced and corporate funds must not be used, and a member who is waiting for money needs to know the product will not invent it."],
            ['(7) What happens next', 'The recovery process, in plain terms.', 'P1', 'Links to the default-handling explanation. The sequence CANONICAL.md fixes — reminder, retry, 48-hour grace, organiser notified, member contacted, default recorded, recovery — is written for members as well as for the risk team.'],
            ['(8) Failed payout', 'A settlement failure and the retry.', 'P1', "Shown as a distinct state from HELD, with the provider's reason and the fact that a retry is automatic. A failed settlement that is not distinguishable from a hold would leave a member thinking their money is gone."],
        ],
        "widths": [0.43, 0.92, 0.42, 4.73],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.21 Transactions and Statement — SCR-MOB-14'},

    {
        "t": "p",
        "text": "The person's own money, in full, in order, with no grouping tricks. This screen replaces the single line *NGN 1,020.00* that most apps would show, because the two rows underneath it are the platform's fee and the platform's own contribution to the pool, and a member who wants to know what AJO.ng took is entitled to see it itemised rather than summed. The statement is the same data with a date range, and it is the artefact people export at the end of an Ajo.",
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Why the fee row is visible and the payment row is also visible',
        "text": 'Showing both the NGN 1,020.00 payment and its NGN 1,000.00 and NGN 20.00 components means the same money appears twice in a list, which is counter-intuitive if you are not reading carefully. The alternative, showing only the two components, hides the amount that actually left the bank account, and a member comparing that with their statement cannot reconcile it. Both are shown, and the payment row is visually subordinate: it carries the reference and the total, and the component rows carry the detail. The period summary resolves the apparent double count by stating that the fee is *part of* the total charged rather than additional to it.',
    },

    {"t": "h3", "text": '6.21.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| Transactions                             |
|                                          |
| Adaeze's Ajo  All  <                     |
+-- (2) GROUP -----------------------------+
| 12 Sep 2026                              |
|   NGN 1,020.00  paid  round 4   >        |
|   NGN   20.00  fee  round 4     >        |
| 05 Sep 2026                              |
|   NGN 10,000.00  received  round 2  >    |
| 29 Aug 2026                              |
|   NGN 1,020.00  paid  round 3   >        |
+-- (3) STATEMENT -------------------------+
| September 2026                           |
| In   NGN 10,000.00                       |
| Out  NGN 1,040.00                        |
| Fee paid  NGN 40.00                      |
|                                          |
| Out is the total charged,                |
| NGN 1,020.00 x 2. The fee                |
| is part of it, not extra.                |
+-- (4) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) FILTERS -----------------------------------------------------------+
| All                                                                      |
| Money in                                                                 |
| Money out                                                                |
| Fees                                                                     |
| This month                                                               |
| Custom range                                                             |
+-- (3) LEDGER TABLE ------------------------------------------------------+
| DATE     AJO            REF      TYPE          IN         OUT            |
| 12 Sep   Adaeze's Ajo   rcpt_1   contribution   -        1,000.00        |
| 12 Sep   Adaeze's Ajo   fee_1    platform fee   -           20.00        |
| 12 Sep   Adaeze's Ajo   pay_7QK  payment        -        1,020.00        |
| 05 Sep   Chima's Ajo    pyt_9KL  payout         10,000.00  -             |
| 29 Aug   Adaeze's Ajo   pay_4TR  payment        -        1,020.00        |
|                                                                          |
| The payment row and its two postings are all listed. A member sees the   |
| breakdown of their own charge, not a collapsed single line.              |
+-- (4) PERIOD SUMMARY ----------------------------------------------------+
| September 2026                                                           |
|                                                                          |
| In            NGN 10,000.00   one payout received                        |
| Out           NGN  2,040.00   two payments charged                       |
| Of which fee  NGN     40.00   NGN 20.00 per payment                      |
| Net           NGN  7,960.00                                              |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.21.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Filters', 'Direction, fee-only, and a date range.', 'P1', 'A **fees-only** filter exists. It is the fastest way for a member to answer *how much did AJO.ng take*, and a product whose fee is 2% should not make that question hard.'],
            ['(2) Grouping by day', 'Date headings with the movements under them.', 'P1', 'Grouped by date rather than by Ajo, because a person checking a payment is looking for a moment, not for a project.'],
            ['(3) Itemised breakdown', 'A payment is shown as its contribution and fee rows.', 'P1', '**The payment row and both of its postings are listed, not collapsed.** On a screen the member uses to reconcile their own balance, a collapsed total is an unexplained number. The interface matches the ledger, and the ledger recognition sequence in CANONICAL.md is what makes the two rows possible in the first place.'],
            ['(4) Direction and sign', 'In and out, never a signed number alone.', 'P1', 'A `+NGN 1,020.00` is ambiguous: it can read as *you received this*. Direction is a separate labelled column or a labelled row, and the fee row is always an outflow.'],
            ['(5) Period summary', 'In, out, of which fee, and net for the period.', 'P1', 'The fee is a line in the summary, not a footnote. The net figure follows from the other three and is shown for completeness rather than as the headline.'],
            ['(6) Reference', 'The posting, receipt or payment reference per row.', 'P1', 'Every row is traceable to a reference that support can look up, and every row is a route into the detail behind it.'],
            ['(7) Export', 'Statement as PDF and CSV.', 'P2', "A CSV of one's own transaction history is a reasonable request from anyone running a group, and refusing it invites the manual spreadsheet that support then fields questions about."],
        ],
        "widths": [0.42, 0.85, 0.42, 4.81],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.22 Notifications — SCR-MOB-15'},

    {
        "t": "p",
        "text": 'The inbox for everything the system tells a person, and the place where the notification catalogue in CANONICAL.md section 8 becomes visible. The screen is deliberately boring: no grouping by type, no clever digest, no promotional category. Every row is an event that happened to this person, and the channel policy is shown on the screen because a person who expects money news by SMS and does not get it will assume the product is broken.',
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Notification preferences do not allow opting out of money or security alerts',
        "text": 'A person may turn off marketing-adjacent categories, and `contribution.due` carries an SMS opt-in because the catalogue marks it optional. Money-critical and security events — `payout.released`, `payout.failed`, `payout.held`, `account.frozen`, `security.login_new_device` — cannot be switched off, because a savings product that lets you stop telling you it cannot pay you has a different product than the one described in CANONICAL.md. The preference screen says which categories are fixed and why, rather than rendering a disabled toggle with no explanation.',
    },

    {"t": "h3", "text": '6.22.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| Notifications                            |
|                                          |
| Mark all read                            |
+-- (2) TODAY -----------------------------+
| !  Round 4 opens 05 Oct, 7 of 10         |
|    paid.  09:41                          |
| !  Your payment of NGN 1,020.00 was      |
|    received.  09:41                      |
|    View receipt  >                       |
+-- (3) EARLIER ---------------------------+
|    Your turn in Chima's Ajo is           |
|    round 10. NGN 10,000.00.              |
|    05 Sep                                |
|    Fatima S. joined Adaeze's Ajo.        |
|    28 Aug                                |
+-- (4) CHANNEL NOTE ----------------------+
| Money and security alerts also go by     |
| SMS. The other 15 do not, and never      |
| will: SMS is reserved.                   |
+-- (5) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) LIST --------------------------------------------------------------+
| STATE   WHEN   EVENT                     MESSAGE                         |
| unread  12 Sep  contribution.due        Round 4 opens 05 Oct, 7 of 10.   |
| unread  12 Sep  contribution.received   Payment NGN 1,020.00 received.   |
| read    12 Sep  payout.released          Payout released NGN 10,000.00.  |
| read    05 Sep  payout.upcoming          Your turn, round 10, NGN        |
|   10,000.                                                                |
| read    28 Aug  member.joined            Fatima S. joined the Ajo.       |
| read    20 Aug  security.login_new_dev   New sign-in, new device.        |
|                                                                          |
| unread is a dot and a word, never a colour alone.                        |
+-- (3) CHANNEL MATRIX ----------------------------------------------------+
| Event                  Push  Email  SMS                                  |
| contribution.due       yes   yes    opt                                  |
| contribution.received  yes   yes    opt                                  |
| payout.released        yes   yes    yes                                  |
| payout.held            yes   yes    yes                                  |
| account.frozen         yes   yes    yes                                  |
| member.joined          yes   yes    no                                   |
| ajo.completed          yes   yes    no                                   |
|                                                                          |
| SMS is reserved for money-critical and security events.                  |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.22.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) List', 'Every notification for this person, newest first.', 'P1', 'Rows are events, in the CANONICAL.md catalogue, and the event name is available to a screen reader. A member who is told *you have an update* cannot act; a member told *round 4 opens 05 Oct* can.'],
            ['(2) Unread state', 'A dot plus the word *unread* to a screen reader.', 'P1', 'Never colour alone. The unread count on the bell is capped and labelled, and Mark all read is per person, never global.'],
            ['(3) Money rows', 'Amounts as the member experienced them.', 'P1', 'A payment-received row shows NGN 1,020.00, the amount charged, and a route to the receipt. A payout row shows NGN 10,000.00, the amount received. The two amounts are never interchangeable, which is why they are never routed from the same notification type.'],
            ['(4) Deep links', 'Every actionable row routes to the thing it describes.', 'P1', '`contribution.due` goes to the pay screen, `payout.released` to the payout detail. A notification that must be acted on somewhere else is a notification that gets missed.'],
            ['(5) Channel policy', 'What goes by SMS and what does not.', 'P1', 'CANONICAL.md reserves SMS for money-critical and security events. Stating it prevents the common failure of a member waiting for an SMS that was never going to be sent.'],
            ['(6) Event identifier', 'The canonical event name per row.', 'P2', 'Rendered small and secondary. It is there so a member reporting a missing alert can quote something precise, which support otherwise has to reconstruct from a timestamp.'],
            ['(7) Retention', 'How long notifications are kept.', 'P2', 'Ninety days in the product, stated in the privacy material. Notifications are a convenience record, not an accounting record; the ledger is the accounting record.'],
        ],
        "widths": [0.42, 1.04, 0.42, 4.62],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.23 Disputes — SCR-MOB-16'},

    {
        "t": "p",
        "text": "The list of a person's own disputes, and the boundary of what a dispute can do, stated on the screen rather than discovered in one. A dispute is the one route by which a member can stop a step without withdrawing from the product, so it has to feel available rather than escalatory. The screen says what a dispute pauses and what it does not, because a member who believes raising one will return their money immediately will raise four of them.",
    },

    {"t": "h3", "text": '6.23.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| Support                                  |
|                                          |
| Disputes                                 |
+-- (2) OPEN DISPUTE ----------------------+
| +------------------------------------+   |
| |  Open disputes 1                   |   |
| |                                    |   |
| |  Round 2, NGN 1,000.00             |   |
| |  Chima's Ajo                       |   |
| |                                    |   |
| |  Waiting on AJO.ng                 |   |
| |  Opened 10 Sep                     |   |
| |                                    |   |
| |  > see the thread                  |   |
| +------------------------------------+   |
+-- (3) CLOSED ----------------------------+
| Closed 2                                 |
| Round 1  resolved  01 Aug                |
| Round 3  withdrawn  28 Jul               |
+-- (4) EXPLANATION -----------------------+
| A dispute pauses the ledger, it does     |
| not move money. Either party may         |
| raise one. See what we can and           |
| cannot do  >                             |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) DISPUTE TABLE -----------------------------------------------------+
| REF     AJO            SUBJECT            STATE     AGE                  |
| dsp_4Q7 Chima's Ajo    round 2 not paid   AWAITING  2d                   |
| dsp_9KX Adaeze's Ajo   payout order       RESOLVED  31d                  |
| dsp_2WT Adaeze's Ajo   wrong round        CLOSED    44d                  |
+-- (3) WHAT A DISPUTE DOES -----------------------------------------------+
| A dispute records a disagreement and freezes the affected step.          |
| It does not move money, does not reverse a settled payout by itself,     |
| and does not delete anything.                                            |
|                                                                          |
| Neither party can withdraw a dispute that has reached a decision.        |
| A withdrawal before a decision is allowed and is recorded.               |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.23.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Open disputes', 'Everything unresolved, with who is waiting on whom.', 'P1', '*Waiting on AJO.ng* and *waiting on the other party* are different states and are shown differently, because the first is a commitment the platform owes and the second is not.'],
            ['(2) Reference', 'A stable dispute reference per row.', 'P1', '`dsp_` plus an opaque suffix, quoted in support. Without it, a member describing *the one about round 2* is describing one of several.'],
            ['(3) Subject', 'What the disagreement is about, in one line.', 'P1', 'Chosen by the person from a short list at creation, then editable. A subject line is what makes a list of disputes navigable, and an editable one is what keeps it honest.'],
            ['(4) Age', 'How long it has been open.', 'P1', 'Ages beyond the published response time are shown, because an unacknowledged age is worse than an acknowledged one.'],
            ['(5) Scope statement', 'What a dispute does and does not do.', 'P1', '**Mandatory.** A dispute freezes an affected step and records a disagreement. It does not move money, does not by itself reverse a settled payout, and does not delete a record. Saying this on the list screen, before anyone creates one, is cheaper than saying it in every dispute.'],
            ['(6) Withdraw', 'Available only before a decision.', 'P1', 'A dispute that has reached a decision cannot be withdrawn, because the decision and its reasoning are on the record and both parties have relied on them.'],
            ['(7) New dispute', 'The creation route, present on the list and on the affected screen.', 'P1', 'Offered from the Ajo, the contribution and the payout screens as well as from here, so the context that triggered it is still on screen.'],
        ],
        "widths": [0.42, 1.17, 0.42, 4.49],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.24 New Dispute — SCR-MOB-17'},

    {
        "t": "p",
        "text": 'Three short steps that turn a grievance into something the platform can act on. The design problem here is not the form, it is calibration: a dispute that is easy to raise and hard to act on produces a queue of feelings rather than a queue of facts. So the subject is a closed list, the affected contribution or payout is picked rather than described, and the screen says up front what the platform can and cannot do once a dispute exists.',
    },

    {
        "t": "callout",
        "kind": 'LEGAL',
        "title": "Disputes are not a substitute for the provider's chargeback process",
        "text": "A dispute raised here is an internal platform process. It is not a chargeback, and it does not by itself reverse a settled payout. If a member's actual complaint is that a bank debited them and the money never arrived, that is a matter for the acquiring bank and, where relevant, for ProvidusUnity's own process. The refund SLA after a provider approves a reversal is open decision D-07 and is unresolved. **The product must not represent a dispute as a route to a chargeback, and no screen may state or imply a refund timeframe that has not been confirmed with the provider and reviewed by qualified Nigerian legal counsel.**",
    },

    {"t": "h3", "text": '6.24.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) STEP 1 ----------------------------+
| What is this about?                      |
|                                          |
| (o) A contribution I was charged         |
|     for and did not expect               |
|                                          |
| ( ) A payout I did not receive           |
|                                          |
| ( ) The payout order                     |
|                                          |
| ( ) Something else                       |
+-- (2) STEP 2 ----------------------------+
| +------------------------------------+   |
| |  Which Ajo and which round?        |   |
| |                                    |   |
| |  Adaeze's Ajo                      |   |
| |  Round 4, due 05 Oct, NGN          |   |
| |    1,000.00                        |   |
| |                                    |   |
| |  Charged 12 Sep 2026               |   |
| |  Reference pay_7QK2M9              |   |
| +------------------------------------+   |
+-- (3) STEP 3 ----------------------------+
| +------------------------------------+   |
| |  Tell us what happened             |   |
| |                                    |   |
| |  [                              ]  |   |
| |  [                              ]  |   |
| |  [                              ]  |   |
| |                                    |   |
| |  What you would like to happen:    |   |
| |  [                              ]  |   |
| |                                    |   |
| |  What we can do: refund, correct   |   |
| |    a                               |   |
| |  record, or explain. We cannot     |   |
| |    move                            |   |
| |  money outside these.              |   |
| +------------------------------------+   |
+-- (4) EVIDENCE --------------------------+
| + Add a receipt, screenshot or note      |
|                                          |
| 0 of 5 files, up to 10 MB each           |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) STEP 1: SUBJECT ---------------------------------------------------+
| What is this about?                                                      |
|                                                                          |
| (o) A contribution I was charged for and did not expect                  |
| ( ) A payout I did not receive                                           |
| ( ) The payout order                                                     |
| ( ) Something else                                                       |
|                                                                          |
| Choose the closest one. You can add detail in step 3.                    |
+-- (2) STEP 2 AND 3 ------------------------------------------------------+
| Adaeze's Ajo, round 4, due 05 Oct 2026, NGN 1,000.00                     |
| Charged 12 Sep 2026. Reference pay_7QK2M9.                               |
|                                                                          |
| Tell us what happened, and what you would like to happen.                |
|                                                                          |
| + Add a receipt, screenshot or note        0 of 5 files, up to 10 MB     |
|   each                                                                   |
|                                                                          |
| What we can do: refund, correct a record, or explain. We cannot move     |
|   money                                                                  |
| outside these. A dispute pauses the affected step; it does not delete a  |
| record, and it does not by itself reverse a settled payout.              |
|                                                                          |
| { Submit dispute }*                                                      |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.24.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Subject list', 'Four choices, radio, one required.', 'P1', 'A closed list rather than free text, because the subject determines which team and which review path the dispute takes, and free-text subjects produce a third of everything. *Something else* keeps the list from being a wall.'],
            ['(2) Affected item', 'The specific Ajo, round, and reference.', 'P1', "**Picked from the person's own records, never typed.** A dispute about *round 4 of Adaeze's Ajo, reference pay_7QK2M9* can be actioned; a dispute about *my money* cannot."],
            ['(3) What happened', 'Free text, with a minimum length to encourage detail.', 'P1', 'The minimum is a real constraint, not a bureaucratic one: a three-word dispute cannot be assessed, and the person raising it is the only source of the facts.'],
            ['(4) What you would like', 'The requested outcome, as text.', 'P1', 'Asked separately from what happened, because the two are different and conflating them produces a dispute that asks for a refund when what was wanted was an explanation.'],
            ['(5) Evidence', 'Up to five files, 10 MB each, with a stated limit.', 'P1', 'Receipts and screenshots are the most common evidence, and the person already has the receipt in the app, so the picker opens there first.'],
            ['(6) Capability statement', 'What a dispute can achieve.', 'P1', '**Mandatory, and repeated from 6.23.** Refund, correct a record, or explain. A dispute cannot move money outside those, cannot delete a record, and cannot by itself reverse a settled payout. Setting that expectation at creation is the difference between a fair process and an unanswerable complaint.'],
            ['(7) No deadline pressure', 'No countdown, no urgency language.', 'P1', 'The platform is under no time pressure and must not manufacture any. The only time reference given is the published response time, stated as an expectation rather than a promise.'],
        ],
        "widths": [0.42, 0.9, 0.42, 4.76],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.25 Dispute Thread — SCR-MOB-18'},

    {
        "t": "p",
        "text": "The conversation, and the record, in one place. A dispute is the only surface in the product where two parties and the platform appear together, and the temptation is to build a chat. It is not a chat: it is an append-only record with support replies, member replies, and a written account of what the dispute did to the ledger. The distinction matters because a chat implies conversational intimacy that a financial record should not have, and because a member's most important question — what actually happened to my money — is answered by the ledger effect, not by the last message.",
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'A thread is a record, not a conversation',
        "text": "The visual treatment is a message list because that is what members understand, but every element of it is a record: timestamps are immutable, messages cannot be edited, the platform's replies are attributed to the organisation rather than an individual, and the dispute is closed only with a written outcome. Building it as a live chat with typing indicators or message deletion would misrepresent what the platform is doing, and would give members a reasonable expectation of a response that the process does not promise.",
    },

    {"t": "h3", "text": '6.25.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| dsp_4Q7                                  |
| Open                                     |
| Chima's Ajo                              |
+-- (2) SUMMARY ---------------------------+
| +------------------------------------+   |
| |  I was charged NGN 1,020.00        |   |
| |  for round 2 and the receipt       |   |
| |  says paid, but the round          |   |
| |  shows 9 of 10 and I have          |   |
| |  no record of it.                  |   |
| +------------------------------------+   |
+-- (3) THREAD ----------------------------+
| 12 Sep  AJO.ng                           |
|   Thanks. We can see the                 |
|   payment and the posting.               |
|   We are checking which                  |
|   round it was applied to.               |
|                                          |
| 12 Sep  Chima O.                         |
|   It is not in my history                |
|   at all.                                |
|                                          |
| 12 Sep  AJO.ng                           |
|   Confirmed: applied to                  |
|   round 3 by mistake. We                 |
|   are correcting it. No                  |
|   refund is due to you.                  |
|                                          |
| x  Chima O.  I would still               |
|    like my money back.                   |
+-- (4) COMPOSER --------------------------+
| [ Write a message            ]           |
| { Send }*                                |
+-- (5) DISCLAIMER ------------------------+
| A dispute does not move money.           |
| It does not delete records.              |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) THREAD ------------------------------------------------------------+
| dsp_4Q7   Chima's Ajo, round 2   STATE: AWAITING MEMBER   AGE 2d         |
|                                                                          |
| SUBJECT   I was charged NGN 1,020.00 for round 2, the receipt says       |
|           paid, the round shows 9 of 10, and I have no record of it.     |
|                                                                          |
| 12 Sep 09:52  AJO.ng (support)                                           |
|   Thanks. We can see the payment and the posting. We are checking        |
|   which round it was applied to.                                         |
|                                                                          |
| 12 Sep 10:14  Chima O. (member)                                          |
|   It is not in my history at all.                                        |
|                                                                          |
| 12 Sep 11:03  AJO.ng (support)                                           |
|   Confirmed: applied to round 3 by mistake. We are correcting it.        |
|   No refund is due to you.                                               |
|                                                                          |
| 12 Sep 11:30  Chima O. (member)                                          |
|   I would still like my money back.                                      |
|                                                                          |
| LEDGER EFFECT   Round 2 obligation reinstated. Round 3 contribution      |
|                 released from the original member and reassigned.        |
|                 A reversing entry was posted. Nothing was deleted.       |
+-- (3) COMPOSER ----------------------------------------------------------+
| A dispute does not move money. It does not delete records, and it does   |
|   not                                                                    |
| by itself reverse a settled payout. Refunds are made by decision and the |
| reasoning is recorded either way.                                        |
|                                                                          |
| [ Write a message                                       ]                |
| { Send }*                                                                |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.25.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Reference and state', 'Reference, affected item, and who is waiting.', 'P1', '*Waiting on AJO.ng* and *waiting on you* are visibly different, because the second is an action the member can take and the first is not.'],
            ['(2) Original statement', 'What the member wrote, in full, unedited.', 'P1', 'Editable by the member only until a support reply exists, after which it is fixed. A grievance that can be edited after it has been answered is a grievance with no record.'],
            ['(3) Thread', 'Interleaved messages, member and platform, timestamped.', 'P1', 'Read-only for the platform after sending, which is a chat convention and a records convention at once. Support cannot edit or delete a sent message.'],
            ['(4) Speaker attribution', 'Who sent each message, and in what capacity.', 'P1', "*AJO.ng (support)*, not a person's first name, because a support reply in a financial record should be attributable to the organisation and not appear to be a friend typing."],
            ['(5) Ledger effect', 'What the dispute changed, or that it changed nothing.', 'P1', '**Mandatory on the screen.** The plain-language account of the ledger consequence — an obligation reinstated, a contribution reassigned, a reversing entry posted, nothing deleted — is what a member actually needs and what support otherwise has to translate from a database diff on every call.'],
            ['(6) Composer', 'A message box, available until the dispute is decided.', 'P1', 'Disabled, with the reason stated, after a decision. A member who can keep typing into a decided dispute reasonably believes it is still open.'],
            ['(7) Scope restatement', 'The capability statement, kept on the thread.', 'P1', 'Repeated from 6.23 and 6.24. A thread is where a member decides whether to escalate to a bank, and the honest limits of the internal process are more useful there than a reassurance.'],
            ['(8) No resolve-without-answer', 'A dispute cannot be closed without a written outcome.', 'P1', '**Prohibited.** Every dispute reaches one of: resolved with an action, resolved with an explanation and no action, or withdrawn before a decision. There is no close-without-reasoning state.'],
        ],
        "widths": [0.49, 0.93, 0.42, 4.66],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.26 Profile — SCR-MOB-19'},

    {
        "t": "p",
        "text": 'The person, their verification state, and their financial summary. The summary is the part that matters, and it is the part most likely to be assembled wrongly: the number that matters to a member is not what they have paid, it is what they are owed and what they are being charged right now. The lifetime figures come after, with the reconciliation sentence that stops the difference between charged and received from reading as a loss.',
    },

    {"t": "h3", "text": '6.26.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| Profile                                  |
|                                          |
| Edit                                     |
+-- (2) IDENTITY --------------------------+
| +------------------------------------+   |
| |  Segun A.                          |   |
| |  0703 000 0009                     |   |
| |  seg***@gmail.com                  |   |
| |                                    |   |
| |  email    done                     |   |
| |  phone    done                     |   |
| |  identity not done                 |   |
| +------------------------------------+   |
+-- (3) FINANCIAL SUMMARY -----------------+
| +------------------------------------+   |
| |  In AJO.ng                         |   |
| |                                    |   |
| |  Ajos joined     3                 |   |
| |  Owed to you  NGN 10,000.00        |   |
| |  You owe        NGN 1,000.00       |   |
| |  Charged           NGN 20.00 fee   |   |
| |                                    |   |
| |  Lifetime paid  NGN 40,620.00      |   |
| |  Lifetime received  NGN 20,000.00  |   |
| |                                    |   |
| |  Difference is AJO.ng's fee and    |   |
| |  the 10,000.00 you are still       |   |
| |  owed, not a loss.                 |   |
| +------------------------------------+   |
+-- (4) ACTIONS ---------------------------+
| < Edit profile >                         |
| < My Ajos >                              |
| < Transactions >                         |
| < Security >                             |
| < Notifications >                        |
+-- (5) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) IDENTITY ----------------------------------------------------------+
| Segun A.   0703 000 0009   seg***@gmail.com                              |
|                                                                          |
| Verification   email   done 12 Aug 2026                                  |
| Verification   phone   done 12 Aug 2026                                  |
| Verification   identity  not started                                     |
+-- (3) FINANCIAL SUMMARY -------------------------------------------------+
| +-----------------------------------------------------------------+      |
| |  In AJO.ng                                                     |       |
| |                                                                 |      |
| |  Ajos joined                        3                          |       |
| |  Owed to you                        NGN 10,000.00              |       |
| |  You owe                            NGN 1,000.00               |       |
| |  Of which AJO.ng fee                     NGN 20.00              |      |
| |                                                                 |      |
| |  Lifetime charged                  NGN 40,620.00               |       |
| |  Lifetime received                 NGN 20,000.00               |       |
| |  Lifetime fee paid                    NGN 812.40              |        |
| |                                                                 |      |
| |  The difference between charged and received is the platform fee |     |
| |  plus NGN 10,000.00 still owed to you, not a loss.               |     |
| +-----------------------------------------------------------------+      |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.26.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Identity', 'Name, masked phone, masked email, and verification state per method.', 'P1', 'Verification is shown as three named methods with their own states, not as a single progress bar, because identity verification is optional under open decision D-04 and a bar would imply a requirement that may not exist.'],
            ['(2) Current position', 'Ajos joined, owed to you, you owe, and the fee inside that.', 'P1', '**The fee is named as a component of what is owed, not as an extra.** *You owe NGN 1,000.00, of which NGN 20.00 is the AJO.ng fee* is one sentence that prevents the recurring misunderstanding.'],
            ['(3) Lifetime totals', 'Charged, received, and fee paid, all three.', 'P1', '**All three or none.** Showing charged and received without fee is a chart of a loss. Showing fee alone, without charged and received, is a receipt.'],
            ['(4) Reconciliation sentence', 'Explains the difference between charged and received.', 'P1', "**Mandatory.** The difference is the platform's fee plus money still owed to this member, and it is stated in words on the profile rather than left for a member to infer from arithmetic."],
            ['(5) Masking', 'Phone and email masked by default, with a reveal action.', 'P1', 'Masked because a profile is the screen most likely to be shared, and revealed only behind a deliberate action because a member checking their own email deserves to be able to.'],
            ['(6) Editing', 'Name, phone and email, each with its own consequence.', 'P1', 'Changing a phone number re-verifies it and re-triggers the OTP. Changing an email re-verifies it. Neither touches membership, position or any settled record.'],
            ['(7) No avatar requirement', 'An avatar is optional and has no default face.', 'P1', 'A default avatar is a small lie about who is in the group, so an account with no avatar shows initials or nothing at all.'],
        ],
        "widths": [0.54, 1.37, 0.42, 4.17],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.27 Security — SCR-MOB-21'},

    {
        "t": "p",
        "text": 'Password, devices, and the two features that protect an account holding money. The design constraint is that the person reading it may be doing so *because* something looks wrong, so the order is: what is signed in, what has happened, what to do. Two-factor is optional and the screen says so, because a mandatory step people cannot complete is worse than an absent one.',
    },

    {
        "t": "callout",
        "kind": 'DECISION',
        "title": 'SMS two-factor, and what is not offered at launch',
        "text": "Two-factor at launch is an SMS code to the already-verified phone number. TOTP with an authenticator app, hardware keys and passkeys are all better and none are offered, because each needs a recovery design that does not exist yet. The trade-off is real: SMS is the weakest of the three, and it is vulnerable to SIM swap, which is a documented and practical attack in Nigeria. The mitigations are that the factor is optional, that a new-factor enrolment sends `security.login_new_device` by push and email so a swap is visible, and that the platform's own OTP flow already proves number possession at registration. **An authenticator app is planned for the first post-launch iteration, and until it exists the screen must not describe SMS 2FA as strong.** Requires confirmation of the provider's number-ownership assurance position with ProvidusUnity.",
    },

    {"t": "h3", "text": '6.27.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| Security                                 |
|                                          |
| Your account                             |
+-- (2) PASSWORDS -------------------------+
| +------------------------------------+   |
| |  Password                          |   |
| |  Last changed 3 months ago         |   |
| |                                    |   |
| |  [ Change password ]*              |   |
| |                                    |   |
| |  You have 1 account linked to      |   |
| |  this number.                      |   |
| +------------------------------------+   |
+-- (3) SESSIONS --------------------------+
| +------------------------------------+   |
| |  Signed in on                      |   |
| |                                    |   |
| |  (o) This phone                    |   |
| |      Lagos, Nigeria, now           |   |
| |                                    |   |
| |  ( ) Laptop                        |   |
| |      Lagos, Nigeria, 11 Sep        |   |
| |                                    |   |
| |  { Sign out this device }          |   |
| +------------------------------------+   |
+-- (4) SECURITY ALERTS -------------------+
| +------------------------------------+   |
| |  ! New sign-in from a new device   |   |
| |    20 Aug, 21:14, Chrome, Lagos    |   |
| |                                    |   |
| |    If that was not you, change     |   |
| |    your password and sign out      |   |
| |    everywhere.                     |   |
| +------------------------------------+   |
+-- (5) TWO-FACTOR ------------------------+
| Two-factor is not on.                    |
| Turning it on needs a phone you          |
| can reach. We have your number.          |
|                                          |
| [ Turn on two-factor ]*                  |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) PASSWORD ----------------------------------------------------------+
| Password       last changed 3 months ago      [ Change password ]        |
|                                                                          |
| Changing it signs out every other device. Your positions, memberships    |
|   and                                                                    |
| settled records are not affected.                                        |
+-- (3) SESSIONS ----------------------------------------------------------+
| THIS DEVICE   Chrome, Linux, Lagos, active now                           |
|   current                                                                |
| Laptop        Chrome, Windows, Lagos, 11 Sep 21:14     [ Sign out ]      |
| Old phone     AJO.ng app, Lagos, 02 Sep 08:31            [ Sign out ]    |
|                                                                          |
| GET /auth/sessions and DELETE /auth/sessions/:id.                        |
| Sign out everywhere is a single action, not a loop over sessions.        |
+-- (4) SECURITY ALERTS ---------------------------------------------------+
| 20 Aug 21:14  security.login_new_device   Chrome, Lagos                  |
| 12 Aug 09:41  security.login_new_device   AJO.ng app, Lagos              |
|                                                                          |
| account.frozen also appears here, and by SMS, because it is              |
| money-critical and security, which is what reserves SMS.                 |
+-- (5) TWO-FACTOR --------------------------------------------------------+
| Two-factor is not on.                                                    |
|                                                                          |
| Turning it on requires a phone you can reach. AJO.ng has your number,    |
| verified. There is no authenticator app in v1.                           |
|                                                                          |
| [ Turn on two-factor ]*                                                  |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.27.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Password', 'Last changed, and the change action.', 'P1', 'Changing it signs out other devices and nothing else. Stating what is *not* affected prevents the common fear that changing a password loses an Ajo position.'],
            ['(2) Device sessions', 'Every signed-in device with place, time and a sign-out action.', 'P1', '`GET /auth/sessions` and `DELETE /auth/sessions/:id`. The current device is marked and cannot be signed out from this list, because signing out the device you are reading on is a confusing way to lose the page.'],
            ['(3) Sign out everywhere', 'One action for all other sessions.', 'P1', 'A single action rather than a loop, because the situation where it is used is a person who no longer trusts the account and should not have to select eleven rows.'],
            ['(4) Security alerts', 'New-device and freeze events, with the response attached.', 'P1', '**The response is in the alert, not in a help page.** *If that was not you, change your password and sign out everywhere* is the whole instruction, and it is on the same screen as the event that triggers it.'],
            ['(5) Two-factor', 'Optional SMS-based second factor.', 'P1', 'Off by default. CANONICAL.md reserves SMS for money-critical and security events, and a 2FA code is a security event, so this use is inside the policy. **There is no authenticator app in v1**, and the screen says so rather than pretending otherwise.'],
            ['(6) No security questions', 'None exist and none are offered.', 'P1', '**Prohibited.** Security questions are weak, they are the most commonly leaked credential store in any breach, and a savings product should not create one.'],
            ['(7) Account freeze is not here', 'Freeze is a platform action, not a self-service one.', 'P1', 'A person who believes their account is compromised needs to sign out and change a password. A member who wants to stop a payment is a different problem, and it is solved by contacting support, not by a self-service switch that would let anyone lock themselves out of their own records.'],
        ],
        "widths": [0.51, 1.05, 0.42, 4.52],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.28 Identity Verification — SCR-MOB-22'},

    {
        "t": "p",
        "text": 'The optional check that gates sending money out, presented as a three-step process with a stated reason. The order is deliberate: the reason comes first, because a person who does not know why a savings app wants their date of birth will assume the worst and abandon. The screen is also explicit about the one thing that is not decided — whether receiving requires verification — because an unstated asymmetry invites every member with a payout to ask why they are being asked for less than the person next to them.',
    },

    {
        "t": "callout",
        "kind": 'LEGAL',
        "title": 'Identity verification: what this section does and does not decide',
        "text": 'CANONICAL.md open decision D-04 asks whether BVN and CAC verification is mandatory for all members or only above a threshold, and D-02 asks who holds the funds, which determines the licensing path. Both are unresolved. This section therefore specifies the **process** and the **data minimisation**, and it does not assert that identity verification is a legal requirement, that the provider performs any particular check, that any document is sufficient, or that the platform is authorised to collect and process biometric or national identification data in Nigeria. **Requires review by qualified Nigerian legal counsel**, together with written confirmation from ProvidusUnity of exactly which fields are matched, where the matched result is stored, its retention period, and whether AJO.ng receives a raw NIN or only a verdict. Until that is confirmed, the copy above describes intent and must not ship as a factual claim about data handling.',
    },

    {"t": "h3", "text": '6.28.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| < Profile        Identity check          |
+-- (2) WHY -------------------------------+
| +------------------------------------+   |
| |  Why we ask                        |   |
| |                                    |   |
| |  AJO.ng holds real money           |   |
| |  between collections. Before       |   |
| |  you take money out, we need       |   |
| |  to know who you are.              |   |
| |                                    |   |
| |  We ask everyone who sends         |   |
| |  out money. Whether you must       |   |
| |  do it to receive is still         |   |
| |  being decided.                    |   |
| +------------------------------------+   |
+-- (3) STEP 1 ----------------------------+
| +------------------------------------+   |
| |  1  Your details                   |   |
| |                                    |   |
| |     Full name      Segun A.        |   |
| |     Date of birth  1991            |   |
| |     Address        set             |   |
| |                                    |   |
| |     { Continue }*                  |   |
| +------------------------------------+   |
+-- (4) STEP 2 ----------------------------+
| +------------------------------------+   |
| |  2  Your identity                  |   |
| |                                    |   |
| |     [ Take a photo   ]             |   |
| |     [ Upload instead ]             |   |
| |                                    |   |
| |     A photo of you holding         |   |
| |     your NIN slip, or your         |   |
| |     NIN slip alone.                |   |
| +------------------------------------+   |
+-- (5) STEP 3 ----------------------------+
| +------------------------------------+   |
| |  3  Your BVN                       |   |
| |                                    |   |
| |     [ 2 0 0 0 0 0 0 0 0 0 ]        |   |
| |                                    |   |
| |     BVN is matched against         |   |
| |     your NIN by the provider.      |   |
| |     AJO.ng does not store          |   |
| |     the NIN.                       |   |
| +------------------------------------+   |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) WHY ---------------------------------------------------------------+
| AJO.ng holds real money between collections. Before you send money out   |
|   we                                                                     |
| need to know who you are. We ask everyone who sends out money.           |
|                                                                          |
| Whether you must do it to receive is open decision D-04, not decided.    |
+-- (3) STEPS -------------------------------------------------------------+
| 1  Your details       full name, date of birth, address      [ Continue  |
|   ]                                                                      |
| 2  Your identity      a photo of you, and your NIN slip     [ Continue ] |
| 3  Your BVN           matched to the NIN by the provider    [ Continue ] |
| 4  Review             what we will store, and what we will not           |
|                                                                          |
| Documents go to the verification provider. AJO.ng stores the result, the |
| reference and the timestamps. It does not store the NIN.                 |
+-- (4) OUTCOME STATES ----------------------------------------------------+
| not started   nothing submitted                                          |
| in progress   submitted, provider has not answered                       |
| approved      verified_checks row with an approval reference             |
| failed        provider reason, with an appeal route and no re-upload     |
|   loop                                                                   |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.28.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Why we ask', 'The reason, before the request.', 'P1', '**Stated before any field.** The reason is that money is held between collections and identity is needed before money goes out. The screen does not claim that verification is legally required, because whether it is depends on D-04 and on the licensing path in D-02, neither of which is settled.'],
            ['(2) Three steps', 'Details, identity document, BVN.', 'P1', 'Ordered so the cheapest information comes first. A person who abandons abandons before uploading a photograph, which is the right place to abandon.'],
            ['(3) Document capture', 'Photograph, or upload.', 'P1', 'Capture is in-app, not by email, so the document never travels through a channel the platform does not control. Upload is offered because not everyone can take a legible photograph in the light available.'],
            ['(4) BVN handling', 'Entered, matched, not stored.', 'P1', '**The BVN is matched against the NIN by the provider and AJO.ng stores neither.** The screen says *we do not store your NIN* in the same place the NIN is asked for, not in a policy page four screens away.'],
            ['(5) Stored-versus-not-stored', 'An explicit list of what is kept.', 'P1', 'Kept: the result, the provider reference, timestamps. Not kept: the NIN, the document image. Stating this is both honest and required for the person to decide.'],
            ['(6) Outcome states', 'Not started, in progress, approved, failed.', 'P1', '*In progress* is a real state, not a spinner: provider verification takes time and a person who cannot tell a wait from a failure will submit again.'],
            ['(7) Failure has an appeal', 'A reason and a route, not a retry loop.', 'P1', '**Prohibited: an unbounded re-upload loop.** Each submission attempt is recorded, and the route out of a failure is an appeal, because a document rejected for a legible-photo reason and a document rejected for a mismatch need different handling.'],
            ['(8) Optional is stated', 'Verification is not presented as universal.', 'P1', 'Repeated from the why block: we ask everyone who sends out money. Whether receiving requires it is open, and the screen says so rather than implying a requirement that may not exist.'],
        ],
        "widths": [0.49, 0.75, 0.42, 4.84],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.29 Support — SCR-MOB-23'},

    {
        "t": "p",
        "text": "The screen a person reaches when something has already gone wrong, so it is organised around their symptom rather than around the product's features. The topic list is written in the words people use, not the words the system uses: *I was charged but the receipt says something else* is a support ticket, and *fee policy* is not. The contact block states what support cannot do, because the most frustrating support experience in a financial product is being told nicely that the agent cannot do the one thing you need.",
    },

    {
        "t": "callout",
        "kind": 'ASSUMPTION',
        "title": 'The support topic list is a first draft, not a researched one',
        "text": 'These topics are inferred from the edge cases in section 19 and from what the fee model is likely to produce. They are **not** based on real support contacts, because the product is pre-launch and has no customers, and no content in this specification may present them as a record of what people actually ask. The first post-launch task for the support owner is to rebuild this list from the first hundred real contacts and to measure which topics route to chat, to a dispute, and to a refund. **A topic list built from assumptions should be labelled as one, because the failure mode is a support function that confidently answers the wrong question.**',
    },

    {"t": "h3", "text": '6.29.1 Wireframe'},

    {
        "t": "p",
        "text": '**Mobile — 375 px.** One column, 16 px gutters, sticky bottom navigation on authenticated screens, and 44 px minimum touch targets. Regions that would overflow become a stacked row or move to a detail page rather than shrinking.',
    },

    {
        "t": "code",
        "text": """
+-- (1) HEADER ----------------------------+
| Support                                  |
+-- (2) SEARCH ----------------------------+
| [ What do you need help with?    ]       |
+-- (3) COMMON ----------------------------+
| I was charged but my receipt             |
|    says something else                   |
| My payout has not arrived                |
| I cannot log in                          |
| How do I leave an Ajo?                   |
| What happens if someone                  |
|    does not pay?                         |
+-- (4) CONTACT ---------------------------+
| +------------------------------------+   |
| |  Still stuck?                      |   |
| |                                    |   |
| |  { Start a chat }*                 |   |
| |  { Send an email }                 |   |
| |  { Raise a dispute }               |   |
| |                                    |   |
| |  Chat 08:00 to 20:00 WAT.          |   |
| |  Disputes are read the same        |   |
| |  hours.                            |   |
| +------------------------------------+   |
+-- (5) BOTTOM NAV ------------------------+
| Home  Ajos  Pay  Alerts  More            |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent left navigation for the app and the console, a constrained 720 px reading column for the money surfaces, and a right-hand context column on the detail screens. Nothing is centred that should be left-aligned.',
    },

    {
        "t": "code",
        "text": """
+-- (1) LEFT NAV ----------------------------------------------------------+
| Home                                                                     |
| My Ajos                                                                  |
| Pay                                                                      |
| Alerts                                                                   |
| Support                                                                  |
|                                                                          |
| Profile                                                                  |
| Settings                                                                 |
+-- (2) SEARCH ------------------------------------------------------------+
| [ What do you need help with?                                     ]      |
+-- (3) TOPICS ------------------------------------------------------------+
| Payments   I was charged but the receipt is wrong                        |
| Payouts    My payout has not arrive                                      |
| Account    I cannot log in, or am locked out                             |
| Ajos       How do I leave, or join, an Ajo                               |
| Defaults   What happens if someone does not pay                          |
| Fees       Why is there a 2% fee, and where does it go                   |
+-- (4) CONTACT -----------------------------------------------------------+
| Chat      08:00 to 20:00 WAT, in-app, with Ajo context attached          |
| Email     support@ajo.ng, answered within one working day                |
| Dispute   raised from the Ajo, contribution or payout, not from here     |
|                                                                          |
| Support can read your records and contact you. Support cannot move       |
|   money,                                                                 |
| alter a financial record, initiate a payout, or override a risk          |
|   decision.                                                              |
| Those are the roles in CANONICAL.md section 2, and a support agent is    |
|   not                                                                    |
| able to do them however sympathetic the situation.                       |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.29.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Search', 'Free text over topics and articles.', 'P1', 'Search is a convenience over a hand-written topic list of about thirty entries, not a knowledge-base search. A product with no live volume has no real query data to tune against, and pretending otherwise is how a search box ships empty.'],
            ['(2) Topic list', 'Symptoms, phrased as the person would say them.', 'P1', "Written from complaints, not from the nav. The six in the frame are the ones the product's own edge cases predict."],
            ['(3) Chat with context', 'Chat that already knows which Ajo the person is looking at.', 'P1', 'The Ajo, contribution or payout reference is attached automatically. A member who pastes a screenshot is describing a picture, and the reference is what turns it into a query.'],
            ['(4) Support hours', 'Published, with a real time zone.', 'P1', '08:00 to 20:00 WAT. A published window with a queue is better support than an always-open channel that answers in nine hours.'],
            ['(5) Capability statement', 'What support can and cannot do.', 'P1', '**Mandatory.** CANONICAL.md gives `support` read access, contact rights and dispute assistance, and explicitly denies moving money, altering financial records, initiating payouts and overriding risk. The screen says so, because a member told *I cannot refund that* deserves to hear it from the product rather than from an agent apologising.'],
            ['(6) Disputes raised elsewhere', 'The dispute route is on the Ajo screens.', 'P1', 'Listed here for completeness, but the primary route is contextual, because a dispute raised from the affected screen arrives with the reference already attached.'],
        ],
        "widths": [0.43, 0.88, 0.42, 4.77],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.30 Console Overview — SCR-ADM-01'},

    {
        "t": "p",
        "text": "The console's front door, and the only screen an administrator sees before deciding what to do. It answers one question — what needs a person right now — and everything else on it is context for that answer. It deliberately shows no growth charts, no top-lists of users by balance, and no revenue projections, because the three questions those answer are not the questions a person opens an operations console to ask.",
    },

    {
        "t": "callout",
        "kind": 'WARNING',
        "title": 'This console is not a member-facing view and shows no member balances',
        "text": "The console shows platform aggregates. It does not offer a browsable list of every user with their balance on one screen, and such a list is **prohibited at launch**: a screen that puts every member's balance in front of every staff member is a concentration of personal financial data that no operational need in v1 justifies. The reasons someone is looking up a particular account — a dispute, a risk event, a support contact — are the routes through which a record is reached, and each is audit-logged with the reason. This is a data-minimisation decision and **it should be revisited by counsel against the platform's actual obligations**, because a support or risk role may be required to be able to see more than this allows.",
    },

    {"t": "h3", "text": '6.30.1 Wireframe'},

    {
        "t": "p",
        "text": '**Tablet — 768 px.** The rail collapses to icons, and the exception list moves above the money block, because on a tablet the exception list is the only thing a person will read.',
    },

    {
        "t": "code",
        "text": """
+-- (1) RAIL ----------------------------------------------------+
| AJO.ng admin                                                   |
| Overview                                                       |
| Users                                                          |
| Ajos                                                           |
| Disputes                                                       |
| Risk                                                           |
| Reports                                                        |
| Audit logs                                                     |
+-- (2) PLATFORM COUNTS -----------------------------------------+
| Users          1,284                                           |
| Ajos              96                                           |
| Disputes open     14                                           |
| Risk events        7                                           |
| Payouts held       2                                           |
+-- (3) MONEY TODAY ---------------------------------------------+
| Collected  NGN 6,180,000.00                                    |
| Fees       NGN   123,600.00                                    |
| Payouts    NGN 3,000,000.00                                    |
| Unreconciled         0                                         |
+-- (4) NEEDS A PERSON ------------------------------------------+
| ! 7 risk events unassigned                                     |
| ! 2 payouts held                                               |
| ! 4 disputes idle 48h+                                         |
+----------------------------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Counts and money on the left, exceptions and recent activity on the right, and the margin warning directly under the money block where the NGN 123,600.00 figure is read.',
    },

    {
        "t": "code",
        "text": """
+-- (1) RAIL --------------------------------------------------------------+
| Overview                                                                 |
| Users                                                                    |
| Ajos                                                                     |
| Disputes                                                                 |
| Risk                                                                     |
|                                                                          |
| Reports                                                                  |
| Audit logs                                                               |
| Settings                                                                 |
+-- (2) COUNTS ------------------------------------------------------------+
| USERS        1,284      +48 this week                                    |
| AJOS            96      71 active, 12 enrollment, 13 completed           |
| DISPUTES OPEN    14      4 idle over 48h                                 |
| RISK EVENTS       7      7 unassigned                                    |
| PAYOUTS HELD      2      oldest 3 days                                   |
+-- (3) MONEY -------------------------------------------------------------+
| COLLECTED TODAY      NGN 6,180,000.00   6,060 contributions              |
| FEES TODAY             NGN 123,600.00   2% of collected                  |
| PAYOUTS TODAY        NGN 3,000,000.00   30 payouts                       |
| UNRECONCILED                     0.00   last run 06:00, 0 findings       |
|                                                                          |
| Gross fee revenue is not net revenue. Payment-partner charges for        |
| collection and payout are unknown and must be obtained in writing from   |
| ProvidusUnity before the margin is stated anywhere. See CANONICAL.md     |
| section 1 and open decision D-03.                                        |
+-- (4) NEEDS A PERSON ----------------------------------------------------+
| !  7  risk events, none assigned        [ Open the queue ]               |
| !  2  payouts held, oldest 3 days         [ Open the queue ]             |
| !  4  disputes idle over 48 hours         [ Open the queue ]             |
+-- (5) RECENT ACTIVITY ---------------------------------------------------+
| 06:02  reconciliation run rc_9KL, 0 findings                             |
| 05:41  payout pyt_2WT settled, NGN 10,000.00                             |
| 04:18  risk event ris_7Q2 created, velocity on 4 accounts                |
| 03:55  freeze applied to usr_2K9 by risk_officer A. Okeke                |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.30.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Rail', "The console's sections.", 'P1', 'Eight sections, matching the admin endpoint groups in CANONICAL.md section 6. Settings is separated from Reports because changing a platform limit and reading a report are different acts with different audit entries.'],
            ['(2) Counts', 'Users, Ajos, disputes, risk events, held payouts.', 'P1', '**Counts with a change, not bare totals.** A count that does not say whether it grew tells an operator nothing about whether anything is wrong.'],
            ['(3) Money today', 'Collected, fees, payouts, and the unreconciled total.', 'P1', 'The unreconciled figure is the one that matters. **It is expected to be NGN 0.00 and its presence is the point**: a console that shows a reconciliation total makes an operator check it, and a console that omits it makes the absence invisible.'],
            ['(4) Margin warning', 'That gross fee revenue is not net revenue.', 'P1', '**Mandatory, and permanent.** CANONICAL.md requires the margin warning in the financial material, and the console is the screen a person will use to convince themselves the business is working. It sits under the money block, not in a footnote, because the person reading NGN 123,600.00 of fees today is exactly the person who will forget to subtract what it cost to collect.'],
            ['(5) Needs a person', 'Unassigned risk, held payouts, idle disputes, each linked to its queue.', 'P1', 'The only actionable region. Each row is a count, an age, and a link. A console that lists exceptions without a way into them is a report, and reports do not get acted on.'],
            ['(6) Recent activity', 'The last few consequential events across the platform.', 'P2', 'A freeze, a settlement, a reconciliation run, a risk event. **Not** a full audit feed — that is 6.33 — because the audit log is append-only and query-only, and mixing it into an overview trains people to expect a mutable activity feed.'],
        ],
        "widths": [0.42, 0.98, 0.42, 4.68],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.31 Dispute Workspace — SCR-ADM-06'},

    {
        "t": "p",
        "text": "Where the platform's people actually work: a queue of disputes on one side and the selected dispute on the other, with the decision controls at the bottom of the workspace rather than in a menu. The layout is the argument — a support agent reading a thread and reaching for a decision control in a different place is an agent who decides before reading. The ledger effect is displayed on every dispute, because the first question after *what should we do* is always *what has this already done*.",
    },

    {
        "t": "callout",
        "kind": 'DECISION',
        "title": 'Refunds are decisions, not corrections',
        "text": 'The interface offers three outcomes: refund, explain without a refund, and request more information. It does not offer *adjust the record*, because that would suggest a dispute can put the ledger right, and in this product the ledger is right by construction and any error in it is fixed by a reversing entry rather than by a dispute decision. A dispute can *cause* a reversing entry, which is a different thing: the agent who finds the error posts the correction in the ledger, and the dispute records that they did and why. The trade-off is that the interface has no fast path for the common case, and the mitigation is that the common case is reached in two clicks: *request more information* on the dispute, then a ledger action in the contribution screen.',
    },

    {"t": "h3", "text": '6.31.1 Wireframe'},

    {
        "t": "p",
        "text": '**Tablet — 768 px.** Two columns, 24 px gutters, a collapsible rail, and a table that drops its least important column rather than becoming a card list. This is the smallest width at which the console is built.',
    },

    {
        "t": "code",
        "text": """
+-- (1) RAIL ----------------------------------------------------+
| Overview                                                       |
| Users                                                          |
| Ajos                                                           |
| Disputes                                                       |
| Risk                                                           |
| Reports                                                        |
| Audit                                                          |
| Settings                                                       |
+-- (2) QUEUE ---------------------------------------------------+
| dsp_4Q7  AWAITING MEMBER   2d   Chima's Ajo                    |
| dsp_9KX  AWAITING PLATFORM 1d   Adaeze's Ajo                   |
| dsp_2WT  AWAITING MEMBER   4d   Adaeze's Ajo                   |
| dsp_5RT  INVESTIGATING    0d   Chima's Ajo                     |
| dsp_8HN  RESOLVED         9d   Adaeze's Ajo                    |
+-- (3) WORKSPACE -----------------------------------------------+
| dsp_4Q7   AWAITING MEMBER                                      |
|                                                                |
| Subject  charged for round 2,                                  |
|          receipt says paid                                     |
|                                                                |
| Effect   round 2 reinstated,                                   |
|          round 3 reassigned                                    |
|                                                                |
| Member wrote 30m ago                                           |
|                                                                |
| { Reply }*  { Decide }                                         |
+----------------------------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent 240 px rail, a 1,280 px content area, and a right context panel. Tables stay tables. A console is a tool for reading many rows at once and converting it to cards at desktop width would be a downgrade.',
    },

    {
        "t": "code",
        "text": """
+-- (1) RAIL --------------------------------------------------------------+
| Overview                                                                 |
| Users                                                                    |
| Ajos                                                                     |
| Disputes                                                                 |
| Risk                                                                     |
|                                                                          |
| Reports                                                                  |
| Audit logs                                                               |
| Settings                                                                 |
+-- (2) QUEUE -------------------------------------------------------------+
| REF     STATE             AGE  SUBJECT            AJO           WAITS ON |
| dsp_5RT  INVESTIGATING     0d   payout not held    Chima's Ajo           |
|   platform                                                               |
| dsp_9KX  AWAITING PLATFORM  1d   payout order       Adaeze's Ajo         |
|   platform                                                               |
| dsp_4Q7  AWAITING MEMBER   2d   wrong round        Chima's Ajo   member  |
| dsp_2WT  AWAITING MEMBER   4d   charged twice      Adaeze's Ajo  member  |
| dsp_1PP  AWAITING PLATFORM  6d   BVN mismatch       Fatima's Ajo         |
|   platform                                                               |
| dsp_8HN  RESOLVED          9d   payout order       Adaeze's Ajo  -       |
+-- (3) WORKSPACE ---------------------------------------------------------+
| dsp_4Q7  Chima's Ajo, round 2   STATE: AWAITING MEMBER   AGE 2d          |
|                                                                          |
| SUBJECT   I was charged NGN 1,020.00 for round 2, the receipt says       |
|           paid, the round shows 9 of 10, and I have no record of it.     |
|                                                                          |
| 12 Sep 09:52  AJO.ng (support)                                           |
|   Thanks. We can see the payment and the posting. We are                 |
|   checking which round it was applied to.                                |
|                                                                          |
| 12 Sep 10:14  Chima O. (member)                                          |
|   It is not in my history at all.                                        |
|                                                                          |
| 12 Sep 11:03  AJO.ng (support)                                           |
|   Confirmed: applied to round 3 by mistake. We are                       |
|   correcting it. No refund is due to you.                                |
|                                                                          |
| 12 Sep 11:30  Chima O. (member)                                          |
|   I would still like my money back.                                      |
|                                                                          |
| LEDGER EFFECT   Round 2 obligation reinstated. Round 3                   |
|                 contribution reassigned. A reversing entry               |
|                 was posted. Nothing was deleted.                         |
|                                                                          |
| DECISION REQUIRED   Refund NGN 1,020.00, or explain that the             |
|                      correction stands.                                  |
|                                                                          |
| { Refund }*   { Explain, no refund }*   { Need more information }        |
+-- (4) DECISION RULES ----------------------------------------------------+
| support       may reply, may not decide a money outcome                  |
| risk_officer  may decide, may not release a payout directly              |
| super_admin   may decide, may not edit or delete a ledger entry          |
|                                                                          |
| Every decision writes an audit_log row with the actor, the reason, and   |
|   the                                                                    |
| before and after state. There is no decision without a reason.           |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.31.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Queue', 'Every dispute, with state, age, subject, Ajo and who waits.', 'P1', "Sorted by age within state rather than by state then age, because the oldest item is the one that breaches a response time. **The *who waits* column is the operational one**: a dispute waiting on the platform is the platform's debt."],
            ['(2) Filters', 'State, Ajo, age, and assignee.', 'P2', "Assignment is a console concept, not a member concept. A dispute is not *owned* by an agent in the member's view, and no member-facing text implies otherwise."],
            ['(3) Thread', 'The same thread the member sees, unedited.', 'P1', "Read-only to agents. A support reply can be composed but an existing message cannot be edited or deleted, so the member's record of what they were told cannot be altered after the fact."],
            ['(4) Ledger effect', 'What the dispute has already changed.', 'P1', '**Mandatory.** Displayed above the decision controls, not below, so that nobody reaches for *Refund* without having read what has already happened. An agent who does not know a reversing entry was posted is an agent who can post a second one.'],
            ['(5) Decision controls', 'Refund, explain with no refund, or request more information.', 'P1', 'Every path requires a reason, and a decision cannot be saved without one. The alternatives considered — resolve, close, escalate — were rejected because *close* implies an outcome that did not happen and *escalate* has no defined destination in v1.'],
            ['(6) Role limits', 'What the signed-in role may do here.', 'P1', '**Enforced in the interface, not only in the API.** CANONICAL.md denies `support` any power to move money and denies `super_admin` any power to edit the ledger, and an interface that shows a control a role cannot use is a control that will be pressed and produce an error.'],
            ['(7) Audit on decision', 'The decision and its reason are written on save.', 'P1', '`audit_logs` records the actor, the action, the reason, and the before and after state. **There is no decision without a reason, and no reason can be edited afterwards.**'],
        ],
        "widths": [0.42, 1.08, 0.42, 4.58],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.32 Risk Queue — SCR-ADM-08'},

    {
        "t": "p",
        "text": 'The screen that decides whether a suspicious pattern becomes a person losing access to their money, and it is designed around one observation: a rule is worth more than a person at 4 a.m. The event detail therefore leads with the money — what has been collected, what has been paid out, and what happens to both under each available action — before it lists the actions. An officer deciding under time pressure needs to know what each button costs, not what it is called.',
    },

    {
        "t": "callout",
        "kind": 'WARNING',
        "title": 'A risk action is visible to the member it is taken against',
        "text": 'Freezing an account and holding a payout both have member-facing consequences, and the interface must make that explicit before the officer presses the button: the member receives `account.frozen` or `payout.held` by push, email and SMS, and sees a screen at SCR-WEB-17 or the held state at 6.20. **A risk action that the member cannot see is a risk action the member cannot appeal**, and the reason field is therefore also the material that becomes the explanation. This is why a reason cannot be empty and cannot later be edited: the officer is writing the explanation at the moment they are taking the action, and the temptation to write something short and revisable is exactly the failure this rule prevents.',
    },

    {"t": "h3", "text": '6.32.1 Wireframe'},

    {
        "t": "p",
        "text": '**Tablet — 768 px.** Two columns, 24 px gutters, a collapsible rail, and a table that drops its least important column rather than becoming a card list. This is the smallest width at which the console is built.',
    },

    {
        "t": "code",
        "text": """
+-- (1) RAIL ----------------------------------------------------+
| Overview                                                       |
| Users                                                          |
| Ajos                                                           |
| Disputes                                                       |
| Risk                                                           |
| Reports                                                        |
| Audit                                                          |
| Settings                                                       |
+-- (2) QUEUE ---------------------------------------------------+
| ris_7Q2  velocity    4 accounts   NEW                          |
| ris_3KL  device reuse 2 accounts  NEW                          |
| ris_9WX  BVN mismatch 1 account   REVIEW                       |
| ris_2PP  payout burst 1 account   ASSIGNED                     |
+-- (3) EVENT ---------------------------------------------------+
| ris_7Q2  velocity                                              |
|                                                                |
| 4 accounts, 3 devices,                                         |
| one phone number, in 6 min.                                    |
|                                                                |
| Collected NGN 40,800.00                                        |
| Payouts NGN 0.00                                               |
|                                                                |
| [ Take ]   [ Reject ]                                          |
+----------------------------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Queue on the left, event on the right, actions beneath the money block. The limits panel sits at the foot of the event column, marked provisional, because D-08 is unresolved.',
    },

    {
        "t": "code",
        "text": """
+-- (1) RAIL --------------------------------------------------------------+
| Overview                                                                 |
| Users                                                                    |
| Ajos                                                                     |
| Disputes                                                                 |
| Risk                                                                     |
|                                                                          |
| Reports                                                                  |
| Audit logs                                                               |
| Settings                                                                 |
+-- (2) QUEUE -------------------------------------------------------------+
| EVENT     TYPE          AGE  SIGNAL           VALUE      STATE           |
| ris_2PP   payout burst  0d   9 payouts, 1 acct NGN 90,000 ASSIGNED       |
| ris_7Q2   velocity      0d   4 accts, 3 devs   NGN 40,800  NEW           |
| ris_3KL   device reuse  1d   2 accounts, 1 dev  NGN 0       NEW          |
| ris_9WX   BVN mismatch  2d   1 account         NGN 0       REVIEW        |
| ris_6TQ   late round    3d   default pattern   NGN 10,000  ASSIGNED      |
+-- (3) EVENT -------------------------------------------------------------+
| ris_7Q2   velocity   STATE: NEW   RAISED 12 Sep 04:18                    |
|                                                                          |
| 4 accounts, 3 devices, 1 phone number, within 6 minutes.                 |
|                                                                          |
| COLLECTED   NGN 40,800.00     PAYOUTS   NGN 0.00                         |
|                                                                          |
| It is 04:18. Nobody is awake. That is what a rule is for, and what       |
| an assign-to-a-person rule is not.                                       |
|                                                                          |
| +----------------------------------------------------------------+       |
| |  What the money would do if the accounts were one person        |      |
| |                                                                |       |
| |  Collected in the window      NGN 40,800.00                    |       |
| |  Already paid out             NGN 0.00                        |        |
| |  Held pending a decision      NGN 40,800.00                   |        |
| |                                                                |       |
| |  Every one of these payouts can be held and none can be lost.  |       |
| +----------------------------------------------------------------+       |
|                                                                          |
| ACTIONS                                                                  |
|                                                                          |
|   Hold the 4 payouts        creates a payout hold                        |
|   Freeze the 3 sessions     ends sessions, keeps records                 |
|   Put 4 accounts in review  blocks new Ajo joins                         |
|   Reject                     records a false positive                    |
|                                                                          |
|   + Any action requires a reason, and it is permanent.                   |
|   + risk_officer may take all four. super_admin may take                 |
|     all four.                                                            |
|   + Nobody may delete an event, even after rejecting it.                 |
+-- (4) LIMITS ------------------------------------------------------------+
| Per account, per round  NGN 5,000,000  (D-08, not final)                 |
| Per account, per day    NGN 5,000,000                                    |
| Ajo size                50 positions  (D-08, not final)                  |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.32.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Queue', 'Risk events with type, age, signal, value and state.', 'P1', '**The value column is the volume at stake, in naira.** An event about NGN 0.00 and an event about NGN 90,000.00 are not the same event, and a queue sorted only by age treats them as equal.'],
            ['(2) Event type', 'The signal that fired, in plain words.', 'P1', 'Velocity, device reuse, BVN mismatch, payout burst, late-round pattern. **The type is a named rule, not a score**, because an officer asked to explain a freeze to a member needs to be able to name the rule.'],
            ['(3) Event detail', 'The evidence, the money, and the actions.', 'P1', 'Evidence first, then money, then actions. A risk screen that leads with buttons trains officers to act on the signal without reading it, which is how a false positive becomes a frozen member.'],
            ['(4) Money-at-risk block', 'Collected, paid out, and held, in one box.', 'P1', '**The answer to *can this still be recovered*, stated numerically.** An officer holding NGN 40,800.00 that has not been paid out is protecting recoverable money; an officer after payout is not, and the two situations call for different actions and different urgency.'],
            ['(5) Actions with consequences', 'Each action labelled with what it does.', 'P1', "*Hold the payouts* is not *Block*. *Freeze the sessions* is not *Ban*. **Prohibited: a control labelled only with the action's internal name.** Each action also states what it does not do, so an officer knows the scope."],
            ['(6) Mandatory reason', 'Every action requires a reason.', 'P1', '**There is no action without a reason and no way to edit a reason afterwards.** A freeze with no stated reason is one a member cannot be told about, and a member who cannot be told why their money is held cannot appeal the hold.'],
            ['(7) Reversible by design', 'Which actions can be undone.', 'P1', 'A payout hold and a review are reversible. A session freeze is reversible. **A ledger entry is not, and there is no action on this screen that edits or deletes one**, which is the CANONICAL.md hard rule applied to the risk function.'],
            ['(8) Limits panel', 'The configured limits, marked as provisional.', 'P1', 'The values shown are **provisional and labelled**, because open decision D-08 has not fixed the maximum Ajo size or the contribution cap. A limit displayed as settled is a limit that will be relied on.'],
        ],
        "widths": [0.53, 0.95, 0.42, 4.6],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.33 Audit Logs — SCR-ADM-11'},

    {
        "t": "p",
        "text": 'The record of who did what to which record, and the only screen in the product with no write operations at all. It is a query surface over an append-only table, and that constraint is visible rather than implied: the screen says it cannot be edited or deleted, and it has no control that could even attempt it. Each row shows the reason and the before-and-after state, because an audit entry without a reason or without the state it changed is a record that can be questioned but not defended.',
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Why the audit log is query-only and never a dashboard',
        "text": 'The audit log is not summarised, not charted, and not given a landing page. It has no counts, no trends, and no alerts of its own, because the moment it gains a dashboard it acquires a meaning — *activity* — that is a judgement about the people whose actions it records, and that judgement has no place on a page an administrator reaches by clicking a person. Activity summaries belong in the risk queue at 6.32, where a signal is acted on, and in the overview at 6.30, where an exception is listed. If a summary of the audit log is ever wanted, it should be built as a derived view with a named owner and a stated purpose, not as a row count at the top of the log itself.',
    },

    {"t": "h3", "text": '6.33.1 Wireframe'},

    {
        "t": "p",
        "text": '**Tablet — 768 px.** Two columns, 24 px gutters, a collapsible rail, and a table that drops its least important column rather than becoming a card list. This is the smallest width at which the console is built.',
    },

    {
        "t": "code",
        "text": """
+-- (1) RAIL ----------------------------------------------------+
| Overview                                                       |
| Users                                                          |
| Ajos                                                           |
| Disputes                                                       |
| Risk                                                           |
| Reports                                                        |
| Audit                                                          |
| Settings                                                       |
+-- (2) FILTER --------------------------------------------------+
| actor  action  entity  from  to                                |
| [ Search ]                                                     |
+-- (3) ROWS ----------------------------------------------------+
| 12 Sep 04:18  risk_officer  hold_payout                        |
|              pyt_2WT   reason: velocity                        |
| 12 Sep 03:55  risk_officer  freeze                             |
|              usr_2K9   reason: device                          |
| 12 Sep 06:02  system        reconcile                          |
|              rc_9KL     0 findings                             |
+-- (4) APPEND-ONLY ---------------------------------------------+
| These rows cannot be edited or                                 |
| deleted, by anyone.                                            |
+----------------------------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": '**Desktop — 1440 px.** Persistent 240 px rail, a 1,280 px content area, and a right context panel. Tables stay tables. A console is a tool for reading many rows at once and converting it to cards at desktop width would be a downgrade.',
    },

    {
        "t": "code",
        "text": """
+-- (1) RAIL --------------------------------------------------------------+
| Overview                                                                 |
| Users                                                                    |
| Ajos                                                                     |
| Disputes                                                                 |
| Risk                                                                     |
|                                                                          |
| Reports                                                                  |
| Audit logs                                                               |
| Settings                                                                 |
+-- (2) FILTERS -----------------------------------------------------------+
| Actor                                                                    |
| Action                                                                   |
| Entity type                                                              |
| Entity id                                                                |
| From                                                                     |
| To                                                                       |
| [ Search ]                                                               |
+-- (3) TABLE -------------------------------------------------------------+
| WHEN            ACTOR         ACTION         ENTITY     REASON           |
| 12 Sep 06:02:04  system        reconcile       rc_9KL     scheduled run  |
| 12 Sep 05:41:18  system        settle_payout  pyt_2WT    provider hook   |
| 12 Sep 04:18:52  risk_officer  hold_payout    pyt_7Q2    velocity, 4     |
|   acct                                                                   |
| 12 Sep 04:18:52  risk_officer  hold_payout    pyt_9WX    velocity, 4     |
|   acct                                                                   |
| 12 Sep 04:18:52  risk_officer  place_review   usr_7Q2    velocity, 4     |
|   acct                                                                   |
| 12 Sep 03:55:11  risk_officer  freeze_account usr_2K9    device reuse    |
| 12 Sep 02:14:33  support       post_dispute   dsp_4Q7    member raised   |
| 10 Sep 17:40:02  ajo_organizer send_reminder  ajo_3KL    round 4         |
|   reminder                                                               |
|                                                                          |
| One action, one row. Four accounts touched means four rows.              |
+-- (4) ENTRY -------------------------------------------------------------+
| ris_7Q2 hold_payout  12 Sep 04:18:52  risk_officer A. Okeke              |
|                                                                          |
| reason      velocity: 4 accounts, 3 devices, 1 number, 6 minutes         |
| before      payout pyt_7Q2 state SCHEDULED                               |
| after       payout pyt_7Q2 state HELD                                    |
| request     X-Request-Id 4f2c-91ab                                       |
|                                                                          |
| This row cannot be edited or deleted, by any role, including             |
|   super_admin.                                                           |
| There is no interface control for it, and there is no API for it.        |
+--------------------------------------------------------------------------+
""",
    },

    {"t": "h3", "text": '6.33.2 Annotated regions'},

    {
        "t": "table",
        "head": ['Region', 'Purpose', 'Priority', 'Notes'],
        "rows": [
            ['(1) Filters', 'Actor, action, entity type, entity id, and a date range.', 'P1', 'The entity **id** as well as the type, because *an account was frozen* is not a useful filter and `usr_2K9` is.'],
            ['(2) One action, one row', 'A multi-entity action writes a row per entity.', 'P1', 'An officer holding four payouts writes four rows. This is the reason the queue above looks repetitive after a bulk action, and it is deliberate: a summary row would let four objects be summarised as one and then audited as one.'],
            ['(3) Reason', 'The free-text reason the actor gave.', 'P1', '**Mandatory and immutable.** A row without a reason is not written. The reason is the material that becomes a member-facing explanation, so it is stored as prose rather than as an enum.'],
            ['(4) Before and after', 'The state before and the state after.', 'P1', 'The single most useful pair of columns in the table, and the reason the log can answer *what did this change* without replaying the history.'],
            ['(5) System rows', 'Reconciliations, webhooks, and scheduled work are actors.', 'P1', '*System* is a first-class actor. **A reconciliation run that finds nothing still writes a row**, because an audit log that records only exceptions cannot prove that a check was performed.'],
            ['(6) Request id', 'The `X-Request-Id` for the request that caused the action.', 'P1', 'Present on every row and echoed on every API response by convention, which makes the log joinable to the request logs and to provider webhooks without a second identifier.'],
            ['(7) No write controls', 'No edit, no delete, no bulk action.', 'P1', '**Prohibited at every level, including `super_admin`.** CANONICAL.md states the hard rule that no role may edit or delete a ledger entry, and the audit log extends the same treatment to itself: an audit log that can be edited is a record of intentions.'],
            ['(8) Retention', 'How long rows are kept.', 'P2', 'Retention is a matter for counsel and for the licensing position in D-02, and the screen states the current period rather than implying permanence.'],
        ],
        "widths": [0.44, 1.11, 0.42, 4.53],
        "size": 7.2,
    },

    {"t": "h2", "text": '6.34 Responsive behaviour summary'},

    {
        "t": "p",
        "text": 'One table, so that the per-screen wireframes above do not each have to restate the same three breakpoint decisions. The column that matters is the third: the rule is that a region is never squeezed to fit, it either reflows, moves to another region, or is deferred to a detail screen.',
    },

    {
        "t": "table",
        "head": ['Region type', '375 px', '768 px', '1440 px', 'Reflow rule'],
        "rows": [
            ['Primary action', 'Full width, in flow, directly under the amount', 'In flow, right-aligned in the footer', 'Single instance in the content column; never duplicated in a column header', '**Never duplicated across breakpoints.** A second copy of a money button is a second chance to charge someone.'],
            ['Money figures', 'Labelled list, one figure per line, rules above totals', 'Two-column labelled list', 'Labelled list, capped at 720 px, never full-bleed', '**Never in a card.** A card implies the figures are optional detail; they are the reason for the screen.'],
            ['Table', 'Row list with the two or three columns that matter; the rest move to a detail screen', 'Table, least important column dropped', 'Full table with all columns', 'A column is never shrunk below legibility to save a row; it is dropped or moved.'],
            ['Chart', 'Not rendered. Figures and counts instead', 'Rendered, full width', 'Rendered at 2/3 width with a context panel', 'A chart that cannot be read at 375 px is a chart that becomes a table, not a squeezed chart.'],
            ['Navigation', 'Bottom bar, five tabs, 44 px targets', 'Top bar, horizontal, horizontally scrollable', 'Persistent 240 px rail', 'Bottom navigation is not a shrunk top navigation; it is a different component with a different job.'],
            ['Filter bar', 'Segmented control or a filter sheet', 'Single row of controls', 'Single row of counts plus controls', 'A filter that needs a sheet on mobile usually needs fewer filters.'],
            ['Sticky behaviour', 'Sticky bottom bar only, and only the tab bar', 'Sticky footer with the page action', 'Sticky header with the page action', '**Sticky money buttons are prohibited** on the pay, payout and dispute-decision screens.'],
            ['Image and avatar', '40 px, initials fallback', '40 px', '40 px in lists, 96 px on profiles', 'No default photographic avatar anywhere; initials or nothing.'],
            ['Empty state', 'Centred in the content column, max 32ch measure', 'Left-aligned at the top of the column', 'Left-aligned at the top of the column', 'An empty state is never centred because the content is centred; it is centred only on mobile, where there is no column.'],
        ],
        "widths": [0.42, 1.62, 0.85, 1.43, 2.18],
        "size": 7.0,
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'The 1024 px floor for the admin console',
        "text": 'The console is built for 768 px and above, and below 768 px it renders a *device not supported* page rather than a squeezed layout. A console that half-works on a phone is worse than one that declines: the operations it performs are financial, and a decision made on a 6-inch screen with a horizontal scrollbar is a decision made without reading the ledger effect. The same page is shown to a member whose session expires on a small screen, and it explains that the console needs a larger screen rather than merely refusing.',
    },

    {"t": "h2", "text": '6.35 Handoff checklist'},

    {
        "t": "p",
        "text": 'The gate between this section and section 7. Nothing in section 7 may be started on a screen that has not passed this list, and nothing in the build may start on a screen that is not in this section. The list is short because the alternatives are either a designer inventing a region that engineering never agreed to, or a screen shipping without a fee disclosure.',
    },

    {
        "t": "numbers",
        "items": [
            '**Every screen has a region table.** No region appears in a design that is not in the table, and no region in the table is missing from the design.',
            '**Every P1 region is present.** P2 regions may be deferred to a second release, and the deferral is recorded, not assumed.',
            '**Every money screen carries the fee disclosure.** Contribution, fee, and total charged, as three separate figures, on the pay screen, the receipt, the Ajo detail screen, and the join confirmation. This is the check most likely to be failed by a redesign and the most expensive to fail.',
            '**Every base-pool figure is labelled as the base pool**, with the derivation shown, and with the sentence that the fee is not part of the pool.',
            '**Every state in the two state machines has a designed screen.** Contribution: pending, paid, overdue, grace, defaulted, recovered, written off. Payment: initiated, pending, success, failed, cancelled, reversed, unknown. Payout: scheduled, funding, released, success, failed, held, and the retry. A missing state is the defect that produces a support ticket nobody can answer from a screenshot.',
            '**Every empty, loading, and error state is drawn.** Not described — drawn. They are regions like any other.',
            '**Every claim about money is a rendered server value.** No client-side computation of a fee, a pool, a payout, or a balance appears anywhere in the implementation.',
            '**Every irreversible action states what it locks** before the action, not after: activation locking positions, verification locking a number, a dispute decision closing the thread.',
            '**Every open decision is labelled where it is visible.** D-02, D-03, D-04 and D-08 appear on the screens they constrain, and no screen asserts a resolution it does not have.',
            '**No compliance claim appears anywhere.** No *licensed*, *approved*, *regulated*, *insured*, or *secured in escrow*. Where a fact depends on ProvidusUnity or on counsel, the copy says so.',
            '**Every screen below 1024 px on the console renders the unsupported-device page** rather than a squeezed layout.',
            '**Every interactive target is at least 44 by 44 CSS pixels** on touch viewports, and every drag interaction has a non-drag equivalent.',
        ],
    },

    {
        "t": "callout",
        "kind": 'DECISION',
        "title": 'What this section deliberately does not specify',
        "text": "Type sizes, colour values, spacing scales, corner radii, iconography, illustration, motion, and dark mode are all out of scope here and are specified in section 7. The reason for the boundary is that those decisions are reversible and these are not: a designer can change a radius without invalidating a wireframe, and a designer cannot change the position of the fee disclosure without invalidating the fee model's disclosure. **Anything moved from section 7 into section 6 has to justify itself against that asymmetry**, and the natural candidates — dark mode, motion, and type scale — do not.",
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Traceability back to section 3',
        "text": 'Every screen in this section carries a `SCR-WEB-nn`, `SCR-MOB-nn` or `SCR-ADM-nn` identifier from the reconciliation table at 3.6.4. Section 2 used the `SCR-MKT`, `SCR-APP` and `SCR-ADM` prefixes, and those names remain in use in that document; the mapping is published in 3.6.4 so a reader holding either document can move between them. The identifiers here are the ones to quote in design files, in pull requests, in analytics events, and in support macros, and **a screen is not considered specified until its identifier appears in this section, its route appears in section 3, and its flow appears in section 2**.',
    },

]
