from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

import pytest

from ledgerkit.currency import CAD, Currency
from ledgerkit.errors import ValidationError
from ledgerkit.money import Money


def test_construct_from_decimal():
    m = Money(Decimal("10.00"))
    assert m.amount == Decimal("10.00")
    assert m.currency == CAD


def test_construct_from_int():
    m = Money(10)
    assert m.amount == Decimal("10.00")


def test_construct_from_string():
    m = Money("10.50")
    assert m.amount == Decimal("10.50")


def test_construct_rejects_excess_precision():
    with pytest.raises(ValidationError):
        Money(Decimal("10.001"))


def test_zero():
    assert Money.zero().amount == Decimal("0.00")
    assert Money.zero().is_zero()


def test_from_rounded_half_up():
    m = Money.from_rounded(Decimal("10.005"), rounding=ROUND_HALF_UP)
    assert m.amount == Decimal("10.01")


def test_from_rounded_down():
    m = Money.from_rounded(Decimal("10.009"), rounding=ROUND_DOWN)
    assert m.amount == Decimal("10.00")


def test_from_rounded_rejects_bad_mode():
    with pytest.raises(ValidationError):
        Money.from_rounded(Decimal("10.00"), rounding="not-a-mode")


def test_addition():
    assert Money(Decimal("10.00")) + Money(Decimal("5.00")) == Money(Decimal("15.00"))


def test_subtraction():
    assert Money(Decimal("10.00")) - Money(Decimal("3.00")) == Money(Decimal("7.00"))


def test_negation():
    assert -Money(Decimal("10.00")) == Money(Decimal("-10.00"))


def test_abs():
    assert abs(Money(Decimal("-10.00"))) == Money(Decimal("10.00"))


def test_addition_currency_mismatch():
    other = Currency(code="USD", exponent=2)
    with pytest.raises(ValidationError):
        Money(Decimal("1.00")) + Money(Decimal("1.00"), other)


def test_scaled_requires_rounding_mode():
    m = Money(Decimal("10.00"))
    result = m.scaled(Decimal("0.1"), rounding=ROUND_HALF_UP)
    assert result.amount == Decimal("1.00")


def test_scaled_rejects_bad_mode():
    m = Money(Decimal("10.00"))
    with pytest.raises(ValidationError):
        m.scaled(Decimal("0.1"), rounding="bogus")


def test_is_negative_and_positive():
    assert Money(Decimal("-1.00")).is_negative()
    assert Money(Decimal("1.00")).is_positive()
    assert not Money(Decimal("0.00")).is_negative()
    assert not Money(Decimal("0.00")).is_positive()


def test_ordering():
    small = Money(Decimal("1.00"))
    big = Money(Decimal("2.00"))
    assert small < big
    assert big > small
    assert small <= small
    assert big >= big


def test_ordering_currency_mismatch():
    other = Currency(code="USD", exponent=2)
    with pytest.raises(ValidationError):
        assert Money(Decimal("1.00")) < Money(Decimal("1.00"), other)


def test_ordering_type_mismatch():
    with pytest.raises(TypeError):
        assert Money(Decimal("1.00")) < 5  # type: ignore[operator]


def test_equality_with_non_money():
    assert Money(Decimal("1.00")) != "1.00"


def test_hashable_in_set():
    s = {Money(Decimal("1.00")), Money(Decimal("1.00")), Money(Decimal("2.00"))}
    assert len(s) == 2


def test_repr_and_str():
    m = Money(Decimal("10.00"))
    assert repr(m) == "Money(10.00, CAD)"
    assert str(m) == "10.00 CAD"


def test_format():
    yen = Currency(code="JPY", exponent=0)
    m = Money(Decimal("100"), yen)
    assert m.format() == "100 JPY"
    assert Money(Decimal("10.5")).format() == "10.50 CAD"


def test_zero_exponent_currency_rejects_fractional_amount():
    yen = Currency(code="JPY", exponent=0)
    with pytest.raises(ValidationError):
        Money(Decimal("1.5"), yen)


def test_addition_with_zero_exponent_currency():
    yen = Currency(code="JPY", exponent=0)
    assert Money(Decimal("100"), yen) + Money(Decimal("50"), yen) == Money(Decimal("150"), yen)


def test_negative_zero_normalizes_to_zero():
    assert Money(Decimal("-0.00")) == Money.zero()
    assert not Money(Decimal("-0.00")).is_negative()


def test_large_amount_arithmetic():
    big = Money(Decimal("999999999999.99"))
    assert (big + Money(Decimal("0.01"))).amount == Decimal("1000000000000.00")


def test_three_way_ordering():
    low, mid, high = Money(Decimal("1.00")), Money(Decimal("2.00")), Money(Decimal("3.00"))
    assert sorted([high, low, mid], key=lambda m: m.amount) == [low, mid, high]


def test_scaled_by_negative_factor():
    m = Money(Decimal("10.00"))
    result = m.scaled(Decimal("-1"), rounding=ROUND_HALF_UP)
    assert result == Money(Decimal("-10.00"))


def test_scaled_by_zero():
    m = Money(Decimal("10.00"))
    assert m.scaled(Decimal("0"), rounding=ROUND_HALF_UP).is_zero()


def test_from_rounded_negative_amount():
    m = Money.from_rounded(Decimal("-10.005"), rounding=ROUND_HALF_UP)
    assert m.amount == Decimal("-10.01")


def test_double_negation_is_identity():
    m = Money(Decimal("5.00"))
    negated = -m
    assert -negated == m


def test_subtraction_yields_zero_for_equal_amounts():
    m = Money(Decimal("42.00"))
    assert (m - m).is_zero()
