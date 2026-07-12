"""The Renderer protocol: turns a trial balance into a display string."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ledgerkit.ledger.trial_balance import TrialBalance


@runtime_checkable
class Renderer(Protocol):
    def render_trial_balance(self, trial_balance: TrialBalance) -> str: ...
