"""SQLite connection management.

An :class:`Engine` owns exactly one connection and hands it out to
repositories and the unit of work. Isolation level is set to ``None``
(autocommit) so transaction boundaries are always explicit — see
:mod:`ledgerkit.storage.unit_of_work`. Two pragmas are set on every new
connection: ``foreign_keys = ON`` (SQLite doesn't enforce foreign keys by
default) and a ``sqlite3.Row`` row factory, so query results support
column-name access (``row["code"]``) instead of only positional indexing.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import TracebackType

from ledgerkit.storage.pragmas import apply_pragmas
from ledgerkit.storage.unit_of_work import UnitOfWork


class Engine:
    """Owns a single SQLite connection for a given database path.

    ``Engine`` is deliberately not a connection pool — ledgerkit is a
    single-process, single-connection library, and pooling would add
    complexity for a concurrency model that doesn't exist here. Passing
    ``":memory:"`` as ``db_path`` creates a private in-memory database,
    which is what the test suite uses throughout.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._connection: sqlite3.Connection | None = None

    @property
    def db_path(self) -> str:
        return self._db_path

    @property
    def is_connected(self) -> bool:
        """Whether :meth:`connect` has been called since the last :meth:`close`."""
        return self._connection is not None

    def connect(self) -> sqlite3.Connection:
        """Return the engine's connection, opening it on first call.

        Calling this repeatedly returns the same connection object; it
        does not reopen or reset anything. This makes it safe to call from
        multiple places (each repository, the CLI's entry point) without
        coordinating who's responsible for opening the connection first.
        """
        if self._connection is None:
            conn = sqlite3.connect(self._db_path, isolation_level=None)
            apply_pragmas(conn)
            conn.row_factory = sqlite3.Row
            self._connection = conn
        return self._connection

    def close(self) -> None:
        """Close the connection, if one is open. Safe to call more than once."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def unit_of_work(self) -> UnitOfWork:
        """A new :class:`~ledgerkit.storage.unit_of_work.UnitOfWork` for this connection.

        A small convenience so callers don't need to import
        ``UnitOfWork`` and the connection separately::

            with engine.unit_of_work():
                ...
        """
        return UnitOfWork(self.connect())

    def __enter__(self) -> Engine:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
