"""Applies numbered migrations to a connection, tracking what's been run."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence

from ledgerkit.clock import Clock
from ledgerkit.errors import StorageError
from ledgerkit.storage.migrations.migration_001_accounts import MIGRATION as MIGRATION_001
from ledgerkit.storage.migrations.migration_002_import_batches import (
    MIGRATION as MIGRATION_002,
)
from ledgerkit.storage.migrations.migration_003_journal import MIGRATION as MIGRATION_003
from ledgerkit.storage.migrations.migration_004_indexes import MIGRATION as MIGRATION_004
from ledgerkit.storage.migrations.types import Migration
from ledgerkit.storage.schema import SCHEMA_MIGRATIONS

ALL_MIGRATIONS: tuple[Migration, ...] = (
    MIGRATION_001,
    MIGRATION_002,
    MIGRATION_003,
    MIGRATION_004,
)


def ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS} ("
        "version INTEGER PRIMARY KEY, "
        "name TEXT NOT NULL, "
        "applied_at TEXT NOT NULL)"
    )


def current_version(conn: sqlite3.Connection) -> int:
    ensure_migrations_table(conn)
    row = conn.execute(f"SELECT MAX(version) FROM {SCHEMA_MIGRATIONS}").fetchone()
    version = row[0]
    return int(version) if version is not None else 0


def apply_migrations(
    conn: sqlite3.Connection,
    clock: Clock,
    migrations: Sequence[Migration] = ALL_MIGRATIONS,
) -> list[int]:
    """Apply every migration with a version greater than the current one.

    Migrations must be contiguous: applying version ``n+2`` before ``n+1``
    is a configuration error, not something to silently skip past.
    """
    ensure_migrations_table(conn)
    applied: list[int] = []
    current = current_version(conn)
    applied_at = clock.now().isoformat()

    for migration in sorted(migrations, key=lambda m: m.version):
        if migration.version <= current:
            continue
        if migration.version != current + 1:
            raise StorageError(
                f"migration gap: expected version {current + 1}, "
                f"got {migration.version} ({migration.name})"
            )
        conn.executescript(migration.sql)
        conn.execute(
            f"INSERT INTO {SCHEMA_MIGRATIONS} (version, name, applied_at) "
            "VALUES (?, ?, ?)",
            (migration.version, migration.name, applied_at),
        )
        current = migration.version
        applied.append(migration.version)

    return applied
