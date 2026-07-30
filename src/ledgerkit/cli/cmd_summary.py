"""``ledgerkit summary``: an at-a-glance view of the ledger's contents."""

from __future__ import annotations

import argparse
import sqlite3

from ledgerkit.clock import Clock
from ledgerkit.ledger.summary import build_ledger_summary


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Register the ``summary`` subcommand. It takes no arguments beyond ``--db``."""
    parser = subparsers.add_parser("summary", help="show account and entry counts")
    parser.set_defaults(handler=run)
    return parser


def run(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    summary = build_ledger_summary(connection)
    print(f"accounts: {summary.account_count} ({summary.active_account_count} active)")
    print(f"journal entries: {summary.entry_count}")
    print(f"balanced: {'yes' if summary.is_balanced else 'no'}")
    return 0
