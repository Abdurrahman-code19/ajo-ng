"""Section 10 — Technical Architecture."""

BLOCKS = [
    {"t": "h1", "text": "10. Technical Architecture"},

    {"t": "lead", "text": "A modular monolith with a strictly separated domain core, "
     "not microservices. The financial integrity requirements — atomic multi-step "
     "money movements, one authoritative ledger, serialisable position claims — are "
     "materially harder to guarantee across a service boundary than inside a single "
     "transaction. Scale is a future problem; correctness is a present one."},

    {"t": "h2", "text": "10.1 Architecture principles"},
    {"t": "numbers", "items": [
        "**The domain core has zero infrastructure dependencies.** It imports nothing from the database, the queue, the payment provider or the framework. It is pure TypeScript and can be tested, reasoned about and moved without any service running.",
        "**All money logic lives in the domain core.** Not in route handlers, not in the UI, not in SQL triggers. A rule that affects a member's money must be expressible as a pure function.",
        "**The ledger is the single source of truth.** The payment provider reports what happened; the ledger records what AJO.ng believes. Where they disagree, we reconcile — we never silently overwrite.",
        "**Every money movement is idempotent and append-only.** Corrections are reversing entries, never updates.",
        "**The financial provider is a port, not a dependency.** AJO.ng code must never import a provider SDK.",
        "**Boring technology.** The stack is chosen for long-term maintainability by a small team, not for novelty.",
    ]},

    {"t": "h2", "text": "10.2 System context"},
    {"t": "code", "size": 8.0, "text": """
                          ┌──────────────────────────────┐
                          │        AJO.ng Platform        │
                          │  (orchestration + ledger)     │
                          └──────────────────────────────┘
                                        │
        ┌───────────────┬───────────────┼───────────────┬──────────────┐
        │               │               │               │              │
   ┌────▼────┐   ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐ ┌─────▼──────┐
   │ Web App │   │ Mobile App  │  │  Admin    │  │  Background │ │  Reporting  │
   │ Next.js │   │ React Native│  │ Console   │  │  Workers    │ │  / Analytics│
   │         │   │ + Expo      │  │ (Next.js) │  │  (queues)   │ │             │
   └────┬────┘   └──────┬──────┘  └─────┬─────┘  └──────┬──────┘ └─────┬──────┘
        └───────────────┴───────────────┴───────────────┴──────────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │      API Gateway / BFF       │
                         │  authn, rate limit, validation│
                         └──────────────┬──────────────┘
        ┌────────────────┬──────────────┼──────────────┬────────────────┐
        │                │              │              │                │
 ┌──────▼──────┐  ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐ ┌───────▼────────┐
 │ Application │  │  Domain     │ │ Financial  │ │  Identity  │ │  Notification  │
 │  Services   │  │   Core      │ │  Provider  │ │  Provider  │ │   Service      │
 │ (use cases) │  │ (pure, no I/O)│ │  Adapter   │ │            │ │                │
 └──────┬──────┘  └──────┬──────┘ └─────┬──────┘ └─────┬──────┘ └───────┬────────┘
        │                │              │              │                │
        └────────────────┴──────────────┴──────┬───────┴────────────────┘
                                                 │
                    ┌────────────────────────────┼──────────────────────────┐
                    │                            │                          │
             ┌──────▼──────┐            ┌────────▼────────┐        ┌────────▼───────┐
             │ PostgreSQL  │            │ ProvidusUnity   │        │  Redis        │
             │ (Supabase)  │            │ (regulated PSP) │        │ (cache/queue) │
             └─────────────┘            └─────────────────┘        └────────────────┘
"""},
    {"t": "callout", "kind": "ASSUMPTION", "title": "Provider drawn as a box, not an integration.",
     "text": "ProvidusUnity is shown as a dependency because it is the intended financial "
     "partner. Its API is not yet available and its actual capabilities are unverified. "
     "No capability is assumed anywhere in this architecture; the interface in section 13 "
     "is what AJO.ng requires, and what the partner is asked to confirm."},

    {"t": "h2", "text": "10.3 Technology stack"},
    {"t": "table", "head": ["Layer", "Choice", "Why this, and what was rejected"], "widths": [1.2, 1.5, 3.8], "size": 8.2, "rows": [
        ["Language", "TypeScript 5.5+ (strict)", "One language across web, mobile and backend. `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess` and branded types catch money bugs at compile time. Rejected: plain JS (no guarantees on money), Go/Rust (team velocity)"],
        ["Web", "Next.js 15 (App Router), React 18", "SSR for the marketing site, static export for the admin console, one codebase. Rejected: separate SPA + CMS (two auth surfaces), pure static site (no app state)"],
        ["Mobile", "React Native + Expo (SDK 52+)", "Shared logic with the web app, OTA updates without store review, mature ecosystem. Rejected: Flutter (second language, smaller hiring pool), native iOS/Android (two codebases for a 2-person team)"],
        ["Styling", "Tailwind CSS v4 + design tokens from section 5", "Token values live in CSS custom properties; Tailwind maps onto semantic names. Rejected: CSS-in-JS (runtime cost), a component library that dictates the brand (21st.dev is a starting point, not the system)"],
        ["Backend", "Node.js 20 LTS + Fastify + TypeScript", "Same language and shared domain package with web and mobile. Fastify gives schema-first validation, which matters more than raw throughput. Rejected: NestJS (heavy DI ceremony for a small team), Express (unmaintained typing story)"],
        ["Domain", "Pure TypeScript package, zero runtime dependencies", "The most important architectural decision in this document. Reusable by the API, the workers and the mobile app for offline validation"],
        ["Database", "PostgreSQL 15+ via Supabase", "Row Level Security gives defence-in-depth at the data layer, not just the API layer. PITR, read replicas and point-in-time recovery are included. Rejected: MySQL (weaker RLS), a document store (the ledger needs ACID and real foreign keys)"],
        ["Cache / queue", "Redis + BullMQ", "Session storage, rate-limit counters, and the asynchronous work that must not sit in a request (notifications, reconciliation, webhooks)"],
        ["Object storage", "Supabase Storage (S3-compatible)", "KYC documents and dispute evidence. S3-compatible so the provider is not a lock-in"],
        ["Validation", "Zod at the edge + TypeScript in the domain", "Parse, don't validate. The API never passes unvalidated data inward"],
        ["Testing", "node:test (domain), Vitest (app), Playwright (E2E)", "Playwright is already an available MCP in the founder's toolchain, so E2E needs no new capability"],
        ["Observability", "OpenTelemetry, Sentry, structured JSON logs", "Distributed tracing matters once a payment takes longer than a request timeout. Structured logs are a compliance requirement, not a preference"],
        ["Hosting", "Vercel (web) + a container host for API/workers (Railway/Fly.io/AWS ECS) + Supabase (database)", "The API must not run on a serverless platform that kills long-lived requests mid-payout. See 10.9 for the reasoning"],
        ["CI/CD", "GitHub Actions", "Required checks on every PR, including the domain test suite and the Playwright suite"],
    ]},

    {"t": "h2", "text": "10.4 Monorepo structure"},
    {"t": "code", "size": 8.0, "text": """
ajo/
├─ apps/
│  ├─ web/                 Next.js — marketing site + member web app
│  ├─ admin/               Next.js — operations console (internal, no public index)
│  └─ mobile/              Expo — Android + iOS
├─ packages/
│  ├─ domain/              PURE TypeScript. Money, ledger, state machines.
│  │                       ZERO runtime deps. This is the crown jewel.
│  ├─ application/         Use cases. Orchestrates domain + ports. No HTTP.
│  ├─ contracts/           Shared API types + Zod schemas + generated OpenAPI
│  ├─ ui-web/              React components consuming design tokens
│  ├─ ui-mobile/           React Native components consuming theme tokens
│  └─ config/              tsconfig bases, eslint, prettier, lint rules
├─ services/
│  ├─ api/                 Fastify. HTTP only: route -> use case -> response.
│  ├─ worker/              BullMQ consumers: notifications, reconciliation,
│  │                       webhook processing, statement generation
│  └─ scheduler/           Cron: contribution due dates, grace period expiry,
│                          enrollment window close, payout scheduling
├─ database/
│  ├─ migrations/          Forward-only, numbered, never edited after apply
│  ├─ seeds/               Development and test fixtures only
│  └─ rls-tests/           Executed in CI against a real Postgres
├─ docs/                   This specification and its generator
└─ brand/                  Logo, icon and imagery assets
"""},
    {"t": "callout", "kind": "NOTE", "title": "The dependency rule that matters:",
     "text": "`packages/domain` may import from nothing but itself and the standard "
     "library. It cannot import from `application`, `api`, Supabase, or any provider "
     "SDK. This is enforced in CI by an ESLint `no-restricted-imports` rule. The reason "
     "is not tidiness: in three years, when the payment partner changes or the database "
     "moves, a domain core with no infrastructure coupling is the only part that can be "
     "proved still correct."},

    {"t": "h2", "text": "10.5 Request lifecycle — paying a contribution"},
    {"t": "p", "text": "The most safety-critical path in the product. Every step here "
     "exists because of a documented failure mode."},
    {"t": "numbers", "items": [
        "Client requests `POST /contributions/:id/pay` with an `Idempotency-Key` header.",
        "API verifies the session, resolves the caller's membership, and confirms via RLS that this member belongs to this Ajo.",
        "The application layer recomputes the amount **server-side from the database** — never from the client's number. The client may display an amount; it may not assert one.",
        "The fee is computed in kobo: `fee = (amount_kobo * 200 + 5000) / 10000`. For NGN 1,000.00 that is exactly 2,000 kobo.",
        "`idempotency_keys` is checked. A replay returns the original response and moves no money.",
        "A `payments` row is written `INITIATED` and a `contribution` moves `PENDING → PROCESSING` inside one database transaction.",
        "The `FinancialProvider` port is called with its own idempotency key derived from the payment ID.",
        "The provider returns a reference. The payment moves to `PENDING` awaiting confirmation. **The contribution is not yet marked paid.**",
        "The provider redirects the member to their bank. AJO.ng returns a 'confirming your payment' screen, never a success screen.",
        "Asynchronously the provider sends a signed webhook. Signature is verified over the raw body before parsing.",
        "A duplicate webhook is recognised by provider reference and ignored — the ledger is idempotent, so a repeat is harmless but is still recorded as a duplicate-receipt event for audit.",
        "The worker posts to the ledger in the mandatory order: `contribution.received`, then `fee.recognised`. Both balance to zero.",
        "The contribution moves to `PAID`; the round's collected total is incremented; the member's confirmation notification is queued.",
        "If the webhook never arrives, the reconciliation job polls `getTransfer` and reaches the same conclusion. The system does not depend on the webhook alone.",
    ]},

    {"t": "h2", "text": "10.6 Financial provider abstraction"},
    {"t": "p", "text": "The single seam between AJO.ng and regulated money movement. "
     "Everything above it is written against this interface and nothing else."},
    {"t": "code", "size": 8.0, "text": """
export interface FinancialProvider {
  readonly id: ProviderId;

  createCollectionAccount(cmd: CreateCollectionAccountCommand): Promise<CollectionAccount>;
  verifyAccount(accountNumber: string): Promise<AccountVerification>;
  initiateCollection(cmd: InitiateCollectionCommand): Promise<Transfer>;
  initiatePayout(cmd: InitiatePayoutCommand): Promise<Transfer>;
  getTransfer(providerReference: string): Promise<Transfer>;

  // MUST verify over rawBody before parsing, constant-time.
  // MUST throw on signature failure. NEVER trust a parsed body.
  parseWebhook(event: ProviderWebhookEvent): Promise<ProviderWebhookEvent>;
}
"""},
    {"t": "bullets", "items": [
        "Every mutating call carries an idempotency key derived from stable business facts, never a random UUID — otherwise a retry after a timeout becomes a duplicate payout.",
        "`parseWebhook` verifies HMAC over the **raw** request body before any JSON parsing, and compares in constant time.",
        "A `MockFinancialProvider` implements this interface for development. It refuses to construct when `NODE_ENV=production`, and every transfer it produces is tagged `MOCK`. A simulated payment that a member or investor believed was real would be a reportable incident, not a bug.",
    ]},

    {"t": "h2", "text": "10.7 Data architecture"},
    {"t": "table", "head": ["Concern", "Approach", "Why"], "widths": [1.5, 2.2, 2.8], "size": 8.2, "rows": [
        ["Money storage", "bigint kobo, never float or numeric", "0.1 + 0.2 ≠ 0.3. A one-kobo drift per operation becomes an unreconcilable dispute"],
        ["Ledger", "Append-only double-entry in the same database transaction as the state change", "Atomicity. Money and state can never disagree"],
        ["Position claims", "`SELECT ... FOR UPDATE` on the target row, or SERIALIZABLE isolation", "Two members claiming the last position must not both succeed"],
        ["Soft deletion", "`deleted_at` on business tables; hard delete only for a documented retention expiry", "An audit trail that can be deleted is not an audit trail"],
        ["Idempotency", "`idempotency_keys` table, request-hashed, TTL-bounded", "Makes every money endpoint safe to retry"],
        ["Webhooks", "`webhook_events` table storing raw payload + signature + dedupe key", "A webhook that was processed must be provable later"],
        ["Reconciliation", "Nightly job comparing ledger against provider statements", "The two records of truth are compared, never assumed to agree"],
        ["RLS", "Policies on every user-facing table; ledger tables service-role only", "A compromised API key must not be sufficient to read another member's records"],
    ]},

    {"t": "h2", "text": "10.8 Background processing"},
    {"t": "table", "head": ["Queue / job", "Trigger", "Responsibility", "Failure handling"], "widths": [1.4, 1.2, 2.2, 1.7], "size": 8.2, "rows": [
        ["webhook.process", "Provider HTTP", "Verify, dedupe, post to ledger, update state", "Retry with backoff; dead-letter after N attempts; page on a failed payout webhook"],
        ["payment.reconcile", "Cron, every 15 min", "Poll unsettled payments, resolve `UNKNOWN` states", "Alert if a payment stays unresolved beyond the provider SLA"],
        ["payout.execute", "Scheduled round completion", "Verify full funding, release payout, post ledger", "If funding is short, move to `HELD` and notify — never a partial payout"],
        ["contribution.remind", "Cron, T-24h and T-2h", "Send due reminders", "Bounded retries; a failed notification is logged, never retried infinitely"],
        ["grace.expire", "Cron, hourly", "Detect 48h grace expiry, record default, notify organizer", "Must be idempotent — a double run must not double-record a default"],
        ["enrollment.close", "Cron, daily", "Close the 5-day window; cancel or activate", "Idempotent per Ajo"],
        ["statement.generate", "Cron, monthly", "Produce a member's statement PDF", "Retryable; stored in object storage"],
        ["reconciliation.run", "Cron, nightly", "Full ledger-vs-provider comparison", "Produces a signed report; any break pages a human"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "Why not do this inline:",
     "text": "A notification that fails must never roll back a contribution that already "
     "succeeded, and a member closing their browser must never abandon a payment. Work "
     "that can fail independently of the user's request belongs in a queue, and the "
     "queue is what makes those two things independent."},

    {"t": "h2", "text": "10.9 Deployment topology"},
    {"t": "table", "head": ["Environment", "Purpose", "Data", "Payments"], "widths": [1.1, 2.0, 1.6, 1.8], "size": 8.2, "rows": [
        ["Development", "Local feature work", "Seeded fixtures only", "Mock provider"],
        ["Staging", "Integration, E2E, QA, demos", "Synthetic members; no real PII", "Provider sandbox, if granted"],
        ["Pilot", "Controlled launch with real, verified members", "Real but small; full audit", "Real, low volume, heavily monitored"],
        ["Production", "General availability", "Real", "Real, at scale"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "Serverless is not appropriate for the API.",
     "text": "Next.js on Vercel is right for the marketing site and the admin console. The "
     "API and workers should run on a container host that supports long-lived requests. "
     "A serverless function killed mid-payout leaves a member's money in an indeterminate "
     "state, and recovering that is a manual, member-visible incident. This is a "
     "deliberate cost-versus-safety trade, and it is the reason the API is not deployed "
     "to Vercel serverless functions."},

    {"t": "h2", "text": "10.10 Caching strategy"},
    {"t": "table", "head": ["Layer", "Cached", "TTL", "Invalidation"], "widths": [1.2, 2.0, 0.9, 2.4], "size": 8.2, "rows": [
        ["CDN", "Marketing site static assets and pages", "Long, hashed filenames", "Deploy purges"],
        ["Redis", "Dashboard summary reads", "30 seconds", "Explicit bust on any write affecting the member"],
        ["Redis", "Rate-limit counters", "Window length", "Natural expiry"],
        ["React Query", "Member Ajo list and schedule", "60 seconds", "Invalidated by mutation"],
        ["Never cached", "Balances, contribution status, payout state, anything from the ledger", "—", "These must be read fresh or the product lies to a member"],
    ]},
    {"t": "callout", "kind": "WARNING", "title": "Never cache a balance.",
     "text": "A stale contribution status produces a member who believes they have paid "
     "when they have not, or the reverse. Either outcome is a trust incident. Section 25 "
     "marks these reads as uncacheable for the same reason."},

    {"t": "h2", "text": "10.11 Observability"},
    {"t": "bullets", "items": [
        "**Structured JSON logs** with `request_id`, `member_id`, `ajo_id`, `transaction_id` on every line. Log retention must satisfy the record-keeping requirements in section 24, which require legal confirmation.",
        "**Distributed tracing** across web → API → queue → provider, so a payout that took 4 minutes can be reconstructed.",
        "**Error tracking** (Sentry) with release tagging and source maps.",
        "**Business metrics** exported to the analytics pipeline in section 21.",
        "**Alerts that page a human**, defined in section 20: solvency assertion failure, a payout in `HELD`, a failed payout, a webhook signature failure, reconciliation break, default rate above threshold.",
    ]},

    {"t": "h2", "text": "10.12 Architectural decisions and trade-offs"},
    {"t": "table", "head": ["ID", "Decision", "Rejected alternative", "Rationale", "Reversible?"], "widths": [0.5, 1.6, 1.4, 2.4, 0.6], "size": 8.0, "rows": [
        ["AD-01", "Modular monolith", "Microservices", "Atomic money movements and one ledger. A 2-person team cannot operate distributed transactions.", "Poorly"],
        ["AD-02", "Pure domain core", "Framework-coupled services (NestJS)", "Keeps business rules testable and portable for years", "Poorly"],
        ["AD-03", "PostgreSQL + Supabase", "Managed NoSQL", "ACID, real FKs, RLS, PITR — a ledger needs relational guarantees", "No"],
        ["AD-04", "Mock provider until approved", "Integrating a provider early against assumptions", "No capability is invented; the real integration is days, not months", "Yes"],
        ["AD-05", "Container host for API", "Vercel serverless", "Long-lived requests; no mid-payout termination", "Yes"],
        ["AD-06", "Events in-domain, no event sourcing in v1", "Full event sourcing", "Eventual-consistency bugs on money are worse than the benefit at MVP scale. The append-only ledger already gives the audit property that matters", "Yes"],
        ["AD-07", "Next.js for web and admin", "Separate SPA + CMS", "One auth surface, one deploy, shared components", "Yes"],
        ["AD-08", "Expo for mobile", "Bare React Native", "OTA updates, faster iteration with a small team", "Yes"],
        ["AD-09", "RLS + application authz", "Application-only authorisation", "Defence in depth: a leaked key alone must not expose member data", "No"],
        ["AD-10", "Queue for all money-adjacent work", "Inline processing", "A notification failure must not roll back a payment", "Poorly"],
    ]},

    {"t": "h2", "text": "10.13 Capacity planning (base case)"},
    {"t": "p", "text": "Derived from the Year-1 base case in section 1. These are "
     "**projections from a pre-launch planning model, not measured load.**"},
    {"t": "table", "head": ["Metric", "Year-1 base case", "Peak assumption", "Design implication"], "widths": [1.7, 1.5, 1.4, 2.0], "size": 8.2, "rows": [
        ["Ajos created", "300", "—", "Trivial"],
        ["Members", "3,000 position slots", "—", "Trivial"],
        ["Contribution transactions", "30,000", "~40% concentrated on a Friday collection window", "Contributions are bursty, not uniform"],
        ["Payout transactions", "3,000", "Aligned to round completion", "Same burstiness"],
        ["Total core payment events", "33,000", "—", "Under 1 event/second average"],
        ["Concurrent users (peak)", "Not modelled", "Assume 10% of members in a collection window", "Comfortably within a single Postgres + Redis"],
    ]},
    {"t": "callout", "kind": "NOTE", "title": "The real scaling constraint is time, not volume.",
     "text": "At 33,000 events per year, AJO.ng will never need to scale out for throughput. "
     "The genuine constraints are (a) the 48-hour grace and 5-day enrollment windows, which "
     "require a scheduler that is reliable rather than fast, and (b) the burst on "
     "contribution day, when many Ajos collect on the same weekday. Read replicas and "
     "queue workers are the correct first scaling moves, not a distributed database."},
]
