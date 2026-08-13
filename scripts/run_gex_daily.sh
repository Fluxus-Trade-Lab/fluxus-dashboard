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
# Post-close runs 16:15 through 17:59 ET. It used to end at 16:59, and on
# 2026-08-12 that cost a whole session: the 16:30 pull hung on IBKR account
# subscriptions, run_step killed it at 900s exactly as designed, and the
# fallback fire an hour later landed at ET 17:30 and was refused as "outside
# pull windows". The timeout guard and the retry schedule disagreed, so a single
# hang meant no settled chain that day and no second chance.
#
# The window now covers the fallback fire. 18:00 is the stop because TWS
# auto-logs-out around 17:00-18:00 and a pull after that reads a dead book,
# which is the failure the _tradeable_now guard exists to refuse.
{ [ "$ET_HOUR" = "16" ] && [ "$((10#$ET_MIN))" -ge 15 ]; } && postclose=true
{ [ "$ET_HOUR" = "17" ]; } && postclose=true
if [ "$premarket" = false ] && [ "$postclose" = false ]; then
    say "ET ${ET_HOUR}:${ET_MIN} outside pull windows (07-08 premarket / 16:15-17:59 post-close) — skip"; exit 0
fi
# A retry must not clobber a good run. Post-close is the primary and always
# re-runs at 16:xx; from 17:00 it only runs if the 16:xx attempt left nothing
# newer than the last session, which is what "the retry" means.
if [ "$ET_HOUR" = "17" ] && [ -f "data/gex/gex_SPX_${DATE}.json" ] \
   && [ "$(TZ=America/New_York date -r "data/gex/gex_SPX_${DATE}.json" +%H)" = "16" ]; then
    say "post-close retry: 16:xx run already produced $DATE — skip"; exit 0
fi
# Premarket is a bonus pass: skip if today's file exists. Post-close ALWAYS
# re-runs — it is the primary, its OI is settled and its volume fields are the
# day's real prints, and an earlier manual/premarket pull must not preempt it.
if [ "$premarket" = true ] && [ -f "data/gex/gex_SPX_${DATE}.json" ]; then
    say "premarket: already have $DATE — skip"; exit 0
fi

# TWS is launched by hand and is sometimes not up when the first window fires —
# it wasn't at 07:30 on 2026-08-10 and the whole premarket chain was lost with
# nothing but an exit code to show for it. Wait rather than give up: the second
# scheduled fire is an hour away, and the open is closer than that.
_waited=0
until nc -z -w3 127.0.0.1 7496 2>/dev/null; do
    if [ "$_waited" -ge "${TWS_WAIT_S:-1500}" ]; then
        say "TWS unreachable on 127.0.0.1:7496 after ${_waited}s — is it logged in? skip"
        exit 1
    fi
    [ "$_waited" = 0 ] && say "TWS not up yet — waiting up to ${TWS_WAIT_S:-1500}s"
    sleep 60
    _waited=$((_waited + 60))
done
[ "$_waited" -gt 0 ] && say "TWS came up after ${_waited}s"

win=$([ "$postclose" = true ] && echo "post-close" || echo "premarket")
# Hard wall-clock ceiling on every IBKR-touching step.
#
# On 2026-08-10 the post-close chain started at 16:36 ET and was still running
# six hours later with 1.5 seconds of CPU: blocked on a market-data subscription
# that never arrives once the session has closed. It produced no file and logged
# no failure, and it held an IBKR client slot the whole time. Nobody would have
# known -- it was found by hand.
#
# A step that cannot finish in this long is not going to finish.
STEP_TIMEOUT="${STEP_TIMEOUT:-900}"
run_step() {                     # run_step <label> <cmd...>
    local label="$1"; shift
    if command -v timeout >/dev/null 2>&1; then
        timeout --signal=TERM --kill-after=30 "$STEP_TIMEOUT" "$@" >>"$LOG" 2>&1
    else
        "$@" >>"$LOG" 2>&1 &
        local pid=$! waited=0
        while kill -0 "$pid" 2>/dev/null && [ "$waited" -lt "$STEP_TIMEOUT" ]; do
            sleep 5; waited=$((waited+5))
        done
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null; sleep 5; kill -KILL "$pid" 2>/dev/null
            say "TIMEOUT after ${STEP_TIMEOUT}s: $label — killed"
            return 124
        fi
        wait "$pid"
    fi
}

say "running GEX pull for $DATE ($win, ET ${ET_HOUR}:${ET_MIN})"
run_step gex_levels .venv/bin/python scripts/gex_levels.py --symbol SPX \
    || { say "FAILED or TIMED OUT at gex_levels"; exit 1; }
run_step pine .venv/bin/python scripts/gex_to_pine.py --symbol SPX || say "warn: pine overlay failed"

if [ "$postclose" = true ]; then
    # The session just closed: its Market Profile is now computable, the brief
    # can join it, and the scorecard has one more finished bar to grade against.
    run_step build_profile .venv/bin/python scripts/build_profile.py \
        && say "profile built for $DATE" || say "warn: build_profile failed or timed out"
    run_step score_levels .venv/bin/python scripts/score_levels.py --symbol SPX \
        && say "scorecard updated" || say "warn: score_levels failed or timed out"
    # The centaur only learns if both parties get graded. Runs post-close, when
    # the session that the views were filed against has an outcome.
    run_step score_views .venv/bin/python scripts/score_views.py --symbol SPX \
        && say "centaur skill updated" || say "warn: score_views failed or timed out"
fi
# The brief renders in both windows — premarket joins yesterday's profile.
# Jones' TFF needs its own history pull and rebuilds the baseline each day,
# excluding the session it is about to read. Non-fatal: a brief without a TFF
# reading says so, and a brief that waited for one would be no brief at all.
run_step build_tff .venv/bin/python scripts/build_tff.py --months 6 \
    || say "warn: TFF tables failed — brief will show no reading"

run_step build_snapshot .venv/bin/python scripts/build_snapshot.py --symbol SPX \
    || { say "FAILED or TIMED OUT at build_snapshot"; exit 1; }
say "brief built (data/snapshots/snapshot_SPX_${DATE}.html)"

# The machine's half of the centaur pairing. Logged from the brief so the record
# accrues without anyone remembering to. Andy's half is his to write:
#   .venv/bin/python scripts/log_view.py down 3 "reason"
.venv/bin/python scripts/log_view.py --machine >>"$LOG" 2>&1 \
    && say "machine view logged" || say "warn: machine view not logged"

# The flow read goes LAST of the data steps and is never fatal. It is the only
# step with a real data cost -- ~100 contracts of trade ticks, about five
# minutes -- and it must never be able to delay the levels pull or the brief.
# Quote ticks are NOT pulled: measured at 142s per contract against 1.9s for
# trades, and the cheap 1-minute-bar substitute agreed with tick NBBO on only
# 56.7% of prints against a 50% coin. See scripts/flow_session.py.
if [ "$postclose" = true ]; then
    run_step flow_session .venv/bin/python scripts/flow_session.py --symbol SPX \
        && say "flow read stored" || say "warn: flow_session failed or timed out"
fi

# Push the card LAST: everything above must have succeeded, or we would be
# sending a stale card that looks current. A failed push is logged and does not
# fail the run — the files are on disk either way.
# Commit-first ordering. The prompt card carries the day's question and nothing
# that answers it, so a view filed against it is an independent second opinion
# rather than an echo. The full brief follows; every push is recorded so the
# anchoring of each view is MEASURED rather than assumed.
if [ "$premarket" = true ]; then
    .venv/bin/python scripts/push_brief.py --symbol SPX --window "$win" --prompt >>"$LOG" 2>&1 \
        && say "pushed commit-first prompt" || say "warn: prompt push failed"
    sleep "${BRIEF_DELAY_S:-2700}"          # ~45 min to commit before the answer
fi
.venv/bin/python scripts/push_brief.py --symbol SPX --window "$win" >>"$LOG" 2>&1 \
    && say "pushed full brief to Discord" \
    || say "warn: Discord push failed — card still at data/snapshots/card_SPX_${DATE}.png"
