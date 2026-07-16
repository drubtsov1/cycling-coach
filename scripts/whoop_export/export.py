#!/usr/bin/env python3
"""Incremental WHOOP history exporter -> one CSV per domain.

Pulls recovery, sleep, cycles, workouts and a body-measurement snapshot, flattens
each record to clean columns, and upserts by record id. The window is
configurable; the default is a cheap incremental pull suitable for a daily
schedule.

Output goes to WHOOP_EXPORT_DATA_DIR if set, else ../../data/whoop relative to
this file.

Usage:
    python3 export.py                 # incremental: from last stored date - lookback
    python3 export.py --months 3      # first run / test window
    python3 export.py --all           # full history
    python3 export.py --since 2025-01-01 --lookback 7

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import csv_store
import whoop_client

# Output dir: env override, else data/whoop relative to this file
# (scripts/whoop_export/ -> ../../data/whoop).
DATA_DIR = os.environ.get("WHOOP_EXPORT_DATA_DIR") or os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "whoop")
)

# Paginated domains: (domain, csv filename, upsert key, date source field)
COLLECTIONS = [
    ("recovery", "recovery.csv", "cycle_id", "created_at"),
    ("sleep", "sleep.csv", "id", "start"),
    ("cycle", "cycles.csv", "id", "start"),
    ("workout", "workouts.csv", "id", "start"),
]

DEFAULT_MONTHS = 3
DEFAULT_LOOKBACK_DAYS = 5
ALL_HISTORY_START = "2015-01-01"


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _date_part(value: str) -> str:
    """First 10 chars of an ISO timestamp -> YYYY-MM-DD (empty if unparseable)."""
    return value[:10] if value and len(value) >= 10 else ""


def flatten_record(rec: dict) -> dict:
    """Collect all scalar leaves by leaf key; lists are JSON-encoded.

    WHOOP nests metrics under `score` (and `score.stage_summary`,
    `score.zone_durations`, ...). Leaf keys are already descriptive and unique
    (hrv_rmssd_milli, resting_heart_rate, total_rem_sleep_time_milli, ...), so
    flattening to leaves yields clean, predictable columns and tolerates the API
    moving fields around within `score`.
    """
    flat: dict = {}

    def walk(obj):
        for k, v in obj.items():
            if isinstance(v, dict):
                walk(v)
            elif isinstance(v, list):
                flat[k] = json.dumps(v, ensure_ascii=False)
            else:
                flat[k] = v

    walk(rec)
    return flat


def _stored_max_date(path: str) -> str:
    rows = csv_store.read_csv(path)
    dates = [r.get("date", "") for r in rows if r.get("date")]
    return max(dates) if dates else ""


def resolve_window(args) -> tuple[str, str]:
    """Return (start_iso, end_iso) for the pull."""
    end = datetime.now(timezone.utc)
    if args.all:
        return ALL_HISTORY_START + "T00:00:00.000Z", _iso(end)
    if args.since:
        return args.since + "T00:00:00.000Z", _iso(end)
    if args.months:
        return _iso(end - timedelta(days=int(args.months * 30.44))), _iso(end)

    # Default: incremental from the earliest stored max date minus lookback.
    stored = [
        _stored_max_date(os.path.join(DATA_DIR, fname))
        for _, fname, _, _ in COLLECTIONS
    ]
    stored = [d for d in stored if d]
    if not stored:
        return _iso(end - timedelta(days=int(DEFAULT_MONTHS * 30.44))), _iso(end)
    oldest_max = min(stored)
    start_dt = datetime.strptime(oldest_max, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_dt -= timedelta(days=args.lookback)
    return _iso(start_dt), _iso(end)


def export_collection(domain: str, fname: str, key: str, date_field: str,
                      start: str, end: str) -> dict:
    records = whoop_client.get(domain, start=start, end=end)
    rows = []
    for rec in records:
        flat = flatten_record(rec)
        flat["date"] = _date_part(str(rec.get(date_field, "")))
        rows.append(flat)
    path = os.path.join(DATA_DIR, fname)
    stats = csv_store.upsert(path, rows, key=key)
    return stats


def export_body(snapshot_date: str) -> dict:
    """Body measurement is a single current object; store a dated snapshot row."""
    obj = whoop_client.get_single("body")
    flat = flatten_record(obj) if obj else {}
    flat["date"] = snapshot_date
    path = os.path.join(DATA_DIR, "body.csv")
    return csv_store.upsert(path, [flat], key="date")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export WHOOP history to CSV.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--months", type=float, help="history window in months")
    group.add_argument("--since", type=str, help="start date YYYY-MM-DD")
    group.add_argument("--all", action="store_true", help="full account history")
    parser.add_argument("--lookback", type=int, default=DEFAULT_LOOKBACK_DAYS,
                        help="days re-pulled before last stored date (incremental mode)")
    args = parser.parse_args(argv)

    os.makedirs(DATA_DIR, exist_ok=True)
    start, end = resolve_window(args)
    print(f"WHOOP export window: {start} .. {end}")
    print(f"output dir: {DATA_DIR}")

    failures = 0
    for domain, fname, key, date_field in COLLECTIONS:
        try:
            s = export_collection(domain, fname, key, date_field, start, end)
            print(f"  {domain:9s} added {s['added']:4d}  updated {s['updated']:4d}  total {s['total']:5d}")
        except Exception as exc:  # noqa: BLE001 — surface per-domain, keep going
            failures += 1
            print(f"  {domain:9s} FAILED: {exc}", file=sys.stderr)

    try:
        s = export_body(_date_part(end))
        print(f"  {'body':9s} added {s['added']:4d}  updated {s['updated']:4d}  total {s['total']:5d}")
    except Exception as exc:  # noqa: BLE001
        failures += 1
        print(f"  {'body':9s} FAILED: {exc}", file=sys.stderr)

    if failures:
        print(f"{failures} domain(s) failed", file=sys.stderr)
        return 1
    print("export OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
