"""The one shipped renderer: a fixed-width plain text table."""

from __future__ import annotations

from collections.abc import Sequence

from ledgerkit.accounts.model import Account
from ledgerkit.ledger.queries import AccountActivity
from ledgerkit.ledger.trial_balance import TrialBalance
from ledgerkit.money import Money

_CODE_WIDTH = 12
_NAME_WIDTH = 24
_AMOUNT_WIDTH = 14
_RULE_WIDTH = _CODE_WIDTH + _NAME_WIDTH + 2 * _AMOUNT_WIDTH

_DATE_WIDTH = 12
_MEMO_WIDTH = 30
_ACTIVITY_AMOUNT_WIDTH = 14
_ACTIVITY_RULE_WIDTH = _DATE_WIDTH + _MEMO_WIDTH + _ACTIVITY_AMOUNT_WIDTH


class TextRenderer:
    def render_trial_balance(self, trial_balance: TrialBalance) -> str:
        header = (
            "Account".ljust(_CODE_WIDTH)
            + "Name".ljust(_NAME_WIDTH)
            + "Debit".rjust(_AMOUNT_WIDTH)
            + "Credit".rjust(_AMOUNT_WIDTH)
        )
        rule = "-" * _RULE_WIDTH
        lines = [header, rule]
        for row in trial_balance.rows:
            lines.append(
                row.account.code.ljust(_CODE_WIDTH)
                + row.account.name[: _NAME_WIDTH - 1].ljust(_NAME_WIDTH)
                + row.debit.format().rjust(_AMOUNT_WIDTH)
                + row.credit.format().rjust(_AMOUNT_WIDTH)
            )
        lines.append(rule)
        lines.append(
            "TOTAL".ljust(_CODE_WIDTH + _NAME_WIDTH)
            + trial_balance.total_debits().format().rjust(_AMOUNT_WIDTH)
            + trial_balance.total_credits().format().rjust(_AMOUNT_WIDTH)
        )
        return "\n".join(lines)

    def render_account_activity(self, account: Account, activity: Sequence[AccountActivity]) -> str:
        header = f"{account.code}  {account.name} ({account.type.value})"
        column_header = (
            "Date".ljust(_DATE_WIDTH)
            + "Memo".ljust(_MEMO_WIDTH)
            + "Amount".rjust(_ACTIVITY_AMOUNT_WIDTH)
        )
        rule = "-" * _ACTIVITY_RULE_WIDTH
        lines = [header, rule, column_header, rule]

        running_balance = Money.zero()
        for row in activity:
            running_balance = running_balance + row.amount
            memo = (row.memo or "").strip()
            lines.append(
                row.entry_date.isoformat().ljust(_DATE_WIDTH)
                + memo[: _MEMO_WIDTH - 1].ljust(_MEMO_WIDTH)
                + row.amount.format().rjust(_ACTIVITY_AMOUNT_WIDTH)
            )

        lines.append(rule)
        lines.append(
            "BALANCE".ljust(_DATE_WIDTH + _MEMO_WIDTH)
            + running_balance.format().rjust(_ACTIVITY_AMOUNT_WIDTH)
        )
        return "\n".join(lines)
