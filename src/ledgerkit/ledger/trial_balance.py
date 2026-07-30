"""Trial balance: every account's balance split into debit and credit columns.

Splitting a signed balance by sign always leaves the debit column summing
to the same total as the credit column — that's a direct consequence of
every posted entry balancing individually, not something asserted here.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from ledgerkit.accounts.model import Account
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.ledger.queries import all_account_balances
from ledgerkit.money import Money


@dataclass(frozen=True, slots=True)
class TrialBalanceRow:
    account: Account
    debit: Money
    credit: Money


@dataclass(frozen=True, slots=True)
class TrialBalance:
    as_of: date | None
    rows: tuple[TrialBalanceRow, ...]

    def total_debits(self) -> Money:
        total = Money.zero()
        for row in self.rows:
            total = total + row.debit
        return total

    def total_credits(self) -> Money:
        total = Money.zero()
        for row in self.rows:
            total = total + row.credit
        return total

    def is_balanced(self) -> bool:
        return self.total_debits() == self.total_credits()


def build_trial_balance(
    connection: sqlite3.Connection, *, as_of: date | None = None
) -> TrialBalance:
    accounts = AccountRepository(connection).list_all()
    balances = all_account_balances(connection, as_of=as_of)
    rows: list[TrialBalanceRow] = []
    for account in accounts:
        assert account.id is not None
        balance = balances[account.id]
        if balance.is_positive():
            debit, credit = balance, Money.zero(balance.currency)
        elif balance.is_negative():
            debit, credit = Money.zero(balance.currency), -balance
        else:
            debit, credit = Money.zero(balance.currency), Money.zero(balance.currency)
        rows.append(TrialBalanceRow(account=account, debit=debit, credit=credit))
    return TrialBalance(as_of=as_of, rows=tuple(rows))
