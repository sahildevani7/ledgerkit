"""Glue between the trial balance query and a renderer.

This module exists so callers — the CLI's ``report trial-balance``
command today — depend on one function rather than needing to know that
building a trial balance and rendering it are two separate steps
(:func:`~ledgerkit.ledger.trial_balance.build_trial_balance` and
:meth:`~ledgerkit.reporting.renderer.Renderer.render_trial_balance`).
"""

from __future__ import annotations

import sqlite3
from datetime import date

from ledgerkit.ledger.trial_balance import build_trial_balance
from ledgerkit.reporting.renderer import Renderer


def render_trial_balance_report(
    connection: sqlite3.Connection, renderer: Renderer, *, as_of: date | None = None
) -> str:
    """Build the trial balance and render it in one call.

    Args:
        connection: An already-migrated connection.
        renderer: Anything implementing
            :class:`~ledgerkit.reporting.renderer.Renderer` —
            :class:`~ledgerkit.reporting.text.TextRenderer` is the one
            shipped today.
        as_of: Restrict the balance to activity on or before this date;
            omit for the balance across all posted activity.
    """
    trial_balance = build_trial_balance(connection, as_of=as_of)
    return renderer.render_trial_balance(trial_balance)
