# Testing conventions

## Layout

Tests live under `tests/`, never beside the source module they exercise,
and never as doctests inside a source module. Naming mirrors the package:
`tests/test_journal_entry.py` covers `ledgerkit/journal/entry.py`,
`tests/test_cli_accounts.py` covers the `accounts` CLI command, and so on.

## Fixtures

Two shared fixtures live in `tests/conftest.py`:

- `fixed_clock` — a `FixedClock` pinned to a fixed instant, for tests that
  need a `Clock` but don't care which instant.
- `migrated_conn` — an in-memory SQLite connection with every migration
  already applied, for any test that needs a working database without the
  overhead of a real file.
- `cli_db` — a file-backed, migrated database seeded with a checking and
  an equity account, for CLI tests that exercise `ledgerkit.cli.main.main`
  end to end.

Module-specific fixtures (a small chart of accounts, a couple of posted
entries) live at the top of the test file that needs them rather than in
`conftest.py`, unless more than one test module needs the exact same
setup.

## What's asserted

Tests assert through public APIs and observable output — a repository's
return value, a query result, what a CLI command printed to stdout —
never against private helpers or internal representations. A test should
keep passing if the implementation changes shape but the observable
behavior doesn't.

## Determinism

Every test that touches time uses `FixedClock`, never `SystemClock`.
Every test that touches randomness — there shouldn't be any, since
ledgerkit doesn't use unseeded randomness anywhere — would need to seed
it explicitly. Tests never depend on dict or set iteration order for
anything observable; where the library itself sorts before returning
data (account lists, rendered reports), the test can assert on exact
order, and where it doesn't, the test sorts before comparing.

## Running the suite

```bash
pytest              # the whole suite
pytest -q           # quieter output
pytest tests/test_money.py     # one file
pytest -k "allocate"           # anything matching a keyword
ruff check .         # lint
mypy                 # type check
```

The full suite is expected to be green, in full, before every commit —
see `CLAUDE.md`. It's also expected to produce byte-identical output and
the same collected test ids across repeated runs; if a test ever needs
`sleep()` or depends on real wall-clock time to pass, that's a bug in the
test, not something to work around.
