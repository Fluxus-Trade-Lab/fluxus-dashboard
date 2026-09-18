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
| 回撤三段计时(`drawdown_pit` 研究) | Drawdown / Underwater curve | close 基准 running-ATH;峰→谷 / 谷→复原 / 总水下(Morgan Stanley Counterpoint Global, *Drawdowns and Recoveries*) | ✅ 照抄(`data/research/drawdown_pit_2026-09/`,2026-09-11) |
| 中期选举季节窗(`midterm_perm` 研究) | Stock Trader's Almanac "Sweet Spot" | 中期年 Q4(10/1)→次年 Q2(6/30);原帖两窗(选举日→+12m、11/1→6/30)作为**变体**并列复刻,已明标非标准 | ✅ 标准窗照抄(`data/research/midterm_perm_2026-09/`,2026-09-11) |
| `mcclellan_osc` | McClellan Oscillator | RANA = net/(adv+dec)×1000，19 与 39 日 EMA 之差；原始口径统计 **NYSE** 上涨/下跌家数 | ⚠️ **公式一致、池子不一致**（2026-09-18 复查改判，原写 ✅）：我们用 Finviz 全池（`ind_stocksonly`），不是 NYSE。±70 极值线查无一手出处（StockCharts 用 ±50/±100）。见 `data/research/metric_audit_2026-09-18/B_market_layer.md` |
| `ad_line` | Advance-Decline Line | 净涨跌家数累加 | ✅ 一致 |
| `t2108` | Worden T2108 | 40 日均线上方占比；TC2000 官方口径是 **NYSE** 股票（[TC2000 help](https://help.tc2000.com/m/69404/l/755052-t2108-of-stocks-above-40-day-pma-also-t2s-110-112-114-116)） | ⚠️ **公式一致、池子不一致**（2026-09-18 复查改判，原写 ✅）：我们用 Finviz 全池。页面分档 <20 超卖 / >80 超买与 Stockbee 一致；**40 / 60 的 weak/strong 查无标准，是自造分档** |
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
| `pct_above_*_sp500` / `t2108_sp500` | StockCharts **$SPXA200R** 等 | 挂在具名指数上 | ✅ **一致**（2026-09-04 落地）。成分来自 Finviz `idx_sp500`（503 支，含双重股权）。成员拿不到时给 NULL，**不回退全池**。⚠️ 09-04→09-09 五晚**实际全是 NULL**：`in_sp500` 设在了 `compute_universe_scores` 的副本上，breadth 拿的是原 frame（`87663899` 修复） |
| `sp500_members` 名单本身 | S&P Dow Jones Indices 官方成分股 | 官方按需调整，非固定周期 | ✅ **每晚现抓**（Finviz `idx_sp500`）。历史换手率约 **4.4%/年 ≈ 22 次**，且**不集中在季度调仓**——1995 年以来落在 3/6/9/12 月第三个周五的反而是少数，多数由并购/退市/不再合规触发，任何一天都可能发生，所以不能降频成「一年查一两次」。名单与变动流水存 `data/reference/sp500_members{,_log}.csv/json`（2026-09-10 建），支持按日回放；单晚变动 >15 只或总数 <480 判为抓漏，拒绝写入并沿用上一版 |
| `market_light.spy.light` / `checks[]` | 课程 **L6 交通灯**（SwingMasterclass） | SPY 日线 10 vs 20：10 在 20 上 + 两条都上倾 = 🟢，**其余一律 🔴**（`L6:183`） | ✅ **一致**（2026-09-11；**Andy 裁「用EMA」，缺口一关闭**）。EMA10/20 `adjust=False`，**「上倾」= 今日 > 昨日是自造操作化**（Studio Q L106）。课程已按 EMA 改印（权威源 课程仓 `_bench/l6_light.json` `coverage_ema_spec`）：**两段最长连续 2017-11-16→2018-01-29 / 2026-02-27→03-30 逐日复现**，绿 56.5 对上；红书印 19.4、我们冻结夹具 19.30——复权序列随下载日漂移（Studio Q），末位不断言。旧 SMA+3 天那套作为 `coverage_chart_spec` 留档；⚠️ 本表首版曾误写它「任何口径都复现不出」，是我只扫了网格两条边 |
| ~~`market_light.spy.plus_n`~~ | 课程 L6B.4 +N/−N 周期计数 | 收盘 vs 21 日线同号游程，≤4 天剔除 | 🗑 **已删**（2026-09-11，Andy「ok删除」；课程仓 `850690a8` 整族出书、`cycle_bench.json` 一并删除）。存活期间 SPY/QQQ 各 7 项逐字复现过；market_light 同日下掉该字段 |
| `market_light.spy.gear` | 课程 **L6B.2 油门七档**（Webster） | 21 EMA、用**最低价**读线；七条规则逐条覆盖、编号大者胜；「急刹」= 今收破且昨收上、前 30 天 ≥22 天低点在线上 | ✅ **一致**（2026-09-11）。**逐字照抄** `_pdf/charts.py::throttle_gears`；复现课文对 MA 2025 图的三句话（急刹 02-21、最大防御 03-05、第 1 档从不触发） |
| `market_light.brightness.setups` | 课程 **L7-Q1** setup 数 | 10+ → 🔥、1-3 → 暗绿、0 → 当红（`L7:49-50`）——**数的是人工精选名单上的手数** | 🚫 **不投票，只显示（Studio Q 裁三终局 2026-09-11，§七 校准报告行下 ↳）**。校准放弃不是待办：四种课程语义收窄的红灯日中位 68/14/25/7 都到不了 1–3——课文数的那张人工名单在系统里不存在，⛔ 不许再加过滤器凑锚。`count` = watchlist `entries` 五面板去重名字 ∩ 2 周档 `Leading` 主题组成员（与 Q2 同池），标 `label: index — not the course's hand count`，**无 band、不配色**；Leading 池缺失时 `count` 为 null（不回落到未收窄的 `pool_count`）。`q1_votes: false`；**恢复投票唯一路径**（`Q1_VOTE_RESTORE`）：出现人工日选名单制品（Focus ≤5 或六席日更）之日，Q1＝该名单当日触发数、按课文 1–3/10+ 读，不做百分位/指数换算 |
| `market_light.brightness.leaders` | 课程 **L7-Q2** 龙头在带头吗 | 最强 5-10 只（上一波或**当前主题**）站在关键均线上/继续走/盘紧 → 🔥；破位或跳空下跌 → 收手（`L7:56`） | ⚠️ **自造，provisional**。= theme_ladder 2 周档 `Leading` 且 `kind=='theme'` 的组成员里 rs_rating 前 10（并列按 3M 表现、再按代码）；状态**只看 50 日线**二元（上=holding、下=broken），21 日线另给 `above_ema21`；**跳空下跌未实现**（零阈值会把几乎每个低开都判破位，阈值待定） |
| `market_light.brightness.breadth` | 课程 **L7-Q3** 广度在确认吗 | 当天上涨多、涨跌比健康、板块轮入而非轮出 → 🔥（`L7` Q3） | ⚠️ **借用映射**（Studio Q 裁：投票卡由方向判断**降级为 Q3 证据**）。= `breadth.json` `verdict.env`：BULLISH→confirm、MIXED→mixed、BEARISH→negate。投票卡 12 票本身的口径见本表 breadth 各行 |
| `market_light.verdict` | 课程 **L7 判决** 🔥/暗绿/回避 | 红灯 = 回避（「sit still」）；**绿灯时三问如何合成，课文没给** | ⚠️ **红灯日课文独定 `avoid`；绿灯日＝Studio Q 合成（`verdict_synthetic`），只合 Q2+Q3**（裁三终局把 Q1 移出：它几乎每天读 good，等于给 🔥 押拇指，「未测量优于假测量」）：Q2 破位占比 ≤20%/中间/≥50% → good/mid/bad；Q3 confirm/mixed/negate；任一 bad→avoid、两问全 good→full、其余 dim；任一问答不出时绿灯日判决为 null（「未测」不是「中」） |
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
| thrust 投票（`THRESHOLDS['thrust'] = {count: 300, days: 2}`；分子 `up_4pct_stockbee`/`down_4pct_stockbee`） | Stockbee（Pradeep Bonde）**breadth thrust** | 「back-to-back 300-plus days」——[Understand market breadth, 2026-07-23](https://stockbee.blogspot.com/2026/07/understand-market-breadth.html)；计数口径 `(100*(C-C1)/C1) >= 4 AND V >= 100000 AND V > V1`，US common stocks、排除 ETF——[How I get the Market Monitor Numbers, 2014-08](https://stockbee.blogspot.com/2014/08/how-i-get-market-monitor-numbers.html) | ✅ **按原作者定义（2026-09-18 起，Andy「确认原作者定义准确与否，按照原作者的定义走」）**：连续两个交易日都 ≥300 才算；门槛为绝对数 300，不随宇宙缩放；分子用三条件的 Stockbee 计数；跌方向对称，两边同时成立记为 churn（中性）。「back-to-back」原文没给更多天数，取最少的 2 天。**替换掉的自造规则**（08-09..09-18）：单日、`0.113 × universe_size`、分子只看涨幅的 `up_4pct`。**已知差异**：他的宇宙是 TC2000 的 US common stocks，我们是 Finviz `ind_stocksonly` 去掉 `_EXCLUDED_INDUSTRIES`；两者没有逐票对过账。09-05 之前的归档没有 Stockbee 列，那段的 thrust 票记为「测不了」。 |
| `oops_buy` / `oops_sell` | Larry Williams **Oops!**（《Long-Term Secrets to Short-Term Trading》1999） | buy：今开 < 昨低 且 今高 ≥ 昨低；sell：今开 > 昨高 且 今低 ≤ 昨高。跳空必须严格 | ✅ **一致**（2026-09-05 落地，Andy「A 做」）。TraderLion 借的是这个名字，本机 Trade-Lab 图集标了 23 次但一句定义都没有——定义是 Williams 的。**只做触发不做「守住了没」**，后者不在定义里 |
| `new_highs_4w` / `new_lows_4w` | *(查过，无标准)* | 52 周是机构惯例；该时间尺度的标准量是 %above-20MA / T2108 / McClellan | ⚠️ **自造**。仅供研究，不得当标准读数上页 |
| — | McClellan Summation Index | McClellan 振荡器累加 | 🔲 我们没有 |
| — | Arms Index (TRIN) | (adv/dec)÷(上涨量/下跌量) | 🔲 我们没有 |
| — | Bullish Percent Index | P&F 买入信号占比 | 🔲 我们没有 |
| —（拟 `climax_signs`） | O'Neil **Climax Top / Climax Run** | 长期上涨（典型 ≥18 周）之后加速的 1–2 周终段，同时看七个征兆：①**exhaustion gap**（跳空高开于昨日高点之上，重量）②**该轮最大单日涨幅** ③**该轮最大单日成交量** ④连续 7–8 个上涨日（或 10 日中 8 日涨）⑤**该轮最大周振幅**（周高−周低大于本轮起点以来任何一周）⑥价格刺穿上轨通道线（该线由 4–5 个月内 ≥3 个高点连成）⑦距 200 日均线 +70~100% 以上 | 🔲 **我们没有**。七条里只有第 ⑦ 条现成（`sma200_dist`）；①②③⑤⑥ 需要「本轮上涨起点」这个锚，而我们**没有任何字段定义"本轮"** |
| —（拟 `ftd`） | O'Neil / IBD **Follow-Through Day** | 前置：指数创新低后出现 **rally attempt 第 1 天**（当日收盘高于开盘 / 高于前收，或小跌但收在当日区间上半部）；随后 2、3 日**不得跌破第 1 天的低点**，跌破则重新计数。**第 4 天或以后**（最佳 4–7 天，最迟约 10 天）某大盘指数**收涨 ≥1.25%**（IBD 现代口径抬到 **≥1.7%**，2% 更好）**且成交量高于前一交易日**——成交量只需高于前一日，不要求高于均量 | 🔲 **管线没有**，且**指数成交量在 `data/output/` 里根本不存在**。研究侧有一版自用检测器（09-07，vault 模型册用，**不在本仓库**），口径与读数见下方「FTD 口径」节 |
| —（拟 `dist_day` / `dist_count_25`） | IBD **Distribution Day** | 某大盘指数（Nasdaq Composite 或 S&P 500）**收跌 >0.2%** **且当日成交量高于前一交易日**（同样只要求高于前一日，不要求高于均量）。计数看**滚动 25 个交易日**窗口；一天在下列任一条件下出列：已过 25 个交易日，或指数自该日收盘起**涨 ≥5%**。**4–5 天 = Under Pressure，6 天以上通常先于回调** | 🔲 **我们没有**；缺的字段与 FTD 同一个（指数日量） |
| —（拟 `sfp`） | **查过，无单一权威**。现代通用名 Swing Failure Pattern (SFP) | 通行描述：一根 K 线的**影线**穿越前一个 swing high / swing low，**收盘回到该极值之内**。Wyckoff 谱系里的对应物是有阶段前提的 **Upthrust After Distribution (UTAD)** 与 **Spring / Shakeout**；SFP 是把同一机制**剥掉阶段前提**推广到任意 swing 极值 | ⚠️ **不得当作标准读数**。同一形状在四套体系里叫四个名字（Wyckoff upthrust / Wilder failure swing / SFP / SMC 的 liquidity sweep），**没有一套给出可判定的数值门槛** |
| —（拟 `weinstein_stage`） | Weinstein **Four Stages**（原书 Ch.2） | 以 **30 周均线（30-week MA）的斜率 + 价格相对它的位置**判定：**Stage 1 基地区**＝MA 由跌转**平**，价格在 MA 上下来回、仍在阻力位下方的箱体内；**Stage 2 上升期**＝价格**放量突破阻力区与 30 周 MA**，MA 突破后不久**转升**，此后每次回调都**守在上升的 MA 之上**、峰与谷双双抬高；**Stage 3 顶部区**＝MA 失去上升斜率**转平**，价格开始在 MA **上下反复穿刺**（Stage 2 时回调始终守在 MA 上或之上），放量滞涨（churning）；**Stage 4 下跌期**＝价格**跌破支撑区**、MA **下行**且价格在 MA 之下（**破位不需要放量也成立**，放量更凶） | 🔲 **我们没有**；**30 周均线的值与斜率两个都没发**（见下） |
| —（拟 `vcp_contractions`） | Minervini **Volatility Contraction Pattern (VCP)** | 整理期内**2 到 6 次逐次变浅的回撤**（理想 2–4 次），**每次约为前一次深度的一半**（示例 25%→15%→8%→3%，或 20%→10%→5%）；**成交量随之收缩，末端出现明显的 volume dry-up**；Minervini 用 **"footprint" 速记**记录（周数、最大回撤/最小回撤、收缩次数，写成 `2T`/`3T`/`4T`，T = 收缩次数）；买点＝突破 pivot 且**放量** | ⚠️ **有可引定义，但只有作者本人的散文式描述——"每次约一半"没有容差、"volume dry-up"没有阈值** |
| `vcs` | oratnek **Volatility Contraction Score v2**（**不是 VCP**） | ATR13/ATR63、stdev13/stdev63、vol5/vol50 三个比值加权 0.4/0.4/0.2，乘 trendFactor，EMA3 平滑 + daysTight 奖励 | ✅ 一致（`pipeline/screeners/vcs.py`，逐字移植自 `indicators/third_party/oratnek_vcs_v2.pine`）。**它测的是压缩程度，不是收缩次数**——与 VCP 同源不同物 |
| `power_trend`（`signals.json` 五项 + `PowerTrend.jsx`） | **Mike Webster / IBD Market School — Power Trend**（**不是 Minervini**） | 四条同时成立才**开启**：①**当日最低价**在 **21 日 EMA 之上，已连续 ≥10 个交易日** ②**21 日 EMA 在 50 日 SMA 之上，已连续 ≥5 个交易日** ③**50 日 SMA 处于上升**（斜率向上）④**当日收盘高于开盘**（阳线）。**关闭**：21 日 EMA 下穿 50 日 SMA（另有两条提前失效：指数在距高点 >10% 时跌破 50 日线；指数收盘跌破当初那个 follow-through day 的最低价） | ⚠️ **五项检查与标准口径无一条对上**（逐条对照见下） |
| —（拟 `adx14`） | **"均线缠绕所以忽略均线" ——查过，无标准。** 但它想表达的那件事**有标准**：Wilder **ADX**（趋势有无） | Wilder《New Concepts in Technical Trading Systems》(1978)：**ADX < 20 = 无趋势**，ADX > 25 = 强趋势，20–25 是灰区 | 🔲 **我们没有 ADX**。这是本轮唯一「口语说法无标准，但它指的现象有一个干净的标准量，而我们恰好没建」的词条 |
| `conditions.today` → 页面 **Market Conditions 0-100** | oratnek 的 **Market Conditions** | 15 个条件对绝对中性线取正项占比，EMA-2 平滑（`breadth_signals.py:conditions_series` docstring 自认「Oratnek's construction」） | ⚠️ **构造复刻、数值从未对表**（与 rs_line_pctl 的 29/29 不同，这个连一次都没对过）。Andy 2026-09-06 先裁「选A」，后裁「可以直接闭了。欠条烧掉」——**免验结案，名字保留**。状态如实留 ⚠️（对表这件事没发生过，不伪造 ✅）；哪天他页面的图顺手到了，随手可补验 |
| `audit_events_vs_bars` 的两条恒等式 + 帧归属（审计闸，**不上页**） | Reconciliation / cross-source validation | 逐单元格比对独立来源 + 容差 + 覆盖率同报；**不规定**具体容差，也没有「帧归属」这一步 | ⚠️ **容差与判定线是自造的，按实测空档定**：①`change_pct` 对 `close/前收−1`，容差 0.005、判定线 0.90（Zac 2026-09-11）；②`volume` 对当日 bar 量，**单边带** [0.90, 1.01]、判定线 0.80、同票同量计一票（Zac 2026-09-14；Finviz 一侧只偏低，成因未证实，带依赖运行时刻）；③帧归属（best-matching bar date）查无标准名，只在判红后给线索；④**「当晚临时量不判」窗口**：K 线库最新一根 bar 若 `fetched_at` 与之同日或次日（UTC），volume 不判它——自造，依据 09-15 实测库量比次日终值少 1–10%、Finviz 与终值差 <0.3%（DATA ALEX 2026-09-17，`_mark_provisional`）。依据与分辨率全在该文件 docstring |
| `rel_volume` | Finviz **Relative Volume**（当日量 ÷ **3 个月**均量） | 当日量 ÷ **20 日**均量（`yfinance_adapter.py:1039,1205`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表）。窗口与 Finviz 不同；页面提示写成「3-month average (Finviz construction)」是错的，已转 UI Claire。20 日窗与 `avg_volume` 同源（`themes/__init__.py` 已声明） |
| `rs_1m` / `rs_3m` / `rs_6m`（别名 `rs_21d` / `rs_63d`） | 形状近 IBD **RS Rating**（横截面 1–99） | 各自窗口收益在 `tradeable` 池内的横截面百分位 ×99（`run_all.py:363-417`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表）。IBD 只公开 12 个月加权、全市场池；我们是单窗 1/3/6 月 + 自划池。`run_all.py:394-409` 注释说收益来自 Finviz 日历窗，与 `finviz_adapter.py:161-165`（免费版不抓 Perf 列）矛盾，收益实际来自 yfinance 日线 |
| `f_score` → 新名 `growth_score` | ⚠️ 撞名 **Piotroski F-Score**（9 项财报二元打分 0–9） | `eps_growth_next_y` 与 `revenue_growth` 两个百分位取均值，缺失记 50（`run_all.py:477-480`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表），与 Piotroski 毫无共同定义。按撞名规则改名 `growth_score`：数据端先双发，UI Claire 切换后删旧名（§七 2026-09-18） |
| `i_score` | 近 IBD **Industry Group RS Rating**（197 组排名，公式未公开） | 行业内 tradeable 成员 `rs_3m` 中位数再排名（`run_all.py:494-496`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表）。形状对齐 IBD 组排名，公式自造 |
| `trend_base` | 自称「Weinstein 式 Stage 2 闸」 | close > SMA50 且 周线 10 均 > 30 均（`yfinance_adapter.py:1113-1122`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表）。注释写「10WMA > 30WMA」，代码是简单均线（`rolling().mean()`）；Weinstein 原文要求 30 周线**上升**，这里没有斜率条件，不能叫 Stage 2 |
| `momentum_97` 列（universe.json） | ⚠️ 撞名三处：`momentum_97.json` 筛子、oratnek「Momentum 97」 | 1 周收益全池分位 ≥0.97 且 3 月分位 ≥0.85（`run_all.py:641-644`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表）。同名的 `momentum_97.json` 是四窗等权综合分位前 3%，两者不是同一个量；oratnek 的查无公开定义 |
| `perf_1w_pctile` / `perf_3m_pctile` | 查过，无标准 | 全池横截面分位（`run_all.py:637-639`），分母与 `rs_*` 的 tradeable 池不同 | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表） |
| `days_since_52wh` | 查过，无标准（各家只有「N 日内创 52 周高」布尔） | 距 52 周高点那根 K 线的交易日数（`yfinance_adapter.py:1211`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表），驱动 Short List「52wh 回撤」席 |
| `range5_pct` | 查过，无同名标准（近亲 Deepvue RMV 公式未公开、Crabel NR7 是单根区间） | 5 日最高最低包络 ÷ close ×100（`yfinance_adapter.py:1225`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表），驱动 Short List 席位排序 |
| `dist_hi20_pct` | 近亲 Donchian 20 日上轨（用 **High**） | 距 20 日**收盘**高点的百分比（`yfinance_adapter.py:1226`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表），用收盘不用 High，与 Donchian 不同 |
| `pp_count_30d` | Pocket Pivot（Morales/Kacher）是单日事件 | 30 日内 pocket pivot 次数（`yfinance_adapter.py:1254`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表），30 日滚动计数查无标准 |
| `ema21_atr_dist` | ATR Matrix（SteveDJacobs）的 EMA21 变体 | (close − EMA21) / ATR（`run_all.py:593-601`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表）。代码注释已写「our own quantity」；与已登记的 `atr_from_sma50`（B/A 式）故意不同式 |
| `eps_growth_next_y` / `eps_growth_this_y` | ⚠️ 撞名 Finviz **EPS next Y / EPS this Y**（财年 EPS 增速、分析师预估） | next_y = forwardEps / trailingEps − 1；this_y = yfinance 单季 YoY（`fundamentals_store.py:84-89`） | ⚠️ **自造，2026-09-18 补登记**（自造数字复查 A 表）。不上页，但喂 `growth_score`；名字与 Finviz 列同名不同义 |
| 前端：ETF 组内 RS（`frontend/src/lib/etfRank.js`，行业/板块卡上的 0–99） | 形状同 IBD **RS Rating**（横截面 1–99） | 窗口收益在**卡片自己那一组 ETF**（11 个板块或行业 ETF 列表）内的百分位 ×99，构造抄 `run_all.py::rank_tradeable` | ⚠️ **前端自造，2026-09-18 登记**（UI Claire，自造数字复查 ⑪）。分母是卡片那一组，不是个股的 tradeable 池——板块的 75 与个股的 75 不是同一个断言，卡片已写明 cohort。不改名：页面标签是 Andy 09-06 亲定 |
| 前端：rotation `rs2w` → 页面 **RS Last 2 weeks** | 查过，无标准 | 相对 SPY 的相对指数 10 个交易日变化 `rel[t]/rel[t−10]−1`（`rotationLogic.js::r2wSeries`）；缺相对指数时退回 `rs_0_1w + rs_1w_1m/3.2` | ⚠️ **前端自造，2026-09-18 登记**（UI Claire，⑪）。只在浏览器算，不上后端；页面标签 Andy 09-06 亲定 |
| 前端：rotation `wkAccel` → 页面 **RS This week vs prior 3** | 查过，无标准 | 本周相对强度 − 前三周平均周速度 `rs_0_1w − rs_1w_1m/3.2`（`PRIOR_WEEKS=3.2`）（`rotationLogic.js::wkAccel`） | ⚠️ **前端自造，2026-09-18 登记**（UI Claire，⑪）。和后端 `rs_accel` 不是同一个量 |
| 首页 **Market conditions** 条的档位词（`frontend/src/components/dashboard/RegimeBand.jsx`） | 查过，无标准 | `conditions.today` 切五档 18/40/62/84，再被 breadth / structure / Power Trend 三个投票人里**最弱的**一个往下拉（只拉低不抬高） | ⚠️ **前端自造，2026-09-18 登记**（UI Claire，⑧）。选的是「页面标明」而不是搬进后端：卡头改为「Market conditions · our composite」+ 悬停说明。与后端 `regime.py` 的 47/63/75 是**两套不同分档**，别混用 |
| ATR from SMA50 的 **0–4 建仓 / 5–7 持有** 两档（`WatchlistPage.jsx` 悬停） | Jacobs / Jeff Sun 的 ATR 带（出自 `atr_enrichment.py:66` 注释） | 0–4 / 5–7 / ≥7；7.0 本身归 ≥7（与 `watchlist.py:246` Extended 面板一致，09-18 前端改 `<7`） | ⚠️ **出处未核原文，2026-09-18 登记**（UI Claire，⑨）。≥7 减仓已由 TradeDudeNYC 行登记；0–4/5–7 这两档只有代码注释出处，4–5 之间是空档 |

来源（本批 2026-09-06 追加，源 [`recap_vocab_sources_2026-09-06.md`](../research/ops/recap_vocab_sources_2026-09-06.md)；Andy 批「候选行批了，Power Trend 改判定对齐 Webster，撞名立机制」，口语三词 hot potato / the tell / lone standout 被裁「都是口语，忽略」，未登记）。

## FTD 口径（2026-09-07 登记）

> **合入说明（Nighty Zac 2026-09-17，OPS 门铃）**：本节 09-07 写在主树、从没提交，今晨只把这一节合进 main 版，表格里不另开 `ftd` 行（09-06 已有「拟 `ftd`」行，已在该行状态列指到这里）。两处与该行不一致，以该行为准：①Day 1 判据，该行写的是「收盘高于开盘/前收，或小跌但收在当日区间上半部」，本节只写了「第一个上涨日」；②「跌破 Day 1 低点重新计数」该行已列为通行口径，本节当时按自造记账。⚠️ 下表与阳性对照的数字是 09-07 登记时的读数，**生成它们的检测器代码不在本仓库，今晨未复算**；引用前先找到代码复算。

**为什么查**：要给 `60_ModelBook/02_市场底部/` 建市场底部册，起手是 2020 年那个窗口。
按本表的规矩，先查有没有专业口径——**有，而且很明确**，所以照抄，没自己造。

**照抄的部分**（来源见文末）：
- `Day 1 of the rally attempt` = 「**the first up day from a bottom in the major indexes**」
- FTD 只能出现在 **Day 4 或之后**（「I only allowed for Follow Through Days to qualify starting Day 4 as per IBD」）
- 当日**涨幅 ≥1.7%**，且**成交量高于前一日**
  （原始口径是 ≥1%；IBD 后来上调到 1.7%，理由是「volatility had increased in the market」）

**⚠️ 自造的部分（三个，必须明写）**：
1. **「bottom」怎么操作化**——我用「收盘价创 20 日新低，且距 252 日收盘高点回撤 ≥8%」。
   原文只说 "from a bottom"，**没给判据**。20 日 / 8% 两个数是我拍的。
2. **尝试何时作废**——盘中低点跌破 Day 1 当日低点即重新计数。这条是 IBD 的通行做法，
   但我没找到它的原始出处，**按自造记账**。
3. **修复退出**——指数收回 Day 1 那天的 252 日高点即放弃计数。
   纯粹是我加的，防止一次尝试在整段牛市里一直数下去（未加之前出现过 Day 338 的荒唐读数）。

**⭐ 阳性对照（外部真值，不是自我验证）**：
《2018-2020 TraderLion Model Book》**独立地**写着「AMZN broke out through \$1,933.02 on **April 6th
as the NASDAQ followed through**」「CRWD…on April 7th, **one day after** the NASDAQ followed through」
「DOCU…on March 30th **about a week before** the NASDAQ followed though」。
我的检测器在 ^IXIC 上给出的 2020 年唯一春季 FTD 是 **2020-04-06**（Day 10，+7.33%，量 ×1.17），
**与这三句话全部自洽**。这是外部来源的复现，不是我拿自己的规则验自己。

**⚠️ 实测：这个信号本身没有可测的择时优势（1998-01 ~ 2026-09，^IXIC / ^GSPC）**

| | ^IXIC | ^GSPC |
|---|---|---|
| FTD 条数（1.7% 口径） | 65 | 45 |
| 一年内跌破 Day 1 低点（＝失败） | **58%** | **58%** |
| 失败的中位耗时 | 20 个交易日 | 27 个交易日 |
| FTD 后 +252 日中位涨幅 / 胜率 | +17.9% / 73% | +12.7% / 68% |
| **同期「已回撤 ≥8% 的任意一天」基线** | **+17.8% / 66%** | **+13.3% / 65%** |

→ **中位涨幅几乎完全相同**（17.9 vs 17.8；12.7 vs 13.3）。胜率高 5–7pp，但 n=65/45，
落在噪声里。**结论：FTD 不是一个能提高指数前瞻收益的择时信号。**
这与 Quantifiable Edges 1971–2008 的独立回测方向一致（他测出 55.7% 的"成功率"，
而 IBD 宣称 70–80%）。

→ **但这不等于它没用**：模型册里它的实际用法不是预测指数，是**给个股突破定位一个时间窗**——
2020 年 12 只龙头有 10 只在 FTD 的 −5 ~ +3 个交易日里突破。
⚠️ 那 12 只是 Ross 事后挑的，**挑的人本来就用 FTD 思考**，所以那个聚集**不是独立证据**，
只是「他们怎么用这个概念」的示范。要证明聚集，得用一个不知道 FTD 的名单重做。

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


FTD 口径来源：[Quantifiable Edges — IBD Follow Through Days pt.1（含 1971-2008 独立回测）](https://quantifiableedges.blogspot.com/2008/01/ibd-follow-through-days-pt-1-are-they.html) ·
[TraderLion — Follow Through Day](https://traderlion.com/trading-strategies/follow-through-day/)（正文 403，仅作出处登记，未取用其文字）

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
