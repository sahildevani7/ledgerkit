"""The transaction boundary every multi-write operation goes through.

A :class:`UnitOfWork` wraps a block of repository calls in a single SQLite
transaction: it commits if the block completes cleanly, and rolls back if
any exception escapes it. This is what makes batch posting atomic —
:func:`~ledgerkit.journal.posting.post_batch` opens one ``UnitOfWork``
around every entry it writes, so a failure on the last entry undoes every
entry already written earlier in the same call.

A ``UnitOfWork`` is single-use per ``with`` block: it can't be entered
again while already active, since SQLite doesn't support nesting a
``BEGIN`` inside another open transaction on the same connection. The same
instance can be reused across separate, sequential ``with`` blocks,
though — nothing about it is consumed by one use.
"""

from __future__ import annotations

import sqlite3
from types import TracebackType

from ledgerkit.errors import StorageError


class UnitOfWork:
    """A single transaction boundary around a SQLite connection."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._active = False

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    @property
    def is_active(self) -> bool:
        """Whether this unit of work currently has an open transaction."""
        return self._active

    def __enter__(self) -> UnitOfWork:
        """Begin the transaction.

        Raises:
            StorageError: If this unit of work is already inside an open
                transaction — reentering it would try to nest a ``BEGIN``,
                which SQLite doesn't support on a single connection.
        """
        if self._active:
            raise StorageError("unit of work is already active")
        self._connection.execute("BEGIN")
        self._active = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """End the transaction: commit on a clean exit, roll back otherwise."""
        self._active = False
        if exc_type is None:
            self._connection.execute("COMMIT")
        else:
            self._connection.execute("ROLLBACK")
