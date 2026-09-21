"""规则 1：动能趋势里第一次回踩 20 日线，是不是几个月的低点？（T-0921-100）

原话（Shake Pryzby，X 2026-05-17）：「动能趋势里 SPY 第一次回踩 20 日线，通常是几个月的低点。」
他的例子：SPY（05-17）、SMH（05-19）、KOSPI（05-18）。→ 书稿「轮动」一节。

口径来源（宪法「先找口径」）：
- 「一段拉升之后第一次碰到均线」在公开资料里有原型但**没有机构标准**：TradingView 开源脚本
  "Optimized 1st Touch 10SMA After Run"、Bulls on Wall Street 的 "First Pullback"
  都是同一形状，但各家的「一段拉升」定义不同。
- 「动能趋势」**查无标准定义**。本脚本自造，见 MOMENTUM GATE。

自造的参数（全在这里，改一处就重算）：
- MA：20 日**简单**均线（他写「20 日线」；他另一处写 20 EMA，所以 EMA 作稳健性一起跑）。
- MOMENTUM GATE（自造）：20MA > 50MA 且 20MA 今天 > 10 个交易日前的 20MA。
  不用「离均线几个 ATR」——那是他「暂停清单」里的另一条，混进来会把两条规则测成一条。
- RUN：连续 ≥ 15 个交易日 Low 始终在 20MA 上方。15 自造；稳健性跑 10 / 25。

**回踩段 = 一次事件，不是一天。** 从第一个 Low ≤ 20MA 的日子起，到 Low 重新完全站上
20MA 为止（上限 20 个交易日）算一段。段内的最低 Low 记作 L。
  - `first_in_regime`：**动能 gate 从关变开之后的第一次回踩**——最贴近他那句话的读法
    （SPY 2026-05-17 就是这种）。每一轮动能趋势只有一个。
  - `first`：段前有 ≥ RUN 个交易日没碰过 20MA（一轮趋势里可以出现多次；
    这是可交易的操作版读法）。
  - `later`：同一轮 gate 里、段前不足 RUN 日的回踩段（同形状，但不是第一次）。
  - 对照（无回踩条件）：同一 gate 下所有交易日的 h 日远期收益中位数。

被测的那句话有两种读法，两种都报：
  - 严格（日内）：此后任何一天 Low < L 就算跌破。
  - 收盘：此后任何一天 Close < L 才算跌破。
并报**跌破有多深**（此后 63 日里相对 L 的最大跌幅）——「守住了」和「被戳穿 0.3%」
和「被砸穿 8%」是三件事，只报比例会把它们混成一件。

输出：r1_first_touch_20dma.json
"""
from __future__ import annotations

import json
import pickle
import statistics
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BENCH = REPO / ".cache" / "fr_bench_panel.pkl"
OUT = HERE / "r1_first_touch_20dma.json"

EPISODE_CAP = 20
HORIZONS = (21, 63, 126)
NAMED = ("SPY", "SMH", "QQQ", "RSP", "IWM")


def episodes(df: pd.DataFrame, ma_kind: str, run_len: int):
    """把回踩切成段，标成 first / later。返回 (events, gate_array, ma20)。"""
    c, lo = df.Close, df.Low
    ma20 = c.ewm(span=20, adjust=False).mean() if ma_kind == "ema" else c.rolling(20).mean()
    ma50 = c.rolling(50).mean()
    gate = ((ma20 > ma50) & (ma20 > ma20.shift(10))).fillna(False).to_numpy()
    ok = (ma20.notna() & ma50.notna()).to_numpy()
    lo_a, c_a, m_a = lo.to_numpy(), c.to_numpy(), ma20.to_numpy()

    out = []
    i, streak = 0, 0
    regime_open = False     # 动能 gate 是否处在「开着」的一段里
    regime_virgin = False   # 这一段 gate 里还没出现过回踩
    n = len(df)
    while i < n:
        if not ok[i]:
            i, streak = i + 1, 0
            regime_open = False
            continue
        if gate[i] and not regime_open:
            regime_open, regime_virgin = True, True
        elif not gate[i]:
            regime_open = False
        if lo_a[i] > m_a[i]:
            streak += 1
            i += 1
            continue
        # 回踩段开始
        start = i
        end = i
        j = i + 1
        while j < n and j - start < EPISODE_CAP:
            if lo_a[j] > m_a[j]:
                break
            end = j
            j += 1
        if gate[start]:
            if regime_virgin and streak >= run_len:
                kind = "first_in_regime"
            elif streak >= run_len:
                kind = "first"
            else:
                kind = "later"
            out.append({"i0": start, "i1": end, "kind": kind})
            regime_virgin = False
        streak = 0
        i = j
    return out, gate, ma20


def measure(df: pd.DataFrame, ep: dict) -> dict:
    lo = df.Low.to_numpy()
    c = df.Close.to_numpy()
    i0, i1 = ep["i0"], ep["i1"]
    L = float(lo[i0:i1 + 1].min())
    rec = {"date": str(df.index[i0].date()), "kind": ep["kind"], "low": round(L, 4)}
    tail_lo, tail_c = lo[i1 + 1:], c[i1 + 1:]
    rec["avail"] = len(tail_lo)

    def first_breach(series):
        for k, v in enumerate(series):
            if v < L:
                return k + 1
            
        return None

    rec["held_intraday"] = first_breach(tail_lo)
    rec["held_close"] = first_breach(tail_c)
    # 63 日内相对 L 的最大跌破深度（正数＝跌破了多少）
    w = tail_lo[:63]
    rec["max_breach63_pct"] = round(100 * (L - float(w.min())) / L, 2) if len(w) else None
    px = c[i1]
    for h in HORIZONS:
        k = i1 + h
        rec[f"fwd{h}"] = round(float(c[k] / px - 1), 4) if k < len(c) else None
    return rec


def summarize(events, h):
    usable = [e for e in events
              if (e["held_intraday"] is not None and e["held_intraday"] <= h)
              or e["avail"] >= h]
    if not usable:
        return None

    def held_pct(field):
        hits = sum(1 for e in usable if e[field] is None or e[field] > h)
        return round(100 * hits / len(usable), 1)

    obs_i = [e["held_intraday"] for e in events if e["held_intraday"] is not None]
    obs_c = [e["held_close"] for e in events if e["held_close"] is not None]
    fwd = [e[f"fwd{h}"] for e in events if e.get(f"fwd{h}") is not None]
    depth = [e["max_breach63_pct"] for e in usable if e["max_breach63_pct"] is not None]
    return {
        "n": len(usable),
        "held_intraday_pct": held_pct("held_intraday"),
        "held_close_pct": held_pct("held_close"),
        "median_held_intraday": round(statistics.median(obs_i), 1) if obs_i else None,
        "median_held_close": round(statistics.median(obs_c), 1) if obs_c else None,
        "median_max_breach63_pct": round(statistics.median(depth), 2) if depth else None,
        f"median_fwd{h}_pct": round(100 * statistics.median(fwd), 2) if fwd else None,
    }


def unconditional(df, gate, h):
    c = df.Close.to_numpy()
    vals = [c[i + h] / c[i] - 1 for i in range(len(c) - h) if gate[i]]
    return round(100 * statistics.median(vals), 2) if vals else None


def main():
    panel = pickle.loads(BENCH.read_bytes())
    symbols = [s for s in panel if s != "^IXIC"]
    result = {"meta": {
        "generated": "2026-09-21",
        "claim": "动能趋势里第一次回踩 20 日线，是几个月的低点（Shake Pryzby X 2026-05-17）",
        "data": "yfinance auto_adjust 日线，2004-01-01 起，截至 2026-09-18；"
                f"{len(symbols)} 个指数/ETF（SPY QQQ RSP SMH IWM + 39 个板块/行业 ETF）",
        "self_made": ["动能趋势 gate = 20MA>50MA 且 20MA 十日前上行（查无标准，自造）",
                      "RUN ≥ 15 日未碰 20MA（自造；稳健性 10/25）",
                      "回踩段上限 20 个交易日（自造）"],
        "standard_checked": "TradingView 开源脚本 1st-Touch-after-Run / Bulls on Wall Street "
                            "First Pullback 是同一形状的公开原型，但无机构标准定义；"
                            "「动能趋势」查过，无标准",
        "survivorship": "指数与仍在交易的 ETF，无退市问题；但 ETF 的上市年份不同"
                        "（XLRE 2015、JETS 2015、HACK 2014），样本按各自历史长度加权",
    }, "variants": {}}

    for ma_kind in ("sma", "ema"):
        for run_len in (10, 15, 25):
            key = f"{ma_kind}_run{run_len}"
            regime1, firsts, laters, per_sym = [], [], [], {}
            uncond = {h: [] for h in HORIZONS}
            for s in symbols:
                df = panel[s]
                eps, gate, _ = episodes(df, ma_kind, run_len)
                r1e = [measure(df, e) for e in eps if e["kind"] == "first_in_regime"]
                fev = [measure(df, e) for e in eps if e["kind"] == "first"]
                lev = [measure(df, e) for e in eps if e["kind"] == "later"]
                regime1 += r1e
                firsts += fev
                laters += lev
                if s in NAMED:
                    per_sym[s] = {"first_in_regime_h63": summarize(r1e, 63),
                                  "first_h63": summarize(fev, 63),
                                  "later_h63": summarize(lev, 63)}
                for h in HORIZONS:
                    u = unconditional(df, gate, h)
                    if u is not None:
                        uncond[h].append(u)
            result["variants"][key] = {
                "n_symbols": len(symbols),
                "n_first_in_regime": len(regime1),
                "n_first": len(firsts), "n_later": len(laters),
                "first_in_regime": {f"h{h}": summarize(regime1, h) for h in HORIZONS},
                "first_touch": {f"h{h}": summarize(firsts, h) for h in HORIZONS},
                "later_touch": {f"h{h}": summarize(laters, h) for h in HORIZONS},
                "unconditional_median_fwd_pct": {
                    f"h{h}": round(statistics.median(uncond[h]), 2) if uncond[h] else None
                    for h in HORIZONS},
                "per_symbol_h63": per_sym,
            }

    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    base = result["variants"]["sma_run15"]
    print("n_regime1", base["n_first_in_regime"],
          "n_first", base["n_first"], "n_later", base["n_later"])
    print("reg1st:", json.dumps(base["first_in_regime"]["h63"], ensure_ascii=False))
    print("first :", json.dumps(base["first_touch"]["h63"], ensure_ascii=False))
    print("later :", json.dumps(base["later_touch"]["h63"], ensure_ascii=False))
    print("uncond:", base["unconditional_median_fwd_pct"])
    for s in NAMED:
        print(s, json.dumps(base["per_symbol_h63"][s], ensure_ascii=False))


if __name__ == "__main__":
    main()
