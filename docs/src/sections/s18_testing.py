"""Section 18 — Test Strategy and Quality Assurance."""

BLOCKS = [
    {"t": "h1", "text": "18. Test Strategy and Quality Assurance"},

    {"t": "lead", "text": "Testing a savings platform is not the same as testing ordinary "
     "software. A bug that displays the wrong round is an inconvenience. A bug that "
     "confirms a payment that was never made, or releases a payout twice, or loses a "
     "member's position, is a business-ending event. The test strategy is therefore "
     "weighted heavily towards money correctness, adversarial conditions, and the "
     "unhappy paths that never appear in a demo."},

    {"t": "h2", "text": "18.1 Objectives"},
    {"t": "numbers", "items": [
        "**Prove the money is right.** Every kobo that enters the system is accounted for, and the ledger invariant holds at all times.",
        "**Prove the state machine cannot be violated.** No sequence of requests may drive an Ajo or a payout into an illegal state.",
        "**Prove idempotency.** No operation may be executed twice, regardless of retries, timeouts, duplicate webhooks, or a member double-tapping a button.",
        "**Prove the unhappy paths.** Provider outage, webhook loss, bank rejection, timeout, clock skew, partial batch failure, and concurrent modification must all be handled without corruption.",
        "**Prove authorisation.** No member, organizer, or staff role may read or act on anything outside their scope.",
        "**Prove the invariants are enforced in the database and not only in application code** — because application code will eventually have a bug.",
    ]},

    {"t": "h2", "text": "18.2 Test pyramid"},
    {"t": "code", "size": 7.8, "text": """
        ╱‾‾‾‾‾‾‾‾‾‾‾╲
       ╱  E2E / contract ╲        ~5%    slow, expensive, few
      ╱   (critical paths)  ╲
     ╱───────────────────────╲
    ╱  Integration / adapter  ╲   ~20%   real DB, real queue, mocked provider
   ╱   (repos, services, RLS)  ╲
  ╱─────────────────────────────╲
 ╱   Unit / property / model     ╲  ~75%  fast, exhaustive, the workhorse
╱   (money, ledger, state machine) ╲
"""},
    {"t": "p", "text": "The shape is inverted from the classic pyramid of most web "
     "products, deliberately. The unit layer is where the financial correctness lives, and "
     "it is the layer where exhaustive coverage is affordable."},

    {"t": "h2", "text": "18.3 Unit tests — the domain core"},
    {"t": "p", "text": "The domain is pure TypeScript with no I/O, which makes it trivially "
     "testable and puts the most important logic in the most thoroughly tested layer."},
    {"t": "h3", "text": "18.3.1 Money"},
    {"t": "bullets", "items": [
        "Arithmetic is exact for values at the top of the realistic range, and the type prevents fractional kobo.",
        "Currency conversion is refused. AJO.ng operates in NGN only, and a conversion bug is never acceptable.",
        "Fee calculation is exact: 2% of 100,000 kobo is exactly 2,000 kobo; 2% of 33,333 kobo rounds by a documented rule, tested at the boundary.",
        "Formatting is correct for every supported magnitude, including zero and the smallest possible amount.",
        "The branded type prevents a raw number being passed where money is expected — verified by a type-level test.",
    ]},
    {"t": "h3", "text": "18.3.2 Ledger"},
    {"t": "bullets", "items": [
        "Every entry balances to zero. Tested with a property-based generator over random valid and invalid inputs.",
        "A posting that does not balance is rejected, and the rejection is atomic — a half-written entry is impossible.",
        "Entries are immutable: there is no API, typed or otherwise, that updates or deletes one.",
        "The sum of all entries equals the sum of all account balances equals the escrow balance. This is the invariant the entire system rests on.",
        "A reversal exactly cancels its original and preserves the original row.",
        "A reversal of a reversal is handled, and the audit trail remains coherent.",
        "Balances are computed from entries, not read from a mutable column — proven by a test that mutates a balance column and asserts that reconciliation fails.",
    ]},
    {"t": "h3", "text": "18.3.3 State machines"},
    {"t": "bullets", "items": [
        "Every legal transition succeeds; **every illegal transition is rejected**. Exhaustive enumeration, not a selection of examples.",
        "The enrollment window is exactly 5 days, tested at 4d 23h 59m and at 5d 0m 1s.",
        "Position lock is permanent: no sequence of events can unlock or remove a locked position.",
        "No transition bypasses a payment prerequisite. This is the test that catches the most expensive class of bug in this product.",
        "Terminal states are terminal. `COMPLETED` and `CANCELLED` have no outgoing transitions.",
        "A property-based test asserts that no reachable state violates any declared invariant, across a randomly generated space of event sequences.",
    ]},

    {"t": "h2", "text": "18.4 Property-based and fuzz testing"},
    {"t": "p", "text": "Example-based tests check what the author imagined. Property-based "
     "tests check what the author did not, and for a financial domain they find real bugs."},
    {"t": "table", "head": ["Property", "Assertion", "Why it matters"], "widths": [1.7, 2.4, 2.4], "size": 8.2, "rows": [
        ["Ledger conservation", "Σ debits = Σ credits for every entry, always", "A breach means money is invented or destroyed"],
        ["Non-negativity", "No member's escrow position is ever negative", "A negative balance is a debt the member did not agree to"],
        ["Monotonicity of contribution", "A contributed position never becomes less contributed", "Progress must never appear to go backwards"],
        ["Terminal irreversibility", "A terminal state has no outgoing transition", "A completed Ajo must not re-open"],
        ["Idempotency", "Applying the same operation twice equals applying it once", "The single most important property in the system"],
        ["Ordering independence", "Replaying events in a different order converges to the same state", "Webhook reordering must not corrupt anything"],
        ["Monotonic clock safety", "Behaviour does not depend on wall-clock order beyond declared time windows", "Timezone and clock-skew bugs are subtle"],
    ]},

    {"t": "h2", "text": "18.5 Integration tests"},
    {"t": "bullets", "items": [
        "**Repository tests against a real PostgreSQL instance** — a containerised database, not SQLite and not a mock. RLS policies, constraints, and triggers do not exist in a mock, and testing them against a mock tests nothing.",
        "**Transaction semantics** — a failure mid-transaction leaves nothing behind. Tested explicitly.",
        "**Constraint enforcement** — a negative amount, a duplicate reference, or an over-credit is rejected by the database, not merely by the application.",
        "**RLS policy tests** — run as each role, asserting both that permitted rows are visible and that forbidden rows are invisible. A test that only checks the permitted case is a test that proves nothing.",
        "**Queue and worker integration** — a job is enqueued, executed, and marked complete; a failing job retries and eventually dead-letters.",
        "**Idempotency at the API boundary** — the same idempotency key sent twice, concurrently, produces one result.",
    ]},

    {"t": "h2", "text": "18.6 Provider contract tests"},
    {"t": "p", "text": "Every `FinancialProvider` adapter is validated against one shared "
     "contract test suite. This is what makes the abstraction real rather than aspirational, "
     "and it is the mechanism by which a provider can be replaced without discovering "
     "unexpected behavioural differences in production."},
    {"t": "bullets", "items": [
        "The same suite runs against the mock and against a sandbox provider, so a new adapter is validated by running one command.",
        "Contract tests cover: payment initiation, webhook signature verification (including a valid signature over a tampered body), status queries, transfers, reversals, account resolution, and error taxonomy mapping.",
        "Provider-specific error codes must be mapped to a platform error taxonomy. An unmapped error is a contract failure, not a runtime surprise.",
        "Timeouts, 5xx responses, and malformed payloads are all part of the contract.",
    ]},

    {"t": "h2", "text": "18.7 End-to-end tests"},
    {"t": "p", "text": "E2E coverage is deliberately narrow. These are the journeys whose "
     "failure would end the business, and each is run against the mock provider so the "
     "suite is fast, deterministic, and free."},
    {"t": "table", "head": ["Journey", "Assertions"], "widths": [2.2, 4.3], "size": 8.2, "rows": [
        ["Register and verify", "Account is created, verification token works once, terms are recorded with a version and timestamp"],
        ["Create an Ajo", "All parameters validated, 5-day enrollment opens, organizer rules apply, Ajo appears as DRAFT"],
        ["Join with an invite", "Invite validates, position is assigned, enrollment counted, the invite is single-use"],
        ["Contribute", "Fee is calculated exactly, total charged matches, webhook confirms, position becomes funded, member notified"],
        ["Complete a cycle and pay out", "All contributions collected, round advances, payout released on time, all members paid, Ajo COMPLETED"],
        ["Handle a default", "Reminder escalation fires, 48-hour grace applies, member is recorded as defaulted, recovery offer is made"],
        ["Dispute a transaction", "Dispute is raised, evidence is attached, timeline is complete, resolution is notified"],
        ["Change a bank account", "Cooling-off is applied, all channels are notified, the payout is blocked during the window"],
        ["Concurrent double-tap", "Two simultaneous payment requests with the same idempotency key produce exactly one capture"],
    ]},

    {"t": "h2", "text": "18.8 Security testing"},
    {"t": "bullets", "items": [
        "**Automated dependency scanning** in CI, with a defined remediation SLA by severity.",
        "**Static analysis and secret scanning** on every commit, blocking the merge.",
        "**Authorisation tests as part of the suite** — an automated matrix that attempts each action as each role and asserts the expected allow or deny. This is the test class most often skipped and most valuable.",
        "**IDOR tests** — sequential and guessable identifiers are probed to confirm they cannot be used to reach another member's data.",
        "**Mass assignment tests** — a request cannot set fields the client is not permitted to set, particularly role, balance, and status.",
        "**Injection tests** — SQL injection, XSS, and command-injection probes against every input surface.",
        "**Independent penetration test** before launch and at least annually, scoped to cover authentication, authorisation, payout initiation, and webhook handling.",
    ]},

    {"t": "h2", "text": "18.9 Performance and load testing"},
    {"t": "table", "head": ["Scenario", "Profile", "Pass criteria"], "widths": [1.8, 2.3, 2.4], "size": 8.2, "rows": [
        ["Payout day", "A single Ajo of 500 members releases all payouts simultaneously", "p95 payout initiation < 2s; zero duplicates; zero lost"],
        ["Month start", "5,000 contributions in 60 seconds", "p95 API latency < 400ms; no queue backlog beyond the burst window"],
        ["Seasonal peak", "10x normal volume", "Graceful degradation, not failure. SLOs may breach; correctness may not"],
        ["Provider slowness", "Provider p99 at 10s", "No timeouts leaking into user-facing errors; jobs queue rather than fail"],
        ["Webhook flood", "Duplicate webhooks at 10x the expected rate", "No double capture; deduplication holds under load"],
        ["Notification burst", "50,000 money events", "Delivery within 5 minutes; rate limits respected"],
    ]},
    {"t": "p", "text": "The passing criterion in every case includes **correctness**, not just "
     "latency. A load test that returns 500s is a failed test even if the latency target is "
     "met, and a load test that double-captures a payment is a catastrophic one."},

    {"t": "h2", "text": "18.10 Data and reconciliation tests"},
    {"t": "bullets", "items": [
        "A **nightly invariant test** in a production-like environment asserts: ledger sum = sum of member balances = escrow cash. A failure pages someone immediately.",
        "**Seeded reconciliation** — a known transaction history produces a known reconciliation report, byte for byte.",
        "**Reconciliation break injection** — a deliberate mismatch is introduced and the system is asserted to detect it, halt payouts, and raise the correct alert. A detector that has never been tested against a real break is not known to work.",
        "**Month-end close** is rehearsed against real data on a schedule, so the process is proven before it is needed.",
    ]},

    {"t": "h2", "text": "18.11 CI/CD quality gates"},
    {"t": "table", "head": ["Gate", "Threshold", "Blocks deploy"], "widths": [2.2, 2.4, 1.9], "size": 8.4, "rows": [
        ["Type check", "Zero errors", "Yes"],
        ["Lint", "Zero errors", "Yes"],
        ["Unit tests", "100% pass, coverage above 90% on the domain core", "Yes"],
        ["Integration tests", "100% pass", "Yes"],
        ["Contract tests", "100% pass against the mock provider", "Yes"],
        ["Security scan", "No critical or high unresolved", "Yes"],
        ["Secret scan", "Zero findings", "Yes"],
        ["E2E smoke", "100% pass on critical journeys", "Yes"],
        ["Build", "Succeeds", "Yes"],
        ["Bundle size", "Within budget", "Yes"],
        ["Visual regression", "No unintended diffs", "Yes"],
    ]},
    {"t": "p", "text": "A coverage number is a prompt for thought, not a target to game. The "
     "requirement that matters is that the money, ledger, and state-machine modules are "
     "thoroughly covered — a coverage percentage achieved by testing getters is worse than "
     "no number at all."},

    {"t": "h2", "text": "18.12 Manual and exploratory testing"},
    {"t": "p", "text": "Automation cannot find the bug nobody thought of. The following are "
     "performed on a schedule and are not optional because they are inconvenient."},
    {"t": "bullets", "items": [
        "**Exploratory testing** on every release, particularly around the money flows, with a chartered time box and findings written up.",
        "**Real device testing** — a genuine low-end Android phone on a mobile network, not only simulators. Emulators hide exactly the problems that matter here.",
        "**Poor-network testing** — throttled bandwidth, high latency, dropped connections, and packet loss during a payment.",
        "**Accessibility walkthrough** with a screen reader and with system font scaling at maximum.",
        "**Payment-rail matrix testing** — every rail, every failure mode, every retry.",
        "**Timezone and DST testing** — a member in a different timezone from the Ajo, and a device with an incorrect clock.",
        "**Long-cycle soak testing** — a full 10-round Ajo run end to end in a staging environment, so that the last round is tested and not just the first.",
    ]},

    {"t": "h2", "text": "18.13 Environments"},
    {"t": "table", "head": ["Environment", "Data", "Provider", "Purpose"], "widths": [1.3, 1.6, 1.4, 2.2], "size": 8.4, "rows": [
        ["Local", "Synthetic", "Mock", "Fast development; the default"],
        ["CI", "Synthetic, reseeded per run", "Mock", "Automated verification on every commit"],
        ["Staging", "Synthetic, realistic scale", "Provider sandbox if available, else mock", "Integration, migration rehearsal, load testing"],
        ["Pre-production", "Production-like, anonymised where possible", "Provider production rails, restricted to staff", "Final rehearsal. Real money movements on a controlled basis only"],
        ["Production", "Real", "Provider production", "Members"],
    ]},
    {"t": "p", "text": "The `MockFinancialProvider` **refuses to initialise when "
     "`NODE_ENV` is `production`**, and this is enforced in code and covered by a test. A "
     "mock provider in production is the kind of mistake that is discovered by members."},

    {"t": "h2", "text": "18.14 Test data"},
    {"t": "bullets", "items": [
        "All test data is synthetic and generated by a seed script. No production data is ever copied into a test environment.",
        "Test data is deliberately **awkward**: zero amounts, maximum amounts, very long names, unicode and emoji in names, expired documents, boundary dates, and duplicate references. Comfortable data tests nothing.",
        "Money test cases include the exact values from CANONICAL.md: NGN 1,000 + NGN 20 = NGN 1,020; NGN 10,000 pool.",
        "Identity test data uses clearly fictional values, so it can never be mistaken for a real person.",
    ]},

    {"t": "h2", "text": "18.15 Defect management"},
    {"t": "table", "head": ["Severity", "Definition", "Response"], "widths": [1.0, 2.8, 2.7], "size": 8.4, "rows": [
        ["S1 — Critical", "Money lost or duplicated; ledger broken; data breach; total outage", "Immediate. Payouts may be halted. Fix or roll back within hours"],
        ["S2 — High", "A journey is blocked for many members; incorrect financial figure shown", "Same day"],
        ["S3 — Medium", "A journey is blocked for some members; a workaround exists", "This sprint"],
        ["S4 — Low", "Cosmetic; minor inconvenience", "Scheduled"],
    ]},
    {"t": "p", "text": "Every S1 and S2 gets a blameless post-mortem. A financial defect that "
     "was fixed without understanding how it happened will recur, usually at a larger "
     "scale and at a worse moment."},

    {"t": "h2", "text": "18.16 Quality metrics"},
    {"t": "table", "head": ["Metric", "Target", "Note"], "widths": [2.2, 1.5, 2.8], "size": 8.4, "rows": [
        ["Escaped defects", "Declining trend", "The number that actually matters"],
        ["Escaped money defects", "Zero", "Any occurrence triggers a post-mortem and a test addition"],
        ["Test suite runtime", "< 10 min for the full CI run", "A slow suite gets ignored, and ignored suites rot"],
        ["Flaky test rate", "< 0.5%", "A flaky test trains the team to ignore red builds"],
        ["Domain core coverage", "> 90% with meaningful assertions", "Money, ledger, state machine only"],
        ["Mean time to detect", "Via monitoring", "Better than mean time to fix, because it is controllable"],
        ["Post-mortem actions closed", "100% within the agreed date", "An unclosed action is a defect waiting to happen"],
    ]},
]
