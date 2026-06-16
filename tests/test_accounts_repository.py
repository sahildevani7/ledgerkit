from __future__ import annotations

import pytest

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.errors import DuplicateError, NotFoundError, ValidationError


@pytest.fixture
def repo(migrated_conn):
    return AccountRepository(migrated_conn)


def test_create_assigns_id(repo):
    account = repo.create(Account(code="1000", name="Cash", type=AccountType.ASSET))
    assert account.id is not None


def test_create_rejects_account_with_id(repo):
    with pytest.raises(ValidationError):
        repo.create(Account(code="1000", name="Cash", type=AccountType.ASSET, id=1))  # type: ignore[arg-type]


def test_create_duplicate_code_raises(repo):
    repo.create(Account(code="1000", name="Cash", type=AccountType.ASSET))
    with pytest.raises(DuplicateError):
        repo.create(Account(code="1000", name="Cash Again", type=AccountType.ASSET))


def test_create_with_missing_parent_raises(repo):
    with pytest.raises(NotFoundError):
        repo.create(Account(code="1000", name="Cash", type=AccountType.ASSET, parent_id=999))  # type: ignore[arg-type]


def test_get_round_trips(repo):
    created = repo.create(Account(code="1000", name="Cash", type=AccountType.ASSET))
    fetched = repo.get(created.id)
    assert fetched == created


def test_get_missing_raises(repo):
    with pytest.raises(NotFoundError):
        repo.get(999)  # type: ignore[arg-type]


def test_get_by_code(repo):
    created = repo.create(Account(code="1000", name="Cash", type=AccountType.ASSET))
    assert repo.get_by_code("1000") == created


def test_get_by_code_missing_raises(repo):
    with pytest.raises(NotFoundError):
        repo.get_by_code("nope")


def test_list_all_sorted_by_code(repo):
    repo.create(Account(code="2000", name="Loans", type=AccountType.LIABILITY))
    repo.create(Account(code="1000", name="Cash", type=AccountType.ASSET))
    codes = [a.code for a in repo.list_all()]
    assert codes == ["1000", "2000"]


def test_create_with_valid_parent(repo):
    parent = repo.create(Account(code="1000", name="Assets", type=AccountType.ASSET))
    child = repo.create(
        Account(code="1100", name="Cash", type=AccountType.ASSET, parent_id=parent.id)
    )
    assert child.parent_id == parent.id


def test_chart_reflects_hierarchy(repo):
    parent = repo.create(Account(code="1000", name="Assets", type=AccountType.ASSET))
    repo.create(Account(code="1100", name="Cash", type=AccountType.ASSET, parent_id=parent.id))
    chart = repo.chart()
    assert [a.code for a in chart.children_of(parent.id)] == ["1100"]


def test_reparent_updates_parent(repo):
    a = repo.create(Account(code="1000", name="A", type=AccountType.ASSET))
    b = repo.create(Account(code="2000", name="B", type=AccountType.LIABILITY))
    c = repo.create(Account(code="1100", name="C", type=AccountType.ASSET, parent_id=a.id))
    reparented = repo.reparent(c.id, b.id)
    assert reparented.parent_id == b.id
    assert repo.get(c.id).parent_id == b.id


def test_reparent_to_none_makes_root(repo):
    a = repo.create(Account(code="1000", name="A", type=AccountType.ASSET))
    c = repo.create(Account(code="1100", name="C", type=AccountType.ASSET, parent_id=a.id))
    reparented = repo.reparent(c.id, None)
    assert reparented.parent_id is None


def test_reparent_rejects_cycle(repo):
    a = repo.create(Account(code="1000", name="A", type=AccountType.ASSET))
    b = repo.create(Account(code="1100", name="B", type=AccountType.ASSET, parent_id=a.id))
    with pytest.raises(ValidationError):
        repo.reparent(a.id, b.id)


def test_reparent_rejects_self(repo):
    a = repo.create(Account(code="1000", name="A", type=AccountType.ASSET))
    with pytest.raises(ValidationError):
        repo.reparent(a.id, a.id)


def test_reparent_missing_account_raises(repo):
    with pytest.raises(NotFoundError):
        repo.reparent(999, None)  # type: ignore[arg-type]


def test_reparent_missing_new_parent_raises(repo):
    a = repo.create(Account(code="1000", name="A", type=AccountType.ASSET))
    with pytest.raises(NotFoundError):
        repo.reparent(a.id, 999)  # type: ignore[arg-type]


def test_set_active_false(repo):
    a = repo.create(Account(code="1000", name="A", type=AccountType.ASSET))
    updated = repo.set_active(a.id, False)
    assert not updated.is_active
    assert not repo.get(a.id).is_active


def test_set_active_missing_raises(repo):
    with pytest.raises(NotFoundError):
        repo.set_active(999, False)  # type: ignore[arg-type]
