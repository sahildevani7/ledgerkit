"""The transaction boundary every multi-write operation goes through.

A :class:`UnitOfWork` wraps a block of repository calls in a single SQLite
transaction: it commits if the block completes cleanly, and rolls back if
any exception escapes it. This is what makes batch posting atomic.
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

    def __enter__(self) -> UnitOfWork:
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
        self._active = False
        if exc_type is None:
            self._connection.execute("COMMIT")
        else:
            self._connection.execute("ROLLBACK")
