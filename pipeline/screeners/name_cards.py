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
               by: Mapping[str, Mapping[str, Any]], exclude: Sequence[str] = ()) -> List[Dict[str, str]]:
    """One ticker per seat; a seat with no qualifier stays empty (that is a
    reading too). `exclude` = manual list + names that would double-count."""
    taken = set(exclude)
    panels = {p["key"]: p for z in wl.get("zones", []) for p in z.get("panels", [])}
    prev_tml = set()
    if wl_prev:
        for z in wl_prev.get("zones", []):
            for p in z.get("panels", []):
                if p["key"] == "true_market_leaders":
                    prev_tml = {t["ticker"] for t in p.get("tickers", [])}

    def hscore(t):
        return (by.get(t, {}).get("h_score") or -1, t)

    out = []

    def seat(name, ticker, why):
        if ticker and ticker not in taken:
            taken.add(ticker)
            out.append({"seat": name, "ticker": ticker, "why": why})
        else:
            out.append({"seat": name, "ticker": None, "why": why if not ticker else "候选与他席重复"})

    hot = next((h for h in heat if h["ticker"] not in taken), None)
    seat("burning", hot["ticker"] if hot else None,
         f"heat 第 1 名({hot['score']}分)" if hot else "heat 榜空")

    tml_now = [t["ticker"] for t in panels.get("true_market_leaders", {}).get("tickers", [])]
    fresh = sorted((t for t in tml_now if t not in prev_tml and t not in taken), key=hscore, reverse=True)
    seat("new_leader", fresh[0] if fresh else None,
         "今日新进 TML" if fresh else "今日无新进 TML")

    ep = [t["ticker"] for t in panels.get("episodic_pivot", {}).get("tickers", []) if t["ticker"] not in taken]
    if ep:
        seat("entry", ep[0], "今日 EP(格内量比最高)")
    else:
        fw = [t["ticker"] for t in panels.get("bullish_4pct", {}).get("tickers", [])
              if t["ticker"] not in taken and not t.get("chase")
              and t.get("rs_high") and (t.get("atr_from_sma50") or 9) <= 4]
        seat("entry", fw[0] if fw else None, "第一波(4%×ATR≤4×RS新高)" if fw else "今日无 EP/第一波")

    vr = [t["ticker"] for t in panels.get("ma_reclaim", {}).get("tickers", [])
          if t["ticker"] not in taken and (by.get(t["ticker"], {}).get("high_52w") or 0) <= -0.25]
    vr = sorted(vr, key=lambda t: -(by.get(t, {}).get("rs_3m") or 0))
    seat("v_reversal", vr[0] if vr else None,
         "均线收复×离52周高≤−25%×rs_3m最高" if vr else "今日无深回撤收复")

    co = [t["ticker"] for t in panels.get("vcs", {}).get("tickers", []) if t["ticker"] not in taken]
    co = sorted(co, key=lambda t: -(by.get(t, {}).get("vcs") or 0))
    seat("coiling", co[0] if co else None, "VCS 格内分最高" if co else "VCS 格空")

    aa = [a for a in assets if (a.get("rs_line_pctl_21") or 0) >= 100 and a.get("hi20")]
    seat("asset", aa[0]["ticker"] if aa else None,
         "RS线21日=100×20日新高" if aa else "资产层无领跑")
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
