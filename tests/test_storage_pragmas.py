from __future__ import annotations

import sqlite3

from ledgerkit.storage.pragmas import apply_pragmas


def test_apply_pragmas_enables_foreign_keys():
    conn = sqlite3.connect(":memory:")
    apply_pragmas(conn)
    (value,) = conn.execute("PRAGMA foreign_keys").fetchone()
    assert value == 1


def test_foreign_keys_off_by_default_without_applying():
    conn = sqlite3.connect(":memory:")
    (value,) = conn.execute("PRAGMA foreign_keys").fetchone()
    assert value == 0
