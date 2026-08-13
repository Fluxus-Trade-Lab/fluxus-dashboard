"""Field-level null-rate guard for the universe.

**Why row counts are not enough.** On 2026-08-09 the daily run produced a
universe of exactly 5,615 rows, the same as a good run, with identical
missingness on every Finviz-sourced column. What had collapsed was the two
columns yfinance enrichment supplies: `avg_volume` went from 1.2% missing to
8.2%, `perf_3m` from 3.0% to 9.9%. Nothing failed. The file was valid JSON, the
schema was complete, and the pipeline's only check -- "is the file non-empty" --
passed.

The damage was downstream and silent. `is_tradeable` multiplies `avg_volume` by
`close`, so a missing volume reads as zero dollars traded: Rocket Lab, at $49.5
billion of market cap, was classified untradeable because we did not know its
volume. 216 names left the tradeable set that way, and since every RS column is
a percentile *within* that set, every threshold in the product moved with them.

**Self-calibrating, not asserted.** A fixed "fail above 5%" is a number nobody
can defend. What is defensible is that a field's null rate should not suddenly
depart from its own recent history, so the guard compares today against the
trailing median of previous runs and only falls back to an absolute ceiling
before that history exists. The history lives in a CSV that the daily job
already commits, so it accumulates whether or not anyone is watching.

**Unmeasurable is not zero** -- the same rule `state_board` enforces. A name
excluded because we have no volume for it and a name excluded because it truly
trades $200k a day are different facts, and `tradeable_status` keeps them apart
so the guard can count the first kind.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

log = logging.getLogger(__name__)

HISTORY = Path("data/history/universe_quality.csv")

# Columns whose absence changes what the product says. Everything here either
# gates membership of the tradeable set or feeds a score computed within it.
TRACKED: List[str] = [
    "market_cap", "avg_volume", "close", "volume",
    "perf_1w", "perf_1m", "perf_3m", "perf_6m", "perf_1y",
    "sector", "industry",
]

# Enough history for a median to mean anything. Below this the guard uses the
# absolute ceiling only, and says so rather than pretending to a baseline.
MIN_HISTORY = 5

# Departure from the field's own trailing median that counts as degraded.
# Both must be exceeded: a field that normally sits at 0.2% can triple to 0.6%
# on nothing, and a field that normally sits at 9% should not trip on 12%.
DEGRADED_RATIO = 3.0
DEGRADED_ABSOLUTE = 0.03

# No baseline excuses this. A third of a column missing is a broken feed
# whatever last week looked like.
SEVERE_CEILING = 0.33

# Used only while `MIN_HISTORY` runs have not accumulated. A guard that grades
# nothing until it has five days of history is blind for exactly the week it is
# newest, and that week happened: on 2026-08-12, with two runs stored,
# avg_volume reached 22.4% missing and the run passed as "ok" because there was
# no baseline to depart from and 22.4% sits under the ceiling.
#
# The number is read off the four observations we have rather than asserted.
# Healthy enrichment runs: 1.2%, 2.0%. Broken ones: 8.2%, 22.4%. Five per cent
# sits in the empty gap between those clusters. It is a bootstrap, not a
# permanent threshold -- once a real baseline exists it is never consulted.
BOOTSTRAP_DEGRADED = 0.05


def null_rate(rows: Sequence[Mapping[str, Any]], field: str) -> float:
    """Share of rows where `field` is absent, None, or empty string."""
    if not rows:
        return 1.0
    missing = sum(1 for r in rows if r.get(field) in (None, "", float("nan"))
                  or r.get(field) != r.get(field))
    return missing / len(rows)


def null_rates(rows: Sequence[Mapping[str, Any]],
               fields: Sequence[str] = TRACKED) -> Dict[str, float]:
    return {f: round(null_rate(rows, f), 6) for f in fields}


def tradeable_status(row: Mapping[str, Any], min_cap: float,
                     min_dollar_volume: float) -> str:
    """`tradeable` / `excluded` / `unmeasurable`.

    The third value is the point of this function. `is_tradeable` has to return
    a bool and so must answer False for a name it cannot measure -- you cannot
    size a position on a number you do not have. But False then means two
    different things, and only one of them is a fact about the market. Counting
    them apart is what turns "216 names dropped out" into "216 names dropped out
    because a column went missing".
    """
    cap = row.get("market_cap")
    vol = row.get("avg_volume")
    close = row.get("close")
    if cap is None or vol is None or close is None:
        return "unmeasurable"
    return ("tradeable" if cap >= min_cap and vol * close >= min_dollar_volume
            else "excluded")


def read_history(path: Path = HISTORY) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def baseline(history: Sequence[Mapping[str, str]], field: str) -> Optional[float]:
    """Trailing median null rate for `field`, or None if too little history."""
    vals = []
    for row in history:
        raw = row.get(field)
        if raw in (None, ""):
            continue
        try:
            vals.append(float(raw))
        except ValueError:
            continue
    if len(vals) < MIN_HISTORY:
        return None
    vals.sort()
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def assess(rates: Mapping[str, float],
           history: Sequence[Mapping[str, str]]) -> Dict[str, Any]:
    """Grade each field against its own past, and the run as a whole."""
    fields: Dict[str, Any] = {}
    for field, rate in rates.items():
        base = baseline(history, field)
        if rate >= SEVERE_CEILING:
            status, why = "severe", f"{rate*100:.1f}% missing, above the {SEVERE_CEILING*100:.0f}% ceiling"
        elif base is None and rate > BOOTSTRAP_DEGRADED:
            status, why = "degraded", (
                f"{rate*100:.1f}% missing, above the {BOOTSTRAP_DEGRADED*100:.0f}% "
                f"bootstrap limit used while no baseline exists "
                f"({len(history)} of {MIN_HISTORY} runs stored)")
        elif base is None:
            status, why = "ok", f"{rate*100:.1f}% missing, no baseline yet ({len(history)} runs stored)"
        elif rate > base * DEGRADED_RATIO and rate - base > DEGRADED_ABSOLUTE:
            status, why = "degraded", (f"{rate*100:.1f}% missing against a "
                                       f"{base*100:.1f}% baseline")
        else:
            status, why = "ok", f"{rate*100:.1f}% missing, baseline {base*100:.1f}%"
        fields[field] = {"rate": rate, "baseline": base, "status": status,
                         "evidence": why}

    worst = "ok"
    for f in fields.values():
        if f["status"] == "severe":
            worst = "severe"
            break
        if f["status"] == "degraded":
            worst = "degraded"
    return {"status": worst, "fields": fields,
            "runs_in_baseline": len(history)}


def append_history(date: str, rates: Mapping[str, float],
                   path: Path = HISTORY) -> None:
    """One row per run, replacing any row already stored for `date`."""
    cols = ["date", *TRACKED]
    kept = [r for r in read_history(path) if r.get("date") != date]
    row = {"date": date, **{f: rates.get(f) for f in TRACKED}}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted([*kept, row], key=lambda r: str(r["date"])))


def check(rows: Sequence[Mapping[str, Any]], date: str,
          path: Path = HISTORY) -> Dict[str, Any]:
    """Measure, grade, record. Returns the block that goes into universe.json.

    Recording happens even when the run is severe: a bad day belongs in the
    baseline's history as much as a good one, and excluding it would let a slow
    drift raise the baseline until nothing ever trips.
    """
    rates = null_rates(rows)
    verdict = assess(rates, read_history(path))
    append_history(date, rates, path)

    for field, f in verdict["fields"].items():
        if f["status"] == "severe":
            log.error("universe quality: %s — %s", field, f["evidence"])
        elif f["status"] == "degraded":
            log.warning("universe quality: %s — %s", field, f["evidence"])
    return verdict
