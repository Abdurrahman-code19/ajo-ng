-- ---------------------------------------------------------------------------
-- 109: replaying a webhook that stopped.
-- ---------------------------------------------------------------------------
--
-- Spec §13.5, durability: "Unprocessed webhooks are retained for 90 days and
-- replayable, so a processing outage is recoverable."
--
-- Retention is not the hard part, and it is worth being precise about why. Nothing
-- in this schema deletes a webhook event, so a row survives 90 days on its own.
-- What is missing is the other half of the sentence, and it is the half that
-- matters: the events that stopped are stopped permanently. `107` gives up after
-- eight attempts and marks the event `failed`, which is the right behaviour for a
-- reference that will never match -- but the same status is what a two-hour
-- database outage produces, one attempt per worker restart until the budget runs
-- out. After that the queue is quiet, the members' money is in the account, and
-- nothing will ever look at those rows again. Eight failed confirmations is not
-- eight confirmations.
--
-- So this function puts them back. The safety argument is not that it is careful,
-- it is that `app.settle_provider_event` is: it re-validates the amount, the
-- currency and the reference against the *current* state of the payment on every
-- attempt, reading what it needs from the stored row rather than from anything it
-- remembered. Replaying an event whose problem was never fixed re-escalates it,
-- which is the same answer it gave the first time. Replaying one whose problem
-- was fixed -- a corrected amount, a payment created late, a database that was
-- down -- captures it. There is no intermediate outcome to guard against, which
-- is a property of the settlement function rather than a claim about this one.
--
-- Three states are deliberately untouchable:
--
--   processed, duplicate -- settled, or a redelivery of something settled. There
--     is nothing to redo, and redoing a capture is the one irreversible mistake
--     available in this file.
--   ignored -- recorded on purpose, with a reason, by `108`. Replaying it would
--     mean second-guessing a decision somebody made deliberately.
--   received, processing -- still on the queue. A worker will get to them.
--
-- `failed` is therefore the only eligible status, and the number returned is the
-- number of rows this call actually re-queued, so a caller replaying by window
-- cannot believe it re-queued an event that was settled last week.
--
-- The return is a bare count rather than a summary row. That is a constraint of
-- the statement shape below, not a preference, and the reasoning is in the body.

CREATE FUNCTION app.replay_provider_event(
  p_since  timestamptz DEFAULT NULL,
  p_before timestamptz DEFAULT NULL,
  p_limit  integer     DEFAULT 100,
  p_reason text        DEFAULT NULL
) RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, app, public
AS $fn$
DECLARE
  v_replayed integer;
BEGIN
  -- A reason is mandatory and the caller has to write it themselves. Replaying a
  -- hundred events is not a recovery action, it is an assertion that a hundred
  -- events deserve to be acted on again, and an audit trail that says "replayed"
  -- with no reason is indistinguishable from an accident six weeks later. This is
  -- the only guard here that cannot be automated away, which is why it is a
  -- parameter and not a default.
  IF p_reason IS NULL OR btrim(p_reason) = '' THEN
    RAISE EXCEPTION
      'a replay must record why the events are being retried (p_reason)'
      USING ERRCODE = '22004';
  END IF;

  -- Bounded, because this is a bulk operation on a money path and an unbounded one
  -- would hold row locks for as long as the backlog takes. An operator replaying
  -- more than 10,000 events is doing something that deserves to be a loop of
  -- deliberate calls, each with its own reason.
  IF p_limit IS NULL OR p_limit < 1 OR p_limit > 10000 THEN
    RAISE EXCEPTION 'p_limit must be between 1 and 10000, got %', p_limit
      USING ERRCODE = '22004';
  END IF;

  IF p_since IS NOT NULL AND p_before IS NOT NULL AND p_since > p_before THEN
    RAISE EXCEPTION 'the replay window runs backwards: % is after %', p_since, p_before
      USING ERRCODE = '22004';
  END IF;

  -- One statement, and that is not a style preference.
  --
  -- The obvious shape is two: SELECT the events to lock and count them, then
  -- UPDATE them. It is wrong, in a way that only shows up under load. A second
  -- statement gets a new snapshot, so rows this call locked and counted can be
  -- changed, processed or failed again by somebody else before the update runs --
  -- and the update, which has no lock of its own at that point, would re-queue a
  -- capture that has already happened. The reported count would also be describing
  -- rows the update never touched.
  --
  -- Sharing one statement removes the gap rather than closing it: the same
  -- snapshot selects, locks, re-queues and audits. The count this returns is
  -- `ROW_COUNT` of the whole statement, which is the number of audit rows written,
  -- which is the number of rows re-queued -- there is no second number to fall out
  -- of step with the first.
  --
  -- WHICH STATEMENT THE AUDIT INSERT IS, is not negotiable, and the failure mode
  -- is worth writing down because the mistake looks like a tidying-up:
  --
  -- `audit_logs` is RLS with FORCE, and the one INSERT policy on it is
  -- `audit_logs_insert_by_trigger` TO `ajo_migrator`. That policy holds when the
  -- insert is the statement plpgsql executes. The identical insert written as a
  -- data-modifying CTE (`audited AS (INSERT ... RETURNING ...)`) is refused:
  -- `new row violates row-level security policy for table "audit_logs"`. So is
  -- the same insert inside a `FOR ... IN` loop query. Measured, not inferred.
  --
  -- So the audit insert is the outermost statement and the UPDATE is a CTE feeding
  -- it. Do not move the insert into a CTE for symmetry with the UPDATE; it works
  -- in a scratch database where the caller is a superuser and fails in production
  -- where it is not.
  --
  -- The consequence for the return value: only `ROW_COUNT` survives, because the
  -- aggregates that would report the id range have nowhere to go once the insert
  -- is outermost -- `INSERT ... RETURNING` cannot aggregate. That is the trade,
  -- and it is a fair one: the count is what a caller must be told, and which
  -- events those were is answered by the audit rows this writes, one per event,
  -- joined on `subject_id`.
  WITH target AS (
    SELECT e.id,
           -- Captured before the update overwrites them, because this is what the
           -- audit row has to say: when it stopped and why. After the statement
           -- there is no way to recover either.
           e.processed_at AS stopped_at,
           e.error_detail  AS previous_error
      FROM public.webhook_events e
     WHERE e.status = 'failed'
       AND e.deleted_at IS NULL
       -- Only events that were *stopped*. A `failed` row with no stop time cannot
       -- have come from either path in `107`, and matching on a null timestamp
       -- would silently widen the window to include it.
       AND e.processed_at IS NOT NULL
       AND (p_since  IS NULL OR e.processed_at >= p_since)
       AND (p_before IS NULL OR e.processed_at <= p_before)
     ORDER BY e.processed_at, e.id
     LIMIT p_limit
       -- A replay running beside the worker, or beside another replay, must not
       -- take the same event twice. The worker claims with the same lock, and
       -- without this the two would interleave and reset each other's attempts.
       FOR UPDATE SKIP LOCKED
  ), requeued AS (
    UPDATE public.webhook_events e
       SET status       = 'received',
           -- A fresh budget. The eight attempts were spent against a system that
           -- was not working; spending them again against the same event would
           -- reproduce the same outcome, which is the opposite of recovery.
           attempts      = 0,
           next_retry_at = now(),
           -- Cleared because the event is not finished with. Leaving the stop time
           -- in place would leave a queued event that looks, to every query that
           -- asks "when did this stop", as though it had.
           processed_at  = NULL,
           updated_at    = now()
      FROM target t
     WHERE e.id = t.id
    RETURNING e.id,
              e.provider,
              e.provider_event_id,
              e.provider_reference,
              e.amount_kobo,
              t.stopped_at,
              t.previous_error
  )
  -- An explicit audit row rather than an `app.audit_row` trigger on the table,
  -- and the distinction is deliberate: every write to this table is routine queue
  -- churn -- ingest, verify, claim, defer -- and auditing all of it would bury the
  -- one write that is an operator decision inside a hundred automatic ones. A
  -- trigger would also record the operator as having "updated" a row, which is not
  -- what happened and does not distinguish this from anything else.
  -- `webhook_event` has been in the `subject_type` enum since the beginning,
  -- waiting for exactly this.
  --
  -- One row per event, not one row per replay: this is the same per-row convention
  -- the 18 audit triggers follow, and it keeps `subject_id` populated, so "was this
  -- event replayed, and by whom" is a lookup rather than a JSON containment test.
  INSERT INTO public.audit_logs
    (actor_user_id, actor_role_code, actor_type, action, subject_type,
     subject_id, before_state, after_state, amount_kobo)
  SELECT
    NULLIF(current_setting('app.actor_user_id', true), '')::uuid,
    NULLIF(current_setting('app.actor_role_code', true), ''),
    -- The `app.actor_type` GUC speaks a different vocabulary from the column, and
    -- `audit_logs.actor_type` has a CHECK constraint the GUC values do not satisfy
    -- (see `100_audit_row_actor_type`). `app.audit_row()` maps it; so must this,
    -- or a caller that sets the GUC the same way the API does -- 'member' for a
    -- person acting as themselves -- would be refused by the CHECK rather than
    -- recorded. Unset means an unattended recovery job, which is a 'system' actor
    -- and not the 'service' that `audit_row` assumes for an HTTP request.
    CASE COALESCE(NULLIF(current_setting('app.actor_type', true), ''), 'system')
      WHEN 'member'  THEN 'user'
      WHEN 'anon'    THEN 'system'
      WHEN 'user'    THEN 'user'
      WHEN 'webhook' THEN 'webhook'
      WHEN 'service' THEN 'service'
      WHEN 'system'  THEN 'system'
      ELSE 'service'
    END,
    'webhook.replay',
    'webhook_event',
    r.id,
    NULL,
    jsonb_build_object(
      'status',             'received',
      'attempts',           0,
      'provider',           r.provider,
      'provider_event_id',  r.provider_event_id,
      'provider_reference', r.provider_reference,
      'reason',             left(p_reason, 200),
      'previous_error',     r.previous_error,
      'stopped_at',         r.stopped_at
    ),
    r.amount_kobo
    FROM requeued r;

  GET DIAGNOSTICS v_replayed = ROW_COUNT;
  -- Zero is not a failure. "Replay everything that failed since the outage" is the
  -- normal way to call this, and once the outage is over there is nothing left to
  -- do; returning 0 is the honest answer and lets the same command be run twice.
  RETURN v_replayed;
END;
$fn$;

COMMENT ON FUNCTION app.replay_provider_event(timestamptz, timestamptz, integer, text) IS
  'Re-queues provider events that stopped, so a processing outage is recoverable '
  'per spec 13.5. Only status failed is eligible: processed and duplicate are '
  'settled, ignored was a deliberate decision, and received/processing are already '
  'on the queue. Safe because app.settle_provider_event re-validates the amount, '
  'the currency and the reference against the payment on every attempt, so a '
  'replay either captures something that became payable or re-escalates something '
  'that did not. p_reason is mandatory. Select, lock, update and audit in one '
  'statement, and the audit insert must stay the outermost statement or RLS '
  'refuses it. Returns the number re-queued. 109.';

GRANT EXECUTE ON FUNCTION app.replay_provider_event(timestamptz, timestamptz, integer, text) TO ajo_app;
REVOKE ALL ON FUNCTION app.replay_provider_event(timestamptz, timestamptz, integer, text) FROM PUBLIC;