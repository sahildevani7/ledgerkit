"""``ledgerkit report``: render a report.

Two report types are registered as sub-subcommands under ``report``:
``trial-balance`` and ``account-activity``. Both go through
:class:`~ledgerkit.reporting.text.TextRenderer` — the CLI is the one place
that constructs a concrete renderer; everything below it takes the
:class:`~ledgerkit.reporting.renderer.Renderer` protocol instead.
"""

from __future__ import annotations

import argparse
import sqlite3
from datetime import date

from ledgerkit.clock import Clock
from ledgerkit.reporting.account_activity_report import render_account_activity_report
from ledgerkit.reporting.text import TextRenderer
from ledgerkit.reporting.trial_balance_report import render_trial_balance_report

_EPILOG = """\
examples:
  ledgerkit --db ledger.db report trial-balance
  ledgerkit --db ledger.db report trial-balance --as-of 2026-06-30
  ledgerkit --db ledger.db report account-activity 1000 --start 2026-01-01
"""


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "report",
        help="render a report",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    report_subparsers = parser.add_subparsers(dest="report_type", required=True)

    trial_balance_parser = report_subparsers.add_parser(
        "trial-balance", help="render the trial balance"
    )
    trial_balance_parser.add_argument("--as-of", default=None, help="ISO date")
    trial_balance_parser.set_defaults(handler=run_trial_balance)

    account_activity_parser = report_subparsers.add_parser(
        "account-activity", help="render one account's transaction history"
    )
    account_activity_parser.add_argument("account_code")
    account_activity_parser.add_argument("--start", default=None, help="ISO date")
    account_activity_parser.add_argument("--end", default=None, help="ISO date")
    account_activity_parser.set_defaults(handler=run_account_activity)

    return parser


def run_trial_balance(
    args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock
) -> int:
    """Render every account's balance, split into debit and credit columns."""
    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    print(render_trial_balance_report(connection, TextRenderer(), as_of=as_of))
    return 0


def run_account_activity(
    args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock
) -> int:
    """Render one account's transaction history with a running balance.

    Raises:
        NotFoundError: If ``args.account_code`` doesn't match any account.
    """
    start = date.fromisoformat(args.start) if args.start else None
    end = date.fromisoformat(args.end) if args.end else None
    report = render_account_activity_report(
        connection, TextRenderer(), args.account_code, start=start, end=end
    )
    print(report)
    return 0
