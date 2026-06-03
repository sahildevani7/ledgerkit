"""The Migration type shared by every numbered migration module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Migration:
    """A single, ordered schema change.

    ``version`` numbers must be contiguous starting at 1; the runner
    enforces that no version is skipped.
    """

    version: int
    name: str
    sql: str
