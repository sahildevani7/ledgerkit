"""post() and post_batch(): the only way journal entries reach storage.

Both go through :class:`~ledgerkit.storage.unit_of_work.UnitOfWork`, so a
batch either posts completely or leaves no trace — an entry referencing an
unknown account rolls back every entry already written earlier in the same
batch. This is deliberately the *only* write path into the journal tables:
:class:`~ledgerkit.journal.repository.JournalRepository` can create a
single entry directly, but nothing calls it without going through here
first, so every posted entry has had its accounts checked against the
same transaction it's written in.
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
    """Post a single journal entry.

    Equivalent to ``post_batch(connection, [entry], clock)[0]`` — a single
    entry is just a batch of one, and gets the same atomicity guarantee.
    """
    return post_batch(connection, [entry], clock)[0]


def post_batch(
    connection: sqlite3.Connection, entries: Sequence[JournalEntry], clock: Clock
) -> list[JournalEntry]:
    """Post a sequence of journal entries as one atomic unit.

    Every line in every entry is checked against the chart of accounts
    before anything is written; the entries are written in the order
    given, and every write happens inside a single
    :class:`~ledgerkit.storage.unit_of_work.UnitOfWork`.

    Args:
        connection: An already-migrated connection.
        entries: The entries to post, in the order they should be
            written. Each must already be internally balanced —
            constructing a :class:`~ledgerkit.journal.entry.JournalEntry`
            enforces that on its own.
        clock: Supplies the ``created_at`` timestamp recorded on each
            entry.

    Returns:
        The same entries, in the same order, each with its assigned
        ``id`` and line ids filled in.

    Raises:
        NotFoundError: If any line references an account that doesn't
            exist. Nothing from this call — including entries earlier in
            ``entries`` that were already written — is persisted.
    """
    account_repo = AccountRepository(connection)
    journal_repo = JournalRepository(connection)
    posted: list[JournalEntry] = []
    with UnitOfWork(connection):
        for entry in entries:
            for line in entry.lines:
                account_repo.get(line.account_id)
            posted.append(journal_repo.create(entry, clock))
    return posted
