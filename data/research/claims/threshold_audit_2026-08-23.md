# 阈值出处审计（2026-08-23，盘点 agent 产出，回填台账的原料）

审计对象：`pipeline/screeners/` + `pipeline/tools/` 全部硬编码阈值。
三分类：第三方定义（照抄公开定义）/ 我们测出来的（注释指向自家研究）/ 没有出处（魔法数字）。

## 最重要的三条观察

1. **`atr_ok: a < 7`（name_cards.py:201-203）是六席里杠杆最大的单个数字，却几乎没有注释。**
   它把 Jacobs 的「减仓区」阈值复用成了全部六席的准入闸；且 `None → 通过`（缺测放行），
   与 first_wave 的 `(atr or 9) <= 4`（缺测淘汰）对「未测量」的处理**相反**。
2. **蓄势席首链（3WT）的证据强度低于注释暗示。** 链条顺序的依据是「VCS 无优势」，
   不是「3WT 有优势」——同一份紧度研究里 3WT 在回踩场景 n=30、胜率 26.7%、edge −12.7（样本太小）；
   且 3WT 的正确用法是突破日加仓，不是回踩雷达。
3. **`tightness_grid.py` 的交易框（+2R/−1.5R/20日）没有出处，但所有紧度结论都建在它上面**，
   包括 08-20 换蓄势席链条的拍板。上游魔法数字污染下游研究结论的典型位置。

## 没有出处的阈值（节选，高杠杆优先）

| 阈值 | 位置 | 控制什么 |
|---|---|---|
| `atr_ok: a<7` | name_cards.py:201 | 六席全局准入闸 |
| `first_wave (atr or 9)<=4` | name_cards.py:264 | 入场席第二链（or 9 缺测默认值纯魔法）|
| `fresh_high_pullback −20%..−3% / 60日 / −15%回退` | name_cards.py:286-289 | V反席首链 |
| `deep: high_52w<=-0.25` | name_cards.py:291 | V反席第二链 |
| `coil: range5<=5 ∧ dist_hi20>=-3` | name_cards.py:313 | 蓄势席第二链（研究自认「拍的操作化」）|
| `3wt 附加闸 high_52w>=-0.15` | name_cards.py:312 | 蓄势席首链 |
| `asset: rs_line_pctl_21>=100` | name_cards.py:327 | 资产席首链 |
| `heat[:50]` | name_cards.py:250 | 燃烧席候选池边界 |
| `CONFLUENCE_BONUS=2.0` | ticker_heat.py:61 | heat 加分幅度（MIN=4 有测量，2.0 没有）|
| `WEIGHTS 3/3/3/1/1/1/1` | ticker_heat.py:35 | heat 权重 |
| `FRAME 2R/−1.5R/20d` | tightness_grid.py:43 | 全部紧度结论的胜负定义 |
| `LEG_PCT/LEG_H/PRE,POST` | leader_footprint.py:31 | 验刀报告的「腿」与命中窗口 |
| ATR 文案分档 `<0/<=4/<7/>=7` | name_cards.py:99 | 与 run_all.py 的 Jacobs 分档存在 4–5 口径差 |

## 有测量出处的（回填时登记为 candidate 或 null）

- `CONFLUENCE_MIN=4`（ticker_events 档案计数）· `CHASE_PCT=0.15`（验刀最差格 −9.3%/36%）
- `TOP_3M_PCTILE=0.85`（oratnek 三天拟合 5.9×→2.5×，保 108/112）
- `MIN_DOLLAR_VOL=2e7`（CBRL 举例论证 + Andy 拍板，非回测）
- `thrust 0.113`（558 session 重放，翻转 3.4%）· `regime BANDS 47/63/75`（558 session 经验四分位 + 前瞻回撤频率单调）
- `ma_reclaim 删量闸`（MU/MRNA 具体案例）· `vcs 格 rs_3m>=80 组合`（oratnek 快照对照）

## 第三方定义（低风险，判据在外部）

VCS 全套常数（oratnek Pine 逐行 port + 黄金对照）· Structure Pivot Fib（脚本默认值）·
EP 10%/3×（Stockbee）· liquid_leader（课程 M2_L09）· 4% B/D、T2108、McClellan（公开阈值）·
ATR Matrix 0-4/5-7/>=7（Jacobs）· 3WT 1.5% 周带（O'Neil）· VCP 收缩比（Minervini，但 window=5 等操作化参数是我们的）

完整表格见盘点 agent 原始输出（本文件为人工节选）。回填截止 2026-08-26（RESEARCH_PROTOCOL §七）。
