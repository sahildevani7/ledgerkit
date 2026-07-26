"""Glue between the account activity query and a renderer."""

from __future__ import annotations

import sqlite3
from datetime import date

from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.ledger.queries import account_activity
from ledgerkit.reporting.renderer import Renderer


def render_account_activity_report(
    connection: sqlite3.Connection,
    renderer: Renderer,
    account_code: str,
    *,
    start: date | None = None,
    end: date | None = None,
) -> str:
    account = AccountRepository(connection).get_by_code(account_code)
    assert account.id is not None
    activity = account_activity(connection, account.id, start=start, end=end)
    return renderer.render_account_activity(account, activity)
