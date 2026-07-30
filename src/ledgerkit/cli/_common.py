"""Shared argument-parsing helpers used across CLI subcommand modules.

Every subcommand that accepts an optional date argument (``--as-of``,
``--start``, ``--end``, ``--entry-date``) parses it the same way, so the
parsing rule — ISO 8601, absent means "no bound" — lives in exactly one
place instead of being repeated with slightly different phrasing in each
`cmd_*.py` module.
"""

from __future__ import annotations

from datetime import date


def parse_optional_date(value: str | None) -> date | None:
    """Parse an ISO 8601 date string, or return ``None`` if ``value`` is ``None``.

    Raises:
        ValueError: If ``value`` is present but not a valid ISO date —
            the same error :meth:`date.fromisoformat` itself raises,
            surfaced directly rather than wrapped.
    """
    if value is None:
        return None
    return date.fromisoformat(value)
