from __future__ import annotations

from datetime import datetime

import pytest

from ledgerkit.clock import FixedClock
from ledgerkit.errors import StorageError
from ledgerkit.storage.engine import Engine
from ledgerkit.storage.migrations.runner import apply_migrations
from ledgerkit.storage.unit_of_work import UnitOfWork


@pytest.fixture
def conn():
    engine = Engine(":memory:")
    connection = engine.connect()
    apply_migrations(connection, FixedClock(datetime(2026, 6, 3, 19, 0, 0)))
    return connection


def _insert_account(conn, code: str) -> None:
    conn.execute(
        "INSERT INTO accounts (code, name, type) VALUES (?, ?, ?)",
        (code, code, "asset"),
    )


def test_commits_on_clean_exit(conn):
    with UnitOfWork(conn):
        _insert_account(conn, "1000")
    rows = conn.execute("SELECT code FROM accounts").fetchall()
    assert [r["code"] for r in rows] == ["1000"]


def test_rolls_back_on_exception(conn):
    with pytest.raises(ValueError):
        with UnitOfWork(conn):
            _insert_account(conn, "1000")
            raise ValueError("boom")
    rows = conn.execute("SELECT code FROM accounts").fetchall()
    assert rows == []


def test_exception_propagates_after_rollback(conn):
    with pytest.raises(ValueError, match="boom"):
        with UnitOfWork(conn):
            raise ValueError("boom")


def test_reentry_while_active_raises(conn):
    uow = UnitOfWork(conn)
    with uow:
        with pytest.raises(StorageError):
            uow.__enter__()


def test_can_reuse_after_clean_exit(conn):
    uow = UnitOfWork(conn)
    with uow:
        _insert_account(conn, "1000")
    with uow:
        _insert_account(conn, "2000")
    rows = conn.execute("SELECT code FROM accounts ORDER BY code").fetchall()
    assert [r["code"] for r in rows] == ["1000", "2000"]


def test_connection_property(conn):
    uow = UnitOfWork(conn)
    assert uow.connection is conn


def test_partial_batch_rolls_back_entirely(conn):
    with pytest.raises(ValueError):
        with UnitOfWork(conn):
            _insert_account(conn, "1000")
            _insert_account(conn, "2000")
            raise ValueError("abort batch")
    rows = conn.execute("SELECT code FROM accounts").fetchall()
    assert rows == []


def test_is_active_false_before_entering(conn):
    uow = UnitOfWork(conn)
    assert not uow.is_active


def test_is_active_true_inside_block(conn):
    uow = UnitOfWork(conn)
    with uow:
        assert uow.is_active


def test_is_active_false_after_clean_exit(conn):
    uow = UnitOfWork(conn)
    with uow:
        pass
    assert not uow.is_active


def test_is_active_false_after_exception(conn):
    uow = UnitOfWork(conn)
    with pytest.raises(ValueError):
        with uow:
            raise ValueError("boom")
    assert not uow.is_active
