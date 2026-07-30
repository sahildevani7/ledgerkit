"""SQLite pragmas ledgerkit relies on, applied to every connection.

Kept separate from :class:`~ledgerkit.storage.engine.Engine` so the exact
set of pragmas — and the reason each one is there — is documented in one
place rather than as an inline `execute` call easy to skim past.
"""

from __future__ import annotations

import sqlite3


def apply_pragmas(connection: sqlite3.Connection) -> None:
    """Apply every pragma the storage layer assumes is set.

    Currently just ``foreign_keys = ON``: SQLite does not enforce foreign
    key constraints by default, and the schema relies on them actually
    being checked — an account's ``parent_id``, a journal line's
    ``account_id``, both reference rows that must exist.
    """
    connection.execute("PRAGMA foreign_keys = ON")
