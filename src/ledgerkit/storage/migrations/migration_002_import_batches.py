"""Migration 002: import batch provenance table."""

from __future__ import annotations

from ledgerkit.storage.migrations.types import Migration

SQL = """
CREATE TABLE import_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    source_name TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL
);
"""

MIGRATION = Migration(version=2, name="create import_batches table", sql=SQL)
