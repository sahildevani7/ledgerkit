from __future__ import annotations

import pytest

from ledgerkit.accounts.model import Account, AccountType, NormalBalance
from ledgerkit.errors import ValidationError


@pytest.mark.parametrize(
    "account_type,expected",
    [
        (AccountType.ASSET, NormalBalance.DEBIT),
        (AccountType.EXPENSE, NormalBalance.DEBIT),
        (AccountType.LIABILITY, NormalBalance.CREDIT),
        (AccountType.EQUITY, NormalBalance.CREDIT),
        (AccountType.INCOME, NormalBalance.CREDIT),
    ],
)
def test_normal_balance(account_type, expected):
    assert account_type.normal_balance == expected


def test_account_construction():
    account = Account(code="1000", name="Cash", type=AccountType.ASSET)
    assert account.code == "1000"
    assert account.id is None
    assert account.is_active


def test_account_rejects_blank_code():
    with pytest.raises(ValidationError):
        Account(code="  ", name="Cash", type=AccountType.ASSET)


def test_account_rejects_blank_name():
    with pytest.raises(ValidationError):
        Account(code="1000", name=" ", type=AccountType.ASSET)


def test_account_is_frozen():
    account = Account(code="1000", name="Cash", type=AccountType.ASSET)
    with pytest.raises(AttributeError):
        account.name = "Other"  # type: ignore[misc]


def test_account_default_is_active_true():
    assert Account(code="1000", name="Cash", type=AccountType.ASSET).is_active


def test_display_label():
    account = Account(code="1000", name="Cash", type=AccountType.ASSET)
    assert account.display_label == "1000 Cash"
