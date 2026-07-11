"""The Importer protocol and the transaction shape every dialect parses to.

An importer never touches storage or posts anything — it only turns raw
statement text into a list of :class:`ImportedTransaction`. Turning those
into journal entries and posting them is a separate step (the CLI's
``import`` command wires the two together).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol, runtime_checkable

from ledgerkit.money import Money


@dataclass(frozen=True, slots=True)
class ImportedTransaction:
    """One row parsed from a statement, not yet posted.

    ``amount`` is signed: positive is money in, negative is money out —
    from the perspective of the account the statement belongs to.
    """

    transaction_date: date
    description: str
    amount: Money


@runtime_checkable
class Importer(Protocol):
    """Something that can parse a statement file's contents into transactions."""

    def parse(self, content: str) -> list[ImportedTransaction]: ...
