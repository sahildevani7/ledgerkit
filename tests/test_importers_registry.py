from __future__ import annotations

from datetime import date

import pytest

from ledgerkit.errors import ValidationError
from ledgerkit.importers.base import ImportedTransaction
from ledgerkit.importers.generic_csv import GenericCsvImporter
from ledgerkit.importers.registry import available_importers, get_importer, register
from ledgerkit.money import Money


def test_generic_csv_is_registered():
    importer = get_importer("generic_csv")
    assert isinstance(importer, GenericCsvImporter)


def test_get_importer_missing_raises():
    with pytest.raises(ValidationError):
        get_importer("does_not_exist")


def test_available_importers_includes_generic_csv():
    assert "generic_csv" in available_importers()


def test_available_importers_is_sorted():
    assert available_importers() == sorted(available_importers())


def test_register_adds_a_new_importer():
    class _StubImporter:
        def parse(self, content: str) -> list[ImportedTransaction]:
            return [
                ImportedTransaction(
                    transaction_date=date(2026, 1, 1), description=content, amount=Money(0)
                )
            ]

    register("stub_for_test", _StubImporter())
    try:
        assert "stub_for_test" in available_importers()
        assert isinstance(get_importer("stub_for_test"), _StubImporter)
    finally:
        from ledgerkit.importers import registry

        del registry._REGISTRY["stub_for_test"]
