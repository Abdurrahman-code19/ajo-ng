-- Letting `app.claim_email_verification_token` see the token it claims.
--
-- The function has never worked. It returned zero rows for every token, which
-- the API faithfully reported as "invalid link", so every verification failed.
--
-- Why. The table has `FORCE ROW LEVEL SECURITY`, and its only SELECT policy is
--
--   email_verification_tokens_select_own
--     USING (user_id = app.request_user_id())
--
-- `app.request_user_id()` reads a GUC, and this function runs with no identity
-- set -- there is no session, because the account being verified has never
-- logged in. So `app.request_user_id()` is NULL, the policy's predicate is NULL,
-- and the function's `SELECT ... FOR UPDATE` matches no rows. `FOUND` is false,
-- the function returns nothing, and the API cannot tell that apart from a forged
-- token. Which is exactly the indistinguishability it was written for, applied
-- to a case that was not a failure at all.
--
-- This went unnoticed because every existing test that read this table did it as
-- the superuser, which bypasses RLS. The bug only appears for a caller subject to
-- RLS, and the API is the only such caller.
--
-- The fix is a policy for `ajo_migrator`, the function's owner. `USING (true)`
-- looks broad, but the alternative is not narrower: there is no predicate
-- available that means "exactly the row whose hash the caller supplied", because
-- the hash is an argument to a function, not a value a policy can see. The table
-- is still unreadable to every application role.
CREATE POLICY email_verification_tokens_select_by_migrator
  ON public.email_verification_tokens
  FOR SELECT
  TO ajo_migrator
  USING (true);

COMMENT ON POLICY email_verification_tokens_select_by_migrator
  ON public.email_verification_tokens IS
  'Lets app.claim_email_verification_token find the row it is about to consume. '
  'Needed because that function runs with no identity -- the account has no '
  'session yet -- so the self-only policy matches nothing. Scoped to the '
  'function''s owner, and invisible to every application role.';
