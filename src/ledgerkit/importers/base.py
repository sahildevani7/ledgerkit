"""The Importer protocol and the transaction shape every dialect parses to.

An importer never touches storage or posts anything — it only turns raw
statement text into a list of :class:`ImportedTransaction`. Turning those
into journal entries and posting them is a separate step (the CLI's
``import`` command, or a caller's own code, wires the two together — see
:mod:`ledgerkit.cli.cmd_import`). Keeping parsing and posting separate
means an importer can be tested against sample text without a database at
all, and a caller that wants different posting behavior (a different
contra account convention, say) doesn't need a different importer.
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
    from the perspective of the account the statement belongs to. This
    matches the sign convention on
    :class:`~ledgerkit.journal.entry.Line`, so turning a transaction into
    a journal line is a direct copy of the amount, not a sign flip.
    """

    transaction_date: date
    description: str
    amount: Money


@runtime_checkable
class Importer(Protocol):
    """Something that can parse a statement file's contents into transactions.

    One dialect (:class:`~ledgerkit.importers.generic_csv.GenericCsvImporter`)
    implements this today, reachable through
    :func:`ledgerkit.importers.registry.get_importer`. A second dialect
    would implement the same protocol and register under its own name;
    nothing about the CLI or the posting path would need to change.
    """

    def parse(self, content: str) -> list[ImportedTransaction]:
        """Parse a statement's full text into transactions, oldest first.

        Raises:
            ValidationError: If the content doesn't match this dialect —
                a missing required column, a malformed date or amount.
                An importer never partially parses a file and silently
                drops bad rows.
        """
        ...
