"""Section 17 — Mobile Experience and Platform Strategy."""

BLOCKS = [
    {"t": "h1", "text": "17. Mobile Experience and Platform Strategy"},

    {"t": "lead", "text": "Most AJO.ng members will meet this product on an Android "
     "phone, on a metered mobile data connection, on a device that may be several years "
     "old and shared with a family member. That is not a constraint to apologise for. It "
     "is the design brief. Every decision in this section follows from it."},

    {"t": "h2", "text": "17.1 Platform strategy"},
    {"t": "h3", "text": "17.1.1 Why React Native and Expo"},
    {"t": "table", "head": ["Decision", "Rationale", "Trade-off accepted"], "widths": [1.6, 2.7, 2.2], "size": 8.2, "rows": [
        ["React Native + Expo", "One JavaScript/TypeScript codebase across Android and iOS, with access to native modules where biometrics and secure storage matter", "Slightly less platform-native polish than a fully native build"],
        ["Expo managed workflow", "Faster iteration, OTA updates without an app-store cycle, built-in handling of deep links and push notification setup", "Constrained by the Expo SDK; escape to a custom native build remains possible"],
        ["TypeScript end to end", "The domain core is shared with the backend, so a money rule cannot drift between client and server", "Requires discipline to keep the shared core pure"],
        ["Offline-first with a local cache", "Members lose signal constantly. Ajo status must remain visible without a network", "Conflict resolution must be designed deliberately, not improvised"],
    ]},
    {"t": "p", "text": "A native Android build (Kotlin) is a credible alternative for a "
     "team strong in Android specifically, and may be worth revisiting once product-market "
     "fit is established and the payment and identity integrations are settled. It should "
     "not be the starting point for a small team that needs to reach both platforms."},

    {"t": "h2", "text": "17.2 Design principles for this market"},
    {"t": "numbers", "items": [
        "**Thumb-reachable and one-handed.** The primary actions sit in the lower third of the screen. A member paying a contribution should not need to reach the top of a large phone.",
        "**Low-bandwidth by default.** Small payloads, aggressive caching, compressed images, and no video. The app must be usable on a poor connection, because a poor connection is normal.",
        "**Legible at arm's length.** Large tap targets (minimum 44×44pt), generous type, and high contrast. Members may be older, may be outdoors, and may have imperfect eyesight.",
        "**Forgiving, not silent.** Every destructive action is confirmed, every failure explains what happened and what to do, and no action is irreversible without a deliberate confirmation.",
        "**Optimised for low-end hardware.** Tested on a genuinely old device, not just a simulator. A 2018-class Android phone is the performance floor.",
        "**Data-conscious.** No autoplaying video, no aggressive background polling, and a visible data-saving mode.",
        "**Bilingual from the start, English-first.** Nigerian Pidgin and Hausa are the two languages with the largest immediate reach among the target users. **Professional translation is required before broad launch** — machine-translated financial instructions are a harm, not a convenience.",
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Localisation is a trust feature.",
     "text": "A member who reads a payment instruction in Hausa and understands every word "
     "trusts the platform more than one who is translating English in their head. This is "
     "not a marketing nicety for a product handling people's savings — it is a "
     "correctness issue, and a mistranslated fee disclosure is a real financial harm."},

    {"t": "h2", "text": "17.3 Information architecture"},
    {"t": "code", "size": 7.8, "text": """
  Home
   ├─ Next contribution (the single most important card)
   ├─ Active Ajos ──────────► Ajo detail
   │                              ├─ Position & progress
   │                              ├─ Contribute
   │                              ├─ Rounds
   │                              ├─ Members
   │                              ├─ Messages
   │                              └─ Rules
   ├─ Payouts (incoming) ────► Payout detail ──► Receipt
   └─ Activity ──────────────► All events, filterable

  Bottom tab bar
   [ Home ]   [ Ajos ]   [ Add (+) ]   [ Activity ]   [ Profile ]

  Add (+)
   ├─ Start an Ajo
   ├─ Join with an invite code
   └─ Pay a pending contribution

  Profile
   ├─ Identity & verification
   ├─ Bank accounts
   ├─ Notifications
   ├─ Security
   ├─ Statements & history
   ├─ Disputes
   └─ Help
"""},
    {"t": "p", "text": "Five tabs is the maximum a member can hold in their head. The "
     "centre `+` is the primary action in the product — starting or joining an Ajo, or "
     "paying what is due — and it is reachable with either thumb."},

    {"t": "h2", "text": "17.4 Key screens"},
    {"t": "h3", "text": "17.4.1 Home"},
    {"t": "bullets", "items": [
        "**Greeting and trust signal** — 'Good morning, Amaka'. No guilt-inducing language about money owed, ever.",
        "**Primary card — what needs your attention.** If a contribution is due, this card leads. If a payout arrived, it leads. If nothing needs attention, it says so plainly and shows the next event.",
        "**Active Ajos strip** — one card per Ajo: name, your position, round progress, and next due date.",
        "**Recent activity** — the last few events, with amounts.",
        "**No clutter.** No promotional banner above a payment requirement. Marketing occupies its own space and never displaces a money action.",
    ]},
    {"t": "h3", "text": "17.4.2 Contribute"},
    {"t": "bullets", "items": [
        "A clear, itemised breakdown: **NGN 1,000.00 contribution + NGN 20.00 service fee = NGN 1,020.00 total.** The fee is shown as a separate line, not buried in a total.",
        "Payment rails presented as tappable options with their own icons and any fee or delay implication stated.",
        "A progress indicator during payment, with a clear 'do not close the app' cue and a real fallback if the member does.",
        "A receipt screen on success with a reference number, and the position status updated to funded.",
        "Failure states that say what happened, whether money moved, and what to do next.",
    ]},
    {"t": "h3", "text": "17.4.3 Ajo detail"},
    {"t": "bullets", "items": [
        "Your position, the pool total, the round progress bar, and the next due date in the Ajo's timezone with your local time beneath it.",
        "A members list showing first name, avatar, and contribution status — never bank details, never a phone number, and never a public 'defaulted' label.",
        "The Ajo rules, always accessible, in plain language.",
        "The organizer shown by name with a verified badge, and a 'Report' action that is present without being accusatory.",
    ]},
    {"t": "h3", "text": "17.4.4 Payout received"},
    {"t": "p", "text": "The most important screen in the product, and the one most often "
     "under-designed. It celebrates without being embarrassing, and it explains."},
    {"t": "bullets", "items": [
        "Amount received, large and unambiguous.",
        "Destination: bank name and last four digits.",
        "A breakdown of the cycle: rounds, contributions made, total fees paid, amount received.",
        "Time sent, and what to do if it has not arrived — a link to a clear 'where is my money' explainer.",
        "Confirmation of what the member has achieved, in one line. A simple, dignified acknowledgement beats confetti.",
    ]},
    {"t": "h3", "text": "17.4.5 Empty states"},
    {"t": "p", "text": "An empty state is a teaching moment and a conversion opportunity. "
     "'No Ajos yet' explains what an Ajo is, in two sentences, and offers one obvious next "
     "action. A blank screen with 'No data' is a failure, not a design."},

    {"t": "h2", "text": "17.5 Offline behaviour"},
    {"t": "p", "text": "Connectivity in the target market is intermittent, and the app must "
     "degrade honestly rather than pretend."},
    {"t": "table", "head": ["Situation", "Behaviour"], "widths": [1.7, 4.8], "size": 8.4, "rows": [
        ["Viewing an Ajo", "Fully available from cache. Clearly marked as last updated, with the timestamp"],
        ["Viewing a position", "Fully available from cache. Never a wrong figure — the cache is written only after a server-confirmed update"],
        ["Starting a payment", "Requires a network connection. The app says so plainly and preserves everything the member has entered"],
        ["Viewing a receipt", "Available from cache once downloaded"],
        ["Any action that moves money", "Online only. Never queued offline and fired later — a surprise payment is unacceptable"],
        ["Cache staleness", "Beyond 24 hours, the app shows a clear 'connect to refresh' state rather than quietly showing old data"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "Never queue a payment for later.",
     "text": "A member who taps 'pay' on a train, loses signal, and has the payment execute "
     "hours later from a café wifi is a member who will never trust the product with money "
     "again. Offline capability is read-only. This is a hard architectural boundary, not a "
     "feature backlog item."},

    {"t": "h2", "text": "17.6 Performance budgets"},
    {"t": "table", "head": ["Metric", "Target", "Method"], "widths": [1.8, 1.4, 3.3], "size": 8.4, "rows": [
        ["Cold start to interactive", "< 2.5s on a mid-range Android", "Measured on a physical device"],
        ["Screen transition", "< 300ms", "Perceived, using the native driver"],
        ["API response (p95)", "< 400ms", "Server-side, excluding third-party payment calls"],
        ["Bundle size", "< 25 MB", "Gzipped, per platform"],
        ["Image payload", "< 300 KB per screen", "Compressed, cached aggressively"],
        ["Battery drain", "Negligible over 8 hours of typical use", "Background work batched and scheduled"],
        ["Memory", "< 250 MB peak", "No unbounded caches"],
        ["Frame rate", "60fps target, never below 30fps", "On a low-end device, not a simulator"],
        ["Crash-free sessions", "> 99.5%", "Session stability is a trust signal"],
        ["ANR rate", "< 0.1%", "Android-specific stability measure"],
    ]},

    {"t": "h2", "text": "17.7 Accessibility"},
    {"t": "bullets", "items": [
        "**Screen reader support on every screen**, including the payment and payout flows. VoiceOver on iOS, TalkBack on Android.",
        "**Dynamic type support** — text scales with the system font size without truncation or overlapping. A financial amount that is cut off is a serious defect.",
        "**Contrast ratios** meet WCAG 2.1 AA. Primary text at minimum 4.5:1; large text at 3:1.",
        "**Colour is never the only signal.** Payment status, contribution status, and risk states each carry a label and an icon, not just a colour. Colour-only signalling excludes a meaningful number of members and is also a common source of accessibility complaints.",
        "**Minimum 44×44pt tap targets**, with adequate spacing to prevent mis-taps on a payment button.",
        "**Reduced motion respected** — no animation for someone who has asked for less of it.",
        "**Focus order follows visual order**, and error messages are announced to screen readers on submission.",
        "**Plain language at a reading level a non-technical Nigerian adult can follow.** Jargon is a defect, not a register.",
    ]},

    {"t": "h2", "text": "17.8 Security on device"},
    {"t": "bullets", "items": [
        "**Biometric unlock** — Face ID or fingerprint, with device PIN as fallback. A convenience and a protection on a shared phone.",
        "**No sensitive data in logs on device.** The app must not log balances, bank details, or BVN, even in debug builds on a developer's device.",
        "**Screenshot and screen-recording protection** on the balance, bank-account, and BVN screens, where the OS allows it.",
        "**App-level data protection** — stored credentials in the platform keystore, and cached financial data encrypted at rest on device with a key held in the keystore.",
        "**No sensitive data in the clipboard**, or if copied, expired automatically.",
        "**Root and jailbreak detection** as a risk signal feeding the risk engine, not as an automatic block. A legitimate member with a rooted phone should still be able to save money.",
        "**Root cause of a wipe is not a remote wipe.** A member who loses a stolen phone should not lose their Ajo history; server-side data survives device loss, and the app is re-authenticated on the new device.",
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Losing a phone is not losing your Ajo.",
     "text": "A member's Ajo position, contribution history, and payout record live on the "
     "server, not on the device. A lost or stolen phone means a new login, not a lost "
     "savings. Saying so explicitly in the recovery flow is important — the fear of losing "
     "years of savings to a stolen phone is a genuine barrier to adoption in this market."},

    {"t": "h2", "text": "17.9 App lifecycle and distribution"},
    {"t": "bullets", "items": [
        "**Minimum OS versions** — Android 8.0 (API 26) and iOS 14. This keeps the install base broad while allowing current security and cryptography features.",
        "**Over-the-air updates** for JavaScript and assets, with a forced-update path for a critical security fix.",
        "**Staged rollout** with an internal ring, then 1%, 5%, 25%, 50%, 100%, with automatic halt on a crash-rate or ANR breach.",
        "**Deep linking** so an SMS or a shared invitation opens the correct screen, with a graceful fallback to the app store if the app is not installed.",
        "**App store compliance** — privacy nutrition labels, a data-safety declaration that matches what the app actually does, and a data-deletion request path where the store requires one.",
        "**Download size discipline.** A large app is a real adoption barrier on metered data. Feature additions must be justified against bundle growth.",
    ]},

    {"t": "h2", "text": "17.10 Platform-agnostic product rules"},
    {"t": "p", "text": "Whatever the client technology, these rules hold. They are written "
     "here so that a future native rebuild, a WhatsApp channel, or a USSD fallback does not "
     "quietly break the product's commitments."},
    {"t": "numbers", "items": [
        "The server is authoritative for every financial figure. No client computes a balance.",
        "The 2% fee is shown as a separate line before every payment, in every channel.",
        "A contribution is not confirmed until the server confirms it. The client may not optimistically claim success.",
        "Deadlines are shown in the Ajo's timezone, with the member's local time alongside.",
        "No money moves through a messaging channel, ever.",
        "A member can always see the full history of their own transactions and receipts.",
        "Every state in the money lifecycle is visible to the member, including the uncomfortable ones.",
    ]},

    {"t": "h2", "text": "17.11 Mobile metrics"},
    {"t": "table", "head": ["Metric", "Definition", "Target"], "widths": [2.0, 3.0, 1.5], "size": 8.4, "rows": [
        ["Install → verified account", "Share of installs completing identity verification", "> 55%"],
        ["Install → first Ajo joined", "Share of installs completing a join", "> 40%"],
        ["Onboarding completion", "Share who finish the flow", "> 70%"],
        ["Contribution conversion", "Share who complete a payment once started", "> 85%"],
        ["Payment completion time", "Start to confirmation", "< 45s"],
        ["D30 retention", "Members active after 30 days", "> 45%"],
        ["Crash-free rate", "Sessions without a crash", "> 99.5%"],
        ["App load time (p75)", "Cold start", "< 2.5s"],
        ["Rating", "App store rating", "> 4.3"],
    ]},
]
