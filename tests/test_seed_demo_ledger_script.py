"""Runs the demo seeding script's own logic directly (not as a subprocess),
so it's covered by the same test suite as everything else and can't
silently bit-rot as the library evolves.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import seed_demo_ledger  # noqa: E402

from ledgerkit.accounts.repository import AccountRepository  # noqa: E402
from ledgerkit.ledger.trial_balance import build_trial_balance  # noqa: E402
from ledgerkit.storage.engine import Engine  # noqa: E402


def test_seed_creates_all_accounts(tmp_path: Path):
    db_path = tmp_path / "demo.db"
    seed_demo_ledger.seed(db_path)
    engine = Engine(db_path)
    connection = engine.connect()
    codes = {a.code for a in AccountRepository(connection).list_all()}
    engine.close()
    assert codes == {code for code, _, _ in seed_demo_ledger._CHART}


def test_seed_produces_a_balanced_ledger(tmp_path: Path):
    db_path = tmp_path / "demo.db"
    seed_demo_ledger.seed(db_path)
    engine = Engine(db_path)
    connection = engine.connect()
    tb = build_trial_balance(connection)
    engine.close()
    assert tb.is_balanced()
    assert not tb.total_debits().is_zero()


def test_main_refuses_to_overwrite_without_force(tmp_path: Path, capsys):
    db_path = tmp_path / "demo.db"
    db_path.write_text("not a real database")
    exit_code = seed_demo_ledger.main(["--db", str(db_path)])
    assert exit_code == 1
    assert "already exists" in capsys.readouterr().out


def test_main_overwrites_with_force(tmp_path: Path):
    db_path = tmp_path / "demo.db"
    db_path.write_text("not a real database")
    exit_code = seed_demo_ledger.main(["--db", str(db_path), "--force"])
    assert exit_code == 0


def test_main_prints_trial_balance(tmp_path: Path, capsys):
    db_path = tmp_path / "demo.db"
    exit_code = seed_demo_ledger.main(["--db", str(db_path)])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "TOTAL" in output
    assert "seeded" in output
