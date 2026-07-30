from __future__ import annotations

from datetime import date

import pytest

from ledgerkit.cli._common import parse_optional_date


def test_none_returns_none():
    assert parse_optional_date(None) is None


def test_parses_iso_date():
    assert parse_optional_date("2026-07-01") == date(2026, 7, 1)


def test_rejects_invalid_date():
    with pytest.raises(ValueError):
        parse_optional_date("not-a-date")
