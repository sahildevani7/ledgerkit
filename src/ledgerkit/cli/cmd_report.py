"""``ledgerkit report``: render a report."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import date

from ledgerkit.clock import Clock
from ledgerkit.reporting.account_activity_report import render_account_activity_report
from ledgerkit.reporting.text import TextRenderer
from ledgerkit.reporting.trial_balance_report import render_trial_balance_report


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("report", help="render a report")
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
    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    print(render_trial_balance_report(connection, TextRenderer(), as_of=as_of))
    return 0


def run_account_activity(
    args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock
) -> int:
    start = date.fromisoformat(args.start) if args.start else None
    end = date.fromisoformat(args.end) if args.end else None
    report = render_account_activity_report(
        connection, TextRenderer(), args.account_code, start=start, end=end
    )
    print(report)
    return 0
