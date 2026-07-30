"""Validation rules for account fields, kept separate from `Account` itself.

Splitting these out means `Account.__post_init__` reads as a list of the
rules that apply, not a block of inline string-checking logic — and any
other code that needs to validate a code or name before constructing an
`Account` (a bulk-import script, say) can call the same functions rather
than duplicating the checks.
"""

from __future__ import annotations

from ledgerkit.errors import ValidationError


def validate_code(code: str) -> None:
    """Raise ValidationError if `code` isn't a usable account code."""
    if not code.strip():
        raise ValidationError("account code must not be empty")


def validate_name(name: str) -> None:
    """Raise ValidationError if `name` isn't a usable account name."""
    if not name.strip():
        raise ValidationError("account name must not be empty")
