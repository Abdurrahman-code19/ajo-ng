# AJO.ng — Canonical Reference (source of truth for all 25 sections)

> Every section of the specification must match this file. If a section
> contradicts this, this file wins and the section is wrong.

## 0. Product identity

- **Name:** AJO.ng
- **Tagline:** *Your Ajo. Your Story.*
- **Founders:** Abdurrahman Lawal & Abdurrahman Oriolowo
- **Stage:** Pre-launch. No live transaction volume. No customer data.
- **Domain:** Digital platform for the Nigerian *Ajo* (also *esusu*) rotating savings scheme.
- **Category:** Savings / rotating-savings fintech.

### Brand palette (fixed)

| Token | Hex | Use |
|---|---|---|
| Deep | `#0B1F3A` | Primary brand surfaces, H1, hero backgrounds |
| Primary | `#146EF5` | Primary actions, links, H2, active states |
| Cyan | `#22C7D6` | Secondary accent, data-viz second series, progress |
| Gold | `#FBBF24` | Accent, warnings, "payout imminent" emphasis |
| White | `#FFFFFF` | Surfaces, text on dark |
| Cloud | `#F4F7FB` | Page background, zebra table rows |
| Dark | `#101828` | Body text |

Tagline direction **"Save together. Take your turn." is NOT used.** The locked
tagline is **"Your Ajo. Your Story."**

---

## 1. Revenue model — 2% platform fee on every contribution deposit

**This supersedes the "fee model not locked" note in the existing Year-1
financial model documents. Those documents should be reissued.**

Mechanic:
- A member owing a ₦1,000 contribution is charged **₦1,020**.
- **₦1,000** = the member's contribution to the round pool.
- **₦20** (2%) = AJO.ng platform fee, recorded as `fees_income`.
- The member whose turn it is receives the **base pool** (10 × ₦1,000 = ₦10,000),
  **not** the ₦10,200 collected.
- Fee is computed in kobo: `fee = (amount_kobo * 200 + 5000) / 10000` (half-up).
- Fee is **never** deducted from a member's contribution and **never** reduces a
  payout. The payout the member was promised is exactly the base pool.

### Worked example (must appear identically in every section that shows an example)

| Item | Value |
|---|---|
| Members | 10 |
| Contribution per member per round | ₦1,000.00 |
| Platform fee (2%) | ₦20.00 |
| **Total charged per member** | **₦1,020.00** |
| **Base pool paid to recipient** | **₦10,000.00** |
| Total collected in the round | ₦10,200.00 |
| Platform fee retained in the round | ₦200.00 |
| Rounds | 10 |
| Total paid in by one member | ₦10,200.00 |
| **Total received by recipient at their turn** | **₦10,000.00** |
| Platform fee over the full Ajo | ₦2,000.00 |
| Total collected across the Ajo | ₦102,000.00 |

**Disclosure rule:** the fee must be shown separately from the contribution on
every receipt, in every Ajo details screen, and in the invitation and join
confirmation, before the member commits.

### Year-1 scenarios (aligned to the existing financial model spreadsheet)

| Scenario | Ajos | Members | Contribution | Rounds | Deposits | Volume | Fee revenue @2% | Fee per Ajo |
|---|---|---|---|---|---|---|---|---|
| Conservative | 150 | 8 | ₦7,500 | 10 | 12,000 | ₦90,000,000 | ₦1,800,000 | ₦12,000 |
| Base Case | 300 | 10 | ₦10,000 | 10 | 30,000 | ₦300,000,000 | ₦6,000,000 | ₦20,000 |
| Growth Case | 600 | 12 | ₦12,000 | 10 | 72,000 | ₦864,000,000 | ₦17,280,000 | ₦28,800 |

Base case: **33,000 core payment events** (30,000 contributions + 3,000 payouts).
Monthly average contribution volume (base): ₦25,000,000 → **₦500,000 fee/month**.

### Margin warning (must appear in the revenue/financial material)

Gross fee revenue is not net revenue. Payment-partner charges for collection and
payout are **unknown and must be obtained in writing from ProvidusUnity**.
At 2% gross, a 1% collection charge plus per-payout fees could consume most or
all of the margin. This must be modelled before the fee is communicated to
members, because the fee cannot be raised later without renegotiating trust.

---

## 2. Roles (exactly six)

| Role | Scope | Can | Cannot |
|---|---|---|---|
| `user` | Own account | Create Ajos, join Ajos, pay, view own records | See others' Ajos, alter financial records |
| `ajo_organizer` | One Ajo | Invite/remove pre-activation members, send reminders, propose position order, request payout release | Withdraw member funds, control payouts, change settled records, guarantee another member's debt, act after Ajo completes |
| `ajo_member` | One Ajo | Pay contributions, see own commitment, raise a dispute, request replacement exit | Change payout order post-activation, unilaterally exit after activation |
| `support` | Platform | Read all records, contact members, assist disputes, **cannot** move money or alter financial records | Initiate/moderate payouts, change balances, override risk decisions |
| `risk_officer` | Platform | View risk events, place accounts/Ajos under review, freeze, approve or reject overrides, manage limits | Delete records, edit ledger, change fee configuration |
| `super_admin` | Platform | Manage roles, configure platform settings, emergency freeze | Bypass the append-only ledger or delete financial history |

**Hard rule:** no role, including `super_admin`, may edit or delete a ledger
entry. Corrections are made only by posting a reversing entry.

---

## 3. Ajo lifecycle state machine

`DRAFT → ENROLLMENT → ACTIVE ⇄ ROUND_IN_PROGRESS → COMPLETED`
with `CANCELLED`, `CANCELLING`, `FROZEN` as branches.

| From | Event | To | Guard |
|---|---|---|---|
| DRAFT | OPEN_ENROLLMENT | ENROLLMENT | ≥2 positions, contribution and frequency set |
| ENROLLMENT | CLOSE_ENROLLMENT | ACTIVE | every position filled, **or** day 5 reached |
| ENROLLMENT | (auto) | CANCELLED | day 5 reached with positions unfilled |
| ACTIVE | START_ROUND | ROUND_IN_PROGRESS | round number = previous + 1 |
| ROUND_IN_PROGRESS | COMPLETE_ROUND | ACTIVE or COMPLETED | full round funds collected **or** recovery path engaged |
| any non-terminal | FREEZE | FROZEN | reason recorded |
| FROZEN | UNFREEZE | ACTIVE | — |
| any non-terminal | CANCEL | CANCELLED | reason recorded |
| COMPLETED / CANCELLED | — | — | **terminal, no events accepted** |

**Enrollment window: exactly 5 days.** If every position is not filled by day 5,
the Ajo cancels and contributions are refunded in full.

**Payout positions lock on activation.** No member may change position after
activation. Reordering requires a formal replacement/transfer request.

---

## 4. Contribution and payment states

Contribution obligation: `PENDING → PAID → (settled)`, with
`OVERDUE → GRACE → DEFAULTED → RECOVERED | WRITTEN_OFF`.

Payment (provider-side): `INITIATED → PENDING → SUCCESS | FAILED | CANCELLED | REVERSED | UNKNOWN`.

Payout: `SCHEDULED → FUNDING → RELEASED → SUCCESS | FAILED → (retry) | HELD`.

### Default handling (fixed, matches existing business documents)

```
Reminder → retry (if supported) → 48-hour grace → organizer notified
→ member contacted → payment or default recorded → recovery process
```

- AJO.ng does **not** automatically charge other members extra.
- AJO.ng does **not** publicly shame or expose defaulting members.
- Defaulting is private between the member, the organizer and platform risk.

### Payout funding principle (fixed)

A payout is released **only** when the required round funds are fully collected
and available under the approved financial arrangement. If ₦100,000 is due and
only ₦90,000 is available, AJO.ng must **not** silently reduce the payout and
must **not** use corporate funds. The round enters `HELD` / pending-funding and
the recovery process begins.

### Ledger recognition sequence (fixed, mandatory order)

Every transaction must balance to zero or be rejected. Each numbered step below is
a **separate, self-balancing** entry — a one-sided "credit fees_income" is not a
transaction and will be rejected by the ledger.

Money in: member is charged ₦1,020 (₦1,000 contribution + ₦20 fee). Both
entries below are balanced, and between them they move ₦1,020 of cash.

```
1. contribution.received   debit escrow_cash 1,000,000
                           credit contributions_receivable 1,000,000
2. fee.recognised          debit escrow_cash 20,000
                           credit fees_income 20,000
```

Then, on the Ajo's payout date:

```
3. payout.recognized       debit contributions_receivable  / credit payouts_payable
4. payout.settled          debit payouts_payable           / credit escrow_cash
```

Note the direction on step 1: a member paying *into* the pool **debits** escrow
cash and **credits** the receivable, because the receivable (an asset, "owed by
members") is extinguished by payment. Step 3 reverses that side when the pot
becomes a liability owed *to* the member.

Skipping step 3 causes escrow to drain against a liability that was never
raised; the solvency assertion will (correctly) halt disbursement.
Omitting step 2 silently banks member contributions as platform revenue, which
overstates revenue by 2% of gross volume.

---

## 5. Core entities

`users`, `profiles`, `verification_checks`, `ajos`, `ajo_positions`,
`ajo_members`, `invitations`, `rounds`, `contribution_schedules`,
`contributions`, `payments`, `payouts`, `ledger_transactions`,
`ledger_postings`, `fees`, `notifications`, `notification_preferences`,
`disputes`, `documents`, `risk_events`, `audit_logs`, `admins`, `roles`,
`role_assignments`, `idempotency_keys`, `webhook_events`, `reconciliation_runs`.

Money columns are **always** `bigint` kobo, never `float`/`numeric`.
Every mutable table has `created_at`, `updated_at`, `deleted_at`.
Business tables are **versioned** (`version int`) for optimistic concurrency.
Ledger tables are **append-only** — no `updated_at`, no `deleted_at`.

---

## 6. API surface (v1, `/api/v1`)

| Group | Endpoints |
|---|---|
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/verify-email`, `/auth/otp/request`, `/auth/otp/verify`, `/auth/password/forgot`, `/auth/password/reset`, `GET /auth/sessions`, `DELETE /auth/sessions/:id` |
| Profile | `GET/PATCH /profile`, `GET /profile/financial-summary`, `POST /profile/avatar` |
| Verification | `POST /verification/identity`, `GET /verification/:id`, `POST /verification/bvn` |
| Ajos | `POST /ajos`, `GET /ajos`, `GET /ajos/:id`, `PATCH /ajos/:id`, `POST /ajos/:id/activate`, `POST /ajos/:id/cancel`, `POST /ajos/:id/freeze`, `POST /ajos/:id/unfreeze`, `GET /ajos/:id/summary` |
| Positions | `GET /ajos/:id/positions`, `POST /ajos/:id/positions/claim`, `POST /ajos/:id/positions/reorder`, `POST /ajos/:id/positions/lock` |
| Members | `GET /ajos/:id/members`, `POST /ajos/:id/members`, `DELETE /ajos/:id/members/:memberId`, `PATCH /ajos/:id/members/:memberId`, `POST /ajos/:id/members/:memberId/replace` |
| Invitations | `POST /invitations`, `GET /invitations`, `GET /invitations/:token`, `POST /invitations/:token/accept`, `POST /invitations/:token/decline`, `POST /invitations/resend` |
| Contributions | `GET /contributions`, `GET /contributions/:id`, `GET /ajos/:id/contributions`, `GET /ajos/:id/schedule`, `POST /contributions/:id/pay`, `POST /contributions/:id/retry` |
| Payments | `POST /payments`, `POST /payments/:id/verify`, `GET /payments/:id`, `GET /payments/:id/receipt` |
| Payouts | `GET /payouts`, `GET /payouts/:id`, `GET /ajos/:id/payouts`, `POST /payouts/:id/release` (organizer request) |
| Transactions | `GET /transactions`, `GET /transactions/:id`, `GET /statements` |
| Notifications | `GET /notifications`, `POST /notifications/:id/read`, `POST /notifications/read-all`, `GET/PUT /notification-preferences` |
| Disputes | `POST /disputes`, `GET /disputes`, `GET /disputes/:id`, `POST /disputes/:id/evidence`, `POST /disputes/:id/messages` |
| Webhooks | `POST /webhooks/payments` (provider → AJO.ng, signature-verified, unauthenticated) |
| Admin | `GET /admin/overview`, `GET /admin/users`, `GET /admin/ajos`, `GET /admin/disputes`, `GET /admin/risk`, `POST /admin/risk/:id/decision`, `POST /admin/users/:id/freeze`, `GET /admin/audit-logs`, `GET /admin/reports/*` |

Conventions: cursor pagination (`?cursor=&limit=`), `Idempotency-Key` header
required on every `POST` that moves money, RFC-7807-shaped error body, and
`X-Request-Id` echoed on every response.

---

## 7. Screen inventory

Marketing: Home, How It Works, Features, Safety & Trust, Fees, About, FAQ, Contact, Login, Register, T&C, Privacy.
App: Dashboard, My Ajos, Create Ajo wizard (7 steps), Join Ajo, Ajo Detail, Members, Schedule, Contributions, Payments, Payouts, Transactions, Notifications, Support, Disputes, Profile, Settings, Security, Help, KYC.
Admin: Overview, Users, Ajos, Disputes, Risk/Fraud, Verification, Reports, Audit Logs, Settings.

---

## 8. Notification catalogue (canonical)

| Event | Recipient | Push | Email | SMS | Timing |
|---|---|---|---|---|---|
| `account.registered` | user | ✔ | ✔ | — | immediate |
| `verification.approved` | user | ✔ | ✔ | — | immediate |
| `verification.failed` | user | ✔ | ✔ | — | immediate |
| `invitation.received` | invitee | ✔ | ✔ | ✔ | immediate |
| `member.joined` | organizer | ✔ | ✔ | — | immediate |
| `contribution.due` | member | ✔ | ✔ | optional | T-24h and T-2h |
| `contribution.received` | member | ✔ | ✔ | optional | immediate |
| `contribution.failed` | member | ✔ | ✔ | optional | immediate |
| `contribution.overdue` | member | ✔ | ✔ | ✔ | at due time |
| `contribution.grace_ended` | organizer | ✔ | ✔ | — | after 48h |
| `member.defaulted` | organizer | ✔ | ✔ | — | on default |
| `payout.upcoming` | recipient | ✔ | ✔ | ✔ | T-24h |
| `payout.released` | recipient | ✔ | ✔ | ✔ | on release |
| `payout.succeeded` | recipient | ✔ | ✔ | ✔ | on settlement |
| `payout.failed` | recipient + organizer | ✔ | ✔ | ✔ | on failure |
| `payout.held` | recipient + organizer | ✔ | ✔ | ✔ | on insufficient funding |
| `ajo.completed` | all members | ✔ | ✔ | — | on completion |
| `dispute.opened` / `dispute.resolved` | parties | ✔ | ✔ | — | immediate |
| `security.login_new_device` | user | ✔ | ✔ | — | immediate |
| `account.frozen` | user | ✔ | ✔ | ✔ | immediate |

SMS reserved for money-critical and security events. Push and email for the rest.

---

## 9. Open decisions (must be labelled as open, not invented)

| ID | Question | Owner |
|---|---|---|
| D-01 | Does the recipient receive the base pool (₦10,000) or the full collected pool (₦10,200)? | Founders — **base pool assumed in this spec** |
| D-02 | Is ProvidusUnity holding funds as principal, or must AJO.ng hold them? Determines licensing path. | Legal + Providus |
| D-03 | Exact Providus collection %, payout flat fee, and settlement timing. | Providus — **required before fee is publicised** |
| D-04 | Is BVN/CAC verification mandatory for all members, or only above a threshold? | Risk + Legal |
| D-05 | Who bears the fee at Ajo cancellation — is it refunded? | Founders + Legal |
| D-06 | Is the 2% fee tax-inclusive, and who remits VAT/WHT? | Tax adviser |
| D-07 | Refund SLA after Providus approves a reversal. | Providus + Legal |
| D-08 | Maximum Ajo size and maximum contribution cap (fraud limit). | Risk |
