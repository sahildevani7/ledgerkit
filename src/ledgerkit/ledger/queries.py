"""Read-only queries over posted journal lines: balances and activity."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.accounts.tree import ChartOfAccounts
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


def all_account_balances(
    connection: sqlite3.Connection, *, as_of: date | None = None
) -> dict[AccountId, Money]:
    """Every account's balance in a single query, keyed by account id.

    This is what :func:`~ledgerkit.ledger.trial_balance.build_trial_balance`
    uses internally — computing every account's balance with one grouped
    query is far cheaper than calling :func:`account_balance` once per
    account, and existing accounts with zero activity still appear in the
    result with a zero balance.
    """
    accounts = AccountRepository(connection).list_all()
    balances: dict[AccountId, Money] = {}
    for account in accounts:
        assert account.id is not None
        balances[account.id] = Money.zero()

    query = (
        "SELECT jl.account_id, jl.amount, jl.currency_code FROM journal_lines jl "
        "JOIN journal_entries je ON je.id = jl.entry_id"
    )
    params: list[object] = []
    if as_of is not None:
        query += " WHERE je.entry_date <= ?"
        params.append(as_of.isoformat())
    rows = connection.execute(query, params).fetchall()

    for row in rows:
        account_id = AccountId(row["account_id"])
        amount = Money(row["amount"], get_currency(row["currency_code"]))
        balances[account_id] = balances.get(account_id, Money.zero()) + amount

    return balances


def accounts_with_activity(connection: sqlite3.Connection) -> list[AccountId]:
    """Every account id that has at least one posted line, sorted by id.

    Useful for distinguishing accounts that have actually been used from
    ones that exist in the chart but have never been posted to.
    """
    rows = connection.execute(
        "SELECT DISTINCT account_id FROM journal_lines ORDER BY account_id"
    ).fetchall()
    return [AccountId(row["account_id"]) for row in rows]


def subtree_balance(
    connection: sqlite3.Connection,
    account_id: AccountId,
    chart: ChartOfAccounts,
    *,
    as_of: date | None = None,
) -> Money:
    """The combined balance of an account and every account beneath it.

    Useful for a parent account that's purely organizational — "Groceries"
    might have "Groceries: Household" and "Groceries: Dining Out" beneath
    it, and this answers "how much, in total, across the whole category"
    without the caller needing to walk the hierarchy itself.

    Args:
        connection: An already-migrated connection.
        account_id: The account to start from; included in the total.
        chart: A :class:`~ledgerkit.accounts.tree.ChartOfAccounts` built
            from the same database — passed in rather than rebuilt here,
            since a caller summing several subtrees would otherwise pay
            for reloading the whole chart of accounts each time.
        as_of: Restrict the balance to activity on or before this date.
    """
    total = account_balance(connection, account_id, as_of=as_of)
    for descendant in chart.descendants_of(account_id):
        assert descendant.id is not None
        total = total + account_balance(connection, descendant.id, as_of=as_of)
    return total
