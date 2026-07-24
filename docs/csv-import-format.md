# Generic CSV import format

The one shipped importer dialect (`ledgerkit.importers.generic_csv`) reads
a plain three-column CSV:

```csv
date,description,amount
2026-07-11,Coffee Shop,-4.50
2026-07-12,Paycheque,1500.00
```

## Columns

- `date` — ISO 8601, `YYYY-MM-DD`. Any other format is rejected rather than
  guessed.
- `description` — free text; becomes the posted entry's memo. Must not be
  empty after trimming whitespace.
- `amount` — a decimal string, positive for money in and negative for
  money out, relative to the account the statement belongs to. Values with
  more precision than the currency's minor unit (e.g. `1.005` for CAD) are
  rejected rather than silently rounded.

Extra columns beyond these three are ignored. Rows are otherwise processed
in file order; the row number reported in an error message counts the
header as row 1.

## What the CLI does with a parsed transaction

`ledgerkit import` turns each transaction into a two-line journal entry:
one line against the statement's `--account`, and an equal-and-opposite
line against the `--contra-account` you name explicitly — the importer
never guesses where the other side of a transaction belongs. The whole
file is posted as a single atomic batch, tagged with one import batch
record for provenance.
