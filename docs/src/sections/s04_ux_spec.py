"""
Section 4 — UI/UX Design Specification.

Source of truth: docs/src/CANONICAL.md
Authoring contract: docs/src/AUTHORING.md
Screen identifiers: section 3 (SCR-WEB-nn / SCR-MOB-nn / SCR-ADM-nn), published
in 3.6.4. Structure: section 6 (wireframes and region numbers), section 5
(design system), section 7 (high-fidelity visual layer), section 2 (flows 2.1 to
2.16), section 1 (business rules BR-001 to BR-032).

This section is the behavioural specification of the interface: what each screen
is for, who it is for, what it contains, what it does while it is loading,
empty, broken and successful, how it changes across a breakpoint, and how it
behaves for a person who is not using a mouse and a sighted screen. It does not
restate the screens — section 3 owns that — and it does not restate the visual
layer — section 7 owns that. Where this section states a number it states the
same number section 7 states, and the reconciliation rule is in 4.0.4.

The 2% platform fee is treated as a product requirement rather than a copy
requirement, and it is specified on every surface that can commit a member to a
payment. A member owing NGN 1,000.00 is charged NGN 1,020.00, of which
NGN 1,000.00 enters the round pool and NGN 20.00 is the AJO.ng platform fee; the
recipient of a ten-member round receives the base pool NGN 10,000.00 and never
NGN 10,200.00. The fee is never netted and never netted silently.

The tagline is "Your Ajo. Your Story."
"""

BLOCKS = [
    {"t": "h1", "text": "4. UI/UX Design Specification"},

    {
        "t": "lead",
        "text": (
            "AJO.ng is not a bank and it is not a wallet. It is a record-keeping "
            "system for a savings habit that already exists in Nigeria, and the "
            "interface has one job no amount of visual polish can substitute for: a "
            "person must be able to look at it and know, in a few seconds, what they "
            "owe, what they have paid, what they will receive, and when. This section "
            "specifies every screen in the product against that job — purpose, "
            "audience, layout, components, navigation, actions, content, fields, "
            "validation, all five non-happy-path states, responsive behaviour and "
            "accessibility — for sixty-two screens across three tiers, using the "
            "screen identifiers published in section 3."
        ),
    },
    {
        "t": "p",
        "text": (
            "**What this section is for.** Sections 3, 5, 6 and 7 between them tell "
            "an engineer where every screen lives, what every region contains and how "
            "every pixel looks. That is enough to build a product that is structurally "
            "correct and behaviourally wrong — a pay screen that looks right and can be "
            "double-submitted, a dashboard that is quiet about a held payout, a wizard "
            "that loses a member's fifteenth step. This section is the behavioural "
            "contract underneath the structure and the visuals, and it is written for "
            "the person who has to decide what happens when the request fails."
        ),
    },

    # =============================================================== 4.0
    {"t": "h2", "text": "4.0 How to read this section"},
    {"t": "h3", "text": "4.0.1 The sub-structure every screen uses"},
    {
        "t": "p",
        "text": (
            "Every screen in 4.4 to 4.23 is specified with the same sixteen-part "
            "sub-structure, in this fixed order, as a single specification table whose "
            "first column is the aspect and whose second column is the specification. "
            "The order is fixed so that two screens can be compared row by row, and so "
            "that a missing row is visible in review rather than in production."
        ),
    },
    {
        "t": "table",
        "head": ["#", "Aspect", "What it fixes", "Where the detail lives"],
        "rows": [
            ["1", "Purpose", "What the screen exists to accomplish in one sentence, and what it is explicitly not for.", "This table, row 1"],
            ["2", "Target user", "Which role, and which emotional state the screen is designed for.", "This table, row 2"],
            ["3", "Layout", "Region order, column behaviour, what is pinned, what scrolls.", "Section 6 region table"],
            ["4", "Components", "The component instances on the screen, by the names in 7.15 and 5.8.", "Sections 5 and 7.15"],
            ["5", "Navigation", "How a person arrives, how they leave, what the back affordance does.", "Sections 3.7 to 3.10"],
            ["6", "Primary CTA", "The one action, its exact label, and where it sits. At most one per screen.", "Sections 3.1.2 and 7.7.1"],
            ["7", "Secondary CTA", "Every other action, with its level and its placement.", "Section 7.7.1"],
            ["8", "Content", "The words and the data shown, including which figures are mandatory.", "Sections 4.25 and 7.12"],
            ["9", "Form fields", "Field by field: label, control, helper, required or optional, format.", "Table following this one, where the screen has a form"],
            ["10", "Validation rules", "Rule by rule, with the message shown and the moment it fires.", "Table following this one, where the screen has a form"],
            ["11", "Loading state", "Skeleton, spinner, progressive region, and what is never skeletonised.", "Sections 5.11 and 7.15"],
            ["12", "Empty state", "What shows when there is genuinely nothing, and whether zero is shown instead.", "Section 7.11.3"],
            ["13", "Error state", "Inline, banner and page-level treatment, and the reference a member is given.", "Section 4.24.6"],
            ["14", "Success state", "What confirms the action, for how long, and where it goes next.", "Section 4.24.5"],
            ["15", "Responsive behaviour", "What changes at each breakpoint, and what is removed rather than hidden.", "Section 4.3"],
            ["16", "Accessibility", "The criteria that bind hardest here, and the product-specific failure it prevents.", "Section 4.2"],
        ],
        "widths": [0.24, 1.06, 3.5, 1.7],
        "size": 7.0,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Screens with no form still declare rows 9 and 10",
        "text": (
            "A screen that collects no input still carries both rows, and both say so "
            "explicitly. This is deliberate: an absent row reads as an oversight, and a "
            "reader who cannot tell whether a screen has a form or whether nobody wrote "
            "the row down will assume the worse. The same applies to row 14 on a screen "
            "that has no successful action."
        ),
    },

    {"t": "h3", "text": "4.0.2 Numbering and cross-references"},
    {
        "t": "p",
        "text": (
            "Section headings are numbered `4.n`. Screen headings are numbered `4.n.m` "
            "and always carry the screen identifier from section 3, so that a screen "
            "here, a route in 3.6, a wireframe in section 6 and a component in 5.8 all "
            "name the same thing. `BR-nnn` is a business rule in section 1, `NFR-*` a "
            "non-functional requirement in 1.18, `C-nn` a constraint in CANONICAL.md, "
            "`D-nn` an open decision in CANONICAL.md section 9, `EC-nnn` an edge case in "
            "section 19. Money is written `NGN 1,000.00` in tables; the naira glyph is "
            "not used in a table because it renders unreliably in Word on the machines "
            "this document is read on."
        ),
    },

    {"t": "h3", "text": "4.0.3 What this section does not decide"},
    {
        "t": "bullets",
        "items": [
            "**Region structure.** Section 6 owns what a screen is made of. This section names the components and their order; it does not add a region.",
            "**Visual specification.** Colour, type, space, radius, elevation and motion belong to section 5 and section 7. This section references them and never restates a hex value.",
            "**Copy that is not regulated.** Marketing copy is a product and content decision. The only copy fixed here is copy the fee model fixes, and copy where a wrong word creates a financial misstatement.",
            "**Payment channel behaviour.** Which channels are offered, what they cost and how long they take require confirmation with ProvidusUnity in writing, and are labelled as such wherever they appear.",
            "**Verification policy.** Whether BVN or CAC verification is mandatory for every member or only above a threshold is D-04 and remains open. The interface supports both shapes and commits to neither.",
        ],
    },

    {"t": "h3", "text": "4.0.4 Reconciliation rule"},
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "When 4, 5, 6 and 7 disagree",
        "text": (
            "CANONICAL.md wins over all of them. Between the others: section 3 owns "
            "existence, section 6 owns structure, section 5 owns tokens and component "
            "definitions, section 7 owns visual behaviour, and this section owns "
            "interaction behaviour. A conflict is resolved by the owner of the topic, "
            "not by whichever document was read last, and it is fixed by editing the "
            "losing document rather than by a note in the winning one."
        ),
    },

    # =============================================================== 4.1
    {"t": "h2", "text": "4.1 UX principles and product tone"},
    {"t": "h3", "text": "4.1.1 The problem this design solves"},
    {
        "t": "p",
        "text": (
            "The design problem is not that there is no AJO.ng yet. It is that AJO.ng "
            "is asking for something it has no right to assume. The person opening the "
            "app is not a fintech customer who happened to hear about savings groups. "
            "They are someone already inside an Ajo, run by a bookkeeper or an elder, "
            "being asked to give a bank account to a company founded by two people, on "
            "a phone that may cost NGN 30,000, over a network that may drop "
            "mid-payment. Every principle below exists to make that ask survivable."
        ),
    },
    {
        "t": "table",
        "head": ["#", "Principle", "What it means in this product", "What it rules out"],
        "rows": [
            ["1", "**Trust before features**", "The first thing any screen shows is the person's own position, obligation and history. Features are never surfaced before the record.", "A carousel, a promotional banner, a referral prompt, or a growth experiment above the obligation block."],
            ["2", "**The number is never ambiguous**", "Every amount names what it is, what it includes and where it goes. Contribution, fee and total are three lines or the component is wrong.", "A single `NGN 1,020.00` with the fee explained afterwards. A total with no noun. A percentage with no count."],
            ["3", "**Plain Nigerian English**", "Short sentences, active voice, no loanwords where an English word exists. Nigerian usage is respected, not corrected; written copy is not forced into pidgin.", "Jargon: KYC, onboarding, leverage, escrow, float, commitment vehicle, financial instrument. None of these appear in member-facing copy."],
            ["4", "**No shame, ever**", "Defaulting, cancellation, a frozen account and a failed payment are stated as states with next steps. The person is never characterised, ranked or displayed to others.", "Red name badges. Public default lists. Streaks. A defaulting member shown to the Ajo with a coloured state. Any leaderboard."],
            ["5", "**No dark patterns**", "The default is always the option that costs the person nothing if they are wrong. Reversible where possible, explained where not.", "Pre-ticked consent. A cancel link smaller than a continue link. A countdown that ends a right. A preselected payment method."],
            ["6", "**The hard thing is next to the easy thing**", "Lock-in, the five-day enrolment window, the fee, the position lock and a payout hold are stated on the screen where they bite, not in a policy page.", "A terms link as the only disclosure. A lock-in warning only at the final wizard step. A hold explained in a help article."],
            ["7", "**One primary action per screen**", "At most one element is styled as the primary action. A second real action is a link or a secondary button, never a second primary.", "Two filled buttons of equal weight on a money screen. A primary label that changes without a state change."],
            ["8", "**The interface is quieter than the anxiety**", "A person checking whether their money arrived is anxious. Motion, colour and copy do not amplify that.", "Celebration on a routine payment, countdown timers on due dates, urgency counts, marketing voice inside tier 2."],
            ["9", "**Nothing is destroyed by a mis-tap**", "Destructive actions are confirmed with a sheet that names the consequence, are never the default, and are never adjacent to the safe option.", "Swipe-to-delete on a financial record, tap-and-hold to commit, an icon-only trash control on a touch viewport."],
            ["10", "**Say what the platform does not know**", "Where something is unconfirmed the interface says it is unconfirmed, rather than inventing a reassurance. Custody and licensing is D-02, open.", "Copy implying custody, deposit insurance, regulatory approval, or a partnership not confirmed in writing."],
        ],
        "widths": [0.24, 1.1, 2.6, 2.56],
        "size": 7.0,
    },

    {"t": "h3", "text": "4.1.2 Product tone: plain Nigerian English"},
    {
        "t": "p",
        "text": (
            "The tone is a competent friend explaining something carefully — not a brand "
            "voice, and not a bank. It is warm without being warm at you, confident "
            "without being promotional, and it never assumes familiarity with finance."
        ),
    },
    {
        "t": "table",
        "head": ["Dimension", "Rule", "Because"],
        "rows": [
            ["Sentence length", "Maximum 20 words in member-facing copy, 12 in a money surface. Two clauses maximum.", "A person reading on a 375 px screen in daylight parses one idea per line, and a money figure is unforgiving of ambiguity."],
            ["Second person", "Always *you* and *your*. Never *the user*, *the customer*, *the saver* or *the member* in member-facing copy.", "The member is a person in a savings group, not a segment. Third-person framing turns a commitment into a metric."],
            ["Register", "Everyday English, with Nigerian spelling: *organiser*, *recognise*, *cancelled*. The product's own vocabulary is kept and not anglicised: *Ajo*, *esusu*, *round*, *position*, *contribution*.", "Translating the product's vocabulary breaks the conversation it is joining. A person who says *Ajo* should see *Ajo* on screen."],
            ["Pidgin", "Not used in written copy and not policed in support conversations. Support agents may write as the member writes, provided the record stays legible.", "Forcing a register onto someone who does not use it in speech is patronising; forcing their register into a record is unprofessional."],
            ["Numbers", "Amounts as `NGN 1,020.00`. Counts as numerals. Dates as `20 Nov 2026`, never `11/20/2026`.", "`NGN 1,020.00` is unambiguous on every device, in every font, in every export, and survives being read aloud on a phone call to support."],
            ["Voice of errors", "Second person, present tense, states the fact and the next step. *Your payment did not go through. Your bank declined it. Try another method or contact your bank.*", "*Payment failed* reports a system state. The other sentence reports what happened to the person, which is what they need."],
            ["No exclamation marks", "In tier 1, tier 2, tier 3 and every transactional message, except the contact form acknowledgement.", "A receipt that says *Payment successful!* is a receipt that has started selling."],
            ["Emoji", "Prohibited in tier 2 and tier 3 product copy. Permitted in transactional SMS only, only one, and only where it improves a glanceable state.", "An emoji is a tone decision a component should not be making on the product's behalf."],
        ],
        "widths": [0.78, 3.0, 2.72],
        "size": 7.0,
    },

    {"t": "h3", "text": "4.1.3 Dark patterns: prohibited patterns and their permitted alternative"},
    {
        "t": "table",
        "head": ["Prohibited pattern", "Where it would be tempting", "The permitted alternative"],
        "rows": [
            ["Email capture before the fee is shown", "The marketing hero, the highest-traffic surface in the product", "Show the worked example — NGN 1,000.00 contribution, NGN 20.00 fee, NGN 1,020.00 charged, NGN 10,000.00 received — above the fold, ungated. A calculator is permitted; a form that captures an address is not."],
            ["Preselected payment method", "The pay screen, to save a tap", "No method selected on first view. The member picks, sees the amount they are about to be charged, then commits. One extra tap is the price of an informed payment."],
            ["Countdown timer on a due date or the enrolment window", "Ajo Detail, the wizard review step, the enrolment banner", "A plain date and a plain consequence. *Enrolment closes on 14 Nov 2026. If it does not fill, everyone is refunded in full.* A live timer creates pressure that is not in the product, and is unfair to a member on a slow connection."],
            ["Streaks, badges or a defaulting leaderboard", "The dashboard, to create a habit loop", "Nothing. Defaulting is private between the member, the organiser and platform risk (CAN §4). A roster visible to ten people is not a place to display a missed payment beyond the organiser's need to chase it."],
            ["Cancellation harder to find than payment", "Account closure, Ajo cancellation, dispute withdrawal", "Every exit is at the same depth as its entry. Where an exit is irreversible, that is stated before the entry, not discovered at the exit."],
            ["Snackbar as the only record of a consequential action", "A successful payment, a session revocation, a reminder dismissal", "A durable destination. A payment navigates to the receipt (SCR-MOB-11), a session revocation returns a confirmation list, a dismissed reminder returns to the schedule."],
            ["Mislabelled controls", "A close icon on a form with unsaved data; a Save button on a switch that saves on change", "Controls say what they do. A control that saves implicitly says *Saved* visibly and immediately."],
            ["Urgency framing", "The Pay tab, the notifications centre, the dashboard next-action block", "The amount and the date. *NGN 1,020.00. Due 20 Nov 2026.* A member who is owed the information will act; a frightened member calls support."],
            ["Guided dark flow", "A three-step interstitial before a support ticket", "One screen, one form, and a visible phone number and email address for the person who does not want to use a form."],
        ],
        "widths": [1.34, 1.86, 3.3],
        "size": 7.0,
    },

    {"t": "h3", "text": "4.1.4 Vocabulary that carries a promise"},
    {
        "t": "p",
        "text": (
            "Some words in this product make a promise, and a promise made in a label is "
            "a commitment the engineering and legal work has to honour. The list below "
            "is binding. A word not on it is ordinary copy and goes through normal "
            "content review; a word on it goes through the founders."
        ),
    },
    {
        "t": "table",
        "head": ["Word", "What it commits us to", "Never paired with"],
        "rows": [
            ["*contribution*", "The NGN 1,000.00 that enters the round pool. Not the NGN 1,020.00 that is charged.", "*charged*, *deposit* or *payment* — those are the total, and using them for the base amount is how the fee gets netted by accident."],
            ["*service fee* / *AJO.ng fee*", "2% of the contribution, charged on top, never deducted from the contribution, never reducing a payout.", "*charge* on its own, which reads as a penalty, and *tax*, which is D-06 and open."],
            ["*total to pay*", "The exact figure that will leave the member's account, itemised above it.", "*amount* or *total* on its own."],
            ["*base pool*", "What the recipient receives: NGN 10,000.00 in the canonical example, never NGN 10,200.00.", "*total collected*, *total in the round*, or *payout* without qualification."],
            ["*organiser*", "Creates the Ajo, invites and removes before activation, proposes order, requests release. Does not control payouts, does not guarantee another member's debt, has no authority after completion (BR-008).", "*accountable for*, *responsible for the money*, *guarantor* — the last is a legal claim and is false."],
            ["*position*", "A member's turn in the rotation, locked on activation.", "*turn* in a state label: *turn* implies flexibility the product does not have."],
            ["*payment*", "A `contributions` row moving through the provider state machine.", "*transfer complete* before the webhook has verified it."],
            ["*held*", "A payout that is fully owed and not yet funded. It does not reduce and it does not disappear.", "*delayed*, which blames our lateness rather than naming a funding gap, and *pending*, which is also a payment state."],
            ["*defaulted*", "A private state between the member, the organiser and platform risk.", "*failed member*, *defaulter*, *cheater* in any member-facing surface."],
            ["*verified*", "A completed `verification_checks` row with a named outcome and a stated retention period.", "*trusted*, *safe*, *approved by the bank* — all unconfirmed claims."],
            ["*refund*", "A confirmed return of funds with a reference and a stated expected date.", "*reversed* used loosely for money that has not moved. Provider-side `REVERSED` and member-facing *refund* stay distinct."],
            ["*Your Ajo. Your Story.*", "The locked tagline (CAN §0).", "Every other tagline, including *Save together. Take your turn.*, which is not used."],
        ],
        "widths": [0.86, 2.84, 2.8],
        "size": 6.9,
    },

    # =============================================================== 4.2
    {"t": "h2", "text": "4.2 Accessibility standard"},
    {"t": "h3", "text": "4.2.1 The target, and what it is not"},
    {
        "t": "callout",
        "kind": "WARNING",
        "title": "WCAG 2.2 AA is the design target, not a conformance claim",
        "text": (
            "**This specification sets WCAG 2.2 Level AA as the design and build target "
            "for every screen in this document. It does not claim that AJO.ng conforms "
            "to WCAG 2.2 Level AA, and no such claim may be published, marketed, or "
            "included in any terms, privacy notice, app-store listing or sales document "
            "until a conformance claim has been produced by a human accessibility test "
            "against the built product and reviewed. An unverified conformance claim is "
            "a false statement to customers, and the people least able to challenge it "
            "are exactly the people who would be harmed by it.** The verification plan "
            "is 4.2.4 and its resourcing is an open item."
        ),
    },
    {
        "t": "p",
        "text": (
            "**Why AA is the target rather than AAA.** The demographic reason comes "
            "first: an Ajo recruits through social trust, and social trust recruits the "
            "oldest member of the group, who is trusted with money and is often not "
            "trusted with interfaces. It also recruits members on low-end Android "
            "devices where a two-megabyte bundle is a four-second first paint, and "
            "members on entry-level handsets over networks that drop mid-request. The "
            "technical reason comes second: several of the failure modes in 4.2.2 are "
            "expensive to fix after a screen is built, so targeting AA front-loads the "
            "cost into design instead of charging it to members."
        ),
    },
    {
        "t": "table",
        "head": ["Commitment", "What is targeted", "Status"],
        "rows": [
            ["**WCAG 2.2 Level AA**", "All A and AA success criteria across every tier-1, tier-2 and tier-3 screen in this document.", "Design and build target. Not yet verified. No public claim is made."],
            ["**Selected AAA where it is cheap**", "2.3.3 Animation from Interactions, 1.4.8 Visual Presentation, 2.4.11 Focus Not Obscured (Minimum), 2.5.5 Target Size (Enhanced).", "Targeted. Cheap because the design system makes them the default rather than an addition."],
            ["**Section 508 / EN 301 549**", "Not targeted. Requires the conformance claim above to be produced first.", "Out of scope for v1. **Requires review by qualified Nigerian counsel** if public-sector or partner procurement ever enters scope."],
            ["**Plain-language target**", "Member-facing transactional copy at or below a defined reading age, checked in content review per 4.25.6.", "Target. No external standard is claimed and no certification is implied."],
            ["**Assistive-technology coverage**", "Android TalkBack, iOS VoiceOver, NVDA on Windows, browser zoom to 400 percent, and a switch-access pass on the money journey.", "Required before launch. See 4.2.4."],
        ],
        "widths": [1.12, 3.34, 2.04],
        "size": 7.0,
    },

    {"t": "h3", "text": "4.2.2 Product-specific failure modes"},
    {
        "t": "p",
        "text": (
            "A generic accessibility checklist would catch almost none of these. Each is "
            "a property of *this* product — a rotating savings scheme settled by people "
            "who did not choose the software — so each carries a binding rule rather "
            "than a guideline. Every rule here is carried into the per-screen "
            "Accessibility row in 4.4 to 4.23."
        ),
    },
    {
        "t": "table",
        "head": ["Failure mode", "Who it affects", "Binding rule", "Criterion"],
        "rows": [
            ["The 2% fee hidden inside a single total", "Everyone; most acutely low-literacy users, screen reader users, and anyone paying by reading the number not the line", "The money surface is one component that cannot render without separate contribution, fee and total lines. There is no compact variant. See 4.12.2.", "1.3.1, 3.3.2, 1.4.1"],
            ["State carried by colour only", "Colour-blind members, low vision, and every member in direct sunlight", "Every state renders as a word inside a filled pill. A coloured dot is decorative and carries `aria-hidden`. A red cell never means late on its own.", "1.4.1, 1.4.11"],
            ["Amounts announced without a currency or a noun", "Screen reader users", "Every amount element has an accessible name containing the currency code and the full value: *Total to pay, NGN 1,020.00*. A table of bare numbers is never exposed without row headers.", "1.1.1, 1.3.1, 2.4.6"],
            ["Progress communicated only by bar width", "Screen reader users, cognitive load", "Every progress bar is `aria-hidden` and is preceded by a live text count: *4 of 10 rounds funded*. The bar is the decoration and the text is the truth.", "1.1.1, 1.3.1, 4.1.3"],
            ["A money action below the 44 px minimum, or a destructive action the same size as a safe one", "Motor impairment, tremor, one-handed use, older members", "Every interactive target is at least 44 by 44 CSS pixels, and every control that moves money is at least 48 by 48 on a touch viewport. Destructive targets are never adjacent to a safe target within 24 pixels.", "2.5.8, 2.5.5"],
            ["A sheet or sticky bar covering the focused control", "Keyboard users, switch access, screen magnification at 200 percent", "A focused element is never left obscured. Sheets trap focus, close on Escape, and restore focus to the opener. Sticky action bars add bottom padding equal to their height plus the safe area.", "2.4.11, 2.1.2, 2.4.3"],
            ["A session timeout or a network drop during a payment", "Everyone on a slow or intermittent connection; anyone using assistive technology that adds latency", "The money journey holds a five-minute warning modal with an extend action, and a payment in flight is never abandoned by a timeout. A payment screen is never cached and never restored to a pre-commit state.", "2.2.1, 3.3.4"],
            ["Ambiguous link text read out of context", "Screen reader users navigating by links list", "Link text names its destination. *Read more* and *click here* are prohibited in all three tiers. Any links list is reviewed as a standalone list.", "2.4.4, 2.4.9"],
            ["Cyan or Gold used as body text on a light surface", "Low vision, sunlight, older members", "Text on a light surface is Dark, Primary, or a named semantic role. Cyan and Gold are fills, chart series and accents only. A contrast assertion runs in the token build.", "1.4.3, 1.4.11"],
            ["A custom select, slider or date picker that is not fully keyboard operable", "Keyboard, motor, switch access", "Every custom control is operable by keyboard with a visible focus ring, supports type-ahead where it has options, and exposes its value and range to assistive technology as text.", "2.1.1, 2.1.2, 4.1.2"],
            ["A form error that only appears visually", "Screen reader users, and everyone under time pressure", "`aria-invalid` is set, the error is referenced by `aria-describedby`, focus moves to the first invalid field on submit, and the spoken sentence is identical to the printed one. See 4.24.7.", "3.3.1, 3.3.2, 3.3.3"],
            ["Time-limited content with no way to extend", "Members on slow connections, members using a screen reader", "No tier-2 content expires by time except a payment authorisation, and that one has a stated deadline with an extend action.", "2.2.1"],
        ],
        "widths": [1.28, 1.42, 2.78, 0.52],
        "size": 6.8,
    },

    {"t": "h3", "text": "4.2.3 Structural requirements applied to every screen"},
    {
        "t": "bullets",
        "items": [
            "**One `h1` per screen**, carrying the screen name and, on a record screen, the record's short identifier. The document outline is the navigation model.",
            "**Correct landmarks**: one `main`, one `nav` for primary navigation, one `nav` for breadcrumbs where they exist. A financial application is read by assistive technology as a list of regions, and a missing landmark deletes a region from that list.",
            "**Skip links** to the main content and, on money screens, a second skip link to the money summary. Those are the two things a screen reader user came for.",
            "**Focus is visible at all times**: a 2 px Primary ring at a 2 px offset, never removed without replacement, visible on Deep, on Cloud, on White and on a Primary fill.",
            "**Focus order equals reading order.** A screen whose DOM order differs from its visual order is a defect caught in review, not shipped.",
            "**Touch targets** are at least 44 by 44 CSS pixels, and 48 by 48 for anything that moves money, at every breakpoint including desktop, where a reduced size is not justified by a mouse.",
            "**Text resizes to 200 percent and zoom reaches 400 percent** with reflow and no horizontal scrolling at 320 CSS pixels. Nothing is hidden at any text size and no information is available only on hover or focus.",
            "**Reduced motion is honoured completely**: every animation becomes an instant state change and every transition becomes a cut. No information is lost and no screen is hidden.",
            "**Forced-colours mode stays usable**: state pills become outlined with their text intact, the progress fill uses `forced-color-adjust: none` on the fill only, and the money surface keeps its rules and labels rather than relying on fill differentiation.",
        ],
    },

    {"t": "h3", "text": "4.2.4 Verification plan — how the target becomes a claim, if it does"},
    {
        "t": "p",
        "text": (
            "Automated tooling is necessary and insufficient. It catches roughly a third "
            "of WCAG issues and almost none of the twelve failure modes in 4.2.2, "
            "because those are semantic and content problems rather than attribute "
            "problems. The plan below is what has to happen, in order, before any "
            "conformance statement is published."
        ),
    },
    {
        "t": "table",
        "head": ["#", "What", "Who", "When", "Pass condition"],
        "rows": [
            ["1", "Automated scan of every route in 3.6 against the built product, not the design, on each release candidate.", "Engineering", "Every release candidate", "No new violations above the filed baseline. New violations block the release."],
            ["2", "Keyboard-only walk of the member journey: register, verify, create an Ajo, join, pay, take a receipt, raise a dispute.", "At least one person who did not build it", "Pre-launch, then each release", "Completed with no trap, no obscured focus, no unreachable control."],
            ["3", "Screen-reader walk of the same journey: TalkBack and VoiceOver at minimum, plus NVDA on Windows.", "At least one person who uses a screen reader daily", "Pre-launch, then each release", "Every amount announced with currency and noun; every state announced as a word; every error announced on submit."],
            ["4", "Low-vision and magnification pass at 200 percent text and 400 percent zoom, in forced-colours mode, on the cheapest supported Android handset.", "A person with low vision, or a documented substitute", "Pre-launch", "No loss of content, no horizontal scroll, no reliance on colour."],
            ["5", "Cognitive walk with a member who has never used a mobile banking application. This is a real risk, not a token one, because the population this product recruits is not the population these screens are usually tested with.", "A recruited member, not a colleague", "Pre-launch", "Completed without a verbal instruction from the facilitator at the fee disclosure and the payout screens."],
            ["6", "Independent review by a qualified accessibility professional, with a written report.", "External, paid", "Before any public conformance statement", "A written report either confirms AA or lists the specific failures. **Requires review by qualified Nigerian professionals; budget and resourcing are an open item.**"],
        ],
        "widths": [0.24, 2.5, 1.18, 1.1, 1.48],
        "size": 6.9,
    },
    {
        "t": "callout",
        "kind": "ASSUMPTION",
        "title": "The verification plan is an unresourced commitment",
        "text": (
            "Steps 2 to 6 of 4.2.4 are a resourcing commitment that has not been agreed "
            "by the founders. It is written as an assumption rather than a plan because "
            "writing it as a plan would imply it is funded. If it is not resourced, the "
            "correct action is to publish no accessibility statement at all, not to "
            "publish a softened one. **Owner: Founders. Decision required before v1 "
            "launch.**"
        ),
    },

    {"t": "h3", "text": "4.2.5 What is explicitly not claimed"},
    {
        "t": "bullets",
        "items": [
            "**No regulatory accessibility claim.** NDPA obligations in Nigeria require review by qualified Nigerian counsel and are not discharged by WCAG conformance alone.",
            "**No claim about third-party components.** Any vendored component is held to the same rules or is not used. A vendored select that fails 2.1.1 fails the screen it sits on.",
            "**No claim that automated testing passed.** A clean scan is one input to the plan and is never quoted as a result on its own.",
            "**No claim of AAA anywhere**, including in marketing. Section 7.14.1 targets selected AAA criteria rather than claiming the level, and a marketing claim would outrun both.",
        ],
    },

    # =============================================================== 4.3
    {"t": "h2", "text": "4.3 Responsive strategy and breakpoint matrix"},
    {"t": "h3", "text": "4.3.1 Strategy"},
    {
        "t": "p",
        "text": (
            "There is one application, not an app and a website. Tier 2 is a single "
            "responsive product at `/app`; there is no separate mobile build, no "
            "separate API surface, and no behaviour that exists only on a phone. The "
            "breakpoints below are the same six named in the visual specification and "
            "the sitemap, and they are the only breakpoints that exist. A component may "
            "respond at a container width, but no screen introduces a seventh named "
            "breakpoint."
        ),
    },
    {
        "t": "bullets",
        "items": [
            "**Mobile first, not mobile only.** Every layout is authored at 320 CSS pixels, because a 375 pixel design breaks on the cheapest supported device and the members who most need the product are disproportionately on it. 320 is the minimum supported viewport and is verified in review.",
            "**Content reflows; data does not disappear.** Below 768 pixels a data table becomes a card list carrying the same fields in the same order. A field is never dropped to make a table fit; a column is dropped only when the same value is already visible elsewhere on the same screen.",
            "**Actions consolidate by consequence, not by count.** On mobile a screen with more than two secondary actions moves them into an overflow sheet, but the primary action and the single most consequential secondary action stay in the in-flow action bar. Destructive actions never move into a sheet; they get their own confirmation route (4.24.1).",
            "**The money surface is identical at every width.** Contribution, fee, total, the same order, the same labels, the same rule. It is never condensed into one line on a small screen. This is the one component that is not responsive, and the reason is that it is the one component that must not vary.",
            "**Tier 1 behaves like a website**: a horizontal top navigation above 768 pixels, a logo, one sign-in affordance and a sheet below that, and no bottom bar at any width. Tier 3 behaves like a console: a fixed rail and no mobile layout at all, per 4.3.5.",
        ],
    },

    {"t": "h3", "text": "4.3.2 Breakpoint matrix"},
    {
        "t": "table",
        "head": ["Name", "Viewport", "Tier 1 nav", "Tier 2 nav", "Cols", "Gutter", "Margin", "Notes"],
        "rows": [
            ["`xs`", "320 to 374", "Logo, sign in, sheet", "Bottom bar, 5 tabs", "1", "—", "16 px", "Minimum supported, verified in review. The fee breakdown and the bottom bar both fit at 320 with a 44 px target."],
            ["`sm`", "375 to 767", "Logo, sign in, sheet", "Bottom bar, 5 tabs", "1", "—", "16 px", "Design width. The reference for every mobile wireframe in section 6."],
            ["`md`", "768 to 1023", "Horizontal, up to 6", "72 px icon rail", "2", "24 px", "24 px", "Bottom bar is replaced. The More sheet is not needed; the rail carries every destination."],
            ["`lg`", "1024 to 1279", "Horizontal, 8 items", "240 px rail", "8", "24 px", "32 px", "Reading column caps at 720 px. Two-column forms become viable. Tables keep all columns with reduced padding."],
            ["`xl`", "1280 to 1439", "Horizontal, 8 items", "240 px rail", "12", "24 px", "40 px", "Right context panel appears on detail screens. Stat tiles go three across."],
            ["`2xl`", "1440 and above", "Horizontal, 8 items", "240 px rail", "12", "24 px", "48 px", "Console design width. Content is capped at 1200 px and never stretched."],
        ],
        "widths": [0.36, 0.62, 0.72, 0.66, 0.3, 0.34, 0.42, 3.08],
        "size": 6.8,
    },

    {"t": "h3", "text": "4.3.3 What changes at each transition"},
    {
        "t": "table",
        "head": ["Transition", "What changes", "What does not change", "Risk at the transition"],
        "rows": [
            ["320 to 375 (`xs` to `sm`)", "Nothing structural. 16 px gutters on both.", "The bottom bar, the money surface, every touch target size.", "None identified."],
            ["767 to 768 (`sm` to `md`)", "Bottom bar becomes a 72 px rail. Card grids become two columns. A card list becomes a real table, keeping every field.", "Region order, action hierarchy, the primary action's label.", "A card list that carried a field the table lacks. Field inventory must be identical in both representations; checked in review per 4.3.4."],
            ["1023 to 1024 (`md` to `lg`)", "Rail expands to 240 px. Reading column caps at 720 px. Two-column form layouts become available.", "The single primary action. The position of the money surface relative to the commit action.", "A form laid out in one column that becomes two, which can move a field below the fold on submit. Field order is fixed and is never reordered by breakpoint."],
            ["1279 to 1280 (`lg` to `xl`)", "Right context panel appears on detail screens. Stat tiles go from two across to three.", "Anything that carries a fee, a state, or a required action.", "Content reflowing into a second column that separates a label from its value. Related fields are never split across columns in a money form."],
            ["1439 and above (`2xl`)", "Content centres at 1200 px. Marketing hero goes full-bleed.", "Everything.", "A full-bleed treatment swallowing the money table. The worked example and every money block stay inside the reading column at every width."],
        ],
        "widths": [0.94, 2.1, 1.86, 1.6],
        "size": 6.9,
    },

    {"t": "h3", "text": "4.3.4 Content priority under reflow"},
    {
        "t": "p",
        "text": (
            "When a layout cannot hold everything, the order below decides what is kept, "
            "what moves, and what is removed. It is fixed, applied per region, and "
            "checked against the field inventory in section 6 in design review."
        ),
    },
    {
        "t": "numbers",
        "items": [
            "**P1 — the money and the state.** Any amount, any due date, any lifecycle state word, the fee breakdown, the primary action, the commit action. These are never removed, never collapsed, and never pushed below a fold that requires scrolling to complete a payment.",
            "**P2 — the action.** Secondary actions, filters, the context switcher, and the record identity: which Ajo, which contribution, which dispute reference.",
            "**P3 — the explanation.** Helper text, state explanations, the default-handling note, the destination of each part of an amount. Moves to a disclosure on mobile and is never deleted, because a collapsed explanation is a hidden one.",
            "**P4 — the supporting record.** Timestamps to the minute, reference identifiers, provider names, technical detail. Available on the record's detail surface at every width, and inline only above `md`.",
            "**Removal requires a replacement.** A column may be removed from a table at a narrow width only when its value appears elsewhere on the same screen. There is no other basis for removal, and no removal of P1 or P2 is permitted at any width.",
        ],
    },

    {"t": "h3", "text": "4.3.5 The admin console device policy"},
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "The admin console is not designed below 1024 CSS pixels",
        "text": (
            "Tier 3 renders a *device not supported* page below 1024 pixels at every "
            "tier-3 route, with a link to contact support. A risk decision or a dispute "
            "decision is made by comparing a member's record, an Ajo's record, a ledger "
            "posting and a verification outcome at the same time, and making that "
            "comparison on a 375 pixel screen is a safety problem rather than a layout "
            "problem. The trade-off is real: a support or risk officer working a "
            "phone-first region cannot use the console, and the answer to that is a "
            "staffing decision, not a responsive layout. **Owner: Founders. Revisit "
            "only if support is staffed from a phone-first region.**"
        ),
    },
    {"t": "pagebreak"},

    # =============================================================== 4.4
    {"t": "h2", "text": "4.4 Marketing website — tier 1"},
    {
        "t": "p",
        "text": (
            "Twelve content pages. Tier 1 has one job: answer the questions that "
            "block a signup, in the order a sceptical Nigerian saver actually asks "
            "them, and disclose the fee before the person has given us anything. No "
            "tier-1 page requires an account to be useful, no tier-1 page makes a "
            "claim about an individual, and no tier-1 page captures an email address "
            "before it has said what the product charges."
        ),
    },
    {
        "t": "table",
        "head": ["Screen", "Route", "Purpose in one line", "Mandatory content"],
        "rows": [
            ["SCR-WEB-01", "`/`", "State the offer, show the mechanic, disclose the fee above the fold.", "The canonical money figures"],
            ["SCR-WEB-02", "`/how-it-works`", "Explain the cycle in six steps.", "Steps 4 and 5 are the money steps and may not be merged or reordered"],
            ["SCR-WEB-03", "`/features`", "Organiser and member tools.", "No performance claims, no traction claims"],
            ["SCR-WEB-04", "`/safety-and-trust`", "The safeguards, stated plainly.", "Must name the custody question as open"],
            ["SCR-WEB-05", "`/fees`", "The single canonical fee page.", "The eleven-row worked table, transcribed"],
            ["SCR-WEB-06", "`/about`", "Founders, context, contact.", "Pre-launch: no traction claims"],
            ["SCR-WEB-07", "`/faq`", "Ranked objections answered.", "Default handling and cancellation first"],
            ["SCR-WEB-08", "`/contact`", "A person, reachable, quickly.", "Published response expectation"],
            ["SCR-WEB-15", "`/terms`", "The versioned contract.", "Organiser is not a guarantor; fee and tax language pending"],
            ["SCR-WEB-16", "`/privacy`", "What is collected and who sees it.", "**Counsel review required before launch**"],
            ["SCR-WEB-17", "`/status`", "Account restricted notice.", "What still works, who to contact, the reference"],
            ["SCR-WEB-18", "`/404`", "Tier-1 not found.", "One way forward and a link home"],
        ],
        "widths": [0.66, 1.02, 1.7, 3.12],
        "size": 7.0,
    },

    {"t": "h3", "text": "4.4.1 Home — SCR-WEB-01"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Make a stranger understand a rotating savings scheme in one screen, tell them exactly what AJO.ng charges, and give them one way to start. It is not a lead-capture page and it gates nothing."],
            ["Target user", "Anyone who has heard the word *Ajo* or *esusu* and has never been in one, plus the organiser looking for a digital record for a group that already meets physically. The emotional state is curiosity, not intent to buy."],
            ["Layout", "Full-bleed hero on Deep, then alternating 1200 px sections: standfirst and worked example, how it works, safety, fee, closing call to action, footer. The hero is the only full-bleed region; every money table sits inside the 720 px reading column."],
            ["Components", "`TopNav`, `Hero`, `StepList` (6 items), `MoneyTable` (canonical), `FeatureGrid`, `FeeCalculator`, `Callout` (NOTE), `Footer`, `Button` (primary), `Button` (secondary)."],
            ["Navigation", "Horizontal top nav, eight items maximum, no mega-menu. The footer carries the full sitemap plus the legal routes. UTM parameters are consumed once and stripped from every internal link."],
            ["Primary CTA", "*Create free account*, to `/register`. One filled Primary button, in the hero and repeated once in the closing section as the same component at the same level."],
            ["Secondary CTA", "*See how it works* (tertiary link) in the hero; *Read the fees* (tertiary link) beside the worked example. Never a second filled button."],
            ["Content", "Standfirst: *the same scheme, recorded properly*. The six steps. The canonical money table verbatim. The default-handling note stating that other members are never charged extra and that a defaulting member is never named in the Ajo. Safety summary. Fee link. Tagline *Your Ajo. Your Story.* in the footer."],
            ["Form fields", "None. A fee calculator is permitted and is a permitted form because it discloses rather than captures: input a contribution amount, output contribution, fee at 2 percent, total charged, and the base pool at ten members. An email capture before the fee is shown is prohibited."],
            ["Validation rules", "Calculator input: numeric; minimum NGN 1,000.00; maximum the contribution cap set by risk (open). One rule, inline, on blur and on input once the field has been blurred. No other input on this page."],
            ["Loading state", "None. Tier-1 content is statically rendered. The calculator computes locally on input with no network call and shows a result synchronously, because a calculator that flickers teaches a member not to trust the number."],
            ["Empty state", "Not applicable. There is no member data on tier 1 and nothing can be empty."],
            ["Error state", "Page-level only, per 4.4.12. The calculator has no error state beyond its inline validation message."],
            ["Success state", "Not applicable. No action on this page succeeds or fails; the only outcome is navigation."],
            ["Responsive behaviour", "Below 768: the hero stacks, the step list becomes a numbered vertical sequence with a 48 px minimum row, the money table becomes a stacked definition list preserving row order, and the top nav collapses to logo, sign in and a sheet. No region is removed at any width, and the worked example is never abbreviated."],
            ["Accessibility", "Landmarks: one `header`, one `main`, one `nav` for the top navigation, one `footer`. The money table is a real table with a caption and row headers. The calculator result is announced in a polite live region that states contribution, fee, total and base pool in that order. No content lives in an image. On the Deep hero all text is White, and the fee is set at label size, never at caption size in Gold."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.4.2 How It Works — SCR-WEB-02"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Explain the rotation in six numbered steps in the order a member lives it, and show the exact figures at the step where each occurs. This is the page a sceptic reads end to end and then decides."],
            ["Target user", "An evaluation-stage reader, often referred by someone already using the product, comparing AJO.ng against the paper record book or the group chat they already use."],
            ["Layout", "720 px reading column, single column, no grid. Title and standfirst, the six steps as a numbered list, the canonical money table beneath, the default-handling callout, then a closing CTA band on Deep."],
            ["Components", "`StepList` (6), `MoneyTable` (canonical), `Callout` (NOTE, default handling), `Button` (primary), `Footer`."],
            ["Navigation", "Same top nav as SCR-WEB-01. In-page anchors for the six steps on desktop; dropped on mobile, where the page is short enough not to need them."],
            ["Primary CTA", "*Create free account*, in the closing band only. One filled button. Repeating it in the page body would be a second primary and is prohibited."],
            ["Secondary CTA", "*See the full fees* (tertiary link) beneath the money table, and *Read the safety details* (tertiary link) in the closing band."],
            ["Content", "Step 1 the group agrees the amount. Step 2 positions are set and locked on activation. Step 3 each round, everyone pays by the due date. Step 4 AJO.ng keeps NGN 20.00 as its fee, charged on top. Step 5 when the round is fully collected, whoever it is due to is paid NGN 10,000.00. Step 6 the next round begins. **Steps 4 and 5 are the money steps and may not be merged, reordered, or summarised into one.**"],
            ["Form fields", "None. The fee calculator from SCR-WEB-01 may be repeated beneath the money table; it is optional and is the only permitted input on this page."],
            ["Validation rules", "Calculator only, per 4.4.1."],
            ["Loading state", "None. Static content."],
            ["Empty state", "Not applicable."],
            ["Error state", "Page-level only, per 4.4.1."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "Single column at every width. Step numerals move from a 32 px hanging gutter to an inline prefix below 768. The money table becomes a stacked list, preserving row order and the two bold rows."],
            ["Accessibility", "The steps are an ordered list, and each step number is part of the accessible name so a screen reader user hears *step 4 of 6*. The two money steps sit under their own subheading so they can be reached by heading navigation. No step is conveyed by an icon or a colour."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.4.3 Features — SCR-WEB-03"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "List what the product does for the organiser and what it does for the member. It is not a comparison table and it is not a claims page."],
            ["Target user", "The organiser of an existing group, deciding whether to move their record-keeping; and a member being convinced by that organiser."],
            ["Layout", "Title, then two columns — organiser, member — on `lg` and above, stacking in that order on mobile. Each column is a list of features with a short heading and one sentence each. No grid of feature icons with three-word labels."],
            ["Components", "`FeatureList` (2 columns), `Callout` (NOTE), `Button` (primary), `Footer`."],
            ["Navigation", "Same top nav."],
            ["Primary CTA", "*Create an Ajo*, in the closing band. One filled button."],
            ["Secondary CTA", "*Read how it works* (tertiary link) in the closing band."],
            ["Content", "Organiser: the roster, the round calendar, reminders, position proposals, the five-day enrolment window. Member: the schedule, one-tap payment with the fee shown before commit, a receipt for every payment, a statement, a payout record. Every feature listed must exist at v1 or be marked as planned with a stated intention. No unavailable feature is listed as available."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "None. Static content."],
            ["Empty state", "Not applicable."],
            ["Error state", "Page-level only."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "Two columns to one below `md`, organiser first. No feature is removed at any width; where the two lists are long, the member list follows the organiser list rather than interleaving with it."],
            ["Accessibility", "The two lists are labelled sections with real headings, so they appear in a heading navigation list. A feature is a heading and a paragraph, never a heading and a colour. No feature icon is the only carrier of a category name."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.4.4 Safety and Trust — SCR-WEB-04"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Answer the question *what stops the organiser taking the money*, and answer it honestly, including where the honest answer is *we do not know yet*."],
            ["Target user", "The decision-maker, usually the person in the group trusted with the fund, being asked to route it through a new system. Sceptical, specific, and unimpressed by reassurance."],
            ["Layout", "Reading column, single column, one `h2` per safeguard with a short paragraph and, where relevant, a small table of who can do what. Deliberately not a grid of trust badges."],
            ["Components", "`ProseSection` (6), `Table` (role capability, transcribed from the canonical role rules), `Callout` (DECISION, custody position), `Button` (primary), `Footer`."],
            ["Navigation", "Same top nav. A contents list appears at `xl` and above and is absent below that rather than collapsed."],
            ["Primary CTA", "*Create free account*, in the closing band. On this page the fee link is a tertiary link; the page's primary action is the one repeated across tier 1."],
            ["Secondary CTA", "*Read the terms* and *Contact us* (tertiary links) in the closing band."],
            ["Content", "Six sections. 1, Positions lock when the Ajo activates and a change needs a formal replacement request. 2, The enrolment window is exactly five days; an unfilled Ajo is cancelled and refunded in full. 3, What happens when someone does not pay: reminder, retry where the payment partner supports it, 48-hour grace, organiser told privately, recovery. Other members are never charged extra and the member is never named in the Ajo. 4, Who can see what: members see the roster and the round state, never another member's bank details, identity documents or dispute. 5, The record: the ledger is append-only, no role including the founders can edit or delete an entry, and a correction is a reversing entry. 6, What we do not yet know: the custody and licensing position and the payment partner's charges, stated as open."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "None."],
            ["Empty state", "Not applicable."],
            ["Error state", "Page-level only."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "Single column throughout. The role-capability table becomes a stacked list below 768, one role per block, with *can* and *cannot* as two labelled sub-lists. The contents list is removed below `xl` and the section count is stated at the top instead."],
            ["Accessibility", "The role-capability table has a real caption and row headers. The section naming the open custody question is a DECISION callout whose title is in the accessible outline, so it is reachable from the contents list and from heading navigation."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.4.5 Fees — SCR-WEB-05"},
    {
        "t": "p",
        "text": (
            "**This is the canonical fee page and the only place on tier 1 where the 2 "
            "percent is quantified.** Every other surface that mentions a figure "
            "transcribes from here. If a figure changes on this page it changes on "
            "every screen, and that change is a code review, not a copy edit."
        ),
    },
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "State exactly what AJO.ng charges, on what, when, and what is not charged. Nothing else. There is no pricing tier, no plan, and no upsell on this page, and there never will be: the product charges one rate."],
            ["Target user", "Anybody, at any moment in the funnel, including a member who has already paid and is checking whether they were overcharged. It is written to be re-read, not read once."],
            ["Layout", "Reading column. H1, a one-sentence statement of the rate, the canonical eleven-row money table, the three-line breakdown block, a note on what is not charged, a note on the open questions, then the closing CTA band."],
            ["Components", "`MoneyTable` (canonical, eleven rows), `MoneyBlock` (three lines), `Callout` (DECISION, partner charges and tax), `Button` (primary), `Footer`."],
            ["Navigation", "Same top nav. Linked in the footer of every tier-1 page, in every transactional email, and from the More sheet in tier 2, so a member can always check the fee without asking."],
            ["Primary CTA", "*Create free account*, in the closing band. One filled button."],
            ["Secondary CTA", "*Read how it works* and *Read the terms* (tertiary links) in the closing band."],
            ["Content", "Rate statement: *AJO.ng charges 2% on every contribution. It is added to the amount you contribute. It is never taken from it, and it never reduces what you receive.* Then the canonical table: members 10; contribution per member per round NGN 1,000.00; platform fee 2% NGN 20.00; total charged per member NGN 1,020.00; base pool paid to the recipient NGN 10,000.00; total collected in the round NGN 10,200.00; platform fee retained in the round NGN 200.00; rounds 10; total paid in by one member NGN 10,200.00; total received by the recipient at their turn NGN 10,000.00; platform fee over the full Ajo NGN 2,000.00; total collected across the Ajo NGN 102,000.00. Then what is not charged: no fee on receiving a payout, no fee on cancelling before activation. Then the open questions: partner charges and tax treatment, stated as unresolved."],
            ["Form fields", "The calculator, optional, identical to SCR-WEB-01."],
            ["Validation rules", "Calculator: numeric input, NGN 1,000.00 to the current contribution cap. Reject non-numeric input without clearing the field."],
            ["Loading state", "None."],
            ["Empty state", "Not applicable."],
            ["Error state", "Page-level only."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "The eleven-row table becomes a stacked list below 768, in the same order, with the two bold rows kept bold. The three-line breakdown never changes at any width. The rate statement is never set below body size."],
            ["Accessibility", "The table has a caption naming the worked example and row headers. The two emphasised rows are emphasised in the accessible name as well as in weight, because weight alone is unreliable at high magnification. The rate statement is a paragraph, not a heading, so it is not skipped by heading navigation but is read in full."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The two rows that may never be merged or reordered",
        "text": (
            "**Total charged per member NGN 1,020.00** and **base pool paid to the "
            "recipient NGN 10,000.00**. Everything else in the table can be presented in "
            "whatever order reads best. These two are the numbers a member will remember, "
            "the numbers they will quote back at support, and the two they will conflate "
            "if they sit on adjacent lines without their labels. NGN 10,200.00 is what "
            "was *collected* in a round. It is never what a recipient is *paid*."
        ),
    },

    {"t": "h3", "text": "4.4.6 About — SCR-WEB-06"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Say who built this and why, and give the reader a route to a person. For this buyer, a name is most of what trust is made of."],
            ["Target user", "A reader who has got as far as asking *who are you* before deciding anything. Rare, high-intent, and the reader most likely to refer."],
            ["Layout", "Reading column. Founders, the problem, the approach, contact routes, a separate press route."],
            ["Components", "`ProseSection`, `Avatar` (initials only; no faces), `Button` (primary), `Button` (secondary), `Footer`."],
            ["Navigation", "Same top nav."],
            ["Primary CTA", "*Talk to us*, to `/contact`. On this page that is the primary rather than *Create free account*, because the reader who reaches About is asking a question, not signing up."],
            ["Secondary CTA", "*Create free account* as a secondary outlined button, and *See how it works* as a tertiary link."],
            ["Content", "Founders named as Abdurrahman Lawal and Abdurrahman Oriolowo. The problem: Ajos already work, and the record is kept in a book or a chat. The approach: the scheme is unchanged, the record-keeping is software. **No funding, partner, traction, customer-count or press claims — the company is pre-launch and any such claim would be false.** Any statement about licensing or regulatory status is labelled as requiring legal review."],
            ["Form fields", "None. A contact link only; the form is on SCR-WEB-08."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "None."],
            ["Empty state", "Not applicable."],
            ["Error state", "Page-level only."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "Single column throughout. Founder blocks stack below `md` and sit side by side at `lg` and above."],
            ["Accessibility", "Founder names are headings, so they appear in a heading navigation list. No photograph carries a name: initials and a name, so the name is in the text layer regardless of image loading."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.4.7 FAQ — SCR-WEB-07"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Answer the ranked objections that stop a signup, in the order they are asked, with the money questions above the reassurance questions."],
            ["Target user", "A reader who has read the fee page and is now looking for the thing that would go wrong. At this stage they are not browsing; they are looking for a reason not to proceed, and the honest answer to each is what converts them."],
            ["Layout", "Reading column. One `h2` per question with the answer immediately beneath. No accordion: an accordion hides the answer from search, from a screen reader's linear read, and from a member checking whether the product will hold their money."],
            ["Components", "`ProseSection`, `Table` (where a question needs figures), `Button` (primary), `Footer`."],
            ["Navigation", "Same top nav. An in-page index of the questions sits below the H1 at `md` and above, and is removed below that, where eight headings make the index redundant."],
            ["Primary CTA", "*Create free account*, in the closing band."],
            ["Secondary CTA", "*Contact us* (tertiary link) in the closing band, which is the CTA for the reader who did not find their answer here."],
            ["Content", "Eight questions, ranked. 1, What exactly is the fee and what does it come to? (the three-line breakdown). 2, What happens if someone does not pay? (the default chain, plus *you are never charged extra* and *they are not named in the Ajo*). 3, What if the Ajo does not fill in five days? (cancelled and refunded in full; whether the fee is returned is stated as open). 4, Can I leave an Ajo I have already joined? (before activation, yes; after activation, a replacement request, and the member stays liable until the replacement completes). 5, Does the organiser take the money? (no, with the role table's *cannot* column quoted). 6, Can the organiser change the order once we start? (no; positions lock on activation). 7, Who can see my details? (roster and round state only). 8, Is my money insured or regulated? (**we do not know yet** — the custody and partner questions are open, and are stated as open)."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "None."],
            ["Empty state", "Not applicable."],
            ["Error state", "Page-level only."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "Single column throughout. Questions 1 and 3 include a money table; both become stacked lists below 768, in row order."],
            ["Accessibility", "The page emits `FAQPage` structured data, generated from the same content the page renders rather than maintained separately, so the two cannot drift. Each question is an `h2` and its answer follows in a section labelled by that heading, so a screen reader user can navigate by question."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.4.8 Contact — SCR-WEB-08"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Put a person within reach of a person, with a stated expectation of how quickly, and without a three-step funnel in front of the form."],
            ["Target user", "A reader who did not find their answer, a member with a problem, and press. A reader who is already a customer is here to check whether support is real, and the visible response expectation is the answer."],
            ["Layout", "Two columns at `md` and above: form on the left, direct channels and the press route on the right. Stacked below `md`, form first. The channels column is never below the form, because a reader who wants to skip the form must be able to."],
            ["Components", "`FormField` (text, textarea, select, checkbox), `Button` (primary), `Button` (secondary), `Callout` (NOTE, response expectation), `Footer`."],
            ["Navigation", "Same top nav."],
            ["Primary CTA", "*Send the message*. One filled button, below the form fields."],
            ["Secondary CTA", "A call link and an email link, rendered as links with the address visible, in the channels column."],
            ["Content", "The form. Direct channels with a published response expectation. A separate press route. A note that support cannot move money or change a balance, and that a payment problem is faster through the in-app route — stated as information, not as a deflection."],
            ["Form fields", "See the field table below."],
            ["Validation rules", "See the validation table below."],
            ["Loading state", "The button enters its working state with its width locked and the form disabled. No spinner over the form, which would hide what the person typed."],
            ["Empty state", "The form renders empty with its helper text. Not locked, not disabled."],
            ["Error state", "Inline per field, per the validation table. A submit failure shows a danger banner above the form with a support reference and the typed content preserved."],
            ["Success state", "The form is replaced in place by a confirmation naming the reference and the response expectation, with a *Send another message* secondary action. The banner does not auto-dismiss, because the reference is something the person may need."],
            ["Responsive behaviour", "Single column below `md`. Field label above control at every width; the textarea is six rows on desktop and grows to fill the remaining height on mobile with the keyboard open."],
            ["Accessibility", "Every field has a bound label; the character count is announced politely, not assertively; the honeypot field is `aria-hidden` and out of the tab order; the submit error banner receives focus."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "table",
        "head": ["Field", "Control", "Required", "Helper text", "Format"],
        "rows": [
            ["Name", "Input, text", "Yes", "None", "2 to 60 characters"],
            ["Email", "Input, email", "Yes", "We reply here.", "Well-formed address; plus-addressing preserved"],
            ["Your phone", "Input, tel", "No", "Only if you would rather we called.", "Nigerian format, 11 digits, `080…` to `080…` or `+234…`"],
            ["What is this about?", "Select", "Yes", "None", "Account, joining an Ajo, a payment, a payout, a dispute, press, something else"],
            ["Message", "Textarea", "Yes", "Please do not send your BVN, your PIN, or a screenshot of a bank app.", "20 to 2,000 characters, live count from 1,800"],
            ["I agree to be contacted about this message", "Checkbox", "Yes", "Required to send. About this message only.", "Must be ticked"],
        ],
        "widths": [1.2, 0.92, 0.5, 2.0, 1.88],
        "size": 7.2,
    },
    {
        "t": "table",
        "head": ["Rule", "When it fires", "Message", "Behaviour"],
        "rows": [
            ["Name length", "Blur and submit", "Enter your name, 2 to 60 characters.", "Field keeps its content"],
            ["Email shape", "Blur", "Enter an email address we can reply to, like name@example.com.", "Field keeps its content"],
            ["Phone shape", "Blur, only if entered", "Enter a Nigerian phone number, like 08012345678.", "Field keeps its content"],
            ["Topic required", "Submit", "Choose what this is about.", "Focus moves to the first invalid field"],
            ["Message too short", "Blur", "Please write at least 20 characters so we can help.", "Field keeps its content"],
            ["Message too long", "Live, past 2,000", "2,000 characters is the limit. Yours is 2,014.", "Input is capped, not silently truncated"],
            ["Consent unticked", "Submit", "Tick the box so we know we may reply.", "Focus moves to the checkbox"],
            ["Rate limited", "Third attempt in 15 minutes", "Too many messages from this connection. Try again in a few minutes, or email help@ajo.ng.", "Field content preserved"],
            ["Submission failed", "5xx or timeout", "We could not send that. Your message is still here. Try again, or email help@ajo.ng. Reference 7FQK2M.", "Field content preserved, banner receives focus"],
        ],
        "widths": [1.06, 1.24, 2.56, 1.64],
        "size": 7.2,
    },
    {"t": "h3", "text": "4.4.9 Terms and Conditions — SCR-WEB-15"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Present the contract, and be the versioned artefact that acceptance is recorded against. The interface around it must never make it look shorter or simpler than it is."],
            ["Target user", "Anyone registering, and any member revisiting. Read once at registration and never again, which is exactly why the interface does not rely on it."],
            ["Layout", "Reading column, 68-character measure, numbered clauses, a table of contents at `lg` and above. The version number and effective date are pinned at the top and repeated in the footer."],
            ["Components", "`ProseSection`, `Table` (fee and refund terms), `Callout` (LEGAL, review status), `Footer`."],
            ["Navigation", "Same top nav. Reachable from every tier, from the register screen, and from the More sheet in tier 2."],
            ["Primary CTA", "*Download the terms*, honestly a tertiary link — a legal document has no primary action of its own. The primary action of the register screen is what references it."],
            ["Secondary CTA", "*Read the privacy policy* (tertiary link) in the footer."],
            ["Content", "The clauses, drafted by counsel. The clauses this product cannot yet write are the fee and tax language, the custody and licensing position, and the partner terms. Each is present as a clearly marked open item rather than omitted, and a version number and effective date are shown."],
            ["Form fields", "None on this page. Acceptance is captured on SCR-WEB-10 and stored as a timestamped version reference, not a boolean."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "None."],
            ["Empty state", "Not applicable."],
            ["Error state", "Page-level only."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "Single column at every width. The contents list is removed below `lg` and the clauses are numbered continuously, so nothing becomes unreachable."],
            ["Accessibility", "A legal document rendered as a wall of small text fails many people. Body size, 1.5 line height, capped measure, and a skip link past the contents to the clauses. Clause numbers are real text, not CSS counters, so they survive copy-paste and are read out."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.4.10 Privacy Policy — SCR-WEB-16"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "State what is collected, why, how long it is kept and who can see it, in language a member can act on. It is the document behind the no-shame and member-visibility rules in 4.1."],
            ["Target user", "Anyone registering; a member checking what the platform holds about them; and, at some point, a regulator. The last reader is why it exists in a versioned form."],
            ["Layout", "Reading column, same template as the terms, so that the two read as one document set."],
            ["Components", "`ProseSection`, `Table` (data categories, purpose, retention), `Callout` (LEGAL), `Footer`."],
            ["Navigation", "Same top nav. Reachable from the terms, the register screen and the More sheet."],
            ["Primary CTA", "None. A privacy policy has no primary action."],
            ["Secondary CTA", "*Read the terms* (tertiary link) in the footer; a *Download* link is present but is not styled as an action."],
            ["Content", "Data categories with purpose and retention: account and profile; contact channels; identity documents and verification checks; Ajo, position and membership; contributions, payments, payouts, ledger entries; notifications; support and dispute records; device and security events. The member-visibility rules are stated explicitly: members see the roster and round state of their Ajo, and never another member's bank details, identity documents, dispute or transaction. The data-rights mechanism is stated as a route, not as a slogan. **NDPA alignment requires review by qualified Nigerian counsel and is not claimed here.**"],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "None."],
            ["Empty state", "Not applicable."],
            ["Error state", "Page-level only."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "Single column throughout. The data-category table becomes a stacked list below 768, one category per block, with purpose and retention as labelled sub-lines."],
            ["Accessibility", "The data-category table has a caption and row headers. Retention periods are given as durations in text, never only as dates, so a member can act on them. Callout titles are in the accessible outline."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.4.11 Account status notice — SCR-WEB-17"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Tell a restricted member exactly what has happened to their account, what they can still do, and who to contact. It is reached by state, never by link, and it is never the entry to support chat."],
            ["Target user", "A member whose account is frozen or under risk review, often frightened, often on a second device. This person is the most anxious user of the product and the one most likely to be treated badly by a generic error page."],
            ["Layout", "Reading column, Deep header band, a plain statement, a three-row capability table, a contact block, and the reference. No illustration, no progress bar, no estimated resolution time that nobody has committed to."],
            ["Components", "`Callout` (WARNING, the statement), `Table` (what you can and cannot do), `Callout` (NOTE, contact), `Footer`."],
            ["Navigation", "Reached by redirect from any tier-2 route when the account is restricted. `noindex`, `no-store`, and never linked from any navigation, footer or menu."],
            ["Primary CTA", "*Contact support*, opening a prefilled support ticket. One filled button."],
            ["Secondary CTA", "*Read the safety and trust page* (tertiary link). A link to the fee page is present so a member can check what was charged while restricted."],
            ["Content", "The state in plain words: *Your account is under review. This is a precaution while we check some activity. Your Ajo records and your money are unaffected and you can read everything.* The three-row table: what you can do (read all your records, download receipts and statements, contact support, add a bank account to be ready) and what you cannot (pay a contribution, join or create an Ajo, invite a member, receive a payout — with the last stated as *a payout will be released when the review closes, not skipped*). The reference ID. The support contact. **No reason is given for the review, because at the point of freezing the decision may not be final and an unconfirmed reason would be a promise the review may break.**"],
            ["Form fields", "None. Support is reached from the primary CTA, and the ticket it opens is specified in 4.22.2."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "None. This page renders from the session's state flag and does not wait on a record."],
            ["Empty state", "Not applicable."],
            ["Error state", "If the reference cannot be resolved, a plain statement and a direct email address. Never a bare 500."],
            ["Success state", "Not applicable. There is no action on this page other than navigating to support."],
            ["Responsive behaviour", "Single column at every width. The capability table becomes a stacked list below 768."],
            ["Accessibility", "The page opens with the state as its `h1`, so a screen reader user learns the situation immediately on arrival. The capability table has a caption and row headers. The reference ID is selectable text, not an image, and is announced as a reference rather than read as a random string."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.4.12 Tier-1 not found — SCR-WEB-18"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Recover a reader who followed a stale or mistyped link. It is a route, not a state: an unknown tier-1 path returns this page with a 404 status."],
            ["Target user", "A reader following a link from a WhatsApp group, an SMS, or a search result that no longer resolves. They are not lost; they are one click from the right page, and this screen is where that click is offered."],
            ["Layout", "Reading column: a one-line explanation, a list of the five most likely destinations as links, and a link home. No search box — a search box on a marketing site is a destination that does not exist yet, and offering one that returns nothing is worse than not offering it."],
            ["Components", "`LinkList` (5 items), `Button` (secondary, home), `Footer`."],
            ["Navigation", "Same top nav, so the reader has the whole site available regardless."],
            ["Primary CTA", "None as a filled button. The page is a list of links, and the list is the content."],
            ["Secondary CTA", "*Go to the home page* (secondary button) below the list."],
            ["Content", "*That page is not here.* Then: Home, How it works, Fees, Safety and trust, Contact. A statement that the link may be old, and an invitation to contact us if someone sent it to them. **No reference to the internal structure of the site and no route enumeration.**"],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "None."],
            ["Empty state", "Not applicable."],
            ["Error state", "This screen *is* the error state for tier 1. It is served with a 404 status so that crawlers and caches behave correctly."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "Single column at every width."],
            ["Accessibility", "The `h1` states what happened, not a numeric error. The link list is a `nav` with a label, and every link names its destination, so a links-list reader sees a usable list rather than five items called *here*."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =============================================================== 4.5
    {"t": "h2", "text": "4.5 Authentication and access — tier 1"},
    {
        "t": "p",
        "text": (
            "Six screens that decide whether a person can become a member, and the "
            "first screens that meet the two rules most likely to be broken under "
            "pressure: a member must always be able to see their money, and a member "
            "must never be signed up to something they have not agreed to. Every screen "
            "in this group is unauthenticated or in-flight, so every one of them states "
            "what it will do with the address being entered before the field is filled."
        ),
    },
    {
        "t": "table",
        "head": ["Screen", "Route", "Purpose in one line", "Mandatory content"],
        "rows": [
            ["SCR-WEB-09", "`/signin`", "Get an existing member back in.", "Recovery route always visible; no social sign-in at v1"],
            ["SCR-WEB-10", "`/register`", "Create an account and agree to the terms.", "Versioned acceptance, not a checkbox alone"],
            ["SCR-WEB-11", "`/forgot-password`", "Send a reset link to an address on file.", "Rate-limited; never reveals whether an account exists"],
            ["SCR-WEB-12", "`/reset-password`", "Set a new password from a valid token.", "Token handling per 4.24.6; password rules stated before submit"],
            ["SCR-WEB-13", "`/verify-email`", "Prove control of the address.", "Resend with cooldown; expiry stated"],
            ["SCR-WEB-14", "`/membership-denied`", "Explain an account with no Ajo.", "The one empty state in the product that is not an error"],
        ],
        "widths": [0.66, 1.02, 1.7, 3.12],
        "size": 7.0,
    },

    {"t": "h3", "text": "4.5.1 Sign in — SCR-WEB-09"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Return an existing member to their Ajos. Not a gate in the marketing funnel: the sign-in link sits beside the create-account link, never above it, so a returning member is not made to feel they are late."],
            ["Target user", "A member on their phone, in a queue, who has forgotten which address they registered with, or whose passkey is not available on this device. The dominant emotion is mild friction, not suspicion."],
            ["Layout", "Single centred card, 420 px, on a Deep background, with the logo and the tagline above it and the legal routes below. The card contains the form and one recovery link. No third-party sign-in."],
            ["Components", "`FormField` (email, password), `Button` (primary), `Button` (secondary, passkey where supported), `Link` (forgot password), `Callout` (NOTE, rate limit), `Footer`."],
            ["Navigation", "Reachable from the top nav of every tier-1 page and from the app's More sheet. `returnTo` is honoured only for an allow-list of internal routes, per 4.24.5."],
            ["Primary CTA", "*Sign in*. One filled button, full card width, 52 px tall."],
            ["Secondary CTA", "*Create an account* as a tertiary link under the form. A passkey action appears as a secondary outlined button only where the platform authenticator is available; it is never the sole route."],
            ["Content", "Email. Password. A *Forgot password* link. A note that signing in does not create an Ajo. **No Facebook, Google or Apple sign-in at v1** — the canonical product does not include social login, and adding it would create an account-linking model that is not specified anywhere."],
            ["Form fields", "Email, input type `email`, required, autofill username. Password, input type `password`, required, autofill current-password, with a visibility toggle."],
            ["Validation rules", "Client-side: email shape on blur; password non-empty on submit. Server-side: the response is identical for an unknown address and a wrong password — *We could not sign you in with those details. Check them, or reset your password.* — with no field-level distinction, because a distinguishable response is an account-enumeration oracle."],
            ["Loading state", "The button enters its working state with its width locked. The form is not disabled, so a person who mistypes can keep correcting while the request is in flight; the submit is the only thing that is inert."],
            ["Empty state", "Empty fields with helper text. No placeholder-as-label."],
            ["Error state", "A single danger banner above the form, above the fields, never inside a field, because the cause may be either field. It never names which field was wrong."],
            ["Success state", "The session is established and the member lands on the destination, or on the home screen of the app. No interstitial, no welcome tour, no *are you sure this is the right account*."],
            ["Responsive behaviour", "The card fills the width below 375 with 16 px side padding and never scrolls horizontally. At `md` and above the password visibility toggle sits inside the field's trailing edge and the card is 420 px."],
            ["Accessibility", "The banner is a live region and receives focus on failure. The password toggle is a real button with a state and a label, not an icon swap. The error banner is not dismissed automatically. Tab order runs email, password, visibility toggle, forgot password, sign in, create account."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "No social sign-in at v1",
        "text": (
            "**SCR-WEB-09 and SCR-WEB-10 have no Facebook, Google or Apple "
            "authentication at v1.** A social identity creates a second identity "
            "source, and with it the need to link, unlink, verify and reconcile it "
            "against a phone number and an email that the Ajo actually depends on. "
            "None of that is specified in the canonical product, and inventing it in "
            "the auth layer would put a requirement nobody asked for underneath every "
            "identity decision that follows. **Owner: Founders. Revisit only together "
            "with an account-linking and recovery specification.**"
        ),
    },

    {"t": "h3", "text": "4.5.2 Register — SCR-WEB-10"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Create an account, and record agreement to a specific version of the terms. Everything the member does afterwards is downstream of this screen, and the record of consent is a versioned reference rather than a boolean."],
            ["Target user", "A first-time member on a phone, often reading a message from the organiser, often on a metered connection and often sharing a device. They are being asked for a phone number, an email, a password, a name and their consent, in one go, and the interface must justify each ask before making it."],
            ["Layout", "Single centred card, 440 px, Deep background, one column, no steps. The card is scrolled naturally; the legal block is a separate full-width region below it and is never a footer link."],
            ["Components", "`FormField` (text, email, tel, password), `Checkbox` (consent), `Button` (primary), `Button` (secondary, sign in instead), `Callout` (NOTE, what we use this for), `Footer`."],
            ["Navigation", "Reached from every tier-1 primary CTA, from the sign-in card, and with `returnTo` honoured per 4.24.5. `returnTo` is cleared on successful registration, so a stale destination cannot reappear after the member's state has changed."],
            ["Primary CTA", "*Create account*. One filled button, full card width, 52 px tall."],
            ["Secondary CTA", "*I already have an account* (tertiary link) under the form. *Read the terms* and *Read the privacy policy* (tertiary links) in the consent block."],
            ["Content", "First name. Last name. Email. Phone, in Nigerian format. Password, with the rules stated before the field is filled, not after a failure. The consent block: *By creating an account you agree to the Terms and acknowledge the Privacy Policy*, with both linked and their version and effective date shown. A NOTE callout naming the two things the phone number is used for: reminders for the Ajos you are in, and sign-in codes. **A note that an account is not an Ajo: creating an account does not join or create an Ajo, and joining one is a separate, deliberate action in the app.**"],
            ["Form fields", "See the field table below."],
            ["Validation rules", "See the validation table below. Every rule fires inline, names the field, and never clears content."],
            ["Loading state", "The button works and locks its width; the form stays editable. No overlay, no spinner across the page, because this form holds a person's typed identity and a spinner over it looks like data loss."],
            ["Empty state", "Empty with helper text. The password rules are visible from the moment the field appears, so the member can satisfy them without a failed attempt."],
            ["Error state", "Inline per field, plus a banner above the form for failures that are not a field's fault. Every error states what to do next. A field the server rejected is not cleared, and the member is not asked to retype the whole form."],
            ["Success state", "The account exists, the member is signed in, and the screen hands off to `returnTo` or to SCR-MOB-02. **A new account with no Ajo lands on SCR-WEB-14, not on an empty dashboard**, because a dashboard with nothing in it is a worse first impression than a plain explanation of what to do next."],
            ["Responsive behaviour", "One column at every width. Labels above controls, 48 px minimum control height. Below 375 the card is flush to the edges with 16 px padding. The consent block wraps its text at 40 characters per line in the 320 px case rather than clipping."],
            ["Accessibility", "Every field has a bound label and a described-by pointing at its helper text and its error. The password rules list is associated with the password field, so a screen reader user hears the rules before typing. The consent checkbox is a real checkbox, not a link with a tick. Error summary appears only above 768, where a jump is not disorienting; below that, each error is announced politely at its field."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "table",
        "head": ["Field", "Control", "Required", "Helper text", "Format"],
        "rows": [
            ["First name", "Input, text", "Yes", "As it should appear on the roster.", "1 to 40 characters"],
            ["Last name", "Input, text", "Yes", "As it should appear on the roster.", "1 to 40 characters"],
            ["Email", "Input, email", "Yes", "We use this for your receipts and nothing else.", "Well-formed; plus-addressing preserved"],
            ["Phone", "Input, tel", "Yes", "For Ajo reminders and sign-in codes only.", "Nigerian format, 11 digits, `080…` to `080…` or `+234…`"],
            ["Password", "Input, password", "Yes", "At least 10 characters, with a number and a symbol.", "10 to 128 characters; checked against a known-breached list"],
            ["I agree to the Terms and acknowledge the Privacy Policy", "Checkbox", "Yes", "Terms v0.0.0, effective date shown. Links open in a new tab.", "Must be ticked; stored as a version reference and timestamp"],
        ],
        "widths": [1.2, 0.92, 0.5, 2.0, 1.88],
        "size": 7.2,
    },
    {
        "t": "table",
        "head": ["Rule", "When it fires", "Message", "Behaviour"],
        "rows": [
            ["Name empty", "Blur", "Enter a first name.", "Field keeps its content"],
            ["Name too long", "Blur", "Use 40 characters or fewer for a name.", "Input capped at 40"],
            ["Email shape", "Blur", "Enter an email address, like name@example.com.", "Field keeps its content"],
            ["Email already registered", "Submit", "That email already has an account. Sign in instead, or reset the password.", "Field keeps its content; a sign-in link appears beside the message"],
            ["Phone shape", "Blur", "Enter a Nigerian phone number, like 08012345678.", "Field keeps its content"],
            ["Phone already registered", "Submit", "That number already has an account. Sign in instead, or reset the password.", "Field keeps its content; no silent merge with an existing account"],
            ["Password too short", "Live, from 1 character", "Use at least 10 characters. 7 so far.", "Field keeps its content; the rule list ticks as it is satisfied"],
            ["Password missing a number or symbol", "Live, from 1 character", "Add a number and a symbol. 7 characters, number added, symbol missing.", "Field keeps its content"],
            ["Password in a known breached list", "Submit", "That password has appeared in a known data breach. Choose a different one.", "Field keeps its content; never suggests a specific alternative password"],
            ["Consent unticked", "Submit", "Tick the box to agree to the Terms.", "Focus moves to the checkbox"],
            ["Rate limited", "Fifth attempt in an hour", "Too many attempts from this connection. Try again in an hour, or contact us.", "Field content preserved"],
            ["Submission failed", "5xx or timeout", "We could not create the account. Your details are still here. Try again. Reference 4RTW9P.", "Field content preserved, banner receives focus"],
            ["Verification email undelivered", "After success", "Account created. We could not send the verification email, so *Resend* is available immediately.", "The member is signed in; unverified state is visible in More"],
        ],
        "widths": [1.06, 1.24, 2.56, 1.64],
        "size": 7.2,
    },

    {"t": "h3", "text": "4.5.3 Forgot password — SCR-WEB-11"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Send a reset link to an address on file, without telling the caller whether that address has an account."],
            ["Target user", "A member locked out, usually on a borrowed or shared phone. They need this to work on the first try, and they must not be exposed by it."],
            ["Layout", "Single card, 420 px, on Deep, with the same logo lockup as SCR-WEB-09. The card holds one field, one button, and one return link."],
            ["Components", "`FormField` (email), `Button` (primary), `Link` (back to sign in), `Footer`."],
            ["Navigation", "Reached from the *Forgot password* link on SCR-WEB-09 only. Returns to sign-in on success."],
            ["Primary CTA", "*Send the reset link*. One filled button, full card width."],
            ["Secondary CTA", "*Back to sign in* (tertiary link) below the form."],
            ["Content", "Email. A statement that the link expires and that it goes to the address on the account, not to whatever address is typed here."],
            ["Form fields", "Email, input type `email`, required, autofill username."],
            ["Validation rules", "Email shape on blur. **The response is identical for a known and an unknown address**: *If that address has an account, a reset link is on its way. It expires in 30 minutes.* Nothing in the message, the timing, or the page distinguishes the two cases."],
            ["Loading state", "The button works with its width locked. No spinner over the card."],
            ["Empty state", "Empty field with helper text."],
            ["Error state", "Shape errors inline. Send failures produce the same neutral response, because telling a caller that the mail was not sent is a weaker signal than a uniform success and buys nothing."],
            ["Success state", "The card is replaced in place by the neutral confirmation. No countdown, no *it is not working? try this* carousel, no second send button in the same state — the resend lives on SCR-WEB-12."],
            ["Responsive behaviour", "Single card, 16 px side padding below 375."],
            ["Accessibility", "The confirmation is announced in a polite live region. The identical-response rule is enforced in the interface, not only in the copy: there is no timing-dependent difference and no redirect difference."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.5.4 Reset password — SCR-WEB-12"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Let a member set a new password from a valid single-use token, and let them know when the token is no longer usable."],
            ["Target user", "A member who followed a link from an email or SMS, possibly hours or days later, possibly on a different device from the one they requested it on."],
            ["Layout", "Single card, 420 px, Deep background. Card content is decided by token state, not by a loading spinner, because the common case is that the token has expired."],
            ["Components", "`FormField` (password ×2), `PasswordStrength`, `Button` (primary), `Button` (secondary, request a new link), `Callout` (WARNING, invalid or expired token), `Footer`."],
            ["Navigation", "Reached only from the emailed link. `returnTo` is not honoured here, so a token link cannot be used as an open redirect."],
            ["Primary CTA", "*Set new password*. One filled button."],
            ["Secondary CTA", "*Send me a new link* (secondary outlined button), present only in the expired or invalid token state. In the valid state there is no secondary action, because the task has exactly one outcome."],
            ["Content", "New password, with the rules listed before the field. Confirm new password, with a *match* check. A NOTE stating that every other signed-in session is signed out when the password changes."],
            ["Form fields", "New password, required, autofill new-password, rules associated. Confirm new password, required, autofill new-password."],
            ["Validation rules", "Same password rules as SCR-WEB-10. Confirm must match. **No complexity rule that contradicts length**: a passphrase is accepted. A mismatch message states which field to fix, not that the values are *invalid*."],
            ["Loading state", "The button works with its width locked. Token validity is checked on arrival, and the result of that check decides the state; the valid state is not shown optimistically and then retracted."],
            ["Empty state", "Empty fields with the rules visible."],
            ["Error state", "Three distinct token states, all in WARNING or DANGER treatment and all offering a new link: expired, already used, malformed. A used token is not treated as a generic failure, because the member may have completed the reset in another tab."],
            ["Success state", "The password is set, every other session is signed out, and the member is signed in on this device. The card shows the outcome and a link to continue. There is no *please sign in again* step, because sending a member who just proved they can get in, back to the sign-in form, is a pointless tax."],
            ["Responsive behaviour", "Single card at every width; 16 px side padding below 375."],
            ["Accessibility", "The rules list is associated with the new-password field and is read before entry. The strength meter is not the only indicator: unmet rules are listed in words. The confirm field's error is polite, and focus moves to the first invalid field on submit."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Tokens are never revealed in an error message",
        "text": (
            "An invalid, expired, used and malformed token all produce the same shape "
            "of response and the same recovery action. A message that distinguishes "
            "*expired* from *used* confirms that the token existed, which turns a reset "
            "link into a probe for whether a given account has a pending reset."
        ),
    },
    {"t": "h3", "text": "4.5.5 Verify email — SCR-WEB-13"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Prove control of the address before anything depends on it, and make the consequence of not verifying obvious rather than punitive."],
            ["Target user", "A newly registered member who has been signed in and is now being asked to confirm an address, usually without having noticed that they have not."],
            ["Layout", "Single card, 420 px, Deep background. The address is shown with a *change* link, the status line, and one button. The card is intentionally short: there is nothing else to do here."],
            ["Components", "`FormField` (email, editable), `Button` (primary), `Button` (secondary, change address), `Badge` (unverified), `Callout` (NOTE, why this matters), `Footer`."],
            ["Navigation", "Reached from the emailed link, and as a persistent, non-blocking state inside the app until verified. **It is never a modal and never an interstitial**: an unverified member may continue to read everything and open the More sheet."],
            ["Primary CTA", "*Send the verification email*. One filled button."],
            ["Secondary CTA", "*Change the email address* (tertiary link) beside the address, and *Resend* as a secondary outlined button once the cooldown is active."],
            ["Content", "The address. The resend cooldown, stated as a clock. A NOTE stating what verification is for: receipts, account recovery, and dispute evidence. A statement that unverified accounts can read but cannot pay a contribution or receive a payout, so the consequence is known before it is met."],
            ["Form fields", "Email, input type `email`, editable in place; changing it restarts the cooldown and re-issues the verification target."],
            ["Validation rules", "Email shape on blur. Resend is limited to one per 60 seconds per address and five per day, and the limit is enforced in the interface, so the button is disabled with a live countdown rather than failing on click."],
            ["Loading state", "The button works with its width locked. The cooldown starts from the moment the send is accepted, not from the moment the response returns, so a slow response cannot be used to send twice."],
            ["Empty state", "The address is never empty on this screen; if it has been cleared, the empty field state is used and the primary button becomes *Send*."],
            ["Error state", "Delivery failure shows the neutral form of the resend message plus a *use a different address* link. It never says the address does not exist, because an unverifiable address is more often a typo or a full mailbox than an attack, and saying so only makes the member defensive."],
            ["Success state", "After the member follows the link, the in-app state changes to verified and a single confirmation line appears in place of the card. The card is not dismissed by a timer."],
            ["Responsive behaviour", "Single card at every width; 16 px side padding below 375."],
            ["Accessibility", "The cooldown is a polite live region updated once a second at most, and is also stated as a text time so a screen reader user is not read a changing number every tick. The verified state change is announced politely once."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.5.6 No Ajo yet — SCR-WEB-14"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Turn the one genuinely empty state in the product into the next action, rather than into an apology. A member with an account and no Ajo is a normal state, not a failure state, and the screen may not look like a 404."],
            ["Target user", "A brand-new member who has just registered and has not yet been added to an Ajo. They do not yet know how Ajos are created or joined, so the screen has to explain both in two sentences."],
            ["Layout", "Two regions. A short explanation on Cloud, then two equal cards: *Join an Ajo* and *Create an Ajo*. The two cards are peers — neither is presented as the real one. A third, quieter line below: *Have an invite link?*"],
            ["Components", "`EmptyState` (illustration, non-essential), `Button` (primary, one per card), `FormField` (invite code, collapsed), `Callout` (NOTE, roles), `Footer`."],
            ["Navigation", "The destination for a registered member with zero Ajo memberships, and the landing route after registration. Also reachable from the dashboard's own empty state, where the copy is identical."],
            ["Primary CTA", "**Two filled buttons, one per card, and this is the only screen in the product where that is correct.** They lead to different places and neither is a subordinate fallback, so ranking them would be a lie. Each card also carries exactly one filled button, never two."],
            ["Secondary CTA", "*I have an invite code* (tertiary link), which expands an inline single-field form. *Sign out* (tertiary link) at the bottom, because a shared device is a plausible situation here."],
            ["Content", "*You are not in an Ajo yet. When you join or create one, your Ajos and your schedule appear here.* The join card: *Ask your organiser for an invite link, or enter a code.* The create card: *Start a new Ajo. You will set the amount, the number of members and the payment day, and invite people to join.* A NOTE explaining that anyone can create an Ajo and that an organiser is simply a member who created one, because the two are frequently confused and the confusion is a barrier to entry."],
            ["Form fields", "Invite code, input text, optional, collapsed by default. NGN-prefixed, 6 to 12 characters, case-insensitive, spaces stripped on input."],
            ["Validation rules", "Code: required if submitted, length 6 to 12 after normalisation. An unknown or expired code produces *That code is not valid, or the invite has closed* — one message for both, because a distinct message for an expired invite is a way to enumerate active invites."],
            ["Loading state", "The code check runs with the field's trailing affordance in a working state, width locked. The two card buttons are not inert while it runs, because they lead somewhere unrelated."],
            ["Empty state", "This screen *is* the empty state, and it is treated as a first-class screen with a route, a title and links, not as a component rendered into a blank page."],
            ["Error state", "Inline on the code field. Join and create failures surface in the relevant card, with the card's content preserved."],
            ["Success state", "A successful code entry transitions to the invitation-pending state, which is a separate route and not this screen. Creating an Ajo transitions to the wizard at SCR-MOB-05.2."],
            ["Responsive behaviour", "Two cards side by side at `md` and above, stacked below it with join first, because joining is the shorter task and the more common route. Neither card is ever removed at any width."],
            ["Accessibility", "The two cards are labelled regions with real headings, so a screen reader user can jump between them. The illustration is decorative and hidden from the accessibility tree. The primary buttons have distinct, self-describing labels — *Join an Ajo* and *Create an Ajo* — not two buttons both called *Continue*."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "pagebreak"},

    # =============================================================== 4.6
    {"t": "h2", "text": "4.6 Dashboard — tier 2, member"},
    {
        "t": "p",
        "text": (
            "The two screens a member sees most often, and the two places where the "
            "product's central promise is either kept or quietly broken. The dashboard "
            "answers *where does my money stand* before it answers anything else, and "
            "the Ajo list answers *which groups am I in* before it asks for anything. "
            "Both open on content, never on a spinner over an empty region."
        ),
    },

    {"t": "h3", "text": "4.6.1 Dashboard — SCR-MOB-01"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Answer the money question first and completely: what I owe, when, what I have paid, what I will receive, and what the last round actually cost. Then show the Ajos, then the activity."],
            ["Target user", "A signed-in member opening the app in the morning, or in a queue, or immediately after a payment notification. They are checking a figure, not browsing. Some of them are anxious about a round they have not paid, and the screen should let them confirm that in two seconds."],
            ["Layout", "Single scrolling column, max 720 px on web and full width capped at 480 px on mobile. Order is fixed: greeting and verification strip; the money summary block; the next obligation card; the Ajo list; recent activity. **The money summary never moves below the fold, and nothing is inserted above it.** A single FAB is absent; the primary action for a member with a due contribution is a full-width button inside the next-obligation card, not a floating control that covers content."],
            ["Components", "`StatCard` ×4, `MoneyBlock` (3 lines), `Card` (obligation), `Card` (Ajo), `ListItem` (activity), `Badge`, `Skeleton`, `EmptyState`, `Button` (primary and secondary), `BottomNav`."],
            [            "Navigation", "Tab 1 of 5 in the bottom bar. Reached by sign-in, by the notification deep link, and from the Ajo list's card tap. There is no top navigation on mobile; the bar is the only chrome."],
            ["Primary CTA", "**Dynamic, and it is the obligation button when one exists**: *Pay NGN 1,020.00*, inside the next-obligation card, only when a contribution is due and unpaid. With nothing due, the primary becomes *View your Ajos*. Exactly one filled button in the first screenful, whichever it is."],
            ["Secondary CTA", "*View statement* (tertiary link) in the money block, and *See all activity* (tertiary link) at the foot of the activity list."],
            ["Content", "Greeting by first name. Verification strip when unverified. Money block: the three canonical lines for the current round — *Contribution NGN 1,000.00*, *Fee NGN 20.00*, *Total charged NGN 1,020.00* — plus a fourth line stating what the base pool will pay, *This round pays out NGN 10,000.00*, and a fifth stating the round's progress, *3 of 10 members have paid*. Obligation card: the due date, the amount, the Ajo, and the round. Ajo list: name, status, the member's position, next event. Activity: the last five events with real dates and amounts."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable. There is no input on this screen, deliberately: a dashboard that offers a search box on mobile is a dashboard nobody uses."],
            ["Loading state", "Skeleton for each block in final position, so the layout does not move when content arrives. The money block skeleton reserves its three lines, and **the screen never shows a partial money total**: either all five lines are present or the block is in its skeleton state."],
            ["Empty state", "A registered member with no Ajo is redirected to SCR-WEB-14 per 4.5.6. A member with an Ajo but no activity gets *No activity yet. Your first payment will appear here*, not an empty bordered box. A member whose Ajo is cancelled sees the cancellation notice in place of the money block, with the Ajo kept read-only and visible."],
            ["Error state", "Block-level and contained. If the money summary fails, the other blocks still render and the money block shows *We could not load your summary. Try again* with a retry control. The screen never replaces itself with a full-page error, because the Ajo list and the activity are still useful."],
            ["Success state", "Not applicable directly. A payment made from this screen returns here with a single confirmation toast naming the amount and the receipt, and the money block updates in place."],
            ["Responsive behaviour", "One column at every width. The four stat cards are a 2×2 grid from `xs` to `sm` and a 4-across row at `md` and above, with the field inventory identical in both arrangements per 4.3.3. The obligation card stays a card at every width; it never becomes a table, because a table with two rows and one action is worse than a card."],
            ["Accessibility", "The money block is a labelled region whose `h2` is *This round*, and it is the first focusable element after the page title. Each of the five lines is a definition-list pair, so a screen reader user can hear figure and label together. The obligation button's accessible name includes the amount and the Ajo name. Progress is stated in text — *3 of 10 members have paid* — never as a bar with a colour. Tab order follows reading order. All touch targets are at least 44 px, and the obligation button is 56 px."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.6.2 Ajo list — SCR-MOB-02"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show every Ajo the member belongs to, in a form that makes the next obligation findable in one glance, and make creating an Ajo reachable without a menu."],
            ["Target user", "A member in two or three Ajos, or in one, checking whether anything is due. The list has to be readable at a glance because it is compared against memory, not searched."],
            ["Layout", "Single scrolling column. A title row with the count, then one `Card` per Ajo, then a full-width secondary button. Cards are 96 px tall and carry five facts: name, status, the member's position, the next event with its date, and a money line when a contribution is due."],
            ["Components", "`Card` (Ajo), `Badge`, `ListItem`, `Skeleton`, `EmptyState`, `Button` (secondary, create), `BottomNav`."],
            ["Navigation", "Tab 2 of 5. Reached by the dashboard's Ajo region, by an Ajo notification, and by the tab bar. A card tap goes to SCR-MOB-03."],
            ["Primary CTA", "None. A list of things to go to is not a place for a primary action, and a filled *Create Ajo* floating over the list would cover the card a member was reaching for. **When the list is empty the single filled button becomes *Create an Ajo*, because then the screen has one job.**"],
            ["Secondary CTA", "*Create an Ajo* (secondary outlined, full width) when the list is not empty. *See cancelled Ajos* (tertiary link) at the foot when any exist."],
            ["Content", "Per card: Ajo name; status badge — `DRAFT`, `ENROLLING`, `ACTIVE`, `CANCELLED`; the member's position; the next event and its date; and, when a contribution is due and unpaid, a right-aligned *Due* line with the total. Cancelled Ajos are hidden by default and reachable through the tertiary link, because a member's active obligations and their history are different questions."],
            ["Form fields", "None. No search and no filter on a list that is expected to hold single digits of items for a very long time."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Four card skeletons at final height, so the list does not reflow. The count in the title row appears only with the cards, never first at zero."],
            ["Empty state", "A dedicated empty state with the *Your Ajo. Your Story.* tagline as its heading, the line *You are not in an Ajo yet*, and a single filled *Create an Ajo*. This is a different component from the empty state on SCR-WEB-14: that one offered joining as a peer, because arriving by registration is not a choice, whereas arriving here is."],
            ["Error state", "Contained to the list region: *We could not load your Ajos. Try again* with a retry control, and the create button stays available, because creating an Ajo does not depend on the list having loaded."],
            ["Success state", "Not applicable. Return from a created Ajo inserts the new card at the top with a single confirmation, and the list is not scrolled back to the top on return, because a member who paid an obligation does not want their position moved."],
            ["Responsive behaviour", "One card per row at every width, full width capped at 480 px on mobile. A horizontal scroll of cards is prohibited: a member comparing two Ajos cannot compare them side by side, and side by side would put amounts at 11 px."],
            ["Accessibility", "The list is a `ul` of links, so a links-list reader announces *5 Ajos*. Each card's accessible name is built from the facts, not the visual order: *Ajo name, active, your position 4, next collection 12 October, contribution of NGN 1,020.00 due*. The status badge is never the only carrier of the status; the word is present in text. Cards are at least 96 px tall so the whole card is a comfortable target."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "No horizontal card carousel on the Ajo list",
        "text": (
            "**The Ajo list is a vertical list at every width.** A carousel was "
            "considered and rejected: two Ajos side by side puts the money line below "
            "12 px, and the whole purpose of a member opening this list is to compare "
            "an amount against what they remember. Comparing requires the amounts to be "
            "the same size. **Owner: Founders.**"
        ),
    },

    {"t": "pagebreak"},

    # =============================================================== 4.7
    {"t": "h2", "text": "4.7 Create Ajo wizard — SCR-MOB-05.1 to SCR-MOB-05.7"},
    {
        "t": "p",
        "text": (
            "Seven steps, seven routes, one Ajo at DRAFT. The wizard is the longest "
            "flow in the product and the one most likely to be abandoned, so the rules "
            "are strict: the amount is chosen before the fee is mentioned, the fee is "
            "shown live from the moment an amount exists, and the final step is an "
            "acknowledgement gate with no commit action. **Nothing in this flow charges "
            "anything.** Activation happens later, in the Ajo detail screen, after the "
            "roster is complete or the five-day window closes."
        ),
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Wizard-wide behaviour",
        "text": (
            "The wizard is resumable. A DRAFT Ajo is created at step 1 and every step "
            "writes to it, so closing the app on step 4 and returning on step 4 loses "
            "nothing. The progress indicator shows *Step N of 7* and the step names, "
            "and previously completed steps are tappable to go back. **Forward navigation "
            "into a step whose inputs are incomplete is blocked with an inline reason, "
            "not a disabled button with no explanation.** Leaving the wizard from a step "
            "with unsaved input prompts per 4.24.3."
        ),
    },

    {"t": "h3", "text": "4.7.1 Step 1, the Ajo's identity — SCR-MOB-05.1"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Create the DRAFT record and capture the name, so the Ajo exists in the member's list and can be left and resumed. This is the only step whose entry to the flow creates a record."],
            ["Target user", "A member acting on the organiser's instruction, often over a phone call, often with the Ajo's details written on a piece of paper in front of them."],
            ["Layout", "Wizard chrome, then a single card: the step name as `h1`, a 40-character hint, the field, and a full-width primary button pinned to the bottom of the viewport on mobile so it does not move as fields validate."],
            ["Components", "`FormField` (text, textarea, select), `WizardProgress`, `Button` (primary), `Link` (leave the wizard), `Callout` (NOTE)."],
            ["Navigation", "Entered from the Ajo list's *Create an Ajo* button and from SCR-MOB-04's *Create instead* secondary action. Exits to the Ajo list, where the DRAFT now appears. `returnTo` is not honoured; leaving a wizard always lands on the Ajo list."],
            ["Primary CTA", "*Continue to the amount*. One filled button, 56 px on mobile, 48 px on web."],
            ["Secondary CTA", "*Save and finish later* (tertiary link) beside the primary, and *Cancel* (tertiary link) as the dismiss route, which is a confirmation when a name has been typed."],
            ["Content", "Ajo name — what the group calls itself. A short description, optional, and a purpose field, optional, which is what the invite screen shows and what makes an invite convincing. A NOTE stating that the Ajo stays a DRAFT until it is activated, and that nothing is charged at any point in this flow."],
            ["Form fields", "See the field table below."],
            ["Validation rules", "See the validation table below."],
            ["Loading state", "The primary button works with its width locked while the DRAFT is created. The step's fields render immediately, because a step that shows nothing until a record exists is a step that looks broken on a slow connection."],
            ["Empty state", "The fields are empty with helper text. The wizard progress indicator shows step 1 of 7 with steps 2 to 7 disabled and named."],
            ["Error state", "DRAFT creation failure is a banner with a retry that preserves the typed name. Duplicate-name rejection is inline on the name field and names the Ajo it collides with, because names inside one member's list are not private and the member needs to know which one."],
            ["Success state", "The DRAFT exists and the wizard advances to 05.2. No toast, because advancing is the feedback."],
            ["Responsive behaviour", "Single card, 16 px side padding below 375. The description textarea is three rows on mobile and four on web. The primary button is pinned to the safe area and the card scrolls beneath it, so the button never sits under the keyboard."],
            ["Accessibility", "The step name is the `h1`, so a screen reader user lands knowing where they are. The progress indicator is an ordered list with the current step marked by `aria-current`, and its accessible name is *Step 1 of 7, the Ajo's identity*. Fields keep their content on every failure."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "table",
        "head": ["Field", "Control", "Required", "Helper text", "Format"],
        "rows": [
            ["Ajo name", "Input, text", "Yes", "What your group calls itself. Members will see this.", "3 to 40 characters; unique within the member's own Ajo list"],
            ["Short description", "Textarea", "No", "One line. Shown on the invite screen.", "0 to 80 characters, live count from 60"],
            ["What is this Ajo for?", "Select", "No", "Helps members decide whether to join.", "Household, business, school group, church group, event, other"],
        ],
        "widths": [1.2, 0.92, 0.5, 2.0, 1.88],
        "size": 7.2,
    },
    {
        "t": "table",
        "head": ["Rule", "When it fires", "Message", "Behaviour"],
        "rows": [
            ["Name empty", "Continue", "Give the Ajo a name so your members recognise it.", "Focus moves to the field"],
            ["Name too short", "Blur", "Use at least 3 characters.", "Field keeps its content"],
            ["Name too long", "Blur", "Use 40 characters or fewer.", "Input capped at 40"],
            ["Name already used by this member", "Continue", "You already have an Ajo called *Market women*. Open it instead, or use another name.", "Field keeps its content; a link to the existing Ajo is offered"],
            ["Description too long", "Live, past 80", "80 characters is the limit. Yours is 86.", "Input capped, not silently truncated"],
            ["DRAFT not created", "Continue", "We could not start this Ajo. Your details are still here. Try again.", "Field content preserved, banner receives focus"],
        ],
        "widths": [1.06, 1.24, 2.56, 1.64],
        "size": 7.2,
    },
    {"t": "h3", "text": "4.7.2 Step 2, the amount and the live fee preview — SCR-MOB-05.2"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Capture the contribution amount per member per round, and show the fee consequence of that number immediately. This step is the fee disclosure, and it happens before the next step, not at the end of the flow."],
            ["Target user", "The organiser, who has a figure in mind and wants to know what it will really cost each person before they tell the group."],
            ["Layout", "Wizard chrome, then a card with the amount field and, directly beneath it, a three-line money block that updates as the field changes. The three lines are the canonical three, in the canonical order, at every amount."],
            ["Components", "`FormField` (amount, preset chips), `MoneyBlock` (3 lines), `WizardProgress`, `Button` (primary and secondary), `Callout` (NOTE, what the recipient gets)."],
            ["Navigation", "Entered from 05.1. Back returns to 05.1 with the name preserved. Forward to 05.3."],
            ["Primary CTA", "*Continue to the payment day*. One filled button."],
            ["Secondary CTA", "*Back* (secondary outlined) below it, and a step link back through the progress indicator."],
            ["Content", "The amount field, pre-filled with NGN 1,000.00 as a working default that the organiser is expected to confirm or change — **it is a default, not a recommendation, and the field is selected on arrival so it is obvious it is editable.** Four preset chips at common values. The live three-line block: *Contribution NGN 1,000.00*, *Fee at 2% NGN 20.00*, *Total each member pays NGN 1,020.00*. A NOTE: *This is what each member pays each round. Whoever receives the round is paid NGN 10,000.00 — the fee is never taken from the payout.*"],
            ["Form fields", "Amount, input type text with numeric input mode, not `number`, because `number` silently discards the member's formatting and rejects the way a Nigerian keyboard offers digits. Required. Preset chips set the same field and keep focus in the field so typing continues to work."],
            ["Validation rules", "Numeric; NGN 1,000.00 minimum, up to the current contribution cap. Thousands separators allowed and stripped before parsing. A value below the minimum is rejected with the figure, not a phrase: *Each member pays at least NGN 1,000.00 per round.* The preview shows the parsed value and never the raw string, so a value of *1,0* never renders a fee of NGN 0.02."],
            ["Loading state", "The preview computes on input with no network call, so there is no loading state and no lag between typing and seeing the fee. Any cap lookup is resolved before the step is entered rather than on input."],
            ["Empty state", "The field is empty and the preview shows the canonical figures as a labelled example, *Example at NGN 1,000.00*, rather than dashes. Dashes teach nothing."],
            ["Error state", "Inline on the amount only. The preview is not blocked by an invalid amount; it keeps showing the last valid value with the new text marked invalid, so the member can see the difference between their typing and the number that will be charged."],
            ["Success state", "The amount is stored on the DRAFT and the wizard advances. Nothing is charged and no receipt exists, so there is nothing to show a member here."],
            ["Responsive behaviour", "One column. The money block sits immediately under the field and is never collapsed, because a fee the member has to open something to see is a fee that gets missed. Below 375 the three lines keep their labels on the left and figures right-aligned."],
            ["Accessibility", "The money block is a description list associated with the field by `aria-describedby`, and is in the accessible outline as a labelled region named *What each member pays*. Amounts use tabular figures so digits align between lines. The preview updates are announced politely, not assertively, and announce the total only, not all three lines on every keystroke."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.7.3 Step 3, the payment day — SCR-MOB-05.3"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Set the day of the month each round is collected, and state that it cannot be changed once the Ajo is active."],
            ["Target user", "The organiser, choosing a day the group can realistically meet. The date they pick has to survive ten rounds of real life, which is why the step shows the consequences rather than a bare date picker."],
            ["Layout", "Wizard chrome, then a card: a day-of-month selector rendered as a 7-column grid of days 1 to 28 plus a *Last day of the month* option, then a consequence panel beneath it."],
            ["Components", "`FormField` (day of month), `WizardProgress`, `Button` (primary and secondary), `Callout` (NOTE, immutability), `Callout` (DECISION, consequence)."],
            ["Navigation", "Entered from 05.2. Back to 05.2. Forward to 05.4."],
            ["Primary CTA", "*Continue to the number of rounds*. One filled button."],
            ["Secondary CTA", "*Back* (secondary outlined)."],
            ["Content", "The day selector. Below it, the consequence panel, computed live: the collection date for the next three rounds, and the reminder timing — reminders go out 72 hours and 24 hours before the due date. A NOTE stating that the payment day locks when the Ajo activates, and that changing it afterwards requires the position-change process on SCR-MOB-06, which is not a calendar setting. Days 29, 30 and 31 are selectable only with *Last day of the month*, because a collection on the 30th that silently moves to the 28th in February is a broken promise. **What happens when that day is a public holiday is not settled, and this step does not pretend otherwise**; a line says a reminder is still sent and the collection is still expected."],
            ["Form fields", "Day of month, single-select, required. *Last day of the month* is a distinct option, not day 31."],
            ["Validation rules", "Required, one of 1 to 28 or the last-day option. A day between 29 and 31 cannot be selected individually, so there is no invalid range to report."],
            ["Loading state", "The consequence panel computes locally. The three sample dates are shown once the day is chosen, with no network call and no spinner."],
            ["Empty state", "Nothing selected and the consequence panel shows a single line: *Choose a day and we will show you the first three collection dates.*"],
            ["Error state", "None beyond the required check, which is inline on continue."],
            ["Success state", "Stored on the DRAFT; the wizard advances. No notice beyond the advance."],
            ["Responsive behaviour", "The day grid is 7 columns from 320 px with 44 px cells; each cell is a real button with the day number, and the selected cell is marked by fill, border and an accessible state together. Below 375 the grid is unchanged rather than reflowed, because a calendar that reflows is not a calendar."],
            ["Accessibility", "The grid is a `grid` with a row and column header structure and an accessible name, *Day of the month*. The selected day is `aria-pressed` or `aria-selected` and also carries a visible tick, so selection is not colour-only. The consequence panel is a live region announcing the three dates once the selection settles, not on each arrow key press."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.7.4 Step 4, the number of rounds — SCR-MOB-05.4"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Set the member count, which is also the round count, and show the total the Ajo will move in the member's own currency rather than an abstract multiplier."],
            ["Target user", "The organiser, who knows the size of the group. They need to see what the arrangement is worth, because that is the thing they are about to promise their group."],
            ["Layout", "Wizard chrome, then a card: a stepper or numeric field for members, and beneath it a four-line summary panel with the resulting schedule and totals."],
            ["Components", "`FormField` (number, stepper), `MoneyBlock`, `WizardProgress`, `Button` (primary and secondary), `Callout` (NOTE, that rounds equal members)."],
            ["Navigation", "Entered from 05.3. Back to 05.3. Forward to 05.5."],
            ["Primary CTA", "*Continue to invite members*. One filled button."],
            ["Secondary CTA", "*Back* (secondary outlined)."],
            ["Content", "Members, defaulting to 10, adjustable 2 to 50 subject to the configured cap. The summary panel, live: *10 members*, *10 rounds*, *each member pays NGN 1,020.00 per round*, *each member pays NGN 10,200.00 in total*, *the whole Ajo collects NGN 102,000.00, of which NGN 2,000.00 is the AJO.ng fee*. A NOTE stating that rounds equal members, so that nobody believes a group of ten can run fifteen rounds. **Both the per-member total and the Ajo total are shown; a member who only ever sees one of them will believe the wrong number.**"],
            ["Form fields", "Members, integer, required, 2 to the cap, with a decrement and increment control that are 48 px targets. A numeric keyboard is not forced, because a stepper is the primary control and a keyboard fights it."],
            ["Validation rules", "Integer within 2 to the cap. Out of range is rejected with the range, not with *invalid*. The summary does not recompute against an invalid value; it keeps the last valid value with the typed text marked invalid, as on 05.2."],
            ["Loading state", "The summary computes locally and appears within the same frame. No spinner, no minimum display time."],
            ["Empty state", "The field is empty and the summary shows the figures at the default of 10, labelled as an example."],
            ["Error state", "Inline on the field. The cap message names the cap figure rather than saying *too many*."],
            ["Success state", "Stored on the DRAFT; the wizard advances to the invite step."],
            ["Responsive behaviour", "The stepper row holds the decrement, the field, the increment and the unit label on one line at every width; the field never shrinks below 96 px. The summary panel stacks its label and figure on the same line at 320 px, keeping the figure right-aligned."],
            ["Accessibility", "The stepper is a labelled group with the field described by *Number of members, between 2 and 50*. Decrement and increment have accessible names stating the resulting value, *Fewer members, 9*, so a screen reader user knows the effect before pressing. The summary panel is a description list and is announced politely once the value settles."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.7.5 Step 5, inviting members — SCR-MOB-05.5"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Mint single-use invite links and hand them over in the way the group actually communicates, which for this product is usually WhatsApp, and show what remains of the five-day window."],
            ["Target user", "The organiser, who is about to send nine messages and wants to do it once. They are also the person most likely to invite someone by accident, so the step must make an invite revocable and obvious."],
            ["Layout", "Wizard chrome, then a card with three single-use invite links, each on its own row with the recipient label, a copy control and a share control, then a counter line and a share panel."],
            ["Components", "`FormField` (recipient name, optional), `CopyButton` (3), `ShareSheet` trigger, `Button` (primary and secondary), `CountdownPill`, `WizardProgress`, `Callout` (NOTE, single use)."],
            ["Navigation", "Entered from 05.4. Back to 05.4. Forward to 05.6, which is reachable whether or not a single invite has been created."],
            ["Primary CTA", "*Continue to the order*. One filled button. **The primary is never *Create invite*, because creating an invite is not the reason the organiser is here and a person who has minted nine links does not need a button to make a tenth.**"],
            ["Secondary CTA", "*Create 3 more invites* (secondary outlined) while the cap allows, and *Share all* (secondary outlined) opening the platform share sheet with the links."],
            ["Content", "The three links, each with a recipient label, a copy control and a share control, and each shown as truncated text with the full value available to a screen reader and to a long-press copy. The counter line: *2 of 3 invites used. The window closes in 4 days 6 hours.* The share panel: a prefilled message naming the Ajo, the amount, the frequency and the deadline, with the three canonical money figures. A NOTE stating that each link works once, that the recipient must sign in before it is consumed, and that an unused link stops working when the window closes. **The countdown is honest: if the window is closing, it is displayed, and it never resets by refreshing.**"],
            ["Form fields", "Recipient name, optional, text, 0 to 40 characters, used only as a label on the link so the organiser can tell which person each is for. Phone or email are **not** collected here: the link carries the invitation and the person supplies their own identity, which is what makes a single-use link single-use."],
            ["Validation rules", "Label length only. An invite mint failure leaves the existing links intact and reports the failure against the *Create 3 more* control, never by clearing the list."],
            ["Loading state", "The copy control shows a check for 2 seconds after use with its width locked, and never changes the row layout. Minting shows a working state on the *Create 3 more* control only; the three existing links stay interactive throughout, because a slow mint is not a reason to take away a copy button."],
            ["Empty state", "Not applicable in practice, because the step pre-mints three. If minting genuinely returns nothing, the step shows the share panel with no links and a working *Create 3 more* control."],
            ["Error state", "Inline against the control that caused it. An expired-window state replaces the links with a plain statement and a route to SCR-MOB-03, since an expired window is an Ajo state and not a form error."],
            ["Success state", "Copying confirms in place. The step does not advance on its own; the organiser chooses when to continue, because they may want to send the links first and may come back later, and the DRAFT is resumable."],
            ["Responsive behaviour", "One link per row at every width. At `md` and above the link, label and both controls sit on one line; below `md` the controls sit on a second line at 48 px tall. The share panel's message is a textarea that is read-only by default and editable, because groups add their own instructions."],
            ["Accessibility", "Each link row is a labelled group whose accessible name contains the Ajo name and the recipient label. The copy control announces *Link copied* politely, and its state change is also a visible tick, not a colour. The countdown is announced politely at most once a minute and is always available as text. **The full link value is never truncated in the accessible name**, so a member using a screen reader can pass it on."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.7.6 Step 6, the order — SCR-MOB-05.6"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Assign positions, and be explicit that the order is a proposal until the Ajo activates. This is the step where the social mechanics of an Ajo are decided, and where a rushed decision is most expensive."],
            ["Target user", "The organiser, who knows the group, and members who may ask to be placed differently. Both need to see who decided each position, not just what it is."],
            ["Layout", "Wizard chrome, then a reorderable list of ten slots, each a draggable row with a position number, a name field and a provisional marker. A legend explains the order rules beneath."],
            ["Components", "`ReorderableList`, `FormField` (name), `Badge` (provisional), `Button` (primary and secondary), `WizardProgress`, `Callout` (NOTE, what activation does)."],
            ["Navigation", "Entered from 05.5. Back to 05.5. Forward to 05.7. **This is the only step two roles can reach, and a member arriving here is read-only except for requesting a swap.**"],
            ["Primary CTA", "*Continue to review*. One filled button."],
            ["Secondary CTA", "*Back* (secondary outlined), and *Request a different position* (tertiary link) available to members, which opens a request naming the slot wanted and the reason."],
            ["Content", "Ten slots, numbered, each with a name field. Above the list, the amount each member pays per round and what the round pays out, so the order is chosen with the figures in view. Beneath, a NOTE stating the three rules plainly: the order is a proposal; a member may request a different position; **the order locks the moment the Ajo activates, and after that a change needs a formal replacement request**. A DECISION callout states that a member who requests a different position keeps their slot until the organiser responds, so requesting costs nothing and cannot be used to hold two slots."],
            ["Form fields", "Ten name fields, each optional, each 0 to 40 characters, each validated for duplicate names within the list. Names are the organiser's assertion about who is in the group; the platform does not verify them and must not imply that it has."],
            ["Validation rules", "Duplicates within the list are rejected on the second field with *This name is already in position N*. Empty slots are permitted, because the organiser may not know all ten yet; the step states how many are filled. Forward navigation is allowed with empty slots and the review step repeats the consequence."],
            ["Loading state", "Reorder persistence is optimistic with a quiet inline indicator, never a blocking spinner: a person dragging a row is not waiting for a save, and blocking them would make the drag feel broken. A failed persist keeps the local order, marks the row, and offers a retry."],
            ["Empty state", "All ten slots empty is allowed and is the common case at this point. The list renders ten numbered rows with empty fields and a line: *Fill in as many as you know. You can change this before you activate.*"],
            ["Error state", "A failed reorder is the only error and is inline on the affected row. A failed save never reverts the organiser's local order without saying so, because silently undoing a drag is the fastest way to lose their trust in the tool."],
            ["Success state", "The provisional order is stored on the DRAFT and the wizard advances. No notice beyond the advance."],
            ["Responsive behaviour", "One slot per row at every width. **Drag and drop is never the only way to reorder**: every row also carries move-up and move-down controls, which are 48 px targets and the primary mechanism on touch. At `sm` and below the drag handle is 24 px wide but the row is 64 px tall, and the whole row is a drag target, not just the handle."],
            ["Accessibility", "The list is an ordered list whose positions are read as *position 3 of 10, name, provisional*. Move controls announce their effect, *Move Ola to position 4*. Drag and drop is not exposed as a custom gesture; the move controls are the accessible path, and they are not hidden behind a long-press."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.7.7 Step 7, the review and acknowledgement — SCR-MOB-05.7"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show the finished Ajo back to the organiser in one read, collect an acknowledgement, and stop. **This step does not activate the Ajo and does not charge anything.** Activation is a separate, deliberate action on SCR-MOB-03, and the interface must not let a person leave this screen believing the Ajo is live."],
            ["Target user", "The organiser, immediately before they would otherwise message the group and say *we are set up*. The gap between *set up* and *active* is where a misunderstanding becomes a dispute."],
            ["Layout", "Wizard chrome, then a single review card: a summary table of the eight configured facts, the full eleven-row canonical money table, the roster, the invite status, and a closing acknowledgement region."],
            ["Components", "`Table` (summary, 8 rows), `MoneyTable` (canonical, 11 rows), `ListItem` (roster), `Checkbox` (acknowledgement), `Button` (primary and secondary), `WizardProgress`, `Callout` (NOTE, what activation means), `Callout` (DECISION, no commit here)."],
            ["Navigation", "Entered from 05.6. Back to 05.6. Exits to the Ajo list, where the Ajo is DRAFT. **There is no route from this screen that activates the Ajo.**"],
            ["Primary CTA", "*Save and close the wizard*, to the Ajo list. One filled button. **The label says what happens, and it is not called *Continue*, *Finish*, *Done* or *Activate* — every one of those reads as a commit to somebody who has not been told what committing does.**"],
            ["Secondary CTA", "*Edit* (tertiary link) beside each of the eight summary rows, returning to the owning step with the value preserved; and *Activate the Ajo* (secondary outlined) only when the preconditions in 4.9.1 are met, carrying a plain statement of what activation locks and what it starts."],
            ["Content", "The eight rows: name and description; members and rounds; amount per member per round; the three canonical money lines; total each member pays over the Ajo; the payment day with the first three collection dates; the proposed order; invite status with the window countdown. Then the full canonical money table. Then the roster as a list, with empty slots shown as *Empty* rather than hidden. Then the acknowledgement region: one checkbox, *I have read this and I understand that the Ajo is not active yet, that nobody can pay anything until it is, and that the order locks when it is activated*, and beneath it the NOTE naming what activation does and starts. **The acknowledgement is stored with a timestamp and the DRAFT's version, so it is a record and not a gesture.**"],
            ["Form fields", "Acknowledgement checkbox, required. The eight summary rows are read-only; editing is by navigation, never by inline edit, because a summary that can be edited in place is a form and not a review."],
            ["Validation rules", "The checkbox must be ticked to save and close. It is not ticked by default and it is never pre-ticked from a previous visit."],
            ["Loading state", "The review card renders in full with skeleton rows in final position. The activate control is inert until the preconditions resolve, and its inert state carries the reason as text rather than a disabled button with no explanation."],
            ["Empty state", "Empty slots in the roster and unconsumed invites are shown as facts, not omitted. A DRAFT with no invites is a valid state and the review says *No invites have been used yet*."],
            ["Error state", "A failed save of the acknowledgement is a banner with a retry; the checkbox state is preserved. A failed activation is handled on SCR-MOB-03, not here."],
            ["Success state", "The wizard closes to the Ajo list with a single confirmation naming the Ajo and stating *still a draft*. The Ajo appears in the list with the DRAFT badge."],
            ["Responsive behaviour", "One column at every width. The summary table becomes a stacked list below 768, label then value, in the same order. The canonical money table stacks as on SCR-WEB-05. The acknowledgement checkbox remains 24 px with a 48 px hit area."],
            ["Accessibility", "The summary is a real table with row headers; in the stacked form below 768 each pair is rendered with its label as a heading, so the relationship survives. The acknowledgement checkbox is a real checkbox with a full-sentence accessible name, and the NOTE is a labelled region that a screen reader user reaches directly from the checkbox via its description. Nothing on this screen is conveyed by a badge colour alone."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "table",
        "head": ["Review row", "Value source", "Stated as"],
        "rows": [
            ["Ajo name and description", "Step 1", "The name exactly as members will see it"],
            ["Members and rounds", "Step 4", "Both figures, with *rounds equal members* stated in the same cell"],
            ["Amount per member per round", "Step 2", "NGN, to the kobo"],
            ["Contribution, fee, total charged", "Computed", "The three canonical lines in the canonical order"],
            ["Total each member pays over the Ajo", "Computed", "NGN, and distinct from the total the Ajo collects"],
            ["Payment day and first three collection dates", "Step 3", "Dates, not a weekday name alone"],
            ["Proposed order", "Step 6", "Every slot, with empty slots shown as empty"],
            ["Invite status", "Step 5", "Used, unused, and the window countdown"],
        ],
        "widths": [1.7, 0.9, 3.9],
        "size": 7.2,
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "No activation from the wizard, and no fee line on this screen",
        "text": (
            "**SCR-MOB-05.7 has no commit action, and its primary button does not "
            "contain the word *activate*.** The wizard's job is to produce a DRAFT that "
            "the organiser is confident in. Activation happens on SCR-MOB-03, where the "
            "roster state, the invite window and the locks are all visible at once, and "
            "where the confirmation dialog can state in full what is being locked. "
            "A seven-step flow that ends by quietly starting a ten-round financial "
            "obligation is the single most expensive mistake this product could make, "
            "and the prevention is a label. **Owner: Founders.**"
        ),
    },
    {"t": "pagebreak"},

    # =============================================================== 4.8
    {"t": "h2", "text": "4.8 Joining and leaving — SCR-MOB-04, SCR-MOB-24, SCR-MOB-25"},
    {
        "t": "p",
        "text": (
            "Three screens and one rule that outranks all of them: **a member is never "
            "added to a financial obligation by a single tap, and a member is never "
            "removed from one by a single tap.** Both of those actions have a fee "
            "consequence, a social consequence inside a group, and in the leaving case "
            "a substitute, so all three screens disclose before they commit and none "
            "of them commits on a link follow."
        ),
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The three states of a membership",
        "text": (
            "**DRAFT** — an organiser configuring an Ajo; no obligation exists. "
            "**ENROLLING** — a window of exactly five days from creation, during which "
            "invites may be issued, positions are provisional, and leaving is free and "
            "immediate. **ACTIVE** — the obligation exists, the order has locked, and "
            "leaving is a replacement request rather than a withdrawal. All three "
            "appear in the join, invite and exit screens because a member can meet any "
            "of them, and a screen that only describes the friendly one is a screen "
            "that surprises somebody."
        ),
    },

    {"t": "h3", "text": "4.8.1 Join by code — SCR-MOB-04"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Let a member join an Ajo with a code from the organiser, and tell them what joining will cost them before they do it."],
            ["Target user", "A member who was told a code in a message or a phone call, and who is standing in a shop queue. They want this to work first time, and they are likely to mistype."],
            ["Layout", "Single card, 420 px. Code field with a large monospaced input, a working control, and beneath it a live validity hint that appears only once a plausible code is present."],
            ["Components", "`FormField` (code), `Button` (primary and secondary), `Callout` (NOTE, what joining means), `Footer`."],
            ["Navigation", "Tab 4 of 5, and the tab's empty state. Deep-linkable, so a notification can carry a code. Reached from SCR-WEB-14's inline code form as well, which shares this component."],
            ["Primary CTA", "*Join the Ajo*. One filled button, 56 px. **Disabled with a visible reason until a code of plausible length is present, and the reason is a line of text, not an absence of affordance.**"],
            ["Secondary CTA", "*Create an Ajo instead* (tertiary link) beneath, so the other route is always visible."],
            ["Content", "The code field, formatted in groups of four as it is typed, uppercase, spaces and hyphens stripped on input. Beneath, on a plausible code: *Found: Market women, 10 members, NGN 1,000.00 per month. You will pay NGN 1,020.00 each round.* **The three canonical lines appear here, at the point of discovery, not after joining.** A NOTE stating what joining does: your position is assigned, the order locks when the Ajo activates, and you can leave free until then."],
            ["Form fields", "Code, required, 6 to 12 characters after normalisation, uppercase, alphanumeric."],
            ["Validation rules", "Shape on blur. Existence is checked only on submit or on a code of plausible length, and **an unknown, expired, already-used and malformed code all produce the same message**: *That code is not valid, or the invite has closed.* One message for four states, because a message that distinguishes an expired invite is a way to enumerate live invites."],
            ["Loading state", "The working control sits inside the field's trailing edge with its width locked. The join button does not lock, so a member can correct a typo without waiting for a round trip."],
            ["Empty state", "Empty field with the helper text, and the NOTE visible so the member understands the commitment before typing."],
            ["Error state", "Inline on the code field for shape; a banner for a submit that fails for reasons other than the code. A rate-limit response names the wait, does not clear the code, and offers the support route."],
            ["Success state", "The membership exists and the member lands on the Ajo detail screen with a single confirmation naming the Ajo, the position and the first due date. The position is stated in words, because position is a social fact and a number alone can be misread as a rank."],
            ["Responsive behaviour", "Single card at every width; 16 px side padding below 375. The code input is 64 px tall on mobile, because a mistyped code on a small keyboard is the most likely failure on this screen and a bigger field is the cheapest defence."],
            ["Accessibility", "The live hint is a polite region, announced once the check settles. The formatted grouping is visual only; the accessible value is the ungrouped string. The join button's accessible name includes the Ajo name once discovered. Rate-limit messaging is not conveyed by a countdown colour alone."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.8.2 Invitation — SCR-MOB-24"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Bridge a member from a link in a message into tier 2, and make accepting an invitation a deliberate act with the fee, the obligation and the position all visible first."],
            ["Target user", "A member who received a link, on a phone, possibly on mobile data, possibly while the organiser is waiting for an answer. They have not chosen this and may not know what an Ajo is."],
            ["Layout", "A single centred card. Above the fields: the Ajo name, description, purpose, member count, amount, frequency and the countdown, in a fixed block. Below: the three canonical money lines. Below that: the position, if the link carries one, or the statement that positions are provisional. At the bottom: the single commit control."],
            ["Components", "`ProseBlock`, `MoneyBlock` (3 lines), `CountdownPill`, `Badge`, `Button` (primary and secondary), `Callout` (NOTE, single use), `Footer`."],
            ["Navigation", "Reached from `/invite/:token` and `/app/join/:token`, both `noindex`, `nofollow`, `no-store`. An unauthenticated visitor is sent through sign-in with `returnTo` to this exact route, per 4.24.5."],
            ["Primary CTA", "**Conditional on authentication, and never a bare *Accept*.** Unauthenticated: *Sign in to accept* (filled). Authenticated and eligible: *Join the Ajo* (filled). Authenticated and ineligible: the filled control is absent and a plain statement replaces it, per the error states below."],
            ["Secondary CTA", "*Not now* (tertiary link) for an authenticated member, which closes the card and returns to the Ajo list. Unauthenticated: *Create an account* (tertiary link) and *Read how it works* (tertiary link)."],
            ["Content", "The Ajo facts, the three canonical money lines, the position or the provisional statement, the countdown to window close, the payment day and the first collection date. A NOTE stating that this link works once, that the position locks at activation, and that leaving is free and immediate until then. **If the link carries a position, the position is shown by name and number together — *Position 4, after Adaeze* — because a number alone invites a member to infer a hierarchy that a rotating scheme does not have.**"],
            ["Form fields", "None. The link carries the invitation; the member supplies nothing beyond an authenticated session, and the interface must not ask for a phone number or a name on this screen."],
            ["Validation rules", "Not applicable. Eligibility is decided server-side from the token's state, the member's membership and the Ajo's state, and the interface renders the result rather than deciding it."],
            ["Loading state", "The card renders after the token resolves, with a skeleton in final position. **The commit control never appears before eligibility resolves**, because a control that appears and then changes its label is a control that has already been tapped."],
            ["Empty state", "Not applicable."],
            ["Error state", "Four non-eligibility states, each with a plain statement, a named reason where the member can act, and one way forward. Expired or window closed: *This invite has closed. Ask the organiser for a new one.* Already a member: *You are already in this Ajo*, with a link to it. Already used by someone else: *This link has already been used. Ask the organiser for a new one.* Restricted account: a link to SCR-WEB-17, which is the only correct destination and not a support chat."],
            ["Success state", "The membership exists and the member lands on the Ajo detail screen. A single confirmation names the Ajo, the position and the first due date. The link is now spent and, if opened again, returns the already-used state rather than an error."],
            ["Responsive behaviour", "The card is one column at every width, max 480 px. The fact block becomes a two-column key-value layout at `sm` and above and stacks below it, always in the same order, with the money lines last and never above the fold on a 320 × 568 screen."],
            ["Accessibility", "The whole card is a labelled region named after the Ajo, so a screen reader user arriving from a link is told what they have landed on before reading further. The countdown is text plus a polite announcement at most once a minute. The three canonical money lines are a description list and are never abbreviated to *NGN 1,020/month*. The commit control's accessible name includes the Ajo name: *Join Market women*."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.8.3 Replacement and exit request — SCR-MOB-25"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Handle the only way a member leaves an active Ajo, which is by asking to be replaced, and make the requester, the organiser and the substitute all aware of the same consequences before anyone commits."],
            ["Target user", "A member who has joined an Ajo, paid a round or several, and can no longer continue. They are frequently embarrassed, and frequently have a real reason they will not want to explain to a group chat. They are also, at that moment, the most likely person in the product to abandon it silently."],
            ["Layout", "Two states on one route. **Before submission**: a single card with the Ajo facts, the reason field, a suggested-substitute field, and the consequence panel. **After submission**: a status region with the request's state, what has and has not happened, and the two people who need to act."],
            ["Components", "`FormField` (reason, substitute), `Callout` (WARNING, consequences), `RadioGroup` (suggested or open), `Button` (primary and secondary), `StatusCard`, `Timeline`, `Footer`."],
            ["Navigation", "Reached from the Ajo detail screen's *Request to leave* action, which appears only on an ACTIVE Ajo. Deep-linkable, per section 3. Reached for a DRAFT or ENROLLING Ajo by the Ajo detail's *Leave* action instead, which is immediate and free and does not use this route."],
            ["Primary CTA", "Before submission: *Send the request*. One filled button, 56 px, and it is never labelled *Leave*, *Exit* or *Remove me* — a member reading a button called *Leave* is agreeing to something they have not been told."],
            ["Secondary CTA", "*Cancel and keep my place* (tertiary link), which is the prominent, easy, unpunished option and is styled as an ordinary link, not as a dead end. *Contact support* (tertiary link) for a member who wants to talk rather than type."],
            ["Content", "Before submission: the Ajo name, the member's position, the rounds remaining, the amount still to be paid by the member, and the substitute field. The consequence panel, stated as four bullets: your place is held until this is resolved; the organiser is told privately and not in the group; **you remain liable for contributions until a replacement is accepted**; the replacement, once accepted, takes your position and the obligation from that round. A WARNING callout for the case where the Ajo has already reached the member's turn: *Your round has already come. Once you have been paid, you keep the money and your place passes to the replacement; you are not asked to return it.* **The reason field is free text and is explicitly optional**, with a note that it is shared with the organiser only and never with the other members."],
            ["Form fields", "Reason, textarea, optional, 0 to 500 characters, with the helper text naming who sees it. Suggested substitute, radio group plus an optional name field, defaulting to *no suggestion*, because suggesting a person on someone's behalf is a social act the member may not want to perform. Both fields are free of validation beyond length."],
            ["Validation rules", "Length only. **A member must be able to submit with no reason and no suggestion**, and the interface must not nudge them to supply either; the friction of a required reason field is exactly what converts a difficult conversation into an abandonment."],
            ["Loading state", "The button works with its width locked and the fields remain editable. After submission the card is replaced by the status region."],
            ["Empty state", "Not applicable. The form is never presented as an empty state, and the consequence panel is visible before any input."],
            ["Error state", "Submit failure is a banner with a retry, preserving the reason and the suggestion. A request already pending shows the status region instead of the form, with a *Withdraw request* tertiary link, because sending two requests is not a thing the member should have to think about."],
            ["Success state", "The status region appears immediately, stating: the request is pending; the organiser has been told privately; the member's place is held; the member remains liable until a replacement is accepted. The organiser's own state is the organiser's screen, not this one. There is no *you have successfully left the Ajo* message, because the member has not left."],
            ["Responsive behaviour", "One column at every width. The consequence panel is a four-bullet list with 8 px between items and no collapse at any width; at 320 px the bullets wrap with a 20 px hanging indent so the markers align."],
            ["Accessibility", "The consequence panel is a labelled region with the `h2` *What happens when you send this*, reachable directly from the submit control's description. The status region's four statements are a definition list, so a screen reader user can hear them one at a time. State changes on the status region are announced politely. The submit control's accessible name is *Send the request to leave Market women*."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "The exit route has no required reason and no exit in the first place",
        "text": (
            "**SCR-MOB-25 is a request to be replaced, not a withdrawal, and it is named "
            "accordingly in the interface.** There is no route anywhere in the product "
            "that removes a member from an ACTIVE Ajo outright, because a rotating "
            "savings scheme cannot absorb a vacancy: the round's pool would be short by "
            "one member's contribution and the next recipient would receive less than "
            "the Ajo promised. The substitute is not an administrative convenience; it "
            "is the mechanism by which the scheme continues to work. The reason field "
            "is optional for the same reason: a required explanation is a tax on a "
            "decision that has already been made, and it is a tax paid to a group. "
            "**Owner: Founders.**"
        ),
    },
    {"t": "pagebreak"},

    # =============================================================== 4.9
    {"t": "h2", "text": "4.9 Ajo detail — SCR-MOB-03"},
    {
        "t": "p",
        "text": (
            "One screen, five jobs, and the only place in the product where a single "
            "control starts a ten-round financial obligation. The screen is organised "
            "around a fixed region order so that a member who has been here before "
            "finds the same thing in the same place, and so that the activate control "
            "is never above the consequences it commits them to."
        ),
    },
    {
        "t": "table",
        "head": ["Region", "Contents", "Visible to", "Present in"],
        "rows": [
            ["Header", "Name, status badge, position, countdown if enrolling", "All participants", "All states"],
            ["State banner", "What this Ajo's state means and what can be done now", "All participants", "All states"],
            ["Economics", "The three canonical money lines, the base pool, the round's progress", "All participants", "All states"],
            ["Next event", "The next collection or payout, with its date", "All participants", "ENROLLING and ACTIVE"],
            ["Actions", "Activate, invite, share, request to leave, or pay, by state and role", "By role and state", "Conditional"],
            ["Roster preview", "First five members and the total count", "All participants", "All states"],
            ["Activity", "The last five events for this Ajo", "All participants", "ENROLLING and ACTIVE"],
        ],
        "widths": [1.0, 2.4, 1.3, 1.8],
        "size": 7.2,
    },

    {"t": "h3", "text": "4.9.1 Ajo detail — SCR-MOB-03"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Be the single page on which a participant understands an Ajo completely: its state, its figures, its people, its next event, and the one action available to them in this state. It also hosts the activation gate."],
            ["Target user", "Any participant. The dominant case is a member who has just joined and is deciding whether they have understood what they signed up for; the second is an organiser with a DRAFT or an ENROLLING Ajo who is deciding whether to activate."],
            ["Layout", "One scrolling column, max 720 px, with the region order above. The actions region sits below the economics and the next event and **above** the roster. On a 375 × 667 screen the header, the state banner and at least the first two economics lines are visible without scrolling; activation is never among them, because an action that commits must be scrolled to."],
            ["Components", "`Header` (name, badge, position), `Callout` (state banner), `MoneyBlock` (3 lines), `Card` (next event), `Button` (primary, conditional), `Button` (secondary, 2 to 3), `ListItem` (roster preview), `ListItem` (activity), `CountdownPill`, `Badge`, `BottomNav`."],
            ["Navigation", "Reached from the Ajo list, the dashboard's Ajo region, the invite card, any Ajo-scoped notification, and the wizard's exit. Deep-linkable. Returns to the Ajo list, not to the dashboard, so back does not lose the member's place in a list they were working through."],
            ["Primary CTA", "**Exactly one, and it is decided by state and role, never by recency.** DRAFT with the organiser: *Activate the Ajo* when the preconditions hold, otherwise *Continue setting up*, which returns to 05.4. ENROLLING with the organiser: *Invite more members*. ENROLLING with a member: nothing; this screen has no member action in this state. ACTIVE with a contribution due: *Pay NGN 1,020.00*. ACTIVE with nothing due: *View the schedule*. CANCELLED: none, ever."],
            ["Secondary CTA", "By state: *Share the invite* (ENROLLING, organiser), *Copy the Ajo code* (ENROLLING, all), *Request to leave* (ACTIVE, member, tertiary), *Invite a member* (ACTIVE, organiser, tertiary), *Read the fees* (all, tertiary), *View all members* (all, secondary, to SCR-MOB-06), *View the schedule* (ACTIVE, secondary, to SCR-MOB-07). **Tertiary actions never carry a filled style, and a destructive or consequential action is never tertiary unless it is a link to more information.**"],
            ["Content", "Header: name, status badge, the member's position by name and number, the countdown if ENROLLING. State banner: one sentence on what the state means, written per state, with what can and cannot be done now. Economics: *Contribution NGN 1,000.00*, *Fee at 2% NGN 20.00*, *Total charged NGN 1,020.00*, then *This round pays out NGN 10,000.00*, then the progress line. Next event: the date, the event, and who it concerns. Actions. Roster preview: five names and *and 5 more*, with no surname on the preview for a member — the full roster is on SCR-MOB-06. Activity: five entries with dates and amounts."],
            ["Form fields", "None on this screen. The one exception is the activation confirmation, which is a dialog, not a form: it has no fields, only a statement and two controls."],
            ["Validation rules", "Not applicable. **Every precondition for activation is resolved and stated before the control is enabled, and the control is never enabled on the basis of a client-side guess.**"],
            ["Loading state", "Region skeletons in final position, with the money block reserving its five lines. The actions region renders only after state and role resolve, so a control is never shown and then retracted."],
            ["Empty state", "A DRAFT with no members shows an empty roster preview with the invitation count and a link to the invite step. An ACTIVE Ajo has activity by definition, and an empty activity list is treated as a loading state rather than shown as empty, because an active Ajo with no activity is a bug, not a state."],
            ["Error state", "Contained per region per 4.24.8. **If the caller is not a participant, this route returns the tier-2 not-found screen, identical to a genuinely absent Ajo — no distinction in status code, wording, timing or layout, so the route cannot be used to discover that an Ajo exists.**"],
            ["Success state", "Payment returns here with a confirmation naming the amount and the receipt. Activation returns here with the state now ACTIVE, the banner rewritten, and a single confirmation naming the order lock and the first due date — the two things that just became true."],
            ["Responsive behaviour", "One column at every width. At `md` and above the economics block and the next-event card sit side by side; below `md` the economics block comes first and is never abbreviated. The roster preview is always five entries, never a carousel."],
            ["Accessibility", "The `h1` is the Ajo name and the status badge's text is part of it, so a screen reader user learns the state on arrival. The money block is a labelled region named *This Ajo's figures* and is the first focusable region after the header. The actions region is a labelled region so it can be reached directly. The activation control is a real button whose accessible name is *Activate the Ajo* and whose description is the dialog's full statement, so the consequence is available before the press. Skip link to the actions region exists on this screen specifically, because it is the region people come here for."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The activation dialog is specified in full",
        "text": (
            "Activating a DRAFT requires every one of these: the roster has at least two "
            "filled slots and no duplicate names; the amount, frequency and member count "
            "are set; the first three collection dates are computable; the organiser has "
            "read the state banner on this screen. Where a precondition fails, the "
            "control is not merely disabled: the failing precondition is stated as text "
            "immediately above it, with a link to the step that fixes it. Where all hold, "
            "the control is enabled and opens a dialog with the `h2` *Activate this Ajo?* "
            "and this body: *Activating locks the order of members. Members will be "
            "assigned contribution dates from the collection day you chose. Nobody can pay "
            "or be paid until then. From activation, every member owes NGN 1,020.00 each "
            "round, and leaving requires a replacement.* Two controls: *Activate* (filled) "
            "and *Not yet* (secondary). **The dialog is not dismissible by tapping the "
            "scrim**, because a destructive commitment that can be lost to a stray tap is "
            "a commitment that will be lost."
        ),
    },

    {"t": "pagebreak"},

    # =============================================================== 4.10
    {"t": "h2", "text": "4.10 Members — SCR-MOB-06"},

    {"t": "h3", "text": "4.10.1 Ajo members — SCR-MOB-06"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show the whole roster, in the order that will be paid, and give the organiser the three write actions they are allowed: invite, propose a position change, and act on a replacement request."],
            ["Target user", "Every participant, who comes here to see who is in the Ajo and when their turn is. The organiser, who comes here to see the same thing and to act. **A non-organiser member viewing the roster is the normal case, and this screen must not read as an admin tool.**"],
            ["Layout", "One column. A header with the count and a status line, then a numbered list of member rows. Each row is 64 px: position number and name on the left, a right-aligned status line, and an overflow control only where the viewer has an action available."],
            ["Components", "`ListItem` (member, numbered), `Badge`, `Sheet` (row actions), `FormField` (proposal), `Button` (primary and secondary), `EmptyState`, `ListItem` (pending requests)."],
            ["Navigation", "Reached from SCR-MOB-03's *View all members*, from a position notification, and from a replacement-request notification. Deep-linkable."],
            ["Primary CTA", "Conditional by state and role. ENROLLING with the organiser: *Invite more members*. ENROLLING with a member: none. ACTIVE with the organiser and a pending replacement request: *Review the request*. ACTIVE with a member and a request they filed: none; the pending request is shown as a status card. **A member with an action available never has it as a filled control in the list itself; it is in the row's sheet, so that one member's action is not mistaken for the Ajo's.**"],
            ["Secondary CTA", "*Propose a position change* (secondary outlined, organiser only, ACTIVE only), and *Copy the invite link* (secondary outlined, ENROLLING, organiser). Tertiary: *Read the fees*."],
            ["Content", "The numbered roster, in position order, each row carrying the position, the name, the membership status, and the member's own due date where one applies. Pending replacement requests appear as a separate list above the roster, visible to the organiser and to the affected member, and to nobody else. **The roster shows a first name and an initial only. Full names, phone numbers, bank details and identity documents are never on this screen, because a roster is the screen most likely to be read over someone's shoulder.**"],
            ["Form fields", "None on the list. The propose-position sheet contains a target position selector and a reason, both optional, and the position-change request sheet contains a name, both conditional and both documented in 4.24.7."],
            ["Validation rules", "Position changes cannot target an occupied slot without naming the member being displaced, and the request states that the displaced member is told. A request cannot be made by a member onto themselves."],
            ["Loading state", "Ten row skeletons at final height. **The count in the header appears with the rows, never first at zero**, because a header that says *0 members* above ten skeletons is a lie for a second."],
            ["Empty state", "A DRAFT or ENROLLING Ajo with no filled slots: *No members yet*, the empty-state line, and the organiser's invite control. A DRAFT with no members is a legitimate state, and this screen does not treat it as an error."],
            ["Error state", "Contained to the list region. A failed action in a row sheet reports inside the sheet and leaves the roster untouched, because a roster that reflows after a failed write looks like the write half-succeeded."],
            ["Success state", "A proposed change shows a status card reading *Position change proposed. It takes effect only if every affected member accepts*, which is the truth and is also the answer to the question every proposer asks immediately afterwards."],
            ["Responsive behaviour", "One row per member at every width, full width capped at 480 px. The overflow control is a 48 px target at the trailing edge. At `sm` and above the status line moves to a second line under the name rather than competing with it for width."],
            ["Accessibility", "The roster is an ordered list; the position is read as *position 4 of 10*. Each row's accessible name contains the name, the status and, for the affected member only, their own due date. The overflow control is a real button with a name naming the member, *Actions for Ola*, never a bare ellipsis. Status is text, not a badge colour."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =============================================================== 4.11
    {"t": "h2", "text": "4.11 Schedule — SCR-MOB-07"},
    {
        "t": "p",
        "text": (
            "The schedule is the Ajo's product. It is the one screen every participant "
            "checks on a specific day — their own collection date — and it is the screen "
            "where a provisional order has to be visibly provisional, because an order "
            "that looks settled in a screenshot is how a group ends up in an argument in "
            "a group chat."
        ),
    },

    {"t": "h3", "text": "4.11.1 Ajo schedule — SCR-MOB-07"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show every round with its collection date, its due member, and its payout date, and make it unmistakable whether the order shown is provisional or locked."],
            ["Target user", "Every participant, checking their own round. The organiser, checking that the collection days they agreed to are what the system will actually do. Both are checking a date, so dates are the largest thing on the screen."],
            ["Layout", "One column: a state strip, then a vertical list of rounds. Each round is a row-group of 88 px with the round number and the collection date on the left, the due member's name in the middle, and the status on the right. A **Your round** marker sits inline on the viewer's own row, not as a separate floating element."],
            ["Components", "`ListItem` (round), `Badge`, `Callout` (NOTE, provisional), `DateRow`, `Button` (primary and secondary), `BottomNav`."],
            ["Navigation", "Reached from SCR-MOB-03's *View the schedule*, from the dashboard's next-event card, and from any collection or payout notification. Deep-linkable, and a notification deep link scrolls to the named round rather than to the top."],
            ["Primary CTA", "Conditional. **A member whose round is the next one due and unpaid: *Pay NGN 1,020.00*.** No other primary on this screen; the schedule is a reading surface and a schedule with a filled button on it is a form wearing a calendar's clothes."],
            ["Secondary CTA", "*Add to calendar* (secondary outlined), offered for the viewer's own round and for the Ajo's collection days as a whole. Tertiary: *Read the fees*."],
            ["Content", "The state strip naming the Ajo's state. Then one row per round: *Round 1*, the collection date, *collected by* and the member's name, and the round's status. Each row also carries what the round will pay out — *pays NGN 10,000.00* — because a member looking at a date wants to know what is moving that day. The provisional note appears at the top of the list, not once per row: *This order is not final. It locks when the Ajo activates.* **Past rounds are shown with their actual status including *not collected*, and a past round that was not collected shows what the group is short by, without naming the member, to anyone but the organiser.**"],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Row skeletons at 88 px. The state strip resolves first and the provisional note is never shown before the state is known, because a provisional note shown on a locked Ajo is a lie and a locked note shown on a provisional one is worse."],
            ["Empty state", "A DRAFT before the payment day is chosen: *Choose a payment day to see the schedule*, with a link back to 05.3. This is the only schedule with nothing in it."],
            ["Error state", "Contained to the list region with a retry. The state strip and the viewer's own round persist, so a member who came here to check their date is not shown an empty screen because the history query failed."],
            ["Success state", "Payment made from this screen returns to it with the row's status updated to *collected* and a single confirmation naming the amount and the receipt."],
            ["Responsive behaviour", "One round per row-group at every width, stacked label-then-value below 375. The round number stays in a fixed 48 px gutter at every width so the eye can track down a column. **No month grid, and no horizontal scroll**: a schedule that a member cannot read in one vertical pass is not a schedule they will consult."],
            ["Accessibility", "The list is an ordered list, one item per round, and each item's accessible name is *Round 4, collection 12 October, collected by Chidi, pays NGN 10,000.00, collected*. The viewer's own round is marked with a text marker, not only a highlight. Dates are absolute and unabbreviated — *12 October 2026*, never *12/10* — because a Nigerian reader reads 12 October first and an ambiguous numeric date is a real failure mode at 12 October. Status is text."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =============================================================== 4.12
    {"t": "h2", "text": "4.12 Contributions — SCR-MOB-08, SCR-MOB-09, SCR-MOB-10"},
    {
        "t": "p",
        "text": (
            "Three screens, three owners, and the rule that governs all three: "
            "**a member is shown the full amount they will be charged, including the "
            "fee, on every surface and before every commit.** The contribution list "
            "answers *what do I owe*, the pay screen asks for the money, and the "
            "processing screen tells the truth about an attempt that has not finished."
        ),
    },

    {"t": "h3", "text": "4.12.1 Obligations and contribution detail — SCR-MOB-08"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "List everything a member owes across every Ajo they are in, grouped by what is due now, what is coming, and what is already settled — and, from the same component, show one contribution in full."],
            ["Target user", "A member with three obligations in three Ajos and a limited amount of money, who needs to decide which to pay first. The organiser, who needs the Ajo-scoped view of who has paid without seeing the amounts any individual paid into a different Ajo."],
            ["Layout", "List state: one column of grouped sections, each with a heading, a count and a total. Detail state: a single obligation card with the three canonical money lines, the Ajo facts, the due date, the state, and the action region. **Groups are ordered by urgency — overdue, due today, due this month, later, settled — and the ordering is stated in the group headings, because a member who has to infer it will assume the wrong one.**"],
            ["Components", "`SectionList`, `ListItem` (obligation), `MoneyBlock` (3 lines), `Card`, `Badge`, `Button` (primary and secondary), `SegmentedControl`, `EmptyState`."],
            ["Navigation", "Tab 3 of 5 as the cross-Ajo list. Deep-linkable in both states. The Ajo-scoped route and the cross-Ajo route render the same component, and a member's obligation is reachable from both the dashboard and the Ajo detail."],
            ["Primary CTA", "Detail state, eligible: *Pay NGN 1,020.00*. List state: **none.** Exactly one obligation's primary is the *only* filled control in the list, and it is on the first overdue or first due item, so a list of five does not become a page of five identical filled buttons."],
            ["Secondary CTA", "Detail: *View the receipt* when one exists, and *Ask for help* (tertiary). List: *View my receipts* (secondary outlined) and a filter control."],
            ["Content", "List rows: Ajo name, round, due date, the total charged, and the state. Detail: the Ajo name and the member's position, the round, the collection date, the three canonical money lines, the state, and the dates that matter — created, due, and paid where applicable. The detail view also states *If the Ajo does not collect this round, your NGN 1,000.00 is not paid out to anyone and the AJO.ng fee is not retained on it*, in a NOTE, because that is the single most common misunderstanding and it is the one that most damages trust when it goes wrong."],
            ["Form fields", "None. A contribution is not editable, only payable. There is no amount field anywhere in this group of screens, because a member who can change what they pay has been given a way to underpay without knowing it."],
            ["Validation rules", "Not applicable to the list. On the detail state, an obligation in a state that cannot be paid — collected, cancelled, expired, or belonging to a replaced membership — renders no action and states why."],
            ["Loading state", "Row skeletons per group, with the group headings rendered from the first response so the ordering is visible immediately. **The detail state never shows a partial amount: either all three money lines are present or the card is a skeleton.**"],
            ["Empty state", "A member with nothing owing: *Nothing to pay. Your next contribution will appear here*, with the Ajo's payment day and the estimated next date so the empty screen is informative. A filtered-empty list says which filter excluded what, and offers to clear it."],
            ["Error state", "Contained per section. **A failure to load the list never hides the dashboard's own summary**, so a member who arrives from the dashboard and finds the obligations region broken still has the figures that matter most."],
            ["Success state", "Payment returns to the detail state with the state updated, the receipt link present, and a single confirmation."],
            ["Responsive behaviour", "One column at every width, full width capped at 480 px. The list is never a two-column layout: two obligations side by side puts the total at a size a member cannot compare reliably on a phone."],
            ["Accessibility", "The list is a list of links whose accessible names follow *Ajo name, round N, due 12 October 2026, NGN 1,020.00, overdue* — amount and state adjacent in the name, because they are what a screen reader user is scanning for. Group headings are real headings. The money block on the detail state is a description list. State is text, and the overdue state is never conveyed by a red row alone."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.12.2 Pay a contribution — SCR-MOB-09"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Take a member's payment for a known obligation, showing the full amount and the fee before the payment method is chosen, and never optimistically."],
            ["Target user", "A member on a phone, possibly with little data, possibly standing somewhere they do not want to be entering bank details. They want this to work and they want to know the amount."],
            ["Layout", "One column, four regions in a fixed order: the obligation summary with the three canonical money lines; the saved payment method, if any; the payment method selector; and the pinned commit region with the total and the control. **The total is repeated in the commit region, adjacent to the control, so the figure a member authorises is the figure they just read.**"],
            ["Components", "`MoneyBlock` (3 lines), `ListItem` (method), `FormField` (card details or bank), `Button` (primary), `Button` (secondary), `Callout` (NOTE, what happens next), `Sheet` (method chooser), `SecurityNote`."],
            ["Navigation", "Reached from SCR-MOB-08's detail state and from its single list primary, and from a due-date notification. Deep-linkable. On success routes to 05.10."],
            ["Primary CTA", "**Dynamic and money-specific, and this is the one place the pattern is mandatory: *Pay NGN 1,020.00*.** The amount is in the label, so a member who has scrolled past the summary still authorises a specific figure. 56 px on mobile. Never a generic *Continue*."],
            ["Secondary CTA", "*Add a new payment method* (secondary outlined) when no method is saved, and *Cancel* (tertiary link) which returns to the obligation without a warning, because nothing has happened yet."],
            ["Content", "The obligation summary: Ajo, round, due date, position, and the three canonical lines. The method: name, type, and last four digits only — **a full card number or account number is never rendered back, not even masked to more than four digits**. A NOTE stating what happens after a successful payment, including that a receipt will be available immediately. A security note stating that AJO.ng never asks for a PIN and never asks for a one-time code by phone, in the imperative, because that sentence is the thing a member will remember when a real scam calls them."],
            ["Form fields", "Only when no method is saved: either card number, expiry and CVV, or bank account number with a resolved account name. Bank details are entered only on this screen, on an explicit user action, and are never pre-filled from anything. **A saved method is selected by tapping a row; no field is editable in place.**"],
            ["Validation rules", "Card: number, Luhn-checked locally, 12 to 19 digits; expiry in the future; CVV 3 or 4 digits. Bank: 10 digits, resolved against a named account, and **the resolved name must be confirmed by the member before the payment is attempted** — a silent name mismatch is how money goes to the wrong person. All messages state the fix."],
            ["Loading state", "The pay control enters a working state with its width locked and the summary stays fully visible. The method row shows its own working state while details resolve. **The control never shows success, and never disables itself permanently, on an attempt that has not returned.**"],
            ["Empty state", "No saved method: the method region shows the two options as a chooser rather than a blank region. An obligation that is already paid never reaches this route; if it does, the summary says so and offers the receipt."],
            ["Error state", "Inline on the fields for validation. A declined attempt produces a danger region with the provider's message in plain words where one is available, plus a named next action, and the obligation remains payable. **A decline never loses the typed card details within the same session**, and never offers an automatic retry: retrying a declined card once, on the member's initiative, is fine; retrying it for them is not."],
            ["Success state", "Routes to SCR-MOB-10 with the attempt's identifier. The obligation is not marked paid in this screen's copy, because the attempt is not the payment."],
            ["Responsive behaviour", "One column at every width. The commit region is pinned above the safe area on mobile, always showing the total and the control together, and the rest of the page scrolls beneath it. **The keyboard never covers the total**, because the total is the one thing that must remain visible while the member types a card number."],
            ["Accessibility", "The total is associated with the pay control by `aria-describedby`, so a screen reader user hears the amount as part of the control's description even if they never read the summary. The method rows are a labelled radio group. Errors are announced assertively; success is not announced here because nothing has succeeded. The security note is a labelled region reachable from the method region."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.12.3 Payment processing — SCR-MOB-10"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Tell the truth about a payment attempt that has not finished, and, once it has, tell the truth about the result. This screen exists because the interval between *I pressed pay* and *I know whether I paid* is where anxiety lives, and a spinner with no information is the worst possible answer to it."],
            ["Target user", "A member who has just pressed pay and is now holding their phone, waiting. A member returning to the app twenty minutes later who needs to know whether the money left. Both are answered by the same screen."],
            ["Layout", "One column. A state headline as the `h1`, a progress region, the three canonical money lines, the attempt facts — reference, method, started time — and the next action region. **There is no cancel control while the attempt is pending**, because a cancel that races the provider is a cancel that sometimes does not cancel."],
            ["Components", "`StatusCard`, `ProgressBar` (determinate where possible, otherwise indeterminate with real elapsed text), `MoneyBlock` (3 lines), `Timeline`, `Button` (secondary and primary, conditional), `Callout` (DANGER on failure), `RetryControl`."],
            ["Navigation", "Reached immediately from SCR-MOB-09, by deep link from the payment notification, and by returning to the app. **The screen is re-entrant: a member who closes it and comes back sees the live state, not a stale one.**"],
            ["Primary CTA", "Conditional on the resolved state. Pending: none. Succeeded: *View the receipt*. Failed or declined: *Try again*, which returns to SCR-MOB-09 with the same obligation and the same amount."],
            ["Secondary CTA", "Pending: *Check again* is a control inside the progress region, not a secondary button, and is used only after 90 seconds. Succeeded: *Back to the Ajo* (secondary outlined). Failed: *Use a different method* (secondary outlined) and *Ask for help* (tertiary)."],
            ["Content", "Pending: *We are confirming your payment. This usually takes under a minute. Do not pay again.* Failed: *Your payment did not go through. You have not been charged.* **That second sentence is the entire job of the failure state**, because a member who has been charged and told nothing is a support ticket, and a member who has not been charged and believes they have is a panic. Succeeded: *Paid. NGN 1,020.00 for round 3 of Market women*, with the receipt link. The attempt facts in all states, so a member quoting a reference reaches a human who can find it."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "This screen is the loading state, and it is specified as a screen rather than an overlay for that reason. The progress region distinguishes three sub-states of pending — sending, at the provider, confirming the result — and the third is the one that takes the time."],
            ["Empty state", "An attempt identifier that resolves to nothing: *We cannot find that payment.*, with the obligation and a way back. Never a bare not-found."],
            ["Error state", "Split deliberately between *declined*, *failed* and *unknown*. Declined and failed mean no money moved and are stated in those words. **Unknown means the result could not be determined and is stated as such: *We cannot confirm this payment yet. Your card has not been charged a second time, and we will tell you here as soon as we know.*** An unknown is never rendered as a failure, and never as a success."],
            ["Success state", "The obligation is marked paid, the receipt becomes available, the ledger entry is created, and the Ajo's progress updates. The member sees a single confirmation naming the amount, the Ajo and the round, and a receipt link."],
            ["Responsive behaviour", "One column at every width. The progress region is 160 px tall on mobile so the elapsed time and the state are both visible without scrolling, and the reference is selectable text."],
            ["Accessibility", "The state headline is the `h1` and changes with the state, so a screen reader user re-entering the screen learns the outcome immediately. **The state change from pending to resolved is announced assertively exactly once**, because an unpaid-then-paid transition is the one moment in this product that must interrupt. The progress region is a live region with a text state, not a bare animation."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "Three terminal states, not two",
        "text": (
            "Most payment interfaces collapse to success or failure. This product does "
            "not, because a provider timeout is a third thing and it is the one that "
            "generates the support tickets. **Unknown is a first-class state with its "
            "own copy, its own controls and its own recovery**, and it is never "
            "presented to a member as a failure. What a member must never be left "
            "believing is that money moved when it did not, or that it did not when it "
            "did."
        ),
    },
    {"t": "pagebreak"},

    # =============================================================== 4.13
    {"t": "h2", "text": "4.13 Receipts — SCR-MOB-11"},
    {
        "t": "p",
        "text": (
            "The receipt is the artefact a member keeps. It is the thing they will show "
            "a group, a spouse, a landlord or a bank, so it is built to be printed and "
            "to be legible in a screenshot, and it is the surface on which the fee is "
            "disclosed one last time, after the money has moved."
        ),
    },

    {"t": "h3", "text": "4.13.1 Receipt — SCR-MOB-11"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show an immutable, complete record of one payment, with the fee on its own line, in a form that can be saved, printed or forwarded and still mean something to a bank."],
            ["Target user", "A member proving they paid. Possibly anxious, possibly asked for proof by an organiser or a third party, possibly viewing on a phone and screenshotting it."],
            ["Layout", "A single centred document, max 480 px on mobile and 720 px on web, with a fixed header block — the AJO.ng mark, *Payment receipt*, the receipt number — then a facts table, then the money table, then a footer with the legal name, the date, and the support route. The action region is a separate full-width bar beneath the document and is **not** part of the document, so a printed or screenshotted receipt never contains a button."],
            ["Components", "`Document` (receipt), `Table` (facts, 8 rows), `MoneyTable` (canonical, 11 rows), `Button` (secondary), `Callout` (NOTE, immutable)."],
            ["Navigation", "Reached from SCR-MOB-10's success state, from SCR-MOB-08's detail state, from the payments list, from a transaction detail, and by deep link. **It is one receipt per route and it is never paginated.**"],
            ["Primary CTA", "None. **A receipt has no primary action**, because a receipt is a record and a record does not proceed anywhere. The document is the content."],
            ["Secondary CTA", "*Save as PDF* and *Share* as two secondary outlined buttons in the action bar, and *Print* on web only, where printing exists."],
            ["Content", "Header: the AJO.ng mark, *Payment receipt*, the receipt number, and the date. Facts: the member's name, the Ajo name, the member's position, the round number, the collection date, the method and its last four digits, the attempt reference, the date paid. **Then the canonical money table, unaltered and complete**, in which *total charged NGN 1,020.00* and *base pool paid to the recipient NGN 10,000.00* both appear, exactly as on SCR-WEB-05. Footer: the legal entity name, the support address, the terms reference, and a NOTE stating the receipt is immutable and that any correction appears as a separate reversing entry rather than an edit to this document."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Document skeleton at final height, including the eleven money rows, so a receipt never appears to grow as it loads — a growing receipt looks like the amount is changing."],
            ["Empty state", "Not applicable. A receipt identifier that does not resolve returns the tier-2 not-found screen, and an identifier belonging to another member returns the identical screen with no timing or wording difference."],
            ["Error state", "A partial load is not permitted. If any part of the receipt cannot be resolved, the whole document is withheld and a plain statement with a retry is shown, **because a receipt showing a contribution but not a fee is worse than no receipt**."],
            ["Success state", "Not applicable. The receipt is the terminal state of a payment and it never changes after issuance."],
            ["Responsive behaviour", "One column at every width, with the facts and money tables becoming stacked label-value pairs below 480 px **in the same order, with the money table's two emphasised rows still emphasised**. The action bar moves below the document and becomes a two-button row at `sm` and above and a stacked pair below it. Print styling removes the action bar, the navigation and the sheet trigger entirely and keeps the document at full width."],
            ["Accessibility", "The document is a `main` region with the receipt number as its accessible name target, so a member can confirm they are looking at the right document. Both tables have captions and row headers. The two emphasised rows are emphasised in weight *and* in the accessible name. **The fee line is never rendered as a small grey footnote**, because the one artefact a member forwards to somebody else must make the fee impossible to miss. The action bar is a labelled region outside the document."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =============================================================== 4.14
    {"t": "h2", "text": "4.14 Payouts — SCR-MOB-12, SCR-MOB-13"},
    {
        "t": "p",
        "text": (
            "A payout is the moment the Ajo delivers, and it is the one screen where a "
            "member is receiving rather than paying. The interface has one job here "
            "beyond recording the fact: **make NGN 10,000.00 unmistakably not "
            "NGN 10,200.00.** A recipient who believes they were short-changed by a fee "
            "is a support ticket and a reputational problem, and the prevention is that "
            "the base pool is the largest figure on the screen and the collected total "
            "is not on it at all unless they go looking."
        ),
    },
    {
        "t": "callout",
        "kind": "NOTE",
        "title": "The recipient's screen never shows the collected total",
        "text": (
            "On SCR-MOB-12 and SCR-MOB-13 the headline figure is **base pool paid to "
            "the recipient NGN 10,000.00**. The figure NGN 10,200.00 does not appear "
            "as a headline, a sub-headline or a tooltip, because a recipient has no "
            "operational reason to know the gross and every reason to misread it. The "
            "gross is available on the Ajo's economics surface for the organiser, where "
            "it is a reconciliation figure, and nowhere else. **Owner: Founders.**"
        ),
    },

    {"t": "h3", "text": "4.14.1 Payout list — SCR-MOB-12"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "List every payout the member has received, with the amount, the Ajo, the round, and the date, and make each one openable to a record."],
            ["Target user", "A member checking whether they have been paid this month, or looking for the record of a payment received months ago. The second group is larger than it looks: a rotating scheme produces a long history and people do look."],
            ["Layout", "One column. A summary line at the top, then a vertical list of payout rows, 80 px each: the amount left-aligned at the largest size on the screen, the Ajo and round in the middle, and the date on the right. **The amount is the visually dominant element of the row, because that is what the member came for.**"],
            ["Components", "`SummaryLine`, `ListItem` (payout), `MoneyBlock`, `Button` (secondary), `EmptyState`, `SegmentedControl`."],
            ["Navigation", "Reached from the dashboard's money block, from the Ajo detail's economics region, and from a payout notification. Deep-linkable, and the Ajo-scoped route renders the same component filtered."],
            ["Primary CTA", "None. A history is a reading surface. The only control in the first screenful is the filter, which is secondary."],
            ["Secondary CTA", "*Download a statement* (secondary outlined) for a selected period, and *View all receipts* (secondary outlined)."],
            ["Content", "The summary line: *3 payouts received, NGN 30,000.00 in total* — a total across payouts, which is a member's own money and carries no fee, so the two kinds of money never share a line anywhere in the product. Then rows: the base pool amount, the Ajo, the round, and the date. Each row carries its state, which for a payout is almost always *paid*."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Row skeletons at 80 px, with the summary line skeleton reserving the amount's width."],
            ["Empty state", "*No payouts yet. You will be paid when your round is collected.*, with the viewer's position and the estimated first payout date where the schedule knows them, because an empty payout screen is alarming and this one can be made reassuring with two facts."],
            ["Error state", "Contained to the list. A failed statement download reports against the control and does not clear the list."],
            ["Success state", "A statement download reports in place with a link to the file. A newly received payout appears at the top with a single confirmation."],
            ["Responsive behaviour", "One row per payout at every width. The amount never drops below 20 px. The filter becomes a sheet below `sm` and a segmented control above it, and **the filter state is stated in the summary line** so a filtered list never presents itself as the whole history."],
            ["Accessibility", "The list is a list of links with accessible names in the form *NGN 10,000.00 received, Market women, round 4, 12 October 2026*. The amount is the first thing in the name. The summary line is a live region updated when the filter changes, so a screen reader user knows the list is now filtered before they start reading it."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.14.2 Payout detail — SCR-MOB-13"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show one payout in full: the amount received, the Ajo and round it came from, the date, the destination, and what the round was worth before the fee."],
            ["Target user", "A member who has been paid and wants to reconcile it: *ten of us paid in, the pool was ten thousand, I got ten thousand.* The reconciliation must be possible from this screen alone, without a support ticket."],
            ["Layout", "A document-like single column: the payout amount as a large display figure, then a facts table, then a short reconciliation block, then a receipt link."],
            ["Components", "`DisplayAmount`, `Table` (facts), `MoneyBlock`, `Button` (secondary), `Callout` (NOTE, where the money came from)."],
            ["Navigation", "Reached from SCR-MOB-12's rows, from the Ajo detail's economics region, and from a payout notification. Deep-linkable."],
            ["Primary CTA", "None."],
            ["Secondary CTA", "*View the receipt* (secondary outlined) and *Download a statement* (secondary outlined)."],
            ["Content", "**Base pool paid to you NGN 10,000.00** as the display figure, at 32 px or larger. Facts: the Ajo, the round, the collection date, the payout date, the destination's masked form, and the payout reference. Then the reconciliation block, in exactly this form: *Ten members each paid NGN 1,000.00, which is NGN 10,000.00. AJO.ng added its fee of NGN 200.00 for the round, which is never taken from what you receive. You were paid NGN 10,000.00.* **The arithmetic is shown, not asserted, so a member can check it in their head and find it correct.** A NOTE linking to the fee page."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Skeleton reserving the display figure's width and the reconciliation block's three lines."],
            ["Empty state", "Not applicable."],
            ["Error state", "A payout that does not resolve, or that belongs to another member, returns the tier-2 not-found screen identically."],
            ["Success state", "Not applicable. Payouts are terminal records."],
            ["Responsive behaviour", "One column at every width. The display figure never wraps or truncates; the longest realistic value fits at 24 px in a 320 px viewport, and the layout steps down rather than clipping. The reconciliation block is prose at body size and is never reduced to a table on mobile."],
            ["Accessibility", "The display figure is a heading-adjacent display text with an accessible name of *Base pool paid to you, ten thousand naira*, so a screen reader user hears the number and its meaning together. The reconciliation is a paragraph read in order, which is the only order in which it makes sense. The masked destination is read as *account ending 4821*, never as a run of asterisks."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "pagebreak"},

    # =============================================================== 4.15
    {"t": "h2", "text": "4.15 Transactions — SCR-MOB-14"},
    {
        "t": "p",
        "text": (
            "Transactions are the ledger, read by a member. This screen is the most "
            "boring in the product and the one that most needs to be exactly right, "
            "because it is the screen a member opens when something has gone wrong and "
            "they are looking for the entry that proves it."
        ),
    },

    {"t": "h3", "text": "4.15.1 Transactions — SCR-MOB-14"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show the member's own ledger, in order, with every entry's type, amount, direction and the entry it corrected, and make each entry a permalink."],
            ["Target user", "A member reconciling what left and what arrived. Increasingly, this is also a member gathering evidence for a dispute or for a bank, which is why every entry is a stable, forwardable link."],
            ["Layout", "One column, grouped by month, each group with a heading and a subtotal, and rows of 64 px carrying a type icon, a one-line description, the date, and a right-aligned signed amount. The amount is right-aligned with tabular figures throughout so the decimal points line up, which is the only way a list of money can be scanned."],
            ["Components", "`SectionList`, `ListItem` (transaction), `MoneyText` (signed), `FilterSheet`, `Button` (secondary), `EmptyState`."],
            ["Navigation", "Reached from the dashboard's *View all activity*, from the More menu, and from any notification that references an entry. Deep-linkable to a single entry. The Ajo-scoped filter is available and states itself."],
            ["Primary CTA", "None. This is a ledger; it is read and exported, not acted upon."],
            ["Secondary CTA", "*Download a statement* (secondary outlined) and a filter control (secondary outlined, opening a sheet). Tertiary: *Read about your ledger* (tertiary link) to a short explanation of entry types."],
            ["Content", "Month headings with subtotals. Rows: the entry type — contribution, fee, payout, correction, refund; a one-line description naming the Ajo and the round; the date and time to the minute, because a correction must be placeable relative to the entry it corrects; and the signed amount, in naira to the kobo. **Corrections render as their own row linked to the entry they correct, and never as an edit to it.** The linked pair is shown together, with the correcting row indented and marked *Correction*."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Row skeletons at 64 px, with the first group heading rendered first so the structure is visible. Pagination loads on scroll with a footer sentinel, not a *Load more* button, and the sentinel carries an accessible label."],
            ["Empty state", "*No transactions yet.* with the two things that will produce the first one, which are the Ajo's payment day and the member's position."],
            ["Error state", "Contained to the list. A page load failure keeps the already-loaded months and reports the failure at the foot, so a member reading history is never returned to the top of an empty screen."],
            ["Success state", "A statement download reports in place with a link."],
            ["Responsive behaviour", "One row per entry at every width. The filter becomes a sheet below `sm`. The signed amount is never truncated and never moves above the description, so the two are never compared at different scales."],
            ["Accessibility", "The list is a list of links with accessible names in the form *Contribution, NGN 1,020.00, Market women round 3, 12 October 2026*. **Direction is stated in words — *paid out* or *received* — and never by a leading minus or plus sign alone**, because a screen reader user is not told which one a minus sign means. A correcting entry's accessible name begins *Correction of*, naming the entry corrected."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =============================================================== 4.16
    {"t": "h2", "text": "4.16 Notifications — SCR-MOB-15"},

    {"t": "h3", "text": "4.16.1 Notifications — SCR-MOB-15"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Collect everything the product has tried to tell a member in one place, permanently, including messages whose delivery channel failed, and make each one a link to the thing it is about."],
            ["Target user", "A member who missed an SMS, or who is checking in with their phone offline, or who wants to know what the system told them last week. The third case is the one people forget to design for and it is the reason this screen is a list rather than a toast stream."],
            ["Layout", "One column. Unread count in the header with a *Mark all read* tertiary link, then rows of 72 px: a type icon, a title, a one-line body, a relative time, and an unread marker. Rows group by day, with a *Today* and *Yesterday* heading."],
            ["Components", "`ListItem` (notification), `Icon`, `Badge` (unread), `RelativeTime`, `EmptyState`, `Button` (secondary)."],
            ["Navigation", "Reached from the top bar's bell, which carries the unread count as text, and from a notification deep link, which marks the entry read on arrival. `noindex`."],
            ["Primary CTA", "None. A list of things to go to has no primary action."],
            ["Secondary CTA", "*Mark all as read* (secondary outlined) at the foot of the list when anything is unread."],
            ["Content", "One row per notification, typed. The types: payment due, payment confirmed, payment failed, payout sent, Ajo activated, Ajo cancelled, round collected, round not collected, position changed, replacement requested, replacement accepted, identity check needed, security alert, support reply. **Every money-bearing notification names the amount and the direction in the body text, not only in the destination screen**, because the notification is often read on a lock screen with half the screen covered. A *not collected* notification names the Ajo and the shortfall and **never names the member who did not pay, to any recipient.**"],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Six row skeletons at 72 px. The unread count resolves with the rows and is never shown as a stale number."],
            ["Empty state", "*No notifications yet. Payment and payout messages will appear here.*, which is the truthful statement of what this screen will ever contain."],
            ["Error state", "Contained to the list with a retry. A failure to mark as read is silent — it is a preference, and surfacing it would be noise."],
            ["Success state", "Marking read removes the marker in place without a toast. Opening a notification marks it read and does not remove it, because a member who has read a payment-failed notification needs it to still be there tomorrow."],
            ["Responsive behaviour", "One row per notification at every width, full width capped at 480 px. At `sm` and above the time moves to the trailing edge; below it sits under the title. The body is clamped to two lines at every width, and the full text is in the row's accessible name."],
            ["Accessibility", "The list is a list of links. The unread marker is a text badge as well as a visual dot, and the row's accessible name begins *Unread* where unread. Relative times are accompanied by the absolute date in the accessible name — *two days ago, 12 October 2026* — because *2d* is meaningless aloud. The unread count on the bell is text, not a bare dot."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "pagebreak"},

    # =============================================================== 4.17
    {"t": "h2", "text": "4.17 Disputes — SCR-MOB-16, SCR-MOB-17, SCR-MOB-18"},
    {
        "t": "p",
        "text": (
            "Three screens: the list, the filing form, and the case. The rule that governs "
            "all three is the hardest one in the product: **the person who filed a "
            "dispute and the person it is about are both participants, and the interface "
            "must let one of them tell the truth about the other's behaviour without "
            "exposing them to each other.** So a case shows a member only what they are "
            "entitled to see, and the other party's name is never rendered as a public "
            "label — it is a party to the case."
        ),
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Default handling never appears in another member's view",
        "text": (
            "**No member-facing screen in this product shows another member's unpaid "
            "contribution, their name beside a *did not pay* state, or any part of a "
            "recovery case that does not concern them.** The organiser sees that a round "
            "is short and by how much, which they need in order to run the Ajo, and does "
            "not see who. Disputes are visible to their parties, to staff, and to nobody "
            "else. This is the rule most likely to be violated by a well-meaning "
            "convenience later — by a share sheet, an export, or an activity feed — and "
            "it is therefore specified here, in the place where a future change would "
            "have to be argued against. **Owner: Founders.**"
        ),
    },
    {"t": "h3", "text": "4.17.1 Dispute list — SCR-MOB-16"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show a member the cases they are a party to, with each case's state, what is awaited and of whom, and nothing at all about anyone else's cases."],
            ["Target user", "A member with a live case, checking whether anything has moved. The waiting is the hard part, so the list's job is to say what happens next and when, not to display a status vocabulary."],
            ["Layout", "One column of case rows, 88 px: the reference at the leading edge, the subject line, the state, and a right-aligned line naming the next step and who owes it — *awaiting your reply* or *awaiting our review*."],
            ["Components", "`ListItem` (case), `Badge`, `Reference`, `EmptyState`, `Button` (primary and secondary)."],
            ["Navigation", "Reached from the More menu and from any dispute notification. Deep-linkable. `noindex`."],
            ["Primary CTA", "**Exactly one, and only when it exists: *Open a dispute*.** With an existing case, the primary is absent, because a member with a live case must not be invited to open a second one over it."],
            ["Secondary CTA", "*Read how disputes work* (secondary outlined), which states the process, the timescales and what a member should gather, in three paragraphs."],
            ["Content", "Per case: the reference, the Ajo and round, the subject as the member wrote it, the state in plain words, the date opened, and the next step with its owner. **States are rendered as sentences — *we have your details and are reviewing* — not as codes**, with the internal code available in the case view for anyone quoting a reference to support."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Row skeletons at 88 px."],
            ["Empty state", "*You have no disputes.*, with the *Open a dispute* control and a line stating that opening one does not affect a member's standing in the Ajo, because that is what people believe will happen and it is not true."],
            ["Error state", "Contained to the list with a retry."],
            ["Success state", "Filing a case returns here with the new case at the top and a confirmation naming the reference."],
            ["Responsive behaviour", "One case per row at every width. The next-step line is never truncated with an ellipsis at any width; it wraps to a second line, because a wrapped *awaiting your reply* is still useful and a truncated one is not."],
            ["Accessibility", "The list is a list of links whose accessible names follow *Case 7FQK2M, Market women round 3, under review, awaiting our reply*. The state is in words. The reference is selectable text, so a member can read it aloud to a support agent."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.17.2 Open a dispute — SCR-MOB-17"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Collect a dispute in the member's own words, attached to a specific obligation, payout or ledger entry, and tell them immediately what will happen and roughly when."],
            ["Target user", "A member who is angry, or frightened, or who has been let down by a group rather than by a platform. They are not going to read a form carefully, and the form must not require them to."],
            ["Layout", "One column: a short statement of what a dispute is and is not, the category selector, the related item selector, the description, the evidence uploader, and a closing region stating the process and the timescales."],
            ["Components", "`Select`, `FormField` (description), `FileUpload`, `Callout` (NOTE, what happens next), `Button` (primary and secondary), `ConsentCheckbox`."],
            ["Navigation", "Reached from SCR-MOB-16, from a receipt's *Ask for help* tertiary action with the related item pre-selected, and from a transaction detail. Not deep-linkable with a body."],
            ["Primary CTA", "*Open the dispute*. One filled button, 56 px."],
            ["Secondary CTA", "*Cancel* (tertiary link), which returns without a prompt, because nothing has been sent. *Read how disputes work* (tertiary link)."],
            ["Content", "A NOTE stating plainly what a dispute does and does not do: *we will look at the record and reply; opening a dispute does not pause a collection, does not change your position, and does not tell the other members*. Category: a payment I made did not arrive, a payment I did not make, a payout that was wrong, a member's conduct, something else. The description field with a prompt, not a label alone: *Tell us what happened, in your own words.* The uploader accepting images and PDFs up to 10 MB, with a line **do not upload your BVN, your PIN, your one-time codes, or a screenshot showing your full bank balance**."],
            ["Form fields", "Category, select, required. Related item, select, required — an obligation, a payout or a transaction, restricted to the member's own items. Description, textarea, required, 30 to 4,000 characters, live count from 3,500. Evidence, optional, up to 5 files, 10 MB each, images and PDFs only. A consent checkbox confirming the statement is true to the best of their knowledge, required."],
            ["Validation rules", "Category and related item required, inline on submit. Description minimum 30 characters, enforced on submit rather than on input, so a member is not stopped mid-thought. File type and size checked on selection, with the offending filename named. **A description that names another member's bank details or documents is not blocked automatically; it is accepted and the warning is repeated, because silently refusing a member's evidence mid-dispute is worse than asking them to remove it.**"],
            ["Loading state", "The open control works with its width locked; the form stays editable. Upload progress is per file, in place, and the control is not disabled while files upload, because the form can be submitted without them."],
            ["Empty state", "The description is empty with the prompt as the helper text. The related-item selector shows *Choose what this is about* when the member has no eligible items, and explains that a dispute must be about something in their own account."],
            ["Error state", "Inline per field. A submit failure preserves everything, including uploaded files, and reports with a reference. An existing open case on the same item is reported before submit, not after, with a link to it."],
            ["Success state", "The case is created and the member lands on SCR-MOB-18 with the reference, the state, and the timescale: *we aim to reply within three working days*. A single confirmation names the reference. **The member is told what happens to the money meanwhile, which is that nothing changes until the case is decided.**"],
            ["Responsive behaviour", "One column at every width. The uploader is a 96 px drop target on mobile with a file-picker button as the accessible route, since a drag target alone is not usable on a phone. The description textarea is eight rows on mobile and grows to fill the remaining height."],
            ["Accessibility", "Every field has a bound label and the prompt is its described-by, so a screen reader user hears *Tell us what happened, in your own words* before the field. The file input is a real input with a label, not a styled div. Upload progress is announced politely per file. The submit error banner receives focus. The timescale is a labelled region reachable from the confirmation."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.17.3 Dispute case — SCR-MOB-18"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show one case to the people entitled to see it: its state, its history, its evidence, and the single next action, with the other party visible only as a party."],
            ["Target user", "A member who has opened the case and is waiting; a member who has been named in the case and is surprised; and the staff member working it, who uses a different console entirely (SCR-ADM-09). This screen is the member-facing half only."],
            ["Layout", "One column: a header with the reference, subject, state and opened date; a next-step region; a facts table; the message history as a chronological thread; the evidence list; and the reply region."],
            ["Components", "`StatusCard`, `Table`, `Thread` (messages), `FileUpload`, `FormField` (reply), `Button` (primary and secondary), `Callout` (NOTE, what we can share)."],
            ["Navigation", "Reached from SCR-MOB-16, from a dispute notification, and by deep link. A case the member is not a party to returns the tier-2 not-found screen, identically to one that does not exist."],
            ["Primary CTA", "**Conditional on the state and the viewer: *Reply*, and only when a reply is actually invited.** On a case awaiting staff review, the filled control is absent and the region instead states what is happening and when to expect a reply. A reply control that leads to *your message will be read when we reply* teaches people to stop writing."],
            ["Secondary CTA", "*Add evidence* (secondary outlined) while the case is open, and *Close the case* (secondary outlined) for the member who opened it, with a confirmation that closes it without a verdict being implied on anyone."],
            ["Content", "Header: reference, subject, the state in a sentence, and the opened date. Next step: what is awaited and of whom, with the timescale. Facts: the Ajo, the round, the related item and its amount. The thread: every message, who wrote it, when, and whether it is visible to the other party. **Every message is visible to both parties.** Evidence: filenames with sizes, uploaded by whom and when. A NOTE stating what cannot be shared: *we will not tell you what another member has told us, and we will not tell them what you have told us.*"],
            ["Form fields", "Reply, textarea, 1 to 2,000 characters, required to send. Add evidence, the same uploader as SCR-MOB-17, up to 5 more files. No category field, no severity field, no resolution field — this screen cannot decide anything."],
            ["Validation rules", "Reply length only. A reply of whitespace is rejected. **A member cannot delete or edit a message after sending it**, and the interface never offers the control, because a dispute record that can be rewritten is not a record."],
            ["Loading state", "Header and next step resolve first, then the thread, then the evidence, each in place. The reply region is inert until the case state is known, so a member never types into a form that turns out to be closed."],
            ["Empty state", "A case with no messages yet shows a single line, *no messages yet*, rather than an empty thread. A closed case shows the closing note and the full history, and the reply region is replaced by a statement naming when the case was closed and by whom."],
            ["Error state", "A failed send preserves the reply text and reports in place. **A send that succeeded but whose acknowledgement was lost shows the message in the thread, not as an unsent draft**, because duplicating a member's statement in a dispute is actively harmful."],
            ["Success state", "The reply appears in the thread, the case state advances, and the other party is notified. No modal, no toast over the thread."],
            ["Responsive behaviour", "One column at every width. The thread is a single column of bubbles at every width and never becomes a two-column conversation layout, which would imply a synchronous exchange this product does not have. The evidence list wraps filenames rather than truncating them."],
            ["Accessibility", "The thread is an ordered list of messages; each has a header naming the author as a party role — *you* or *the other party* — **never as a name in a member-facing view where the name would expose the other party unnecessarily, and never as a role that implies blame.** Message text is selectable. The next-step region is a labelled region with the `h2` *What happens next*. The reply region's `aria-describedby` points at the visibility note, so a member learns that what they write is shared before they write it."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =============================================================== 4.18
    {"t": "h2", "text": "4.18 Profile — SCR-MOB-19"},
    {
        "t": "p",
        "text": (
            "The profile is what other members see of a person, and it is the one place "
            "where this product has to hold two ideas at once: a member is entitled to "
            "know who else is in their Ajo, and is entitled to keep their phone number, "
            "their bank details and their documents to themselves. The profile is "
            "therefore split into a *what others see* section and a *only you can see* "
            "section, and the boundary between them is drawn explicitly rather than "
            "implied by which section a field happens to sit in."
        ),
    },

    {"t": "h3", "text": "4.18.1 Profile — SCR-MOB-19"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Let a member see and edit their own details, and show them exactly what another member will see of them."],
            ["Target user", "A member correcting a name before it appears on ten rosters, or checking what a group can see before joining a second Ajo with the same people."],
            ["Layout", "One column, two labelled regions. **What other members see**: avatar initials, first name, last initial, member since. **Only you can see**: email, phone, and the state of identity verification. Each region ends with its own edit control."],
            ["Components", "`Avatar`, `ListItem` (field), `Badge`, `Sheet` (edit), `Button` (secondary and primary), `Divider`, `Callout` (NOTE)."],
            ["Navigation", "Reached from the More menu and from the dashboard's greeting. Deep-linkable. `noindex`."],
            ["Primary CTA", "None on the view state. The view is content. Inside the edit sheet, the primary is *Save*."],
            ["Secondary CTA", "*Edit details* (secondary outlined) per region, and *Manage identity documents* (secondary outlined) in the private region."],
            ["Content", "The public region with the four fields and, beneath it, a line stating what a member in an Ajo can see: *members of the same Ajo can see your name, your position and your membership status. They cannot see your phone number, your email, your bank details or your documents.* The private region with email, phone and the verification state, and a line stating who can see these: *only you and, where we are legally required to, the authorities. We never show them to another member, including an organiser.*"],
            ["Form fields", "In the edit sheet only: first name, last name, both required, same rules as registration. Email and phone are edited in the security screen, not here, because changing either has a verification consequence that a profile edit should not carry silently."],
            ["Validation rules", "Name rules as on SCR-WEB-10. **A name change is applied immediately to all rosters** and the interface says so before the save, because a member who changes their name mid-Ajo should know their group will see it."],
            ["Loading state", "The private region resolves separately from the public one, so a failure to load an email does not hide a name. Each region has its own skeleton."],
            ["Empty state", "A member with no display name — impossible through the registration flow, but possible through a data import — sees *No name set* with the edit control, not a blank row."],
            ["Error state", "Per region. A failed name save reports inside the sheet and preserves the typed value."],
            ["Success state", "The region updates in place with a polite confirmation. No toast."],
            ["Responsive behaviour", "One column at every width. The two regions are stacked at every width and are never interleaved; a member reading the public region should not have the private one appearing between its fields."],
            ["Accessibility", "Each region is a labelled section with an `h2` whose text states the visibility rule, so the boundary is in the accessible outline and not only in the visual layout. Every field's accessible name includes its visibility, *Phone number, only you can see*. The avatar's initials are hidden from the accessibility tree because the name is already present as text."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "pagebreak"},

    # =============================================================== 4.19
    {"t": "h2", "text": "4.19 Settings — SCR-MOB-20"},
    {
        "t": "p",
        "text": (
            "Settings is a list of switches, and a list of switches is where products "
            "usually go wrong by burying consequential actions among cosmetic ones. The "
            "consequence here is a three-band structure: things that change how the "
            "product reaches you, things that change what data is held, and things that "
            "end the relationship."
        ),
    },

    {"t": "h3", "text": "4.19.1 Settings — SCR-MOB-20"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Let a member control notifications, choose their language, and reach the three irreversible actions: sign out everywhere, request data deletion, and close the account."],
            ["Target user", "A member who is being notified too often, or who wants the product in a language other than English, or who is leaving and wants to know what happens to their record."],
            ["Layout", "One column in three labelled bands with dividers. **Reach**: notification channels per event type, language. **Data**: download a copy, request deletion. **Account**: sign out everywhere, close the account. The destructive band is last, visually separated, and never adjacent to a switch."],
            ["Components", "`ListItem` (switch row), `Switch`, `Select`, `Divider`, `Button` (secondary and danger), `Sheet` (channel matrix), `Callout` (DANGER)."],
            ["Navigation", "Reached from the More menu. Deep-linkable to a single band. `noindex`."],
            ["Primary CTA", "None. Settings is a configuration surface, and every row acts on itself."],
            ["Secondary CTA", "*Save notification preferences* is not a control, because preferences save on change; instead each switch shows its saved state with a quiet saved indicator. Tertiary: *Read the privacy policy*."],
            ["Content", "Reach band: a summary row *Notifications*, opening a channel matrix — in-app, email, SMS — against the event types a member can actually be notified about, with the money events **pre-ticked and explained as such**, because a member must not be able to switch off the only channel that will tell them their round is due. Language: a select. Data band: *Download my data* and *Request deletion of my data*. Account band: *Sign out of all devices* and *Close my account*."],
            ["Form fields", "A language select, and the channel matrix as a grid of switches. Nothing else."],
            ["Validation rules", "Money-event channels cannot all be switched off: the interface permits the last one to be turned off only after an explicit confirmation explaining that the member may then miss a due date, and it records that the member was told. **The interface never silently re-enables a channel and never re-enables one on the next visit.**"],
            ["Loading state", "Switch rows render in their stored state immediately from the session; the matrix resolves in place. A switch never appears off when its stored value is on."],
            ["Empty state", "Not applicable. Every row has a value."],
            ["Error state", "A failed save of a preference leaves the switch in its attempted position with a quiet inline warning and a retry, rather than snapping back silently, because a switch that snaps back teaches a member the switch is broken."],
            ["Success state", "Each destructive action opens a confirmation stating exactly what will happen, what will be kept, and for how long, per the privacy policy. **Account closure is never a single tap and never a toggle.**"],
            ["Responsive behaviour", "One column at every width. Switch rows are 64 px with the label on the left and the switch on the right, and the label is not truncated at 320 px — it wraps to two lines, which keeps the control usable."],
            ["Accessibility", "Every switch is a real `role=\"switch\"` with a state, and its accessible name is the row label, not *toggle*. The channel matrix is a labelled table with row and column headers so a screen reader user can hear *SMS, round due, on*. The destructive band is a labelled region, so it can be reached and skipped deliberately."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =============================================================== 4.20
    {"t": "h2", "text": "4.20 Security — SCR-MOB-21"},
    {
        "t": "p",
        "text": (
            "Security is the screen that has to be usable by somebody who has just "
            "received a *your sign-in was blocked* message, on a phone that is not "
            "theirs, at a time when they are worried. It is therefore organised by task "
            "rather than by security concept, and the two genuinely dangerous actions — "
            "signing out everywhere and withdrawing all sessions — are separated from the "
            "everyday ones by a band and a confirmation."
        ),
    },

    {"t": "h3", "text": "4.20.1 Security — SCR-MOB-21"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Let a member change their password, change their phone number, review where they are signed in, and end sessions they do not recognise."],
            ["Target user", "A member who suspects something, or who has simply lost a phone. Both arrive at this screen in a hurry and both need the first thing on it to be the thing they came for."],
            ["Layout", "One column in two bands. **Your access**: password with a change control, phone with a change control. **Signed-in devices**: a list of sessions with device, place, last activity and a per-row *Sign out* control, plus the *Sign out everywhere* control at the foot."],
            ["Components", "`ListItem` (session), `Button` (secondary and danger), `FormField`, `Sheet` (change), `Callout` (WARNING), `Divider`."],
            ["Navigation", "Reached from the More menu and from a security-alert notification, which deep-links here. Deep-linkable. `noindex`."],
            ["Primary CTA", "None on the view state. The password change's primary is inside its sheet: *Change password*."],
            ["Secondary CTA", "*Change password* and *Change phone number* (secondary outlined), and *Sign out of this device* (secondary outlined) at the foot of the session list."],
            ["Content", "Your access: the last password change date, never the password itself. Phone: the masked number, with the note that a change requires verification on the new number. Devices: one row per active session with a human device name, the approximate place and the last activity, sorted newest first, **with the current session marked *This device* and not offered a sign-out control**, because signing yourself out of the device you are holding is a support ticket waiting to happen. A WARNING note stating that AJO.ng will never ask for a password, a PIN or a one-time code, and what to do instead."],
            ["Form fields", "In the change sheet: current password, new password, confirm new password. In the phone sheet: the new number, then a verification code sent to it. The current password is required even with an active session, because a stolen session must not be enough to take over an account."],
            ["Validation rules", "New password rules as on SCR-WEB-12, with the same allowance for passphrases. The current password must match before the new one is accepted, and a mismatch says *That is not your current password* without any indication of length or format. The verification code is 6 digits, single use, expiring in 10 minutes, with a resend cooldown of 60 seconds."],
            ["Loading state", "The device list resolves in place with row skeletons. A password change works with its width locked and the sheet stays editable until the response returns."],
            ["Empty state", "A single-session account shows one row and the *Sign out everywhere* control is still present but its confirmation states plainly that this is the only device, because hiding it would be a lie by omission and showing it as if it were meaningful would be theatre."],
            ["Error state", "A failed password change preserves the new password field and clears only the current-password field, since that is the field that was wrong. A failed phone change preserves the number and offers a resend."],
            ["Success state", "A password change signs out every other session and says so in the confirmation, because otherwise a member who just removed a suspicious session has no way to know it worked. A phone change re-sends the verification and the old number remains in place until the new one is verified."],
            ["Responsive behaviour", "One column at every width. Session rows stack label-above-value below 375 and never truncate the device name mid-word. Sheets are full-height on mobile with their own primary at the foot."],
            ["Accessibility", "Session rows are list items, not a table, at every width, and each row's accessible name is *Signed in on a Samsung, Android, Lagos, last active two hours ago*. The *This device* marker is text, not a highlight. The warning note is a labelled region. The change sheets trap focus and restore it to the control that opened them on close, including after a failure."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "pagebreak"},

    # =============================================================== 4.21
    {"t": "h2", "text": "4.21 Identity verification — SCR-MOB-22"},
    {
        "t": "p",
        "text": (
            "The rule here is narrow and non-negotiable: **identity verification is "
            "required for receiving a payout and is not required for creating an Ajo, "
            "joining one, or paying a contribution.** A product that gates participation "
            "on documents is a product that loses its members in the exact moment it "
            "starts to matter, and the screen has to be clear about which door this is "
            "before a member is asked for anything."
        ),
    },
    {
        "t": "callout",
        "kind": "DECISION",
        "title": "Verification gates exactly one action",
        "text": (
            "**An unverified member can create an Ajo, join an Ajo, and pay every "
            "contribution. An unverified member cannot receive a payout.** The screen "
            "states this in the first sentence, before any field, and states that a "
            "round's payout to an unverified member is **held and not skipped**: the "
            "Ajo's progress is not blocked, the money is not redistributed, and the "
            "member is told plainly that the hold exists and what ends it. Verification "
            "is also never presented as a condition of the product working — it is a "
            "condition of one specific action. **Owner: Founders.**"
        ),
    },
    {
        "t": "h3", "text": "4.21.1 Identity verification — SCR-MOB-22"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Complete identity verification when a member needs to receive a payout, and explain the consequence of not doing so without using it as leverage."],
            ["Target user", "A member whose turn has come and who is being asked, possibly for the first time, for a document they were not told about. They are entitled to know why, in one sentence, before anything else."],
            ["Layout", "One column: a state headline as the `h1`; a two-sentence statement of what verification is for and what it is not required for; a document selector; a capture or upload control; and a status region that shows the three states without a diagram."],
            ["Components", "`StatusCard`, `Select`, `FileUpload` (camera or gallery), `Button` (primary and secondary), `Callout` (NOTE, what we store), `Checklist`."],
            ["Navigation", "Reached from the More menu, from a payout that is held, and from an identity-check-needed notification, which deep-links here. Deep-linkable. `noindex`."],
            ["Primary CTA", "**Conditional and specific: *Verify my identity*.** It is one filled button, and it says what it verifies. With a document already submitted and under review, the filled control is absent and the status region takes its place."],
            ["Secondary CTA", "*Why do you need this?* (tertiary link), which opens a sheet with the full explanation, and *Read the privacy policy* (tertiary link) in the storage note."],
            ["Content", "The headline: *Verify your identity to receive payouts*. Then: *You need this once, before your first payout. It is not needed to create an Ajo, join one, or pay a contribution.* Then the document selector — a Nigerian identity document type, with the options enumerated rather than assumed. Then the capture control. Then the storage NOTE: *We check your document and keep only the result, a reference and the date. We do not keep a copy of the document.* **That sentence is a design commitment, not a disclaimer, and the upload control is not presented as a place where a document is retained.**"],
            ["Form fields", "Document type, select, required. Document image or PDF, required, front and back where the document has both, images only, up to 10 MB. No name, no date of birth, no address: those are read from the document by the verification provider, and asking for them as well would create two sources of truth for the same fact."],
            ["Validation rules", "A document type is required. An unreadable image is rejected immediately, before upload, with *We could not read that. Try again in better light, or upload a photo of the original.* A file over 10 MB or of the wrong type is rejected by name. A document that fails the provider's check returns a named reason and a fresh upload, never a rejection with no explanation."],
            ["Loading state", "The upload control shows per-file progress in place. The submit control works with its width locked while the provider responds, and the form stays editable. **A verification in progress is shown as such and never as a spinner over a blank region.**"],
            ["Empty state", "Not applicable. The three states are *not started*, *under review* and *verified*, and each is a complete rendering of the screen with its own controls."],
            ["Error state", "A provider timeout produces *We could not check that document. Try again* — never a rejection. A member who has uploaded twice and failed twice is offered the support route rather than a third silent attempt."],
            ["Success state", "The screen moves to *verified*, the held payout is released, and the member is told that in the same place, with the release named: *Your payout of NGN 10,000.00 has been released.* **The two events are shown together because they are, from the member's point of view, one event.**"],
            ["Responsive behaviour", "One column at every width. The capture control is a 128 px full-width target on mobile with a camera route and a gallery route as two distinct buttons, because a combined *Choose a photo* control on a phone is a tap that opens the wrong thing. Documents are previewed as images at 96 px, never as a filename alone."],
            ["Accessibility", "Every control has a bound label. The document type is a real select. The preview is an image with an alternative text of *Front of your document* — **not** an OCR of its contents, which would put a member's identity document contents into a screen reader's buffer for no benefit. The status region's changes are announced politely, and the verified state change is announced assertively because it releases money."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =============================================================== 4.22
    {"t": "h2", "text": "4.22 Support — SCR-MOB-23"},
    {
        "t": "p",
        "text": (
            "Support is where the product's promises are tested, because a member arrives "
            "here having already been let down by something. Two decisions shape the "
            "screen: a member may open a ticket from any surface in the product and have "
            "the context attached automatically, and the ticket list shows the state of "
            "the thing they asked about, not only the state of the conversation."
        ),
    },

    {"t": "h3", "text": "4.22.1 Support — SCR-MOB-23"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Let a member start a conversation with a person, with the context that matters already attached, and follow it to an answer."],
            ["Target user", "A member with a problem they could not resolve from the product, usually about money, usually anxious, and often using a phone they are not certain is safe. They need to know their message is not going into a void."],
            ["Layout", "Two states. **List state**: a header with the response expectation, then ticket rows of 88 px carrying the reference, subject, the related item, the state and the last activity. **New state**: a single card with a category selector, a message field, an attachment control and the context summary."],
            ["Components", "`ListItem` (ticket), `FormField`, `Select`, `FileUpload`, `Thread` (short), `Callout` (NOTE, response expectation), `Button` (primary and secondary)."],
            ["Navigation", "Reached from the More menu, from the *Ask for help* tertiary action on any money surface, and from a support-reply notification. Deep-linkable. `noindex`."],
            ["Primary CTA", "New state: *Send to support*. One filled button, 56 px. List state: *Start a new message* (secondary outlined, never filled, because the list is a history and a filled button on a history page invites accidental new tickets)."],
            ["Secondary CTA", "*Attach a screenshot* (secondary outlined) in the new state, and *View the item this is about* (tertiary link) in a ticket."],
            ["Content", "The response expectation, stated once at the top of both states: *we aim to reply within one working day, and we will tell you here either way*. New state: the category, the message with the prompt *Tell us what happened*, attachments, and **a context summary of whatever the member opened support from — the Ajo, the round, the amount, the last action — labelled as attached so the member can see it and remove it.** List state: each ticket with its state in a sentence and its last activity."],
            ["Form fields", "Category, select, required, pre-filled from the surface the member came from and still changeable. Message, textarea, required, 20 to 4,000 characters, live count from 3,500. Attachment, optional, up to 5 files. The context summary is a read-only list with per-item removal, not a field."],
            ["Validation rules", "Message length, as on the contact form. **A ticket opened from a money surface must carry the item's reference, and it does so from the context summary rather than from anything the member types**, so a support agent can find the record from a screenshot."],
            ["Loading state", "The send control works with its width locked and the form stays editable. The list resolves with row skeletons."],
            ["Empty state", "List state: *No messages yet. If something is not right, tell us — we would rather hear about it.*, with the new-message control. A member who has never needed support and opens the screen is welcome, not suspicious."],
            ["Error state", "A failed send preserves the message and the attachments and reports with a reference. **A send whose acknowledgement was lost is shown as sent, not as a draft**, for the same reason as in disputes: a duplicated support message about money is a real cost."],
            ["Success state", "The ticket is created and the member lands on it with the reference, the state and the expectation, plus a single confirmation. A ticket opened from a money surface names the item in the confirmation so the member can see it was attached."],
            ["Responsive behaviour", "One column at every width. The context summary is a stacked list below 375 and a two-column key-value list above, in the same order. The message textarea is eight rows on mobile and grows with the keyboard open."],
            ["Accessibility", "The context summary is a labelled region with the `h2` *Attached to this message*, and each removable item's control is named for the item, *Remove Market women round 3*, never a bare *Remove*. The response expectation is in the accessible outline. The thread is an ordered list. The send control's accessible name is *Send to support* and its description carries the expectation."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "pagebreak"},

    # =============================================================== 4.23
    {"t": "h2", "text": "4.23 Admin console — SCR-ADM-01 to SCR-ADM-13"},
    {
        "t": "p",
        "text": (
            "The console exists for two jobs: to see what is happening across the "
            "product, and to make the small number of decisions that cannot be "
            "delegated — a dispute, a freeze, a verification. Everything else about it "
            "is designed to be the opposite of the member application: denser, wider, "
            "and far more reluctant. **Three principles run through all thirteen "
            "screens, and each of them exists because the alternative is a permanent "
            "and unfixable record.**"
        ),
    },
    {
        "t": "table",
        "head": ["Screen", "Route", "Purpose in one line", "Who can write"],
        "rows": [
            ["SCR-ADM-01", "`/admin`", "What needs a person today.", "Nobody; links out only"],
            ["SCR-ADM-02", "`/admin/users`", "Find a member.", "Nobody"],
            ["SCR-ADM-03", "`/admin/users/:id`", "Read one member's whole record.", "**Read-only. Never.**"],
            ["SCR-ADM-04", "`/admin/ajos`", "Find an Ajo.", "Nobody"],
            ["SCR-ADM-05", "`/admin/ajos/:id`", "Read one Ajo's whole record.", "**Read-only. Never.**"],
            ["SCR-ADM-06", "`/admin/disputes`", "The dispute queue.", "Queue state only"],
            ["SCR-ADM-07", "`/admin/disputes/:id`", "Decide one case.", "`[S]`, `support`, `admin`"],
            ["SCR-ADM-08", "`/admin/risk`", "Freeze and release, with a reason.", "`[S]`, `risk`"],
            ["SCR-ADM-09", "`/admin/verification`", "Approve or reject a document check.", "`[S]`, `compliance`"],
            ["SCR-ADM-10", "`/admin/reports`", "Reconciliation figures.", "Nobody"],
            ["SCR-ADM-11", "`/admin/audit-logs`", "The append-only record of every privileged action.", "Nobody, ever"],
            ["SCR-ADM-12", "`/admin/settings`", "Product configuration.", "`admin` only, `super` for money"],
            ["SCR-ADM-13", "`/admin/*` denied", "Say no, and say why.", "Nobody"],
        ],
        "widths": [0.8, 1.2, 2.2, 2.3],
        "size": 7.0,
    },
    {
        "t": "table",
        "head": ["Principle", "What it forbids", "Why"],
        "rows": [
            ["Read-only means read-only", "No edit control on SCR-ADM-03 or SCR-ADM-05, not even for an `admin` role.", "A member's record must be correctable by the member and by nobody else, so that what the member sees is the truth. A console edit makes that unverifiable."],
            ["Every privileged action is reasoned", "No freeze, release, dispute decision or verification rejection without a recorded reason drawn from a list.", "A decision with no reason cannot be reviewed, appealed or audited, and the append-only log is only as good as what it records."],
            ["No edit, ever", "The ledger has no update path in the console. Corrections are reversing entries created in the member's own flow or by a documented process.", "The canonical product's ledger is append-only. A console that could edit a ledger entry would make the receipt and the ledger disagree, and both would be evidence."],
        ],
        "widths": [1.4, 2.4, 2.7],
        "size": 7.1,
    },

    {"t": "h3", "text": "4.23.1 Overview — SCR-ADM-01"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Answer one question: what needs a person today, and nothing else. It is a queue of work, not a dashboard of vanity."],
            ["Target user", "A support, risk or compliance officer starting their day, or an operator checking in at the end of one. They need to know whether anything is stuck, and to get to it in one click."],
            ["Layout", "Persistent left navigation at 240 px from `lg`, a top bar with the environment name, the operator's name and a sign-out control, and a single content column of five blocks, each with a heading, a count and a link."],
            ["Components", "`Shell` (admin), `Table` (counts), `Card` (queue block), `Badge`, `Button` (secondary), `AlertBar`."],
            ["Navigation", "The console root. Reached by sign-in and by the top bar. Every console route is `noindex` and never linked from the member application."],
            ["Primary CTA", "None. The screen's purpose is triage, and every block is a link to a queue. A filled button on an overview would imply an action that is not the right action for most visits."],
            ["Secondary CTA", "*Open the oldest item* (secondary outlined) in the three queues that have work, which is the single most common reason to open this screen."],
            ["Content", "Five blocks: disputes awaiting a decision, verifications awaiting review, accounts frozen, Ajos whose enrolment window closes in under 24 hours, and payment attempts whose result is unknown. **Each block shows a count and the age of the oldest item, never a percentage or a trend line.** A banner at the top when the unknown-payment count is above zero, because that is the block where delay costs a member money."],
            ["Form fields", "None."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Counts resolve independently per block with the heading always rendered, so the screen's shape is stable and no block is a blank rectangle."],
            ["Empty state", "A block with no work shows *Nothing waiting* rather than being removed, because a queue that disappears cannot be distinguished from a queue that failed to load."],
            ["Error state", "Per block. A failed block reports inline and does not blank the other four."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "The console is tier 3 and per 4.3.5 is not designed below 1024 CSS pixels. Left navigation collapses to a top bar with a menu sheet between 1024 and 1280, and the content column never exceeds 1200 px so a wide monitor does not stretch a table beyond the point where a row can be read as one line."],
            ["Accessibility", "The left navigation is a `nav` with a label and a `ul`; the current item is `aria-current` and is marked by weight and a marker, not colour alone. Each block's count is text. The table of counts has a caption and row and column headers. Skip link to the content column is present in the shell."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.23.2 Users — SCR-ADM-02"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Find one member among the population, and get to their record. Searching is the entire job, so the search is the entire first screenful."],
            ["Target user", "An operator with a reference, a phone number or a name from a support conversation. They want one record, fast, and they are usually on a second monitor with a ticket open."],
            ["Layout", "A search field at the top, 320 px, always focused on arrival, with the results table beneath it filling the remaining height and scrolling internally."],
            ["Components", "`SearchField`, `Table` (results), `Pagination`, `EmptyState`, `Button` (secondary)."],
            ["Navigation", "Left navigation. Reached by search from the top bar on any console screen, and from the overview's account links."],
            ["Primary CTA", "None. Selecting a row is the action, and a row is a link."],
            ["Secondary CTA", "*Clear search* (secondary outlined) when a query is present, and *Copy the search link* (tertiary) so an operator can hand a filtered view to a colleague."],
            ["Content", "Results as a table: reference, name, phone masked, email masked, state, joined date, last activity. **Phone and email are masked by default in the list and never unmasked by a click**; the full value lives on SCR-ADM-03, behind a recorded reveal, because a list of a thousand unmasked phone numbers on a shared screen is a data incident waiting for a screenshot."],
            ["Form fields", "Search: reference, phone number, email, or name. One field, not four, with a single query matched across all of them and a label stating so."],
            ["Validation rules", "A query shorter than 3 characters returns a prompt rather than a result set of everything, which is both a performance and a privacy control. A phone query accepts spaces and dashes and normalises before matching."],
            ["Loading state", "The results table shows a skeleton in place. **The search field never loses focus and never loses its query during a search**, so an operator can keep typing."],
            ["Empty state", "*No members match that.*, with the query echoed and a hint that the reference format is seven characters, because a mistyped reference is the most common cause."],
            ["Error state", "A failed search reports in place with a retry and the query preserved. A failed result page keeps the first page of results rather than emptying the screen."],
            ["Success state", "Not applicable."],
            ["Responsive behaviour", "Console only, per 4.3.5. The table scrolls horizontally below 1280 with the reference and name columns frozen, because an operator scrolling a wide table needs to know which row they are on."],
            ["Accessibility", "The results table has a caption stating the query and the count, and row headers. Each row is a single link in the reference cell, and the row's accessible name includes the reference and name so a links list is navigable. The masked values are read as *phone ending 4821*, not as a run of asterisks."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },

    {"t": "h3", "text": "4.23.3 User detail — SCR-ADM-03"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Show one member's complete record to an operator, read-only, so that an operator never has to guess, and never has to change anything to resolve a question."],
            ["Target user", "An operator answering a support question or assessing a risk signal. They are looking for what happened, when, in what order, and who else was involved."],
            ["Layout", "Two columns at 1440 and above — identity and status on the left, membership and money on the right — collapsing to one at 1024. Below the fold, three tabbed regions: memberships, transactions, and the audit trail of privileged actions touching this member."],
            ["Components", "`Table` (facts), `Tabs`, `ListItem`, `Disclosure` (reveal), `Button` (secondary), `Callout` (WARNING, restricted), `MoneyText`."],
            ["Navigation", "Reached from SCR-ADM-02, from a dispute, from the risk queue, and from any record link. Deep-linkable within the console."],
            ["Primary CTA", "None. **There is no write path on this screen for any role, including `admin` and `super`.** The only controls are reveals, tabs and links to the queues that can act."],
            ["Secondary CTA", "*Reveal phone number* and *Reveal email* (secondary outlined, each a recorded disclosure). *Freeze account* (secondary outlined) — a link to SCR-ADM-08, never inline. *Export this record* (secondary outlined), producing a timestamped file. Tertiary: *Open in the risk queue*."],
            ["Content", "Identity: name, reference, created date, state and the reason for any state, last sign-in, verification state. Contact: masked, with per-item reveal. Memberships: every Ajo with position, state and the member's standing in each. Money: balances owed, payouts received, transactions, all reconciled to the ledger. A WARNING region for a restricted account, naming the reason and the reviewer. **Anything that would let an operator *correct* a member's data is absent by design, and its absence is documented here so a later feature request has to argue with this paragraph.**"],
            ["Form fields", "None. The two reveals are confirmations, not fields: a dialog stating that the value will be recorded in the audit log against the operator's name."],
            ["Validation rules", "Not applicable."],
            ["Loading state", "Per-region skeletons, with the identity block resolving first because it is what an operator came for."],
            ["Empty state", "An account with no memberships shows the state plainly. **An account with no transactions is either brand new or suspicious, and the screen says which by showing the joined date** rather than rendering an empty table that reads the same in both cases."],
            ["Error state", "Per region, contained. A failed reveal reports against the control and does not clear the masked value, so the operator can see what they were trying to see."],
            ["Success state", "A reveal confirms in place and the audit entry is written. Nothing on this screen reports success otherwise."],
            ["Responsive behaviour", "Console only. The tabbed regions become stacked labelled sections below 1280, with the tabs removed rather than collapsed, so every region is reachable by scrolling."],
            ["Accessibility", "The facts are a real table with a caption. Tabs are a proper tablist with `aria-selected` and arrow-key navigation. The reveal dialogs are modal, trap focus, and their titles name what is being revealed. Every disclosure is announced to the operator, and the audit trail region is labelled *Privileged actions on this record*."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.23.4 Ajos and Ajo detail — SCR-ADM-04, SCR-ADM-05"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "Find an Ajo among the population and read one Ajo's whole record, read-only, with the money reconciled to the ledger and the roster complete."],
            ["Target user", "An operator investigating an Ajo rather than a person: a support question about a group, a risk signal across a roster, or a reconciliation at month end."],
            ["Layout", "SCR-ADM-04: a filter bar above a results table filling the remaining height. SCR-ADM-05: a header with the Ajo's name, state and reference; a facts row; a two-column body — economics and roster on one side, activity on the other; and a tabbed region for the full ledger."],
            ["Components", "`FilterBar`, `Table`, `Table` (facts), `MoneyTable` (canonical), `ListItem`, `Tabs`, `Button` (secondary), `Callout` (WARNING)."],
            ["Navigation", "Reached from the console navigation, from SCR-ADM-01's Ajo block, and from any user record's membership entry. Deep-linkable within the console."],
            ["Primary CTA", "Neither screen has a primary action. SCR-ADM-05 is read-only like SCR-ADM-03, and the write actions that exist for Ajos — a cancellation, a position correction — are process actions taken by the product's own rules and are surfaced as state with their cause, not as buttons an operator presses."],
            ["Secondary CTA", "SCR-ADM-04: *Clear filters* and *Export the filtered set*. SCR-ADM-05: *Export the ledger* (secondary outlined) and *Copy the Ajo reference* (tertiary)."],
            ["Content", "SCR-ADM-04 columns: reference, name, state, members filled of total, rounds, amount per member, created date, last activity. **SCR-ADM-05 economics** is the canonical money table, complete and unaltered, so an operator reconciling a figure reads exactly what a member reads. The roster shows every member, position, standing and contribution state, **including unpaid members, because this is the one view in the product where naming them is the operator's job and is necessary to the work.** The activity region shows every state change in order, and the ledger tab shows every entry with its correcting entry. A WARNING region when a round is short, stating the shortfall and that no recovery case is open."],
            ["Form fields", "None on either screen. SCR-ADM-04's filter bar is a set of controls, not fields: state, a date range, filled-or-not, and a text search."],
            ["Validation rules", "A date range with a start after its end is rejected inline on the control that caused it, naming which bound. Filters compose; the applied set is stated in the results caption."],
            ["Loading state", "Table skeletons on the list; region skeletons on the detail, economics first."],
            ["Empty state", "SCR-ADM-04: *No Ajos match these filters*, with the filters echoed and a *Clear filters* control. SCR-ADM-05: a DRAFT Ajo legitimately has no rounds and says *No rounds yet — this Ajo has not been activated*, which is a different sentence from an empty table."],
            ["Error state", "Per region, contained. A failed ledger export reports against the control and leaves the table intact."],
            ["Success state", "An export reports in place with a link and a note that the file is timestamped and watermarked to the requesting operator."],
            ["Responsive behaviour", "Console only. SCR-ADM-05's two-column body becomes one at 1280, economics first. Tables scroll horizontally with frozen identifier columns below 1280."],
            ["Accessibility", "Both tables have captions and row and column headers. The roster is a real table with the position as a row header, and the unpaid state is text plus a marker, never colour alone. The ledger tab is a proper tablist. The WARNING region is labelled and in the outline, so an operator can navigate to the shortfall directly."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
    {"t": "h3", "text": "4.23.5 Disputes and the dispute workspace — SCR-ADM-06, SCR-ADM-07"},
    {
        "t": "table",
        "head": ["Aspect", "Specification"],
        "rows": [
            ["Purpose", "SCR-ADM-06: get a case to the right person, oldest first, with the waiting time visible. SCR-ADM-07: let an authorised operator reach a decision on one case with the whole record in front of them, and record why."],
            ["Target user", "A support or dispute officer, working a queue, who must be able to reach a defensible decision in minutes and whose decisions will be reviewed later by somebody else."],
            ["Layout", "SCR-ADM-06: a queue table filling the height, sorted by age descending, with the wait in days as a column. SCR-ADM-07: a three-column body at 1440 — the case record and thread on the left, the related money record in the middle, the decision region on the right — collapsing to one column at 1024 with the decision region last."],
            ["Components", "`Table` (queue), `Thread`, `Table` (related record), `DecisionPanel`, `ReasonSelect`, `TextArea` (note to parties), `Button` (primary and secondary and danger), `Callout` (WARNING)."],
            ["Navigation", "SCR-ADM-06 is the console's dispute destination and the target of SCR-ADM-01's first block. SCR-ADM-07 is reached by row selection and by direct link from a notification."],
            ["Primary CTA", "SCR-ADM-07 only, and it is the decision: *Record the decision*. **It is enabled only once a reason has been chosen and a note has been written**, and the button's label always names the decision — *Resolve in the member's favour*, *Resolve against the member*, *Request more information* — so no decision is ever recorded as *Submit*."],
            ["Secondary CTA", "*Request more information* (secondary outlined) where that is a possible outcome, *Add an internal note* (secondary outlined, never visible to a party), and *Escalate* (tertiary, with a recorded reason)."],
            ["Content", "SCR-ADM-07 shows, in one view: the case as the member wrote it, every message from both parties with author roles, the related obligation or payout with its full money record, the member's history in this Ajo, the Ajo's state, and the prior cases between the same parties. A WARNING region states the decision's effect on the money explicitly, in words and figures, **before** the decision control: *This resolves the case and refunds NGN 1,020.00 to the member, taken from the round. The round will then be NGN 200.00 short and the recipient will be paid NGN 9,800.00 unless another member's contribution is recovered.* A decision that changes a payout says so in the same sentence."],
            ["Form fields", "Reason, a select of the allowed reasons per decision type, required and closed-ended. Note to parties, a textarea, 20 to 2,000 characters, required, and **every word of it is read by the parties, which the label says**. Internal note, a textarea, optional, never rendered in the member application under any circumstance."],
            ["Validation rules", "A decision cannot be recorded without a reason from the list, because free-text reasons cannot be counted or reviewed. **A reason cannot be edited after the decision is recorded**, and the interface never offers the control. A member-supplied payment is rejected; an operator cannot resolve a case by entering a figure."],
            ["Loading state", "The queue table and the workspace's three regions resolve independently, and the decision region is inert until the case and the related record have both loaded, because a decision taken against a half-loaded record is unreviewable."],
            ["Empty state", "SCR-ADM-06: *No open cases*, which is the desired state of a queue and is shown as such. SCR-ADM-07: a case with no messages yet shows that fact; a case with no related record — which happens when the item was deleted by a documented retention process — states that explicitly rather than showing a blank panel."],
            ["Error state", "A failed decision reports against the decision control, preserves the reason and the note, and **does not fall back to recording a partial decision**, because a dispute recorded without its reason is the one artefact in this product that cannot be reconstructed afterwards."],
            ["Success state", "The case moves to a decided state, the parties are notified with the note, the ledger effect is applied, and the operator is returned to the queue with the case no longer in it."],
            ["Responsive behaviour", "Console only. At 1024 the three columns stack in the order record, money, decision, so the decision is never the first thing seen without its context. Textareas and selects are never narrower than 320 px."],
            ["Accessibility", "The queue table has a caption with the sort and the count, and a row header of the reference. The thread is an ordered list with author roles as headers, and internal notes are marked as such in text for the operator, not by styling. The decision region's `aria-describedby` points at the money-effect warning, so the consequence is read before the control. The reason select is a real labelled select and its options state their effect."],
        ],
        "widths": [1.06, 5.44],
        "size": 7.3,
    },
]
