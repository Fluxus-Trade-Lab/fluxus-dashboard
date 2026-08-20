"""Name cards -- the standardized per-ticker dossier, one engine, three outlets.

2026-08-20 (Andy: "把它做成标准化的产品…每天你生成 6 个名字卡片…不合适的我会
打岔，你可以自我学习我的选择"). Design: docs/plans/2026-08-20-shortlist-design.md.

One card = everything the eight-name comparison artifact showed, as data:
readings from the nightly universe row, 130 sessions of price series with
signal marks (same definitions as the pipeline), the archived panel hits and
screener/preset events, and a DETERMINISTIC verdict sentence (same input,
same sentence -- it is a template over the five-step read, not prose).

Outlets: nightly `shortlist.json` (manual list + six seats), the chat
artifact (pipeline/tools/name_cards_html.py, later), and the feedback loop
(GAS Shortlist tab, frontend half pending).

Pure compute; the one yf.download lives in fetch_bars()."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import pandas as pd

logger = logging.getLogger(__name__)

OUT = Path("data/output/shortlist.json")
LOG = Path("data/history/shortlist_log.csv")
MANUAL = Path("data/reference/shortlist_manual.json")

SEATS = [
    ("burning", "今天谁在堆叠信号"),
    ("new_leader", "谁刚成为 TML"),
    ("entry", "今天最好的入场刀"),
    ("v_reversal", "谁在深回撤后翻身"),
    ("coiling", "谁压得最紧"),
    ("asset", "资产层里谁在领跑"),
]


# ── signal marks from bars (identical rules to the validation reports) ──

def marks_from_bars(hist: pd.DataFrame, spy_close: Optional[pd.Series],
                    n_days: int = 130) -> List[Dict[str, Any]]:
    c, v, o = hist["Close"], hist["Volume"], hist["Open"]
    av = v.rolling(50).mean()
    ema21 = c.ewm(span=21, adjust=False).mean()
    sma50 = c.rolling(50).mean()
    rs = (c / spy_close).dropna() if spy_close is not None else None
    out = []
    for i in range(max(21, len(c) - n_days), len(c)):
        chg = float(c.iloc[i] / c.iloc[i - 1] - 1)
        rv = float(v.iloc[i] / av.iloc[i]) if av.iloc[i] and av.iloc[i] > 0 else None
        kinds = []
        if chg >= 0.10 and rv and rv >= 3:
            kinds.append("EP")
        elif chg >= 0.04 and rv and rv >= 1:
            kinds.append("4%")
        hi20 = bool(c.iloc[i] >= c.iloc[max(0, i - 19):i + 1].max())
        if hi20 and rs is not None:
            win = rs[rs.index <= c.index[i]].iloc[-21:]
            if len(win) == 21 and float((win <= win.iloc[-1]).mean()) >= 1.0:
                kinds.append("NH+RS")
        if float(c.iloc[i - 1]) < float(ema21.iloc[i - 1]) and float(c.iloc[i]) >= float(ema21.iloc[i]):
            kinds.append("x21")
        if not pd.isna(sma50.iloc[i - 1]) and float(c.iloc[i - 1]) < float(sma50.iloc[i - 1]) \
                and float(c.iloc[i]) >= float(sma50.iloc[i]):
            kinds.append("x50")
        if kinds:
            out.append({"d": str(c.index[i].date()), "kinds": kinds,
                        "chg": round(chg * 100, 1), "rv": round(rv, 1) if rv else None})
    return out


def series_from_bars(hist: pd.DataFrame, n_days: int = 130) -> Dict[str, list]:
    c = hist["Close"].iloc[-n_days:]
    ema21 = hist["Close"].ewm(span=21, adjust=False).mean().iloc[-n_days:]
    sma50 = hist["Close"].rolling(50).mean().iloc[-n_days:]
    v = hist["Volume"].iloc[-n_days:]
    return {"d": [str(x.date()) for x in c.index],
            "c": [round(float(x), 2) for x in c],
            "e21": [round(float(x), 2) for x in ema21],
            "s50": [None if pd.isna(x) else round(float(x), 2) for x in sma50],
            "v": [int(x) for x in v]}


# ── verdict: a template over the five-step read, never prose ─────────────

def verdict(r: Mapping[str, Any], state: Optional[str], tml: bool,
            entry_panels: Sequence[str], roster_streak: int) -> str:
    parts = []
    parts.append({"Leading": "水域✓", "Improving": "水域～(Improving)"}.get(state or "", "水域✗" if state else "无主题"))
    parts.append("TML✓" if tml else ("资格✓(liquid leader)" if r.get("liquid_leader") else "资格✗"))
    a = r.get("atr_from_sma50")
    if a is None:
        parts.append("位置未测")
    elif a < 0:
        parts.append(f"50线下({a:.1f} ATR)")
    elif a <= 4:
        parts.append(f"建仓区({a:.1f} ATR)")
    elif a < 7:
        parts.append(f"持有区({a:.1f} ATR)")
    else:
        parts.append(f"减仓区({a:.1f} ATR)")
    if entry_panels:
        parts.append("今日刀: " + "+".join(entry_panels))
    chg = r.get("change_pct")
    if chg is not None and chg >= 0.15:
        parts.append("⚠当日≥15%不追")
    if roster_streak >= 5:
        parts.append(f"⚠Sugar Babies 名册 {roster_streak} 连(反指)")
    if "bar_date" in r and r.get("bar_date") is None:
        parts.append("⚠当晚无K线(429)")
    return " · ".join(parts)


def build_card(ticker: str, *, row: Optional[Mapping[str, Any]], group: Optional[str],
               state: Optional[str], hist: Optional[pd.DataFrame],
               spy_close: Optional[pd.Series], events: pd.DataFrame,
               panels: pd.DataFrame, heat: Optional[Mapping[str, Any]],
               heat_rank: Optional[int], asset_row: Optional[Mapping[str, Any]] = None,
               source: str = "manual", seat: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if row is None and asset_row is None:
        return None
    r = dict(asset_row or {}) if row is None else dict(row)
    ev = events[events["ticker"] == ticker].copy() if len(events) else events
    ev_list = []
    if len(ev):
        for d, g in ev[ev["date"] >= str(pd.Timestamp.now().year - 1)].groupby("date"):
            ev_list.append({"date": d, "screeners": sorted(set(
                s.replace("preset:", "P:") for s in g["screener"]))})
        ev_list = ev_list[-40:]
    roster = sum(1 for e in ev_list[-10:] if any(s == "P:sugar_babies" for s in e["screeners"]))
    pan = panels[panels["ticker"] == ticker] if len(panels) else panels
    pan_list = [{"date": p["date"], "panel": p["panel"], "chg_pct": p.get("chg_pct"),
                 "atr": p.get("atr_from_sma50")} for _, p in pan.iterrows()][-20:] if len(pan) else []
    today = max((p["date"] for p in pan_list), default=None)
    entry_today = [p["panel"] for p in pan_list if p["date"] == today
                   and p["panel"] in ("ma_reclaim", "episodic_pivot", "ll_hl_1st", "ll_hl_2nd",
                                      "ll_hl_trend_break", "liquid_leader_pullback")]
    tml = any(p["panel"] == "true_market_leaders" and p["date"] == today for p in pan_list)
    card: Dict[str, Any] = {
        "ticker": ticker, "source": source, "seat": seat,
        "group": group, "state": state,
        "is_asset": row is None,
        "readings": {k: r.get(k) for k in (
            "close", "change_pct", "rel_volume", "rs_1m", "rs_3m", "h_score",
            "rs_line_pctl_21", "rs_line_pctl_63", "atr_from_sma50", "ema21_atr_dist",
            "high_52w", "high_52w_dist", "vcs", "trend_base", "sector", "market_cap",
            "sp_signal", "perf_1m", "perf_3m", "label", "category", "hi20")},
        "heat": {"rank": heat_rank, "score": heat.get("score") if heat else None,
                 "confluence_days": heat.get("confluence_days") if heat else None},
        "verdict": verdict(r, state, tml, entry_today, roster),
        "events": ev_list[-15:],
        "panels": pan_list,
        "flags": {"chase": bool((r.get("change_pct") or 0) >= 0.15),
                  "roster_streak": roster, "tml": tml},
    }
    if hist is not None and len(hist) >= 25:
        card["series"] = series_from_bars(hist)
        card["marks"] = marks_from_bars(hist, spy_close)
    return card


# ── six seats, deterministic ─────────────────────────────────────────────

def pick_seats(wl: Mapping[str, Any], wl_prev: Optional[Mapping[str, Any]],
               heat: Sequence[Mapping[str, Any]], assets: Sequence[Mapping[str, Any]],
               by: Mapping[str, Mapping[str, Any]], states: Optional[Mapping[str, str]] = None,
               exclude: Sequence[str] = ()) -> List[Dict[str, str]]:
    """Six seats, deterministic. v2 rules (Andy 2026-08-20):
    - ATR gate everywhere: atr_from_sma50 < 7 or unmeasured -- "我不想交易任何
      已经 extended 的股票"; an extended EP loses the seat to the substitute.
    - Theme state matters: seats 1/2/3/5 prefer Leading, then Improving, then
      the rest (two-pass, never a hard cut -- a great setup in a quiet theme
      still shows, ranked behind). Seats 4 (V-reversal: the long-ignored
      bottoming archetype lives in weak themes by construction) and 6 (assets
      have no theme) are exempt.
    - No empty seats: every seat has a substitute chain; only a truly dry
      day leaves ticker=null, and the why says which chain came up empty."""
    states = states or {}
    taken = set(exclude)
    panels = {p["key"]: p for z in wl.get("zones", []) for p in z.get("panels", [])}
    prev_tml = set()
    if wl_prev:
        for z in wl_prev.get("zones", []):
            for p in z.get("panels", []):
                if p["key"] == "true_market_leaders":
                    prev_tml = {t["ticker"] for t in p.get("tickers", [])}

    def atr_ok(t):
        a = by.get(t, {}).get("atr_from_sma50")
        return a is None or a < 7

    def state_rank(t):
        return {"Leading": 0, "Improving": 1}.get(states.get(t), 2)

    def hscore(t):
        return by.get(t, {}).get("h_score") or -1

    def prefer(cands, key):
        """Two-pass theme preference, then `key` desc, then ticker asc."""
        pool = [t for t in cands if t not in taken and atr_ok(t)]
        return sorted(pool, key=lambda t: (state_rank(t), -key(t), t))

    def panel_tickers(k):
        return [t["ticker"] for t in panels.get(k, {}).get("tickers", [])]

    out = []

    def seat(name, chain):
        for why, cands, key in chain:
            got = prefer(cands, key)
            if got:
                taken.add(got[0])
                out.append({"seat": name, "ticker": got[0], "why": why})
                return
        out.append({"seat": name, "ticker": None,
                    "why": "空：" + " / ".join(w for w, _, _ in chain) + " 都无合格者(ATR<7)"})

    heat_names = [h["ticker"] for h in heat[:50]]
    heat_rank = {t: i for i, t in enumerate(heat_names)}
    seat("burning", [("heat 前 50 内最高(ATR<7,主题优先)", heat_names,
                      lambda t: 50 - heat_rank.get(t, 50))])

    tml_now = panel_tickers("true_market_leaders")
    fresh = [t for t in tml_now if t not in prev_tml]
    seat("new_leader", [
        ("今日新进 TML", fresh, hscore),
        ("替补:在册 TML 中 ATR 位最低(最贴基底)", tml_now,
         lambda t: -(by.get(t, {}).get("atr_from_sma50") if by.get(t, {}).get("atr_from_sma50") is not None else 99)),
    ])

    b4 = panels.get("bullish_4pct", {}).get("tickers", [])
    first_wave = [t["ticker"] for t in b4 if not t.get("chase") and t.get("rs_high")
                  and (t.get("atr_from_sma50") or 9) <= 4]
    seat("entry", [
        ("今日 EP", panel_tickers("episodic_pivot"),
         lambda t: by.get(t, {}).get("rel_volume") or 0),
        ("第一波(4%×ATR≤4×RS新高)", first_wave, hscore),
        ("替补:Leading 主题里的回踩", [t for t in panel_tickers("liquid_leader_pullback")
                                        if states.get(t) == "Leading"], hscore),
    ])

    reclaim = panel_tickers("ma_reclaim")
    pullback = panel_tickers("liquid_leader_pullback")
    rs3 = lambda t: by.get(t, {}).get("rs_3m") or 0  # noqa: E731

    def fresh_high_pullback(t):
        """Made a 52wh recently, now pulled back and turning (Andy 2026-08-20:
        "特别是出新52wh后回撤的"). Fresh = days_since_52wh <= 60 when the field
        exists (ships from tonight), else within 15% of the high as a proxy;
        pulled back = 3-20% under it; turning = it sits in a pullback/reclaim
        panel (that is how it got into `cands` at all)."""
        r = by.get(t, {})
        dist = r.get("high_52w")
        if dist is None or not (-0.20 <= dist <= -0.03):
            return False
        days = r.get("days_since_52wh")
        return (days <= 60) if days is not None else (dist >= -0.15)

    deep = [t for t in reclaim if (by.get(t, {}).get("high_52w") or 0) <= -0.25]
    seat("v_reversal", [
        ("新高后回踩(52wh 新鲜×回撤3-20%×在回踩/收复格)",
         [t for t in {*pullback, *reclaim} if fresh_high_pullback(t)], rs3),
        ("深 V:均线收复×离52周高≤−25%", deep, rs3),
        ("替补:均线收复中 rs_3m 最高", reclaim, rs3),
    ])

    # Coiling seat v3 (Andy 2026-08-20): the tightness study judged VCS
    # no-edge (无优势) while 3WT and the daily coil carry it, so they lead
    # the chain. VCS is NOT discarded -- it stays third AND keeps logging
    # nightly (vcs panel in watchlist_hits, vcs column in shortlist_log) so
    # the comparison continues; if it earns its way back, it comes back.
    from pipeline.screeners.watchlist import passes_gate

    def _tight(t, mode):
        r = by.get(t, {})
        if not passes_gate(r):        # full-universe scan must honor the $1B/$20M gate
            return False
        above50 = (r.get("sma50_dist") or 0) > 0
        if mode == "3wt":
            return r.get("wk_tight_3") is True and above50 and (r.get("high_52w") or -1) >= -0.15
        rng, hi20 = r.get("range5_pct"), r.get("dist_hi20_pct")
        return (rng is not None and rng <= 5 and hi20 is not None and hi20 >= -3 and above50)

    universe_names = list(by)
    vcs_p = panel_tickers("vcs")
    vcsv = lambda t: by.get(t, {}).get("vcs") or 0  # noqa: E731
    rng_tight = lambda t: -(by.get(t, {}).get("range5_pct") or 99)  # noqa: E731 -- tighter first
    seat("coiling", [
        ("3周紧(周K三连1.5%带×>50SMA×近52wh)", [t for t in universe_names if _tight(t, "3wt")], rs3),
        ("日线coil(5日幅≤5%×近20日高×>50SMA)", [t for t in universe_names if _tight(t, "coil")], rng_tight),
        ("替补:VCS 格(已判无优势,留作对照)", vcs_p, vcsv),
        ("替补:anticipation 格", panel_tickers("anticipation"), vcsv),
    ])

    lead_assets = [a["ticker"] for a in assets if (a.get("rs_line_pctl_21") or 0) >= 100 and a.get("hi20")]
    all_assets = sorted(assets, key=lambda a: -(a.get("rs_line_pctl_21") or 0))
    a_by = {a["ticker"]: a for a in assets}
    if lead_assets or all_assets:
        pick = next((t for t in lead_assets if t not in taken), None)
        why = "RS线21日=100×20日新高"
        if pick is None:
            pick = next((a["ticker"] for a in all_assets
                         if a["ticker"] not in taken and (a.get("atr_from_sma50") or 0) < 7), None)
            why = "替补:资产层 RS 线自百分位最高(ATR<7)"
        if pick:
            taken.add(pick)
            out.append({"seat": "asset", "ticker": pick, "why": why})
        else:
            out.append({"seat": "asset", "ticker": None, "why": "空：资产层无合格者"})
    else:
        out.append({"seat": "asset", "ticker": None, "why": "空：asset_signals 缺失"})
    return out


def archive(payload: Mapping[str, Any], path: Path = LOG) -> int:
    """One row per (date, ticker) with seat + the readings the learning loop
    will join Andy's vetoes against. Idempotent per date."""
    import csv
    fields = ["date", "ticker", "source", "seat", "state", "verdict",
              "rs_1m", "rs_3m", "rs_line_pctl_21", "atr_from_sma50", "heat_rank",
              "chase", "roster_streak", "tml"]
    date = payload["date"]
    old = []
    if path.exists():
        with path.open(newline="") as fh:
            old = [r for r in csv.DictReader(fh) if r.get("date") != date]
    new = []
    for c in payload["cards"]:
        rd = c["readings"]
        new.append({"date": date, "ticker": c["ticker"], "source": c["source"], "seat": c.get("seat"),
                    "state": c.get("state"), "verdict": c["verdict"],
                    "rs_1m": rd.get("rs_1m"), "rs_3m": rd.get("rs_3m"),
                    "rs_line_pctl_21": rd.get("rs_line_pctl_21"),
                    "atr_from_sma50": rd.get("atr_from_sma50"),
                    "heat_rank": c["heat"]["rank"],
                    "chase": c["flags"]["chase"], "roster_streak": c["flags"]["roster_streak"],
                    "tml": c["flags"]["tml"]})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in [*old, *new]:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
    return len(new)


def manual_tickers(path: Path = MANUAL) -> List[str]:
    try:
        return [t.upper() for t in json.loads(path.read_text()).get("tickers", [])][:20]
    except Exception:  # noqa: BLE001
        return []


def fetch_bars(tickers: Sequence[str]) -> Dict[str, pd.DataFrame]:
    import time
    import yfinance as yf
    tickers = list(dict.fromkeys(["SPY", *tickers]))
    out: Dict[str, pd.DataFrame] = {}
    for attempt in range(3):
        missing = [t for t in tickers if t not in out]
        if not missing:
            break
        if attempt:
            time.sleep(20 * attempt)
        data = yf.download(missing, period="7mo", group_by="ticker",
                           auto_adjust=True, progress=False, threads=True)
        for t in missing:
            try:
                h = data[t].dropna(subset=["Close"]) if len(missing) > 1 else data.dropna(subset=["Close"])
            except KeyError:
                continue
            if len(h):
                out[t] = h
    return out
