"""Migration 004: indexes for the query paths the ledger actually uses."""

from __future__ import annotations

from ledgerkit.storage.migrations.types import Migration

SQL = """
CREATE INDEX idx_accounts_parent_id ON accounts(parent_id);
CREATE INDEX idx_journal_lines_account_id ON journal_lines(account_id);
CREATE INDEX idx_journal_lines_entry_id ON journal_lines(entry_id);
CREATE INDEX idx_journal_entries_entry_date ON journal_entries(entry_date);
"""

MIGRATION = Migration(version=4, name="add lookup indexes", sql=SQL)
