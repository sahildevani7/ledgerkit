"""``ledgerkit post``: post a manual journal entry from the command line."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation

from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import Clock
from ledgerkit.errors import ValidationError
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.posting import post as post_entry
from ledgerkit.money import Money


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("post", help="post a manual journal entry")
    parser.add_argument(
        "--debit", action="append", default=[], metavar="CODE:AMOUNT", required=True
    )
    parser.add_argument(
        "--credit", action="append", default=[], metavar="CODE:AMOUNT", required=True
    )
    parser.add_argument("--entry-date", default=None, help="ISO date; defaults to today")
    parser.add_argument("--memo", default=None)
    parser.set_defaults(handler=run)
    return parser


def _parse_spec(spec: str) -> tuple[str, Decimal]:
    code, sep, amount_str = spec.partition(":")
    if not sep:
        raise ValidationError(f"expected CODE:AMOUNT, got {spec!r}")
    try:
        amount = Decimal(amount_str)
    except InvalidOperation as exc:
        raise ValidationError(f"invalid amount in {spec!r}") from exc
    return code, amount


def run(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    account_repo = AccountRepository(connection)
    lines: list[Line] = []
    for spec in args.debit:
        code, amount = _parse_spec(spec)
        account = account_repo.get_by_code(code)
        assert account.id is not None
        lines.append(Line(account_id=account.id, amount=Money(amount)))
    for spec in args.credit:
        code, amount = _parse_spec(spec)
        account = account_repo.get_by_code(code)
        assert account.id is not None
        lines.append(Line(account_id=account.id, amount=-Money(amount)))

    entry_date = date.fromisoformat(args.entry_date) if args.entry_date else clock.today()
    entry = JournalEntry(entry_date=entry_date, lines=tuple(lines), memo=args.memo)
    posted = post_entry(connection, entry, clock)
    print(f"posted entry {posted.id}")
    return 0
