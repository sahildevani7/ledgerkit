# Error handling

## The hierarchy

Every error ledgerkit raises is a subclass of
`ledgerkit.errors.LedgerError`, and every subclass carries a stable
`code` string:

| Class | `code` | Raised when |
|---|---|---|
| `ValidationError` | `validation_error` | Input fails a domain rule: empty account code, unbalanced entry, bad rounding mode, malformed CSV row |
| `NotFoundError` | `not_found` | A lookup by id or code finds nothing |
| `UnbalancedEntryError` | `unbalanced_entry` | A journal entry's lines don't sum to zero (a `ValidationError` subclass) |
| `DuplicateError` | `duplicate` | Creating an account whose code already exists |
| `StorageError` | `storage_error` | The persistence layer itself fails — a migration gap, a transaction misuse |
| `ConfigError` | `config_error` | Configuration fails to load or parse |

There's no error class per feature area. A new failure mode in, say, the
importer gets a `ValidationError` with a specific message, not a new
`ImporterError` class — the `code` is meant to be coarse-grained enough
that a caller can branch on "was this bad input vs. a missing entity vs.
a storage problem" without needing to know about every individual
message.

## Catching errors

```python
from ledgerkit.errors import LedgerError, NotFoundError, ValidationError

try:
    account = repo.get_by_code("9999")
except NotFoundError:
    ...  # the code didn't match anything
except ValidationError:
    ...  # the input itself was malformed
except LedgerError as exc:
    ...  # anything else — still has .code and .message
```

Catching the base `LedgerError` is always safe and always gives you
`.message` (what `str(exc)` returns) and `.details` (a `Mapping` of
supplementary context, empty by default). `.to_dict()` gives a plain-data
snapshot — `{"code": ..., "message": ..., "details": ...}` — for anywhere
that needs to cross a boundary that doesn't speak exceptions.

## In the CLI

`ledgerkit.cli.main.main` catches `LedgerError` at the top level, prints
`error: <message>` to stderr, and returns exit code `1`. Every other
exception — a bug, not a domain error — is left to propagate and crash
loudly with a full traceback, deliberately: a `LedgerError` is an
expected outcome a script can check for; anything else is a bug that
should be visible immediately, not swallowed into a generic non-zero exit
code.

Argument-parsing failures (a missing required flag, an unrecognized
subcommand) never reach this handler at all — `argparse` exits directly
with its own conventional code, `2`, before `main`'s `try` block runs.
