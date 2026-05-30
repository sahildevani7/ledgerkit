from __future__ import annotations

from pathlib import Path

import pytest

from ledgerkit.config import LedgerConfig, load_config
from ledgerkit.errors import ConfigError


def test_defaults():
    cfg = load_config()
    assert cfg.db_path == "ledger.db"
    assert cfg.fiscal_year_start_month == 1
    assert cfg.default_currency_code == "CAD"


def test_overrides_take_precedence():
    cfg = load_config(db_path="custom.db")
    assert cfg.db_path == "custom.db"


def test_env_overrides_defaults():
    env = {"LEDGERKIT_DB_PATH": "from_env.db", "LEDGERKIT_FISCAL_YEAR_START_MONTH": "4"}
    cfg = load_config(env=env)
    assert cfg.db_path == "from_env.db"
    assert cfg.fiscal_year_start_month == 4


def test_overrides_beat_env():
    env = {"LEDGERKIT_DB_PATH": "from_env.db"}
    cfg = load_config(env=env, db_path="from_kwarg.db")
    assert cfg.db_path == "from_kwarg.db"


def test_env_rejects_non_integer_for_int_field():
    env = {"LEDGERKIT_FISCAL_YEAR_START_MONTH": "not-a-number"}
    with pytest.raises(ConfigError):
        load_config(env=env)


def test_ignores_unrelated_env_keys():
    env = {"PATH": "/usr/bin", "HOME": "/home/x"}
    cfg = load_config(env=env)
    assert cfg == LedgerConfig()


def test_missing_file_raises(tmp_path: Path):
    missing = tmp_path / "nope.toml"
    with pytest.raises(ConfigError):
        load_config(path=missing)


def test_load_from_toml_file(tmp_path: Path):
    config_file = tmp_path / "ledgerkit.toml"
    config_file.write_text('db_path = "from_file.db"\nfiscal_year_start_month = 7\n')
    cfg = load_config(path=config_file)
    assert cfg.db_path == "from_file.db"
    assert cfg.fiscal_year_start_month == 7


def test_invalid_toml_raises(tmp_path: Path):
    config_file = tmp_path / "bad.toml"
    config_file.write_text("this is not [valid toml")
    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_unknown_key_in_file_raises(tmp_path: Path):
    config_file = tmp_path / "unknown.toml"
    config_file.write_text('made_up_key = "x"\n')
    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_file_then_env_then_override_layering(tmp_path: Path):
    config_file = tmp_path / "ledgerkit.toml"
    config_file.write_text('db_path = "file.db"\nfiscal_year_start_month = 3\n')
    env = {"LEDGERKIT_DB_PATH": "env.db"}
    cfg = load_config(path=config_file, env=env, fiscal_year_start_month=9)
    assert cfg.db_path == "env.db"
    assert cfg.fiscal_year_start_month == 9


def test_with_overrides_returns_new_instance():
    cfg = LedgerConfig()
    updated = cfg.with_overrides(db_path="other.db")
    assert updated.db_path == "other.db"
    assert cfg.db_path == "ledger.db"
