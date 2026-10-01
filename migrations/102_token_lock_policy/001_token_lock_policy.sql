-- Letting the migrator lock the verification token row.
--
-- `FOR UPDATE` applies a table's UPDATE policies, not only its SELECT policies,
-- so `app.claim_email_verification_token` needed both. Migration 101 gave the
-- migrator SELECT, and the function's `SELECT ... FOR UPDATE` still matched
-- nothing: there is an `email_verification_tokens_update_own` policy, but it
-- defines only a `WITH CHECK` clause, which governs rows being written and not
-- rows being read. A policy with no `USING` clause silently means "no rows are
-- visible for this command", so the lock saw an empty table.
--
-- This is the same class of mistake as the missing SELECT policy: a permissive
-- command was never granted to the role that needs it, and the function's
-- zero-row return is indistinguishable from a forged token, so the failure read
-- as a security property rather than as a missing grant.
--
-- The policy is scoped the same way 101's is: to `ajo_migrator`, on this one
-- table. Application roles keep their own-row UPDATE `WITH CHECK`, so a member
-- can still only modify their own token, and the `consumed_at` write inside the
-- function stays constrained by that check.
CREATE POLICY email_verification_tokens_update_by_migrator
  ON public.email_verification_tokens
  FOR UPDATE
  TO ajo_migrator
  USING (true);

COMMENT ON POLICY email_verification_tokens_update_by_migrator
  ON public.email_verification_tokens IS
  'Lets app.claim_email_verification_token take the row lock that makes claiming '
  'atomic. FOR UPDATE applies UPDATE policies, and the pre-existing '
  'email_verification_tokens_update_own has no USING clause, so it exposed zero '
  'rows to the function''s owner.';
