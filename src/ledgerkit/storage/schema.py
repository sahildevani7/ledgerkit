"""Table name constants, plus small introspection helpers over ``sqlite_master``.

Table names live here (rather than as string literals scattered through the
codebase) so a rename is a one-line change and a typo is a ``NameError``
instead of a silent no-op query. The introspection helpers exist for
diagnostics and tests that need to assert on the shape of the schema
without hand-rolling a ``PRAGMA`` query each time.
"""

from __future__ import annotations

import sqlite3

SCHEMA_MIGRATIONS = "schema_migrations"
ACCOUNTS = "accounts"
IMPORT_BATCHES = "import_batches"
JOURNAL_ENTRIES = "journal_entries"
JOURNAL_LINES = "journal_lines"

#: Every table ledgerkit's migrations create, in creation order.
ALL_TABLES = (ACCOUNTS, IMPORT_BATCHES, JOURNAL_ENTRIES, JOURNAL_LINES)


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    """Whether a table named ``table_name`` exists in the database."""
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table_name,)
    ).fetchone()
    return row is not None


def column_names(connection: sqlite3.Connection, table_name: str) -> list[str]:
    """The column names of ``table_name``, in table definition order.

    Returns an empty list if the table doesn't exist, rather than raising —
    callers that want existence checked separately should call
    :func:`table_exists` first.

    ``PRAGMA`` statements don't support bound parameters in SQLite, so
    ``table_name`` is restricted to ledgerkit's own known tables rather
    than interpolated directly into SQL from arbitrary input.
    """
    known_tables = (*ALL_TABLES, SCHEMA_MIGRATIONS)
    if table_name not in known_tables:
        raise ValueError(f"unknown table: {table_name!r}")
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row["name"] for row in rows]
