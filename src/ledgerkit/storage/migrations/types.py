"""The Migration type shared by every numbered migration module.

Each ``migration_NNN_<name>.py`` module in this package defines exactly
one module-level ``MIGRATION`` constant of this type and nothing else —
no conditional logic, no environment checks. A migration is a fixed,
already-decided schema change; anything that needs to vary by environment
belongs in :mod:`ledgerkit.config`, not here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Migration:
    """A single, ordered schema change.

    Attributes:
        version: Must be contiguous starting at 1 across every migration
            in :data:`~ledgerkit.storage.migrations.runner.ALL_MIGRATIONS`;
            the runner raises :class:`~ledgerkit.errors.StorageError` if it
            finds a gap.
        name: A short, human-readable description, recorded in the
            ``schema_migrations`` table alongside the version number.
        sql: The DDL to execute. May contain multiple statements — it's
            run through :meth:`sqlite3.Connection.executescript`, not a
            single ``execute`` call.
    """

    version: int
    name: str
    sql: str
