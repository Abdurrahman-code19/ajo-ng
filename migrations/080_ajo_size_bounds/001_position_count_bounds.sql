-- Ajo size: 5 to 20 members, default 10, creator included.
--
-- The adopted schema carried the earlier rule, `CHECK (position_count >= 2)` on
-- `ajos_position_count_check`, which permitted a two-person "Ajo". The product
-- decision is 5 to 20: below five it is a transfer rather than a rotation, and
-- above twenty it is a group one organiser cannot realistically invite, monitor
-- and default-handle.
--
-- The column had no default at all, so an INSERT that omitted position_count
-- stored NULL and failed the old CHECK. It now defaults to 10, the working
-- example the specification uses throughout, which is a value the CHECK
-- accepts: a table whose default fails its own constraint is a bug that only
-- appears in production.
--
-- The creator is one of these positions rather than one in addition to them, so
-- a ten-member Ajo is one organiser and nine invitees. That half of the rule is
-- enforced by app.materialize_organizer_membership() and is not expressible as
-- a CHECK, because it spans `ajos` and `ajo_members` in two tables.
ALTER TABLE public.ajos
  DROP CONSTRAINT IF EXISTS ajos_position_count_check;

ALTER TABLE public.ajos
  ALTER COLUMN position_count SET DEFAULT 10;

ALTER TABLE public.ajos
  ADD CONSTRAINT ajos_position_count_within_bounds
  CHECK (position_count BETWEEN 5 AND 20);

COMMENT ON COLUMN public.ajos.position_count IS
  'Members in the Ajo, between 5 and 20, defaulting to 10. The creator occupies '
  'one of these positions: a ten-member Ajo is one organiser and nine invitees. '
  'Rounds equal members, so this is also the number of rounds.';
