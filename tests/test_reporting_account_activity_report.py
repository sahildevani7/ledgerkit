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
from ledgerkit.money import Money
from ledgerkit.reporting.account_activity_report import render_account_activity_report
from ledgerkit.reporting.text import TextRenderer


@pytest.fixture
def accounts(migrated_conn):
    repo = AccountRepository(migrated_conn)
    checking = repo.create(Account(code="1000", name="Checking", type=AccountType.ASSET))
    opening = repo.create(Account(code="3000", name="Opening Balance", type=AccountType.EQUITY))
    return checking, opening


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 7, 25, 20, 0, 0))


def test_renders_empty_activity(migrated_conn, accounts):
    report = render_account_activity_report(migrated_conn, TextRenderer(), "1000")
    assert "Checking" in report


def test_renders_posted_activity(migrated_conn, accounts, clock):
    checking, opening = accounts
    entry = JournalEntry(
        entry_date=date(2026, 7, 1),
        memo="opening",
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("100.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("100.00"))),
        ),
    )
    JournalRepository(migrated_conn).create(entry, clock)
    report = render_account_activity_report(migrated_conn, TextRenderer(), "1000")
    assert "100.00" in report
    assert "opening" in report


def test_unknown_account_raises(migrated_conn):
    with pytest.raises(NotFoundError):
        render_account_activity_report(migrated_conn, TextRenderer(), "no-such-code")


def test_date_range_filters_activity(migrated_conn, accounts, clock):
    checking, opening = accounts
    repo = JournalRepository(migrated_conn)
    for day, amount in ((1, "10.00"), (15, "20.00")):
        entry = JournalEntry(
            entry_date=date(2026, 7, day),
            lines=(
                Line(account_id=checking.id, amount=Money(Decimal(amount))),
                Line(account_id=opening.id, amount=-Money(Decimal(amount))),
            ),
        )
        repo.create(entry, clock)
    report = render_account_activity_report(
        migrated_conn, TextRenderer(), "1000", start=date(2026, 7, 10)
    )
    assert "20.00" in report
