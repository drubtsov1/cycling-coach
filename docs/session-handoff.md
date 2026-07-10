# Session continuity — the handoff file

Each Claude Code session starts without memory of the last. For a coach, most of
what matters is re-fetched fresh anyway — training load, power and activities come
from Intervals.icu, food from your nutrition log. But one layer lives nowhere
else: the **conversational layer** — plan adjustments and deviations, decisions
and their reasoning, how you're feeling, motivation, work/life constraints, and
pending follow-ups. Without somewhere to put it, every new session starts "cold"
and you repeat yourself.

The fix is a single file — `state/session-handoff.md` — that the coach reads at
the start of a session and keeps current as the day unfolds.

## What goes in it

Only the conversational layer — the stuff no data source records:

- plan adjustments / deviations (downgraded a session, moved a ride, took a day off)
- decisions and the reasoning behind them
- how you feel, motivation, niggles
- work/life constraints affecting training
- pending follow-ups ("retest FTP next week", "check the knee after Saturday")

## What does NOT go in it

Anything already recorded elsewhere — never duplicate:

- training load / power / activities → Intervals.icu (pulled fresh via MCP)
- recovery / sleep / HRV → Whoop (or Intervals wellness)
- food → your nutrition log

## Two rules

1. **On session start** — read `state/session-handoff.md` before answering, so the
   coach recovers context instead of starting cold.
2. **Continuously** — update it right after any plan adjustment, decision,
   cancelled/moved ride, or notable thing you mention. Don't wait; treat the file
   as the source of truth for the conversational layer, kept current at all times.

Keep it compact — prune stale entries.

## Format

Append dated lines:

```
- 2026-07-10 08:05 — moved Sat long ride to Sun (rain forecast); Sat becomes easy Z2
- 2026-07-10 18:30 — knee felt tight on the climbs, watch it; skip standing efforts
```

## Setup

Copy the template once, into your project:

```bash
mkdir -p state
cp /path/to/cycling-coach/templates/state/session-handoff.md.template state/session-handoff.md
```

Then add this block to your `CLAUDE.md` so the coach does it automatically every
session:

```markdown
## Session continuity (handoff)

Each session starts without memory of the last. To avoid starting "cold", the
conversational layer is persisted to `state/session-handoff.md`:

1. On the first action of any session, read `state/session-handoff.md` before
   answering.
2. As the day unfolds, update it right after any plan adjustment, decision,
   cancelled/moved ride, or notable thing the user tells you — don't wait.

Don't duplicate what's already in Intervals (load/power/activities) or the
nutrition log (food) — only the conversational layer and decisions. Keep it
compact; prune stale entries. Append-format: `- YYYY-MM-DD HH:MM — <what/why>`.
```

The file is personal — keep it out of version control (the plugin's `.gitignore`
already excludes `state/`).
