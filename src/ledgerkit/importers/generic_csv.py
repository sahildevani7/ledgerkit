"""The one shipped importer dialect: a plain three-column CSV.

Expected header: ``date,description,amount``. ``date`` is ISO 8601
(``YYYY-MM-DD``); ``amount`` is a decimal string, positive for money in and
negative for money out. See :doc:`/csv-import-format` for the full format
description with examples.

Every row is validated before any transaction is returned — a malformed
row anywhere in the file fails the whole parse, rather than returning a
partial list with the bad row silently skipped. That's deliberate: a
statement import is usually unattended, and a silently dropped
transaction is far worse than a loud failure the caller has to notice and
fix.
"""

from __future__ import annotations

import csv
import io
from datetime import date as date_cls
from decimal import Decimal, InvalidOperation

from ledgerkit.errors import ValidationError
from ledgerkit.importers.base import ImportedTransaction
from ledgerkit.money import Money

REQUIRED_COLUMNS = ("date", "description", "amount")


class GenericCsvImporter:
    def parse(self, content: str) -> list[ImportedTransaction]:
        reader = csv.DictReader(io.StringIO(content))
        if reader.fieldnames is None:
            raise ValidationError("CSV has no header row")
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ValidationError(f"CSV missing required column(s): {missing}")

        transactions: list[ImportedTransaction] = []
        for line_number, row in enumerate(reader, start=2):
            transactions.append(self._parse_row(row, line_number))
        return transactions

    def _parse_row(self, row: dict[str, str | None], line_number: int) -> ImportedTransaction:
        raw_date = (row.get("date") or "").strip()
        try:
            parsed_date = date_cls.fromisoformat(raw_date)
        except ValueError as exc:
            raise ValidationError(f"row {line_number}: invalid date {raw_date!r}") from exc

        description = (row.get("description") or "").strip()
        if not description:
            raise ValidationError(f"row {line_number}: description must not be empty")

        raw_amount = (row.get("amount") or "").strip()
        try:
            amount = Money(Decimal(raw_amount))
        except InvalidOperation as exc:
            raise ValidationError(f"row {line_number}: invalid amount {raw_amount!r}") from exc

        return ImportedTransaction(
            transaction_date=parsed_date, description=description, amount=amount
        )
