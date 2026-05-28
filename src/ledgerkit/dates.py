"""Calendar period helpers.

Everything here is pure date arithmetic: no clock reads, no I/O. Callers get
the current date from an injected :class:`~ledgerkit.clock.Clock` and pass it
in explicitly.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from ledgerkit.errors import ValidationError


def month_start(d: date) -> date:
    return d.replace(day=1)


def month_end(d: date) -> date:
    last_day = calendar.monthrange(d.year, d.month)[1]
    return d.replace(day=last_day)


def quarter_of(d: date) -> int:
    return (d.month - 1) // 3 + 1


def quarter_start(d: date) -> date:
    q = quarter_of(d)
    first_month = 3 * (q - 1) + 1
    return date(d.year, first_month, 1)


def quarter_end(d: date) -> date:
    start = quarter_start(d)
    end_month = start.month + 2
    return month_end(date(start.year, end_month, 1))


def year_start(d: date) -> date:
    return date(d.year, 1, 1)


def year_end(d: date) -> date:
    return date(d.year, 12, 31)


def is_leap_year(year: int) -> bool:
    return calendar.isleap(year)


@dataclass(frozen=True, slots=True)
class Period:
    """An inclusive date range: ``start`` and ``end`` are both in the period."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValidationError(
                f"period start {self.start} is after end {self.end}"
            )

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

    def overlaps(self, other: Period) -> bool:
        return self.start <= other.end and other.start <= self.end

    def days(self) -> int:
        return (self.end - self.start).days + 1


@dataclass(frozen=True, slots=True)
class FiscalCalendar:
    """A fiscal calendar defined by the month its fiscal year starts in.

    ``start_month=1`` is a calendar-year fiscal calendar.
    """

    start_month: int = 1

    def __post_init__(self) -> None:
        if not 1 <= self.start_month <= 12:
            raise ValidationError(f"start_month must be 1-12, got {self.start_month}")

    def fiscal_year_of(self, d: date) -> int:
        """Return the fiscal year label a date falls in.

        The fiscal year is labeled by the calendar year its *start* falls in.
        """
        if d.month >= self.start_month:
            return d.year
        return d.year - 1

    def fiscal_year_start(self, fiscal_year: int) -> date:
        return date(fiscal_year, self.start_month, 1)

    def fiscal_year_end(self, fiscal_year: int) -> date:
        return self.fiscal_year_start(fiscal_year + 1) - timedelta(days=1)

    def fiscal_period(self, fiscal_year: int) -> Period:
        return Period(
            start=self.fiscal_year_start(fiscal_year),
            end=self.fiscal_year_end(fiscal_year),
        )
