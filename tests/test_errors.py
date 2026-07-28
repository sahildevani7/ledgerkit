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


def test_details_default_to_empty():
    err = ValidationError("bad input")
    assert err.details == {}


def test_details_stored():
    err = ValidationError("bad input", details={"field": "code", "value": ""})
    assert err.details == {"field": "code", "value": ""}


def test_to_dict_includes_code_message_and_details():
    err = NotFoundError("no such account", details={"account_id": 42})
    assert err.to_dict() == {
        "code": "not_found",
        "message": "no such account",
        "details": {"account_id": 42},
    }


def test_to_dict_with_no_details():
    err = ValidationError("bad input")
    assert err.to_dict() == {"code": "validation_error", "message": "bad input", "details": {}}


def test_to_dict_returns_a_copy_not_the_live_mapping():
    err = ValidationError("bad input", details={"x": 1})
    snapshot = err.to_dict()
    snapshot["details"]["x"] = 999
    assert err.details == {"x": 1}
