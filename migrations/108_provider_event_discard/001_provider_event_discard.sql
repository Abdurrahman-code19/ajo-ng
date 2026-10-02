-- ---------------------------------------------------------------------------
-- 108: recording an event we will never settle.
-- ---------------------------------------------------------------------------
--
-- Spec §13.5: "Unknown event types: Acknowledged, logged, and ignored -- never a
-- 4xx, and never a crash."
--
-- `106` wrote the function for that: `app.ignore_provider_event`, which records
-- the reason nothing happened. It cannot be reached. It asserts the event is
-- signature-verified, and the only function that records a verification --
-- `app.mark_provider_event_verified` -- refuses to run without the provider
-- reference, the amount and the state. Those are the values settlement matches
-- on, so insisting on them is correct *for an event that will be settled*.
--
-- The two requirements meet exactly where the spec wants them to: an event type
-- we do not act on is precisely the event most likely to have no transfer
-- reference in it at all. `account.updated` carries an account and a state, not
-- a `provider_reference`. So the HTTP layer has exactly two bad options for an
-- unrecognised event -- refuse it (a 4xx, which the spec forbids and which
-- invites the provider to retry a delivery that will never be understood) or
-- fail to verify it (which leaves an unexplained row in the queue that no
-- operator can tell apart from a forgery).
--
-- This function is the third option: verification recorded from a signature the
-- adapter has already checked, the event marked ignored in the same statement,
-- and none of the settlement values required. It is deliberately narrow -- an
-- event it has marked `ignored` is never claimable, because
-- `app.claim_provider_event` selects only `received` and `processing`, and
-- `app.settle_provider_event` refuses anything that is not `processing`.

CREATE FUNCTION app.discard_provider_event(
  p_event_id            uuid,
  p_signature_algorithm text,
  p_reason              text,
  p_provider_reference  text DEFAULT NULL
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

  -- The same rule `app.mark_provider_event_verified` applies: an event nobody
  -- can say how it was verified is not a verified event. The difference is that
  -- this one is never acted on, so a wrong algorithm name here costs a
  -- diagnostic row rather than a capture.
  IF p_signature_algorithm IS NULL OR btrim(p_signature_algorithm) = '' THEN
    RAISE EXCEPTION 'a discarded event must record which algorithm verified it'
      USING ERRCODE = '22004';
  END IF;

  -- A redelivery of something already processed is not an error. Refusing would
  -- make a provider's honest second delivery of a good event look like an
  -- attack, which is the same reasoning as in `mark_provider_event_verified`.
  IF v_status IN ('processed', 'duplicate') THEN
    RETURN;
  END IF;

  UPDATE public.webhook_events
     SET signature_verified  = true,
         signature_algorithm = p_signature_algorithm,
         -- Recorded when the adapter got one, because the index this lands in is
         -- the one reconciliation reads: "what did the provider say about this
         -- reference, and what did we do about it" is the question an ignored
         -- event exists to answer, and it is unanswerable by event id alone.
         -- Harmless for the queue -- this row is already unreachable by the
         -- claim, and nothing matches a payment by reference until settlement
         -- runs, which this event never will.
         provider_reference   = nullif(btrim(p_provider_reference), ''),
         status              = 'ignored',
         error_detail        = left(coalesce(p_reason, 'event type not acted on'), 200),
         processed_at        = now(),
         updated_at          = now()
   WHERE id = p_event_id;
END;
$fn$;

COMMENT ON FUNCTION app.discard_provider_event(uuid, text, text, text) IS
  'Records a signature-verified provider event this system does not act on, and '
  'why. Exists because app.ignore_provider_event requires a verification to '
  'already be recorded, and app.mark_provider_event_verified requires the '
  'reference, amount and state that an unrecognised event type usually does not '
  'have. The event is never claimable afterwards: the claim reads only received '
  'and processing. 108.';

GRANT EXECUTE ON FUNCTION app.discard_provider_event(uuid, text, text, text) TO ajo_app;
REVOKE ALL ON FUNCTION app.discard_provider_event(uuid, text, text, text) FROM PUBLIC;