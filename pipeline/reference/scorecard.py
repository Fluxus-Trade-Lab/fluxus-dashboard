"""Score published levels against what price actually did.

The rule that makes this worth publishing: a level is scored against the session
AFTER it was published. Scoring a level against the same session's own high/low
is hindsight dressed as a record.

Verdicts are deliberately blunt:
  * `held`     — price reached the level and did not close through it
  * `broke`    — price closed through it
  * `untested` — price never got there

`untested` is neither a win nor a loss and is counted separately; folding it into
a "hit rate" is the standard way these numbers get flattered.
"""
from __future__ import annotations


def score_level(level: float, side: str, high: float, low: float, close: float,
                touch_tol: float = 0.0) -> str:
    """Score one level. `side` is 'support' or 'resistance'."""
    if side == "support":
        if low > level + touch_tol:
            return "untested"
        return "broke" if close < level else "held"
    if high < level - touch_tol:
        return "untested"
    return "broke" if close > level else "held"


def score_session(entry: dict, bar: dict, touch_tol: float = 0.0) -> list[dict]:
    """Score one published entry against the NEXT session's OHLC bar."""
    out = []
    plan = (("call_wall", "resistance"), ("put_wall", "support"),
            ("zero_gamma_flip", "pivot"), ("charm_peak_strike", "magnet"))
    for field, kind in plan:
        lvl = entry.get(field)
        if not isinstance(lvl, (int, float)):
            continue
        # flip/magnet have no inherent side; score them against where spot sat.
        side = kind
        if kind in ("pivot", "magnet"):
            ref = entry.get("spot")
            if not isinstance(ref, (int, float)):
                continue
            side = "resistance" if lvl > ref else "support"
        out.append({
            "level_name": field,
            "kind": kind,
            "level": lvl,
            "verdict": score_level(lvl, side, bar["high"], bar["low"], bar["close"],
                                   touch_tol),
            "session": bar.get("date"),
            "published_at": entry.get("generated_at"),
        })
    return out


def compare_cohorts(results: list[dict], split, labels=("flagged", "unflagged")) -> dict:
    """Does a flag actually predict anything? Split the same results and compare.

    This is the only way a method change can be judged rather than assumed. If
    gamma-charm confluence adds information, confluence-flagged levels should
    hold more often than unflagged ones; if the two rates sit on top of each
    other, the flag is decoration and should be dropped.

    `edge` is the difference in held-rate. `verdict` is deliberately conservative:
    with few tested observations the honest answer is "inconclusive", and it says
    so rather than reporting a difference that a couple of flips would erase.
    """
    a = [r for r in results if split(r)]
    b = [r for r in results if not split(r)]
    sa, sb = summarise(a)["total"], summarise(b)["total"]
    edge = (sa["held_pct"] - sb["held_pct"]
            if sa["held_pct"] is not None and sb["held_pct"] is not None else None)
    tested = sa["tested"] + sb["tested"]
    if edge is None or sa["tested"] < MIN_TESTED or sb["tested"] < MIN_TESTED:
        verdict = "inconclusive — too few tested observations"
    elif abs(edge) < 10:
        verdict = "no measurable difference"
    else:
        verdict = f"{labels[0] if edge > 0 else labels[1]} held more often"
    return {labels[0]: sa, labels[1]: sb, "edge_pct": edge,
            "tested_total": tested, "verdict": verdict}


# Below this many tested observations per cohort, refuse to call a winner.
MIN_TESTED = 30


def summarise(results: list[dict]) -> dict:
    """Cumulative table. Tested-only rate is reported next to the raw counts."""
    by_name: dict[str, dict] = {}
    for r in results:
        b = by_name.setdefault(r["level_name"],
                               {"held": 0, "broke": 0, "untested": 0, "n": 0})
        b[r["verdict"]] += 1
        b["n"] += 1
    for b in by_name.values():
        tested = b["held"] + b["broke"]
        # None, not 0: "no tested observations" and "never held" are different claims.
        b["tested"] = tested
        b["held_pct"] = round(100 * b["held"] / tested, 1) if tested else None
    total = {"held": sum(b["held"] for b in by_name.values()),
             "broke": sum(b["broke"] for b in by_name.values()),
             "untested": sum(b["untested"] for b in by_name.values())}
    total["tested"] = total["held"] + total["broke"]
    total["held_pct"] = (round(100 * total["held"] / total["tested"], 1)
                         if total["tested"] else None)
    return {"by_level": by_name, "total": total}
