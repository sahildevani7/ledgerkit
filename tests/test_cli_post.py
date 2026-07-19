from __future__ import annotations

from ledgerkit.cli.main import main


def test_post_creates_balanced_entry(cli_db, capsys):
    exit_code = main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:100.00",
            "--credit", "3000:100.00",
            "--entry-date", "2026-07-17",
            "--memo", "opening balance",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "posted entry" in captured.out


def test_post_updates_balance(cli_db):
    main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:50.00",
            "--credit", "3000:50.00",
            "--entry-date", "2026-07-17",
        ]
    )
    exit_code = main(["--db", cli_db, "balance", "1000"])
    assert exit_code == 0


def test_post_unbalanced_returns_exit_code_one(cli_db, capsys):
    exit_code = main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:100.00",
            "--credit", "3000:50.00",
            "--entry-date", "2026-07-17",
        ]
    )
    assert exit_code == 1
    assert "error:" in capsys.readouterr().err


def test_post_unknown_account_returns_exit_code_one(cli_db):
    exit_code = main(
        [
            "--db", cli_db, "post",
            "--debit", "9999:100.00",
            "--credit", "3000:100.00",
            "--entry-date", "2026-07-17",
        ]
    )
    assert exit_code == 1


def test_post_bad_spec_format_returns_exit_code_one(cli_db):
    exit_code = main(
        [
            "--db", cli_db, "post",
            "--debit", "1000",
            "--credit", "3000:100.00",
            "--entry-date", "2026-07-17",
        ]
    )
    assert exit_code == 1


def test_post_multiple_debits_and_credits(cli_db):
    exit_code = main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:60.00",
            "--debit", "1000:40.00",
            "--credit", "3000:100.00",
            "--entry-date", "2026-07-17",
        ]
    )
    assert exit_code == 0


def test_post_missing_debit_argument_exits_nonzero(cli_db):
    import pytest

    with pytest.raises(SystemExit):
        main(["--db", cli_db, "post", "--credit", "3000:100.00"])
