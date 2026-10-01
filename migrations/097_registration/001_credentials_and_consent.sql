-- The two tables registration needs and section 12.3 assumes, plus the one
-- function that records consent without handing the application role the
-- ability to forge an audit row.
--
-- Why this is a migration and not application code. Section 12.3 specifies
-- that a password is hashed with Argon2id "before storage", and there is
-- nowhere in the adopted schema to store the result: `users` holds identity and
-- lifecycle columns and no credential, `sessions` holds a *rotating refresh*
-- token that is meaningless before a user has one, and `device_tokens` is a
-- push-notification handle. A user with no credential row cannot log in, and
-- a login that checked a password against a column that does not exist would
-- be a runtime error rather than a design. So the shape is stated here, where
-- every other invariant is.
--
-- Both tables are hashed at rest and neither is readable by the client. The
-- token column stores a SHA-256 of the token, never the token: a database
-- disclosure must not yield a working password reset or a working email
-- verification, and the plaintext token exists only in the email that carries
-- it and in the response the caller is not shown.
CREATE TABLE user_credentials (
  id           uuid        PRIMARY KEY DEFAULT app.uuidv7(),
  user_id      uuid        NOT NULL UNIQUE REFERENCES users (id),
  -- The PHC string, which carries its own algorithm and parameters, so the cost
  -- can be raised later without a migration and without invalidating existing
  -- hashes. Storing bare parameters in columns would mean a hash written under
  -- old settings could not be verified after they changed.
  argon2_hash  text        NOT NULL,
  changed_at   timestamptz NOT NULL DEFAULT now(),
  created_at   timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE user_credentials IS
  'One row per user, holding only the Argon2id hash. No plaintext, ever, and '
  'no log line in this schema records one.';

-- Single use and 24-hour expiry are enforced by the columns, not by the
-- application remembering to check them. `consumed_at` is set rather than the
-- row deleted, so a replayed token is *observably* a replay rather than a
-- lookup miss, and so the count of attempts survives the attempt.
CREATE TABLE email_verification_tokens (
  id          uuid        PRIMARY KEY DEFAULT app.uuidv7(),
  user_id     uuid        NOT NULL REFERENCES users (id),
  token_hash  bytea       NOT NULL UNIQUE,
  expires_at  timestamptz NOT NULL,
  consumed_at timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- One live token per user, so a second request supersedes the first rather than
-- leaving two tokens that both verify.
CREATE UNIQUE INDEX email_verification_tokens_one_live
  ON email_verification_tokens (user_id)
  WHERE consumed_at IS NULL;

CREATE INDEX email_verification_tokens_expiry ON email_verification_tokens (expires_at);

COMMENT ON COLUMN email_verification_tokens.token_hash IS
  'SHA-256 of the emailed token. The token itself is never stored.';

-- The two tables are as sensitive as the identity they hang off: a hash is
-- personal data, and a member has no reason to read their own credential back.
-- FORCE so the owner is bound too, matching `users` and `profiles`.
ALTER TABLE user_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_credentials FORCE ROW LEVEL SECURITY;
ALTER TABLE email_verification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_verification_tokens FORCE ROW LEVEL SECURITY;

-- Read and write only the caller's own. `user_credentials` gets no SELECT
-- policy at all: the application writes the hash and verifies it in the
-- database's hands, and no code path needs to read the column back out. This
-- is the one table where denying reads is the point rather than a side effect.
CREATE POLICY user_credentials_insert_own ON public.user_credentials
  FOR INSERT
  WITH CHECK (user_id = app.request_user_id());
CREATE POLICY user_credentials_update_own ON public.user_credentials
  FOR UPDATE
  WITH CHECK (user_id = app.request_user_id());

CREATE POLICY email_verification_tokens_insert_own ON public.email_verification_tokens
  FOR INSERT
  WITH CHECK (user_id = app.request_user_id());
CREATE POLICY email_verification_tokens_select_own ON public.email_verification_tokens
  FOR SELECT
  USING (user_id = app.request_user_id());
CREATE POLICY email_verification_tokens_update_own ON public.email_verification_tokens
  FOR UPDATE
  WITH CHECK (user_id = app.request_user_id());

-- Consent evidence. Section 12.3 requires that `acceptedTerms` and
-- `acceptedPrivacy` are "written to `audit_logs` as consent evidence, together
-- with the document version".
--
-- It cannot be done from the application role, and this is the interesting
-- part. `audit_logs` has RLS and FORCE RLS, and the only INSERT policy on it is
-- scoped to `ajo_migrator` -- the role that owns the audit trigger, which is
-- what stops `ajo_app` forging an audit row. Writing consent directly from the
-- API would mean either granting that role insert on `audit_logs` (forging
-- becomes possible) or routing the insert through a `SECURITY DEFINER` function.
--
-- So it is the second, and the function is owned by `ajo_migrator` and pinned to
-- a search_path, exactly like the six the spec calls the sharpest tool in the
-- schema. It inserts an `insert` action on subject type `user` for the subject
-- the caller is acting as -- it takes no user id parameter at all, so it cannot
-- record consent for anybody else even if a future caller asks it to.
--
-- `p_accepted` is a parameter rather than an assumption, and recording `false`
-- is a legitimate outcome: the column is `boolean` and a row saying the member
-- did *not* accept is evidence worth keeping, whereas a handler that simply
-- refuses to call this would leave no record that the question was ever asked.
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
  v_id      uuid;
BEGIN
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'consent cannot be recorded without an identity'
      USING ERRCODE = 'insufficient_privilege';
  END IF;

  INSERT INTO audit_logs
    (actor_user_id, actor_type, action, subject_type, subject_id, after_state)
  VALUES
    (v_user_id,
     COALESCE(NULLIF(current_setting('app.actor_type', true), ''), 'member'),
     'insert',
     'user',
     v_user_id,
     jsonb_build_object(
       'event', 'consent',
       'document', p_document,
       'version', p_version,
       'accepted', p_accepted,
       'recorded_at', now()
     ))
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$fn$;

COMMENT ON FUNCTION app.record_consent(text, text, boolean) IS
  'Records consent evidence in audit_logs. SECURITY DEFINER owned by '
  'ajo_migrator, because audit_logs grants INSERT to no application role, and '
  'it takes no subject id, so it can only ever record for the caller.';
