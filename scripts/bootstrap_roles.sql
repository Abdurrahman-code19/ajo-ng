-- Three roles, never one. §9.2.
--
-- This is bootstrap, not migration, and the distinction is not fussiness.
-- A role is cluster-wide state; a migration is per-database and checksum-tracked.
-- A database restored from a dump on a cluster that lacks these roles would have
-- grants referring to roles that do not exist, and would fail to restore or
-- restore into a weaker shape than it was dumped from. So the roles are created
-- here, idempotently, and the migration ledger never records them.
--
-- It is tempting to put this in a migration because CREATE ROLE is in fact
-- transactional and would work there. The reason not to is the one above: a
-- restored database must be able to come up before anyone has run a migration.
--
-- Safe to run repeatedly. Every statement is conditional on current state.
--
--   psql -d <name> -f scripts/bootstrap_roles.sql
--
-- The three roles are NOLOGIN. They are not accounts; they are bundles of
-- privilege that a real login role is granted. No human or process logs in as
-- any of them.

\set ON_ERROR_STOP on

-- ---------------------------------------------------------------------------
-- The roles
-- ---------------------------------------------------------------------------
-- NOBYPASSRLS on all three, explicitly, because it is the whole point. A role
-- with BYPASSRLS makes every policy in 9.6 decorative, and it is a one-word
-- change that no test would catch unless something asserted it.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ajo_migrator') THEN
    CREATE ROLE ajo_migrator NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ajo_app') THEN
    CREATE ROLE ajo_app NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ajo_analytics') THEN
    CREATE ROLE ajo_analytics NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
END
$$;

-- The CREATE above only runs for a role that does not exist yet, which meant
-- this script's own comment was true of a role it created and false of a role
-- it found. That is not a theoretical gap: while diagnosing the schema-grant
-- bug further down, a diagnostic turned BYPASSRLS on to see whether the
-- SECURITY DEFINER functions depended on it, and the reset afterwards did not
-- hold. The role is cluster-wide, so that silently unbound every policy in
-- every database on the cluster -- including the live one -- while this script
-- kept reporting success, because it had nothing left to assert.
--
-- So the attributes are stated unconditionally, not only at creation. This is
-- what makes the script self-healing rather than merely idempotent: it restores
-- the intended privilege of a role that already exists, which is the one
-- situation where a "safe to run repeatedly" script has to be safe against
-- having been run on a damaged cluster.
ALTER ROLE ajo_migrator  NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION;
ALTER ROLE ajo_app       NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION;
ALTER ROLE ajo_analytics NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION;

-- ---------------------------------------------------------------------------
-- Ownership
-- ---------------------------------------------------------------------------
-- ajo_migrator owns the schema, not the table owner per se. Ownership is what
-- makes ajo_app and ajo_analytics non-owners, and a non-owner is the only kind
-- of role that a row-level security policy applies to.
--
-- Ownership is transferred in full, including the SECURITY DEFINER functions in
-- app. Their owner is the privilege boundary: they execute as whoever owns them,
-- so leaving them owned by a superuser would let any caller of ajo_app read
-- through them without restriction. See the WARNING callout in 9.6.
--
-- Note what is NOT transferred: the roles themselves. Ownership of a table does
-- not confer the right to change the table's owner or to create other tables.

ALTER SCHEMA app OWNER TO ajo_migrator;

-- Read this one twice, because getting it wrong is invisible and total.
--
-- This database has no USAGE on schema public for PUBLIC -- correctly, it is a
-- closed schema. A superuser ignores that, which is why nothing has ever
-- noticed. But the moment ownership of the tables moves off the superuser onto
-- ajo_migrator, ajo_migrator becomes an ordinary role subject to ordinary
-- schema privileges, and the six SECURITY DEFINER functions -- which execute as
-- their owner -- stop being able to resolve the tables they read.
--
-- The symptom is not an error at bootstrap time. `app.has_platform_role()`
-- simply reports "relation role_assignments does not exist", because
-- PostgreSQL hides an object you have no USAGE to see rather than admitting it
-- exists. A role split that grants ownership but forgets the schema grant
-- therefore looks correct and is completely broken.
--
-- CREATE as well as USAGE: this is the role that applies tomorrow's migration,
-- and it cannot add a table to a schema it has no CREATE on.
GRANT USAGE, CREATE ON SCHEMA public TO ajo_migrator;

DO $$
DECLARE
  stmt text;
BEGIN
  FOR stmt IN
    SELECT format('ALTER TABLE public.%I OWNER TO ajo_migrator', c.relname)
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')

    UNION ALL

    SELECT format('ALTER SEQUENCE public.%I OWNER TO ajo_migrator', c.relname)
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind = 'S'

    UNION ALL

    SELECT format('ALTER FUNCTION public.%I(%s) OWNER TO ajo_migrator',
                  p.proname, pg_get_function_identity_arguments(p.oid))
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'

    UNION ALL

    SELECT format('ALTER FUNCTION app.%I(%s) OWNER TO ajo_migrator',
                  p.proname, pg_get_function_identity_arguments(p.oid))
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'app'
  LOOP
    EXECUTE stmt;
  END LOOP;
END
$$;

-- ---------------------------------------------------------------------------
-- Grants
-- ---------------------------------------------------------------------------
-- The grants are the point of the split, so they are stated as a matrix rather
-- than left to defaults:
--
--                 schema  DML   SELECT  EXECUTE app.*   DDL
--   ajo_migrator  own     own    own     own          yes
--   ajo_app       usage   yes    yes     yes          no
--   ajo_analytics usage   no     yes     6 of them    no
--
-- DML on public is granted to ajo_app in full, and the RLS policies then decide
-- what a given caller may actually touch. That is the intended layering: grants
-- say "this role may write to this table", policies say "this request may write
-- to this row". A table with RLS on and no policy for a given command therefore
-- denies that command, which is why an INSERT into users -- which has SELECT and
-- UPDATE policies but no INSERT policy -- is refused even for a role with full
-- DML grants. That is the correct answer, not a gap.
--
-- ajo_analytics deliberately has no EXECUTE on app.*. Those are the six
-- SECURITY DEFINER functions, and EXECUTE on them is the same as reading the
-- tables behind them; a reporting role that can call them can read anything.

GRANT USAGE ON SCHEMA public TO ajo_app, ajo_analytics;
GRANT USAGE ON SCHEMA app TO ajo_app, ajo_analytics;

-- The RLS policies in 9.6 call six app functions. Every role that is subject to
-- those policies must be able to EXECUTE them, or SELECT simply errors with
-- "permission denied for function" instead of returning the rows it is allowed
-- to see. That is not a corner case: it is what a reporting query hits on its
-- first join.
--
-- So analytics gets EXECUTE on the six policy-support functions, and no DML.
-- It can read what a member could read and nothing else. It is deliberately not
-- granted EXECUTE on current_ajo_ids(), which returns a SETOF and is a data
-- leak dressed as a predicate -- the policies that need it are the ones ajo_app
-- is the role for.

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ajo_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ajo_analytics;

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO ajo_app;

-- Functions are EXECUTE to PUBLIC by default in PostgreSQL, which means every
-- role in the cluster can call the SECURITY DEFINER set. That default is
-- withdrawn and then granted back only to the role that is supposed to have it.
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA app FROM PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO ajo_app;

-- The six functions the policies call, for analytics, by name. A blanket grant
-- would hand it the SECURITY DEFINER write-path functions (audit_row,
-- materialize_organizer_membership) and current_ajo_ids(), none of which a
-- dashboard has any business calling.
GRANT EXECUTE ON FUNCTION
  app.request_user_id(),
  app.request_actor_type(),
  app.is_platform_staff(),
  app.has_platform_role(text),
  app.is_ajo_member(uuid),
  app.shares_ajo_with(uuid)
TO ajo_analytics;

-- Same default, same reasoning, on public.
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ajo_app, ajo_analytics;

-- citext is the exception that proves the rule, and it is worth writing down.
-- Its operators are functions, so an equality test on a citext column needs
-- EXECUTE on them. Every index on users.email, and every unique constraint on
-- it, goes through citext_eq. Revoking without this grants line made a plain
-- SELECT on users fail with "permission denied for function citext_eq" for
-- both roles -- a wrong error message for what is really a missing grant.

-- A role that could create a table could create a table with a permissive
-- policy and then read through it, or shadow a function that SECURITY DEFINER
-- resolves at call time. Neither role may create in public.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- New objects inherit these, so a table added by tomorrow's migration is not
-- accidentally private to the migrator. Without this the grants above would
-- have to be remembered again each time.
ALTER DEFAULT PRIVILEGES FOR ROLE ajo_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ajo_app;
ALTER DEFAULT PRIVILEGES FOR ROLE ajo_migrator IN SCHEMA public
  GRANT SELECT ON TABLES TO ajo_analytics;
ALTER DEFAULT PRIVILEGES FOR ROLE ajo_migrator IN SCHEMA app
  GRANT EXECUTE ON FUNCTIONS TO ajo_app;

COMMENT ON SCHEMA app IS
  'Trigger and policy functions. Owned by ajo_migrator so the six SECURITY '
  'DEFINER functions in here execute with bounded privilege instead of a '
  'superuser''s.';

-- ---------------------------------------------------------------------------
-- The trigger write path
-- ---------------------------------------------------------------------------
-- This is the one policy that belongs in bootstrap rather than in a migration,
-- and the reason is worth stating because it is easy to get wrong in the other
-- direction.
--
-- `app.audit_row()` is SECURITY DEFINER, so the 18 audit triggers that use it
-- insert into `audit_logs` as the function's owner. That owner is `ajo_migrator`.
-- `audit_logs` is RLS and FORCE RLS, and FORCE applies to the owner too -- that
-- is the entire reason it exists. So with no INSERT policy, the audit insert
-- is denied.
--
-- The consequence is worth being blunt about, because it is silent. This script
-- reported success while the audit trail was broken. Every audited write -- a
-- user registering, an Ajo being created, a payment recorded -- was refused by
-- its own audit trigger, inside a transaction that rolled back, and nothing
-- printed a warning. The write looked like it would work; it did not; the only
-- evidence was that it did not.
--
-- Before the split, that same insert succeeded because the definer function
-- was owned by a superuser, and a superuser bypasses FORCE ROW LEVEL SECURITY
-- unconditionally. So the audit trail did not work; it was waived. This policy
-- is what makes it work.
--
-- It is scoped to `ajo_migrator` deliberately, and that scoping is the spec's
-- position rather than a compromise: 9.6 says nobody reads `audit_logs`, and
-- this is a write policy, not a read one, so it grants no SELECT. `ajo_migrator`
-- is NOLOGIN, so there is no way for a person or a request to use this path --
-- the only caller that can is the trigger function, which is the only writer the
-- schema defines. `ajo_app` still holds no INSERT on `audit_logs` and still
-- cannot forge an audit row, which is the property that matters.
--
-- The other five tables with RLS and no INSERT policy -- `payments`, `payouts`,
-- `ledger_transactions`, `ledger_postings`, `risk_events` -- are left without
-- one, which means they are unwritable by a non-owner. That is deliberate and
-- is argued in `migrations/096_rls_write_policies/001_self_row_inserts.sql`.
CREATE POLICY audit_logs_insert_by_trigger ON public.audit_logs
  FOR INSERT
  TO ajo_migrator
  WITH CHECK (true);
