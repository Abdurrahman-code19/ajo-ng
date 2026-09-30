-- The creator is a member, and the draft-exit floor is 5.
--
-- Two halves of one product rule, both of which the adopted schema had wrong or
-- missing.
--
-- **Missing: the organizer's own membership was never created.** `ajos` has an
-- `organizer_user_id` and `ajo_members` has a `user_id`, and the ERD says the
-- organizer is "always also a member", but nothing in the database made that
-- true. An organizer could create an Ajo and never appear in it, which means no
-- position, no contribution obligation and no payout for the person running the
-- group. Nothing about that is a reasonable state, so it is now enforced rather
-- than documented.
--
-- **Wrong: the draft-exit floor was two.** `app.assert_draft_exit()` rejected
-- leaving DRAFT with fewer than two positions, which is the rule this project
-- replaced with 5 to 20. Left alone, an organiser could fill two of ten
-- positions, satisfy the old check and activate a group that could never rotate.
--
-- Why triggers and not a CHECK: the rule spans two tables. A CHECK sees one row
-- and cannot ask whether a membership row exists elsewhere.
--
-- Why the trigger hangs off `ajo_positions` and not `ajos`:
-- `ajo_positions.ajo_id` is a foreign key onto `ajos(id)`, so the Ajo row is
-- forced to exist before any position can reference it. The first position
-- INSERT is therefore always the moment at which there is both an organizer and
-- a seat for them, and it is the correct and only place to bind the two
-- together. A trigger on `ajos` could never find a position to assign.
--
-- `SECURITY DEFINER` with a pinned search_path, like every other `app.*`
-- function, because the trigger fires as the table owner and must not depend on
-- the caller's privileges.

-- ---------------------------------------------------------------------------
-- 1. Materialise the organizer's membership when positions are created.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.materialize_organizer_membership()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, app
AS $fn$
DECLARE
  v_user_id  uuid;
  v_position integer;
BEGIN
  SELECT organizer_user_id INTO v_user_id
    FROM public.ajos
   WHERE id = NEW.ajo_id;

  IF v_user_id IS NULL THEN
    RETURN NULL;
  END IF;

  -- Idempotent, because a single INSERT of all N positions fires this N times
  -- and only the first should create the membership.
  IF EXISTS (
    SELECT 1 FROM public.ajo_members m
     WHERE m.ajo_id = NEW.ajo_id AND m.user_id = v_user_id
  ) THEN
    RETURN NULL;
  END IF;

  -- The organizer takes the first free position. Position 1 is correct by
  -- convention and is also what makes the group's round order start with the
  -- person who set it up, which is what members expect to see.
  SELECT min(p.position_number) INTO v_position
    FROM public.ajo_positions p
   WHERE p.ajo_id = NEW.ajo_id
     AND p.deleted_at IS NULL
     AND NOT EXISTS (
       SELECT 1
         FROM public.ajo_members m
        WHERE m.ajo_id = NEW.ajo_id
          AND m.position_id = p.id
          AND m.status IN ('invited', 'active', 'defaulted')
     );

  IF v_position IS NULL THEN
    RAISE EXCEPTION
      'Ajo % has no free position left for its organizer; all % of its position(s) are claimed',
      NEW.ajo_id,
      (SELECT count(*) FROM public.ajo_positions p
        WHERE p.ajo_id = NEW.ajo_id AND p.deleted_at IS NULL)
      USING ERRCODE = 'check_violation',
            HINT = 'The organizer occupies one of the position_count positions, so if they '
                   'are not already a member there is no seat left to give them.';
  END IF;

  INSERT INTO public.ajo_members (
    ajo_id, user_id, position_id, status, joined_at
  )
  SELECT NEW.ajo_id, v_user_id, p.id, 'active', now()
    FROM public.ajo_positions p
   WHERE p.ajo_id = NEW.ajo_id
     AND p.position_number = v_position
     AND p.deleted_at IS NULL
  ON CONFLICT (ajo_id, user_id) DO NOTHING;

  -- Claim the seat as well as binding it. `ajo_positions.status` is the
  -- occupancy flag that app.assert_draft_exit() reads when it decides whether
  -- an Ajo is full, so leaving it at 'open' would make the database believe a
  -- seat is unfilled while the organizer is standing in it. Two tables describe
  -- one fact, so both are written here.
  UPDATE public.ajo_positions
     SET status = 'claimed'
   WHERE ajo_id = NEW.ajo_id
     AND position_number = v_position
     AND deleted_at IS NULL
     AND status = 'open';

  RETURN NULL;
END;
$fn$;

COMMENT ON FUNCTION app.materialize_organizer_membership() IS
  'CAN §3 and ERD §8.2: the creator occupies one of the position_count positions '
  'rather than one in addition to them, so a ten-member Ajo is one organiser and '
  'nine invitees. Fires on the first ajo_positions INSERT of an Ajo, which is the '
  'earliest point at which both the organizer and a seat exist. Idempotent, so a '
  'multi-row insert of all positions still yields exactly one membership. Also '
  'claims the seat, because ajo_positions.status is the occupancy flag '
  'app.assert_draft_exit() counts on.';

DROP TRIGGER IF EXISTS ajo_positions_materialize_organizer ON public.ajo_positions;
CREATE TRIGGER ajo_positions_materialize_organizer
  AFTER INSERT ON public.ajo_positions
  FOR EACH ROW EXECUTE FUNCTION app.materialize_organizer_membership();

-- ---------------------------------------------------------------------------
-- 2. Verify the invariant at commit, in case positions were never created.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.assert_organizer_is_member()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, app
AS $fn$
DECLARE
  v_has_membership boolean;
BEGIN
  SELECT EXISTS (
    SELECT 1
      FROM public.ajo_members m
     WHERE m.ajo_id = NEW.id
       AND m.user_id = NEW.organizer_user_id
       AND m.deleted_at IS NULL
  ) INTO v_has_membership;

  IF NOT v_has_membership THEN
    RAISE EXCEPTION
      'Ajo % has organizer %, who is not a member of it; the creator occupies one of the % position(s)',
      NEW.id, NEW.organizer_user_id, NEW.position_count
      USING ERRCODE = 'check_violation',
            HINT = 'Create the Ajo and its position_count positions in one transaction, '
                   'so the organizer is bound to a seat.';
  END IF;

  RETURN NULL;
END;
$fn$;

COMMENT ON FUNCTION app.assert_organizer_is_member() IS
  'CAN §3: an Ajo cannot be committed unless its organizer is a member. '
  'Deferred to COMMIT, so the Ajo, its positions and the organizer membership '
  'may be written in any order within a single transaction.';

DROP TRIGGER IF EXISTS ajos_organizer_is_member ON public.ajos;
CREATE CONSTRAINT TRIGGER ajos_organizer_is_member
  AFTER INSERT OR UPDATE ON public.ajos
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION app.assert_organizer_is_member();

-- ---------------------------------------------------------------------------
-- 3. The draft-exit floor is 5, not 2, and the ceiling is 20.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.assert_draft_exit()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public, app
AS $fn$
DECLARE
  v_positions integer;
  v_filled    integer;
  v_window    interval;
BEGIN
  IF NEW.status IN ('enrollment', 'active', 'round_in_progress', 'completed')
     AND OLD.status = 'draft' THEN
    SELECT count(*) INTO v_positions
      FROM public.ajo_positions
     WHERE ajo_id = NEW.id AND deleted_at IS NULL;

    -- Between 5 and 20, matching ajos_position_count_within_bounds. An Ajo of
    -- one is a transfer, not a rotation, and twenty is the most a single
    -- organiser can realistically invite, monitor and default-handle.
    IF v_positions < 5 THEN
      RAISE EXCEPTION
        'Ajo % cannot leave DRAFT with % position(s); an Ajo needs at least 5',
        NEW.id, v_positions
        USING ERRCODE = 'check_violation',
              HINT = 'An Ajo of one is a transfer, not a rotation. Between 5 and 20 members.';
    END IF;

    IF v_positions > 20 THEN
      RAISE EXCEPTION
        'Ajo % cannot leave DRAFT with % position(s); an Ajo may have at most 20',
        NEW.id, v_positions
        USING ERRCODE = 'check_violation',
              HINT = 'Between 5 and 20 members.';
    END IF;
  END IF;

  -- ENROLLMENT -> ACTIVE either fills every position or reaches day five.
  IF NEW.status = 'active' AND OLD.status = 'enrollment' THEN
    SELECT count(*), count(*) FILTER (WHERE p.status <> 'open')
      INTO v_positions, v_filled
      FROM public.ajo_positions p
     WHERE p.ajo_id = NEW.id AND p.deleted_at IS NULL;

    v_window := NEW.enrollment_closes_at - NEW.enrollment_opens_at;

    IF v_filled < v_positions AND now() < NEW.enrollment_closes_at THEN
      RAISE EXCEPTION
        'Ajo % cannot activate with % of % position(s) filled before the enrollment window closes',
        NEW.id, v_filled, v_positions
        USING ERRCODE = 'check_violation',
              HINT = 'Either fill every position or wait for the five-day window to close, '
                     'which cancels the Ajo and refunds contributions in full.';
    END IF;
  END IF;

  RETURN NEW;
END;
$fn$;

COMMENT ON FUNCTION app.assert_draft_exit() IS
  'CAN §3: an Ajo holds between 5 and 20 positions, and cannot activate until '
  'every position is filled or the five-day enrollment window has closed.';
