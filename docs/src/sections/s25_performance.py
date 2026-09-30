"""Section 25 — Performance, Scalability and Financial Performance."""

BLOCKS = [
    {"t": "h1", "text": "25. Performance, Scalability and Financial Performance"},

    {"t": "lead", "text": "Performance in a savings product is not vanity. A member who "
     "waits eight seconds to learn their money arrived will conclude the money did not "
     "arrive. A payout cycle that takes a day longer than promised teaches the whole market "
     "that AJO.ng is unreliable. The technical budgets and the commercial projections in this "
     "section describe the same promise from two directions."},

    {"t": "h2", "text": "25.1 Performance philosophy"},
    {"t": "numbers", "items": [
        "**Budgets are set from the member's expectation, not from what the code happens to do.** A member expects a confirmation within seconds, not within a technical margin of error.",
        "**The slowest legitimate path is a failure.** Money confirmation arrives by webhook, so a fast API that optimistically confirms would be both dishonest and dangerous.",
        "**Every budget has a method and a device.** A target measured on a laptop is meaningless; a target measured on the slowest supported phone is a real one.",
        "**Correctness is never traded for latency.** A slow correct answer is a support ticket; a fast wrong one is a financial incident.",
    ]},

    {"t": "h2", "text": "25.2 Service level objectives"},
    {"t": "table", "head": ["Journey", "SLO", "Measurement", "Error budget"], "widths": [1.7, 1.4, 2.2, 1.2], "size": 8.0, "rows": [
        ["Contribution confirmation (card/wallet)", "99.5% within 60s", "Webhook receipt to ledger capture", "0.5% / month"],
        ["Contribution confirmation (transfer)", "99.0% within 4 hours", "Reference match to capture", "1% / month"],
        ["Ajo activation", "99.5% within 5s", "Request to AJO state change", "0.5% / month"],
        ["Payout initiation", "99.9% within 2s", "Request accepted to provider called", "0.1% / month"],
        ["Payout delivered", "99.0% within 30 min", "Transfer accepted to bank credit", "1% / month"],
        ["Dashboard load", "99.0% within 2s", "Request to rendered", "1% / month"],
        ["API availability", "99.9% monthly", "Successful non-5xx responses", "0.1% / month"],
        ["Reconciliation accuracy", "100%", "Sessions with a detected break", "**Zero tolerance**"],
    ]},
    {"t": "p", "text": "The two zero-tolerance lines are deliberate. Availability can degrade "
     "briefly; an incorrect ledger cannot. A platform that is briefly unavailable loses some "
     "transactions. A platform whose ledger is wrong has lost the only thing it has."},

    {"t": "h2", "text": "25.3 Latency budgets"},
    {"t": "h3", "text": "25.3.1 API endpoints (p95, excluding third-party payment calls)"},
    {"t": "table", "head": ["Endpoint", "Budget", "Note"], "widths": [2.3, 1.2, 3.0], "size": 8.4, "rows": [
        ["GET /me", "150ms", "Cached; the app calls this on every launch"],
        ["GET /ajos", "250ms", "Member's Ajos with position and progress"],
        ["GET /ajos/:id", "300ms", "Aggregate loaded in one query, not six"],
        ["POST /contributions", "200ms", "Creates the pending record; the payment itself is a redirect"],
        ["GET /contributions/:id", "200ms", "Contribution status, for the polling fallback"],
        ["POST /payouts", "400ms", "Precondition checks plus intent creation"],
        ["GET /dashboard", "400ms", "Home screen aggregation"],
        ["GET /statements", "800ms", "Larger dataset; permitted to be the slowest read"],
    ]},
    {"t": "h3", "text": "25.3.2 Mobile"},
    {"t": "table", "head": ["Measurement", "Budget", "Note"], "widths": [2.3, 1.2, 3.0], "size": 8.4, "rows": [
        ["Cold start to interactive", "< 2.5s", "On a 2018-class Android device"],
        ["Warm start to interactive", "< 1.0s", ""],
        ["Screen transition", "< 300ms", "Perceived, using the native driver"],
        ["Payment flow, initiate to redirect", "< 3s", "Excluding the provider's own page"],
        ["List scroll", "60fps, never below 30fps", "Virtualised lists"],
        ["Offline cache read", "< 200ms", "No network at all"],
    ]},

    {"t": "h2", "text": "25.4 Throughput capacity"},
    {"t": "p", "text": "The design target is chosen to be comfortably above the realistic "
     "one-year peak, so that growth is an operations problem rather than an architecture "
     "problem."},
    {"t": "table", "head": ["Scenario", "Volume", "Design target", "Headroom"], "widths": [1.9, 1.6, 1.4, 1.6], "size": 8.2, "rows": [
        ["Registered members (year 1)", "Up to 30,000", "100,000", "3x"],
        ["Active members at any time", "Up to 8,000", "25,000", "3x"],
        ["Contributions per minute at peak", "400", "1,500", "3.5x"],
        ["Payouts released in a single minute", "500 (one large Ajo completing)", "1,500", "3x"],
        ["Notifications per minute at peak", "2,000", "6,000", "3x"],
        ["Concurrent API requests", "300", "1,000", "3x"],
        ["Total member transactions in year 1", "~360,000", "—", "—"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "The peak that matters is a single Ajo completing.",
     "text": "Not the average load — the moment a 500-member Ajo releases 500 payouts in one "
     "batch, on the same day, while everything else continues. This is a workload-shape "
     "problem, and it is solved by queue isolation, per-rail rate limits, and chunked batch "
     "dispatch rather than by a larger database."},

    {"t": "h2", "text": "25.5 Scalability architecture"},
    {"t": "h3", "text": "25.5.1 Read path"},
    {"t": "bullets", "items": [
        "Every Ajo detail screen is served by a single aggregate query. A screen that needs six round trips is a screen that will be slow on a bad network.",
        "The home dashboard is one query, not a fan-out. The same endpoint serves the web and the mobile client.",
        "Read replicas carry all reporting and analytics traffic, so a heavy dashboard never competes with a payment.",
        "Redis caches stable, slow-changing data — Ajo configuration, member profile. Money balances are **never** cached beyond the request, because a stale balance is a financial error.",
    ]},
    {"t": "h3", "text": "25.5.2 Write path"},
    {"t": "bullets", "items": [
        "All money writes are short, single-transaction operations. No long transaction ever holds a lock on a money table.",
        "Asynchronous work — notifications, analytics, statements — never shares a transaction with a money write.",
        "Queue isolation by workload class, so a notification burst cannot delay a payout.",
        "Write batching only where it does not compromise durability. A contribution is never batched.",
    ]},
    {"t": "h3", "text": "25.5.3 Database"},
    {"t": "bullets", "items": [
        "Every query is indexed for its access pattern, and slow-query logging is enabled from day one with a threshold well below what would be felt by a member.",
        "Connection pooling with PgBouncer, because a serverless-ish autoscaling pattern plus direct connections exhausts PostgreSQL connections long before CPU.",
        "The ledger is partitioned by month once it grows, with cold partitions archived to cold storage.",
        "Reads that are only for reporting go to a replica, and a read that must be consistent — anything touching money — goes to the primary.",
    ]},
    {"t": "h3", "text": "25.5.4 Rate limiting"},
    {"t": "table", "head": ["Operation", "Limit", "Reason"], "widths": [1.8, 1.6, 3.1], "size": 8.2, "rows": [
        ["Login attempts", "10 per account per 15 minutes", "Credential stuffing"],
        ["OTP requests", "5 per hour per destination", "Cost and SMS abuse"],
        ["Contribution initiation", "20 per member per hour", "Double-tap and script abuse"],
        ["Ajo creation (new accounts)", "3 per 30 days under 30 days old", "Account farming"],
        ["Payout destination change", "2 per 30 days", "Redirection fraud"],
        ["API, general reads", "300 per minute per token", "Abuse and cost control"],
        ["Webhook ingestion", "Rate-limited per IP with a generous ceiling", "Flood protection without breaking a burst"],
    ]},

    {"t": "h2", "text": "25.6 Financial projections"},
    {"t": "callout", "kind": "NOTE", "title": "These are projections built on a 2% fee and stated assumptions.",
     "text": "They are not revenue, not forecasts of earnings, and not a financial plan. "
     "They demonstrate that the fee model produces a coherent shape at plausible volumes. "
     "**PSP transaction costs, settlement timing, and operating costs are not included in "
     "the fee figures, and are unknown until the ProvidusUnity agreement is obtained.** The "
     "net margin is therefore materially smaller than the gross fee revenue, and must be "
     "modelled with real rates before any investment decision is made."},

    {"t": "h3", "text": "25.6.1 Scenarios"},
    {"t": "table", "head": ["Scenario", "Ajos", "Members", "Contribution", "Volume", "Gross fee (2%)", "Fee per Ajo"], "widths": [1.3, 0.8, 0.9, 1.3, 1.4, 1.2, 1.1], "size": 7.6, "rows": [
        ["Conservative", "150", "8", "NGN 7,500", "NGN 90,000,000", "NGN 1,800,000", "NGN 12,000"],
        ["Base", "300", "10", "NGN 10,000", "NGN 300,000,000", "NGN 6,000,000", "NGN 20,000"],
        ["Growth", "600", "12", "NGN 12,000", "NGN 864,000,000", "NGN 17,280,000", "NGN 28,800"],
    ]},
    {"t": "h3", "text": "25.6.2 Worked example — base scenario, per Ajo"},
    {"t": "code", "size": 7.6, "text": """
  10 members  x  NGN 10,000  x  10 rounds  =  NGN 1,000,000  pooled per Ajo
  Total charged per member per round:  NGN 10,000 + NGN 200 fee = NGN 10,200
  Total charged per member over 10 rounds:                       NGN 102,000
  Total collected per Ajo:                                       NGN 1,020,000
  Platform fee per Ajo (2%):                                     NGN  20,400

  What the recipient receives:            NGN 1,000,000  (the base pool)
  What the platform earns:                NGN    20,400
  Platform margin as % of contribution:   2.00%
  Platform margin as % of collected:      2.00% of contributions
"""},
    {"t": "h3", "text": "25.6.3 Volume shape"},
    {"t": "table", "head": ["Metric", "Conservative", "Base", "Growth"], "widths": [2.0, 1.5, 1.5, 1.5], "size": 8.4, "rows": [
        ["Ajos per year", "150", "300", "600"],
        ["Deposits per year", "12,000", "30,000", "72,000"],
        ["Payouts per year", "1,200", "3,000", "7,200"],
        ["Gross fee revenue", "NGN 1.80m", "NGN 6.00m", "NGN 17.28m"],
        ["Gross fee per member per year", "NGN 1,500", "NGN 2,000", "NGN 2,400"],
        ["Ajo completions", "150", "300", "600"],
        ["Monthly gross fee (averaged)", "NGN 150,000", "NGN 500,000", "NGN 1,440,000"],
    ]},
    {"t": "p", "text": "The gross fee per member rises with contribution size in these "
     "scenarios because the scenarios assume larger contributions, not because of any "
     "scaling mechanism. A 2% fee is a 2% fee: it does not improve with loyalty, and no "
     "volume tier or reward should be built on the assumption that it does."},

    {"t": "h3", "text": "25.6.4 What is deliberately excluded"},
    {"t": "table", "head": ["Excluded", "Why"], "widths": [2.0, 4.5], "size": 8.4, "rows": [
        ["PSP transaction fees", "Unknown until the provider agreement is obtained. The single largest variable cost"],
        ["SMS and message delivery", "Modelled per notification volume, not yet quantified with real rates"],
        ["Infrastructure and staff costs", "Not modelled; the business case is a volume question, not a cost-structure question, at this stage"],
        ["Fraud losses", "Budgeted at under 5 basis points of volume, per section 15.10. Immaterial to revenue at that level"],
        ["Defaults and recoveries", "A default reduces collected volume but does not reduce the platform fee, since the fee is charged on the contribution that was made"],
        ["Tax", "The treatment of fee income is a question for Nigerian tax advisors, per section 24.1"],
        ["Interest or yield on pooled funds", "**There is none. AJO.ng does not invest member money and does not pay returns.** Any figure implying otherwise would be a misrepresentation"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "There is no yield line, and that is a feature of the design.",
     "text": "The single most misleading thing a fintech presentation can do is show a "
     "returns figure. AJO.ng members receive their own savings and nothing more. Adding an "
     "apparent yield would change the product's legal character, mislead every member who "
     "reads it, and violate the disclosure principles in section 24.8. The absence of that "
     "line is the honest one."},

    {"t": "h2", "text": "25.7 Unit economics"},
    {"t": "p", "text": "Unit economics is the discipline of asking what one member is worth "
     "over time, and whether it exceeds what it costs to acquire and serve. With a 2% fee, "
     "the answer is sensitive to every variable cost, which is why the earlier decision to "
     "establish provider pricing before pursuing volume was the right one."},
    {"t": "table", "head": ["Variable", "Formula", "Direction", "Note"], "widths": [1.4, 2.1, 1.1, 1.9], "size": 8.0, "rows": [
        ["Gross fee per member", "2% x total contributions", "Fixed by the model", "NGN 2,000 at a NGN 10,000 x 10 Ajo"],
        ["PSP cost per member", "Fee per collection x rounds + fee per payout", "Reduces margin", "**Unknown. Dominant variable cost**"],
        ["Notification cost", "Cost per message x messages per member", "Reduces margin", "Bounded by the daily reminder cap"],
        ["Net margin per member", "Gross fee − PSP − notifications − support", "Must be positive", "Cannot yet be computed"],
        ["Lifetime value", "Net margin x expected Ajos per member", "Depends on repeat rate", "Repeat Ajo rate is the key driver"],
        ["Payback period", "Acquisition cost ÷ monthly net margin per member", "Must be < 18 months", "Cannot yet be computed"],
    ]},
    {"t": "p", "text": "The strategy implication is clear: **maximise the number of Ajos a "
     "member completes, not the number of members acquired.** Repeat behaviour compounds; "
     "acquisition does not. This is why the repeat Ajo rate in section 21.3 is a more "
     "important metric than member count, and why the product work should concentrate on "
     "making the second and third Ajo effortless."},

    {"t": "h2", "text": "25.8 Capacity planning triggers"},
    {"t": "table", "head": ["Trigger", "Action", "Lead time"], "widths": [2.1, 2.7, 1.7], "size": 8.4, "rows": [
        ["Sustained CPU above 70% on the API tier", "Scale out horizontally", "Minutes"],
        ["Database connections above 70% of the limit", "Add pooling, then read replicas", "Hours"],
        ["Primary replication lag above 1 minute", "Investigate; move reporting to a replica", "Hours"],
        ["Ledger table above 50M rows", "Implement monthly partitioning", "Weeks"],
        ["Queue oldest job above 30 minutes", "Scale workers, then split queues", "Hours"],
        ["Contributions above 1,000 per minute sustained", "Capacity review of the write path", "Days"],
        ["Members above 30,000", "Full capacity and cost review", "Weeks"],
        ["Provider rate limits approached", "Negotiate higher limits, or add a second provider", "Weeks"],
    ]},

    {"t": "h2", "text": "25.9 Performance monitoring and alerting"},
    {"t": "table", "head": ["Signal", "Threshold", "Severity", "Response"], "widths": [1.7, 1.6, 0.9, 2.3], "size": 8.4, "rows": [
        ["Contribution confirmation p95", "> 60s for card/wallet", "P2", "Investigate webhook processing"],
        ["Payout initiation p95", "> 2s", "P2", "Check for lock contention"],
        ["Payout delivery p95", "> 30 min", "P1", "Check provider and bank status"],
        ["Dashboard load p95", "> 2s", "P3", "Add a cache, or fix the query"],
        ["Cold start p75", "> 2.5s", "P3", "Bundle analysis, defer non-critical work"],
        ["Error budget burn", "Fast burn", "P1", "Freeze feature releases, stabilise"],
        ["Database CPU", "> 70% sustained", "P2", "Read replicas, index review"],
        ["Queue age", "> 30 min", "P2", "Scale workers"],
    ]},

    {"t": "h2", "text": "25.10 Performance summary"},
    {"t": "table", "head": ["Dimension", "Target", "Hard limit"], "widths": [2.0, 2.2, 2.3], "size": 8.4, "rows": [
        ["Contribution confirmation", "< 60s (card/wallet), same day (transfer)", "Never longer than the member's trust"],
        ["Payout delivery", "< 30 min", "Communicate before, not after"],
        ["API availability", "99.9%", ""],
        ["Ledger correctness", "100%", "**No compromise. There is no acceptable version of this**"],
        ["Reconciliation accuracy", "100%", "**No compromise**"],
        ["Mobile cold start", "< 2.5s", "Tested on a low-end device"],
        ["Crash-free sessions", "> 99.5%", ""],
        ["Member retention (repeat Ajo)", "> 50%", "The metric that compounds"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "The two lines with no acceptable compromise.",
     "text": "Ledger correctness and reconciliation accuracy are the only two entries in "
     "this document with an empty hard-limit column, and that is the correct answer. Every "
     "other number can be traded against something else. These two cannot — they are the "
     "reason members can safely leave their savings with the platform, and a 99.9%-correct "
     "ledger is not a thing that can be sold to anybody."},
]
