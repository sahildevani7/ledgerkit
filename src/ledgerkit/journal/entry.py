"""JournalEntry and Line: the double-entry invariant, in one place.

A line's amount is signed relative to the debit/credit convention used
throughout ledgerkit: positive is a debit, negative is a credit. An entry
is valid only if its lines' amounts sum to exactly zero — that's the whole
of double-entry bookkeeping, enforced once, here, before anything reaches
storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from ledgerkit.errors import UnbalancedEntryError, ValidationError
from ledgerkit.ids import AccountId, EntryId, ImportBatchId, LineId
from ledgerkit.money import Money


@dataclass(frozen=True, slots=True)
class Line:
    """One side of a journal entry: an account and a signed amount."""

    account_id: AccountId
    amount: Money
    id: LineId | None = None

    def __post_init__(self) -> None:
        if self.amount.is_zero():
            raise ValidationError("a journal line amount must not be zero")

    @property
    def is_debit(self) -> bool:
        return self.amount.is_positive()

    @property
    def is_credit(self) -> bool:
        return self.amount.is_negative()


@dataclass(frozen=True, slots=True)
class JournalEntry:
    """A balanced group of journal lines posted on a single date."""

    entry_date: date
    lines: tuple[Line, ...]
    memo: str | None = None
    import_batch_id: ImportBatchId | None = None
    created_at: datetime | None = None
    id: EntryId | None = None

    def __post_init__(self) -> None:
        if len(self.lines) < 2:
            raise ValidationError("a journal entry needs at least two lines")
        total = self.total()
        if not total.is_zero():
            raise UnbalancedEntryError(
                f"entry does not balance: lines sum to {total}, expected zero"
            )

    def total(self) -> Money:
        currency = self.lines[0].amount.currency
        result = Money.zero(currency)
        for line in self.lines:
            result = result + line.amount
        return result

    def debit_total(self) -> Money:
        currency = self.lines[0].amount.currency
        result = Money.zero(currency)
        for line in self.lines:
            if line.is_debit:
                result = result + line.amount
        return result

    def credit_total(self) -> Money:
        currency = self.lines[0].amount.currency
        result = Money.zero(currency)
        for line in self.lines:
            if line.is_credit:
                result = result + (-line.amount)
        return result

    def involves_account(self, account_id: AccountId) -> bool:
        """Whether any line in this entry posts against ``account_id``."""
        return any(line.account_id == account_id for line in self.lines)

    def lines_for_account(self, account_id: AccountId) -> tuple[Line, ...]:
        """Every line in this entry that posts against ``account_id``.

        Usually a single line, but an entry can legitimately post more than
        one line to the same account (splitting a payment across
        categories that happen to share an account, for instance).
        """
        return tuple(line for line in self.lines if line.account_id == account_id)

    def __len__(self) -> int:
        """The number of lines in this entry — always at least 2."""
        return len(self.lines)
