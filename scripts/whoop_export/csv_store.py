"""Per-domain CSV store with idempotent, keyed upsert.

- Files are written UTF-8 with BOM (utf-8-sig) so Excel opens them cleanly.
- Upsert merges new rows by a key column; re-running never duplicates rows.
- Schema growth: if new rows introduce a column, the union of fieldnames is used
  and older rows get an empty cell for it.

Stdlib only (csv, os).
"""

from __future__ import annotations

import csv
import os


def read_csv(path: str) -> list[dict]:
    """Read a CSV (utf-8-sig tolerates a BOM) into a list of dict rows.

    Returns [] if the file does not exist.
    """
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    """Write rows atomically with a BOM and a stable column order."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    os.replace(tmp, path)


def _ordered_fieldnames(existing_rows: list[dict], new_rows: list[dict], key: str) -> list[str]:
    """Union of columns: key first, then existing order, then any new columns."""
    names: list[str] = [key]
    for row in existing_rows + new_rows:
        for col in row.keys():
            if col not in names:
                names.append(col)
    return names


def upsert(path: str, new_rows: list[dict], key: str) -> dict:
    """Merge new_rows into the CSV at path, keyed by `key`.

    New key -> insert; existing key -> overwrite. Rows are sorted by key
    ascending. Returns {'added', 'updated', 'total'}.
    """
    existing = read_csv(path)
    by_key: dict[str, dict] = {}
    for row in existing:
        k = str(row.get(key, ""))
        if k != "":
            by_key[k] = row

    added = 0
    updated = 0
    for row in new_rows:
        k = str(row.get(key, ""))
        if k == "":
            continue
        if k in by_key:
            updated += 1
        else:
            added += 1
        by_key[k] = row

    fieldnames = _ordered_fieldnames(existing, new_rows, key)
    merged = sorted(by_key.values(), key=lambda r: str(r.get(key, "")))
    write_csv(path, merged, fieldnames)
    return {"added": added, "updated": updated, "total": len(merged)}
