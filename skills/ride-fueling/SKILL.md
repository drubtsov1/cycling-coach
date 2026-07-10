---
name: ride-fueling
description: Calculate on-ride nutrition plan (carbs, bottles, gels, shop stops). Activate when user asks what food/fuel to take on a ride, or asks about nutrition for an upcoming ride/race.
version: 1.0.0
---

# Ride Fueling Calculator

## When to activate

User asks what to take on a ride, what to eat during a ride, or how to fuel a specific workout/race.

## Step 1: Gather info

1. **What ride?** Get planned duration, expected intensity (Z2 endurance, threshold intervals, race, etc.). Check Intervals.icu calendar if needed.
2. **What's available?** Ask the user what gels, drink mixes, bars, and food they currently have at home. Don't assume — always ask.
3. **Shop stops?** On long rides (2h+), user can stop at shops for cola, haribo, candy, etc. Factor this in.

## Step 2: Calculate target carbs/hour

| Ride duration | Intensity | Target (g/h) |
|---|---|---|
| < 1 h | any | 0 (water only) |
| 1-2 h | Z1-Z2 | 30-40 |
| 1-2 h | Z3+ | 40-60 |
| 2-3 h | Z1-Z2 | 60-70 |
| 2-3 h | Z3+ | 70-80 |
| 3-4 h | Z1-Z2 | 70-80 |
| 3-4 h | Z3+ | 80-100 |
| 4+ h | Z1-Z2 | 80-90 |
| 4+ h | Z3+ / race | 90-120 |

For races, always use the upper end. For training, mid-range is fine.

Adjust for gut training status — if user hasn't been practicing high-carb intake, cap at 60-80 g/h and note that they should ramp up gradually.

## Step 3: Build the plan

### Carb content of common sources

**Gels & sport nutrition:**
| Product | Carbs (g) | Notes |
|---|---|---|
| Typical gel (40ml) | 20-25 | quick, easy on climbs |
| SiS GO gel (60ml) | 22 | isotonic, no water needed |
| Maurten 160 (500ml mix) | 40 | hydrogel, easy on stomach |
| Maurten 320 (500ml mix) | 80 | very concentrated |
| SiS Beta Fuel (500ml mix) | 80 | 1:0.8 glucose:fructose |
| Energy bar (typical) | 30-45 | good for Z2, hard to eat at Z4+ |

**Homemade drink mix (per 500ml bottle):**
| Recipe | Carbs (g) | Notes |
|---|---|---|
| 25g maltodextrin + 15g fructose | 40 | ~8% solution, comfortable |
| 40g maltodextrin + 20g fructose | 60 | ~12%, thick, sip slowly |
| 50g maltodextrin + 30g fructose | 80 | ~16%, very thick, race concentration |

Add 0.5-1g salt + lemon juice to all mixes.

**Shop stop foods:**
| Product | Carbs (g) | Serving |
|---|---|---|
| Coca-Cola | 10.6 per 100ml | 330ml can = 35g |
| Haribo gummy bears | 77 per 100g | small bag 100g = 77g |
| Snickers bar | 35 | 1 bar (52g) |
| Banana | 25-30 | 1 medium |
| Dates (3 pcs) | 50 | natural, dense |
| White bread + jam | 40-50 | 2 slices |
| Fanta/Sprite | 9-11 per 100ml | 330ml = ~33g |

### Glucose:fructose ratio

- Up to 60 g/h: single source OK (pure maltodextrin, gels)
- 60-90 g/h: use 2:1 glucose:fructose
- 90-120 g/h: use 1:0.8 glucose:fructose

### Hydration

500-750 ml/h. In heat (>25°C): 750-1000 ml/h. Add sodium 500-700 mg/h.

## Step 4: Output

Present a concrete plan:
1. **Total carbs needed** (target g/h × hours)
2. **What to take from home** — bottles, gels, bars (with exact quantities)
3. **What to buy at shop stops** (if applicable, with timing — e.g. "at ~2h mark, buy a can of cola + haribo")
4. **Feeding schedule** — when to eat what (e.g. "every 20 min: alternate gel and sip from bottle")
5. **Caffeine** (if race/hard ride): 3-6 mg/kg 30 min before start, optional booster gel in last hour

Keep it simple and actionable. User needs a checklist, not a lecture.

## Pre-ride fueling (before the start)

Carbs 30–60 min before rolling out, scaled to the ride. This tops up liver
glycogen after the overnight fast — it is **not** the on-ride fuel (that's the
plan above). Keep it low-fat and low-fibre so it clears the stomach fast.

| Ride type | Carbs before start | Easy sources |
|---|---|---|
| Off / Z1 < 45 min | 0 (optional) | nothing, or a banana |
| Z2 60–90 min | 25–35 g | banana + a date, or toast + honey |
| Z2 2–3 h | 40–50 g | banana + 30 g energy bar, or 30 g dry oats |
| Tempo / VO2 (any length) | 40–60 g | banana + oatmeal (30 g dry) |
| Long 3–4 h | 50–70 g | oatmeal (50 g dry) + honey + banana |
| Race day (long event) | 2–3 g/kg full breakfast 2–3 h before, then +25–35 g 30 min before | see Race fueling below |

- Fast, low-fibre carbs sit best pre-start (ripe banana, white toast + jam/honey,
  dates, a gel). Save high-fibre wholegrains for later in the day.
- Don't combine with fatty food in the last hour before the start — fat slows the
  fast carbs.

## Race fueling (events)

For A-races, also cover (use the athlete's body weight from CLAUDE.md profile):

- **Days before:** 8-12 g carbs/kg/day for 2-3 days
- **Race morning:** 2-3 g/kg 3-4h before start
- **Start eating immediately** — don't wait for hunger
- **Climbs:** liquid carbs (drink mix, gels). **Descents/flats:** solid food OK
- **Last hour:** gels only + caffeine gel 45 min before finish
