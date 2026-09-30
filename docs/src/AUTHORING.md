# Section authoring contract

Every section is a Python module at `docs/src/sections/sNN_slug.py` that exports
a module-level list named `BLOCKS`.

```python
BLOCKS = [
    {"t": "h1", "text": "1. Product Requirements Document"},
    {"t": "lead", "text": "Opening framing paragraph."},
    {"t": "h2", "text": "1.1 Executive Summary"},
    {"t": "p", "text": "Body text. Supports **bold**, *italic* and `inline code`."},
    {"t": "bullets", "items": ["Point one", "Point two"]},
    {"t": "numbers", "items": ["Step one", "Step two"]},
    {"t": "kv", "pairs": [("Label", "Value")]},
    {"t": "table", "head": ["A", "B"], "rows": [["1", "2"]], "widths": [2.0, 3.0], "size": 8.5},
    {"t": "code", "text": "ASCII diagram or snippet"},
    {"t": "callout", "kind": "LEGAL", "title": "Requires review", "text": "..."},
    {"t": "pagebreak"},
]
```

## Rules

1. **Read `docs/src/CANONICAL.md` first.** It is the source of truth. Never
   contradict it. Fee model, roles, state machines, API paths, entity names,
   notification names and the worked example must match it exactly.
2. One `h1` per section, numbered to match the section number. Start with it.
3. Number `h2` as `<section>.<n>` and `h3` as `<section>.<n>.<m>`.
4. Use tables wherever they beat prose. Tables are not decoration.
5. `callout` kinds: `NOTE`, `WARNING`, `LEGAL`, `ASSUMPTION`, `DECISION`.
   Use `LEGAL` for anything needing Nigerian professional review, `ASSUMPTION`
   for anything invented to fill a gap, `DECISION` for an open choice with
   trade-offs. Label; never state as fact.
6. Never claim regulatory compliance, approval, or provider capability as fact.
   Say "requires confirmation with ProvidusUnity" or "requires review by
   qualified Nigerian legal counsel".
7. Depth over breadth. A section with real tables, real numbers, real edge
   cases and real rationale beats a long shallow one. 800–2,000 words typical;
   the PRD, ERD, schema, API, security and risk sections should be longer.
8. Use `NGN 1,000.00` for money, never `$` or bare `₦` inside tables (the naira
   glyph renders unreliably). The naira sign is fine in prose.
9. No placeholder text. No "TBD" without an owner and a decision path.
10. Diagram in `code` blocks: keep lines under ~78 characters so they fit A4.

## Fee model — restated so you cannot get it wrong

- Member owing NGN 1,000 is charged **NGN 1,020.00**.
- NGN 1,000.00 is the contribution to the pool; NGN 20.00 is the 2% fee.
- The recipient receives the **base pool: NGN 10,000.00**, not NGN 10,200.00.
- Fee is never deducted from a member's contribution and never reduces a payout.
- Worked example: 10 members × NGN 1,000 × 10 rounds.
  Each member pays NGN 10,200.00 total. Recipient receives NGN 10,000.00.
  AJO.ng retains NGN 2,000.00. Total collected across the Ajo: NGN 102,000.00.
- Tagline is **"Your Ajo. Your Story."** Never "Save together. Take your turn."
