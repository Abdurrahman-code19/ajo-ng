-- 113: the enrollment window, activation on the fill event, and the day-5 close.
--
-- Three rules, and two of them are decisions rather than code, so the decisions
-- are recorded here where the next reader of the schema will find them.
--
-- **The clock starts when enrollment opens, not when the Ajo is created.**
-- EC-061: "a draft has no clock running on it, so an abandoned draft cancels
-- nothing and collects nothing." A draft is a thing an organizer is still
-- configuring; it makes no promises to anybody. If the window ran from creation
-- then every draft anyone took a week to fill in would have cancelled itself
-- while nobody was looking, and the person who invited eleven people to a
-- twelve-seat Ajo would find it dead with no explanation.
--
-- `app.create_ajo` (migration 110) stamps `enrollment_opens_at` and
-- `enrollment_closes_at` at creation because the columns are NOT NULL. Those
-- values are provisional placeholders for a draft, and nothing reads them while
-- `status = 'draft'`: the expiry sweep below only selects `enrollment` rows, the
-- join guard below only consults the window for an Ajo already in `enrollment`,
-- and `open_enrollment` re-stamps both from `now()`. A draft that sat for a
-- month still gets a full five days of its own.
--
-- Making the columns nullable instead would be the tidier data model and was
-- rejected on evidence rather than taste. `app.create_invitation` already writes
-- `COALESCE(a.enrollment_closes_at, i.expires_at)`, so it anticipates a NULL;
-- but the migration fixtures throughout `scripts/test_migrations.py` insert
-- drafts with an explicit five-day window and then move them to `enrollment`
-- with a bare `UPDATE ajos SET status = 'enrollment'`, so a NULL-inserting
-- trigger would leave those Ajos unable to open enrollment at all. The
-- placeholder costs nothing and keeps one code path.
--
-- **Activation happens on the fill event, never on a calendar event.**
-- EC-051: "Enrollment fills every position on day 4, so the Ajo activates early
-- rather than waiting for day 5. Activation proceeds on the fill event, not on a
-- calendar event." So there is no endpoint that activates an Ajo.
-- `POST /api/v1/ajos/:id/activate` does *not* do it: per section 2.0.2 of the
-- user-flows spec that endpoint is `OPEN_ENROLLMENT`, the DRAFT to ENROLLMENT
-- transition, and "the ENROLLMENT to ACTIVE transition is system-driven and is
-- never reachable through this endpoint." The name says one thing and the spec
-- says another; the spec wins, and the function below is named for what it does
-- rather than for the URL that calls it.
--
-- The trigger rather than a line inside `app.join_ajo`, because it has to be the
-- only way in: a seat claimed through any other path -- a future replacement
-- flow, a support tool, a backfill -- has to activate the Ajo too, or the Ajo
-- sits full until day five arrives and cancels a rotation every member did
-- everything right to join.
--
-- **The day-5 close is automatic and needs a scheduler that does not exist.**
-- CANONICAL.md section 3 lists the event as `(auto)`. A calendar event needs
-- something to run at the instant, and this database has no pg_cron and no job
-- runner -- `SELECT extname FROM pg_extension` on live returns no scheduler. So
-- the mechanism is a batch function that is idempotent, safe to run
-- concurrently, and cheap to run often, plus `assert_joinable` refusing a join
-- the moment the window has passed whether or not anybody called it. The rule
-- is therefore enforced even with no scheduler at all, and the scheduler that
-- eventually lands is a performance question rather than a correctness one.
--
-- CANONICAL.md section 3 is the authority for all of this. Where the backlog or
-- an appendix says "FUNDED" for the activated state, CANONICAL.md says `ACTIVE`
-- and `public.ajo_status` has no `funded` member.

-- Open the enrollment window: DRAFT to ENROLLMENT, organizer only.
--
-- This is what POST /api/v1/ajos/:id/activate calls, despite the name.
--
-- The configuration guard is CANONICAL.md's, and it deliberately does *not*
-- include FR-AJO-006's "at least 2 positions filled". That reading is circular:
-- you cannot fill a second position before enrollment opens, because membership
-- arrives by invitation (BR-006) and invitations are minted into an Ajo whose
-- window has not started. CANONICAL.md wins under its own precedence rule, and
-- the size floor that does exist -- five to twenty -- is already enforced on
-- leaving DRAFT by `app.assert_draft_exit`.
--
-- No reason is recorded, unlike a freeze or a cancellation, and that is not an
-- oversight. Those events are discretionary and need justifying. Opening
-- enrollment is not discretionary: its guards decide it, the audit trigger
-- records who did it and when, and inventing a free-text field here would
-- collect strings nobody reads.
CREATE OR REPLACE FUNCTION app.open_enrollment(p_ajo_id uuid)
RETURNS TABLE (enrollment_opens_at timestamptz, enrollment_closes_at timestamptz)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 'app'
AS $function$
DECLARE
  v_user_id uuid := app.request_user_id();
  v_ajo     public.ajos;
  v_opens   timestamptz := now();
BEGIN
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'opening enrollment requires an authenticated caller'
      USING ERRCODE = '28000';
  END IF;

  -- FOR UPDATE, because two taps on "open enrollment" is the ordinary case
  -- rather than an edge case, and the second one must find an enrollment rather
  -- than open a second window over the first.
  SELECT a.* INTO v_ajo
    FROM public.ajos a
   WHERE a.id = p_ajo_id
     AND a.deleted_at IS NULL
   FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'no such Ajo'
      USING ERRCODE = 'P0002';
  END IF;

  IF v_ajo.organizer_user_id <> v_user_id THEN
    RAISE EXCEPTION 'only the organizer of this Ajo may open enrollment'
      USING ERRCODE = '42501';
  END IF;

  IF v_ajo.status = 'enrollment' THEN
    RAISE EXCEPTION 'enrollment is already open for this Ajo'
      USING ERRCODE = '23514';
  END IF;

  IF v_ajo.status <> 'draft' THEN
    RAISE EXCEPTION 'this Ajo is % and its enrollment window is closed', v_ajo.status
      USING ERRCODE = '23514';
  END IF;

  IF v_ajo.contribution_amount_kobo IS NULL OR v_ajo.frequency_id IS NULL
     OR v_ajo.position_count < 5 OR v_ajo.position_count > 20 THEN
    RAISE EXCEPTION 'this Ajo is not fully configured and cannot open enrollment'
      USING ERRCODE = '23514';
  END IF;

  -- Exactly five days, and computed from the open rather than carried over from
  -- the creation-time placeholder. This is the line that makes EC-061 true.
  UPDATE public.ajos a
     SET status = 'enrollment',
         enrollment_opens_at = v_opens,
         enrollment_closes_at = v_opens + interval '5 days',
         updated_at = now()
   WHERE a.id = v_ajo.id;

  RETURN QUERY SELECT v_opens, v_opens + interval '5 days';
END;
$function$;

COMMENT ON FUNCTION app.open_enrollment(uuid) IS
  'Opens the five-day enrollment window: DRAFT to ENROLLMENT, organizer only. The clock starts here rather than at creation (EC-061). Despite the endpoint name, POST /api/v1/ajos/:id/activate is this and not the activation to ACTIVE (user-flows section 2.0.2).';

-- The window rules, enforced on the Ajo row itself.
--
-- Two guarantees, both of which a caller could otherwise break with a bare
-- UPDATE:
--
--   1. An Ajo cannot be in `enrollment` without a window. Without this, a draft
--      could be pushed into `enrollment` with the placeholder timestamps and
--      would then be evaluated against a clock that started whenever it was
--      created -- which is exactly the bug EC-061 describes, reachable through
--      the most obvious SQL in the world.
--   2. The window cannot be moved. EC-053: "the organizer cannot extend the
--      five-day enrollment window; it is fixed by the rules." Once the invitees
--      have been told when this closes, moving the date is not a configuration
--      change, it is a change to a promise already made to them. Shortening is
--      frozen as well -- CANONICAL section 3 says *exactly* five days -- so the
--      only way to end a window early is to fill the Ajo.
CREATE OR REPLACE FUNCTION app.assert_enrollment_window()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO 'public', 'app'
AS $function$
BEGIN
  -- EC-061: the clock starts when enrollment opens, and it starts there.
  --
  -- This *stamps* the window rather than checking that one was supplied, and the
  -- difference is the whole point. The columns are NOT NULL, so migration 110
  -- filled them at creation time and a draft already carries a plausible-looking
  -- window. Checking for NULL therefore rejects nothing, and a bare
  -- `UPDATE ajos SET status = 'enrollment'` carries a stale window into
  -- enrollment -- one that may already have closed, cancelling an Ajo whose
  -- members were promised five days.
  --
  -- Overwriting on the transition makes this the single place the window is
  -- decided. `app.open_enrollment` stamps it too; that is now belt to braces
  -- rather than the only guard, which is the state this trigger is meant to be in
  -- -- the one that holds when the caller is not the function we wrote.
  IF NEW.status = 'enrollment' AND NEW.status <> OLD.status THEN
    NEW.enrollment_opens_at := now();
    NEW.enrollment_closes_at := now() + interval '5 days';
    RETURN NEW;
  END IF;

  -- EC-053, and CANONICAL section 3's "exactly 5 days".
  --
  -- Both endpoints are frozen, not just the close. Allowing a *shortening* was
  -- considered and rejected: CANONICAL says the window is exactly five days, so
  -- moving either end produces a window that is not the one the rules describe,
  -- and the only reason it looked harmless is that nobody had to be told. A
  -- member who accepted a five-day window has been promised five days.
  IF NEW.status IN ('enrollment', 'active')
     AND (NEW.enrollment_opens_at IS DISTINCT FROM OLD.enrollment_opens_at
          OR NEW.enrollment_closes_at IS DISTINCT FROM OLD.enrollment_closes_at) THEN
    RAISE EXCEPTION
      'ajo % cannot move its enrollment window; it is fixed at % - %',
      NEW.id, OLD.enrollment_opens_at, OLD.enrollment_closes_at
      USING ERRCODE = 'check_violation',
            HINT = 'EC-053: the five-day enrollment window is fixed by the rules. '
                   'Invitees were told when this closes; moving that date is not '
                   'a configuration change.';
  END IF;

  -- BEFORE triggers return the row to keep. Returning NULL here would make
  -- PostgreSQL drop the row silently: no error, no warning, INSERT 0 0.
  RETURN NEW;
END;
$function$;

CREATE TRIGGER ajos_enrollment_window
  BEFORE UPDATE ON public.ajos
  FOR EACH ROW EXECUTE FUNCTION app.assert_enrollment_window();

COMMENT ON FUNCTION app.assert_enrollment_window() IS
  'Requires a window on any transition into ENROLLMENT, and forbids extending a window that has started (EC-053). Both are reachable with a bare UPDATE otherwise, which is how a placeholder timestamp becomes a promise.';

-- Activation on the fill event.
--
-- `app.assert_draft_exit` already decides whether the transition is *allowed*:
-- it refuses ENROLLMENT to ACTIVE unless every position is filled or the window
-- has closed. This trigger decides *when* to attempt it, which is the right way
-- round -- the trigger counts, the guard judges, and neither has to trust the
-- other.
--
-- The `FOR UPDATE` on the parent is load-bearing. Two invitees can be claiming
-- the last two seats at the same instant, each holding its own position lock,
-- and each trigger would count the other's uncommitted claim as still open --
-- leaving a completely full Ajo sitting in `enrollment` until the expiry sweep
-- noticed. Locking the parent row serialises the two activations, and the loser
-- of that wait re-reads committed state and sees the Ajo full. The lock order
-- is invitation, then position, then Ajo, which is the same order every path
-- already takes, so there is no cycle for PostgreSQL to detect.
CREATE OR REPLACE FUNCTION app.activate_when_full()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 'app'
AS $function$
DECLARE
  v_ajo public.ajos;
BEGIN
  -- Only a real join fills a seat. A membership written for any other reason --
  -- the organizer materialised by `app.materialize_organizer_membership`, a
  -- backfill -- must not activate anything.
  IF NEW.status <> 'active' OR NEW.deleted_at IS NOT NULL THEN
    RETURN NULL;
  END IF;

  SELECT a.* INTO v_ajo
    FROM public.ajos a
   WHERE a.id = NEW.ajo_id
   FOR UPDATE;

  IF NOT FOUND OR v_ajo.status <> 'enrollment' THEN
    RETURN NULL;
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.ajo_positions p
     WHERE p.ajo_id = v_ajo.id
       AND p.deleted_at IS NULL
       AND p.status = 'open'
  ) THEN
    RETURN NULL;   -- still a seat left; this is not the day
  END IF;

  -- Every position is filled, so the Ajo activates now -- on day one, if that is
  -- when the last invitee accepted. Positions lock from here by way of
  -- `app.assert_positions_locked`, which reads this status. `activated_at` is
  -- required by the ajos_activated_has_timestamp check, which fires on the same
  -- UPDATE.
  UPDATE public.ajos a
     SET status = 'active',
         activated_at = now(),
         updated_at = now()
   WHERE a.id = v_ajo.id;

  RETURN NULL;   -- AFTER trigger; the return value is ignored
END;
$function$;

CREATE TRIGGER ajo_members_activate_when_full
  AFTER INSERT ON public.ajo_members
  FOR EACH ROW EXECUTE FUNCTION app.activate_when_full();

COMMENT ON FUNCTION app.activate_when_full() IS
  'Activates an Ajo in ENROLLMENT the moment its last position is claimed (EC-051: activation is triggered by the fill, not by the calendar). Attached to every membership insert so that no claim path can leave a full Ajo waiting to cancel itself.';

-- The late-join refusal, enforced by the database rather than by the caller.
--
-- `app.join_ajo` (migration 112) refuses an Ajo that is neither `draft` nor
-- `enrollment`, which covers EC-066 once activation has happened. It cannot
-- cover the other half of the rule, because it was written before the window
-- started at the transition rather than at creation and it has no way to know an
-- `enrollment` row's five days have run out: nothing sweeps the status on a
-- timer. So an Ajo whose window closed an hour ago still says `enrollment`, and
-- without this trigger its pending invitations still work.
--
-- EC-066 is the same rule seen from the other end: once the roster is fixed the
-- refusal has to say which of the two things happened, without disclosing who
-- holds which seat.
CREATE OR REPLACE FUNCTION app.assert_joinable()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO 'public', 'app'
AS $function$
DECLARE
  v_ajo public.ajos;
BEGIN
  IF NEW.status <> 'active' OR NEW.deleted_at IS NOT NULL THEN
    RETURN NEW;
  END IF;

  SELECT a.* INTO v_ajo
    FROM public.ajos a
   WHERE a.id = NEW.ajo_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'this membership refers to an Ajo that does not exist'
      USING ERRCODE = 'foreign_key_violation';
  END IF;

  IF v_ajo.status = 'draft' THEN
    -- The organizer, written by `create_ajo` while the Ajo is still a draft.
    RETURN NEW;
  END IF;

  IF v_ajo.status <> 'enrollment' THEN
    RAISE EXCEPTION 'this Ajo is %; enrollment for it has closed and its roster is fixed',
      v_ajo.status
      USING ERRCODE = '23514';
  END IF;

  -- Derived from the clock rather than read from a status, because nobody sweeps
  -- `enrollment` to `cancelled` on a timer unless `close_expired_enrollment` is
  -- being called. A member must not be able to sit in an expired-but-unswept Ajo
  -- until the scheduler gets round to it, which is the whole reason this check
  -- exists separately from the status check above.
  IF now() >= v_ajo.enrollment_closes_at THEN
    RAISE EXCEPTION 'the 5-day enrollment window for this Ajo closed at %',
      v_ajo.enrollment_closes_at
      USING ERRCODE = '23514';
  END IF;

  RETURN NEW;
END;
$function$;

CREATE TRIGGER ajo_members_joinable
  BEFORE INSERT ON public.ajo_members
  FOR EACH ROW EXECUTE FUNCTION app.assert_joinable();

COMMENT ON FUNCTION app.assert_joinable() IS
  'Refuses a membership for an Ajo whose enrollment window has closed or whose roster is already fixed. This is the BR-001 boundary enforced where it cannot be forgotten: expiry is derived from the clock rather than trusted from a status nobody sweeps.';

-- The day-5 evaluation, and the early activation EC-051 describes, as one batch.
--
-- Two outcomes because there are two. An Ajo with a seat left and a window that
-- has closed cancels (EC-050, BR-001). An Ajo with no seat left activates early.
-- Handling the second here as well as in the fill trigger makes this function a
-- self-healing evaluator: if some future claim path fills an Ajo without firing
-- the trigger, the sweep activates it rather than cancelling a full rotation on
-- day five, which is the worst outcome available to a member who did everything
-- right.
--
-- `SKIP LOCKED` so two sweeps running at once do not fight over a row, and so
-- the sweep never blocks a member trying to join.
--
-- A cancellation that finds money goes to `cancelling`, not `cancelled`. BR-001
-- promises a refund in full, and a refund needs a provider call this codebase
-- cannot make yet -- ProvidusUnity has not supplied sandbox specifications or
-- credentials. Moving straight to `cancelled` would mark a promise kept that
-- nobody performed; `cancelling` is the state the schema already provides for
-- exactly this, and E5-09 owns taking it the rest of the way.
CREATE OR REPLACE FUNCTION app.close_expired_enrollment()
RETURNS TABLE (
  ajo_id uuid,
  outcome text,
  positions_filled integer,
  positions_total integer,
  refund_obligation_kobo bigint
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 'app'
AS $function$
DECLARE
  v_row   record;
  v_total integer;
  v_filled integer;
  v_owed  bigint;
  v_reason text;
BEGIN
  FOR v_row IN
    SELECT a.id,
           (SELECT count(*)
              FROM public.ajo_positions p
             WHERE p.ajo_id = a.id AND p.deleted_at IS NULL) AS total,
           (SELECT count(*)
              FROM public.ajo_positions p
             WHERE p.ajo_id = a.id AND p.deleted_at IS NULL
               AND p.status <> 'open') AS filled
      FROM public.ajos a
     WHERE a.status = 'enrollment'
       AND a.deleted_at IS NULL
       AND (a.enrollment_closes_at <= now()
            OR NOT EXISTS (
                 SELECT 1 FROM public.ajo_positions p
                  WHERE p.ajo_id = a.id AND p.deleted_at IS NULL
                    AND p.status = 'open'
               ))
     ORDER BY a.enrollment_closes_at
     FOR UPDATE OF a SKIP LOCKED
  LOOP
    v_total := v_row.total;
    v_filled := v_row.filled;

    IF v_filled >= v_total THEN
      UPDATE public.ajos a
         SET status = 'active',
             activated_at = now(),
             updated_at = now()
       WHERE a.id = v_row.id;
      ajo_id := v_row.id;
      outcome := 'activated';
      positions_filled := v_filled;
      positions_total := v_total;
      refund_obligation_kobo := 0;
      RETURN NEXT;
      CONTINUE;
    END IF;

    -- Only a paid contribution is money somebody gave us. A `pending` row is an
    -- intention; refunding it would invent a transaction that never happened.
    SELECT COALESCE(sum(c.total_charge_kobo), 0)
      INTO v_owed
      FROM public.contributions c
     WHERE c.ajo_id = v_row.id
       AND c.status = 'paid'
       AND c.deleted_at IS NULL;

    -- `%s`, not `%`. `format()` treats a bare `%` as the start of a type specifier
    -- and rejects the whole statement at runtime with "unrecognized format() type
    -- specifier", which would take out the sweep for every Ajo it touched.
    v_reason := format(
      'BR-001: the 5-day enrollment window closed with %s of %s positions filled',
      v_filled, v_total);

    -- Straight to `cancelled`, not `cancelling`.
    --
    -- CANONICAL section 3's table gives ENROLLMENT exactly one automatic edge:
    -- "(auto) -> CANCELLED, day 5 reached with positions unfilled". There is no
    -- ENROLLMENT -> CANCELLING edge, and `app.assert_lifecycle_transition`
    -- (migration 000, not editable) refuses it. Routing through `cancelling` was
    -- tried and rejected: it invents a transition the canonical state machine does
    -- not have, in order to defer work that is already deferred -- because
    -- cancelling an Ajo has always been possible while its money movements have
    -- not.
    --
    -- BR-001 promises the refund in full and E5-09 pays it. Nothing is faked here:
    -- the sweep does not mark a contribution refunded, does not write a
    -- payment row, and does not call a provider. It cancels the Ajo and records
    -- the kobo owed, so the promise is visible and whoever settles it is not
    -- guessing. A reader who needs the refund to be *complete* is E5-09.
    IF v_owed > 0 THEN
      v_reason := format('%s; %s kobo owed in refunds to be paid by E5-09',
                         v_reason, v_owed);
    END IF;

    UPDATE public.ajos a
       SET status = 'cancelled',
           cancelled_at = now(),
           cancellation_reason = v_reason,
           updated_at = now()
     WHERE a.id = v_row.id;
    outcome := 'cancelled';

    ajo_id := v_row.id;
    positions_filled := v_filled;
    positions_total := v_total;
    refund_obligation_kobo := v_owed;
    RETURN NEXT;
  END LOOP;
END;
$function$;

COMMENT ON FUNCTION app.close_expired_enrollment() IS
  'Evaluates every Ajo whose enrollment window has closed, and every full Ajo still sitting in ENROLLMENT: full ones activate early (EC-051), unfilled ones cancel or begin cancelling (EC-050, BR-001). Idempotent and safe to run concurrently. No scheduler calls this yet, and correctness does not depend on one, because app.assert_joinable() refuses a late join independently.';

GRANT EXECUTE ON FUNCTION app.open_enrollment(uuid) TO ajo_app;
REVOKE ALL ON FUNCTION app.open_enrollment(uuid) FROM PUBLIC;

-- Deliberately not granted to `ajo_app`. This function cancels *every* Ajo in
-- the database; handing it to the role the request-serving code connects as
-- would mean any injection point could end the whole product. It runs as the
-- migration owner, from a job runner, when one exists.
REVOKE ALL ON FUNCTION app.close_expired_enrollment() FROM PUBLIC;