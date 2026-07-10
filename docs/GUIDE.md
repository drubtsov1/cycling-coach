# Cycling Coach — user guide

Turns Claude Code into a training analyst, fueling planner, and Intervals.icu
workout builder that knows your numbers, your week, and your goals. This guide is
the full tour; for install steps see the [README](../README.md).

- [What it is](#what-it-is)
- [Quick start](#quick-start)
- [Capabilities](#capabilities)
  - [Skills](#skills)
  - [Data sources & routing](#data-sources--routing)
  - [Extras](#extras)
- [Daily workflows](#daily-workflows)
- [Example prompts](#example-prompts)
- [Customization](#customization)

---

## What it is

The plugin is three things working together:

1. **A coach persona** — a `CLAUDE.md` template that carries your athlete profile
   (FTP, LTHR, weight, zones), your weekly schedule, your goals, and a set of
   coaching principles (watch CTL/ATL/TSB, analyse rides in depth, keep the plan
   flexible).
2. **Skills** — focused capabilities that activate automatically when relevant:
   building workouts, analysing rides, fueling, nutrition, onboarding.
3. **Live data** — the Intervals.icu MCP (required) plus optional Whoop
   (recovery) and Open-Meteo (weather), so the coach reasons about *today's* data
   instead of guessing.

Everything is yours to edit — the skills and the profile are a starting point, not
gospel.

## Quick start

1. Install and wire up Intervals.icu (README, ~10 min).
2. Ask the coach to **onboard** you: *"help me set up"* — the `onboarding` skill
   interviews you and fills in your `CLAUDE.md`.
3. Optionally add [Whoop and weather](../README.md#optional-whoop-recovery-and-weather).
4. Try it: *"show me my latest activity"* or *"plan my week"*.

## Capabilities

### Skills

| Skill | What it does | Fires when… | Example prompt |
|-------|--------------|-------------|----------------|
| `onboarding` | Interviews you and fills your `CLAUDE.md` profile; points at optional MCPs & extras | you ask to set up, or the profile still has `{{PLACEHOLDERS}}` | *"help me set up the coach"* |
| `intervals-workout` | Creates/edits structured workouts in Intervals.icu via MCP — correct power targets, intensity fields, lap-press behavior | you ask to plan or change a workout | *"put a 3×12 threshold on Thursday"* |
| `ride-analysis` | Deep analysis from raw streams: NP/IF/TSS/VI/EF, Pw:HR decoupling, a climb's length/gradient/power, device laps from the FIT | you ask to analyse a ride, climb, or segment beyond the summary | *"analyse yesterday's ride, look at the intervals"* |
| `ride-fueling` | On-ride nutrition plan: target carbs/h, bottles, gels, shop stops, pre-ride and race fueling | you ask what to eat/take on a ride | *"what should I fuel for a 4h hilly ride?"* |
| `post-ride-drink` | Recovery drink carbs + protein (g/kg) from ride duration and TSS/h | after a ride, or you ask about recovery nutrition | *"what's my recovery drink after that?"* |
| `nutrition-log` | Daily food log with macros summed against a training-scaled target | you log a meal or ask about the day's macros | *"lunch: 150g chicken, 200g rice — how am I doing today?"* |

### Data sources & routing

The coach pulls live data and routes each question to the right source:

| Question | Source |
|----------|--------|
| Training load (CTL/ATL/TSB), power, activities, planned workouts | **Intervals.icu** |
| Recovery, sleep, HRV, RHR, SpO₂ | **Whoop** first; fall back to Intervals wellness |
| Weather for ride planning | **Open-Meteo** (always a fresh pull) |
| A fatigue read / cross-check | both, reconciled |

Two calibration notes the coach follows (documented in the `CLAUDE.md` template):

- **Whoop *strain* is unreliable** for cyclists — it's HR-zone-based and
  overestimates low-HR muscular load. For training load, trust TSS from Intervals.
- **Whoop *calories* undershoot** low-HR cycling (20–40%). Per-ride kcal → Intervals
  (power-based); daily total expenditure → Whoop.

### Extras

- **`scripts/whoop_export/`** — optionally mirror your full Whoop history to CSV
  with a rolling 30/60-day HRV/RHR baseline, for longitudinal trends. See its
  [README](../scripts/whoop_export/README.md).
- **Session handoff** — an optional `state/session-handoff.md` file that persists
  the conversational layer (plan tweaks, decisions, how you feel) so a new session
  doesn't start cold. See [docs/session-handoff.md](session-handoff.md).

## Daily workflows

**Morning readiness.** *"How's my readiness today?"* → the coach pulls recovery/
sleep/HRV (Whoop) and load (CTL/ATL/TSB from Intervals), reconciles them, and says
whether to push, hold, or back off — reading the wellness date as your state going
*into* the day.

**Plan or adjust a workout.** *"Give me a threshold session Thursday"* → the
`intervals-workout` skill writes it to your Intervals calendar with the right
targets, so it syncs to your head unit. If you later change a rec in chat
("make it easier, legs are heavy"), the coach updates the calendar event too — the
plan you train off never goes stale.

**Analyse a completed ride.** *"Break down Saturday's ride"* → the `ride-analysis`
skill goes per-interval (not just NP/IF/TSS), checks decoupling inside the hard
efforts, and profiles any climb base→summit.

**Fuel a ride + recover.** *"Fuel plan for a 3h hilly Z2 with a café stop"* →
`ride-fueling` gives carbs/h, bottles, gels, shop-stop timing, and pre-ride carbs.
Afterwards, `post-ride-drink` sizes the recovery drink from duration and TSS/h.

**Log nutrition.** Send a meal (text or photo) → `nutrition-log` estimates macros,
appends to the day file, and shows the running total vs a target scaled to the
day's training.

**Weekly load review.** *"How's my week looking?"* → the coach reads the CTL/ATL/
TSB trend and ramp rate and flags over- or under-reaching before it bites.

## Example prompts

```
help me set up the coach
show me my latest activity
how's my readiness today?
plan my week around a long ride Saturday
put a 3×12 threshold on Thursday, best on a climb
analyse yesterday's ride — look at the intervals, not just the summary
what should I fuel for a 4-hour hilly ride with one café stop?
what's my recovery drink after a 90-min tempo?
lunch: 2 eggs, 80g oats, a banana — how am I doing on today's target?
is it going to rain on my ride tomorrow morning?
```

## Customization

- **Skills are a starting point.** Open
  `~/.claude/plugins/cycling-coach/skills/<name>/SKILL.md` and edit the carb
  tables, zone definitions, or analysis defaults if you disagree.
- **Your `CLAUDE.md` is yours after onboarding.** Add race notes, route quirks,
  preferences ("no intervals over 5 min", "always keep Wednesday's club ride").
  The more specific the profile, the better the coaching.
- **Re-run onboarding** any time your numbers change (e.g. after an FTP retest).
