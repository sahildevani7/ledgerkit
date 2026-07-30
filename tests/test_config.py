from __future__ import annotations

from pathlib import Path

import pytest

from ledgerkit.config import LedgerConfig, find_config_file, load_config, write_config
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


def test_find_config_file_in_start_directory(tmp_path: Path):
    (tmp_path / "ledgerkit.toml").write_text('db_path = "x.db"\n')
    assert find_config_file(tmp_path) == tmp_path / "ledgerkit.toml"


def test_find_config_file_in_ancestor_directory(tmp_path: Path):
    (tmp_path / "ledgerkit.toml").write_text('db_path = "x.db"\n')
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    assert find_config_file(nested) == tmp_path / "ledgerkit.toml"


def test_find_config_file_returns_none_when_absent(tmp_path: Path):
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    assert find_config_file(isolated) is None


def test_find_config_file_prefers_closest_ancestor(tmp_path: Path):
    (tmp_path / "ledgerkit.toml").write_text('db_path = "outer.db"\n')
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "ledgerkit.toml").write_text('db_path = "inner.db"\n')
    assert find_config_file(nested) == nested / "ledgerkit.toml"


def test_write_config_creates_file(tmp_path: Path):
    path = tmp_path / "ledgerkit.toml"
    write_config(path, LedgerConfig())
    assert path.exists()


def test_write_config_round_trips_defaults(tmp_path: Path):
    path = tmp_path / "ledgerkit.toml"
    write_config(path, LedgerConfig())
    assert load_config(path=path) == LedgerConfig()


def test_write_config_round_trips_custom_values(tmp_path: Path):
    path = tmp_path / "ledgerkit.toml"
    config = LedgerConfig(
        db_path="custom.db", fiscal_year_start_month=4, default_currency_code="CAD"
    )
    write_config(path, config)
    assert load_config(path=path) == config


def test_write_config_escapes_special_characters(tmp_path: Path):
    path = tmp_path / "ledgerkit.toml"
    config = LedgerConfig(db_path='weird "quoted" \\path.db')
    write_config(path, config)
    assert load_config(path=path) == config


def test_write_config_overwrites_existing_file(tmp_path: Path):
    path = tmp_path / "ledgerkit.toml"
    write_config(path, LedgerConfig(db_path="first.db"))
    write_config(path, LedgerConfig(db_path="second.db"))
    assert load_config(path=path).db_path == "second.db"
