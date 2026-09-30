-- Migration ledger.
--
-- Applied migrations, with the checksum of the file that was applied. The
-- checksum is the point: a migration that is edited after it has been applied
-- will not match its recorded checksum, and the runner refuses to continue
-- rather than leaving a database whose shape no longer matches the repository.
--
-- The table is in `app` rather than `public` because it is not part of the
-- product's data model and nothing outside a migration runner should read it.
--
-- scripts/migrate.py applies this file before any other migration, which is why
-- it creates the `app` schema itself rather than assuming that
-- migrations/000_foundation has already run.
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.schema_migrations (
  version     text        PRIMARY KEY,
  checksum    text        NOT NULL,
  applied_at  timestamptz NOT NULL DEFAULT now(),
  duration_ms integer     NOT NULL
);

COMMENT ON TABLE app.schema_migrations IS
  'Applied migrations and the sha256 of the file applied, so an edited migration '
  'is detected rather than silently divergent.';
COMMENT ON COLUMN app.schema_migrations.version IS
  'The migration file name, e.g. 000_foundation/001_adopt.sql.';
COMMENT ON COLUMN app.schema_migrations.checksum IS
  'Full sha256 of the file contents, hex encoded.';
COMMENT ON COLUMN app.schema_migrations.duration_ms IS
  'How long the migration took, so a regression is visible in the log.';
