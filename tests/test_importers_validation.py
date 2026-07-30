from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

import pytest

from ledgerkit.errors import ValidationError
from ledgerkit.importers.validation import parse_row_amount, parse_row_date


def test_parse_row_date_valid():
    assert parse_row_date("2026-07-01", 2) == date(2026, 7, 1)


def test_parse_row_date_invalid_raises_with_row_number():
    with pytest.raises(ValidationError, match="row 5"):
        parse_row_date("not-a-date", 5)


def test_parse_row_amount_valid():
    assert parse_row_amount("10.50") == Decimal("10.50")


def test_parse_row_amount_invalid_raises_invalid_operation():
    with pytest.raises(InvalidOperation):
        parse_row_amount("not-a-number")
