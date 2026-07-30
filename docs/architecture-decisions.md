# Architecture decisions

Short records of choices that weren't obvious, kept together so the
reasoning doesn't have to be reconstructed from commit history later.

## Signed amounts instead of separate debit/credit columns

A journal line stores one signed `Money` — positive for a debit, negative
for a credit — rather than two columns (`debit_amount`, `credit_amount`)
where exactly one is non-zero. Both represent the same information, but
the signed form makes the double-entry invariant a one-line check
(`sum(line.amount for line in lines) == 0`) instead of a check that has
to reason about which column is populated on each row. It also means
`account_balance` is a single `SUM`, not a `SUM(debit) - SUM(credit)`
across two columns.

The cost is that "debit" and "credit" aren't nouns in the schema — they're
derived from a sign, via `Line.is_debit` / `Line.is_credit`. That's a
deliberate trade: the invariant that matters (balance) is cheap to check;
the display concept (which column to print something in) is computed
only where it's actually needed, in `TrialBalance` and the text renderer.

## Amounts stored as text, not a numeric column

SQLite has no fixed-precision decimal column type — `REAL` is a
double-precision float, exactly the representation `Money` exists to
avoid. Storing the canonical decimal string (`"10.00"`, not `"1e1"` or
`"10"`) and parsing it back through `Money`'s own constructor means the
same precision and rounding rules apply on the way out as on the way in,
with no separate serialization format to keep in sync.

## One `AccountRepository.chart()` call per hierarchy operation

`reparent()` rebuilds a full `ChartOfAccounts` from the database on every
call, rather than keeping a cached tree that's incrementally updated. For
the data volumes this library is built for (a personal or small
organization's chart of accounts — tens to low hundreds of accounts, not
millions), the cost of a full table scan and rebuild is negligible, and
it eliminates an entire category of cache-invalidation bugs. If the chart
of accounts ever needed to scale past that, the fix would be a smarter
`ChartOfAccounts` construction, not a wider API.

## The CLI is the only place that constructs concrete implementations

`SystemClock()`, `TextRenderer()`, and `GenericCsvImporter()` (indirectly,
through the registry) are each constructed in exactly one place: the CLI
entry point, or the registry's own module-level `register()` call. Every
function below that takes the corresponding protocol
(`Clock`, `Renderer`, `Importer`) as a parameter. This is what makes the
seams in `reporting/`, `importers/`, and `clock.py` real rather than
theoretical — swapping an implementation is a constructor call at one
call site, not a search-and-replace.

## Why `post_batch` re-validates every account on every call

`post_batch` calls `AccountRepository.get()` for every line in every
entry, even though the caller may have already looked the account up
once (the CLI's `import` and `post` commands both do). This is
deliberate redundancy: `post_batch` is the boundary that guarantees
atomicity, and it shouldn't trust that whatever called it validated
correctly. The cost is a handful of extra primary-key lookups per batch,
which is immaterial next to the cost of the inserts themselves.
