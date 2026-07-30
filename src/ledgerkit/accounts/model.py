"""The Account entity and its normal-balance semantics.

Every account has a normal balance side (debit or credit) determined
entirely by its type. Increases to an asset or expense account are debits;
increases to a liability, equity, or income account are credits. Nothing
about a specific account overrides this — it's a property of the type.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ledgerkit.errors import ValidationError
from ledgerkit.ids import AccountId


class NormalBalance(Enum):
    """Which side of the ledger an increase to an account posts to."""

    DEBIT = "debit"
    CREDIT = "credit"


class AccountType(Enum):
    """The five account categories the accounting equation is built from.

    Assets = Liabilities + Equity, and Income/Expense feed into Equity
    through retained earnings. Every account belongs to exactly one of
    these; there's no sixth category and no per-account override.
    """

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"

    @property
    def normal_balance(self) -> NormalBalance:
        """The side (debit or credit) an increase to this account type posts to."""
        if self in (AccountType.ASSET, AccountType.EXPENSE):
            return NormalBalance.DEBIT
        return NormalBalance.CREDIT


@dataclass(frozen=True, slots=True)
class Account:
    """A single account in the chart of accounts.

    ``id`` is ``None`` until the account has been persisted, at which point
    the repository returns a copy with the assigned id.
    """

    code: str
    name: str
    type: AccountType
    parent_id: AccountId | None = None
    is_active: bool = True
    id: AccountId | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValidationError("account code must not be empty")
        if not self.name.strip():
            raise ValidationError("account name must not be empty")

    @property
    def display_label(self) -> str:
        """A single-line ``"code name"`` label, handy for logs and CLI output."""
        return f"{self.code} {self.name}"
