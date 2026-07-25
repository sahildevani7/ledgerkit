from __future__ import annotations

from pathlib import Path

import pytest

from ledgerkit.cli.main import main


@pytest.fixture
def fresh_db(tmp_path: Path) -> str:
    return str(tmp_path / "accounts.db")


def test_create_account(fresh_db, capsys):
    exit_code = main(["--db", fresh_db, "accounts", "create", "1000", "Checking", "asset"])
    assert exit_code == 0
    assert "created account 1000" in capsys.readouterr().out


def test_create_duplicate_code_returns_exit_code_one(fresh_db):
    main(["--db", fresh_db, "accounts", "create", "1000", "Checking", "asset"])
    exit_code = main(["--db", fresh_db, "accounts", "create", "1000", "Other", "asset"])
    assert exit_code == 1


def test_create_rejects_bad_type(fresh_db):
    with pytest.raises(SystemExit):
        main(["--db", fresh_db, "accounts", "create", "1000", "Checking", "not-a-type"])


def test_create_with_parent(fresh_db, capsys):
    main(["--db", fresh_db, "accounts", "create", "1000", "Assets", "asset"])
    exit_code = main(
        ["--db", fresh_db, "accounts", "create", "1100", "Cash", "asset", "--parent", "1000"]
    )
    assert exit_code == 0


def test_create_with_missing_parent_returns_exit_code_one(fresh_db):
    exit_code = main(
        ["--db", fresh_db, "accounts", "create", "1100", "Cash", "asset", "--parent", "9999"]
    )
    assert exit_code == 1


def test_list_shows_created_accounts(fresh_db, capsys):
    main(["--db", fresh_db, "accounts", "create", "1000", "Checking", "asset"])
    capsys.readouterr()
    main(["--db", fresh_db, "accounts", "list"])
    output = capsys.readouterr().out
    assert "1000" in output
    assert "Checking" in output


def test_list_excludes_inactive_by_default(fresh_db, capsys):
    main(["--db", fresh_db, "accounts", "create", "1000", "Checking", "asset"])
    main(["--db", fresh_db, "accounts", "deactivate", "1000"])
    capsys.readouterr()
    main(["--db", fresh_db, "accounts", "list"])
    assert "1000" not in capsys.readouterr().out


def test_list_include_inactive_shows_deactivated(fresh_db, capsys):
    main(["--db", fresh_db, "accounts", "create", "1000", "Checking", "asset"])
    main(["--db", fresh_db, "accounts", "deactivate", "1000"])
    capsys.readouterr()
    main(["--db", fresh_db, "accounts", "list", "--include-inactive"])
    output = capsys.readouterr().out
    assert "1000" in output
    assert "[inactive]" in output


def test_list_shows_parent_note(fresh_db, capsys):
    main(["--db", fresh_db, "accounts", "create", "1000", "Assets", "asset"])
    main(["--db", fresh_db, "accounts", "create", "1100", "Cash", "asset", "--parent", "1000"])
    capsys.readouterr()
    main(["--db", fresh_db, "accounts", "list"])
    output = capsys.readouterr().out
    assert "parent: 1000" in output


def test_reparent_moves_account(fresh_db):
    main(["--db", fresh_db, "accounts", "create", "1000", "A", "asset"])
    main(["--db", fresh_db, "accounts", "create", "2000", "B", "liability"])
    main(["--db", fresh_db, "accounts", "create", "1100", "C", "asset", "--parent", "1000"])
    exit_code = main(["--db", fresh_db, "accounts", "reparent", "1100", "--parent", "2000"])
    assert exit_code == 0


def test_reparent_to_root(fresh_db):
    main(["--db", fresh_db, "accounts", "create", "1000", "A", "asset"])
    main(["--db", fresh_db, "accounts", "create", "1100", "C", "asset", "--parent", "1000"])
    exit_code = main(["--db", fresh_db, "accounts", "reparent", "1100"])
    assert exit_code == 0


def test_reparent_cycle_returns_exit_code_one(fresh_db):
    main(["--db", fresh_db, "accounts", "create", "1000", "A", "asset"])
    main(["--db", fresh_db, "accounts", "create", "1100", "B", "asset", "--parent", "1000"])
    exit_code = main(["--db", fresh_db, "accounts", "reparent", "1000", "--parent", "1100"])
    assert exit_code == 1


def test_deactivate_then_activate(fresh_db, capsys):
    main(["--db", fresh_db, "accounts", "create", "1000", "A", "asset"])
    exit_code = main(["--db", fresh_db, "accounts", "deactivate", "1000"])
    assert exit_code == 0
    exit_code = main(["--db", fresh_db, "accounts", "activate", "1000"])
    assert exit_code == 0
    capsys.readouterr()
    main(["--db", fresh_db, "accounts", "list"])
    assert "1000" in capsys.readouterr().out


def test_deactivate_missing_account_returns_exit_code_one(fresh_db):
    exit_code = main(["--db", fresh_db, "accounts", "deactivate", "no-such-code"])
    assert exit_code == 1


def test_accounts_requires_subcommand(fresh_db):
    with pytest.raises(SystemExit):
        main(["--db", fresh_db, "accounts"])
