#!/usr/bin/env python3
"""Assemble the material pack for one session → pack.json (local only, never git).

Usage:
    python3 -m pipeline.content.recap.build_pack --date 2026-09-11 [--sample]

What goes in (each block carries its source so every printed number is traceable):
  data     — archives on origin/main, read AS OF the session (never data/output's
             latest value): breadth_archive, breadth_replay verdicts, conditions
             series, asset_signals, groups_archive, ticker_events, leaders_log.
             Each block holds T and the previous session P, so the writer can
             apply skill 四问 #1 (「它昨天是什么？」).
  andy     — Discord #live-commentary for the session, ET-stamped. Other channels
             are member chatter and never enter the pack (member names never print).
  founders — Founders Note for T and the first entry after T (skill: the note for
             session T is usually written the next morning; both are given, the
             writer does not pick silently). Empty → "empty", unreachable → error.
  book     — Portfolio from GAS, reduced to R and % ONLY (Andy 2026-09-13:
             「管线只做R 和%, 不写股数和美元」). Dollars and quantities are used
             in-process to form ratios and are never written.
  transcript — path to transcript.md from fetch_transcript.

Credentials: GAS_URL / GAS_SYNC_TOKEN from the environment, else parsed from the
main checkout's .env. Never printed, never written; errors carry the type only.
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
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from pipeline.content.recap import pack_dir
from pipeline.marketcal import last_trading_day

REPO = Path(__file__).resolve().parents[3]
ET = ZoneInfo("America/New_York")

BREADTH_FIELDS = [  # status per data/reference/METRIC_SOURCES.md
    "spx_close", "advances", "declines", "net_advances",
    "up_4pct_stockbee", "down_4pct_stockbee",            # ✅ Stockbee 4%
    "ratio_5d", "ratio_10d",
    "t2108",                                              # ✅ Worden (whole pool)
    "pct_above_20sma_sp500", "pct_above_50sma_sp500", "pct_above_200sma_sp500", "t2108_sp500",  # ✅ index-bound
    "new_highs_common", "new_lows_common", "record_high_pct",  # ✅
    "mcclellan_osc",                                      # ✅
]
INDEX_TICKERS = ["SPY", "QQQ", "IWM", "DIA", "RSP"]


# ------------------------------------------------------------------ git reads
def show(path: str) -> str:
    r = subprocess.run(["git", "-C", str(REPO), "show", f"origin/main:{path}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise FileNotFoundError(f"origin/main:{path}")
    return r.stdout


def csv_rows(path: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(show(path))))


def fnum(x) -> Optional[float]:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def prev_session(d: dt.date) -> dt.date:
    return last_trading_day(d - dt.timedelta(days=1))


# ------------------------------------------------------------------ data blocks
def breadth_block(T: str, P: str) -> dict:
    rows = {r["date"]: r for r in csv_rows("data/history/breadth_archive.csv")}
    if T not in rows:
        raise SystemExit(f"breadth_archive has no row for {T}")
    pick = lambda r: {k: fnum(r.get(k)) for k in BREADTH_FIELDS}
    series = [r for d, r in sorted(rows.items()) if d <= T][-6:]
    return {"source": "data/history/breadth_archive.csv", "T": pick(rows[T]),
            "P": pick(rows[P]) if P in rows else None,
            "last6": [{"date": r["date"], "up_4pct_stockbee": fnum(r["up_4pct_stockbee"]),
                       "down_4pct_stockbee": fnum(r["down_4pct_stockbee"]),
                       "net_advances": fnum(r["net_advances"]),
                       "mcclellan_osc": fnum(r["mcclellan_osc"])} for r in series]}


def verdict_block(T: str, P: str) -> dict:
    v = json.loads(show("data/output/breadth_replay.json"))["verdicts"]
    keep = lambda x: None if x is None else {
        "env": x["env"], "score": x["score"], "risk": x.get("risk"),
        "votes": x.get("votes"),
        "vote_detail": [{k: vd[k] for k in ("label", "side", "value", "line", "margin", "unit", "measurable")}
                        for vd in x.get("vote_detail", [])]}
    c = {h["date"]: h for h in json.loads(show("data/output/breadth.json"))["conditions"]["history"]}
    return {"source": "breadth_replay.json verdicts[date] · breadth.json conditions.history[date]",
            "T": keep(v.get(T)), "P": keep(v.get(P)),
            "conditions_T": c.get(T), "conditions_P": c.get(P),
            "conditions_series": [c[d]["score"] for d in sorted(c) if d <= T][-60:]}


def asset_block(T: str, P: str) -> dict:
    rows = csv_rows("data/history/asset_signals.csv")
    by = {(r["date"], r["ticker"]): r for r in rows}
    out = {}
    for (d, tk), r in by.items():
        if d != T:
            continue
        p = by.get((P, tk), {})
        ev = []
        if r["cross_ema21_up"] == "True": ev.append("reclaimed 21EMA")
        if r["cross_sma50_up"] == "True": ev.append("reclaimed 50SMA")
        # "lost" has no archived event column; derived from the position fields'
        # sign flip between P and T (same definition, two consecutive closes).
        for col, lab in (("ema21_dist", "21EMA"), ("sma50_dist", "50SMA")):
            a, b = fnum(p.get(col)), fnum(r.get(col))
            if a is not None and b is not None and a >= 0 > b:
                ev.append(f"lost {lab}")
        out[tk] = {"category": r["category"], "close": fnum(r["close"]),
                   "change_pct": fnum(r["change_pct"]), "rel_volume": fnum(r["rel_volume"]),
                   "rs_line_pctl_21": fnum(r["rs_line_pctl_21"]),
                   "ema21_dist": fnum(r["ema21_dist"]), "sma50_dist": fnum(r["sma50_dist"]),
                   "atr_from_sma50": fnum(r["atr_from_sma50"]), "perf_1m": fnum(r["perf_1m"]),
                   "events": ev,
                   "P": {"change_pct": fnum(p.get("change_pct")), "ema21_dist": fnum(p.get("ema21_dist")),
                         "sma50_dist": fnum(p.get("sma50_dist"))} if p else None}
    return {"source": "data/history/asset_signals.csv (events: cross_* columns; lost = *_dist sign flip P→T)",
            "rows": out}


def groups_block(T: str, P: str, n: int = 8) -> dict:
    rows = csv_rows("data/history/groups_archive.csv")
    prev = {(r["kind"], r["group"]): r for r in rows if r["date"] == P}
    cur = [r for r in rows if r["date"] == T and fnum(r["perf_1d"]) is not None]
    out = {"source": "data/history/groups_archive.csv"}
    for kind in ("industry", "theme"):
        s = sorted((r for r in cur if r["kind"] == kind), key=lambda r: fnum(r["perf_1d"]), reverse=True)
        fmt = lambda r: {"group": r["group"], "members": int(r["members"]), "state": r["state"],
                         "state_P": prev.get((kind, r["group"]), {}).get("state"),
                         "perf_1d": fnum(r["perf_1d"]), "perf_1w": fnum(r["perf_1w"])}
        out[kind] = {"n": len(s), "top": [fmt(r) for r in s[:n]], "bottom": [fmt(r) for r in s[-n:]],
                     "state_changes": [fmt(r) for r in s
                                       if (kind, r["group"]) in prev and prev[(kind, r["group"])]["state"] != r["state"]]}
    return out


TICKER_RE = re.compile(r"(?<![A-Za-z$])\$?([A-Z]{2,5})(?![A-Za-z])")
NOT_TICKERS = {"CPI", "PPI", "FOMC", "MoM", "YOY", "ETF", "RS", "AI", "US", "WSJ", "ORH", "MA", "MAs",
               "SPX", "VIX", "ACT", "ER", "RSI", "EMA", "SMA", "ATH", "NFP", "BTC", "ETH", "OK", "MMTW",
               "MMFI", "TIMIRAOS", "V", "HNGE"}


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
        chg = next((fnum(r["change_pct"]) for r in rs if fnum(r["change_pct"]) is not None), None)
        rv = next((fnum(r["rel_volume"]) for r in rs if fnum(r["rel_volume"]) is not None), None)
        ext = next((fnum(r["atr_ext"]) for r in rs if fnum(r["atr_ext"]) is not None), None)
        lead = ll.get(tk)
        if not rs and not lead:
            out[tk] = None
            continue
        out[tk] = {"change_pct": chg, "rel_volume": rv, "atr_from_sma50": ext,
                   "screeners": sorted({r["screener"] for r in rs}),
                   "rs_1m": fnum(lead["rs_1m"]) if lead else None,
                   "group": lead["group"] if lead else None,
                   "group_state": lead["group_state"] if lead else None}
    return {"source": "data/history/ticker_events.csv + leaders_log.csv (null = not in either archive that day)",
            "rows": out}


# ------------------------------------------------------------------ Andy
def andy_block(T: str) -> dict:
    try:
        msgs = json.loads(show(f"data/output/threads/{T}/messages.json"))
    except FileNotFoundError:
        return {"source": None, "messages": [], "note": "no thread export for this date"}
    live = []
    for m in msgs:
        if m.get("channel") != "live-commentary" or not (m.get("content") or "").strip():
            continue
        ts = dt.datetime.fromisoformat(m["timestamp"]).astimezone(ET)
        phase = ("pre-session" if ts.date().isoformat() < T or ts.time() < dt.time(9, 30)
                 else "after-close" if ts.time() >= dt.time(16, 0) else "session")
        live.append({"et": ts.strftime("%m-%d %H:%M"), "phase": phase, "text": m["content"].strip()})
    return {"source": f"data/output/threads/{T}/messages.json · channel live-commentary only",
            "messages": live, "named_tickers": named_tickers(live)}


# ------------------------------------------------------------------ credentials
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


def gas_pull() -> dict:
    url, tok = gas_credentials()
    # Cut a pasted ?query/#fragment by string split: rebuilding via urlunsplit turned
    # the real deployment URL into a 404 (measured 2026-09-13, raw URL → 200).
    endpoint = url.split("#", 1)[0].split("?", 1)[0]
    try:
        with urllib.request.urlopen(f"{endpoint}?action=pull&token={urllib.parse.quote(tok)}", timeout=60) as r:
            d = json.load(r)
    except Exception as e:  # the URL carries the token: report the type only
        raise RuntimeError(f"GAS pull failed: {type(e).__name__}") from None
    if not d.get("ok"):
        raise RuntimeError("GAS pull rejected")
    return d


# ------------------------------------------------------------------ Founders Note
def founders_block(T: str, meta: dict) -> dict:
    from pipeline.tools.founders_note import entries_for
    months = {T[:7], (dt.date.fromisoformat(T) + dt.timedelta(days=31)).isoformat()[:7]}
    ent: dict = {}
    for mo in months:
        ent.update(entries_for(meta, "founders-daily", mo))
    ent = {d: str(v).strip() for d, v in ent.items() if str(v).strip()}
    after = sorted(d for d in ent if d > T)
    return {"source": "GAS meta writing:founders-daily:<YYYY-MM> (pipeline/tools/founders_note.py)",
            "T": ent.get(T), "first_after_T": {"date": after[0], "text": ent[after[0]]} if after else None,
            "status": "ok" if ent else "empty — no founders-daily entries in GAS meta for these months"}


# ------------------------------------------------------------------ Portfolio (R and % only)
def _closes(tickers: list[str], T: str) -> dict[str, float]:
    if not tickers:
        return {}
    import yfinance as yf
    d = dt.date.fromisoformat(T)
    df = yf.download(tickers, start=(d - dt.timedelta(days=10)).isoformat(),
                     end=(d + dt.timedelta(days=1)).isoformat(), auto_adjust=False,
                     progress=False, group_by="ticker")
    out = {}
    for tk in tickers:
        try:
            s = (df[tk]["Close"] if len(tickers) > 1 else df["Close"]).dropna()
            s = s[s.index.date <= d]
            out[tk] = float(s.iloc[-1])
        except Exception:  # noqa: BLE001
            pass
    return out


def book_block(T: str, data: dict) -> dict:
    """Everything returned is R, %, or a count. Nothing in $ or shares."""
    from pipeline.portfolio.sheets_source import to_trades
    trades = to_trades(data.get("stockTrades") or [])
    meta = data.get("meta") or {}
    start_cap = fnum(meta.get("startingCapital"))
    d = dt.date.fromisoformat(T)
    week0 = d - dt.timedelta(days=d.weekday())

    def held_at(t) -> int:
        return t.original_qty - sum(x.qty for x in t.trims if x.date <= d)

    live = [t for t in trades if t.entry_date <= d]
    open_ = [t for t in live if held_at(t) > 0]
    closed = [t for t in live if held_at(t) <= 0]
    px = _closes(sorted({t.ticker for t in open_}), T)

    def sgn(t): return 1.0 if t.direction == "long" else -1.0
    def realized_between(a: dt.date, b: dt.date) -> tuple[float, int]:
        r, n = 0.0, 0
        for t in live:
            if not t.has_R:
                continue
            for x in t.trims:
                if a <= x.date <= b:
                    r += sgn(t) * (x.price - t.entry_price) * x.qty / t.R_dollars
                    n += 1
        return r, n

    positions, missing_px, open_r, no_r = [], [], 0.0, 0
    long_mv = short_mv = unreal = 0.0
    for t in open_:
        q = held_at(t)
        c = px.get(t.ticker)
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
    r_day, n_day = realized_between(d, d)
    r_wtd, n_wtd = realized_between(week0, d)
    out = {
        "source": "GAS stockTrades (live Sheet) · closes via yfinance at the session close · options book not included",
        "as_of": T,
        "open_positions": len(open_), "open_names": len({t.ticker for t in open_}),
        "closed_trades": len(closed),
        "opened_on_T": sum(1 for t in live if t.entry_date == d),
        "closed_on_T": sum(1 for t in closed if t.exit_date == d),
        "open_R_total": round(open_r, 2), "open_positions_without_R": no_r,
        "realized_R_session": round(r_day, 2), "realized_legs_session": n_day,
        "realized_R_week_to_date": round(r_wtd, 2), "realized_legs_wtd": n_wtd,
        "positions": sorted(positions, key=lambda p: p["entry_date"]),
        "missing_close": missing_px,
    }
    if start_cap:
        equity = start_cap + realized_all + unreal
        out["return_pct"] = round((equity / start_cap - 1) * 100, 2)
        out["long_exposure_pct"] = round(long_mv / equity * 100, 1)
        out["short_exposure_pct"] = round(short_mv / equity * 100, 1)
        out["cash_pct"] = round(100 - out["long_exposure_pct"] - out["short_exposure_pct"], 1)
        out["pct_method"] = ("equity = starting capital + all realized P/L to T + open P/L at T close; "
                             "exposure = market value / equity; cash = 100 − long − short (stock book only)")
    return out


# ------------------------------------------------------------------ main
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--no-gas", action="store_true", help="skip Founders Note + Portfolio")
    a = ap.parse_args(argv)
    t0 = time.time()
    d = dt.date.fromisoformat(a.date)
    if last_trading_day(d) != d:
        print(f"{a.date} is not an NYSE session", file=sys.stderr)
        return 2
    T, P = a.date, prev_session(d).isoformat()
    out_dir = pack_dir(T, a.sample)
    out_dir.mkdir(parents=True, exist_ok=True)
    andy = andy_block(T)
    pack = {"date": T, "prev_session": P, "weekday": d.strftime("%A"),
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "breadth": breadth_block(T, P), "verdict": verdict_block(T, P),
            "assets": asset_block(T, P), "groups": groups_block(T, P),
            "andy": andy, "stocks": stocks_block(T, andy.get("named_tickers", []))}
    t_data = time.time()
    if a.no_gas:
        pack["founders_note"] = {"status": "skipped"}
        pack["book"] = {"status": "skipped"}
    else:
        try:
            g = gas_pull()
            pack["founders_note"] = founders_block(T, g.get("meta") or {})
            pack["book"] = book_block(T, g)
        except RuntimeError as e:
            pack["founders_note"] = {"status": f"unreachable: {e}"}
            pack["book"] = {"status": f"unreachable: {e}"}
    tr = out_dir / "transcript.md"
    pack["transcript"] = str(tr) if tr.exists() else None
    pack["timing_s"] = {"archives": round(t_data - t0, 1), "gas": round(time.time() - t_data, 1)}
    (out_dir / "pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=1))
    print(f"ok {out_dir / 'pack.json'} · archives {pack['timing_s']['archives']}s · gas {pack['timing_s']['gas']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
