from __future__ import annotations

from ledgerkit.ids import AccountId, EntryId, ImportBatchId, LineId


def test_ids_are_plain_ints_at_runtime():
    account_id = AccountId(1)
    assert account_id == 1
    assert isinstance(account_id, int)


def test_distinct_id_types_can_still_compare_by_value():
    assert AccountId(1) == EntryId(1)


def test_all_id_types_constructible():
    assert LineId(3) == 3
    assert ImportBatchId(4) == 4
