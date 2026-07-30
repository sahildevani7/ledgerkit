"""The importer registry: name to :class:`~ledgerkit.importers.base.Importer`.

One dialect is registered today. The registry exists so callers (the CLI's
``import`` command) select a dialect by name instead of importing a
concrete class directly — the same pattern as
:mod:`ledgerkit.reporting.renderer` and :mod:`ledgerkit.currency`'s
currency lookup: one real registration proving the seam works, with
nothing unregistered sitting around unused.
"""

from __future__ import annotations

from ledgerkit.errors import ValidationError
from ledgerkit.importers.base import Importer
from ledgerkit.importers.generic_csv import GenericCsvImporter

_REGISTRY: dict[str, Importer] = {}


def register(name: str, importer: Importer) -> None:
    """Register ``importer`` under ``name``, replacing any prior registration.

    There's no validation on ``name`` beyond it being a string — dialect
    names are an internal convention (``generic_csv``), not a format with
    its own rules.
    """
    _REGISTRY[name] = importer


def get_importer(name: str) -> Importer:
    """Look up a registered importer by name.

    Raises:
        ValidationError: If nothing is registered under ``name``. The
            message doesn't enumerate valid names — call
            :func:`available_importers` for that — since a typo'd name at
            the CLI usually means the user already knows roughly what
            they meant to type.
    """
    try:
        return _REGISTRY[name]
    except KeyError:
        raise ValidationError(f"no importer registered as {name!r}") from None


def available_importers() -> list[str]:
    """Every registered dialect name, sorted for deterministic output."""
    return sorted(_REGISTRY)


register("generic_csv", GenericCsvImporter())
