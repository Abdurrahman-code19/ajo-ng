-- 111: inviting members to an Ajo.
--
-- `POST /api/v1/invitations` (spec section 11.5) mints one single-use,
-- time-limited invitation per invited address. Two writes are needed and both
-- are `SECURITY DEFINER` for the same reason migration 110's create is: there is
-- no INSERT policy on `public.invitations` (only SELECT), and there should not
-- be. A policy that let `ajo_app` insert invitations directly would let any
-- caller name any `ajo_id` and any `invited_by_user_id`, minting invitations
-- into somebody else's Ajo. The functions derive the actor from
-- `app.request_user_id()` and take no organizer id, so they can only ever act
-- for the caller who owns the Ajo.
--
-- Email-only for now. Section 11.5's request shape carries a `phoneNumber` and
-- an SMS channel, but the schema (and section 9's own description of
-- `invitations`) addresses an invitation by email, and there is no SMS provider
-- until `E7-05`. Rather than invent a `phone_number` column ahead of the
-- provider that would need it, the divergence is recorded here and the email
-- path is built exactly. The 72-hour default expiry is section 11.5's own
-- number, marked there as an open decision; it lives in the domain as
-- `INVITATION_TTL_HOURS` so the decision changes one constant.
--
-- Two functions:
--   * `create_invitation` -- the write, gated on the caller being the organizer
--     of an Ajo that is still collecting members.
--   * `preview_invitation` -- the read behind `GET /api/v1/invitations/:token`,
--     which is *anonymous*. It returns a curated `jsonb` projection rather than
--     the row, because FR-INV-003 is explicit that a preview must not disclose
--     the Ajo's other members or the pot value. A function that returned the
--     invitation row would hand an anonymous caller the Ajo id; one that joined
--     the members table would leak the roster. The projection returns only what
--     the invitee is allowed to see.

CREATE OR REPLACE FUNCTION app.create_invitation(
  p_ajo_id uuid,
  p_email text,
  p_token_hash bytea,
  p_expires_at timestamp with time zone,
  p_message text
) RETURNS public.invitations
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 'app'
AS $function$
DECLARE
  v_user_id uuid := app.request_user_id();
  v_ajo     public.ajos;
  v_occupied integer;
  v_inv     public.invitations;
BEGIN
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'create_invitation requires an authenticated caller'
      USING ERRCODE = '28000';
  END IF;

  SELECT * INTO v_ajo
    FROM public.ajos
   WHERE id = p_ajo_id
     AND deleted_at IS NULL;

  IF NOT FOUND THEN
    -- 42501 rather than 404: telling a caller "no such Ajo" for one they do not
    -- own would let them probe which ids exist. "Not yours" and "not there" are
    -- the same answer from outside.
    RAISE EXCEPTION 'no Ajo to invite to, or the caller does not own it'
      USING ERRCODE = '42501';
  END IF;

  IF v_ajo.organizer_user_id <> v_user_id THEN
    RAISE EXCEPTION 'only the organizer may invite members to this Ajo'
      USING ERRCODE = '42501';
  END IF;

  -- Invitations belong to the collecting phase. Once enrollment closes -- or the
  -- Ajo is cancelled or frozen -- the roster is fixed and a new invite would be
  -- an entry nobody can accept.
  IF v_ajo.status <> 'draft' AND v_ajo.status <> 'enrollment' THEN
    RAISE EXCEPTION 'invitations are closed once an Ajo is %', v_ajo.status
      USING ERRCODE = '23514';
  END IF;

  -- "Full" counts occupied seats, not members: the organizer occupies seat 1
  -- from creation, so a five-member Ajo has four seats to invite into.
  SELECT count(*) INTO v_occupied
    FROM public.ajo_positions
   WHERE ajo_id = p_ajo_id
     AND status IN ('claimed', 'locked')
     AND deleted_at IS NULL;

  IF v_occupied >= v_ajo.position_count THEN
    RAISE EXCEPTION 'this Ajo has no free positions'
      USING ERRCODE = '23514';
  END IF;

  IF p_email IS NULL OR position('@' IN btrim(p_email)) = 0 THEN
    RAISE EXCEPTION 'an invitation needs an email address'
      USING ERRCODE = '23514';
  END IF;

  -- An address already in the Ajo is not invitable again. `citext` makes this
  -- the same comparison the unique index makes below.
  IF EXISTS (
    SELECT 1
      FROM public.ajo_members m
      JOIN public.users u ON u.id = m.user_id
     WHERE m.ajo_id = p_ajo_id
       AND m.deleted_at IS NULL
       AND u.email = btrim(p_email)::citext
  ) THEN
    RAISE EXCEPTION 'that address is already a member of this Ajo'
      USING ERRCODE = '23505';
  END IF;

  IF p_expires_at IS NULL OR p_expires_at <= now() THEN
    RAISE EXCEPTION 'an invitation must expire in the future'
      USING ERRCODE = '23514';
  END IF;

  -- A second pending invitation to the same address for the same Ajo is refused
  -- by `invitations_one_pending_per_ajo_email` (23505), which is the database
  -- enforcing FR-INV-005's "never duplicate a membership" without this function
  -- having to remember to.
  INSERT INTO public.invitations (
    ajo_id, email, token_hash, invited_by_user_id, expires_at, message
  ) VALUES (
    p_ajo_id, btrim(p_email)::citext, p_token_hash, v_user_id, p_expires_at, p_message
  )
  RETURNING * INTO v_inv;

  RETURN v_inv;
END;
$function$;

COMMENT ON FUNCTION app.create_invitation(uuid, text, bytea, timestamp with time zone, text) IS
  'Mints one pending invitation for the authenticated organizer of a draft or enrolling Ajo. Derives the inviter from app.request_user_id(); never accepts it. Refuses a full Ajo, a non-collecting Ajo, and an address already in the Ajo.';

-- FR-INV-003: "must not disclose the Ajo's other members or the pot value". The
-- projection is the disclosure boundary, stated in one place, and it is a
-- function because the caller is anonymous and cannot read `ajos` through RLS.
CREATE OR REPLACE FUNCTION app.preview_invitation(p_token_hash bytea)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO 'public', 'app'
AS $function$
  SELECT jsonb_build_object(
    'status', i.status::text,
    'expiresAt', i.expires_at,
    'ajo', jsonb_build_object(
      'id', a.id,
      'name', a.name,
      'status', a.status::text,
      'contributionKobo', a.contribution_amount_kobo,
      'currency', btrim(a.currency::text),
      'frequencyCode', cf.code,
      'collectionDay', a.collection_day,
      'durationRounds', a.total_rounds,
      'maxMembers', a.position_count,
      'membersCount', (
        SELECT count(*)
          FROM public.ajo_positions p
         WHERE p.ajo_id = a.id
           AND p.status IN ('claimed', 'locked')
           AND p.deleted_at IS NULL
      ),
      'endsAt', COALESCE(a.enrollment_closes_at, i.expires_at)
    ),
    'organizer', jsonb_build_object(
      -- A display name or nothing; never the organizer's email, phone or id.
      'name', COALESCE(pr.display_name, 'The organizer')
    ),
    'positionOptions', COALESCE((
      SELECT jsonb_agg(p.position_number ORDER BY p.position_number)
        FROM public.ajo_positions p
       WHERE p.ajo_id = a.id
         AND p.status = 'open'
         AND p.deleted_at IS NULL
    ), '[]'::jsonb)
  )
    FROM public.invitations i
    JOIN public.ajos a ON a.id = i.ajo_id
    LEFT JOIN public.contribution_frequencies cf ON cf.id = a.frequency_id
    LEFT JOIN public.profiles pr
      ON pr.user_id = a.organizer_user_id AND pr.deleted_at IS NULL
   WHERE i.token_hash = p_token_hash
     AND i.deleted_at IS NULL;
$function$;

COMMENT ON FUNCTION app.preview_invitation(bytea) IS
  'Anonymous preview of an invitation by token hash. Returns a curated jsonb with no member roster and no pot value (FR-INV-003), or NULL when the token matches no invitation.';

-- `ajo_app` only, and PUBLIC revoked explicitly. `ajo_api` is a member of
-- `ajo_app` and inherits EXECUTE, which is what lets the unauthenticated preview
-- route call it; PUBLIC is the dangerous grant, because it would let any role on
-- the cluster address it.
GRANT EXECUTE ON FUNCTION app.create_invitation(
  uuid, text, bytea, timestamp with time zone, text
) TO ajo_app;
REVOKE ALL ON FUNCTION app.create_invitation(
  uuid, text, bytea, timestamp with time zone, text
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION app.preview_invitation(bytea) TO ajo_app;
REVOKE ALL ON FUNCTION app.preview_invitation(bytea) FROM PUBLIC;
