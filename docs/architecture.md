# Architecture

ledgerkit is a library first, CLI second. Every command in `ledgerkit.cli`
is a thin wrapper around calls any other Python application could make
directly.

## Layers

```
cli          argparse commands; the only place SystemClock is constructed
importers    parse raw statement text into ImportedTransaction, nothing else
journal      the double-entry invariant, and posting it atomically
ledger       read-only queries over what's been posted
accounts     the chart of accounts and its hierarchy
reporting    turns a query result into a display string
storage      SQLite connection, schema migrations, transaction boundary
money/currency/dates/ids/clock/errors/config   shared domain primitives
```

Dependencies point downward: `cli` depends on everything above it, but
`money` depends on nothing else in the package. `journal` and `ledger` both
depend on `accounts` (to validate account references) and `storage`, but
not on each other beyond that.

## The double-entry invariant

A `Line` carries a signed `Money` amount: positive is a debit, negative is
a credit. A `JournalEntry` is only constructible if its lines sum to
exactly zero — there's no code path that persists an entry without going
through that check, because the check lives in `JournalEntry.__post_init__`,
not in a separate validation step someone could forget to call.

## Atomicity

`journal.posting.post_batch` wraps every entry it posts in one
`storage.unit_of_work.UnitOfWork`. If any line in any entry references an
account that doesn't exist, the whole batch — including entries already
written earlier in the same call — rolls back. Nothing partial is ever
observable in storage.

## Extension seams

A few places are one-implementation-deep by design, not by oversight:

- `importers.registry` — one CSV dialect registered today.
- `reporting.renderer` — one text renderer.
- `currency` — one currency (CAD) registered.

Each is a real `Protocol` with a real implementation behind it, wired
through a small registry or direct construction. Adding a second
implementation means registering it, not restructuring anything.

## Where read and write paths diverge

Writes go through repositories (`AccountRepository`, `JournalRepository`)
and, for anything multi-row, `UnitOfWork`. Reads mostly bypass the
repositories and query the tables directly —
`ledger.queries.account_balance` and `all_account_balances` issue their
own SQL rather than reconstructing full `JournalEntry` objects for every
line just to sum them. This is a deliberate asymmetry: a repository's job
is to turn rows into domain objects faithfully, which is the right cost
to pay when something is being modified, but wasted work for an
aggregate that never needs the intermediate objects at all.

## What a new query function looks like

Every function in `ledger.queries` follows the same shape: validate the
account exists (via `AccountRepository.get`, which raises `NotFoundError`
on its own), build a parameterized SQL query with optional date bounds,
and map rows back into `Money` through `get_currency` rather than
assuming CAD. A new aggregate — `subtree_balance` is the most recent
example — follows that shape rather than introducing a different query
style.
