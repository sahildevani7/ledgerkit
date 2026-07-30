# CLI reference

Every command takes `--db PATH` before the subcommand name. The database
is created and migrated automatically the first time it's touched — there
is no separate init step.

```
ledgerkit --db ledger.db <command> ...
```

## `accounts`

Manage the chart of accounts.

- `accounts create CODE NAME TYPE [--parent CODE]` — create an account.
  `TYPE` is one of `asset`, `liability`, `equity`, `income`, `expense`.
- `accounts list [--include-inactive]` — list accounts, one per line, with
  their type and parent (if any).
- `accounts reparent CODE [--parent CODE]` — move an account under a new
  parent, or to the root if `--parent` is omitted.
- `accounts deactivate CODE` / `accounts activate CODE` — toggle whether an
  account is active. Deactivating doesn't delete anything; it just marks
  the account so tooling built on top of ledgerkit can choose to hide it.

## `post`

Post a manual journal entry.

```
ledgerkit --db ledger.db post \
  --debit 1000:100.00 \
  --credit 3000:100.00 \
  --entry-date 2026-07-01 \
  --memo "opening balance"
```

`--debit` and `--credit` each accept `CODE:AMOUNT` and can be repeated to
build a multi-line entry, as long as the debits and credits sum to the
same total — the entry is rejected otherwise, before anything is written.
`--entry-date` defaults to today if omitted.

## `import`

Import a CSV bank statement (see [csv-import-format.md](csv-import-format.md)
for the file format) and post it as journal entries.

```
ledgerkit --db ledger.db import statement.csv \
  --account 1000 --contra-account 3000
```

Every row becomes a two-line entry between `--account` and
`--contra-account`; the whole file posts as one atomic batch. `--dialect`
selects which registered importer parses the file (`generic_csv` is the
only one that ships today).

## `balance`

```
ledgerkit --db ledger.db balance 1000 [--as-of 2026-06-30]
```

Prints the account's signed balance as of the given date, or across all
activity if `--as-of` is omitted.

## `report`

- `report trial-balance [--as-of DATE]` — every account's balance split
  into debit and credit columns, with totals.
- `report account-activity CODE [--start DATE] [--end DATE]` — one
  account's transaction history with a running balance.

## Exit codes

`0` on success. `1` when a `LedgerError` is raised — a bad account code, an
unbalanced entry, a malformed CSV row — with the message printed to
stderr as `error: ...`. Argument-parsing failures (missing a required
flag, an unknown subcommand) use argparse's own exit code, `2`.
