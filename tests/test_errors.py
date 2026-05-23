from __future__ import annotations

import pytest

from ledgerkit.errors import (
    ConfigError,
    DuplicateError,
    LedgerError,
    NotFoundError,
    StorageError,
    UnbalancedEntryError,
    ValidationError,
)


@pytest.mark.parametrize(
    "cls,expected_code",
    [
        (LedgerError, "ledger_error"),
        (ValidationError, "validation_error"),
        (NotFoundError, "not_found"),
        (UnbalancedEntryError, "unbalanced_entry"),
        (DuplicateError, "duplicate"),
        (StorageError, "storage_error"),
        (ConfigError, "config_error"),
    ],
)
def test_error_codes(cls, expected_code):
    assert cls.code == expected_code


def test_all_errors_are_ledger_errors():
    for cls in (
        ValidationError,
        NotFoundError,
        UnbalancedEntryError,
        DuplicateError,
        StorageError,
        ConfigError,
    ):
        assert issubclass(cls, LedgerError)


def test_message_and_str():
    err = ValidationError("bad input")
    assert err.message == "bad input"
    assert str(err) == "bad input"


def test_raisable_and_catchable_as_base():
    with pytest.raises(LedgerError):
        raise NotFoundError("missing")
