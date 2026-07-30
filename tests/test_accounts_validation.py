from __future__ import annotations

import pytest

from ledgerkit.accounts.validation import validate_code, validate_name
from ledgerkit.errors import ValidationError


def test_validate_code_accepts_nonempty():
    validate_code("1000")  # should not raise


def test_validate_code_rejects_empty():
    with pytest.raises(ValidationError):
        validate_code("")


def test_validate_code_rejects_whitespace_only():
    with pytest.raises(ValidationError):
        validate_code("   ")


def test_validate_name_accepts_nonempty():
    validate_name("Checking")  # should not raise


def test_validate_name_rejects_empty():
    with pytest.raises(ValidationError):
        validate_name("")
