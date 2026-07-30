"""Shared row-level parsing helpers for statement importers.

`GenericCsvImporter` is the only dialect that uses these today, but the
date/amount parsing rules (ISO date, decimal amount, both failing loudly
with a row number in the message) aren't specific to CSV — a future
dialect parsing a different file format would want the same rules
applied the same way, not reimplemented with slightly different wording.
"""

from __future__ import annotations

from datetime import date as date_cls
from decimal import Decimal

from ledgerkit.errors import ValidationError


def parse_row_date(raw: str, line_number: int) -> date_cls:
    """Parse an ISO 8601 date from one row, raising with the row number on failure."""
    try:
        return date_cls.fromisoformat(raw)
    except ValueError as exc:
        raise ValidationError(f"row {line_number}: invalid date {raw!r}") from exc


def parse_row_amount(raw: str) -> Decimal:
    """Parse a decimal amount from one row's raw text.

    Raises:
        decimal.InvalidOperation: If `raw` isn't a valid decimal. Left
            unwrapped rather than turned into a `ValidationError` here,
            since callers need the row number to build a useful message
            and this function doesn't have one.
    """
    return Decimal(raw)
