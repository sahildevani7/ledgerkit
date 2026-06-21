"""post() and post_batch(): the only way journal entries reach storage.

Both go through :class:`~ledgerkit.storage.unit_of_work.UnitOfWork`, so a
batch either posts completely or leaves no trace — an entry referencing an
unknown account rolls back every entry already written earlier in the same
batch.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence

from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import Clock
from ledgerkit.journal.entry import JournalEntry
from ledgerkit.journal.repository import JournalRepository
from ledgerkit.storage.unit_of_work import UnitOfWork


def post(connection: sqlite3.Connection, entry: JournalEntry, clock: Clock) -> JournalEntry:
    """Post a single journal entry."""
    return post_batch(connection, [entry], clock)[0]


def post_batch(
    connection: sqlite3.Connection, entries: Sequence[JournalEntry], clock: Clock
) -> list[JournalEntry]:
    """Post a sequence of journal entries as one atomic unit."""
    account_repo = AccountRepository(connection)
    journal_repo = JournalRepository(connection)
    posted: list[JournalEntry] = []
    with UnitOfWork(connection):
        for entry in entries:
            for line in entry.lines:
                account_repo.get(line.account_id)
            posted.append(journal_repo.create(entry, clock))
    return posted
