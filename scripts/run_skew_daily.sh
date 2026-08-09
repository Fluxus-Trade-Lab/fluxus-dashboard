#!/usr/bin/env bash
# One skew row per underlying per ET trading day.
#
# Unlike the GEX pull, this MUST run inside RTH: the smile is read from live
# two-sided option quotes, and outside 09:30-16:00 ET those are one-sided or
# absent entirely. A post-close run silently records nothing, so the window here
# is 15:00-15:59 ET — late enough that the day's positioning is settled, early
# enough that quotes are still firm.
#
# This machine is in JST. launchd fires at 04:00/05:00 JST; the guard checks
# ACTUAL ET time so exactly one fire per DST regime proceeds.
#
# Install:
#   cp scripts/com.fluxus.skew-daily.plist ~/Library/LaunchAgents/
#   launchctl load ~/Library/LaunchAgents/com.fluxus.skew-daily.plist
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
LOG="data/reference/skew_daily.log"
mkdir -p data/reference
say() { echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $*" >>"$LOG"; }

ET_HOUR=$(TZ=America/New_York date +%H)
ET_MIN=$(TZ=America/New_York date +%M)
ET_DOW=$(TZ=America/New_York date +%u)
DATE=$(TZ=America/New_York date +%Y-%m-%d)

[ "$ET_DOW" -gt 5 ] && { say "weekend — skip"; exit 0; }
[ "$ET_HOUR" = "15" ] || { say "ET ${ET_HOUR}:${ET_MIN} outside the 15:00-15:59 RTH window — skip"; exit 0; }

# Already have today? The store dedupes anyway, but skipping saves the quotes.
if [ -f data/reference/skew_log.jsonl ] && grep -q "\"date\": \"${DATE}\"" data/reference/skew_log.jsonl; then
    say "already logged for $DATE — skip"; exit 0
fi
if ! nc -z -w3 127.0.0.1 7496 2>/dev/null; then
    say "TWS not reachable on 7496 — skip"; exit 1
fi

say "measuring skew for $DATE (ET ${ET_HOUR}:${ET_MIN})"
.venv/bin/python scripts/log_skew.py >>"$LOG" 2>&1
say "exit $?"
