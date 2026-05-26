from __future__ import annotations

from datetime import date, datetime, timedelta

from ledgerkit.clock import Clock, FixedClock, SystemClock


def test_fixed_clock_now_and_today():
    clock = FixedClock(datetime(2026, 3, 17, 9, 30))
    assert clock.now() == datetime(2026, 3, 17, 9, 30)
    assert clock.today() == date(2026, 3, 17)


def test_fixed_clock_advance():
    clock = FixedClock(datetime(2026, 3, 17, 9, 30))
    clock.advance(timedelta(days=2))
    assert clock.today() == date(2026, 3, 19)


def test_fixed_clock_set():
    clock = FixedClock(datetime(2026, 3, 17, 9, 30))
    clock.set(datetime(2030, 1, 1))
    assert clock.today() == date(2030, 1, 1)


def test_system_clock_returns_real_time():
    clock = SystemClock()
    before = datetime.now()
    reported = clock.now()
    after = datetime.now()
    assert before <= reported <= after


def test_system_clock_today_matches_now_date():
    clock = SystemClock()
    assert clock.today() == clock.now().date()


def test_fixed_clock_satisfies_clock_protocol():
    clock: Clock = FixedClock(datetime(2026, 1, 1))
    assert isinstance(clock, Clock)


def test_system_clock_satisfies_clock_protocol():
    clock: Clock = SystemClock()
    assert isinstance(clock, Clock)
