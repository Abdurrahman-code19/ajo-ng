-- 110: creating an Ajo.
--
-- `POST /api/v1/ajos` (spec section 11) creates a DRAFT Ajo, the organizer's
-- membership in it, and every payout position, and it has to be one statement
-- because the schema makes it one fact: `app.materialize_organizer_membership`
-- fires on `ajo_positions` INSERT, and `ajos_organizer_is_member` is a
-- DEFERRABLE INITIALLY DEFERRED constraint trigger that refuses the commit if
-- the organizer is not a member. Insert the Ajo alone and the deferred check
-- fails; insert positions without the Ajo and there is no `ajo_id` to attach
-- them to. The write is only ever correct as a unit, so it gets one function.
--
-- It is `SECURITY DEFINER` for the same reason the money functions are: there is
-- no INSERT policy on `ajo_positions` (only SELECT), and there should not be. A
-- policy that let `ajo_app` write positions directly would let any caller name
-- any `ajo_id` and any `position_number` -- claiming seats in somebody else's
-- Ajo. The function takes no organizer id at all; it derives the organizer from
-- `app.request_user_id()` and can therefore only ever create an Ajo the caller
-- owns, with the positions that Ajo's `position_count` declares. That is
-- strictly stronger than a `WITH CHECK (organizer_user_id = app.request_user_id())`
-- on the positions table, which has no `organizer_user_id` to compare against.
--
-- Two columns are added here as well. `ajos` had nowhere to record the weekday a
-- collection lands on (`collection_day`) or the date the first round begins
-- (`start_date`), and the create wizard collects both before the draft exists.
-- A draft that cannot remember its schedule is not resumable, so they are stored
-- now, nullable, in the database's own lower-case vocabulary. `090`'s reference
-- data already spells the cadences `weekly`/`fortnightly`/`monthly`; the API's
-- `BIWEEKLY` maps to `fortnightly` in the domain, not here.

ALTER TABLE public.ajos
  ADD COLUMN collection_day text,
  ADD COLUMN start_date date;

-- Nullable, because rows written before 110 have no schedule and because a draft
-- may be abandoned before the wizard reaches its schedule step. NOT NULL would
-- reject both, and the second is a legitimate state the product has.
ALTER TABLE public.ajos
  ADD CONSTRAINT ajos_collection_day_check
  CHECK (
    collection_day IS NULL
    OR collection_day IN (
      'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
    )
  );

COMMENT ON COLUMN public.ajos.collection_day IS
  'Weekday a collection lands on, lower-case (monday..sunday). NULL before 110, or on a draft whose schedule is not yet chosen.';
COMMENT ON COLUMN public.ajos.start_date IS
  'Date the first round is scheduled to begin. NULL before 110, or on a draft whose schedule is not yet chosen.';

CREATE OR REPLACE FUNCTION app.create_ajo(
  p_name text,
  p_description text,
  p_contribution_amount_kobo bigint,
  p_currency text,
  p_frequency_code text,
  p_position_count integer,
  p_collection_day text,
  p_start_date date
) RETURNS public.ajos
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 'app'
AS $function$
DECLARE
  v_user_id      uuid := app.request_user_id();
  v_frequency_id uuid;
  v_ajo          public.ajos;
BEGIN
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'create_ajo requires an authenticated caller'
      USING ERRCODE = '28000';
  END IF;

  -- The same gate the route applies, repeated where it cannot be bypassed.
  -- "Email-verified active member" is the spec's precondition for creating an
  -- Ajo, and stating it here means the rule holds for a caller that reaches the
  -- function another way, not only for the one route that exists today.
  IF NOT EXISTS (
    SELECT 1
      FROM public.users u
     WHERE u.id = v_user_id
       AND u.deleted_at IS NULL
       AND u.status = 'active'
       AND u.is_email_verified
  ) THEN
    RAISE EXCEPTION 'create_ajo requires an email-verified active member'
      USING ERRCODE = '42501';
  END IF;

  -- Bounds repeated from the domain and the CHECK constraints, because a
  -- constraint that is NOT VALID does not fire for historical rows but does for
  -- new ones, and a caller should get the rule's own message rather than a
  -- truncation error. See ajos_position_count_within_bounds and
  -- ajos_contribution_amount_kobo_check.
  IF p_position_count IS NULL OR p_position_count < 5 OR p_position_count > 20 THEN
    RAISE EXCEPTION 'an Ajo needs between 5 and 20 members, received %', p_position_count
      USING ERRCODE = '23514';
  END IF;

  IF p_contribution_amount_kobo IS NULL
     OR p_contribution_amount_kobo < 100000
     OR p_contribution_amount_kobo > 500000000 THEN
    RAISE EXCEPTION 'a contribution must be between 1000 and 5000000 naira, received % kobo',
      p_contribution_amount_kobo
      USING ERRCODE = '23514';
  END IF;

  IF p_name IS NULL OR length(btrim(p_name)) < 3 OR length(btrim(p_name)) > 80 THEN
    RAISE EXCEPTION 'an Ajo name must be 3 to 80 characters'
      USING ERRCODE = '23514';
  END IF;

  SELECT id INTO v_frequency_id
    FROM public.contribution_frequencies
   WHERE code = p_frequency_code
     AND is_active
     AND deleted_at IS NULL;

  IF v_frequency_id IS NULL THEN
    RAISE EXCEPTION 'unknown or inactive frequency %', p_frequency_code
      USING ERRCODE = '22023';
  END IF;

  -- `total_rounds` is set from `position_count`, not passed in. Rounds equal
  -- members -- one winner per round -- so accepting them as two arguments would
  -- accept a disagreement between them, and the invariant from CANONICAL.md
  -- section 3 would become something the caller has to remember rather than
  -- something the write cannot get wrong.
  INSERT INTO public.ajos (
    organizer_user_id, name, description,
    contribution_amount_kobo, currency,
    frequency_id, position_count, total_rounds,
    collection_day, start_date,
    enrollment_opens_at, enrollment_closes_at
  ) VALUES (
    v_user_id, btrim(p_name), p_description,
    p_contribution_amount_kobo, p_currency::character(3),
    v_frequency_id, p_position_count, p_position_count,
    p_collection_day, p_start_date,
    now(), now() + interval '5 days'
  )
  RETURNING * INTO v_ajo;

  -- All N positions in one INSERT, which fires
  -- app.materialize_organizer_membership once per row. The first firing creates
  -- the organizer's active membership and claims the lowest-numbered free
  -- position; the rest are idempotent no-ops. Nothing here names the organizer:
  -- the function has no organizer id to pass, by design.
  INSERT INTO public.ajo_positions (ajo_id, position_number, status)
  SELECT v_ajo.id, g, 'open'::public.position_status
    FROM generate_series(1, p_position_count) AS g;

  RETURN v_ajo;
END;
$function$;

COMMENT ON FUNCTION app.create_ajo(text, text, bigint, text, text, integer, text, date) IS
  'Creates a DRAFT Ajo for the authenticated caller and its position_count positions in one transaction, so the deferred organizer-is-member check can pass and the organizer is bound to seat 1. Derives the organizer from app.request_user_id(); never accepts it.';

-- `ajo_app` only. PostgreSQL grants EXECUTE on a new function to PUBLIC at
-- creation, so PUBLIC is revoked explicitly. Leaving it granted would not last
-- anyway -- bootstrap_roles.sql revokes PUBLIC from every function in the schema
-- -- but relying on that is the drift 106's README note warns about: the grant
-- would be open between this migration and the next bootstrap.
GRANT EXECUTE ON FUNCTION app.create_ajo(
  text, text, bigint, text, text, integer, text, date
) TO ajo_app;

REVOKE ALL ON FUNCTION app.create_ajo(
  text, text, bigint, text, text, integer, text, date
) FROM PUBLIC;
