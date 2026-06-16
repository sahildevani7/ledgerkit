from __future__ import annotations

import sqlite3
from datetime import datetime

import pytest

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
