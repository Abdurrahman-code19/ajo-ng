-- 107_provider_event_settlement -- the queue that turns a verified webhook into
-- money, and refuses to do it when the webhook does not add up.
--
-- Spec §13.5, the two rows migration 106 could not reach:
--
--   Fast acknowledgement  -- "Verify, persist to a queue, return 2xx. Business
--     processing happens asynchronously. A slow webhook handler causes provider
--     retries and duplicate risk."
--
--   Amount and reference check -- "The received amount, currency, and reference
--     must match the pending contribution. A mismatch is escalated to
--     reconciliation, not silently accepted."
--
-- 106's own comment said neither was enforced and that saying so was better than
-- a function that looked like it did. That is what this migration changes, and
-- the first half of the change is structural: the HTTP handler cannot post the
-- capture, because the handler returns 2xx before this file runs.
--
-- Three new problems have to be solved to get there.
--
-- 1. THE QUEUE NEEDS A LEASE. Two API instances draining the same event would
--    both settle it. The notification queue in 104 solved this with
--    `FOR UPDATE SKIP LOCKED` plus a lease written into `next_retry_at`, and this
--    reuses that shape deliberately rather than inventing a second one: an event
--    whose worker died mid-processing has `next_retry_at` in the past and is
--    reclaimed by the next drain.
--
-- 2. THE VALUES TO MATCH ON HAVE TO BE RECORDED. 106 stored the raw payload and
--    nothing else, so the amount and reference could only be re-extracted by
--    re-parsing a payload with an adapter that may have changed in the two years
--    a 90-day-old webhook can still be replayed. They are recorded once, at the
--    moment the signature was verified and the adapter's parse produced them, and
--    settlement reads the recorded values.
--
--    The alternative -- matching inside this function by reading provider-specific
--    paths out of `raw_payload` -- would put a guessed ProvidusUnity field name in
--    the one function that moves money, and it would be wrong the moment the
--    adapter was written.
--
-- 3. THE MONEY RULE BELONGS IN THE DATABASE. The reference match, the amount
--    match, the currency match and the terminal-state resolution are four rules
--    that must hold no matter which language, or which future service, calls this.
--    So they are here, where they can be tested against a real database, rather
--    than in a handler that a future refactor could quietly weaken.
--
-- What this migration deliberately does NOT do: it does not call the provider.
-- `getTransfer` exists on the seam as a reconciliation aid, but a query in the
-- middle of settlement would turn a webhook into a network call inside a
-- transaction holding a payment lock. Reconciliation is E3-08 and it queries the
-- provider outside any lock.

-- ---------------------------------------------------------------------------
-- The ingest, restated.
-- ---------------------------------------------------------------------------
--
-- Byte-for-byte the 106 body except for one column in one INSERT. Hand-rewriting
-- it from memory would be how `app.audit_row` below nearly lost its DELETE branch
-- and its no-op suppression, so this is the 106 text with a patch applied to it,
-- not a new implementation.

CREATE OR REPLACE FUNCTION app.ingest_provider_event(p_provider text, p_provider_event_id text, p_event_type text, p_occurred_at timestamp with time zone, p_raw_payload jsonb, p_received_at timestamp with time zone DEFAULT now())
 RETURNS TABLE(event_id uuid, is_new boolean)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE
  v_id     uuid;
  v_status public.webhook_processing_status;
  v_inserted boolean;
BEGIN
  IF p_provider IS NULL OR btrim(p_provider) = '' THEN
    RAISE EXCEPTION 'a provider event must name its provider'
      USING ERRCODE = '22004';
  END IF;

  IF p_provider_event_id IS NULL OR btrim(p_provider_event_id) = '' THEN
    RAISE EXCEPTION 'a provider event must carry a provider event id'
      USING ERRCODE = '22004';
  END IF;

  IF p_raw_payload IS NULL THEN
    RAISE EXCEPTION 'a provider event must retain its raw payload'
      USING ERRCODE = '22004';
  END IF;

  -- Replay protection, and the reason this is checked on the way *in*.
  --
  -- A signature stays valid forever: nothing about an old webhook makes it
  -- stop verifying. The only thing that stops an attacker who captured one from
  -- replaying it forever is refusing it once it is old. Five minutes is the
  -- specification's number (§13.5), and it is generous for a provider that
  -- retries promptly while still bounding the replay window.
  --
  -- A genuinely late delivery is refused rather than absorbed. That is the
  -- correct answer even though it means a provider outage longer than five
  -- minutes loses events: the events are not lost, they are unprocessed and
  -- replayable, and recovery is reconciliation rather than a silent acceptance
  -- of a stale success. Status-querying the provider is the tool for that.
  IF p_occurred_at IS NULL THEN
    RAISE EXCEPTION 'a provider event must carry the time it occurred'
      USING ERRCODE = '22004';
  END IF;

  IF p_occurred_at < now() - interval '5 minutes' THEN
    RAISE EXCEPTION
      -- Bare `%` placeholders. RAISE has no type specifiers -- `%s` does not mean
      -- "string" here, it substitutes the next argument and then emits a literal
      -- `s`, so this message used to read "past the 5 minutess replay window".
      -- That is `format()`'s syntax, not RAISE's, and the mistake is silent:
      -- the message still arrives, just wrong, and nothing else notices.
      'provider event % from % is % old, past the five-minute replay window',
      p_provider_event_id, p_provider,
      to_char(now() - p_occurred_at, 'MI:SS')
      USING ERRCODE = '22023';
  END IF;

  -- The insert is the deduplication. `ON CONFLICT DO NOTHING` against the
  -- (provider, provider_event_id) index means a redelivery collides here and
  -- returns the row that was already stored, rather than being refused -- and
  -- rather than being stored twice, which is what a duplicate would cost if it
  -- were allowed to drive a second capture.
  INSERT INTO public.webhook_events (
    id, provider, provider_event_id, event_type, signature_verified,
    raw_payload, status, attempts, occurred_at, received_at, created_at, updated_at
  ) VALUES (
    gen_random_uuid(), p_provider, p_provider_event_id, p_event_type,
    false, p_raw_payload, 'received', 0, p_occurred_at, p_received_at, now(), now()
  )
  ON CONFLICT (provider, provider_event_id) DO NOTHING
  RETURNING id INTO v_id;

  v_inserted := v_id IS NOT NULL;

  IF NOT v_inserted THEN
    SELECT e.id, e.status INTO v_id, v_status
      FROM public.webhook_events e
     WHERE e.provider = p_provider
       AND e.provider_event_id = p_provider_event_id;

    -- A redelivery of something already processed is recorded as a duplicate
    -- so that "how many times did the provider send this" is answerable, which
    -- is a provider-health question that otherwise has no data at all.
    IF v_status = 'processed' THEN
      UPDATE public.webhook_events
         SET status = 'duplicate',
             attempts = attempts + 1,
             updated_at = now()
       WHERE id = v_id;
    ELSE
      UPDATE public.webhook_events
         SET attempts = attempts + 1,
             updated_at = now()
       WHERE id = v_id;
    END IF;
  END IF;

  RETURN QUERY SELECT v_id, v_inserted;
END;
$function$;

COMMENT ON FUNCTION app.ingest_provider_event(text, text, text, timestamptz, jsonb, timestamptz) IS
  'Records an unverified provider event and deduplicates on (provider, '
  'provider_event_id), reporting whether this delivery was the first sighting. '
  '106. Superseded by 107 only to store occurred_at, which 106 validated and '
  'discarded; the body is otherwise unchanged from the 106 text.';

-- `format()` and `RAISE` take opposite placeholder syntax, and this file got it
-- wrong in both directions before it worked. `RAISE` has no type specifiers --
-- `%s` substitutes the argument and then emits a literal `s`, which is what
-- migration 106's error message did. `format()` is the other way round: there a
-- bare `%` is an error, because `format` expects `%s`, `%I` or `%L`, and `%` followed
-- by a space raises `unrecognized format() type specifier` at run time rather
-- than at migration time. Both are silent until the line executes, so both are
-- only found by a test that reaches them.

-- ---------------------------------------------------------------------------
-- Recorded values.
-- ---------------------------------------------------------------------------

-- `occurred_at` is here because 106 threw it away.
--
-- 106's `ingest_provider_event` takes the provider's own event timestamp, checks
-- it against the five-minute replay window -- and then does not store it. There
-- was nowhere to put it: `webhook_events` had `received_at` and `created_at` and
-- no column for when the provider says the thing happened.
--
-- That is invisible while the only consumer is a replay-window check on the way
-- in, and it stops being invisible the moment anything needs the event's own
-- time: `settled_at` would be stamped with our arrival time rather than the
-- provider's, a late delivery's age could not be re-checked, and the spec's
-- promise that unprocessed webhooks stay replayable for 90 days would be measured
-- from when we received them. Backfilled from `received_at`, which is the closest
-- thing available and is the same value the check above used.
ALTER TABLE public.webhook_events
  ADD COLUMN occurred_at       timestamptz,
  ADD COLUMN provider_reference text,
  ADD COLUMN amount_kobo        bigint,
  ADD COLUMN currency           text,
  ADD COLUMN reported_state     public.payment_status;

UPDATE public.webhook_events SET occurred_at = received_at WHERE occurred_at IS NULL;

COMMENT ON COLUMN public.webhook_events.occurred_at IS
  'When the provider says the event happened, not when we received it. Used for '
  'the five-minute replay window and stamped onto payments as the provider''s '
  'completion time. Stored from the first ingest -- 107; 106 validated it and '
  'discarded it.';

COMMENT ON COLUMN public.webhook_events.provider_reference IS
  'The transfer reference the provider sent, recorded once at verification. '
  'Matches public.payments.provider_reference within the same provider.';
COMMENT ON COLUMN public.webhook_events.amount_kobo IS
  'The amount the provider reported, in kobo, recorded once at verification. '
  'Compared against payments.charged_amount_kobo, which is what we asked the '
  'provider to collect -- contribution plus fee, not the contribution alone.';
COMMENT ON COLUMN public.webhook_events.currency IS
  'Currency the provider reported. Compared against the Ajo''s currency.';
COMMENT ON COLUMN public.webhook_events.reported_state IS
  'The transfer state the provider reported, mapped by the adapter. The value '
  'resolution starts from, not the value written: app.resolve_transfer_state '
  'decides which of the two survives.';

ALTER TABLE public.webhook_events
  ADD CONSTRAINT webhook_events_amount_non_negative
  CHECK (amount_kobo IS NULL OR amount_kobo >= 0);

-- The claim. Partial on the two states that are claimable, because a queue that
-- has been drained for the day should not be walked end to end to find nothing.
CREATE INDEX webhook_events_claim_idx
  ON public.webhook_events (next_retry_at)
  WHERE signature_verified AND status IN ('received', 'processing');

-- Reconciliation reads these in both directions: settling an event looks up the
-- payment by reference, and the reconciliation report reads the events behind a
-- reference.
CREATE INDEX webhook_events_reference_idx
  ON public.webhook_events (provider, provider_reference)
  WHERE provider_reference IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Verification now records what was verified.
-- ---------------------------------------------------------------------------
--
-- 106 marked the signature verified and moved the event straight to
-- `processing`, which conflated two things: an event that has been verified and
-- queued, and an event a worker has picked up. Both said `processing`, so there
-- was no way to ask which events were waiting, and a worker crash left an event
-- indistinguishable from one being worked on right now.
--
-- The signature changes, so the old function goes. Nothing calls it outside the
-- test suite -- the HTTP surface this is written for does not exist yet -- and
-- leaving both would leave two ways to record a verification, which is how the
-- next person picks the one that skips the amount.
DROP FUNCTION IF EXISTS app.mark_provider_event_verified(uuid, text);

CREATE FUNCTION app.mark_provider_event_verified(
  p_event_id           uuid,
  p_signature_algorithm text,
  p_provider_reference text,
  p_amount_kobo        bigint,
  p_currency           text,
  p_reported_state     public.payment_status
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, app, public
AS $fn$
DECLARE
  v_status public.webhook_processing_status;
BEGIN
  SELECT e.status INTO v_status
    FROM public.webhook_events e
   WHERE e.id = p_event_id
     FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'no provider event with id %', p_event_id
      USING ERRCODE = 'P0002';
  END IF;

  IF p_signature_algorithm IS NULL OR btrim(p_signature_algorithm) = '' THEN
    RAISE EXCEPTION 'a verified event must record which algorithm verified it'
      USING ERRCODE = '22004';
  END IF;

  -- The recorded values are what settlement matches on, so an event verified
  -- without them could never be settled and would sit in the queue until it aged
  -- out. Refusing here says so at the point where the caller can still fix it.
  IF p_provider_reference IS NULL OR btrim(p_provider_reference) = '' THEN
    RAISE EXCEPTION 'a verified event must record the provider reference it names'
      USING ERRCODE = '22004';
  END IF;

  IF p_amount_kobo IS NULL THEN
    RAISE EXCEPTION 'a verified event must record the amount the provider reported'
      USING ERRCODE = '22004';
  END IF;

  IF p_reported_state IS NULL THEN
    RAISE EXCEPTION 'a verified event must record the state the provider reported'
      USING ERRCODE = '22004';
  END IF;

  IF p_amount_kobo < 0 THEN
    RAISE EXCEPTION 'a verified event cannot report a negative amount (%)', p_amount_kobo
      USING ERRCODE = '22004';
  END IF;

  -- Already processed is not an error: a redelivery is verified again, and
  -- refusing would make the second delivery of a perfectly good webhook look like
  -- an attack.
  IF v_status IN ('processed', 'duplicate') THEN
    RETURN;
  END IF;

  -- Status stays `received`. Verification queues the event; the claim below is
  -- what makes it `processing`. See the note above.
  UPDATE public.webhook_events
     SET signature_verified    = true,
         signature_algorithm   = p_signature_algorithm,
         provider_reference    = p_provider_reference,
         amount_kobo           = p_amount_kobo,
         currency              = p_currency,
         reported_state        = p_reported_state,
         status                = 'received',
         updated_at            = now()
   WHERE id = p_event_id;
END;
$fn$;

COMMENT ON FUNCTION app.mark_provider_event_verified(uuid, text, text, bigint, text, public.payment_status) IS
  'Marks a provider event signature-verified and records the algorithm, the '
  'transfer reference, the amount, the currency and the state the provider '
  'reported. Only the API calls it, and only after verifying the HMAC over the '
  'raw body -- the database cannot verify a signature and has no secret. Queues '
  'the event as `received`; app.claim_provider_event picks it up. Idempotent, '
  'and idempotent for a redelivery of an event already processed. 107.';

-- ---------------------------------------------------------------------------
-- The claim.
-- ---------------------------------------------------------------------------

CREATE FUNCTION app.claim_provider_event(
  p_batch_size    integer DEFAULT 10,
  p_lease_seconds integer DEFAULT 300
) RETURNS SETOF public.webhook_events
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, app, public
AS $fn$
BEGIN
  -- Exhaustion, first, so an event that is past the ceiling is not handed out
  -- again on the way past.
  --
  -- `app.defer_provider_event` bounds its own retries, but it only runs on the
  -- paths that reach it. An event whose settlement *raises* -- a unique
  -- violation, say, two confirmed payments on one contribution -- never gets
  -- there: the caller's transaction rolls back, the event stays `processing`,
  -- and the next drain reclaims it. Nothing about a third attempt resolves it, so
  -- without this the row is claimed, raised, reclaimed, raised for as long as the
  -- queue runs, and `processing` is exactly what a stuck event looks like.
  UPDATE public.webhook_events e
     SET status       = 'failed',
         error_detail = format('gave up after %s attempts: the settlement raised and left nothing to read',
                               e.attempts),
         processed_at = now(),
         updated_at   = now()
   WHERE e.signature_verified
     AND e.status IN ('received', 'processing')
     AND e.attempts >= 8;

  RETURN QUERY
  WITH claimable AS (
    SELECT e.id
      FROM public.webhook_events e
     WHERE e.signature_verified
       AND e.status IN ('received', 'processing')
       AND e.attempts < 8
       AND COALESCE(e.next_retry_at, '-infinity') <= now()
     ORDER BY COALESCE(e.next_retry_at, '-infinity'), e.received_at
     LIMIT greatest(coalesce(p_batch_size, 10), 1)
       -- Skip locked, not block. Two workers running at once is the normal case,
       -- not the exception, and the second one must move on to the next event
       -- instead of waiting on the first.
       FOR UPDATE SKIP LOCKED
  )
  UPDATE public.webhook_events e
     SET status        = 'processing',
         attempts      = e.attempts + 1,
         -- The lease is written into `next_retry_at`, the same column the retry
         -- backoff uses. An event still `processing` when this timestamp passes
         -- has had its worker die, and the next drain reclaims it. One column for
         -- both jobs, so there is no second clock to disagree with.
         next_retry_at = now() + make_interval(secs => greatest(coalesce(p_lease_seconds, 300), 1)),
         updated_at    = now()
    FROM claimable c
   WHERE e.id = c.id
  RETURNING e.*;
END;
$fn$;

COMMENT ON FUNCTION app.claim_provider_event(integer, integer) IS
  'Claims up to p_batch_size verified events for processing and leases each for '
  'p_lease_seconds. Verified-but-unclaimed events are `received`; claiming makes '
  'them `processing`. Uses SKIP LOCKED so concurrent workers do not queue behind '
  'each other, and reclaims an event whose worker died. Anything at eight attempts '
  'is filed as failed here rather than claimed an ninth time, which also bounds '
  'the paths that raise instead of defer. 107.';

-- ---------------------------------------------------------------------------
-- Settlement.
-- ---------------------------------------------------------------------------

CREATE FUNCTION app.settle_provider_event(p_event_id uuid) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, app, public
AS $fn$
DECLARE
  v_event         public.webhook_events%ROWTYPE;
  v_payment       public.payments%ROWTYPE;
  v_contribution  public.contributions%ROWTYPE;
  v_currency      text;
  v_next          public.payment_status;
  v_actor_user_id uuid;
BEGIN
  SELECT * INTO v_event
    FROM public.webhook_events e
   WHERE e.id = p_event_id
     FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'no provider event with id %', p_event_id
      USING ERRCODE = 'P0002';
  END IF;

  IF NOT v_event.signature_verified THEN
    RAISE EXCEPTION 'provider event % has an unverified signature and cannot be settled', p_event_id
      USING ERRCODE = '42501';
  END IF;

  -- `processing`, not `received`. A verified event that nobody has claimed is
  -- waiting; settling it here would skip the lease and run concurrently with
  -- whichever worker does hold it.
  IF v_event.status <> 'processing' THEN
    RAISE EXCEPTION 'provider event % is % and is not claimed for processing', p_event_id, v_event.status
      USING ERRCODE = '42501';
  END IF;

  IF v_event.reported_state IS NULL OR v_event.provider_reference IS NULL THEN
    RAISE EXCEPTION 'provider event % was verified without the values settlement needs', p_event_id
      USING ERRCODE = '42501';
  END IF;

  -- Reference match. `(provider, provider_reference)` is unique on payments, so
  -- this cannot match two rows -- and it must be scoped to the provider, because
  -- two providers can legitimately hand out the same reference and matching on
  -- the reference alone would settle the wrong provider's payment.
  SELECT * INTO v_payment
    FROM public.payments p
   WHERE p.provider = v_event.provider
     AND p.provider_reference = v_event.provider_reference
   FOR UPDATE;

  IF NOT FOUND THEN
    -- Retryable, not terminal. The provider can confirm a transfer faster than we
    -- finish writing the pending payment that names it, and treating that race as
    -- a permanent failure would drop a real payment on the floor. Bounded by
    -- attempts: a reference that never appears stops costing anything.
    PERFORM app.defer_provider_event(
      p_event_id,
      format('no payment in provider %s matches reference %s', v_event.provider, v_event.provider_reference)
    );
    RETURN 'deferred: no matching payment';
  END IF;

  SELECT * INTO v_contribution
    FROM public.contributions c
   WHERE c.id = v_payment.contribution_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'payment % references contribution %, which does not exist',
      v_payment.id, v_payment.contribution_id
      USING ERRCODE = 'foreign_key_violation';
  END IF;

  -- Amount match. Against `charged_amount_kobo`, which is what we asked the
  -- provider to collect -- the contribution plus the 2% fee, and for this member
  -- 102000 rather than 100000. Matching against the contribution alone would
  -- reject every correct webhook in the system, because the provider's figure
  -- includes the fee.
  --
  -- NULL means the pending payment never recorded a charged amount, which is a
  -- gap in what we instructed rather than a disagreement between two numbers. It
  -- falls back to the contribution plus its fee, which is the same arithmetic
  -- `app.post_collection_capture` performs.
  IF v_event.amount_kobo <> COALESCE(
       v_payment.charged_amount_kobo,
       v_contribution.amount_kobo + v_contribution.fee_kobo
     ) THEN
    UPDATE public.webhook_events
       SET status       = 'failed',
           error_detail = format('amount mismatch: provider reported %s kobo, payment expects %s kobo',
                                 v_event.amount_kobo,
                                 COALESCE(v_payment.charged_amount_kobo,
                                          v_contribution.amount_kobo + v_contribution.fee_kobo)),
           processed_at = now(),
           updated_at   = now()
     WHERE id = p_event_id;

    -- No capture, and no retry: the provider is not going to send a different
    -- amount for the same reference. This is the escalation the spec asks for --
    -- a row in `failed` with the two figures on it, for E3-08 to reconcile.
    RETURN 'escalated: amount mismatch';
  END IF;

  -- Currency match. `contributions` carries no currency of its own; the Ajo's is
  -- the currency the contribution was raised in.
  SELECT a.currency INTO v_currency
    FROM public.ajos a
   WHERE a.id = v_contribution.ajo_id;

  IF v_event.currency IS NOT NULL AND v_event.currency <> v_currency THEN
    UPDATE public.webhook_events
       SET status       = 'failed',
           error_detail = format('currency mismatch: provider reported %s, the Ajo collects %s',
                                 v_event.currency, v_currency),
           processed_at = now(),
           updated_at   = now()
     WHERE id = p_event_id;

    RETURN 'escalated: currency mismatch';
  END IF;

  -- The payment row records who this payment is for, so the ledger entry carries
  -- a member rather than a null actor. `actor_type` is what marks the actor as a
  -- webhook; see the audit_row replacement below.
  SELECT u.id INTO v_actor_user_id
    FROM public.users u
   WHERE u.id = v_contribution.user_id;

  -- Terminal state, resolved rather than assigned. A payment already `success`
  -- stays `success` whatever arrives next; a `pending` that gets a `success`
  -- settles.
  v_next := app.resolve_transfer_state(v_payment.status, v_event.reported_state);

  -- A terminal payment and a different terminal report is a contradiction, and it
  -- has to be caught BEFORE the general no-change case below.
  --
  -- It cannot be caught afterwards. `resolve_transfer_state` keeps the first
  -- terminal state, so for `success` followed by `failed` it returns `success`,
  -- which equals the payment's current status, and the no-change branch below
  -- would swallow it. The first version of this function had the contradiction
  -- check after that branch, where nothing could ever reach it -- the rule was
  -- written down and unreachable on the same day.
  --
  -- What is recorded, and what is not: the payment keeps its state, because the
  -- ledger has entries against a success and a later message does not unwrite
  -- them. But the event is recorded as a contradiction rather than as routine,
  -- with both states on it, because "the provider says failed and we say success"
  -- is exactly the row E3-08's reconciliation exists to find. Marking it
  -- processed rather than failed is deliberate too: nothing about a third
  -- delivery will resolve it, and retrying would re-report it forever.
  IF v_payment.status IN ('success', 'failed', 'cancelled', 'reversed')
     AND v_event.reported_state IN ('success', 'failed', 'cancelled', 'reversed')
     AND v_event.reported_state <> v_payment.status THEN
    UPDATE public.webhook_events
       SET status       = 'processed',
           error_detail = format('contradiction: payment is already %s and the provider reported %s; the settled state stands',
                                 v_payment.status, v_event.reported_state),
           processed_at = now(),
           updated_at   = now()
     WHERE id = p_event_id;

    RETURN 'contradiction recorded';
  END IF;

  IF v_next = v_payment.status THEN
    -- Nothing to change: either the state repeats, or a non-terminal message
    -- arrived for a transfer already at that state. Recorded and done. Retrying
    -- would be pointless -- the next webhook for this transfer is a different
    -- event with its own id.
    UPDATE public.webhook_events
       SET status        = 'processed',
           processed_at  = now(),
           error_detail  = format('no state change: payment is %s and the provider reported %s',
                                 v_payment.status, v_event.reported_state),
           updated_at    = now()
     WHERE id = p_event_id;

    RETURN 'no change';
  END IF;

  UPDATE public.payments
     SET status            = v_next,
         settled_at        = CASE WHEN v_next IN ('success', 'failed', 'cancelled', 'reversed')
                                  THEN COALESCE(settled_at, v_event.occurred_at) ELSE settled_at END,
         provider_completed_at = COALESCE(provider_completed_at, v_event.occurred_at),
         webhook_event_id  = CASE WHEN v_next = 'success' THEN p_event_id ELSE webhook_event_id END,
         updated_at        = now()
   WHERE id = v_payment.id;

  -- Only a success posts. A failure, a cancellation and a reversal leave the
  -- ledger alone: no money arrived, so there is nothing to write.
  IF v_next = 'success' THEN
    -- `post_collection_capture` requires the payment to already be `success`, and
    -- refuses otherwise with a hint saying this is the webhook's job. That is
    -- this function, reached only through a verified, amount-matched, claimed
    -- event.
    PERFORM app.post_collection_capture(v_payment.id, v_actor_user_id);

    UPDATE public.webhook_events
       SET status       = 'processed',
           processed_at = now(),
           updated_at   = now()
     WHERE id = p_event_id;

    RETURN 'captured';
  END IF;

  UPDATE public.webhook_events
     SET status       = 'processed',
         processed_at = now(),
         updated_at   = now()
   WHERE id = p_event_id;

  RETURN format('recorded %s', v_next);
END;
$fn$;

COMMENT ON FUNCTION app.settle_provider_event(uuid) IS
  'Settles one claimed, signature-verified provider event. Matches the payment on '
  '(provider, provider_reference), refuses to post unless the amount and currency '
  'match what we instructed, resolves the payment state through '
  'app.resolve_transfer_state rather than assigning it, and posts the capture only '
  'on a success. A mismatch is escalated into a failed event carrying both figures '
  'for E3-08, never silently accepted. Returns a short outcome for the caller to '
  'log. 107.';

-- ---------------------------------------------------------------------------
-- Deferral.
-- ---------------------------------------------------------------------------

CREATE FUNCTION app.defer_provider_event(p_event_id uuid, p_reason text) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, app, public
AS $fn$
DECLARE
  v_attempts smallint;
  v_max      constant integer := 8;
BEGIN
  SELECT e.attempts INTO v_attempts
    FROM public.webhook_events e
   WHERE e.id = p_event_id
     FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'no provider event with id %', p_event_id
      USING ERRCODE = 'P0002';
  END IF;

  -- Exponential, capped at an hour, and bounded in attempts as well as in time.
  -- Both matter: unbounded backoff on a reference that will never match turns one
  -- bad webhook into a permanent row somebody has to notice and clear, and the
  -- spec's 90-day replay guarantee is about *unprocessed* events, so an event
  -- that has given up is no longer one.
  IF v_attempts >= v_max THEN
    UPDATE public.webhook_events
       SET status       = 'failed',
           error_detail = format('%s (gave up after %s attempts)', left(coalesce(p_reason, 'deferred'), 200), v_attempts),
           processed_at = now(),
           updated_at   = now()
     WHERE id = p_event_id;
    RETURN;
  END IF;

  UPDATE public.webhook_events
     SET status        = 'received',
         error_detail  = left(coalesce(p_reason, 'deferred'), 200),
         next_retry_at = now() + make_interval(
           secs => least(3600, (2 ^ greatest(coalesce(v_attempts, 1), 1))::integer * 5)),
         updated_at    = now()
   WHERE id = p_event_id;
END;
$fn$;

COMMENT ON FUNCTION app.defer_provider_event(uuid, text) IS
  'Puts a claimed event back on the queue with the reason recorded and an '
  'exponential backoff, or marks it failed once it has been attempted too many '
  'times. Split out of settle because the worker needs the same escape hatch for '
  'a capture that raised, and because a retry policy that lives inside one '
  'function cannot be tested against the other. 107.';

-- ---------------------------------------------------------------------------
-- A webhook is an actor worth naming.
-- ---------------------------------------------------------------------------
--
-- `audit_logs.actor_type` has always allowed `webhook`, and nothing has ever been
-- able to write it: `app.audit_row()` maps the `app.actor_type` GUC's vocabulary
-- (`anon`, `member`) onto the column's (`system`, `user`) and sends everything
-- else to `service`.
--
-- So the first money this system posts from a provider confirmation would be
-- audited as `service` -- indistinguishable from a cron job or a migration. On
-- every line of the ledger that matters: `webhook` says a verified provider event
-- caused this, which is the first thing anyone reading the trail asks.
--
-- RLS is unaffected. `app.request_actor_type()` returns the GUC verbatim and the
-- policies compare it to `member`, so a webhook actor matches no member policy --
-- which is correct, and it is why settlement runs as a definer function and not
-- as the handler's role.
-- The 104 body with one CASE branch added. The DELETE branch, the no-op
-- UPDATE suppression, the generic `amount_kobo` extraction and the search_path are
-- 104's, unchanged; the first version of this wrote its own version of this
-- function from memory and silently lost the first two.
CREATE OR REPLACE FUNCTION app.audit_row()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'app', 'public'
AS $function$
DECLARE
  v_subject_id uuid;
  v_before     jsonb;
  v_after      jsonb;
  v_amount     bigint;
BEGIN
  IF TG_OP = 'DELETE' THEN
    v_subject_id := OLD.id;
    v_before     := to_jsonb(OLD);
    v_after      := NULL;
  ELSIF TG_OP = 'INSERT' THEN
    v_subject_id := NEW.id;
    v_before     := NULL;
    v_after      := to_jsonb(NEW);
  ELSE
    v_subject_id := NEW.id;
    v_before     := to_jsonb(OLD);
    v_after      := to_jsonb(NEW);
    -- An UPDATE that changed nothing is not an audit event. Recording it puts
    -- rows in a table that investigators read, and the cost of a noisy audit
    -- trail is that nobody reads it.
    IF v_before = v_after THEN
      RETURN NULL;
    END IF;
  END IF;

  -- Money columns touched, for the finance audit view. NULL means the row is
  -- not a money row, which is most of them. The values themselves stay in the
  -- ledger; this is a pointer, not a copy of the money.
  IF v_after IS NOT NULL AND v_after ? 'amount_kobo' THEN
    v_amount := (v_after ->> 'amount_kobo')::bigint;
  END IF;

  -- subject_type is the table name minus its plural, which is the convention
  -- every table here already follows. An audited table whose singular is not
  -- in the subject_type enum is a gap in the taxonomy, and this cast is where
  -- it surfaces -- loudly, at migration time, rather than as an unqueryable
  -- NULL six months later.
  INSERT INTO audit_logs
    (actor_user_id, actor_type, action, subject_type, subject_id,
     before_state, after_state, request_id, ip_address, amount_kobo)
  VALUES
    (NULLIF(current_setting('app.actor_user_id', true), '')::uuid,
     -- The mapping. 'member' is the GUC's word for a person acting as
     -- themselves and 'user' is the column's; anything unrecognised becomes
     -- 'service' rather than being written through unvalidated, because an
     -- audit trail that accepts an arbitrary string in the actor column is not a
     -- trail anybody can query.
     CASE COALESCE(NULLIF(current_setting('app.actor_type', true), ''), 'service')
       WHEN 'member'  THEN 'user'
       WHEN 'anon'    THEN 'system'
       WHEN 'webhook' THEN 'webhook'
       ELSE 'service'
     END,
     lower(TG_OP),
     (rtrim(TG_TABLE_NAME, 's'))::subject_type,
     v_subject_id, v_before, v_after,
     NULLIF(current_setting('app.request_id', true), ''),
     NULLIF(current_setting('app.ip_address', true), '')::inet,
     v_amount);

  RETURN NULL;
END;
$function$;

COMMENT ON FUNCTION app.audit_row() IS
  'Writes one audit_logs row per meaningful change to an audited table. Maps '
  'app.actor_type (anon|member|webhook) onto audit_logs.actor_type '
  '(system|user|webhook|service). 107 adds webhook, so a capture driven by a '
  'verified provider event is recorded as a webhook rather than as service. 104 '
  'for everything else.';

-- ---------------------------------------------------------------------------
-- Grants.
-- ---------------------------------------------------------------------------
--
-- `ajo_app` only. The handler and the worker are both `ajo_app`, and PUBLIC is
-- revoked explicitly because PostgreSQL grants EXECUTE on a new function to
-- PUBLIC at creation.
GRANT EXECUTE ON FUNCTION app.mark_provider_event_verified(
  uuid, text, text, bigint, text, public.payment_status) TO ajo_app;
GRANT EXECUTE ON FUNCTION app.claim_provider_event(integer, integer) TO ajo_app;
GRANT EXECUTE ON FUNCTION app.settle_provider_event(uuid) TO ajo_app;
GRANT EXECUTE ON FUNCTION app.defer_provider_event(uuid, text) TO ajo_app;

REVOKE ALL ON FUNCTION app.mark_provider_event_verified(
  uuid, text, text, bigint, text, public.payment_status) FROM PUBLIC;
REVOKE ALL ON FUNCTION app.claim_provider_event(integer, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION app.settle_provider_event(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION app.defer_provider_event(uuid, text) FROM PUBLIC;