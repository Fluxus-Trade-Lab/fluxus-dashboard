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
                   "2024-2026 it did not predict the next month's return, but "
                   "5% drawdown frequency fell monotonically from 27% in "
                   "Damaged to 6% in Extended — on only ten independent "
                   "episodes, in one rising regime"),
    }


def build(board: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """The block that goes into `breadth.json` as `regime`."""
    s = score(board)
    return {
        "bands": BANDS,
        **(s or {"score": None, "band": None,
                 "evidence": "no dimension of the board is measurable"}),
    }
