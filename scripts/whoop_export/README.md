# WHOOP history export

Optional companion script. Incrementally mirrors your full WHOOP history into
CSV files, plus a rolling 30/60-day HRV/RHR baseline. Use it for **longitudinal**
questions (trends over weeks/months) so the coach can read a local CSV instead of
paging the Whoop MCP.

Stdlib Python only — nothing to install. Requires the Whoop MCP already set up
(see the plugin README) so a token store exists at `~/.whoop-mcp/tokens.json`.

## Output

Written to `$WHOOP_EXPORT_DATA_DIR` if set, else `../../data/whoop`:

| File | Contents | Upsert key |
|------|----------|------------|
| `recovery.csv` | recovery score, HRV (rmssd), RHR, SpO₂, skin temp | `cycle_id` |
| `sleep.csv` | stages, efficiency, performance, respiratory rate | `id` |
| `cycles.csv` | day strain, energy (kJ), avg/max HR | `id` |
| `workouts.csv` | strain, HR, kJ, distance, altitude, zone durations | `id` |
| `body.csv` | dated snapshots of weight / height / max HR | `date` |
| `baseline.csv` | rolling 30/60-day median+mean HRV & RHR per day | `date` |
| `baseline_verdict.txt` | latest baseline (and drift vs your reference, if set) | — |

All CSVs are UTF-8 with BOM (open cleanly in Excel).

## Usage

```bash
cd scripts/whoop_export

python3 export.py              # incremental: from last stored date − lookback
python3 export.py --months 3   # first run / test window
python3 export.py --all        # full account history
python3 export.py --since 2025-01-01 --lookback 7

python3 baseline.py            # recompute baselines + verdict from recovery.csv
```

Re-running is safe: rows upsert by id, so a re-run extends the dataset and
refreshes the recent days (WHOOP finalizes scores a day or two late) without
duplicating anything.

### Configuration (env)

| Variable | Effect |
|----------|--------|
| `WHOOP_EXPORT_DATA_DIR` | where the CSVs are written (default `../../data/whoop`) |
| `WHOOP_HRV_REF` | optional HRV reference; `baseline.py` reports drift of the rolling median vs this |
| `WHOOP_RHR_REF` | optional RHR reference; same idea |
| `WHOOP_CLIENT_ID` / `WHOOP_CLIENT_SECRET` | used only if a token refresh is needed and they aren't already in `~/.claude.json` |

Without `WHOOP_HRV_REF`/`WHOOP_RHR_REF`, `baseline.py` just reports the computed
baseline (no drift line).

## Scheduling

Best run shortly after your Whoop token is refreshed elsewhere (e.g. just after a
daily brief) so the exporter reads a fresh token and stays read-only.

**macOS (launchd):** copy `launchd.plist.template`, replace `__WHOOP_EXPORT_DIR__`
with this directory's absolute path, then load it:

```bash
cp launchd.plist.template ~/Library/LaunchAgents/com.example.whoop-export.plist
# edit the copy: set __WHOOP_EXPORT_DIR__
launchctl load -w ~/Library/LaunchAgents/com.example.whoop-export.plist
launchctl start com.example.whoop-export   # fire once now
```

**Linux (cron):**

```
15 8 * * *  /path/to/scripts/whoop_export/run.sh
```

Logs: `export.log` (pipeline output), `launchd.out.log` / `launchd.err.log`.

## Token safety

The exporter shares the Whoop MCP's token store (`~/.whoop-mcp/tokens.json`).

- **The common path is read-only.** If the on-disk access token is still valid,
  the exporter just reads it and makes read-only GETs — no token refresh, no
  rotation, no collision with a running Whoop MCP.
- **Guarded fallback.** If the token is expired at run time, the exporter performs
  exactly one refresh under an exclusive `flock`, writing the rotated token
  atomically with a `.bak`. It never runs two refreshers concurrently.

WHOOP rotates the refresh token on every refresh, so a single, serialized,
immediately-persisted refresh is important — hence the lock and the atomic write.

## Tests

```bash
python3 -m pytest tests/
```

Covers the pure logic: BOM / upsert / idempotency (`csv_store`) and rolling
median / outlier-robustness / drift check (`baseline`). The live API pull is
verified by running `export.py --months 3` and checking the CSVs.
