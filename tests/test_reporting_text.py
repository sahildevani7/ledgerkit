from __future__ import annotations

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.ids import AccountId
from ledgerkit.ledger.trial_balance import TrialBalance, TrialBalanceRow
from ledgerkit.money import Money
from ledgerkit.reporting.text import TextRenderer


def _account(code, name):
    return Account(id=AccountId(1), code=code, name=name, type=AccountType.ASSET)


def _row(code, name, debit=None, credit=None):
    return TrialBalanceRow(
        account=_account(code, name),
        debit=debit if debit is not None else Money.zero(),
        credit=credit if credit is not None else Money.zero(),
    )


def test_render_empty_trial_balance_has_header_and_totals():
    tb = TrialBalance(as_of=None, rows=())
    output = TextRenderer().render_trial_balance(tb)
    assert "Account" in output
    assert "TOTAL" in output


def test_render_includes_account_code_and_name():
    tb = TrialBalance(as_of=None, rows=(_row("1000", "Checking", debit=Money(100)),))
    output = TextRenderer().render_trial_balance(tb)
    assert "1000" in output
    assert "Checking" in output


def test_render_shows_debit_and_credit_amounts():
    tb = TrialBalance(as_of=None, rows=(_row("1000", "Checking", debit=Money(100)),))
    output = TextRenderer().render_trial_balance(tb)
    assert "100.00" in output


def test_render_totals_row_sums_all_rows():
    tb = TrialBalance(
        as_of=None,
        rows=(
            _row("1000", "Checking", debit=Money(100)),
            _row("2000", "Loan", credit=Money(100)),
        ),
    )
    output = TextRenderer().render_trial_balance(tb)
    total_line = next(line for line in output.splitlines() if line.startswith("TOTAL"))
    assert "100.00" in total_line


def test_render_truncates_long_account_names():
    long_name = "A" * 50
    tb = TrialBalance(as_of=None, rows=(_row("1000", long_name),))
    output = TextRenderer().render_trial_balance(tb)
    lines = output.splitlines()
    assert len(lines[2]) == len(lines[0])


def test_render_output_is_deterministic_for_same_input():
    tb = TrialBalance(as_of=None, rows=(_row("1000", "Checking", debit=Money(100)),))
    renderer = TextRenderer()
    assert renderer.render_trial_balance(tb) == renderer.render_trial_balance(tb)
