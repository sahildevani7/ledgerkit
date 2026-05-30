"""Flat configuration loading.

Configuration is a small, flat set of scalars — no nested sections, no
plugins. It can come from a TOML file, an environment mapping, or explicit
keyword overrides, applied in that order (each layer overrides the last).
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from ledgerkit.errors import ConfigError

_ENV_PREFIX = "LEDGERKIT_"

_FIELD_TYPES: dict[str, type] = {}


@dataclass(frozen=True, slots=True)
class LedgerConfig:
    """Runtime configuration for a ledgerkit instance."""

    db_path: str = "ledger.db"
    fiscal_year_start_month: int = 1
    default_currency_code: str = "CAD"

    def with_overrides(self, **overrides: object) -> LedgerConfig:
        return replace(self, **overrides)  # type: ignore[arg-type]


_FIELD_TYPES.update(
    {
        "db_path": str,
        "fiscal_year_start_month": int,
        "default_currency_code": str,
    }
)


def _coerce(field: str, raw: str) -> object:
    field_type = _FIELD_TYPES[field]
    if field_type is int:
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigError(f"{field} must be an integer, got {raw!r}") from exc
    return raw


def _from_env(env: Mapping[str, str]) -> dict[str, object]:
    values: dict[str, object] = {}
    for field in _FIELD_TYPES:
        key = f"{_ENV_PREFIX}{field.upper()}"
        if key in env:
            values[field] = _coerce(field, env[key])
    return values


def load_config(
    path: Path | None = None,
    env: Mapping[str, str] | None = None,
    **overrides: object,
) -> LedgerConfig:
    """Load configuration from an optional TOML file, then env, then overrides."""
    values: dict[str, object] = {}

    if path is not None:
        if not path.exists():
            raise ConfigError(f"config file not found: {path}")
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"invalid TOML in {path}: {exc}") from exc
        unknown = set(data) - set(_FIELD_TYPES)
        if unknown:
            raise ConfigError(f"unknown config key(s): {sorted(unknown)}")
        values.update(data)

    if env is not None:
        values.update(_from_env(env))

    values.update(overrides)

    try:
        return LedgerConfig(**values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ConfigError(f"invalid configuration: {exc}") from exc
