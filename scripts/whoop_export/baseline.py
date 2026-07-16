#!/usr/bin/env python3
"""Rolling HRV/RHR baselines from recovery.csv, with an optional drift check.

- Trailing 30- and 60-day median + mean of HRV (rmssd) and RHR per date.
- Optionally compares the latest computed baseline against a reference you supply
  (env WHOOP_HRV_REF / WHOOP_RHR_REF), reporting how far the reference sits from
  the measured rolling median — a drift monitor. Without a reference it just
  writes the computed baseline.

Median is the headline statistic: it ignores single-night outliers (e.g. one
unusually high HRV night), while mean is recorded alongside for reference.

Output goes to WHOOP_EXPORT_DATA_DIR if set, else ../../data/whoop.

Stdlib only.
"""

from __future__ import annotations

import os
import statistics
from datetime import datetime, timedelta

import csv_store

DATA_DIR = os.environ.get("WHOOP_EXPORT_DATA_DIR") or os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "whoop")
)
RECOVERY_CSV = os.path.join(DATA_DIR, "recovery.csv")
BASELINE_CSV = os.path.join(DATA_DIR, "baseline.csv")
VERDICT_TXT = os.path.join(DATA_DIR, "baseline_verdict.txt")

# A baseline computed from fewer than this many days is labelled provisional.
MIN_DAYS_FOR_STABLE = 30

BASELINE_FIELDS = [
    "date", "n30", "hrv_med30", "hrv_mean30", "rhr_med30", "rhr_mean30",
    "n60", "hrv_med60", "hrv_mean60", "rhr_med60", "rhr_mean60",
]


def _env_float(name: str):
    val = os.environ.get(name)
    try:
        return float(val) if val not in (None, "") else None
    except ValueError:
        return None


# Optional reference baselines for the drift check (unset -> no verdict lines).
HRV_REF = _env_float("WHOOP_HRV_REF")
RHR_REF = _env_float("WHOOP_RHR_REF")


def _is_calibrating(row: dict) -> bool:
    return str(row.get("user_calibrating", "")).strip().lower() in ("true", "1")


def _f(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def parse_recovery(rows: list[dict]) -> list[tuple[datetime, float, float]]:
    """-> sorted [(date, hrv, rhr)] with calibrating/null rows dropped."""
    out = []
    for row in rows:
        if _is_calibrating(row):
            continue
        d = row.get("date", "")
        if not d:
            continue
        hrv = _f(row.get("hrv_rmssd_milli"))
        rhr = _f(row.get("resting_heart_rate"))
        if hrv is None or rhr is None:
            continue
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            continue
        out.append((dt, hrv, rhr))
    out.sort(key=lambda t: t[0])
    return out


def _window_stats(series, end_dt, window_days):
    """median/mean of hrv,rhr over (end_dt - window_days, end_dt]."""
    start = end_dt - timedelta(days=window_days - 1)
    hrv = [h for (dt, h, _) in series if start <= dt <= end_dt]
    rhr = [r for (dt, _, r) in series if start <= dt <= end_dt]
    if not hrv:
        return None
    return {
        "n": len(hrv),
        "hrv_med": round(statistics.median(hrv), 1),
        "hrv_mean": round(statistics.mean(hrv), 1),
        "rhr_med": round(statistics.median(rhr), 1),
        "rhr_mean": round(statistics.mean(rhr), 1),
    }


def compute_baseline_table(recovery_rows: list[dict]) -> list[dict]:
    series = parse_recovery(recovery_rows)
    table = []
    for (dt, _, _) in series:
        w30 = _window_stats(series, dt, 30)
        w60 = _window_stats(series, dt, 60)
        table.append({
            "date": dt.strftime("%Y-%m-%d"),
            "n30": w30["n"], "hrv_med30": w30["hrv_med"], "hrv_mean30": w30["hrv_mean"],
            "rhr_med30": w30["rhr_med"], "rhr_mean30": w30["rhr_mean"],
            "n60": w60["n"], "hrv_med60": w60["hrv_med"], "hrv_mean60": w60["hrv_mean"],
            "rhr_med60": w60["rhr_med"], "rhr_mean60": w60["rhr_mean"],
        })
    return table


def _delta_line(label, computed, reference):
    """Human line: how a reference baseline compares to the computed median."""
    pct = (reference - computed) / computed * 100 if computed else 0.0
    if abs(pct) < 3:
        verdict = "accurate"
    elif pct > 0:
        verdict = "HIGH (reference above computed)"
    else:
        verdict = "LOW (reference below computed)"
    return f"{label}: computed median {computed} vs reference {reference} -> reference is {pct:+.1f}% {verdict}"


def compute_verdict(recovery_rows: list[dict],
                    hrv_ref: float | None = None,
                    rhr_ref: float | None = None) -> dict:
    table = compute_baseline_table(recovery_rows)
    if not table:
        return {"ok": False, "reason": "no usable recovery data"}
    latest = table[-1]
    # Prefer the 60d window; fall back to 30d when history is short.
    use60 = latest["n60"] >= MIN_DAYS_FOR_STABLE
    win = "60d" if use60 else "30d"
    hrv = latest["hrv_med60"] if use60 else latest["hrv_med30"]
    rhr = latest["rhr_med60"] if use60 else latest["rhr_med30"]
    n = latest["n60"] if use60 else latest["n30"]
    res = {
        "ok": True,
        "as_of": latest["date"],
        "window": win,
        "n": n,
        "provisional": n < MIN_DAYS_FOR_STABLE,
        "hrv_computed": hrv,
        "rhr_computed": rhr,
    }
    if hrv_ref is not None:
        res["hrv_line"] = _delta_line(f"HRV {win} median", hrv, hrv_ref)
    if rhr_ref is not None:
        res["rhr_line"] = _delta_line(f"RHR {win} median", rhr, rhr_ref)
    return res


def main() -> int:
    rows = csv_store.read_csv(RECOVERY_CSV)
    if not rows:
        print(f"no recovery data at {RECOVERY_CSV}; run export.py first")
        return 1

    table = compute_baseline_table(rows)
    csv_store.write_csv(BASELINE_CSV, table, BASELINE_FIELDS)
    print(f"wrote {len(table)} baseline rows -> {BASELINE_CSV}")

    v = compute_verdict(rows, hrv_ref=HRV_REF, rhr_ref=RHR_REF)
    if not v["ok"]:
        print(v["reason"])
        return 1

    lines = [
        f"Baseline as of {v['as_of']} ({v['window']} window, n={v['n']}"
        + (", PROVISIONAL" if v["provisional"] else "") + ")",
        v.get("hrv_line", f"HRV {v['window']} median: {v['hrv_computed']}"),
        v.get("rhr_line", f"RHR {v['window']} median: {v['rhr_computed']}"),
        "Note: median used — robust to single-night spikes.",
    ]
    report = "\n".join(lines)
    print("\n" + report)
    with open(VERDICT_TXT, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
