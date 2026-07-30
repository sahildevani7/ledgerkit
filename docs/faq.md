# FAQ

## Why CAD only? When is multi-currency coming?

`Currency` and `Money` are both currency-aware already — every `Money`
carries a `Currency`, and combining two different currencies raises
`ValidationError` rather than silently doing the wrong thing. What's
missing is a second registered currency, exchange rates, and
revaluation, which is a meaningfully different problem (what rate applies
on what date, how rounding residue from a conversion gets absorbed) and
isn't solved by this codebase yet.

## Why doesn't the CLI have an `init` command?

There's nothing to separately initialize. Every command opens `--db`,
applies any outstanding migrations, and proceeds — a brand-new path and
an existing one are handled identically. Splitting that into an explicit
`init` step would just be one more thing a new user has to remember to
run first.

## Can I delete a posted journal entry?

Not through anything ledgerkit ships. `JournalRepository` has no
`delete`, and there's no CLI command for it. Accounting systems generally
don't delete posted entries — mistakes get corrected with an offsetting
entry, preserving the record of what actually happened — and that's the
direction this library is headed, not a delete button.

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
