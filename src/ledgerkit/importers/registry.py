"""The importer registry: name to :class:`~ledgerkit.importers.base.Importer`.

One dialect is registered today. The registry exists so callers (the CLI's
``import`` command) select a dialect by name instead of importing a
concrete class directly.
"""

from __future__ import annotations

from ledgerkit.errors import ValidationError
from ledgerkit.importers.base import Importer
from ledgerkit.importers.generic_csv import GenericCsvImporter

_REGISTRY: dict[str, Importer] = {}


def register(name: str, importer: Importer) -> None:
    _REGISTRY[name] = importer


def get_importer(name: str) -> Importer:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise ValidationError(f"no importer registered as {name!r}") from None


def available_importers() -> list[str]:
    return sorted(_REGISTRY)


register("generic_csv", GenericCsvImporter())
