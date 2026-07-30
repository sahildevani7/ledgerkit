"""``ledgerkit post``: post a manual journal entry from the command line.

``--debit`` and ``--credit`` each take one ``CODE:AMOUNT`` pair and can be
repeated to build a multi-line entry — the CLI equivalent of constructing
several :class:`~ledgerkit.journal.entry.Line` objects by hand. The lines
still have to balance; that's enforced by
:class:`~ledgerkit.journal.entry.JournalEntry` itself; this module doesn't
duplicate the check.
"""

from __future__ import annotations

import argparse
import sqlite3
from decimal import Decimal, InvalidOperation

from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.cli._common import parse_optional_date
from ledgerkit.clock import Clock
from ledgerkit.errors import ValidationError
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.posting import post as post_entry
from ledgerkit.money import Money

_EPILOG = """\
examples:
  ledgerkit --db ledger.db post --debit 1000:100.00 --credit 3000:100.00
  ledgerkit --db ledger.db post \\
      --debit 5000:60.00 --debit 5000:40.00 --credit 1000:100.00 \\
      --entry-date 2026-07-01 --memo "groceries, split receipt"
"""


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Register the ``post`` subcommand and its arguments."""
    parser = subparsers.add_parser(
        "post",
        help="post a manual journal entry",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--debit",
        action="append",
        default=[],
        metavar="CODE:AMOUNT",
        required=True,
        help="a debit line; repeat for more than one",
    )
    parser.add_argument(
        "--credit",
        action="append",
        default=[],
        metavar="CODE:AMOUNT",
        required=True,
        help="a credit line; repeat for more than one",
    )
    parser.add_argument("--entry-date", default=None, help="ISO date; defaults to today")
    parser.add_argument("--memo", default=None, help="a free-text note for the entry")
    parser.set_defaults(handler=run)
    return parser


def _parse_spec(spec: str) -> tuple[str, Decimal]:
    """Split a ``CODE:AMOUNT`` argument into its account code and amount.

    Raises:
        ValidationError: If ``spec`` has no ``:`` separator, or the part
            after it isn't a valid decimal.
    """
    code, sep, amount_str = spec.partition(":")
    if not sep:
        raise ValidationError(f"expected CODE:AMOUNT, got {spec!r}")
    try:
        amount = Decimal(amount_str)
    except InvalidOperation as exc:
        raise ValidationError(f"invalid amount in {spec!r}") from exc
    return code, amount


def run(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    """Build a journal entry from ``--debit``/``--credit`` arguments and post it.

    Raises:
        ValidationError: If a ``CODE:AMOUNT`` argument is malformed, or if
            the resulting entry doesn't balance
            (:class:`~ledgerkit.errors.UnbalancedEntryError`, a subclass).
        NotFoundError: If a referenced account code doesn't exist.
    """
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

    entry_date = parse_optional_date(args.entry_date) or clock.today()
    entry = JournalEntry(entry_date=entry_date, lines=tuple(lines), memo=args.memo)
    posted = post_entry(connection, entry, clock)
    print(f"posted entry {posted.id}")
    return 0
