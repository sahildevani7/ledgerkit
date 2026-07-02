from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import FixedClock
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.repository import JournalRepository
from ledgerkit.ledger.trial_balance import build_trial_balance
from ledgerkit.money import Money


@pytest.fixture
def accounts(migrated_conn):
    repo = AccountRepository(migrated_conn)
    checking = repo.create(Account(code="1000", name="Checking", type=AccountType.ASSET))
    loan = repo.create(Account(code="2000", name="Loan", type=AccountType.LIABILITY))
    opening = repo.create(Account(code="3000", name="Opening Balance", type=AccountType.EQUITY))
    return checking, loan, opening


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 7, 1, 20, 0, 0))


def test_empty_ledger_balances(migrated_conn, accounts):
    tb = build_trial_balance(migrated_conn)
    assert tb.is_balanced()
    assert tb.total_debits() == Money.zero()
    assert tb.total_credits() == Money.zero()


def test_includes_every_account(migrated_conn, accounts):
    tb = build_trial_balance(migrated_conn)
    codes = {row.account.code for row in tb.rows}
    assert codes == {"1000", "2000", "3000"}


def test_debit_and_credit_split(migrated_conn, accounts, clock):
    checking, loan, opening = accounts
    entry = JournalEntry(
        entry_date=date(2026, 7, 1),
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("500.00"))),
            Line(account_id=loan.id, amount=-Money(Decimal("300.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("200.00"))),
        ),
    )
    JournalRepository(migrated_conn).create(entry, clock)
    tb = build_trial_balance(migrated_conn)
    by_code = {row.account.code: row for row in tb.rows}
    assert by_code["1000"].debit == Money(Decimal("500.00"))
    assert by_code["1000"].credit == Money.zero()
    assert by_code["2000"].credit == Money(Decimal("300.00"))
    assert by_code["2000"].debit == Money.zero()
    assert by_code["3000"].credit == Money(Decimal("200.00"))


def test_totals_balance_after_activity(migrated_conn, accounts, clock):
    checking, loan, opening = accounts
    entry = JournalEntry(
        entry_date=date(2026, 7, 1),
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("500.00"))),
            Line(account_id=loan.id, amount=-Money(Decimal("300.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("200.00"))),
        ),
    )
    JournalRepository(migrated_conn).create(entry, clock)
    tb = build_trial_balance(migrated_conn)
    assert tb.is_balanced()
    assert tb.total_debits() == Money(Decimal("500.00"))
    assert tb.total_credits() == Money(Decimal("500.00"))


def test_as_of_date_excludes_later_entries(migrated_conn, accounts, clock):
    checking, loan, opening = accounts
    early = JournalEntry(
        entry_date=date(2026, 6, 1),
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("100.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("100.00"))),
        ),
    )
    later = JournalEntry(
        entry_date=date(2026, 7, 15),
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("50.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("50.00"))),
        ),
    )
    repo = JournalRepository(migrated_conn)
    repo.create(early, clock)
    repo.create(later, clock)
    tb = build_trial_balance(migrated_conn, as_of=date(2026, 7, 1))
    by_code = {row.account.code: row for row in tb.rows}
    assert by_code["1000"].debit == Money(Decimal("100.00"))
