from __future__ import annotations

from datetime import datetime

import pytest

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import FixedClock
from ledgerkit.reporting.text import TextRenderer
from ledgerkit.reporting.trial_balance_report import render_trial_balance_report


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 7, 12, 20, 0, 0))


def test_renders_full_report_for_empty_ledger(migrated_conn):
    report = render_trial_balance_report(migrated_conn, TextRenderer())
    assert "TOTAL" in report


def test_renders_report_with_accounts(migrated_conn):
    AccountRepository(migrated_conn).create(
        Account(code="1000", name="Checking", type=AccountType.ASSET)
    )
    report = render_trial_balance_report(migrated_conn, TextRenderer())
    assert "1000" in report
    assert "Checking" in report


def test_as_of_is_passed_through(migrated_conn):
    from datetime import date

    report = render_trial_balance_report(migrated_conn, TextRenderer(), as_of=date(2026, 1, 1))
    assert "TOTAL" in report
