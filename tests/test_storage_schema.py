from __future__ import annotations

import pytest

from ledgerkit.storage.schema import ACCOUNTS, ALL_TABLES, column_names, table_exists


def test_table_exists_true_for_migrated_table(migrated_conn):
    assert table_exists(migrated_conn, ACCOUNTS)


def test_table_exists_false_for_unknown_table(migrated_conn):
    assert not table_exists(migrated_conn, "not_a_real_table")


def test_all_tables_exist_after_migration(migrated_conn):
    for table in ALL_TABLES:
        assert table_exists(migrated_conn, table)


def test_column_names_for_accounts(migrated_conn):
    columns = column_names(migrated_conn, ACCOUNTS)
    assert columns == ["id", "code", "name", "type", "parent_id", "is_active"]


def test_column_names_rejects_unknown_table(migrated_conn):
    with pytest.raises(ValueError):
        column_names(migrated_conn, "not_a_real_table")


def test_column_names_before_migration_is_empty():
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    assert column_names(conn, ACCOUNTS) == []
