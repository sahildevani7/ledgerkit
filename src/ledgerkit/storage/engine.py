"""SQLite connection management.

An :class:`Engine` owns exactly one connection and hands it out to
repositories and the unit of work. Isolation level is set to ``None``
(autocommit) so transaction boundaries are always explicit — see
:mod:`ledgerkit.storage.unit_of_work`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import TracebackType


class Engine:
    """Owns a single SQLite connection for a given database path."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._connection: sqlite3.Connection | None = None

    @property
    def db_path(self) -> str:
        return self._db_path

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            conn = sqlite3.connect(self._db_path, isolation_level=None)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            self._connection = conn
        return self._connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

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
