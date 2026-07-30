"""Glue between the account activity query and a renderer.

The mirror image of :mod:`ledgerkit.reporting.trial_balance_report`: looks
an account up by its human-readable code, fetches its activity, and
renders it in one call — the CLI's ``report account-activity`` command is
a thin wrapper around this single function.
"""

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
    """Look up an account by code and render its transaction history.

    Args:
        connection: An already-migrated connection.
        renderer: Anything implementing
            :class:`~ledgerkit.reporting.renderer.Renderer`.
        account_code: The account's human-readable code, not its numeric id.
        start: Restrict activity to entries dated on or after this date.
        end: Restrict activity to entries dated on or before this date.

    Raises:
        NotFoundError: If ``account_code`` doesn't match any account.
    """
    account = AccountRepository(connection).get_by_code(account_code)
    assert account.id is not None
    activity = account_activity(connection, account.id, start=start, end=end)
    return renderer.render_account_activity(account, activity)
