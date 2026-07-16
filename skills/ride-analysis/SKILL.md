---
name: ride-analysis
description: Analyze a completed ride or a specific climb/segment in depth from Intervals.icu — per-interval quality, NP/IF/TSS/VI/EF/decoupling computed from raw streams, a climb's length/gradient/power base→summit, or real device laps parsed from the FIT. Use when the user asks to analyze a ride, segment or climb beyond the activity summary, or when the summary alone would mislead (e.g. whole-ride decoupling on a ride with a long easy tail).
version: 1.0.0
---

# Analyzing Intervals.icu rides in depth

Go past the activity summary. Pull the **per-interval breakdown** and the **raw
per-second streams**, and compute what you need yourself — so the answer doesn't
depend on which fields Intervals happens to pre-calc, and so you can analyze any
sub-segment (a single climb, one interval) the summary can't.

## When to activate

- The user asks to analyze a ride, a race, a climb, or a segment.
- A summary number looks off or could mislead — e.g. **whole-ride decoupling** on
  a ride with a long easy tail (a Z1 spin home inflates it). Judge drift *inside*
  the hard efforts instead.
- The user asks "did you look at the intervals themselves?" — always go per-rep,
  not just NP/IF/TSS for the whole ride.

## Data sources (MCP first, raw streams for depth)

Via the Intervals.icu MCP:

- **`get_activity_details`** — the summary: NP/IF/TSS/decoupling pre-computed in
  `icu_*` fields. Good as a cross-check.
- **`get_activity_intervals`** — the per-lap / per-interval breakdown as
  Intervals segmented it (auto work/rest blocks, structured-workout steps, or
  imported device laps, depending on the activity's *"use device laps"* setting).
  Each object carries `start_index`/`end_index` into the streams plus
  pre-computed `average_watts`, `moving_time`, etc.
- **`get_activity_streams`** — the **raw per-second time-series**. This is the
  material for computing anything yourself and for slicing an arbitrary window.

For heavier work (compute in Python, slice a climb, or read genuine button laps)
fall back to the **direct Intervals.icu API** — pull `streams.csv` or the
original `.fit`. Auth is HTTP Basic: username is the literal `API_KEY`, password
is the athlete's personal key (Intervals.icu → Settings → Developer Settings →
API Key). Get the athlete's FTP from the CLAUDE.md profile — it anchors IF/TSS/zones.

```bash
KEY="the_api_key"
ATHLETE="i123456"          # athlete id (top-left of the API key page)
ID="i000000000"            # an activity id

# List recent activities (to find IDs)
curl -s -u "API_KEY:$KEY" \
  "https://intervals.icu/api/v1/athlete/$ATHLETE/activities?oldest=2026-06-01&newest=2026-06-09"

# Ride summary
curl -s -u "API_KEY:$KEY" "https://intervals.icu/api/v1/activity/$ID"

# Raw streams for the whole track → CSV
curl -s -u "API_KEY:$KEY" \
  "https://intervals.icu/api/v1/activity/$ID/streams.csv?types=time,watts,heartrate,cadence,velocity_smooth,altitude,distance,latlng,temp" \
  -o ride.csv
```

## 1. Streams are raw material, not a summary

An activity is stored as **streams** — parallel ~1 Hz arrays, all aligned by
index. Index `i` is the same instant across every stream.

| Stream | Meaning | | Stream | Meaning |
|--------|---------|-|--------|---------|
| `time` | seconds since start | | `altitude` | elevation (m) |
| `watts` | power (W) | | `latlng` | GPS `[lat, lon]` |
| `heartrate` | HR (bpm) | | `distance` | cumulative distance (m) |
| `cadence` | rpm | | `temp` | temperature (°C) |
| `velocity_smooth` | speed (m/s) | | `torque`, `respiration`, … | if recorded |

You can filter which streams you pull:
`…/streams.csv?types=time,watts,heartrate,altitude,distance,latlng`

## 2. Whole-ride metrics

- **NP (Normalized Power)** — variability-adjusted power; what the ride "felt
  like" to the body.
- **IF (Intensity Factor)** = `NP / FTP`. ~0.6 easy, ~0.75–0.85 tempo/long race,
  ≥0.9 a hard sustained effort.
- **TSS (Training Stress Score)** — total load (duration × intensity). ~50 an
  easy hour, ~100 a solid hour at threshold.
- **VI (Variability Index)** = `NP / avg power`. ~1.0 steady (TT/climb), >1.2
  punchy/group.
- **EF (Efficiency Factor)** = `NP / avg HR`. Track over time — rising EF =
  aerobic gains.
- **Decoupling (Pw:HR)** — does HR drift up while power holds? Split the steady
  aerobic part in half; if EF drops >5% first→second half, you're decoupling
  (durability limit / fatigue / heat). Negative = you were fresh.
- **L/R balance** — pedaling symmetry (dual-sided power meter).

```python
import pandas as pd, numpy as np

FTP = 290  # ← set to the athlete's FTP from CLAUDE.md

df = pd.read_csv("ride.csv")
w  = df["watts"].fillna(0).to_numpy()      # coasting = 0 W → fillna OK for power
hr = df["heartrate"].to_numpy()            # do NOT zero-fill HR (drop NaN)
dur = len(df)                              # seconds, since ~1 Hz

def NP_of(arr):                            # 30s rolling avg → 4th power → mean → 4th root
    r = pd.Series(arr).rolling(30, min_periods=1).mean().to_numpy()
    return (np.nanmean(r**4))**0.25

NP  = NP_of(w); avg = w.mean()
IF  = NP / FTP
TSS = (dur * NP * IF) / (FTP * 3600) * 100
VI  = NP / avg
EF  = NP / np.nanmean(hr)
print(f"dur {dur/3600:.2f}h  avgP {avg:.0f}  NP {NP:.0f}  IF {IF:.2f}  "
      f"TSS {TSS:.0f}  VI {VI:.2f}  EF {EF:.2f}")

# Decoupling: EF first half vs second half
h = dur // 2
ef1 = NP_of(w[:h]) / np.nanmean(hr[:h])
ef2 = NP_of(w[h:]) / np.nanmean(hr[h:])
print(f"decoupling {(ef1-ef2)/ef1*100:+.1f}%   (>+5% drifting, negative = fresh)")

# Power-zone time (classic 7 zones)
edges = [0, .55, .75, .90, 1.05, 1.20, 1.50, np.inf]
names = ["Z1","Z2","Z3","Z4","Z5","Z6","Z7"]
z = pd.cut(w/FTP, bins=edges, labels=names, right=True)
print((z.value_counts().sort_index() / 60).round(1).to_string())  # minutes per zone
```

## 3. Segment / climb analysis

To analyze one climb (or any stretch) slice the streams to that **window** and
compute on the slice. Three ways to find the window: by **distance** (km A→B), by
**GPS** (match `latlng` to known base/summit coords), or by the **altitude
profile** (local min before the climb → local max at the top — most robust for a
repeatable climb).

> **Gotcha:** don't trust auto-detected "work" intervals for climb length — they
> clip the real ascent (they cut where power dips, not where the hill starts/ends).
> For true length and gradient, slice on the **altitude stream** base→summit
> yourself. This is exactly why a 12-minute climb can show up as a "10-minute"
> auto-interval.

```python
def segment_stats(df, FTP, start_m=None, end_m=None, i0=None, i1=None):
    """Slice by distance (meters) or by index; return climb stats."""
    if start_m is not None:
        i0 = (df["distance"] - start_m).abs().idxmin()
        i1 = (df["distance"] - end_m).abs().idxmin()
    seg = df.iloc[i0:i1+1]
    length   = seg["distance"].iloc[-1] - seg["distance"].iloc[0]   # m
    gain     = seg["altitude"].iloc[-1] - seg["altitude"].iloc[0]   # m net
    duration = seg["time"].iloc[-1] - seg["time"].iloc[0]           # s
    grad     = gain / length * 100 if length else 0
    r        = seg["watts"].rolling(30, min_periods=1).mean().to_numpy()
    print(f"length {length/1000:.2f} km · gain {gain:+.0f} m · grad {grad:.1f}% · "
          f"time {duration/60:.1f} min · avgP {seg['watts'].mean():.0f} W · "
          f"NP {(np.nanmean(r**4))**0.25:.0f} W · HR {seg['heartrate'].mean():.0f}")

segment_stats(df, FTP=290, start_m=12000, end_m=15700)   # a climb from km 12.0 to 15.7
```

Because `get_activity_intervals` exposes `start_index`/`end_index`, you can feed
those straight in as `i0`/`i1` to recompute any lap or interval yourself. Once
you've profiled a repeatable climb (length, gain, typical full-ascent time), reuse
it as a benchmark — same hill, compare power held and time across rides.

## 4. Laps vs intervals (button-press laps)

Streams contain **no lap markers**, so you cannot recover button laps from
`streams.csv` alone. They live in two different places:

**A. Real device laps** (the lap button pressed on a Karoo/Garmin) — stored in the
**original FIT** as `lap` messages. Download the exact file the head unit uploaded:

```bash
curl -u "API_KEY:$KEY" "https://intervals.icu/api/v1/activity/$ID/file" -o original.fit
```

- `/activity/{id}/file` → the **original upload** (genuine button laps live here;
  manually-entered activities may 404).
- `/activity/{id}/fit-file` → a FIT **re-generated by Intervals** — a fallback when
  the original was a GPX/TCX without lap messages.

```python
import fitdecode
laps = []
with fitdecode.FitReader("original.fit") as fit:
    for f in fit:
        if f.frame_type == fitdecode.FIT_FRAME_DATA and f.name == "lap":
            laps.append({
                "dist_m": f.get_value("total_distance"),
                "time_s": f.get_value("total_elapsed_time"),
                "avg_w":  f.get_value("avg_power"),
                "avg_hr": f.get_value("avg_heart_rate"),
            })
```

**B. `get_activity_intervals`** returns Intervals' own segmentation — which may or
may not equal your button presses (see §Data sources).

> Rule of thumb: **button laps → parse the FIT**; **"intervals" → the endpoint**.

## 5. Practical notes

- **~1 Hz sampling**, so `len(df)` ≈ duration in seconds. "Smart" (variable)
  sampling → resample to 1 s first.
- **Dropouts**: `fillna(0)` for power (coasting = 0 W), but **drop** NaN HR, don't
  zero-fill it.
- **Indoor/trainer rides** have no `latlng`/`altitude` — use time or distance
  windows, not GPS.
- **GPS altitude is noisy**; prefer barometric altitude for gradient, and measure
  net gain over the whole climb rather than summing tiny deltas.
- The summary endpoint already has NP/IF/TSS/decoupling — handy as a cross-check,
  but computing from streams is portable and works on any sub-segment.

*Workflow in one line:* find the activity id → pull streams → compute whole-ride
metrics and/or slice a segment → write a per-rep verdict, not just the summary.
