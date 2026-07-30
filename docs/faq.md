# FAQ

## Why CAD only?

`Currency` and `Money` are both currency-aware already — every `Money`
carries a `Currency`, and combining two different currencies raises
`ValidationError` rather than silently doing the wrong thing. Only CAD is
registered, via `ledgerkit.currency.get_currency` — see
[money-and-currency.md](money-and-currency.md) for how that registry
works.

## Why doesn't the CLI have an `init` command?

There's nothing to separately initialize. Every command opens `--db`,
applies any outstanding migrations, and proceeds — a brand-new path and
an existing one are handled identically. Splitting that into an explicit
`init` step would just be one more thing a new user has to remember to
run first.

## Can I delete a posted journal entry?

Not through anything ledgerkit ships. `JournalRepository` has no
`delete` method, and there's no CLI command for it — posting is the only
write path into the journal tables.

## Why is `Money` immutable?

Two `Money` values are compared and combined constantly — every posting,
every balance calculation — and immutability means neither side of a
`+` or a comparison has to worry about the other mutating underneath it.
It also makes `Money` hashable, so it can be used as a dict value or
inside another frozen dataclass (as it is, throughout `Line`,
`JournalEntry`, and `TrialBalanceRow`) without extra ceremony.

## Why SQLite instead of Postgres or another server database?

ledgerkit is a single-user, single-process library — there's no
deployment where multiple processes would contend for the same database
at once. SQLite is zero-configuration, ships with Python, and is
completely adequate for that shape of workload. Nothing about the
architecture (the `Engine`/`UnitOfWork` split, repositories talking to a
`sqlite3.Connection`) assumes SQLite specifically at the type level, but
no other backend is implemented or planned.

## What happens if I post an entry dated in the past, after later entries already exist?

Nothing special — `entry_date` has no relationship to insertion order,
and queries that filter by date (`account_balance(..., as_of=...)`,
`build_trial_balance(..., as_of=...)`) work off the dates on the rows,
not the order they were inserted in. There's currently no concept of a
"closed" period that would reject a late entry; every date is open to
posting.

## Why does `Account` keep its `id` as the last field instead of the first?

`Account(code, name, type, parent_id, is_active, id)` puts `id` last so
that constructing a new, not-yet-persisted account reads naturally —
`Account(code="1000", name="Checking", type=AccountType.ASSET)` — without
having to pass `id=None` explicitly or skip positional arguments. Every
other entity (`JournalEntry`, `Line`) follows the same convention: the
fields a caller provides come first, the field the repository assigns
comes last, defaulting to `None`.

## Does ledgerkit validate that an account code follows a particular numbering scheme?

No. `Account.code` just has to be non-empty; there's no enforced
numbering convention (1000s for assets, 5000s for expenses, or anything
else). Plenty of real charts of accounts follow a convention like that,
but it's a convention the *user* of the library chooses and follows, not
a rule ledgerkit enforces — codes are opaque strings as far as the model
is concerned.

## Why is the demo script under `scripts/` instead of `src/ledgerkit/`?

`scripts/seed_demo_ledger.py` is a developer convenience, not something
`ledgerkit` (the package) imports or the CLI wires up — running it
requires the library to already be installed, the same way a user's own
script would. Keeping it outside `src/ledgerkit/` makes that boundary
explicit: nothing under `src/` depends on it, and it could be deleted
without affecting the installed package at all.
