# Security notes

## No network access

Nothing in `ledgerkit` — the library, the CLI, or the test suite — makes
a network call. There's no telemetry, no update check, no remote
exchange-rate lookup. Everything it does is local: read a file, write to
a local SQLite database, print to stdout.

## What's stored, and where

Everything lives in the SQLite file passed as `--db` (or constructed
directly via `Engine`): account names and codes, journal entries, line
amounts, and import provenance (source filename, row count, timestamp).
None of that is encrypted at rest — `ledgerkit` treats the database file
the same way a spreadsheet treats its own file, and protecting it (disk
encryption, file permissions, backups) is the same responsibility a user
already has for any local financial file.

## No secrets in the codebase

There's nothing to configure that resembles a credential — no API key, no
password, no connection string beyond a local file path. `ledgerkit.toml`
and the `LEDGERKIT_*` environment variables only ever carry the flat,
non-sensitive settings in `LedgerConfig` (a database path, a fiscal year
start month, a currency code).

## Input handling

CSV statement parsing (`GenericCsvImporter`) and TOML config loading
(`load_config`) both reject malformed input outright rather than trying
to recover from it — a bad row fails the whole import, an unknown config
key fails the whole load. Neither ever executes anything from the input
file; a CSV cell or a TOML value is read as a plain string or number,
never evaluated.
