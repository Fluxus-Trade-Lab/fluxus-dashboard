"""Relative-strength engine: disjoint-window RS, acceleration, four-state.

The Finviz universe ships *cumulative* performance columns (perf_1w, perf_1m,
perf_3m, perf_6m).  Cumulative windows overlap, so differencing them directly
would double-count the recent period.  We first convert them into
**disjoint** buckets by chaining the compound returns apart::

    r(1w..1m) = (1 + perf_1m) / (1 + perf_1w) - 1

Relative strength is then the excess of each disjoint bucket over the
benchmark's same bucket.  Two "acceleration" quantities are shipped and they
answer different questions (FOUR_STATE_DESIGN.md, section 8):

Two display levels ship alongside them -- ``excess_3m`` (the state's level
axis) and ``excess_1m`` (display only) -- so the page's three windows all read
a precomputed excess instead of deriving one of them in the browser.

* ``rs_accel``       -- last month's excess minus the *total* excess of the
                        two months before it.  Unequal windows on purpose: a
                        steady-pace outperformer scores NEGATIVE here.  This
                        is the validated gate that separates Leading from
                        Weakening; it is a high bar, not a slope.
* ``rs_accel_rate``  -- the same comparison with the prior stretch folded to
                        a one-month rate, so a steady pace reads zero.  This
                        is the slope.  Anything that says "accelerating" or
                        "decelerating" in words must read THIS field.

The same functions apply to a single stock, an industry aggregate or a
curated theme aggregate; only the input rows differ.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Cumulative performance columns, ordered near -> far.  The engine derives
# disjoint buckets from consecutive pairs.
CUMULATIVE_COLS: list[str] = ["perf_1w", "perf_1m", "perf_3m", "perf_6m"]

# Disjoint bucket names produced from the columns above.
BUCKETS: list[str] = ["0_1w", "1w_1m", "1m_3m", "3m_6m"]

# Window choice is empirical, not stylistic -- see FOUR_STATE_DESIGN.md and
# validate_accel.py.  Across 139 ETFs x 2y, every scheme whose near bucket was
# two weeks or shorter failed half-sample consistency: the Leading-minus-
# Lagging spread changed sign between the first and second half (one went from
# -2.10% to +0.62%).  Only the month-scale scheme held up on all four tests --
# full sample +1.53%, non-overlapping +1.11%, first half +1.05%, second +1.86%.
#
# So: near bucket = the last month, prior bucket = the two months before it,
# level = cumulative three-month excess.
_LEVEL_COL = "perf_3m"
_NEAR_COL = "perf_1m"       # cumulative 0..1m, used as the near bucket
_PRIOR_BUCKET = "1m_3m"     # disjoint 1m..3m

# The one-month level. Equal to _NEAR_COL today and declared separately anyway:
# _NEAR_COL is an input to the acceleration GATE, which is a validated choice
# that could move if the validation is redone, while this is the window a
# reader picks on the Themes page. One constant serving two questions is how a
# tuning change to one silently rewrites the other.
_LEVEL_1M_COL = "perf_1m"

# Finviz occasionally reports corporate-action artefacts as returns of several
# hundred x (one aerospace name printed +31,192% for perf_1m).  Values beyond
# this magnitude are data errors, not moves, and are dropped before aggregation.
_MAX_PLAUSIBLE_RETURN = 5.0

STATES: list[str] = ["Leading", "Weakening", "Improving", "Lagging"]


def disjoint_returns(row: Mapping[str, Any]) -> Dict[str, float]:
    """Convert cumulative perf_* fields into disjoint bucket returns.

    Missing or non-finite inputs yield NaN for the affected buckets rather
    than silently propagating a zero, which would read as "flat" and put the
    name in the wrong state.
    """
    out: Dict[str, float] = {}
    prev_cum = 0.0
    prev_ok = True

    for col, bucket in zip(CUMULATIVE_COLS, BUCKETS):
        raw = row.get(col)
        cum = float(raw) if raw is not None and np.isfinite(_as_float(raw)) else np.nan

        if not np.isfinite(cum) or not prev_ok:
            out[bucket] = np.nan
            prev_ok = np.isfinite(cum)
            if prev_ok:
                prev_cum = cum
            continue

        # Chain apart: the far window divided by the near window it contains.
        out[bucket] = (1.0 + cum) / (1.0 + prev_cum) - 1.0
        prev_cum = cum
        prev_ok = True

    return out


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def relative_strength(
    row: Mapping[str, Any],
    benchmark: Mapping[str, Any],
) -> Dict[str, float]:
    """Excess return of *row* over *benchmark* for each disjoint bucket."""
    mine = disjoint_returns(row)
    theirs = disjoint_returns(benchmark)
    return {b: mine[b] - theirs[b] for b in BUCKETS}


def acceleration(
    row: Mapping[str, Any],
    benchmark: Mapping[str, Any],
) -> float:
    """Last month's excess minus the TOTAL excess of the two months before it.

    The windows are unequal (21 vs 42 sessions) and that is deliberate: a group
    that outperforms at a perfectly steady pace comes out negative here, so
    this is a high bar ("did the last month beat the two before it combined"),
    not a slope. It is the only thing separating Leading from Weakening, and
    the length-matched variant (V7) was weaker on every validation cut, so the
    gate stays. For the slope, see `acceleration_rate`.
    """
    rs_near = (_as_float(row.get(_NEAR_COL))
               - _as_float(benchmark.get(_NEAR_COL)))
    prior = relative_strength(row, benchmark).get(_PRIOR_BUCKET, np.nan)
    return rs_near - prior


# The prior bucket spans two months against a one-month near bucket.
_PRIOR_MONTHS = 2.0


def _to_monthly_rate(r: float) -> float:
    """Fold a two-month compounded return to its one-month rate.

    Geometric, not linear: these are compounded returns, so the per-period
    rate is the k-th root; a linear divide would understate a positive stretch
    and overstate a negative one. Sign-preserving so a stretch worse than
    -100% (a data artefact) does not raise.
    """
    if not np.isfinite(r):
        return np.nan
    return float(np.sign(1.0 + r) * np.abs(1.0 + r) ** (1.0 / _PRIOR_MONTHS) - 1.0)


def acceleration_rate(
    row: Mapping[str, Any],
    benchmark: Mapping[str, Any],
) -> float:
    """Last month's excess minus the prior stretch's excess AT A MONTHLY RATE.

    Length-matched, so a steady pace reads zero, faster-than-before reads
    positive, slower reads negative -- the quantity the words "accelerating"
    and "decelerating" actually mean. Descriptive only: it does NOT feed
    `classify`, because as a gate it separated Leading from Lagging less well
    than the unequal-window `acceleration` on every cut (V7 in
    validate_accel.py). Ship both; state from the gate, words from the rate.
    """
    rs_near = (_as_float(row.get(_NEAR_COL))
               - _as_float(benchmark.get(_NEAR_COL)))
    mine = disjoint_returns(row).get(_PRIOR_BUCKET, np.nan)
    theirs = disjoint_returns(benchmark).get(_PRIOR_BUCKET, np.nan)
    prior_rate = _to_monthly_rate(mine) - _to_monthly_rate(theirs)
    return rs_near - prior_rate


def classify(excess_3m: float, rs_accel: float) -> str | None:
    """Four-state classification from RS level and RS acceleration.

    Returns None when either input is unusable, so callers can drop the row
    instead of defaulting it into Lagging.
    """
    if not np.isfinite(excess_3m) or not np.isfinite(rs_accel):
        return None
    if excess_3m > 0:
        return "Leading" if rs_accel > 0 else "Weakening"
    return "Improving" if rs_accel > 0 else "Lagging"


# Windows the persistence count is measured across.  A group that only leads
# on one horizon may be riding a single gap; one that leads on all five is
# leading for a reason.  This is the third dimension -- magnitude (level) and
# change (accel) say nothing about how many timescales agree.
PERSISTENCE_COLS: list[str] = ["perf_1w", "perf_1m", "perf_3m", "perf_6m", "perf_1y"]

# The session's change, carried for display next to perf_1w. Deliberately in
# neither list above: a one-day move is not an RS bucket and must not widen the
# persistence denominator. Vendor rows spell it `change_pct`; aggregates and
# payloads spell it `perf_1d` so it sits in the perf_* family it belongs to.
_ONE_DAY_SRC = "change_pct"
ONE_DAY_COL = "perf_1d"


def persistence(
    row: Mapping[str, Any],
    benchmark: Mapping[str, Any],
    cohort: Sequence[Mapping[str, Any]] | None = None,
    top_pct: float = 75.0,
) -> int | None:
    """Horizons this row leads on, as ``(hits, measured)``.

    With a *cohort*, "leads" means top-quartile of that cohort on the horizon
    -- the cross-sectional reading a trader gets from sorting a group table.
    Without one, it falls back to beating the benchmark, which can only be
    judged on windows the benchmark actually reports.

    The denominator is returned rather than assumed: the SPY row carries only
    1w/1m/3m, so a stock's fallback score is out of 3, while a group scored
    against its cohort is out of 5. Printing both as a bare integer would put
    two different scales under one column.
    """
    hits = 0
    seen = 0
    for col in PERSISTENCE_COLS:  # noqa: PLR1702
        mine = _as_float(row.get(col))
        if not np.isfinite(mine):
            continue
        seen += 1
        if cohort:
            peers = [_as_float(r.get(col)) for r in cohort]
            peers = [p for p in peers if np.isfinite(p)]
            if not peers:
                continue
            if mine >= np.percentile(peers, top_pct):
                hits += 1
        else:
            theirs = _as_float(benchmark.get(col))
            if not np.isfinite(theirs):
                seen -= 1          # benchmark lacks this window; do not count it
                continue
            if mine > theirs:
                hits += 1
    return (hits, seen) if seen else None


def _excess(row: Mapping[str, Any], benchmark: Mapping[str, Any], col: str) -> float:
    """Cumulative excess over the benchmark on one column. One definition."""
    return _as_float(row.get(col)) - _as_float(benchmark.get(col))


def excess_3m(row: Mapping[str, Any], benchmark: Mapping[str, Any]) -> float:
    """Three-month return minus the benchmark's -- "by how much is it ahead".

    Named for what it is rather than "rs_level", because the screener already
    ships ``rs_63d`` and the two rank names identically (Spearman 1.00): both
    are built on perf_3m, and subtracting a constant benchmark cannot reorder
    anything. They are not redundant, they answer different questions --
    ``rs_63d`` is a percentile ("ahead of how many"), this is a magnitude
    ("ahead by how much"). A 40-point percentile gap can be half a percent of
    return in a flat tape, or twenty in a trending one.

    Deliberately a *cumulative* column so it stays independent of the disjoint
    buckets that acceleration is built from.
    """
    return _excess(row, benchmark, _LEVEL_COL)


def excess_1m(row: Mapping[str, Any], benchmark: Mapping[str, Any]) -> float:
    """One-month return minus the benchmark's -- the same question, shorter.

    Shipped because the Themes page offers 1W / 1M / 3M and only two of them
    had an excess to read: 1W reduces to the first disjoint bucket (rs_0_1w)
    and 3M ships as excess_3m, so the frontend was deriving the middle one
    itself from perf_1m and a separately-fetched SPY row. Same construction,
    computed twice, in two languages -- the arrangement that put two different
    accelerations on one page. The window belongs here with its siblings.

    NOT a state input. `classify` reads excess_3m and the acceleration gate;
    this is a display level, and adding it changes no classification.
    """
    return _excess(row, benchmark, _LEVEL_1M_COL)


def score_row(
    row: Mapping[str, Any],
    benchmark: Mapping[str, Any],
) -> Dict[str, Any]:
    """Full RS payload for one row: buckets, level, acceleration, state."""
    rs = relative_strength(row, benchmark)
    accel = acceleration(row, benchmark)
    level = excess_3m(row, benchmark)
    state = classify(level, accel)

    payload: Dict[str, Any] = {
        f"rs_{b}": _round(rs[b]) for b in BUCKETS
    }
    payload["excess_3m"] = _round(level)
    payload["excess_1m"] = _round(excess_1m(row, benchmark))
    payload["rs_accel"] = _round(accel)
    payload["rs_accel_rate"] = _round(acceleration_rate(row, benchmark))
    payload["state"] = state
    payload[ONE_DAY_COL] = _round(_first_finite(row, (ONE_DAY_COL, _ONE_DAY_SRC)))
    p = persistence(row, benchmark)
    payload["persistence"] = p[0] if p else None
    payload["persistence_of"] = p[1] if p else None
    return payload


def safe_round(value: Any, digits: int = 6) -> float | None:
    """Round, mapping NaN/inf/None to None.

    Public because every writer of groups.json must use it. Python's
    ``json.dumps`` emits a bare ``NaN``, which is not valid JSON -- browsers
    reject the whole document. One NaN in one perf_1y field took the entire
    Groups page down with a parse error, while the file looked fine on disk
    and served with a 200.
    """
    return _round(value, digits)


def _round(value: float, digits: int = 6) -> float | None:
    if value is None or not np.isfinite(_as_float(value)):
        return None
    return round(float(value), digits)


def aggregate_rows(
    rows: Sequence[Mapping[str, Any]],
    method: str = "median",
) -> Dict[str, float]:
    """Collapse constituent rows into one synthetic row of perf_* columns.

    **Median by default, and that choice is load-bearing.**  A single Finviz
    corporate-action artefact (+31,192% on one aerospace name) moved that
    industry's mean 1-month return from +5% to +629%.  The median was
    unaffected.  Means are available via ``method='mean'`` but should not be
    used on raw vendor data.
    """
    agg: Dict[str, float] = {}
    # Union, not just CUMULATIVE_COLS: persistence needs perf_1y, and a group
    # row that silently lacked it would be scored over 4 windows while a stock
    # row was scored over 5 -- two different scales printed under one name.
    cols = [*CUMULATIVE_COLS, *(c for c in PERSISTENCE_COLS
                                if c not in CUMULATIVE_COLS)]
    for col in [*cols, ONE_DAY_COL]:
        # perf_1d reads the vendor spelling on the way in; a row that already
        # carries perf_1d (a re-aggregated aggregate) is honoured too.
        srcs = (ONE_DAY_COL, _ONE_DAY_SRC) if col == ONE_DAY_COL else (col,)
        values = [
            v for v in (_first_finite(row, srcs) for row in rows)
            if np.isfinite(v) and abs(v) <= _MAX_PLAUSIBLE_RETURN
        ]
        if not values:
            agg[col] = np.nan
        elif method == "mean":
            agg[col] = float(np.mean(values))
        else:
            agg[col] = float(np.median(values))
    return agg


def extension_stats(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Share of members sitting >= 4 and >= 7 ATRs above their SMA50, and the
    median -- read from each member's `atr_from_sma50`; members without it are
    excluded, not counted as zero.

    What it is for (2026-08-17 study, 48 themes x 293 sessions): among
    Leading theme-days the probability of STILL being Leading 21 sessions
    later fell monotonically with this share (>=4 share <20%: 28%; 20-40%:
    14%; 40-60%: 6%; >60%: 0%) while the next-21-day excess return did not
    fall (median +1.6% -> +2.5..3.8%). So it is a warning that the Leading
    label is about to expire -- the rs_accel gate flips after a two-month run
    -- not a call that the theme will underperform. Jacobs's scale-out is a
    single-stock rule; at the group level this says "the move is priced".
    """
    vals = [v for v in (_as_float(r.get("atr_from_sma50")) for r in rows) if np.isfinite(v)]
    if not vals:
        return {"ext_share_4": None, "ext_share_7": None, "ext_median": None, "ext_n": 0}
    a = np.array(vals)
    return {"ext_share_4": round(float((a >= 4).mean()), 4),
            "ext_share_7": round(float((a >= 7).mean()), 4),
            "ext_median": round(float(np.median(a)), 4),
            "ext_n": int(len(a))}


def _first_finite(row: Mapping[str, Any], keys: Sequence[str]) -> float:
    for k in keys:
        v = _as_float(row.get(k))
        if np.isfinite(v):
            return v
    return np.nan


def score_groups(
    universe: Sequence[Mapping[str, Any]],
    group_key: str,
    benchmark: Mapping[str, Any],
    min_members: int = 5,
    method: str = "median",
) -> List[Dict[str, Any]]:
    """Group *universe* by ``group_key`` and score each group.

    Groups with fewer than *min_members* constituents are dropped -- a
    three-stock "industry" produces a relative-strength reading that is
    really just one company's news.
    """
    buckets: Dict[Any, list[Mapping[str, Any]]] = {}
    for row in universe:
        key = row.get(group_key)
        if key in (None, "", "-"):
            continue
        buckets.setdefault(key, []).append(row)

    results: List[Dict[str, Any]] = []
    for name, members in buckets.items():
        if len(members) < min_members:
            continue
        synthetic = aggregate_rows(members, method=method)
        payload = score_row(synthetic, benchmark)
        if payload["state"] is None:
            logger.debug("Group %s has unusable RS inputs - skipped", name)
            continue
        payload["group"] = name
        payload["members"] = len(members)
        payload["tickers"] = sorted(
            str(m.get("ticker")) for m in members if m.get("ticker")
        )
        # Every column the aggregate produced, not just the four used for
        # disjoint buckets -- persistence needs perf_1y, and copying a subset
        # here silently shrank its denominator from 5 to 3.
        for col in synthetic:
            payload[col] = _round(synthetic.get(col, np.nan))
        payload.update(extension_stats(members))
        results.append(payload)

    # Cohort mode: "leading" means top quartile of the other groups on that
    # horizon, which is what sorting a group table by each timeframe shows you.
    # Benchmark mode would fall back to SPY, and SPY carries only three of the
    # five windows -- a 3-window score printed beside a 5-window one.
    for payload in results:
        p = persistence(
            {c: payload.get(c) for c in PERSISTENCE_COLS},
            benchmark, cohort=results,
        )
        payload["persistence"] = p[0] if p else None
        payload["persistence_of"] = p[1] if p else None

    results.sort(key=lambda r: (r["excess_3m"] is None, -(r["excess_3m"] or 0)))
    return results


def rank_within_group(
    universe: Sequence[Mapping[str, Any]],
    group_key: str,
    benchmark: Mapping[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Per-ticker RS payload plus the ticker's percentile inside its group.

    ``top_quartile`` marks the strongest 25 % of a group, which is how a
    leader is separated from a name merely carried along by its theme.
    """
    scored: Dict[str, Dict[str, Any]] = {}
    by_group: Dict[Any, list[str]] = {}

    for row in universe:
        ticker = row.get("ticker")
        if not ticker:
            continue
        payload = score_row(row, benchmark)
        payload["group"] = row.get(group_key)
        scored[str(ticker)] = payload
        if payload["group"] not in (None, "", "-"):
            by_group.setdefault(payload["group"], []).append(str(ticker))

    for _group, tickers in by_group.items():
        usable = [t for t in tickers if scored[t]["excess_3m"] is not None]
        if not usable:
            continue
        series = pd.Series({t: scored[t]["excess_3m"] for t in usable})
        pct = series.rank(pct=True) * 100.0
        for ticker in usable:
            value = float(pct[ticker])
            scored[ticker]["group_pctile"] = round(value, 2)
            scored[ticker]["top_quartile"] = value >= 75.0

    return scored
