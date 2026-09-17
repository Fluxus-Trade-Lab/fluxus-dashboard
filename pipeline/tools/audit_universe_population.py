"""Universe population -- is "the whole market" still made of the same kind of name?

`audit_universe_shape` measures a CONTENT dimension of the archive (the share of
symbols sorting after "L") because a source cut in half along content is flawless
under every count check. Its own docstring names the next dimensions that would
work -- "sector mix, market-cap quantile mix" -- and then implements only the
first letter.

On 2026-06-26 both dimensions moved on the same night, and only one was watched.
The Finviz filter `cap_1.0to` (market cap >= $1B) stopped binding: 1,613 names
with a median cap of $143M entered the universe at once, the list passed 3,000,
and the 150-page cap began truncating it mid-alphabet. The letter guard caught
the truncation. Nothing caught the population change -- and the truncation was
fixed on 2026-08-10 while the population change is still in force, undeclared,
twelve weeks later.

    A universe can keep its size, its row counts and its alphabet
    and still stop being the same market.

So this file measures what the names ARE, not how many there are:

  P1  the share of the universe below $1B moves off its trailing median by more
      than --tolerance (default 10pp)
  P2  the median market cap moves by more than --factor (default 1.5x) against
      its trailing median, in either direction
  P3  not enough trailing sessions to judge; reported, never fatal

⚠️ The $1B line is SELF-MADE, not a standard. It is where `cap_1.0to` actually
bit: through 2026-06-25 the published universe had 0.0% of its names below it.
Any threshold in the same neighbourhood would do -- what is being watched is
movement, not the level. Registered as self-made per CLAUDE.md 2026-08-31.

⚠️ Like the letter guard, this alarms on RECOVERY too: if the filter ever comes
back, the session it returns will move the share by ~53pp against a trailing
median made of post-break sessions, and that is a real report, not a false one.
A rule that hides "it came back" would also hide "it broke again".

Verified on real history (`--since 2026-03-01`): fires P1+P2 on **2026-06-26**,
the first affected session, and is silent on every session before it.

`check()` is pure. Reading git history lives in `snapshots()`.

    python3 -m pipeline.tools.audit_universe_population
    python3 -m pipeline.tools.audit_universe_population --since 2026-06-01 -q
"""
from __future__ import annotations

import argparse
import datetime
import json
import statistics
import subprocess
import zoneinfo
from typing import Dict, List, Optional

UNIVERSE = 'data/output/universe.json'
SMALL_CAP = 1e9          # self-made line; see the warning above
TOLERANCE = 0.10         # share may drift this far (10 percentage points)
FACTOR = 1.5             # median cap may move this far, either direction
WINDOW = 20
MIN_NAMES = 200          # below this a snapshot is a fragment, not a universe
ET = zoneinfo.ZoneInfo('America/New_York')


def et_session(timestamp) -> Optional[str]:
    """The ET session a snapshot belongs to, from its OWN timestamp.

    Never the git commit date: git filters by the local clock, and a 22:5x UTC
    scrape lands on the next day in JST. That mistake dated a whole backfill
    wrong once already (DATA_RELIABILITY.md section 256) and dated this guard's
    own first draft wrong a second time.
    """
    try:
        dt = datetime.datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(ET).date().isoformat()


def share_small(caps: List[float], line: float = SMALL_CAP) -> Optional[float]:
    usable = [c for c in caps if c and c > 0]
    if not usable:
        return None
    return sum(1 for c in usable if c < line) / len(usable)


def check(by_session: Dict[str, List[float]], line: float = SMALL_CAP,
          tolerance: float = TOLERANCE, factor: float = FACTOR,
          window: int = WINDOW, min_names: int = MIN_NAMES) -> dict:
    """by_session: {"YYYY-MM-DD": [market_cap, ...]} as published that session."""
    sessions = sorted(by_session)
    rows, violations, warnings = [], [], []
    for i, day in enumerate(sessions):
        caps = [c for c in by_session[day] if c and c > 0]
        n = len(caps)
        sh = share_small(caps, line)
        med = statistics.median(caps) if caps else None

        prior_days = sessions[max(0, i - window):i]
        prior_sh = [s for s in (share_small(by_session[p], line) for p in prior_days)
                    if s is not None]
        prior_med = [statistics.median([c for c in by_session[p] if c and c > 0])
                     for p in prior_days if any(c > 0 for c in by_session[p])]
        base_sh = statistics.median(prior_sh) if prior_sh else None
        base_med = statistics.median(prior_med) if prior_med else None

        rec = {'session': day, 'names': n,
               'share_small': None if sh is None else round(sh, 4),
               'median_cap': None if med is None else round(med, 1),
               'baseline_share': None if base_sh is None else round(base_sh, 4),
               'baseline_median': None if base_med is None else round(base_med, 1),
               'kind': None}

        if n < min_names:
            rec['kind'] = 'P3'
            warnings.append(f'P3 {day}: only {n} names, not judged')
        elif len(prior_sh) < 3 or base_sh is None or base_med is None:
            rec['kind'] = 'P3'
            warnings.append(f'P3 {day}: only {len(prior_sh)} trailing sessions, not judged')
        else:
            moved = abs(sh - base_sh)
            ratio = (med / base_med) if base_med else 1.0
            if moved > tolerance:
                rec['kind'] = 'P1'
                violations.append(
                    f'P1 {day}: share below ${line:,.0f} is {sh:.2f} vs trailing '
                    f'median {base_sh:.2f} (moved {moved * 100:.0f}pp, tolerance '
                    f'{tolerance * 100:.0f}pp) over {n} names')
            if ratio > factor or ratio < 1 / factor:
                rec['kind'] = 'P2' if rec['kind'] is None else 'P1+P2'
                violations.append(
                    f'P2 {day}: median market cap {med:,.0f} vs trailing median '
                    f'{base_med:,.0f} (x{ratio:.2f}, band x{1 / factor:.2f}-x{factor:.2f})')
        rows.append(rec)

    return {'line': line, 'tolerance': tolerance, 'factor': factor,
            'sessions': len(sessions), 'rows': rows,
            'violations': violations, 'warnings': warnings, 'ok': not violations}


def snapshots(since: str, path: str = UNIVERSE) -> Dict[str, List[float]]:
    """{ET session: [market_cap, ...]} from every committed snapshot of `path`."""
    out: Dict[str, List[float]] = {}
    hashes = subprocess.run(
        ['git', 'log', '--format=%H', f'--since={since}', '--', path],
        capture_output=True, text=True).stdout.split()
    for h in reversed(hashes):                      # oldest first: later wins
        raw = subprocess.run(['git', 'show', f'{h}:{path}'],
                             capture_output=True, text=True).stdout
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        day = et_session(payload.get('timestamp'))
        if not day:
            continue
        out[day] = [float(r.get('market_cap') or 0) for r in payload.get('rows', [])]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--since', default='2026-03-01')
    ap.add_argument('--path', default=UNIVERSE)
    ap.add_argument('--line', type=float, default=SMALL_CAP)
    ap.add_argument('--tolerance', type=float, default=TOLERANCE)
    ap.add_argument('--factor', type=float, default=FACTOR)
    ap.add_argument('--window', type=int, default=WINDOW)
    ap.add_argument('--json')
    ap.add_argument('-q', '--quiet', action='store_true')
    a = ap.parse_args(argv)

    by = snapshots(a.since, a.path)
    if not by:
        print('BAD  no universe snapshots found -- nothing checked, which is not a pass')
        return 2

    result = check(by, a.line, a.tolerance, a.factor, a.window)
    for rec in result['rows']:
        if a.quiet and rec['kind'] in (None, 'P3'):
            continue
        mark = rec['kind'] or 'OK'
        share = '   -  ' if rec['share_small'] is None else f'{rec["share_small"]:6.3f}'
        med = '        -' if rec['median_cap'] is None else f'{rec["median_cap"]:9,.0f}'
        print(f'{mark:5s} {rec["session"]}  names {rec["names"]:5d}  '
              f'<line {share}  median {med}')
    for line in result['violations']:
        print(line)
    for line in result['warnings'] if not a.quiet else []:
        print(line)
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump(result, fh, indent=2)
    print(f'\n{"OK" if result["ok"] else "BAD"}: {len(result["violations"])} violation(s), '
          f'{len(result["warnings"])} warning(s) over {result["sessions"]} session(s)')
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
