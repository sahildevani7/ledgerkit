# Money and Currency

## Why not `float`

Binary floating point can't represent most decimal fractions exactly —
`0.1 + 0.2 == 0.30000000000000004` in IEEE 754 double precision. In an
accounting system that error compounds across every posting, and it's
exactly the kind of bug that stays invisible until a trial balance is off
by a cent and nobody can find why. `ledgerkit.money.Money` sidesteps the
problem structurally: it stores a `decimal.Decimal`, quantized to the
currency's minor unit, and it never accepts a float as input at all.

## Construction is exact by default

```python
Money(Decimal("10.00"))  # fine — exactly 2 decimal places for CAD
Money(Decimal("10.005"))  # raises ValidationError — too much precision
```

If a value genuinely needs rounding, say so explicitly:

```python
Money.from_rounded(Decimal("10.005"), rounding=ROUND_HALF_UP)  # 10.01
```

There's no library-wide default rounding mode. Every call site that can
produce a fractional minor unit — `from_rounded`, `scaled`, `allocate` —
takes `rounding` as a required argument, so the choice is visible at the
point it matters rather than buried in a global setting.

## Splitting an amount: `allocate`

`Money.allocate(ratios)` divides an amount into proportional parts using
the largest-remainder method: each part is rounded down, and the
minor units left over are handed out one at a time to the parts with the
largest fractional remainder. The parts always sum to exactly the
original amount.

```python
Money(Decimal("10.00")).allocate([1, 1, 1])
# [Money(3.34, CAD), Money(3.33, CAD), Money(3.33, CAD)]
```

## Currency

`ledgerkit.currency.Currency` is a small value object: an ISO 4217 code
and the number of decimal places its minor unit has (2 for CAD, 0 for
JPY). Only `CAD` is registered today — `ledgerkit.currency.get_currency`
is the seam a future multi-currency mode would extend, without
`Money` or the storage layer needing to change.

## What `Money` deliberately doesn't do

- No currency conversion. Adding or comparing two different currencies
  raises `ValidationError` rather than guessing an exchange rate.
- No implicit rounding, anywhere, ever. If an operation might need to
  round, it asks.
- No formatting locale support beyond `format()`'s fixed
  `amount currency-code` layout. Locale-aware display is a presentation
  concern outside the library's scope.
