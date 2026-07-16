---
name: nutrition-log
description: Maintain a daily food log with running totals against a training-scaled target. Use when the user logs a meal (text or photo), asks about their day's calories/macros, or wants a nutrition target for the day. Reads and writes nutrition/foods.md and nutrition/days/YYYY-MM-DD.md.
version: 1.0.0
---

# Nutrition log

A lightweight food diary: one file per day, macros summed against a target that
scales with the day's training. Carbs are the lever that moves with training
volume; protein stays roughly constant per kg; fat fills the rest.

## Structure

```
nutrition/
├── foods.md            # food database (macros per standard portion)
└── days/
    └── YYYY-MM-DD.md   # one page per day
```

On first use, copy the templates: `templates/nutrition/foods.md.template` →
`nutrition/foods.md`, and start each day from `templates/nutrition/day.md.template`.

## Logging a meal

1. The user sends a meal — text ("lunch: 150 g chicken + 200 g rice") or a photo.
2. From a photo, estimate portions by eye (a fist ≈ 150 g cooked grains, a palm ≈
   100 g meat, etc.).
3. Look up macros in `foods.md`. If an item is missing, estimate from standard
   values and consider adding it to `foods.md` so it's reusable.
4. Append to `days/YYYY-MM-DD.md`: `time — item — portion — kcal / C / P / F`.
5. Recompute the running day total and compare to the day's target.

## Daily targets (scale to the athlete's weight)

Read body weight from the CLAUDE.md profile. `kcal ≈ C×4 + P×4 + F×9`.

| Day type                 | Carbs (g/kg) | Protein (g/kg) | Fat (g/kg) |
|--------------------------|--------------|----------------|------------|
| Off / recovery           | 3–4          | 1.6–1.8        | 0.8–1.0    |
| Easy Z1 < 1 h            | 4–5          | 1.6–1.8        | 0.8–1.0    |
| Z2 1–1.5 h               | 5–6          | 1.7–1.9        | 0.8–1.0    |
| Z2 2–3 h / intensity     | 6–8          | 1.7–1.9        | 0.8–1.0    |
| Long 4 h+ / race         | 8–12         | 1.7–1.9        | 0.8–1.0    |

Example — a 70 kg athlete on a Z2 2–3 h day: ~420–560 g carbs, ~120–133 g protein,
~56–70 g fat ≈ 2900–3400 kcal. Recovery day → keep protein up (muscle repair),
carbs moderate.

## Energy accounting

For the **ride's** kcal, use Intervals.icu (power-based) — not Whoop. Whoop
undershoots low-HR cycling by 20–40% (see the *Energy tracking* section in
CLAUDE.md). Daily non-exercise expenditure → Whoop daily total, if connected.

## Conventions

- All weights in grams; kcal rounded to integers; C/P/F in grams
- Meal times in 24-hour format
- **Morning:** generate the day file with the target from the planned workout
- **Evening:** show the diff — actual vs target
- Don't nag about a missed target — report the number and move on
