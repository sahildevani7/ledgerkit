"""Typed error hierarchy shared across the library.

Every error raised by ledgerkit is a subclass of :class:`LedgerError` and
carries a stable ``code`` string, so callers (including the CLI) can branch
on error kind without parsing message text. Each subclass corresponds to
one broad failure category; a new feature area gets a new *message*, not a
new error class, unless the failure mode is genuinely distinct from
everything below.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class LedgerError(Exception):
    """Base class for all errors raised by ledgerkit.

    Args:
        message: A human-readable description of what went wrong. This is
            what :func:`str` on the exception returns, and what the CLI
            prints to stderr.
        details: Optional structured context about the failure — for
            example, the offending value or the id involved. Purely
            supplementary; callers should still be able to understand the
            error from ``message`` alone.
    """

    code: str = "ledger_error"

    def __init__(self, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: Mapping[str, Any] = details or {}

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """A structured representation of this error: code, message, and details.

        Useful anywhere an error needs to cross a boundary that only
        speaks plain data — logging, a future non-text output format —
        without callers needing to know about the exception hierarchy.
        """
        return {"code": self.code, "message": self.message, "details": dict(self.details)}


class ValidationError(LedgerError):
    """Input failed a domain validation rule.

    Raised for malformed or out-of-range input that's caught before it
    touches storage — an empty account code, an unbalanced journal entry,
    an unsupported rounding mode, and similar.
    """

    code = "validation_error"


class NotFoundError(LedgerError):
    """A referenced entity does not exist.

    Raised when a lookup by id or code finds nothing — a missing account,
    a missing journal entry, an unregistered importer name.
    """

    code = "not_found"


class UnbalancedEntryError(LedgerError):
    """A journal entry's debits and credits do not sum to zero.

    This is the one error that exists specifically to guard the
    double-entry invariant, rather than being a general validation
    failure, because it's the single rule the whole library is built
    around.
    """

    code = "unbalanced_entry"


class DuplicateError(LedgerError):
    """An operation would create a duplicate of a unique entity.

    Raised, for instance, when creating an account whose code already
    exists.
    """

    code = "duplicate"


class StorageError(LedgerError):
    """The storage layer failed to complete an operation.

    Raised for failures in the persistence layer itself — a migration
    version gap, a transaction misuse — as opposed to bad input, which is
    a :class:`ValidationError`.
    """

    code = "storage_error"


class ConfigError(LedgerError):
    """Configuration failed to load or contains an invalid value."""

    code = "config_error"
