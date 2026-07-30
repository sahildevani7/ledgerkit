from __future__ import annotations

from datetime import date, timedelta

import pytest

from ledgerkit.dates import (
    FiscalCalendar,
    Period,
    is_leap_year,
    month_end,
    month_start,
    quarter_end,
    quarter_of,
    quarter_start,
    week_end,
    week_start,
    year_end,
    year_start,
)
from ledgerkit.errors import ValidationError


def test_month_start():
    assert month_start(date(2026, 3, 17)) == date(2026, 3, 1)


def test_month_end_31_days():
    assert month_end(date(2026, 3, 17)) == date(2026, 3, 31)


def test_month_end_30_days():
    assert month_end(date(2026, 4, 17)) == date(2026, 4, 30)


def test_month_end_february_leap():
    assert month_end(date(2028, 2, 1)) == date(2028, 2, 29)


def test_month_end_february_non_leap():
    assert month_end(date(2026, 2, 1)) == date(2026, 2, 28)


@pytest.mark.parametrize(
    "month,expected",
    [
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 2),
        (5, 2),
        (6, 2),
        (7, 3),
        (8, 3),
        (9, 3),
        (10, 4),
        (11, 4),
        (12, 4),
    ],
)
def test_quarter_of(month, expected):
    assert quarter_of(date(2026, month, 15)) == expected


def test_quarter_start_and_end():
    d = date(2026, 5, 15)
    assert quarter_start(d) == date(2026, 4, 1)
    assert quarter_end(d) == date(2026, 6, 30)


def test_quarter_start_and_end_q4():
    d = date(2026, 11, 1)
    assert quarter_start(d) == date(2026, 10, 1)
    assert quarter_end(d) == date(2026, 12, 31)


def test_year_start_end():
    d = date(2026, 6, 1)
    assert year_start(d) == date(2026, 1, 1)
    assert year_end(d) == date(2026, 12, 31)


def test_is_leap_year():
    assert is_leap_year(2028)
    assert not is_leap_year(2026)
    assert not is_leap_year(2100)
    assert is_leap_year(2000)


class TestPeriod:
    def test_contains(self):
        p = Period(start=date(2026, 1, 1), end=date(2026, 1, 31))
        assert p.contains(date(2026, 1, 1))
        assert p.contains(date(2026, 1, 31))
        assert p.contains(date(2026, 1, 15))
        assert not p.contains(date(2026, 2, 1))

    def test_dunder_contains_matches_contains(self):
        p = Period(start=date(2026, 1, 1), end=date(2026, 1, 31))
        assert date(2026, 1, 15) in p
        assert date(2026, 2, 1) not in p

    def test_rejects_inverted_range(self):
        with pytest.raises(ValidationError):
            Period(start=date(2026, 2, 1), end=date(2026, 1, 1))

    def test_equal_start_end_is_valid(self):
        p = Period(start=date(2026, 1, 1), end=date(2026, 1, 1))
        assert p.days() == 1

    def test_days(self):
        p = Period(start=date(2026, 1, 1), end=date(2026, 1, 31))
        assert p.days() == 31

    def test_overlaps_true(self):
        a = Period(start=date(2026, 1, 1), end=date(2026, 1, 31))
        b = Period(start=date(2026, 1, 15), end=date(2026, 2, 15))
        assert a.overlaps(b)
        assert b.overlaps(a)

    def test_overlaps_false(self):
        a = Period(start=date(2026, 1, 1), end=date(2026, 1, 31))
        b = Period(start=date(2026, 2, 1), end=date(2026, 2, 28))
        assert not a.overlaps(b)

    def test_overlaps_adjacent_touching_is_overlap(self):
        a = Period(start=date(2026, 1, 1), end=date(2026, 1, 31))
        b = Period(start=date(2026, 1, 31), end=date(2026, 2, 28))
        assert a.overlaps(b)


class TestFiscalCalendar:
    def test_default_is_calendar_year(self):
        cal = FiscalCalendar()
        assert cal.fiscal_year_of(date(2026, 1, 1)) == 2026
        assert cal.fiscal_year_of(date(2026, 12, 31)) == 2026

    def test_rejects_bad_start_month(self):
        with pytest.raises(ValidationError):
            FiscalCalendar(start_month=13)
        with pytest.raises(ValidationError):
            FiscalCalendar(start_month=0)

    def test_offset_fiscal_year_before_start(self):
        cal = FiscalCalendar(start_month=4)
        assert cal.fiscal_year_of(date(2026, 3, 31)) == 2025
        assert cal.fiscal_year_of(date(2026, 4, 1)) == 2026

    def test_fiscal_year_start_and_end(self):
        cal = FiscalCalendar(start_month=4)
        assert cal.fiscal_year_start(2026) == date(2026, 4, 1)
        assert cal.fiscal_year_end(2026) == date(2027, 3, 31)

    def test_fiscal_year_start_and_end_calendar_year(self):
        cal = FiscalCalendar(start_month=1)
        assert cal.fiscal_year_start(2026) == date(2026, 1, 1)
        assert cal.fiscal_year_end(2026) == date(2026, 12, 31)

    def test_fiscal_period(self):
        cal = FiscalCalendar(start_month=7)
        p = cal.fiscal_period(2026)
        assert p.start == date(2026, 7, 1)
        assert p.end == date(2027, 6, 30)

    def test_fiscal_year_end_over_leap_february(self):
        cal = FiscalCalendar(start_month=3)
        assert cal.fiscal_year_end(2027) == date(2028, 2, 29)

    def test_fiscal_year_of_boundary_at_calendar_start(self):
        cal = FiscalCalendar(start_month=10)
        assert cal.fiscal_year_of(date(2026, 9, 30)) == 2025
        assert cal.fiscal_year_of(date(2026, 10, 1)) == 2026

    def test_fiscal_period_days_count(self):
        cal = FiscalCalendar(start_month=1)
        p = cal.fiscal_period(2026)
        assert p.days() == 365

    def test_fiscal_period_days_count_leap_year(self):
        cal = FiscalCalendar(start_month=1)
        p = cal.fiscal_period(2028)
        assert p.days() == 366


class TestPeriodEdgeCases:
    def test_period_of_single_day_does_not_overlap_next_day(self):
        a = Period(start=date(2026, 1, 1), end=date(2026, 1, 1))
        b = Period(start=date(2026, 1, 2), end=date(2026, 1, 2))
        assert not a.overlaps(b)

    def test_period_fully_containing_another(self):
        outer = Period(start=date(2026, 1, 1), end=date(2026, 12, 31))
        inner = Period(start=date(2026, 6, 1), end=date(2026, 6, 30))
        assert outer.overlaps(inner)
        assert inner.overlaps(outer)

    def test_quarter_end_spans_month_boundary_correctly(self):
        assert quarter_end(date(2026, 4, 1)) == date(2026, 6, 30)

    def test_month_end_of_december_stays_in_same_year(self):
        assert month_end(date(2026, 12, 15)) == date(2026, 12, 31)


class TestWeekHelpers:
    def test_week_start_default_monday(self):
        # 2026-07-30 is a Thursday
        assert week_start(date(2026, 7, 30)) == date(2026, 7, 27)

    def test_week_end_default_sunday(self):
        assert week_end(date(2026, 7, 30)) == date(2026, 8, 2)

    def test_week_start_on_the_boundary_day_is_itself(self):
        monday = date(2026, 7, 27)
        assert week_start(monday) == monday

    def test_week_start_custom_first_weekday_sunday(self):
        # first_weekday=6 means weeks start on Sunday
        assert week_start(date(2026, 7, 30), first_weekday=6) == date(2026, 7, 26)

    def test_week_span_is_seven_days(self):
        start = week_start(date(2026, 7, 30))
        end = week_end(date(2026, 7, 30))
        assert (end - start).days == 6


class TestSplitByMonth:
    def test_single_month_period_returns_one_segment(self):
        p = Period(start=date(2026, 3, 5), end=date(2026, 3, 20))
        segments = p.split_by_month()
        assert segments == [p]

    def test_spans_two_months(self):
        p = Period(start=date(2026, 3, 20), end=date(2026, 4, 10))
        segments = p.split_by_month()
        assert segments == [
            Period(start=date(2026, 3, 20), end=date(2026, 3, 31)),
            Period(start=date(2026, 4, 1), end=date(2026, 4, 10)),
        ]

    def test_spans_full_calendar_year(self):
        p = Period(start=date(2026, 1, 1), end=date(2026, 12, 31))
        segments = p.split_by_month()
        assert len(segments) == 12
        assert segments[0] == Period(start=date(2026, 1, 1), end=date(2026, 1, 31))
        assert segments[-1] == Period(start=date(2026, 12, 1), end=date(2026, 12, 31))

    def test_segments_cover_period_with_no_gaps_or_overlaps(self):
        p = Period(start=date(2026, 2, 10), end=date(2026, 5, 3))
        segments = p.split_by_month()
        for earlier, later in zip(segments, segments[1:], strict=False):
            assert later.start == earlier.end + timedelta(days=1)
        assert segments[0].start == p.start
        assert segments[-1].end == p.end

    def test_single_day_period(self):
        p = Period(start=date(2026, 6, 15), end=date(2026, 6, 15))
        assert p.split_by_month() == [p]
