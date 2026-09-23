#!/usr/bin/env python3
"""Assemble the material pack for one session or one ISO week → pack.json (local only, never git).

Usage:
    python3 -m pipeline.content.recap.build_pack --date 2026-09-11 [--sample]
    python3 -m pipeline.content.recap.build_pack --week 2026-W37 [--sample]

What goes in (each block carries its source so every printed number is traceable):
  data     — archives on origin/main, read AS OF the session (never data/output's latest
             value): breadth_archive, breadth_replay verdicts, conditions, asset_signals,
             groups_archive, ticker_events, leaders_log. Daily blocks hold T and the previous
             session P (skill 四问 #1「它昨天是什么？」); weekly blocks hold every session of the
             week and the prior week's close W0.
  weekly_k — skill 周五规格 fields (wk_ema10/20, three_weeks_tight from universe.json;
             rs_0_1w from groups.json). Those files carry only the latest run, so they are used
             only when their own date stamp equals the week's last session; otherwise null.
  andy     — Discord #live-commentary, ET-stamped. Other channels never enter the pack.
             Older exports without a channel field are live-commentary-only exports and are
             flagged as such (unlabeled_export_dates).
  founders — Founders Note: daily = T and first entry after T; weekly = the ISO-week entry.
  book     — Portfolio from GAS reduced to R and % ONLY (Andy 2026-09-13:
             「管线只做R 和%, 不写股数和美元」). Dollars/quantities stay in-process.
  transcript — path to transcript.md from fetch_transcript.

Credentials: GAS_URL / GAS_SYNC_TOKEN from the environment, else parsed from .env
(worktree, then main checkout). Never printed, never written; errors carry the type only.
GAS answers the same URL with 404 or 200 on consecutive calls (measured 2026-09-13), so the
pull retries; the URL is used exactly as configured.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from pipeline.content.recap import month_dir, pack_dir
from pipeline.content.recap.weeks import prior_week_close, week_sessions
from pipeline.marketcal import last_trading_day

REPO = Path(__file__).resolve().parents[3]
ET = ZoneInfo("America/New_York")

BREADTH_FIELDS = [  # status per data/reference/METRIC_SOURCES.md
    "spx_close", "advances", "declines", "net_advances",
    "up_4pct_stockbee", "down_4pct_stockbee",
    "ratio_5d", "ratio_10d", "t2108",
    "pct_above_20sma_sp500", "pct_above_50sma_sp500", "pct_above_200sma_sp500", "t2108_sp500",
    "new_highs_common", "new_lows_common", "record_high_pct", "mcclellan_osc",
]
INDEX_TICKERS = ["SPY", "QQQ", "IWM", "DIA", "RSP"]
CROSS_ASSET = ["TLT", "IEF", "GLD", "USO", "IBIT", "ETHA", "UUP"]


# ------------------------------------------------------------------ git reads
def show(path: str) -> str:
    r = subprocess.run(["git", "-C", str(REPO), "show", f"origin/main:{path}"], capture_output=True, text=True)
    if r.returncode != 0:
        raise FileNotFoundError(f"origin/main:{path}")
    return r.stdout


_csv_cache: dict[str, list[dict]] = {}


def csv_rows(path: str) -> list[dict]:
    if path not in _csv_cache:
        _csv_cache[path] = list(csv.DictReader(io.StringIO(show(path))))
    return _csv_cache[path]


def fnum(x) -> Optional[float]:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def prev_session(d: dt.date) -> dt.date:
    return last_trading_day(d - dt.timedelta(days=1))


# ------------------------------------------------------------------ breadth / verdict
def _breadth_rows() -> dict:
    return {r["date"]: r for r in csv_rows("data/history/breadth_archive.csv")}


def breadth_block(T: str, P: str) -> dict:
    rows = _breadth_rows()
    if T not in rows:
        raise SystemExit(f"breadth_archive has no row for {T}")
    pick = lambda r: {k: fnum(r.get(k)) for k in BREADTH_FIELDS}
    return {"source": "data/history/breadth_archive.csv", "T": pick(rows[T]),
            "P": pick(rows[P]) if P in rows else None}


def _verdicts():
    v = json.loads(show("data/output/breadth_replay.json"))["verdicts"]
    c = {h["date"]: h for h in json.loads(show("data/output/breadth.json"))["conditions"]["history"]}
    return v, c


def verdict_block(T: str, P: str) -> dict:
    v, c = _verdicts()
    keep = lambda x: None if x is None else {
        "env": x["env"], "score": x["score"], "risk": x.get("risk"), "votes": x.get("votes"),
        "vote_detail": [{k: vd[k] for k in ("label", "side", "value", "line", "margin", "unit", "measurable")}
                        for vd in x.get("vote_detail", [])]}
    return {"source": "breadth_replay.json verdicts[date] · breadth.json conditions.history[date]",
            "T": keep(v.get(T)), "P": keep(v.get(P)),
            "conditions_T": c.get(T), "conditions_P": c.get(P),
            "conditions_series": [c[d]["score"] for d in sorted(c) if d <= T][-60:]}


def days_block(sessions: list[str], W0: str) -> dict:
    rows = _breadth_rows()
    v, c = _verdicts()
    out = []
    for d in [W0] + sessions:
        r = rows.get(d, {})
        out.append({"date": d, "is_base": d == W0,
                    "env": (v.get(d) or {}).get("env"), "score": (v.get(d) or {}).get("score"),
                    "conditions": (c.get(d) or {}).get("score"),
                    "up_4pct": fnum(r.get("up_4pct_stockbee")), "down_4pct": fnum(r.get("down_4pct_stockbee")),
                    "net_advances": fnum(r.get("net_advances")), "mcclellan_osc": fnum(r.get("mcclellan_osc")),
                    "t2108": fnum(r.get("t2108")),
                    "sp500_above_20": fnum(r.get("pct_above_20sma_sp500")),
                    "sp500_above_50": fnum(r.get("pct_above_50sma_sp500"))})
    return {"source": "breadth_archive.csv + breadth_replay.json + breadth.json conditions (row 0 = prior week close)",
            "rows": out, "conditions_series": [c[d]["score"] for d in sorted(c) if d <= sessions[-1]][-60:]}


# ------------------------------------------------------------------ assets
def _asset_index():
    return {(r["date"], r["ticker"]): r for r in csv_rows("data/history/asset_signals.csv")}


def _events(prev: Optional[dict], r: dict) -> list[str]:
    ev = []
    if r["cross_ema21_up"] == "True":
        ev.append("reclaimed 21EMA")
    if r["cross_sma50_up"] == "True":
        ev.append("reclaimed 50SMA")
    # no archived "lost" column: sign flip of the position field between consecutive closes
    for col, lab in (("ema21_dist", "21EMA"), ("sma50_dist", "50SMA")):
        a, b = fnum((prev or {}).get(col)), fnum(r.get(col))
        if a is not None and b is not None and a >= 0 > b:
            ev.append(f"lost {lab}")
    return ev


def asset_block(T: str, P: str) -> dict:
    by = _asset_index()
    out = {}
    for (d, tk), r in by.items():
        if d != T:
            continue
        p = by.get((P, tk))
        out[tk] = {"category": r["category"], "close": fnum(r["close"]), "change_pct": fnum(r["change_pct"]),
                   "rel_volume": fnum(r["rel_volume"]), "rs_line_pctl_21": fnum(r["rs_line_pctl_21"]),
                   "ema21_dist": fnum(r["ema21_dist"]), "sma50_dist": fnum(r["sma50_dist"]),
                   "atr_from_sma50": fnum(r["atr_from_sma50"]), "perf_1m": fnum(r["perf_1m"]),
                   "events": _events(p, r)}
    return {"source": "data/history/asset_signals.csv (events: cross_* columns; lost = *_dist sign flip P→T)",
            "rows": out}


def week_asset_block(sessions: list[str], W0: str) -> dict:
    by = _asset_index()
    T = sessions[-1]
    out = {}
    for tk in INDEX_TICKERS + CROSS_ASSET:
        rT, r0 = by.get((T, tk)), by.get((W0, tk))
        if not rT:
            continue
        events, prev = [], r0
        for d in sessions:
            r = by.get((d, tk))
            if not r:
                continue
            events += [f"{d[5:]} {x}" for x in _events(prev, r)]
            prev = r
        cT, c0 = fnum(rT["close"]), fnum(r0["close"]) if r0 else None
        out[tk] = {"category": rT["category"], "close_T": cT, "close_W0": c0,
                   "week_pct": (cT / c0 - 1) if cT and c0 else None,
                   "daily": [{"date": d, "change_pct": fnum(by[(d, tk)]["change_pct"])} for d in sessions if (d, tk) in by],
                   "events": events, "ema21_dist": fnum(rT["ema21_dist"]), "sma50_dist": fnum(rT["sma50_dist"]),
                   "rs_line_pctl_21": fnum(rT["rs_line_pctl_21"]), "rel_volume_T": fnum(rT["rel_volume"])}
    return {"source": f"data/history/asset_signals.csv · week % = close {T} / close {W0} − 1", "rows": out}


# ------------------------------------------------------------------ groups
def groups_block(T: str, P: str, sort_col: str = "perf_1d", n: int = 8) -> dict:
    rows = csv_rows("data/history/groups_archive.csv")
    prev = {(r["kind"], r["group"]): r for r in rows if r["date"] == P}
    cur = [r for r in rows if r["date"] == T and fnum(r[sort_col]) is not None]
    out = {"source": f"data/history/groups_archive.csv · sorted by {sort_col} · state_P as of {P}", "sort": sort_col}
    for kind in ("industry", "theme"):
        s = sorted((r for r in cur if r["kind"] == kind), key=lambda r: fnum(r[sort_col]), reverse=True)
        fmt = lambda r: {"group": r["group"], "members": int(r["members"]), "state": r["state"],
                         "state_P": prev.get((kind, r["group"]), {}).get("state"),
                         "perf_1d": fnum(r["perf_1d"]), "perf_1w": fnum(r["perf_1w"]), "perf_1m": fnum(r["perf_1m"])}
        out[kind] = {"n": len(s), "top": [fmt(r) for r in s[:n]], "bottom": [fmt(r) for r in s[-n:]],
                     "state_changes": [fmt(r) for r in s if (kind, r["group"]) in prev
                                       and prev[(kind, r["group"])]["state"] != r["state"]]}
    return out


# ------------------------------------------------------------------ weekly K (周五规格)
def weekly_k_block(T: str, tickers: list[str]) -> dict:
    out: dict = {"source": "data/output/universe.json (wk_ema10/20, three_weeks_tight) · data/output/groups.json (rs_0_1w)"}
    try:
        u = json.loads(show("data/output/universe.json"))
        rows = u["rows"] if isinstance(u["rows"], list) else list(u["rows"].values())
    except (FileNotFoundError, KeyError, ValueError):
        rows = []
    stamped = [r for r in rows if r.get("bar_date") == T]
    if not rows or len(stamped) < 0.9 * len(rows):
        out["universe"] = None
        out["universe_note"] = f"universe.json not stamped {T} — weekly K fields withheld"
    else:
        by = {r["ticker"]: r for r in stamped}
        lead = []
        for tk in tickers:
            r = by.get(tk)
            if not r:
                continue
            c, e10, e20 = fnum(r.get("close")), fnum(r.get("wk_ema10")), fnum(r.get("wk_ema20"))
            lead.append({"ticker": tk, "perf_1w": fnum(r.get("perf_1w")), "close": c,
                         "vs_wk_ema10": (c / e10 - 1) if c and e10 else None,
                         "vs_wk_ema20": (c / e20 - 1) if c and e20 else None,
                         "three_weeks_tight": bool(r.get("three_weeks_tight")), "rs_rating": fnum(r.get("rs_rating"))})
        tradeable = [r for r in stamped if r.get("tradeable")]
        above10 = [r for r in tradeable if fnum(r.get("close")) and fnum(r.get("wk_ema10")) and r["close"] > r["wk_ema10"]]
        out["universe"] = {"as_of": T, "n_tradeable": len(tradeable),
                           "three_weeks_tight_tradeable": sum(1 for r in tradeable if r.get("three_weeks_tight")),
                           "pct_tradeable_above_wk_ema10": round(100 * len(above10) / len(tradeable), 1) if tradeable else None,
                           "named": lead}
    try:
        g = json.loads(show("data/output/groups.json"))
    except (FileNotFoundError, ValueError):
        g = {}
    if g.get("date") == T:
        th = sorted((t for t in g.get("themes", []) if t.get("rs_0_1w") is not None), key=lambda t: t["rs_0_1w"], reverse=True)
        f = lambda t: {"group": t["group"], "rs_0_1w": t["rs_0_1w"], "perf_1w": t.get("perf_1w"), "state": t.get("state")}
        out["themes_rs_0_1w"] = {"top": [f(t) for t in th[:5]], "bottom": [f(t) for t in th[-5:]]}
    else:
        out["themes_rs_0_1w"] = None
    return out


# ------------------------------------------------------------------ stocks
TICKER_RE = re.compile(r"(?<![A-Za-z$])\$?([A-Z]{2,5})(?![A-Za-z])")
NOT_TICKERS = {"CPI", "PPI", "FOMC", "MoM", "YOY", "YoY", "ETF", "RS", "AI", "US", "WSJ", "ORH", "MA", "MAs",
               "SPX", "VIX", "ACT", "ER", "RSI", "EMA", "SMA", "ATH", "NFP", "BTC", "ETH", "OK", "MMTW",
               "MMFI", "TIMIRAOS", "HNGE", "APPLE", "EST", "GS", "NQ", "CRUDE", "IWM", "QQQ", "SPY", "DIA", "RSP"}


def named_tickers(msgs: list[dict]) -> list[str]:
    seen: list[str] = []
    for m in msgs:
        for tk in TICKER_RE.findall(m["text"]):
            if tk not in NOT_TICKERS and tk not in seen:
                seen.append(tk)
    return seen


def stocks_block(T: str, tickers: list[str]) -> dict:
    ev = [r for r in csv_rows("data/history/ticker_events.csv") if r["date"] == T and r["ticker"] in set(tickers)]
    ll = {r["ticker"]: r for r in csv_rows("data/history/leaders_log.csv") if r["date"] == T}
    out = {}
    for tk in tickers:
        rs = [r for r in ev if r["ticker"] == tk]
        lead = ll.get(tk)
        if not rs and not lead:
            out[tk] = None
            continue
        first = lambda col: next((fnum(r[col]) for r in rs if fnum(r[col]) is not None), None)
        out[tk] = {"change_pct": first("change_pct"), "rel_volume": first("rel_volume"), "atr_from_sma50": first("atr_ext"),
                   "screeners": sorted({r["screener"] for r in rs}),
                   "rs_1m": fnum(lead["rs_1m"]) if lead else None,
                   "group": lead["group"] if lead else None, "group_state": lead["group_state"] if lead else None}
    return {"source": "data/history/ticker_events.csv + leaders_log.csv (null = in neither archive that day)", "rows": out}


# ------------------------------------------------------------------ Andy
def _thread(date_iso: str) -> Optional[list]:
    try:
        return json.loads(show(f"data/output/threads/{date_iso}/messages.json"))
    except FileNotFoundError:
        return None


def andy_block(dates: list[str]) -> dict:
    """Session T's commentary = thread file T (which opens with the prior evening) plus the
    after-close messages dated T (ET) that the next day's file carries. The next export is how
    a session with no file of its own (09-08) still gets its post-close read."""
    live, missing, unlabeled, seen = [], [], [], set()
    for T in dates:
        sources = []
        own = _thread(T)
        if own is None:
            missing.append(T)
        else:
            sources.append((T, own, False))
        nxt = (dt.date.fromisoformat(T) + dt.timedelta(days=1))
        for k in range(4):  # next export may be after a weekend/holiday
            d = (nxt + dt.timedelta(days=k)).isoformat()
            f = _thread(d)
            if f is not None:
                sources.append((d, f, True))
                break
        for fdate, msgs, is_next in sources:
            for m in msgs:
                ch = m.get("channel")
                if ch is not None and ch != "live-commentary":
                    continue
                text = (m.get("content") or "").strip()
                if not text:
                    continue
                ts = dt.datetime.fromisoformat(m["timestamp"]).astimezone(ET)
                if is_next and not (ts.date().isoformat() == T and ts.time() >= dt.time(16, 0)):
                    continue
                key = (m["timestamp"], text)
                if key in seen:
                    continue
                seen.add(key)
                if ch is None and fdate not in unlabeled:
                    unlabeled.append(fdate)
                phase = ("pre-session" if ts.date().isoformat() < T or ts.time() < dt.time(9, 30)
                         else "after-close" if ts.time() >= dt.time(16, 0) else "session")
                live.append({"session": T, "et": ts.strftime("%m-%d %H:%M"), "phase": phase, "text": text})
    live.sort(key=lambda x: x["et"])
    return {"source": "data/output/threads/<date>/messages.json · live-commentary only (+ T's after-close lines from the next export)",
            "messages": live, "missing_dates": missing, "unlabeled_export_dates": unlabeled,
            "named_tickers": named_tickers(live)}


# ------------------------------------------------------------------ credentials / GAS
def _main_checkout() -> Path:
    r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True)
    return Path(r.stdout.strip()).parent if r.returncode == 0 else REPO


def gas_credentials() -> tuple[str, str]:
    url = os.environ.get("GAS_URL") or os.environ.get("FLUXUS_GAS_URL") or ""
    tok = os.environ.get("GAS_SYNC_TOKEN") or os.environ.get("FLUXUS_SYNC_TOKEN") or ""
    if url and tok:
        return url.strip(), tok.strip()
    for env in (REPO / ".env", _main_checkout() / ".env"):
        if env.exists():
            t = env.read_text()
            mu = re.search(r'^(?:export\s+)?GAS_URL="?([^"\n]+)"?', t, re.M)
            mt = re.search(r'^(?:export\s+)?GAS_SYNC_TOKEN="?([^"\n]+)"?', t, re.M)
            if mu and mt:
                return mu.group(1).strip(), mt.group(1).strip()
    raise RuntimeError("GAS credentials not configured")


def gas_pull(attempts: int = 8, wait_s: float = 12.0) -> dict:
    url, tok = gas_credentials()
    last = "unknown"
    for i in range(attempts):
        try:
            with urllib.request.urlopen(f"{url}?action=pull&token={urllib.parse.quote(tok)}", timeout=60) as r:
                d = json.load(r)
            if d.get("ok"):
                d["_attempts"] = i + 1
                return d
            last = "rejected"
        except urllib.error.HTTPError as e:   # the URL carries the token: report the code only
            last = f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001
            last = type(e).__name__
        time.sleep(wait_s)
    raise RuntimeError(f"GAS pull failed after {attempts} attempts: {last}")


def founders_block(meta: dict, T: str, weekly_monday: Optional[str] = None) -> dict:
    from pipeline.tools.founders_note import entries_for
    src = "GAS meta writing:founders-*:<YYYY-MM> (pipeline/tools/founders_note.py)"
    if weekly_monday:
        ent = entries_for(meta, "founders-weekly", weekly_monday[:7])
        text = str(ent.get(weekly_monday) or "").strip() or None
        return {"source": src, "week_of": weekly_monday, "text": text, "status": "ok" if text else "empty"}
    months = {T[:7], (dt.date.fromisoformat(T) + dt.timedelta(days=31)).isoformat()[:7]}
    ent: dict = {}
    for mo in months:
        ent.update(entries_for(meta, "founders-daily", mo))
    ent = {d: str(v).strip() for d, v in ent.items() if str(v).strip()}
    after = sorted(d for d in ent if d > T)
    return {"source": src, "T": ent.get(T),
            "first_after_T": {"date": after[0], "text": ent[after[0]]} if after else None,
            "status": "ok" if ent else "empty",
            "meta_key_prefixes": sorted({k.split(":")[0] for k in meta})}


# ------------------------------------------------------------------ Portfolio (R and % only)
def _last_close(rows: list[tuple[dt.date, float]], d: dt.date) -> tuple[Optional[float], bool]:
    """rows: [(date, close), ...], any order, dates <= d only expected but not required.
    Returns (close on-or-before d, is_stale). is_stale=True means the most recent
    available date is before d — the vendor hasn't published d's bar yet, so the
    caller must not print it as d's close (09-16: pack.json printed 09-15's close
    as 09-16's, INBOX L2803)."""
    prior = [r for r in rows if r[0] <= d]
    if not prior:
        return None, True
    latest_date, latest_close = max(prior, key=lambda r: r[0])
    return latest_close, latest_date != d


def _closes_override(T: str) -> tuple[dict[str, float], str]:
    """Secondary-source closes for a session the primary vendor has not published.

    Read from RECAP_ROOT/<YYYY-MM>/<T>/pack/closes_override.json:
        {"source": "<where each number came from>", "asof": "<ET timestamp>",
         "closes": {"ARM": 333.20, ...}}
    This never overrides a close the primary vendor DID publish, and it never
    supplies a prior session's number — the file is written by hand from a named
    second source, and its provenance is copied into book["source"] so the PDF's
    numbers stay traceable (09-16: a silent prior-session fallback printed the
    wrong day's close, INBOX L2803)."""
    from . import RECAP_ROOT
    p = RECAP_ROOT / T[:7] / T / "pack" / "closes_override.json"
    if not p.exists():
        return {}, ""
    blob = json.loads(p.read_text())
    px = {k: float(v) for k, v in (blob.get("closes") or {}).items()}
    src = str(blob.get("source") or "unnamed secondary source")
    asof = str(blob.get("asof") or "")
    return px, (f"{src}{' @ ' + asof if asof else ''}" if px else "")


def _closes(tickers: list[str], T: str) -> tuple[dict[str, float], list[str]]:
    """(ticker -> close on T, tickers whose T-day bar is not published yet).
    Stale tickers are never returned in the price dict — the caller must treat
    them like a missing close, not fall back to a prior session silently."""
    if not tickers:
        return {}, []
    import yfinance as yf
    d = dt.date.fromisoformat(T)
    df = yf.download(tickers, start=(d - dt.timedelta(days=10)).isoformat(),
                     end=(d + dt.timedelta(days=1)).isoformat(), auto_adjust=False,
                     progress=False, group_by="ticker")
    out, stale = {}, []
    for tk in tickers:
        try:
            s = (df[tk]["Close"] if len(tickers) > 1 else df["Close"]).dropna()
            rows = [(ts.date(), float(v)) for ts, v in s.items()]
        except Exception:  # noqa: BLE001
            stale.append(tk)
            continue
        px, is_stale = _last_close(rows, d)
        if px is None or is_stale:
            stale.append(tk)
        else:
            out[tk] = px
    if stale:
        ovr, src = _closes_override(T)
        taken = [tk for tk in stale if tk in ovr]
        if taken:
            for tk in taken:
                out[tk] = ovr[tk]
            stale = [tk for tk in stale if tk not in taken]
            _closes.override_note = f"{', '.join(sorted(taken))} via {src}"
    return out, stale


def book_block(T: str, data: dict, period_start: Optional[str] = None) -> dict:
    """Everything returned is R, %, or a count. Nothing in $ or shares."""
    from pipeline.portfolio.sheets_source import to_trades
    trades = to_trades(data.get("stockTrades") or [])
    start_cap = fnum((data.get("meta") or {}).get("startingCapital"))
    d = dt.date.fromisoformat(T)
    week0 = d - dt.timedelta(days=d.weekday())
    p0 = dt.date.fromisoformat(period_start) if period_start else d

    held_at = lambda t: t.original_qty - sum(x.qty for x in t.trims if x.date <= d)
    live = [t for t in trades if t.entry_date <= d]
    open_ = [t for t in live if held_at(t) > 0]
    closed = [t for t in live if held_at(t) <= 0]
    px, stale_close = _closes(sorted({t.ticker for t in open_}), T)
    sgn = lambda t: 1.0 if t.direction == "long" else -1.0

    def realized_between(a: dt.date, b: dt.date) -> tuple[float, int]:
        r, n = 0.0, 0
        for t in live:
            if t.has_R:
                for x in t.trims:
                    if a <= x.date <= b:
                        r += sgn(t) * (x.price - t.entry_price) * x.qty / t.R_dollars
                        n += 1
        return r, n

    positions, missing_px, open_r, no_r = [], [], 0.0, 0
    long_mv = short_mv = unreal = 0.0
    for t in open_:
        q, c = held_at(t), px.get(t.ticker)
        if c is None:
            missing_px.append(t.ticker)
            continue
        pl = sgn(t) * (c - t.entry_price) * q
        unreal += pl
        if t.direction == "long":
            long_mv += c * q
        else:
            short_mv += c * q
        r = pl / t.R_dollars if t.has_R else None
        if r is None:
            no_r += 1
        else:
            open_r += r
        positions.append({"ticker": t.ticker, "direction": t.direction,
                          "entry_date": t.entry_date.isoformat(), "open_R": None if r is None else round(r, 2)})
    realized_all = sum(sgn(t) * (x.price - t.entry_price) * x.qty for t in live for x in t.trims if x.date <= d)
    r_per, n_per = realized_between(p0, d)
    r_wtd, n_wtd = realized_between(week0, d)
    out = {
        "source": "GAS stockTrades (live Sheet) · closes via yfinance at the session close"
                  + (" · " + _closes.override_note if getattr(_closes, "override_note", "") else "")
                  + " · options book not included",
        "as_of": T, "period_start": p0.isoformat(),
        "open_positions": len(open_), "open_names": len({t.ticker for t in open_}), "closed_trades": len(closed),
        "opened_in_period": sum(1 for t in live if p0 <= t.entry_date <= d),
        "closed_in_period": sum(1 for t in closed if t.exit_date and p0 <= t.exit_date <= d),
        "open_R_total": round(open_r, 2), "open_positions_without_R": no_r,
        "realized_R_period": round(r_per, 2), "realized_legs_period": n_per,
        "realized_R_week_to_date": round(r_wtd, 2), "realized_legs_wtd": n_wtd,
        "positions": sorted(positions, key=lambda p: p["entry_date"]), "missing_close": missing_px,
        "closes_stale": bool(stale_close),
    }
    if stale_close:
        out["stale_close"] = sorted(stale_close)
    if start_cap:
        equity = start_cap + realized_all + unreal
        out["return_pct"] = round((equity / start_cap - 1) * 100, 2)
        out["long_exposure_pct"] = round(long_mv / equity * 100, 1)
        out["short_exposure_pct"] = round(short_mv / equity * 100, 1)
        out["cash_pct"] = round(100 - out["long_exposure_pct"] - out["short_exposure_pct"], 1)
    return out


# ------------------------------------------------------------------ main
def _gas_blocks(pack: dict, T: str, period_start: Optional[str], weekly_monday: Optional[str]) -> None:
    try:
        g = gas_pull()
        pack["gas"] = {"attempts": g.get("_attempts"), "meta_keys": sorted((g.get("meta") or {}).keys())}
        pack["founders_note"] = founders_block(g.get("meta") or {}, T, weekly_monday)
        pack["book"] = book_block(T, g, period_start)
    except RuntimeError as e:
        pack["gas"] = {"error": str(e)}
        pack["founders_note"] = {"status": f"unreachable: {e}"}
        pack["book"] = {"status": f"unreachable: {e}"}


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--date")
    g.add_argument("--week", help="ISO week label, e.g. 2026-W37")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--no-gas", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.week:
        sessions = [d.isoformat() for d in week_sessions(a.week)]
        T, W0 = sessions[-1], prior_week_close(a.week).isoformat()
        out_dir = pack_dir(a.week, a.sample)
        andy = andy_block(sessions)
        pack = {"kind": "weekly", "label": a.week, "sessions": sessions, "date": T, "prev_week_close": W0,
                "assets": week_asset_block(sessions, W0), "days": days_block(sessions, W0),
                "groups": groups_block(T, W0, "perf_1w"), "andy": andy,
                "weekly_k": weekly_k_block(T, andy["named_tickers"])}
        period_start, monday = sessions[0], (dt.date.fromisoformat(T) - dt.timedelta(days=dt.date.fromisoformat(T).weekday())).isoformat()
    else:
        d = dt.date.fromisoformat(a.date)
        if last_trading_day(d) != d:
            print(f"{a.date} is not an NYSE session", file=sys.stderr)
            return 2
        T, P = a.date, prev_session(d).isoformat()
        out_dir = pack_dir(T, a.sample)
        andy = andy_block([T])
        pack = {"kind": "daily", "label": T, "date": T, "prev_session": P, "weekday": d.strftime("%A"),
                "breadth": breadth_block(T, P), "verdict": verdict_block(T, P),
                "assets": asset_block(T, P), "groups": groups_block(T, P, "perf_1d"),
                "andy": andy, "stocks": stocks_block(T, andy["named_tickers"])}
        period_start, monday = None, None
    out_dir.mkdir(parents=True, exist_ok=True)
    pack["generated_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    t_data = time.time()
    if a.no_gas:
        pack["founders_note"], pack["book"] = {"status": "skipped"}, {"status": "skipped"}
    else:
        _gas_blocks(pack, T, period_start, monday)
    tr = out_dir / "transcript.md"
    pack["transcript"] = str(tr) if tr.exists() else None
    pack["timing_s"] = {"archives": round(t_data - t0, 1), "gas": round(time.time() - t_data, 1)}
    (out_dir / "pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=1))
    print(f"ok {out_dir / 'pack.json'} · archives {pack['timing_s']['archives']}s · gas {pack['timing_s']['gas']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
