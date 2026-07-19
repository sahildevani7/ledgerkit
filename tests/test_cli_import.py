from __future__ import annotations

from pathlib import Path

from ledgerkit.cli.main import main


def _write_statement(tmp_path: Path) -> Path:
    path = tmp_path / "statement.csv"
    path.write_text(
        "date,description,amount\n"
        "2026-07-16,Coffee Shop,-4.50\n"
        "2026-07-17,Paycheque,200.00\n"
    )
    return path


def test_import_posts_all_transactions(cli_db, tmp_path, capsys):
    statement = _write_statement(tmp_path)
    exit_code = main(
        [
            "--db", cli_db, "import", str(statement),
            "--account", "1000", "--contra-account", "3000",
        ]
    )
    assert exit_code == 0
    assert "imported 2 transaction(s)" in capsys.readouterr().out


def test_import_updates_balance(cli_db, tmp_path, capsys):
    statement = _write_statement(tmp_path)
    main(
        [
            "--db", cli_db, "import", str(statement),
            "--account", "1000", "--contra-account", "3000",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "balance", "1000"])
    assert capsys.readouterr().out.strip() == "195.50 CAD"


def test_import_missing_file_returns_exit_code_one(cli_db, tmp_path):
    missing = tmp_path / "nope.csv"
    exit_code = main(
        [
            "--db", cli_db, "import", str(missing),
            "--account", "1000", "--contra-account", "3000",
        ]
    )
    assert exit_code == 1


def test_import_unknown_account_returns_exit_code_one(cli_db, tmp_path):
    statement = _write_statement(tmp_path)
    exit_code = main(
        [
            "--db", cli_db, "import", str(statement),
            "--account", "9999", "--contra-account", "3000",
        ]
    )
    assert exit_code == 1


def test_import_bad_csv_rolls_back_everything(cli_db, tmp_path, capsys):
    bad_statement = tmp_path / "bad.csv"
    bad_statement.write_text(
        "date,description,amount\n2026-07-16,Coffee,-4.50\n2026-07-17,Bad Row,not-a-number\n"
    )
    exit_code = main(
        [
            "--db", cli_db, "import", str(bad_statement),
            "--account", "1000", "--contra-account", "3000",
        ]
    )
    assert exit_code == 1

    capsys.readouterr()
    main(["--db", cli_db, "balance", "1000"])
    assert capsys.readouterr().out.strip() == "0.00 CAD"


def test_import_unknown_dialect_returns_exit_code_one(cli_db, tmp_path):
    statement = _write_statement(tmp_path)
    exit_code = main(
        [
            "--db", cli_db, "import", str(statement),
            "--account", "1000", "--contra-account", "3000", "--dialect", "no-such-dialect",
        ]
    )
    assert exit_code == 1
