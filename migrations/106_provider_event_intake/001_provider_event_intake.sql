-- ---------------------------------------------------------------------------
-- Provider event intake.
--
-- Spec §13.5: "For card, transfer and wallet payments, the provider's webhook is
-- the event that tells AJO.ng money arrived. It must be treated as hostile
-- input."
--
-- `webhook_events` already exists with the columns and the two unique indexes
-- this needs -- one on (provider, provider_event_id), one partial on
-- provider_event_id where the event has been processed. It has never had a
-- writer, because `096` left it closed, so none of §13.5 was enforced: nothing
-- deduplicated a redelivery, nothing checked a timestamp, and nothing recorded
-- that an event had been seen at all.
--
-- What this migration does NOT do is verify a signature, because that is the
-- one part of the requirement the database cannot satisfy and should not try.
-- The secret belongs to the application; a schema that could verify HMAC would
-- be a schema holding the provider secret. See the reasoning under
-- `mark_provider_event_verified` for what is enforced here instead.
-- ---------------------------------------------------------------------------

-- A redelivery is not an error, so it is recorded as its own outcome rather
-- than raising. The caller answers 2xx either way: a provider that gets a 4xx
-- for a duplicate retries until it gives up, and one that gives up can leave a
-- genuine event unprocessed.

-- ---------------------------------------------------------------------------
-- Ingest a received event.
-- ---------------------------------------------------------------------------
--
-- Deliberately records the event as *unverified*. See below.

CREATE OR REPLACE FUNCTION app.ingest_provider_event(
  p_provider           text,
  p_provider_event_id  text,
  p_event_type         text,
  p_occurred_at        timestamptz,
  p_raw_payload        jsonb,
  p_received_at        timestamptz DEFAULT now()
) RETURNS TABLE (event_id uuid, is_new boolean)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
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
    raw_payload, status, attempts, received_at, created_at, updated_at
  ) VALUES (
    gen_random_uuid(), p_provider, p_provider_event_id, p_event_type,
    false, p_raw_payload, 'received', 0, p_received_at, now(), now()
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
$$;

COMMENT ON FUNCTION app.ingest_provider_event(text, text, text, timestamptz, jsonb, timestamptz) IS
  'Records a provider webhook exactly once. Returns the event id and whether it '
  'is new; a redelivery returns the original id with is_new = false. Refuses an '
  'event older than five minutes, which is the replay window. The event is stored '
  'unverified: only app.mark_provider_event_verified may make it actionable.';

-- ---------------------------------------------------------------------------
-- Mark an event verified.
-- ---------------------------------------------------------------------------
--
-- This split is the whole design, so it is worth being explicit about why the
-- database does not just take `p_signature_verified boolean` and get on with it.
--
-- A boolean parameter is a claim, not a fact. Any caller holding EXECUTE could
-- pass true, and the row would read as verified with nothing behind it -- the
-- one column whose entire purpose is to distinguish "we checked" from "we did
-- not". Making verification a separate function turns that claim into an act
-- with its own call, its own audit trail and its own grant, which is as much
-- verification as a schema can meaningfully attest to.
--
-- The database still cannot check the HMAC, and should not: the provider secret
-- belongs to the application environment, and putting it in a table to make a
-- constraint verifiable would move a secret to satisfy a constraint that can
-- already be satisfied by structure.
--
-- Nothing that moves money reads an unverified event. That is enforced by
-- `assert_provider_event_verified` below, not by convention.

CREATE OR REPLACE FUNCTION app.mark_provider_event_verified(
  p_event_id           uuid,
  p_signature_algorithm text
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
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

  -- Already verified is not an error: a redelivery is verified again, and
  -- refusing would make the second delivery of a perfectly good webhook look
  -- like an attack.
  IF v_status IN ('processed', 'duplicate') THEN
    RETURN;
  END IF;

  UPDATE public.webhook_events
     SET signature_verified = true,
         signature_algorithm = p_signature_algorithm,
         status = CASE WHEN status = 'received' THEN 'processing' ELSE status END,
         updated_at = now()
   WHERE id = p_event_id;
END;
$$;

COMMENT ON FUNCTION app.mark_provider_event_verified(uuid, text) IS
  'Marks a provider event signature-verified and records which algorithm did it. '
  'Separate from ingest on purpose: a boolean argument would be a claim, this is '
  'an auditable act. The API calls it only after verifying the HMAC over the raw '
  'body. Idempotent.';

-- ---------------------------------------------------------------------------
-- The gate.
-- ---------------------------------------------------------------------------
--
-- Spec §13.5 also says "Parse JSON only after verification", and "Amount and
-- reference check: the received amount, currency, and reference must match the
-- pending contribution. A mismatch is escalated to reconciliation, not silently
-- accepted".
--
-- Neither is enforced here yet, and saying so is better than a function that
-- looks like it does. What IS enforced is the precondition both depend on: only
-- a verified, unprocessed event may be acted on. A caller that skipped
-- verification cannot reach the point of comparing amounts.

CREATE OR REPLACE FUNCTION app.assert_provider_event_verified(p_event_id uuid)
RETURNS void
LANGUAGE plpgsql
STABLE
SET search_path = public, pg_temp
AS $$
DECLARE
  v_verified boolean;
  v_status   public.webhook_processing_status;
BEGIN
  SELECT e.signature_verified, e.status INTO v_verified, v_status
    FROM public.webhook_events e
   WHERE e.id = p_event_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'no provider event with id %', p_event_id
      USING ERRCODE = 'P0002';
  END IF;

  IF NOT v_verified THEN
    RAISE EXCEPTION
      'provider event % has an unverified signature and cannot be acted on', p_event_id
      USING ERRCODE = '42501';
  END IF;

  -- An allow-list of the statuses still open for work, rather than a deny-list of
  -- the finished ones. Every status other than these is a decision that has
  -- already been taken: processed, failed, ignored, duplicate. An allow-list means
  -- a status added later is refused by default and someone has to decide whether
  -- it is actionable -- the direction you want a new enum value to fail in. A
  -- deny-list would quietly treat it as actionable.
  --
  -- `ignored` is here because an ignored event is precisely the one whose reason
  -- was recorded: we decided not to act on it, and the gate is what enforces that
  -- rather than leaving it to whoever calls it next.
  IF v_status NOT IN ('received', 'processing') THEN
    RAISE EXCEPTION
      'provider event % is % and cannot be acted on again', p_event_id, v_status
      USING ERRCODE = '42501';
  END IF;
END;
$$;

COMMENT ON FUNCTION app.assert_provider_event_verified(uuid) IS
  'Raises unless the event exists, its signature is verified, and it has not '
  'already been processed. The precondition for anything that acts on a webhook.';

-- ---------------------------------------------------------------------------
-- Terminal state resolution.
-- ---------------------------------------------------------------------------
--
-- Spec §13.5: "Out-of-order delivery: A success arriving after a failure for
-- the same reference is resolved by the terminal state, not by arrival order."
--
-- The sentence is about one thing: a transfer that has already settled does not
-- unsettle because a later message disagrees. So the rule is that a terminal
-- payment state is never left, whatever arrives afterwards.
--
-- The genuinely ambiguous case is the other way round -- a failure followed by a
-- success -- and both of those are terminal. This function keeps the first
-- terminal state it is given, because a provider that reports success and then
-- failure for one reference is contradicting itself and the honest response is
-- to escalate to reconciliation, not to silently pick the more convenient one.
-- That is a reading of the specification, not a fact about a provider, and it
-- is the one thing here that has to be confirmed against ProvidusUnity's actual
-- semantics before it is wired to real money. It is marked in TODO under E3-01.

CREATE OR REPLACE FUNCTION app.resolve_transfer_state(
  p_current  public.payment_status,
  p_incoming public.payment_status
) RETURNS public.payment_status
LANGUAGE plpgsql
IMMUTABLE
SET search_path = public, pg_temp
AS $$
BEGIN
  IF p_current IS NULL THEN
    RETURN p_incoming;
  END IF;

  IF p_incoming IS NULL THEN
    RETURN p_current;
  END IF;

  -- Terminal wins, in whichever order it arrived. Once a contribution is
  -- settled the ledger has entries against it and the member has been told
  -- something; a later PENDING or UNKNOWN cannot take that back.
  IF p_current IN ('success', 'failed', 'cancelled', 'reversed') THEN
    RETURN p_current;
  END IF;

  -- A terminal incoming state settles a transfer that has not settled.
  IF p_incoming IN ('success', 'failed', 'cancelled', 'reversed') THEN
    RETURN p_incoming;
  END IF;

  -- UNKNOWN means "we could not find out". It is not evidence, so it does not
  -- overwrite what is already known; it is only accepted when nothing better is
  -- on record. Without this, a single unreadable webhook would replace `pending`
  -- with `unknown` and the reconciliation report would lose the fact that the
  -- transfer had a definite state a moment ago.
  IF p_incoming = 'unknown' THEN
    RETURN p_current;
  END IF;

  -- Two non-terminal states: the later one refines the earlier, which is how
  -- initiated -> pending -> success works at all.
  RETURN p_incoming;
END;
$$;

COMMENT ON FUNCTION app.resolve_transfer_state(public.payment_status, public.payment_status) IS
  'Applies spec 13.5 out-of-order delivery: a terminal payment state is never '
  'left, whatever arrives after it. An incoming unknown does not overwrite a '
  'known state. Two terminal states keep the first, which needs confirming '
  'against the approved provider.';

-- ---------------------------------------------------------------------------
-- Ignoring an event we do not act on.
-- ---------------------------------------------------------------------------
--
-- Spec §13.5: "Unknown event types: Acknowledged, logged, and ignored -- never a
-- 4xx, and never a crash." The acknowledgement is the HTTP layer's job; this is
-- the record that says why nothing happened, which is what makes an unexplained
-- gap in a provider's events diagnosable six months later.

CREATE OR REPLACE FUNCTION app.ignore_provider_event(
  p_event_id    uuid,
  p_error_detail text DEFAULT NULL
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  PERFORM app.assert_provider_event_verified(p_event_id);

  UPDATE public.webhook_events
     SET status = 'ignored',
         error_detail = COALESCE(p_error_detail, error_detail),
         processed_at = now(),
         updated_at = now()
   WHERE id = p_event_id;
END;
$$;

COMMENT ON FUNCTION app.ignore_provider_event(uuid, text) IS
  'Records a verified event as deliberately not acted on, with the reason. Used '
  'for event types the application does not implement: spec 13.5 requires those '
  'to be acknowledged and logged, never refused.';

-- ---------------------------------------------------------------------------
-- Row-level access and grants.
-- ---------------------------------------------------------------------------
--
-- Same reasoning as migration 105, for the same reason: these are
-- SECURITY DEFINER functions owned by `ajo_migrator`, and `webhook_events` is
-- RLS with a staff-only SELECT policy, so without these the functions would see
-- no rows and refuse every write while reporting that nothing exists.

CREATE POLICY webhook_events_migrator_select ON public.webhook_events
  FOR SELECT TO ajo_migrator USING (true);
CREATE POLICY webhook_events_migrator_insert ON public.webhook_events
  FOR INSERT TO ajo_migrator WITH CHECK (true);
CREATE POLICY webhook_events_migrator_update ON public.webhook_events
  FOR UPDATE TO ajo_migrator USING (true) WITH CHECK (true);

GRANT EXECUTE ON FUNCTION app.ingest_provider_event(
  text, text, text, timestamptz, jsonb, timestamptz
) TO ajo_app;
GRANT EXECUTE ON FUNCTION app.mark_provider_event_verified(uuid, text) TO ajo_app;
GRANT EXECUTE ON FUNCTION app.ignore_provider_event(uuid, text) TO ajo_app;

REVOKE EXECUTE ON FUNCTION app.ingest_provider_event(
  text, text, text, timestamptz, jsonb, timestamptz
) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION app.mark_provider_event_verified(uuid, text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION app.ignore_provider_event(uuid, text) FROM PUBLIC;

-- `assert_provider_event_verified` is STABLE rather than SECURITY DEFINER, so it
-- runs as the caller's role and needs no row policy of its own -- the caller's
-- own SELECT policy governs whether the row is visible. `resolve_transfer_state`
-- is IMMUTABLE and reads no table at all.
--
-- Neither of them needs a policy, and both of them still need their EXECUTE
-- revoked from PUBLIC: PostgreSQL grants EXECUTE on a new function to PUBLIC
-- automatically, so "this function is not security definer" says nothing about
-- who may call it. Leaving `assert_...` public would let any role ask it about
-- any event id and learn whether that event exists and was verified. Not the
-- money, but it is the shape of the table, and it is free to close.
REVOKE EXECUTE ON FUNCTION app.assert_provider_event_verified(uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION app.resolve_transfer_state(
  public.payment_status, public.payment_status
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION app.assert_provider_event_verified(uuid) TO ajo_app;

-- `resolve_transfer_state` reads no table and could safely be PUBLIC, and it was
-- granted that way at first. It is not, because `bootstrap_roles.sql` revokes
-- PUBLIC from every function in the schema and then grants only `ajo_app`, so a
-- PUBLIC grant here would hold until the next role bootstrap and silently not
-- after it -- the same class of bug as migration 105's ledger primitive being
-- reopened by a blanket grant. Two behaviours depending on when a role was last
-- bootstrapped is one too many. Every caller is server-side with credentials
-- anyway, so the grant buys nothing; closed by default, like everything else.
GRANT EXECUTE ON FUNCTION app.resolve_transfer_state(
  public.payment_status, public.payment_status
) TO ajo_app;