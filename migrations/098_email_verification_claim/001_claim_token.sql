-- Spending an email verification token.
--
-- This is a separate migration from 097 on purpose. 097 was already applied to
-- the live database before this function was written, and the migration runner
-- correctly refuses to let an applied migration be edited -- the checksum guard
-- is what stops a migration meaning one thing in development and another in
-- production. So the function that 097's table was missing lives here, in a
-- migration that can be applied exactly once.
--
-- Before an account is verified there is no session, so the token is the *only*
-- credential the caller holds, and it has to be checked without one.
-- `email_verification_tokens` has no SELECT policy for the application role, so
-- the check cannot be a query the API writes -- hence a function, running as the
-- table owner, that finds the token and marks it used in the same transaction.
--
-- Single use is enforced here rather than in application code, and specifically
-- by `FOR UPDATE` rather than by a read followed by an update. Two concurrent
-- requests carrying one token both pass a bare SELECT; both then try to write
-- `consumed_at`, and the second blocks on the row lock until the first commits,
-- at which point READ COMMITTED re-evaluates its `consumed_at IS NULL` predicate
-- against the new row version, matches nothing, and returns no row. So exactly
-- one caller wins, and the loser gets the same empty result as a forged token.
-- That is the property the whole check is for, and it is why this is not a
-- SELECT the API can be trusted to write.
--
-- Every failure -- unknown hash, already consumed, expired -- returns zero rows.
-- The API turns all of them into one indistinguishable error, because the
-- endpoint is unauthenticated and any difference between the cases tells an
-- attacker holding a stolen token whether it is worth continuing to guess.
CREATE OR REPLACE FUNCTION app.claim_email_verification_token(
  p_token_hash bytea,
  p_now        timestamptz
)
RETURNS TABLE (user_id uuid, already_verified boolean)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = app, public
AS $fn$
DECLARE
  v_user_id  uuid;
  v_verified boolean;
BEGIN
  SELECT t.user_id
    INTO v_user_id
    FROM public.email_verification_tokens t
   WHERE t.token_hash = p_token_hash
     AND t.consumed_at IS NULL
     AND t.expires_at > p_now
     FOR UPDATE;

  IF NOT FOUND THEN
    -- Zero rows, not an exception. The caller cannot tell this apart from any
    -- other rejection, which is the intent.
    RETURN;
  END IF;

  UPDATE public.email_verification_tokens
     SET consumed_at = p_now
   WHERE token_hash = p_token_hash
     AND consumed_at IS NULL;

  SELECT u.is_email_verified
    INTO v_verified
    FROM public.users u
   WHERE u.id = v_user_id;

  RETURN QUERY SELECT v_user_id, COALESCE(v_verified, false);
END;
$fn$;

COMMENT ON FUNCTION app.claim_email_verification_token(bytea, timestamptz) IS
  'Atomically claims an unused, unexpired email verification token and marks it '
  'consumed. FOR UPDATE makes it single-use under concurrency. Returns no row '
  'for every rejection reason so the caller can answer identically in each case.';
