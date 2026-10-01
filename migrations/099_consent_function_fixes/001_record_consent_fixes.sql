-- Correcting `app.record_consent`, which could not be called at all.
--
-- Found by the API integration test, and the two bugs are both about the same
-- thing: `audit_logs` is the most locked-down table in the schema, and this
-- function was written as though it were an ordinary one.
--
-- Bug 1: it wrote the GUC's value straight into `audit_logs.actor_type`. The
-- two columns have different vocabularies, and neither is derivable from the
-- other by accident:
--
--   * `app.actor_type` -- read by `app.request_actor_type()` -- is 'anon' or
--     'member'. It is the *authorisation* vocabulary, and `users_update_own` and
--     `profiles_update_own` compare against exactly 'member'.
--   * `audit_logs.actor_type` -- a CHECK constraint -- allows user, system,
--     service, webhook. It is the *descriptive* vocabulary, where the human
--     equivalent of 'member' is 'user'.
--
-- Writing 'member' into the column therefore violated the CHECK constraint, and
-- because the value only becomes a string at runtime, no type checker could have
-- caught it. The API surfaced it as a 500 on every registration, which is the
-- correct behaviour for an unexpected error and a useless place to have found it.
--
-- Bug 2: it used `RETURNING id`, which makes the INSERT read the row back. Under
-- RLS that read is authorised by the table's SELECT policies, and the only one on
-- `audit_logs` is `audit_logs_select_staff`, which requires
-- `app.is_platform_staff()`. So the INSERT was refused for every member, with an
-- error about the row violating policy -- which reads as though the write were
-- forbidden, when the write was fine and only the read-back was not.
--
-- Both were found together because a `SECURITY DEFINER` function on a table with
-- `FORCE ROW LEVEL SECURITY` runs the INSERT as its owner and gets no exemption
-- from the SELECT policies, so a function that "only inserts" can still fail on
-- a read it did not know it was doing.
--
-- This is a replacement rather than a new function because the contract is
-- unchanged: same name, same arguments, same return value. A caller that got a
-- 500 from the old one gets a working call from this.
CREATE OR REPLACE FUNCTION app.record_consent(
  p_document text,
  p_version  text,
  p_accepted boolean
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = app, public
AS $fn$
DECLARE
  v_user_id uuid := app.request_user_id();
  v_id      uuid := app.uuidv7();
  -- The column's vocabulary, mapped from the GUC's. Only the two cases that can
  -- reach this function are mapped: it refuses a NULL identity below, so
  -- 'anon' cannot arrive from a caller that got that far, and anything else
  -- falls through to 'system' rather than being passed through unvalidated.
  v_actor_type text;
BEGIN
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'consent cannot be recorded without an identity'
      USING ERRCODE = 'insufficient_privilege';
  END IF;

  v_actor_type := CASE app.request_actor_type()
    WHEN 'member' THEN 'user'
    ELSE 'system'
  END;

  -- The id is generated here and passed explicitly, rather than taken from the
  -- column default and returned. `RETURNING` is what bug 2 was: reading the row
  -- back is a SELECT, and this function has no business reading `audit_logs`.
  INSERT INTO audit_logs (id, actor_user_id, actor_type, action, subject_type, subject_id, after_state)
  VALUES
    (v_id,
     v_user_id,
     v_actor_type,
     'insert',
     'user',
     v_user_id,
     jsonb_build_object(
       'event', 'consent',
       'document', p_document,
       'version', p_version,
       'accepted', p_accepted,
       'recorded_at', now()
     ));

  RETURN v_id;
END;
$fn$;

COMMENT ON FUNCTION app.record_consent(text, text, boolean) IS
  'Records consent evidence in audit_logs. SECURITY DEFINER owned by '
  'ajo_migrator, because audit_logs grants INSERT to no application role, and '
  'it takes no subject id, so it can only ever record for the caller. Returns '
  'the audit row id, generated in advance rather than read back with RETURNING, '
  'which would need a SELECT policy this table deliberately denies.';
