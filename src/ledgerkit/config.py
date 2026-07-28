"""Flat configuration loading.

Configuration is a small, flat set of scalars — no nested sections, no
plugins. It can come from a TOML file, an environment mapping, or explicit
keyword overrides, applied in that order (each layer overrides the last).

A typical config file, ``ledgerkit.toml``, looks like::

    db_path = "ledger.db"
    fiscal_year_start_month = 4
    default_currency_code = "CAD"

Unknown keys are rejected rather than silently ignored, since a typo in a
config file is otherwise invisible.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from ledgerkit.errors import ConfigError

_ENV_PREFIX = "LEDGERKIT_"
_CONFIG_FILENAME = "ledgerkit.toml"

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


def find_config_file(start: Path) -> Path | None:
    """Search ``start`` and its ancestors for a ``ledgerkit.toml``.

    Mirrors how tools like git and pytest locate their config: starting
    from a working directory and walking upward, so a config file at a
    project's root is found regardless of which subdirectory a command is
    run from.

    Args:
        start: The directory to begin searching from.

    Returns:
        The first ``ledgerkit.toml`` found, or ``None`` if none of
        ``start``'s ancestors (including ``start`` itself) has one.
    """
    current = start.resolve()
    while True:
        candidate = current / _CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        if current.parent == current:
            return None
        current = current.parent
