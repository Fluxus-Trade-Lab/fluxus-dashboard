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
    leaders       -- who leads?              True Market Leaders (liquid leader x
                                             Leading home group x rs_1m>=80); Liquid Leaders
    entries       -- can I enter today?      LL-HL 1st / 2nd / trend-line break;
                                             Liquid Leader Pullback (course M2_L09)
    compression   -- what is loading?         VCS; anticipation (strong x quiet x VCS)
    accumulation  -- who is being bought?     Vol>10D today / 2+ in 10d (oratnek) ; Morales pocket pivot in 10d
    moving        -- what is running?         Weekly Momentum 97 / 4% Bullish / Weekly 20%+
    trouble       -- what broke? (holders)    stop hit / LL break / >= 7 ATR extended

Gate: $1B market cap and $20M average dollar volume for every panel (oratnek's
premise was 1M shares; dollar volume since 2026-08-18);
the Screener keeps its own gates. Recipes are defined HERE, once; the three
panels that duplicate Screener presets are pinned equal to
frontend/public/data/screener-presets.json by test_watchlist.py so the two
pages cannot drift apart again.

Method reference: data/reference/screener_methods.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

MIN_CAP = 1e9
LEADERS_LOG = Path("data/history/leaders_log.csv")
# 2026-08-18: DOLLAR volume, not shares (Andy: "改可以的"). The 1M-share gate
# was tight on high-priced names and loose on $2 ones: CBRL ($58 x 862k =
# $50M/day) failed it while a $2 name printing 1.1M shares ($2M/day) passed.
MIN_DOLLAR_VOL = 2e7
MAX_PER_PANEL = 25
# >= 2 zones listed 177 names on 08-14 (143 of them exactly two, mostly
# leaders x moving); three zones is where the list is short enough to read.
MIN_CROSS_ZONES = 3
# same-day move at/above which a 4% day is a chase, not an entry (2026-08-19)
CHASE_PCT = 0.15
PANEL_HITS_LOG = Path("data/history/watchlist_hits.csv")
TOP_3M_PCTILE = 0.85          # 'top_3m' flag: oratnek's pool, fitted on 08-11/13/14


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
    cap, vol, px = _f(r, "market_cap"), _f(r, "avg_volume"), _f(r, "close")
    if cap is None or vol is None or px is None:
        return False
    return cap >= MIN_CAP and vol * px >= MIN_DOLLAR_VOL


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
    # --- leaders (qualification, not entries) ---
    Panel("true_market_leaders", "True Market Leaders",
          "liquid_leader and home theme/industry state = Leading and rs_1m >= 80 -- the leader inside a leading water",
          ["liquid_leader", "_group_state"],
          lambda r: r.get("liquid_leader") is True and r.get("_group_state") == "Leading" and _ge(r, "rs_1m", 80)),
    Panel("liquid_leaders", "Liquid Leaders",
          "avg_volume >= 2M, above SMA50, rs_3m >= 80 (course M2_L09; Alex's list). Top 25 by Hybrid RS shown, count is the whole list",
          ["liquid_leader"], lambda r: r.get("liquid_leader") is True),
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
    Panel("ma_reclaim", "MA Reclaim (close crossed up the 21EMA / 50SMA)",
          "cross_ema21_up or cross_sma50_up (yesterday's close under the MA, today's at/above it) and rel_volume >= 1. "
          "2026-08-19 scanner validation: MU / SNDK / NBIS / RBRK's August starts came from 14-28% under the 50SMA, "
          "where every trend panel is by definition dark; the reclaim was the one footprint that lit before the "
          "20-day high. On leaders alone it is a coin flip (edge -2.9 vs +11 baseline) -- it is the deep-pullback "
          "V-reversal entry, not a trend entry; read it with the theme state and the ATR position, not by itself",
          ["cross_ema21_up", "cross_sma50_up", "rel_volume"],
          lambda r: (r.get("cross_ema21_up") is True or r.get("cross_sma50_up") is True)
          and _ge(r, "rel_volume", 1.0)),
    Panel("liquid_leader_pullback", "Liquid Leader Pullback",
          "liquid_leader; perf_1w < 12%; 0.5-1 ATR from the 21EMA; 0-3 ATR from the 50SMA (course M2_L09; the two clauses we cannot read -- 5d/20d range contraction, earnings 7+ days out -- are not applied)",
          ["liquid_leader", "ema21_atr_dist", "atr_from_sma50"],
          lambda r: r.get("liquid_leader") is True and _le(r, "perf_1w", 0.12)
          and _ge(r, "ema21_atr_dist", 0.5) and _le(r, "ema21_atr_dist", 1.0)
          and _ge(r, "atr_from_sma50", 0.0) and _le(r, "atr_from_sma50", 3.0)),
    # --- compression ---
    Panel("vcs", "Volatility Contraction Score",
          "vcs >= 60 and rs_3m >= 80 and above SMA50 and adr_pct >= 3 -- compression INSIDE a leader. "
          "VCS alone at >= 70 listed 33 gated names on 08-14, half of them weak (rs_1m < 30); oratnek's "
          "same-day panel had 2 (COTY 64 / CBRL 62, both rs_3m >= 88). Raising the VCS bar does not fix it "
          "(>= 90 still 8, all weak); the leadership gate does (15, his two inside). 60 = his 'developing' band edge",
          ["vcs", "rs_3m", "sma50_dist", "adr_pct"],
          lambda r: _ge(r, "vcs", 60) and _ge(r, "rs_3m", 80) and _f(r, "sma50_dist") is not None
          and _f(r, "sma50_dist") > 0 and _ge(r, "adr_pct", 3)),
    Panel("anticipation", "Anticipation (strong x quiet x VCS)",
          "any of ti65>1.05 / c_low52w>=1.8 / mdt>1.19; |change_pct|<=1%; vcs>=60; adr_pct>=3",
          ["vcs", "change_pct", "adr_pct"],
          lambda r: _strong(r) and _quiet(r) and _ge(r, "vcs", 60) and _ge(r, "adr_pct", 3)),
    # --- accumulation ---
    # All three carry the CONTEXT gate (trend_base: above SMA50 + weekly
    # WMA10 > WMA30). The 2026-08-17 event study (1,505 names x 293 sessions)
    # found the definition mattered less than the context: without it the
    # left tail of either pivot was 2.7pp DEEPER than a random day (high-
    # volume green bars include distribution days); with it 1-2pp shallower.
    Panel("pp_today", "PP (Vol > 10D)",
          "vol10_green today (green bar, volume above ALL prior 10 bars' max -- oratnek's definition) and trend_base",
          ["vol10_green", "trend_base"], lambda r: r.get("vol10_green") is True and r.get("trend_base") is True),
    Panel("pp_2plus_10d", "PP 2+ times (10D)",
          "vol10_green_count_10d >= 2 and trend_base", ["vol10_green_count_10d", "trend_base"],
          lambda r: _ge(r, "vol10_green_count_10d", 2) and r.get("trend_base") is True),
    Panel("morales_pp_10d", "Pocket Pivot (Morales, 3+ in 10D)",
          "pp_count_10d >= 3 (up day on volume above the prior 10 bars' DOWN-day max; buying vs selling, +0.71 with the A/D ratio) and trend_base. "
          ">= 1 listed 372 names on 08-14 -- a single Morales pivot is common; three in ten sessions is his 'cluster' (111 on 08-14)",
          ["pp_count_10d", "trend_base"], lambda r: _ge(r, "pp_count_10d", 3) and r.get("trend_base") is True),
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
          "perf_5d >= 20% and adr_pct 3.5-10 (five SESSIONS from bars = the weekly candle oratnek reads; "
          "the Screener preset still reads Finviz perf_1w, a calendar week that on 08-14 held four sessions)",
          ["perf_5d"],
          lambda r: _ge(r, "perf_5d", 0.20) and _le(r, "perf_5d", 5.0)
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
    {"key": "leaders", "label": "Who leads?", "panels": ["true_market_leaders", "liquid_leaders"]},
    {"key": "entries", "label": "Can I enter today?", "panels": ["ma_reclaim", "ll_hl_1st", "ll_hl_2nd", "ll_hl_trend_break", "liquid_leader_pullback"]},
    {"key": "compression", "label": "What is loading?", "panels": ["vcs", "anticipation"]},
    {"key": "accumulation", "label": "Who is being bought?", "panels": ["pp_today", "pp_2plus_10d", "morales_pp_10d"]},
    {"key": "moving", "label": "What is running?", "panels": ["weekly_momentum_97", "bullish_4pct", "weekly_20_gainers"]},
    {"key": "trouble", "label": "What broke?", "panels": ["stop_hit", "ll_break", "extended"]},
]

# The three panels that duplicate Screener presets, by preset name.
PRESET_TWINS = {"weekly_momentum_97": "Weekly Momentum 97",
                "bullish_4pct": "4% Bullish",
                "weekly_20_gainers": "Weekly 20%+ Gainers"}


def _entry(r: Mapping[str, Any]) -> Dict[str, Any]:
    e = {"ticker": r["ticker"],
         "rs_1m": _int_or_none(_f(r, "rs_1m")),
         # oratnek's "RS 1M" (self-percentile of the RS line, 21 sessions) --
         # the number HIS page prints beside a ticker; ours above is the
         # cross-sectional one. Both, so the page can show either.
         "rs_line_pctl_21": _int_or_none(_f(r, "rs_line_pctl_21")),
         # detection only (Andy 2026-08-18: "只做检测,不否定现有的参数"): the RS
         # line is at a one-month high. 26 of the 29 names on oratnek's 08-17
         # page had this; our LL-HL 1st panel had 58 names of which 2 did.
         # The page can offer it as a toggle; the recipes do not filter on it.
         "rs_high": (_f(r, "rs_line_pctl_21") is not None and _f(r, "rs_line_pctl_21") >= 100.0),
         # detection only (Andy 2026-08-18: "只探不筛"): in the top 15% of 3M
         # performance. Three days of oratnek's page fitted (data/research/
         # oratnek_diff): his universe is a 3M-leaders list -- this one flag
         # takes our lists from 5.9x his to 2.5x while keeping 108/112 of his
         # names. The page offers it as a pool toggle; recipes do not filter.
         "top_3m": (_f(r, "perf_3m_pctile") is not None and _f(r, "perf_3m_pctile") >= TOP_3M_PCTILE),
         # today's move, in % (one decimal), and the chase flag: a >= 15% day.
         # 4% Bullish x same-day >= 15% was the worst cell of the whole
         # validation (20d -9.3%, 36% win); the page folds these to the
         # bottom of the panel, greyed, instead of deleting them.
         "chg_pct": _round(_f(r, "change_pct") * 100.0) if _f(r, "change_pct") is not None else None,
         "chase": (_f(r, "change_pct") is not None and _f(r, "change_pct") >= CHASE_PCT),
         "atr_from_sma50": _round(_f(r, "atr_from_sma50")),
         "hybrid_rs": _round(_f(r, "h_score")),
         "sector": r.get("sector")}
    if r.get("_group") is not None:
        e["group"] = r.get("_group")
        e["group_state"] = r.get("_group_state")
    return e


def load_group_states(groups_payload: Mapping[str, Any]) -> Dict[str, Tuple[str, Optional[str]]]:
    """ticker -> (home group name, its four-state) from groups.json."""
    themes = {t["group"]: t for t in groups_payload.get("themes") or []}
    inds = {i["group"]: i for i in groups_payload.get("industries") or []}
    out = {}
    for t, s in (groups_payload.get("stocks") or {}).items():
        g = s.get("primary_group")
        gg = themes.get(g) or inds.get(g)
        out[t] = (g, gg.get("state") if gg else None)
    return out


def _with_groups(rows, group_states):
    if not group_states:
        return list(rows)
    out = []
    for r in rows:
        g = group_states.get(r.get("ticker"))
        if g:
            r = {**r, "_group": g[0], "_group_state": g[1]}
        out.append(r)
    return out


def archive_leaders(rows, *, date: str, group_states=None, path: Path = LEADERS_LOG) -> int:
    """One row per liquid leader per date (idempotent per date): the
    prospective record for judging Liquid Leader / TML forward returns --
    theme states have no history before 2026-08-07, so this is how the TML
    dimension gets validated at all."""
    import csv
    fields = ["date", "ticker", "liquid_leader", "tml", "rs_1m", "rs_3m", "h_score",
              "group", "group_state", "close", "atr_from_sma50", "ema21_atr_dist"]
    rows = [r for r in _with_groups(rows, group_states) if r.get("liquid_leader") is True and passes_gate(r)]
    old = []
    if path.exists():
        with path.open(newline="") as fh:
            old = [r for r in csv.DictReader(fh) if r.get("date") != date]
    new = []
    for r in rows:
        new.append({"date": date, "ticker": r["ticker"], "liquid_leader": True,
                    "tml": bool(r.get("_group_state") == "Leading" and _ge(r, "rs_1m", 80)),
                    "rs_1m": _int_or_none(_f(r, "rs_1m")), "rs_3m": _int_or_none(_f(r, "rs_3m")),
                    "h_score": _round(_f(r, "h_score")), "group": r.get("_group"),
                    "group_state": r.get("_group_state"), "close": _f(r, "close"),
                    "atr_from_sma50": _f(r, "atr_from_sma50"), "ema21_atr_dist": _f(r, "ema21_atr_dist")})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in [*old, *new]:
            w.writerow({k: r.get(k, "") for k in fields})
    return len(new)


def archive_panel_hits(payload: Mapping[str, Any], rows, *, path: Path = PANEL_HITS_LOG) -> int:
    """One row per (date, panel, ticker) for EVERY hit -- not the 25 the page
    shows -- idempotent per date. Nightly since 2026-08-19: the panels had no
    history either, so the validation had to rebuild eleven as-of days by
    hand (data/research/scanner_validation_2026-08/asof_all_panels). Rows
    carry the readings the playbook keys on, so a forward study needs no
    rebuild."""
    import csv
    fields = ["date", "panel", "zone", "ticker", "close", "chg_pct", "rel_volume",
              "atr_from_sma50", "ema21_atr_dist", "rs_line_pctl_21", "rs_1m", "rs_3m",
              "h_score", "perf_3m_pctile", "vcs", "sp_signal", "group", "group_state"]
    date = payload["date"]
    by_t = {r.get("ticker"): r for r in rows if r.get("ticker")}
    old = []
    if path.exists():
        with path.open(newline="") as fh:
            old = [r for r in csv.DictReader(fh) if r.get("date") != date]
    new = []
    for z in payload.get("zones", []):
        for p in z.get("panels", []):
            if not p.get("measured"):
                continue
            # tickers[] is truncated at MAX_PER_PANEL; re-test the recipe on
            # the gated rows to log the whole list.
            hits = [r for r in by_t.values() if passes_gate(r) and PANELS[p["key"]].test(r)]
            for r in hits:
                new.append({"date": date, "panel": p["key"], "zone": z["key"], "ticker": r["ticker"],
                            "close": _f(r, "close"),
                            "chg_pct": _round(_f(r, "change_pct") * 100.0) if _f(r, "change_pct") is not None else None,
                            "rel_volume": _round(_f(r, "rel_volume"), 2),
                            "atr_from_sma50": _round(_f(r, "atr_from_sma50"), 2),
                            "ema21_atr_dist": _round(_f(r, "ema21_atr_dist"), 2),
                            "rs_line_pctl_21": _int_or_none(_f(r, "rs_line_pctl_21")),
                            "rs_1m": _int_or_none(_f(r, "rs_1m")), "rs_3m": _int_or_none(_f(r, "rs_3m")),
                            "h_score": _round(_f(r, "h_score")),
                            "perf_3m_pctile": _round(_f(r, "perf_3m_pctile"), 3),
                            "vcs": _int_or_none(_f(r, "vcs")), "sp_signal": r.get("sp_signal"),
                            "group": r.get("_group"), "group_state": r.get("_group_state")})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in [*old, *new]:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
    return len(new)


def _int_or_none(v):
    return None if v is None else int(round(v))


def _round(v, nd=1):
    return None if v is None else round(v, nd)


def build(rows: Sequence[Mapping[str, Any]], *, date: str,
          group_states: Optional[Mapping[str, Tuple[str, Optional[str]]]] = None) -> Dict[str, Any]:
    """Zones -> panels -> tickers (RS 1M beside, sorted by Hybrid RS desc), plus
    the cross-ZONE count. Panels whose fields are absent from every row are
    emitted empty with measured=False. `group_states` (from groups.json via
    load_group_states) supplies the home group and its four-state; without it
    the True Market Leaders panel is unmeasured."""
    rows = _with_groups(rows, group_states)
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
                "count_rs_high": sum(1 for r in hits if (_f(r, "rs_line_pctl_21") or 0) >= 100.0),
                "count_top_3m": sum(1 for r in hits if (_f(r, "perf_3m_pctile") or 0) >= TOP_3M_PCTILE),
                "count_chase": sum(1 for r in hits if (_f(r, "change_pct") or 0) >= CHASE_PCT),
                "tickers": [_entry(r) for r in hits[:MAX_PER_PANEL]],
                "truncated": max(0, len(hits) - MAX_PER_PANEL),
                "preset": PRESET_TWINS.get(pk),
            })
        zones_out.append({"key": z["key"], "label": z["label"], "panels": panels_out})

    zone_order = [z["key"] for z in ZONES]
    by_ticker = {r["ticker"]: r for r in gated}
    cross = [{"ticker": t, "count": len(zs), "zones": [z for z in zone_order if z in zs],
              **{k: v for k, v in _entry(by_ticker[t]).items() if k != "ticker"}}
             for t, zs in zone_hits.items() if len(zs) >= MIN_CROSS_ZONES]
    cross.sort(key=lambda c: (-c["count"], -(c["hybrid_rs"] or -1), c["ticker"]))

    return {
        "date": date,
        "gate": {"min_market_cap": MIN_CAP, "min_dollar_volume": MIN_DOLLAR_VOL},
        "sort": "hybrid_rs desc; the number beside each ticker is rs_line_pctl_21 (oratnek's RS 1M: RS-line self-percentile, 21 sessions); rs_1m (cross-sectional) is the second reading",
        "cross_zone_rule": f"count of ZONES a name appears in (not panels); >= {MIN_CROSS_ZONES} listed",
        "rs_high_rule": "rs_high = RS line (close/SPY) at a 21-session high (rs_line_pctl_21 == 100); detection only, no panel filters on it; count_rs_high per panel",
        "top_3m_rule": f"top_3m = perf_3m_pctile >= {TOP_3M_PCTILE} (top 15% of 3M performance, whole universe); oratnek's pool as fitted on three sessions; detection only, count_top_3m per panel",
        "chase_rule": f"chase = change_pct >= {CHASE_PCT:.0%} today; count_chase per panel. 4% Bullish x same-day >= 15% was 20d -9.3% / 36% win in the 2026-08 validation -- fold these to the panel bottom, greyed",
        "zones": zones_out,
        "cross_zone": cross,
        "universe_gated": len(gated),
    }
