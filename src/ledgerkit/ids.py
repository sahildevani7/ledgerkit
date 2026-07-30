"""Typed identifiers.

Every entity persisted by ledgerkit is keyed by a SQLite ``AUTOINCREMENT``
integer surrogate key — never a randomly generated id, since ledgerkit
avoids unseeded randomness everywhere and a monotonically increasing
integer is also simply easier to read in a debugger or a SQL shell.

These ``NewType`` wrappers exist purely for static type checking: at
runtime an ``AccountId`` *is* an ``int``, with zero wrapping overhead, but
mypy will flag passing one where an ``EntryId`` is expected. That's worth
having — every repository method takes an id of a specific entity type,
and a mixed-up id is exactly the kind of bug that's invisible until the
wrong row comes back.
"""

from __future__ import annotations

from typing import NewType

AccountId = NewType("AccountId", int)
EntryId = NewType("EntryId", int)
LineId = NewType("LineId", int)
ImportBatchId = NewType("ImportBatchId", int)
