"""Selection Lab -- the fresh-high-pullback practice deck.

Design: docs/plans/2026-08-20-selection-lab-design.md (approved 2026-08-20).
One setup only. Two modes: blind historical reps (deal a random archived
session, mask the future, reveal instantly after judging) and live dailies.

    python -m pipeline.tools.selection_lab --deal            # random past day
    python -m pipeline.tools.selection_lab --deal --asof 2026-05-12
    python -m pipeline.tools.selection_lab --reveal r001     # after judgments

The deal writes rounds/<id>.json (cards + hidden answers) and an HTML deck;
`record()` appends judged decisions to decisions.csv. The chat drives it:
Claude deals, publishes the deck artifact, pre-commits its own predictions,
Andy judges, Claude records + reveals.

Setup definition (bars-only, so any archived day replays):
  * 52wh (252d) set within the last 60 sessions
  * now 3-20% below it, close above the 50SMA
  * near the short base: within 1.5 ATR of the 21EMA (the pullback is live,
    not a crash)
  * liquidity: 20d avg dollar volume >= $20M (cap gate approximated -- bars
    carry no market cap; noted on every deck)
Bars: event_bars.pkl (names that fired signals in 2026; selection bias noted).
"""

from __future__ import annotations

import argparse
import json
import pickle
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

LAB = Path("data/research/selection_lab")
BARS = Path("data/research/scanner_validation_2026-08/event_bars.pkl")
DECISIONS = LAB / "decisions.csv"
DEC_FIELDS = ["round", "date_practiced", "mode", "asof", "setup", "ticker",
              "andy_verdict", "andy_reason", "tags", "claude_pred", "claude_reason",
              "close0", "dist_52wh_pct", "days_since_52wh", "atr_from_sma50",
              "ema21_atr_dist", "rs_line_pctl_21", "range5_pct",
              "fwd5", "fwd10", "fwd20", "mae20", "mfe20"]


def _atr(h: pd.DataFrame, i: int, period: int = 14) -> Optional[float]:
    sl = h.iloc[max(0, i - 40):i + 1]
    hl = sl["High"] - sl["Low"]
    hc = (sl["High"] - sl["Close"].shift()).abs()
    lc = (sl["Low"] - sl["Close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    v = tr.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    return float(v) if v == v else None


def candidates(bars: Dict[str, pd.DataFrame], asof: pd.Timestamp,
               spy_close: pd.Series) -> List[dict]:
    out = []
    for t, df in bars.items():
        if t == "SPY":
            continue
        h = df[df.index <= asof]
        n = len(h)
        if n < 130:
            continue
        c = h["Close"]
        px = float(c.iloc[-1])
        hi252 = c.iloc[-252:] if n >= 252 else c
        hi = float(hi252.max())
        days_hi = int(len(hi252) - 1 - int(np.argmax(hi252.values)))
        dist = px / hi - 1
        if not (-0.20 <= dist <= -0.03) or days_hi > 60:
            continue
        sma50 = float(c.rolling(50).mean().iloc[-1])
        if px <= sma50:
            continue
        atr = _atr(h, n - 1)
        ema21 = float(c.ewm(span=21, adjust=False).mean().iloc[-1])
        if not atr or abs(px - ema21) / atr > 1.5:
            continue
        dv = float((h["Volume"] * h["Close"]).rolling(20).mean().iloc[-1])
        if dv < 2e7:
            continue
        rs = (c / spy_close).dropna()
        win = rs.iloc[-21:]
        rsl = round(float((win <= win.iloc[-1]).mean() * 100)) if len(win) == 21 else None
        rng5 = float((h["High"].iloc[-5:].max() - h["Low"].iloc[-5:].min()) / px * 100)
        out.append({"ticker": t, "close0": round(px, 2),
                    "dist_52wh_pct": round(dist * 100, 1), "days_since_52wh": days_hi,
                    "atr_from_sma50": round((px - sma50) / atr, 2),
                    "ema21_atr_dist": round((px - ema21) / atr, 2),
                    "rs_line_pctl_21": rsl, "range5_pct": round(rng5, 1)})
    return sorted(out, key=lambda r: r["dist_52wh_pct"])


def answers(bars: Dict[str, pd.DataFrame], asof: pd.Timestamp, ticker: str) -> Optional[dict]:
    c = bars[ticker]["Close"]
    idx = c.index.get_indexer([asof], method="pad")[0]
    if idx < 0 or idx + 20 >= len(c):
        return None
    p0 = float(c.iloc[idx])
    seg = c.iloc[idx:idx + 21]
    return {"fwd5": round(float(c.iloc[idx + 5] / p0 - 1) * 100, 1),
            "fwd10": round(float(c.iloc[idx + 10] / p0 - 1) * 100, 1),
            "fwd20": round(float(c.iloc[idx + 20] / p0 - 1) * 100, 1),
            "mae20": round(float((seg / p0 - 1).min()) * 100, 1),
            "mfe20": round(float((seg / p0 - 1).max()) * 100, 1)}


def deal(asof_str: Optional[str] = None, n_cards: int = 10, seed: Optional[int] = None,
         bars_path: Path = BARS, lab: Path = LAB) -> dict:
    bars = pickle.load(open(bars_path, "rb"))
    spy = bars["SPY"]["Close"]
    dates = spy.index
    lo, hi = 130, len(dates) - 21          # need history behind, answers ahead
    rng = random.Random(seed)
    if asof_str:
        asof = pd.Timestamp(asof_str)
    else:
        asof = dates[rng.randrange(lo, hi)]
    cands = candidates(bars, asof, spy[spy.index <= asof])
    if len(cands) > n_cards:
        cands = rng.sample(cands, n_cards)
        cands.sort(key=lambda r: r["ticker"])
    ans = {c["ticker"]: answers(bars, asof, c["ticker"]) for c in cands}
    rounds = sorted((lab / "rounds").glob("r*.json"))
    rid = f"r{len(rounds) + 1:03d}"
    payload = {"round": rid, "mode": "blind", "asof": str(asof.date()),
               "setup": "fresh_high_pullback", "cards": cands, "answers": ans}
    (lab / "rounds").mkdir(parents=True, exist_ok=True)
    (lab / "rounds" / f"{rid}.json").write_text(json.dumps(payload, indent=1))
    return payload


def record(rid: str, judgments: Dict[str, dict], date_practiced: str,
           lab: Path = LAB) -> int:
    """judgments: ticker -> {andy_verdict, andy_reason, tags, claude_pred, claude_reason}"""
    import csv
    payload = json.loads((lab / "rounds" / f"{rid}.json").read_text())
    by = {c["ticker"]: c for c in payload["cards"]}
    rows = []
    for t, j in judgments.items():
        c = by.get(t)
        if not c:
            continue
        a = payload["answers"].get(t) or {}
        rows.append({"round": rid, "date_practiced": date_practiced, "mode": payload["mode"],
                     "asof": payload["asof"], "setup": payload["setup"], "ticker": t,
                     **{k: j.get(k) for k in ("andy_verdict", "andy_reason", "tags",
                                              "claude_pred", "claude_reason")},
                     **{k: c.get(k) for k in ("close0", "dist_52wh_pct", "days_since_52wh",
                                              "atr_from_sma50", "ema21_atr_dist",
                                              "rs_line_pctl_21", "range5_pct")},
                     **a})
    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    exists = DECISIONS.exists()
    with DECISIONS.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=DEC_FIELDS)
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in DEC_FIELDS})
    return len(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deal", action="store_true")
    ap.add_argument("--asof")
    ap.add_argument("--cards", type=int, default=10)
    ap.add_argument("--seed", type=int)
    args = ap.parse_args(argv)
    if args.deal:
        p = deal(args.asof, args.cards, args.seed)
        print(f"{p['round']} asof {p['asof']}: {len(p['cards'])} cards")
        for c in p["cards"]:
            print(" ", c["ticker"], c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
