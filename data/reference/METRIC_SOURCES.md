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
| `wk_tight_3` | IBD **3 Tight Closes** | **closes within 1.5%**、vol drops、secondary BP（+10 cents）——本机 `CAN_SLIM_Chart_Pattern_Cheat_Sheet.pdf` | ⚠️ **阈值对、形式偏离**：表只给 1.5%，IBD 文章说相邻周两两比较；我们是三根全域带宽。待改（方案 C） |
| `dcr_pct` | TraderLion **Closing Range** | (close − low)/(high − low)——本机 `The-TraderLion-Ultimate-Trading-Guide.pdf` | ✅ 一致 |
| `pocket_pivot` | TraderLion **10-Day Pocket Pivot** | 上涨日量 > 过去 10 日任一**下跌日**量——同上 | ✅ 一致（`vol10_green` 是另一个量：比前 10 根**全部**bar） |
| `atr_from_sma50` | SteveDJacobs **ATR Matrix** `extAtrAsPctOfATR` | (close/SMA50−1)/(ATR/close)——本机 `ATR Matrix.txt` | ✅ 一致；≥7× 减仓 / ≥11× 衰竭来自本机 `Candles Stage Analysis.txt`（@TradeDudeNYC），**不是 Weinstein 原书** |
| `rs_line_pctl_21/63/126` | @jfsrev **1-Month RS** | RS=close/SPY 的自百分位，`rank/(N−1)×100`，严格排名——本机 `1-Month Relative Strength.txt` | ⚠️ 我们用 `<=`（下限 1/n），它用严格排名（下限 0）。并入方案 D |
| 新高/新低 · Record High Percent · RANA | Gregory Morris《Market Breadth Indicators》 | 52 周；adjusted for Total Issues；Cohen 10 日 NH/(NH+NL)；Ratio-Adjusted McClellan——本机 epub | ✅ 一手依据补齐（08-31 采用时引的是 StockCharts） |
| `new_highs_4w` / `new_lows_4w` | *(查过，无标准)* | 52 周是机构惯例；该时间尺度的标准量是 %above-20MA / T2108 / McClellan | ⚠️ **自造**。仅供研究，不得当标准读数上页 |
| — | McClellan Summation Index | McClellan 振荡器累加 | 🔲 我们没有 |
| — | Arms Index (TRIN) | (adv/dec)÷(上涨量/下跌量) | 🔲 我们没有 |
| — | Bullish Percent Index | P&F 买入信号占比 | 🔲 我们没有 |

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

## 已登记的口径

### 黄金/白银的月度季节性（"autumn effect" / 中文语境的「金9银10」）—— 2026-09-05 登记

**有标准口径，且不是老话说的那两个月。照抄，零自造。**

| | |
|---|---|
| **权威源** | Baur, D. G. (2013), *The autumn effect of gold*, **Research in International Business and Finance** 27(1)（SSRN 1989593）。1980–2010 逐月检验：**九月与十一月是仅有的两个正且统计显著的月份**（+2.2% / +1.8%）。 |
| **后续文献** | Int'l Journal of Management and Economics (2024), `10.2478/ijme-2024-0011` —— 自称 Baur 研究的 extended reproduction，结论原文 **"the autumn effect on the gold market has been reversed and replaced by the winter effect"**。 |
| **度量** | 月度收益按**每月最后一个有报价交易日**的定盘价计；显著性用单样本 t（预先声明单尾）+ 符号检验旁证。 |
| **价格源** | **LBMA 官方定盘价**（`https://prices.lbma.org.uk/json/gold_pm.json` / `silver.json`，免登录）。黄金起 **1968-04**、白银起 **1968-01**。⚠️ 不要用 yfinance 的 `GLD`(2004) / `GC=F`(2000) 当"最长可得"——那是工具的边界不是世界的边界。 |
| **我们自己的复核** | [`data/research/gold_autumn_2026-09/`](../research/gold_autumn_2026-09/results.md)：样本内复现出 +2.52% / +1.89%（仪器校准通过）；**Baur 样本之后的 2011–2026 全部 NULL，九月翻负 4/15**。 |

**两条给下次用的判词**：

1. **中文的「金9银10」和英文文献对不上。** 学术结果是**九月＋十一月**；
   「十月」那一半在标准里没有任何对应结果，两个窗口两种金属都不显著。
   写进任何对外内容之前先知道这件事。
2. **这里的假设是文献点名的，不是从 12×2 里挑的**，所以多重比较用 **×(点名个数)** 而不是 ×24。
   反过来说：谁要重开一轮「哪个月最好」的搜索，那就真是 24 次比较，
   按 `RESEARCH_PROTOCOL.md` §二先预注册。

## 相关

- 事故与实测数字：[nhnl_4w.md](../research/canary_2026-08/nhnl_4w.md)
- 研究纪律（预注册/证据分级/holdout）：[RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md)
- 数字的唯一权威源：`KNOWLEDGE.md` 数字权威表（本表管**口径**，那张表管**数值**）

来源：[StockCharts ChartSchool 市场指标目录](https://chartschool.stockcharts.com/table-of-contents/market-indicators) ·
[Barchart 新高新低汇总（池子排除规则）](https://www.barchart.com/stocks/highs-lows/summary) ·
[AAII: Using New Highs and New Lows to Measure Market Breadth](https://www.aaii.com/journal/article/455994-using-new-highs-and-new-lows-to-measure-market-breadth)
