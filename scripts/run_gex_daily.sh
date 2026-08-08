#!/bin/bash
# Daily GEX pull wrapper — run by launchd (com.fluxus.gex-daily).
#
# This machine is in JST. We run in TWO ET windows and let whichever fire lands
# inside a window proceed (DST-agnostic — the guard checks actual ET time):
#   * POST-CLOSE ~16:30 ET (PRIMARY) — TWS is guaranteed logged in before the
#     ~5pm auto-logout. Note: OI settles overnight, so a close pull returns the
#     PRIOR session's OI (today's trades haven't settled yet). One session stale
#     vs. the ideal, but reliable given 2FA blocks unattended morning re-login.
#   * PREMARKET 07:00-08:59 ET (BONUS) — freshest OI, runs only if TWS happens to
#     be up that morning. When it does, its output wins (_latest points to it).
# launchd fires at 05:30/06:30 JST (→ 16:30 ET post-close) and 20:30/21:30 JST
# (→ 07:30 ET premarket); the guard admits exactly one per window per DST regime.
# A per-ET-day lockfile stops a double run (post-close + same-day premarket give
# identical OI anyway, so skipping the redundant one is correct).
#
# Requires TWS / IB Gateway running + logged in on port 7496 (see docs/gex-levels.md).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
mkdir -p data/gex
LOG=data/gex/cron.log
say() { echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $*" >>"$LOG"; }

ET_HOUR=$(TZ=America/New_York date +%H)
ET_MIN=$(TZ=America/New_York date +%M)
ET_DOW=$(TZ=America/New_York date +%u)          # 1-5 = Mon-Fri
DATE=$(TZ=America/New_York date +%Y%m%d)

[ "$ET_DOW" -gt 5 ] && { say "weekend (ET dow $ET_DOW) — skip"; exit 0; }

# 10#$ForcesBase-10 so a leading-zero minute (e.g. "08") isn't read as octal.
premarket=false; postclose=false
{ [ "$ET_HOUR" = "07" ] || [ "$ET_HOUR" = "08" ]; } && premarket=true
{ [ "$ET_HOUR" = "16" ] && [ "$((10#$ET_MIN))" -ge 15 ]; } && postclose=true
if [ "$premarket" = false ] && [ "$postclose" = false ]; then
    say "ET ${ET_HOUR}:${ET_MIN} outside pull windows (07-08 premarket / 16:15+ post-close) — skip"; exit 0
fi
# Premarket is a bonus pass: skip if today's file exists. Post-close ALWAYS
# re-runs — it is the primary, its OI is settled and its volume fields are the
# day's real prints, and an earlier manual/premarket pull must not preempt it.
if [ "$premarket" = true ] && [ -f "data/gex/gex_SPX_${DATE}.json" ]; then
    say "premarket: already have $DATE — skip"; exit 0
fi

if ! nc -z -w3 127.0.0.1 7496 2>/dev/null; then
    say "TWS/Gateway not reachable on 127.0.0.1:7496 — is it running + logged in? skip"; exit 1
fi

win=$([ "$postclose" = true ] && echo "post-close" || echo "premarket")
say "running GEX pull for $DATE ($win, ET ${ET_HOUR}:${ET_MIN})"
.venv/bin/python scripts/gex_levels.py --symbol SPX >>"$LOG" 2>&1 \
    || { say "FAILED at gex_levels — see log above"; exit 1; }
.venv/bin/python scripts/gex_to_pine.py --symbol SPX >/dev/null 2>>"$LOG" || say "warn: pine overlay failed"

if [ "$postclose" = true ]; then
    # The session just closed: its Market Profile is now computable, the brief
    # can join it, and the scorecard has one more finished bar to grade against.
    .venv/bin/python scripts/build_profile.py >>"$LOG" 2>&1 \
        && say "profile built for $DATE" || say "warn: build_profile failed"
    .venv/bin/python scripts/score_levels.py --symbol SPX >>"$LOG" 2>&1 \
        && say "scorecard updated" || say "warn: score_levels failed"
fi
# The brief renders in both windows — premarket joins yesterday's profile.
.venv/bin/python scripts/build_snapshot.py --symbol SPX >>"$LOG" 2>&1 \
    || { say "FAILED at build_snapshot — see log above"; exit 1; }
say "brief built (data/snapshots/snapshot_SPX_${DATE}.html)"

# The machine's half of the centaur pairing. Logged from the brief so the record
# accrues without anyone remembering to. Andy's half is his to write:
#   .venv/bin/python scripts/log_view.py down 3 "reason"
.venv/bin/python scripts/log_view.py --machine >>"$LOG" 2>&1 \
    && say "machine view logged" || say "warn: machine view not logged"

# Push the card LAST: everything above must have succeeded, or we would be
# sending a stale card that looks current. A failed push is logged and does not
# fail the run — the files are on disk either way.
.venv/bin/python scripts/push_brief.py --symbol SPX --window "$win" >>"$LOG" 2>&1 \
    && say "pushed card to Discord" \
    || say "warn: Discord push failed — card still at data/snapshots/card_SPX_${DATE}.png"
