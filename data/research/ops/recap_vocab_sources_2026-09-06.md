# 复盘用词的口径溯源（2026-09-06）

**这是给 `data/reference/METRIC_SOURCES.md` 的候选行，未落表、未 commit 进登记表本体，等 Andy 批。**

起因：每日复盘稿在用一批带方法论出身的词（climax top / follow-through day / distribution day /
stage 2 / VCP / power trend …），它们**听起来像标准读数**。按宪法 08-31 条，动手算之前先查有没有专业口径。
本轮 9 个词条、11 行候选。

引用顺序按 `CANON_LIBRARY.md`：**本机一手 → 发明者/官方网页 → 社区复刻**。

> ⚠️ **本轮的一手来源盘点更新**：`CANON_LIBRARY.md` 的「没有（查过）」一节说
> 「Stan Weinstein《Secrets for Profiting in Bull and Bear Markets》原书——本机无；阶段口径只有 TraderLion 转述」。
> **这条已经过期**：原书 2026-09-05 14:53 落到
> `~/Documents/Trading/03_Trading_Strategies/Books_References/stan-weinstein-s-secrets-for-profiting-in-bull-and-bear-markpdf_compress.pdf`，
> 有完整文字层（`pdftotext -layout` 出 12,418 行）。下面 stage 那行引的是**原书**，不再是转述。
> 建议一并修 `CANON_LIBRARY.md`（不在本文件范围内）。

---

## 1. climax top / exhaustion gap

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| —（拟 `climax_signs`） | O'Neil **Climax Top / Climax Run** | 长期上涨（典型 ≥18 周）之后加速的 1–2 周终段，同时看七个征兆：①**exhaustion gap**（跳空高开于昨日高点之上，重量）②**该轮最大单日涨幅** ③**该轮最大单日成交量** ④连续 7–8 个上涨日（或 10 日中 8 日涨）⑤**该轮最大周振幅**（周高−周低大于本轮起点以来任何一周）⑥价格刺穿上轨通道线（该线由 4–5 个月内 ≥3 个高点连成）⑦距 200 日均线 +70~100% 以上 | 🔲 **我们没有**。七条里只有第 ⑦ 条现成（`sma200_dist`）；①②③⑤⑥ 需要「本轮上涨起点」这个锚，而我们**没有任何字段定义"本轮"** |

**出处**：IBD《Beware Of Climax-Run Signals After Long, Spectacular Runs》
（[Yahoo Finance 转载全文](https://finance.yahoo.com/news/beware-climax-run-signals-long-225300520.html)；investors.com 本体对我们的 UA 封锁，转载版是同一篇）。
七条与 QCOM 1999-12 实例（连续 7 日、+251% over 200MA、到 2000-01-28 腰斩）均出自该文。
**exhaustion gap 本身的谱系更老**：Edwards & Magee《Technical Analysis of Stock Trends》的三分类
breakaway / runaway(measuring) / exhaustion，见 [LuxAlgo 概念页](https://www.luxalgo.com/library/concept/exhaustion-gap/)、
[Wikipedia Gap (chart pattern)](https://en.wikipedia.org/wiki/Gap_(chart_pattern))。
⚠️ 一手未见：**本机无 O'Neil 原书、无 Edwards & Magee**，两处都是二手。

**能不能算**：❌ 现状不能，缺的不是数据是**锚**。
- 有：`universe.json` 的 `sma200_dist`（第⑦条）；`data/output/tickers/<T>.json` 的 `ohlc_2y`（502 根 open/high/low/close/volume，够算①②③④⑤）。
- 缺一：`ohlc_2y` **只覆盖 217 支**（`ls data/output/tickers | wc -l` = 217），5630 支的 `universe.json` 没有任何逐根 bar。
- 缺二（真缺口）：①②③⑤ 全部是**「自本轮上涨开始以来的最大」**，需要先定义"本轮起点"。仓库里没有这个量，
  最接近的 `days_since_52wh` 是"距 52 周高多少天"，方向反了。**这个锚不定义，七条里五条无法判真假**。

---

## 2. follow-through day

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| —（拟 `ftd`） | O'Neil / IBD **Follow-Through Day** | 前置：指数创新低后出现 **rally attempt 第 1 天**（当日收盘高于开盘 / 高于前收，或小跌但收在当日区间上半部）；随后 2、3 日**不得跌破第 1 天的低点**，跌破则重新计数。**第 4 天或以后**（最佳 4–7 天，最迟约 10 天）某大盘指数**收涨 ≥1.25%**（IBD 现代口径抬到 **≥1.7%**，2% 更好）**且成交量高于前一交易日**——成交量只需高于前一日，不要求高于均量 | 🔲 **我们没有**，且**指数成交量在 `data/output/` 里根本不存在** |

**出处**：MarketSmith（IBD 自家产品）香港站
[Follow-Through Day](https://www.marketsmith.hk/follow-through-day/?lang=en)——原话「closing up 1.7% plus, preferably 2% plus,
on volume greater than the prior day on the fourth day or later of a rally attempt」。
1.25% 的原始口径与 4–7 天最佳窗口见 [TraderLion](https://traderlion.com/trading-strategies/follow-through-day/)（页面对 WebFetch 返 403，标题与摘要来自检索结果）
与 [QuantifiedStrategies](https://www.quantifiedstrategies.com/follow-through-day/)。
rally attempt 第 1 天的判定见 [Trade That Swing](https://tradethatswing.com/when-to-buy-stocks-after-a-stock-market-correction/) 与
[aistockselection 术语页](https://www.aistockselection.com/en/glossary/follow-through-day)。
本机一手：**无**。TraderLion Ultimate Trading Guide 只在 p.84 把 FTD 当既知前提用了一次
（"Assumption: Follow-through day just occurred"），**全书没有定义它** — `traderlion.txt:1738`。
Mike Webster 的 21EMA 播客里同样只是提及（`webster_21ema_wro9_GxQpyUfZv4U.txt:9`：
"there was this thing called distribution days and follow through days but I didn't understand them"）。

**能不能算**：❌ 不能。**指数日线成交量在 `data/output/` 里没有任何字段**。
- `data/output/signals.json` 给 SPY/QQQ/IWM/RSP/^GSPC 的是**当日快照**：`close` `ema8` `ema21` `sma20/50/200`，**无 volume、无历史**。
- `data/output/tickers/` 的 217 支**不含 SPY/QQQ/IWM/RSP**（已核）。
- `data/output/breadth.json` 的 `history` 只有 `dates` / `pct_above_20/50/200sma` / `mcclellan_osc`，加一个 `spx_close`——**无量**。
- `data/history/asset_signals.csv` 有 SPY 行的 `close` `change_pct` `rel_volume`，但 ①只有 **12 个交易日**（2026-08-19 ~ 09-03）
  ②`rel_volume` 按 `pipeline/screeners/volume_enrichment.py:6` 是**今日 ÷ 三个月均量**（Finviz 口径），
  不是「今日 vs 昨日」。用 `rel_volume_t / rel_volume_{t-1}` 反推是**近似**（分母的三月均量在动），**不是标准口径**，不该冒充。

---

## 3. distribution day

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| —（拟 `dist_day` / `dist_count_25`） | IBD **Distribution Day** | 某大盘指数（Nasdaq Composite 或 S&P 500）**收跌 >0.2%** **且当日成交量高于前一交易日**（同样只要求高于前一日，不要求高于均量）。计数看**滚动 25 个交易日**窗口；一天在下列任一条件下出列：已过 25 个交易日，或指数自该日收盘起**涨 ≥5%**。**4–5 天 = Under Pressure，6 天以上通常先于回调** | 🔲 **我们没有**；缺的字段与 FTD 同一个（指数日量） |

**出处**：[Bulkowski, thepatternsite.com — Distribution Days](https://www.thepatternsite.com/DistributionDay.html)
（0.2% 门槛、higher volume、"5 or 6 distribution days over a period of about four weeks"）；
25 个交易日窗口与两条出列规则见 [aistockselection 计数说明](https://www.aistockselection.com/en/articles/how-to-count-distribution-days)。
本机一手：**无**。TraderLion Guide p.102 有「Signs of Distribution」一节，但那是**定性清单**
（大量收在低点、跳空低开、失败突破、跌破关键均线、"pay special attention to clusters of distribution days"），
**没有 0.2% 也没有量的条件** — `traderlion.txt:2238`。

> ⚠️ **值得单独拎给 Andy 的一条**：Bulkowski 对这个指标做过实证，结论是**否定的**——
> 568 支股票（2005–2010）与 S&P 500（1950–2010）上，distribution day 成簇**只在价格已经处于下跌趋势时**
> 才预示下跌，**在上涨趋势里预测顶部的表现很差**，与 IBD 的用法相反。
> 也就是说：这个词有清清楚楚的标准口径，但**标准口径的有效性有公开的反面证据**。
> 上页之前应当自己在我们的历史上重做一遍，别把"有口径"当成"有信号"。

**能不能算**：❌ 不能，同 §2。%跌幅那一半有（`asset_signals.csv` 的 `change_pct`，但只有 12 天），
量那一半没有。5% 出列规则还需要指数收盘序列——`breadth.json` 的 `spx_close` 只有当日一个值，
`history` 里没有 spx_close 序列（已核 `history` 的键只有 dates / 三个 pct_above / mcclellan_osc）。

---

## 4. swing failure

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| —（拟 `sfp`） | **查过，无单一权威**。现代通用名 Swing Failure Pattern (SFP) | 通行描述：一根 K 线的**影线**穿越前一个 swing high / swing low，**收盘回到该极值之内**。Wyckoff 谱系里的对应物是有阶段前提的 **Upthrust After Distribution (UTAD)** 与 **Spring / Shakeout**；SFP 是把同一机制**剥掉阶段前提**推广到任意 swing 极值 | ⚠️ **不得当作标准读数**。同一形状在四套体系里叫四个名字（Wyckoff upthrust / Wilder failure swing / SFP / SMC 的 liquidity sweep），**没有一套给出可判定的数值门槛** |

**出处与溯源结论**：
- **不是 Wyckoff 的**。Wyckoff 的 upthrust/UTAD **要求分布区间与阶段上下文**，SFP 明确取消了这个前提 —
  [LuxAlgo: Upthrust After Distribution](https://www.luxalgo.com/library/concept/upthrust-after-distribution/) ·
  [LuxAlgo: In-Depth Exploration of the Swing Failure Pattern](https://www.luxalgo.com/blog/in-depth-exploration-of-the-swing-failure-pattern/)。
- **也不是 Wilder 的**。Wilder《New Concepts》里的 "failure swing" 是 **RSI 上的**形态，不是价格 swing。
- **"swing failure pattern" 这个名字**目前可追到的最早公开使用是 **Trader Dante 2012 年的一场 webinar**；
  连他自己都说这形态是他研究出来的、不是他发明的（同上 LuxAlgo 溯源文）。
- 本机一手：**无**。本机有 Dante 的转录 `data/research/videos_2026-08/dante_stop_moaning_Vy1_URi88eE.txt`，
  **全文 grep `swing failure` / `failure swing` / `liquidity` 零命中定义**（只有 `:252` 提到 "the last swing high"、
  `:276` 提到 "available liquidity"），**这份转录不能当 SFP 的出处**。

**能不能算**：⚠️ 机械判定本身容易（需要 swing 高低点 + 当日 high/low/close），但**没有可引的门槛**：
影线要穿多深、收盘要收回多少、swing 点用多长的 pivot length，四套说法都没给数。
仓库里已经有一个**能提供 swing 点**的现成件：`pipeline/screeners/structure_pivot.py`（oratnek Advanced Structure Pivot 的逐根移植），
输出 `sp_hl` / `sp_ll` / `sp_1st` / `sp_2nd`。若要做，应当**挂在它的 pivot 上**并**明写门槛是自造的**。

---

## 5. stage 1 / 2 / 3 / 4

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| —（拟 `weinstein_stage`） | Weinstein **Four Stages**（原书 Ch.2） | 以 **30 周均线（30-week MA）的斜率 + 价格相对它的位置**判定：**Stage 1 基地区**＝MA 由跌转**平**，价格在 MA 上下来回、仍在阻力位下方的箱体内；**Stage 2 上升期**＝价格**放量突破阻力区与 30 周 MA**，MA 突破后不久**转升**，此后每次回调都**守在上升的 MA 之上**、峰与谷双双抬高；**Stage 3 顶部区**＝MA 失去上升斜率**转平**，价格开始在 MA **上下反复穿刺**（Stage 2 时回调始终守在 MA 上或之上），放量滞涨（churning）；**Stage 4 下跌期**＝价格**跌破支撑区**、MA **下行**且价格在 MA 之下（**破位不需要放量也成立**，放量更凶） | 🔲 **我们没有**；**30 周均线的值与斜率两个都没发**（见下） |

**出处（本机一手，原书）**：
`~/Documents/Trading/03_Trading_Strategies/Books_References/stan-weinstein-s-secrets-for-profiting-in-bull-and-bear-markpdf_compress.pdf`
（`pdftotext -layout` 后行号）：四阶段命名 `:1313-1314`（"(1) The basing area, (2) the advancing stage, (3) the top area, and (4) the declining stage"）·
Stage 1 `:1327-1377` · Stage 2 `:1381-1420` · Stage 3 `:1482-1536` · Stage 4 `:1564-1600`。
**最可直接落成代码的一段是书里的自测答案** `:1809-1835`，Weinstein 自己把判据压成了两个变量：
「Stage 4. MA declining and stock still below MA.」「Stage 2. MA rising and stock still comfortably above MA.」
「Stage 1. MA flat and stock price still in base area below resistance.」
「Stage 3. MA flat and stock price starting to whip back and forth through MA after big Stage 2 advance.」
均线定义 `:738-751`（30 周＝30 个周收盘的均值）；注意 `:1130-1132` 他实际看的 Mansfield 图用的是**加权** 30 周 MA，不是等权。
**二手对照与一处偏差**：TraderLion Ultimate Trading Guide 转述四阶段时写
「Stan Weinstein uses 3 moving averages: a 50-day/10-week, 150-day/30-week, and a 200-day/40-week」（`traderlion.txt:476-477`）。
**原书不是这么说的**：Weinstein `:738-740` 只给两条——「**30 周 MA 对长期投资者最好，10 周 MA 对交易者最好**」，
**全书的阶段判据自始至终只挂 30 周这一条**，150/200 日那组是 TraderLion 加的。
落地时以原书为准：**判 stage 只用 30 周**。

**能不能算**：❌ 不能，**差一条均线**。
- **没有 150 日 / 30 周均线**：`data/output/tickers/<T>.json` 的 `technicals` 只有 `ma20` `ma50` `ma200`；
  `universe.json` 只有 `sma20_dist` `sma40_dist` `sma50_dist` `sma200_dist` 与周线 `wk_ema10` `wk_ema20`——
  **`sma40_dist` 是 40 日不是 40 周，`wk_ema20` 是 20 周 EMA 不是 30 周 SMA**，都不能替。
- **管线内部其实算过 30 周**：`pipeline/adapters/yfinance_adapter.py` 的 `trend_base` = `close > SMA50 且 10WMA > 30WMA`
  （周线重采样后 `rolling(30).mean()`）。但它只**吐一个 bool**，**30 周 MA 的值和斜率都没有落到任何输出字段**——
  而 Weinstein 的判据恰恰是这两个。这是一个「算了但没发」的缺口，成本很低。
- ⚠️ **名字撞车预警**：`universe.json` 里已有 `sp_phase`（值 1/2/3）。那是 **oratnek Advanced Structure Pivot 的内部阶段**
  （`pipeline/screeners/structure_pivot.py:113`），**与 Weinstein 的 stage 毫无关系**。
  复盘稿如果写"stage 2"而页面上有个 `sp_phase=2`，两者会被读者接成一个。落地时必须避开 `stage` / `phase` 这两个词根。

---

## 6. VCP

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| —（拟 `vcp_contractions`） | Minervini **Volatility Contraction Pattern (VCP)** | 整理期内**2 到 6 次逐次变浅的回撤**（理想 2–4 次），**每次约为前一次深度的一半**（示例 25%→15%→8%→3%，或 20%→10%→5%）；**成交量随之收缩，末端出现明显的 volume dry-up**；Minervini 用 **"footprint" 速记**记录（周数、最大回撤/最小回撤、收缩次数，写成 `2T`/`3T`/`4T`，T = 收缩次数）；买点＝突破 pivot 且**放量** | ⚠️ **有可引定义，但只有作者本人的散文式描述——"每次约一半"没有容差、"volume dry-up"没有阈值** |
| `vcs` | oratnek **Volatility Contraction Score v2**（**不是 VCP**） | ATR13/ATR63、stdev13/stdev63、vol5/vol50 三个比值加权 0.4/0.4/0.2，乘 trendFactor，EMA3 平滑 + daysTight 奖励 | ✅ 一致（`pipeline/screeners/vcs.py`，逐字移植自 `indicators/third_party/oratnek_vcs_v2.pine`）。**它测的是压缩程度，不是收缩次数**——与 VCP 同源不同物 |

**出处**：Minervini《Trade Like a Stock Market Wizard》(2013) 与《Think & Trade Like a Champion》(2017) —
[TrendSpider 学习中心](https://trendspider.com/learning-center/volatility-contraction-pattern-vcp/)（2–6 次回撤、20/10/5 示例、量随价缩）·
[LuxAlgo 概念页](https://www.luxalgo.com/library/concept/volatility-contraction-pattern/)（"each roughly half the depth of the prior one"、25/15/8/3 示例、footprint 速记）·
[TraderLion](https://traderlion.com/technical-analysis/volatility-contraction-pattern/)。
本机一手：**无**。本机无 Minervini 任何一本书（`find` 全盘 `*Minervini*` / `*Stock Market Wizard*` / `*Think*Trade*Champion*` 零命中）。
唯一的本机人声旁证是 Brian Shannon 在 TraderLion 访谈里的顺口一提
（`data/research/videos_2026-08/traderlion_shannon_avwap_J_pYTy94thc.txt:87`：
"like what M[iner]vini calls a volatility c...ontraction pattern"），**只是引用不是定义**。

**回答任务里的那个问题（VCP 是不是 `wk_band_3` 那一类）**：**不是，但也不是干净的标准。**
- `wk_band_3` 的病是**冒用了别人的形态名**（原名 `wk_tight_3` 冒充 IBD 的 "3 Tight Closes"），而它的口径是我们自造的。
- VCP **有作者本人反复公开的定义**，收缩次数（2–6，理想 2–4）与"每次约前次一半"是**可引的**，比 `wk_band_3` 强一个档。
- 但它**止步于散文**："roughly half" 没有容差带，"volume dry-up" 没有阈值，回撤起止点没有 pivot length。
  任何代码实现都必须自己补这三个数——**补的部分是自造的，必须写明**。
- ⚠️ 现状还有个具体风险：`universe.json` 已经有 `vcs` 这个字段。`vcs` ≠ VCP。
  复盘稿写 "VCP" 而页面有 `vcs` 列，会被当成同一个东西。**若真要做 VCP，字段名不许用 `vcp` 之外的缩写，且必须在页面上与 `vcs` 分开标注。**

---

## 7. power trend

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| `power_trend`（`signals.json` 五项 + `PowerTrend.jsx`） | **Mike Webster / IBD Market School — Power Trend**（**不是 Minervini**） | 四条同时成立才**开启**：①**当日最低价**在 **21 日 EMA 之上，已连续 ≥10 个交易日** ②**21 日 EMA 在 50 日 SMA 之上，已连续 ≥5 个交易日** ③**50 日 SMA 处于上升**（斜率向上）④**当日收盘高于开盘**（阳线）。**关闭**：21 日 EMA 下穿 50 日 SMA（另有两条提前失效：指数在距高点 >10% 时跌破 50 日线；指数收盘跌破当初那个 follow-through day 的最低价） | ⚠️ **五项检查与标准口径无一条对上**（逐条对照见下） |

**出处**：
- **发明人本机自述（一手人声）**：`data/research/videos_2026-08/webster_21ema_wro9_GxQpyUfZv4U.txt`
  `:33`「Power trend is heavily based on the ... something we came up with ... **three of us came up with**」
  `:59-60` 他讲 21 日的用法时明确用的是「**你的 low 在它之上**」并连续计数
  （"three consecutive days with your low above it"、"third or more consecutive day that closes up with ... our low is above your 21 day"），
  以及第三人 Chuck 贡献的「**50 日必须是平的或向上，不能是向下的**」——这正好对应标准口径的 ① 与 ③。
  `:9-12` 讲 21 EMA 的来历：他在 O'Neil 研究部做回测，Bill O'Neil 本人只用 50/200 日（10/40 周）SMA。
- **成文规则**：[TradingSim, Riding the Power Trend](https://www.tradingsim.com/blog/riding-the-power-trend-navigating-the-next-big-market-wave)
  （四条 + 关闭条件 + 两条提前失效，并明确 credit 给 Mike Webster）·
  [Deepvue, Mike Webster Indicators](https://deepvue.com/indicators/mike-webster-indicators/)（10 日 / 5 日 / 50 日上升 / 收阳，及黄-橙-绿三档点）。

> 🔴 **归属更正（这是本轮最该拉响的一条）**：任务书把 power trend 记在 Minervini 名下，**查下来不是他的**。
> 它出自 **Mike Webster**（O'Neil Capital Management / IBD，与另外两人在 IBD Market School 共同定型），
> Webster 本人在本机那份转录里说得很清楚。
> 而**我们代码里的第三种归属也是错的**：`pipeline/macro/calc_signals.py:81` 的分节注释写 `Power Trend (Oratnek-style)`。
> 一个词，任务书、代码注释、真实出处，**三个不同的人**。

**五项检查 vs 标准口径，逐条**（我们的在 `pipeline/macro/calc_signals.py:84-141`，页面在 `frontend/src/components/macro/PowerTrend.jsx`）：

| 我们的检查 | 标准里对应的条 | 对不对得上 |
|---|---|---|
| `3d_gt_20sma`：近 3 根**收盘**的最小值 > **SMA20** | ①：**最低价** > **EMA21**，连续 **10** 天 | ❌ 三处都不同：**收盘 vs 最低价**、**SMA20 vs EMA21**、**3 天 vs 10 天** |
| `3d_gt_50sma`：近 3 根收盘最小值 > SMA50 | 标准里**没有这一条** | ❌ 多出来的 |
| `3d_gt_200sma`：近 3 根收盘最小值 > SMA200 | 标准里**没有这一条** | ❌ 多出来的 |
| `20sma_gt_50sma`：SMA20 > SMA50（**当日一次**） | ②：**EMA21** > SMA50，**连续 ≥5 天** | ⚠️ 形状对，但均线类型错（SMA20 vs EMA21）且**没有持续期** |
| `50sma_gt_200sma`：SMA50 > SMA200 | 标准里**没有这一条**（黄金交叉不是 power trend 的条件） | ❌ 多出来的 |
| — | ③ **SMA50 上升** | 🔲 **我们没查斜率** |
| — | ④ **当日收盘 > 当日开盘** | 🔲 **我们没查** |
| — | 关闭条件（EMA21 下穿 SMA50 等三条） | 🔲 **完全没有关闭态**——我们的是每日重算的五个 bool，没有"开/关"这个状态机 |

**结论**：五条里 **0 条完全一致，1 条形状近似**；标准的 4 条我们**缺 2 条**、**多 3 条**。
`signals.json` 今天 SPY 的实际输出是 `{'3d_gt_20sma': False, '3d_gt_50sma': True, '3d_gt_200sma': True, '20sma_gt_50sma': True, '50sma_gt_200sma': True}`——
**这不是 Power Trend 的读数**，页面上标着 "Power Trend" 属于**自造量冒充标准读数**，宪法明令禁止。

**能不能算（改成标准口径）**：⚠️ **一半能，一半差数据**。
- ①②③ 需要指数的 **EMA21 / SMA50 序列 + 每日最低价**。`signals.json` 有当日 `ema21` 与 `sma50`（快照），
  但**没有历史**、**没有 low**，所以 10 天 / 5 天的连续计数**现在算不出**。
- ④ 需要指数当日 open 与 close：**`signals.json` 只有 `close`**，无 open。
- 但**管线拿得到**：`calculate_power_trend` 的入参就是一个带 OHLC 的 `hist` DataFrame，
  ①②③④ 全部可在同一个 `hist` 上算出来。**这是四个词条里唯一"改口径不需要新数据源"的一个**——
  缺的只是把 `hist` 里已有的 `Low`/`Open` 用起来，以及把 SMA20 换成 EMA21。

---

## 8. "hot potato" / "the tell" / "lone standout"

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| —（口语，拟不落字段） | **hot potato**：**查过，有标准名但指的是别的东西** | 学界/交易台的 "hot potato trading" 指**外汇同业市场上做市商之间快速转手库存失衡**（Lyons 的 FX 微观结构用法），与"资金在板块间轮动"无关 | ⚠️ **撞名**。用它描述板块轮动不是"没有标准"，是**占用了一个已有确切含义的术语** |
| —（口语，拟不落字段） | **the tell**：**查过，无标准** | — | ⚠️ **无标准**。检索只回到扑克术语 tell 与航海 tell-tale，技术分析语境下无定义 |
| —（口语，拟不落字段） | **lone standout**：**查过，无标准** | — | ⚠️ **无标准**。最接近的**有**标准的量是 **market breadth / 参与度**（我们已有 `advances` `declines` `pct_above_*sma` `t2108` `record_high_pct`） |

**查过什么**（留痕）：
- `"hot potato" market commentary technical analysis definition indicator rotation term standard`
  → 命中 [Babypips Forexpedia: Hot Potato Trading](https://www.babypips.com/forexpedia/hot-potato-trading)
  与 [ScienceDirect《Hot potatoes: Underpricing of stocks following extreme negative returns》](https://www.sciencedirect.com/science/article/abs/pii/S0378426623000018)
  ——两者都不是"轮动"的意思。
- `"the tell" trading term definition technical indicator standard "lone standout" stock market breadth definition`
  → 无技术分析定义；返回的是 [Tell (poker)](https://en.wikipedia.org/wiki/Tell_(poker))、Tell-tale (sailing)。
  breadth 一侧命中 [Nasdaq glossary: Breadth of the market](https://www.nasdaq.com/glossary/b/breadth-of-the-market)。
- StockCharts ChartSchool 市场指标目录里三个词**都不在**。

**提议的可测代理（⚠️ 三个全部是自造的，必须在页面与契约行里明写"自造"，不得当标准读数）**：

| 口语词 | 自造代理 | 用现成字段 | 偏离了什么标准 |
|---|---|---|---|
| hot potato | 「领涨板块换手」：`groups.json` 的板块日涨幅排名，今日 Top-3 与前一日 Top-3 的**交集 ≤1**，连续 ≥N 日 | `data/output/groups.json` · `groups_history.json` | **没有对标任何标准**——轮动强度学界有 sector rotation / dispersion 的正式度量，本代理没查过它们 |
| the tell | 不做。**建议直接从复盘用词里删掉** | — | 它不是一个量，是"我注意到了 X"的修辞；给它配代理等于把修辞伪装成读数 |
| lone standout | 「参与度收窄」：指数创新高（`spx_close` 新高）**当日** `pct_above_20sma` < 其自身 252 日 20 百分位 | `breadth.json`（`spx_close` · `pct_above_20sma`）· `breadth_archive.csv` 574 行 | 标准工具箱里治这个病的是 **breadth divergence / Record High Percent / High-Low Index**，**我们三个都已经有了**。先用标准的，别造这个 |

---

## 9. moving-average alignment / flat tape 里的 ping-pong

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| —（拟 `adx14`） | **"均线缠绕所以忽略均线" ——查过，无标准。** 但它想表达的那件事**有标准**：Wilder **ADX**（趋势有无） | Wilder《New Concepts in Technical Trading Systems》(1978)：**ADX < 20 = 无趋势**，ADX > 25 = 强趋势，20–25 是灰区 | 🔲 **我们没有 ADX**。这是本轮唯一「口语说法无标准，但它指的现象有一个干净的标准量，而我们恰好没建」的词条 |

**出处**：[StockCharts ChartSchool — Average Directional Index (ADX)](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx)
——原话 "Wilder suggests that a strong trend is present when ADX is above 25 and no trend is present when ADX is below 20"，
并注明 20–25 是 "a gray zone"。ChartSchool 是本表 08-31 已采用的权威源之一。

**Brian Shannon 那本书的结论：不能引，且不该等它。**
- `~/Documents/Trading/03_Trading_Strategies/Books_References/Brian Shannon - Technical Analysis Using Multiple Timeframes ... (2008).pdf`
  是 **198 页纯扫描件，没有文字层**（`pdffonts` 输出零字体，`pdftotext -layout` 出 0 行）。
  本机**没装 tesseract / ocrmypdf**，本轮无法读它。**"Shannon 书里有没有这条"这个问题本轮未回答**，不是回答了"没有"。
- **但本机有 Shannon 本人的转录**，且他讲的与"均线缠绕就忽略均线"**不是一回事**：
  `data/research/videos_2026-08/traderlion_shannon_avwap_J_pYTy94thc.txt:46`
  「Is a 50-day moving average magic? No. **But we all use it.** We all have it on our chart. So we use that as a **reference point of value**.」
  `:71`「All I do is buy the touch of the 21 EMA or the 20 SMA or the 50 or whatever ... and it works every time. **No, it doesn't.**」
  `:76`「**Level of interest.** ... Let's see how it behaves.」
  → 他的立场是**均线永远只是"关注位"、永远要看在那里的行为**，**不是"横盘时把均线关掉"**。
  拿他给"均线缠绕所以忽略均线"背书，是**引用的权威不站在我们这边**。

**能不能算**：⚠️ ADX 我们**没有**，但**造它零风险**——`data/output/tickers/<T>.json` 的 `ohlc_2y`（high/low/close 齐全）
和管线里给全池取的 `hist` 都够算 Wilder 的 DM/TR/ADX；口径是 1978 年的公开原文，没有自造空间。
指数一侧仍受 §2 那个缺口拖累（`signals.json` 无 OHLC 历史），**个股一侧现在就能算**。

---

## 收口：两张清单

### A. 无标准（或标准不指这件事）——**不得当标准读数上页**

| 词 | 性质 | 处置建议 |
|---|---|---|
| **the tell** | 查过，无标准。是修辞不是量 | **从复盘用词表删除**，不配代理 |
| **lone standout** | 查过，无标准 | 改用已有的标准量（breadth / `record_high_pct` / `high_low_index`）说同一件事 |
| **hot potato** | **有标准名，但指 FX 同业库存转手**，不是板块轮动 | 换词；若坚持用，代理必须标"自造" |
| **swing failure** | 有通行描述，**无单一权威、无任何数值门槛**；不是 Wyckoff 的（UTAD 要阶段前提）、不是 Wilder 的（那是 RSI 上的） | 可实现，但门槛全部是自造的，须逐个写明 |
| **均线缠绕→忽略均线** | 查过，无标准；**Shannon 的公开立场与它相反**（均线是"关注位"，不是"横盘时关掉"） | 换成 **ADX < 20**（Wilder 1978，ChartSchool 有条目） |
| **VCP** | 半个：收缩次数（2–6，理想 2–4）与"每次约前次一半"可引，但**容差 / 量的阈值 / pivot length 三个数标准里都没有** | 可实现，补的三个数须写明自造 |

### B. 有标准，但**本仓库现在算不出**——按缺口排序

| 缺什么 | 挡住了谁 | 修起来多大 |
|---|---|---|
| 🔴 **指数的日线成交量序列**（SPY/QQQ/Nasdaq/^GSPC，逐日 volume + open/high/low + 足够长的历史） | **follow-through day** 与 **distribution day** 全部两个词条 —— 两者的口径都是「%变动 **且** 量高于前一日」，**量那一半我们一个字段都没有** | 中。`signals.json` 是快照式（无历史无量）；`tickers/` 的 217 支不含指数；`asset_signals.csv` 只有 12 天且 `rel_volume` 是三月均量口径。需要新开一份指数日线 store |
| 🟠 **30 周（150 日）均线的值与斜率** | **Weinstein stage 1/2/3/4**（判据就是这两个量） | **小**。管线里 `trend_base` 已经在算 30 周 WMA，只是只吐了一个 bool，没把值和斜率落成字段 |
| 🟠 **"本轮上涨的起点"这个锚** | **climax top** 七条征兆里的五条（最大单日涨幅 / 最大单日量 / 最大周振幅 / 连涨日 / 通道线），全都是「自本轮开始以来的最大」 | 中。仓库无此概念；`days_since_52wh` 方向相反 |
| 🟡 **指数的 EMA21/SMA50 历史 + 每日 low/open** | **power trend** 的标准口径（10 日 / 5 日连续计数、50 日斜率、当日阳线） | **小**。`calculate_power_trend` 的入参 `hist` 里 `Low`/`Open` 本来就在，是没用；改口径**不需要新数据源** |
| 🟡 **ADX** | 「横盘该不该看均线」这件事的标准答案 | **小**。`ohlc_2y` / 管线 `hist` 够算，口径是 1978 公开原文 |

### C. 顺手记下的两处**名字撞车**（不改口径也该处理）

1. `universe.json` 的 **`sp_phase`（1/2/3）** 是 oratnek Structure Pivot 的内部阶段
   （`pipeline/screeners/structure_pivot.py:113`），**与 Weinstein stage 无关**。复盘稿说"stage 2"时两者会被读者接上。
2. `universe.json` 的 **`vcs`** 是 oratnek Volatility Contraction **Score**（`pipeline/screeners/vcs.py`，测压缩程度），
   **不是 Minervini 的 VCP**（数收缩次数）。两个词在页面上并排出现必然被当成同一个。

这两处与登记表里 `wk_band_3`（原名 `wk_tight_3` 冒充 IBD "3 Tight Closes"）、
`rs_ibd`（冒充 IBD RS Rating）是**同一个形状的第 3、第 4 次**——按三次律，
建议 OPS 周检把「**新字段命名前先 grep 该名字在业界指哪个东西**」升成机制，而不是继续一个个改名。

---

## 附：本轮用到的本机一手文件（路径已核，可点开）

| 文件 | 本轮用它证了什么 |
|---|---|
| `~/Documents/Trading/03_Trading_Strategies/Books_References/stan-weinstein-s-secrets-for-profiting-in-bull-and-bear-markpdf_compress.pdf` | 四阶段的原书判据（含自测答案里那组两变量口径）。**09-05 才到本机，`CANON_LIBRARY.md` 仍记为"没有"** |
| `~/Library/CloudStorage/GoogleDrive-zhuandy531@gmail.com/My Drive/Fluxus Trade Lab/02_Areas/Discord Business/Old Discord Files to sort/Swing Class 2025/The-TraderLion-Ultimate-Trading-Guide.pdf` | 反证：**FTD 与 distribution day 全书都没有定义**（p.84 当前提用、p.102 只给定性清单）；四阶段转述与原书一致 |
| `data/research/videos_2026-08/webster_21ema_wro9_GxQpyUfZv4U.txt` | Power Trend 的**发明人自述**（"three of us came up with"）、21 EMA 用 **low** 判、Chuck 的 50 日斜率条件 |
| `data/research/videos_2026-08/traderlion_shannon_avwap_J_pYTy94thc.txt` | Shannon 本人的均线立场（"level of interest"），**反驳**"缠绕就忽略均线" |
| `data/research/videos_2026-08/dante_stop_moaning_Vy1_URi88eE.txt` | 反证：本机这份 Trader Dante 转录**没有** SFP 的定义，不能当出处 |
| `~/Documents/Trading/03_Trading_Strategies/Strategy_Docs/CAN_SLIM_Chart_Pattern_Cheat_Sheet.pdf` | 已登记行的复核（3 Tight Closes 1.5%、所有 BP +10 cents）；**无 climax top / FTD / distribution day** |
| `Books_References/Brian Shannon - Technical Analysis Using Multiple Timeframes (2008).pdf` | **无文字层**（198 页扫描，`pdffonts` 零字体），本机无 OCR 工具，本轮**未能读** |
