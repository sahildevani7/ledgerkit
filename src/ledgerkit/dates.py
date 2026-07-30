"""Calendar period helpers.

Everything here is pure date arithmetic: no clock reads, no I/O. Callers get
the current date from an injected :class:`~ledgerkit.clock.Clock` and pass it
in explicitly. Every function here computes the boundaries of a single,
already-known period (a month, a quarter, a fiscal year, an arbitrary
range) — none of it depends on any other date beyond the one passed in.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from ledgerkit.errors import ValidationError


def month_start(d: date) -> date:
    """The first day of the month ``d`` falls in."""
    return d.replace(day=1)


def month_end(d: date) -> date:
    """The last day of the month ``d`` falls in, accounting for leap years."""
    last_day = calendar.monthrange(d.year, d.month)[1]
    return d.replace(day=last_day)


def week_start(d: date, *, first_weekday: int = 0) -> date:
    """The first day of the calendar week ``d`` falls in.

    Args:
        d: Any date within the target week.
        first_weekday: Which weekday a week starts on, using Python's
            ``date.weekday()`` numbering (``0`` is Monday, ``6`` is
            Sunday). Defaults to Monday, the ISO 8601 convention.
    """
    offset = (d.weekday() - first_weekday) % 7
    return d - timedelta(days=offset)


def week_end(d: date, *, first_weekday: int = 0) -> date:
    """The last day of the calendar week ``d`` falls in. See :func:`week_start`."""
    return week_start(d, first_weekday=first_weekday) + timedelta(days=6)


def quarter_of(d: date) -> int:
    """Which calendar quarter (1-4) ``d`` falls in."""
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
            raise ValidationError(f"period start {self.start} is after end {self.end}")

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

    def __contains__(self, d: date) -> bool:
        """Support ``d in period``, equivalent to :meth:`contains`."""
        return self.contains(d)

    def overlaps(self, other: Period) -> bool:
        """Whether this period shares at least one day with ``other``.

        Periods that only touch at a shared boundary day count as
        overlapping — a period ending on the day another begins is not
        disjoint from it.
        """
        return self.start <= other.end and other.start <= self.end

    def days(self) -> int:
        return (self.end - self.start).days + 1

    def split_by_month(self) -> list[Period]:
        """Break this period into calendar-month-aligned sub-periods.

        The first and last sub-periods are clipped to this period's actual
        start and end; every sub-period in between spans a full calendar
        month. Useful for reporting month-by-month over an arbitrary
        range without special-casing the partial months at either end.

        Returns:
            Sub-periods in chronological order, always non-empty.
        """
        segments: list[Period] = []
        cursor = self.start
        while cursor <= self.end:
            segment_end = min(month_end(cursor), self.end)
            segments.append(Period(start=cursor, end=segment_end))
            cursor = segment_end + timedelta(days=1)
        return segments


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
