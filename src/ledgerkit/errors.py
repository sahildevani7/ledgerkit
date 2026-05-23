"""Typed error hierarchy shared across the library.

Every error raised by ledgerkit is a subclass of :class:`LedgerError` and
carries a stable ``code`` string, so callers (including the CLI) can branch
on error kind without parsing message text.
"""

from __future__ import annotations


class LedgerError(Exception):
    """Base class for all errors raised by ledgerkit."""

    code: str = "ledger_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class ValidationError(LedgerError):
    """Input failed a domain validation rule."""

    code = "validation_error"


class NotFoundError(LedgerError):
    """A referenced entity does not exist."""

    code = "not_found"


class UnbalancedEntryError(LedgerError):
    """A journal entry's debits and credits do not sum to zero."""

    code = "unbalanced_entry"


class DuplicateError(LedgerError):
    """An operation would create a duplicate of a unique entity."""

    code = "duplicate"


class StorageError(LedgerError):
    """The storage layer failed to complete an operation."""

    code = "storage_error"


class ConfigError(LedgerError):
    """Configuration failed to load or contains an invalid value."""

    code = "config_error"
