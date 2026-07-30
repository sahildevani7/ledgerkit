from __future__ import annotations

from datetime import datetime

import pytest

from ledgerkit.clock import FixedClock
from ledgerkit.errors import StorageError
from ledgerkit.storage.engine import Engine
from ledgerkit.storage.migrations.runner import (
    ALL_MIGRATIONS,
    apply_migrations,
    current_version,
)
from ledgerkit.storage.migrations.types import Migration
from ledgerkit.storage.schema import ALL_TABLES


@pytest.fixture
def conn():
    engine = Engine(":memory:")
    return engine.connect()


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 6, 2, 20, 0, 0))


def test_fresh_db_starts_at_version_zero(conn):
    assert current_version(conn) == 0


def test_apply_migrations_returns_all_versions_in_order(conn, clock):
    applied = apply_migrations(conn, clock)
    assert applied == [1, 2, 3, 4]


def test_apply_migrations_creates_all_tables(conn, clock):
    apply_migrations(conn, clock)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    table_names = {row["name"] for row in rows}
    for table in ALL_TABLES:
        assert table in table_names


def test_current_version_after_apply(conn, clock):
    apply_migrations(conn, clock)
    assert current_version(conn) == 4


def test_second_run_is_a_no_op(conn, clock):
    apply_migrations(conn, clock)
    applied_again = apply_migrations(conn, clock)
    assert applied_again == []
    assert current_version(conn) == 4


def test_resumes_from_partial_state(conn, clock):
    first_only = tuple(m for m in ALL_MIGRATIONS if m.version == 1)
    apply_migrations(conn, clock, first_only)
    assert current_version(conn) == 1
    remaining = apply_migrations(conn, clock)
    assert remaining == [2, 3, 4]
    assert current_version(conn) == 4


def test_migration_gap_raises(conn, clock):
    gapped = (
        Migration(version=1, name="a", sql="CREATE TABLE a (id INTEGER);"),
        Migration(version=3, name="c", sql="CREATE TABLE c (id INTEGER);"),
    )
    with pytest.raises(StorageError):
        apply_migrations(conn, clock, gapped)


def test_applied_at_recorded_from_clock(conn, clock):
    apply_migrations(conn, clock)
    rows = conn.execute(
        "SELECT version, applied_at FROM schema_migrations ORDER BY version"
    ).fetchall()
    for row in rows:
        assert row["applied_at"] == clock.now().isoformat()


def test_migrations_are_contiguous_from_one():
    versions = [m.version for m in sorted(ALL_MIGRATIONS, key=lambda m: m.version)]
    assert versions == list(range(1, len(versions) + 1))


def test_migration_names_are_unique():
    names = [m.name for m in ALL_MIGRATIONS]
    assert len(names) == len(set(names))
