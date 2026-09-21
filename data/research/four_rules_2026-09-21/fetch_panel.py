"""四条外部规则测试 —— 取数（T-0921-100，2026-09-21）

两个面板，都缓存进 .cache/（gitignore 内，不进仓库）：

  bench_panel.pkl  指数与族群 ETF。OHLC，2004-01-01 起。
                   SPY/QQQ/RSP/SMH 是四条规则直接点名的；^IXIC 是规则 3 的「纳指」；
                   其余是规则 2 的「族群」代理（见 r2 脚本注释里为什么不用 groups.json）。

  stock_panel.pkl  个股。OHLC，2010-01-01 起。名单取自今天的 universe.json，
                   闸：close×avg_volume ≥ $20M/日 且 market_cap ≥ $2B，且在 groups.json 里有行业。
                   ⚠️ 幸存者偏差：这是**今天还活着**的 1885 只。退市/被并购的票一只都不在。
                   偏差方向在每个结论里单独讨论，不在这里一笔带过。

用法：python3 data/research/four_rules_2026-09-21/fetch_panel.py [--refresh]
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
CACHE = REPO / ".cache"
BENCH_PKL = CACHE / "fr_bench_panel.pkl"
STOCK_PKL = CACHE / "fr_stock_panel.pkl"
COVERAGE = Path(__file__).resolve().parent / "coverage.json"

BENCH_START = "2004-01-01"
STOCK_START = "2010-01-01"
END = "2026-09-19"          # 最近完成交易日 2026-09-18 的次日（yfinance end 是开区间）

# 指数 + 四条规则点名的 ETF
INDEXES = ["SPY", "QQQ", "RSP", "SMH", "^IXIC", "IWM"]

# 规则 2 的族群代理：11 个 SPDR 板块 + 一批有十年以上历史的行业/主题 ETF。
# 选择判据只有一条——2010 年以前就上市，好让样本跨两轮以上完整周期。
GROUP_ETFS = [
    "XLK", "XLF", "XLV", "XLE", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC",
    "SMH", "IGV", "XBI", "IBB", "ITB", "XHB", "XRT", "KRE", "KIE", "XOP", "OIH",
    "GDX", "IYT", "IYR", "VNQ", "TAN", "LIT", "URA", "PBW", "JETS", "HACK", "SKYY",
    "FDN", "SOXX", "XME", "MOO", "PHO", "IHI", "XAR",
]

BATCH = 120


def _download(tickers: list[str], start: str) -> dict[str, pd.DataFrame]:
    import yfinance as yf
    panel: dict[str, pd.DataFrame] = {}
    uniq = sorted(set(tickers))
    for i in range(0, len(uniq), BATCH):
        chunk = uniq[i:i + BATCH]
        print(f"  {i}-{i + len(chunk)} / {len(uniq)}", flush=True)
        data = yf.download(chunk, start=start, end=END, group_by="ticker",
                           auto_adjust=True, progress=False, threads=True,
                           actions=False)
        for t in chunk:
            try:
                frame = data[t][["Open", "High", "Low", "Close", "Volume"]]
            except (KeyError, TypeError):
                continue
            frame = frame.dropna(how="all")
            if len(frame) < 260:          # 不足一年，52 周口径没法用
                continue
            frame.index = pd.DatetimeIndex(frame.index).tz_localize(None)
            panel[t] = frame.sort_index()
    return panel


def stock_universe() -> list[str]:
    rows = json.loads((REPO / "data/output/universe.json").read_text())["rows"]
    groups = json.loads((REPO / "data/output/groups.json").read_text())["stocks"]
    out = []
    for r in rows:
        t = r["ticker"]
        close = r.get("close") or 0
        avgvol = r.get("avg_volume") or 0
        mcap = r.get("market_cap") or 0
        if close * avgvol >= 20e6 and mcap >= 2e9 and t in groups:
            out.append(t)
    return sorted(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    CACHE.mkdir(exist_ok=True)

    cov = {}

    if args.refresh or not BENCH_PKL.exists():
        want = INDEXES + GROUP_ETFS
        print(f"bench: {len(set(want))} symbols")
        bench = _download(want, BENCH_START)
        BENCH_PKL.write_bytes(pickle.dumps(bench))
        cov["bench"] = {"requested": len(set(want)), "returned": len(bench),
                        "missing": sorted(set(want) - set(bench))}
    else:
        print("bench: cached")

    if args.refresh or not STOCK_PKL.exists():
        want = stock_universe()
        print(f"stocks: {len(want)} symbols")
        stocks = _download(want, STOCK_START)
        STOCK_PKL.write_bytes(pickle.dumps(stocks))
        cov["stocks"] = {"requested": len(want), "returned": len(stocks),
                         "missing": sorted(set(want) - set(stocks))}
    else:
        print("stocks: cached")

    if cov:
        old = json.loads(COVERAGE.read_text()) if COVERAGE.exists() else {}
        old.update(cov)
        COVERAGE.write_text(json.dumps(old, indent=2))
        for k, v in cov.items():
            print(f"{k}: {v['returned']}/{v['requested']} returned, "
                  f"{len(v['missing'])} missing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
