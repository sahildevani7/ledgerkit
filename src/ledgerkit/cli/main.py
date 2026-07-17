"""The ``ledgerkit`` command-line entry point.

The database at ``--db`` is created and migrated automatically before any
subcommand runs — there's no separate init step.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from ledgerkit.cli import cmd_balance, cmd_import, cmd_post, cmd_report
from ledgerkit.clock import SystemClock
from ledgerkit.errors import LedgerError
from ledgerkit.storage.engine import Engine
from ledgerkit.storage.migrations.runner import apply_migrations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ledgerkit", description="A double-entry accounting engine"
    )
    parser.add_argument("--db", default="ledger.db", help="path to the SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)
    cmd_import.add_arguments(subparsers)
    cmd_post.add_arguments(subparsers)
    cmd_balance.add_arguments(subparsers)
    cmd_report.add_arguments(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
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
