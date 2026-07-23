"""End-to-end coverage of the vertical slice: import, post, query, report.

These tests exercise the public library API the way an application built
on top of ledgerkit actually would, rather than one module in isolation.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import FixedClock
from ledgerkit.importers.generic_csv import GenericCsvImporter
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.posting import post, post_batch
from ledgerkit.journal.repository import JournalRepository
from ledgerkit.ledger.queries import account_activity, account_balance
from ledgerkit.ledger.trial_balance import build_trial_balance
from ledgerkit.money import Money
from ledgerkit.reporting.text import TextRenderer
from ledgerkit.reporting.trial_balance_report import render_trial_balance_report


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 7, 21, 20, 0, 0))


@pytest.fixture
def chart(migrated_conn):
    repo = AccountRepository(migrated_conn)
    checking = repo.create(Account(code="1000", name="Checking", type=AccountType.ASSET))
    savings = repo.create(Account(code="1010", name="Savings", type=AccountType.ASSET))
    opening = repo.create(Account(code="3000", name="Opening Balance", type=AccountType.EQUITY))
    groceries = repo.create(Account(code="5000", name="Groceries", type=AccountType.EXPENSE))
    salary = repo.create(Account(code="4000", name="Salary", type=AccountType.INCOME))
    return {
        "checking": checking,
        "savings": savings,
        "opening": opening,
        "groceries": groceries,
        "salary": salary,
    }


def test_opening_balance_then_report(migrated_conn, chart, clock):
    entry = JournalEntry(
        entry_date=date(2026, 7, 1),
        memo="opening balance",
        lines=(
            Line(account_id=chart["checking"].id, amount=Money(Decimal("1000.00"))),
            Line(account_id=chart["opening"].id, amount=-Money(Decimal("1000.00"))),
        ),
    )
    post(migrated_conn, entry, clock)

    assert account_balance(migrated_conn, chart["checking"].id) == Money(Decimal("1000.00"))

    tb = build_trial_balance(migrated_conn)
    assert tb.is_balanced()

    report = render_trial_balance_report(migrated_conn, TextRenderer())
    assert "1000.00 CAD" in report


def test_import_statement_then_categorize_manually(migrated_conn, chart, clock):
    csv_content = (
        "date,description,amount\n"
        "2026-07-05,Grocery Store,-85.32\n"
        "2026-07-06,Employer Payroll,2200.00\n"
    )
    transactions = GenericCsvImporter().parse(csv_content)
    entries = [
        JournalEntry(
            entry_date=txn.transaction_date,
            memo=txn.description,
            lines=(
                Line(account_id=chart["checking"].id, amount=txn.amount),
                Line(
                    account_id=(
                        chart["groceries"].id if txn.amount.is_negative() else chart["salary"].id
                    ),
                    amount=-txn.amount,
                ),
            ),
        )
        for txn in transactions
    ]
    posted = post_batch(migrated_conn, entries, clock)
    assert len(posted) == 2

    checking_balance = account_balance(migrated_conn, chart["checking"].id)
    assert checking_balance == Money(Decimal("2114.68"))

    groceries_balance = account_balance(migrated_conn, chart["groceries"].id)
    assert groceries_balance == Money(Decimal("85.32"))

    salary_balance = account_balance(migrated_conn, chart["salary"].id)
    assert salary_balance == Money(Decimal("-2200.00"))


def test_transfer_between_own_accounts_nets_to_zero_across_both(migrated_conn, chart, clock):
    seed = JournalEntry(
        entry_date=date(2026, 7, 1),
        lines=(
            Line(account_id=chart["checking"].id, amount=Money(Decimal("500.00"))),
            Line(account_id=chart["opening"].id, amount=-Money(Decimal("500.00"))),
        ),
    )
    post(migrated_conn, seed, clock)

    transfer = JournalEntry(
        entry_date=date(2026, 7, 10),
        memo="move to savings",
        lines=(
            Line(account_id=chart["checking"].id, amount=-Money(Decimal("200.00"))),
            Line(account_id=chart["savings"].id, amount=Money(Decimal("200.00"))),
        ),
    )
    post(migrated_conn, transfer, clock)

    checking_balance = account_balance(migrated_conn, chart["checking"].id)
    savings_balance = account_balance(migrated_conn, chart["savings"].id)
    assert checking_balance == Money(Decimal("300.00"))
    assert savings_balance == Money(Decimal("200.00"))
    assert checking_balance + savings_balance == Money(Decimal("500.00"))


def test_activity_history_across_accounts_stays_consistent(migrated_conn, chart, clock):
    repo = JournalRepository(migrated_conn)
    for day, amount in enumerate(("10.00", "20.00", "30.00"), start=1):
        entry = JournalEntry(
            entry_date=date(2026, 7, day),
            lines=(
                Line(account_id=chart["checking"].id, amount=Money(Decimal(amount))),
                Line(account_id=chart["opening"].id, amount=-Money(Decimal(amount))),
            ),
        )
        repo.create(entry, clock)

    checking_activity = account_activity(migrated_conn, chart["checking"].id)
    opening_activity = account_activity(migrated_conn, chart["opening"].id)
    assert len(checking_activity) == len(opening_activity) == 3

    total_in = sum((row.amount for row in checking_activity), start=Money.zero())
    total_out = sum((row.amount for row in opening_activity), start=Money.zero())
    assert total_in == -total_out


def test_trial_balance_stays_tied_through_many_postings(migrated_conn, chart, clock):
    repo = JournalRepository(migrated_conn)
    amounts = ["12.34", "56.78", "9.01", "100.00", "0.02"]
    for i, amount in enumerate(amounts):
        entry = JournalEntry(
            entry_date=date(2026, 7, 1 + i),
            lines=(
                Line(account_id=chart["checking"].id, amount=Money(Decimal(amount))),
                Line(account_id=chart["salary"].id, amount=-Money(Decimal(amount))),
            ),
        )
        repo.create(entry, clock)

    tb = build_trial_balance(migrated_conn)
    assert tb.is_balanced()
    assert tb.total_debits() == tb.total_credits()


def test_as_of_reporting_matches_manual_recomputation(migrated_conn, chart, clock):
    repo = JournalRepository(migrated_conn)
    early = JournalEntry(
        entry_date=date(2026, 6, 1),
        lines=(
            Line(account_id=chart["checking"].id, amount=Money(Decimal("100.00"))),
            Line(account_id=chart["opening"].id, amount=-Money(Decimal("100.00"))),
        ),
    )
    late = JournalEntry(
        entry_date=date(2026, 8, 1),
        lines=(
            Line(account_id=chart["checking"].id, amount=Money(Decimal("50.00"))),
            Line(account_id=chart["opening"].id, amount=-Money(Decimal("50.00"))),
        ),
    )
    repo.create(early, clock)
    repo.create(late, clock)

    as_of_july = account_balance(migrated_conn, chart["checking"].id, as_of=date(2026, 7, 31))
    assert as_of_july == Money(Decimal("100.00"))

    tb = build_trial_balance(migrated_conn, as_of=date(2026, 7, 31))
    by_code = {row.account.code: row for row in tb.rows}
    assert by_code["1000"].debit == Money(Decimal("100.00"))


def test_full_ledger_is_zero_sum_across_all_accounts(migrated_conn, chart, clock):
    entries = [
        JournalEntry(
            entry_date=date(2026, 7, 1),
            lines=(
                Line(account_id=chart["checking"].id, amount=Money(Decimal("1000.00"))),
                Line(account_id=chart["opening"].id, amount=-Money(Decimal("1000.00"))),
            ),
        ),
        JournalEntry(
            entry_date=date(2026, 7, 5),
            lines=(
                Line(account_id=chart["groceries"].id, amount=Money(Decimal("40.00"))),
                Line(account_id=chart["checking"].id, amount=-Money(Decimal("40.00"))),
            ),
        ),
        JournalEntry(
            entry_date=date(2026, 7, 10),
            lines=(
                Line(account_id=chart["checking"].id, amount=Money(Decimal("2000.00"))),
                Line(account_id=chart["salary"].id, amount=-Money(Decimal("2000.00"))),
            ),
        ),
    ]
    post_batch(migrated_conn, entries, clock)

    total = Money.zero()
    for account in chart.values():
        total = total + account_balance(migrated_conn, account.id)
    assert total.is_zero()
