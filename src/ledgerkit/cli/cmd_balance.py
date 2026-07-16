"""``ledgerkit balance``: print an account's balance."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import date

from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import Clock
from ledgerkit.ledger.queries import account_balance


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("balance", help="show an account's balance")
    parser.add_argument("account_code")
    parser.add_argument("--as-of", default=None, help="ISO date; defaults to all activity")
    parser.set_defaults(handler=run)
    return parser


def run(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    account = AccountRepository(connection).get_by_code(args.account_code)
    assert account.id is not None
    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    balance = account_balance(connection, account.id, as_of=as_of)
    print(balance.format())
    return 0
