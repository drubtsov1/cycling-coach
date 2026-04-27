---
name: intervals-workout
description: Use this skill when creating, updating or deleting structured workouts in Intervals.icu via MCP. Covers correct step structure, power targets, intensity fields, and known API quirks.
version: 1.0.0
---

# Creating Intervals.icu Workouts via MCP

## Before creating any event

Always verify the day of week for the target date using the shell — never calculate mentally. Confirm the date falls on one of the athlete's training days (see weekly schedule in CLAUDE.md).

```bash
date -j -f "%Y-%m-%d" "2026-04-01" +%A   # macOS
date -d "2026-04-01" +%A                  # Linux
```

Do this for EVERY date before creating. Mental math is unreliable.

## Critical API rules

### 1. Update doesn't work — always delete + recreate

The `add_or_update_event` update path returns 400. To modify a workout:
1. Call `delete_event` with the event_id
2. Call `add_or_update_event` without event_id to create fresh

### 2. Step intensity field is required for power to save correctly

Using only `"warmup": true` or `"cooldown": true` **strips the power value** from the stored step. Always pair the boolean flag with `"intensity"`:

```json
{ "warmup": true, "intensity": "warmup", "power": {...}, "duration": 1200 }
{ "cooldown": true, "intensity": "cooldown", "power": {...}, "duration": 900 }
{ "intensity": "interval", "power": {...}, "duration": 720 }
{ "intensity": "recovery", "power": {...}, "duration": 300 }
```

### Default lap-press rules

**Warmup and cooldown steps MUST always have `until_lap_press: true`** when the athlete rides outdoors from home — warmup/cooldown duration depends on traffic and route to/from the training spot, so fixed times are unrealistic. Set a sensible fallback duration for TSS estimation, but always flag these.

For recovery/transition steps between intervals on outdoor terrain (descents, roll-outs to climbs, etc.), also prefer lap-press unless the user specifies otherwise.

### 3. `until_lap_press` requires patched text serialization

The MCP server sends `workout_doc` as a text description (`str(workout_doc)` in server.py), which Intervals.icu re-parses. The default `Step.__str__` doesn't render `until_lap_press`, so the flag is dropped.

Fix: patched `types.py` `Step.__str__` to emit `- Press lap {duration} ` instead of `- {duration} ` when `until_lap_press=True`. Duration stays as fallback — Intervals uses it for estimated TSS/zone stats but honors lap button at runtime.

Side effect: Intervals overwrites the step's `text` field with literal `"Press lap"` on save, so custom step comments are lost for lap-press steps. Put coaching notes in the workout description instead.

### 4. Power value format

Always use numeric value (not string), with `%ftp` units:

```json
{ "power": { "value": 82, "units": "%ftp" } }
```

Ramps with `start`/`end` only work reliably on non-warmup/cooldown steps. For warmup/cooldown use a single `value`.

## Sensible default power targets

Always express targets as `%ftp` in the workout_doc. Intervals.icu resolves to watts from the athlete's current FTP.

**Coggan zones:**

| Zone | Name           | % FTP    |
|------|----------------|----------|
| Z1   | Recovery       | < 55%    |
| Z2   | Endurance      | 56–75%   |
| Z3   | Tempo          | 76–90%   |
| Z4   | Threshold      | 91–105%  |
| Z5   | VO2max         | 106–120% |
| Z6   | Anaerobic      | 121–150% |
| Z7   | Neuromuscular  | > 150%   |

**Targets for workout steps (per Coggan/TrainingPeaks/TrainerRoad):**

| Step type          | % FTP   | Zone | Source |
|--------------------|---------|------|--------|
| Warmup             | 50–65%  | Z1–Z2 | Joe Friel |
| Z2 main block      | 60–72%  | Z2 | Coggan |
| Tempo (Z3)         | 76–90%  | Z3 | Coggan |
| Threshold (Z4)     | 91–105% | Z4 | Coggan |
| Sweet spot         | 84–97%  | Z3–Z4 | TrainerRoad |
| VO2max (Z5)        | 106–120%| Z5 | Coggan |
| Recovery between intervals | 40–55% | Z1 | TrainerRoad |
| Cooldown           | 45–55%  | Z1 | Coggan/Friel |

**Key rules:**
- Recovery between intervals = Z1 (40–55%). Lower is correct — it allows lactate clearance. If it "feels too easy", that's the point.
- Cooldown = Z1 (45–55%). Not Z2.
- Warmup = Z1 progressing into Z2. Optionally 2–3 x 1-min openers at ~100% FTP at the end of warmup before hard intervals.
- Don't confuse Z3 Tempo (76–90%) with Z4 Threshold (91–105%). Label workouts correctly.

## Correct full workout structure example (threshold 3×12)

```json
{
  "description": "3x12 min threshold. Best on a climb. Cut to 2x12 if legs are heavy.",
  "steps": [
    {
      "duration": 1200,
      "power": { "value": 65, "units": "%ftp" },
      "warmup": true,
      "intensity": "warmup",
      "text": "Warmup"
    },
    {
      "reps": 3,
      "text": "3x12 min threshold",
      "steps": [
        {
          "duration": 720,
          "power": { "value": 82, "units": "%ftp" },
          "intensity": "interval",
          "text": "Interval — steady, don't blow up"
        },
        {
          "duration": 300,
          "power": { "value": 60, "units": "%ftp" },
          "intensity": "recovery",
          "text": "Recovery — easy spin"
        }
      ]
    },
    {
      "duration": 900,
      "power": { "value": 62, "units": "%ftp" },
      "cooldown": true,
      "intensity": "cooldown",
      "text": "Cooldown"
    }
  ]
}
```

## Verify the result

After creating, check the returned `workout_doc.steps` to confirm power values are present on all steps. If any step is missing power — it wasn't saved correctly.

Also check `zoneTimes` makes sense: Z3/Z4 seconds should equal reps × interval duration.

## Workout names

Always in English.
