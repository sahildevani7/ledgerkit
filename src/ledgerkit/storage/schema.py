"""Table name constants shared between migrations and repositories.

Keeping the names here (rather than as string literals scattered through the
codebase) means a rename is a one-line change and a typo is a ``NameError``
instead of a silent no-op query.
"""

from __future__ import annotations

SCHEMA_MIGRATIONS = "schema_migrations"
ACCOUNTS = "accounts"
IMPORT_BATCHES = "import_batches"
JOURNAL_ENTRIES = "journal_entries"
JOURNAL_LINES = "journal_lines"

ALL_TABLES = (ACCOUNTS, IMPORT_BATCHES, JOURNAL_ENTRIES, JOURNAL_LINES)
