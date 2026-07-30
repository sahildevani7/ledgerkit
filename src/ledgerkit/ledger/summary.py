"""A single at-a-glance summary of a ledger's contents.

Answers "what's actually in this database" without the caller needing to
combine an account count, an entry count, and a trial balance check
themselves — useful for a quick sanity check after an import or a batch
of manual postings.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.journal.repository import JournalRepository
from ledgerkit.ledger.trial_balance import build_trial_balance


@dataclass(frozen=True, slots=True)
class LedgerSummary:
    """Counts and a balance check for a ledger, as of the moment it was built."""

    account_count: int
    active_account_count: int
    entry_count: int
    is_balanced: bool


def build_ledger_summary(connection: sqlite3.Connection) -> LedgerSummary:
    """Compute a `LedgerSummary` for the ledger at `connection`."""
    accounts = AccountRepository(connection).list_all()
    entry_count = JournalRepository(connection).count()
    trial_balance = build_trial_balance(connection)
    return LedgerSummary(
        account_count=len(accounts),
        active_account_count=sum(1 for account in accounts if account.is_active),
        entry_count=entry_count,
        is_balanced=trial_balance.is_balanced(),
    )
