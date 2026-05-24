"""Money: a Decimal-backed amount with an explicit rounding policy.

Every monetary value in ledgerkit is a :class:`Money` instance. There is no
implicit float conversion and no implicit rounding: constructing a
``Money`` from a value that doesn't fit the currency's minor unit exactly
raises :class:`~ledgerkit.errors.ValidationError`, and any operation that
*can* produce a fractional minor unit (scaling by a ratio) requires the
caller to name a rounding mode explicitly.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP, Decimal
from typing import Final

from ledgerkit.currency import CAD, Currency
from ledgerkit.errors import ValidationError

#: Rounding modes ledgerkit permits at explicit-rounding call sites. Callers
#: name one of these; there is no library-wide default.
ROUNDING_MODES: Final = (ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_UP, ROUND_DOWN)


def _quantum(currency: Currency) -> Decimal:
    return Decimal(1).scaleb(-currency.exponent)


class Money:
    """An exact amount of a single currency's minor units."""

    __slots__ = ("_amount", "_currency")

    def __init__(self, amount: Decimal | int | str, currency: Currency = CAD) -> None:
        dec = amount if isinstance(amount, Decimal) else Decimal(str(amount))
        quantum = _quantum(currency)
        quantized = dec.quantize(quantum, rounding=ROUND_HALF_EVEN)
        if quantized != dec:
            raise ValidationError(
                f"amount {dec} has more precision than {currency.code} allows "
                f"({currency.exponent} decimal places); round explicitly first"
            )
        self._amount = quantized
        self._currency = currency

    @classmethod
    def zero(cls, currency: Currency = CAD) -> Money:
        return cls(Decimal(0), currency)

    @classmethod
    def from_rounded(
        cls, amount: Decimal | int | str, currency: Currency = CAD, *, rounding: str
    ) -> Money:
        """Construct a ``Money``, rounding ``amount`` to the currency's minor unit.

        ``rounding`` must be one of :data:`ROUNDING_MODES`; there is no default.
        """
        if rounding not in ROUNDING_MODES:
            raise ValidationError(f"unsupported rounding mode: {rounding!r}")
        dec = amount if isinstance(amount, Decimal) else Decimal(str(amount))
        quantized = dec.quantize(_quantum(currency), rounding=rounding)
        return cls(quantized, currency)

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> Currency:
        return self._currency

    def _check_currency(self, other: Money) -> None:
        if self._currency != other._currency:
            raise ValidationError(
                f"cannot combine {self._currency.code} with {other._currency.code}"
            )

    def __add__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return Money(self._amount + other._amount, self._currency)

    def __sub__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return Money(self._amount - other._amount, self._currency)

    def __neg__(self) -> Money:
        return Money(-self._amount, self._currency)

    def __abs__(self) -> Money:
        return Money(abs(self._amount), self._currency)

    def scaled(self, factor: Decimal | int | str, *, rounding: str) -> Money:
        """Multiply by ``factor``, rounding the result to the minor unit.

        ``rounding`` must be one of :data:`ROUNDING_MODES`; there is no default,
        since scaling can produce fractional minor units.
        """
        if rounding not in ROUNDING_MODES:
            raise ValidationError(f"unsupported rounding mode: {rounding!r}")
        factor_dec = factor if isinstance(factor, Decimal) else Decimal(str(factor))
        raw = self._amount * factor_dec
        quantized = raw.quantize(_quantum(self._currency), rounding=rounding)
        return Money(quantized, self._currency)

    def is_zero(self) -> bool:
        return self._amount == 0

    def is_negative(self) -> bool:
        return self._amount < 0

    def is_positive(self) -> bool:
        return self._amount > 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._amount == other._amount and self._currency == other._currency

    def __hash__(self) -> int:
        return hash((self._amount, self._currency))

    def _compare_check(self, other: object) -> Money:
        if not isinstance(other, Money):
            raise TypeError(f"cannot compare Money with {type(other).__name__}")
        self._check_currency(other)
        return other

    def __lt__(self, other: object) -> bool:
        o = self._compare_check(other)
        return self._amount < o._amount

    def __le__(self, other: object) -> bool:
        o = self._compare_check(other)
        return self._amount <= o._amount

    def __gt__(self, other: object) -> bool:
        o = self._compare_check(other)
        return self._amount > o._amount

    def __ge__(self, other: object) -> bool:
        o = self._compare_check(other)
        return self._amount >= o._amount

    def __repr__(self) -> str:
        return f"Money({self._amount!s}, {self._currency.code})"

    def __str__(self) -> str:
        return f"{self._amount} {self._currency.code}"

    def format(self) -> str:
        """Render with a fixed number of decimal places and a currency suffix."""
        return f"{self._amount:.{self._currency.exponent}f} {self._currency.code}"
