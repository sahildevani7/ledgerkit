from __future__ import annotations

import pytest

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.tree import ChartOfAccounts
from ledgerkit.errors import NotFoundError
from ledgerkit.ids import AccountId


def _acc(id_, code, parent_id=None):
    return Account(
        id=AccountId(id_), code=code, name=code, type=AccountType.ASSET, parent_id=parent_id
    )


@pytest.fixture
def chart():
    accounts = [
        _acc(1, "1000"),  # root: assets
        _acc(2, "1100", parent_id=AccountId(1)),  # current assets
        _acc(3, "1110", parent_id=AccountId(2)),  # cash
        _acc(4, "1120", parent_id=AccountId(2)),  # receivables
        _acc(5, "2000"),  # root: liabilities
    ]
    return ChartOfAccounts(accounts)


def test_roots(chart):
    roots = chart.roots()
    assert [a.code for a in roots] == ["1000", "2000"]


def test_children_of(chart):
    children = chart.children_of(AccountId(1))
    assert [a.code for a in children] == ["1100"]


def test_children_of_leaf_is_empty(chart):
    assert chart.children_of(AccountId(3)) == []


def test_children_sorted_by_code(chart):
    children = chart.children_of(AccountId(2))
    assert [a.code for a in children] == ["1110", "1120"]


def test_ancestors_of(chart):
    ancestors = chart.ancestors_of(AccountId(3))
    assert [a.code for a in ancestors] == ["1100", "1000"]


def test_ancestors_of_root_is_empty(chart):
    assert chart.ancestors_of(AccountId(1)) == []


def test_descendants_of(chart):
    descendants = chart.descendants_of(AccountId(1))
    assert {a.code for a in descendants} == {"1100", "1110", "1120"}


def test_descendants_of_leaf_is_empty(chart):
    assert chart.descendants_of(AccountId(3)) == []


def test_get_missing_raises(chart):
    with pytest.raises(NotFoundError):
        chart.get(AccountId(999))


def test_children_of_missing_raises(chart):
    with pytest.raises(NotFoundError):
        chart.children_of(AccountId(999))


def test_would_create_cycle_self(chart):
    assert chart.would_create_cycle(AccountId(1), AccountId(1))


def test_would_create_cycle_descendant(chart):
    assert chart.would_create_cycle(AccountId(1), AccountId(3))


def test_would_not_create_cycle_unrelated(chart):
    assert not chart.would_create_cycle(AccountId(3), AccountId(5))


def test_would_not_create_cycle_reparent_to_sibling(chart):
    assert not chart.would_create_cycle(AccountId(4), AccountId(3))


def test_all_accounts_sorted(chart):
    codes = [a.code for a in chart.all_accounts()]
    assert codes == sorted(codes)


def test_rejects_unpersisted_accounts():
    unpersisted = Account(code="1000", name="Cash", type=AccountType.ASSET)
    with pytest.raises(ValueError):
        ChartOfAccounts([unpersisted])


def test_depth_of_root_is_zero(chart):
    assert chart.depth_of(AccountId(1)) == 0


def test_depth_of_leaf(chart):
    assert chart.depth_of(AccountId(3)) == 2


def test_path_to_root(chart):
    path = chart.path_to(AccountId(1))
    assert [a.code for a in path] == ["1000"]


def test_path_to_leaf(chart):
    path = chart.path_to(AccountId(3))
    assert [a.code for a in path] == ["1000", "1100", "1110"]


def test_path_to_missing_raises(chart):
    with pytest.raises(NotFoundError):
        chart.path_to(AccountId(999))


def test_is_root_true_for_root(chart):
    assert chart.is_root(AccountId(1))


def test_is_root_false_for_child(chart):
    assert not chart.is_root(AccountId(2))
