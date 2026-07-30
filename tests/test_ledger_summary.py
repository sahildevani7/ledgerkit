from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import FixedClock
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.repository import JournalRepository
from ledgerkit.ledger.summary import build_ledger_summary
from ledgerkit.money import Money


def test_summary_of_empty_ledger(migrated_conn):
    summary = build_ledger_summary(migrated_conn)
    assert summary.account_count == 0
    assert summary.active_account_count == 0
    assert summary.entry_count == 0
    assert summary.is_balanced


def test_summary_counts_accounts(migrated_conn):
    repo = AccountRepository(migrated_conn)
    repo.create(Account(code="1000", name="Checking", type=AccountType.ASSET))
    a2 = repo.create(Account(code="2000", name="Loan", type=AccountType.LIABILITY))
    repo.set_active(a2.id, False)

    summary = build_ledger_summary(migrated_conn)
    assert summary.account_count == 2
    assert summary.active_account_count == 1


def test_summary_counts_entries(migrated_conn):
    repo = AccountRepository(migrated_conn)
    checking = repo.create(Account(code="1000", name="Checking", type=AccountType.ASSET))
    opening = repo.create(Account(code="3000", name="Opening", type=AccountType.EQUITY))
    entry = JournalEntry(
        entry_date=date(2026, 7, 1),
        lines=(
            Line(account_id=checking.id, amount=Money(Decimal("10.00"))),
            Line(account_id=opening.id, amount=-Money(Decimal("10.00"))),
        ),
    )
    JournalRepository(migrated_conn).create(entry, FixedClock(datetime(2026, 7, 1, 12, 0)))

    summary = build_ledger_summary(migrated_conn)
    assert summary.entry_count == 1
    assert summary.is_balanced
