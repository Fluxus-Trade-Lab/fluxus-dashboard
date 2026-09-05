# 度量的权威口径表

**立于 2026-08-31（Andy 亲定）。** 起因：我为了给"新高新低"配一个短窗版本，
手搓了三个选择——4 周窗口、`$5/股 + $5M 成交额`的流动性闸、200 根 K 线下限。
Andy：**「很多数据是有专业的衡量的，不需要你去计算去创造。只需要去哪里找。」**

一查就知道他是对的，而且不是小对：

- **行业标准的做法根本不是流动性闸，是证券类型过滤。** NYSE / Nasdaq / NYSE Arca
  的官方新高新低口径明确排除 unit investment trusts、closed-end funds、warrants、
  preferred、ETF、**SPAC**、非 SIC 分类(OTC)股。我们被 SPAC 污染的那 88%，
  在标准口径里**根本不该进这个池子**。我的成交额闸只是它的粗糙代理，
  而且会顺手扔掉合法的小盘普通股。
- **「4 周新高新低」不是一个行业指标。** 52 周是机构惯例。那个时间尺度上的标准量是
  %above-20MA、T2108(%above-40MA)、McClellan——**这三个我们本来就有**。
- **标准工具箱里有两个我们没有的东西，正好治我们的病**：`Record High Percent`
  = NH/(NH+NL)，和 `High-Low Index` = 前者的 10 日均。它们是**比值**，
  所以对 08-14 那次 universe 从 3000 涨到 5614 的断层免疫——
  而我一直在用会被断层污染的原始计数做时序比较。

## 规矩

> 引用顺序（09-04 起）：**本机一手（见 [CANON_LIBRARY.md](CANON_LIBRARY.md)）→ 发明者/官方网页 → 社区复刻**。

> **动手算一个量之前，先查它有没有专业口径和公开源。有就照抄，没有才自己造，
> 并把「查了什么、为什么没有」写进本表。**

判定「有没有」的最低动作：一次针对性检索（指标名 + "definition" / "calculation"）
+ 至少一个权威来源（StockCharts ChartSchool、Worden、交易所官方口径、指数编制方法书、
学术原文）。查不到也要留痕——写"查过，无标准"，比不查就造强。

自造的量必须在代码注释和契约行里**明写它是自造的**，并写清它偏离了哪个标准、为什么。
自造量**不得**出现在页面上冒充标准读数。

> **命名新发布字段前，先查本表（Andy 2026-09-06 定，原话「候选行批了，Power Trend 改判定对齐
> Webster，撞名立机制」）**：一个标准的名字/缩写，只有它那一行的状态是 ✅ 一致 时才能拿来当
> 我们的字段名；口径不一致或本来就是自造，就必须换一个不同的名字，并在状态列自报偏离。
> 三次律第四次：`wk_band_3`（原名 `wk_tight_3`，冒用了 IBD "3 Tight Closes" 的形态名）·
> `rs_ibd`（现 `rs_rating`，冒用了 IBD RS Rating 的名字）· `sp_phase`（oratnek Structure
> Pivot 的内部阶段 1/2/3，与 Weinstein 的 stage 撞名但无共享定义）·
> `vcs`（oratnek Volatility Contraction Score，与 Minervini 的 VCP 撞名但测的不是收缩次数）。
> 机制见 [`pipeline/tools/audit_metric_names.py`](../../pipeline/tools/audit_metric_names.py)。

## 登记表

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| `mcclellan_osc` | McClellan Oscillator | RANA = net/(adv+dec)×1000，19 与 39 日 EMA 之差 | ✅ **一致**（`breadth_store.py:84-91`） |
| `ad_line` | Advance-Decline Line | 净涨跌家数累加 | ✅ 一致 |
| `t2108` | Worden T2108 | 40 日均线上方占比 | ✅ 一致 |
| `pct_above_20/50/200sma` | Percent Above Moving Average | **挂在具名指数上**：`$SPXA200R`(标普500) / `$NYA200R`(NYSE) 等，五个标准均线长度 | ⚠️ **口径不全**——公式对，但池子是 5630 支 Finviz 自选池，不对应任何公开指数，因此**与任何公开读数都不可比**（含 S5TH） |
| `new_highs` / `new_lows` | 52-week New Highs/Lows | 52 周极值，**池子只含普通股** | ⚠️ **原始计数保留不动**（574 行档案的连续性），标准口径另发下一行 |
| `new_highs_common` / `new_lows_common` | 同上 | 排除 UIT / CEF / warrant / preferred / ETF / **SPAC** / 非 SIC OTC | ✅ **一致**（2026-08-31 落地）。Finviz 已挡住 ETF/CEF/preferred/warrant，我们补上 `industry == "Shell Companies"` |
| `record_high_pct` | Record High Percent | NH/(NH+NL) | ✅ **一致**（2026-08-31 落地），用 common 计数做分子 |
| `high_low_index` | High-Low Index | Record High Percent 的 10 日均 | ✅ **一致**（2026-08-31 落地） |
| `adr_pct` | ADR% (Qullamaggie / Deepvue / TradingView) | `100×(mean(High_i/Low_i, 20根)−1)`：纯日内、算术平均、每根除自己的 low | ✅ **一致**（2026-09-04 落地 `843d527d`）。此前发的是 ATR%，而闸阈值 3.5–10 是从 Qullamaggie 借的——实测生产闸 ≥3.5，我们过 226 / 标准过 205，**24 支（10.6%）只因读数偏高才进来** |
| `atr_pct` | ATR% | 含跳空的 true range ÷ 收盘 | ✅ 一致。**与 ADR% 是两个指标不是别名**（TradingView 官方文档明写）。止损距离与 R 倍数用它 |
| `bo_count_1m/3m/6m/1y` 的**判定** | Stockbee 4% Breakout | 涨幅 ≥4% **且** 量 > 前一根 **且** 量 > 100,000 | ✅ **一致**（2026-09-04 落地）。此前是 `量 ≥ 9,000,000 且 涨幅 ≥4%`——9M 来自另一个扫描（EP 9 Million，且在那里指 `maxv65` 不是当日量），而 9M 日地板对大盘股恒真，于是缺失的放量条件从未生效，剩下的只是「今天涨了 4%」 |
| `bo_count_*` 的**聚合** | *(无标准)* | Stockbee 的是**单日横截面广度**（今天全市场有多少只） | ⚠️ **自造**：逐票纵向滚动计数。已在代码里明写 |
| `h_score_pctl` → 页面 **Composite Score** | IBD Composite Rating 的**形状**（多因子合成后再排 1–99） | 合成后必须再排名成百分位 | ✅ 排名一致（2026-09-04 落地）。**权重是自造的**：IBD 六个系数专有、查无可引用的表；20% 基本面 + 30% 行业 + 50% RS。Andy 09-04 定名 Composite Score，不再叫 RS |
| `h_score`（原值） | *(无标准)* | 五个百分位的加权平均 | ⚠️ **自造且不是百分位**（顶档 0.6%、IQR 29）。保留仅为归档连续性，**不上页** |
| `three_weeks_tight` / `twt_buy_point` | IBD **3 Tight Closes** | 每周收盘与**前一周**相差 ≤1.5%、连续三周；买点 = 三周最高 + $0.10——本机 `CAN_SLIM_Chart_Pattern_Cheat_Sheet.pdf` | ✅ **一致**（2026-09-04 落地）。相邻两两比较，不是全域带宽 |
| `wk_band_3` | *(无标准)* | — | ⚠️ **自造**：三根周收盘的全域带宽 ≤1.5%。原名 `wk_tight_3`，冒充了 IBD 的形态名。保留仅为让 08-20 紧致度研究可复现 |
| `bar_scale_jumps` | 厂商数据质检通行做法 | ①复权 vs 未复权比对 ②逐日收盘比落在拆股比上——[FMP](https://site.financialmodelingprep.com/how-to/how-to-compare-adjusted-vs-unadjusted-stock-prices-with-a-free-api) · [StockCharts](https://help.stockcharts.com/data-and-ticker-symbols/data-availability/price-data-adjustments) | ⚠️ **标准形状**：①在 MNST 上失效（两个 feed 同样错乱），只能用②；容差 0.03（对数空间）与「当日 H/L 解释不了该跳空」这第二条件是我们加的 |
| `pct_above_*_sp500` / `t2108_sp500` | StockCharts **$SPXA200R** 等 | 挂在具名指数上 | ✅ **一致**（2026-09-04 落地）。成分来自 Finviz `idx_sp500`（503 支，含双重股权）。成员拿不到时给 NULL，**不回退全池** |
| `rs_rating` | *(IBD 专有；社区复刻)* | `0.4·q1 + 0.2·q2 + 0.2·q3 + 0.2·q4` 对 SPY 的超额，再排 1–99 | ⚠️ **社区重建不是 IBD 一手**（[skyte](https://github.com/skyte/relative-strength) · [Optuma](https://forum.optuma.com/t/ibd-style-relative-strength/6614) 互相转抄）。q3(189日) 由 6m/1y 插值，是我们的近似。原名 `rs_ibd` 冒充了 IBD |
| `atr_pct_pctl_252` / `range5_pct_pctl_252` | IV Percentile 的**归一化方式** | 严格低于今日的天数占比 | ⚠️ **标准形状**：比较符已改严格（下限 0）；**被测的量是自造的**（ATR%，非日对数收益年化标准差），名字里已写明。`atr_pctl_63` 已删（63 窗口无业界锚点、零消费者） |
| `dcr_pct` | TraderLion **Closing Range** | (close − low)/(high − low)——本机 `The-TraderLion-Ultimate-Trading-Guide.pdf` | ✅ 一致 |
| `pocket_pivot` | TraderLion **10-Day Pocket Pivot** | 上涨日量 > 过去 10 日任一**下跌日**量——同上 | ✅ 一致（`vol10_green` 是另一个量：比前 10 根**全部**bar） |
| `atr_from_sma50` | SteveDJacobs **ATR Matrix** `extAtrAsPctOfATR` | (close/SMA50−1)/(ATR/close)——本机 `ATR Matrix.txt` | ✅ 一致；≥7× 减仓 / ≥11× 衰竭来自本机 `Candles Stage Analysis.txt`（@TradeDudeNYC），**不是 Weinstein 原书** |
| `rs_line_pctl_21/63/126` | oratnek 的 **RS 1M** | 自百分位，`count(RS_i <= RS_today)/n × 100` | ✅ **保持 `<=`，不改**。09-04 一度按 IV Percentile 的严格 `<` 去改，**撤回了**：这个 `<=` 是 08-18 从他页面逆向工程出来的，29 个数全部精确复现且有 fixture 钉住。外部真值验证过的复现，优先于形式上更「标准」的比较符 |
| 新高/新低 · Record High Percent · RANA | Gregory Morris《Market Breadth Indicators》 | 52 周；adjusted for Total Issues；Cohen 10 日 NH/(NH+NL)；Ratio-Adjusted McClellan——本机 epub | ✅ 一手依据补齐（08-31 采用时引的是 StockCharts） |
| `is_tradeable` | S&P **FALR**（换手率） | 年美元成交额 ÷ 流通调整市值 ≥ 0.1——[S&P 方法书](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-indices.pdf) | ⚠️ **标准形状 · 三条偏离已声明**：①绝对量非比值（FALR 会把 BRK 判负；我们问「一天能不能建仓」）②两个常量各自拍的、松紧从未对齐 ③窗口 09-05 前从未声明（实测 20 日，58/58 误差 0.0000）。09-05 补上证券类型过滤 |
| `falr_252` | S&P FALR | 同上 | ⚠️ **报告值不做闸**。分子由 20 日均量外推一年、分母未做流通调整，两处近似。实测 09-03：FALR≥0.1 通过率 96.7%、我们的闸 45.3%，只 FALR 过 2810 支——**两把尺子测的不是同一件事** |
| `up_4pct_stockbee` / `down_4pct_stockbee` | Stockbee **4% breadth** | 当日全市场满足「涨 ≥4% 且 量 > 前一日 且 量 > 100k」的普通股家数 | ✅ **一致**（2026-09-05 落地）。原 `up_4pct`/`down_4pct` 只有涨幅一条件，保留不动（574 行档案） |
| `oops_buy` / `oops_sell` | Larry Williams **Oops!**（《Long-Term Secrets to Short-Term Trading》1999） | buy：今开 < 昨低 且 今高 ≥ 昨低；sell：今开 > 昨高 且 今低 ≤ 昨高。跳空必须严格 | ✅ **一致**（2026-09-05 落地，Andy「A 做」）。TraderLion 借的是这个名字，本机 Trade-Lab 图集标了 23 次但一句定义都没有——定义是 Williams 的。**只做触发不做「守住了没」**，后者不在定义里 |
| `new_highs_4w` / `new_lows_4w` | *(查过，无标准)* | 52 周是机构惯例；该时间尺度的标准量是 %above-20MA / T2108 / McClellan | ⚠️ **自造**。仅供研究，不得当标准读数上页 |
| — | McClellan Summation Index | McClellan 振荡器累加 | 🔲 我们没有 |
| — | Arms Index (TRIN) | (adv/dec)÷(上涨量/下跌量) | 🔲 我们没有 |
| — | Bullish Percent Index | P&F 买入信号占比 | 🔲 我们没有 |
| —（拟 `climax_signs`） | O'Neil **Climax Top / Climax Run** | 长期上涨（典型 ≥18 周）之后加速的 1–2 周终段，同时看七个征兆：①**exhaustion gap**（跳空高开于昨日高点之上，重量）②**该轮最大单日涨幅** ③**该轮最大单日成交量** ④连续 7–8 个上涨日（或 10 日中 8 日涨）⑤**该轮最大周振幅**（周高−周低大于本轮起点以来任何一周）⑥价格刺穿上轨通道线（该线由 4–5 个月内 ≥3 个高点连成）⑦距 200 日均线 +70~100% 以上 | 🔲 **我们没有**。七条里只有第 ⑦ 条现成（`sma200_dist`）；①②③⑤⑥ 需要「本轮上涨起点」这个锚，而我们**没有任何字段定义"本轮"** |
| —（拟 `ftd`） | O'Neil / IBD **Follow-Through Day** | 前置：指数创新低后出现 **rally attempt 第 1 天**（当日收盘高于开盘 / 高于前收，或小跌但收在当日区间上半部）；随后 2、3 日**不得跌破第 1 天的低点**，跌破则重新计数。**第 4 天或以后**（最佳 4–7 天，最迟约 10 天）某大盘指数**收涨 ≥1.25%**（IBD 现代口径抬到 **≥1.7%**，2% 更好）**且成交量高于前一交易日**——成交量只需高于前一日，不要求高于均量 | 🔲 **我们没有**，且**指数成交量在 `data/output/` 里根本不存在** |
| —（拟 `dist_day` / `dist_count_25`） | IBD **Distribution Day** | 某大盘指数（Nasdaq Composite 或 S&P 500）**收跌 >0.2%** **且当日成交量高于前一交易日**（同样只要求高于前一日，不要求高于均量）。计数看**滚动 25 个交易日**窗口；一天在下列任一条件下出列：已过 25 个交易日，或指数自该日收盘起**涨 ≥5%**。**4–5 天 = Under Pressure，6 天以上通常先于回调** | 🔲 **我们没有**；缺的字段与 FTD 同一个（指数日量） |
| —（拟 `sfp`） | **查过，无单一权威**。现代通用名 Swing Failure Pattern (SFP) | 通行描述：一根 K 线的**影线**穿越前一个 swing high / swing low，**收盘回到该极值之内**。Wyckoff 谱系里的对应物是有阶段前提的 **Upthrust After Distribution (UTAD)** 与 **Spring / Shakeout**；SFP 是把同一机制**剥掉阶段前提**推广到任意 swing 极值 | ⚠️ **不得当作标准读数**。同一形状在四套体系里叫四个名字（Wyckoff upthrust / Wilder failure swing / SFP / SMC 的 liquidity sweep），**没有一套给出可判定的数值门槛** |
| —（拟 `weinstein_stage`） | Weinstein **Four Stages**（原书 Ch.2） | 以 **30 周均线（30-week MA）的斜率 + 价格相对它的位置**判定：**Stage 1 基地区**＝MA 由跌转**平**，价格在 MA 上下来回、仍在阻力位下方的箱体内；**Stage 2 上升期**＝价格**放量突破阻力区与 30 周 MA**，MA 突破后不久**转升**，此后每次回调都**守在上升的 MA 之上**、峰与谷双双抬高；**Stage 3 顶部区**＝MA 失去上升斜率**转平**，价格开始在 MA **上下反复穿刺**（Stage 2 时回调始终守在 MA 上或之上），放量滞涨（churning）；**Stage 4 下跌期**＝价格**跌破支撑区**、MA **下行**且价格在 MA 之下（**破位不需要放量也成立**，放量更凶） | 🔲 **我们没有**；**30 周均线的值与斜率两个都没发**（见下） |
| —（拟 `vcp_contractions`） | Minervini **Volatility Contraction Pattern (VCP)** | 整理期内**2 到 6 次逐次变浅的回撤**（理想 2–4 次），**每次约为前一次深度的一半**（示例 25%→15%→8%→3%，或 20%→10%→5%）；**成交量随之收缩，末端出现明显的 volume dry-up**；Minervini 用 **"footprint" 速记**记录（周数、最大回撤/最小回撤、收缩次数，写成 `2T`/`3T`/`4T`，T = 收缩次数）；买点＝突破 pivot 且**放量** | ⚠️ **有可引定义，但只有作者本人的散文式描述——"每次约一半"没有容差、"volume dry-up"没有阈值** |
| `vcs` | oratnek **Volatility Contraction Score v2**（**不是 VCP**） | ATR13/ATR63、stdev13/stdev63、vol5/vol50 三个比值加权 0.4/0.4/0.2，乘 trendFactor，EMA3 平滑 + daysTight 奖励 | ✅ 一致（`pipeline/screeners/vcs.py`，逐字移植自 `indicators/third_party/oratnek_vcs_v2.pine`）。**它测的是压缩程度，不是收缩次数**——与 VCP 同源不同物 |
| `power_trend`（`signals.json` 五项 + `PowerTrend.jsx`） | **Mike Webster / IBD Market School — Power Trend**（**不是 Minervini**） | 四条同时成立才**开启**：①**当日最低价**在 **21 日 EMA 之上，已连续 ≥10 个交易日** ②**21 日 EMA 在 50 日 SMA 之上，已连续 ≥5 个交易日** ③**50 日 SMA 处于上升**（斜率向上）④**当日收盘高于开盘**（阳线）。**关闭**：21 日 EMA 下穿 50 日 SMA（另有两条提前失效：指数在距高点 >10% 时跌破 50 日线；指数收盘跌破当初那个 follow-through day 的最低价） | ⚠️ **五项检查与标准口径无一条对上**（逐条对照见下） |
| —（拟 `adx14`） | **"均线缠绕所以忽略均线" ——查过，无标准。** 但它想表达的那件事**有标准**：Wilder **ADX**（趋势有无） | Wilder《New Concepts in Technical Trading Systems》(1978)：**ADX < 20 = 无趋势**，ADX > 25 = 强趋势，20–25 是灰区 | 🔲 **我们没有 ADX**。这是本轮唯一「口语说法无标准，但它指的现象有一个干净的标准量，而我们恰好没建」的词条 |
| `conditions.today` → 页面 **Market Conditions 0-100** | oratnek 的 **Market Conditions** | 15 个条件对绝对中性线取正项占比，EMA-2 平滑（`breadth_signals.py:conditions_series` docstring 自认「Oratnek's construction」） | ⚠️ **构造复刻、数值从未对表**（与 rs_line_pctl 的 29/29 不同，这个连一次都没对过）。Andy 2026-09-06 裁「选A」：拿他页面现图对数值，对上 → 转 ✅ 名字保留；对不上 → 按撞名闸改名。**验证进行中，缺他页面截图** |

来源（本批 2026-09-06 追加，源 [`recap_vocab_sources_2026-09-06.md`](../research/ops/recap_vocab_sources_2026-09-06.md)；Andy 批「候选行批了，Power Trend 改判定对齐 Webster，撞名立机制」，口语三词 hot potato / the tell / lone standout 被裁「都是口语，忽略」，未登记）。

## 已登记的债

1. **把新高新低的池子换成标准的普通股口径**（排除 SPAC/CEF/ETF/preferred/warrant/
   非 SIC）。这是根治；现在的 `*_liq` 三道闸是代理，替换后应退役。
   需要证券类型字段——Finviz 有没有、还是要另找源，未查。
2. **建 `Record High Percent` 与 `High-Low Index`**。比值口径能让 08-14 断层
   前后的序列重新可比，我们现在整段历史的原始计数是不可比的。
3. `new_highs_4w` 的去留，等 1 和 2 落地后重估——很可能标准量已经够用，
   它就不必存在。
4. 本表的三个阈值（`$5`、`$5M`、`200 根`）**没有搜索过备选、没有对标任何标准**，
   是我拍的。替换为类型过滤后它们应当消失，而不是被"调优"。

## 相关

- 事故与实测数字：[nhnl_4w.md](../research/canary_2026-08/nhnl_4w.md)
- 研究纪律（预注册/证据分级/holdout）：[RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md)
- 数字的唯一权威源：`KNOWLEDGE.md` 数字权威表（本表管**口径**，那张表管**数值**）

来源：[StockCharts ChartSchool 市场指标目录](https://chartschool.stockcharts.com/table-of-contents/market-indicators) ·
[Barchart 新高新低汇总（池子排除规则）](https://www.barchart.com/stocks/highs-lows/summary) ·
[AAII: Using New Highs and New Lows to Measure Market Breadth](https://www.aaii.com/journal/article/455994-using-new-highs-and-new-lows-to-measure-market-breadth)


## 已删除的字段（2026-09-05，第二关 I 项）

删前**逐个现场复查**了消费者，不只信底账——底账的印象「bo_count 全家零消费者」是错的：
`boCount3m` 与 `boCount1y` **有真 preset 在用**，只有 1m/6m 没有。

| 删掉 | 为什么 |
|---|---|
| `rs_126d` | `rs_6m` 的别名。前端只在 `?? ` 回落位出现（本名在前，永不触发），无 preset |
| `ema21_r` · `sma50_r` | 仿射复制（`1 + sma20_dist` / `1 + sma50_dist`）。名字骗人两次：既不是 EMA21 也不是 R 倍数。零读者 |
| `ad_ratio_20` · `cmf21` | 每晚为 5,555 行计算，无页面、无 preset、无扫描读它 |
| `vol10_green_count_30d` | 同上（10d 那个有读者，保留） |
| `bo_count_1m` · `bo_count_6m` | preset 只用 3m 与 1y |
| `ema21_low_dist` | 两条筛选路径实证走不通；`preset_hits` 里那条是死映射 |

**没删（有真消费者，与底账不同）**：`volume`（`quality.py` 用它的缺失率）· `rs_63d`/`rs_21d`
（`TickerStats` 直接打印、4% Bullish 面板闸、preset `rs21d`）· `c_low52w`（Anticipation 面板三分之一条闸）。

两条区分对照没有删掉，改成守「它不该回来」：`sma50_r` 与 `ema21_r` 各自那条断言现在检查
**列不存在**，同时仍然断言 `atr_from_sma50` / `ema21_atr_dist` 不等于旧比值——08-24 那次
misport 正是把这两者搞混，对照要留着。
