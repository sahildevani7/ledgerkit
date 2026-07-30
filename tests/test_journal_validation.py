from __future__ import annotations

from decimal import Decimal

import pytest

from ledgerkit.errors import UnbalancedEntryError, ValidationError
from ledgerkit.journal.validation import validate_balanced, validate_line_count
from ledgerkit.money import Money


def test_validate_line_count_accepts_two():
    validate_line_count(2)  # should not raise


def test_validate_line_count_accepts_more_than_two():
    validate_line_count(5)  # should not raise


def test_validate_line_count_rejects_one():
    with pytest.raises(ValidationError):
        validate_line_count(1)


def test_validate_line_count_rejects_zero():
    with pytest.raises(ValidationError):
        validate_line_count(0)


def test_validate_balanced_accepts_zero():
    validate_balanced(Money.zero())  # should not raise


def test_validate_balanced_rejects_nonzero():
    with pytest.raises(UnbalancedEntryError):
        validate_balanced(Money(Decimal("1.00")))
