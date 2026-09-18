# 自造数字全面复查 · 2026-09-18（DATA ALEX）

Andy 09-18：「我们数据端是否还有其他在自己造的数字，检查后台的数据端，以及显示在前端的数据。之前有做过统计，现在再进行一次检查。」
上一次是 09-04 的字段整改（[`HANDOFF_DATA_field_audit_2026-09-04.md`](../../reference/HANDOFF_DATA_field_audit_2026-09-04.md)），只盘了 `universe.json` 108 个字段、只查了 7 格口径。本次四块全覆盖，每块一个只读 agent，结论经主会话现场抽查。

| 文件 | 范围 | 项目数 |
|---|---|---|
| [A_universe_fields.md](A_universe_fields.md) | `universe.json` 全部 108 字段，与 09-04 逐项对账 | 108 |
| [B_market_layer.md](B_market_layer.md) | 宽度 / 投票 / Board / regime / 交通灯 / 风险模型 / tick | 49 |
| [C_lists_and_tickers.md](C_lists_and_tickers.md) | 面板 / 预设 / 筛子单 / 主题状态 / 个股页 | 55 |
| [D_frontend.md](D_frontend.md) | 前端自己算或写死的数字（不含 portfolio/journal） | 40 |

## 主会话抽查（逐条现场核过）

- ✅ `rel_volume` = 当日量 ÷ **20 日**均量（`yfinance_adapter.py:1039,1205`），页面 tooltip 写「3-month average (Finviz construction)」。
- ✅ `f_score` = EPS/营收增速分位均值（`run_all.py:480`），与 Piotroski F-Score 同名不同物。
- ✅ 个股页「Avg Vol (50D)」实为 20 日；「Dist 20EMA%」实为 `sma20_dist`；「52W High%」未 ×100（NVDA −0.0706 印成 −0.1%）。
- ✅ `state_board.py` thrust 行仍是单日、只看价格的旧规则——两个 agent 独立报出；已修（见 commit）。
- ✅ Stockbee 9M 原文 `v>=8900000`（[2019-09](https://stockbee.blogspot.com/2019/09/simple-scan-that-can-make-you-millions.html)，TC2000 的 `v` 为当日量）；`METRIC_SOURCES.md` 第 60 行「在那里指 maxv65」与此文冲突，待再查他其他帖子后定。
- ⚠️ `ema21_watch` 用 SMA20 近似 21EMA——代码注释已声明是近似，属「已声明的替代」而非隐瞒，但名字仍指 EMA。

## 汇总数（各报告原文）

- **A**：108 字段，自造度量 29，**18 个未登记，其中 12 个在页面上显示**；撞名：`f_score` `rel_volume` `eps_growth_*` `momentum_97`。
- **B**：49 项上页，照抄原文 6，自造已登记 6，**自造未登记 27**，挂标准名未核 10；**与 thrust 同形状 7 个**（5/10 日比值、25%/季、13%/34 天、25%/50%/月、Up/Down 4% 牌面、Board thrust 行）。
- **C**：55 项，照抄原文 3，自造已登记 5，**自造未登记 33**，挂原作者名有偏离 14；**与 thrust 同形状 9 个**（Stockbee 9M、Liquid Leaders、LL Pullback、21EMA Watch、VCP、EP、Pocket Pivot、Anticipation、asset 层 ATR Matrix）。
- **D**：40 项，**双份规则 21**，其中已不一致 7（thrust 牌面 8 天 6 天读反；BreadthTable %>200 上色 33% 与引擎相反；Screener Liquid 闸还是退役的股数规则……），自造未声明 18，与原文不符 8；首页 Regime 条整条是前端自造。
