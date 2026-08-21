# Turin/TRKY 逆向 + 回测方案

*2026-08-20 立。上游拆解见 [turin_trky_study.md](turin_trky_study.md)。数据可得性已实测（本文 §三表）。*
*纪律：算数不荐股（calc engine, not advice）；每个实验先写死 NULL 判据再跑；换池即换答案，全部结论标口径。*
*⭐ **Andy 2026-08-21 定调：不删除、不取消 turin 的任何方法。** 复刻规格永远保持全忠实（六条件、全部件照建照跑）；我们的检验判定（PASS/NULL）和发现（交互关系、变换敏感性等）只作为**旁注**贴在旁边。NULL 只作用于一个出口——「进不进我们自己的 correction_risk 表」——不作用于复刻本身。*

---

## 一、核心设计理念（逆向出的六条 + 我们的取舍）

| # | 他的理念 | 证据 | 我们采不采 |
|---|---|---|---|
| 1 | **状态机，不是预测器**——输出 0/1/−1 仓位档，从不输出概率或点位 | TRKY oscillator 规格；全部公开规则皆阈值式 | ✅ 采。与我们 logistic NULL（OOS 输给基准率）互证：这条赛道上概率输出是已证伪的形态，阈值状态没测过 |
| 2 | **因果链定角色**：credit 是因、vol 是果、breadth 是确认 | "vol 是 credit 的兄弟，vol regime 由 credit cycle 驱动"；定版 regime filter 换成 HY credit TR 的 HMA | ⚠️ 当假设测，不当公理。我们 HYG/IEF 特征化失败过，但趋势化用法未测 |
| 3 | **顶底不对称**：顶是过程（自满水平仪：SKEW/PC/VIX TS/防御轮动），底是事件（washout 确认器：z 上穿） | 初版 4 top + 2 bottom 条件的分工；"top period is long, bottom period is short" | ✅ 采为设计原则。我们 correction_risk 目前顶底同一张表，值得拆 |
| 4 | **edge 在错误成本不对称，不在信号准确率**——假信号快速反穿小亏出局，真底一路持有 | 2023-03 thread 的两分支设计；我们复现也验证：cross 日均值无优势（+0.92% vs +1.46%）但三次大底全中 | ✅ 关键认知：**评估他的部件不能只看均值抬升，要看「闸 + 退出结构」的组合**。单看前瞻均值会把它误判成 NULL |
| 5 | **简单部件 + 超长历史**：部件 5 行代码级，回测 60 年，VIX 数据自己算回 1990 | "Notice how simple it is"；1990+ 3m6m 自制表 | ✅ 采。复杂度预算花在数据不花在模型——和我们表切法同路线 |
| 6 | **对齐分档不加权**：绿=全对齐 / 橙=部分对齐，无权重参数 | 初版信号规格 | ✅ 采。无权重=无可过拟合参数，天然过半样本检验 |

**一句话版**：他做的不是「预测回调」，是「用长历史校准的阈值状态机 + 不对称退出，让错误变便宜」。这和 Andy 体系的兼容点在闸（gate）思维，冲突点在他是系统化持仓、我们是自主决策——所以落点只能是 correction_risk 的表切与读数，不是跟单。

## 二、Reverse engineering 方案

### 2.1 已知 / 未知清单

**已锁定（有原话或规格）**：
- R1 washout 确认：cum AD 线 21d z-score 上穿 0；z<0 禁抄底
- R2 regime：Nas cum AD > 100d SMA，或 252d z > −1
- R3 VIX TS：VIX/VIX3M 的 3EMA；<0.8 自满、1.0–1.1 恐慌/投降
- R5 教学策略：smoothed cum AD × 50w MA 穿越
- 部件名单：SKEW、equity P/C、WMT/XLY z、NYSE A/D ratio、R3K %>20dma、52w NHNL、HY credit TR 的 HMA
- turin_LT 条件族：%>MA、Adv/Decl、252d rvol（周线 HA，SPY）

**未知（需标定）**：
- WMT/XLY z 的窗口；SKEW / P/C 的阈值；NHNL 线的平滑（poly reg or EMA，他两个都提过）
- HY credit TR index 的构造（他自制）与 HMA 周期
- 「对齐」的具体逻辑（同日对齐还是 N 日窗口内对齐）；退出规则细节；0/1 oscillator 的映射
- turin_LT 三条件的参数与组合逻辑

### 2.2 Ground truth 三源（标定靠对答案，不靠猜）

1. **历史信号日期**：study 文档 §六的 tweet 清单 + 追加采集他 2022–2026 的带图 call（图里有信号箭头日期）
2. **初版脚本描述**（TLEZspXT）：条件分工与信号分级的规格书
3. **⭐ Forward fixtures：SPXL-V3 每日 plot 即将由 claude bot 自动发在 @bcrossleypy**——建一个每晚采集任务存图+日期，逐日记录「他的状态 vs 我们复刻的状态」。**前瞻对齐不可能过拟合**，这是最干净的标定源，成本几乎为零

### 2.3 标定纪律

- dev episodes：2022 熊市全程 + 2024-08 washout。holdout episodes：2025-03/04、2025-11、2026-03、2026-06→08——**holdout 只许验一次**
- 未知参数逐个网格搜，但**自由参数总数 < fixture 信号数的 1/3**，否则该部件降级为「形状复刻」不做参数宣称
- 每个部件先在 dev 上对齐他的历史图，再冻结参数跑 holdout；对不齐就承认对不齐，写进文档（参照 oratnek 逐格对照的做法：事件探到但选择不同也是结论）

### 2.4 部件复刻顺序（按数据成本排）

| 批次 | 部件 | 数据源 | 历史 |
|---|---|---|---|
| P1（纯 yfinance，零成本，先跑） | SKEW 阈值、WMT/XLY z、VIX/VIX3M 3EMA、252d rvol、%>MA(我们池) | ^SKEW ^VIX ^VIX3M WMT XLY + breadth_archive | 1990+ / 2006+ / 2024+ |
| P2（TV probe 工作流） | NYSE/Nas cum AD 线、NHNL 线、R3K %>20dma 长历史 | TradingView ADD/ADVN/DECN/HIGN/LOWN，走 `pipeline/tools/*_probe.py` 手工粘贴模式 | 视 TV feed，目标 2000+ |
| P3（构造件） | HY credit TR index ≈ HYG adj-close（2007+），HMA 趋势 | HYG（分红再投）| 2007+ |
| P4（可弃项） | equity P/C：CBOE 归档 CSV 只到 2019，之后要另找源 | CBOE archive | 2003–2019，**允许缺席** |

## 三、Backtesting 方案

### 3.1 数据层（2026-08-20 实测）

| 序列 | 源 | 覆盖 | 备注 |
|---|---|---|---|
| ^SKEW | yfinance | **1990→今 (9,151)** | 意外的全历史，P1 主力 |
| ^VIX | yfinance | 1990→今 | 已在 correction_risk 用 |
| ^VIX3M | yfinance | 2006-07→**2026-07-17 停更** | ⚠️ 尾部要用 CBOE CSV 或 ^VIX3M 替代源补；先验证停更是否持续 |
| HYG / IEF | yfinance | 2007+ / 2002+ | auto_adjust=True 即 TR |
| WMT / XLY | yfinance | 1972+ / 1998+ | 轮动 z 可回测 1999+ |
| 我们 breadth 档案 | data/history/breadth_archive.csv | 2024-05→今 (567) | 自选池口径 |
| NYSE A/D、NHNL、TRIN、^CPCE | yfinance | **无** | 缺口=binding constraint；走 P2 的 TV probe |
| **SqueezeMetrics DIX/GEX** | `SqueezeMetrics/DIX.csv`（免费下载口仍活，curl 即刷） | **2011-05→今（日频 price/dix/gex）** | 08-20 从旧 side-project 文件夹重新发现并刷新；white papers + PVGD 文档同目录 |

**SqueezeMetrics 快测（2026-08-20，3,848 sessions）**：GEX/px² 252d 分位五档对 P(≥5% dd/21d) 单调 33.8%→12.0%，半样本 rho [−0.9,−0.6] **方向一致 → 升为 E1 正式候选 ⑤**（正式测必须验对 VIX 五分位的增量——低 gamma 与高 VIX 高度重叠，不给增量就只是 VIX 换皮）。**DIX 同切法 NULL**（不单调、两半不一致，rho −0.1/+0.3）——turin 的 "DIX? Lol" 成立，别再测这种切法。另：SM 的 GEX 聚合序列可当我们 GEX 引擎的外部基准（接 todo_gex_coverage_check 的相关性核对）。

### 3.1b 缺口序列的三层获取策略（2026-08-20 Andy 定调："要么有数据，要么用 backtest 形式模拟"；他的 Google Sheet 不开源，不去追）

| 层 | 序列 | 做法 |
|---|---|---|
| **A 直接有** | SKEW/VIX 1990+ · WMT/XLY 1999+ · HYG 2007+ | yfinance，已验 |
| **B 导出可得** | NYSE/Nas A/D、NHNL 长历史 | TV probe 手工粘贴（ADD/ADVN/DECN/HIGN/LOWN，TV feed 有几十年）；零现金成本，费一次手工时段 |
| **C 合成回填** | VIX3M pre-2006：在 2006+ 重叠段拟合 `VIX3M ~ f(VIX, 21d RV, …)`，回填 1990–2006 · breadth 备胎：等权/市值权比价（RSP/SPY 2003+，更早用 Value Line Geometric）当 A/D 线代理 | **合成三纪律**：① 拟合段留 holdout（如 2015+ 只验不拟）；② 合成列带 provenance 标签（synthetic=true，照期权分析法的惯例）；③ 任何结论必须先在真数据子段单独成立，合成段只做延伸不做证据主体 |

**顺带的清醒剂**：他的 60 年回测和 1.42 Sharpe 也是建立在自制合成数据上的——他的「长历史」护城河其实是「合成方法 + 校准功夫」，不是独家数据源。这个护城河我们完全可以自建，而且建完可以公开方法（BUILD 内容素材）。

### 3.2 实验组（判据先写死）

**E1 · 部件当表切**（接 correction_risk 开放问题 #2，方法照旧：条件基准率表 + 半样本单调 + 非重叠 21d 采样）
- 候选切：① SKEW 五分位（1990+，先跑——最长历史零成本）② WMT/XLY 63d z 三态 ③ VIX/VIX3M 3EMA 三态（0.8/1.0/1.1）④ AD 21d z 正负（先我们池，P2 后换 NYSE 口径重跑）
- **NULL 判据**：半样本 ρ 单调不成立，或全样本极差 < VIX 五分位已给的档差（新切必须带增量信息，不许换汤）
- 输出：每切一行结论进 correction_risk 记忆文件，表数据进 `logistic_appendix()` 同级的研究脚本

**E2 · 规则当闸**（照 B4 两道闸 / sequence mining 的 matched-baseline 方法）
- R1：z21<0 禁买 vs 无闸，比较「买点集合」的 21d/63d 前瞻分布 + **maxDD**（理念 #4：必须带 DD 口径，只比均值会误判）
- R3：三态下的前瞻 vol 与回撤条件分布（它标榜的是 vol 状态不是收益）
- baseline：同月份同波动环境的随机日期对照组
- **NULL 判据**：闸内外分布差 p>0.05，或方向与他宣称相反

**E3 · 策略级复刻 turin_LT**（验自述，不为跟单）
- SPY 周线，2007→今；条件 = %>MA + Adv/Decl + 252d rvol 的组合网格（参数在 dev 窗定，2022+ 当 forward 段对照他 "live since 22'"）
- 对照：SPY B&H 的 CAGR/maxDD/时间在场；他的宣称值（min 14.58% DD since '07）当靶子——**能逼近则自述可信度上调，逼不近也是结论**
- **NULL 判据**：全网格无一组合在 dev 窗同时满足「DD < B&H 一半」且「CAGR ≥ B&H − 1pp」→ 判「宣称不可复现」

### 3.2b E1 正式结果（2026-08-21 跑毕；脚本 `scripts/research/turin_e1_cuts.py`，明细 `data/research/turin_e1_results.json`）

口径 = correction_risk 引擎原函数（y、分位边、半样本 spearman、episode 计数）。判据照 §3.2 预注册。

| 候选 | 判定 | 表（P(≥5%dd/21d)） | 半样本 ρ | 极差 vs 同样本 VIX 档差 | VIX 三分位内方向一致 |
|---|---|---|---|---|---|
| **vixts3** VIX/VIX3M 3EMA（0.8/1.0） | ✅ **PASS** | **5.9% / 17.1% / 32.1%**（n=220/4314/498，2006+，115 episodes） | 1.0 / 1.0 / 1.0 | **26.2pp > 21.2pp——唯一正面击败 VIX 的候选** | 否（见下） |
| **gex5** GEX/px² 252d 滚动分位（预注册版） | ✅ PASS | 21.2%→8.9% 单调（2012+，68 ep） | −1.0 / −0.8 / −0.9 | 12.2pp < 14.7pp | **是**（每个 VIX 档内都成立=真增量） |
| **adz2** 我们池 AD 21d z 正负 | ✅ PASS（⚠短样本） | z≤0: 18.3% vs z>0: 7.9%（2024+，仅 10 ep） | −1.0 全对 | 10.4pp < 20.0pp | **是** |
| skew5 SKEW 五分位 | ❌ NULL | **反向**：高 SKEW 更安全（Q5 12.4% vs Q1 18.8%），极差仅 6.4pp | −0.7（未达 0.9） | 差 | 否 |
| wmtxly3 WMT/XLY 63d z 三态 | ❌ NULL | 只有「防御滞后=安全」一半成立（14.3%），「防御轮动=危险」不成立（20.8%≈中性 21.3%） | 0.5 | 差 | 否 |
| gex5_fullsample（稳健性变体） | ❌ NULL | 全样本切位后二半 ρ 崩到 −0.3——**变换敏感性证据**，趋势序列必须滚动分位 | | | |

**注记：**
1. vixts3 的「方向不一致」是结构性的、不是缺陷：低/中 VIX 档内 backwardation 反而安全（洗盘已发生），高 VIX 档内 backwardation = 35.9% vs 21.4%——**该维度和 VIX 是交互关系，联表使用价值高于独立使用**。非重叠 21d 抽样复核通过（0%/16.9%/33.3%）。⚠ 生产化前置：Yahoo ^VIX3M 停更 2026-07-17，须换源。
2. skew5 反向本身有信息：大众叙事「SKEW 高=崩盘预警」在这个口径下是**反的**——SKEW 高多发生在平静市。turin 拿它当四条件之一的用法未被否证（对齐≠单切），但进不了我们的表。
3. WMT/XLY 同理：作为单切 NULL；他的用法是四条件 confluence。
4. GEX 教训：**同一个量两种切位两个答案**（滚动分位 PASS / 全样本 NULL）——预注册变换救了这次；记入 [[pitfall-same-quantity-three-names]] 家族。

**给 correction_risk 的建议（等 Andy 拍板）**：表从 (VIX 五分位 × 200dma) 扩为 **(VIX × 200dma × VIX-TS 三态)**，GEX 滚动分位作第四读数旁注（数据依赖 SqueezeMetrics 外源）；AD z 等 NYSE 长历史导出后复验再定。

### 3.2c Phase 2 结果（2026-08-21：TV 长历史导出 + 交易所口径复验）

**数据资产已建**：`data/reference/breadth_tv/`（10 个 CSV）——NYSE/Nasdaq 的 ADVN/DECN/ADVQ/DECQ（2007-09+，4,753 根）+ HIGN/LOWN/HIGQ/LOWQ（**2001-06+，6,338 根**）。获取走 `scripts/research/fetch_tv_breadth.py`（tvdatafeed 匿名 websocket，**无需登录无需 Export chart data**，可复跑可进夜跑）。⚠ USI 前缀的「1971 年起」序列是假长——1971 只有一行 0 值、真数据 2003 起、且无 declining 对应序列，已弃用。原设想的浏览器 Export chart data 路线不需要了（Comet 里 TV 未登录，反而逼出了这条更好的路）。

| 候选 | 判定 | 表 | 半样本 ρ | 极差 vs VIX | VIX 档内方向一致 |
|---|---|---|---|---|---|
| **nhnl3** NYSE NHNL 比率 10d EMA（KY 阈值 0.30/0.85） | ✅ **新冠军** | **37.2% / 19.4% / 9.1%**（2001+，146 ep） | −1.0 全对 | **28.0pp > 24.0pp——第二个正面击败 VIX 的候选** | 是（低 VIX 档内 oversold 格子极小样本，档内 spread 虚高，看方向不看幅度） |
| **r2_nas2** turin R2 原文（Nas cumAD>100dSMA 或 252d z>−1） | ✅ PASS | risk-off 24.1% vs risk-on 11.5%（2007+，111 ep） | −1.0 全对 | 12.6pp < 22.0pp | 是 |
| adz2_nyse NYSE cumAD 21d z 正负 | ❌ NULL | 23.0% vs 15.3%——方向对但极差仅 7.7pp，不过预注册的「≥VIX 档差一半」线 | −1.0 全对 | 差 | 否 |

**注记：**
1. adz2 的池间逆转是 [[pitfall-the-universe-chose-the-answer]] 的现场版：我们池 10.4pp → NYSE 口径 7.7pp，方向都对但档差缩水过线。**这不否证 turin 的 R1**——R1 是带退出结构的 timing 确认规则，正确的检验场是 E2 的 matched-baseline，不是表切（且按 Andy 08-21 定调，本判定只是旁注）。
2. r2_nas2 = turin 最爱 regime filter 的**原文逐字复验通过**（19 年、111 episodes）——旁注：作为表切档差不及 VIX，但作为 regime 闸的方向与幅度都真。
3. nhnl3 的三态里 oversold(<0.30)=37.2% 高危读数与 KY 的「oversold=买点」不矛盾：washout 区往往还有下探（我们量的是未来 21 天 5% 回撤概率），底部买点确认要配 R1 类的转向规则——正是 turin「底部条件」和「washout 确认」分成两件事的原因。
4. **E1 最终计分：8 个候选 → 5 PASS**（vixts3 · gex5 · nhnl3 · r2_nas2 · adz2 我们池⚠）/ 4 NULL（skew5 反向 · wmtxly3 · adz2_nyse · gex5 全样本变体）。击败 VIX 本身的两个：**vixts3（26.2pp）与 nhnl3（28.0pp）**。

### 3.2d E2 结果（2026-08-21 跑毕；脚本 `scripts/research/turin_e2_gates.py`，明细 `data/research/turin_e2_results.json`）

**R1 washout 确认闸 = ❌ NULL（这是本轮最有信息量的负结果）。** 2007+ 的 1,584 个 dip 日（≥3% off 60d 高点）、77 个 episode：闸内外的前瞻分布**几乎无差**——fwd21 中位 allowed +2.16% vs forbidden **+2.87%**（方向还反了）；再跌 5% 概率 41.1% vs 43.7%；episode 级 Mann-Whitney 全部 p>0.46。
**机制注脚（旁注，不动他的规则）**：E1 里 z 正负是分得开的（23.0% vs 15.3%）——但**一旦条件在 dip 上，信息就被 dip 本身吸收了**：z<0 的 dip 日买得更深，入场价优势恰好抵消确认的安全性。「等确认」的代价 ≈ 确认的好处。这与 [[project-b4-gates-null]] 同形状。他的原始用法（带快速止损退出的策略入场）未被此测否证——那是 E3 的范畴。

**R3 VIX-TS 三态 = 两条主张一强一弱，按预注册判定记 NULL（复合判据），按内容记「半通过」：**
| 主张 | 结果 |
|---|---|
| backwardation → VIX 一个月内均值回归（short-vol 区） | ✅ **强通过**：ΔVIX 中位 **−18.0%** vs 中性 −1.4%，p≈0；同时左尾仍在——P(VIX 再 +50%) = 11%，约 1/9，他没说的这半句我们补上 |
| complacency → 前瞻 vol 扩张 | 预注册口径（RV 扩张比）方向对但 p=0.44；**事后标注口径（ΔVIX）强支持**：中位 +9.6% vs −1.4%、P(VIX 上行)=76.8% vs 46.8%、p=2e-21（day-level 重叠夸大精度，方向与效应量为准）——弱的是我选的度量，不是他的主张 |

E2 判定小结：R1 NULL（entry-gate 用法），R3 = backwardation 半边成立、complacency 半边度量之争。0.8/1.0 阈值作为**风险状态机**（E1 已 PASS）比作为**买卖时点**更硬——与「不出概率出状态」的理念 #1 自洽。

### 3.2e E3 结果（2026-08-21 跑毕；脚本 `scripts/research/turin_e3_lt_replication.py`，明细 `data/research/turin_e3_results.json`）

**判定：❌ NULL——「outperforms SPX B&H w min 14.58% DD since '07」在我们的网格里不可复现。** 预注册协议：54 组合网格（MMTH>{40/50/60} × AD线{>100d/>200d/R2式} × rvol 分位≤{45/60/75} × {AND/2of3}），dev 窗 2008-09→2021-12 选、forward 2022+ 只验幸存者；判线 = DD 好于 B&H 一半 **且** CAGR ≥ B&H−1pp。两种标的读法都跑了：

| 标的读法 | 结果 | 最接近的组合 |
|---|---|---|
| SPY 现货（周线信号，现金 0%） | **0/54** | DD 可压到 **−8.7%**（比他宣称的 −14.58% 还低！）但 CAGR 只剩 2–5%（B&H 12.8%）——**DD 保护买得到，代价是收益** |
| SPXL 3x（置顶原话 "long only LETF port"，真实基金数据） | **0/54** | 最优 12.89% CAGR ≈ B&H 12.80%、tim 37%，但 DD −25.3% 超判线 4pp、超他宣称 10.7pp |

forward 窗一次都没动用（无幸存者）。

**公平性注记（旁注，不作数于判定）：**
1. 窗口错位：数据迫使我们从 2008-09 起跑，无法含 2007 顶——他的 "since 07" 含躲过 2007-10 建仓顶的功劳，对择时策略有利；
2. 现金按 0% 计：按 T-bill 计可给 SPXL 最优组合加约 +2.5pp CAGR（过 CAGR 线），**但 DD 线仍然不过**——判定不翻转；
3. 网格是我们对他三条件推文的解读；他的完整周线脚本还有 VIX TS/WVF/HMA/credit 部件（release notes），tweet 只报了三条件。
4. **Andy 注（08-21，终审口径）**：他实际用 SPXL/TQQQ/SOXL 按一定配比组合，且 timing 模型细节未公开——**业绩宣称定为「无法确认」**（不是「有水分」）：标的配比 + timing 两个自由度都不在我们手里，复现本就不可能闭合。E3 到此终结，不再追。
5. 补扫佐证（08-21 fixtures 补扫）：他 2026-08-21 自述 LT 策略节奏为「**3-6 trades/year**」——我们网格是周频信号（幸存 DD 组合年换手 ≫6），节奏差一个量级，进一步支持「无法确认≠不成立」的终审口径；另有 2024-03 业绩自述 $55k→$3.5M/6年（含义与 1.42 Sharpe 同级，无审计）。

**E1/E2/E3 全系列完成。** 总图景：turin 的东西**当风险状态机全部成立**（E1：5/8 PASS，两个击败 VIX），**当买卖时点全部软**（E2 R1 NULL、E3 业绩宣称不可复现）。这恰好是他自己理念 #1「不出概率出状态」的镜像——他的公开部件里真正值钱的是 regime 层，不是 timing 层。剩余待做：Phase 0 的 SPXL-V3 bot 每日 plot 采集（等他开播）+ credit HMA 趋势化测试（E1 未竟项）。

### 3.3 执行顺序与工作量

1. **Phase 0**（半晚）：VIX3M 尾部补源验证；SPXL-V3 每日 plot 采集任务上线（等他 bot 开播）
2. **Phase 1**（1 晚）：P1 部件 + E1 的 ①②③——全部 yfinance，脚本一个：`scripts/research/turin_e1_cuts.py`（复用 correction_risk 的表框架）
3. **Phase 2**（1–2 晚 + 手工 probe 时段）：TV 导出 A/D、NHNL 长历史 → E1-④ NYSE 口径 + E2
4. **Phase 3**（1 晚）：E3 策略复刻
5. **汇报门**：每 Phase 出一节追加进本文档；**是否有任何东西接进 correction_risk 的表甚至前端，等 Andy 拍板**——该项目仍是 parked 状态

### 3.4 风险清单

- **口径风险**（最大）：我们池 ≠ NYSE/R3K；E1-④ 必须两口径都跑，只报一致的部分
- **VIX3M 停更**：若 Yahoo 长期不修，CBOE CSV 只有 2009-09+，1990 回测段需照他的 3m6m 自制思路补，工作量另计
- **P/C 缺席**：初版 4 顶条件我们最多复刻 3 个——对齐率上限要预先下调，别把数据缺口读成模型分歧
- **他的自述无审计**：E3 的靶子（14.58% DD、1.42 Sharpe）可能本身是曲线拟合产物；复刻失败 ≠ 我们错
