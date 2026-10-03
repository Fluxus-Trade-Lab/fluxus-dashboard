"""第7章读数核对：全市场普通股「5 个交易日涨 ≥20%」每日家数（T-1003-68）。

口径
- 池子：data/output/universe.json 当前全部行，剔除 industry == "Shell Companies"（SPAC/壳，
  与 pipeline/screeners/breadth_metrics.py `_EXCLUDED_INDUSTRIES` 同口径）。
  未加市值闸：这是「全市场」。另给 ≥$1B 子集（universe 的 tradeable 口径）作对照。
- 价格：yfinance 日线，auto_adjust=True（拆股+分红调整）。**不是未复权**：未复权会把
  反向拆股读成假的 +N% 涨幅。
- 涨幅：收盘 / 5 个交易日前收盘 − 1 ≥ 0.20（5 个 bar 前，即同一 ticker 的行序，不按日历日）。
- 对照子集：收盘 ≥ $5 且 20 日均成交额 ≥ $5M（与 Stockbee/阈值常用的流动性底线相近，仅作敏感性）。
- 窗口：2023-11-01 起（START），之前 dv20 未满 20 根，流动性列失真。
- 幸存者偏差：池子是**今天**的名单，已退市的不在里面，因此读数会偏低；契约行须写明。

用法
  python3 data/research/course_ch07/count_5d20.py fetch   # 拉数据到 CACHE（分块，可断点续）
  python3 data/research/course_ch07/count_5d20.py count   # 从 CACHE 算每日家数 → OUT_CSV
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
UNIVERSE = ROOT / "data/output/universe.json"
CACHE = Path("/tmp/ch07_5d20_cache")
OUT_CSV = ROOT / "data/research/course_ch07/count_5d20_daily.csv"
PERIOD = "3y"
CHUNK = 200
# 读数起点：dv20（20 日均成交额）要攒满 20 根 K 线才有值，之前「流动性」一列读成 0 或偏低。
START = "2023-11-01"


def universe_tickers() -> tuple[list[str], dict[str, float]]:
    rows = json.load(open(UNIVERSE))["rows"]
    common = [r for r in rows if r.get("industry") != "Shell Companies"]
    tickers = [r["ticker"] for r in common]
    cap = {r["ticker"]: (r.get("market_cap") or 0) for r in common}
    return tickers, cap


def fetch() -> None:
    import yfinance as yf

    CACHE.mkdir(parents=True, exist_ok=True)
    tickers, _ = universe_tickers()
    for i in range(0, len(tickers), CHUNK):
        part = tickers[i:i + CHUNK]
        path = CACHE / f"chunk_{i:05d}.pkl"
        if path.exists():
            continue
        df = yf.download(part, period=PERIOD, auto_adjust=True, group_by="column",
                         threads=True, progress=False)
        df.to_pickle(path)
        print(f"chunk {i}: {len(part)} tickers → {path.name}", flush=True)


def load_panels() -> tuple[pd.DataFrame, pd.DataFrame]:
    closes, vols = [], []
    for path in sorted(CACHE.glob("chunk_*.pkl")):
        df = pd.read_pickle(path)
        closes.append(df["Close"])
        vols.append(df["Volume"])
    close = pd.concat(closes, axis=1)
    vol = pd.concat(vols, axis=1)
    return close, vol


def daily_counts(close: pd.DataFrame, vol: pd.DataFrame, cap: dict[str, float]) -> pd.DataFrame:
    """纯函数：close/vol 为 日期×ticker 面板，cap 为 ticker→市值。返回逐日四列（未截起点）。"""
    close = close.sort_index()
    vol = vol.reindex(close.index)
    ret5 = close / close.shift(5) - 1
    # 1e-9 容差：120/100-1 在浮点里是 0.19999999999999996，恰好 +20% 必须计入
    hit = ret5 >= 0.20 - 1e-9
    valid = ret5.notna()
    big = pd.Series({t: cap.get(t, 0) >= 1e9 for t in close.columns})
    dv20 = (close * vol).rolling(20, min_periods=20).mean()
    liquid = (close >= 5) & (dv20 >= 5e6)
    out = pd.DataFrame({
        "n_valid": valid.sum(axis=1),
        "n_hit_all": hit.sum(axis=1),
        "n_hit_cap1b": (hit & big).sum(axis=1),
        "n_hit_liquid": (hit & liquid).sum(axis=1),
    })
    out.index = pd.to_datetime(out.index).strftime("%Y-%m-%d")
    out.index.name = "date"
    return out


def count() -> None:
    _, cap = universe_tickers()
    close, vol = load_panels()
    out = daily_counts(close, vol, cap)
    # 起点之前 dv20 未满、池子也未满，丢弃；起点后有效名仍可能低于中位数 80%，同样不计
    out = out.loc[START:]
    out = out[out["n_valid"] >= 0.8 * out["n_valid"].median()]
    out.to_csv(OUT_CSV)
    print(f"wrote {OUT_CSV} rows={len(out)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "count":
        count()
    else:
        print(__doc__)
