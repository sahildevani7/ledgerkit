# Schema migrations

Migrations live in `ledgerkit.storage.migrations` as numbered modules —
`migration_001_accounts.py`, `migration_002_import_batches.py`, and so on —
each exporting a single `Migration(version, name, sql)`.

## Applying migrations

`ledgerkit.storage.migrations.runner.apply_migrations(connection, clock)`
applies every migration with a version greater than the database's current
version, in order. It's idempotent: calling it again against an
up-to-date database applies nothing and returns an empty list.

Every command in the CLI calls this before doing anything else, so a fresh
`--db` path is created and brought up to date automatically — there's no
separate init step.

## Adding a migration

1. Add `migration_00N_<name>.py` with the next version number and a short,
   descriptive migration name.
2. Register it in `runner.ALL_MIGRATIONS`.
3. Versions must be contiguous starting at 1 — the runner raises
   `StorageError` if it finds a gap, rather than silently skipping ahead.

Once a migration has shipped, it's never edited — a later change to the
same table is a new migration, not a rewrite of an old one.
