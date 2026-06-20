"""Currency value object.

ledgerkit's base currency is always Canadian dollars. This module exists as
its own seam so a future multi-currency mode has somewhere to plug in
without touching :mod:`ledgerkit.money`.
"""

from __future__ import annotations

from dataclasses import dataclass

from ledgerkit.errors import ValidationError


@dataclass(frozen=True, slots=True)
class Currency:
    """A currency: its ISO 4217 code and its minor-unit exponent.

    ``exponent`` is the number of decimal places a minor unit represents,
    e.g. 2 for CAD (cents).
    """

    code: str
    exponent: int

    def __post_init__(self) -> None:
        if len(self.code) != 3 or not self.code.isalpha() or not self.code.isupper():
            raise ValueError(f"currency code must be 3 uppercase letters, got {self.code!r}")
        if self.exponent < 0:
            raise ValueError(f"exponent must be non-negative, got {self.exponent}")

    def __str__(self) -> str:
        return self.code


CAD = Currency(code="CAD", exponent=2)

_REGISTRY: dict[str, Currency] = {CAD.code: CAD}


def default_currency() -> Currency:
    """Return the ledger's base currency."""
    return CAD


def get_currency(code: str) -> Currency:
    """Look up a registered currency by its ISO code.

    Only :data:`CAD` is registered today; storage round-trips a currency
    code through here rather than assuming CAD, so a future registration
    of a second currency doesn't require touching the storage layer.
    """
    try:
        return _REGISTRY[code]
    except KeyError:
        raise ValidationError(f"unsupported currency: {code!r}") from None
