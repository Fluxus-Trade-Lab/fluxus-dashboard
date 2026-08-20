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

# The tracked set maintains ITSELF. It began as a hand-kept list, and a
# hand-kept list has exactly one failure mode: the column nobody added.
# change_pct was that column — Finviz renamed its header on 2026-08-07, the
# column went 100% null, three screeners emptied and the thrust vote in the
# breadth verdict was cast on nothing, for a week, while the guard reported
# every run "ok" because change_pct was not on its list.
#
# So the list is now derived, not written: every column present in today's
# rows is measured, UNIONED with every column the history file has ever
# recorded. The union is the part that matters — a column that is renamed
# away does not just degrade, it vanishes from the rows, and a guard that
# only reads today's keys would stop watching at the exact moment it should
# scream. History remembers the column existed; its rate reads 100%.
#
# TRACKED remains as the floor: columns measured even before any history
# exists (first run ever).
TRACKED: List[str] = [
    "market_cap", "avg_volume", "close", "volume", "change_pct",
    "perf_1w", "perf_1m", "perf_3m", "perf_6m", "perf_1y",
    "sector", "industry",
]

# Identity/bookkeeping columns: never graded, a null ticker is a row bug not
# a feed regression, and grading free-text noise would drown real alarms.
UNGRADED: frozenset = frozenset({"ticker"})

# Sparse-by-design columns: null on most rows BY DEFINITION, so a high null
# rate is not a symptom. `sp_signal` is set only on the day a structure crosses
# a level (~12% of rows on a normal day); `sp_1st`, `sp_2nd`, `sp_phase`... only
# while a structure exists; `sp_counter` only while one does not. The ladder
# read the first such run as "88% missing" and warned. These are graded on the
# one failure they can have -- going from carrying something to carrying
# NOTHING -- and on nothing else. Names or prefixes.
SPARSE_BY_DESIGN: frozenset = frozenset({
    "sp_signal", "sp_counter", "sp_len", "sp_ll", "sp_hl", "sp_1st", "sp_2nd",
    "sp_tp1", "sp_tp2", "sp_phase", "sp_stop", "sp_days", "sp_dist_1st_pct",
    "sp_dist_2nd_pct",
})
SPARSE_PREFIXES: tuple = ()
# Fundamentals (2026-08-17 source switch): a loss-making name has no EPS
# growth rate and Yahoo has no revenue figure for ~20% of the pool; ~20-55%
# null is the column's nature, not a feed dying. Graded on death only.
SPARSE_BY_DESIGN = SPARSE_BY_DESIGN | frozenset({
    "eps_growth_next_y", "eps_growth_this_y", "revenue_growth", "fund_source", "fund_asof"})


def is_sparse_by_design(field: str) -> bool:
    return field in SPARSE_BY_DESIGN or field.startswith(SPARSE_PREFIXES)


def discovered_fields(rows: Sequence[Mapping[str, Any]],
                      history: Sequence[Mapping[str, str]]) -> List[str]:
    """Union of the floor, today's columns, and every column history knows."""
    fields = set(TRACKED)
    for r in rows[:50]:                       # keys are uniform; sampling is enough
        fields.update(r.keys())
    for h in history[:1]:                     # header via first row's keys
        fields.update(k for k in h.keys() if k != "date")
    return sorted(fields - UNGRADED)

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


def min_reference(history: Sequence[Mapping[str, str]], field: str) -> Optional[float]:
    """The best (lowest) null rate this field has ever recorded.

    The baseline (median of >=5 runs) answers "what is normal"; this answers a
    prior question -- "has this column ever actually been populated". One
    stored value is enough for that, which is what lets the guard grade a
    brand-new column the day after it first appears instead of five runs
    later, and lets it tell a dead feed from a column that never lived.
    """
    vals = []
    for row in history:
        raw = row.get(field)
        if raw in (None, ""):
            continue
        try:
            vals.append(float(raw))
        except ValueError:
            continue
    return min(vals) if vals else None


def assess(rates: Mapping[str, float],
           history: Sequence[Mapping[str, str]]) -> Dict[str, Any]:
    """Grade each field against its own past, and the run as a whole.

    The severity ladder distinguishes three ways a column can be empty:

    * **dead feed** -- it used to be populated (min reference < 30%) and now a
      third or more is missing. Severe: the run does not publish.
    * **never lived** -- every recorded rate is ~100% (eps_growth_next_y has
      been null for its whole life). `unpopulated`, informational: a column
      that never carried data cannot have broken, and halting the pipeline
      over it would teach everyone to ignore the guard.
    * **degrading** -- above its own baseline (or, before one exists, its own
      best-ever plus the bootstrap gates). Warns, still publishes.
    """
    fields: Dict[str, Any] = {}
    for field, rate in rates.items():
        base = baseline(history, field)
        ref = min_reference(history, field)
        if is_sparse_by_design(field):
            # Only "did it die": everything non-null yesterday-ish and 100%
            # null today. A quiet day on a signal column is not a failure, and
            # a first run with nothing to compare against is not either.
            if rate >= 0.999 and ref is not None and ref < 0.999:
                status, why = "severe", (
                    f"sparse-by-design column is 100% null but has carried data "
                    f"before (min {ref*100:.1f}% missing) — the feed behind it has died")
            else:
                status, why = "ok", (
                    f"sparse by design: {(1-rate)*100:.1f}% populated, graded only on death")
            fields[field] = {"rate": rate, "baseline": base, "status": status, "evidence": why}
            continue
        if rate >= 0.95 and (ref is None or ref >= 0.90):
            status, why = "unpopulated", (
                f"{rate*100:.1f}% missing and never below "
                f"{(ref if ref is not None else 1)*100:.0f}% — this column has "
                f"never carried data, so nothing has broken")
        elif rate >= SEVERE_CEILING and ref is not None and ref < 0.30:
            status, why = "severe", (
                f"{rate*100:.1f}% missing in a column that has been as low as "
                f"{ref*100:.1f}% — a feed that worked has died")
        elif rate >= SEVERE_CEILING and ref is None:
            # First run ever: no way to tell dead from never-lived, so warn
            # loudly and publish rather than halt on ignorance.
            status, why = "degraded", (
                f"{rate*100:.1f}% missing on the first recorded run — cannot "
                f"yet distinguish a dead feed from an unpopulated column")
        elif base is None and rate > BOOTSTRAP_DEGRADED \
                and (ref is None or rate > ref * DEGRADED_RATIO + DEGRADED_ABSOLUTE):
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
    """One row per run, replacing any row already stored for `date`.

    Columns are dynamic: the header is the union of what history already
    records and what today measured, so a newly discovered column starts its
    own history the day it first appears and an old column keeps its record
    after it stops appearing. Widening the ledger is how the tracked set
    maintains itself; a fixed header here would quietly discard exactly the
    measurements the discovery step was added to keep.
    """
    kept = [r for r in read_history(path) if r.get("date") != date]
    old_cols = [c for c in (kept[0].keys() if kept else []) if c != "date"]
    cols = ["date", *sorted({*old_cols, *rates.keys()})]
    row = {"date": date, **rates}
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
    history = read_history(path)
    rates = null_rates(rows, discovered_fields(rows, history))
    verdict = assess(rates, history)
    append_history(date, rates, path)

    for field, f in verdict["fields"].items():
        if f["status"] == "severe":
            log.error("universe quality: %s — %s", field, f["evidence"])
        elif f["status"] == "degraded":
            log.warning("universe quality: %s — %s", field, f["evidence"])
    return verdict


# ── Site-wide coverage ──────────────────────────────────────────────────
#
# The operator's directive after the change_pct week: the maintenance scope is
# every file the site actually reads, not just universe.json. Same machinery,
# one ledger per source, so each file's columns accumulate their own history
# and a column dying in etf_data is caught by the same dead-feed rule that now
# guards the universe.

QUALITY_DIR = Path("data/history/quality")


def check_source(source: str, rows: Sequence[Mapping[str, Any]], date: str,
                 history_dir: Path = QUALITY_DIR) -> Dict[str, Any]:
    """Measure, grade and record one site-consumed source.

    Unlike the universe check, a severe verdict here does not halt anything:
    by the time these run the files are already written, and a halt after the
    fact protects nobody. Severe is logged at ERROR and lands in the
    consolidated quality.json where the site itself can show it.
    """
    path = history_dir / f"{source}.csv"
    history = read_history(path)
    rates = null_rates(rows, discovered_fields(rows, history))
    verdict = assess(rates, history)
    append_history(date, rates, path)
    for field, f in verdict["fields"].items():
        if f["status"] == "severe":
            log.error("quality[%s]: %s — %s", source, field, f["evidence"])
        elif f["status"] == "degraded":
            log.warning("quality[%s]: %s — %s", source, field, f["evidence"])
    return verdict


def site_rows(name: str, payload: Any) -> Optional[List[Mapping[str, Any]]]:
    """Flatten one site file into gradeable rows, or None to skip it.

    Extractors are deliberately shallow: they pull the row lists the frontend
    actually iterates. Derived screener outputs (momentum_97, gainers...) are
    not listed -- their columns are projections of universe columns, and
    grading them would alarm twice for one upstream failure.
    """
    try:
        if name == "etf_data":
            return payload if isinstance(payload, list) else None
        if name == "groups_themes":
            return payload.get("themes")
        if name == "groups_stocks":
            s = payload.get("stocks")
            return list(s.values()) if isinstance(s, dict) else None
        if name == "rotation_baskets":
            return payload.get("baskets")
        if name == "breadth_last":
            # breadth.json's history is columnar; the gradeable row is the
            # current snapshot: the `mm` block (counts, ratios) merged with
            # the `breadth` block (percent-above, highs/lows).
            mm = payload.get("mm") or {}
            br = payload.get("breadth") or {}
            row = {**br, **mm}
            return [row] if row else None
        if name == "signals":
            return [v for v in payload.values() if isinstance(v, dict)]
    except Exception:  # noqa: BLE001 — an extractor must never break the run
        return None
    return None


# Which output file feeds each source name.
# Blocks a frontend page cannot render without. 2026-08-19: breadth.json
# shipped without all four of its blocks and check_site said "ok" -- it
# graded row-level null rates, never block-level presence. A missing block
# here grades the source "severe" (and the nightly Discord failure fires via
# the schema gate); additions are free, removals are a break.
REQUIRED_BLOCKS: Dict[str, List[str]] = {
    "breadth.json": ["regime", "state_board", "verdict", "conditions", "breadth", "mm"],
    "watchlist.json": ["zones", "cross_zone", "date"],
    "groups.json": ["themes", "industries", "stocks"],
    "rotation.json": ["verdict", "baskets", "cuts"],
    "universe.json": ["rows", "quality"],
    "ticker_events.json": ["events", "as_of"],
    "market_health.json": ["spy", "qqq"],
    "signals.json": [],
    "etf_data.json": [],
}


def check_required_blocks(output_dir: Path) -> Dict[str, List[str]]:
    """filename -> missing top-level blocks (empty dict = all present)."""
    import json as _json
    missing: Dict[str, List[str]] = {}
    for filename, blocks in REQUIRED_BLOCKS.items():
        fp = output_dir / filename
        if not fp.exists():
            missing[filename] = ["<file missing>"]
            continue
        try:
            payload = _json.loads(fp.read_text())
        except ValueError:
            missing[filename] = ["<unparsable>"]
            continue
        lost = [b for b in blocks if not isinstance(payload, dict) or b not in payload
                or payload.get(b) in (None, [], {})]
        if lost:
            missing[filename] = lost
    return missing


SITE_SOURCES: Dict[str, str] = {
    "etf_data": "etf_data.json",
    "groups_themes": "groups.json",
    "groups_stocks": "groups.json",
    "rotation_baskets": "rotation.json",
    "breadth_last": "breadth.json",
    "signals": "signals.json",
}


def check_site(output_dir: Path, date: str,
               history_dir: Path = QUALITY_DIR) -> Dict[str, Any]:
    """Grade every site-consumed source; return the consolidated report."""
    import json as _json
    report: Dict[str, Any] = {"date": date, "sources": {}}
    for source, filename in SITE_SOURCES.items():
        fp = output_dir / filename
        if not fp.exists():
            report["sources"][source] = {"status": "missing"}
            log.error("quality[%s]: %s does not exist", source, filename)
            continue
        try:
            payload = _json.loads(fp.read_text())
        except ValueError:
            report["sources"][source] = {"status": "unparsable"}
            log.error("quality[%s]: %s is not valid JSON", source, filename)
            continue
        rows = site_rows(source, payload)
        if not rows:
            report["sources"][source] = {"status": "no_rows"}
            continue
        v = check_source(source, rows, date, history_dir)
        report["sources"][source] = {
            "status": v["status"],
            "flagged": {f: x["status"] for f, x in v["fields"].items()
                        if x["status"] not in ("ok", "unpopulated")},
        }
    lost = check_required_blocks(output_dir)
    report["missing_blocks"] = lost
    for filename, blocks in lost.items():
        log.error("quality[site]: %s missing required blocks %s", filename, blocks)
        report["sources"][filename] = {"status": "severe", "flagged": {b: "missing_block" for b in blocks}}
    worst = "ok"
    for s in report["sources"].values():
        if s["status"] in ("severe", "missing", "unparsable"):
            worst = "severe"
            break
        if s["status"] == "degraded":
            worst = "degraded"
    report["status"] = worst
    return report
