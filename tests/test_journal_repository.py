from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import FixedClock
from ledgerkit.errors import NotFoundError, ValidationError
from ledgerkit.ids import EntryId
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.repository import JournalRepository
from ledgerkit.money import Money


@pytest.fixture
def accounts(migrated_conn):
    repo = AccountRepository(migrated_conn)
    checking = repo.create(Account(code="1000", name="Checking", type=AccountType.ASSET))
    opening = repo.create(Account(code="3000", name="Opening Balance", type=AccountType.EQUITY))
    return checking, opening


@pytest.fixture
def repo(migrated_conn):
    return JournalRepository(migrated_conn)


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 6, 20, 21, 0, 0))


def _entry(checking, opening, amount="100.00", entry_date=date(2026, 6, 20), memo="opening"):
    return JournalEntry(
        entry_date=entry_date,
        memo=memo,
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal(amount))),
            Line(account_id=opening.id, amount=-Money(Decimal(amount))),
        ),
    )


def test_create_assigns_ids(repo, accounts, clock):
    checking, opening = accounts
    created = repo.create(_entry(checking, opening), clock)
    assert created.id is not None
    assert all(line.id is not None for line in created.lines)


def test_create_records_created_at_from_clock(repo, accounts, clock):
    checking, opening = accounts
    created = repo.create(_entry(checking, opening), clock)
    assert created.created_at == clock.now()


def test_create_rejects_entry_with_id(repo, accounts, clock):
    checking, opening = accounts
    entry = _entry(checking, opening)
    from dataclasses import replace

    with_id = replace(entry, id=EntryId(1))
    with pytest.raises(ValidationError):
        repo.create(with_id, clock)


def test_get_round_trips(repo, accounts, clock):
    checking, opening = accounts
    created = repo.create(_entry(checking, opening), clock)
    fetched = repo.get(created.id)
    assert fetched == created


def test_get_missing_raises(repo):
    with pytest.raises(NotFoundError):
        repo.get(999)  # type: ignore[arg-type]


def test_get_preserves_line_order(repo, accounts, clock):
    checking, opening = accounts
    created = repo.create(_entry(checking, opening), clock)
    fetched = repo.get(created.id)
    assert [line.account_id for line in fetched.lines] == [
        line.account_id for line in created.lines
    ]


def test_list_all_sorted_by_date_then_id(repo, accounts, clock):
    checking, opening = accounts
    first = repo.create(_entry(checking, opening, entry_date=date(2026, 6, 21)), clock)
    second = repo.create(_entry(checking, opening, entry_date=date(2026, 6, 20)), clock)
    entries = repo.list_all()
    assert [e.id for e in entries] == [second.id, first.id]


def test_list_all_filters_by_start(repo, accounts, clock):
    checking, opening = accounts
    repo.create(_entry(checking, opening, entry_date=date(2026, 6, 1)), clock)
    later = repo.create(_entry(checking, opening, entry_date=date(2026, 6, 20)), clock)
    entries = repo.list_all(start=date(2026, 6, 10))
    assert [e.id for e in entries] == [later.id]


def test_list_all_filters_by_end(repo, accounts, clock):
    checking, opening = accounts
    early = repo.create(_entry(checking, opening, entry_date=date(2026, 6, 1)), clock)
    repo.create(_entry(checking, opening, entry_date=date(2026, 6, 20)), clock)
    entries = repo.list_all(end=date(2026, 6, 10))
    assert [e.id for e in entries] == [early.id]


def test_list_all_filters_by_range(repo, accounts, clock):
    checking, opening = accounts
    repo.create(_entry(checking, opening, entry_date=date(2026, 6, 1)), clock)
    mid = repo.create(_entry(checking, opening, entry_date=date(2026, 6, 10)), clock)
    repo.create(_entry(checking, opening, entry_date=date(2026, 6, 20)), clock)
    entries = repo.list_all(start=date(2026, 6, 5), end=date(2026, 6, 15))
    assert [e.id for e in entries] == [mid.id]


def test_memo_round_trips(repo, accounts, clock):
    checking, opening = accounts
    created = repo.create(_entry(checking, opening, memo="test memo"), clock)
    assert repo.get(created.id).memo == "test memo"


def test_import_batch_id_defaults_to_none(repo, accounts, clock):
    checking, opening = accounts
    created = repo.create(_entry(checking, opening), clock)
    assert created.import_batch_id is None
