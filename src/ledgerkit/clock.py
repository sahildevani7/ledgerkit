"""Clock: the one place wall-clock time is allowed to enter the system.

Every part of ledgerkit that needs "now" takes a :class:`Clock` rather than
calling :func:`datetime.datetime.now` directly, so tests can pin time and
behavior never depends on when the code happens to run. This matters more
than it might look: a test that posts a journal entry and checks its
``created_at`` timestamp would otherwise need to tolerate a small time
window, which is exactly the kind of near-miss flakiness a repeatedly-run
test suite eventually surfaces.

There are exactly two implementations, and there should stay exactly two:
:class:`SystemClock` for real use, and :class:`FixedClock` for tests. A
third implementation (say, a clock that ticks forward by a fixed step
each call) would be solving a problem ledgerkit doesn't have yet.
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
    """The one real implementation: reads the actual system clock.

    Constructed exactly once, at the composition root — see
    :func:`ledgerkit.cli.main.main` — and threaded down into whatever
    needs it. Nothing below the CLI entry point constructs a
    ``SystemClock`` itself.
    """

    def now(self) -> datetime:
        return datetime.now()

    def today(self) -> date:
        return datetime.now().date()


class FixedClock:
    """A clock pinned to a fixed instant, for deterministic tests.

    ``now()`` and ``today()`` always return the same instant until
    explicitly moved with :meth:`advance` or :meth:`set` — there is no
    hidden auto-advance, so a test can post several entries in sequence
    and expect them all to carry an identical timestamp unless it moves
    the clock itself.
    """

    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed

    def today(self) -> date:
        return self._fixed.date()

    def advance(self, delta: timedelta) -> None:
        """Move the clock forward (or backward, with a negative delta)."""
        self._fixed = self._fixed + delta

    def set(self, fixed: datetime) -> None:
        """Jump the clock directly to a new instant."""
        self._fixed = fixed
