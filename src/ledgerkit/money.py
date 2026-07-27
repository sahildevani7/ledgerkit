"""Money: a Decimal-backed amount with an explicit rounding policy.

Every monetary value in ledgerkit is a :class:`Money` instance. There is no
implicit float conversion and no implicit rounding: constructing a
``Money`` from a value that doesn't fit the currency's minor unit exactly
raises :class:`~ledgerkit.errors.ValidationError`, and any operation that
*can* produce a fractional minor unit (scaling by a ratio, splitting a
total into parts) requires the caller to name a rounding mode explicitly.

Design rationale
-----------------
Floating-point amounts are the single most common source of accounting
bugs: ``0.1 + 0.2 != 0.3`` in IEEE 754 binary floating point, and that kind
of error compounds silently across thousands of postings. ``Money`` avoids
the problem structurally rather than by convention — it only ever stores a
:class:`decimal.Decimal` quantized to the currency's minor unit, and it
refuses to construct itself from a value that would require rounding
unless the caller says explicitly how to round.

The immediate consequence is that two ``Money`` values of the same
currency can always be compared and combined exactly, with no epsilon
comparisons anywhere in the codebase.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP, Decimal
from typing import Final

from ledgerkit.currency import CAD, Currency
from ledgerkit.errors import ValidationError

#: Rounding modes ledgerkit permits at explicit-rounding call sites. Callers
#: name one of these; there is no library-wide default rounding policy.
ROUNDING_MODES: Final = (ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_UP, ROUND_DOWN)


def _quantum(currency: Currency) -> Decimal:
    """The smallest representable increment of a currency, e.g. ``0.01`` for CAD."""
    return Decimal(1).scaleb(-currency.exponent)


def _check_rounding(rounding: str) -> None:
    if rounding not in ROUNDING_MODES:
        raise ValidationError(f"unsupported rounding mode: {rounding!r}")


class Money:
    """An exact amount of a single currency's minor units.

    Instances are immutable and hashable, so they can be used as dict keys
    or set members and safely shared between callers without defensive
    copying.
    """

    __slots__ = ("_amount", "_currency")

    def __init__(self, amount: Decimal | int | str, currency: Currency = CAD) -> None:
        """Construct a Money value.

        Args:
            amount: The exact amount, as a ``Decimal``, ``int``, or a
                decimal string. Floats are deliberately not accepted —
                convert through ``str`` first if you must start from one,
                so the imprecision is visible at the call site.
            currency: The currency the amount is denominated in. Defaults
                to CAD, ledgerkit's base currency.

        Raises:
            ValidationError: If ``amount`` has more decimal places than
                the currency's minor unit allows. Use :meth:`from_rounded`
                if the value needs rounding rather than rejecting.
        """
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
        """A zero amount in the given currency."""
        return cls(Decimal(0), currency)

    @classmethod
    def from_rounded(
        cls, amount: Decimal | int | str, currency: Currency = CAD, *, rounding: str
    ) -> Money:
        """Construct a ``Money``, rounding ``amount`` to the currency's minor unit.

        Args:
            amount: The amount to round and store.
            currency: The currency the amount is denominated in.
            rounding: One of :data:`ROUNDING_MODES`. There is no default —
                every caller that needs rounding has to say which kind.

        Raises:
            ValidationError: If ``rounding`` isn't a recognized mode.
        """
        _check_rounding(rounding)
        dec = amount if isinstance(amount, Decimal) else Decimal(str(amount))
        quantized = dec.quantize(_quantum(currency), rounding=rounding)
        return cls(quantized, currency)

    @classmethod
    def parse(cls, text: str, currency: Currency = CAD) -> Money:
        """Parse a plain decimal string such as ``"-4.50"`` into a Money.

        Unlike :meth:`__init__`, this accepts and strips surrounding
        whitespace, which is convenient at input boundaries (CLI
        arguments, CSV cells) where stray whitespace is common.

        Raises:
            ValidationError: If ``text`` isn't a valid decimal, or has
                more precision than the currency allows.
        """
        stripped = text.strip()
        try:
            dec = Decimal(stripped)
        except Exception as exc:
            raise ValidationError(f"not a valid amount: {text!r}") from exc
        return cls(dec, currency)

    @property
    def amount(self) -> Decimal:
        """The underlying exact amount, already quantized to the minor unit."""
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

        Args:
            factor: The multiplier. Need not be an integer.
            rounding: One of :data:`ROUNDING_MODES`. There is no default,
                since scaling can produce fractional minor units.

        Raises:
            ValidationError: If ``rounding`` isn't a recognized mode.
        """
        _check_rounding(rounding)
        factor_dec = factor if isinstance(factor, Decimal) else Decimal(str(factor))
        raw = self._amount * factor_dec
        quantized = raw.quantize(_quantum(self._currency), rounding=rounding)
        return Money(quantized, self._currency)

    def allocate(self, ratios: list[int]) -> list[Money]:
        """Split this amount across ``len(ratios)`` parts proportional to ``ratios``.

        This is the classic "split the bill" problem: proportional
        division of an exact amount essentially never divides evenly into
        the currency's minor unit, so a plain ``amount / n`` per part would
        either lose or fabricate money at the edges. Instead, each part is
        rounded down first, and the leftover minor units (there are at
        most ``len(ratios) - 1`` of them) are handed out one at a time, in
        order, to the parts with the largest fractional remainder — the
        "largest remainder method". The parts always sum to exactly the
        original amount, regardless of currency or ratios.

        Args:
            ratios: Relative weights for each part, e.g. ``[1, 1, 1]`` for
                an even three-way split, or ``[2, 1]`` for a 2:1 split.
                Every ratio must be a positive integer.

        Returns:
            A list of ``Money`` values, one per ratio, in the same order,
            summing exactly to ``self``.

        Raises:
            ValidationError: If ``ratios`` is empty or contains a
                non-positive value.
        """
        if not ratios:
            raise ValidationError("allocate requires at least one ratio")
        if any(r <= 0 for r in ratios):
            raise ValidationError("allocate ratios must all be positive")

        quantum = _quantum(self._currency)
        total_units = int((self._amount / quantum).to_integral_value(rounding=ROUND_DOWN))
        ratio_total = sum(ratios)

        shares = [(total_units * ratio) // ratio_total for ratio in ratios]
        remainders = [
            (index, (total_units * ratio) % ratio_total) for index, ratio in enumerate(ratios)
        ]
        leftover = total_units - sum(shares)

        remainders.sort(key=lambda pair: pair[1], reverse=True)
        for index, _ in remainders[:leftover]:
            shares[index] += 1

        return [Money(share * quantum, self._currency) for share in shares]

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
