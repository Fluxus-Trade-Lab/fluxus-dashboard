"""Universe freshness -- is this payload a COMPLETED SESSION, or just an hour?

Third in a line of guards that each added a dimension the previous one could
not see:

    audit_archives        COUNT    -- how many rows, how many nulls, is the
                                     date series continuous
    audit_universe_shape  CONTENT  -- 2026-06-26, the archive kept its row count
                                     and silently lost every symbol after "L"
    audit_universe_population  WHO -- same night, the $1B filter stopped binding
                                     and the universe stopped being the same
                                     market while keeping its size
    this file             WHEN     -- the rows are all there, every field is
                                     populated, the numbers are internally
                                     consistent, and they are Monday's
                                     PREMARKET rather than Friday's close

The shape and population guards both open with the same sentence in different
clothes: a defect along a dimension nobody measures passes every check along
the dimensions they do. The dimension left unmeasured here is the CLOCK.

    A snapshot taken at 05:31 has every field the 21:03 one has.
    What it does not have is a day of trading behind it.

Why no existing guard sees it:

  * `quality` inside the payload grades NULL RATES. On 2026-08-10 05:31 the
    premarket payload carried volume at a 0.0 null rate and the pipeline
    stamped it `quality.status: "ok"` -- while `d2337e85`, a genuine 2026-08-19
    close, is stamped `"degraded"`. The self-grade and this dimension are
    orthogonal: one asks whether values are present, this asks what hour they
    are from.
  * `data/history/universe_quality.csv` is the same null-rate ledger, archived.
  * the letter and cap guards measure statistics that premarket does not move
    (a ticker's first letter and its market cap are the same at 05:31 as at
    21:03), so they read a premarket payload as a normal session and say so.

THE QUANTITY

    aggregate RVOL = sum(volume) / sum(avg_volume)  over the whole universe

RVOL (current volume / average volume over the same period) is a standard,
published indicator -- StockCharts ChartSchool, TradingView, Finviz all carry
it, and platform write-ups note it is normally TIME-OF-DAY ADJUSTED so that
morning volume is only compared with historical morning volume. That adjustment
is exactly what our payloads do not have, which is why an unadjusted RVOL near
zero is a reliable "this is not a whole day".

⚠️ SELF-MADE, registered per CLAUDE.md 2026-08-31: RVOL is standard PER NAME.
Searched for a published market-aggregate construction and found none, so the
aggregation (one share-weighted ratio of sums across the whole universe) and
both thresholds below are ours, not anybody's standard.

Missing values count as 0 on BOTH sides of the ratio. That is deliberate and it
is what makes F2 possible: when `avg_volume` died for eight sessions in July
2026 the denominator went to nearly nothing while volume kept arriving, and the
ratio left the top of the band instead of quietly staying at 1.0.

NO MARKET-CAP FILTER. The private version of this gate (written inside
`data/research/ep_qullamaggie_baserate_2026-09-20/replay.py`, 2026-09-20)
measured the ratio over the >=$1B names only. Over all 156 committed snapshots
the whole-universe ratio and the >=$1B ratio return the identical verdict on
every single one, so the filter buys nothing -- and dropping it makes this
guard immune to the 2026-06-26 population change that `audit_universe_population`
exists to watch. A guard whose own denominator moves when the universe moves is
a guard that goes quiet exactly when something is wrong.

THE THRESHOLDS come from the empty bands, not from theory. Over 156 snapshots:

    143 snapshots   0.611 .. 1.969      median 0.980
      5 snapshots   0.0059 .. 0.0241    premarket payloads
      8 snapshots   95.4 .. 347.2       the 2026-07-15..24 avg_volume outage

Below the good band the nearest value is 0.024; above it the nearest is 95.4.
0.5 and 3.0 sit in gaps 25x and 48x wide. Any pair in those gaps behaves the
same -- what is being watched is which side of an empty band a payload lands on.

  F1  aggregate RVOL below --low: not a completed session (premarket shape)
  F2  aggregate RVOL above --high: the denominator died, volume did not
  F3  not judgeable -- too few rows, or a zero denominator. Reported, never
      fatal, because "cannot tell" is not "fine"
  F4  a SESSION whose every snapshot is F1/F2. Strictly worse than one bad
      snapshot among several: there is no usable payload for that session at
      all, and any replay that picks "the last commit of that day" picks a bad
      one. Nine sessions qualify -- the eight July outage days, plus
      **2026-08-10**, whose only two committed snapshots are the 05:31
      premarket pair. 08-17 and 08-19 also hold premarket snapshots but each
      has a clean evening one beside it, so they are F1 without being F4

Sessions are labelled by the ET CALENDAR DAY of the payload's own timestamp,
matching `audit_universe_population.et_session` so the two speak about the same
key. `replay.py` labels the same snapshot by `last_completed_session` instead
and lands it on 2026-08-07. Both labellings are defensible and neither rescues
the payload; what changes is only which session ends up holding it.

Verified on real history (`--since 2026-03-01`): 156 snapshots / 141 sessions,
22 violations -- 5 F1, 8 F2, 9 F4 -- and silent on the other 143 snapshots.

How invisible the premarket row is on the dimension that IS watched: in
`data/history/universe_quality.csv` the 2026-08-10 row (computed from the
premarket payload, and the file's very first row -- the commit that wrote it,
`8fb939f4`, is titled "a clean run, and the guard's first baseline row")
differs from the median of its four neighbouring close sessions by at most
**0.33 percentage points** across the 11 comparable columns, median 0.22pp,
nothing over 5pp. It is not that the null-rate ledger failed to notice. On its
own dimension there was nothing to notice.

`check()` is pure. Reading git history lives in `snapshots()`.

    python3 -m pipeline.tools.audit_universe_freshness
    python3 -m pipeline.tools.audit_universe_freshness --since 2026-08-01 -q
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import zoneinfo
from typing import Dict, List, Optional

UNIVERSE = 'data/output/universe.json'
LOW = 0.5                # below this the payload is not a whole session
HIGH = 3.0               # above this the denominator, not the market, moved
MIN_NAMES = 200          # below this a snapshot is a fragment, not a universe
ET = zoneinfo.ZoneInfo('America/New_York')


def et_session(timestamp) -> Optional[str]:
    """The ET calendar day a snapshot belongs to, from its OWN timestamp.

    Same rule as `audit_universe_population.et_session`, and never the git
    commit date: git filters by the local clock, so a 22:5x UTC scrape lands on
    the next day in JST.
    """
    try:
        dt = datetime.datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(ET).date().isoformat()


def _num(value) -> float:
    """Anything that is not a finite number contributes 0. See the docstring."""
    if value is None or isinstance(value, bool):
        return 0.0
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if f != f or f in (float('inf'), float('-inf')) else f


def aggregate_rvol(rows) -> Optional[float]:
    """sum(volume) / sum(avg_volume) over every row. None when undecidable."""
    traded = sum(_num(r.get('volume')) for r in rows)
    usual = sum(_num(r.get('avg_volume')) for r in rows)
    if usual <= 0:
        return None
    return traded / usual


def classify(rvol: Optional[float], names: int, low: float = LOW,
             high: float = HIGH, min_names: int = MIN_NAMES) -> tuple:
    """(kind, why) for one snapshot. kind is None when the payload looks whole."""
    if names < min_names:
        return 'F3', f'only {names} names, not judged'
    if rvol is None:
        return 'F3', 'avg_volume sums to zero, ratio undecidable'
    if rvol < low:
        return 'F1', (f'aggregate RVOL {rvol:.4f} below {low} -- not a completed '
                      f'session (premarket shape)')
    if rvol > high:
        return 'F2', (f'aggregate RVOL {rvol:.1f} above {high} -- avg_volume died '
                      f'while volume kept arriving')
    return None, ''


def check(records: List[dict], low: float = LOW, high: float = HIGH,
          min_names: int = MIN_NAMES) -> dict:
    """records: [{'session','snapshot','rvol','names'}, ...], any order."""
    rows, violations, warnings = [], [], []
    clean_by_session: Dict[str, int] = {}
    seen_by_session: Dict[str, int] = {}

    for rec in sorted(records, key=lambda r: (r['session'], r.get('snapshot') or '')):
        kind, why = classify(rec.get('rvol'), rec.get('names', 0), low, high, min_names)
        day = rec['session']
        seen_by_session[day] = seen_by_session.get(day, 0) + 1
        clean_by_session.setdefault(day, 0)
        if kind is None:
            clean_by_session[day] += 1
        out = dict(rec)
        out['kind'] = kind
        rows.append(out)
        where = f'{day} ({rec.get("snapshot") or "?"})'
        if kind in ('F1', 'F2'):
            violations.append(f'{kind} {where}: {why}')
        elif kind == 'F3':
            warnings.append(f'F3 {where}: {why}')

    for day in sorted(seen_by_session):
        if clean_by_session[day] == 0 and seen_by_session[day] > 0:
            judged = [r for r in rows if r['session'] == day and r['kind'] != 'F3']
            if judged:
                violations.append(
                    f'F4 {day}: none of its {seen_by_session[day]} snapshot(s) is a '
                    f'completed session -- this session has no usable payload')

    return {'low': low, 'high': high,
            'snapshots': len(rows), 'sessions': len(seen_by_session),
            'rows': rows, 'violations': violations, 'warnings': warnings,
            'ok': not violations}


def snapshots(since: str, path: str = UNIVERSE) -> List[dict]:
    """One record per committed snapshot of `path`, oldest first."""
    out: List[dict] = []
    hashes = subprocess.run(
        ['git', 'log', '--format=%H', f'--since={since}', '--', path],
        capture_output=True, text=True).stdout.split()
    for h in reversed(hashes):
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
        rows = payload.get('rows') or []
        out.append({'session': day, 'snapshot': h[:8], 'names': len(rows),
                    'rvol': aggregate_rvol(rows),
                    'timestamp': payload.get('timestamp')})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--since', default='2026-03-01')
    ap.add_argument('--path', default=UNIVERSE)
    ap.add_argument('--low', type=float, default=LOW)
    ap.add_argument('--high', type=float, default=HIGH)
    ap.add_argument('--min-names', type=int, default=MIN_NAMES)
    ap.add_argument('--json')
    ap.add_argument('-q', '--quiet', action='store_true')
    a = ap.parse_args(argv)

    records = snapshots(a.since, a.path)
    if not records:
        print('BAD  no universe snapshots found -- nothing checked, which is not a pass')
        return 2

    result = check(records, a.low, a.high, a.min_names)
    for rec in result['rows']:
        if a.quiet and rec['kind'] is None:
            continue
        rvol = '     -' if rec['rvol'] is None else f'{rec["rvol"]:10.4f}'
        print(f'{rec["kind"] or "OK":3s} {rec["session"]}  {rec["snapshot"]}  '
              f'names {rec["names"]:5d}  rvol {rvol}')
    for line in result['violations']:
        print(line)
    for line in result['warnings'] if not a.quiet else []:
        print(line)
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump(result, fh, indent=2)
    print(f'\n{"OK" if result["ok"] else "BAD"}: {len(result["violations"])} violation(s), '
          f'{len(result["warnings"])} warning(s) over {result["snapshots"]} snapshot(s) '
          f'/ {result["sessions"]} session(s)')
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
