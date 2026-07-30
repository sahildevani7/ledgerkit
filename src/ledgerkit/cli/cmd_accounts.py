"""``ledgerkit accounts``: manage the chart of accounts from the command line.

The library exposes account creation and hierarchy management through
:class:`~ledgerkit.accounts.repository.AccountRepository` directly; this
module is a thin CLI wrapper around the same operations, so setting up a
chart of accounts doesn't require writing a Python script.
"""

from __future__ import annotations

import argparse
import sqlite3

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import Clock

_TYPE_CHOICES = tuple(t.value for t in AccountType)


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("accounts", help="manage the chart of accounts")
    account_subparsers = parser.add_subparsers(dest="accounts_command", required=True)

    list_parser = account_subparsers.add_parser("list", help="list accounts")
    list_parser.add_argument(
        "--include-inactive", action="store_true", help="also list deactivated accounts"
    )
    list_parser.set_defaults(handler=run_list)

    create_parser = account_subparsers.add_parser("create", help="create a new account")
    create_parser.add_argument("code")
    create_parser.add_argument("name")
    create_parser.add_argument("type", choices=_TYPE_CHOICES)
    create_parser.add_argument("--parent", default=None, help="parent account code")
    create_parser.set_defaults(handler=run_create)

    reparent_parser = account_subparsers.add_parser(
        "reparent", help="move an account under a new parent"
    )
    reparent_parser.add_argument("code")
    reparent_parser.add_argument(
        "--parent", default=None, help="new parent code; omit to make it a root account"
    )
    reparent_parser.set_defaults(handler=run_reparent)

    deactivate_parser = account_subparsers.add_parser(
        "deactivate", help="mark an account inactive"
    )
    deactivate_parser.add_argument("code")
    deactivate_parser.set_defaults(handler=run_deactivate)

    activate_parser = account_subparsers.add_parser("activate", help="mark an account active")
    activate_parser.add_argument("code")
    activate_parser.set_defaults(handler=run_activate)

    show_parser = account_subparsers.add_parser(
        "show", help="show one account's details, path, and children"
    )
    show_parser.add_argument("code")
    show_parser.set_defaults(handler=run_show)

    return parser


def run_list(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    repo = AccountRepository(connection)
    accounts = repo.list_all()
    if not args.include_inactive:
        accounts = [account for account in accounts if account.is_active]
    for account in accounts:
        parent_note = ""
        if account.parent_id is not None:
            parent_note = f" (parent: {repo.get(account.parent_id).code})"
        status_note = "" if account.is_active else " [inactive]"
        print(f"{account.code}\t{account.name}\t{account.type.value}{parent_note}{status_note}")
    return 0


def run_create(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    repo = AccountRepository(connection)
    parent_id = repo.get_by_code(args.parent).id if args.parent is not None else None
    account = repo.create(
        Account(code=args.code, name=args.name, type=AccountType(args.type), parent_id=parent_id)
    )
    print(f"created account {account.code} ({account.id})")
    return 0


def run_reparent(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    repo = AccountRepository(connection)
    account = repo.get_by_code(args.code)
    assert account.id is not None
    new_parent_id = repo.get_by_code(args.parent).id if args.parent is not None else None
    repo.reparent(account.id, new_parent_id)
    print(f"reparented {account.code}")
    return 0


def run_deactivate(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    repo = AccountRepository(connection)
    account = repo.get_by_code(args.code)
    assert account.id is not None
    repo.set_active(account.id, False)
    print(f"deactivated {account.code}")
    return 0


def run_activate(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    repo = AccountRepository(connection)
    account = repo.get_by_code(args.code)
    assert account.id is not None
    repo.set_active(account.id, True)
    print(f"activated {account.code}")
    return 0


def run_show(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    repo = AccountRepository(connection)
    account = repo.get_by_code(args.code)
    assert account.id is not None
    chart = repo.chart()

    path = " > ".join(a.name for a in chart.path_to(account.id))
    children = chart.children_of(account.id)
    status = "active" if account.is_active else "inactive"

    print(f"{account.display_label} ({account.type.value}, {status})")
    print(f"path: {path}")
    if children:
        print("children:")
        for child in children:
            print(f"  {child.display_label}")
    else:
        print("children: none")
    return 0
