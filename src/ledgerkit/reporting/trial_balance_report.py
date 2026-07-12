"""Glue between the trial balance query and a renderer."""

from __future__ import annotations

import sqlite3
from datetime import date

from ledgerkit.ledger.trial_balance import build_trial_balance
from ledgerkit.reporting.renderer import Renderer


def render_trial_balance_report(
    connection: sqlite3.Connection, renderer: Renderer, *, as_of: date | None = None
) -> str:
    trial_balance = build_trial_balance(connection, as_of=as_of)
    return renderer.render_trial_balance(trial_balance)
