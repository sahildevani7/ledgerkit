from __future__ import annotations

from ledgerkit.cli.main import main


def test_trial_balance_empty_ledger(cli_db, capsys):
    exit_code = main(["--db", cli_db, "report", "trial-balance"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "1000" in output
    assert "TOTAL" in output


def test_trial_balance_reflects_postings(cli_db, capsys):
    main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:100.00",
            "--credit", "3000:100.00",
            "--entry-date", "2026-07-17",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "report", "trial-balance"])
    output = capsys.readouterr().out
    assert "100.00 CAD" in output


def test_trial_balance_as_of(cli_db, capsys):
    main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:100.00",
            "--credit", "3000:100.00",
            "--entry-date", "2026-08-01",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "report", "trial-balance", "--as-of", "2026-07-01"])
    output = capsys.readouterr().out
    assert "0.00 CAD" in output


def test_report_requires_report_type(cli_db):
    import pytest

    with pytest.raises(SystemExit):
        main(["--db", cli_db, "report"])


def test_account_activity_empty(cli_db, capsys):
    exit_code = main(["--db", cli_db, "report", "account-activity", "1000"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Checking" in output
    assert "0.00" in output


def test_account_activity_reflects_postings(cli_db, capsys):
    main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:75.00",
            "--credit", "3000:75.00",
            "--entry-date", "2026-07-17",
            "--memo", "test entry",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "report", "account-activity", "1000"])
    output = capsys.readouterr().out
    assert "75.00" in output
    assert "test entry" in output


def test_account_activity_date_range(cli_db, capsys):
    main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:10.00",
            "--credit", "3000:10.00",
            "--entry-date", "2026-06-01",
        ]
    )
    main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:20.00",
            "--credit", "3000:20.00",
            "--entry-date", "2026-07-01",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "report", "account-activity", "1000", "--start", "2026-06-15"])
    output = capsys.readouterr().out
    assert "20.00" in output


def test_account_activity_unknown_account_returns_exit_code_one(cli_db):
    exit_code = main(["--db", cli_db, "report", "account-activity", "no-such-code"])
    assert exit_code == 1
