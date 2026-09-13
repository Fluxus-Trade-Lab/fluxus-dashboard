"""One-time backfill of the ticker event archive from git history.

The daily cron commits every screener JSON, so `git show <sha>:<path>` recovers
exactly what each screener said on each past trading day. This tool replays
those snapshots through the same extractor the daily append uses.

Dates come from the git commit date (the cron commits the session it just
processed) — never the host clock. Not part of the cron; run manually:

    python3 -m pipeline.tools.backfill_ticker_events --dry-run
    python3 -m pipeline.tools.backfill_ticker_events

NOTE: a screener that was legitimately empty on a day is indistinguishable
from one that failed that day; this tool records what the commit contained
and never interpolates. Use --dry-run's per-month counts to spot holes.
"""

from __future__ import annotations

import datetime as dt

import argparse
import json
import logging
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pipeline.marketcal import MARKET_TZ, is_trading_day, last_completed_session
from pipeline.screeners.ticker_events import (
    SCREENER_FILES, extract_events, is_plausible_day, is_session_date,
    load_events, load_sessions, rolling_momentum_median, upsert_day,
    write_events,
)

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_CSV = _REPO / 'data' / 'history' / 'ticker_events.csv'
_DEFAULT_SESSIONS_CSV = _REPO / 'data' / 'history' / 'breadth_archive.csv'


# `--format` every caller must pass to `git log` for snapshot_dates: the full
# author instant WITH its offset. The short calendar-date form is the bug
# this replaced (see snapshot_dates).
GIT_LOG_FORMAT = '--format=%H %aI'


PREMARKET_OPEN = dt.time(4, 0)


def _next_premarket(session: dt.date) -> dt.datetime:
    """04:00 ET on the first trading day after `session`."""
    day = session + dt.timedelta(days=1)
    while not is_trading_day(day):
        day += dt.timedelta(days=1)
    return dt.datetime.combine(day, PREMARKET_OPEN, tzinfo=MARKET_TZ)


def snapshot_dates(git_log_output: str) -> List[Tuple[str, str]]:
    """Parse '<sha> <ISO-8601 instant with offset>' lines (git's newest-first
    order) -> oldest-first (sha, ET session).

    Each commit is labelled with the session its data can hold:
    `marketcal.last_completed_session` at the commit instant, in ET.

    The first version read git's short-date output, i.e. the calendar day in the
    commit's OWN timezone. The nightly cron commits in UTC, so `69754ed3`
    (2026-08-07 01:08 UTC = 08-06 21:08 ET, holding the 08-06 session) was
    stamped 2026-08-07, and the preset backfill wrote the 08-06 tape under
    08-07: 72/72 change_pct matched the 08-06 bars, 0/72 the 08-07 bars
    (Nighty Zac, audit_events_vs_bars, 2026-09-11). Same family as the
    `--date=format:` bug in pitfall_the_exemption_makes_the_check_green.

    A commit made once the NEXT session's premarket has begun (04:00 ET) is
    not a snapshot of any session and is dropped: its bars still end on the
    previous close, but vendor fields are live -- `05cf2a1c` reverted exactly
    such a run ("09:18 UTC dispatch pulled Finviz PREM"). Without this rule the
    newest-wins pick below would let a Monday-premarket manual run (`65bbb080`,
    `8fb939f`) or a daytime dev commit (`fbf2c0fb`) displace the clean
    post-close snapshot of the Friday before.

    A bare date is rejected, not guessed: it carries no clock, and the clock is
    what decides the session. One commit per session: git lists newest first,
    so the first line seen for a session is its final committed state.
    """
    seen: Dict[str, str] = {}
    for line in git_log_output.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, stamp = parts
        try:
            ts = dt.datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        except ValueError:
            continue
        if ts.tzinfo is None:
            continue
        session = last_completed_session(ts)
        if ts.astimezone(MARKET_TZ) >= _next_premarket(session):
            continue
        seen.setdefault(session.isoformat(), sha)
    return [(seen[d], d) for d in sorted(seen)]


def rows_from_snapshot(payloads: Dict[str, Any], date_iso: str) -> List[Dict[str, Any]]:
    """All event rows for one day, across every screener payload present."""
    rows: List[Dict[str, Any]] = []
    for screener, payload in payloads.items():
        if not isinstance(payload, dict):
            continue
        rows.extend(extract_events(screener, payload, date_iso))
    return rows


def plan_purge(existing_dates: set[str], skipped_dates: set[str],
               mined_dates: set[str]) -> set[str]:
    """Dates safe to delete from an already-written archive.

    A date is purged only when it is BOTH currently archived AND newly
    judged bad (skipped) AND actually looked at this run (mined). A date
    absent from `mined_dates` is never purged — that's the renamed-file /
    lost-history case, where `--follow` failed to find history for a
    screener and its dates would otherwise look "skipped" by accident.
    Pure function, no I/O.
    """
    return existing_dates & skipped_dates & mined_dates


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Dry-run report figures."""
    return {
        'total': len(rows),
        'by_screener': dict(Counter(r['screener'] for r in rows)),
        'by_month': dict(Counter(r['date'][:7] for r in rows)),
        'tickers': len({r['ticker'] for r in rows}),
    }


# ── git access (not unit-tested; exercised by --dry-run) ─────────────

def _git(args: List[str]) -> str:
    return subprocess.run(['git', *args], cwd=_REPO, check=True,
                          capture_output=True, text=True).stdout


def _commits_for(screener: str) -> str:
    # --follow keeps history across a rename of the screener's output file;
    # without it a renamed file looks like it has no history at all, and its
    # dates would appear "skipped" by accident (see plan_purge).
    return _git(['log', '--follow', GIT_LOG_FORMAT, '--',
                 f'data/output/{screener}.json'])


def _payload_at(sha: str, screener: str) -> Dict[str, Any] | None:
    try:
        return json.loads(_git(['show', f'{sha}:data/output/{screener}.json']))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--csv', default=str(_DEFAULT_CSV))
    parser.add_argument('--allow-purge', action='store_true',
                        help='Actually delete archived rows for dates this run '
                             'judged bad. Without this flag, the tool only '
                             'reports what it would purge.')
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    # Union of every screener's commit dates; each date maps to that
    # screener's own commit for the day.
    per_screener: Dict[str, Dict[str, str]] = {}
    all_dates: set[str] = set()
    for screener in SCREENER_FILES:
        pairs = snapshot_dates(_commits_for(screener))
        per_screener[screener] = {d: sha for sha, d in pairs}
        all_dates.update(per_screener[screener])
    logger.info("Found %d snapshot dates across %d screeners",
                len(all_dates), len(SCREENER_FILES))

    sessions = load_sessions(str(_DEFAULT_SESSIONS_CSV))

    rows: List[Dict[str, Any]] = []
    skipped: List[Tuple[str, str]] = []
    # momentum_97 counts of the days we have already accepted, oldest first:
    # the plausibility guard grades each new day against this rolling norm.
    accepted_momentum: List[int] = []
    for i, date in enumerate(sorted(all_dates), 1):
        payloads = {}
        for screener, by_date in per_screener.items():
            sha = by_date.get(date)
            if sha:
                payload = _payload_at(sha, screener)
                if payload is not None:
                    payloads[screener] = payload
        day_rows = rows_from_snapshot(payloads, date)

        if not is_session_date(date, sessions):
            reason = 'non-session date'
            logger.info("Skipping %s: %s", date, reason)
            skipped.append((date, reason))
            continue
        plausible, reason = is_plausible_day(
            day_rows, momentum_median=rolling_momentum_median(accepted_momentum))
        if not plausible:
            logger.info("Skipping %s: %s", date, reason)
            skipped.append((date, reason))
            continue

        accepted_momentum.append(
            sum(1 for r in day_rows if r['screener'] == 'momentum_97'))
        rows.extend(day_rows)
        if i % 20 == 0:
            logger.info("  ...%d/%d dates, %d rows so far", i, len(all_dates), len(rows))

    s = summarize(rows)
    print(f"\nMined {s['total']} events across {s['tickers']} tickers")
    print("\nBy screener:")
    for k, v in sorted(s['by_screener'].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<18}{v}")
    print("\nBy month (holes here mean the pipeline was down, not a quiet tape):")
    for k, v in sorted(s['by_month'].items()):
        print(f"  {k}  {v}")
    print(f"\nSkipped days ({len(skipped)}):")
    for date, reason in skipped:
        print(f"  {date}  {reason}")

    frame = load_events(args.csv)
    # Skipped dates never produce rows for upsert_day to replace, but the
    # archive may already hold rows for them from before a guard tightened
    # (or from a prior run) — purge those explicitly so a rejected day can't
    # linger in the archive it was rejected from. Only dates this run
    # actually mined are eligible: a screener file that lost history (e.g. a
    # rename --follow couldn't resolve) must never be treated as "skipped".
    skipped_reasons = {date: reason for date, reason in skipped}
    skipped_dates = set(skipped_reasons)
    existing_dates = set(frame['date']) if len(frame) else set()
    purge_dates = plan_purge(existing_dates, skipped_dates, all_dates)

    if purge_dates:
        print(f"\n{'=' * 60}")
        if args.allow_purge:
            print(f"PURGING {len(purge_dates)} archived date(s) rejected by this run:")
        else:
            print(f"WOULD PURGE {len(purge_dates)} archived date(s) rejected by this run:")
        for date in sorted(purge_dates):
            print(f"  {date}  {skipped_reasons.get(date, 'unknown reason')}")
        if not args.allow_purge:
            print("\nRe-run with --allow-purge to delete these rows from the archive.")
        print('=' * 60)

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    if purge_dates and args.allow_purge:
        frame = frame[~frame['date'].isin(purge_dates)]
    for date in sorted({r['date'] for r in rows}):
        frame = upsert_day(frame, [r for r in rows if r['date'] == date])
    write_events(frame, args.csv)
    print(f"\nWrote {len(frame)} rows to {args.csv}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
