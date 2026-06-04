"""Migration 003: journal entries and their lines.

A line's ``amount`` is signed relative to the debit/credit convention:
positive is a debit, negative is a credit. An entry balances exactly when
its lines' amounts sum to zero. Amounts are stored as text (a canonical
decimal string) rather than a numeric type, since SQLite has no exact
decimal column type.
"""

from __future__ import annotations

from ledgerkit.storage.migrations.types import Migration

SQL = """
CREATE TABLE journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT NOT NULL,
    memo TEXT,
    created_at TEXT NOT NULL,
    import_batch_id INTEGER REFERENCES import_batches(id)
);

CREATE TABLE journal_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL REFERENCES journal_entries(id),
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    amount TEXT NOT NULL,
    currency_code TEXT NOT NULL
);
"""

MIGRATION = Migration(version=3, name="create journal_entries and journal_lines tables", sql=SQL)
