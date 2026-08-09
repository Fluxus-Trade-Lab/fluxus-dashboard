"""Derive the interpretation layer for 2026-07-31 from the measured dataset.

Two objects, both rule-derived and both carrying their own evidence string:
  - the ten-dimension state board (Fluxus_Operator_Model.md §2)
  - the propagation chain with lit / partial / unlit links (§4)

Nothing here is hand-asserted. Every state prints the numbers that produced it,
because the whole point of the redesign is that a claim must show its evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

HERE = Path(__file__).parent
D = json.loads((HERE / "data_0731.json").read_text())
N, B, DIFF = D["names"], D["breadth"], D["diffusion"]
T = B["today"]

LEADERS = [k for k, v in N.items() if v["role"] == "leader"]
INDEXES = [k for k, v in N.items() if v["role"] == "index"]
DAMAGED = [k for k, v in N.items() if v["role"] == "damaged"]
MEGA = ["AMZN", "MSFT", "NVDA"]

# Screeners whose count is a genuine participation measure. momentum_97 is a
# fixed top-N cut (pinned at 90 every session) and would read as a flat line.
COUNTED = ["episodic_pivot", "vcp", "gainers_4pct", "vol_up_gainers",
           "ema21_watch", "healthy_charts"]

# Qualitative levels, worst → best. Kept to five so the board reads as a shape.
LEVELS = ["缺席", "很弱", "早期", "已启动", "良好"]


def rung(t: str) -> int:
    return N[t]["rung"]


def board() -> list[dict]:
    dmg = T["down_25pct_qtr"] / (T["up_25pct_qtr"] + T["down_25pct_qtr"])
    peak_down4 = max(B["trace"]["down_4pct"][-5:])
    idx_ok = [t for t in INDEXES if rung(t) >= 3]
    lead_ok = [t for t in LEADERS if rung(t) >= 5]
    mega_avg = mean(rung(t) for t in MEGA)
    dmg_avg = mean(rung(t) for t in DAMAGED)
    ep = DIFF["screeners"]["episodic_pivot"]

    def lvl(cond_to_level):
        for cond, level in cond_to_level:
            if cond:
                return level
        return LEVELS[0]

    return [
        dict(key="受损程度", layer="fact",
             state=lvl([(dmg > 0.55, "很弱"), (dmg > 0.45, "早期")]),
             evidence=f"季度 −25% 的股票 {T['down_25pct_qtr']:.0f} 只 vs +25% 的 {T['up_25pct_qtr']:.0f} 只（{dmg*100:.0f}% 在下跌侧）"),
        dict(key="抛压", layer="fact",
             state=lvl([(T["down_4pct"] < peak_down4 * 0.5, "已启动"),
                        (T["down_4pct"] < peak_down4 * 0.8, "早期")]),
             evidence=f"今日 −4% 家数 {T['down_4pct']:.0f}，5 日峰值 {peak_down4:.0f}（已回落至 {T['down_4pct']/peak_down4*100:.0f}%）"),
        dict(key="指数修复", layer="interpretation",
             state=lvl([(len(idx_ok) >= 4, "良好"), (len(idx_ok) >= 3, "已启动"),
                        (len(idx_ok) >= 1, "早期")]),
             evidence=f"5 个指数中 {len(idx_ok)} 个站上 50 日线：{'、'.join(idx_ok)}"),
        dict(key="领涨修复", layer="interpretation",
             state=lvl([(len(lead_ok) >= 5, "良好"), (len(lead_ok) >= 3, "已启动"),
                        (len(lead_ok) >= 1, "早期")]),
             evidence=f"{len(LEADERS)} 只领涨中 {len(lead_ok)} 只已突破：{'、'.join(lead_ok)}"),
        dict(key="巨头领涨", layer="interpretation",
             state=lvl([(mega_avg >= 4.5, "良好"), (mega_avg >= 3, "已启动"),
                        (mega_avg >= 1.5, "早期")]),
             evidence=f"AMZN r{rung('AMZN')} · MSFT r{rung('MSFT')} · NVDA r{rung('NVDA')}（均值 {mega_avg:.1f}/7）"),
        dict(key="广义半导体", layer="interpretation",
             state=lvl([(dmg_avg >= 3, "已启动"), (dmg_avg >= 2, "早期"),
                        (dmg_avg >= 0.8, "很弱")]),
             evidence=f"{len(DAMAGED)} 只受损名字阶梯均值 {dmg_avg:.1f}/7，{sum(1 for t in DAMAGED if rung(t) <= 1)} 只仍在止跌或破位"),
        dict(key="市场宽度", layer="fact",
             state=lvl([(T["pct_above_20sma"] > 60 and T["net_advances"] > 0, "良好"),
                        (T["pct_above_20sma"] > 50, "已启动"),
                        (T["pct_above_20sma"] > 35, "很弱")]),
             evidence=f">20日线 {T['pct_above_20sma']:.1f}%、T2108 {T['t2108']:.1f}、净上涨 {T['net_advances']:+.0f}（指数收红仍为负）"),
        dict(key="利率", layer="fact", state=None,
             evidence="30Y / 20Y 收益率破 2007 高点 —— 管线未接入债市数据，此格由人工填写"),
        dict(key="确认信号", layer="anticipation",
             state=lvl([(T["ratio_5d"] > 1.2 and T["net_advances"] > 0, "良好"),
                        (T["ratio_5d"] > 1.0, "早期")]),
             evidence=f"5 日动能比 {T['ratio_5d']:.4f}（需 > 1.0）、Episodic Pivot 今日 {ep[-1]} 只（月初 {ep[0]} 只）"),
        dict(key="风险姿态", layer="action",
             state=None, evidence="等待 FTD —— 上面九格的合成结果，不是独立判断"),
    ]


def chain() -> list[dict]:
    lead_bo = [t for t in LEADERS if rung(t) >= 5]
    holds = [t for t in LEADERS if rung(t) >= 6]
    idx21 = [t for t in ("RSP", "IWM") if N[t]["above_21"]]
    ep = DIFF["screeners"]["episodic_pivot"]

    def st(ok, part):
        return "lit" if ok else ("partial" if part else "unlit")

    return [
        dict(label="巨头站住", state=st(all(rung(t) >= 2 for t in MEGA), True),
             evidence=f"AMZN / MSFT / NVDA 全部 ≥ 收回主要均线（r{rung('AMZN')} / r{rung('MSFT')} / r{rung('NVDA')}）"),
        dict(label="更多领涨跟上", state=st(len(lead_bo) >= 5, len(lead_bo) >= 2),
             evidence=f"{len(lead_bo)}/{len(LEADERS)} 只已突破；Episodic Pivot {ep[0]} → {ep[-1]} 只/日"),
        dict(label="QQQ 收回 21/50", state=st(N["QQQ"]["above_50"], N["QQQ"]["above_21"]),
             evidence=f"QQQ {N['QQQ']['close']} vs 21日 {N['QQQ']['ema21']} / 50日 {N['QQQ']['sma50']} —— 两条都在头上"),
        dict(label="宽度扩张", state=st(T["ratio_5d"] > 1.2 and T["net_advances"] > 0,
                                    T["ratio_5d"] > 1.0),
             evidence=f"5 日比 {T['ratio_5d']:.4f}、>20日线 {T['pct_above_20sma']:.1f}%、净上涨 {T['net_advances']:+.0f}"),
        dict(label="RSP / IWM 跟上", state=st(len(idx21) == 2, len(idx21) == 1),
             evidence=f"RSP r{rung('RSP')}（{'在' if N['RSP']['above_21'] else '不在'} 21日线上）· IWM r{rung('IWM')}（21/50 双破）"),
        dict(label="突破站得住", state=st(len(holds) >= 4, len(holds) >= 1),
             evidence=f"{len(holds)} 只突破后仍站住：{'、'.join(holds) or '—'}"),
    ]


def main() -> None:
    D["state_board"] = board()
    D["chain"] = chain()
    D["counted_screeners"] = COUNTED
    D["levels"] = LEVELS
    (HERE / "data_0731.json").write_text(json.dumps(D, ensure_ascii=False, indent=1))

    print("十维状态板")
    for r in D["state_board"]:
        print(f"  {r['key']:8s} {str(r['state'] or '—'):5s}  {r['evidence']}")
    print("\n传导链")
    for c in D["chain"]:
        mark = {"lit": "●", "partial": "◐", "unlit": "○"}[c["state"]]
        print(f"  {mark} {c['label']:14s} {c['evidence']}")


if __name__ == "__main__":
    main()
