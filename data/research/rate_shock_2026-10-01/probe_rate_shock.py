#!/usr/bin/env python3
"""十年期收益率急升之后，股指前向 5/21/63 日收益分档统计。

任务 T-1001-103（linda，2026-10-01）。起因：X 调研主班连续多班记同一个弹药缺口——
圈内满屏 n=1 的先例（「上次十年期在这儿是 2007 年 5 月」「RSI 到了 2022 年那个位置」），
没有人给出分档统计。

口径三件全部照抄，没有自造事件定义（见 README「口径出处」）：
  A  Goldman Sachs（Kostin，2025-06-05）：「yields rise by more than two standard
     deviations in a month」——21 个交易日的收益率变动 ≥ 2σ。
  B  TMC Research（Picerno，2026-05-05）：收益率相对**前六个月最低点**的抬升，
     分档 50 / 100 / 200 / 300 bp，带排他窗口防同一轮急升重复计数。
  C  X 线当天说的那个数（bluechipdaily：「二十天涨 43 个基点」）——Δ20d ≥ 40bp。
     这一档不是学术口径，是为了直接答圈内那句话。

超额收益两种，都是 MacKinlay (1997) 列的标准模型：
  constant mean return model  →  fwd − 该标的全样本无条件均值（基准只算一次）
  market-adjusted model       →  fwd − 同期 SPY fwd（只对 IWM/RSP/QQQ）

自造的只有两个参数，README 里明写：σ 的回看长度、排他窗口长度。两个都按扫描给，不挑一个。
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RNG_SEED = 20261001

ASSETS = ["SPY", "IWM", "RSP", "QQQ", "^GSPC"]
HORIZONS = [5, 21, 63]

# —— 自造参数，按扫描给，不挑一个 ——
SIGMA_LOOKBACKS = [756, 1260, 2520]      # 3y / 5y / 10y 交易日
EXCL_WINDOWS = [0, 21, 126]              # 0=不去重（原始）, 21=GS 的「一个月」节奏, 126=TMC 的六个月
HEADLINE_SIGMA_LB = 756                  # 3y：GS 的 60bp 锚点在这一档复算出 61.0bp，见 gs_calibration_check
HEADLINE_EXCL = 21

N_BOOT = 10000


# ------------------------------------------------------------------ 取数

def load_dgs10() -> pd.Series:
    """FRED DGS10（10-Year Treasury Constant Maturity，日频，1962-01-02 起）。"""
    cache = HERE / "dgs10.csv.gz"
    if not cache.exists():
        import urllib.request
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
        with urllib.request.urlopen(url, timeout=60) as r:
            pd.read_csv(io.BytesIO(r.read())).to_csv(cache, index=False)
    raw = pd.read_csv(cache)
    datecol = raw.columns[0]
    s = pd.Series(
        pd.to_numeric(raw["DGS10"], errors="coerce").values,
        index=pd.to_datetime(raw[datecol]),
        name="DGS10",
    ).dropna()
    return s.sort_index()


def load_prices() -> pd.DataFrame:
    cache = HERE / "prices.csv.gz"
    if not cache.exists():
        import yfinance as yf
        cols = {}
        for t in ASSETS:
            h = yf.Ticker(t).history(period="max", auto_adjust=True)
            if h.empty:
                raise RuntimeError(f"{t}: yfinance 返回空")
            cols[t] = h["Close"].tz_localize(None)
        pd.DataFrame(cols).to_csv(cache)
    df = pd.read_csv(cache, index_col=0, parse_dates=True)
    return df[ASSETS].sort_index()


# ------------------------------------------------------- 事件定义（三套口径）

def build_yield_features(y: pd.Series, grid: pd.DatetimeIndex) -> pd.DataFrame:
    """把收益率对齐到交易日网格（取 ≤ 当日的最后一个读数，交易者当天能看到的那个）。"""
    ya = y.reindex(y.index.union(grid)).ffill().reindex(grid)
    out = pd.DataFrame({"y": ya})
    out["d21"] = ya - ya.shift(21)
    out["d20"] = ya - ya.shift(20)
    out["runup126"] = ya - ya.rolling(126, min_periods=126).min()
    out["rel63"] = ya / ya.shift(63) - 1.0          # Signal_Sigma 的「三个月涨两成」
    for lb in SIGMA_LOOKBACKS:
        # shift(1)：σ 只用到前一日为止的信息，不看未来
        out[f"sig{lb}"] = out["d21"].rolling(lb, min_periods=lb // 2).std().shift(1)
        out[f"z{lb}"] = out["d21"] / out[f"sig{lb}"]
    return out


def dedupe(dates: pd.DatetimeIndex, grid: pd.DatetimeIndex, excl: int) -> pd.DatetimeIndex:
    """排他窗口：同一轮急升里只留第一天。excl 以交易日计；0 = 不去重。"""
    if excl <= 0 or len(dates) == 0:
        return dates
    pos = {d: i for i, d in enumerate(grid)}
    kept, last = [], -10**9
    for d in dates:
        i = pos[d]
        if i - last >= excl:
            kept.append(d)
            last = i
    return pd.DatetimeIndex(kept)


def event_sets(feat: pd.DataFrame, grid: pd.DatetimeIndex) -> dict:
    """返回 {档名: {excl: DatetimeIndex}}。"""
    specs: dict[str, pd.Series] = {}
    # A · GS：Δ21d ≥ kσ
    for lb in SIGMA_LOOKBACKS:
        z = feat[f"z{lb}"]
        for lo, hi, lab in [(2.0, 2.5, "2.0-2.5"), (2.5, 3.0, "2.5-3.0"), (3.0, np.inf, "3.0+")]:
            specs[f"A_sig{lb}_z{lab}"] = (z >= lo) & (z < hi)
        specs[f"A_sig{lb}_z2.0+"] = z >= 2.0
    # B · TMC：相对前六个月低点的抬升
    for bp in [50, 100, 200, 300]:
        specs[f"B_runup126_{bp}bp+"] = feat["runup126"] >= bp / 100.0
    # C · X 线那句话：Δ20d ≥ 40bp（另给 60bp = GS 文章里那个锚点值）
    for bp in [40, 60]:
        specs[f"C_d20_{bp}bp+"] = feat["d20"] >= bp / 100.0
    # D · Signal_Sigma 那句话：三个月相对涨幅 ≥ 20%
    for pct in [20, 30]:
        specs[f"D_rel63_{pct}pct+"] = feat["rel63"] >= pct / 100.0

    out = {}
    for name, mask in specs.items():
        dates = grid[mask.reindex(grid).fillna(False).to_numpy()]
        out[name] = {e: dedupe(dates, grid, e) for e in EXCL_WINDOWS}
    return out


# ------------------------------------------------------------------ 统计

def summarize(fwd: pd.Series, uncond_mean: float, uncond_med: float,
              uncond_hit: float, events: pd.DatetimeIndex, rng) -> dict:
    """fwd 已经是「某标的某horizon」的前向收益序列（NaN=尾部不足）。"""
    pool = fwd.dropna()
    sub = fwd.reindex(events).dropna()
    n = int(len(sub))
    if n == 0:
        return {"n": 0}
    med = float(sub.median())
    boot = None
    if len(pool) > n:
        idx = rng.integers(0, len(pool), size=(N_BOOT, n))
        boot = np.median(pool.to_numpy()[idx], axis=1)
    return {
        "n": n,
        "mean": float(sub.mean()),
        "median": med,
        "p25": float(sub.quantile(0.25)),
        "p75": float(sub.quantile(0.75)),
        "hit": float((sub > 0).mean()),
        # constant mean return model（MacKinlay 1997）：减该标的全样本无条件基准
        "abn_mean": float(sub.mean() - uncond_mean),
        "abn_median": float(med - uncond_med),
        "abn_hit": float((sub > 0).mean() - uncond_hit),
        # 随机化检验：从同一标的全样本里抽同样多的日子，看中位数比观测值更极端的比例
        "p_two_sided": (None if boot is None else
                        float(2 * min((boot >= med).mean(), (boot <= med).mean()))),
    }


def main() -> int:
    prices = load_prices()
    y = load_dgs10()

    # —— 先复算出处印出来的数：GS 2025-06-05 说「2σ 的月度变动大约 60bp」 ——
    gridg = prices.index
    featg = build_yield_features(y, gridg)
    calib = {}
    asof = pd.Timestamp("2025-06-05")
    row_i = featg.index.searchsorted(asof, side="right") - 1
    for lb in SIGMA_LOOKBACKS:
        calib[f"sigma_lookback_{lb}d"] = {
            "asof": str(featg.index[row_i].date()),
            "two_sigma_bp": round(float(featg[f"sig{lb}"].iloc[row_i]) * 200, 1),
            "y_level_pct": float(featg["y"].iloc[row_i]),
        }

    # —— 当下读数：最近一个交易日站在哪一档 ——
    now = {"asof": str(featg.index[-1].date())}
    for col in ["y", "d20", "d21", "runup126", "rel63"]:
        now[col] = round(float(featg[col].iloc[-1]), 4)
    for lb in SIGMA_LOOKBACKS:
        now[f"z{lb}"] = round(float(featg[f"z{lb}"].iloc[-1]), 2)
        now[f"two_sigma_bp_{lb}"] = round(float(featg[f"sig{lb}"].iloc[-1]) * 200, 1)

    uncond: dict = {}
    per_asset: dict = {}

    for a in ASSETS:
        px = prices[a].dropna()
        grid = px.index
        feat = build_yield_features(y, grid)
        fwds = {h: px.shift(-h) / px - 1.0 for h in HORIZONS}
        # SPY 对齐（market-adjusted model 用）
        spy = prices["SPY"].dropna()
        spy_f = {h: (spy.shift(-h) / spy - 1.0).reindex(grid) for h in HORIZONS}

        uncond[a] = {}
        series: dict[tuple[str, int], pd.Series] = {}
        for h in HORIZONS:
            raw = fwds[h]
            series[("abs", h)] = raw
            uncond[a][f"abs_{h}"] = {
                "n": int(raw.notna().sum()),
                "mean": float(raw.mean()), "median": float(raw.median()),
                "hit": float((raw.dropna() > 0).mean()),
            }
            if a not in ("SPY", "^GSPC"):
                rel = raw - spy_f[h]
                series[("rel_spy", h)] = rel
                uncond[a][f"rel_spy_{h}"] = {
                    "n": int(rel.notna().sum()),
                    "mean": float(rel.mean()), "median": float(rel.median()),
                    "hit": float((rel.dropna() > 0).mean()),
                }

        evs = event_sets(feat, grid)
        rng = np.random.default_rng(RNG_SEED)
        buckets: dict = {}
        for name, by_excl in evs.items():
            buckets[name] = {}
            for excl, dates in by_excl.items():
                cell = {"n_event_days": int(len(dates))}
                for (kind, h), s in series.items():
                    u = uncond[a][f"{kind}_{h}"]
                    cell[f"{kind}_{h}"] = summarize(
                        s, u["mean"], u["median"], u["hit"], dates, rng)
                buckets[name][str(excl)] = cell

        if a == "^GSPC":
            out_dates = {}
            for nm in ["A_sig756_z2.0+", "C_d20_40bp+", "D_rel63_20pct+"]:
                out_dates[nm] = [str(x.date()) for x in evs[nm][21]]
            (HERE / "event_dates_spx.json").write_text(json.dumps(out_dates, indent=1))

        # —— 稳健性：事件扎堆在 2022–23，剔掉那两年还剩多少（两个头条档都做）——
        robustness = {}
        for bname in ["A_sig756_z2.0+", "C_d20_40bp+"]:
            rob = {}
            base = evs[bname][HEADLINE_EXCL]
            yrs = pd.Series(base).dt.year if len(base) else pd.Series(dtype=int)
            rob["events_by_year"] = {str(k): int(v) for k, v in
                                     (yrs.value_counts().sort_index().items() if len(base) else [])}
            for lbl, drop in [("all", []), ("ex2022", [2022]), ("ex2022_2023", [2022, 2023])]:
                dd = base if not drop else base[~yrs.isin(drop).to_numpy()]
                rob[lbl] = {}
                for h in HORIZONS:
                    u = uncond[a][f"abs_{h}"]
                    rob[lbl][f"abs_{h}"] = summarize(series[("abs", h)], u["mean"],
                                                     u["median"], u["hit"], dd,
                                                     np.random.default_rng(RNG_SEED))
            robustness[bname] = rob

        per_asset[a] = {
            "robustness": robustness,
            "sample": {"start": str(grid.min().date()), "end": str(grid.max().date()),
                       "n_sessions": int(len(grid))},
            "uncond": uncond[a],
            "buckets": buckets,
        }

    out = {
        "task": "T-1001-103",
        "generated_for_date": str(prices.index.max().date()),
        "dgs10": {"start": str(y.index.min().date()), "end": str(y.index.max().date()),
                  "n_obs": int(len(y)), "last": float(y.iloc[-1])},
        "params": {
            "sigma_lookbacks_d": SIGMA_LOOKBACKS, "excl_windows_d": EXCL_WINDOWS,
            "headline_sigma_lookback_d": HEADLINE_SIGMA_LB, "headline_excl_d": HEADLINE_EXCL,
            "horizons_d": HORIZONS, "n_bootstrap": N_BOOT, "seed": RNG_SEED,
        },
        "gs_calibration_check": calib,
        "current_reading": now,
        "assets": per_asset,
    }
    (HERE / "rate_shock.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"wrote {HERE / 'rate_shock.json'}")
    print("GS 60bp 锚点复算：", json.dumps(calib, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
