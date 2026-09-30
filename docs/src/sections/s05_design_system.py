"""Section 5 — Design System."""

BLOCKS = [
    {"t": "h1", "text": "5. Design System — AJO.ng"},

    {"t": "lead", "text": "One token set and one component language shared by the "
     "web application, the mobile application and the admin console. A member who "
     "learns the product on a phone should not have to relearn it on a laptop."},

    {"t": "h2", "text": "5.1 Principles"},
    {"t": "bullets", "items": [
        "**Trust is the primary aesthetic.** A savings product is judged on whether it "
        "feels safe, not whether it looks clever. Restraint beats decoration.",
        "**Numbers first.** Money is the content. Typography, spacing and colour serve "
        "legibility of a figure, not the other way round.",
        "**Never hide the mechanism.** The 2% fee, the payout order and the enrollment "
        "deadline are always visible, never buried in a disclosure the member must hunt for.",
        "**One meaning per colour.** Green is only ever settled money. Gold is only ever "
        "an imminent payout. A member who learns three signals keeps them.",
        "**Accessible by construction.** Contrast, focus and target size are token-level "
        "constraints, not per-screen judgement calls.",
        "**Consistent across platforms.** The same token resolves to the same value on "
        "web, mobile and admin.",
    ]},

    {"t": "h2", "text": "5.2 Colour tokens"},
    {"t": "p", "text": "The seven brand colours below are fixed and were supplied by the "
     "founders. Everything after this table is derived from them."},

    {"t": "table", "head": ["Token", "Hex", "Role", "Primary usage", "Contrast on white", "Do not use for"], "widths": [0.75, 0.75, 0.9, 1.9, 0.9, 1.3], "size": 8.2, "rows": [
        ["Deep", "#0B1F3A", "Brand anchor", "H1 headings, dark surfaces, hero bands, admin sidebar", "15.9:1", "Body text on light surfaces at small sizes — use Dark instead"],
        ["Primary", "#146EF5", "Primary action", "Primary buttons, active nav, links, H2 headings, data-viz series 1", "4.6:1", "Large blocks of text; body copy fails contrast on white"],
        ["Cyan", "#22C7D6", "Secondary accent", "Progress indicators, data-viz series 2, active tab underline, focus ring pair", "1.9:1", "Text on white — insufficient contrast. Accent fills and shapes only"],
        ["Gold", "#FBBF24", "Attention accent", "'Payout imminent', position lock, warning banners, achievement moments", "1.7:1", "Text on white. Never the sole carrier of meaning"],
        ["White", "#FFFFFF", "Surface", "Cards, page background under Cloud, text on dark surfaces", "—", "Body text on light surfaces"],
        ["Cloud", "#F4F7FB", "Canvas", "Page background, zebra table rows, empty-state panels", "1.1:1", "Borders or separators — too low contrast"],
        ["Dark", "#101828", "Body text", "All body copy, table data, input text, labels", "16.9:1", "Background fills behind small text"],
    ]},

    {"t": "h3", "text": "5.2.1 Derived semantic tokens"},
    {"t": "p", "text": "Semantic names rather than colour names, so a theme change "
     "requires no component edits. The status ramp is an **addition** to the supplied "
     "palette — the seven brand colours contain no success or danger colour, and a "
     "savings product cannot ship without both."},

    {"t": "table", "head": ["Semantic token", "Value", "Maps from", "Usage"], "widths": [1.5, 0.9, 1.1, 3.0], "size": 8.4, "rows": [
        ["bg-canvas", "#F4F7FB", "Cloud", "Page background"],
        ["bg-surface", "#FFFFFF", "White", "Cards, sheets, modals, table header"],
        ["bg-subtle", "#F4F7FB", "Cloud", "Zebra rows, inset panels, code blocks"],
        ["bg-inverse", "#0B1F3A", "Deep", "Top nav on mobile, admin sidebar, hero"],
        ["border-default", "#D0D5DD", "— (addition)", "Card, input and table borders"],
        ["border-strong", "#98A2B3", "— (addition)", "Focused input, active table sort"],
        ["text-primary", "#101828", "Dark", "Body copy, headings in tables"],
        ["text-secondary", "#475467", "— (addition)", "Helper text, metadata, captions"],
        ["text-inverse", "#FFFFFF", "White", "Text on Deep/Primary backgrounds"],
        ["action-primary", "#146EF5", "Primary", "Primary buttons, active nav item"],
        ["action-primary-hover", "#0F5AD0", "— (derived)", "Primary button hover, 12% darken"],
        ["action-primary-pressed", "#0B4CB0", "— (derived)", "Primary button active state"],
        ["action-secondary", "#FFFFFF", "White", "Secondary button fill with Primary border"],
        ["link", "#146EF5", "Primary", "Inline text links, underlined on hover"],
        ["success", "#12B76A", "— (addition)", "Contribution settled, KYC approved, Ajo completed"],
        ["success-bg", "#ECFDF3", "— (addition)", "Success banner fill"],
        ["warning", "#DC6803", "— (addition)", "Payment overdue, grace period running"],
        ["warning-bg", "#FFFAEB", "— (addition)", "Warning banner fill — pairs with Gold accent"],
        ["danger", "#D92D20", "— (addition)", "Default recorded, payment failed, account frozen"],
        ["danger-bg", "#FEF3F2", "— (addition)", "Danger banner fill"],
        ["info", "#146EF5", "Primary", "Neutral informational banner"],
        ["info-bg", "#EFF6FF", "— (derived)", "Informational banner fill"],
        ["money-positive", "#12B76A", "success", "Received, credited, settled"],
        ["money-negative", "#D92D20", "danger", "Owed, overdue, debited"],
        ["money-pending", "#DC6803", "warning", "In flight, awaiting provider confirmation"],
        ["money-fee", "#146EF5", "Primary", "The 2% platform fee line, wherever it appears"],
    ]},

    {"t": "callout", "kind": "DECISION", "title": "Contrast verified:",
     "text": "Cyan (#22C7D6) at 1.9:1 and Gold (#FBBF24) at 1.7:1 fail WCAG AA for text "
     "on white. Both are therefore restricted to fills, shapes, progress indicators and "
     "decorative accents, never to carry text. Where an accent must appear in a text "
     "run, a darkened variant is used. This is a constraint, not a preference."},

    {"t": "h2", "text": "5.3 Typography"},

    {"t": "h3", "text": "5.3.1 Typeface selection"},
    {"t": "table", "head": ["Option", "Family", "Strengths", "Trade-offs", "Status"], "widths": [0.7, 1.3, 1.9, 2.0, 0.7], "size": 8.3, "rows": [
        ["A (recommended)", "Inter", "Excellent numerals including tabular figures, tall x-height suits dense financial tables, variable font, broad weight range, self-hostable", "Heavier payload than a system stack; must be self-hosted to avoid a third-party render dependency in Nigeria", "Recommended"],
        ["B", "Plus Jakarta Sans", "Warmer, more distinctive, reads as contemporary fintech", "Weaker tabular-figure support, requires careful fallback metrics on dense tables", "Alternative"],
        ["C", "System stack (-apple-system, Segoe UI, Roboto)", "Zero payload, zero licensing risk, instant render on every device", "Inconsistent metrics across platforms; harder to guarantee the money-number rendering rule", "Fallback"],
    ]},
    {"t": "callout", "kind": "ASSUMPTION", "title": "Open decision.",
     "text": "The typeface is a recommendation, not a locked decision. Licence terms, "
     "self-hosting feasibility and a real rendering test on low-end Android devices "
     "common in the target market must be confirmed before the type scale is frozen."},

    {"t": "h3", "text": "5.3.2 Type scale"},
    {"t": "table", "head": ["Token", "Size", "Weight", "Line height", "Letter spacing", "Usage"], "widths": [1.1, 0.6, 0.65, 0.85, 0.95, 2.4], "size": 8.3, "rows": [
        ["display-1", "40 / 44px", "700", "1.1", "-0.02em", "Marketing hero, payout-confirmation headline"],
        ["display-2", "32 / 38px", "700", "1.15", "-0.02em", "Ajo balance headline on mobile"],
        ["heading-1", "24 / 32px", "700", "1.2", "-0.01em", "Page title"],
        ["heading-2", "20 / 28px", "700", "1.25", "-0.01em", "Card title, section title"],
        ["heading-3", "16 / 24px", "600", "1.3", "0", "Sub-section, list-group title"],
        ["body-lg", "16 / 26px", "400", "1.5", "0", "Primary reading size, form input text"],
        ["body", "15 / 23px", "400", "1.5", "0", "Default body copy"],
        ["body-sm", "13 / 20px", "400", "1.45", "0", "Table cells, helper text"],
        ["label", "13 / 18px", "600", "1.3", "0.01em", "Form labels, table headers"],
        ["caption", "12 / 17px", "400", "1.4", "0.01em", "Timestamps, footnotes, legal text"],
        ["money-lg", "28 / 34px", "700", "1.1", "-0.01em", "Payout amount, Ajo pot — tabular figures"],
        ["money-md", "20 / 26px", "600", "1.2", "0", "Contribution amount, schedule cell"],
        ["money-sm", "15 / 21px", "600", "1.2", "0", "Transaction-list amount, table money column"],
    ]},
    {"t": "bullets", "items": [
        "**Tabular figures are mandatory** for every money token. `font-variant-numeric: "
        "tabular-nums` on web, `fontVariant: ['tabular-nums']` on native. Without this, "
        "amounts in a column will not align and a NGN 9.00 can read as NGN 8.00.",
        "Never set a money figure in a weight lighter than 600 — thin numerals disappear "
        "on a phone screen in daylight.",
        "Never abbreviate a money figure. NGN 1,000,000.00 is written in full, with "
        "separators. A member checking a statement must never be asked to do arithmetic.",
    ]},

    {"t": "h2", "text": "5.4 Spacing scale"},
    {"t": "p", "text": "4pt base. Every gap in the product is a multiple of 4."},
    {"t": "table", "head": ["Token", "Value", "Typical use"], "widths": [1.1, 0.8, 4.6], "size": 8.4, "rows": [
        ["space-0", "0", "Reset"],
        ["space-1", "4px", "Icon to label, badge padding-y"],
        ["space-2", "8px", "Chip padding, tight label gap"],
        ["space-3", "12px", "List item internal gap, input label to field"],
        ["space-4", "16px", "Default card padding (mobile), button icon gap"],
        ["space-5", "20px", "Card padding (desktop), field gap in a form"],
        ["space-6", "24px", "Card internal section separation"],
        ["space-8", "32px", "Between cards in a list"],
        ["space-10", "40px", "Between page sections"],
        ["space-12", "48px", "Page top padding, hero padding-y"],
        ["space-16", "64px", "Marketing section padding-y"],
        ["space-20", "80px", "Marketing hero padding-y"],
    ]},
    {"t": "p", "text": "Section rhythm inside the document follows the same logic: "
     "h1 space-before 20px, h2 15px, h3 11px, body space-after 7px."},

    {"t": "h2", "text": "5.5 Border radius"},
    {"t": "table", "head": ["Token", "Value", "Use"], "widths": [1.2, 0.9, 4.4], "size": 8.4, "rows": [
        ["radius-sm", "6px", "Badges, chips, small pills, input on dense tables"],
        ["radius-md", "10px", "Buttons, inputs, selects, menu items"],
        ["radius-lg", "14px", "Cards, panels, modals on mobile"],
        ["radius-xl", "20px", "Bottom sheets, large feature cards"],
        ["radius-full", "9999px", "Avatar, status dot, progress ring, circular icon button"],
    ]},

    {"t": "h2", "text": "5.6 Elevation"},
    {"t": "table", "head": ["Token", "Shadow", "Use"], "widths": [1.2, 2.5, 2.8], "size": 8.4, "rows": [
        ["shadow-none", "none", "Flat surface, table rows"],
        ["shadow-xs", "0 1px 2px rgba(16,24,40,0.05)", "Resting card"],
        ["shadow-sm", "0 1px 3px rgba(16,24,40,0.10), 0 1px 2px rgba(16,24,40,0.06)", "Raised card, sticky header"],
        ["shadow-md", "0 4px 8px rgba(16,24,40,0.10), 0 2px 4px rgba(16,24,40,0.06)", "Dropdown, popover, hovered card"],
        ["shadow-lg", "0 12px 16px rgba(16,24,40,0.14), 0 4px 6px rgba(16,24,40,0.08)", "Modal, drawer"],
        ["shadow-focus", "0 0 0 3px rgba(20,110,245,0.30)", "Focus ring on any focusable element"],
    ]},

    {"t": "h2", "text": "5.7 Layout, containers and breakpoints"},
    {"t": "table", "head": ["Breakpoint", "Min width", "Container", "Columns", "Gutter", "Margin"], "widths": [1.2, 1.0, 1.1, 0.8, 0.8, 1.6], "size": 8.4, "rows": [
        ["xs", "0px", "fluid", "4", "16px", "16px"],
        ["sm", "480px", "fluid", "4", "16px", "16px"],
        ["md", "768px", "fluid", "8", "20px", "24px"],
        ["lg", "1024px", "960px", "12", "24px", "32px"],
        ["xl", "1280px", "1120px", "12", "24px", "auto centre"],
        ["2xl", "1536px", "1200px", "12", "24px", "auto centre"],
    ]},
    {"t": "table", "head": ["Region", "Mobile", "Tablet", "Desktop"], "widths": [1.6, 1.65, 1.65, 1.6], "size": 8.4, "rows": [
        ["Primary nav", "Bottom bar, 5 items", "Bottom bar, 5 items", "Top bar, horizontal"],
        ["Page padding-x", "16px", "24px", "32px"],
        ["Card grid", "1 column", "2 columns", "3 columns above lg, 2 at md"],
        ["Data table", "Card-per-row list", "Card-per-row list", "Full table with sticky header"],
        ["Primary CTA", "Full-width, bottom-anchored", "Inline, right-aligned", "Inline, right-aligned"],
        ["Form field width", "100%", "100% to 420px", "100% to 480px"],
        ["Modal", "Bottom sheet, 90vh", "Centred dialog", "Centred dialog, max 640px"],
    ]},

    {"t": "h2", "text": "5.8 Component specifications"},
    {"t": "p", "text": "Anatomy and variants for every component. Deviation requires a "
     "design-system review; the point of this section is that a developer should not "
     "have to invent a button."},

    {"t": "h3", "text": "Button"},
    {"t": "kv", "pairs": [
        ("Anatomy", "Container, optional leading icon, label, optional trailing icon, optional progress spinner replacing the label during submit"),
        ("Variants", "Primary (action-primary fill), Secondary (white fill, Primary border), Tertiary (no fill, Primary text), Danger (danger fill), Ghost (transparent, hover fill), Link (text only)"),
        ("Sizes", "sm 32px/12px text, md 40px/14px, lg 48px/16px. Mobile primary CTAs are always lg"),
        ("States", "Default, hover, active/pressed, focus-visible, disabled, loading, destructive-confirm"),
        ("Rules", "Exactly one Primary per view. Never two primaries side by side. Never a tertiary where a primary belongs. Disabled state must still be readable at 4.5:1, not greyed to illegibility"),
        ("Do not use", "As a decorative element, as a navigation link, or in a form where the label implies an action other than the one it performs"),
    ]},

    {"t": "h3", "text": "Input"},
    {"t": "kv", "pairs": [
        ("Anatomy", "Label, optional required marker, input, optional leading icon, optional prefix/suffix, helper text, error text, character counter where applicable"),
        ("Variants", "Default, with leading icon, with prefix, with suffix, search, OTP/code, amount-with-keypad (mobile)"),
        ("Sizes", "sm 36px, md 44px, lg 52px. All touch targets minimum 44x44px"),
        ("States", "Default, focus, filled, error, disabled, read-only, loading (verification in progress)"),
        ("Rules", "Label is always visible above the field — never a placeholder used as a label. Error text sits below the field, is announced to assistive technology, and names the fix, not just the problem. Autofill must be supported"),
        ("Do not use", "Disabled as a way of hiding a permission the user lacks; explain the requirement instead"),
    ]},

    {"t": "h3", "text": "Select, Checkbox, Radio, Switch"},
    {"t": "table", "head": ["Component", "Use when", "Key rules"], "widths": [1.3, 1.9, 3.3], "size": 8.4, "rows": [
        ["Select", "7 or more options, or options needing explanation", "Native picker on mobile. Never for yes/no"],
        ["Checkbox", "Multi-select, consent, 'I agree to the Ajo rules'", "Consent checkbox must accompany an inline link to the rules; a pre-ticked consent box is unlawful and prohibited"],
        ["Radio", "2–6 mutually exclusive options that should all be visible", "Default choice is never pre-selected where it implies a financial commitment"],
        ["Switch", "A setting that takes effect immediately", "Never for an action requiring a submit. A switch must state what changed after it flips"],
    ]},

    {"t": "h3", "text": "Card"},
    {"t": "kv", "pairs": [
        ("Anatomy", "Header (title + optional action), body, optional footer (meta or primary CTA)"),
        ("Variants", "Default (white, shadow-xs, radius-lg, 16–20px padding), interactive (hover lift + border-strong), selected (Primary 2px border), Ajo card (adds status pill + progress ring)"),
        ("Rules", "One card expresses one idea. An Ajo card shows: Ajo name, status pill, your position, contribution amount, next due date, progress ring of rounds complete. It must not show four competing buttons"),
        ("Do not use", "Nesting cards inside cards, or a full-bleed clickable card containing its own button"),
    ]},

    {"t": "h3", "text": "Status pill and badge"},
    {"t": "table", "head": ["Status", "Colour", "Icon (required)", "Never used alone as the only signal"], "widths": [1.6, 1.5, 1.5, 1.9], "size": 8.4, "rows": [
        ["DRAFT / Enrollment open", "info / info-bg", "Clock", "—"],
        ["ACTIVE", "success / success-bg", "Check", "—"],
        ["Round in progress", "Primary / info-bg", "Refresh", "—"],
        ["Payout imminent", "Gold fill, Dark text", "Star", "Gold text on white"],
        ["Payout held", "warning / warning-bg", "Pause", "—"],
        ["Overdue", "warning / warning-bg", "Alert triangle", "—"],
        ["Defaulted", "danger / danger-bg", "Alert octagon", "—"],
        ["Cancelled / Completed", "secondary / Cloud", "Flag / Check-double", "—"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Non-negotiable:",
     "text": "Every status is carried by colour **and** an icon **and** a text label. "
     "Colour alone fails roughly 1 in 12 men and is the single most common accessibility "
     "defect in financial dashboards."},

    {"t": "h3", "text": "Modal, drawer and bottom sheet"},
    {"t": "table", "head": ["Surface", "Use for", "Rules"], "widths": [1.3, 1.9, 3.3], "size": 8.4, "rows": [
        ["Modal", "Confirmation of a consequential action; short focused form", "Focus trapped, Escape closes, background inert, labelled by its heading. Never for a multi-step task"],
        ["Drawer", "Filtering, secondary detail that must not lose list context", "Desktop right-side, mobile full-height. Never for a destructive confirm"],
        ["Bottom sheet", "Mobile equivalent of modal", "Drag handle, max 90vh, backdrop tap dismisses, respects safe-area insets"],
    ]},

    {"t": "h3", "text": "Data table"},
    {"t": "kv", "pairs": [
        ("Anatomy", "Sticky header row, sortable column headers, money column right-aligned with tabular figures, status column with pill, row actions, pagination or infinite scroll, empty and loading states"),
        ("Rules", "Money right-aligned, always. Dates in a single consistent format, ISO-derived display. Member names left-aligned. Action column last and right-aligned. Row height 56px minimum for touch"),
        ("Do not use", "Horizontal scroll on mobile — switch to the card-per-row pattern below 768px"),
    ]},

    {"t": "h3", "text": "Progress ring and progress bar"},
    {"t": "kv", "pairs": [
        ("Ring", "Ajo completion, 3–10 rounds, shown in the Ajo card and on Ajo detail"),
        ("Bar", "Contribution collection within a round — paid members of total, e.g. 7 of 10"),
        ("Rules", "Always accompanied by the literal count ('7 of 10 members paid'). Cyan-to-Primary gradient is permitted; Gold reserved for a position the member holds. Never a bare ring with no figure"),
    ]},

    {"t": "h3", "text": "Empty, loading, error, success states"},
    {"t": "table", "head": ["State", "Pattern", "Must include"], "widths": [1.2, 2.2, 3.1], "size": 8.4, "rows": [
        ["Loading (fast, <300ms)", "Nothing — avoid flash", "No spinner for sub-300ms responses"],
        ["Loading (slow)", "Skeleton matching final layout", "Shape must match content to avoid layout shift"],
        ["Loading (payment)", "Indeterminate bar with explicit wording", "'Confirming your payment — do not close this page'"],
        ["Empty (first use)", "Illustration + one sentence + one action", "Explain what will appear here and how to create the first one"],
        ["Empty (filtered)", "Icon + 'No results' + clear-filter action", "Name the filter that produced nothing"],
        ["Error (recoverable)", "Inline, adjacent to the field or block", "State what happened and what the user can do next"],
        ["Error (system)", "Full-panel with a request ID", "Request ID is copyable so support can trace it"],
        ["Success", "Toast for background completion; inline confirmation for a screen transition", "Never a modal success for a background action"],
    ]},

    {"t": "h2", "text": "5.9 The money component — non-negotiable rules"},
    {"t": "p", "text": "Every amount in AJO.ng is rendered by one component. These rules "
     "exist because a misread figure is the fastest way to destroy member trust."},
    {"t": "numbers", "items": [
        "Tabular numerals always. Amounts in a column align on the decimal point.",
        "Currency is always explicit: NGN prefix on the first occurrence, permitted omission on subsequent lines of the same breakdown where the header establishes it.",
        "Full precision. NGN 1,000.00 never renders as '1k' or '1,000'.",
        "Sign and direction are stated in words where ambiguity is possible: 'You pay NGN 1,020.00' beats a bare figure.",
        "The 2% platform fee is ALWAYS a separate line. It is never merged into the contribution, never shown as a percentage alone without the resulting naira amount, and never netted silently into a payout.",
        "The recipient's payout is always the base pool. A payout screen must never imply the recipient receives more than the agreed pool because of the fee.",
    ]},
    {"t": "code", "size": 8.2, "text": """
  PAY NGN 1,020.00 FOR THIS ROUND
  ─────────────────────────────────────────────
  Contribution                     NGN 1,000.00
  Platform fee (2%)                  NGN  20.00
  ─────────────────────────────────────────────
  Total to be charged              NGN 1,020.00

  The recipient receives NGN 10,000.00 — the agreed
  pool. The fee is AJO.ng's and does not change it.
"""},
    {"t": "p", "text": "Where members are configured to pay the fee, the wording is "
     "fixed as: *'NGN 1,000.00 contribution + 2% platform fee (NGN 20.00) = NGN 1,020.00 "
     "charged today.'* This is tested copy and is covered by the acceptance criteria for "
     "the payment screen."},

    {"t": "h2", "text": "5.10 Form patterns"},
    {"t": "bullets", "items": [
        "Validate on blur, re-validate on change once a field has errored, and on submit validate everything again.",
        "Server-side errors map to the field when possible; unmapable errors surface as a form-level banner above the submit button, not as a toast.",
        "Never clear a field on validation failure. Never reset a multi-step wizard when one step fails.",
        "The Create Ajo wizard persists every completed step so a dropped connection loses nothing.",
        "Irreversible steps show a summary confirmation naming the exact figures, including the fee.",
    ]},

    {"t": "h2", "text": "5.11 Motion"},
    {"t": "table", "head": ["Interaction", "Duration", "Easing", "Notes"], "widths": [1.7, 1.0, 1.2, 2.6], "size": 8.4, "rows": [
        ["Hover / press feedback", "100–150ms", "ease-out", "Colour and transform only"],
        ["Card lift", "150ms", "ease-out", "Max 2px translate, never a scale > 1.01"],
        ["Sheet / modal enter", "200ms", "cubic-bezier(0.16, 1, 0.3, 1)", "Slide from edge"],
        ["Toast in / out", "150 / 200ms", "ease-out", "Auto-dismiss 5s, pause on hover"],
        ["Progress ring fill", "600ms", "ease-in-out", "Rounds completed"],
        ["Payment processing", "indeterminate, ≤ 15s then fail visibly", "linear", "Must never spin indefinitely"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Reduced motion:",
     "text": "Under `prefers-reduced-motion: reduce`, all transforms and non-essential "
     "animation are removed; state changes become instant opacity swaps of no more than "
     "100ms. No information is ever conveyed by motion alone."},

    {"t": "h2", "text": "5.12 Accessibility in the design system"},
    {"t": "bullets", "items": [
        "**Contrast** — 4.5:1 for body text, 3:1 for large text and UI component boundaries. Cyan and Gold are excluded from text use by design (5.2).",
        "**Focus** — every interactive element shows `shadow-focus` on keyboard focus. Focus is never removed, only restyled. Skip-to-content link is the first tab stop.",
        "**Targets** — minimum 44x44px on mobile, 24x24px with spacing on desktop. Primary mobile CTAs are 48px.",
        "**Screen readers** — every icon-only control has an accessible name. Status pills expose their text label. Money components expose the full value, not a truncated visual.",
        "**Structure** — one H1 per view, no skipped heading levels, tables with real `<th scope>` and caption.",
        "**Zoom** — layout survives 200% zoom and 320px width without horizontal scroll.",
        "**Errors** — error text linked to its input via `aria-describedby`; form errors announced in a live region.",
        "Target is WCAG 2.2 AA. This is a target requiring verification by a human accessibility test with assistive technology, not a claim of conformance.",
    ]},

    {"t": "h2", "text": "5.13 Web-to-mobile component mapping"},
    {"t": "table", "head": ["Web component", "Mobile equivalent", "Differences"], "widths": [1.6, 1.7, 3.2], "size": 8.4, "rows": [
        ["Top navigation bar", "Top app bar + bottom navigation", "Bottom bar shows 5 destinations; back is a system gesture"],
        ["Data table", "Card-per-row list", "Each card is one row; metadata moves to a secondary line"],
        ["Select (dropdown)", "Native picker wheel / modal list", "Never a custom dropdown — native is faster and accessible"],
        ["Text input", "Text input or numeric keypad", "Amount fields use `inputMode=\"decimal\"`, not a bespoke keypad that breaks the OS keyboard"],
        ["Modal", "Bottom sheet", "Full-width, 90vh max, safe-area padding"],
        ["Toast", "In-app banner below the app bar", "Android SnackBar behaviour; never obscures the primary CTA"],
        ["Tooltip", "Long-press hint or inline helper", "Hover does not exist on touch"],
        ["Hover-revealed row actions", "Always-visible swipe or inline action", "No hover-only affordance is ever shipped"],
        ["Date picker", "Native date picker", "Contribution day is a weekday, not a free date"],
    ]},

    {"t": "h2", "text": "5.14 Token delivery"},
    {"t": "p", "text": "One source of truth per platform, generated from a single token "
     "file so a brand change propagates. Values shown here are the resolved design-system "
     "values, not the build tooling."},
    {"t": "code", "size": 8.0, "text": """
/* Web — CSS custom properties */
:root {
  /* brand */
  --ajo-deep:     #0B1F3A;
  --ajo-primary:  #146EF5;
  --ajo-cyan:     #22C7D6;
  --ajo-gold:     #FBBF24;
  --ajo-white:    #FFFFFF;
  --ajo-cloud:    #F4F7FB;
  --ajo-dark:     #101828;

  /* semantic */
  --bg-canvas:            var(--ajo-cloud);
  --bg-surface:           var(--ajo-white);
  --bg-inverse:           var(--ajo-deep);
  --border-default:       #D0D5DD;
  --text-primary:         var(--ajo-dark);
  --text-secondary:       #475467;
  --action-primary:       var(--ajo-primary);
  --success:              #12B76A;
  --warning:              #DC6803;
  --danger:               #D92D20;
  --money-positive:       #12B76A;
  --money-negative:       #D92D20;
  --money-pending:        #DC6803;
  --money-fee:            #146EF5;

  /* spacing (4pt base) */
  --space-1:  4px;  --space-2:  8px;  --space-3: 12px;
  --space-4: 16px;  --space-5: 20px;  --space-6: 24px;
  --space-8: 32px;  --space-10:40px;  --space-12:48px;

  /* money display */
  --font-money: 600 15px/1.2 Inter, system-ui, sans-serif;
  --font-money-lg: 700 28px/1.1 Inter, system-ui, sans-serif;
  --font-money-numeric: tabular-nums;
}
.money     { font-variant-numeric: tabular-nums; }
.money--lg { font: var(--font-money-lg); font-variant-numeric: tabular-nums; }
"""},
    {"t": "code", "size": 8.0, "text": """
// Mobile — React Native theme object
export const theme = {
  color: {
    brand: {
      deep: '#0B1F3A', primary: '#146EF5', cyan: '#22C7D6',
      gold: '#FBBF24', white: '#FFFFFF', cloud: '#F4F7FB',
      dark: '#101828',
    },
    bg:     { canvas: '#F4F7FB', surface: '#FFFFFF', inverse: '#0B1F3A' },
    text:   { primary: '#101828', secondary: '#475467', inverse: '#FFFFFF' },
    border: { default: '#D0D5DD', strong: '#98A2B3' },
    action:{ primary: '#146EF5', primaryHover: '#0F5AD0', danger: '#D92D20' },
    status:{ success: '#12B76A', warning: '#DC6803', danger: '#D92D20',
             info: '#146EF5', pending: '#DC6803' },
    money: { positive: '#12B76A', negative: '#D92D20',
             pending: '#DC6803', fee: '#146EF5' },
  },
  space: { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24,
           8: 32, 10: 40, 12: 48 },
  radius:{ sm: 6, md: 10, lg: 14, xl: 20, full: 9999 },
  type: {
    moneySm:   { fontSize: 15, lineHeight: 21, fontWeight: '600' },
    moneyMd:   { fontSize: 20, lineHeight: 26, fontWeight: '600' },
    moneyLg:   { fontSize: 28, lineHeight: 34, fontWeight: '700' },
    body:      { fontSize: 15, lineHeight: 23, fontWeight: '400' },
    bodySm:    { fontSize: 13, lineHeight: 20, fontWeight: '400' },
    label:     { fontSize: 13, lineHeight: 18, fontWeight: '600' },
    caption:   { fontSize: 12, lineHeight: 17, fontWeight: '400' },
  },
  // MANDATORY for every amount rendered. Without it, columns
  // do not align and NGN 9.00 can read as NGN 8.00.
  moneyFontVariant: ['tabular-nums'] as const,
} as const;

export type Theme = typeof theme;
"""},

    {"t": "h2", "text": "5.15 Contribution and governance"},
    {"t": "table", "head": ["Rule", "Detail"], "widths": [1.8, 4.7], "size": 8.4, "rows": [
        ["Single source", "One token file. Web and mobile artefacts are generated, never hand-maintained."],
        ["No new colours", "A new colour requires design and engineering review with an accessibility check. The palette is closed by default."],
        ["Component lifecycle", "Proposed → In review → Stable → Deprecated. Deprecated components ship a codemod and a removal date."],
        ["Definition of done", "Figma spec, tokens, both platform implementations, Storybook/Expo story, unit test, and an accessibility note."],
        ["Enforcement", "Lint rules block raw hex values in component code; only semantic tokens may be referenced."],
        ["Versioning", "Design tokens are semver'd. A breaking token rename is a major version and requires a migration note."],
    ]},
    {"t": "callout", "kind": "DECISION", "title": "Typeface and dark mode remain open.",
     "text": "The typeface (5.3.1) and the decision on whether dark mode is in MVP are "
     "both explicitly deferred. Dark mode is proposed for post-MVP; committing to it now "
     "would double the design and QA surface before a single member has used the product."},
]
