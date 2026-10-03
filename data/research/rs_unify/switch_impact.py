#!/usr/bin/env python3
"""RS 统一（选项 A）上线前回测：换判据会不会出现巨大变化。

Andy 2026-10-04：「选A，并且看能否回测，出现巨大变化，然后也需要5天观察期，
不对的话，我们得改回来。」

做法：只看各面板的 **RS 那一条腿**（其余腿缺五年历史，无法回放；这是本研究的
覆盖边界，结论只说「RS 腿换读数」的影响，不说整面板）。逐个交易日：
  旧腿：现行判据（rs_3m≥80 / rs_1m≥60 / rs_1m 97–99 / 行业内 rs_3m 中位数排名）
  新腿：同一位置改读 rs_rating，阈值两种取法——
        same   阈值数字不变（直接把 rs_3m 换成 rs_rating）
        sized  按五年平均名单规模对齐（新阈值让平均入选只数与旧腿相同）
量：每天新旧名单的重合率（旧名单里有多少仍在新名单）、名单规模；以及旧名单、
新名单、只在旧里、只在新里四组之后 20/63 个交易日相对 SPY 的超额与胜率。

「巨大变化」的判据（自造，写死在这里便于复核）：某天旧名单在新名单中留存 < 50%。

存活偏差：样本是今天还能交易的名字投影回五年前（同 rs_compare.py），所有绝对
收益数字偏乐观；但新旧两组受同一偏差，**两组之差**受影响小得多——本研究只用差。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rs_compare as RC  # noqa: E402

HORIZONS = (20, 63)
WARMUP = 260
OUT = Path(__file__).resolve().parent / "switch_impact.json"

# 现行判据（与消费者清单同源：run_all.py:675 · watchlist.py:285-292,344-347 ·
# screener-presets.json:62-66,121-137）
LEGS = {
    "liquid_leader / vcs": {"field": "rs_3m", "lo": 80, "hi": None},
    "4% Bullish": {"field": "rs_1m", "lo": 60, "hi": None},
    "Monthly Leader 97": {"field": "rs_1m", "lo": 97, "hi": 99},
}


def membership(df: pd.DataFrame, lo: float, hi):
    m = df >= lo
    if hi is not None:
        m &= df <= hi
    return m


def sized_threshold(new: pd.DataFrame, old_mask: pd.DataFrame, width, days) -> float:
    """找新阈值 lo，让新腿五年平均入选只数≈旧腿。
    width=None 表示开区间（≥lo）；否则区间 [lo, lo+width]，宽度与旧腿相同。"""
    target = old_mask.loc[days].sum(axis=1).mean()
    sub = new.loc[days]
    best, err = None, None
    for t in np.arange(40, 99.01, 0.25):
        m = membership(sub, t, None if width is None else t + width)
        e = abs(m.sum(axis=1).mean() - target)
        if err is None or e < err:
            best, err = t, e
    return float(best)


def leg_study(f, name, spec, days):
    old_df, new_df = f[spec["field"]], f["rs_rating"]
    old = membership(old_df, spec["lo"], spec["hi"])
    out = {"old_rule": f"{spec['field']} " + (f">= {spec['lo']}" if spec["hi"] is None
                                               else f"{spec['lo']}–{spec['hi']}")}
    variants = {"same": spec["lo"]}
    variants["sized"] = sized_threshold(new_df, old, None if spec["hi"] is None else spec["hi"] - spec["lo"], days)
    for vname, lo in variants.items():
        hi = None if spec["hi"] is None else lo + (spec["hi"] - spec["lo"])
        new = membership(new_df, lo, hi)
        o, n = old.loc[days], new.loc[days]
        size_o, size_n = o.sum(axis=1), n.sum(axis=1)
        both = (o & n).sum(axis=1)
        keep = (both / size_o.replace(0, np.nan))
        res = {
            "new_rule": "rs_rating " + (f">= {lo:g}" if hi is None else f"{lo:g}–{hi:g}"),
            "size_old_mean": round(float(size_o.mean()), 1),
            "size_new_mean": round(float(size_n.mean()), 1),
            "keep_median": round(float(keep.median()), 3),
            "keep_p10": round(float(keep.quantile(0.10)), 3),
            "days_keep_below_50pct": int((keep < 0.5).sum()),
            "days_total": int(keep.notna().sum()),
        }
        for h in HORIZONS:
            fwd = f["fwd"][h].loc[days]
            grp = {"old": o, "new": n, "old_only": o & ~n, "new_only": n & ~o}
            for g, mask in grp.items():
                vals = fwd.where(mask).stack().dropna()
                res[f"{g}_{h}d_mean"] = round(float(vals.mean() * 100), 2) if len(vals) else None
                res[f"{g}_{h}d_win"] = round(float((vals > 0).mean()), 3) if len(vals) else None
                res[f"{g}_{h}d_n"] = int(len(vals))
        out[vname] = res
    return out


def industry_study(f, days, industry: dict):
    """行业前 20：行业内 rs_3m 中位数排名 vs rs_rating 中位数排名，逐日前 20 重合。"""
    cols = [c for c in f["rs_3m"].columns if c in industry]
    groups = pd.Series({c: industry[c] for c in cols})
    keep = []
    for d in days[::5]:                       # 每周取一天，够看分布
        a = f["rs_3m"].loc[d, cols].groupby(groups).median().dropna()
        b = f["rs_rating"].loc[d, cols].groupby(groups).median().dropna()
        ok = (groups.value_counts() >= 3)
        a, b = a[ok.reindex(a.index).fillna(False)], b[ok.reindex(b.index).fillna(False)]
        if len(a) < 20 or len(b) < 20:
            continue
        ta, tb = set(a.nlargest(20).index), set(b.nlargest(20).index)
        keep.append(len(ta & tb) / 20)
    s = pd.Series(keep)
    return {"weeks": int(len(s)), "keep_median": round(float(s.median()), 3),
            "keep_p10": round(float(s.quantile(0.10)), 3),
            "weeks_keep_below_50pct": int((s < 0.5).sum())}


def main():
    close = RC.load_panel(fetch_now="--fetch" in sys.argv)
    f = RC.build_features(close)
    days = f["rs_rating"].index[WARMUP:-max(HORIZONS)]
    out = {"panel": {"tickers": int(close.shape[1] - 1),
                     "start": str(days[0].date()), "end": str(days[-1].date()),
                     "days": int(len(days))}}
    for name, spec in LEGS.items():
        out[name] = leg_study(f, name, spec, days)
        print(name, json.dumps(out[name], ensure_ascii=False)[:400])
    uni = json.loads(Path("data/output/universe.json").read_text())["rows"]
    ind = {r["ticker"]: r.get("industry") for r in uni if r.get("industry")}
    out["industry top20"] = industry_study(f, days, ind)
    print("industry", out["industry top20"])
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("→", OUT)


if __name__ == "__main__":
    main()
