"""The Trade Facilitation Factor, built from Jones' own paper.

    Donald L. Jones, "The trade facilitation factor",
    Stocks & Commodities V. 6:9 (318-321), 1988.

    "A cardinal rule for traders using the Chicago Board of Trade's daily
     Liquidity Data Bank report is to avoid markets that are not 'facilitating'
     trade. Over a period of days, such markets are characterized by decreasing
     volume, a narrowing of the trading range and an increasing number of TPOs
     per tick."

I got this wrong twice before reading the source, and the two mistakes were
different, so both are recorded.

**First**, `facilitation.py` this morning called TFF "a ratio across TPO
expansion, tick activity and volume movement". Wrong on volume: Jones states
plainly that volume is *not considered* — "not that volume is unimportant, but
rather that volume is not available during the trading day" — and offers it only
as an after-the-close fourth cross-check.

**Second**, and worse, I read Jones' "ticks" as tick-by-tick trade data and
concluded we could not implement TFF without a tape. **Ticks here are price
ticks traversed** — the height of the profile in price increments. Figure 5
settles it: TPO-Total 48, Ticks 23, TF Factor 2.1, and 48/23 = 2.09. The tick
count is the number of distinct prices the profile has touched. That is
`len(union of price buckets)`, and we have had it since the profile engine was
built. Class: `wrong_reference` — the same word meaning a different thing in
1988 Chicago than in a modern market-data API.

## The three tables

Jones builds three, and calls the second and third **cross-checks**, not
alternatives:

  * **TPO count** (his Figure 1) — cumulative letters through each half hour.
    Counts time spent at price.
  * **Tick count** (Figure 2) — cumulative distinct prices touched. "The focus
    is on the trading range and its growth."
  * **TPO / tick ratio** (Figure 3) — a third reference. It runs the *other*
    way: "the high ratios are caused by the fattening of the profiles during
    periods of low trade facilitation."

The ratio matters because the first two can both be low on a quiet day and both
be high on a violent one; the ratio separates *fat and slow* from *thin and
fast*, which is the distinction the cardinal rule is actually about.

## How the table is built, and why it is not a simple percentile

This is the part a paraphrase loses. Jones converts each day into a line of
cumulative counts (A..L), then **sorts every day on the LAST column** and
compresses the sorted days into bands by averaging. So the value printed in the
H column of the 85% row is not "the 85th percentile of H periods" — it is
*"what the H period looked like on the days that FINISHED in the 85th band"*.

Reading it intraday therefore estimates **where today is heading**, not where it
currently ranks. Those are different questions and the forward one is the useful
one.

Jones names the cost himself: "there is no guarantee that values in other TPO
columns will uniformly go from low to high", and points at a bump in his own
Figure 1's D column. A column that is not monotone makes the lookup ambiguous,
so `lookup()` reports the ambiguity instead of hiding it behind a nearest-match.

`percentile_line()` computes the plain per-bracket percentile as well, precisely
so the two can be compared rather than confused.

## What the number is not

Non-facilitation is **not bearish and not bullish**. It is an absence of
information, and a warning of range expansion. No function here returns a
direction and the verdict vocabulary contains no directional word.
"""
from __future__ import annotations

from .tpo import price_buckets

# Jones used 210 days compressed into 21 bands of 10. Below this the bands are
# thinner than his and the averaging stops smoothing anything.
MIN_BASELINE_SESSIONS = 60
DEFAULT_ROWS = 21

MEASURES = ("tpo", "tick", "ratio")

# His own case-history language, mapped to the TFF percentages he used it at:
# "Dead, dead, dead" below 1%; "not facilitating" at 15%; "maybe, maybe not —
# actually pretty active" at 45%; "actively facilitating" at 80%; "highly
# facilitating" at 95-100%.
BANDS = ((0.05, "dead"), (0.25, "not_facilitating"), (0.60, "ambiguous"),
         (0.90, "facilitating"), (1.01, "highly_facilitating"))


def tpo_line(bars: list[dict], tick: float) -> list[int]:
    """Cumulative TPO count through each bracket — Jones' Figure 1 input.

    One bracket contributes one letter to every price it touched, so the
    per-bracket contribution is its span in ticks and the line is their running
    sum. A bracket that never moved still contributes one: the auction was
    there, it just did not travel.
    """
    if tick <= 0:
        raise ValueError("tick must be positive")
    out, run = [], 0
    for b in bars:
        run += len(price_buckets(b["low"], b["high"], tick))
        out.append(run)
    return out


def tick_line(bars: list[dict], tick: float) -> list[int]:
    """Cumulative DISTINCT prices touched — Jones' Figure 2 input.

    Not the sum of the TPO line. A price revisited in a later bracket adds a TPO
    and no tick, which is exactly the difference the two tables exist to expose.
    """
    if tick <= 0:
        raise ValueError("tick must be positive")
    seen: set[float] = set()
    out = []
    for b in bars:
        seen.update(price_buckets(b["low"], b["high"], tick))
        out.append(len(seen))
    return out


def ratio_line(bars: list[dict], tick: float) -> list[float]:
    """TPOs per tick — Jones' Figure 3. HIGH means a fat, slow profile."""
    return [round(t / k, 4) if k else 0.0
            for t, k in zip(tpo_line(bars, tick), tick_line(bars, tick))]


def _line(bars, tick, measure):
    if measure not in MEASURES:
        raise ValueError(f"measure must be one of {MEASURES}")
    return {"tpo": tpo_line, "tick": tick_line, "ratio": ratio_line}[measure](bars, tick)


def build_table(sessions: dict[str, list[dict]], tick: float,
                measure: str = "tpo", rows: int = DEFAULT_ROWS) -> dict:
    """Jones' table: days sorted on the LAST column, compressed into bands.

    Only sessions long enough to reach the final bracket take part in the sort,
    because a half day has no last column and ranking it by a column it never
    printed would put quiet-by-truncation days in the dead band.
    """
    lines = {d: _line(bs, tick, measure) for d, bs in sessions.items()}
    if not lines:
        return {"tick": tick, "measure": measure, "n_sessions": 0,
                "rows": [], "n_brackets": 0}
    full = max(len(v) for v in lines.values())
    complete = {d: v for d, v in lines.items() if len(v) == full}

    ordered = sorted(complete.values(), key=lambda v: v[-1])
    n = len(ordered)
    group = max(1, n // rows)
    bands = []
    for r in range(rows):
        chunk = ordered[r * group:(r + 1) * group] if r < rows - 1 \
            else ordered[(rows - 1) * group:]
        if not chunk:
            continue
        bands.append({
            "tff": round(r / (rows - 1), 4) if rows > 1 else 1.0,
            "n_days": len(chunk),
            "columns": [round(sum(c[i] for c in chunk) / len(chunk), 4)
                        for i in range(full)],
        })
    return {"tick": tick, "measure": measure, "n_sessions": n,
            "n_excluded_short": len(lines) - n,
            "rows": bands, "n_brackets": full, "group_size": group}


def _column(table: dict, i: int) -> list[tuple[float, float]]:
    return [(b["columns"][i], b["tff"]) for b in table["rows"]
            if i < len(b["columns"])]


def lookup(table: dict, bracket: int, value: float) -> dict | None:
    """Cross today's count in this bracket's column over to the TFF column.

    Jones: "look up that value in the table and obtain an immediate estimate of
    facilitation from the TFF column."

    A column need not be monotone — he says so and shows a bump in his own
    Figure 1. Where the nearest match is ambiguous the runner-up is returned
    alongside, because a silent nearest-match would present a coin flip between
    two bands as a reading.
    """
    col = _column(table, bracket)
    if not col:
        return None
    ranked = sorted(col, key=lambda cv: (abs(cv[0] - value), cv[1]))
    best = ranked[0]
    runner = ranked[1] if len(ranked) > 1 else None
    ambiguous = bool(runner and abs(runner[0] - value) == abs(best[0] - value)
                     and runner[1] != best[1])
    monotone = all(a[0] <= b[0] for a, b in zip(col, col[1:]))
    return {"tff": best[1], "matched_column_value": best[0], "value": value,
            "ambiguous": ambiguous,
            "runner_up_tff": runner[1] if runner else None,
            "column_monotone": monotone}


def percentile_line(bars: list[dict], tick: float, sessions: dict,
                    measure: str = "tpo") -> list[float | None]:
    """The plain per-bracket percentile — a DIFFERENT question from the table.

    Kept beside Jones' construction so the two can be compared. This one asks
    "how does today's bracket 5 rank among all bracket 5s"; his asks "days that
    looked like this at bracket 5 finished where". Confusing them is the kind of
    substitution this project keeps auditing for.
    """
    today = _line(bars, tick, measure)
    hist = [_line(bs, tick, measure) for bs in sessions.values()]
    out: list[float | None] = []
    for i, v in enumerate(today):
        sample = [h[i] for h in hist if i < len(h)]
        if len(sample) < MIN_BASELINE_SESSIONS:
            out.append(None)
            continue
        below = sum(1 for x in sample if x < v)
        equal = sum(1 for x in sample if x == v)
        out.append(round((below + equal / 2) / len(sample), 4))
    return out


def band(tff: float, measure: str = "tpo") -> str:
    """Name the reading — INVERTING the ratio table, which runs the other way.

    Caught on the first live run, where 2026-08-12 printed "ratio TFF 100% —
    highly facilitating" beside two tables reading dead. Jones says the opposite
    in as many words: "the high ratios are caused by the fattening of the
    profiles during periods of LOW trade facilitation." A high TPO-per-tick
    reading is a fat, slow profile.

    So the ratio table's percentile is a rank of *fatness*, and calling a fat
    profile "highly facilitating" inverted the one thing the table is for. The
    percentile itself was right; only the word attached to it was wrong, which
    is how this class of error always arrives.
    """
    if measure not in MEASURES:
        raise ValueError(f"measure must be one of {MEASURES}")
    x = 1.0 - tff if measure == "ratio" else tff
    for cut, name in BANDS:
        if x < cut:
            return name
    return BANDS[-1][1]


def read(bars: list[dict], tick: float, tables: dict) -> dict | None:
    """Today's reading on all three of Jones' tables, plus his cross-check.

    `tables` maps each measure name to a table from `build_table`. All three are
    reported. They are not averaged into a score: Jones treats the second and
    third as cross-checks on the first, and a mean of a cross-check and the thing
    it checks is neither.
    """
    if not bars or not tables:
        return None
    first = next(iter(tables.values()))
    if first.get("n_sessions", 0) < MIN_BASELINE_SESSIONS:
        return {"measurable": False, "note": (
            f"baseline holds {first.get('n_sessions', 0)} sessions; "
            f"{MIN_BASELINE_SESSIONS} needed"), "measures": {}}

    out, last_i = {}, len(bars) - 1
    for m, tbl in tables.items():
        if tbl["tick"] != tick:
            raise ValueError(
                f"the {m} table was built on tick {tbl['tick']} and this session "
                f"on {tick}; counts are denominated in ticks and do not compare")
        line = _line(bars, tick, m)
        i = min(last_i, tbl["n_brackets"] - 1)
        hit = lookup(tbl, i, line[i])
        out[m] = {**(hit or {}), "line": line, "through_bracket": i + 1,
                  "measure": m,
                  "band": band(hit["tff"], m) if hit else None}

    return {"measurable": True, "measures": out,
            "through_bracket": out[next(iter(out))]["through_bracket"],
            "note": _explain(out)}


def _explain(m: dict) -> str:
    """One sentence, built whole per branch — the shared-prefix shape has let a
    correct check down three times in this project."""
    t = m.get("tpo")
    if not t:
        return "no TPO table available"
    head = (f"TPO TFF {t['tff']:.0%} through bracket {t['through_bracket']} — "
            f"{t['band'].replace('_', ' ')}")
    k = m.get("tick")
    if not k:
        return f"{head}; no tick cross-check"
    if abs(k["tff"] - t["tff"]) <= 0.15:
        return f"{head}; the tick table agrees at {k['tff']:.0%}"
    return (f"{head}; the tick table disagrees at {k['tff']:.0%} — range and "
            f"time are telling different stories")


def is_non_facilitating(r: dict | None) -> bool | None:
    """Jones' cardinal rule as one question. None when unmeasurable.

    True is not a short signal. It says the session carried little information
    and that range expansion is the risk being warned about.
    """
    if not r or not r.get("measurable"):
        return None
    return r["measures"]["tpo"]["band"] in ("dead", "not_facilitating")
