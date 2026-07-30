#!/usr/bin/env python3
"""Seed a throwaway ledger with a small chart of accounts and some activity.

Handy for manually poking at the CLI or the library without typing out a
chart of accounts by hand every time::

    python scripts/seed_demo_ledger.py --db demo.db
    ledgerkit --db demo.db report trial-balance
    ledgerkit --db demo.db report account-activity 1000

Not part of the ``ledgerkit`` package — this is a one-off developer tool,
not something the library imports or the CLI wires up.
"""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import SystemClock
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.posting import post
from ledgerkit.ledger.trial_balance import build_trial_balance
from ledgerkit.money import Money
from ledgerkit.reporting.text import TextRenderer
from ledgerkit.storage.engine import Engine
from ledgerkit.storage.migrations.runner import apply_migrations

_CHART = [
    ("1000", "Checking", AccountType.ASSET),
    ("1010", "Savings", AccountType.ASSET),
    ("3000", "Opening Balance", AccountType.EQUITY),
    ("4000", "Salary", AccountType.INCOME),
    ("5000", "Groceries", AccountType.EXPENSE),
    ("5100", "Rent", AccountType.EXPENSE),
]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="path to the SQLite database to create")
    parser.add_argument(
        "--force", action="store_true", help="overwrite the database file if it already exists"
    )
    return parser.parse_args(argv)


def seed(db_path: Path) -> None:
    clock = SystemClock()
    engine = Engine(db_path)
    connection = engine.connect()
    apply_migrations(connection, clock)

    account_repo = AccountRepository(connection)
    accounts = {
        code: account_repo.create(Account(code=code, name=name, type=account_type))
        for code, name, account_type in _CHART
    }

    opening_entry = JournalEntry(
        entry_date=date(2026, 1, 1),
        memo="opening balance",
        lines=(
            Line(account_id=accounts["1000"].id, amount=Money(Decimal("2500.00"))),
            Line(account_id=accounts["1010"].id, amount=Money(Decimal("5000.00"))),
            Line(account_id=accounts["3000"].id, amount=-Money(Decimal("7500.00"))),
        ),
    )
    post(connection, opening_entry, clock)

    monthly_activity = [
        (date(2026, 1, 5), "5100", "1000", "1200.00", "rent"),
        (date(2026, 1, 10), "1000", "4000", "4200.00", "salary"),
        (date(2026, 1, 12), "5000", "1000", "310.45", "groceries"),
        (date(2026, 1, 26), "5000", "1000", "88.20", "groceries"),
    ]
    for entry_date, debit_code, credit_code, amount, memo in monthly_activity:
        entry = JournalEntry(
            entry_date=entry_date,
            memo=memo,
            lines=(
                Line(account_id=accounts[debit_code].id, amount=Money(Decimal(amount))),
                Line(account_id=accounts[credit_code].id, amount=-Money(Decimal(amount))),
            ),
        )
        post(connection, entry, clock)

    engine.close()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    db_path = Path(args.db)
    if db_path.exists():
        if not args.force:
            print(f"{db_path} already exists; pass --force to overwrite")
            return 1
        db_path.unlink()

    seed(db_path)

    engine = Engine(db_path)
    connection = engine.connect()
    print(f"seeded {db_path} with {len(_CHART)} accounts")
    print(TextRenderer().render_trial_balance(build_trial_balance(connection)))
    engine.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
