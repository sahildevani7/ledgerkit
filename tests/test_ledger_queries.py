from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import FixedClock
from ledgerkit.errors import NotFoundError
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.repository import JournalRepository
from ledgerkit.ledger.queries import account_activity, account_balance
from ledgerkit.money import Money


@pytest.fixture
def accounts(migrated_conn):
    repo = AccountRepository(migrated_conn)
    checking = repo.create(Account(code="1000", name="Checking", type=AccountType.ASSET))
    opening = repo.create(Account(code="3000", name="Opening Balance", type=AccountType.EQUITY))
    return checking, opening


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 6, 30, 19, 0, 0))


def _post(conn, clock, checking_id, opening_id, amount, entry_date):
    entry = JournalEntry(
        entry_date=entry_date,
        lines=(
            Line(account_id=checking_id, amount=Money(Decimal(amount))),
            Line(account_id=opening_id, amount=-Money(Decimal(amount))),
        ),
    )
    return JournalRepository(conn).create(entry, clock)


def test_balance_with_no_activity_is_zero(migrated_conn, accounts):
    checking, _ = accounts
    assert account_balance(migrated_conn, checking.id).is_zero()


def test_balance_missing_account_raises(migrated_conn):
    with pytest.raises(NotFoundError):
        account_balance(migrated_conn, 999)  # type: ignore[arg-type]


def test_balance_sums_activity(migrated_conn, accounts, clock):
    checking, opening = accounts
    _post(migrated_conn, clock, checking.id, opening.id, "100.00", date(2026, 6, 1))
    _post(migrated_conn, clock, checking.id, opening.id, "50.00", date(2026, 6, 15))
    assert account_balance(migrated_conn, checking.id) == Money(Decimal("150.00"))
    assert account_balance(migrated_conn, opening.id) == Money(Decimal("-150.00"))


def test_balance_as_of_date_excludes_later_activity(migrated_conn, accounts, clock):
    checking, opening = accounts
    _post(migrated_conn, clock, checking.id, opening.id, "100.00", date(2026, 6, 1))
    _post(migrated_conn, clock, checking.id, opening.id, "50.00", date(2026, 6, 15))
    balance = account_balance(migrated_conn, checking.id, as_of=date(2026, 6, 10))
    assert balance == Money(Decimal("100.00"))


def test_balance_as_of_boundary_is_inclusive(migrated_conn, accounts, clock):
    checking, opening = accounts
    _post(migrated_conn, clock, checking.id, opening.id, "100.00", date(2026, 6, 15))
    balance = account_balance(migrated_conn, checking.id, as_of=date(2026, 6, 15))
    assert balance == Money(Decimal("100.00"))


def test_activity_empty_when_no_lines(migrated_conn, accounts):
    checking, _ = accounts
    assert account_activity(migrated_conn, checking.id) == []


def test_activity_missing_account_raises(migrated_conn):
    with pytest.raises(NotFoundError):
        account_activity(migrated_conn, 999)  # type: ignore[arg-type]


def test_activity_ordered_by_date(migrated_conn, accounts, clock):
    checking, opening = accounts
    _post(migrated_conn, clock, checking.id, opening.id, "50.00", date(2026, 6, 15))
    _post(migrated_conn, clock, checking.id, opening.id, "100.00", date(2026, 6, 1))
    rows = account_activity(migrated_conn, checking.id)
    assert [r.amount.amount for r in rows] == [Decimal("100.00"), Decimal("50.00")]


def test_activity_filtered_by_start_and_end(migrated_conn, accounts, clock):
    checking, opening = accounts
    _post(migrated_conn, clock, checking.id, opening.id, "10.00", date(2026, 6, 1))
    _post(migrated_conn, clock, checking.id, opening.id, "20.00", date(2026, 6, 10))
    _post(migrated_conn, clock, checking.id, opening.id, "30.00", date(2026, 6, 20))
    rows = account_activity(
        migrated_conn, checking.id, start=date(2026, 6, 5), end=date(2026, 6, 15)
    )
    assert [r.amount.amount for r in rows] == [Decimal("20.00")]


def test_activity_includes_memo(migrated_conn, accounts, clock):
    checking, opening = accounts
    entry = JournalEntry(
        entry_date=date(2026, 6, 1),
        memo="rent",
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("10.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("10.00"))),
        ),
    )
    JournalRepository(migrated_conn).create(entry, clock)
    rows = account_activity(migrated_conn, checking.id)
    assert rows[0].memo == "rent"


def test_balance_unaffected_by_other_accounts_activity(migrated_conn, accounts, clock):
    checking, opening = accounts
    _post(migrated_conn, clock, checking.id, opening.id, "100.00", date(2026, 6, 1))
    assert account_balance(migrated_conn, opening.id) == Money(Decimal("-100.00"))


def test_balance_as_of_before_any_activity_is_zero(migrated_conn, accounts, clock):
    checking, opening = accounts
    _post(migrated_conn, clock, checking.id, opening.id, "100.00", date(2026, 6, 15))
    balance = account_balance(migrated_conn, checking.id, as_of=date(2026, 6, 1))
    assert balance.is_zero()


def test_activity_returns_entry_id(migrated_conn, accounts, clock):
    checking, opening = accounts
    posted = _post(migrated_conn, clock, checking.id, opening.id, "10.00", date(2026, 6, 1))
    rows = account_activity(migrated_conn, checking.id)
    assert rows[0].entry_id == posted.id


def test_activity_reflects_multiple_lines_same_entry(migrated_conn, accounts, clock):
    checking, opening = accounts
    entry = JournalEntry(
        entry_date=date(2026, 6, 1),
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("30.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("10.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("20.00"))),
        ),
    )
    JournalRepository(migrated_conn).create(entry, clock)
    rows = account_activity(migrated_conn, opening.id)
    assert len(rows) == 2
    assert sorted(r.amount.amount for r in rows) == [Decimal("-20.00"), Decimal("-10.00")]
