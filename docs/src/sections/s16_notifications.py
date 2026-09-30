"""Section 16 — Notifications and Messaging."""

BLOCKS = [
    {"t": "h1", "text": "16. Notifications and Messaging"},

    {"t": "lead", "text": "An Ajo is a schedule that other people depend on. The "
     "notification system is not a convenience feature — it is the mechanism by which "
     "members know when money is due, when money has arrived, and when something has gone "
     "wrong. If notifications fail, the product fails, because people stop trusting it."},

    {"t": "h2", "text": "16.1 Principles"},
    {"t": "numbers", "items": [
        "**Every money event is notified, in every channel the member has enabled.** No exceptions, no opt-out for financial events.",
        "**In-app is the source of truth; push, email, and SMS are delivery mechanisms.** A member who misses a push still sees the event in the app.",
        "**Urgent, actionable, and informational are different things.** They have different channels, different cadences, and different escalation rules.",
        "**Never notify in a way that leaks sensitive financial information.** A lock-screen notification saying 'You were paid NGN 10,000' is a privacy problem on a shared phone.",
        "**Send money information, not personal information.** Amounts and events are safe; balances, bank details, and BVN never appear in a notification.",
        "**Preference-respecting, with one hard exception.** Members choose channels and quiet hours for non-essential categories. Money events ignore quiet hours.",
    ]},
    {"t": "callout", "kind": "WARNING", "title": "Financial notifications cannot be opted out of.",
     "text": "Opting out of a payment notification is a design mistake with real "
     "consequences: a member who misses 'your contribution is due' defaults, which harms "
     "the whole group. Money events are mandatory on at least one channel. Everything else "
     "is a preference."},

    {"t": "h2", "text": "16.2 Channels"},
    {"t": "table", "head": ["Channel", "Strengths", "Limitations", "Used for"], "widths": [1.1, 1.9, 1.9, 1.6], "size": 8.2, "rows": [
        ["In-app", "Always available, rich content, no cost, no third-party dependency", "Requires the app to be opened", "Everything. The canonical record"],
        ["Push (APNs / FCM)", "Fast, low friction, high open rate, works on mobile data", "Requires permission; silent if the app is killed; OS-level throttling", "All money events; reminders; urgent"],
        ["Email", "Rich, linkable, attachable, works on desktop and web", "Slow, often filtered, requires an app check", "Monthly statements; Ajo invitations; security alerts; long-form"],
        ["SMS", "Reaches any phone, no smartphone needed, no app required", "Cost per message, character limits, poor readability, spoofable", "Critical fallback: payment due, payout sent, security"],
        ["WhatsApp Business API", "Where members already are; high engagement; rich media", "Requires opt-in, template approval, per-message cost, 24-hour session window", "Optional enhancement. Not a launch dependency"],
        ["In-app chat", "Direct, asynchronous, recorded", "Moderation burden, harassment risk", "Organizer–member questions within an Ajo"],
    ]},
    {"t": "p", "text": "AJO.ng's launch requirement is in-app plus push, with email and "
     "SMS as fallbacks. WhatsApp integration is valuable and should be built when the "
     "provider approval and cost are known, but it must never be the only channel for a "
     "money event."},

    {"t": "h2", "text": "16.3 Notification taxonomy"},
    {"t": "table", "head": ["Category", "Examples", "Default channels", "Priority"], "widths": [1.4, 2.5, 1.5, 0.9], "size": 8.0, "rows": [
        ["Money received", "Contribution confirmed; payout credited; refund issued", "Push + in-app + email", "Critical"],
        ["Money due", "Contribution due; round closing; last 24 hours", "Push + in-app + SMS", "High"],
        ["Money action needed", "Verification pending; bank-account change; step-up required; dispute outcome", "Push + in-app + email", "High"],
        ["Payout status", "Payout scheduled; payout sent; payout held for review", "Push + in-app + email + SMS", "Critical"],
        ["Ajo lifecycle", "Ajo funded; Ajo completed; Ajo cancelled; new member joined", "Push + in-app", "Medium"],
        ["Default and recovery", "Payment failed; retry scheduled; grace period started; grace period ending", "Push + in-app + SMS", "High"],
        ["Invitation", "Invited to an Ajo; invitation expiring", "Push + email + SMS", "Medium"],
        ["Security", "New device login; password changed; BVN or bank detail updated; token reuse detected", "Push + email + SMS", "Critical"],
        ["Informational", "Round summary; Ajo anniversary; product updates; tips", "In-app + email", "Low"],
        ["Marketing", "Promotions; new features; campaigns", "Email + push", "Low, opt-in"],
    ]},

    {"t": "h2", "text": "16.4 Money event templates"},
    {"t": "p", "text": "Templates are the product. A vague notification causes a support "
     "call; a precise one does not. Every template below is written to be understood on a "
     "first read, by someone who is not thinking about the product."},
    {"t": "h3", "text": "16.4.1 Contribution due"},
    {"t": "table", "head": ["Element", "Content"], "widths": [1.4, 5.1], "size": 8.2, "rows": [
        ["Push title", "Contribution due — {Ajo name}"],
        ["Push body", "Round {n} of {total}. NGN {amount + fee} is due by {date}. Tap to pay."],
        ["SMS", "AJO.ng: Your {Ajo name} contribution of NGN {total} is due by {date}. Pay in the app."],
        ["In-app title", "Round {n} is open until {date}"],
        ["In-app body", "Contribute NGN {amount}. A NGN {fee} service fee applies, so NGN {total} in total. Your position stays funded when this is paid."],
        ["CTA", "Pay now"],
        ["Tone", "Neutral and factual. No guilt, no shaming, no urgency theatre"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Show the total, always.",
     "text": "The contribution screen and the notification both state NGN 1,000 plus a "
     "NGN 20 fee, NGN 1,020 in total. A member who discovers a fee at the payment step "
     "feels ambushed and may abandon, and a member who is surprised later feels "
     "misinformed. Stating the total up front, twice, costs nothing."},

    {"t": "h3", "text": "16.4.2 Contribution confirmed"},
    {"t": "table", "head": ["Element", "Content"], "widths": [1.4, 5.1], "size": 8.2, "rows": [
        ["Push title", "Contribution received"],
        ["Push body", "NGN {total} received for {Ajo name}, round {n}. You are fully funded for this round."],
        ["In-app body", "We received NGN {total} — NGN {amount} to your Ajo pool and a NGN {fee} service fee. Your position is funded for round {n}."],
        ["CTA", "View transaction"],
    ]},

    {"t": "h3", "text": "16.4.3 Payout sent"},
    {"t": "table", "head": ["Element", "Content"], "widths": [1.4, 5.1], "size": 8.2, "rows": [
        ["Push title", "Your Ajo payout is on its way"],
        ["Push body", "NGN {amount} to {bank name} •••• {last4}. Sent {time}. Funds usually arrive within minutes."],
        ["SMS", "AJO.ng: NGN {amount} has been sent to your {bank name} account ending {last4}. It should arrive shortly."],
        ["In-app body", "Round {n} is complete and NGN {amount} has been sent to your bank account. Tap to see the full breakdown of your contributions and fees."],
        ["CTA", "View payout"],
    ]},
    {"t": "p", "text": "The push body shows the bank and the last four digits. That is the "
     "single most useful detail for a member who needs to know *where* their money went, "
     "and masking the rest is a reasonable privacy trade-off on a shared device."},

    {"t": "h3", "text": "16.4.4 Payment failed"},
    {"t": "table", "head": ["Element", "Content"], "widths": [1.4, 5.1], "size": 8.2, "rows": [
        ["Push title", "We couldn't take your payment"],
        ["Push body", "Your NGN {total} payment for {Ajo name} didn't go through. No money has left your account. Try again."],
        ["In-app body", "Your payment of NGN {total} was not completed. Reasons this happens: insufficient funds, a bank decline, or a network interruption. Your position in {Ajo name} is still unpaid for round {n}."],
        ["CTA", "Try again"],
        ["Tone", "Reassuring and precise. Explicitly state that no money was taken — members assume the worst"],
    ]},

    {"t": "h3", "text": "16.4.5 Payout held"},
    {"t": "table", "head": ["Element", "Content"], "widths": [1.4, 5.1], "size": 8.2, "rows": [
        ["Push title", "Your payout needs a quick check"],
        ["Push body", "Your NGN {amount} payout is being reviewed. We'll update you by {time}. Nothing is required from you unless we contact you."],
        ["In-app body", "We're completing a routine check before releasing your NGN {amount} payout from {Ajo name}. This usually takes under {duration}. If we need anything from you, we'll ask here first — we will never ask you to call a number you found in a message."],
        ["CTA", "See what's happening"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "The anti-phishing line belongs here.",
     "text": "Every hold message should state plainly that AJO.ng will not ask for a PIN, a "
     "BVN, or a bank code over chat. This is the moment a member is most receptive to a "
     "follow-up 'call to release your funds' scam, and the highest-value sentence in the "
     "whole notification system is the one that warns them."},

    {"t": "h2", "text": "16.5 Reminder schedule for contributions"},
    {"t": "p", "text": "Reminders are the mechanism that keeps an Ajo on schedule. The "
     "schedule escalates gradually, in proportion to urgency, and always in the same order."},
    {"t": "table", "head": ["When", "Channel", "Content", "To"], "widths": [1.3, 1.5, 2.6, 1.1], "size": 8.2, "rows": [
        ["Round opens", "In-app", "Round is open. Here's your amount and schedule", "Unpaid members"],
        ["T−7 days", "Push", "Contribution due in a week", "Unpaid members"],
        ["T−3 days", "Push + SMS", "Three days to go. NGN {total} due {date}", "Unpaid members"],
        ["T−1 day", "Push + SMS", "Due tomorrow", "Unpaid members"],
        ["T−0 (due date)", "Push + SMS", "Due today. Contribute by {time}", "Unpaid members"],
        ["T+1", "Push", "Round closes at {time}. You are still unpaid", "Unpaid members"],
        ["Round closes", "Push + SMS + in-app", "Round {n} closed with {n} of {total} positions funded", "All members, unpaid first"],
        ["After close", "In-app", "You missed round {n}. Your next contribution is {date}. [Offer a recovery plan]", "Defaulted members"],
    ]},
    {"t": "bullets", "items": [
        "No more than three money reminders per member per day, regardless of how many Ajos they are in. Reminder fatigue produces unsubscribes, and an unsubscribed member is a defaulting member.",
        "Escalation is per-Ajo, not global, but the daily cap is global.",
        "A member who has paid is never sent a payment reminder. This is a correctness bug if it happens, and it damages confidence in the entire system.",
        "Quiet hours apply to reminders, not to money events. A round closing at 6pm local time must be communicated that evening.",
    ]},

    {"t": "h2", "text": "16.6 Delivery architecture"},
    {"t": "code", "size": 7.6, "text": """
  domain event                queue (BullMQ)         fan-out worker
  ────────────────             ──────────────         ─────────────────
  contribution.captured  ──▶  notifications.money  ──▶  push (APNs/FCM)
  payout.succeeded       ──▶  notifications.money  ──▶  email (transactional)
  payout.held            ──▶  notifications.money  ──▶  SMS
  contribution.due       ──▶  notifications.remind ──▶  [in-app record written]
  security.alert         ──▶  notifications.security ─▶ [preference check]
                                    │
                                    ├──▶ per-channel worker (independent, retryable)
                                    ├──▶ preference check (except money events)
                                    ├──▶ quiet-hours check (except money events)
                                    ├──▶ rate limit / dedupe / frequency cap
                                    └──▶ delivery log  (status, provider ref, error)
"""},
    {"t": "bullets", "items": [
        "**Asynchronous, always.** A notification failure must never roll back a payment. The ledger entry is committed first; the notification is a downstream consequence.",
        "**Per-channel independent queues** so an email provider outage does not delay push notifications.",
        "**Idempotent delivery** — a notification has a unique key, so a retried job cannot produce a duplicate message.",
        "**Delivery logging** — sent, delivered, failed, bounced. Bounced email and invalid phone numbers are suppressed and flagged, not retried forever.",
        "**Exponential backoff with a cap**, then a dead-letter queue with alerting. A dead-letter queue nobody watches is an outage that never surfaces.",
    ]},

    {"t": "h2", "text": "16.7 Preferences and quiet hours"},
    {"t": "bullets", "items": [
        "Per channel, per category. A member may disable marketing email and keep all payment push notifications.",
        "Quiet hours are configurable, default 22:00–07:00 local, and apply to informational, marketing, and reminder categories only.",
        "Money events and security events always bypass quiet hours.",
        "A member in a different timezone from the Ajo — and with a contribution deadline in the Ajo's local time — sees deadlines in **the Ajo's timezone**, clearly labelled, with their local equivalent shown alongside. Getting this wrong causes defaults.",
        "Timezone is derived from the phone number at onboarding, confirmed by the member, and re-derivable from location with consent.",
    ]},
    {"t": "callout", "kind": "NOTE", "title": "One deadline, one clock.",
     "text": "The most avoidable cause of default in a group savings product is a deadline "
     "displayed in the wrong timezone. A member in Lagos and an organizer in Kaduna must "
     "agree on when the round closes, and the app is the only place that can guarantee "
     "that. Everything else about a default is a harder problem; this one is solvable."},

    {"t": "h2", "text": "16.8 Statements and records"},
    {"t": "bullets", "items": [
        "**Every notification is a record.** It is written to a durable member-visible notification history, and is retained even if the member later changes their phone number.",
        "**Monthly statement** — a PDF and an in-app view covering contributions, fees, payouts, and the member's position in every Ajo, issued by email on a fixed day each month.",
        "**Annual statement** — for tax and personal records, with the total fees paid clearly itemised. Whether contributions are tax-deductible or a fee is taxable is a **question for Nigerian tax advisors**, and the statement should present the facts without characterising them.",
        "**Transaction receipts** — every contribution, fee, and payout has a receipt with a reference number, usable as evidence in a dispute.",
        "**Export** — a member can export their full transaction history in a machine-readable format at any time.",
    ]},

    {"t": "h2", "text": "16.9 Messaging safety"},
    {"t": "p", "text": "If the app has messaging, it has a moderation problem, a "
     "harassment problem, and a fraud problem. That is why messaging is scoped rather than "
     "open."},
    {"t": "bullets", "items": [
        "Messaging is **organizer to members within a single Ajo**, plus member to member on request. There is no open directory, no global discoverability, and no ability to message a member who is not in the same Ajo.",
        "Every message is retained and auditable. A member can report a message; reports are reviewed by a human.",
        "Blocking and muting are available to every member and take effect immediately.",
        "Contact details are hidden by default. A member who chooses to share does so deliberately, and sharing is revocable.",
        "**Money never travels through chat.** A message asking for money is both prohibited and reportable. This is stated in the terms, in the Ajo rules, and in the compose screen.",
        "Rate limits on outbound messages, with a low threshold for new accounts, prevent spam and mass-targeting.",
    ]},

    {"t": "h2", "text": "16.10 Notification metrics"},
    {"t": "table", "head": ["Metric", "Definition", "Target", "Why"], "widths": [1.7, 2.1, 1.1, 1.6], "size": 8.0, "rows": [
        ["Push opt-in rate", "Members with push enabled ÷ registered", "> 90%", "The primary delivery channel"],
        ["Open rate by category", "Opens ÷ delivered, per category", "Money > 70%", "A low open rate on money events predicts defaults"],
        ["Contribution rate after reminder", "Contributions within 24h of a reminder ÷ reminders sent", "> 40%", "The reminder system's actual job"],
        ["Time to read a due notice", "Median time from send to open", "< 4 hours", "Determines whether the reminder is useful"],
        ["Failed delivery rate", "Failures ÷ attempts, per channel", "< 1%", "Above this, the channel is not working"],
        ["Bounce and invalid rate", "Bad addresses ÷ sends", "< 0.5%", "Needs a data-hygiene task, not more retries"],
        ["Duplicate send rate", "Duplicates ÷ total sends", "Zero", "Any duplicate is a defect"],
        ["Dead-letter queue depth", "Undeliverable notifications awaiting triage", "< 50", "An unwatched queue is a silent outage"],
        ["Unsubscribe rate", "Opt-outs ÷ sends, marketing", "< 0.5%", "Frequency and relevance discipline"],
        ["Support tickets about notifications", "Tickets tagged notification", "Declining trend", "A proxy for template quality"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "The one notification that must never fail.",
     "text": "'Your payout was sent' is the emotional peak of the entire product. It is "
     "also the one notification that must not be duplicated, delayed past the moment of "
     "credit, or lost to a provider outage. It should be the most heavily monitored "
     "notification in the system, with its own alerting."},
]
