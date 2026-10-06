# DESIGN.md — AJO.ng web app

Register: **product** (see `PRODUCT.md`). Design serves the task; the only place
brand is allowed to be loud is the enrollment moment and the signed-out surfaces.

## 1. Theme

**Scene:** a market trader or family organiser checks, on a mid-range Android
phone in daylight, whether this week's contribution is due and whether the Ajo
they are building has filled its seats. Standing up, one hand, ten seconds.

That scene forces the answer: **light.** The canonical palette
(`#0B1F3A` Deep, `#146EF5` Primary, `#22C7D6` Cyan, `#FBBF24` Gold,
`#F4F7FB` Cloud, `#101828` Dark) is specified for a consumer finance product
used outdoors and shared with family members over WhatsApp. Deep navy is a
*surface*, not a background: it appears where the Ajo's state is being stated
(the lifecycle rail, the signed-out header), never as the app's body.

**Color strategy: Restrained, with one committed band.**
Neutrals carry the chrome; `Primary` is reserved for the one action available on
a screen; `Cyan` marks progress that is *happening* (seats filling, the window
draining); `Gold` marks money and time pressure. No decorative accent. If a
colour cannot be justified as a state, it is not used.

## 2. Palette

Brand hexes are fixed by CANONICAL §0 and are not mine to remix; OKLCH is the
implementation format.

| Token | OKLCH | Hex | Role |
|---|---|---|---|
| `--deep` | `oklch(23.93% 0.058 256.7)` | `#0B1F3A` | Lifecycle rail, signed-out header, dialogs' dark surfaces |
| `--primary` | `oklch(57.26% 0.218 259.8)` | `#146EF5` | The single primary action, links, focus ring, active nav |
| `--cyan` | `oklch(75.91% 0.125 204.8)` | `#22C7D6` | In-progress state: claimed seats, window drain, progress |
| `--gold` | `oklch(83.69% 0.164 84.4)` | `#FBBF24` | Money figures, countdown urgency, payout emphasis |
| `--cloud` | `oklch(97.50% 0.006 255.5)` | `#F4F7FB` | Page background, zebra rows, input wells |
| `--ink` | `oklch(20.99% 0.034 263.4)` | `#101828` | Body text |
| `--surface` | `oklch(100% 0 0)` | `#FFFFFF` | Cards, panels, table surfaces |
| `--line` | `oklch(91.5% 0.008 255)` | `#E4EAF3` | 1px rules, input borders |

Derived states (kept on the brand hues, never pure grey):

- `--primary-hover` `oklch(50% 0.218 259.8)` · `--primary-wash` `oklch(96% 0.03 259.8)`
- `--danger` `oklch(54% 0.19 25)` (a red on the same axis as brand blue, used for
  refusal and the cancelled lifecycle state only)
- `--success` `oklch(56% 0.14 155)` (confirmation only; never a CTA)
- `--cyan-wash` `oklch(95% 0.04 205)` · `--gold-wash` `oklch(95% 0.06 84)`

Contrast floor: `--ink` on `--cloud` = 15.9:1; `--surface` on `--deep` = 14.8:1;
`--primary` as link on `--surface` = 4.9:1. Muted text uses
`oklch(45% 0.02 260)` (≈7:1 on white) — never a light grey.

## 3. Typography

**One family for the product: Inter** (variable), because this is a UI and the
`product.md` register rule is explicit — display fonts in labels are a defect.
The personality is carried by *scale discipline and numerals*, not by a second
face.

- **Numerals:** `font-variant-numeric: tabular-nums` on every amount, count,
  position number and countdown. Money never animates (PRODUCT principle 2).
- **Scale (rem, fixed — no clamp in app UI):**
  `12 / 14 / 16 / 18 / 20 / 24 / 30 / 36` with ratio ≈1.2.
  H1 (screen title) 30/1.15 weight 650, tracking `-0.02em`;
  H2 (section) 20/1.3 weight 650; body 16/1.5 weight 400;
  label 14/1.4 weight 550; caption 12/1.4 weight 500 tracking `0.01em`.
- **Eyebrow:** used *once per screen at most* — the Ajo reference
  (`AJO-01A10E…`) and the status word. Not above every section.
- **Naira:** `₦1,000.00` with the symbol attached to tabular figures;
  kobo shown only where it matters (fees, refunds).

The one display exception is the **countdown** on the lifecycle rail, which is
set at 36px tabular and is the largest type in the app — deliberately, because
"how long do I have to fill this" is the app's most consequential number.

## 4. Layout

Single-column task flow, max content width `1120px`, gutters `16 / 24 / 32`.

```
┌────────────────────────────────────────────────┐
│  ◤ AJO.ng        My Ajos   [ + Create ]   (user)│  ← 56px sticky topbar
├────────────────────────────────────────────────┤
│  Dashboard                                     │
│  ┌──────────────────────────────────────────┐  │
│  │  LIFECYCLE RAIL  (Deep surface)          │  │  ← signature, §5
│  │  draft ● enrollment ● active ● …         │  │
│  │  seats 7/10        4d 11h left           │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  Due next                     Your position    │  ← two-up → stacked ≤720
│  ₦1,000.00 · Friday          Seat 3 · Round 1  │
│                                                │
│  Your Ajos                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │  ← auto-fit minmax(300px)
│  │ …        │ │ …        │ │ empty    │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└────────────────────────────────────────────────┘
```

Ajo Detail: rail first, then a **seat grid** (10 numbered squares, not a
progress bar — a seat is a discrete, claimable object and deserves a discrete
representation), then the roster table, then invitations.

Create Ajo: one page, field groups separated by rules, sticky footer with a
single `Continue` — not a 7-step wizard on the first pass; the wizard's steps
exist in the spec but a wizard with no validation feedback is worse than an
honest single form.

Mobile ≤720: topbar collapses to logo + avatar, rail stays full-bleed, seat grid
becomes 5×2, tables become stacked rows with the label inline.

## 5. Signature: the lifecycle rail

The one thing this app should be remembered for, and the one thing the demo
turns on.

A **Deep navy band** spanning the content width. On it, the Ajo's state machine
rendered literally — `draft · enrollment · active · round in progress ·
completed` — as nodes joined by a track. Past nodes are solid white, the current
node is a ringed Cyan dot with its label at 18/650, future nodes are 40% white.
`cancelled` and `frozen` replace the track with a `danger`/`gold` terminus.

Two live elements ride on it:

1. **The seat ticker** — `7 / 10` at 36px tabular, and beneath it ten seat
   pips. A claimed pip fills Cyan in 200ms when the count increments.
2. **The window countdown** — `4d 11h` with a thin Cyan→Gold drain line under
   the rail whose width is `remaining/total`. Under 24h the numerals turn Gold.

When the last seat fills, **the rail advances**: the `enrollment` node
collapses into `active`, the track between them draws left-to-right over 420ms
(`cubic-bezier(0.2, 0.8, 0.2, 1)`), the seat ticker settles, and the row
re-orders to the top of the dashboard. That single transition is the entire
argument of the product — *the group activated itself* — so it is the only
orchestrated animation in the app. Everything else is 150–250ms state
communication.

Reduced motion: the rail jumps to its new state with a 120ms crossfade; pips
change colour without transition; the drain line updates discretely.

## 6. Components & vocabulary

- **Button:** 40px tall, 8px radius, one `primary` per screen; secondary is a
  1px `--line` border on white; destructive is text-first until confirmed.
  Every button ships default / hover / focus-visible / active / disabled /
  loading.
- **Input:** 44px, 8px radius, `--cloud` well with `--line` border, focus ring
  `0 0 0 3px oklch(57.26% 0.218 259.8 / 0.25)`. Errors appear under the field,
  never only in a toast.
- **Status chip:** text + 6px dot, never colour alone.
- **Cards:** 12px radius, `1px solid --line`, **no drop shadow** (the ghost-card
  pairing is banned). Elevation, where needed, is `0 4px 12px rgb(16 24 40 / 8%)`.
- **Icons:** Lucide, 16/20px, stroke 1.75. One set, one weight.
- **Toasts:** bottom-centre on mobile, bottom-right on desktop, 4s, one at a time.
- **Empty states:** teach the next action ("This Ajo has 10 seats and 1 member.
  Invite the rest to open enrollment.") — never "No data".

Copy rules: sentence case, plain verbs, active voice, no filler. Buttons name
the action (`Invite members`, `Open enrollment`). Errors say what happened and
what to do, without apology.

## 7. Motion & interaction budget

| Moment | Motion | Duration |
|---|---|---|
| Lifecycle advance (the demo moment) | track draw + node swap | 420ms |
| Seat claimed | pip fill + ticker digit flip | 200ms |
| Button/input state | colour + 1px transform | 150ms |
| Panel/dialog open | fade + 8px rise | 180ms |
| Toast | rise 12px | 200ms |

Nothing else moves. No page-load choreography, no scroll-triggered reveals, no
countdown tick animation (the number updates once a minute; animating seconds
is noise in a finance UI). All transitions honour
`prefers-reduced-motion: reduce`.

## 8. Accessibility

WCAG 2.2 AA. Focus-visible ring on every control, 3px, 2px offset, `--primary`.
Hit targets ≥44px. Status never colour-only. The lifecycle rail is a single
`<ol>` with `aria-current="step"`, so a screen reader hears "Enrollment, current
step" rather than a div soup. The countdown is `aria-live="off"` (updated text
every minute would be hostile) but a seat-count change is `aria-live="polite"`.
