# cycling-coach

A personal cycling coach for [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) — turns Claude into your training analyst, fueling planner, and Intervals.icu workout builder.

## What you get

**Skills** (auto-activated when relevant):
- `post-ride-drink` — recovery drink carbs + protein (g/kg) based on duration + TSS/h
- `ride-fueling` — full ride nutrition plan: pre-ride, on-ride (bottles, gels, shop stops), and race fueling
- `nutrition-log` — daily food log with macros summed against a training-scaled target
- `intervals-workout` — create/modify structured workouts in Intervals.icu via MCP, with the right power targets, intensity fields, and lap-press behavior
- `ride-analysis` — deep per-interval / segment / climb analysis from raw streams (NP/IF/TSS/decoupling, gradient base→summit, FIT device laps)

**MCP integration:** the [Intervals.icu MCP server](https://github.com/mvilanova/intervals-mcp-server) wired into Claude Code so it can read your activities, training load, and calendar in real time. Two **optional** MCPs extend it — **Open-Meteo** (free weather for ride planning, no key) and **Whoop** (direct recovery/sleep/HRV, fresher than the wearable data mirrored into Intervals). See [Optional: Whoop and weather](#optional-whoop-recovery-and-weather) below.

**Coach persona:** a `CLAUDE.md` template that turns Claude into a coach who plans around your social rides, watches your CTL/ATL/TSB balance, and respects that cycling is supposed to be fun.

## Setup (one-time, ~10 minutes)

### 1. Install the plugin

In Claude Code:

```
/plugin marketplace add drubtsov1/cycling-coach
/plugin install cycling-coach
```

### 2. Clone the Intervals.icu MCP server

The plugin doesn't ship the MCP server — you clone it yourself so you control updates and the location.

```bash
git clone https://github.com/mvilanova/intervals-mcp-server.git ~/cycling/intervals-mcp-server
```

You also need [`uv`](https://docs.astral.sh/uv/) installed (`brew install uv` on macOS).

### 3. Get your Intervals.icu API key

1. Go to https://intervals.icu/settings → API tab
2. Copy your **API key** and **Athlete ID** (starts with `i`, e.g. `i123456`)

### 4. Set environment variables

Append the contents of `templates/zshenv.snippet` to your `~/.zshenv`, edit the values:

```bash
# --- cycling-coach plugin ---
export UV_PATH="$HOME/.local/bin/uv"                            # which uv
export INTERVALS_MCP_PATH="$HOME/cycling/intervals-mcp-server"  # where you cloned it
export INTERVALS_API_KEY="your-api-key-here"
export INTERVALS_ATHLETE_ID="i123456"
```

Then **restart your terminal** (so the variables get loaded), and **restart Claude Code**.

> Why `~/.zshenv` and not `~/.zshrc`? `.zshenv` is loaded for every zsh invocation (interactive or not), so the MCP server gets your credentials whether you launch Claude from terminal, alias, or script.

### 5. Set up your project

In whatever directory you want to use the coach (e.g. `~/cycling/`):

```bash
# Copy the MCP config
cp /path/to/cycling-coach/templates/mcp.json.template ./.mcp.json

# Copy the coach persona + your profile
cp /path/to/cycling-coach/templates/CLAUDE.md.template ./CLAUDE.md
```

Then **edit `CLAUDE.md`** — replace all `{{PLACEHOLDERS}}` with your real values (FTP, weight, schedule, goals).

### 6. Verify

Restart Claude Code in your project directory. Ask it:

> show me my latest activity

If it can fetch from Intervals.icu and reply in coach mode — you're set.

## Optional: Whoop (recovery) and weather

Both are optional — the coach works fine on Intervals.icu alone.

**Open-Meteo (weather)** is already in `mcp.json.template`, so it's wired up as
soon as you copy the template. It's free and needs no key — just set your
**Location** in `CLAUDE.md` and the coach pulls forecasts for ride planning.
Delete the `open-meteo` block from `.mcp.json` if you don't want it.

**Whoop (recovery, sleep, HRV)** — fresher and more complete than the wearable
data mirrored into Intervals. To add it:

1. Create an OAuth app at https://developer.whoop.com — set the redirect URL to
   `http://localhost:3000/callback` and enable the read scopes (recovery, sleep,
   workout, cycles, profile, body measurement) plus `offline`.
2. Add the client id/secret to `~/.zshenv` (the `templates/zshenv.snippet` has
   commented lines for them):
   ```bash
   export WHOOP_CLIENT_ID="your-whoop-client-id"
   export WHOOP_CLIENT_SECRET="your-whoop-client-secret"
   ```
3. Add a `whoop` block to `mcpServers` in your `.mcp.json`:
   ```json
   "whoop": {
     "type": "stdio",
     "command": "npx",
     "args": ["-y", "whoop-ai-mcp"],
     "env": {
       "WHOOP_CLIENT_ID": "${WHOOP_CLIENT_ID}",
       "WHOOP_CLIENT_SECRET": "${WHOOP_CLIENT_SECRET}"
     }
   }
   ```
4. Restart your terminal and Claude Code. The first Whoop call opens an OAuth flow
   in your browser; tokens are cached at `~/.whoop-mcp/tokens.json` and refresh
   automatically.

The CLAUDE.md template already routes recovery/sleep/HRV questions to Whoop when
present (and documents why Whoop *strain* and *calories* are unreliable for
cyclists).

## Updating

```
/plugin update cycling-coach
```

Skills and templates update automatically. The Intervals.icu MCP server you update yourself with `git pull` in its directory.

## Customization

**Skills are a starting point**, not gospel. Open `~/.claude/plugins/cycling-coach/skills/<skill-name>/SKILL.md` and edit if you disagree with the carb tables or zone definitions.

**The CLAUDE.md template is yours after you copy it.** Add your race calendar, preferred locations, any quirks ("I hate intervals over 5 min", "always plan around Wednesday club rides"). The more specific your profile, the better the coaching.

## Troubleshooting

**MCP not connecting?** Run `claude mcp list` — it should say `Intervals.icu: ✓ Connected`. If not, check that:
- All three env vars (`INTERVALS_API_KEY`, `INTERVALS_ATHLETE_ID`, `INTERVALS_MCP_PATH`) are set in `~/.zshenv`
- You restarted Claude Code after setting them
- `uv` is installed and `UV_PATH` points to the right binary

**API returns 401?** Your `INTERVALS_API_KEY` is wrong or expired — regenerate at https://intervals.icu/settings.

**Whoop not connecting?** Check `WHOOP_CLIENT_ID` / `WHOOP_CLIENT_SECRET` are set
in `~/.zshenv` and that the OAuth app's redirect URL is exactly
`http://localhost:3000/callback`. Whoop access tokens live ~1 h and refresh
automatically; if a session goes stale, restart Claude Code to reload the cached
token from `~/.whoop-mcp/tokens.json`.

## Credits

- Zone definitions follow Coggan / Joe Friel / TrainerRoad conventions
- The Intervals.icu MCP server is maintained by [@mvilanova](https://github.com/mvilanova/intervals-mcp-server)

## License

MIT.
