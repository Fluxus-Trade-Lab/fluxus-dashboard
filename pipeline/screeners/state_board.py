"""State board + propagation chain — the decision-first objects the v2 UI renders.

Design source: `Fluxus_Brand/visual/Fluxus_Operator_Model.md`. The board is the
ten-dimension picture the operator actually carries in his head; the chain is the
question "can this repair propagate?" laid out as ordered links.

Two rules this module exists to enforce:

1. **Every level carries its evidence.** A row is `(key, layer, level, evidence)`
   — never a bare label. The UI is not allowed to state a condition without the
   numbers that produced it.
2. **Unmeasurable is not zero.** A dimension the pipeline cannot compute returns
   `level=None` and says so in `evidence`. The design draws that as an empty
   outline, outside the scale. Never guess a level to fill the grid.

Pure functions, no I/O and no clock — same discipline as `breadth_signals`, so
the Time Machine can replay these over a truncated frame unchanged.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import pandas as pd

# Five ordinal levels, worst → best. The board reads as a shape, so the count
# has to stay small and fixed.
LEVELS: List[str] = ["absent", "very weak", "early", "started", "good"]

# Layer drives the typographic register in the UI. Measurement and opinion must
# never look alike — that separation is what makes the interpretation safe.
FACT, INTERP, ANTICIP = "fact", "interpretation", "anticipation"


def _num(x) -> Optional[float]:
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _lvl(*rules) -> Optional[int]:
    """First rule whose condition is true wins; returns its level index."""
    for cond, level in rules:
        if cond:
            return level
    return 0


def _row(key: str, layer: str, level: Optional[int], evidence: str) -> Dict[str, Any]:
    return {
        "key": key,
        "layer": layer,
        "level": level,
        "level_label": None if level is None else LEVELS[level],
        "evidence": evidence,
    }


def state_board(frame: pd.DataFrame, health: Optional[Dict[str, Any]] = None
                ) -> List[Dict[str, Any]]:
    """Nine conditions from `frame` (ascending archive) plus `market_health`.

    `frame` must end on the session being scored; nothing after it is read, so a
    truncated frame replays exactly.
    """
    if frame is None or frame.empty:
        return []
    row = frame.iloc[-1]
    prev5 = frame.iloc[-6:-1]

    out: List[Dict[str, Any]] = []

    # 1 · Damage — how much of the market is still deeply broken
    qu, qd = _num(row.get("up_25pct_qtr")), _num(row.get("down_25pct_qtr"))
    if qu is None or qd is None or (qu + qd) == 0:
        out.append(_row("damage", FACT, None, "quarterly 25% counts unavailable"))
    else:
        share = qd / (qu + qd)
        out.append(_row(
            "damage", FACT,
            _lvl((share > 0.55, 1), (share > 0.45, 2), (share > 0.35, 3), (True, 4)),
            f"{qd:.0f} names −25% on the quarter against {qu:.0f} up 25% "
            f"— {share*100:.0f}% on the down side"))

    # 2 · Selling pressure — today against the recent peak, not against zero
    dn4 = _num(row.get("down_4pct"))
    peak = _num(prev5["down_4pct"].max()) if len(prev5) else None
    if dn4 is None or not peak:
        out.append(_row("selling pressure", FACT, None, "4% decliner counts unavailable"))
    else:
        frac = dn4 / peak
        out.append(_row(
            "selling pressure", FACT,
            _lvl((frac < 0.5, 3), (frac < 0.8, 2), (True, 1)),
            f"{dn4:.0f} names −4% today against a five-day peak of {peak:.0f}, "
            f"back to {frac*100:.0f}% of it"))

    # 3 · Breadth — the participation check the index cannot fake
    p20, net = _num(row.get("pct_above_20sma")), _num(row.get("net_advances"))
    if p20 is None:
        out.append(_row("breadth", FACT, None, "%>20-day unavailable"))
    else:
        t2108 = _num(row.get("t2108"))
        out.append(_row(
            "breadth", FACT,
            _lvl((p20 > 60 and (net or 0) > 0, 4), (p20 > 50, 3), (p20 > 35, 1), (True, 0)),
            f"{p20:.1f}% above the 20-day"
            + (f", T2108 {t2108:.1f}" if t2108 is not None else "")
            + (f", net advances {net:+.0f}" if net is not None else "")))

    # 4 · Trend
    p200 = _num(row.get("pct_above_200sma"))
    out.append(_row("trend", FACT, None, "%>200-day unavailable") if p200 is None else _row(
        "trend", FACT,
        _lvl((p200 > 50, 4), (p200 > 40, 3), (p200 > 30, 2), (True, 1)),
        f"{p200:.1f}% above the 200-day"))

    # 5 · Thrust
    up4 = _num(row.get("up_4pct"))
    if up4 is None or dn4 is None:
        out.append(_row("thrust", FACT, None, "4% counts unavailable"))
    else:
        out.append(_row(
            "thrust", FACT,
            _lvl((up4 >= 300 and up4 > dn4, 4), (dn4 >= 300 and dn4 > up4, 0), (True, 2)),
            f"{up4:.0f} names +4% against {dn4:.0f} −4%"))

    # 6 · Extremes
    nh, nl = _num(row.get("new_highs")), _num(row.get("new_lows"))
    if nh is None or nl is None:
        out.append(_row("extremes", FACT, None, "new high/low counts unavailable"))
    else:
        out.append(_row(
            "extremes", FACT,
            _lvl((nh > nl * 2, 4), (nh > nl, 3), (nl > nh * 2, 0), (True, 2)),
            f"{nh:.0f} new 52-week highs against {nl:.0f} new lows"))

    # 7 · Index repair — from the benchmark candles, not from breadth
    out.append(_index_repair(health))

    # 8 · Confirmation — the thing that is either present or absent, no middle
    r5 = _num(row.get("ratio_5d"))
    if r5 is None:
        out.append(_row("confirmation", ANTICIP, None, "5-day ratio unavailable"))
    else:
        # The evidence has to describe the reading it actually got. A fixed
        # "needs to clear 1.0" printed under a 1.75 reading is a caption that
        # contradicts its own number.
        if r5 > 1.2 and (net or 0) > 0:
            why = f"five-day ratio {r5:.4f}, clear of 1.2 with net advances positive"
        elif r5 > 1.0:
            why = (f"five-day ratio {r5:.4f}, above 1.0 but "
                   + ("net advances still negative" if (net or 0) < 0 else "not yet clear of 1.2"))
        else:
            why = f"five-day ratio {r5:.4f}, needs to clear 1.0"
        out.append(_row(
            "confirmation", ANTICIP,
            _lvl((r5 > 1.2 and (net or 0) > 0, 4), (r5 > 1.0, 2), (True, 0)),
            why))

    # 9 · Rates — deliberately blank. The pipeline has no bond data, and an
    # invented level here would be exactly the dishonesty the design forbids.
    out.append(_row("rates", FACT, None,
                    "long-end yields are not wired into the pipeline — filled by hand"))
    return out


def _index_repair(health: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """How many benchmarks are back above their own 50-day."""
    if not health:
        return _row("index repair", INTERP, None, "market health data unavailable")
    ok, seen = [], []
    for sym in ("spy", "qqq"):
        candles = (health.get(sym) or {}).get("candles") or []
        closes = [c.get("c") for c in candles if c.get("c") is not None]
        if len(closes) < 50:
            continue
        sma50 = sum(closes[-50:]) / 50
        seen.append(sym.upper())
        if closes[-1] > sma50:
            ok.append(sym.upper())
    if not seen:
        return _row("index repair", INTERP, None, "fewer than 50 sessions of benchmark data")
    return _row(
        "index repair", INTERP,
        _lvl((len(ok) == len(seen), 4), (len(ok) > 0, 3), (True, 1)),
        f"{len(ok)} of {len(seen)} benchmarks above the 50-day"
        + (f": {', '.join(ok)}" if ok else ""))


# ── propagation chain ────────────────────────────────────────────────

def propagation_chain(board: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ordered links, each lit / partial / unlit, plus how much is carrying.

    `carrying` is drawn as a width (Minard), and the width is a **running
    minimum** downstream — a current that has stopped cannot resume, so the UI
    must never let the band swell again after a dead link.
    """
    by_key = {r["key"]: r for r in board}

    def frac(key: str) -> Optional[float]:
        r = by_key.get(key)
        if not r or r["level"] is None:
            return None
        return r["level"] / (len(LEVELS) - 1)

    spec = [
        ("index repair", "Indexes repair"),
        ("thrust", "Buyers show up"),
        ("breadth", "Breadth expands"),
        ("extremes", "New highs take over"),
        ("confirmation", "Confirmation arrives"),
    ]
    links, running = [], None
    for key, label in spec:
        f = frac(key)
        measured = f
        if f is None:
            state, carrying = "unmeasured", None
        else:
            running = f if running is None else min(running, f)
            carrying = running
            state = "lit" if running >= 0.75 else "partial" if running > 0.05 else "unlit"
        links.append({
            "key": key, "label": label, "state": state,
            "carrying": carrying, "measured": measured,
            "fed": None if (measured is None or carrying is None)
                  else bool(measured <= carrying + 1e-9),
            "evidence": (by_key.get(key) or {}).get("evidence", ""),
        })
    return links


def build(frame: pd.DataFrame, health: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The block that goes into `breadth.json` as `state_board`."""
    board = state_board(frame, health)
    return {
        "levels": LEVELS,
        "rows": board,
        "chain": propagation_chain(board),
        "measured": sum(1 for r in board if r["level"] is not None),
        "total": len(board),
    }
