"""Validation rules for a journal entry, kept separate from construction.

`JournalEntry.__post_init__` calls these rather than inlining the checks,
so the double-entry invariant reads as "a line count rule and a balance
rule apply" rather than being buried in dataclass boilerplate.
"""

from __future__ import annotations

from ledgerkit.errors import UnbalancedEntryError, ValidationError
from ledgerkit.money import Money

MIN_LINE_COUNT = 2


def validate_line_count(line_count: int) -> None:
    """Raise ValidationError if an entry has fewer than :data:`MIN_LINE_COUNT` lines."""
    if line_count < MIN_LINE_COUNT:
        raise ValidationError("a journal entry needs at least two lines")


def validate_balanced(total: Money) -> None:
    """Raise UnbalancedEntryError if `total` (a sum of line amounts) isn't zero."""
    if not total.is_zero():
        raise UnbalancedEntryError(
            f"entry does not balance: lines sum to {total}, expected zero"
        )
