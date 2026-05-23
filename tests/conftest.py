from __future__ import annotations

from datetime import datetime

import pytest

from ledgerkit.clock import FixedClock


@pytest.fixture
def fixed_clock() -> FixedClock:
    return FixedClock(datetime(2026, 1, 15, 12, 0, 0))
