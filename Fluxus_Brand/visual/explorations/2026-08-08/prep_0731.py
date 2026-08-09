"""Build the real 2026-07-31 dataset the three design explorations render.

Everything here is measured from committed repo data (breadth archive, ticker
events) plus daily OHLC — local store first, yfinance only for what's missing.
No hand-typed numbers: every claim in the mockups must carry its measurement.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "/Users/taolezhu/Documents/AI-Trading-System")
from pipeline.tickers.ohlc_store import load_local_ohlc  # noqa: E402

ROOT = Path("/Users/taolezhu/Documents/AI-Trading-System")
OUT = Path(__file__).parent / "data_0731.json"
AS_OF = "2026-07-31"

# The names that appear in the 7/31 recap, tagged by the role they play in it.
NAMES = {
    "index":   ["SPY", "QQQ", "RSP", "DIA", "IWM"],
    # RING is deliberately excluded: the recap's RING ("earnings pop, Voice AI")
    # is not the RING that resolves on the tape (iShares Global Gold Miners ETF),
    # so no verifiable bars exist for it. Better absent than wrong.
    "leader":  ["AMZN", "MSFT", "NVDA", "ANET", "AXTI", "NTAP", "DXCM"],
    "damaged": ["TER", "MXL", "SNDK", "GLW", "NVTS", "GFS", "AAPL"],
}
ALL = [t for v in NAMES.values() for t in v]


# ---------------------------------------------------------------- bars

def _reaches(df: pd.DataFrame) -> bool:
    return not df.empty and str(pd.to_datetime(df["date"]).max().date()) >= AS_OF


def get_bars(sym: str) -> pd.DataFrame | None:
    rows = load_local_ohlc(sym, tickers_dir=ROOT / "data/output/tickers")
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    # The local store can be stale (a ticker file written before AS_OF). Falling
    # back only on *absence* silently dropped names, so check reach too.
    if not df.empty and not _reaches(df):
        df = pd.DataFrame()
    if df.empty:
        import yfinance as yf
        df = yf.download(sym, period="2y", interval="1d",
                         auto_adjust=True, progress=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index().rename(columns={
            "Date": "date", "Open": "open", "High": "high",
            "Low": "low", "Close": "close", "Volume": "volume"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df[df["date"] <= AS_OF].sort_values("date").reset_index(drop=True)
    return df if len(df) >= 210 else None


# ---------------------------------------------------------- ladder rung

RUNGS = [
    ("broken",       "破位"),
    ("stabilizing",  "止跌"),
    ("reclaim",      "收回主要均线"),
    ("above_50",     "站上 50日"),
    ("pivot",        "逼近 pivot"),
    ("breakout",     "突破"),
    ("holds",        "突破站住"),
    ("expansion",    "扩张"),
]


RECENT = 5  # sessions — what still counts as "just happened"


def _sessions_above(close: pd.Series, ma: pd.Series) -> int:
    """Consecutive sessions the close has held above `ma`, counting back from today.

    0 = below it today. This is what separates a *reclaim* (a repair step that
    just happened) from merely *being above* a level for months — the difference
    between NVDA's 200-day reclaim and QQQ never having lost it.
    """
    a = (close > ma).values
    if not a[-1]:
        return 0
    n = 0
    for i in range(len(a) - 1, -1, -1):
        if a[i]:
            n += 1
        else:
            break
    return n


def classify(df: pd.DataFrame) -> dict:
    """Place a name on the repair ladder, and record the evidence for the placement."""
    c = df["close"].iloc[-1]
    prev = df["close"].iloc[-2]
    ema21_s = df["close"].ewm(span=21, adjust=False).mean()
    sma50_s = df["close"].rolling(50).mean()
    sma200_s = df["close"].rolling(200).mean()
    ema21, sma50, sma200 = ema21_s.iloc[-1], sma50_s.iloc[-1], sma200_s.iloc[-1]

    held21 = _sessions_above(df["close"], ema21_s)
    held50 = _sessions_above(df["close"], sma50_s)
    held200 = _sessions_above(df["close"], sma200_s)
    just_reclaimed_21 = 0 < held21 <= RECENT
    just_reclaimed_200 = 0 < held200 <= RECENT
    # A fresh loss of the 21/50 is deterioration, not repair — carried as a
    # direction flag so the ladder shows position and the arrow shows travel.
    just_lost = (held21 == 0 and (df["close"] > ema21_s).iloc[-RECENT - 1:-1].any()) or \
                (held50 == 0 and (df["close"] > sma50_s).iloc[-RECENT - 1:-1].any())
    hi20 = df["high"].iloc[-21:-1].max()      # 20d high, excluding today
    hi50 = df["high"].iloc[-51:-1].max()
    lo20 = df["low"].iloc[-21:-1].min()
    hi252 = df["high"].iloc[-252:].max()

    # was today's close a fresh 20d high, and had it been one in the prior 5 days?
    broke_out = c > hi20
    held = any(df["close"].iloc[-i] > df["high"].iloc[-21 - i:-1 - i].max()
               for i in range(2, 6))

    if broke_out and c > hi50:
        rung, why = 7, f"收在 50日高点 {hi50:.2f} 之上"
    elif broke_out and held:
        rung, why = 6, f"突破后仍站在 20日高点 {hi20:.2f} 上方"
    elif broke_out:
        rung, why = 5, f"收 {c:.2f} > 20日高 {hi20:.2f}"
    elif c > sma50 and c >= hi20 * 0.97:
        rung, why = 4, f"距 20日高 {hi20:.2f} 仅 {(hi20 / c - 1) * 100:.1f}%"
    elif c > sma50:
        rung, why = 3, f"收在 50日线 {sma50:.2f} 之上"
    elif just_reclaimed_200:
        # A 200-day reclaim while still capped by the 50-day is a genuine repair
        # step. Ranking it on position alone buried NVDA's reclaim among names
        # that simply never lost the level.
        rung, why = 2, f"{held200} 个交易日前上穿 200日线 {sma200:.2f}，50日线 {sma50:.2f} 仍在头上"
    elif just_reclaimed_21:
        rung, why = 2, f"{held21} 个交易日前上穿 21日线 {ema21:.2f}，50日线 {sma50:.2f} 仍在头上"
    elif c > sma200:
        rung, why = 1, f"21/50 日线之下，但守住 200日线 {sma200:.2f}（已 {held200} 日）"
    else:
        rung, why = 0, f"跌破 200日线 {sma200:.2f}"

    return {
        "close": round(float(c), 2),
        "chg_pct": round(float(c / prev - 1) * 100, 2),
        "rung": rung,
        "rung_key": RUNGS[rung][0],
        "rung_label": RUNGS[rung][1],
        "evidence": why,
        # An upward step wins over a recent loss: NVDA both lost the 21-day and
        # reclaimed the 200-day inside the same week, and the reclaim is the
        # event that set its rung.
        "direction": "up" if (just_reclaimed_21 or just_reclaimed_200 or broke_out)
                     else ("down" if just_lost else "flat"),
        "held_21": held21, "held_50": held50, "held_200": held200,
        "above_21": bool(c > ema21),
        "above_50": bool(c > sma50),
        "above_200": bool(c > sma200),
        "from_52wh_pct": round(float(c / hi252 - 1) * 100, 1),
        "ema21": round(float(ema21), 2),
        "sma50": round(float(sma50), 2),
        "sma200": round(float(sma200), 2),
        # 30-session close trace, normalised, for sparklines
        "trace": [round(float(x), 4) for x in df["close"].iloc[-30:]],
    }


# ------------------------------------------------------------- assemble

def main() -> None:
    br = pd.read_csv(ROOT / "data/history/breadth_archive.csv")
    br = br[br["date"] <= AS_OF].tail(30).reset_index(drop=True)
    today = br.iloc[-1]

    ev = pd.read_csv(ROOT / "data/history/ticker_events.csv")
    ev = ev[ev["date"] <= AS_OF]
    sessions = sorted(ev["date"].unique())[-10:]
    win = ev[ev["date"].isin(sessions)]

    # 领涨扩散的证据 ①：每天各筛选器命中数
    counts = (win.groupby(["date", "screener"])["ticker"].nunique()
                 .unstack(fill_value=0).reindex(sessions, fill_value=0))
    # 领涨扩散的证据 ②：质量档（vcp / episodic_pivot / momentum_97）的板块构成变化
    QUALITY = ["vcp", "episodic_pivot", "momentum_97"]
    qual = win[win["screener"].isin(QUALITY)]
    sect = (qual.groupby(["date", "sector"])["ticker"].nunique()
                .unstack(fill_value=0).reindex(sessions, fill_value=0))
    sect = sect[sect.sum().sort_values(ascending=False).index[:8]]

    names = {}
    for role, syms in NAMES.items():
        for s in syms:
            df = get_bars(s)
            if df is None or df["date"].iloc[-1] != AS_OF:
                print(f"  skip {s} (no bars through {AS_OF})")
                continue
            names[s] = {"role": role, **classify(df)}
            print(f"  {s:5s} rung {names[s]['rung']} {names[s]['rung_label']}")

    out = {
        "as_of": AS_OF,
        "rungs": [{"key": k, "label": v} for k, v in RUNGS],
        "names": names,
        "breadth": {
            "today": {k: (None if pd.isna(today[k]) else float(today[k]))
                      for k in br.columns if k not in ("date", "source")},
            "trace": {k: [None if pd.isna(x) else float(x) for x in br[k]]
                      for k in ["t2108", "pct_above_20sma", "pct_above_50sma",
                                "pct_above_200sma", "ratio_5d", "ratio_10d",
                                "mcclellan_osc", "up_4pct", "down_4pct",
                                "net_advances", "spx_close"]},
            "dates": list(br["date"]),
        },
        "diffusion": {
            "sessions": sessions,
            "screeners": {c: [int(x) for x in counts[c]] for c in counts.columns},
            "sectors": {c: [int(x) for x in sect[c]] for c in sect.columns},
        },
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\nwrote {OUT}  ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
