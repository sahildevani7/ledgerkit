from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import FixedClock
from ledgerkit.storage.engine import Engine
from ledgerkit.storage.migrations.runner import apply_migrations


@pytest.fixture
def fixed_clock() -> FixedClock:
    return FixedClock(datetime(2026, 1, 15, 12, 0, 0))


@pytest.fixture
def migrated_conn() -> sqlite3.Connection:
    engine = Engine(":memory:")
    connection = engine.connect()
    apply_migrations(connection, FixedClock(datetime(2026, 1, 15, 12, 0, 0)))
    return connection


@pytest.fixture
def cli_db(tmp_path: Path) -> str:
    """A file-backed, migrated database seeded with a checking and an
    equity account, for exercising the CLI end to end."""
    db_path = tmp_path / "cli.db"
    engine = Engine(db_path)
    connection = engine.connect()
    apply_migrations(connection, FixedClock(datetime(2026, 1, 15, 12, 0, 0)))
    repo = AccountRepository(connection)
    repo.create(Account(code="1000", name="Checking", type=AccountType.ASSET))
    repo.create(Account(code="3000", name="Opening Balance", type=AccountType.EQUITY))
    engine.close()
    return str(db_path)
