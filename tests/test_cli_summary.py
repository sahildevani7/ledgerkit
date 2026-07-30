from __future__ import annotations

from ledgerkit.cli.main import main


def test_summary_on_seeded_db(cli_db, capsys):
    exit_code = main(["--db", cli_db, "summary"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "accounts: 2" in output
    assert "journal entries: 0" in output
    assert "balanced: yes" in output


def test_summary_reflects_posted_entry(cli_db, capsys):
    main(
        [
            "--db", cli_db, "post",
            "--debit", "1000:50.00",
            "--credit", "3000:50.00",
            "--entry-date", "2026-07-17",
        ]
    )
    capsys.readouterr()
    main(["--db", cli_db, "summary"])
    output = capsys.readouterr().out
    assert "journal entries: 1" in output
    assert "balanced: yes" in output
