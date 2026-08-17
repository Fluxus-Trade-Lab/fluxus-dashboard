"""Nightly watchlist -- the morning briefing, computed once, rendered as-is.

The Screener page is the workbench: the whole universe, thirty filter keys,
recipes the user edits and saves. This is the other reading of the same
fields: **zones = the questions a trader asks after the close, panels = the
signals that answer them**, each panel a short list with RS 1M beside the
ticker, sorted by Hybrid RS. oratnek's "Today's Watchlist" is the model; the
change is that his nine panels are grouped into five questions, and "in N
watchlists" counts ZONES rather than panels -- his three momentum panels all
say "moving", so 3+ there mostly meant one thing three times.

Zones (order is the reading order):
    entries       -- can I enter today?      LL-HL 1st / 2nd / trend-line break
    compression   -- what is loading?         VCS; anticipation (strong x quiet x VCS)
    accumulation  -- who is being bought?     pocket pivot TODAY / 2+ in 10d
    moving        -- what is running?         Weekly Momentum 97 / 4% Bullish / Weekly 20%+
    trouble       -- what broke? (holders)    stop hit / LL break / >= 7 ATR extended

Gate: $1B market cap and 1M average volume for every panel (oratnek's premise);
the Screener keeps its own gates. Recipes are defined HERE, once; the three
panels that duplicate Screener presets are pinned equal to
frontend/public/data/screener-presets.json by test_watchlist.py so the two
pages cannot drift apart again.

Method reference: data/reference/screener_methods.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

MIN_CAP = 1e9
MIN_AVG_VOL = 1e6
MAX_PER_PANEL = 25


def _f(r: Mapping[str, Any], k: str) -> Optional[float]:
    v = r.get(k)
    if v is None or isinstance(v, bool):
        return None if v is None else float(v)
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def passes_gate(r: Mapping[str, Any]) -> bool:
    cap, vol = _f(r, "market_cap"), _f(r, "avg_volume")
    return cap is not None and vol is not None and cap >= MIN_CAP and vol >= MIN_AVG_VOL


@dataclass(frozen=True)
class Panel:
    key: str
    label: str
    recipe: str                       # human-readable, printed on the page
    needs: Sequence[str]              # fields that must exist for the panel to be 'measured'
    test: Callable[[Mapping[str, Any]], bool]


def _sig(r, *names):
    return r.get("sp_signal") in names


def _ge(r, k, x):
    v = _f(r, k)
    return v is not None and v >= x


def _le(r, k, x):
    v = _f(r, k)
    return v is not None and v <= x


def _strong(r) -> bool:
    return _ge(r, "ti65", 1.05) or _ge(r, "c_low52w", 1.8) or _ge(r, "mdt", 1.19)


def _quiet(r) -> bool:
    v = _f(r, "change_pct")
    return v is not None and abs(v) <= 0.01


PANELS: Dict[str, Panel] = {p.key: p for p in [
    # --- entries ---
    Panel("ll_hl_1st", "LL-HL Structure 1st Pivot",
          "sp_signal = 1st_break (close crossed the Fib-0.618 entry today)",
          ["sp_signal"], lambda r: _sig(r, "1st_break")),
    Panel("ll_hl_2nd", "LL-HL Structure 2nd Pivot",
          "sp_signal = 2nd_break (close crossed the structure high today)",
          ["sp_signal"], lambda r: _sig(r, "2nd_break")),
    Panel("ll_hl_trend_break", "LL-HL Structure Trend Line Break",
          "sp_signal = counter_break (close crossed the counter-trend line today)",
          ["sp_signal"], lambda r: _sig(r, "counter_break")),
    # --- compression ---
    Panel("vcs", "Volatility Contraction Score",
          "vcs >= 70 and adr_pct >= 3 (the ADR floor keeps deal-pinned names out; 70 = upper half of his 'developing' band, revisit once VCS v2 has run)",
          ["vcs", "adr_pct"], lambda r: _ge(r, "vcs", 70) and _ge(r, "adr_pct", 3)),
    Panel("anticipation", "Anticipation (strong x quiet x VCS)",
          "any of ti65>1.05 / c_low52w>=1.8 / mdt>1.19; |change_pct|<=1%; vcs>=60; adr_pct>=3",
          ["vcs", "change_pct", "adr_pct"],
          lambda r: _strong(r) and _quiet(r) and _ge(r, "vcs", 60) and _ge(r, "adr_pct", 3)),
    # --- accumulation ---
    Panel("pp_today", "PP (Vol > 10D)",
          "pocket_pivot today (green bar, volume above the prior 10 bars' max) -- oratnek's panel is TODAY's PP",
          ["pocket_pivot"], lambda r: r.get("pocket_pivot") is True),
    Panel("pp_2plus_10d", "PP 2+ times (10D)",
          "pp_count_10d >= 2", ["pp_count_10d"], lambda r: _ge(r, "pp_count_10d", 2)),
    # --- moving (same recipes as the Screener presets; pinned by test) ---
    Panel("weekly_momentum_97", "Weekly Momentum 97",
          "perf_1w_pctile >= 0.97 and perf_3m_pctile >= 0.85 and trend_base and adr_pct 3.5-10",
          ["perf_1w_pctile", "perf_3m_pctile"],
          lambda r: _ge(r, "perf_1w_pctile", 0.97) and _ge(r, "perf_3m_pctile", 0.85)
          and r.get("trend_base") is True and _ge(r, "adr_pct", 3.5) and _le(r, "adr_pct", 10)),
    Panel("bullish_4pct", "4% Bullish",
          "change_pct >= 4%, rel_volume >= 1, from_open_pct >= 0, rs_21d >= 60, adr_pct 3.5-10",
          ["change_pct", "rel_volume"],
          lambda r: _ge(r, "change_pct", 0.04) and _ge(r, "rel_volume", 1.0)
          and _ge(r, "from_open_pct", 0.0) and _ge(r, "rs_21d", 60)
          and _ge(r, "adr_pct", 3.5) and _le(r, "adr_pct", 10)),
    Panel("weekly_20_gainers", "Weekly 20%+ Gainers",
          "perf_1w >= 20% and adr_pct 3.5-10", ["perf_1w"],
          lambda r: _ge(r, "perf_1w", 0.20) and _le(r, "perf_1w", 5.0)
          and _ge(r, "adr_pct", 3.5) and _le(r, "adr_pct", 10)),
    # --- trouble ---
    Panel("stop_hit", "Stop Hit (structure)",
          "sp_signal = stop_hit (close under the current-phase stop today)",
          ["sp_signal"], lambda r: _sig(r, "stop_hit")),
    Panel("ll_break", "Lower Low Break",
          "sp_signal = ll_break (close under the structure's LL today)",
          ["sp_signal"], lambda r: _sig(r, "ll_break")),
    Panel("extended", "Extended (>= 7 ATR from SMA50)",
          "atr_from_sma50 >= 7 (Jacobs's scale-out zone)",
          ["atr_from_sma50"], lambda r: _ge(r, "atr_from_sma50", 7)),
]}

ZONES: List[Dict[str, Any]] = [
    {"key": "entries", "label": "Can I enter today?", "panels": ["ll_hl_1st", "ll_hl_2nd", "ll_hl_trend_break"]},
    {"key": "compression", "label": "What is loading?", "panels": ["vcs", "anticipation"]},
    {"key": "accumulation", "label": "Who is being bought?", "panels": ["pp_today", "pp_2plus_10d"]},
    {"key": "moving", "label": "What is running?", "panels": ["weekly_momentum_97", "bullish_4pct", "weekly_20_gainers"]},
    {"key": "trouble", "label": "What broke?", "panels": ["stop_hit", "ll_break", "extended"]},
]

# The three panels that duplicate Screener presets, by preset name.
PRESET_TWINS = {"weekly_momentum_97": "Weekly Momentum 97",
                "bullish_4pct": "4% Bullish",
                "weekly_20_gainers": "Weekly 20%+ Gainers"}


def _entry(r: Mapping[str, Any]) -> Dict[str, Any]:
    return {"ticker": r["ticker"],
            "rs_1m": _int_or_none(_f(r, "rs_1m")),
            "hybrid_rs": _round(_f(r, "h_score")),
            "sector": r.get("sector")}


def _int_or_none(v):
    return None if v is None else int(round(v))


def _round(v, nd=1):
    return None if v is None else round(v, nd)


def build(rows: Sequence[Mapping[str, Any]], *, date: str) -> Dict[str, Any]:
    """Zones -> panels -> tickers (RS 1M beside, sorted by Hybrid RS desc), plus
    the cross-ZONE count. Panels whose fields are absent from every row are
    emitted empty with measured=False."""
    gated = [r for r in rows if r.get("ticker") and passes_gate(r)]
    present = set()
    for r in rows[:200]:
        present.update(k for k, v in r.items() if v is not None)
    # a field counts as present if any row in the whole file has it non-null
    for r in rows:
        present.update(k for k, v in r.items() if v is not None)

    zone_hits: Dict[str, set] = {}
    zones_out = []
    for z in ZONES:
        panels_out = []
        for pk in z["panels"]:
            p = PANELS[pk]
            measured = all(n in present for n in p.needs)
            hits = [r for r in gated if measured and p.test(r)]
            hits.sort(key=lambda r: (-(_f(r, "h_score") or -1), -(_f(r, "rs_1m") or -1), r["ticker"]))
            for r in hits:
                zone_hits.setdefault(r["ticker"], set()).add(z["key"])
            panels_out.append({
                "key": pk, "label": p.label, "recipe": p.recipe, "measured": measured,
                "count": len(hits),
                "tickers": [_entry(r) for r in hits[:MAX_PER_PANEL]],
                "truncated": max(0, len(hits) - MAX_PER_PANEL),
                "preset": PRESET_TWINS.get(pk),
            })
        zones_out.append({"key": z["key"], "label": z["label"], "panels": panels_out})

    zone_order = [z["key"] for z in ZONES]
    by_ticker = {r["ticker"]: r for r in gated}
    cross = [{"ticker": t, "count": len(zs), "zones": [z for z in zone_order if z in zs],
              **{k: v for k, v in _entry(by_ticker[t]).items() if k != "ticker"}}
             for t, zs in zone_hits.items() if len(zs) >= 2]
    cross.sort(key=lambda c: (-c["count"], -(c["hybrid_rs"] or -1), c["ticker"]))

    return {
        "date": date,
        "gate": {"min_market_cap": MIN_CAP, "min_avg_volume": MIN_AVG_VOL},
        "sort": "hybrid_rs desc; the number beside each ticker is rs_1m",
        "cross_zone_rule": "count of ZONES a name appears in (not panels); >= 2 listed",
        "zones": zones_out,
        "cross_zone": cross,
        "universe_gated": len(gated),
    }
