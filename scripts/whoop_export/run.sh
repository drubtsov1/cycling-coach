#!/bin/bash
# launchd/cron wrapper for the WHOOP history export.
#
# Best scheduled shortly after your Whoop token is refreshed elsewhere (e.g. just
# after a daily brief) so the exporter reads a fresh token and runs read-only —
# no refresh-token rotation, no collision with a running Whoop MCP.
#
# Runs export.py then baseline.py, appends timestamped output to export.log, and
# propagates a non-zero exit so failures are visible.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$SCRIPT_DIR/export.log"

# launchd/cron hand us a minimal PATH; ensure python3 + curl resolve.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
PY="$(command -v python3)"

ts() { date "+%Y-%m-%d %H:%M:%S"; }

{
  echo "===== $(ts) whoop-export start ====="
  "$PY" "$SCRIPT_DIR/export.py"
  "$PY" "$SCRIPT_DIR/baseline.py"
  echo "===== $(ts) whoop-export done ====="
} >> "$LOG" 2>&1
