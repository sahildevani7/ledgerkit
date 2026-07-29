"""Persistence for journal entries and their lines."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import date, datetime

from ledgerkit.clock import Clock
from ledgerkit.currency import get_currency
from ledgerkit.errors import NotFoundError, ValidationError
from ledgerkit.ids import AccountId, EntryId, ImportBatchId, LineId
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.money import Money


class JournalRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def create(self, entry: JournalEntry, clock: Clock) -> JournalEntry:
        if entry.id is not None:
            raise ValidationError("cannot create an entry that already has an id")
        created_at = clock.now()
        cursor = self._conn.execute(
            "INSERT INTO journal_entries (entry_date, memo, created_at, import_batch_id) "
            "VALUES (?, ?, ?, ?)",
            (
                entry.entry_date.isoformat(),
                entry.memo,
                created_at.isoformat(),
                entry.import_batch_id,
            ),
        )
        entry_id = EntryId(cursor.lastrowid)  # type: ignore[arg-type]

        persisted_lines: list[Line] = []
        for line in entry.lines:
            line_cursor = self._conn.execute(
                "INSERT INTO journal_lines (entry_id, account_id, amount, currency_code) "
                "VALUES (?, ?, ?, ?)",
                (
                    entry_id,
                    line.account_id,
                    str(line.amount.amount),
                    line.amount.currency.code,
                ),
            )
            new_line_id = LineId(line_cursor.lastrowid)  # type: ignore[arg-type]
            persisted_lines.append(replace(line, id=new_line_id))

        return replace(entry, id=entry_id, lines=tuple(persisted_lines), created_at=created_at)

    def get(self, entry_id: EntryId) -> JournalEntry:
        entry_row = self._conn.execute(
            "SELECT id, entry_date, memo, created_at, import_batch_id "
            "FROM journal_entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if entry_row is None:
            raise NotFoundError(f"no journal entry with id {entry_id}")
        return _row_to_entry(entry_row, self._fetch_lines(entry_row["id"]))

    def list_all(self, *, start: date | None = None, end: date | None = None) -> list[JournalEntry]:
        query = "SELECT id, entry_date, memo, created_at, import_batch_id FROM journal_entries"
        clauses: list[str] = []
        params: list[str] = []
        if start is not None:
            clauses.append("entry_date >= ?")
            params.append(start.isoformat())
        if end is not None:
            clauses.append("entry_date <= ?")
            params.append(end.isoformat())
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY entry_date, id"
        entry_rows = self._conn.execute(query, params).fetchall()
        return [
            _row_to_entry(entry_row, self._fetch_lines(entry_row["id"])) for entry_row in entry_rows
        ]

    def list_for_import_batch(self, import_batch_id: ImportBatchId) -> list[JournalEntry]:
        """Every entry created as part of a given import batch, oldest first."""
        entry_rows = self._conn.execute(
            "SELECT id, entry_date, memo, created_at, import_batch_id FROM journal_entries "
            "WHERE import_batch_id = ? ORDER BY id",
            (import_batch_id,),
        ).fetchall()
        return [
            _row_to_entry(entry_row, self._fetch_lines(entry_row["id"])) for entry_row in entry_rows
        ]

    def count(self) -> int:
        """The total number of posted journal entries."""
        (total,) = self._conn.execute("SELECT COUNT(*) FROM journal_entries").fetchone()
        return int(total)

    def _fetch_lines(self, entry_id: int) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT id, account_id, amount, currency_code FROM journal_lines "
            "WHERE entry_id = ? ORDER BY id",
            (entry_id,),
        ).fetchall()


def _row_to_entry(entry_row: sqlite3.Row, line_rows: list[sqlite3.Row]) -> JournalEntry:
    lines = tuple(
        Line(
            id=LineId(r["id"]),
            account_id=AccountId(r["account_id"]),
            amount=Money(r["amount"], get_currency(r["currency_code"])),
        )
        for r in line_rows
    )
    import_batch_id = (
        ImportBatchId(entry_row["import_batch_id"])
        if entry_row["import_batch_id"] is not None
        else None
    )
    return JournalEntry(
        id=EntryId(entry_row["id"]),
        entry_date=date.fromisoformat(entry_row["entry_date"]),
        lines=lines,
        memo=entry_row["memo"],
        import_batch_id=import_batch_id,
        created_at=datetime.fromisoformat(entry_row["created_at"]),
    )
