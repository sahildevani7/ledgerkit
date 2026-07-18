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
