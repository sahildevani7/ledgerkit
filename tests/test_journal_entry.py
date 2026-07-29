from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from ledgerkit.currency import CAD
from ledgerkit.errors import UnbalancedEntryError, ValidationError
from ledgerkit.ids import AccountId
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.money import Money


def _line(account_id, amount):
    return Line(account_id=AccountId(account_id), amount=Money(Decimal(amount)))


def test_line_rejects_zero_amount():
    with pytest.raises(ValidationError):
        Line(account_id=AccountId(1), amount=Money.zero())


def test_line_is_debit_and_is_credit():
    debit = _line(1, "10.00")
    credit = _line(1, "-10.00")
    assert debit.is_debit and not debit.is_credit
    assert credit.is_credit and not credit.is_debit


def test_balanced_entry_constructs():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "10.00"), _line(2, "-10.00")),
    )
    assert entry.total().is_zero()


def test_unbalanced_entry_raises():
    with pytest.raises(UnbalancedEntryError):
        JournalEntry(
            entry_date=date(2026, 6, 20),
            lines=(_line(1, "10.00"), _line(2, "-9.00")),
        )


def test_entry_requires_at_least_two_lines():
    with pytest.raises(ValidationError):
        JournalEntry(entry_date=date(2026, 6, 20), lines=(_line(1, "10.00"),))


def test_entry_with_three_lines():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "10.00"), _line(2, "-6.00"), _line(3, "-4.00")),
    )
    assert entry.total().is_zero()


def test_debit_total_and_credit_total():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "10.00"), _line(2, "-6.00"), _line(3, "-4.00")),
    )
    assert entry.debit_total() == Money(Decimal("10.00"))
    assert entry.credit_total() == Money(Decimal("10.00"))


def test_entry_currency_mismatch_across_lines_raises():
    from ledgerkit.currency import Currency

    usd = Currency(code="USD", exponent=2)
    with pytest.raises(ValidationError):
        JournalEntry(
            entry_date=date(2026, 6, 20),
            lines=(
                Line(account_id=AccountId(1), amount=Money(Decimal("10.00"), CAD)),
                Line(account_id=AccountId(2), amount=Money(Decimal("-10.00"), usd)),
            ),
        )


def test_entry_is_frozen():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "10.00"), _line(2, "-10.00")),
    )
    with pytest.raises(AttributeError):
        entry.memo = "changed"  # type: ignore[misc]


def test_entry_memo_optional():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "10.00"), _line(2, "-10.00")),
    )
    assert entry.memo is None


def test_involves_account_true():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "10.00"), _line(2, "-10.00")),
    )
    assert entry.involves_account(AccountId(1))
    assert entry.involves_account(AccountId(2))


def test_involves_account_false():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "10.00"), _line(2, "-10.00")),
    )
    assert not entry.involves_account(AccountId(3))


def test_lines_for_account_single_match():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "10.00"), _line(2, "-10.00")),
    )
    lines = entry.lines_for_account(AccountId(1))
    assert len(lines) == 1
    assert lines[0].amount == Money(Decimal("10.00"))


def test_lines_for_account_multiple_matches():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "6.00"), _line(1, "4.00"), _line(2, "-10.00")),
    )
    lines = entry.lines_for_account(AccountId(1))
    assert len(lines) == 2


def test_lines_for_account_no_match_returns_empty_tuple():
    entry = JournalEntry(
        entry_date=date(2026, 6, 20),
        lines=(_line(1, "10.00"), _line(2, "-10.00")),
    )
    assert entry.lines_for_account(AccountId(99)) == ()
