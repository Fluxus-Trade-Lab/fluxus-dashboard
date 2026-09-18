"""Regime score -- the state board collapsed into one number.

**Why collapse it at all.** The board is nine dimensions with evidence attached,
which is more information than a competitor's single 0-100 reading and less
usable. A chain that runs environment -> theme -> stock needs each link to hand
the next one something sortable; L2 and L3 already are numbers, and L1 was an
instrument panel. This is the missing convergence, not a new measurement --
every input is a level the board already computed and published.

**What it is: a census of conditions, equally weighted.** The mean of the
measured levels, on the board's own 0-4 ordinal scale, expressed 0-100. Equal
weight is a choice against a false precision: any weighting we could write down
would be an unfalsifiable opinion about which dimension matters more, dressed
up as arithmetic. `coverage` is published beside the score for the same reason
-- an eight-of-nine score and a six-of-nine score are not the same claim.

**It says nothing about the mean.** Tested over 558 sessions (2024-05 to
2026-08), the score does not predict the next month's return, and what signal
there is runs the wrong way for acting on it:

    forward 21d, SPX                Spearman -0.08 full, -0.29 non-overlapping
    forward 21d, IWM over SPY       -0.15 full, -0.16 non-overlapping
    forward 21d, IPOs over SPY      -0.18 full, -0.35 non-overlapping

Negative in fifteen of sixteen cells across full / non-overlapping / half
samples. High readings were followed by *less* reward for taking risk, not
more.

**It does separate the left tail.** Mean and tail are different statistical
objects, and the same score that is flat against one is monotone against the
other. Probability that SPX draws down 5% or more within the next 21 sessions,
by band, over the same window:

    Damaged   27.2%   (first half 30.7, second half 23.7)
    Mixed     10.9%   (15.3, 6.7)
    Healthy    9.8%   (14.3, 5.4)
    Extended   5.8%   (9.1, 2.6)

Monotone in the full sample and in both halves; the worst band carries about
4.7x the drawdown frequency of the best. This is close to mechanical rather
than clairvoyant -- "damaged" means breadth is already broken, and a broken
tape is more likely to break further -- which is also why the mean washes out:
the drawdown is followed by the recovery.

**Re-cut 2026-09-18** on the original-definition inputs (thrust, quarterly
25%, ratios = Stockbee's own scans), with history back-filled from his
published Market Monitor sheet -- our own counts match his within a few
percent on every overlapping day. 587 sessions, index repair rebuilt from
SPY/QQQ closes (data/research/regime_recal_2026-09-18):

    quartiles 50.0 / 64.3 / 75.0 -- on the score's own grid these cut
    exactly where 47 / 63 / 75 do, so the constants stand
    Damaged 28.3%   Mixed 11.9%   Healthy 8.1%   Extended 6.5%
    Damaged vs the other three: 28.3% vs 8.7% (halves 37.5/13.7, 16.4/3.9)

Only Damaged separates reliably: the upper three order in the full sample
but not in the first half (Healthy 11.4% < Extended 14.3%). Selling pressure
reads down_4pct_stockbee (re-checked the same day it moved). The table
above is kept as the 08-09 record.

The ten-episode caveat below is now partly answered for one input. On his
sheet alone, 2009-2026 (4,418 sessions, ~60 independent episodes), the
damage condition's own levels run 27.4 / 16.6 / 15.1 / 10.0% worst to best,
and worst-above-best holds in each of 2009-14, 2015-19, 2020-23, 2024-26.
The composite itself still has only 2.2 years.

Not calibrated: `extremes` now reads common-stock new highs/lows, which exist
from 2026-08-28 only, so it is unmeasured across the whole calibration
window. On the 14 days it exists it lowers the score by 3.8 points on average.

**So its use is the risk budget, not the direction.** It answers how much can
be lost here, never which way to lean.

Three caveats that matter as much as the numbers. The sample is a single
rising regime, in which every damaged reading was in fact a dip to buy. Those
537 observations overlap: they contain only **ten independent 5% drawdown
episodes**, so the effective sample is ten, not five hundred. And at roughly
5.5 such episodes a year, a defensible tail model needs about twenty years of
inputs -- which our breadth archive, 2.2 years old, does not have.

The bands are therefore named for the tape they describe, never for the action
they imply. There is no "tactical bull" band here, because we cannot show that
a high reading makes swing trading work.

Pure functions, no I/O and no clock -- the Time Machine replays these.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from pipeline.screeners.state_board import LEVELS

# Cuts are the empirical quartiles of the score over the 558 sessions in
# `data/history/breadth_archive.csv` as of 2026-08-09, rounded: p25 46.9,
# p50 62.5, p75 75.0. Quartiles rather than the round numbers a competitor
# asserts, so that "top band" means "the strongest quarter of what we have
# actually seen" instead of "85 out of an imagined 100".
#
# Frozen constants, not recomputed per run: a threshold that drifts with every
# new session would relabel yesterday's reading without yesterday changing.
#
# ⚠ THERE ARE TWO BAND SCHEMES OVER THE SAME 0-100 SCORE. They are deliberate,
# not a duplication -- but they are not interchangeable, and mixing them up
# silently produces wrong attribution tables (it already did once):
#
#   THIS FILE  Damaged / Mixed / Healthy / Extended, cuts 47 / 63 / 75.
#              Empirical quartiles, validated monotone against 5% drawdown
#              frequency. USE FOR ANALYSIS: bucketing trades by regime,
#              risk-budget work, anything statistical.
#
#   frontend/src/components/dashboard/RegimeBand.jsx
#              Defence / Caution / Neutral / Constructive / Full, even cuts
#              12 / 34 / 56 / 78. Position language -- what the state permits
#              you to hold. USE FOR DISPLAY: the dashboard's regime band.
#              Even cuts on purpose; a fitted curve there would be a second,
#              unvalidated model sitting on top of this one.
#
# If you are attributing trade performance to market state, use THIS file's
# bands and say so in the output label.
BANDS: List[Dict[str, Any]] = [
    {"key": "damaged",  "label": "Damaged",  "min": 0,  "max": 47,
     "describes": "most conditions absent or very weak"},
    {"key": "mixed",    "label": "Mixed",    "min": 47, "max": 63,
     "describes": "conditions split — repair started, not carried"},
    {"key": "healthy",  "label": "Healthy",  "min": 63, "max": 75,
     "describes": "most conditions met"},
    {"key": "extended", "label": "Extended", "min": 75, "max": 101,
     "describes": "nearly every condition met at once"},
]

_MAX_LEVEL = len(LEVELS) - 1


def band_for(score: float) -> Dict[str, Any]:
    for b in BANDS:
        if b["min"] <= score < b["max"]:
            return b
    return BANDS[-1]


def score(board: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    """Collapse a state board into `{score, band, coverage, evidence}`.

    Returns None when nothing on the board is measurable. Unmeasured dimensions
    are excluded from the mean rather than scored zero -- treating "we have no
    bond data" as "bonds are bad" is the specific dishonesty `state_board`
    exists to prevent, and it would be reintroduced here by a fixed
    denominator.
    """
    levels = [r["level"] for r in board if r.get("level") is not None]
    if not levels:
        return None

    raw = sum(levels) / len(levels) / _MAX_LEVEL
    pts = round(raw * 100, 1)
    b = band_for(pts)

    strong = [r["key"] for r in board if (r.get("level") or 0) >= _MAX_LEVEL]
    weak = [r["key"] for r in board
            if r.get("level") is not None and r["level"] <= 1]

    parts = [f"{len(levels)} of {len(board)} conditions measured, "
             f"averaging {sum(levels)/len(levels):.1f} of {_MAX_LEVEL}"]
    if strong:
        parts.append(f"at full strength: {', '.join(strong)}")
    if weak:
        parts.append(f"weak or absent: {', '.join(weak)}")

    return {
        "score": pts,
        "band": b["key"],
        "band_label": b["label"],
        "describes": b["describes"],
        "measured": len(levels),
        "of": len(board),
        "strong": strong,
        "weak": weak,
        "evidence": "; ".join(parts),
        # Carried on every payload so no consumer can render the number
        # without the finding that qualifies it.
        # Two separate claims, because they point opposite ways and a single
        # boolean would have to lie about one of them.
        "predicts_return": False,
        "separates_tail": True,
        "caveat": ("a risk-budget reading, not a direction call: over "
                   "2024-2026 it did not predict the next month's return; "
                   "5% drawdown frequency was 28% in Damaged against 9% in "
                   "the other three bands, which do not separate from each "
                   "other — on about ten independent episodes. The damage "
                   "condition alone, on Stockbee's own counts 2009-2026 "
                   "(~60 episodes), ran 27% at its worst level against 10% "
                   "at its best, in every era"),
    }


def build(board: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """The block that goes into `breadth.json` as `regime`."""
    s = score(board)
    return {
        "bands": BANDS,
        **(s or {"score": None, "band": None,
                 "evidence": "no dimension of the board is measurable"}),
    }
