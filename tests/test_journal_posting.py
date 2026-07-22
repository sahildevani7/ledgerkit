from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import FixedClock
from ledgerkit.errors import NotFoundError
from ledgerkit.ids import AccountId
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.posting import post, post_batch
from ledgerkit.journal.repository import JournalRepository
from ledgerkit.money import Money


@pytest.fixture
def accounts(migrated_conn):
    repo = AccountRepository(migrated_conn)
    checking = repo.create(Account(code="1000", name="Checking", type=AccountType.ASSET))
    opening = repo.create(Account(code="3000", name="Opening Balance", type=AccountType.EQUITY))
    return checking, opening


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 6, 21, 20, 0, 0))


def _entry(checking_id, opening_id, amount="100.00", entry_date=date(2026, 6, 21)):
    return JournalEntry(
        entry_date=entry_date,
        lines=(
            Line(account_id=checking_id, amount=Money(Decimal(amount))),
            Line(account_id=opening_id, amount=-Money(Decimal(amount))),
        ),
    )


def test_post_single_entry(migrated_conn, accounts, clock):
    checking, opening = accounts
    posted = post(migrated_conn, _entry(checking.id, opening.id), clock)
    assert posted.id is not None
    assert JournalRepository(migrated_conn).get(posted.id) == posted


def test_post_batch_posts_all(migrated_conn, accounts, clock):
    checking, opening = accounts
    entries = [
        _entry(checking.id, opening.id, "10.00"),
        _entry(checking.id, opening.id, "20.00"),
    ]
    posted = post_batch(migrated_conn, entries, clock)
    assert len(posted) == 2
    assert JournalRepository(migrated_conn).list_all() == posted


def test_post_batch_rolls_back_entirely_on_unknown_account(migrated_conn, accounts, clock):
    checking, opening = accounts
    good_entry = _entry(checking.id, opening.id, "10.00")
    bad_entry = JournalEntry(
        entry_date=date(2026, 6, 21),
        lines=(
            Line(account_id=AccountId(9999), amount=Money(Decimal("5.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("5.00"))),
        ),
    )
    with pytest.raises(NotFoundError):
        post_batch(migrated_conn, [good_entry, bad_entry], clock)
    assert JournalRepository(migrated_conn).list_all() == []


def test_post_batch_empty_list_is_noop(migrated_conn, clock):
    assert post_batch(migrated_conn, [], clock) == []


def test_post_batch_preserves_order(migrated_conn, accounts, clock):
    checking, opening = accounts
    entries = [
        _entry(checking.id, opening.id, "1.00", date(2026, 6, 1)),
        _entry(checking.id, opening.id, "2.00", date(2026, 6, 2)),
        _entry(checking.id, opening.id, "3.00", date(2026, 6, 3)),
    ]
    posted = post_batch(migrated_conn, entries, clock)
    assert [p.entry_date for p in posted] == [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)]


def test_post_batch_bad_second_entry_rolls_back_first(migrated_conn, accounts, clock):
    checking, opening = accounts
    good = _entry(checking.id, opening.id, "10.00")
    bad = JournalEntry(
        entry_date=date(2026, 6, 21),
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("5.00"))),
            Line(account_id=AccountId(12345), amount=-Money(Decimal("5.00"))),
        ),
    )
    with pytest.raises(NotFoundError):
        post_batch(migrated_conn, [good, bad], clock)
    assert JournalRepository(migrated_conn).list_all() == []
    from ledgerkit.ledger.queries import account_balance

    assert account_balance(migrated_conn, checking.id).is_zero()


def test_post_single_entry_three_lines(migrated_conn, accounts, clock):
    checking, opening = accounts
    entry = JournalEntry(
        entry_date=date(2026, 6, 21),
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("30.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("10.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("20.00"))),
        ),
    )
    posted = post(migrated_conn, entry, clock)
    assert len(posted.lines) == 3
