-- The ledger write path, and the first thing written through it.
--
-- The adopted schema has every guarantee a money system needs and no way to
-- exercise one. `ledger_transactions` and `ledger_postings` carry
-- `ledger_transactions_append_only` and `ledger_postings_append_only`, a
-- deferred constraint trigger that refuses an unbalanced transaction, another
-- that refuses `payout.settled` without a preceding `payout.recognized`, and
-- `payments.fee_kobo` generated from the amount rather than accepted from a
-- caller. Every one of those is a wall with nothing behind it. Until this
-- migration there is no function in `app` that inserts a ledger row at all, and
-- both tables are closed to `ajo_app`, so the only way to write money history is
-- a superuser with `BYPASSRLS` -- which is precisely the person those triggers
-- were written to be unreachable by.
--
-- So this supplies the writer. Two functions, and the split between them is the
-- design:
--
--   * `app.post_ledger_transaction` is the primitive. It takes postings, proves
--     they balance, and writes them. It is granted to nobody outside `app`.
--   * `app.post_collection_capture` is the one real transaction shape, and it is
--     the only one granted to `ajo_app`.
--
-- The API therefore cannot say "post a debit of 500,000 to escrow". It can say
-- "this payment was captured", and the shape of what that means is decided here,
-- in the database, once. A grant straight to the primitive would make the ledger
-- schema a suggestion: the first code path that wanted a slightly different
-- entry would invent one, and the guarantee that survives is only that the
-- numbers added up somewhere.
--
-- ## What a capture is
--
-- BR-021 fixes the sequence and its order:
--
--   1. `contribution.received`  debit escrow_cash, credit contributions_receivable
--   2. `fee.recognised`         debit escrow_cash, credit fees_income
--   3. `payout.recognized`      debit contributions_receivable, credit payouts_payable
--   4. `payout.settled`         debit payouts_payable, credit escrow_cash
--
-- Steps 3 and 4 are payouts and are not written here; `assert_ledger_sequence`
-- already refuses step 4 without step 3, so nothing is lost by leaving both
-- alone. This migration writes steps 1 and 2, and the order matters within them
-- for the same reason it matters across the sequence: a reader who sees fee
-- income recognised before the contribution it was taken from is looking at an
-- entry that cannot have happened in that order.
--
-- Each step is its own `ledger_transactions` row and balances on its own. Not one
-- transaction of 10,200 splitting three ways -- because then "did the fee get
-- recognised" and "did the contribution get recognised" are the same question, and
-- a partial failure leaves no way to tell what did happen. Two rows that are
-- each independently balanced is the shape the spec asks for and the shape that
-- survives a crash between the two.
--
-- The money is not created by a capture. It arrives from the provider, and
-- `escrow_cash` is where it is until a payout moves it out. `contributions_
-- receivable` is the claim against it, which is why the pool sitting in escrow
-- is a liability to the members who paid it and not revenue: step 1 credits the
-- receivable for the contribution and step 2 credits `fees_income` for the fee
-- only. Ajo.ng's 2% is the whole of what is ever recognised as income on a
-- collection.
--
-- ## Why this is not the collection flow
--
-- It is the first money that has ever moved in this system, and it moves without
-- a provider, a webhook, or an endpoint. `payments.status = 'success'` is taken
-- as given here; something else has to set it, and that something is E3-04's
-- signed webhook. What this migration proves is that when a capture is
-- *recognised*, the resulting books are correct, itemised, and posted exactly
-- once. Building the provider seam before that would mean debugging a ledger bug
-- and a webhook bug in the same diff, and the ledger one is the one that matters.

-- ---------------------------------------------------------------------------
-- The primitive.
-- ---------------------------------------------------------------------------
--
-- `p_postings` is JSON rather than a table type because there is no composite
-- type for a posting and inventing one is more ceremony than the problem needs.
-- The shape is checked here and again by the constraints on `ledger_postings`, so
-- a malformed element is refused with a message naming the offending account
-- rather than by a cast error three frames later.
--
-- Everything is validated before anything is inserted. Not for tidiness: a
-- deferred balance trigger only fires at COMMIT, so a function that inserted and
-- then discovered the entries did not add up would have written rows that exist
-- only to be rolled back, and the error the caller sees would be about a
-- transaction that no longer does. Checking first means the rejection happens
-- before the first write, so there is nothing to undo.
CREATE FUNCTION app.post_ledger_transaction(
  p_kind                   ledger_entry_type,
  p_postings               jsonb,
  p_idempotency_key        text   DEFAULT NULL,
  p_actor_user_id          uuid   DEFAULT NULL,
  p_ajo_id                 uuid   DEFAULT NULL,
  p_round_id               uuid   DEFAULT NULL,
  p_member_id              uuid   DEFAULT NULL,
  p_payment_id             uuid   DEFAULT NULL,
  p_payout_id              uuid   DEFAULT NULL,
  p_reverses_transaction_id uuid  DEFAULT NULL,
  p_occurred_at            timestamptz DEFAULT NULL,
  p_memo                   text   DEFAULT NULL
) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, app, public
AS $fn$
DECLARE
  v_existing  uuid;
  v_txn        uuid;
  v_element    jsonb;
  v_account    ledger_account_kind;
  v_side       ledger_side;
  v_amount     bigint;
  v_total      bigint := 0;
  v_count      integer := 0;
  v_target     ledger_entry_type;
  v_occurred   timestamptz := COALESCE(p_occurred_at, now());
BEGIN
  -- Idempotency first, before any validation. A replay of a request that already
  -- succeeded must return the original transaction even if the caller has since
  -- changed what it is asking for -- otherwise a retry after a timeout is a way to
  -- post the same money twice under two different keys, which is the one thing the
  -- idempotency key exists to prevent. Validating first would make the retry fail
  -- on its own inconsistency instead of harmlessly returning what already happened.
  IF p_idempotency_key IS NOT NULL THEN
    SELECT id INTO v_existing
      FROM public.ledger_transactions
     WHERE idempotency_key = p_idempotency_key;

    IF FOUND THEN
      RETURN v_existing;
    END IF;
  END IF;

  IF p_postings IS NULL OR jsonb_typeof(p_postings) <> 'array' THEN
    RAISE EXCEPTION 'postings must be a JSON array, got %', jsonb_typeof(p_postings)
      USING ERRCODE = 'invalid_parameter_value';
  END IF;

  FOR v_element IN SELECT jsonb_array_elements(p_postings) LOOP
    v_account := (v_element ->> 'account_kind')::ledger_account_kind;
    v_side    := (v_element ->> 'side')::ledger_side;
    v_amount  := (v_element ->> 'amount_kobo')::bigint;

    IF v_amount IS NULL OR v_amount <= 0 THEN
      RAISE EXCEPTION
        'a posting of % kobo to % is not a posting; amounts must be positive',
        v_amount, v_account
        USING ERRCODE = 'check_violation',
              HINT = 'Postings carry the magnitude. The side carries the '
                     'direction. A negative amount is a double negative.';
    END IF;

    IF v_side = 'debit' THEN
      v_total := v_total + v_amount;
    ELSE
      v_total := v_total - v_amount;
    END IF;

    v_count := v_count + 1;
  END LOOP;

  IF v_count < 2 THEN
    RAISE EXCEPTION 'a ledger transaction needs at least two postings, got %', v_count
      USING ERRCODE = 'check_violation',
            HINT = 'Every entry moves money between accounts. A single posting '
                   'creates or destroys value, which is not something this '
                   'ledger can express.';
  END IF;

  IF v_total <> 0 THEN
    RAISE EXCEPTION
      'the postings do not balance: debits exceed credits by % kobo', v_total
      USING ERRCODE = 'check_violation',
            HINT = 'This entry was not written. BR-21: a one-sided entry is '
                   'rejected rather than posted.';
  END IF;

  -- CR-21, enforced here as well as by `assert_ledger_sequence`. The trigger only
  -- fires on rows that exist, so a reversal pointing at nothing would be caught by
  -- a foreign key at COMMIT rather than by a message that says what a reversal is.
  IF p_kind = 'reversal' THEN
    IF p_reverses_transaction_id IS NULL THEN
      RAISE EXCEPTION 'a reversal must name the transaction it reverses'
        USING ERRCODE = 'not_null_violation';
    END IF;

    SELECT kind INTO v_target
      FROM public.ledger_transactions
     WHERE id = p_reverses_transaction_id;

    IF NOT FOUND THEN
      RAISE EXCEPTION 'reversal references transaction %, which does not exist',
        p_reverses_transaction_id USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF v_target = 'reversal' THEN
      RAISE EXCEPTION
        'reversing a reversal is not a correction, it is an untraceable second one'
        USING ERRCODE = 'check_violation',
              HINT = 'Reversals are one level deep (CR-21).';
    END IF;
  END IF;

  INSERT INTO public.ledger_transactions (
    kind, ajo_id, round_id, member_id, payment_id, payout_id,
    idempotency_key, reverses_transaction_id, request_id, actor_user_id,
    occurred_at, memo
  ) VALUES (
    p_kind, p_ajo_id, p_round_id, p_member_id, p_payment_id, p_payout_id,
    p_idempotency_key, p_reverses_transaction_id,
    current_setting('app.request_id', true), p_actor_user_id,
    v_occurred, p_memo
  )
  RETURNING id INTO v_txn;

  -- Re-read rather than reuse the loop variables: the loop validated, this writes,
  -- and a single read of the same JSON is the source for both so they cannot
  -- disagree about what was asked for.
  INSERT INTO public.ledger_postings (
    transaction_id, account_kind, side, amount_kobo, member_id, round_id, memo
  )
  SELECT v_txn,
         (e ->> 'account_kind')::ledger_account_kind,
         (e ->> 'side')::ledger_side,
         (e ->> 'amount_kobo')::bigint,
         NULLIF(e ->> 'member_id', '')::uuid,
         NULLIF(e ->> 'round_id', '')::uuid,
         e ->> 'memo'
    FROM jsonb_array_elements(p_postings) AS e;

  RETURN v_txn;
END;
$fn$;

COMMENT ON FUNCTION app.post_ledger_transaction IS
  'The ledger primitive. Balanced by construction, idempotent on its key, and '
  'granted to nobody: callers use app.post_collection_capture, which fixes the '
  'entry shape. 105.';

-- ---------------------------------------------------------------------------
-- The first transaction written through it.
-- ---------------------------------------------------------------------------
--
-- Reads `payments.fee_kobo`, never computes it. The column is generated from the
-- contribution amount by a 2% half-up rule the schema already owns, and BR-010 and
-- `assert_fee_matches_payment` both exist to stop anyone recomputing it. A second
-- arithmetic path here would be a third thing that can disagree with the receipt.
--
-- The `FOR UPDATE` is what makes this safe to call twice concurrently. Two
-- webhook deliveries of the same provider event arriving at once would both read
-- `status = 'success'` and both post; the lock serialises them, and the second one
-- finds `v_already` already set. Without it, idempotency on the derived key would
-- still hold -- the unique index refuses the second insert -- but the caller would
-- get an exception rather than the transaction that already exists, and a webhook
-- handler that treats that as a failure retries forever.
CREATE FUNCTION app.post_collection_capture(
  p_payment_id    uuid,
  p_actor_user_id uuid
) RETURNS uuid[]
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, app, public
AS $fn$
DECLARE
  v_payment        public.payments%ROWTYPE;
  v_contribution   public.contributions%ROWTYPE;
  v_receipt_txn    uuid;
  v_fee_txn        uuid;
  v_already        uuid[];
BEGIN
  SELECT * INTO v_payment
    FROM public.payments
   WHERE id = p_payment_id
   FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'payment % does not exist', p_payment_id
      USING ERRCODE = 'foreign_key_violation';
  END IF;

  -- Anything already posted for this payment. Checked before the status test so
  -- that a replay of a capture whose payment has since been reversed returns the
  -- original transaction ids rather than refusing on a status that is no longer
  -- what it was.
  SELECT array_agg(id ORDER BY occurred_at) INTO v_already
    FROM public.ledger_transactions
   WHERE payment_id = p_payment_id;

  IF v_already IS NOT NULL THEN
    RETURN v_already;
  END IF;

  -- Only a provider-confirmed capture is recognised. `initiated`, `pending` and
  -- `unknown` are all unconfirmed, and `unknown` is the one that looks like an
  -- answer: it means we asked the provider and could not find out, which is
  -- exactly the state in which posting is a guess.
  IF v_payment.status <> 'success' THEN
    RAISE EXCEPTION
      'payment % has status %, and only a provider-confirmed success is recognised',
      p_payment_id, v_payment.status
      USING ERRCODE = 'check_violation',
            HINT = 'Setting status = ''success'' is the webhook''s job, and only '
                   'a signature-verified webhook may do it.';
  END IF;

  SELECT * INTO v_contribution
    FROM public.contributions
   WHERE id = v_payment.contribution_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'payment % references contribution %, which does not exist',
      p_payment_id, v_payment.contribution_id
      USING ERRCODE = 'foreign_key_violation';
  END IF;

  -- Step 1. The contribution itself: the cash is in escrow, and the claim on it
  -- moves from the member's obligation to the group. Debit escrow, credit the
  -- receivable, by the contribution amount only. The fee is step 2's business and
  -- mixing them here would make `fees.ledger_transaction_id` point at an entry that
  -- also contains something else.
  --
  -- `idempotency_key` is deliberately left NULL. The column is a foreign key to
  -- `idempotency_keys`, which is the HTTP request table: it records a caller, a
  -- route and a request hash. A capture is more often reached from a webhook than
  -- from a request, so there is no request to point at, and inventing a row there
  -- with a synthetic route to satisfy the constraint would put a fiction into the
  -- one table whose job is to record what actually happened. Idempotency comes from
  -- the payment instead -- the lock above and the check above it -- and the payment
  -- is the real business key: one capture per payment is the invariant, and no
  -- amount of retrying can produce a second one.
  v_receipt_txn := app.post_ledger_transaction(
    p_kind            => 'contribution.received',
    p_postings        => jsonb_build_array(
      jsonb_build_object('account_kind', 'escrow_cash',          'side', 'debit',
                         'amount_kobo', v_contribution.amount_kobo),
      jsonb_build_object('account_kind', 'contributions_receivable', 'side', 'credit',
                         'amount_kobo', v_contribution.amount_kobo)
    ),
    p_actor_user_id   => p_actor_user_id,
    p_ajo_id          => v_contribution.ajo_id,
    p_round_id        => v_contribution.round_id,
    p_member_id       => v_contribution.member_id,
    p_payment_id      => p_payment_id
  );

  -- Step 2. The 2%, itemised as its own entry. A separate transaction so that "was
  -- the fee recognised" is answerable on its own -- if it is missing, revenue is
  -- understated and a member's receipt does not match the books; if it were folded
  -- into step 1, that difference would be invisible.
  v_fee_txn := app.post_ledger_transaction(
    p_kind            => 'fee.recognised',
    p_postings        => jsonb_build_array(
      jsonb_build_object('account_kind', 'escrow_cash',   'side', 'debit',
                         'amount_kobo', v_payment.fee_kobo),
      jsonb_build_object('account_kind', 'fees_income',   'side', 'credit',
                         'amount_kobo', v_payment.fee_kobo)
    ),
    p_actor_user_id   => p_actor_user_id,
    p_ajo_id          => v_contribution.ajo_id,
    p_round_id        => v_contribution.round_id,
    p_member_id       => v_contribution.member_id,
    p_payment_id      => p_payment_id
  );

  -- The fee as a row of its own, pointing at the entry that recognised it. BR-010
  -- and `assert_fee_matches_payment` both make this row's numbers non-negotiable,
  -- and the link is what makes "which entry recognised this fee" answerable
  -- without a join on a memo string.
  --
  -- `fee_kobo` is not supplied: it is a generated column here as it is on
  -- `payments`, and inserting a value into one is an error rather than a warning.
  -- Both sides generate it from the same base and the same 2% half-up rule, and
  -- `assert_fee_matches_payment` exists to prove the two agree -- which is a
  -- stronger statement than copying one into the other and hoping.
  INSERT INTO public.fees (
    payment_id, contribution_id, contribution_amount_kobo,
    fee_rate_bps, status, ledger_transaction_id
  ) VALUES (
    p_payment_id, v_contribution.id, v_payment.contribution_amount_kobo,
    v_payment.fee_rate_bps, 'accrued', v_fee_txn
  );

  -- The obligation is discharged, so the contribution moves to paid, stamped with
  -- when the provider said it succeeded rather than when we noticed. Those are
  -- different instants and the later one is the one a member would argue about if
  -- a webhook was delayed by an hour.
  UPDATE public.contributions
     SET status     = 'paid',
         paid_at    = v_payment.provider_completed_at,
         updated_at = now(),
         version    = version + 1
   WHERE id = v_contribution.id;

  -- The round's stored aggregates, restated in the same transaction that changed
  -- the contribution. `assert_round_pool` is deferred to COMMIT and says so
  -- explicitly: this may come later in the transaction, but not in the next one.
  -- That note is written for exactly this statement.
  UPDATE public.rounds r
     SET base_pool_kobo = (
           SELECT COALESCE(sum(c.amount_kobo), 0)
             FROM public.contributions c
            WHERE c.round_id = r.id
              AND c.status = 'paid'
              AND c.superseded_at IS NULL
              AND c.deleted_at IS NULL
         ),
         fee_collected_kobo = (
           SELECT COALESCE(sum(c.fee_kobo), 0)
             FROM public.contributions c
            WHERE c.round_id = r.id
              AND c.status = 'paid'
              AND c.superseded_at IS NULL
              AND c.deleted_at IS NULL
         ),
         updated_at = now()
   WHERE r.id = v_contribution.round_id;

  RETURN ARRAY[v_receipt_txn, v_fee_txn];
END;
$fn$;

COMMENT ON FUNCTION app.post_collection_capture(uuid, uuid) IS
  'BR-021 steps 1 and 2 of a collection capture, in order, each balanced on its '
  'own, idempotent per payment. Steps 3 and 4 are payouts and are not written '
  'here. 105.';

-- ---------------------------------------------------------------------------
-- Grants.
-- ---------------------------------------------------------------------------
--
-- The primitive is closed to PUBLIC because PUBLIC includes every role in the
-- cluster, including the analytics role and any future reporting role. It is
-- granted to `ajo_app` because the capture function is `SECURITY DEFINER` and
-- needs to call it as its owner.
REVOKE ALL ON FUNCTION app.post_ledger_transaction(
  ledger_entry_type, jsonb, text, uuid, uuid, uuid, uuid, uuid, uuid, uuid,
  timestamptz, text
) FROM PUBLIC;
REVOKE ALL ON FUNCTION app.post_ledger_transaction(
  ledger_entry_type, jsonb, text, uuid, uuid, uuid, uuid, uuid, uuid, uuid,
  timestamptz, text
) FROM ajo_app;

-- The capture is the API's entry point. `ajo_app` can recognise a capture and
-- nothing else; it cannot post an arbitrary entry, and it cannot post anything at
-- all without a `payments` row the provider has already confirmed.
GRANT EXECUTE ON FUNCTION app.post_collection_capture(uuid, uuid) TO ajo_app;
REVOKE ALL ON FUNCTION app.post_collection_capture(uuid, uuid) FROM PUBLIC;

-- ---------------------------------------------------------------------------
-- Row-level access for the role that owns the two functions.
-- ---------------------------------------------------------------------------
--
-- Both functions are `SECURITY DEFINER`, so they read and write as
-- `ajo_migrator` -- which is not the superuser that applied the migrations, and
-- is not a `BYPASSRLS` role. Every table they touch has RLS enabled with a policy
-- that admits either the member who owns the row or platform staff, so as
-- `ajo_migrator` the functions see no rows at all and are refused every write.
--
-- The failure is quiet and total: `post_collection_capture` reports "payment
-- <uuid> does not exist" for a payment that demonstrably does, because the SELECT
-- that found nothing was the SELECT that RLS emptied. Nothing is written, so no
-- guard catches it, and the books stay correct while the feature is dead. A test
-- that inserts its fixture as the migration role and then calls the function as
-- the migration role passes; only calling it as the role the API actually uses
-- finds it.
--
-- This is the same shape as the policies migration 103 added for
-- `app.verify_login_credential`, which reads an Argon2id hash that no member may
-- read. That role is not an application role: no session ever assumes it, it
-- cannot log in, and the policies below are named after it so the next reader can
-- see that reading `payments` was deliberate rather than an oversight.
--
-- The policies are additive on purpose. They widen what `ajo_migrator` can see;
-- they do not widen what `ajo_api` or `ajo_app` can see, which is the part that
-- matters for the ledger. `ledger_transactions` and `ledger_postings` remain
-- staff-readable and member-invisible to every application role.
--
-- `fees` and `payments` are the only tables that get write access, and only the
-- two statements the capture needs: mark the contribution's payment recognised,
-- and itemise the fee. Everything else it does is a write to an aggregate that is
-- itself checked at COMMIT.

-- The capture reads a payment and its contribution, round and fee before it
-- decides anything, and marks the payment paid at the end.
CREATE POLICY payments_migrator_select ON public.payments
  FOR SELECT TO ajo_migrator USING (true);
CREATE POLICY payments_migrator_update ON public.payments
  FOR UPDATE TO ajo_migrator USING (true) WITH CHECK (true);

CREATE POLICY contributions_migrator_select ON public.contributions
  FOR SELECT TO ajo_migrator USING (true);
CREATE POLICY contributions_migrator_update ON public.contributions
  FOR UPDATE TO ajo_migrator USING (true) WITH CHECK (true);

CREATE POLICY rounds_migrator_select ON public.rounds
  FOR SELECT TO ajo_migrator USING (true);
CREATE POLICY rounds_migrator_update ON public.rounds
  FOR UPDATE TO ajo_migrator USING (true) WITH CHECK (true);

CREATE POLICY fees_migrator_select ON public.fees
  FOR SELECT TO ajo_migrator USING (true);
CREATE POLICY fees_migrator_insert ON public.fees
  FOR INSERT TO ajo_migrator WITH CHECK (true);
CREATE POLICY fees_migrator_update ON public.fees
  FOR UPDATE TO ajo_migrator USING (true) WITH CHECK (true);

-- The two ledger tables had no writer at all until this migration. They are given
-- INSERT and read-back only: the primitive validates the sum it just inserted
-- before returning, which is why it needs to read them back rather than trust its
-- own arithmetic.
CREATE POLICY ledger_transactions_migrator_insert ON public.ledger_transactions
  FOR INSERT TO ajo_migrator WITH CHECK (true);
CREATE POLICY ledger_transactions_migrator_select ON public.ledger_transactions
  FOR SELECT TO ajo_migrator USING (true);
CREATE POLICY ledger_postings_migrator_insert ON public.ledger_postings
  FOR INSERT TO ajo_migrator WITH CHECK (true);
CREATE POLICY ledger_postings_migrator_select ON public.ledger_postings
  FOR SELECT TO ajo_migrator USING (true);

-- ---------------------------------------------------------------------------
-- ---------------------------------------------------------------------------
-- Restate the fee aggregate before guarding it.
-- ---------------------------------------------------------------------------
--
-- The guard below is a deferred constraint trigger, so it does not run against
-- rows that already exist: it only fires when a round or a contribution is next
-- written. That is what makes this migration safe to apply to a live database,
-- and it is also the trap in it. A round whose stored fee total is already wrong
-- keeps its wrong number and becomes un-updatable -- the first ordinary write to
-- it fails, with an error naming a column the writer did not touch.
--
-- That is not hypothetical. On the adopted production database there is one
-- round, `base_pool_kobo` correct at 200000, and `fee_collected_kobo` sitting at
-- 0 against two paid contributions worth 4000 between them. The column was
-- created in `096` as a stored aggregate and nothing in the schema wrote it,
-- because until this migration nothing could. Applying the guard without
-- restating first would have left that round unable to accept a contribution.
--
-- So the correction is part of the migration rather than a one-off command run
-- against production. A migration is version-controlled, transactional and
-- recorded in the migration ledger; `UPDATE rounds SET ...` typed into a live
-- session is none of those three, and a money correction nobody can find in
-- version control is exactly the kind that gets made twice.
--
-- Only rows that disagree are touched, so this is a no-op on a database built
-- from these files alone -- where no round has ever existed -- and on any round
-- that is already correct. It runs before the guard is installed, so the one
-- statement that disagrees with the new rule is the statement that fixes it.
--
-- `assert_round_pool` needs no equivalent: `base_pool_kobo` was already being
-- restated by whatever wrote the contributions, and it agrees on the live data.

UPDATE public.rounds r
   SET fee_collected_kobo = COALESCE(booked.fee, 0)
  FROM (
    SELECT round_id, sum(fee_kobo)::bigint AS fee
      FROM public.contributions
     WHERE status = 'paid'
       AND superseded_at IS NULL
       AND deleted_at IS NULL
     GROUP BY round_id
  ) AS booked
 WHERE r.id = booked.round_id
   AND r.fee_collected_kobo IS DISTINCT FROM booked.fee;

-- ---------------------------------------------------------------------------
-- `rounds.fee_collected_kobo` had no enforcement at all.
-- ---------------------------------------------------------------------------
--
-- `assert_round_pool` guards `base_pool_kobo` and nothing guards this one, so it is
-- a stored aggregate that nothing restates and nothing checks: a number in the
-- revenue reporting that drifts from the fees actually booked, silently, until
-- someone reconciles the accounts by hand and finds it. `assert_round_pool` was
-- written for the sibling column and the failure mode is identical, so the guard is
-- written the same way.
CREATE FUNCTION app.assert_round_fee_collected() RETURNS trigger
LANGUAGE plpgsql
AS $fn$
DECLARE
  v_round  uuid;
  v_stored bigint;
  v_actual bigint;
BEGIN
  -- Named `id` here and `round_id` on `contributions`, for the same reason
  -- `assert_round_pool` names both: which column holds the round is a property of
  -- the table, not something the trigger should assume. `rounds` has no
  -- `round_id`, so reading it unconditionally is a runtime error on the first
  -- INSERT rather than a wrong answer.
  IF TG_TABLE_NAME = 'rounds' THEN
    v_round := NEW.id;
  ELSE
    v_round := COALESCE(NEW.round_id, OLD.round_id);
  END IF;

  SELECT fee_collected_kobo INTO v_stored FROM public.rounds WHERE id = v_round;

  SELECT COALESCE(sum(c.fee_kobo), 0)
    INTO v_actual
    FROM public.contributions c
   WHERE c.round_id      = v_round
     AND c.status        = 'paid'
     AND c.superseded_at IS NULL
     AND c.deleted_at    IS NULL;

  IF v_stored IS DISTINCT FROM v_actual THEN
    RAISE EXCEPTION
      'round % records % kobo of fees collected but its paid, unsuperseded '
      'contributions total % kobo of fee',
      v_round, v_stored, v_actual
      USING ERRCODE = 'check_violation',
            HINT = 'fee_collected_kobo is a stored aggregate. Restate it in the '
                   'SAME statement that changed the contributions; this trigger '
                   'is deferred to COMMIT.';
  END IF;

  RETURN NULL;
END;
$fn$;

COMMENT ON FUNCTION app.assert_round_fee_collected() IS
  'The guard `assert_round_pool` is for base_pool_kobo, applied to '
  'fee_collected_kobo, which had none. 105.';

CREATE CONSTRAINT TRIGGER rounds_fee_collected_matches
  AFTER INSERT OR UPDATE ON public.contributions
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION app.assert_round_fee_collected();

-- Same guard from the other side, so restating the round without restating the
-- contributions is caught as well. Without this the check only fires when a
-- contribution changes, and a bad UPDATE of `rounds` alone would pass.
CREATE CONSTRAINT TRIGGER rounds_fee_collected_selfcheck
  AFTER INSERT OR UPDATE ON public.rounds
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION app.assert_round_fee_collected();