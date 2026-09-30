# AGENTS.md

Working notes for anyone (human or agent) changing this repository.

## What this repository is

Two things that must never disagree with each other:

1. **`packages/domain`** — the financial core. Integer kobo, a balanced
   double-entry ledger, and the Ajo lifecycle. This is the part that touches
   members' money, so it is the part that is tested hardest.
2. **`docs/`** — the full product and technical specification, generated into
   `AJO-ng-Complete-Product-Technical-Specification.docx`.

`docs/src/CANONICAL.md` is the source of truth for terminology, the money
rules, roles, states and the API surface. When the code and the specification
disagree, the specification is wrong until proven otherwise — and the fix is to
change the text, not to quietly special-case the code.

## Commit and push after every edit

**Commit and push after every meaningful change.** Do not batch a session's
work into one commit at the end, and do not leave verified work sitting
uncommitted on the machine.

```bash
./scripts/commit.sh "Short imperative summary of the change"
```

The pre-commit hook runs `npm run verify` (typecheck plus 61 domain tests) and
**refuses the commit if it fails**. If a commit is rejected, fix the failure
rather than reaching for `--no-verify`. The only legitimate exception is a
change that genuinely cannot affect the build, and that should be said
explicitly in the commit message.

### Editing the specification

`docs/src/sections/*.py` are the source; the `.docx` is a build artefact.

```bash
python3 docs/src/build_spec.py   # takes roughly 2-4 minutes
```

Regenerate the `.docx` and commit it whenever you change a section file. A
spec change with no rebuilt `.docx` is a change nobody else will see.

Two failure modes worth knowing:

- **The build must be detached.** `nohup` is not enough; the surrounding
  process group can be killed on timeout. Use
  `setsid nohup python3 -u docs/src/build_spec.py > /tmp/build.log 2>&1 < /dev/null &`
  and poll the log.
- **Do not trust `pgrep -f build_spec.py`** to check whether the build is still
  running. It matches its own command line and will report a process that
  already exited. Check the log and the output file's timestamp instead.

Verify the output rather than assuming it built:

```bash
python3 -c "import sys,os; sys.path.insert(0,'docs/src'); from build_spec import check; raise SystemExit(check(os.path.abspath('AJO-ng-Complete-Product-Technical-Specification.docx')))"
```

## The money rules

These are not negotiable, and they are encoded in `packages/domain/src/money.ts`
and `ledger.ts` with tests that assert them.

- **Everything is integer kobo.** No floating point anywhere in the money path.
  `0.1 + 0.2 !== 0.3` in IEEE-754, and a one-kobo drift per operation becomes
  an unrecoverable member dispute.
- **The platform fee is 2%, charged to the member on top.** A NGN 1,000
  contribution means a NGN 20 fee and NGN 1,020 charged, while the recipient
  still receives the full NGN 1,000 base pool. The fee is never deducted from
  the pool.
- **Rounding is half-up in integer kobo**, expressed as `FEE_BASIS_POINTS` so
  the rate is a named constant rather than a literal `0.02`.
- **Every ledger entry balances to zero on its own, or it is rejected.** There
  are no update and no delete methods; a correction is a new reversing
  transaction. History is the product.
- **Recognition is separate from settlement.** `payout.recognized` raises the
  liability, `payout.settled` moves the cash. Skipping recognition makes
  `assertSolvent` correctly report insolvency and halt disbursement.
- **The contribution and the fee are separate entries** so a provider refund can
  reverse one while leaving the earned fee intact. A bare `credit fees_income`
  with no matching debit is not a transaction and `post()` rejects it.

When a member pays *in*, the direction is **debit `escrow_cash`, credit
`contributions_receivable`**. Getting this backwards means escrow drains
against a liability that was never raised.

## Known open items

These are open on purpose, and none of them is an engineering task:

- **All fifteen items on the pre-launch legal checklist in section 24.14 are
  outstanding.** Regulatory characterisation, licensing, custody, AML/KYC,
  data protection, retention, tax. They require qualified Nigerian legal and
  compliance professionals before launch, and they are the critical path.
- **ProvidusUnity's API, pricing, settlement timing and permitted account
  structures are unverified.** Never invent its behaviour. `MockFinancialProvider`
  refuses to construct under `NODE_ENV=production` for exactly this reason.
- **Page-level layout of the `.docx` is unverified.** LibreOffice and pandoc
  are not available in this environment, so pagination and TOC page numbers
  have not been checked. Open the file in Word and press Ctrl+A then F9 to
  populate the table of contents.
