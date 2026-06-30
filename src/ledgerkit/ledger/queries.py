"""Read-only queries over posted journal lines: balances and activity."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.currency import get_currency
from ledgerkit.ids import AccountId, EntryId
from ledgerkit.money import Money


@dataclass(frozen=True, slots=True)
class AccountActivity:
    """One posted line against an account, with its entry's context."""

    entry_id: EntryId
    entry_date: date
    memo: str | None
    amount: Money


def account_balance(
    connection: sqlite3.Connection, account_id: AccountId, *, as_of: date | None = None
) -> Money:
    """The signed sum of an account's posted lines, optionally as of a date.

    Positive means a net debit balance, negative a net credit balance,
    matching the sign convention used on :class:`~ledgerkit.journal.entry.Line`.
    """
    AccountRepository(connection).get(account_id)
    query = (
        "SELECT jl.amount, jl.currency_code FROM journal_lines jl "
        "JOIN journal_entries je ON je.id = jl.entry_id "
        "WHERE jl.account_id = ?"
    )
    params: list[object] = [account_id]
    if as_of is not None:
        query += " AND je.entry_date <= ?"
        params.append(as_of.isoformat())
    rows = connection.execute(query, params).fetchall()

    total = Money.zero()
    for row in rows:
        total = total + Money(row["amount"], get_currency(row["currency_code"]))
    return total


def account_activity(
    connection: sqlite3.Connection,
    account_id: AccountId,
    *,
    start: date | None = None,
    end: date | None = None,
) -> list[AccountActivity]:
    """Every posted line against an account, oldest first, optionally bounded."""
    AccountRepository(connection).get(account_id)
    query = (
        "SELECT je.id AS entry_id, je.entry_date, je.memo, jl.amount, jl.currency_code "
        "FROM journal_lines jl JOIN journal_entries je ON je.id = jl.entry_id "
        "WHERE jl.account_id = ?"
    )
    params: list[object] = [account_id]
    if start is not None:
        query += " AND je.entry_date >= ?"
        params.append(start.isoformat())
    if end is not None:
        query += " AND je.entry_date <= ?"
        params.append(end.isoformat())
    query += " ORDER BY je.entry_date, je.id, jl.id"
    rows = connection.execute(query, params).fetchall()

    return [
        AccountActivity(
            entry_id=EntryId(row["entry_id"]),
            entry_date=date.fromisoformat(row["entry_date"]),
            memo=row["memo"],
            amount=Money(row["amount"], get_currency(row["currency_code"])),
        )
        for row in rows
    ]
