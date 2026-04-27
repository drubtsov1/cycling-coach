---
name: post-ride-drink
description: Calculate post-ride recovery drink carbs based on ride duration, intensity (TSS/h), and body weight. Use after analyzing a completed ride or when the user asks about post-ride nutrition.
version: 1.0.0
---

# Post-Ride Recovery Drink Calculator

Calculate grams of carbohydrates for the post-ride drink (within 10 minutes of finishing).

## How to calculate

1. Get ride duration and TSS from the activity (via Intervals.icu MCP or user input)
2. Calculate TSS/h = TSS / (duration_hours)
3. Look up carb dose (g/kg) from the table below
4. Multiply by the athlete's body weight (read from the athlete profile in CLAUDE.md) to get total grams

## Carb dose table (g/kg body weight)

| Ride duration | TSS/h | Carbs (g/kg) |
|---------------|-------|--------------|
| <=45 min | <50 | 0.3-0.4 |
| <=45 min | 50-60 | 0.4-0.5 |
| <=45 min | 61-72 | 0.5-0.6 |
| <=45 min | >=73 | 0.5-0.7 |
| 46-75 min | <50 | 0.3-0.4 |
| 46-75 min | 50-60 | 0.4-0.5 |
| 46-75 min | 61-72 | 0.5-0.6 |
| 46-75 min | >=73 | 0.6-0.7 |
| 76-120 min | <50 | 0.4-0.5 |
| 76-120 min | 50-60 | 0.5-0.6 |
| 76-120 min | 61-72 | 0.6-0.7 |
| 76-120 min | >=73 | 0.7-0.8 |
| 121-180 min | <50 | 0.8-0.9 |
| 121-180 min | 50-60 | 0.9-1.0 |
| 121-180 min | 61-72 | 1.0-1.1 |
| 121-180 min | >=73 | 1.1-1.2 |
| 181-240 min | <50 | 0.8-0.9 |
| 181-240 min | 50-60 | 1.0-1.1 |
| 181-240 min | 61-72 | 1.1-1.2 |
| 181-240 min | >=73 | 1.2 |
| >240 min | <50 | 0.8-0.9 |
| >240 min | 50-60 | 1.0-1.1 |
| >240 min | 61-72 | 1.1-1.2 |
| >240 min | >=73 | 1.2 |

## Output format

Report: duration, TSS, TSS/h, carb dose range (g/kg), total carbs range (g), and a practical suggestion (e.g. "mix 80-90g maltodextrin in water").
