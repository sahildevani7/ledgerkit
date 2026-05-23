from __future__ import annotations

import pytest

from ledgerkit.currency import CAD, Currency, default_currency


def test_cad_defaults():
    assert CAD.code == "CAD"
    assert CAD.exponent == 2


def test_default_currency_is_cad():
    assert default_currency() == CAD


def test_currency_is_frozen():
    with pytest.raises(AttributeError):
        CAD.code = "USD"  # type: ignore[misc]


def test_rejects_bad_code_length():
    with pytest.raises(ValueError):
        Currency(code="CADX", exponent=2)


def test_rejects_lowercase_code():
    with pytest.raises(ValueError):
        Currency(code="cad", exponent=2)


def test_rejects_negative_exponent():
    with pytest.raises(ValueError):
        Currency(code="CAD", exponent=-1)


def test_str():
    assert str(CAD) == "CAD"


def test_equality():
    assert Currency(code="CAD", exponent=2) == CAD
    assert Currency(code="USD", exponent=2) != CAD
