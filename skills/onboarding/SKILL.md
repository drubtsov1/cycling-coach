---
name: onboarding
description: Guided first-time setup — interview the athlete for their profile (FTP, weight, LTHR, weekly schedule, goals, local routes) and fill in their CLAUDE.md from the template, then point at the optional MCPs and extras. Use when the user asks to set up / onboard / "get started", or when the project CLAUDE.md still contains {{PLACEHOLDERS}}.
version: 1.0.0
---

# Onboarding — set up the coach

Run a short interview and write the athlete's `CLAUDE.md`, so they don't have to
edit placeholders by hand. The goal: after this, the coach knows their numbers,
their week, and their goals.

## When to activate

- The user asks to set up, onboard, configure, or "get started".
- The project `CLAUDE.md` is missing or still has unfilled `{{PLACEHOLDERS}}`.

## How to run it

1. **Ensure a CLAUDE.md exists.** If `./CLAUDE.md` is missing, copy
   `templates/CLAUDE.md.template` → `./CLAUDE.md` first.
2. **Interview in small batches** — never dump 20 questions at once. Where the
   answer is a choice (e.g. which days they ride), offer structured options; where
   it's a number, take free text. Group the questions:

   | Batch | Fields | Required? |
   |-------|--------|-----------|
   | Essentials | FTP (+ when last tested), weight, LTHR | required |
   | Schedule | typical training days, weekday time limit, long-ride day(s) | required |
   | Goals | A-races / events with dates, or "just fitness" | required |
   | Optional | indoor FTP, max HR, resting HR, Critical Power/W′, devices, location (for weather), club, local routes/climbs | skip freely |

3. **Compute derived fields.** `W/kg = FTP / weight`. If the user wants concrete
   numbers, resolve the power-zone watts from FTP in the table.
4. **Write the values** into `./CLAUDE.md`, replacing the matching
   `{{PLACEHOLDERS}}`. Leave the fixed sections (zones, coach role, energy
   tracking, response style) as they are. **Delete** the placeholder line for any
   optional field the user skipped — don't leave a dangling `{{...}}`.
5. **Verify.** Re-read `CLAUDE.md` and confirm no `{{PLACEHOLDER}}` remains except
   ones intentionally deleted.
6. **Offer the optional MCPs.** Ask whether they use **Whoop** (recovery/sleep/HRV)
   or want **weather** (Open-Meteo). Point them at the README's *Optional: Whoop
   and weather* section for the OAuth-app / `.mcp.json` steps — don't try to do the
   OAuth flow for them.
7. **Offer the extras**, one line each, let them opt in:
   - a daily **nutrition log** (the `nutrition-log` skill + `templates/nutrition/`)
   - a **session-handoff** file for continuity (`docs/session-handoff.md`)
   - the **whoop_export** script for longitudinal HRV/RHR trends (`scripts/whoop_export/`)

## Interview style

- One friendly batch at a time; read back what you'll write and confirm before
  saving.
- **Never invent numbers.** If the user doesn't know their FTP or LTHR, explain
  how to get it (a ramp test or 20-minute test for FTP; LTHR from a hard 30-min
  effort's last-20-min average HR) or set a conservative estimate and mark it to
  refine later.
- Keep it light — this should feel like a coach getting to know them, not a form.

## After onboarding

Suggest a first action — "show me my latest activity" or "plan my week" — and let
them know they can re-run onboarding any time to update the profile (e.g. after an
FTP retest).
