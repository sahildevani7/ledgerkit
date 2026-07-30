"""The ``ledgerkit`` command-line entry point.

The database at ``--db`` is created and migrated automatically before any
subcommand runs — there's no separate init step. Every subcommand module
(``cmd_accounts``, ``cmd_import``, ``cmd_post``, ``cmd_balance``,
``cmd_report``) exposes an ``add_arguments(subparsers)`` function that
registers its own parser and a ``handler`` default, and a matching
``run*(args, connection, clock)`` function that does the actual work. This
module's job is limited to wiring those together, opening the database,
and translating a raised :class:`~ledgerkit.errors.LedgerError` into a
clean exit code instead of a traceback.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version

from ledgerkit.cli import cmd_accounts, cmd_balance, cmd_import, cmd_post, cmd_report
from ledgerkit.clock import SystemClock
from ledgerkit.errors import LedgerError
from ledgerkit.storage.engine import Engine
from ledgerkit.storage.migrations.runner import apply_migrations


def _package_version() -> str:
    try:
        return version("ledgerkit")
    except PackageNotFoundError:
        return "unknown"


_EPILOG = """\
commands:
  accounts   manage the chart of accounts
  import     import a bank statement and post it
  post       post a manual journal entry
  balance    show an account's balance
  report     render a trial balance or an account's activity

run `ledgerkit <command> --help` for a command's own options and examples.
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with every subcommand registered."""
    parser = argparse.ArgumentParser(
        prog="ledgerkit",
        description="A double-entry accounting engine",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"ledgerkit {_package_version()}")
    parser.add_argument("--db", default="ledger.db", help="path to the SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)
    cmd_accounts.add_arguments(subparsers)
    cmd_import.add_arguments(subparsers)
    cmd_post.add_arguments(subparsers)
    cmd_balance.add_arguments(subparsers)
    cmd_report.add_arguments(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, open the database, and dispatch to the chosen subcommand.

    Returns:
        ``0`` on success, ``1`` if a :class:`~ledgerkit.errors.LedgerError`
        was raised while handling the command (the message is printed to
        stderr). Argument-parsing failures exit through argparse's own
        mechanism before this function returns anything, using argparse's
        conventional exit code of ``2``.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    clock = SystemClock()
    engine = Engine(args.db)
    try:
        connection = engine.connect()
        apply_migrations(connection, clock)
        handler = args.handler
        return int(handler(args, connection, clock))
    except LedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.close()


if __name__ == "__main__":
    sys.exit(main())
