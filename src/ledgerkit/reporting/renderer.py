"""The Renderer protocol: turns query results into display strings.

There's one shipped implementation
(:class:`~ledgerkit.reporting.text.TextRenderer`). A future renderer —
say, one that emits JSON instead of plain text — would implement this
same protocol rather than requiring changes anywhere that calls it: both
of the ``render_*_report`` glue functions in this package, and both CLI
report commands, take a ``Renderer`` and never construct
``TextRenderer`` themselves except at the CLI's own composition root.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ledgerkit.accounts.model import Account
from ledgerkit.ledger.queries import AccountActivity
from ledgerkit.ledger.trial_balance import TrialBalance


@runtime_checkable
class Renderer(Protocol):
    """Something that can turn a query result into a display string."""

    def render_trial_balance(self, trial_balance: TrialBalance) -> str:
        """Render a full trial balance: every account, debits, credits, totals."""
        ...

    def render_account_activity(
        self, account: Account, activity: Sequence[AccountActivity]
    ) -> str:
        """Render one account's transaction history, oldest first."""
        ...
