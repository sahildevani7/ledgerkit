"""Clock: the one place wall-clock time is allowed to enter the system.

Every part of ledgerkit that needs "now" takes a :class:`Clock` rather than
calling :func:`datetime.datetime.now` directly, so tests can pin time and
behavior never depends on when the code happens to run.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Anything that can report the current date and time."""

    def now(self) -> datetime: ...

    def today(self) -> date: ...


class SystemClock:
    """The one real implementation: reads the actual system clock."""

    def now(self) -> datetime:
        return datetime.now()

    def today(self) -> date:
        return datetime.now().date()


class FixedClock:
    """A clock pinned to a fixed instant, for deterministic tests."""

    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed

    def today(self) -> date:
        return self._fixed.date()

    def advance(self, delta: timedelta) -> None:
        self._fixed = self._fixed + delta

    def set(self, fixed: datetime) -> None:
        self._fixed = fixed
