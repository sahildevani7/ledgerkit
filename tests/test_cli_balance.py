from __future__ import annotations

from ledgerkit.cli.main import main


def test_balance_zero_for_new_account(cli_db, capsys):
    exit_code = main(["--db", cli_db, "balance", "1000"])
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "0.00 CAD"


def test_balance_after_posting(cli_db, capsys):
    main(
        [
            "--db",
            cli_db,
            "post",
            "--debit",
            "1000:75.00",
            "--credit",
            "3000:75.00",
            "--entry-date",
            "2026-07-17",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "balance", "1000"])
    assert capsys.readouterr().out.strip() == "75.00 CAD"


def test_balance_as_of_excludes_later_entries(cli_db, capsys):
    main(
        [
            "--db",
            cli_db,
            "post",
            "--debit",
            "1000:75.00",
            "--credit",
            "3000:75.00",
            "--entry-date",
            "2026-08-01",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "balance", "1000", "--as-of", "2026-07-01"])
    assert capsys.readouterr().out.strip() == "0.00 CAD"


def test_balance_missing_account_returns_exit_code_one(cli_db):
    exit_code = main(["--db", cli_db, "balance", "no-such-code"])
    assert exit_code == 1


def test_balance_include_subaccounts_rolls_up_children(cli_db, capsys):
    main(["--db", cli_db, "accounts", "create", "5000", "Groceries", "expense"])
    main(
        [
            "--db", cli_db, "accounts", "create", "5010", "Household", "expense",
            "--parent", "5000",
        ]
    )
    main(
        [
            "--db", cli_db, "post",
            "--debit", "5010:40.00",
            "--credit", "1000:40.00",
            "--entry-date", "2026-07-17",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "balance", "5000", "--include-subaccounts"])
    assert capsys.readouterr().out.strip() == "40.00 CAD"


def test_balance_without_include_subaccounts_excludes_children(cli_db, capsys):
    main(["--db", cli_db, "accounts", "create", "5000", "Groceries", "expense"])
    main(
        [
            "--db", cli_db, "accounts", "create", "5010", "Household", "expense",
            "--parent", "5000",
        ]
    )
    main(
        [
            "--db", cli_db, "post",
            "--debit", "5010:40.00",
            "--credit", "1000:40.00",
            "--entry-date", "2026-07-17",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "balance", "5000"])
    assert capsys.readouterr().out.strip() == "0.00 CAD"
