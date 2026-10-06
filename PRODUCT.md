# PRODUCT.md

## Register

**Product.** This repository contains two surfaces:

- `docs/` — a marketing/brand surface (the generated specification and its landing material).
- `packages/web` (new) — the authenticated **product app**: Dashboard, My Ajos, Create Ajo, Ajo Detail.

Default register for design work is **product**, because the surface being built first is the signed-in application. A task that touches `docs/` marketing pages may override the register per task.

## What the product is

AJO.ng is a Nigerian digital platform for the *Ajo* (also *esusu*) rotating savings scheme: a group of 5–20 people contributes a fixed amount each round, and each round the whole base pool is paid to one member in turn. AJO.ng coordinates membership, the contribution schedule, the payout order, and the 2% platform fee.

The core state machine is `DRAFT → ENROLLMENT → ACTIVE ⇄ ROUND_IN_PROGRESS → COMPLETED`. Enrollment is **exactly five days**; if the seats do not fill in that window the Ajo cancels. The Ajo activates the instant the last seat is claimed — a system event, never an organizer button press.

## Who uses it

- **Organizer** — a trusted person in a savings group (market trader, community organiser, family coordinator) who creates the Ajo, sets the rules, invites members, and is accountable to the group for collections. Often on a mid-range Android phone, mobile data, sometimes intermittently connected.
- **Member** — someone who was invited by somebody they already trust. Their jobs: read the rules, accept or decline, see what they owe and when, pay, and watch their turn approach.

Their context is **money they cannot afford to lose, handled on behalf of people they know personally.** The emotional register is trust plus clarity, never excitement. Every figure on screen must be readable at a glance on a small screen in daylight.

## Primary tasks

| Screen | The one job |
|---|---|
| Dashboard | Know your position: what is due, what is next, which Ajo needs you |
| My Ajos | Scan the Ajos you belong to and their state |
| Create Ajo | Set rules once, correctly, before anybody is invited |
| Ajo Detail | See seats filling, the five-day window counting down, and the roster |
| Join Ajo | Read the rules, accept or decline, claim a seat |

## Brand personality

- **Grounded** — this is a familiar communal practice made dependable, not a crypto product.
- **Warmly authoritative** — a good treasurer: precise about money, generous in tone.
- **Legible before clever** — figures, dates and obligations outrank any visual idea.

Tagline (locked): **"Your Ajo. Your Story."** The alternative "Save together. Take your turn." is explicitly *not* used.

## Anti-references

- Neon/glassmorphic crypto dashboards and any "wealth growth" trading aesthetic.
- Generic SaaS blue-on-white admin templates with icon-in-a-circle cards.
- Gamified savings apps that treat money as playful (confetti on payment, streak badges).
- Dark-mode-by-default tooling aesthetics; this is a consumer finance app used in daylight.

## Strategic design principles

1. **The lifecycle is the story.** The status of an Ajo — draft, filling, active, cancelled — is the single most important thing on any screen, and it must be visible as a changing thing, not a static label.
2. **Money is never decorative.** Amounts are set in tabular figures, in kobo-accurate naira, always with the unit. No gradient numbers, no animated counters on money.
3. **The database is the source of truth, and the UI shows that.** Seats, windows and statuses come from the API. The interface never fakes a state the backend has not confirmed.
4. **Familiar components, exact states.** Buttons, inputs, dialogs and tables behave the way a Nigerian user has already learned elsewhere. Surprise belongs to the enrollment moment, not to the controls.
5. **Mobile first is structural**, not a scaled-down desktop: single column, large hit targets, sticky primary actions.

## Accessibility

- WCAG 2.2 AA: ≥4.5:1 body text, ≥3:1 large text, visible focus rings on every control.
- `prefers-reduced-motion` respected on every animation.
- Status is never conveyed by colour alone — the lifecycle stepper and seat grid always carry text.
