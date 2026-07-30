"""Persistence for accounts."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

from ledgerkit.accounts.model import Account, AccountType
from ledgerkit.accounts.tree import ChartOfAccounts
from ledgerkit.errors import DuplicateError, NotFoundError, ValidationError
from ledgerkit.ids import AccountId

_SELECT_COLUMNS = "id, code, name, type, parent_id, is_active"


class AccountRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def create(self, account: Account) -> Account:
        if account.id is not None:
            raise ValidationError("cannot create an account that already has an id")
        if account.parent_id is not None:
            self.get(account.parent_id)
        try:
            cursor = self._conn.execute(
                "INSERT INTO accounts (code, name, type, parent_id, is_active) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    account.code,
                    account.name,
                    account.type.value,
                    account.parent_id,
                    1 if account.is_active else 0,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateError(f"account code already exists: {account.code}") from exc
        new_id = AccountId(cursor.lastrowid)  # type: ignore[arg-type]
        return replace(account, id=new_id)

    def get(self, account_id: AccountId) -> Account:
        row = self._conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"no account with id {account_id}")
        return _row_to_account(row)

    def get_by_code(self, code: str) -> Account:
        row = self._conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM accounts WHERE code = ?", (code,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"no account with code {code!r}")
        return _row_to_account(row)

    def list_all(self) -> list[Account]:
        rows = self._conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM accounts ORDER BY code"
        ).fetchall()
        return [_row_to_account(r) for r in rows]

    def chart(self) -> ChartOfAccounts:
        return ChartOfAccounts(self.list_all())

    def reparent(self, account_id: AccountId, new_parent_id: AccountId | None) -> Account:
        account = self.get(account_id)
        if new_parent_id is not None:
            self.get(new_parent_id)
            chart = self.chart()
            if chart.would_create_cycle(account_id, new_parent_id):
                raise ValidationError(
                    f"reparenting {account_id} under {new_parent_id} would create a cycle"
                )
        self._conn.execute(
            "UPDATE accounts SET parent_id = ? WHERE id = ?", (new_parent_id, account_id)
        )
        return replace(account, parent_id=new_parent_id)

    def set_active(self, account_id: AccountId, is_active: bool) -> Account:
        self.get(account_id)
        self._conn.execute(
            "UPDATE accounts SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, account_id),
        )
        return self.get(account_id)

    def rename(self, account_id: AccountId, new_name: str) -> Account:
        """Rename an account, leaving its code and hierarchy untouched.

        A name is display metadata, not an identifier — nothing else in
        ledgerkit references an account by name, so renaming one has no
        effect on any journal entry or query result beyond this account's
        own ``name`` field.

        Raises:
            NotFoundError: If ``account_id`` doesn't exist.
            ValidationError: If ``new_name`` is blank.
        """
        self.get(account_id)
        if not new_name.strip():
            raise ValidationError("account name must not be empty")
        self._conn.execute(
            "UPDATE accounts SET name = ? WHERE id = ?", (new_name, account_id)
        )
        return self.get(account_id)

    def exists(self, code: str) -> bool:
        """Whether an account with ``code`` has been created."""
        row = self._conn.execute("SELECT 1 FROM accounts WHERE code = ?", (code,)).fetchone()
        return row is not None

    def count(self) -> int:
        """The total number of accounts, active and inactive."""
        (total,) = self._conn.execute("SELECT COUNT(*) FROM accounts").fetchone()
        return int(total)

    def search(self, code_prefix: str) -> list[Account]:
        """Accounts whose code starts with ``code_prefix``, sorted by code.

        Useful for a chart of accounts organized by numeric range (e.g.
        every ``1xxx`` code is an asset) — ``search("1")`` finds them all
        without the caller needing to know the full hierarchy.
        """
        rows = self._conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM accounts WHERE code LIKE ? ORDER BY code",
            (f"{code_prefix}%",),
        ).fetchall()
        return [_row_to_account(r) for r in rows]


def _row_to_account(row: sqlite3.Row) -> Account:
    return Account(
        id=AccountId(row["id"]),
        code=row["code"],
        name=row["name"],
        type=AccountType(row["type"]),
        parent_id=AccountId(row["parent_id"]) if row["parent_id"] is not None else None,
        is_active=bool(row["is_active"]),
    )
