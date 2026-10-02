# TODO — AJO.ng

Build plan for AJO.ng, derived from `AJO-ng-Complete-Product-Technical-Specification.docx`.

Every requirement below traces to the specification. Section numbers (`§1`, `§9.3`) refer to
the numbered sections of the DOCX; `FR-*`, `BR-*` and `NFR-*` are requirement IDs from §1;
`E*-**` are backlog items from §23. Nothing here is invented — if a task is not traceable to
the specification, it should not be in this file.

**Source of truth:** `docs/src/CANONICAL.md` for terminology, money rules, roles, states and
API surface. When this file and the specification disagree, the specification is right and
this file is a bug.

---

## How to read this

**Status legend**

| Mark | Meaning |
|---|---|
| `[x]` | Done and verified |
| `[ ]` | Not started |
| `[~]` | Partially done — note what is missing |
| `[!]` | Blocked on something outside engineering |

**Priority**

| Mark | Meaning |
|---|---|
| `P0` | Blocks everything else, or touches member money |
| `P1` | Required for MVP |
| `P2` | Required before public launch |
| `P3` | Post-launch |

**Rule of thumb**, from §23.1: *safety before money movement, money movement before
convenience, convenience before polish.* A beautiful interface on an incorrect ledger is a
liability.

**Two hard gates.** These are not engineering tasks and no amount of code substitutes for
them:

1. **No real money before the legal position is established** (§24.14, all 15 items).
2. **No money movement before the ledger and reconciliation are tested** (§22.1).

---

## Current state

| | |
|---|---|
| Specification | Complete — 26 sections, ~238k words, 445 tables |
| Domain core | 2,018 lines, 61 tests passing |
| Database | **0 of 40 tables built** |
| API | **0 of 66 endpoints built** |
| Web / admin | Not started |
| Mobile | Not started |
| Legal | **0 of 15 items cleared** |

Verified at `fe884ae`: `npm run verify` → 61/61 pass.

---

## Phase 0 — Foundation ✅

The financial core, built before any product surface. This is the most consequential
decision in the project: it is far cheaper to get the money right now than to migrate a live
ledger later.

- [x] Canonical business and financial specification (`docs/src/CANONICAL.md`)
- [x] Complete product and technical specification (26 sections, DOCX)
- [x] `E1-01` Money in integer kobo, branded, no floating point
- [x] `E1-02` NGN formatting and parsing across all magnitudes
- [x] `E1-03` Double-entry ledger with balanced postings
- [x] `E1-04` Reversal-only correction; no update or delete path
- [x] `E1-05` Balances computed from entries, never from mutable columns
- [x] `E1-06` Ajo lifecycle state machine with all transitions
- [x] `E1-07` Five-day enrollment window and position lock (`BR-001`, `BR-002`)
- [x] `E1-08` `FinancialProvider` interface
- [x] `E1-09` `MockFinancialProvider` with a production guard
- [x] `E1-10` Adversarial test suite
- [x] `E1-11` Balanced 2% fee posting for contribution capture — `entries.feeRecognised`
- [x] `E1-12` Fee reversal preserving recognised revenue — reversal test in `ledger.test.ts`
- [x] `E1-13` Payout recognition and settlement entries — `entries.payoutRecognized` / `payoutSettled`
- [x] `E1-14` Continuous invariant check — `assertSolvent()`
- [x] `E11-01` Repository, CI pipeline, and quality gates — private GitHub remote, pre-commit
      hook blocking unverified pushes via versioned `core.hooksPath`, and
      `.github/workflows/ci.yml` running `npm run verify` plus the specification
      structure and staleness checks on every push to `main`
- [x] Pre-commit hook blocking unverified pushes (`.githooks/pre-commit`)
- [x] CI workflow on push and pull request (`.github/workflows/ci.yml`) — `verify`, `db` and
      `spec` jobs, with `concurrency` cancelling superseded runs
- [x] CI green on the real remote — run 36777830629, all three jobs `success`
- [x] Reproducible specification build — `_normalise_zip()` pins zip entry timestamps, so
      an unchanged spec rebuilds byte-identically and the CI staleness gate is meaningful
- [x] Database invariants in CI — the `db` job builds a database from `migrations/` alone
      against a Postgres 16 service container and asserts 7 cases, because a rule enforced
      only in the domain code is a rule the first direct SQL write will break

**Note:** §23.3 and §22.2 have been reconciled with the code. See *Spec maintenance*.

---

## Phase 1 — Hardened core and legal position

Phase 1 has a legal exit criterion, not just an engineering one. The advice obtained here
determines whether AJO.ng may operate at all, and in what form.

### Engineering

- [ ] `E1-15` Reconciliation service — compare provider statement against ledger, daily
- [ ] `E1-16` Reconciliation break alerting — **halts payouts** on a break (`E3-09`)
- [ ] `E1-17` Fault-injection test proving a deliberately broken invariant is *detected*
- [ ] `E11-07` Migration strategy: expand-then-contract, no destructive change in one deploy
- [ ] `E11-02` Environments: local, CI, staging, pre-prod, production
- [ ] `E11-08` Secret management and rotation
- [ ] `E11-03` Structured logging with PII redaction **at source**
- [ ] `E11-06` Backups with a rehearsed restore (a backup never tested is not a backup)

### Legal and compliance — `[!]` blocked, requires qualified Nigerian counsel

Per §24.14. **All 15 items outstanding.** None is an engineering task.

- [ ] `!` 1. Regulatory characterisation and licensing determination, in writing
- [ ] `!` 2. Payments partner agreement executed, permitted use cases confirmed
- [ ] `!` 3. Custody position confirmed and account structure approved
- [ ] `!` 4. Terms of service drafted by counsel and approved
- [ ] `!` 5. Privacy notice and cookie notice drafted, published
- [ ] `!` 6. Ajo rules and organizer role agreement drafted and approved
- [ ] `!` 7. AML/CTF risk assessment completed, if legally required
- [ ] `!` 8. Data protection registration or notification made, if required
- [ ] `!` 9. Data processing agreements executed with every processor
- [ ] `!` 10. Retention schedule approved and implemented in the system
- [ ] `!` 11. Complaint procedure published and staffed
- [ ] `!` 12. Trademark search completed; name and marks protected
- [ ] `!` 13. Insurance arranged
- [ ] `!` 14. Staff contracts, confidentiality, IP assignment in place
- [ ] `!` 15. Advice on tax treatment of the fee and of contributions

**Build against current assumptions, adjust when counsel answers. Never treat any of this as
cleared.**

### Payments partner

- [ ] `!` `E3-01` ProvidusUnity technical due diligence — verified sandbox spec, published fee
      schedule, settlement behaviour — **or a documented decision to use a different provider**
- [ ] Never invent ProvidusUnity behaviour. `MockFinancialProvider` refuses production use for
      exactly this reason.

---

## Phase 2 — Payments spine

The first phase where real money can move. Everything before this is reversible.

### Database — 40 tables (§9.3), 576 columns, 145 indexes, 216 constraints, 73 triggers

The counts are the database's own, read back from `pg_class`, `pg_index` and `pg_constraint`.

- [x] **Size rule:** `position_count` between **5 and 20**, default 10, **creator included**
- [x] **Identity (7):** `users` `profiles` `admins` `sessions` `device_tokens` `roles` `role_assignments`
- [x] **Onboarding (5):** `invitations` `verification_checks` `verification_check_types` `document_types` `documents`
- [x] **Ajo core (6):** `ajos` `ajo_positions` `ajo_members` `rounds` `contribution_schedules` `contribution_frequencies`
- [x] **Money (5):** `contributions` `payments` `fees` `payouts` `payment_channels`
- [x] **Ledger (2):** `ledger_transactions` `ledger_postings` — postings sum to exactly zero
- [x] **Disputes (4):** `disputes` `dispute_messages` `dispute_evidence` `dispute_reasons`
- [x] **Risk and ops (5):** `risk_events` `reconciliation_runs` `support_tickets` `audit_logs` `platform_settings`
- [x] **Notifications (3):** `notifications` `notification_templates` `notification_preferences`
- [x] **Infrastructure (3):** `idempotency_keys` `webhook_events` `outbox_events`
- [x] **Reference data:** 4 frequencies, 6 roles, 3 payment channels, 10 document types,
      7 verification checks, 8 dispute reasons, 7 platform settings, 53 notification templates

All 40 tables are in `migrations/`, adopted from the existing schema and verified: CI builds a
database from the migration files alone and asserts the invariants against it (`npm run test:db`).

The working `ajo` database has been reconciled with that source of truth, rather than being
recreated, so its append-only ledger and audit history were never rewritten. `000`-`070` were
recorded as **baselined** after `scripts/compare_schemas.py` proved the live database already
matched them object for object; `080` and `090` were then applied for real. A clean build from
`migrations/` and the live `ajo` now agree on all 1641 catalogued objects across 10 categories,
and all 13 ledger postings and 42 audit rows are intact.

The comparison is deliberately strict, and being strict found something. An earlier version of
`compare_schemas.py` skipped the whole `public` schema when fingerprinting functions, on the
assumption that only extension internals lived there. That assumption was wrong: it hid
`public._t1_decode(uuid)`, a pg_dump helper that had leaked into the adopted database's `public`
schema and had no dependents. The filter now excludes extension members by extension membership
rather than by schema name, compares function bodies rather than just signatures, and also
compares trigger enabled state, policy roles and constraint validation. `095_pgdump_artifacts`
drops the stray helper, so the two databases agree with no ignore list at all. Backup of the pre-change state:
`/tmp/opencode/preserve/ajo_before_baseline.dump`.

Enforced by the database, not just by the domain:

- `ajos_position_count_within_bounds` — 5 to 20, with `position_count` defaulting to 10.
  Added `NOT VALID` on purpose: the adopted database holds one three-member Ajo ("Test Ajo")
  whose append-only ledger cannot be removed. `NOT VALID` enforces the rule on every INSERT
  and UPDATE while grandfathering that one row, rather than inventing two members and two
  rounds of history that never happened. The legacy Ajo is consequently frozen, which is the
  honest outcome — an Ajo of three can be retired but not made valid. Retiring it and running
  `VALIDATE CONSTRAINT` is the follow-up.
- `app.materialize_organizer_membership()` — the creator is bound to position 1, so a
  ten-member Ajo is one organiser and nine invitees
- `app.assert_organizer_is_member()` — a deferred constraint trigger refusing to commit an
  Ajo whose organiser is not a member of it
- `app.assert_draft_exit()` — at least 5 positions, and no more than 20, before DRAFT is left

- [x] Three roles, never one (`§9.2`): `ajo_migrator` (owns the schema, migrations only),
      `ajo_app` (DML, does **not** own tables so RLS holds), `ajo_analytics` (`SELECT` only).
      `scripts/bootstrap_roles.sql`, not a migration: a role is cluster state, and a database
      restored onto a cluster without these roles has to be able to come up before anyone
      runs a migration. Applied to `ajo`; 7 role cases assert it, including that the owner
      is neither superuser nor `BYPASSRLS` and that `ajo_app` sees 1 of 3 users where the
      owner sees 3.
- [ ] **Write path for the five tables `096` deliberately leaves closed.** `payments`, `payouts`,
      `ledger_transactions`, `ledger_postings` and `risk_events` have RLS and no `INSERT` policy,
      so a non-owner cannot write them. This is correct today and is *not* an oversight, but it
      means those tables are unwritable until the application layer that owns them exists. The
      spec's `§9.6` table is headed "Who can read a row", so its "Nobody" is a statement about
      `SELECT` and is not permission to write. No function in `app` writes any of the five --
      the only writer the migrations create is `app.audit_row()`, which writes `audit_logs`.
      The fix is `SECURITY DEFINER` functions that validate the entry (a balanced ledger
      transaction, a closed round, a settled payment), **not** a grant to a role that already
      holds DML on every table. `scripts/test_migrations.py` asserts these five stay closed, so
      a later "just grant it" cannot land unnoticed. Who may write a payout is a product
      decision and is not a detail to change in passing.
- [ ] Reconcile the column count: the adopted schema has **621** columns, the spec says 576.
      Tables, indexes, constraints, triggers and policies all match. Until this is resolved,
      treat the migrations as the source of truth for shape and the spec as the source of
      truth for intent, and log every divergence rather than assuming either is wrong.

### Identity — E2

- [x] `E2-01` Registration with email verification and consent capture
- [ ] `E2-02` BVN verification and liveness flow — the BVN is never stored in full
- [x] `E2-03` Phone normalisation to E.164 and uniqueness (`BR-030` one identity, one account)
- [ ] `E2-04` Account states: pending, active, frozen, suspended, dormant, closed
- [ ] `E2-05` Profile management and self-service data export
- [x] `E2-06` Login, refresh rotation, reuse detection

  Routes `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`,
  `GET /auth/sessions`, `DELETE /auth/sessions/:id`. EdDSA access tokens at 15
  minutes; the refresh token is opaque, hashed, and rotated on every use, with
  the spent-token ledger that makes a replay distinguishable from a forgery.

  Three things in here are unfinished, deliberately and with the reason:

  - **Now delivered by migration `104` and `packages/api/src/notifications.ts`.**
    Both security events are enqueued to `outbox_events` by a trigger on
    `audit_logs`, so the alarm is written by the same transaction that revokes the
    sessions and cannot be lost between the revocation committing and a worker
    noticing. A worker drains the outbox into one row per channel, leases them, and
    sends email. Security notifications ignore `notification_preferences` and quiet
    hours, deliberately: a mute anyone can set is a mute an attacker can set.
  - Still open there: **push and SMS have no provider.** Both rows are materialised
    and leased, then left `queued` rather than marked failed, because "failed" would
    be a false report about a channel nobody has integrated. They will be delivered
    when a provider exists — and the backlog accumulated in the meantime is
    deliberate, not a leak.
  - Refresh replacement reuses the 30-day window, so a session that is refreshed
    every 29 days can live indefinitely. The absolute limit (90 days) is enforced
    against `sessions.created_at` and is the real bound; if 12.4.3 is read as
    requiring the refresh window to be non-sliding as well, that is a change to
    `app.claim_refresh_token` and not to the API.
  - `12.4.3`'s five-session cap evicts the oldest; the spec does not say whether a
    sixth sign-in should warn first. It does not, and asking a member to confirm a
    sign-in is the kind of friction that teaches people to click through prompts.
- [ ] `E2-07` MFA — SMS OTP for sensitive actions, TOTP for staff
- [ ] `E2-08` Step-up authentication framework
- [ ] `E2-09` Device management and revocation
- [ ] `E2-10` Role and permission enforcement with RLS
- [ ] `E2-11` Staff access review tooling

### Payments — E3

- [ ] `E3-02` `ProvidusFinancialProvider` adapter
- [ ] `E3-03` Provider contract test suite
- [ ] `E3-04` Webhook verification, replay protection, idempotency, out-of-order handling
- [ ] `E3-05` Collection initiation and pending contribution flow
- [ ] `E3-06` Fee calculation and capture posting — itemised, never a hidden line
- [ ] `E3-07` Escrow and settlement account setup — **no member funds in operating accounts, ever**
- [ ] `E3-08` Daily reconciliation service and reporting
- [ ] `E3-09` Reconciliation alerting, with payouts halted on a break
- [ ] `E3-10` Refunds and reversals, including duplicate capture
- [ ] `E3-11` Unmatched inbound payment handling and aging
- [ ] `E3-12` Provider status polling as a webhook backstop
- [ ] `E3-13` Payment status query for members
- [ ] `E3-14` USSD or feature-phone fallback

### Payouts — E4

- [ ] `E4-01` Payout preconditions engine
- [ ] `E4-02` `PayoutIntent` state machine
- [ ] `E4-03` Single payout with ledger recognition then settlement
- [ ] `E4-04` Batch dispatch for a completing Ajo
- [ ] `E4-05` Retry with exponential backoff, then human review
- [ ] `E4-06` `HELD` state with bounded automatic release — a payout is never silently reduced
- [ ] `E4-07` Receipt and payout notification
- [ ] `E4-08` Member-initiated payout request
- [ ] `E4-09` Monthly and annual statements
- [ ] `E4-10` Payout reconciliation against bank statements

---

## Phase 3 — Member experience

### Ajo lifecycle — E5

- [ ] `E5-01` Create an Ajo with all parameters and validation — 5 to 20 members, default 10,
      `CHECK (position_count BETWEEN 5 AND 20)`; the creator occupies one of those positions
- [x] Ajo size rule enforced in the domain — `assertValidMemberCount`, 8 tests, `CAN §3`
- [ ] `E5-02` Ajo rules and acknowledgement record (`BR-004` complete-cycle commitment)
- [ ] `E5-03` Invitation generation, single-use validation (`BR-006` invitation only)
- [ ] `E5-04` Join and position assignment
- [ ] `E5-05` Five-day enrollment window with **boundary tests** (`BR-001`)
- [ ] `E5-06` Activation to `FUNDED` — positions lock here (`BR-002`)
- [ ] `E5-07` Round scheduling and advance
- [ ] `E5-08` Completion and Ajo closure — terminal states are terminal (`BR-009`)
- [ ] `E5-09` Cancellation before activation, with full refunds
- [ ] `E5-10` Ajo detail and history view
- [ ] `E5-11` Ajo completion record
- [ ] `BR-003` No unilateral post-activation exit — there is no mechanism, by design
- [ ] `BR-005` Terms immutable once active

### Contributions and defaults — E6

- [ ] `E6-01` Contribution schedule and due dates
- [ ] `E6-02` Collection flow with the fee shown as a separate line
- [ ] `E6-03` Position status: unpaid, pending, funded
- [ ] `E6-04` Reminder escalation schedule
- [ ] `E6-05` Default recording (`BR-016` fixed sequence)
- [ ] `E6-06` 48-hour grace period with recovery offer
- [ ] `E6-07` Organizer acknowledgement of a default
- [ ] `E6-08` Recovery payment flow
- [ ] `E6-09` Replacement member with debt assumption
- [ ] `E6-10` Assert no extra charge to other members (`BR-015`, `BR-018`)

The default sequence is fixed: reminder → retry → 48-hour grace → organizer notified → member
contacted → payment or default recorded. **No shaming** (`BR-014`), **no reputational
consequence**, and a default is private between the member, the organizer and platform risk.

### Notifications — E7

- [ ] `E7-01` Event model and taxonomy
- [ ] `E7-02` In-app notification centre and history
- [ ] `E7-03` Push delivery — APNs and FCM
- [ ] `E7-04` Email templates and delivery
- [ ] `E7-05` SMS fallback for critical events
- [ ] `E7-06` Money event templates, complete set
- [ ] `E7-07` Reminder scheduler with quiet hours and daily caps
- [ ] `E7-08` Preference centre, per channel and category
- [ ] `E7-09` Delivery logging, bounce handling, dead letters
- [ ] `E7-10` WhatsApp Business integration
- [ ] `E7-11` Localisation of templates

### Web — Next.js

- [ ] `P1` Design system and component library from `§5`, `§6`, `§7`
- [ ] `P1` Onboarding: registration, verification, consent
- [ ] `P1` Create and join an Ajo, with the fee disclosed pre-commitment (`BR-011`)
- [ ] `P1` Contribute — fee as a separate line, correct total, failure states handled
- [ ] `P1` Payout experience: receipt and statement
- [ ] `P1` Profile, bank accounts, settings — cooling-off enforced on bank changes
- [ ] `P1` Help and support with a documented escalation path
- [ ] Accessibility target: WCAG 2.2 AA, verified, not asserted

### Mobile — React Native / Expo

- [ ] `P2` Member app: Ajo list, contribute, payout status, notifications
- [ ] `P2` `E11-11` Build pipeline, signing, staged rollout
- [ ] Feature-phone reach is a deliberate consideration; USSD fallback is `E3-14`

---

## Phase 4 — Organizer and admin

### Organizer tools — E8

- [ ] `E8-01` Dashboard for their own Ajos only
- [ ] `E8-02` Invitation management
- [ ] `E8-03` Contribution status monitoring
- [ ] `E8-04` Member removal, **before activation only** (`BR-007`)
- [ ] `E8-05` Send reminders, as AJO.ng messages — never impersonating a member
- [ ] `E8-06` Default acknowledgement (`BR-020`)
- [ ] `E8-07` Ajo completion reporting
- [ ] `E8-08` Ajo history and reputation signals
- [ ] `E8-09` Messaging within the Ajo
- [ ] `BR-008` The organizer is not a guarantor — enforced in copy and in the disclaimer
- [ ] `BR-022` The organizer never handles the money

### Operations console — E9

- [ ] `E9-01` Admin: Ajo and member oversight
- [ ] `E9-02` Support lookup by transaction or member
- [ ] `E9-03` Reconciliation dashboard with break alerts
- [ ] `E9-04` Manual payout retry and destination reassignment
- [ ] `E9-05` Manual ledger correction — **reversal only** (`BR-025` no role edits the ledger)
- [ ] `E9-06` Risk queue with holds, reasons, deadlines
- [ ] `E9-07` Audit log viewer
- [ ] `E9-08` Dispute management
- [ ] `E9-09` Finance reporting and month-end close
- [ ] `E9-10` Role assignment administration
- [ ] `BR-023` Support never moves money

---

## Phase 5 — Trust and safety

Not deferrable to "after launch". The cooling-off period and multi-channel notification are
what stand between a legitimate member and a drained account.

- [ ] `E10-01` Bank-account change cooling-off, **14 days**
- [ ] `E10-02` Multi-channel notification of every sensitive change
- [ ] `E10-03` Risk engine v1 — interpretable scores **with reasons**, not a black box
- [ ] `E10-04` Velocity limits: contribution, Ajo count, payout count
- [ ] `E10-05` Device, phone, and bank graph analysis
- [ ] `E10-06` Sanctions and PEP screening
- [ ] `E10-07` Member reporting of organizers and messages
- [ ] `E10-08` Freeze that blocks sending but **never** receiving
- [ ] `E10-09` SAR workflow and filing — statutory deadline, named reporting officer
- [ ] `E10-10` Fraud metrics including false positive rate
- [ ] `E10-11` Anti-phishing messaging throughout the product

---

## Phase 6 — Platform

- [ ] `E11-04` Metrics, dashboards, alerting with runbooks
- [ ] `E11-05` Distributed tracing across the async boundary
- [ ] `E11-09` API versioning and backward compatibility
- [ ] `E11-10` Feature flags with an audit trail
- [ ] Operations runbook for §13.13, rehearsed before the pilot

---

## Phase 7 — Controlled pilot `[!]` gate

- [ ] `[!]` All Phase 1 legal items cleared
- [ ] `[!]` Payments partner agreement executed
- [ ] 10–20 trusted members, recruited personally, with real money
- [ ] At least three complete Ajo cycles to a real bank account, reconciled
- [ ] Runbook followed for the full pilot **without improvisation**
- [ ] At least one real default processed end to end
- [ ] Structured interviews with every pilot member
- [ ] All critical and high defects closed

A pilot exists to discover the assumptions that were wrong. If three cycles produce no
surprises, the pilot was not run properly — the cohort was too safe, or nobody was watching.

---

## Phase 8 — Public launch

- [ ] `[!]` Legal items cleared, pen test passed
- [ ] Open registration, with onboarding and verification proven at volume
- [ ] Independent penetration test — all critical and high findings closed
- [ ] Observability live, alerting routed to a real rota, runbooks written
- [ ] Operations staffed: reconciliation, support, risk
- [ ] Professional localisation of all financial and instructional content
- [ ] Pre-approved incident templates and a member communication process

---

## Out of scope for MVP (§22.10)

Do not build these. Each was considered and rejected on purpose.

- Corporate or institutional Ajos, employer partnerships
- Partial or graduated payouts — full payout or no payout
- Late-payment penalties, or charging other members for a default (`BR-015`)
- Public defaulters lists, shaming, reputational consequences (`BR-014`)
- Open social features: public profiles, member directory, follower graphs, feeds
- Unilateral post-activation exit (`BR-003`)
- Escrow in the legal sense — AJO.ng holds no member funds itself, pending determination
- Cryptocurrency, investment products, or any return on savings (`BR-027`, `BR-028`)
- Multi-currency — all money is NGN, all values integer kobo (`BR-031`)
- Native Android-only build
- An independent escrow agent as a launch dependency

---

## The money rules

Encoded in `packages/domain/src/money.ts` and `ledger.ts`, with tests that assert them. These
are not preferences.

- Everything is **integer kobo**. No floating point anywhere in the money path.
- The fee is **2%, added on top** (`BR-010`). NGN 1,000 → NGN 20 fee → NGN 1,020 charged, and
  the recipient still receives the full NGN 1,000 base pool. The fee never reduces a payout
  (`BR-012`).
- Rounding is **half-up in integer kobo**, expressed as `FEE_BASIS_POINTS`.
- **Every entry balances to zero on its own, or it is rejected** (`BR-013`). No update, no
  delete; a correction is a new reversing transaction.
- **Recognition is separate from settlement.** `payout.recognized` raises the liability,
  `payout.settled` moves the cash. Skipping recognition makes `assertSolvent` correctly report
  insolvency and halt disbursement (`BR-020`).
- Contribution and fee are **separate entries** so a refund can reverse one while keeping the
  earned fee. A bare `credit fees_income` with no debit is not a transaction.
- When a member pays *in*: **debit `escrow_cash`, credit `contributions_receivable`**.
- Idempotency on **every** money movement (`BR-024`).
- Money moves by **two events only** (`BR-032`): a contribution, and a payout.
- The **recognition sequence is mandatory and ordered** (`BR-021`): contribution.received →
  fee.recognised → payout.recognized → payout.settled. Steps are not skipped or reordered.
- A **payout failure is never hidden** (`BR-017`): it is surfaced to the member, escalated to a
  human, and visible in the ops console. A silently failed payout is a trust-ending event.
- The fee may **never** be raised silently (`BR-026`).
- **Invitation-only at MVP** (`BR-029`) — the one registration path is a single-use invitation.

---

## Engineering standards

**Stack:** TypeScript throughout. Fastify API, Next.js web/admin, React Native/Expo mobile,
PostgreSQL/Supabase, Redis/BullMQ. Modular monolith with a pure domain core. **No long-lived
financial work on serverless functions** — a payout that times out halfway is a payout nobody
can trace.

**Testing:** Vitest for units, testcontainers for integration against real PostgreSQL,
Playwright for end-to-end. The ledger needs adversarial tests, not coverage percentages.

**Definition of done** (§23.15): working, tested, reviewed, documented, observable, and
security-checked. Not "it works on my machine".

**Before every commit**

```bash
./scripts/commit.sh "message"    # stages, verifies, commits, pushes
```

The pre-commit hook runs `npm run verify` and refuses the commit on failure. It travels with
the repo via `core.hooksPath`, so a fresh clone is protected too.

**When editing the specification:** `docs/src/sections/*.py` are the source, the DOCX is a
build artefact. Rebuild with `python3 docs/src/build_spec.py` (2–4 minutes — detach with
`setsid`, and do not trust `pgrep -f build_spec.py`, which self-matches and reports a process
that has already exited). Commit the rebuilt DOCX.

---

## Cross-cutting requirements

Every phase inherits these. They are not a phase.

| Area | Requirement | Source |
|---|---|---|
| Money | Integer kobo, balanced entries, reversal-only correction | `BR-010`–`BR-013`, `BR-031` |
| Legal | Licensed, not a savings group, no implied return | `BR-027`, `BR-028` |
| Privacy | Consent records, DSR, retention enforced in the system | `§14`, legal item 10 |
| Security | RLS, MFA, step-up, cooling-off, PII redaction at source | `§12`, `§14` |
| Accessibility | WCAG 2.2 AA, verified | `§4` |
| Audit | Every sensitive action in `audit_logs` | `NFR-AUD-*` |
| Money copy | Correct about money; a placeholder in a payment flow is a defect | `§4` |

**Requirement coverage:** 148 `FR-*`, 31 `BR-*`, 40 `NFR-*`, 38 `US-*`, 40 tables, 66 endpoints,
15 legal items. When implementing, check the requirement is satisfied — do not assume.

---

## Spec maintenance

The specification is not self-updating, and drift is how a spec stops being trustworthy.

- [x] Update `§23.3` E1-11 → E1-14 to **Done** — verified, all four read `Done`
- [x] Update `§22.2` test count — 44 → 61 → **70**, kept in step with `npm test`
- [x] `§22.2` "Technical specification document: In progress" → **Complete**
- [x] Add a status column to the legal checklist that reflects reality — `§24` carries a
      `Status` column, and all fifteen items correctly read **Outstanding**
- [x] Rebuild the DOCX after any spec edit, and commit it — now enforced by CI, which fails
      when the committed DOCX differs from a fresh rebuild
- [x] Reconcile `§22.2` with the member-count rule so the roadmap and the DDL agree

---

## Open questions

Answers change the design. Chase them early.

1. **Does ProvidusUnity support the required rails,** and what are the real fees? If not, the
   adapter boundary keeps the cost of switching to engineering rather than redesign.
2. **Does holding member funds in a pooled account constitute custody?** If yes, the account
   structure, segregation, reconciliation and possibly licensing all change.
3. **What are the AML, KYC and SAR obligations, and who discharges them?** A reporting officer
   may be legally required, and the deadline is statutory.
4. **How is a default legally characterised** — breach, debt, or loss? Foundational, not an
   edge case.
5. **What is the tax treatment** of the fee and of contributions?
6. **What is the refund SLA** after a provider approves a reversal? No screen may state a
   timeframe that has not been confirmed.

---

## Immediate next steps

1. **Read the spec.** Skim §1 (PRD), §9 (schema), §11 (API) before building. 238k words
   generated from source has never been reviewed by a human.
2. ~~**Create the three roles** and their grants.~~ Done in `eb35903`: `scripts/bootstrap_roles.sql`
   creates them, `096_rls_write_policies` restores the two self-owned write paths the split
   removed, and seven cases assert the owner is neither superuser nor `BYPASSRLS` while
   `ajo_app` sees 1 of 3 users where the owner sees 3. **The five money, ledger and risk tables
   are still closed to writes by design** — see the item above. Nothing else in this list
   depends on them being open.
3. **Redis** is the last piece of local infrastructure still missing — needed for rate
   limiting, idempotency locks and the outbox worker. PostgreSQL is done and CI-verified.
4. **E2 identity**, then **E3 collection flow** with the mock provider.
5. **Start the legal engagement.** It is the critical path and it does not run through
   engineering. Every week it does not start is a week closer to the date it gates.
