"""Tests for csv_store: BOM, keyed upsert, idempotency, schema growth."""
import csv_store


def test_write_has_bom_and_header(tmp_path):
    path = str(tmp_path / "x.csv")
    csv_store.write_csv(path, [{"id": "1", "v": "a"}], ["id", "v"])
    with open(path, "rb") as fh:
        raw = fh.read()
    assert raw.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    assert b"id,v" in raw


def test_upsert_overwrite_does_not_duplicate(tmp_path):
    path = str(tmp_path / "x.csv")
    csv_store.upsert(path, [{"id": "1", "v": "a"}], key="id")
    stats = csv_store.upsert(path, [{"id": "1", "v": "b"}], key="id")
    rows = csv_store.read_csv(path)
    assert len(rows) == 1
    assert rows[0]["v"] == "b"
    assert stats == {"added": 0, "updated": 1, "total": 1}


def test_upsert_insert_new_key(tmp_path):
    path = str(tmp_path / "x.csv")
    csv_store.upsert(path, [{"id": "1", "v": "a"}], key="id")
    stats = csv_store.upsert(path, [{"id": "2", "v": "b"}], key="id")
    assert len(csv_store.read_csv(path)) == 2
    assert stats["added"] == 1


def test_idempotent_rerun_is_byte_identical(tmp_path):
    path = str(tmp_path / "x.csv")
    rows = [{"id": "2", "v": "b"}, {"id": "1", "v": "a"}]
    csv_store.upsert(path, rows, key="id")
    first = open(path, "rb").read()
    csv_store.upsert(path, rows, key="id")
    second = open(path, "rb").read()
    assert first == second


def test_new_column_unions_and_backfills(tmp_path):
    path = str(tmp_path / "x.csv")
    csv_store.upsert(path, [{"id": "1", "a": "1"}], key="id")
    csv_store.upsert(path, [{"id": "2", "a": "2", "b": "9"}], key="id")
    rows = csv_store.read_csv(path)
    by_id = {r["id"]: r for r in rows}
    assert by_id["1"]["b"] == ""   # old row backfilled
    assert by_id["2"]["b"] == "9"


def test_key_is_first_column(tmp_path):
    path = str(tmp_path / "x.csv")
    csv_store.upsert(path, [{"v": "a", "id": "1"}], key="id")
    header = open(path, "r", encoding="utf-8-sig").readline().strip()
    assert header.split(",")[0] == "id"
