"""``ledgerkit import``: import a bank statement and post it as journal entries.

Every imported transaction becomes a two-line journal entry against the
statement's account and a contra account the caller names explicitly —
ledgerkit doesn't guess where the other side of an import should land. The
whole file is posted as a single atomic batch, tagged with one import batch
record for provenance.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from ledgerkit.accounts.repository import AccountRepository
from ledgerkit.clock import Clock
from ledgerkit.errors import ValidationError
from ledgerkit.ids import ImportBatchId
from ledgerkit.importers.registry import get_importer
from ledgerkit.journal.entry import JournalEntry, Line
from ledgerkit.journal.repository import JournalRepository
from ledgerkit.storage.unit_of_work import UnitOfWork

_EPILOG = """\
examples:
  ledgerkit --db ledger.db import statement.csv \\
      --account 1000 --contra-account 3000
  ledgerkit --db ledger.db import statement.csv \\
      --account 1000 --contra-account 9999 --dialect generic_csv
"""


def add_arguments(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Register the ``import`` subcommand and its arguments."""
    parser = subparsers.add_parser(
        "import",
        help="import a bank statement",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", help="path to the statement file")
    parser.add_argument("--account", required=True, help="account code the statement belongs to")
    parser.add_argument(
        "--contra-account", required=True, help="account code to balance imported lines against"
    )
    parser.add_argument(
        "--dialect", default="generic_csv", help="which registered importer parses the file"
    )
    parser.set_defaults(handler=run)
    return parser


def run(args: argparse.Namespace, connection: sqlite3.Connection, clock: Clock) -> int:
    """Parse a statement file and post it as one atomic batch of journal entries.

    Every transaction becomes a two-line entry between ``--account`` and
    ``--contra-account``; the whole file, plus the import batch
    provenance record, is written in a single transaction — a malformed
    row midway through the file leaves nothing partially imported.

    Raises:
        ValidationError: If the file can't be read, the dialect isn't
            registered, or the file's content doesn't match the dialect.
        NotFoundError: If ``--account`` or ``--contra-account`` don't
            match existing accounts.
    """
    try:
        content = Path(args.file).read_text()
    except OSError as exc:
        raise ValidationError(f"could not read {args.file}: {exc}") from exc
    importer = get_importer(args.dialect)
    transactions = importer.parse(content)

    account_repo = AccountRepository(connection)
    account = account_repo.get_by_code(args.account)
    contra = account_repo.get_by_code(args.contra_account)
    assert account.id is not None
    assert contra.id is not None

    journal_repo = JournalRepository(connection)
    with UnitOfWork(connection):
        cursor = connection.execute(
            "INSERT INTO import_batches (account_id, source_name, imported_at, row_count) "
            "VALUES (?, ?, ?, ?)",
            (account.id, Path(args.file).name, clock.now().isoformat(), len(transactions)),
        )
        batch_id = ImportBatchId(cursor.lastrowid)  # type: ignore[arg-type]
        for transaction in transactions:
            entry = JournalEntry(
                entry_date=transaction.transaction_date,
                memo=transaction.description,
                import_batch_id=batch_id,
                lines=(
                    Line(account_id=account.id, amount=transaction.amount),
                    Line(account_id=contra.id, amount=-transaction.amount),
                ),
            )
            journal_repo.create(entry, clock)

    print(f"imported {len(transactions)} transaction(s) into batch {batch_id}")
    return 0
