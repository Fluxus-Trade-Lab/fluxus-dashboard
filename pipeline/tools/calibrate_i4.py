"""I4/I7 bands -- measured from the archives instead of guessed.

DATA_RELIABILITY.md §六.1 said the I4 thresholds (0.30x / 3.0x of the
trailing median) were "拍的". Measuring them says worse than that: over the
96 checkable sessions in ticker_events.csv the daily row count has never
left [0.63x, 2.28x], so the band has never fired and could only fire on a
catastrophe. It is decoration, not a gate.

The leak it waves through is the one the archives already lived: Finviz
renamed `Change` to `Change %` on 2026-08-07 (fix e8ac440, a week later),
change_pct went 100% null, and the three screeners that read it wrote
ZERO rows on 08-07 / 08-11 / 08-12 / 08-13. breadth counted 956 / 530 /
527 / 617 names up >=4% on those same days. Total ticker_events rows on
those days: 0.68x / 1.00x / 1.05x / 1.17x the trailing median. Nothing in
the pipeline said a word -- is_plausible_day only wants >=4 of 7 screeners
reporting, and 4 were.

So the unit of the check is the SERIES, not the file:

  reliable  present on >=95% of sessions AND trailing median >= 20 rows
            -> writing zero rows is a VIOLATION (I7)
  sparse    everything else (episodic_pivot's median is 4; some presets
            legitimately return nothing) -> absence says nothing

and each series carries its own count band, the empirical [p02, p98] of
its ratio-to-trailing-median widened by `--margin`, floored/ceiled so a
thin history cannot mint an absurdly tight band.

The registry is COMMITTED and only moves on an explicit --update, exactly
like schema_snapshot.json. That is the whole point: a rolling recompute
lets an outage teach the baseline that it is normal. Frozen on data before
2026-08-07 this registry flags all four dead sessions and none of the
healthy ones; recomputed rolling, it flags 08-07 and 08-11 and then goes
quiet while the outage continues.

    python -m pipeline.tools.calibrate_i4              # print, write nothing
    python -m pipeline.tools.calibrate_i4 --update     # rewrite the registry
    python -m pipeline.tools.calibrate_i4 --until 2026-08-06   # freeze a cut
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

HISTORY = Path("data/history")
BANDS = Path("data/reference/i4_bands.json")

WINDOW = 20            # trailing sessions the ratio is measured against
MIN_SESSIONS = 12      # below this a series gets no band at all
RELIABLE_PRESENCE = 0.95
RELIABLE_MEDIAN = 20   # rows; below this an empty day is ordinary
MARGIN = 0.15          # widen the empirical band by this fraction each side
FLOOR_CAP = 0.60       # a floor is never stricter than this
CEIL_FLOOR = 1.60      # a ceiling is never tighter than this


def _ratios(counts: pd.Series) -> List[float]:
    """count / median(previous WINDOW sessions), one per session that has one."""
    out: List[float] = []
    vals = counts.tolist()
    for i in range(len(vals)):
        prev = [v for v in vals[max(0, i - WINDOW):i] if v == v and v > 0]
        if len(prev) < 5:
            continue
        med = pd.Series(prev).median()
        if med > 0 and vals[i] == vals[i]:
            out.append(float(vals[i]) / float(med))
    return out


def _band(ratios: List[float]) -> Dict[str, float]:
    s = pd.Series(ratios)
    lo = float(s.quantile(0.02)) * (1 - MARGIN)
    hi = float(s.quantile(0.98)) * (1 + MARGIN)
    return {"floor": round(min(lo, FLOOR_CAP), 3), "ceil": round(max(hi, CEIL_FLOOR), 3),
            "observed_min": round(float(s.min()), 3), "observed_max": round(float(s.max()), 3),
            "n": int(len(s))}


def calibrate(history: Path = HISTORY, until: Optional[str] = None) -> Dict[str, Any]:
    """Registry for every archive that carries a series column."""
    from pipeline.tools.audit_archives import ARCHIVES

    reg: Dict[str, Any] = {"window": WINDOW, "margin": MARGIN,
                           "reliable_presence": RELIABLE_PRESENCE,
                           "reliable_median_rows": RELIABLE_MEDIAN,
                           "built_until": until or "", "archives": {}}
    for name, spec in ARCHIVES.items():
        if not spec.get("counts"):
            continue
        path = history / name
        if not path.exists():
            continue
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        dcol = spec["date"]
        if dcol not in frame.columns:
            continue
        frame[dcol] = frame[dcol].astype(str)
        if until:
            frame = frame[frame[dcol] < until]
        if not len(frame):
            continue
        entry: Dict[str, Any] = {"sessions": int(frame[dcol].nunique()), "series": {}}
        total = frame.groupby(dcol).size().sort_index()
        if len(total) >= MIN_SESSIONS:
            r = _ratios(total)
            if r:
                entry["total"] = _band(r)
        scol = spec.get("series")
        if scol and scol in frame.columns:
            counted = frame[[dcol, scol]].copy()
            counted["_n"] = 1
            piv = counted.pivot_table(index=dcol, columns=scol, values="_n",
                                      aggfunc="sum").sort_index()
            n_sessions = len(piv)
            for series in piv.columns:
                col = piv[series]
                seen = int(col.notna().sum())
                if seen < MIN_SESSIONS:
                    continue
                presence = seen / n_sessions
                med = float(col.dropna().median())
                kind = ("reliable" if presence >= RELIABLE_PRESENCE and med >= RELIABLE_MEDIAN
                        else "sparse")
                item: Dict[str, Any] = {"kind": kind, "presence": round(presence, 3),
                                        "median_rows": round(med, 1), "sessions_seen": seen}
                r = _ratios(col)
                if r:
                    item["band"] = _band(r)
                entry["series"][str(series)] = item
        reg["archives"][name] = entry
    return reg


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true", help="write data/reference/i4_bands.json")
    ap.add_argument("--until", help="only use sessions strictly before this ISO date")
    ap.add_argument("--history", default=str(HISTORY))
    ap.add_argument("--out", default=str(BANDS))
    args = ap.parse_args(argv)

    reg = calibrate(Path(args.history), args.until)
    for name, e in reg["archives"].items():
        t = e.get("total")
        print(f"{name}  sessions={e['sessions']}"
              + (f"  total band [{t['floor']}, {t['ceil']}] (seen {t['observed_min']}-{t['observed_max']}, n={t['n']})" if t else ""))
        for s, v in sorted(e["series"].items(), key=lambda kv: (kv[1]["kind"], kv[0])):
            b = v.get("band")
            print(f"    {v['kind']:8s} {s:26s} med={v['median_rows']:>7.1f} present={v['presence']:.0%}"
                  + (f"  band [{b['floor']}, {b['ceil']}]" if b else ""))
    if args.update:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(reg, indent=1) + "\n")
        print(f"\nwrote {p}")
    else:
        print("\n(dry run -- pass --update to write the registry)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
