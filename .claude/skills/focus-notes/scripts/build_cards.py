#!/usr/bin/env python3
"""Fact cards for the Screener funnel's Focus candidates -- the only numbers a
one-sentence note may use.

Reads data/output only (never writes there). One card per candidate of each
live setup, with the funnel verdict baked in:

  ① universe gate  = Today's List gate (Andy 2026-09-26 「紧的当默认」):
                     market cap >= $1B, avg $ volume >= $20M, ADR >= 3.5%
  ③ §11.1 gate     = the four measurable conditions: above 50-day, 10 EMA > 20 EMA,
                     within 25% of the 52-week high, >= 30% above the 52-week low.
                     The two "rising" halves need slopes the pipeline does not
                     publish yet (T-0926-62) -- NOT checked, and a card says so.
  Focus            = ① and ③ 4/4.

Group for the sentence: the ticker's theme (kind=theme) with the highest 3-month
excess; no theme -> its industry. `prev` is the group's ribbon, oldest first,
current last.

usage: build_cards.py --data data/output --out cards.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

GATE = {"cap": 1e9, "dollar_vol": 20e6, "adr": 3.5}
SETUPS = {
    "pullback": ("龙头回踩 21EMA", "Leader pullback to 21EMA", "ema21_watch.json"),
    "ep": ("EP 事件驱动跳空", "Episodic pivot", ("ep_qullamaggie.json", "ep_stockbee.json")),
    "vcp": ("VCP", "VCP", "vcp.json"),
}


def _load(d: Path, name: str):
    return json.loads((d / name).read_text())


def _dollar_vol(r):
    v = r.get("sb_avg_dollar_vol_20")
    return v if v is not None else (r.get("avg_volume") or 0) * (r.get("close") or 0)


def passes_gate(r) -> bool:
    return ((r.get("market_cap") or 0) >= GATE["cap"] and _dollar_vol(r) >= GATE["dollar_vol"]
            and (r.get("adr_pct") or 0) >= GATE["adr"])


def s111(r) -> dict:
    hi = r.get("high_52w_dist")
    return {
        "above50": (r.get("sma50_dist") or -1) > 0,
        "e10_20": (r.get("ema10") or 0) > (r.get("ema20") or 0),
        "near_high": (hi if hi is not None else -1) >= -0.25,
        "off_low": ((r.get("c_low52w") or 1) - 1) >= 0.30,
    }


def _pct(x, d=1):
    return None if x is None else round(x * 100, d)


def group_card(g) -> dict:
    rb = [x for x in (g.get("ribbon") or []) if x]
    return {"name": g["group"], "state": g["state"], "prev": [x.get("state") for x in rb],
            "ex1m": _pct(g.get("excess_1m")), "ex3m": _pct(g.get("excess_3m")),
            "accel": _pct(g.get("rs_accel")), "perf_1w": _pct(g.get("perf_1w")),
            "members": g.get("members") or len(g.get("tickers") or [])}


def setup_members(d: Path) -> dict:
    out = {}
    e = _load(d, "ema21_watch.json")
    out["pullback"] = [x["ticker"] for g in e["rs_groups"].values() for x in g]
    ep = set()
    for f in SETUPS["ep"][2]:
        ep.update(x["ticker"] for x in _load(d, f)["tickers"])
    out["ep"] = sorted(ep)
    out["vcp"] = [x["ticker"] for x in _load(d, "vcp.json")["results"]]
    return out


def build(d: Path) -> dict:
    u = _load(d, "universe.json")
    rows = u["rows"]
    by = {r["ticker"]: r for r in rows}
    groups = _load(d, "groups.json")
    stocks = groups["stocks"]
    themes = {}
    for t in groups["themes"]:
        if t.get("kind") == "theme":
            for tk in t.get("tickers") or []:
                themes.setdefault(tk, []).append(t)
    inds = {i["group"]: i for i in groups["industries"]}
    healthy = {x["ticker"] for g in _load(d, "healthy_charts.json")["rs_groups"].values() for x in g}

    def earnings(tk):
        p = d / "tickers" / f"{tk}.json"
        if not p.exists():
            return None
        ne = json.loads(p.read_text()).get("next_earnings")
        if isinstance(ne, dict):
            return ne.get("date") or ne.get("earnings_date")
        return ne or None

    def card(tk):
        r, s = by[tk], stocks.get(tk, {})
        th = max(themes[tk], key=lambda t: t["excess_3m"]) if tk in themes else None
        ind = inds.get(s.get("primary_group")) or inds.get(r.get("industry"))
        q = s111(r)
        return {
            "t": tk, "rs": r.get("rs_rating"), "close": r.get("close"), "chg": _pct(r.get("change_pct")),
            "ema21_atr": r.get("ema21_atr_dist"),
            "sma50_atr": None if r.get("sma50_atr_dist") is None else round(r["sma50_atr_dist"], 2),
            "dcr": round((r.get("dcr_pct") or 0) * 100),
            "adr": round(r.get("adr_pct") or 0, 1), "cap_b": round((r.get("market_cap") or 0) / 1e9, 1),
            "eps": _pct(r.get("eps_growth_this_y"), 0), "rev": _pct(r.get("revenue_growth"), 0),
            "hi52": _pct(r.get("high_52w_dist")) or 0.0, "perf_1m": _pct(r.get("perf_1m")),
            "perf_3m": _pct(r.get("perf_3m")),
            "q": q, "qn": sum(q.values()), "tight": passes_gate(r), "healthy": tk in healthy,
            "focus": passes_gate(r) and sum(q.values()) == 4,
            "sector": r.get("sector"), "industry": r.get("industry"),
            "stock_state": s.get("state"), "grp_pctile": s.get("group_pctile"), "grp": s.get("group"),
            "theme": group_card(th) if th else None, "n_themes": len(themes.get(tk, [])),
            "ind": group_card(ind) if ind else None, "earn": earnings(tk),
        }

    members = setup_members(d)
    setups = {k: {"label": SETUPS[k][0], "label_en": SETUPS[k][1],
                  "rows": [card(t) for t in members[k] if t in by]} for k in SETUPS}

    ml, br = _load(d, "market_light.json"), _load(d, "breadth.json")
    v, reg = br["verdict"], br["regime"]
    vd = {x["key"]: x["value"] for x in v["vote_detail"]}
    ext = next(x for x in br["state_board"]["rows"] if x["key"] == "extremes")["evidence"]
    m = re.search(r"(\d+) new 52-week highs against (\d+) new lows", ext)
    leaders = ml["brightness"]["leaders"]
    market = {
        "spy_light": ml["spy"]["light"], "spy_checks": ml["spy"]["checks_passed"],
        "qqq_light": ml["qqq"]["light"], "qqq_checks": ml["qqq"]["checks_passed"],
        "light_verdict": ml["verdict"], "env": v["env"], "score": v["score"], "exposure": v["exposure"],
        "regime": reg["band_label"], "regime_score": reg["score"],
        "t2108": vd.get("t2108_zone"), "pct200": vd.get("pct200"),
        "nh": int(m[1]) if m else None, "nl": int(m[2]) if m else None,
        "leaders_hold": sum(1 for x in leaders if x["status"] == "holding"), "leaders_n": len(leaders),
    }
    for st in ("Leading", "Improving", "Weakening", "Lagging"):
        market["themes_" + st.lower()] = [t["group"] for t in groups["themes"]
                                          if t.get("kind") == "theme" and t["state"] == st]
    gated = [r for r in rows if passes_gate(r)]
    return {
        "asof": ml["date"], "universe_timestamp": u["timestamp"],
        "rule": {"gate": GATE, "s111_checked": ["above50", "e10_20", "near_high", "off_low"],
                 "s111_unchecked": ["50-day rising", "10/20 EMA rising (no slope field yet)"],
                 "focus": "gate and s111 4/4"},
        "counts": {"universe": len(rows), "gate": len(gated), "healthy": len(healthy),
                   "healthy_gate": len(healthy & {r["ticker"] for r in gated})},
        "setups": setups, "market": market,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/output")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cards = build(Path(a.data))
    Path(a.out).write_text(json.dumps(cards, ensure_ascii=False))
    n = {k: sum(r["focus"] for r in v["rows"]) for k, v in cards["setups"].items()}
    print(f"asof {cards['asof']} · focus {n}")


if __name__ == "__main__":
    main()
