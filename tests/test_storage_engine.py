from __future__ import annotations

import sqlite3
from pathlib import Path

from ledgerkit.storage.engine import Engine


def test_connect_returns_a_connection():
    engine = Engine(":memory:")
    conn = engine.connect()
    assert isinstance(conn, sqlite3.Connection)


def test_connect_is_idempotent():
    engine = Engine(":memory:")
    first = engine.connect()
    second = engine.connect()
    assert first is second


def test_foreign_keys_pragma_enabled():
    engine = Engine(":memory:")
    conn = engine.connect()
    (value,) = conn.execute("PRAGMA foreign_keys").fetchone()
    assert value == 1


def test_row_factory_is_row():
    engine = Engine(":memory:")
    conn = engine.connect()
    assert conn.row_factory is sqlite3.Row


def test_close_allows_reconnect_with_fresh_connection():
    engine = Engine(":memory:")
    first = engine.connect()
    engine.close()
    second = engine.connect()
    assert first is not second


def test_close_is_safe_when_never_connected():
    engine = Engine(":memory:")
    engine.close()  # should not raise


def test_context_manager_closes_on_exit():
    engine = Engine(":memory:")
    with engine as e:
        conn = e.connect()
        conn.execute("SELECT 1")
    assert engine._connection is None


def test_file_backed_db_path(tmp_path: Path):
    db_file = tmp_path / "test.db"
    engine = Engine(db_file)
    conn = engine.connect()
    conn.execute("CREATE TABLE t (id INTEGER)")
    engine.close()
    assert db_file.exists()


def test_db_path_property():
    engine = Engine("some.db")
    assert engine.db_path == "some.db"
