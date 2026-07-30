from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from ledgerkit.errors import ValidationError
from ledgerkit.importers.generic_csv import GenericCsvImporter
from ledgerkit.money import Money


@pytest.fixture
def importer():
    return GenericCsvImporter()


def test_parses_valid_rows(importer):
    content = (
        "date,description,amount\n2026-07-11,Coffee Shop,-4.50\n2026-07-12,Paycheque,1500.00\n"
    )
    transactions = importer.parse(content)
    assert len(transactions) == 2
    assert transactions[0].transaction_date == date(2026, 7, 11)
    assert transactions[0].description == "Coffee Shop"
    assert transactions[0].amount == Money(Decimal("-4.50"))
    assert transactions[1].amount == Money(Decimal("1500.00"))


def test_rejects_missing_header():
    with pytest.raises(ValidationError):
        GenericCsvImporter().parse("")


def test_rejects_missing_required_column(importer):
    with pytest.raises(ValidationError):
        importer.parse("date,amount\n2026-07-11,10.00\n")


def test_rejects_bad_date(importer):
    with pytest.raises(ValidationError):
        importer.parse("date,description,amount\nnot-a-date,Coffee,-4.50\n")


def test_rejects_empty_description(importer):
    with pytest.raises(ValidationError):
        importer.parse("date,description,amount\n2026-07-11,,-4.50\n")


def test_rejects_bad_amount(importer):
    with pytest.raises(ValidationError):
        importer.parse("date,description,amount\n2026-07-11,Coffee,not-a-number\n")


def test_rejects_excess_precision_amount(importer):
    with pytest.raises(ValidationError):
        importer.parse("date,description,amount\n2026-07-11,Coffee,1.005\n")


def test_whitespace_is_trimmed(importer):
    content = "date,description,amount\n 2026-07-11 , Coffee Shop , -4.50 \n"
    transactions = importer.parse(content)
    assert transactions[0].description == "Coffee Shop"
    assert transactions[0].amount == Money(Decimal("-4.50"))


def test_empty_body_returns_empty_list(importer):
    assert importer.parse("date,description,amount\n") == []


def test_extra_columns_are_ignored(importer):
    content = "date,description,amount,note\n2026-07-11,Coffee,-4.50,decaf\n"
    transactions = importer.parse(content)
    assert len(transactions) == 1
