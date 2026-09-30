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

### The database

`migrations/` is the source of truth for schema. It was adopted from a working
database that had no version control, so the files are a `pg_dump` broken up by
dependency order rather than hand-written DDL — which is exactly why the runner
checksums them and refuses to proceed if one changes after being applied.

```bash
python3 scripts/migrate.py --db <name>            # apply pending migrations
python3 scripts/migrate.py --db <name> --status   # what is applied and what is pending
python3 scripts/migrate.py --db <name> --check    # fail if any applied file has drifted
python3 scripts/migrate.py --db <name> --baseline <prefix>   # adopt an existing schema
python3 scripts/test_migrations.py                # build a scratch DB and assert the invariants
python3 scripts/compare_schemas.py --a <x> --b <y>          # diff two databases
```

`npm run test:db` is the same thing. CI runs it against a real Postgres service
container, so the claim being tested is that the *database* refuses bad data, not
that the TypeScript would have caught it.

Things that will bite you:

- **Connection.** The scripts read `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD` and
  fall back to `sudo -n -u postgres` only when those are unset. Set them in CI; do
  not hardcode a connection.
- **Each migration is one transaction.** The runner hands the file to `psql
  --single-transaction`, so a failure rolls the whole file back and leaves the
  database as it was. This is why the files contain no `BEGIN`/`COMMIT` and why
  `seed_reference_data.py` does not emit them. A file that genuinely cannot run
  in a transaction opts out with a `-- no-transaction` marker, and says so in the
  runner output.
- **Baselining is for databases that have the schema but no history.**
  `--baseline 080` builds everything before `080` into a throwaway database,
  fingerprints both with `compare_schemas.py`, and only records the rows if they
  match object for object. It refuses on any difference, and it refuses again if
  the target already records some of those migrations, because a partial history
  means something the runner cannot guess. Recorded rows carry
  `baselined = true` and `duration_ms = 0`, so the ledger never claims a
  migration ran when it was only verified.
- **The prefix boundary is a sort order, not a string match.** `--baseline 080`
  means *everything sorting before `080`*, leaving `080` and `090` pending. A
  "does not start with the prefix" filter gets this wrong, because it sweeps in
  everything that is not `080` — including `090`, which sorts after it.
- **Never edit an applied migration.** The checksum in `app.schema_migrations`
  will no longer match and every deployment will halt. Add a new file.
- **The three roles are bootstrap, not migration** (`§9.2`). Run
  `psql -d <name> -f scripts/bootstrap_roles.sql`; it creates `ajo_migrator`,
  `ajo_app` and `ajo_analytics` and is safe to re-run, including against a role
  whose attributes were damaged. A role is cluster state, so a database restored
  onto a cluster without them must be able to come up before anyone migrates.
  `test_migrations.py` applies it before the role cases, because those cases
  would otherwise pass vacuously against the superuser that ran the migrations.
- **A `SECURITY DEFINER` function writes as its owner, and `FORCE ROW LEVEL
  SECURITY` binds the owner too.** So the 18 audit triggers on `app.audit_row()`
  insert into `audit_logs` as `ajo_migrator` and need a policy of their own. The
  failure mode is silent: the write is refused inside a transaction that rolls
  back, and nothing prints a warning. The policy lives in the bootstrap rather
  than in a migration because it names a cluster role, and a clean build may not
  have that role. Any new `SECURITY DEFINER` function that writes needs the same
  treatment, and a test that asserts the row was actually written.
- **A role with DML on every table is bound by policies, not by grants.** A table
  with RLS on and no policy for a command denies that command, so `INSERT` into
  `users` was refused until `096_rls_write_policies` added the self-owned
  policies. Five tables are still deliberately closed — `payments`, `payouts`,
  both ledger tables and `risk_events` — and the reason is in that migration and
  in `TODO.md`. Do not open one with a bare `GRANT`.
- **Two GUCs, and the audit trigger reads the one people forget.** The policies
  read `app.user_id`; `app.audit_row()` reads `app.actor_user_id` and
  `app.actor_type`. A request that sets only `app.user_id` writes an audit row
  with `actor_user_id` null and `actor_type` `'service'`, which is a correct
  record of a system action and a useless record of a person's.
- **To regenerate after a schema change**, run
  `python3 scripts/adopt_schema.py --from-db <name>` and
  `python3 scripts/seed_reference_data.py --from-db <name>`, then read the diff.
  These overwrite files, so commit the schema change first.
- **`ledger_postings.signed_kobo` is generated** from `side` and `amount_kobo`.
  Inserting it is an error, which is the point: a posting cannot lie about which
  way money moved.
- **Rules that span two tables need a trigger, not a CHECK.** A CHECK sees one
  row. The creator-is-a-member rule is the worked example: an
  `AFTER INSERT` trigger on `ajo_positions` binds the organiser to a seat, and a
  `DEFERRABLE INITIALLY DEFERRED` constraint trigger on `ajos` refuses to commit
  an Ajo whose organiser is not a member.

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
