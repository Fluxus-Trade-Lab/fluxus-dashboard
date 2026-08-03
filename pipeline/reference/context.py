"""Historical + structural context for a GEX reading — pure, no IO.

A level on its own says nothing. "net GEX -1.9B" only becomes information once you
know where that sits in its own recent history, how the walls moved since yesterday,
and which strikes rank behind the headline walls. This module supplies that framing
and nothing else — it does not fetch, judge, or recommend.
"""
from __future__ import annotations


def percentile_of(value: float, history: list[float]) -> dict:
    """Where `value` sits within `history`, with the sample size attached.

    `n` is returned deliberately: a percentile over 14 sessions and one over 500
    look identical on the page and are not remotely the same claim. Callers must
    be able to show the reader which one they are looking at.
    """
    sample = [h for h in history if h is not None]
    n = len(sample)
    if n == 0:
        return {"pct": None, "n": 0, "min": None, "max": None, "thin": True}
    below = sum(1 for h in sample if h < value)
    ties = sum(1 for h in sample if h == value)
    pct = (below + 0.5 * ties) / n * 100.0
    return {
        "pct": round(pct, 1),
        "n": n,
        "min": min(sample),
        "max": max(sample),
        # Under ~30 observations a percentile is indicative at best.
        "thin": n < 30,
    }


def ranked_levels(per_strike: dict[float, float],
                  spot: float,
                  exclude: set[float] | None = None,
                  n: int = 7) -> list[dict]:
    """Strikes ranked by |net GEX|, the headline walls removed.

    The walls answer "where is the biggest thing"; this answers "and what is behind
    it" — the ladder a trader actually needs for targets and stops between the walls.
    """
    exclude = exclude or set()
    rows = [(float(k), float(v)) for k, v in per_strike.items()
            if float(k) not in exclude and v]
    rows.sort(key=lambda kv: abs(kv[1]), reverse=True)
    out = []
    for rank, (k, v) in enumerate(rows[:n], start=1):
        out.append({
            "rank": rank,
            "strike": k,
            "gex": v,
            "side": "above" if k > spot else ("below" if k < spot else "at"),
            "distance": round(k - spot, 1),
            "sign": "positive" if v > 0 else "negative",
        })
    return out


def load_history(docs: list[dict], field: str = "total_gex") -> list[float]:
    """Pull one numeric field out of prior GEX documents, newest last."""
    return [d.get(field) for d in docs if isinstance(d.get(field), (int, float))]
