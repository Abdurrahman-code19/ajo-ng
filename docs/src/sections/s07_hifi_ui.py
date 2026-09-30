"""
Section 7 — High-Fidelity UI Specification.

Source of truth: docs/src/CANONICAL.md
Authoring contract: docs/src/AUTHORING.md
Structure source: section 6 (wireframes) — every component here belongs to a
numbered region of a numbered screen.

This section turns the wireframes into a visual system. It fixes colour, type,
space, motion and component behaviour. It does not add screens, and it does not
add regions: a component that cannot be traced to a region table in section 6 is
not built, and a screen that is not in section 6 does not get a visual treatment
here.

The two things that are fixed across every screen, and that this section
reproduces rather than restates, are the 2% fee disclosure and the base-pool
label. They are specified once, in 7.12, and the component there is mandatory
wherever an amount is shown. The tagline is "Your Ajo. Your Story."
"""

BLOCKS = [
    {"t": "h1", "text": '7. High-Fidelity UI Specification'},

    {
        "t": "lead",
        "text": 'The visual system for AJO.ng: the tokens, the components, the states, and the rules that decide between them. It is written for two audiences at once, a designer producing the interface and an engineer implementing it, and it assumes both can read a table. Where a decision has a trade-off it is stated with the alternative that was rejected, because a rule with no stated alternative is a rule that gets re-litigated by the next person who disagrees with it.',
    },

    {"t": "h2", "text": '7.1 Purpose, scope, and how to read this section'},

    {
        "t": "p",
        "text": 'This section exists to make the interface legible to people who do not already trust it. That is the design problem, stated plainly: AJO.ng asks for a bank account, an identity document, and a standing commitment to pay a fixed amount on a fixed day, from people who are used to being asked for none of it. Every visual decision below is judged against that, and a rule that is merely tidy is not enough reason to keep it.',
    },

    {"t": "h3", "text": '7.1.1 What this section specifies'},

    {
        "t": "bullets",
        "items": [
            '**Tokens** — colour, type, space, radius, elevation, motion duration — as named values with one definition each, in 7.3 to 7.5 and 7.13.',
            '**Components** — the reusable pieces a section 6 region is built from, with their states and their behaviour, in 7.7, 7.8, 7.11, 7.12 and 7.15.',
            '**Screen-level composition** — one screen specified in full, the dashboard, in 7.9, because it is the screen every member sees first and the one whose hierarchy decides whether the product feels like a bank or like a list.',
            '**Data visualisation** — the chart forms that are permitted, the ones that are not, and the accessibility rules they carry, in 7.10.',
            '**Motion** — durations, easing, and the reduced-motion contract, in 7.13.',
            '**Accessibility** — the WCAG 2.2 AA target and the specific ways this product fails people without it, in 7.14.',
            '**Dark mode** — an explicit MVP and deferred decision, in 7.16.',
        ],
    },

    {"t": "h3", "text": '7.1.2 What this section does not specify'},

    {
        "t": "bullets",
        "items": [
            '**Screens or regions.** Section 6 owns that. A design that needs a region the wireframe does not have changes section 6 first.',
            '**Marketing copy beyond the fee and the tagline.** Copy is a product decision, not a design system decision, and the only copy fixed here is copy that is regulated by the fee model.',
            '**Illustration and photography direction.** 7.6 covers the rules that constrain them; the direction itself belongs to whoever owns the brand.',
            '**Offline behaviour.** The product is online-only at v1. If that changes, 7.11 changes with it.',
            '**Native app surfaces.** v1 is web and responsive. Where a native app follows, the component definitions apply and the navigation does not.',
        ],
    },

    {"t": "h3", "text": '7.1.3 How to read a component'},

    {
        "t": "p",
        "text": 'Each component is given a name that matches the code, a purpose line, a states table, and behaviour notes. Where a component has a rule that is easy to break under deadline — a money component, a destructive action, a state carried only by colour — that rule is called out and marked as non-negotiable, and the reason is stated so it can be argued with rather than merely obeyed.',
    },

    {"t": "h2", "text": '7.2 Design principles'},

    {
        "t": "p",
        "text": 'Five principles, in priority order. When two of them disagree, the earlier one wins, and the disagreement is resolved in that order rather than by whoever is closest to the decision.',
    },

    {
        "t": "table",
        "head": ['#', 'Principle', 'What it means here', 'What it rules out'],
        "rows": [
            ['1', '**The number is never ambiguous**', 'Every amount names what it is, what it includes, and where it goes. Contribution, fee, and total are three lines or the component is wrong.', 'A single NGN 1,020.00 with no breakdown. A total with no noun. A progress bar with no count. A chart with no axis label.'],
            ['2', '**No state is carried by colour alone**', 'Every state has a word, a shape, or a position as well as a colour. Overdue is the word *overdue*, not a red cell.', 'Red means late. Green means paid. A green dot for a verified badge. A coloured chart series with no direct label.'],
            ['3', '**The interface is quieter than the anxiety**', 'A person checking whether their money arrived is anxious. The interface does not amplify that with motion, confetti, urgency counts, or marketing voice.', "Celebration on a routine payment. A countdown timer on a due date. *Don't miss out* anywhere in the product."],
            ['4', '**Say the hard thing in the same place as the easy thing**', 'Limits, lock-in, holds, and fees appear next to the action they constrain, not in a policy page.', 'A terms link as the only disclosure. A lock warning only at the final step. A hold explained in support.'],
            ['5', '**The default is the safe one**', 'Confirmations default to the outcome that loses nothing. Destructive and irreversible controls are not the default, are not adjacent to the safe one, and are not a tap target on mobile.', "A swipe-to-confirm that also swipes back to cancel. A primary action pre-selected. An expiry that defaults to the person's advantage."],
        ],
        "widths": [0.42, 1.0, 2.79, 2.29],
        "size": 7.4,
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Principle 1 is the one that will be tested under deadline',
        "text": 'Everything else in this section can be traded. The fee disclosure cannot, because CANONICAL.md requires the fee to be shown separately from the contribution on every receipt, in every Ajo details screen, and in the invitation and join confirmation before the member commits. A redesign that improves the visual system and merges those lines has made the product worse no matter how it looks, and the merge is invisible in a screenshot review because the numbers still add up. The component in 7.12 exists so that the rule is a component rather than a habit.',
    },

    {"t": "h2", "text": '7.3 Colour system'},

    {"t": "h3", "text": '7.3.1 The fixed brand palette'},

    {
        "t": "p",
        "text": 'CANONICAL.md fixes seven colours. They are not a theme, they are the brand, and they are used in the roles given below. A colour outside this list is a new token and requires the same review as a new component.',
    },

    {
        "t": "table",
        "head": ['Token', 'Hex', 'Role', 'Where it is used', 'Where it is never used'],
        "rows": [
            ['Deep', '#0B1F3A', 'Primary brand surface', "Hero and section backgrounds on marketing pages, the app's dark chrome, H1 on light", 'Body text on White at body size, which fails contrast'],
            ['Primary', '#146EF5', 'Primary action and link', 'Primary buttons, links, active nav item, H2 on light, focus ring base', 'Body text on White, which is 4.6:1 and only just passes'],
            ['Cyan', '#22C7D6', 'Secondary accent and data series one', 'Progress fills, the second chart series, information banners', 'Text on White, which fails badly. Never. No size, no weight.'],
            ['Gold', '#FBBF24', 'Accent, warning, payout emphasis', 'Payout-imminent emphasis, warning callouts, the Gold series in charts', 'As a text colour on White, which fails. Always on a dark or tinted surface.'],
            ['White', '#FFFFFF', 'Surface', 'Card and sheet surfaces, the marketing page background above the fold', 'As a disabled-state background on White, which is invisible'],
            ['Cloud', '#F4F7FB', 'Page background', 'Page background behind cards, zebra table rows', 'As a text colour, and as a border colour at full strength'],
            ['Dark', '#101828', 'Body text', 'All body copy, table cells, labels', 'As a background behind Gold text, which is not a combination this product uses'],
        ],
        "widths": [0.42, 0.42, 1.11, 2.15, 2.4],
        "size": 7.2,
    },

    {"t": "h3", "text": '7.3.2 Semantic colours, added on top'},

    {
        "t": "p",
        "text": 'Four semantic roles are needed and the fixed palette does not contain them: success, warning, danger, and information. They are defined once here, derived to stay inside the brand, and every other team uses these four rather than inventing a red.',
    },

    {
        "t": "table",
        "head": ['Role', 'Light fill', 'Light border', 'Text on fill', 'Contrast', 'Never used for'],
        "rows": [
            ['success', '#ECFDF3', '#ABEFC6', '#05603A', '7.1:1', 'A paid amount. Money states use the brand, not green.'],
            ['warning', '#FFFAEB', '#FEDF89', '#93370D', '7.4:1', 'A generic notice. Only for something that needs attention before it becomes a problem.'],
            ['danger', '#FEF3F2', '#FECDCA', '#B42318', '6.2:1', 'A declined payment, a failed payout, a frozen account, a destructive confirmation.'],
            ['information', '#EFF8FF', '#B2DDFF', '#175CD3', '6.1:1', 'Anything that is merely helpful. If it does not change what the person should do, it is not a banner.'],
        ],
        "widths": [0.46, 0.42, 0.51, 0.51, 0.42, 4.18],
        "size": 7.4,
    },

    {"t": "h3", "text": '7.3.3 Money and state colour'},

    {
        "t": "p",
        "text": "A specific and deliberate decision: **money and payment states are not coloured semantically.** A paid contribution is not green and an overdue one is not red, because the same words appear in the roster, the schedule, the statement and the receipt, and colouring them there would make one screen's green another screen's warning. Money is always Dark, and state is always a word.",
    },

    {
        "t": "code",
        "text": """
PAID       Dark on Cloud        #101828 on #F4F7FB
DUE        Dark on White        #101828 on #FFFFFF, with a Gold left rule
OVERDUE    Dark on danger fill  #101828 on #FEF3F2, with the word overdue
HELD       Dark on warning fill #101828 on #FFFAEB, with the word held
DEFAULTED  Dark on danger fill  #101828 on #FEF3F2, with the word defaulted

Gold is used only where a payout is imminent or a decision needs attention
before it becomes a problem. It is never the fill of a row.
""",
    },

    {
        "t": "callout",
        "kind": 'WARNING',
        "title": 'Cyan is not a text colour',
        "text": 'Cyan #22C7D6 on White is roughly 2.0:1 and fails every text threshold at every size and weight. It appears in this system as a chart series, a progress fill and a banner background, and in each of those it is adjacent to a Dark or White glyph rather than carrying text itself. **The most common misuse is a Cyan link on a White page**, and it is worth stating as a prohibition because Cyan reads as a link colour and will be used as one by someone who has not read this section. Links are Primary #146EF5.',
    },

    {"t": "h2", "text": '7.4 Typography'},

    {"t": "h3", "text": '7.4.1 Typeface and fallbacks'},

    {
        "t": "p",
        "text": "One variable sans for the interface, chosen for legibility at small sizes on mid-range Android hardware rather than for character, because the least conspicuous screen in this product is a roster on a 375 px phone in daylight. **The choice of family is an ASSUMPTION pending the founders' confirmation**, and the tokens below are named rather than bound to a family so the scale survives a change of family.",
    },

    {
        "t": "kv",
        "pairs": [
            ('Sans stack', "`'Inter var', 'Inter', -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`"),
            ('Numeric stack', "`'Inter var'` with `font-variant-numeric: tabular-nums` on every amount, count, date and reference"),
            ('Monospace', "Only inside `code` regions: `ui-monospace, 'SF Mono', Menlo, Consolas, monospace`"),
        ],
    },

    {
        "t": "p",
        "text": '**Every amount, count, date, and reference is tabular.** This is not a polish decision. A schedule table whose naira column changes width as the digits change is unreadable as a column, and a receipt whose total does not align with the line above it is a receipt people photograph and ask about.',
    },

    {"t": "h3", "text": '7.4.2 The scale'},

    {
        "t": "table",
        "head": ['Token', 'Size / line', 'Weight', 'Use', 'Max measure'],
        "rows": [
            ['display', '44 / 48', '700', 'Marketing H1 only. Not used in the app.', '16ch'],
            ['h1', '32 / 38', '700', 'Section title, page title on desktop', '24ch'],
            ['h2', '24 / 30', '600', 'Screen title, card title', '32ch'],
            ['h3', '19 / 26', '600', 'Sub-section, list group heading', '44ch'],
            ['body', '16 / 24', '400', 'All body copy, all table cells', '68ch'],
            ['body-strong', '16 / 24', '600', 'Emphasis inside body copy, labels that must be found', '68ch'],
            ['label', '14 / 20', '500', 'Field labels, table headers, button labels', '—'],
            ['caption', '13 / 18', '400', 'Supporting text, helper text, references', '—'],
            ['micro', '12 / 16', '500', 'State words, timestamps, event names', '—'],
            ['money', '24 / 30', '600', 'The single amount on a money surface', '—'],
            ['money-lg', '34 / 40', '700', 'Receipt total, payout amount. One per screen.', '—'],
        ],
        "widths": [0.79, 0.79, 0.43, 3.7, 0.79],
        "size": 7.2,
    },

    {"t": "h3", "text": '7.4.3 Measure and the money column'},

    {
        "t": "p",
        "text": "Body copy is capped at 68 characters. Money blocks are capped at 40 characters, which is wide enough for `NGN 1,020.00` and `NGN 102,000.00` with a rule above it and narrow enough that the digits sit close enough to compare. This is the second reason a money block is never centred: a centred block at full container width puts the contribution and the fee four hundred pixels apart, and the person's eye has to travel to check the arithmetic.",
    },

    {
        "t": "callout",
        "kind": 'DECISION',
        "title": 'One variable sans, no second display face',
        "text": 'A marketing site in this category almost always pairs a display serif with a sans. It was rejected for two reasons. The first is that a rotating savings scheme run by a group of friends is a trust product, and trust products look more trustworthy in the typeface their users already read every day. The second is cost: two families means two loading strategies, two sets of metrics, and a second decision to revisit. **A single family also makes the fee disclosure harder to miss**, because there is no typographic contrast to hide it in. If the founders later choose a display face for the marketing pages only, it must not appear on any screen where an amount is shown.',
    },

    {"t": "h2", "text": '7.5 Space, grid, breakpoints, radius, elevation'},

    {"t": "h3", "text": '7.5.1 The spacing scale'},

    {
        "t": "p",
        "text": 'A 4 px base with named steps. Every margin, padding and gap in the product is one of these values. The scale is short on purpose: a long scale is a long list of decisions that all look reasonable and none of which anybody remembers.',
    },

    {
        "t": "table",
        "head": ['Token', 'Value', 'Typical use'],
        "rows": [
            ['space-1', '4 px', 'Icon to label, badge inset, table cell vertical padding'],
            ['space-2', '8 px', 'Between a label and its value, chip gaps, inline icon pairs'],
            ['space-3', '12 px', 'Between related form fields, list row padding'],
            ['space-4', '16 px', 'Card padding on mobile, page gutter on mobile, region gaps'],
            ['space-5', '24 px', 'Card padding on desktop, gutter on tablet, between blocks'],
            ['space-6', '32 px', 'Between major regions on mobile'],
            ['space-7', '48 px', 'Between major regions on tablet and desktop'],
            ['space-8', '64 px', 'Marketing section padding, console page padding'],
        ],
        "widths": [0.64, 0.46, 5.4],
        "size": 7.4,
    },

    {"t": "h3", "text": '7.5.2 Breakpoints and grid'},

    {
        "t": "table",
        "head": ['Name', 'Range', 'Columns', 'Gutter', 'Page margin', 'Notes'],
        "rows": [
            ['xs', '320 to 374', '1', '—', '16 px', 'Smallest supported. Verified at 320 px because a 375 px design breaks here.'],
            ['sm', '375 to 767', '1', '—', '16 px', 'The design width. Bottom navigation applies.'],
            ['md', '768 to 1023', '2', '24 px', '24 px', 'Bottom navigation becomes a top bar. Console becomes usable.'],
            ['lg', '1024 to 1279', '8', '24 px', '32 px', 'Reading column caps at 720 px. The right context panel is not yet available.'],
            ['xl', '1280 to 1439', '12', '24 px', '40 px', 'Right context panel appears. Summary tiles go three across.'],
            ['2xl', '1440 and up', '12', '24 px', '48 px', 'The console design width. Content is capped, never stretched.'],
        ],
        "widths": [0.42, 0.67, 0.42, 0.42, 0.62, 3.95],
        "size": 7.2,
    },

    {
        "t": "p",
        "text": "Content is **capped and left-aligned, never centred and never full-bleed** below 1280 px, with two exceptions: the marketing hero, which is full-bleed, and the console's data tables, which use the full grid because a table with unused columns to its right is a table with too few columns.",
    },

    {"t": "h3", "text": '7.5.3 Radius and elevation'},

    {
        "t": "table",
        "head": ['Token', 'Radius', 'Used by'],
        "rows": [
            ['radius-sm', '4 px', 'Badges, chips, small inline elements, the state pill'],
            ['radius-md', '8 px', 'Inputs, selects, small buttons, list rows'],
            ['radius-lg', '12 px', 'Cards, the money block, sheets'],
            ['radius-pill', '999 px', 'Only the segmented control and the state pill. Not buttons, not cards.'],
        ],
        "widths": [0.82, 0.45, 5.23],
        "size": 7.4,
    },

    {
        "t": "p",
        "text": 'Elevation is one level, plus a scrim. There is no shadow scale in v1, because the only time two surfaces overlap in this product is a sheet over a page, and a single shadow plus a 40 percent Deep scrim is enough. A card on a Cloud page is separated by a 1 px `#E4EAF2` border and a very faint shadow, not by a floating one, because a field of floating cards is a dashboard cliché and this is a savings product.',
    },

    {"t": "h2", "text": '7.6 Iconography and imagery'},

    {"t": "h3", "text": '7.6.1 Icons'},

    {
        "t": "p",
        "text": 'A 24 px grid, 1.75 px stroke, round caps and joins, drawn in the same family as the interface so the weights match. Icons are never the only carrier of meaning: an icon-only control requires an accessible name, a tooltip, and a visible label on the surface it appears on. Three icons are prohibited outright.',
    },

    {
        "t": "bullets",
        "items": [
            '**No icon that implies a state.** A green tick for *paid* is prohibited, because the same tick is used for *verified*, *settled* and *complete* elsewhere and the reader has to learn four meanings for one shape. State is a word.',
            '**No icon-only destructive control.** A trash can with no label is prohibited on any touch viewport, on the grounds that a member should not be able to destroy a record by mis-tapping something they thought was a filter.',
            '**No money icon.** No naira glyph, no coin, no banknote, no wallet next to an amount. An amount is text, always, and the icon adds a claim about what the money is that the copy has to work harder to support.',
        ],
    },

    {"t": "h3", "text": '7.6.2 Imagery'},

    {
        "t": "p",
        "text": "There is no stock photography of smiling families in the product. Marketing pages may use one photographic treatment per page at most, and it must not be the first thing on the page above the fold, because the product's first job on a marketing page is to explain a rotating savings scheme to someone who has never been in one and does not know it is called anything. AJO.ng's diagrams carry that explanation better than a photograph does. **Illustration is drawn in the two-colour brand system at Deep and Cyan, and never depicts a specific person, a specific device, or a specific bank.**",
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'No avatars, no faces',
        "text": 'A member with no avatar shows their initials in a Deep circle, or nothing at all. There is no default photographic avatar, because a default face is a small false statement about who is in the group, and a group of ten people who have never met are being asked to trust each other with money on the strength of this interface. Section 6.26 already fixes the initials fallback; this is the visual rule behind it.',
    },

    {"t": "h2", "text": '7.7 Buttons, links, and action hierarchy'},

    {"t": "h3", "text": '7.7.1 The four levels of action'},

    {
        "t": "table",
        "head": ['Level', 'Component', 'Appearance', 'Count per screen', 'Use'],
        "rows": [
            ['Primary', 'Button, filled', 'Primary #146EF5, White label, 48 px tall, radius-md', '**One.** Zero on a screen with no single next step.', 'The one thing the person came to do.'],
            ['Secondary', 'Button, outlined', '1 px Primary border, Primary label, 48 px', 'Two or three', 'A real alternative to the primary, not a variant of it.'],
            ['Tertiary', 'Button, quiet', 'Primary label, transparent, 44 px', 'As needed', 'Navigation-ish actions: *Members*, *Schedule*, *Download PDF*.'],
            ['Destructive', 'Button, danger', 'danger fill, White label, 48 px', '**One, and never adjacent to a primary**', 'Cancel an Ajo, freeze, end a session, withdraw before a decision.'],
        ],
        "widths": [0.42, 0.54, 1.71, 1.71, 2.12],
        "size": 7.2,
    },

    {"t": "h3", "text": '7.7.2 Rules that do not bend'},

    {
        "t": "bullets",
        "items": [
            '**One primary per screen.** On the pay screen it is *Continue to payment*. On the receipt there is no primary at all, because a receipt has no next step and giving it a big button teaches people to expect one.',
            '**No duplicated primary across breakpoints.** The mobile sticky-bar primary and the desktop in-flow primary are the same button at two sizes, not two buttons. Two money buttons on one screen is two chances to charge someone.',
            '**A disabled button states why.** Every disabled primary is accompanied by the condition that would enable it, in the same field group, not in a tooltip. A greyed button with no explanation is the most common support ticket in consumer fintech.',
            '**Destructive controls are never a tap-and-hold.** A destructive action on touch is a confirmation sheet, and the sheet names the consequence in the button, not only in the body: *Cancel this Ajo and refund NGN 10,200.00*.',
            '**Loading is a state of the button, not a new screen.** The label becomes *Working*, the width is locked so the layout does not jump, and the control is disabled for the duration.',
        ],
    },

    {
        "t": "code",
        "text": """
+----------------------------------+
|  Cancel this Ajo?                |
|                                  |
|  Everyone who has paid receives  |
|  a full refund of NGN 10,200.00. |
|  Positions close. The Ajo cannot |
|  be reopened.                    |
|                                  |
|  [ Keep the Ajo ]   [ Cancel it ]|
|                                  |
|  The second button is danger and |
|  names the action. Never just     |
|  Confirm.                        |
+----------------------------------+
""",
    },

    {"t": "h3", "text": '7.7.3 Links'},

    {
        "t": "p",
        "text": 'Primary #146EF5, underlined, 16 px, offset 2 px. Underline is not optional: a link distinguished only by colour fails WCAG 1.4.1 for a proportion of users and fails for everyone in sunlight. Links inside a paragraph are underlined; links that are the entire content of a block — the row of legal links in a footer, for instance — are not, because a whole row of underlines is a wall.',
    },

    {"t": "h2", "text": '7.8 Form controls and validation'},

    {"t": "h3", "text": '7.8.1 Control specification'},

    {
        "t": "table",
        "head": ['Control', 'Height', 'Label position', 'Notes'],
        "rows": [
            ['Text input', '48 px', 'Above, always', 'Never a placeholder as the only label. Placeholder text disappears exactly when a person needs to check what the field wanted.'],
            ['Amount input', '56 px', 'Above', 'Right-aligned, tabular, with `NGN` as a static prefix rather than as typed text.'],
            ['Select', '48 px', 'Above', 'Native on mobile, custom on desktop. A custom select must support type-ahead and must show the selected value, not the index.'],
            ['Radio group', '48 px per option', 'Above the group', 'Options stacked, never in a row of chips. See 7.8.2.'],
            ['Checkbox', '24 px box, 48 px target', 'Right of the box, wrapping', 'Used for acknowledgement and for multi-select filters. Not used for on/off switches.'],
            ['Switch', '44 x 26 track', 'Left of the track', 'Only for preferences that take effect immediately. Never inside a form that needs a save button.'],
            ['OTP input', '56 px, 6 cells', 'Above', 'Paste fills all six cells. One cell is not a focus trap; arrow keys move within.'],
            ['Date', '48 px', 'Above', 'Native picker on mobile. On desktop, a masked input with a calendar affordance, never a free-text date.'],
        ],
        "widths": [0.42, 0.8, 0.9, 4.38],
        "size": 7.2,
    },

    {"t": "h3", "text": '7.8.2 Radio groups are never chips'},

    {
        "t": "p",
        "text": 'A segmented control that looks like a set of chips is used in this product for one thing only: a filter with no consequences. A frequency choice in the Create Ajo wizard, a payment method, and a dispute subject are radio groups with real labels under each option, because each option carries a consequence that a chip has no room to state. *Weekly* on its own is a duration; *Every Monday* is an obligation.',
    },

    {"t": "h3", "text": '7.8.3 Validation'},

    {
        "t": "p",
        "text": 'Validate on blur, never on keystroke, except for a field whose validity is knowable while typing — an amount, a phone number, a password. Three rules, in order of importance.',
    },

    {
        "t": "numbers",
        "items": [
            '**The error appears next to the field, in danger, with a specific sentence.** *That is more than NGN 5,000,000, which is the per-round limit* and not *Invalid amount*. A person who cannot tell which constraint they hit will ask support.',
            '**The field keeps what they typed.** Never cleared, never reformatted under the cursor mid-entry. The amount field accepts `1000` and displays `1,000.00` on blur, not before.',
            '**Focus moves to the first invalid field on a failed submit**, and the page does not scroll to the top to show a summary banner. A summary is useful for a nine-field form and useless for a three-field one, and it is the one place a person is guaranteed to be looking at the bottom of the screen.',
        ],
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Validation messages are a product surface, not a string table',
        "text": 'Every validation message in this product names a limit, a rule, or a next step. The per-round cap in the amount field is a good example: the message says what the limit is *and that risk sets it*, because a limit with no stated owner becomes an argument about whether the product is being difficult. The same applies to the five-day enrollment window, the D-08 Ajo size cap, and the one-position-per-member rule. Every one of those is a decision somebody made, and every one of them is visible on the screen where it bites.',
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '7.9 The dashboard, specified'},

    {
        "t": "p",
        "text": 'The dashboard is the screen every member sees first and the screen they return to most, and it is specified in full here rather than left to a pattern library because its hierarchy decides what this product feels like. A rotating savings scheme is a ledger with a countdown in it, and a dashboard that looks like a crypto wallet makes people expect a chart; one that looks like a bank statement makes them expect a number, and the number is what they came for.',
    },

    {"t": "h3", "text": '7.9.1 What the dashboard answers, in order'},

    {
        "t": "numbers",
        "items": [
            '**Do I owe anything right now?** The Next action block, at the top, present only when there is a due or overdue contribution. This is the single most-looked-at region on the screen and it is the reason the dashboard exists.',
            '**How much has gone into my Ajo, and how much is there?** The Ajo summary card, with three figures in a fixed order: contributed, in the pool now, and received to date.',
            '**When is my next turn?** The round timeline, immediately after the summary, because a person who has just paid wants to know what that payment bought them in time terms.',
            '**What happened to my last payment?** The last activity row, one line, dated, amount, and state word.',
            '**Is anything wrong?** Held, failed, or disputed items surface as a banner above everything else, not in a notification centre.',
        ],
    },

    {
        "t": "p",
        "text": 'Everything else — other Ajos, notifications, support, KYC prompts — is one tap away and is not on the dashboard. The five answers above are the dashboard; the rest is navigation.',
    },

    {"t": "h3", "text": '7.9.2 Region order and specification'},

    {
        "t": "table",
        "head": ['Order', 'Region', 'Component', 'Content rule', 'Absent when'],
        "rows": [
            ['1', 'Alert banner', '`Banner`', 'Held, failed, or disputed item, with the action that resolves it', 'Nothing is wrong'],
            ['2', 'Next action', '`NextActionBlock`', 'One due or overdue contribution, with amount, Ajo name, due date, and one primary button', 'Nothing is due'],
            ['3', 'Ajo summary', '`AjoCard`', 'Ajo name, status, three figures: contributed, in pool now, received. Progress bar with a count, not a percentage alone', 'Member is in no Ajo'],
            ['4', 'Round timeline', '`RoundTimeline`', 'Ten rounds, current one marked, payout marked, past ones dimmed. Always all ten, never a window', 'Member is in no Ajo'],
            ['5', 'Last activity', '`ActivityRow`', 'One row: date, description, amount, state word', 'No activity yet'],
            ['6', 'Other Ajos', '`AjoCard` list', 'One line per additional Ajo: name, status, next due', 'Member is in one Ajo only'],
        ],
        "widths": [0.42, 0.51, 0.62, 4.04, 0.91],
        "size": 7.2,
    },

    {"t": "h3", "text": '7.9.3 The three figures, and why they are in that order'},

    {
        "t": "p",
        "text": "Contributed, in the pool now, received to date. This order is the member's history: what I have put in, what my money is doing right now, and what it has become. The alternative order — received first, because it is the largest and the most satisfying number — puts the payout before the obligation and makes the screen read like a reward rather than a balance.",
    },

    {
        "t": "code",
        "text": """
Chima's Ajo  ·  Round 4 of 10  ·  ACTIVE

CONTRIBUTED          IN THE POOL NOW     RECEIVED
NGN 4,000.00         NGN 32,000.00        NGN 0.00

|####################-------------------|
4 of 10 rounds funded

Next payout to you:  Round 10,  20 Nov 2026
""",
    },

    {
        "t": "callout",
        "kind": 'WARNING',
        "title": 'The progress bar carries a count, never a percentage on its own',
        "text": '40 percent is a number about a chart. *4 of 10 rounds funded* is a number about the group, and it is the one a member can act on. The bar is a Cloud track with a Primary fill and a 3 px Cloud border; the text beneath it is label size, tabular, and never replaced by the bar. A progress bar with no count is also an accessibility failure, because it conveys its information only through width.',
    },

    {"t": "h3", "text": '7.9.4 The next action block'},

    {
        "t": "p",
        "text": "This is the only block on the dashboard with a filled Primary button, and it is the reason the product's money flows work. Its copy is fixed, because a person returning to the app to pay does not want a sentence.",
    },

    {
        "t": "code",
        "text": """
+------------------------------------------+
|  DUE IN 2 DAYS                            |
|  Your contribution to Chima's Ajo        |
|                                          |
|  NGN 1,000.00                             |
|                                          |
|  [ Pay now ]                              |
+------------------------------------------+
""",
    },

    {
        "t": "p",
        "text": 'Overdue changes the label to **OVERDUE — 3 DAYS** in danger fill and moves the block above the Ajo summary, because an overdue contribution affects the whole Ajo and the member needs to know that before anything else. The primary button still says *Pay now*. It does not say *Pay now or your Ajo fails*, which is a sentence that produces support tickets and does not change behaviour.',
    },

    {"t": "h3", "text": '7.9.5 The empty dashboard'},

    {
        "t": "p",
        "text": 'A new member with no Ajo gets one card, not an illustration of a person looking at a phone. It states what an Ajo is in two sentences, shows the fee disclosure because they will be charged it, and offers *Create an Ajo* and *Join with a code* as two Secondary buttons, because at this point the member genuinely does not know which they want and the interface should not pretend otherwise.',
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'The empty dashboard shows the fee, and this is not optional',
        "text": 'The empty state is where a member first sees the 2 percent fee, and it is shown as a real MoneyBlock, not as a sentence in a paragraph. The requirement in CANONICAL.md is that the fee appears separately from the contribution on every receipt and before a member commits, and the moment before a member commits is this screen. A design that reveals the fee for the first time on the first payment has met the letter of the rule and failed the intent of it.',
    },

    {"t": "h3", "text": '7.9.6 Dashboard states'},

    {
        "t": "table",
        "head": ['State', 'What shows', 'What is prohibited'],
        "rows": [
            ['Loading', 'Skeleton for summary, timeline, and activity only. The next action block is not skeletonised, because showing a fake amount in the one block that moves money is worse than a brief empty space.', 'A spinner centred on the page. A skeleton with plausible numbers in it.'],
            ['Offline', 'A single Cloud banner, *You are offline*, and the dashboard in its last loaded state with a timestamp. Every money action disabled.', 'Disabled buttons with no explanation. A cached balance presented as current.'],
            ['Empty', 'The empty dashboard of 7.9.5', 'A zero balance. NGN 0.00 as a hero figure reads as a failure.'],
            ['Partial', 'The Ajo summary and timeline render; the activity list shows a quiet retry if it fails alone. A region failure is not a page failure.', 'The whole dashboard behind a spinner because one region is slow.'],
            ['KYC pending', 'A Gold left rule on the Ajo card and one line: *Verification in review. Payouts wait for this.*', 'A modal. A blocking overlay. Anything that stops a member paying a contribution, because contributions are not blocked by KYC.'],
        ],
        "widths": [0.42, 3.59, 2.49],
        "size": 7.2,
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '7.10 Data visualisation'},

    {
        "t": "p",
        "text": 'This product has a strong temptation to visualise and a weak need to. Members want to know three things — what they owe, what they have, and when they are paid — and none of them is a distribution. The rules below are therefore restrictive, and the restriction is the point: a chart in a savings product is an argument that the data is more interesting than the answer, and it is usually wrong.',
    },

    {"t": "h3", "text": '7.10.1 Permitted forms'},

    {
        "t": "table",
        "head": ['Form', 'Used for', 'Series limit', 'Rules'],
        "rows": [
            ['Progress bar', 'Round funding progress on the Ajo card', '1', 'With a count beneath it. Never a percentage alone. Never a ring.'],
            ['Timeline', 'The ten rounds of an Ajo, current and payout marked', 'n/a', 'All ten rounds always shown, so the end is visible from round one.'],
            ['Sparkline', 'Thirty-day balance trend in the Ajo summary, desktop only', '1', 'No axis, no labels, no tooltip. Decoration, and it is allowed to be, because the figures are present as text beside it.'],
            ['Stacked bar', 'Pool composition by round in the console, and member-count mix by risk band', '2 to 4', 'Only where the parts sum to a meaningful whole, and only with direct labels.'],
            ['Dot plot', "Payout timing spread across an Ajo's members, console only", '1 series', 'Preferred over a histogram; see 7.10.4.'],
        ],
        "widths": [0.42, 2.24, 0.42, 3.42],
        "size": 7.2,
    },

    {"t": "h3", "text": '7.10.2 Prohibited forms'},

    {
        "t": "bullets",
        "items": [
            '**Pie and donut charts.** A part-to-whole with more than two parts is read by angle, and angles are compared badly. A stacked bar with labels does the same job and survives a screen reader.',
            '**3D anything.** Perspective changes apparent length, and the lengths are the data.',
            '**Dual-axis charts.** Two scales on one frame let the author imply any correlation they like by choosing the ranges.',
            '**Line charts of individual member balances.** A dip in a line is read as a loss, and a contribution is not a market. Money here only goes in and comes out, and a chart implies it moves on its own.',
            '**Word clouds, gauges, and speedometers.** A gauge has one number in it and a lot of chrome. Use the number, at money size.',
            '**Any chart of a single value.** One number is a figure, not a chart, and it is set in `money-lg`.',
        ],
    },

    {"t": "h3", "text": '7.10.3 Series colour and order'},

    {
        "t": "p",
        "text": 'The fixed palette contains exactly four colours that are allowed as series, and the order is fixed so that a reader learns the mapping once: **Primary for the subject of the chart, Cyan for the comparison, Gold for a total or a payout, and Cloud for remainder and empty track.** Series are never coloured semantically, and Gold is never used for a series where a total is also present, because Gold means total in the money block and reusing it for a category breaks the mapping.',
    },

    {"t": "h3", "text": '7.10.4 Distribution over histogram'},

    {
        "t": "p",
        "text": "Where a distribution is genuinely needed — the spread of payout timings in a console review, or the distribution of a risk score — it is drawn as a dot plot with a median rule, not as a histogram. A histogram's bin width is a choice the author makes, and in fraud and risk work the choice is where the disagreement hides. A dot plot with a stated median shows the same data and does not require the reader to accept a bin boundary.",
    },

    {
        "t": "code",
        "text": """
Payout timing, days from round close to payout

  0 |  . . :  . :
  1 |  . ::. :::
  2 |  ::::.:.:
  3 |  :::.:
  4 |  :.
    +-----------
    n = 10      median 1.4 d

One mark per member. The median is the only annotation.
""",
    },

    {"t": "h3", "text": '7.10.5 Every chart carries the same four things'},

    {
        "t": "numbers",
        "items": [
            '**A title that states the finding, not the metric.** *Most payouts settle within two days* and not *Payout timing*. If the chart does not support a finding, the chart should be a number.',
            '**An axis label with a unit, or an explicit statement that the axis is not to scale.** *Days from round close*, and never a bare `0 5 10`.',
            '**Direct labels on the series.** Not a legend. A legend is a lookup step, and on a 375 px screen the reader cannot hold the legend and the data at once.',
            '**The underlying figures, reachable.** Every chart has a text alternative listing the values, and in the console every chart has a *Download CSV* that uses the same permission as the underlying query.',
        ],
    },

    {
        "t": "callout",
        "kind": 'ASSUMPTION',
        "title": 'No charting library is chosen at v1',
        "text": "The forms permitted in 7.10.1 are all simple enough to draw directly in SVG, and the accessibility requirements in 7.10.5 — a text alternative with the actual values, direct labels, a stated median — are easier to satisfy without a library than to configure inside one. A library can be adopted later for the console's larger datasets; the constraint is that whatever renders a chart must be able to emit the text alternative, and that if it cannot, the chart is not shipped. This is recorded as an assumption because it constrains implementation and has not been reviewed by engineering.",
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '7.11 Tables, lists, and empty states'},

    {"t": "h3", "text": '7.11.1 Data tables'},

    {
        "t": "table",
        "head": ['Rule', 'Detail'],
        "rows": [
            ['Column widths', 'Content-driven, computed by the `table` rule in the authoring tooling so that column widths always sum to the text measure. Never a hand-tuned 30/70 split.'],
            ['Header', '`label` size, 500 weight, Dark, on a Cloud fill. The header row repeats on every page and every scroll container.'],
            ['Numeric columns', 'Right-aligned, tabular. Amounts right-align on the decimal, which is what tabular figures are for.'],
            ['Row height', '48 px minimum, 56 px on touch. Rows are never denser than 48 px, and no row is a tap target that opens something destructive.'],
            ['Zebra', 'Every other row on Cloud #F9FBFD, one step lighter than the page. Not the full Cloud, which reads as a selected row.'],
            ['Sort', 'Header click, with a caret and a visually hidden `Sorted ascending`. Server-side only; a client-side sort of a partial page is a lie about the data.'],
            ['Pagination', '30 rows on mobile, 50 on desktop, with the total count stated: *Showing 1 to 30 of 214*. Never an infinite scroll on a financial table, because a person needs to know where the list ends.'],
            ['Selection', 'Checkboxes for bulk actions only, and a destructive bulk action always uses the confirmation sheet of 7.7.2.'],
        ],
        "widths": [0.48, 6.02],
        "size": 7.4,
    },

    {"t": "h3", "text": '7.11.2 Lists'},

    {
        "t": "p",
        "text": 'A list row is 64 px on mobile and 56 px on desktop, with a 48 px tap target regardless. A row carries, left to right: a leading element if the thing has an identity, a title, one supporting line, a trailing value or status, and a chevron if the row navigates. **A row never has a chevron unless it navigates**, because a chevron on a tappable row that opens a sheet teaches people that the interface is guessing, and it is a WCAG 2.2 AA problem under 2.4.11 Focus Not Obscured when the destination is a sheet that covers the row.',
    },

    {"t": "h3", "text": '7.11.3 Empty states'},

    {
        "t": "p",
        "text": 'Every list in the product has an empty state, and none of them is a picture. An empty state is three things in order: a plain statement of what is empty, a sentence on why it is empty, and the action that fills it. Where there is no action, the state says so rather than inviting one.',
    },

    {
        "t": "table",
        "head": ['State', 'Statement', 'Why', 'Action'],
        "rows": [
            ['No Ajos', '*You are not in an Ajo yet*', 'An Ajo needs ten people and yours has not been created.', '*Create an Ajo* and *Join with a code*'],
            ['Empty activity', '*No payments yet*', 'Activity appears when a contribution or payout is recorded.', 'None. This is not a problem to solve.'],
            ['Empty schedule', '*No schedule yet*', 'A schedule is created when the organizer sets frequency and start date.', '*Set the schedule* — organizer only'],
            ['Empty statement', '*No transactions in this period*', 'The period filter excluded everything recorded.', '*This month* — resets the filter'],
            ['Empty search', '*No results for \\u201cxyz\\u201d*', 'The query matched nothing.', '*Clear search*'],
            ['Console, no cases', '*No cases match these filters*', 'Filters excluded everything, or the queue is genuinely empty.', '*Reset filters* — and the two are different messages'],
        ],
        "widths": [0.64, 1.21, 2.68, 1.97],
        "size": 7.4,
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'Empty is not zero',
        "text": 'An empty Ajo list shows a sentence, not `NGN 0.00` and not a dash. A zero is a measurement; an empty list is the absence of one, and a person who has just signed up does not need to be told they have nothing in the way a bank app tells them. This applies to the roster, the schedule, the statement, and every console queue. The one exception is a figure that genuinely is zero and is genuinely expected to be zero, such as received to date on round one, which is shown as `NGN 0.00` because it is a figure and its zero is information.',
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '7.12 Money surfaces'},

    {
        "t": "p",
        "text": 'This is the most important component in the product and the one with the fewest permitted variations. Everything in this section exists so that a member can answer three questions about any amount they see: **how much, of what, and where does it go.** An interface that answers two of the three is worse than one that answers none, because a confident wrong figure is trusted.',
    },

    {"t": "h3", "text": '7.12.1 The MoneyBlock, and it is non-negotiable'},

    {
        "t": "code",
        "text": """
Your contribution
-------------------------------
Contribution              NGN 1,000.00
Service fee (2%)             NGN 20.00
-------------------------------
Total to pay             NGN 1,020.00

NGN 1,000.00 goes into the Ajo pool.
NGN 20.00 is the AJO.ng service fee.
""",
    },

    {
        "t": "numbers",
        "items": [
            '**Contribution and fee are always on separate lines, with a rule between them and a total below the rule.** Never merged into a single figure with the fee mentioned afterwards.',
            '**The fee line is named, not implied.** *Service fee (2%)* — the name, the rate, and the amount. The rate is in the label so the arithmetic is checkable without a second document.',
            '**The destination of each part is stated in words below.** The contribution goes into the pool; the fee does not. This is the sentence that prevents the most common misunderstanding in this product category, and it is prose, not a footnote.',
            "**Amounts are `NGN 1,000.00` everywhere** — thousands separated, exactly two decimals, never a bare number, never a currency symbol in place of the code. A screen showing `₦1,000` is using a glyph the recipients' own devices may not render.",
            '**The fee is shown before the member commits, at the point of commitment, and on the receipt.** Those are three placements and they are the same component, not three implementations of the same idea.',
        ],
    },

    {
        "t": "callout",
        "kind": 'WARNING',
        "title": 'The one component that cannot be redesigned under deadline',
        "text": 'Merging the contribution and the fee into `NGN 1,020.00` is the single most likely way this product breaks its own rule, and it is likely because the merged version is prettier, shorter, and passes a screenshot review. It must not happen. CANONICAL.md requires the fee to be shown separately from the contribution on every receipt and in the join and invitation confirmation before the member commits, and the requirement is not about tidiness — it is about a member being able to see what they are paying for. The 2 percent is NGN 20.00 on a NGN 1,000.00 contribution. A member who cannot see NGN 20.00 has not been told what AJO.ng charges them, whatever the total says.',
    },

    {"t": "h3", "text": '7.12.2 Where the MoneyBlock appears'},

    {
        "t": "table",
        "head": ['Surface', 'Variant', 'Required content'],
        "rows": [
            ['Create Ajo, step 2', 'Estimate', 'Per-member contribution, fee, total per member, and the pool total for ten members. The member is deciding what ten of them will pay.'],
            ['Join an Ajo', 'Estimate', "The organizer's amount, fee, total, frequency, and start date, immediately above the join button."],
            ['Pay contribution', 'Confirm', 'The same three lines, plus the payment method, immediately above the pay button.'],
            ['Payment processing', 'Locked', 'The same three lines, non-interactive, plus the processing notice. Not a confirmation yet.'],
            ['Receipt', 'Receipt', 'The three lines, a reference, a timestamp, the payer, the Ajo, and the round. Downloadable as PDF and shareable as an image.'],
            ['Transaction detail', 'Single', 'The three lines, the round, the state word, and the reference.'],
            ['Payout', 'Receipt', 'The gross payout, no fee line, and the note that no fee is charged on receipt of funds.'],
            ['Console, Ajo view', 'Table', 'Contribution and fee as two columns, never a computed total.'],
        ],
        "widths": [0.74, 0.42, 5.34],
        "size": 7.2,
    },

    {
        "t": "callout",
        "kind": 'DECISION',
        "title": 'No fee is charged on payout',
        "text": "The 2 percent fee is charged once, on contribution, and never on payout. The payout surface therefore has no fee line at all, and this is stated in the component rather than left as an absence, because a payout showing a fee line with a zero in it invites a support conversation that a line with no fee on it does not. The console's Ajo view does show both figures per member, because that is where a reviewer is reconciling what was taken against what was pooled, and there the total is a column rather than a headline.",
    },

    {"t": "h3", "text": '7.12.3 Payout emphasis'},

    {
        "t": "p",
        "text": 'A payout is the only figure in the product set in `money-lg` on its own screen, and it is the only place Gold appears on a figure. It is centred on the payout surface and nowhere else, because centring is correct exactly once per Ajo and becomes noise the second time. The payout screen carries the amount, the date, the destination reference, and one primary action — *Done* — with no share and no celebration animation. A member receiving money is not a milestone; the routine case is ten times out of ten.',
    },

    {
        "t": "code",
        "text": """
Payout received

        NGN 10,000.00
     to Kemi A.  ·  GTBank  ·  0451128873
        20 Nov 2026

         [  Done  ]

No service fee is charged on a payout.
""",
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '7.13 Motion'},

    {
        "t": "p",
        "text": 'Motion in this product has one job: to explain a change of state. It is not used for personality, and it is not used to reward. **Every duration in the product is between 150 ms and 250 ms**, which is long enough for the eye to track a change and short enough that a person paying money does not wait for it.',
    },

    {"t": "h3", "text": '7.13.1 Duration and easing'},

    {
        "t": "table",
        "head": ['Token', 'Duration', 'Easing', 'Applied to'],
        "rows": [
            ['motion-instant', '0 ms', 'none', 'State changes that must feel immediate: button press, checkbox, tab change'],
            ['motion-fast', '150 ms', '`cubic-bezier(0.2, 0, 0, 1)`', 'Sheets and menus entering, list rows appearing, banner reveal'],
            ['motion-base', '200 ms', '`cubic-bezier(0.2, 0, 0, 1)`', 'Card expansion, the round timeline advancing, amount changes'],
            ['motion-slow', '250 ms', '`cubic-bezier(0.4, 0, 0.2, 1)`', 'Page-level transitions, the step change in the wizard'],
        ],
        "widths": [0.72, 0.42, 1.55, 3.81],
        "size": 7.4,
    },

    {"t": "h3", "text": '7.13.2 What is allowed'},

    {
        "t": "bullets",
        "items": [
            '**A sheet rising 16 px and fading in** over 150 ms. This is the maximum travel distance in the product.',
            '**A list row appearing** as a 150 ms fade with an 8 px rise, capped at the first eight rows. A staggered cascade is prohibited; it delays the tenth payment behind nine decorations.',
            "**A round timeline advancing** one position over 200 ms, with the new position's label cross-fading in the same interval.",
            '**An amount changing** by a 200 ms cross-fade, never by a count-up. A number counting upward to a figure is a number that is briefly wrong, and it is the wrong thing to do to a balance.',
            '**A skeleton to content** cross-fade of 150 ms.',
        ],
    },

    {"t": "h3", "text": '7.13.3 What is prohibited'},

    {
        "t": "bullets",
        "items": [
            '**Confetti, confetti, and every other celebration.** A successful contribution is a receipt. A successful payout is a receipt with a larger number on it.',
            '**Count-up numbers**, on any figure, ever.',
            '**Parallax, scroll-jacking, and any animation bound to scroll position.** A person scrolling a transaction list is reading, and reading is not a cutscene.',
            '**A spinner over content that is already readable.** A region refresh is silent; only a full-page load blocks.',
            '**Auto-advancing carousels** in the marketing hero, and any hero animation longer than 250 ms.',
            '**Looping motion.** A continuously moving element in a financial product is read as *pending*.',
        ],
    },

    {"t": "h3", "text": '7.13.4 Reduced motion'},

    {
        "t": "p",
        "text": 'The product honours `prefers-reduced-motion: reduce` completely, and the contract is simple enough to state as a rule rather than a list: **under reduced motion, every animation becomes an instant state change and every transition becomes a cut.** Nothing is removed, no information is lost, and no screen is hidden.',
    },

    {
        "t": "code",
        "text": """
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
""",
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'No `!important` on colour or layout, only on motion',
        "text": 'The reduced-motion block above touches duration and iteration only. A common mistake is to strip transforms as well, which leaves a sheet rendered at its final position but with the fade still present, and leaves a list row with an 8 px offset it can no longer animate away. The correct approach is that the motion tokens are the only thing that changes: `motion-fast`, `motion-base` and `motion-slow` all resolve to 0 ms under reduced motion, and no component hard-codes a duration. **WCAG 2.2 AA 2.3.3 Animation from Interactions is Level AAA and is therefore not strictly required**, but the product targets it anyway, because a rotating savings scheme is not a place to be surprising someone.',
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '7.14 Accessibility'},

    {
        "t": "p",
        "text": 'The target is **WCAG 2.2 Level AA**, and the reason it is a target rather than an aspiration is demographic rather than ethical: a rotating savings scheme recruits through social trust, and social trust recruits people the average financial app is not designed for — older members who are trusted with money and are not trusted with interfaces, members on low-end Android devices where a 2 MB bundle is a 4-second first paint, and members using the cheapest handset their network can carry. A member who cannot read the screen cannot be a reliable member, and the person organising the Ajo is usually the one who feels this first.',
    },

    {"t": "h3", "text": '7.14.1 Conformance commitment'},

    {
        "t": "bullets",
        "items": [
            '**WCAG 2.2 Level AA** is the conformance target for every screen in section 6, member and admin alike.',
            '**Level AAA is met where it is cheap**, specifically 2.3.3 Animation from Interactions, 1.4.8 Visual Presentation at AA, and 2.4.11 Focus Not Obscured.',
            '**No exceptions are claimed and no partial conformance is claimed.** A screen that cannot meet AA is not shipped; it is redesigned.',
            '**The accessibility statement is published with the product**, naming the level, the date, and the known issues. An unlisted known issue is a defect.',
        ],
    },

    {"t": "h3", "text": '7.14.2 The specific ways this product fails people'},

    {
        "t": "p",
        "text": 'A generic accessibility checklist would not catch most of these. Each is a property of *this* product, and each has a rule in the component definitions.',
    },

    {
        "t": "table",
        "head": ['Failure', 'Who it affects', 'Rule', 'Criterion'],
        "rows": [
            ['Amounts and dates carried only by visual position', 'Screen reader, low vision, cognitive', 'Every amount is inside a labelled element with an accessible name that includes the currency and the full value', '1.1.1, 1.3.1'],
            ['Fee hidden inside a single total', 'Everyone, but most acutely low-literacy users and screen reader users', 'MoneyBlock always separates contribution, fee, and total — see 7.12', '1.3.1, 3.3.2'],
            ['State carried by colour', 'Colour-blind users, low vision, in sunlight', 'Every state has a word; the state pill is text with a fill, never a bare dot', '1.4.1'],
            ['Progress bar with no text', 'Screen reader, cognitive', 'Every bar is followed by a count; the bar has `aria-hidden` and the text is the truth', '1.1.1, 1.3.1'],
            ['Countdown to a due date creating pressure', 'Cognitive, anxiety', 'No timers, no countdowns, no urgency counters. A due date is a date.', '—'],
            ['48 px tap targets missed on a money action', 'Motor impairment, tremor, one-handed use', 'Every interactive element is at least 44 x 44 CSS px, and 48 px on touch for anything that moves money', '2.5.8'],
            ['Chart with no text alternative', 'Screen reader', 'Every chart emits a text alternative containing the actual values', '1.1.1'],
            ['Sheet covering the focused element', 'Keyboard, switch access, screen magnification', 'A focused element is never left behind a sheet or a sticky bar; the sheet traps focus and restores it on close', '2.4.11 Focus Not Obscured'],
            ['Ambiguous link text', 'Screen reader out of context', 'Link text is never *click here*, *read more*, or *learn more* on its own; the link names its destination', '2.4.4'],
            ['Low-contrast Cyan or Gold text', 'Low vision, sunlight', 'Cyan and Gold are never text on White. Text on White is Dark or Primary only', '1.4.3, 1.4.11'],
            ['Custom select without type-ahead', 'Keyboard, motor', 'Every custom control is operable by keyboard with a visible focus ring, and the select supports type-ahead', '2.1.1, 2.1.2'],
            ['Session timeout during payment', 'Cognitive, slow connections, assistive tech', 'The session warning is a 5-minute modal with an extend action, and a payment in flight is never lost to a timeout', '2.2.1'],
        ],
        "widths": [1.24, 1.75, 2.88, 0.63],
        "size": 7.0,
    },

    {"t": "h3", "text": '7.14.3 Keyboard and focus'},

    {
        "t": "bullets",
        "items": [
            '**Focus is never removed without a destination.** Closing a sheet returns focus to the control that opened it.',
            '**Focus is always visible**: a 2 px Primary ring with a 2 px offset, never `outline: none` without a replacement. The ring is visible on Deep, on Cloud, and on Primary.',
            '**Focus order follows the visual order**, and it follows the region order in 7.9.2 exactly. A dashboard whose DOM order differs from its reading order is a defect found in review, not shipped.',
            '**Skip links** to the main content and to the money summary, because the next action block and the MoneyBlock are the two things a screen reader user came for and should not have to traverse a nav to reach.',
            '**The wizard traps nothing** and moves focus to the step heading on every step change, with the step announced. A seven-step wizard with no focus move is a wizard a keyboard user cannot complete.',
        ],
    },

    {"t": "h3", "text": '7.14.4 Forms'},

    {
        "t": "p",
        "text": 'Every input has a `<label>` bound by `for`, and where a field has a format the member might get wrong — phone, OTP, BVN, account number — the format is stated in helper text below the field rather than only in the placeholder. Errors are announced: `aria-invalid` is set, the error text is referenced by `aria-describedby`, and focus moves to the first invalid field on a failed submit, per 7.8.3. **A person using a screen reader hears the error before they see the red**, and it is the same sentence.',
    },

    {"t": "h3", "text": '7.14.5 Forced colours and platform settings'},

    {
        "t": "p",
        "text": "In Windows High Contrast mode the palette is replaced by the system colours, and the product stays usable: borders become `ButtonBorder`, state pills become outlined with their text intact, and the progress bar's fill is expressed with `forced-color-adjust: none` on the fill only so it remains visible. Text scaling to 200 percent and browser zoom to 400 percent reflow rather than scroll horizontally at every breakpoint including 320 px. **Nothing is hidden at any text size**, and no information is available only through hover.",
    },

    {
        "t": "callout",
        "kind": 'ASSUMPTION',
        "title": 'Accessibility is verified by people, not only by tools',
        "text": 'Automated testing catches roughly a third of WCAG issues and in this product it catches almost none of the ones in 7.14.2, because those are all semantic and content problems rather than attribute problems. The assumption recorded here is that before v1 launch the member journeys are walked with at least one person using a screen reader and at least one using only a keyboard, on the actual built product rather than on a design. This is an assumption because it is a a resourcing commitment that has not been agreed, and if it is not made, the conformance claim in 7.14.1 should be withdrawn rather than softened.',
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '7.15 Component inventory'},

    {
        "t": "p",
        "text": 'Every component below exists because a numbered region in section 6 needs it. The third column is the traceability requirement: a component with no region reference is either redundant or is a signal that section 6 is missing a screen.',
    },

    {
        "t": "table",
        "head": ['Component', 'Purpose', 'Used by regions', 'Variants'],
        "rows": [
            ['`AppShell`', 'Nav, page frame, safe areas', 'Every screen', 'Bottom nav (mobile), top bar (tablet and desktop), console rail (console)'],
            ['`MoneyBlock`', 'Contribution, fee, total, destination', '7.12 surfaces; regions in 6.16, 6.17, 6.19, 6.20', 'Estimate, Confirm, Locked, Receipt, Single'],
            ['`AjoCard`', 'One Ajo with its three figures and progress', '6.10, 6.11, 6.14', 'Active, Pending, Completed, Frozen, plus a KYC-pending rule'],
            ['`NextActionBlock`', 'The one due or overdue contribution', '6.10', 'Due, Overdue'],
            ['`RoundTimeline`', 'Ten rounds, current and payout marked', '6.10, 6.14, 6.16', 'Member view, Organizer view with per-member state'],
            ['`StatePill`', 'A state as a word with a fill', 'Every list, table, and card', 'Paid, Due, Overdue, Held, Defaulted, Pending, Frozen, Active, Completed, Disputed'],
            ['`DataTable`', 'Sortable, paginated rows', '6.15, 6.16, 6.21, 6.31, 6.32, 6.33', 'Member, Organizer, Admin, with selection'],
            ['`WizardStep`', 'One step of seven, with a guard', '6.12', 'Seven bodies, shared chrome, forward and back'],
            ['`FormField`', 'Label, control, helper, error', 'Every form in 6.5 to 6.9, 6.13, 6.17, 6.24, 6.28', 'Text, Amount, Select, Radio, Checkbox, Switch, OTP, Date, File'],
            ['`Banner`', 'Something that changes what you should do', '6.10, 6.22, 6.23, 6.29, 6.30', 'Information, Warning, Danger, Offline'],
            ['`Callout`', 'A statement that belongs to the page, not to a control', 'Section 6 decision and note callouts', 'NOTE, WARNING, LEGAL, ASSUMPTION, DECISION'],
            ['`Sheet`', 'A focused task over a page', '6.8, 6.11, 6.19, 6.25, 6.27, 6.31', 'Bottom sheet on mobile, centred dialog on desktop'],
            ['`ReceiptCard`', 'A durable record of a movement', '6.19, 6.20', 'Contribution, Payout, with PDF and share'],
            ['`UploadField`', 'A document capture with progress and retry', '6.28', 'Camera, file, with type, size, and legibility guidance'],
            ['`Thread`', 'Messages on a dispute', '6.25, 6.31', 'Member view, Admin view with internal note'],
            ['`Chart`', 'The forms permitted in 7.10.1', '6.10, 6.30, 6.32', 'Progress, Timeline, Sparkline, StackedBar, DotPlot'],
            ['`Skeleton`', 'A loading state with correct geometry', 'Every region that loads', 'Card, Row, Table, Block'],
            ['`EmptyState`', 'Statement, reason, action', 'Every list', 'With action, without action, filter-cleared'],
        ],
        "widths": [0.55, 1.76, 1.56, 2.63],
        "size": 6.8,
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": "Two components in this table are the product's real differentiators",
        "text": '`MoneyBlock` and `RoundTimeline` are the only two things in the interface that a competitor cannot copy with a colour change, and they are also the two that are easiest to get subtly wrong. The timeline in particular earns its place by showing all ten rounds from round one, so a member can see the shape of the commitment before making it — a commitment product that hides the end until you are halfway through has not earned the trust it is asking for. Both are worth disproportionate care in review, and both are covered by the states in their own tables rather than by a global states pattern.',
    },

    {"t": "h2", "text": '7.16 Dark mode'},

    {
        "t": "callout",
        "kind": 'DECISION',
        "title": 'Dark mode is deferred past v1 and this is a decision, not an omission',
        "text": "v1 ships light mode only. Dark mode is deliberately out of scope for the first release and is planned for the release after, once the component set in 7.15 has stabilised. The two reasons are that a financial interface is read in daylight more often than at night, so light mode is the case that has to be right first, and that every surface in the palette was chosen and contrast-checked for a light background — Deep and Cyan both behave differently as a large fill, and doing dark mode properly means re-checking all of 7.14 rather than inverting a colour. **Shipping a half-done dark mode is worse than shipping none**, because a member whose OS is set to dark will get the one they did not choose and cannot turn off, and this product's users are not the population most able to work around that.",
    },

    {"t": "h3", "text": '7.16.1 What is required before dark mode is built'},

    {
        "t": "numbers",
        "items": [
            '**The component set is stable.** 7.15 stops changing. Every new component after dark mode ships must be designed in both modes from the start, which is a permanent tax on the design system and is worth paying late rather than early.',
            '**The semantic roles in 7.3.2 are re-derived for a dark surface** and contrast-checked individually, not inverted. The success, warning, danger, and information fills each need their own dark-surface values, and the state pills need their own text colours, because Gold on a dark surface and Gold on a light surface are not the same colour to a reader.',
            '**Charts get a second palette** for a dark surface, chosen by luminance rather than by inversion, and re-checked against 1.4.11 Non-text Contrast at 3:1.',
            '**Images and screenshots in receipts** are re-rendered rather than left as light rectangles on a dark surface, because a receipt is a record and it must look the same as the record it refers to.',
        ],
    },

    {"t": "h3", "text": '7.16.2 What must not happen in the meantime'},

    {
        "t": "bullets",
        "items": [
            '**No automatic inversion, ever.** An inverted light palette produces text at 4.1:1 and a Cyan that reads as a different colour, and it is detectable in a screenshot.',
            '**No half-support.** A dark status bar on a light page is a half-support, and it reads as a bug.',
            '**No `prefers-color-scheme` branch in v1.** The branch does not exist until the palette in 7.16.1 exists, because a branch with no values behind it is a class of bugs that surfaces on exactly the devices least able to report them.',
        ],
    },

    {"t": "pagebreak"},

    {"t": "h2", "text": '7.17 Tokens and handoff'},

    {"t": "h3", "text": '7.17.1 The token set, complete'},

    {
        "t": "p",
        "text": 'Every value in this section, in one place, in the form engineering consumes. This is the only list in the document that is a specification rather than a justification, and it is the one to build from.',
    },

    {
        "t": "kv",
        "pairs": [
            ('Colour — brand', '`deep #0B1F3A`, `primary #146EF5`, `cyan #22C7D6`, `gold #FBBF24`, `white #FFFFFF`, `cloud #F4F7FB`, `dark #101828`'),
            ('Colour — surfaces', '`surface-page #F4F7FB`, `surface-card #FFFFFF`, `surface-row #F9FBFD`, `surface-dark #0B1F3A`, `border #E4EAF2`, `border-strong #C9D4E4`'),
            ('Colour — text', '`text-primary #101828`, `text-secondary #475467`, `text-tertiary #667085`, `text-inverse #FFFFFF`, `text-link #146EF5`'),
            ('Colour — semantic fills', '`success-fill #ECFDF3`, `success-text #05603A`, `warning-fill #FFFAEB`, `warning-text #93370D`, `danger-fill #FEF3F2`, `danger-text #B42318`, `info-fill #EFF8FF`, `info-text #175CD3`'),
            ('Type', '`family-sans` per 7.4.1, and the scale tokens `display`, `h1`, `h2`, `h3`, `body`, `body-strong`, `label`, `caption`, `micro`, `money`, `money-lg` with the sizes and line heights in 7.4.2'),
            ('Space', '`space-1` 4, `space-2` 8, `space-3` 12, `space-4` 16, `space-5` 24, `space-6` 32, `space-7` 48, `space-8` 64'),
            ('Radius', '`radius-sm` 4, `radius-md` 8, `radius-lg` 12, `radius-pill` 999'),
            ('Breakpoints', '`xs` 320, `sm` 375, `md` 768, `lg` 1024, `xl` 1280, `2xl` 1440'),
            ('Elevation', '`elevation-card` `0 1px 2px rgba(16,24,40,0.05)`, `elevation-sheet` `0 -4px 16px rgba(16,24,40,0.12)`, `scrim` `rgba(11,31,58,0.40)`'),
            ('Motion', '`motion-instant` 0, `motion-fast` 150, `motion-base` 200, `motion-slow` 250, easing `cubic-bezier(0.2, 0, 0, 1)` and `cubic-bezier(0.4, 0, 0.2, 1)`, all 0 under reduced motion'),
            ('Focus', '`focus-ring` 2 px `primary`, offset 2 px, never removed without replacement'),
            ('Tap target', '`target-min` 44 x 44 px, `target-money` 48 x 48 px on touch'),
            ('Chart series', '`series-1` primary, `series-2` cyan, `series-total` gold, `series-remainder` cloud, in that fixed order'),
        ],
    },

    {"t": "h3", "text": '7.17.2 Handoff notes'},

    {
        "t": "numbers",
        "items": [
            "**Tokens are the only source of colour, size, and duration in the codebase.** A hex literal or a millisecond value outside the token file is a review finding, not a preference. This is how 7.13.4's reduced-motion block can be a single variable change rather than an audit.",
            '**The component set in 7.15 is delivered with its states, not without them.** A component delivered in its default state only is not delivered; the loading, empty, error, and off states in its own table are part of the definition.',
            '**Region references are load-bearing.** When a section 6 region changes, the components in 7.15 and the specifications in 7.9 and 7.10 are checked in the same review, because a region can grow a new state that no component has.',
            '**The MoneyBlock is reviewed by someone who did not write it,** against 7.12, on every change. It is the only component in the product with a review requirement rather than a review guideline, and the reason is in 7.12.1.',
            '**Any screen that cannot be traced to a numbered region in section 6 is not built.** This is the mechanism that keeps the three sections in agreement, and it is why this section specifies components rather than pages.',
        ],
    },

    {"t": "h3", "text": '7.17.3 Open items carried into build'},

    {
        "t": "p",
        "text": "Three items in this section are recorded as assumptions rather than decisions, and they are collected here so they are not lost between documents: the typeface in 7.4.1, pending the founders' confirmation; the absence of a charting library in 7.10.5; and the human verification in 7.14.5. Each is cheap to change now and expensive to change after the interface is built, which is the only reason they are written down at all.",
    },

    {
        "t": "callout",
        "kind": 'NOTE',
        "title": 'What this section deliberately does not do',
        "text": 'It does not add a screen, a region, a state, or a promise. Section 6 owns the structure, section 2 owns the flows, and CANONICAL.md owns the product. What this section does is make the interface that results from those three consistent, legible, and honest about money — which, for a product whose whole proposition is that other people can be trusted with it, is the only visual requirement that was ever really in question.',
    },

]
