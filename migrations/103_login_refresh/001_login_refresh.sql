-- Login, refresh rotation, and reuse detection.
--
-- Section 12.4 states the design and this migration supplies the three pieces of
-- it the adopted schema does not have. What it already has is `sessions`, with
-- `refresh_token_hash` NOT NULL and uniquely indexed, and a comment saying a
-- revoked session that is used again is evidence worth keeping.
--
-- The gap is that rotating a refresh token destroys the evidence. Overwriting
-- `sessions.refresh_token_hash` on rotation means the spent token matches no
-- row, and "this token was already used" becomes indistinguishable from "this
-- token was forged". Both are answered with the same 401, which is correct for
-- the caller and useless for the member: 12.4.2 says presenting an
-- already-rotated token means the token was copied, the whole lineage is
-- revoked, and `security.suspicious_token_reuse` is sent. None of that is
-- possible if the schema cannot tell the two cases apart.
--
-- So the spent hashes go in a second table, and the live one stays on the
-- session row where the adopted schema put it. The unique index on
-- `sessions.refresh_token_hash` then keeps doing its real job -- two live
-- sessions cannot share a token -- and the rotated table is what makes reuse
-- observable.
--
-- A family is a session. This is worth stating because 12.4.2 names "family" as
-- a separate concept and it is not one: a family is one login's rotation
-- lineage, and `sessions` is already one row per login. Rotation never crosses
-- sessions, and a second login on the same device replaces the row rather than
-- extending it -- `sessions_one_active_per_device` forces that already. So
-- "revoke the entire family" is "revoke this session", and 12.4.2's other half,
-- "all sessions for that member are invalidated", is the wider statement that
-- needs a real query. No family table is created, because it would be a second
-- name for a row that exists.
--
-- Three other things ride along because the login flow cannot be written without
-- them:
--
--   * `sessions.refresh_expires_at`, because the adopted table has no column to
--     expire a refresh token against, and "30 days" is not enforceable from a
--     row that cannot record when it started.
--   * A SELECT policy for `ajo_migrator` on `user_credentials`, because
--     `app.verify_login_credential` has to read the Argon2id hash and that table
--     has FORCE ROW LEVEL SECURITY and no SELECT policy for anybody. The
--     alternative -- granting `ajo_app` SELECT -- would let any code path in the
--     API read every member's password hash, which is precisely what 097
--     withheld.
--   * INSERT and UPDATE policies on `sessions`, which has only SELECT and DELETE.
--     Creating a session on login and revoking one are both writes, and the
--     reused-token path revokes *every* session the member has, so without an
--     UPDATE policy the one response that matters most would be the one the
--     database refuses.

-- The spent-token ledger. `user_id` is denormalised onto every row so that
-- "revoke everything this member holds" is one indexed statement rather than a
-- join decided inside a security-critical function.
CREATE TABLE session_rotated_tokens (
  id           uuid        PRIMARY KEY DEFAULT app.uuidv7(),
  session_id   uuid        NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
  user_id      uuid        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  token_hash   bytea       NOT NULL UNIQUE,
  rotated_at   timestamptz NOT NULL,
  -- Kept so a reuse detection can say how stale the copied lineage is, which is
  -- the difference between "someone is using a token from this morning" and
  -- "someone has had a month-old token".
  expires_at   timestamptz NOT NULL
);

CREATE INDEX session_rotated_tokens_session ON session_rotated_tokens (session_id);
CREATE INDEX session_rotated_tokens_user ON session_rotated_tokens (user_id);

COMMENT ON TABLE session_rotated_tokens IS
  'Every refresh token that has been rotated out, hashed. This is what makes '
  'reuse detection possible: without it, a spent token matches no row and is '
  'indistinguishable from a forged one. Section 12.4.2.';

COMMENT ON COLUMN session_rotated_tokens.token_hash IS
  'SHA-256 of the spent token. The token itself is never stored.';

ALTER TABLE sessions
  ADD COLUMN refresh_expires_at timestamptz;

COMMENT ON COLUMN sessions.refresh_expires_at IS
  'When the live refresh_token_hash stops being accepted. 12.4 gives a refresh '
  'token 30 days; without this column the session row cannot record it.';

-- Same treatment as `user_credentials` in 097: RLS on, and FORCE so the owner is
-- bound by it too. The only writer is `app.claim_refresh_token`, so the only
-- policies needed are the ones that function's owner requires.
ALTER TABLE session_rotated_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_rotated_tokens FORCE ROW LEVEL SECURITY;

-- 101 and 102 for this table. `app.claim_refresh_token` runs with no identity --
-- the caller presenting a refresh token has no session yet, and a caller whose
-- token turns out to be stolen is precisely the caller that must not be given
-- one -- so the self-only policies that would normally apply match nothing, and
-- the function's zero-row return would read as a forged token rather than as a
-- missing grant. That is the same failure 101 fixed, in a third place.
CREATE POLICY session_rotated_tokens_select_by_migrator
  ON public.session_rotated_tokens
  FOR SELECT
  TO ajo_migrator
  USING (true);

CREATE POLICY session_rotated_tokens_insert_by_migrator
  ON public.session_rotated_tokens
  FOR INSERT
  TO ajo_migrator
  WITH CHECK (true);

-- Login and refresh both act as the member they have just authenticated, so the
-- session rows they write are their own. `users_insert_own` in 096 is the
-- precedent and the reasoning is the same: a self-owned policy is not relaxed to
-- let signup through, it is satisfied by acting as the row's owner.
--
-- The UPDATE policy is what makes revocation possible, and revocation is not a
-- convenience. 12.4.2 requires that reuse detection invalidates every session
-- the member holds, and 12.4.3 requires that a freeze or a password change kills
-- sessions immediately. Both are UPDATEs on this table, and without a USING
-- clause this policy would expose zero rows and refuse both -- silently, inside
-- a transaction that rolls back, which is the failure mode 102 documents.
CREATE POLICY sessions_insert_own ON public.sessions
  FOR INSERT
  WITH CHECK (user_id = app.request_user_id());

CREATE POLICY sessions_update_own ON public.sessions
  FOR UPDATE
  USING (user_id = app.request_user_id())
  WITH CHECK (user_id = app.request_user_id());

-- The login lookup.
--
-- It has to be a function because `user_credentials` has no SELECT policy for any
-- application role, deliberately: a password hash is not something a member reads
-- back and not something a bug in a route should be able to reach. Argon2id
-- verification is not something the database can do, so the hash has to reach the
-- process that owns the Argon2id library. The narrowest way to arrange that is a
-- function that returns exactly one row for exactly one email address, owned by
-- the role that already owns the table, and callable only by `ajo_app`.
--
-- `p_email` is compared through the same `citext` the column is stored as, so a
-- login is case-insensitive in the same way a registration uniqueness check is.
-- The two must agree: a member who registered as `Ada@Example.ng` and logs in as
-- `ada@example.ng` is the same person, and a comparison that was case-sensitive
-- on one side and not the other would be an account that exists and cannot be
-- reached.
--
-- The cast is load-bearing rather than decorative. `citext` casts to `text`
-- implicitly and the other way only for assignment, so `users.email = p_email`
-- with `p_email` declared `text` resolves to `texteq` -- a byte comparison -- and
-- the function quietly becomes case-sensitive. It fails in the direction that
-- looks like a typo: a member who registered with capitals cannot log in, and
-- nothing reports why. `citext` operators are ordinary functions rather than
-- built-ins, which is also why `bootstrap_roles.sql` has to GRANT EXECUTE on
-- them explicitly; both facts about this comparison are the same fact.
--
-- The status comes back with the hash because the two decisions are made
-- together. 12.2 says no state ever prevents a member from seeing their own
-- records, and a frozen member is still a member who can log in; a
-- `pending_verification` member is not. Returning the row and letting the caller
-- decide keeps that judgement in one place.
--
-- It returns nothing for an unknown address rather than raising, so the caller
-- cannot tell "no such member" from "no credential row" -- and the API burns an
-- equivalent Argon2id verification in both cases, so the timing does not tell it
-- either.
CREATE OR REPLACE FUNCTION app.verify_login_credential(p_email text)
RETURNS TABLE (user_id uuid, argon2_hash text, status public.user_status, is_email_verified boolean)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = app, public
AS $fn$
BEGIN
  RETURN QUERY
    SELECT c.user_id, c.argon2_hash, u.status, u.is_email_verified
      FROM public.user_credentials c
      JOIN public.users u ON u.id = c.user_id
     WHERE u.email = p_email::citext
       AND u.deleted_at IS NULL;
END;
$fn$;

COMMENT ON FUNCTION app.verify_login_credential(text) IS
  'Returns the Argon2id hash and account state for one email address, or no rows. '
  'SECURITY DEFINER because user_credentials has no SELECT policy for any '
  'application role and Argon2id cannot be verified in the database. Returns no '
  'rows rather than raising, so the caller cannot distinguish an unknown address '
  'from a missing credential.';

-- Rotating a refresh token, and detecting a reused one.
--
-- The three outcomes are `rotated`, `reused` and `unknown`, and the last one is
-- deliberately the same answer for a token that was never issued and one that
-- looks forged. `reused` is not distinguishable to the caller either -- both get
-- a 401 and both should -- but the function acts on it before returning, because
-- the member has to be protected whether or not the person holding the token
-- knows what they did.
--
-- Single use is `FOR UPDATE`, for the reason 098 gives: two concurrent refreshes
-- carrying one token must produce one winner, and the loser must get the same
-- empty result as a forgery rather than a second token. READ COMMITTED
-- re-evaluates the predicate against the committed row version, so the second
-- transaction matches nothing.
--
-- Expiry is checked here rather than in the API for the same reason the email
-- token's is: an unauthenticated endpoint should not have two places that decide
-- whether a bearer secret is still good.
CREATE OR REPLACE FUNCTION app.claim_refresh_token(
  p_token_hash       bytea,
  p_replacement_hash bytea,
  p_now              timestamptz,
  p_replacement_expiry timestamptz
)
RETURNS TABLE (user_id uuid, session_id uuid, outcome text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = app, public
AS $fn$
DECLARE
  v_session_id uuid;
  v_user_id    uuid;
  v_expires    timestamptz;
  v_created    timestamptz;
  v_last_seen  timestamptz;
  v_revoked_at timestamptz;
  v_deleted_at timestamptz;
  v_reason     text;
BEGIN
  -- 12.4.3: a family is a session, so a rotated token is evidence about the
  -- session it belonged to. Looked up *without* a `revoked_at IS NULL` filter, so
  -- that a revoked session whose token comes back is still found rather than
  -- looking like a forgery. It is then refused, just below, by an explicit check
  -- rather than by the filter.
  --
  -- `FOR UPDATE` is what makes single use true, and the predicate not carrying
  -- `revoked_at IS NULL` is the same statement seen from the other side: the
  -- second transaction to arrive re-evaluates this against the row the first one
  -- committed -- a row whose `refresh_token_hash` is now the successor -- matches
  -- nothing, and falls through to the spent-token ledger below, which is the
  -- correct answer for a token that has already been rotated.
  --
  -- Without the lock both transactions read the same live row and both issue a
  -- successor, so one refresh token becomes two. The unique index on
  -- `session_rotated_tokens.token_hash` would catch the loser, but as an
  -- unhandled unique violation -- a 500 rather than the 401 the caller should get,
  -- and a rolling one is a worse way to learn that two devices are using the same
  -- lineage than a log line that says so.
  -- `revoked_at` and `deleted_at` are selected as well as the timestamps, and
  -- they are checked below. The reason is not tidiness: it is that 12.4.2's
  -- theft response *revokes every session the member holds*, and this row is one
  -- of them. Without the check, the attacker who triggered the detection is
  -- holding the newest token in the lineage -- the successor their own rotation
  -- produced -- and it would still be accepted afterwards, because the lookup
  -- below matches on the token hash alone and never asks whether the session is
  -- still alive. Detection would then close every door except the one the
  -- attacker is standing in. The API test that found this asserts exactly that:
  -- the attacker's successor must also be refused.
  SELECT s.id, s.user_id, s.refresh_expires_at, s.created_at, s.last_active_at,
         s.revoked_at, s.deleted_at
    INTO v_session_id, v_user_id, v_expires, v_created, v_last_seen,
         v_revoked_at, v_deleted_at
    FROM public.sessions s
   WHERE s.refresh_token_hash = p_token_hash
     FOR UPDATE;

  IF NOT FOUND THEN
    -- Either never issued, or spent and rotated out. Check the spent ledger: a
    -- token in there is a copied lineage, which is a security event and not a
    -- failed guess.
    SELECT r.user_id, r.session_id
      INTO v_user_id, v_session_id
      FROM public.session_rotated_tokens r
     WHERE r.token_hash = p_token_hash;

    IF FOUND THEN
      -- The entire lineage goes, and so does everything else the member holds.
      -- 12.4.2 asks for both, and the second half is the one that limits the
      -- damage: an attacker with one stolen token would otherwise keep whatever
      -- else they had taken.
      --
      -- Aliased, and not because of style. `RETURNS TABLE (user_id uuid, ...)`
      -- makes `user_id` an OUT *parameter* as well as the name of a column on
      -- `sessions`, and an unqualified reference to a name that is both is
      -- ambiguous -- plpgsql raises rather than guessing. The table alias makes
      -- it a column reference, which is what it is.
      UPDATE public.sessions AS s
         SET revoked_at = p_now,
             revoked_reason = 'refresh_token_reuse'
       WHERE s.user_id = v_user_id
         AND s.revoked_at IS NULL;

      -- Recorded here rather than by a trigger on `sessions`, for a reason that
      -- is about the audit trail rather than about security. A trigger would fire
      -- on every rotation, because `last_active_at` moves on each refresh, and
      -- `app.audit_row()` correctly discards an UPDATE that changed nothing --
      -- so a trigger here would either be silent about reuse or bury it under
      -- refresh noise. The cost of a noisy audit trail is that nobody reads it.
      INSERT INTO public.audit_logs
        (actor_user_id, actor_type, action, subject_type, subject_id, after_state)
      VALUES
        (NULL, 'system', 'session.refresh_token_reuse', 'session', v_session_id,
         jsonb_build_object(
           'event', 'refresh_token_reuse',
           'user_id', v_user_id,
           'detected_at', p_now
         ));

      RETURN QUERY SELECT v_user_id, v_session_id, 'reused';
      RETURN;
    END IF;

    -- Never issued. Same answer as a spent token, to the caller.
    RETURN;
  END IF;

  -- The session this token belongs to is already closed. Refuse, and say nothing
  -- else.
  --
  -- The temptation is to treat this as theft, because a live token for a revoked
  -- session is anomalous. It is not, and calling it theft would be actively
  -- harmful. Three ordinary paths produce it: the member signed out and a stale
  -- client refreshed afterwards; the session was evicted by the five-session cap;
  -- the session was replaced by a later login on the same device. In all three
  -- the member is the victim of a slow client, and revoking *every* session they
  -- hold -- plus an audit row naming them as the source of a breach -- would
  -- punish a legitimate member for a timer.
  --
  -- The real theft case, the attacker's successor after a detection, arrives
  -- here too, and is refused by the same line. That is the point: the token stops
  -- working, which is what protects the member, and no false accusation is
  -- recorded on the way.
  IF v_revoked_at IS NOT NULL OR v_deleted_at IS NOT NULL THEN
    RETURN;
  END IF;

  -- Idle and absolute timeouts, 12.4.3. Idle is measured from `last_active_at`,
  -- absolute from `created_at`, and they are different rules: a member who uses
  -- the app every day still loses the session at 90 days, and a member who
  -- disappears for a fortnight loses it at 14 without the absolute clock running.
  IF v_expires IS NULL OR v_expires <= p_now THEN
    v_reason := 'refresh_expired';
  ELSIF v_last_seen IS NOT NULL AND v_last_seen <= p_now - interval '14 days' THEN
    v_reason := 'idle_timeout';
  ELSIF v_created <= p_now - interval '90 days' THEN
    v_reason := 'absolute_timeout';
  END IF;

  IF v_reason IS NOT NULL THEN
    UPDATE public.sessions
       SET revoked_at = p_now,
           revoked_reason = v_reason
     WHERE id = v_session_id;
    RETURN QUERY SELECT v_user_id, v_session_id, 'unknown';
    RETURN;
  END IF;

  -- The live token becomes evidence, and the replacement becomes live. Both in
  -- this statement pair, inside the transaction the caller's `FOR UPDATE` is
  -- holding, so there is no window in which the old token is neither live nor
  -- recorded as spent.
  INSERT INTO public.session_rotated_tokens
    (session_id, user_id, token_hash, rotated_at, expires_at)
  VALUES
    (v_session_id, v_user_id, p_token_hash, p_now, v_expires);

  UPDATE public.sessions
     SET refresh_token_hash = p_replacement_hash,
         refresh_expires_at = p_replacement_expiry,
         last_active_at = p_now
   WHERE id = v_session_id;

  RETURN QUERY SELECT v_user_id, v_session_id, 'rotated';
END;
$fn$;

COMMENT ON FUNCTION app.claim_refresh_token(bytea, bytea, timestamptz, timestamptz) IS
  'Rotates a refresh token, or detects that the presented one was already used. '
  'Returns rotated, reused, or no rows. A reused token revokes every session the '
  'member holds and records the event in audit_logs before returning, so the '
  'member is protected whether or not whoever presented the token knows what they '
  'did. The caller cannot distinguish reused from unknown: both are a 401.';

-- `app.verify_login_credential` reads `user_credentials` as its owner, and
-- `user_credentials` has FORCE ROW LEVEL SECURITY, so FORCE applies to the owner
-- exactly as it does to every other role. Without this policy the function finds
-- no rows for any address and every login reports a bad password.
--
-- Scoped to `ajo_migrator` and to this one table, as 101's is. `ajo_app` still
-- has no SELECT on `user_credentials` and still cannot read a hash back out
-- through any query it writes itself; the only way a hash reaches the API is this
-- function, and only for an address the caller is already answering a login for.
CREATE POLICY user_credentials_select_by_migrator
  ON public.user_credentials
  FOR SELECT
  TO ajo_migrator
  USING (true);

COMMENT ON POLICY user_credentials_select_by_migrator
  ON public.user_credentials IS
  'Lets app.verify_login_credential read the hash it must hand to the Argon2id '
  'verifier. Required because user_credentials has FORCE ROW LEVEL SECURITY and '
  'no SELECT policy for the function''s owner. Invisible to every application '
  'role.';

-- And the same grant on `users`, which is the second table that function reads
-- and the one that is easier to forget. `users` has FORCE ROW LEVEL SECURITY and
-- its only SELECT policy is `users_select_self_or_staff`, which needs an identity
-- -- and there is none yet, because a member who is logging in has not proved
-- anything at this point in the flow.
--
-- The failure mode here is worse than a missing row. `app.verify_login_credential`
-- is a SELECT with no rows, so the caller falls through to "no such member",
-- burns a verification, and answers a correct password with the same 401 it
-- gives a wrong one: every login on the platform fails, and the only symptom is
-- that the error is indistinguishable from a typo in the email. That is 101's
-- bug verbatim, in a function whose whole purpose is to make a wrong answer
-- impossible to act on, so it is pinned by a migration case as well as here.
--
-- Scoped to `ajo_migrator` on this one table, as 101's is. `ajo_app` keeps
-- `users_select_self_or_staff`, so an authenticated session still reads exactly
-- one user row and this changes nothing an application role can see.
CREATE POLICY users_select_by_migrator
  ON public.users
  FOR SELECT
  TO ajo_migrator
  USING (true);

COMMENT ON POLICY users_select_by_migrator
  ON public.users IS
  'Lets app.verify_login_credential read the status and verification flag it has '
  'to return with the credential. Required for the same reason as '
  'user_credentials_select_by_migrator: FORCE ROW LEVEL SECURITY with no policy '
  'for the function''s owner, and no identity to satisfy the self-only one. '
  'Invisible to every application role, which keeps users_select_self_or_staff.';
