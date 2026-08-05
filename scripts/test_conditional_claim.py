#!/usr/bin/env python3
"""Test a 'when X happens, the market does Y' claim against a matched control.

Claims of this shape are cheap to publish and hard to check, and the check is
almost always the same three questions:

  1. **How rare is it really?** 'Rare air' is a claim about frequency and is
     falsifiable on its own, before any forward return is computed.
  2. **Compared to what?** A conditional sample must be compared to the sample
     it was drawn FROM, not to all days. 'SPX up and VIX up' is a subset of
     'SPX up'; measured against all days it inherits whatever up-days do.
  3. **Mean or median?** Over 1-5 days the mean is tail-driven. A sample can
     have a flat mean and a positive median with 58% of outcomes positive —
     'flat to small negative' describes only the first.

Usage:
    .venv/bin/python scripts/test_conditional_claim.py --hist data.json \
        --since 2020 --horizons 1,2,3,4,5
"""
from __future__ import annotations

import math
import statistics as st


def forward_returns(closes: list[float], idx: list[int], k: int) -> list[float]:
    """Close-to-close % return k sessions after each event index."""
    return [(closes[i + k] / closes[i] - 1) * 100 for i in idx if i + k < len(closes)]


def summarise(rets: list[float]) -> dict | None:
    """Mean AND median AND hit rate — reporting only one of the three is how
    these claims survive contact with data."""
    if len(rets) < 2:
        return None
    sd = st.pstdev(rets)
    return {"n": len(rets), "mean": st.mean(rets), "median": st.median(rets),
            "pos_pct": 100 * sum(1 for x in rets if x > 0) / len(rets),
            "sd": sd, "se": sd / math.sqrt(len(rets))}


def compare(event: dict | None, control: dict | None) -> dict | None:
    """Difference in means with its standard error.

    `t` below ~2 means the difference is indistinguishable from noise at this
    sample size. It is reported rather than thresholded so the reader judges.
    """
    if not event or not control:
        return None
    diff = event["mean"] - control["mean"]
    se = math.sqrt(event["se"] ** 2 + control["se"] ** 2)
    return {"diff": diff, "se": se, "t": diff / se if se else None}


def rarity(n_event: int, n_universe: int) -> float:
    """The frequency claim, isolated. 10% of sessions is not rare air."""
    return 100.0 * n_event / n_universe if n_universe else 0.0
