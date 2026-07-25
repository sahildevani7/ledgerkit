# ledgerkit

A double-entry accounting engine with a command-line interface.

`ledgerkit` ingests bank statement exports, posts journal entries under a
strictly enforced double-entry invariant, persists everything to SQLite, and
produces balance and trial balance reports. It's built as a small library
(`ledgerkit`) plus a `ledgerkit` CLI on top of it.

## Why

Most personal-finance tooling either hides the accounting model behind a
polished UI or gets the model wrong (floats for money, implicit rounding,
no real double-entry invariant). This is the opposite: a plain library with
an explicit domain model, so the accounting is correct first and the
interface is secondary.

## Features

- **Double-entry posting.** Every journal entry must balance — total debits
  equal total credits, enforced before anything touches storage.
- **Chart of accounts.** Typed account kinds (asset, liability, equity,
  income, expense) with correct normal-balance sign handling, and a tree
  structure that supports re-parenting.
- **CSV import.** Bank statement rows come in through a small importer
  protocol; one dialect ships today.
- **Reporting.** Balances, as-of-date queries, account activity, and a text
  trial balance report.
- **SQLite storage** with a real migration runner and a unit-of-work
  transaction boundary — every multi-entry operation is atomic.

## Installation

```bash
pip install -e ".[dev]"
```

Requires Python 3.12+.

## Quick start

The database file is created and migrated automatically the first time any
command touches it — there's no separate init step.

```bash
# set up a chart of accounts
ledgerkit --db ledger.db accounts create 1000 Checking asset
ledgerkit --db ledger.db accounts create 3000 "Opening Balance" equity

# import a CSV bank statement
ledgerkit --db ledger.db import statement.csv --account 1000 --contra-account 3000

# post a manual journal entry
ledgerkit --db ledger.db post \
  --debit 1000:100.00 \
  --credit 3000:100.00 \
  --memo "opening balance"

# check a balance
ledgerkit --db ledger.db balance 1000

# render a trial balance
ledgerkit --db ledger.db report trial-balance
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy
```

## Project layout

```
src/ledgerkit/
├── money.py, currency.py, dates.py, ids.py, clock.py, errors.py, config.py
├── accounts/       chart of accounts and account model
├── journal/        journal entries and the posting engine
├── ledger/         balance and trial balance queries
├── storage/        SQLite engine, schema, migrations, unit of work
├── importers/       statement import protocol + CSV dialect
├── reporting/       report rendering protocol + text renderer
└── cli/            command-line entry points
```

Tests live under `tests/`, mirroring the package layout.

## Design notes

- Money is always `Decimal`-backed; there is no floating-point arithmetic
  anywhere near an amount.
- The base currency is CAD. Multi-currency support is not implemented yet.
- All dates and times flow through an injected `Clock`, so behavior is
  reproducible in tests and never depends on wall-clock time.

## License

MIT
