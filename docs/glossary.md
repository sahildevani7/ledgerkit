# Glossary

Terms as ledgerkit uses them — some of this is standard bookkeeping
vocabulary, some is specific to how this codebase models it.

**Account** — A named bucket in the chart of accounts, typed as asset,
liability, equity, income, or expense. See `ledgerkit.accounts.model.Account`.

**Normal balance** — Which side (debit or credit) an *increase* to an
account posts to. Assets and expenses have a debit normal balance;
liabilities, equity, and income have a credit normal balance. Determined
entirely by `AccountType`, never overridden per account.

**Journal entry** — A balanced group of lines posted on a single date. An
entry is either fully valid (its lines sum to zero) or it doesn't exist —
there's no "draft" or "unposted" state.

**Line** — One side of a journal entry: an account and a signed amount.
Positive is a debit, negative is a credit — see
[architecture-decisions.md](architecture-decisions.md) for why a signed
amount is used instead of separate debit/credit columns.

**Posting** — The act of writing a journal entry (or a batch of them) to
storage, via `ledgerkit.journal.posting.post` / `post_batch`. Always
atomic: a batch either posts completely or leaves no trace.

**Trial balance** — Every account's balance as of a given date, split
into debit and credit columns. Always ties out (total debits equal total
credits) as a direct consequence of every posted entry balancing
individually.

**Chart of accounts** — The full set of accounts and their parent/child
hierarchy. See `ledgerkit.accounts.tree.ChartOfAccounts`.

**Subtree balance** — The combined balance of an account and every
account beneath it in the hierarchy — what `balance --include-subaccounts`
computes.

**Import batch** — One CSV file's worth of imported transactions, tagged
with a single `import_batches` row for provenance (which account, which
source file, how many rows).

**As-of date** — A date passed to a balance or trial balance query that
restricts the result to activity on or before that date. Omitting it
means "across all posted activity, ever."

**Renderer** — Something that turns a query result (a trial balance, an
account's activity) into a display string. One implementation ships
today: `ledgerkit.reporting.text.TextRenderer`.

**Dialect** — A specific statement file format an importer knows how to
parse. One ships today: `generic_csv`.

**Unit of work** — The transaction boundary around a block of repository
calls: commit on success, roll back on any exception. See
`ledgerkit.storage.unit_of_work.UnitOfWork`.

**Migration** — A single, numbered, one-time schema change. Migrations
are never edited after they ship; a later change to the same table is a
new migration.
