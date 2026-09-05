# Jeff Sun 的扫描清单 · 我们自己做一份 + 盘清我们现在的 scanner 在做什么

**2026-09-05 · DATA ALEX · 规划稿（Andy：「做好了详细规划就停下来告诉我」）**

先读了已有规划再动笔：`scanner_validation_2026-08/`（08-18 起每把刀 A–E 五段验刀，已有 13 把的判词）、
`screener_competitors_2026-08-17.md`（四家口径拆解）、`JeffSun_Wiki/wiki/screener-overview.md`（他的 14 个后市扫描 + 2 个盘中）。
这份是**对账表 + 下一步**，不是平行方案。

## 〇、今天已经落地的（阶段 0）

| 件 | 在哪 |
|---|---|
| Jeff 的 **13 个 TradingView 扫描**（Colab 逐字）+ **7 个 Finviz 扫描**（他原推里的 URL 逐字解码）编成数据 | `pipeline/screeners/jeff_sun.py` · `TV_SCANS` / `FINVIZ_SCANS` |
| 能真跑：`python -m pipeline.screeners.jeff_sun --tv`（venv 里装了 `tradingview-screener`，**不是管线依赖、不在 cron**） | 今天 13 个扫描的真实命中 → `tv_hits_20260905.json` |
| **诚实的本地部分复刻** `local_mask()`：只套我们池子能表达的子句，**返回跳过了哪些** | 9 条测试钉住「逐字」与「跳过要报」 |
| TradingView 字段语义用数据钉死（不是读文档猜） | 见 §一 |

## 一、先把尺子对齐：TradingView / Finviz 的字段到底是什么

10 支票实测（yfinance 未复权 bar）：

| TV 字段 | 实测 = | 比值中位 | 对应我们 |
|---|---|---|---|
| `Volatility.M` | **mean(H/L − 1) × 100，约 21 根** | 1.011 | **= 我们 09-04 起的 `adr_pct`**（20 根）✅ |
| `Volatility.W` | 同上，5 根 | 1.000 | 无（可算） |
| `average_volume_60d_calc` | 60 日均量 | 1.000 | 我们 `avg_volume` 是 **20 日**，Finviz 的是 **3 个月** —— 三把不同尺子 |
| `gap` | open/prev_close − 1 × 100 | 精确 | 无（可算） |
| `relative_volume_10d_calc` | 今量 / 10 日均 | ≈1.0 | 我们 `rel_volume` 是 Finviz 的 **3 个月** |

Finviz 帮助页原文：Volatility = "average daily high/low % range"（= ADR%）；Average Volume = 3-month；Relative Volume = today / 3-month。
**所以 Jeff 的 `ta_volatility_mo5` 就是「月 ADR% > 5」**——和我们刚修好的 ADR 口径同源。

## 二、对账：Jeff 的 14 个扫描 ↔ 我们的 24 个模块 / 20 个面板

| # | Jeff 的扫描 | 他的定义（一手） | 我们最接近的 | 差在哪 | 档 |
|---|---|---|---|---|---|
| 1 | CANSLIM-inspired | EPS & 营收 YoY >25%（季度）、FCF >25%、float <100M、60d 量 >300K、只挂 50MA、月波动 3% 去掉并购股 | **无**（`f_score` 是百分位不是闸） | 我们没有 float、FCF、季度 EPS yoy | 缺 |
| 2 | High ADR% Hottest Stock | 过去一月大动 + 过去一周收缩（TV v2，参数未公开数值） | ADR 3.5–10 闸 + `wk_band_3`/VCS | 我们有零件没有这把刀 | 缺 |
| 3 | KC Extended Base（Cup & Handle） | Finviz 2025 版，长期整理 | `vcp_detector`（自造收缩计数）、`vcs`（oratnek 移植） | 形态不同源 | T3/T1 |
| 4 | **Strongest Mover 1W/1M/3M/6M** | 1W >20% / 1M >30%（强市 50%）/ 3M >50% / 6M >100%；小盘 $300M–10B float<50M 月波动>3；大盘 >$10B float<150M；后过滤 52w 低点 ×1.5、SMA10 在 close 的 80–90% 内 | `weekly_20_gainers`（5 根 ≥20%）、`momentum_97`（四窗口等权前 3%） | 我们没有 float/波动/SMA10 闸；Momentum 97 是**排名**他是**绝对阈值** | T2 |
| 5 | IPO（周） | Finviz：cap mid+、EPS yoy 正、**上市 ≤1 年**、均量 >1M | **无** | 没有 IPO 日期字段 | 缺 |
| 6 | High Short Float（周） | cap small+、均量 >1M、float <100M、**short float >30%** | **无** | 没有 short float 字段 | 缺 |
| 7 | Liquid ETF | ETF、均量 >1M、周波动 >3 | `asset_signals`（无来源标注） | 口径未对 | T3 |
| 8 | Watchlist Scan / Daily Tightness | **收盘在 5-EMA 的 ±5%（Colab 版 97%）**、SMA10 > SMA20、周涨 <5%、月波动 >3.5 | `three_weeks_tight`（IBD）、`wk_band_3`、VCS | 他是**日线对 5-EMA 的贴合**，我们是周线/压缩分 | 缺 |
| 9 | Liquid Mega Cap 固定名单 | >$1B 日均美元成交额 + 对应杠杆 ETF | `liquid_leader`（$2M 股量 + >SMA50 + rs_3m≥80） | 他是资格名单我们是信号；量级差 500× | T2 |
| 14 | Julian Komar Strongest Stock | 小盘：$300M–10B、60d 量 >500K、月波动 >3、float <50M、EPS/营收 >25%、>SMA50；后过滤 52w 低 ×1.7、SMA10 在 90% 内 | **无** | 同 #1 缺字段 | 缺 |
| — | Post-Earnings Cont Base（Colab） | gap >5%、rvol10 ≥2、>SMA20、float <50M、cap >$50M | `episodic_pivot`（gap ≥10%、rvol ≥3、cap ≥$500M） | 我们更严更晚；他要的是**财报后延续基底** | T2 |
| — | 2 个盘中 RVOL 扫描 | Focus list × RVOL、盘前 gapper × RVOL | 无盘中 | 不在夜间管线范围 | — |

**我们有、他没有的**（都是入场触发不是候选池）：LL-HL 三格（oratnek，T1 移植）、MA Reclaim、PP 三格、Stop Hit / LL Break、Extended ≥7 ATR（Jacobs）、anticipation（Stockbee）。

**我们 12 个老模块里 6 个没有来源标注**：`vol_up_gainers` `episodic_pivot` `healthy_charts` `ema21_watch` `ticker_heat` `asset_signals`（`presets.md` 里 A 段给了前四个的口头出处，代码里没写）。

## 三、今天的实测：两套系统在看不同的名字

TV 今日命中（09-05）vs 我们 09-04 收盘的面板（日期差一天，看的是重合结构不是精确对账）：

| | |
|---|---|
| Jeff 13 扫描去重 | **122 支**，100% 在我们 universe，87 支 tradeable |
| 出现在我们任一面板 | **20 支** |
| 我们 20 面板去重 | 239 支，出现在 Jeff 任一扫描 **20 支** |
| 重合最多的面板 | `extended`（他的 mover 常已 ≥7 ATR）、`morales_pp_10d`、`anticipation`（Daily_Tightness 与我们的安静日闸同向） |

**读法**：不是 bug。他的是**基本面 + float + 多周期动量的候选池**，我们的是**技术事件触发器**。Jeff 自己说「Screening only builds a generic watchlist」——这正好和 08-18 验刀的结论对上：我们的入场刀里只有 LL-HL / vcp 有边，候选池类（Weekly 97 / Liquid Leaders）单独无边。**两者是上下游，不是竞品。**

**本地复刻测过了，不行**：13 个扫描合计 TV 真命中 167，本地能表达的子句留下 4,140 → recall 0.79、**precision 0.032**（宽 25 倍）。差距全在我们没有的列：**float、FCF 增速、季度 EPS yoy、60 日均量、10 日相对量、gap、SMA10、EMA5、short float、IPO 日期**。

## 四、下一步规划（等 Andy 点头再动）

### 阶段 1 · 补数据（2 天）— 三选一，我建议 A
| 方案 | 做法 | 优 | 劣 |
|---|---|---|---|
| **A · TradingView 扫描 API 夜间跑**（建议） | 每晚跑 13 个扫描（他的平台、逐字），落 `data/output/jeff_scans.json` + 归档 `data/history/jeff_scan_hits.csv`；顺手把 float / FCF / 60d 量 / SMA10 / EMA5 存进 universe 对应票 | **T1 逐字**、字段全、今天已跑通、免费无登录 | 非官方接口（`tradingview-screener` 是社区库），有失效/限流风险；要加 `tradingview-screener` 进 requirements 并接 `yahoo_budget` 式的退避 |
| B · Finviz 补列 | 我们已用 Finviz 导出（v=152），再拉 v=131（Ownership：Float、Short Float、Insider）与 IPO Date 列 | 同一供应商、进 universe 所有票都有 | Finviz 的 3 月均量/ADR 与 TV 的 60 日/21 日**不是一把尺子**，复刻 TV 版还是差 |
| C · 自算 | 从日线算 SMA10/EMA5/gap/60d 量/rel_vol_10d（都能算）；float/short/IPO/FCF 没有源 | 零依赖 | 只能补一半，Jeff 的核心闸（float、基本面增速）还是缺 |

A + B 的子集（B 只取 float / short float / IPO date 三列）是最完整的组合。

### 阶段 2 · 上页（2 天，MVP：两周内 Today's Watchlist 多一个区）
- Today's Watchlist 新增 **「Jeff 的候选池」zone**：Strongest Mover ×4（小盘）、Strongest Stock JK、Fundamental Growth、Daily Tightness —— 每格标 **T1 · 原文链接**，数字旁写「TradingView 21 日 ADR%」等口径注。
- **不**把他的扫描改成我们的口径去凑；也**不**把我们的面板改成他的。两套并排。

### 阶段 3 · 研究（预注册 1 天 + 前瞻 4 周）— 这才是「研究」的主体
按 `RESEARCH_PROTOCOL.md` 先封存再算：
- **假设**：Jeff 候选池 × 我们的入场触发（LL-HL 1st/2nd、MA Reclaim）在 10/20 日的表现 **优于** 触发单独（08-18 已测：触发单独 LL-HL +2.75%/20d，候选池类单独 ≈0 或负）。
- **度量**：20 日收益中位 vs 同日同池随机基线；MAE 中位；胜率。**先算最小可检 p**（触发 × 池交集一天只有几支，四周可能不够——不够就说不够）。
- **holdout**：从今晚起的前瞻账本，不回填（回填的候选池会有幸存者偏差：TV 只返回今天还活着的票）。
- **阴性对照**：随机候选池 × 同样触发。
- **判据**：交集不优于触发单独 → Jeff 池对我们无增量，只当「阅读用」不做闸；优于 → 进入场闸的前置条件。

### 阶段 4 · 口径与清场（1 天）
- 20 个 Jeff 扫描登记进 `METRIC_SOURCES.md`（T1）与 `CANON_LIBRARY.md`（一手：Colab + 原推 URL）。
- 我们 6 个无来源标注的模块：代码注释补 A 段出处（`presets.md` 里已有四个），补不出的标 T3。
- 近重复判去留：`weekly_20_gainers`（5 根 ≥20%，无 cap/float/波动闸）vs `Mom_1W_Small`——**建议保留我们的、标自造**，他的并排上页；`momentum_97`（排名）vs Strongest Mover（绝对阈值）——两个问题，都留。

## 五、要 Andy 定的三件

1. **阶段 1 选 A / B / A+B子集**（我建议 A+B 子集）。A 意味着夜间多一个非官方接口依赖——这是我不该自己拍的。
2. **Jeff 的面板放哪**：Today's Watchlist 新 zone（建议）/ 独立页 / 只进研究不上页。
3. **6 个无来源模块**：要不要趁这次退役其中确认无边的（08-18 判词：`vol_up_gainers` ❌、`ema21_watch` ❌ 接刀、`healthy_charts` ≈ 无边无害）。

## 六、边界（老实话）
- 今天的 122 vs 239 重合是**一天**的读数，且 TV 是盘中/最新、我们是前一收盘。结构性结论（候选池 vs 触发器）稳，数字会变。
- Colab 是**别人**对 Jeff 扫描的复刻，我逐字抄的是他的代码不是 Jeff 的 TV 配置本体；Jeff 2025-10 在 TV 开了 Screen Sharing 链接，**拿到那个链接才是真一手**。Finviz 那 7 条是 Jeff 本人的 URL，是一手。
- `local_mask` 的 recall 0.79 说明我们池子**不缺票**，缺的是**闸的列**——补列比换池便宜。
