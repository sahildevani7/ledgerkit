"""Typed identifiers.

Every entity persisted by ledgerkit is keyed by a SQLite-assigned integer
surrogate key. These ``NewType`` wrappers keep an ``AccountId`` from being
passed where an ``EntryId`` is expected, without adding runtime overhead.
"""

from __future__ import annotations

from typing import NewType

AccountId = NewType("AccountId", int)
EntryId = NewType("EntryId", int)
LineId = NewType("LineId", int)
ImportBatchId = NewType("ImportBatchId", int)
