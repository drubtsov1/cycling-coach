"""Tests for baseline: rolling median/mean, outlier robustness, drift check."""
from datetime import date, timedelta

import baseline


def _rows(values, start="2026-01-01", rhr=50.0, calibrating=False):
    """Build recovery rows: values is a list of HRV numbers, one per consecutive day."""
    d0 = date.fromisoformat(start)
    rows = []
    for i, hrv in enumerate(values):
        rows.append({
            "date": (d0 + timedelta(days=i)).isoformat(),
            "hrv_rmssd_milli": str(hrv),
            "resting_heart_rate": str(rhr),
            "user_calibrating": "true" if calibrating else "false",
        })
    return rows


def test_rolling_median_constant_series():
    rows = _rows([90.0] * 60)
    table = baseline.compute_baseline_table(rows)
    assert table[-1]["hrv_med60"] == 90.0
    assert table[-1]["n60"] == 60
    assert table[-1]["rhr_med60"] == 50.0


def test_median_is_robust_to_outlier():
    # 30 days of ~90 with a single 200 spike — median barely moves, mean jumps.
    vals = [90.0] * 29 + [200.0]
    rows = _rows(vals)
    last = baseline.compute_baseline_table(rows)[-1]
    assert last["hrv_med30"] == 90.0           # spike ignored
    assert last["hrv_mean30"] > last["hrv_med30"]


def test_verdict_reports_high_when_reference_above_computed():
    rows = _rows([88.0] * 60)
    v = baseline.compute_verdict(rows, hrv_ref=100.0, rhr_ref=53.0)
    assert v["ok"] is True
    assert v["window"] == "60d"
    assert v["hrv_computed"] == 88.0
    assert "HIGH" in v["hrv_line"]
    assert "+13.6%" in v["hrv_line"]


def test_verdict_accurate_within_tolerance():
    rows = _rows([100.0] * 60, rhr=53.0)
    v = baseline.compute_verdict(rows, hrv_ref=100.0, rhr_ref=53.0)
    assert "accurate" in v["hrv_line"]
    assert "accurate" in v["rhr_line"]


def test_no_reference_omits_verdict_lines():
    rows = _rows([90.0] * 60)
    v = baseline.compute_verdict(rows)
    assert v["ok"] is True
    assert "hrv_line" not in v
    assert v["hrv_computed"] == 90.0


def test_short_history_is_provisional_and_uses_30d():
    rows = _rows([90.0] * 10)
    v = baseline.compute_verdict(rows)
    assert v["provisional"] is True
    assert v["window"] == "30d"
    assert v["n"] == 10


def test_calibrating_and_null_rows_excluded():
    good = _rows([90.0] * 40)
    bad = _rows([10.0] * 40, calibrating=True)  # would crush the median if counted
    v = baseline.compute_verdict(good + bad)
    assert v["hrv_computed"] == 90.0


def test_empty_input():
    v = baseline.compute_verdict([])
    assert v["ok"] is False
