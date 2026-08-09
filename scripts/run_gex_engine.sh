#!/bin/zsh
# scripts/run_gex_engine.sh — launchd entrypoint for the daily GEX run.
set -u
REPO="/Users/taolezhu/Documents/AI-Trading-System"
LOG="$REPO/data/gex/engine.log"
cd "$REPO" || exit 1
echo "=== gex run $(date -u +%FT%TZ) ===" >> "$LOG"
"$REPO/.venv/bin/python" -m pipeline.gex.engine >> "$LOG" 2>&1
echo "=== exit $? ===" >> "$LOG"
