"""Migration 001: the chart of accounts table."""

from __future__ import annotations

from ledgerkit.storage.migrations.types import Migration

SQL = """
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    parent_id INTEGER REFERENCES accounts(id),
    is_active INTEGER NOT NULL DEFAULT 1
);
"""

MIGRATION = Migration(version=1, name="create accounts table", sql=SQL)
