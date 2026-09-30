"""Section 20 — Infrastructure, DevOps and Environments."""

BLOCKS = [
    {"t": "h1", "text": "20. Infrastructure, DevOps and Environments"},

    {"t": "lead", "text": "The infrastructure decisions for AJO.ng follow from one "
     "requirement: the money path must be reliable, auditable, and observable, and it must "
     "keep running when a third party does not. Everything else is chosen to be the "
     "simplest thing that satisfies that."},

    {"t": "h2", "text": "20.1 Architecture rationale"},
    {"t": "table", "head": ["Decision", "Rationale", "Consequence"], "widths": [1.7, 2.5, 2.3], "size": 8.0, "rows": [
        ["Modular monolith, not microservices", "A savings platform has few true domains, and financial correctness is far easier to guarantee inside one deployable unit and one transaction boundary", "Deliberate deferral of distributed-system complexity until there is measured evidence it is needed"],
        ["Node.js + Fastify API", "Shares a language and a type system with the domain core and the mobile client, so a money rule cannot be implemented twice with different behaviour", "Runtime is not ideal for heavy CPU work; no such work is required"],
        ["Next.js for web and admin", "Fast to build, good SSR for marketing and public pages, same TypeScript ecosystem", "The member-facing money screens live in the mobile app, not the web"],
        ["React Native + Expo for mobile", "One codebase for both platforms with native access where needed", "See section 17"],
        ["PostgreSQL via Supabase", "Transactions, strong constraints, row-level security, and a mature managed offering", "Vendor dependency on a managed platform; schema and access are portable"],
        ["Redis + BullMQ for queues", "Job retries, delayed jobs for reminder scheduling, and fan-out for notifications, with far less operational surface than a dedicated broker", "Redis is not a system of record; the ledger and the database remain authoritative"],
        ["Containerised, container-host managed", "A predictable runtime without a container platform team in the early stage", "Managed platform cost scales with usage"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "No serverless functions on the money path.",
     "text": "A 10,000-member payout cycle means 10,000 units of work with a hard time "
     "constraint. Serverless function time limits, cold starts, and concurrency caps are a "
     "poor fit for long-running, retryable, auditable financial processing. The API and the "
     "workers should run as long-lived processes. Serverless may be acceptable for a "
     "stateless public marketing page, and nowhere else."},

    {"t": "h2", "text": "20.2 Environments"},
    {"t": "table", "head": ["Environment", "Purpose", "Data", "Payment provider", "Access"], "widths": [1.2, 1.9, 1.5, 1.6, 1.3], "size": 8.0, "rows": [
        ["local", "Day-to-day development", "Seeded synthetic", "Mock", "Developers"],
        ["ci", "Automated verification", "Seeded per run", "Mock", "Automated"],
        ["staging", "Integration, migration rehearsal, load tests", "Synthetic at realistic scale", "Provider sandbox if available, else mock", "Developers, QA"],
        ["pre-production", "Final rehearsal of deploys and processes", "Production-like", "Provider production, staff accounts only", "Named staff, audited"],
        ["production", "Members", "Real", "Provider production", "Break-glass, time-boxed, logged"],
    ]},
    {"t": "bullets", "items": [
        "Environments are identical in shape. A deploy that works in staging works in production, because there is nothing to configure differently.",
        "**No production data is ever copied downward.** De-identified or synthetic data is used instead, and de-identification is verified rather than assumed.",
        "Secrets are per-environment and never shared. A development credential cannot touch production, and a production credential cannot be read from a development machine.",
    ]},

    {"t": "h2", "text": "20.3 Repository and branching"},
    {"t": "code", "size": 7.6, "text": """
  main        ──●──●──●──●──●──●──●   protected, always releasable
                ╲        ╱
  feature/x     ●──●──●──●──●
  release/x        ●──●
  hotfix/urgent          ●──●
"""},
    {"t": "bullets", "items": [
        "`main` is protected: no direct push, and it must pass the full CI gate including tests, lint, type check, and security scan.",
        "Short-lived branches. A branch older than a week is a review problem and a merge risk.",
        "Pull requests require one approving reviewer, and a second for anything touching money, authorisation, or the schema.",
        "**Squash merge with a conventional commit message**, so history is readable and releases are derivable from it.",
        "`hotfix/urgent` exists for production incidents, with a mandatory retrospective patch to `main` afterwards.",
    ]},

    {"t": "h2", "text": "20.4 CI/CD pipeline"},
    {"t": "code", "size": 7.6, "text": """
  on push / pull request
      │
      ├─ install (lockfile enforced)
      ├─ type check + lint + format check
      ├─ unit + property tests          ─── fail ──▶ STOP
      ├─ integration tests (PostgreSQL) ─── fail ──▶ STOP
      ├─ contract tests (mock provider) ─── fail ──▶ STOP
      ├─ security scan + secret scan     ─── fail ──▶ STOP
      ├─ build all services
      ├─ bundle size check              ─── fail ──▶ STOP
      │
      └─ on main: deploy staging ──▶ smoke tests ──▶ manual approval ──▶ deploy production
                                                    │
                                            (canary 5% ──▶ monitor ──▶ full rollout)
"""},
    {"t": "h3", "text": "20.4.1 Deployment strategy"},
    {"t": "bullets", "items": [
        "Rolling deployment with zero downtime. A member is never told the app is down because a deploy is happening.",
        "**Database migrations run separately and safely** — expand first, migrate second, contract later. Never a destructive migration in the same deploy as the code that stops using the column.",
        "**Backward compatibility is mandatory during rollout.** The previous version of the API must keep working while the new one rolls out, because two versions of the mobile app are in the wild simultaneously and cannot be updated atomically.",
        "**Feature flags** for anything risky, with an audit trail of who set what and when. A flag without a removal date becomes permanent complexity.",
        "**Canary release** at 5% of traffic with automated halt on an error-rate or latency breach, and an immediate kill switch.",
        "**Automatic rollback** on a failed health check, with a database compatibility check first, because an automatic rollback that corrupts data is worse than an outage.",
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Mobile clients cannot be updated atomically.",
     "text": "A server deploy must be compatible with every version of the app that is in "
     "the wild, and that window is weeks. In practice this means additive, backward-"
     "compatible API changes only: never remove a field, never change a type, and never "
     "change a response shape in a release. Deprecate first, remove months later."},

    {"t": "h2", "text": "20.5 Observability"},
    {"t": "h3", "text": "20.5.1 Structured logging"},
    {"t": "p", "text": "Logs are structured JSON with a request ID propagated across "
     "services, and with the sensitive fields from section 14.6 redacted at the source "
     "rather than filtered later."},
    {"t": "code", "size": 7.4, "text": """
  { "ts": "2026-03-14T09:12:44.221Z",
    "level": "info",
    "svc": "payments",
    "reqId": "01HQ8...", "memberId": "uuid", "ajoId": "uuid",
    "event": "contribution.captured",
    "ref": "AJO-7f3a-R3-2c91", "amountKobo": 102000,
    "feeKobo": 2000, "providerRef": "pv_9x2...",
    "ms": 412 }
"""},
    {"t": "h3", "text": "20.5.2 Metrics"},
    {"t": "table", "head": ["Domain", "Metrics"], "widths": [1.4, 5.1], "size": 8.2, "rows": [
        ["Golden signals", "Latency, traffic, errors, saturation — for every service"],
        ["Business", "Contributions per minute, capture success rate, payouts released, Ajos funded, default rate"],
        ["Financial", "Escrow balance vs ledger sum (the invariant), unsettled payments, unmatched inbound, fee accrued"],
        ["Queue", "Depth, oldest job age, processing rate, dead-letter count, retry rate"],
        ["Dependency", "Provider latency, error rate, and webhook delivery lag, per provider endpoint"],
        ["Reliability", "SLO compliance, error budget burn rate, incident count and duration"],
        ["Mobile", "Crash-free rate, ANR rate, cold start time, API error rate by app version"],
    ]},
    {"t": "h3", "text": "20.5.3 Distributed tracing"},
    {"t": "p", "text": "Request traces span the API, the database, the queue, and the "
     "provider call. The specific value here is a single transaction crossing an "
     "asynchronous boundary: a trace makes it possible to answer 'what happened to this "
     "member's contribution' in one query rather than by correlating four services' logs "
     "by hand."},
    {"t": "h3", "text": "20.5.4 Alerting"},
    {"t": "p", "text": "Alerts are actionable or they are noise, and noise is the fastest "
     "way to make an on-call engineer stop reading them. Every alert has a runbook, a "
     "named owner, and a severity."},
    {"t": "table", "head": ["Alert", "Severity", "Action"], "widths": [2.4, 1.0, 3.1], "size": 8.4, "rows": [
        ["Ledger invariant broken", "P1", "Page. Halt payouts"],
        ["Payout batch failure", "P1", "Page. Investigate before the retry window"],
        ["Webhook delivery gap > 2h", "P1", "Page. Members are stuck pending"],
        ["Provider error rate > 10%", "P1", "Page. Check provider status"],
        ["Escrow reconciliation mismatch", "P1", "Page. Halt payouts"],
        ["Queue oldest job > 30 min", "P2", "Investigate during the day"],
        ["Dead-letter queue growing", "P2", "Triage within 24h"],
        ["P95 latency breach", "P2", "Investigate"],
        ["SLO burn rate fast", "P2", "Prioritise"],
        ["Certificate or secret expiry < 14 days", "P3", "Schedule renewal"],
    ]},

    {"t": "h2", "text": "20.6 Backup and disaster recovery"},
    {"t": "table", "head": ["Asset", "Backup", "RPO", "RTO", "Verified"], "widths": [1.5, 2.0, 0.8, 0.8, 1.4], "size": 8.2, "rows": [
        ["PostgreSQL (primary)", "Continuous WAL archiving + daily full snapshot", "< 5 min", "< 1 hour", "Quarterly restore drill"],
        ["PostgreSQL (read replica)", "Streaming replication", "n/a", "n/a", "Continuous health check"],
        ["Ledger", "In the database, append-only, plus a nightly export to object storage", "< 5 min", "< 1 hour", "Quarterly"],
        ["Object storage (statements, documents)", "Versioned, cross-region replication", "< 15 min", "< 4 hours", "Quarterly"],
        ["Redis (queues, cache)", "Not backed up — a rebuildable cache", "Loss of in-flight jobs only", "< 1 hour", "Documented job replay"],
        ["Configuration and infrastructure as code", "In the repository", "n/a", "Rebuild", "Per deploy"],
        ["Secrets", "Managed secret store, versioned", "n/a", "Per provider", "Per rotation"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "A backup that has never been restored is a hypothesis.",
     "text": "Recovery objectives are only real if a restore has been performed. Quarterly "
     "rehearsals are scheduled, timed, and documented, and the measured time is compared "
     "against the stated RTO. A platform that has never restored its database is a platform "
     "that has never tested its own ability to survive losing it."},

    {"t": "h2", "text": "20.7 Scalability"},
    {"t": "table", "head": ["Dimension", "Approach", "Trigger to revisit"], "widths": [1.4, 2.9, 2.2], "size": 8.2, "rows": [
        ["Web/API", "Vertical scaling behind a managed load balancer; stateless services scale horizontally", "Sustained CPU saturation above 70%"],
        ["Database", "Connection pooling (PgBouncer), indexed access paths, read replicas for reporting", "Primary CPU or IO saturation, or replication lag above 1 min"],
        ["Writes", "Partition the ledger by month once it grows large; archive cold partitions", "Ledger table beyond ~50M rows"],
        ["Queues", "Named queues per workload class so a notification burst cannot delay a payout job", "Sustained queue age above target"],
        ["Payout batches", "Chunked with configurable daily caps; parallel dispatch within provider limits", "Payout completion outside the promised window"],
        ["Storage", "Object storage for documents and statements, never in the database", "Standard practice from day one"],
    ]},
    {"t": "p", "text": "The scaling question that actually matters for AJO.ng is not raw "
     "throughput — it is a single large Ajo completing on time while the platform serves "
     "everything else. That is a workload-shape problem, solved by isolation and scheduling, "
     "not by buying a bigger database."},

    {"t": "h2", "text": "20.8 Cost model"},
    {"t": "p", "text": "Costs are dominated by three things, in this order: payment "
     "provider fees, message delivery, and infrastructure. Payment costs are a per-transaction "
     "cost that scales directly with revenue, and the exact rates depend on the provider "
     "agreement that has not yet been obtained."},
    {"t": "table", "head": ["Line", "Driver", "Scales with", "Note"], "widths": [1.4, 2.0, 1.3, 1.8], "size": 8.2, "rows": [
        ["Provider transaction fees", "Per collection and per payout", "Volume", "**Unknown until the provider agreement is confirmed.** The dominant variable cost"],
        ["SMS", "Per message", "Notifications", "Reminder and money-event traffic. Cost per thousand must be modelled"],
        ["Push notifications", "Per message", "Notifications", "Typically free or nominal at MVP volume"],
        ["Email", "Per message", "Notifications", "Nominal"],
        ["Compute", "Instance hours", "Traffic and jobs", "Modest at MVP. Grows with queue volume, not with members"],
        ["Database", "Storage and connections", "Data volume", "Ledger retention dominates over time"],
        ["Storage", "Documents and statements", "Members", "Small per member"],
        ["Observability", "Log and metric volume", "Traffic", "Budgeted deliberately; an unconstrained log bill is a real risk"],
        ["Support", "Headcount", "Members and incidents", "Grows with member count, not with transactions"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Verify the unit economics before scaling volume.",
     "text": "The gross revenue is 2% of contributions, but the *net* margin is 2% minus "
     "provider fees minus message costs minus support. If a provider charges 1.2% per "
     "collection, the margin is thin and the business case depends on contribution volume "
     "per member, not on member count. This calculation must be done with real provider "
     "rates and real message volumes before volume is pursued."},

    {"t": "h2", "text": "20.9 Operational readiness checklist"},
    {"t": "table", "head": ["Area", "Ready when", "Owner"], "widths": [1.5, 3.9, 1.1], "size": 8.4, "rows": [
        ["Monitoring and alerting", "Dashboards live, alerts route to a real on-call with runbooks", "Engineering"],
        ["Reconciliation", "All three procedures automated, run daily, with a named owner and a signed record", "Finance"],
        ["Runbook", "Documented procedures for the top ten incident types, rehearsed", "Operations"],
        ["Support tooling", "Agents can look up a transaction, a payout, and a dispute without engineering help", "Support"],
        ["On-call", "Rotation established, escalation path defined, compensation agreed", "Engineering"],
        ["Disaster recovery", "Backup restore rehearsed and timed against the RTO", "Engineering"],
        ["Security", "Penetration test findings closed, secrets rotated, access reviewed", "Security"],
        ["Compliance", "Counsel's sign-off on licensing, data protection, and terms", "Founder / legal"],
        ["Capacity", "Load-tested against the largest realistic Ajo and the month-start peak", "Engineering"],
        ["Communication", "Pre-approved templates for the likely member-facing scenarios", "Support"],
    ]},
]
