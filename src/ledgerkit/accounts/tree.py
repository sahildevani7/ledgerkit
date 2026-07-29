"""An in-memory view of the chart of accounts as a hierarchy.

:class:`ChartOfAccounts` is built from a flat list of accounts (as read from
storage) and answers hierarchy questions — children, ancestors,
descendants, and whether a proposed re-parent would create a cycle. It does
not itself write anything; :mod:`ledgerkit.accounts.repository` uses it to
validate a re-parent before persisting it.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from ledgerkit.accounts.model import Account
from ledgerkit.errors import NotFoundError
from ledgerkit.ids import AccountId


class ChartOfAccounts:
    def __init__(self, accounts: Iterable[Account]) -> None:
        self._by_id: dict[AccountId, Account] = {}
        children: dict[AccountId | None, list[AccountId]] = defaultdict(list)
        for account in accounts:
            if account.id is None:
                raise ValueError("ChartOfAccounts requires persisted accounts (id is not None)")
            self._by_id[account.id] = account
            children[account.parent_id].append(account.id)
        for ids in children.values():
            ids.sort(key=lambda aid: self._by_id[aid].code)
        self._children = children

    def get(self, account_id: AccountId) -> Account:
        try:
            return self._by_id[account_id]
        except KeyError:
            raise NotFoundError(f"no account with id {account_id}") from None

    def roots(self) -> list[Account]:
        return [self._by_id[i] for i in self._children.get(None, [])]

    def children_of(self, account_id: AccountId) -> list[Account]:
        self.get(account_id)  # validate existence
        return [self._by_id[i] for i in self._children.get(account_id, [])]

    def ancestors_of(self, account_id: AccountId) -> list[Account]:
        """Return ancestors ordered from immediate parent to root."""
        result: list[Account] = []
        current = self.get(account_id)
        seen: set[AccountId] = {account_id}
        while current.parent_id is not None:
            if current.parent_id in seen:
                raise ValueError(f"cycle detected in chart of accounts at {current.parent_id}")
            parent = self.get(current.parent_id)
            result.append(parent)
            seen.add(parent.id)  # type: ignore[arg-type]
            current = parent
        return result

    def descendants_of(self, account_id: AccountId) -> list[Account]:
        """Return all descendants, breadth-first, in deterministic order."""
        self.get(account_id)
        result: list[Account] = []
        queue = list(self._children.get(account_id, []))
        while queue:
            child_id = queue.pop(0)
            child = self._by_id[child_id]
            result.append(child)
            queue.extend(self._children.get(child_id, []))
        return result

    def would_create_cycle(self, account_id: AccountId, new_parent_id: AccountId) -> bool:
        """Would re-parenting ``account_id`` under ``new_parent_id`` create a cycle?

        True if ``new_parent_id`` is ``account_id`` itself or one of its
        descendants.
        """
        if account_id == new_parent_id:
            return True
        descendant_ids = {d.id for d in self.descendants_of(account_id)}
        return new_parent_id in descendant_ids

    def all_accounts(self) -> list[Account]:
        return sorted(self._by_id.values(), key=lambda a: a.code)

    def depth_of(self, account_id: AccountId) -> int:
        """How many ancestors ``account_id`` has; ``0`` for a root account."""
        return len(self.ancestors_of(account_id))

    def path_to(self, account_id: AccountId) -> list[Account]:
        """The breadcrumb path from the root down to ``account_id``, inclusive.

        This is :meth:`ancestors_of` reversed with the account itself
        appended — convenient for rendering something like
        ``Assets > Current Assets > Cash`` without the caller having to
        remember which order ``ancestors_of`` returns things in.
        """
        return [*reversed(self.ancestors_of(account_id)), self.get(account_id)]

    def is_root(self, account_id: AccountId) -> bool:
        return self.get(account_id).parent_id is None
