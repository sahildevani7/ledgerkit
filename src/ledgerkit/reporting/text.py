"""The one shipped renderer: a fixed-width plain text table."""

from __future__ import annotations

from ledgerkit.ledger.trial_balance import TrialBalance

_CODE_WIDTH = 12
_NAME_WIDTH = 24
_AMOUNT_WIDTH = 14
_RULE_WIDTH = _CODE_WIDTH + _NAME_WIDTH + 2 * _AMOUNT_WIDTH


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
