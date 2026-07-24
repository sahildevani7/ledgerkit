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
