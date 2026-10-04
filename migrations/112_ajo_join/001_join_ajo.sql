-- 112: redeeming an invitation -- joining an Ajo and claiming a seat.
--
-- `POST /api/v1/invitations/accept` and `POST /api/v1/invitations/:token/decline`
-- (spec section 11.5) are writes to `ajo_members`, `ajo_positions` and
-- `invitations` at once, and none of those tables has an INSERT or UPDATE policy
-- that would let `ajo_app` do it directly. There is a second reason beyond the
-- first: the whole point of accepting is to claim *a specific* seat out of many
-- without two invitees winning the same one. That is a read-then-write race,
-- and the only place it can be made atomic is inside the transaction that owns
-- the rows.
--
-- `app.join_ajo` is therefore the join path, and it is deliberately the only
-- one. A route that inserted the member row itself and then claimed a seat
-- afterwards would produce the exact state FR-INV-005 forbids -- a membership
-- with no position -- every time the process died between the two writes.
--
-- The seat is claimed with `FOR UPDATE SKIP LOCKED`, so two invitees accepting
-- at the same moment cannot both be handed the last open seat: the loser is
-- told the Ajo is full rather than being given a seat someone else holds. That
-- is the concurrency property section 11.5 asks of the whole lifecycle, proven
-- here at the only layer that can prove it.
--
-- `app.decline_invitation` is the same shape for the smaller fact: it spends a
-- token without creating anything, which frees the partial unique index slot so
-- the organizer can invite that address again.
--
-- Every table in both functions is aliased. `RETURNS TABLE (ajo_id uuid, ...)`
-- declares PL/pgSQL variables named `ajo_id`, `position_number` and
-- `rules_version`, and an unqualified `WHERE ajo_id = ...` is then ambiguous
-- between the variable and the column -- 42702, at run time, on the first
-- accepting invitee. The aliases are not style.

-- The version a member consented to, on the row that proves they joined.
--
-- Nullable, and not as an oversight: the organizer's own membership is written
-- by `app.create_ajo` before any rules were ever shown to them, and an
-- organizer does not consent to the rules of an Ajo they are running. Only an
-- invitee has something to acknowledge.
--
-- It is stored rather than logged because "the member agreed to the rules" is
-- the fact a dispute is actually about, and a fact you cannot name the version
-- of is no use in one. See `AJO_RULES_VERSION` in the domain, which is the
-- authority for the text; the check below is what keeps a stale acknowledgement
-- out, and `scripts/test_migrations.py` asserts the two agree.
ALTER TABLE public.ajo_members
  ADD COLUMN IF NOT EXISTS rules_acknowledged_version smallint;

CREATE OR REPLACE FUNCTION app.ajo_rules_version()
RETURNS smallint
LANGUAGE sql
STABLE
AS $function$
  SELECT 1::smallint;
$function$;

COMMENT ON FUNCTION app.ajo_rules_version() IS
  'The version of the Ajo rules text currently being consented to. Mirrors AJO_RULES_VERSION in packages/domain/src/invitations.ts, which owns the clauses themselves.';

CREATE OR REPLACE FUNCTION app.join_ajo(
  p_token_hash bytea,
  p_email text,
  p_rules_version smallint
)
RETURNS TABLE (ajo_id uuid, position_number integer, rules_version integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 'app'
AS $function$
DECLARE
  v_user_id  uuid := app.request_user_id();
  v_inv      public.invitations;
  v_ajo      public.ajos;
  v_email    citext := btrim(p_email)::citext;
  v_position public.ajo_positions;
  v_number   integer;
BEGIN
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'joining requires an authenticated caller'
      USING ERRCODE = '28000';
  END IF;

  SELECT i.* INTO v_inv
    FROM public.invitations i
   WHERE i.token_hash = p_token_hash
     AND i.deleted_at IS NULL
   FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'that invitation link is not valid'
      USING ERRCODE = 'P0002';
  END IF;

  IF v_inv.email <> v_email THEN
    -- 42501 and not 404: the caller is authenticated, so saying "this link is
    -- not yours" leaks nothing they could not already learn, and it is the
    -- honest answer. It is also the rule that stops one member redeeming a
    -- link that was forwarded to them by another.
    RAISE EXCEPTION 'this invitation was sent to a different address'
      USING ERRCODE = '42501';
  END IF;

  IF v_inv.status <> 'pending' THEN
    RAISE EXCEPTION 'this invitation is already %', v_inv.status
      USING ERRCODE = '23514';
  END IF;

  -- Derived, not trusted: the row is still `pending` after it lapses because
  -- nothing sweeps the table on a timer.
  IF v_inv.expires_at <= now() THEN
    RAISE EXCEPTION 'this invitation has expired'
      USING ERRCODE = '23514';
  END IF;

  -- Refused before the seat is claimed, so a stale consent cannot leave a
  -- claimed seat and a rolled-back membership behind. The API layer already
  -- insists the invitee *acknowledged* something; this insists it was the
  -- current thing.
  IF p_rules_version IS DISTINCT FROM app.ajo_rules_version() THEN
    RAISE EXCEPTION 'the Ajo rules have changed since this invitation was sent; read them again before joining'
      USING ERRCODE = '23514';
  END IF;

  SELECT a.* INTO v_ajo
    FROM public.ajos a
   WHERE a.id = v_inv.ajo_id
     AND a.deleted_at IS NULL;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'the Ajo this invitation refers to no longer exists'
      USING ERRCODE = '23514';
  END IF;

  IF v_ajo.status <> 'draft' AND v_ajo.status <> 'enrollment' THEN
    RAISE EXCEPTION 'this Ajo is % and is no longer taking members', v_ajo.status
      USING ERRCODE = '23514';
  END IF;

  -- Already in: FR-INV-005. Checked before the seat is claimed, so a repeat
  -- accept cannot burn a seat and then fail.
  IF EXISTS (
    SELECT 1
      FROM public.ajo_members m
     WHERE m.ajo_id = v_ajo.id
       AND m.user_id = v_user_id
       AND m.deleted_at IS NULL
  ) THEN
    RAISE EXCEPTION 'you are already a member of this Ajo'
      USING ERRCODE = '23505';
  END IF;

  SELECT pos.* INTO v_position
    FROM public.ajo_positions pos
   WHERE pos.ajo_id = v_ajo.id
     AND pos.status = 'open'
     AND pos.deleted_at IS NULL
   ORDER BY pos.position_number
   FOR UPDATE SKIP LOCKED
   LIMIT 1;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'this Ajo has no free positions left'
      USING ERRCODE = '23514';
  END IF;

  v_number := v_position.position_number;

  UPDATE public.ajo_positions pos
     SET status = 'claimed',
         updated_at = now()
   WHERE pos.id = v_position.id;

  INSERT INTO public.ajo_members (
    ajo_id, user_id, position_id, invitation_id, status, joined_at,
    rules_acknowledged_version
  ) VALUES (
    v_ajo.id, v_user_id, v_position.id, v_inv.id, 'active', now(),
    p_rules_version
  );

  UPDATE public.invitations inv
     SET status = 'accepted',
         accepted_by_user_id = v_user_id,
         accepted_at = now(),
         updated_at = now()
   WHERE inv.id = v_inv.id;

  -- Cast, because the return column is `integer` and the acknowledgement is
  -- stored as `smallint`. Without it PostgreSQL reports 42804 at run time.
  RETURN QUERY SELECT v_ajo.id, v_number, p_rules_version::integer;
END;
$function$;

COMMENT ON FUNCTION app.join_ajo(bytea, text, smallint) IS
  'Claims the lowest open seat, creates the active membership, and spends the invitation, in one transaction. Single-use: the invitation is FOR UPDATE-locked and its status is re-checked. Refuses an acknowledgement of any version but the current one, and records that version on the membership. Returns the Ajo, the seat number, and the rules version the joiner acknowledged (BR-004).';

CREATE OR REPLACE FUNCTION app.decline_invitation(p_token_hash bytea, p_email text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 'app'
AS $function$
DECLARE
  v_inv public.invitations;
BEGIN
  IF app.request_user_id() IS NULL THEN
    RAISE EXCEPTION 'declining requires an authenticated caller'
      USING ERRCODE = '28000';
  END IF;

  SELECT i.* INTO v_inv
    FROM public.invitations i
   WHERE i.token_hash = p_token_hash
     AND i.deleted_at IS NULL
   FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'that invitation link is not valid'
      USING ERRCODE = 'P0002';
  END IF;

  IF v_inv.email <> btrim(p_email)::citext THEN
    RAISE EXCEPTION 'this invitation was sent to a different address'
      USING ERRCODE = '42501';
  END IF;

  IF v_inv.status <> 'pending' THEN
    RAISE EXCEPTION 'this invitation is already %', v_inv.status
      USING ERRCODE = '23514';
  END IF;

  -- An expired link cannot be declined either. Accepting one is refused for the
  -- same reason, and it would be strange for the refusal to depend on which
  -- verb the caller chose.
  IF v_inv.expires_at <= now() THEN
    RAISE EXCEPTION 'this invitation has expired'
      USING ERRCODE = '23514';
  END IF;

  UPDATE public.invitations inv
     SET status = 'declined',
         declined_at = now(),
         updated_at = now()
   WHERE inv.id = v_inv.id;

  RETURN true;
END;
$function$;

COMMENT ON FUNCTION app.decline_invitation(bytea, text) IS
  'Spends a pending invitation without creating a membership, which frees the partial unique index slot so the organizer may invite that address again.';

-- Same grant discipline as migration 111: `ajo_app` (and therefore `ajo_api`,
-- which is a member of it) may call these; PUBLIC may not.
GRANT EXECUTE ON FUNCTION app.ajo_rules_version() TO ajo_app;
REVOKE ALL ON FUNCTION app.ajo_rules_version() FROM PUBLIC;

GRANT EXECUTE ON FUNCTION app.join_ajo(bytea, text, smallint) TO ajo_app;
REVOKE ALL ON FUNCTION app.join_ajo(bytea, text, smallint) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION app.decline_invitation(bytea, text) TO ajo_app;
REVOKE ALL ON FUNCTION app.decline_invitation(bytea, text) FROM PUBLIC;