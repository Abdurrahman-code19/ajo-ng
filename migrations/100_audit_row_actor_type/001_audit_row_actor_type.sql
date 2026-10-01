-- Mapping `app.actor_type` onto `audit_logs.actor_type` in `app.audit_row()`.
--
-- This is a bug in the adopted schema, not in the API, and it is why the API's
-- first registration attempt failed with a 500.
--
-- Two things called `actor_type`, with two different vocabularies:
--
--   * `app.actor_type` is a GUC, read by `app.request_actor_type()`, and its
--     values are 'anon' and 'member'. It answers "who is this request acting as,
--     for the purposes of authorising it", and `users_update_own` and
--     `profiles_update_own` both compare against exactly 'member'.
--
--   * `audit_logs.actor_type` is a column with a CHECK constraint allowing
--     'user', 'system', 'service' and 'webhook'. It answers "what kind of thing
--     did this", for a human reading the trail months later, where the word for
--     a member is 'user'.
--
-- `audit_row()` passed the GUC value straight through, so any audited write with
-- `app.actor_type` set to 'member' -- which is every write the API makes, because
-- the policies require it -- violated the CHECK constraint and rolled back.
--
-- It went unnoticed for two reasons. The GUC's default is 'service', which *is* a
-- legal column value, so a write with the GUC unset works. And the migration test
-- suite never set the GUC, so its passing audited-write test was passing on the
-- default rather than on the path an application actually takes. The constraint
-- was right all along; nothing was checking the case it was written to catch.
--
-- The fix belongs here rather than in the API because the GUC value is correct:
-- the policies depend on it, and changing it to satisfy an audit column would
-- break authorisation to fix a vocabulary mismatch. The translation belongs where
-- the two vocabularies meet.
--
-- 'anon' maps to 'system' because the column has no anonymous value and a request
-- with no identity is a background or service action as far as the trail is
-- concerned. It cannot in practice reach here: `audit_row()` runs only from
-- triggers on member tables, each of which requires an identity first. Mapping it
-- anyway is for totality, not for a case that occurs.
--
-- The rest of the function is the version that was already applied, with this one
-- expression changed. It is reproduced in full rather than patched in place
-- because a migration is the only place a function body can be replaced, and
-- reproducing it is what makes the diff reviewable.
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
       WHEN 'member' THEN 'user'
       WHEN 'anon'   THEN 'system'
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
  'app.actor_type (anon|member) onto audit_logs.actor_type '
  '(system|user|service|webhook), which is a different vocabulary with a CHECK '
  'constraint that the GUC values alone do not satisfy.';
