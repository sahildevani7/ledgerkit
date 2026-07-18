from __future__ import annotations

from pathlib import Path

import pytest

from ledgerkit.cli.main import main


def test_no_command_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code != 0


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0


def test_unknown_command_exits_nonzero():
    with pytest.raises(SystemExit) as exc_info:
        main(["bogus-command"])
    assert exc_info.value.code != 0


def test_db_file_created_and_migrated(tmp_path: Path):
    db_path = tmp_path / "fresh.db"
    assert not db_path.exists()
    exit_code = main(["--db", str(db_path), "balance", "does-not-exist"])
    assert exit_code == 1
    assert db_path.exists()


def test_ledger_error_returns_exit_code_one(tmp_path: Path, capsys):
    db_path = tmp_path / "fresh.db"
    exit_code = main(["--db", str(db_path), "balance", "no-such-account"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err
