"""主题四态板 —— 代理 ETF + 两周桶。

口径（每一条都有实测支撑，验收记录在私有仓 fluxus-ops）：

    桶      = 整 14 个**日历天**（不是 10 根 K 线）。同样是"两周"，按日历天
              在 9 月是 10 根、70 天在 7 月底是 47 根而 9 月底是 49 根 ——
              **根数会漂，日历天不漂**，这是靠四个不同日期的印数定出来的。
    起点    = ≤ 目标日的最后一个交易日；价格用**未复权**收盘。
    rs(k)   = 该桶内代理 ETF 涨幅 − 基准同期涨幅
    动能(k) = rs(k) − rs(k+1)          （近两周超额 减 前两周超额）
    四态    = rs>0 ? (动能>=0 ? leading : weakening)
                   : (动能>=0 ? improving : lagging)     零算正

**代理 ETF 的四态不等于成员股的状态。** 代理是市值加权的：实测 2026-09-21
的 Cloud Software 代理读 leading，而 70 只成员里 43 只走弱或落后。所以每行
必须带 `members` 分布，页面上常驻显示（Andy 2026-09-23 裁决）。

自己的失败域：这个模块炸了不能让 groups/ladder 看起来是坏的。
"""
from __future__ import annotations

import datetime as dt
from typing import Dict, Iterable, Mapping, Optional, Sequence

import pandas as pd

BUCKET_DAYS = 14
N_BUCKETS = 7          # 页面显示 5 个，多算两个是为了最老那桶也有动能
BENCH = "SPY"

STATES = ("leading", "weakening", "improving", "lagging")


def classify(level: Optional[float], momentum: Optional[float]) -> Optional[str]:
    if level is None or momentum is None:
        return None
    if level > 0:
        return "leading" if momentum >= 0 else "weakening"
    return "improving" if momentum >= 0 else "lagging"


def close_on_or_before(series: pd.Series, day: dt.date) -> Optional[tuple]:
    """≤ day 的最后一个有价交易日 -> (日期, 收盘)。没有就 None。"""
    s = series.dropna()
    if s.empty:
        return None
    s = s[s.index.date <= day] if hasattr(s.index, "date") else s[s.index <= day]
    if s.empty:
        return None
    idx = s.index[-1]
    return (idx.date() if hasattr(idx, "date") else idx, float(s.iloc[-1]))


def bucket_edges(anchor: dt.date, bench: pd.Series,
                 n: int = N_BUCKETS) -> list[Optional[dt.date]]:
    """n+1 个桶界；每个界是 ≤ (锚点 − 14k 天) 的最后一个交易日。"""
    edges: list[Optional[dt.date]] = []
    for k in range(n + 1):
        hit = close_on_or_before(bench, anchor - dt.timedelta(days=BUCKET_DAYS * k))
        edges.append(hit[0] if hit else None)
    return edges


def excess(series: pd.Series, bench: pd.Series,
           newer: Optional[dt.date], older: Optional[dt.date]) -> Optional[float]:
    if newer is None or older is None or newer == older:
        return None
    a, b = close_on_or_before(series, newer), close_on_or_before(series, older)
    q, p = close_on_or_before(bench, newer), close_on_or_before(bench, older)
    if not (a and b and q and p) or b[1] == 0 or p[1] == 0:
        return None
    return (a[1] / b[1] - 1) * 100 - (q[1] / p[1] - 1) * 100


def series_for(bars: Mapping[str, object], ticker: str) -> Optional[pd.Series]:
    """bars 既接受 {ticker: DataFrame(有 Close 列)} 也接受 {ticker: Series}。"""
    obj = bars.get(ticker)
    if obj is None:
        return None
    if isinstance(obj, pd.Series):
        s = obj
    elif isinstance(obj, pd.DataFrame):
        col = "Close" if "Close" in obj.columns else ("close" if "close" in obj.columns else None)
        if col is None:
            return None
        s = obj[col]
    else:
        return None
    return s.dropna() if len(s) else None


def member_distribution(tickers: Iterable[str], bars: Mapping[str, object],
                        bench: pd.Series, edges: Sequence[Optional[dt.date]]) -> Dict[str, int]:
    """成员各自的当期四态计数。

    ⚠️ 成员用的是 ladder 那次下载的**复权**收盘（省一次 2400 只的网络调用），
    主题读数用未复权。股息对个股当期超额的影响在 0.1pp 量级，只影响贴着
    零线的个别名字的归类——分布是个粗计数，不当精确读数用。
    """
    dist = {s: 0 for s in STATES}
    dist["n/a"] = 0
    for t in tickers:
        s = series_for(bars, t)
        if s is None:
            dist["n/a"] += 1
            continue
        lvl = excess(s, bench, edges[0], edges[1])
        prv = excess(s, bench, edges[1], edges[2])
        st = classify(lvl, None if (lvl is None or prv is None) else lvl - prv)
        dist[st or "n/a"] += 1
    return dist


def build(proxies: Mapping[str, str],
          etf_bars: Mapping[str, object],
          member_bars: Mapping[str, object],
          members: Mapping[str, Sequence[str]],
          old_states: Mapping[str, str],
          anchor: Optional[dt.date] = None,
          parallel_until: Optional[str] = None,
          proxy_map_date: Optional[str] = None) -> dict:
    bench = series_for(etf_bars, BENCH)
    if bench is None or bench.empty:
        raise ValueError("基准 SPY 没有价格 —— 主题板的每个数都以它为分母，不能静默跳过")

    if anchor is None:
        last = bench.index[-1]
        anchor = last.date() if hasattr(last, "date") else last
    edges = bucket_edges(anchor, bench)
    mem_bench = series_for(member_bars, BENCH)
    if mem_bench is None or mem_bench.empty:
        mem_bench = bench   # 成员那份没带基准时退回主基准（不是 `or`：Series 不能做真值判断）

    rows = []
    for theme in sorted(proxies):
        etf = proxies[theme]
        s = series_for(etf_bars, etf)
        if s is None:
            continue
        rs = [excess(s, bench, edges[k], edges[k + 1]) for k in range(N_BUCKETS)]
        buckets = []
        for k in range(N_BUCKETS):
            if rs[k] is None:
                continue
            nxt = rs[k + 1] if k + 1 < len(rs) else None
            mom = None if nxt is None else rs[k] - nxt
            buckets.append({
                "weeks": 2 * (k + 1),
                "from": edges[k + 1].isoformat() if edges[k + 1] else None,
                "to": edges[k].isoformat() if edges[k] else None,
                "rs": round(rs[k], 2),
                "momentum": None if mom is None else round(mom, 2),
                "state": classify(rs[k], mom),
            })
        if not buckets:
            continue
        rows.append({
            "theme": theme,
            "etf": etf,
            "state": buckets[0]["state"],
            "state_prev": old_states.get(theme),   # 并排期的旧读数
            "rs": buckets[0]["rs"],
            "momentum": buckets[0]["momentum"],
            "buckets": buckets,
            "members": member_distribution(members.get(theme, ()), member_bars,
                                           mem_bench, edges),
            "member_count": len(members.get(theme, ())),
        })

    counts = {s: sum(1 for r in rows if r["state"] == s) for s in STATES}
    _ml = mem_bench.index[-1]
    members_asof = (_ml.date() if hasattr(_ml, "date") else _ml).isoformat()

    return {
        "asof": anchor.isoformat(),
        # 成员那份行情的最后一天。和 asof 不同 = 分布比主题读数旧一天
        # （两边是两次下载，一边先落一边后落时会这样）。宁可发出来让人看见，
        # 也不要静默地把昨天的分布挂在今天的四态旁边。
        "members_asof": members_asof,
        "benchmark": BENCH,
        "bucket_days": BUCKET_DAYS,
        "proxy_map_date": proxy_map_date,
        "parallel_until": parallel_until,   # 并排期结束日，到期撤 state_prev
        "counts": counts,
        "themes": rows,
    }


def fetch_bars(tickers: Sequence[str], period: str = "6mo", download=None
               ) -> Dict[str, pd.Series]:
    """代理 ETF 的日线。**未复权** —— 口径要求，别改成 auto_adjust=True。"""
    if download is None:
        import yfinance as yf

        def download(ts):
            return yf.download(ts, period=period, interval="1d", auto_adjust=False,
                               progress=False, group_by="ticker", threads=True)

    raw = download(list(tickers))
    out: Dict[str, pd.Series] = {}
    if isinstance(raw.columns, pd.MultiIndex):
        for t in tickers:
            if (t, "Close") in raw.columns:
                s = raw[(t, "Close")].dropna()
                if len(s):
                    out[t] = s
    elif "Close" in raw.columns and len(tickers) == 1:
        s = raw["Close"].dropna()
        if len(s):
            out[tickers[0]] = s
    if BENCH not in out:
        raise ValueError("基准 SPY 没取到 —— 拒绝出一份没有分母的板")
    return out
