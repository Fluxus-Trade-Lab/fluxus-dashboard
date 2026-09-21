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
| `bo_count_1m/3m/6m/1y` 的**判定** | Stockbee 4% Breakout | 涨幅 ≥4% **且** 量 > 前一根 **且** 量 > 100,000 | ✅ **一致**（2026-09-04 落地）。此前是 `量 ≥ 9,000,000 且 涨幅 ≥4%`——9M 来自另一个扫描（Stockbee 9 million breakout，[2019-09-23](https://stockbee.blogspot.com/2019/09/simple-scan-that-can-make-you-millions.html) 正文是**当日量** `v>=8900000`；`maxv65>=8900000` 是他 2019-09-14 评论里的另一个扫描——65 日内出过 9M 大量日的观察池。**2026-09-18 更正**：此处原写「在那里指 maxv65」是张冠李戴），而 9M 日地板对大盘股恒真，于是缺失的放量条件从未生效，剩下的只是「今天涨了 4%」 |
| `bo_count_*` 的**聚合** | *(无标准)* | Stockbee 的是**单日横截面广度**（今天全市场有多少只） | ⚠️ **自造**：逐票纵向滚动计数。已在代码里明写 |
| `h_score_pctl` → 页面 **Composite Score** | IBD Composite Rating 的**形状**（多因子合成后再排 1–99） | 合成后必须再排名成百分位 | ✅ 排名一致（2026-09-04 落地）。**权重是自造的**：IBD 六个系数专有、查无可引用的表；20% 基本面 + 30% 行业 + 50% RS。Andy 09-04 定名 Composite Score，不再叫 RS |
| `h_score`（原值） | *(无标准)* | 五个百分位的加权平均 | ⚠️ **自造且不是百分位**（顶档 0.6%、IQR 29）。保留仅为归档连续性，**不上页** |
| `three_weeks_tight` / `twt_buy_point` | IBD **3 Tight Closes** | 每周收盘与**前一周**相差 ≤1.5%、连续三周；买点 = 三周最高 + $0.10——本机 `CAN_SLIM_Chart_Pattern_Cheat_Sheet.pdf` | ✅ **一致**（2026-09-04 落地）。相邻两两比较，不是全域带宽 |
| `wk_band_3` | *(无标准)* | — | ⚠️ **自造**：三根周收盘的全域带宽 ≤1.5%。原名 `wk_tight_3`，冒充了 IBD 的形态名。保留仅为让 08-20 紧致度研究可复现 |
| `bar_scale_jumps` | 厂商数据质检通行做法 | ①复权 vs 未复权比对 ②逐日收盘比落在拆股比上——[FMP](https://site.financialmodelingprep.com/how-to/how-to-compare-adjusted-vs-unadjusted-stock-prices-with-a-free-api) · [StockCharts](https://help.stockcharts.com/data-and-ticker-symbols/data-availability/price-data-adjustments) | ⚠️ **标准形状**：①在 MNST 上失效（两个 feed 同样错乱），只能用②；容差 0.03（对数空间）与「当日 H/L 解释不了该跳空」这第二条件是我们加的 |
| `pct_above_*_sp500` / `t2108_sp500` | StockCharts **$SPXA200R** 等 | 挂在具名指数上 | ✅ **一致**（2026-09-04 落地）。成分来自 Finviz `idx_sp500`（503 支，含双重股权）。成员拿不到时给 NULL，**不回退全池**。⚠️ 09-04→09-09 五晚**实际全是 NULL**：`in_sp500` 设在了 `compute_universe_scores` 的副本上，breadth 拿的是原 frame（`87663899` 修复） |
| `sp500_members` 名单本身 | S&P Dow Jones Indices 官方成分股 | 官方按需调整，非固定周期 | ✅ **每晚现抓**（Finviz `idx_sp500`）。历史换手率约 **4.4%/年 ≈ 22 次**，且**不集中在季度调仓**——1995 年以来落在 3/6/9/12 月第三个周五的反而是少数，多数由并购/退市/不再合规触发，任何一天都可能发生，所以不能降频成「一年查一两次」。名单与变动流水存 `data/reference/sp500_members{,_log}.csv/json`（2026-09-10 建），支持按日回放；单晚变动 >15 只或总数 <480 判为抓漏，拒绝写入并沿用上一版 |
| `market_light.spy.light` / `checks[]` | 课程 **L6 交通灯**（SwingMasterclass） | SPY 日线 10 vs 20：10 在 20 上 + 两条都上倾 = 🟢，**其余一律 🔴**（**L6.1「绿灯三问」**；⚠️ 原引用 `L6:183` 是行号，课程改版后已作废，2026-09-21 起改按小节名引——课程仓实测 `M2_L06_Market_Cycle_Filter.md` 三条判据与「Any no → 🔴 RED LIGHT」都在 L6.1，不在 L6.2 Core Drill） | ✅ **一致**（2026-09-11；**Andy 裁「用EMA」，缺口一关闭**）。EMA10/20 `adjust=False`，**「上倾」= 今日 > 昨日是自造操作化**（Studio Q L106）。课程已按 EMA 改印（权威源 课程仓 `_bench/l6_light.json` `coverage_ema_spec`）：**两段最长连续 2017-11-16→2018-01-29 / 2026-02-27→03-30 逐日复现**，绿 56.5 对上；红书印 19.4、我们冻结夹具 19.30——复权序列随下载日漂移（Studio Q），末位不断言。旧 SMA+3 天那套作为 `coverage_chart_spec` 留档；⚠️ 本表首版曾误写它「任何口径都复现不出」，是我只扫了网格两条边 |
| ~~`market_light.spy.plus_n`~~ | 课程 L6B.4 +N/−N 周期计数 | 收盘 vs 21 日线同号游程，≤4 天剔除 | 🗑 **已删**（2026-09-11，Andy「ok删除」；课程仓 `850690a8` 整族出书、`cycle_bench.json` 一并删除）。存活期间 SPY/QQQ 各 7 项逐字复现过；market_light 同日下掉该字段 |
| ~~`market_light.spy.gear`~~ | 课程 **L6B.2 油门七档**（Webster） | 21 EMA、用**最低价**读线；七条规则逐条覆盖、编号大者胜；「急刹」= 今收破且昨收上、前 30 天 ≥22 天低点在线上 | 🗑 **已删**（2026-09-21，Andy「L6B.2 --L6B.6全部删除」；课程只剩 L6B.1「三条线，三群人」）。存活期间逐字照抄 `_pdf/charts.py::throttle_gears`、复现过课文对 MA 2025 图的三句话（急刹 02-21、最大防御 03-05、第 1 档从不触发）；`market_light` 同日下掉该字段（`instrument_block()` 不再返回 `gear`），`audit_ledger.EVIDENCE['market_light']` 同步摘掉 `gear` 证据要求。`gear_series`/`GEARS` 仍留在 `pipeline/screeners/market_light.py`，只是不再进入输出 |
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
| `new_highs_4w_sp500` / `new_lows_4w_sp500` | *(查过，无标准；池子按 Andy 2026-09-21 指定)* | Andy 原话「4周净新高新低是SP500的成分股。」课程 §07.6 已按此写进书。窗口本身仍是上一行那个自造的 4 周，这里只是把池子从全宇宙换成 `in_sp500`（同 `pct_above_*_sp500` 用的 Finviz `idx_sp500` 成分表） | ⚠️ **窗口自造，池子标准**。成员拿不到（`in_sp500` 缺失或为空集）或 20 日高低列缺失时给 NULL，不回退全池、不回退 0 |
| — | McClellan Summation Index | McClellan 振荡器累加 | 🔲 我们没有 |
| — | Arms Index (TRIN) | (adv/dec)÷(上涨量/下跌量) | 🔲 我们没有 |
| — | Bullish Percent Index | P&F 买入信号占比 | 🔲 我们没有 |
| —（拟 `climax_signs`） | O'Neil **Climax Top / Climax Run** | 长期上涨（典型 ≥18 周）之后加速的 1–2 周终段，同时看七个征兆：①**exhaustion gap**（跳空高开于昨日高点之上，重量）②**该轮最大单日涨幅** ③**该轮最大单日成交量** ④连续 7–8 个上涨日（或 10 日中 8 日涨）⑤**该轮最大周振幅**（周高−周低大于本轮起点以来任何一周）⑥价格刺穿上轨通道线（该线由 4–5 个月内 ≥3 个高点连成）⑦距 200 日均线 +70~100% 以上 | 🔲 **我们没有**。七条里只有第 ⑦ 条现成（`sma200_dist`）；①②③⑤⑥ 需要「本轮上涨起点」这个锚，而我们**没有任何字段定义"本轮"** |
| —（拟 `ftd`） | O'Neil / IBD **Follow-Through Day** | 前置：指数创新低后出现 **rally attempt 第 1 天**（当日收盘高于开盘 / 高于前收，或小跌但收在当日区间上半部）；随后 2、3 日**不得跌破第 1 天的低点**，跌破则重新计数。**第 4 天或以后**（最佳 4–7 天，最迟约 10 天）某大盘指数**收涨 ≥1.25%**（IBD 现代口径抬到 **≥1.7%**，2% 更好）**且成交量高于前一交易日**——成交量只需高于前一日，不要求高于均量 | 🔲 **管线没有**，且**指数成交量在 `data/output/` 里根本不存在**。研究侧有一版自用检测器（09-07，vault 模型册用，**不在本仓库**），口径与读数见下方「FTD 口径」节 |
| —（拟 `dist_day` / `dist_count_25`） | IBD **Distribution Day** | 某大盘指数（Nasdaq Composite 或 S&P 500）**收跌 >0.2%** **且当日成交量高于前一交易日**（同样只要求高于前一日，不要求高于均量）。计数看**滚动 25 个交易日**窗口；一天在下列任一条件下出列：已过 25 个交易日，或指数自该日收盘起**涨 ≥5%**。**4–5 天 = Under Pressure，6 天以上通常先于回调** | 🔲 **我们没有**；缺的字段与 FTD 同一个（指数日量） |
| —（拟 `sfp`） | **查过，无单一权威**。现代通用名 Swing Failure Pattern (SFP) | 通行描述：一根 K 线的**影线**穿越前一个 swing high / swing low，**收盘回到该极值之内**。Wyckoff 谱系里的对应物是有阶段前提的 **Upthrust After Distribution (UTAD)** 与 **Spring / Shakeout**；SFP 是把同一机制**剥掉阶段前提**推广到任意 swing 极值 | ⚠️ **不得当作标准读数**。同一形状在四套体系里叫四个名字（Wyckoff upthrust / Wilder failure swing / SFP / SMC 的 liquidity sweep），**没有一套给出可判定的数值门槛** |
| `weinstein_stage`（`wk_sma30` / `wk_sma30_dist` / `wk_sma30_rising`） | Stan Weinstein **Four Stages**（《Secrets for Profiting in Bull and Bear Markets》1988，本机 PDF） | 30 周线 = 本周五收盘加前 29 个周五收盘 ÷ 30（Ch.1）；Stage 1 = 30 周线失去下跌斜率走平、价格在均线上下来回（Ch.2）；Stage 2 = 放量突破阻力区与 30 周线，均线随后转升、回调守在上升均线之上（Ch.2）；突破量：单周 ≥ 过去一个月均量 2×，或 3–4 周累积 ≥ 之前几周均量 2× 且突破周有增加；日线脚注：突破日 > 前一周均量 2×（Ch.4 p.105） | ✅ **2026-09-18 实现**（周线状态机，`stage_analysis.py` 注释逐句引原书）。原书未给数字者为我们的操作化：斜率容差 0（本周均线对上周）、阻力 / 支撑取前 10 周高 / 低、「several weeks」取 8 周。1 年日线只够状态机跑约 22 周，更早进入的阶段由首周「价格×斜率」四象限起算。Deepvue、LuxAlgo 的阶段指标公式不公开，Steve Jacobs 的为专有代码（他本人原话），均不作口径。本机 Pine（「Candles Stage Analysis」，@TradeDudeNYC 改编）曾逐行移植，与本尺子一致率 40.4%，Andy 判未验证，**已弃用、不发布** |
| `vcp`（`vcp.json`，`vcp_detector.py`） | Minervini **Volatility Contraction Pattern (VCP)**（《Trade Like a Stock Market Wizard》第 10 章） | 收缩 "typically two to four"、"as many as five or six"；"each successive contraction is generally contained to about half (plus or minus a reasonable amount) of the previous"；量随价缩 | ⚠️ **2026-09-18 起两条构成条件参与筛选**（此前只标记不筛，Andy「全部按原文」）：收缩 2–6 次、逐次变浅、量逐次收缩。**「约一半」原文未给数字（"plus or minus a reasonable amount"），0.30–0.75 是我们对这句的操作化**（沿用旧代码）；末端 volume dry-up 无阈值，只实现为「每次收缩均量不高于上一次」；原句取自广为转引的段落，书不在本机，**非一手核对**。09-17 数据命中 27 → 4 |
| `vcs` | oratnek **Volatility Contraction Score v2**（**不是 VCP**） | ATR13/ATR63、stdev13/stdev63、vol5/vol50 三个比值加权 0.4/0.4/0.2，乘 trendFactor，EMA3 平滑 + daysTight 奖励 | ✅ 一致（`pipeline/screeners/vcs.py`，逐字移植自 `indicators/third_party/oratnek_vcs_v2.pine`）。**它测的是压缩程度，不是收缩次数**——与 VCP 同源不同物 |
| `power_trend`（`signals.json` 五项 + `PowerTrend.jsx`） | **Mike Webster / IBD Market School — Power Trend**（**不是 Minervini**） | 四条同时成立才**开启**：①**当日最低价**在 **21 日 EMA 之上，已连续 ≥10 个交易日** ②**21 日 EMA 在 50 日 SMA 之上，已连续 ≥5 个交易日** ③**50 日 SMA 处于上升**（斜率向上）④**当日收盘高于开盘**（阳线）。**关闭**：21 日 EMA 下穿 50 日 SMA（另有两条提前失效：指数在距高点 >10% 时跌破 50 日线；指数收盘跌破当初那个 follow-through day 的最低价） | ✅ **开启四条与关闭条件一致**（2026-09-06 `6e76861a` 对齐 Webster；2026-09-21 复核改判，原写「五项检查与标准口径无一条对上」已过期）：`calc_signals.py:146-213` 发四个条件布尔 + `is_power_trend` 状态机（开启＝四条同时成立，关闭＝EMA21 < SMA50，中间保持），常量 `LOW_ABOVE_EMA21_DAYS = 10`、`EMA21_ABOVE_SMA50_DAYS = 5`（`:121-123`）。**已声明的偏离**（`:102-118`）：两条提前失效未实现（FTD 低点需要指数日量，本仓没有；「距高点 >10%」没说从哪个高点量）；`sma50_rising` 取严格 `>`（书面口径「rising」，不取口述的「flat or incline」）；EMA21 用 pandas 默认 `adjust=True`。旧的五个 bool 已拆出为 `ma_structure`（自造，不挂 Webster 名） |
| —（拟 `adx14`） | **"均线缠绕所以忽略均线" ——查过，无标准。** 但它想表达的那件事**有标准**：Wilder **ADX**（趋势有无） | Wilder《New Concepts in Technical Trading Systems》(1978)：**ADX < 20 = 无趋势**，ADX > 25 = 强趋势，20–25 是灰区 | 🔲 **我们没有 ADX**。这是本轮唯一「口语说法无标准，但它指的现象有一个干净的标准量，而我们恰好没建」的词条 |
| `conditions.today` → 页面 **Market Conditions 0-100** | oratnek 的 **Market Conditions** | 15 个条件对绝对中性线取正项占比，EMA-2 平滑（`breadth_signals.py:conditions_series` docstring 自认「Oratnek's construction」） | ⚠️ **构造复刻、数值从未对表**（与 rs_line_pctl 的 29/29 不同，这个连一次都没对过）。Andy 2026-09-06 先裁「选A」，后裁「可以直接闭了。欠条烧掉」——**免验结案，名字保留**。状态如实留 ⚠️（对表这件事没发生过，不伪造 ✅）；哪天他页面的图顺手到了，随手可补验。**输入列（2026-09-21 补记，随并行改动）**：15 个条件里读计数/比值的几项改读 Stockbee 列——`ratio_5d_stockbee` / `ratio_10d_stockbee`、`new_highs_common` / `new_lows_common`、`up/down_25pct_qtr_stockbee`、`up/down_13pct_34d_stockbee`、`net_4pct`（由 `up/down_4pct_stockbee` 相减，见本表 `net_4pct` 行）；其余（t2108、%above 20/50/200、McClellan、net_advances、SPX 1m/3m/1y 方向）不变。每一列首个有值的交易日之前，该条件记为「测不了」，**从分母里去掉**，不按 0 或中性计（`conditions_series` 的 `counted = measures.notna()`，`breadth_signals.py:670-672`）——所以早期历史的分数是更少条件上的占比，与近期不严格同尺。⚠️ 写本行时 origin/main 的 `_CONDITION_COLS` / `_CONDITION_SPREADS`（`breadth_signals.py:572-580`）仍读旧列 `ratio_5d`、`new_highs`、`up_25pct_qtr`、`up_4pct` 等，以并行改动合入后的代码为准 |
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
| 首页 **Market conditions** 条的档位词（`frontend/src/components/dashboard/RegimeBand.jsx`） | 查过，无标准 | `conditions.today` 切五档 18/40/62/84，再被 breadth / structure / power 三个投票人里**最弱的**一个往下拉（只拉低不抬高）；power 投票人读的是 SPY/QQQ 较弱者的 **Power 3** 档（`POWER_LEVEL`，`RegimeBand.jsx:72,115-129`），不是 Webster 的 Power Trend——Power Trend 四条件只出现在「binding」说明文字里（2026-09-21 更正，原写「Power Trend 投票人」） | ⚠️ **前端自造，2026-09-18 登记**（UI Claire，⑧）。选的是「页面标明」而不是搬进后端：卡头改为「Market conditions · our composite」+ 悬停说明。与后端 `regime.py` 的 47/63/75 是**两套不同分档**，别混用 |
| ATR from SMA50 的 **0–4 建仓 / 5–7 持有** 两档（`WatchlistPage.jsx` 悬停） | Jacobs / Jeff Sun 的 ATR 带（出自 `atr_enrichment.py:66` 注释） | 0–4 / 5–7 / ≥7；7.0 本身归 ≥7（与 `watchlist.py:246` Extended 面板一致，09-18 前端改 `<7`） | ⚠️ **出处未核原文，2026-09-18 登记**（UI Claire，⑨）。≥7 减仓已由 TradeDudeNYC 行登记；0–4/5–7 这两档只有代码注释出处，4–5 之间是空档 |
| `ratio_5d_stockbee` / `ratio_10d_stockbee` | Stockbee MM **5/10 日 breadth ratio** | 5（10）日三条件 4% b/o 之和 ÷ 同期 4% b/d 之和——[MM 页作者回复](https://stockbee.blogspot.com/p/mm.html)；10 日「goes above 2 … bullish breadth thrust」「below .5 … bearish thrust」——[2010-05](https://stockbee.blogspot.com/2010/05/what-you-need-to-know-about-market.html)（主会话 09-18 现场核过原句） | ✅ 分子一致；10 日线 >2 / <.5 一致（严格）；原文前提「after market has been in bearish phase for sometime」无量化口径，未实现。**5 日线 1.0 / 0.5 原文未给，⚠️ 自造**。投票 2026-09-18 起读这两列；原 `ratio_5d`/`ratio_10d`（只看价格）保留不投票 |
| `up/down_25pct_qtr_stockbee` | Stockbee **25% in a quarter** | `100*((C+.01)-(MINC65+.01))/(MINC65+.01)>=25 and AVGC20*AVGV20>=250000`（跌：MAXC65，<=-25），US common stocks——[扫描公式](https://stockbee.blogspot.com/2014/08/how-i-get-market-monitor-numbers.html) | ✅ 一致（2026-09-18）。读法：符号投票＝原文「breadth crossover confirm trend change」；水平读法（<200 为极值）未实现。复权为 yfinance 全复权（TC2000 仅拆股复权）。历史行无此列；原 `up/down_25pct_qtr`（Finviz 点到点）保留不投票 |
| `up/down_13pct_34d_stockbee` | Stockbee **13% in 34 days** | MINC34 / MAXC34、±13、同流动性条件——同上 | ✅ 一致（2026-09-18）。原 `up/down_13pct_34d` 保留不投票 |
| `up/down_{25,50}pct_month_stockbee` | Stockbee **25% / 50% in a month** | `C20>=5 AND AVGC20*AVGV20>=250000 AND 100*(C-C20)/C20>=25`（±25 / ±50）——同上 | ✅ 一致（2026-09-18），暂无投票读者；原日历月四列保留 |
| nh_nl 投票 / Board extremes 的分子 | 新高新低（普通股口径） | 读已登记 ✅ 的 `new_highs_common` / `new_lows_common` | ✅ 2026-09-18 起切换（此前读被 SPAC 污染的原始 `new_highs`/`new_lows`）；原始列仍在页面旧 key 上，待前端切换 |
| Conditions 的 `net_4pct` 条件（原名 `thrust`，Market Conditions 0-100 的 15 个条件之一） | *(查过，无标准)*；⚠️ 原名撞 Stockbee **breadth thrust** | Stockbee thrust＝连续两日 ≥300（见本表 thrust 投票行），与净计数的符号不是同一个量 | ⚠️ **自造，2026-09-21 登记**（自造数字复查 B 表 M9；Andy 2026-09-21「ok的。」）：`up_4pct_stockbee − down_4pct_stockbee` 的净数，中性线 0，大于 0 记正项。门槛 0 是「净涨过半」的自然边界（`breadth_signals.py:582-593` 注释：每条中性线要么是公开阈值、要么是自然边界）。**改名原因**：它只是一个符号，和 Stockbee「背靠背 300+」没有共同定义，叫 thrust 属撞名。⚠️ 改名与换列随并行改动落地；写本行时 origin/main `breadth_signals.py:579` 仍是 `'thrust': ('up_4pct', 'down_4pct')`（只看价格的旧计数） |
| pct200 投票 50 / 30（`THRESHOLDS['pct200']`） | *(查过，无标准切点)* | %above-200MA 本身是标准量（见本表 `pct_above_*` 行），投票切点无出处 | ⚠️ **自造，2026-09-21 登记**（B 表 M15）：`≥50` bull、`<30` bear、中间 neutral（`breadth_signals.py:64,191-200`）。50 是「一半的股票」；30 的**理由未留档**（设计文档 `docs/plans/2026-07-31-breadth-signal-engine-design.md:54` 只列数不给理由）。池子是 Finviz 全池，与任何公开读数不可比（见 `pct_above_*` 行） |
| spy_danger / qqq_danger 投票 ≤1 / ≥4 | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（B 表 M18）：五个 danger 信号里亮 ≤1 个 bull、≥4 个 bear、2–3 neutral（`breadth_signals.py:66-67,503-511`）。**理由未留档**（设计文档 `:56-57` 只列数）。同一对阈值还被 `spy_state` / `qqq_state` 复用（见下方 state 行） |
| SPY/QQQ 五个 danger 信号（`market_health.*.danger`：below_20sma · stoch_cross · stoch_down · lower_lows · close_below_lows） | *(查过，无标准组合)*；随机指标 14,3,3 是 George Lane 的通行设定 | — | ⚠️ **自造组合，2026-09-21 登记**（B 表 M19）：①收盘 < SMA20 ②快随机线 < 慢随机线 ③两条随机线同时下弯 ④连续 3 个更低的低点 ⑤收盘破前 3 根最低价（`breadth_signals.py:305-318`；随机指标 `:292-302`，H14==L14 时沿用前值）。来源只写「the reference screenshot」（`docs/plans/2026-07-30-breadth-data-v2-design.md:15`），截图是谁的没记——**出处与理由未留档**。检索「danger signals 3 lower lows below 20 sma stochastic」无果（审计 B 表） |
| bench_trend 投票 | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（B 表 M20）：SPY、QQQ 收盘都在 SMA50 上 → bull，都在下 → bear，一上一下 → neutral（`breadth_signals.py:726-730`）。只看 50 日线的**理由未留档** |
| `verdict.env` / `verdict.score`：BULLISH / MIXED / BEARISH | ⚠️ 设计文档写「**Stockbee absolutes decide**」——对合成这一层**不成立** | Stockbee 原文只说看全景（「It is total picture not just one thing」），**没有给过合成打分** | ⚠️ **自造，2026-09-21 登记**（B 表 M21）：12 票等权（ratio_5d、ratio_10d、thrust、qtr_spread、spread_13_34、mcclellan、nh_nl、pct200、t2108_zone、spy_danger、qqq_danger、bench_trend），`score = bull 票数 − bear 票数`，`≥+4` BULLISH、`≤−4` BEARISH、其余 MIXED（`breadth_signals.py:732-733`）；T2108 <20 / >80 覆盖成 OVERSOLD / OVERBOUGHT（`:736-744`，20/80 见 `t2108` 行）。等权与 ±4 的**理由未留档**。单票里照原作者的是 thrust、10 日比值、两条 spread 的读法；合成这一步是我们的。它是 dashboard 头牌，也是 market_light Q3 的唯一输入（见 `market_light.brightness.breadth` 行） |
| `verdict.risk`：Low / Elevated / High | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（B 表 M22）：`warn_total` = SPY 亮的 danger 数 + QQQ 亮的 danger 数（0–10），`≤2` Low、`≤6` Elevated、其余 High（`breadth_signals.py:754-755`）。**理由未留档**（设计文档 `:68` 只列数） |
| `verdict.spy_state` / `qqq_state` / `alignment` | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（B 表 M23）：收盘 < SMA200 或 danger ≥4 → Downtrend；danger ≤1 且收盘 > SMA20 → Uptrend；其余 Mixed；两者重叠判 Downtrend（注释「deliberate: fail bearish」，`breadth_signals.py:491-500`）。`alignment` = 两个 state 相同为 Aligned，否则 Divergent（`:757-759`）。≤1/≥4 复用 danger 投票阈值；SMA20 / SMA200 这两条线的**理由未留档**。喂 RegimeBand structure 投票人 |
| `verdict.confirmation` 文案 | *(查过，无标准)* | Stockbee 原文：breadth crossover 用来确认主趋势（见本表 thrust 行、25%/季行） | ⚠️ **自造规则，2026-09-21 登记**（B 表 M24）：5 日比值、10 日比值、25%/季 spread、13%/34 日 spread 四票全 bull → 「Confirmed bull」，四票全 bear → 「Confirmed bear」，否则 Inconclusive 并写出哪一对不一致（`breadth_signals.py:761-773`）。要求四票一致的**理由未留档** |
| `verdict.exposure` / `playbook` / `guidance` 建议文案 | *(无标准)* | — | ⚠️ **自撰文案，2026-09-21 登记**（B 表 M25）：按 (env, risk) 15 格查表出仓位建议与一句话（`breadth_signals.py:432-474`）。OVERSOLD 几句引 Stockbee「back-to-back 300+ up-4% days」，与原文一致（`{thrust}` 由 `render_copy` 填当日门槛）；**其余措辞与仓位档（Full / Reduced / Defensive）都是我们写的，理由未留档**。是仓位建议，不是标准读数 |
| `verdict.context` 百分位 | *(无标准)* | — | ⚠️ **自造，2026-09-21 登记**（B 表 M26）：今天在自己历史里的百分位 `(历史 ≤ 今天).mean()`（`breadth_signals.py:821-848`）。比值类（ratio_5d、t2108、mcclellan_osc）对全档案排；计数类（up_4pct、down_4pct、nh_nl_net、qtr_spread）只在同一宇宙时代内排（断点 2026-06-26 / 2026-08-10，`:797`），同时代不足 `MIN_ERA_RANK_N = 20` 场就不给（`:799`）——理由在代码注释：跨时代的原始计数不可比，拿全档案排会把今天的 up-4% 抬高约 39 个百分点（Nighty Zac 2026-09-18）。**并行改动**：换成 Stockbee 列后，**计数只在该列自己有值的那段历史里排，历史不够就不给**（写本行时 main 仍读旧列）。只作注记，不冒充标准读数 |
| RegimeBand breadth 投票人切点 8 / 4 / −3 / −7（`RegimeBand.jsx`） | *(查过，无标准)* | — | ⚠️ **前端自造，2026-09-21 登记**（B 表 M29）：把 `verdict.score`（−12..+12）切五档：`≥8`→4、`≥4`→3、`≥−3`→2、`≥−7`→1、其余 0（`RegimeBand.jsx:87-99`）。`4` 与 `−3` 两条边正好对上 env 的 ±4（≥+4 BULLISH、≤−4 BEARISH）；**8 与 −7 的理由未留档** |
| RegimeBand power 投票人（`RegimeBand.jsx`） | 档位来自 **Power 3**（自造，见下方 Power 3 行）；说明文字列的是 Webster **Power Trend** 四条件 | — | ⚠️ **前端自造，2026-09-21 登记**（B 表 M30）：SPY、QQQ 取 Power 3 档较弱者，`POWER_3`→4、`CAUTION`→3、`WARNING`→1、`RISK_OFF`→0、未知→2（`RegimeBand.jsx:72,115-129`）；「binding」一栏打印较弱者 Power Trend 四条件里没成立的几条（`:80-85`）。**两个不同指标挤在一个投票人里**：档位量 Power 3，文字解释 Power Trend，两者可以互相矛盾。档位映射（跳过 2）**理由未留档**。首页 Market conditions 行（上方）已同步更正 |
| state_board 另外七行的切点（damage · selling pressure · breadth · trend · extremes · confirmation · index repair） | *(查过，无标准)*；设计出处 `Fluxus_Brand/visual/Fluxus_Operator_Model.md` | — | ⚠️ **自造，2026-09-21 登记**（B 表 M31）。代码注释自认「The cut points on top of them … are still ours」（`state_board.py:33-36`）。逐行：**damage** 下跌份额 `qd/(qu+qd)` >0.55 / >0.45 / >0.35（`:100`，读 Stockbee 25%/季列）· **selling pressure** 今日 Stockbee 4% 下跌数 ÷ 前 5 日峰值 <0.5 / <0.8（`:117`）· **breadth** %>20 日 >60 且净涨 >0 / >50 / >35（`:129`）· **trend** %>200 日 >50 / >40 / >30（`:138`）· **extremes** 普通股 NH > 2×NL / NH > NL / NL > 2×NH（`:167`）· **confirmation** Stockbee 5 日比值 >1.2 且净涨 >0 / >1.0（`:198`）· **index repair** SPY/QQQ 站上各自 50 日线 2/2、1/2、0/2（`:226`）。输入列 2026-09-18 已换成原作者口径；**切点本身理由未留档**（引入 commit `ae2192fe` 2026-08-09 没写）。thrust 行读引擎的 `thrust_state`，不另设切点 |
| propagation chain 的 lit / partial（0.75 / 0.05） | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（B 表 M32）：五环（index repair → thrust → breadth → extremes → confirmation）各取 `level/4`，沿链取 running minimum，`≥0.75` lit、`>0.05` partial、其余 unlit（`state_board.py:257-264`）。按五级刻度读，0.75＝上游每一环都至少到「started」，0.05 只把「有一环是 absent」分出来。**理由未留档** |
| `regime.score` + 分档 47 / 63 / 75（Damaged / Mixed / Healthy / Extended） | *(查过，无标准)*；分档是经验四分位 | — | ⚠️ **自造，2026-09-21 登记**（B 表 M33）：state_board 已测维度 level 的等权平均，0–4 映射到 0–100；分档常量冻结，不逐晚重算（`regime.py:94-130`）。理由在 docstring：等权是拒绝伪精度；切点 = 2026-08-09 档案 558 场的四分位（p25 46.9 / p50 62.5 / p75 75.0）。**2026-09-18 RND Linda 用原作者口径输入重切**（587 场，历史用 Stockbee 公开 MM 表回填）：四分位 50.0 / 64.3 / 75.0，在分数自己的格点上正好落在 47 / 63 / 75，**切点不变**；只有 Damaged 一档稳定分得开（未来 21 日内 5% 回撤频率 28.3% vs 其余三档 8.7%）——见 [`data/research/regime_recal_2026-09-18/README.md`](../research/regime_recal_2026-09-18/README.md) 与 `regime.py:45-69`。`extremes` 维度 2026-08-28 起才有数，未参与定标。与前端 RegimeBand 18/40/62/84 是两套分档；`regime.py:112-117` 注释里写的前端切点 12/34/56/78 已过期 |
| Power 3 信号（`signals.*.signal`：POWER_3 / CAUTION / WARNING / RISK_OFF） | *(查过，无标准)*——检索「Power 3 8 EMA 21 EMA 50 SMA」只有通用的「均线多头排列」说法 | — | ⚠️ **自造，2026-09-21 登记**（B 表 M34）：EMA8 > EMA21 > SMA50 > SMA200 → POWER_3；否则 EMA8 > EMA21 且收盘 > SMA200 → CAUTION；否则收盘 > SMA200 → WARNING；其余 RISK_OFF（`calc_signals.py:71-77`；`yfinance_adapter.py:1446-1455` 另有一份同式拷贝，写 `signals.json` 的是这份）。均线组合与档位**理由未留档**。页面「RISK OFF」标签与 RegimeBand power 投票人读它。**与 Webster Power Trend 无关** |
| `signals.*.trend_status`（9E / 21E / 50S / 200S / 52wH 距离） | 注释自称「Oratnek style」，未核对他的定义 | — | ⚠️ **自造，2026-09-21 登记**（B 表 M35）：四条均线距离 = `(close − MA) / close × 100`（**除以收盘，不是除以均线**），52 周高距离 = `(close − high_52w) / high_52w × 100`（`yfinance_adapter.py:1482-1488`）——同一组数用了两个分母。`high_52w` = 最近 252 根的**最高收盘**，不是盘中最高价（`:1462-1463`）。「Oratnek style」**未核**；分母与收盘高点的选择**理由未留档** |
| Correction risk 主读数（`correction_risk.prob` / `today` / `table`） | *(查过，无同类公开口径)*；自建条件频率表 | — | ⚠️ **自造（研究产出），2026-09-21 登记**（B 表 M44）：格子 = (VIX 全样本五分位, SPX 在 200 日线上/下)，值 = 1990 起该格里「未来 21 个交易日内最大回撤 ≤ −5%」的历史频率（`correction_risk.py:52-54,100-150,286-302`）；第三维 VIX/VIX3M 3EMA 三态另表（`:153-200`）。选表不选模型的理由在 docstring（`:10-39`）：9 特征 logistic 走步外样本输给基准率（Brier 0.133 vs 0.121），有样本外技能的只有 VIX 水平与 200 日线一侧，表保留这点技能且不加参数；**21 日 / −5% 两个常量理由未留档**。不冒充任何标准。VIX/VIX3M 三态注释写「turin thresholds verbatim」，但他原文是 0.8/1.0/1.1 三个切点、我们只用前两个（审计 B 表 M45，不在本轮范围） |
| Correction risk 的 VIX/VIX3M 期限结构四态（`ts_state`，3 日 EMA） | @turintrader，[2022-03-28](https://x.com/turintrader/status/1508257418387599361)：「.8 as complacency and 1/1.1 as fear/capitulation zones」 | <0.8 自满 / 0.8–1.0 / 1.0–1.1 恐慌 / ≥1.1 投降 | ✅ **切点照原文（2026-09-21 补回 1.1，Andy「全都修了。」，B 表 M45）**。此前代码只有 0.8/1.0 却注释「verbatim」。**自造部分**：0.8–1.0 的名字「neutral」、恰落在切点上的归属（<0.8 / ≤1.0 / <1.1）。条件频率表每晚按四态现算；E1（08-21）测的是旧三态，**不是这四态的检验**。⚠️ `regime_ledger.csv` 的 `ts_state` 在 09-21 前的 3 代表所有 >1.0；`lamp_ts` 仍＝>1.0（3 或 4） |
| Correction risk 旁注 NH/NL「Breadth washout」：10-EMA，<0.30 / >0.85 | 近亲 StockCharts **High-Low Index**（Record High Percent 的 **10 日 SMA**，读 30 / 50 / 70） | [ChartSchool](https://chartschool.stockcharts.com/table-of-contents/market-indicators/high-low-index) | ⚠️ **借来的阈值 + 自选平滑，2026-09-21 登记**（B 表 M46）：`NH/(NH+NL)` 取 **10 日 EMA**，<0.30 oversold、>0.85 overbought、其余 mid（`correction_risk.py:257-259`）。数据是 TradingView 导出的 **NYSE** 新高新低（`INDEX_HIGN` / `INDEX_LOWN`，`:253-256`），不是我们的 Finviz 池。0.30 / 0.85 借自 KaibaraYuzan（KY）的免费 TradingView 套件（`data/research/turin_trky_study.md:129`、`turin_trky_replication_plan.md:133`），**KY 原脚本本轮未复核**；选它的理由已留档：E1（2026-08-21）里它是正面击败 VIX 五分位价差的候选之一（37.2 / 19.4 / 9.1%，2001 起）。与标准 High-Low Index 差两处：EMA 不是 SMA、上沿 0.85 不是 70。页面不用标准名，不算冒充；只作旁注，不进 `prob` |
| Correction risk 旁注 GEX：252 日分位五分位 | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（B 表 M47）：SqueezeMetrics `gex / price²`，今天在最近 252 个值里的分位 `(w ≤ today).mean()`，`min(int(pr×5)+1, 5)` 切成 Q1–Q5（`correction_risk.py:269-280`）。选它的理由已留档：E1 里在每个 VIX 三分位内都单调（`:246-249`，`turin_trky_replication_plan.md:76`）；**五档与 252 日窗口本身理由未留档**。各档历史频率冻结在 `_GEX_E1`（`:236-242`）。只作旁注。读的是 SqueezeMetrics 文件，与 09-17 退役的 SPX GEX 引擎无关 |
| TICK cycle（`tick_cycle.json`：band grind / washout，SMA15） | 复刻 Linda Raschke 的私有 LBR TICK 周期指标（她只发过图，**无公开参数**） | 查过，无公开口径 | ⚠️ **逆向 + 自造分档，2026-09-21 登记**（B 表 M48）：NYSE TICK（TradingView `USI:TICK`，小时线重建日高/日低）的日高、日收、日低各取 SMA15；带宽 = MA(high) − MA(low)，今天在 252 日里的分位 ≤0.10 → grind（红）、≥0.90 → washout（绿）、其余 neutral（`regime_ledger.py:72-74,294-306`）。**n=15 是逆向出来的，不是拍的**：对她图上印的当日读数，收盘线对到 −25.7 vs −27（`indicators/fluxus-lbr-tick-cycle.txt:13-21`，规格文件自评高置信；审计 B 表写「n≈15 是猜的」不准确）。**分位分档是我们的改造**，规格原话「那是我们自己的改造，不是她的原版」（`:33-34`）；用带宽做 zone 的思路借自 @ChartsLector。证据常数 `_EVIDENCE`（17 年、卖出带 71 次）冻结自 `scripts/research/lbr_tick_zone_test.py`。代码 docstring 没写「自造」 |
| preset `Stockbee 9M Setup` | Stockbee **9 million breakout** | `v>=8900000`，当日量——[2019-09-23](https://stockbee.blogspot.com/2019/09/simple-scan-that-can-make-you-millions.html) | ✅ 一致（2026-09-18，新键 `volumeMin`）。另有 $1B 市值闸：universe 规则（Andy 09-18「市值这个闸是要加上的」），非原文 |
| `liquid_leader` | Andy 课程 **M2_L09 Liquid Leaders** | `M2_L09_Scanning_Routines.md:134`「ADV ≥ 2M shares, above 50 SMA, RS rank top 20%」 | ✅ 一致（课程版，Andy 09-18「9 用课程版」）。RS 窗口自选 `rs_3m`、ADV 为 20 日均，均为课程未写明处。**不是** TradersLab 同名扫描（Alex 原文七项另有一套） |
| panel `liquid_leader_pullback` / preset `21EMA Watch` 的回踩条件 | Alex Desjardins · TradersLab **21dma-structure Pullback** | DCR>10%、周<15%、0–1×ATR 离 21ema、−0.5–4×ATR 离 50sma、21ema 上行——[TradersLab](https://traderslab.gitbook.io/primetrading/alexs-scans-and-workflow-traderslab) | ✅ 一致（2026-09-18）。ATR 距离用 plain（`sma50_atr_dist`），非 B/A；「21ema 上行」由 ≥0 下限蕴含。未做：5 日收缩（原文无数字）、财报 7 日（无数据）；底池是课程版 LL。预设里另有非 Alex 条件（ppCount、ADR 3–6、trend_base、剔医疗），该预设名不挂作者，保留 |
| 筛子单 `ema21_watch.json` | 同上一行（Alex Desjardins 21dma-structure Pullback） | 2026-09-21 起**就是** `21EMA Watch` 预设：读 `screener-presets.json`，经 `preset_hits.passes` 判定——一条规则 | ✅ **与预设同一规则（2026-09-21，审计 C 表 #41）**。退役的自造代理：SMA20 −2%..+3% 冒充 21EMA、站上 SMA50/200、RS 档 ≥80。RS 5 分一档只做分组，不再筛人——名单会出现 RS 80 以下的票 |
| `sma50_atr_dist` | Alex ATR extensions「ATR-normalized distance」 | (close − SMA50) / ATR | ✅ 一致（2026-09-18 新列）。与 `atr_from_sma50`（Jeff Sun / SteveDJacobs B/A 式）是两个量：B/A = plain ×(1+dist) |
| panel `morales_pp_10d` / preset `Pocket Pivot` | Morales / Kacher **Ten Rules for Pocket Pivots** | 量 > 前 10 日最大下跌日量；规则 7「Do not buy pocket pivots if the stock is under a critical moving average such as the 50-dma or 200-dma」——[virtueofselfishinvesting.com](https://www.virtueofselfishinvesting.com/faqs/answer/Ten-Rules-for-Pocket-Pivots) | ✅ 一致（2026-09-18）。删去「≥3 次 = cluster」（原文无）；未做「贴近 10 日线、未延伸」（原文无数字）；10D 展示窗口自造 |
| `min_vol_3d_1` · Anticipation 流动性 | Stockbee **minv3.1** | 截至昨日 3 根的最小量 `>=100000`——[2019-10](https://stockbee.blogspot.com/2019/10/anticipation-scans-that-can-make-you.html)（作者评论释义 minv3.1） | ✅ 一致（2026-09-18 新列）。vcs≥60、adr≥3 为自造；原文 Buyout 条件未做；强度阈值 1.05 / 1.8 / 1.19 在该帖找不到出处，**待查** |
| `ep_stockbee` | Stockbee **Episodic Pivot**（2014-07《My process flow for EP》） | `c/c1>1.04 and v>3*avgv50.1 and v>=300000`；avgv50.1 = `avg_vol50_prev`（截至昨日的 50 日均量）——[原文](https://stockbee.blogspot.com/2014/07/my-process-flow-for-episodic-pivots-ep.html) | ✅ 逐字（2026-09-18，Andy「12 注册 EP Stockbee和 EP Qullamaggie」）。原文的人工判断「neglect + game changing earnings」做不到。跑在 $1B 宇宙上（universe 规则，非原文） |
| `ep_qullamaggie` | Qullamaggie **Episodic Pivot**（《How to master a setup: EP》） | 「a gap up of 10% or more」＋ 开盘头 15–20 分钟成交一个日均量——[原文](https://qullamaggie.com/how-to-master-a-setup-episodic-pivots/) | ⚠️ **只做到部分**（2026-09-18）：`gap_pct≥0.10` 且全天量 ≥ `avg_vol50_prev`；「前 15–20 分钟」需分时数据；均量窗口 50 借自 Stockbee，自选。名单比原文宽。跑在 $1B 宇宙上 |
| `episodic_pivot` | — | 收盘涨 ≥10%、相对量 ≥3、市值 ≥$5 亿 | **2026-09-18 退役**（三位作者的原文都对不上）。`episodic_pivot.json` 只作前端兼容文件（两个新 EP 的并集），不进 `ticker_events`、不计热度；历史归档中该名最后有效日 2026-09-17。热度分把两个 EP 与旧名视为同一族，只计一次 |
| 组四态 Leading / Weakening / Improving / Lagging（两套：`groups.json` + `theme_ladder.json`） | ⚠️ 借用 JdK **RRG** 四象限名 | `groups.json` 系统 = 一阶超额 × 二阶加速度；`theme_ladder.json` 系统 = 一阶超额 × 一阶动量，均非 RRG 的 RS-Ratio/RS-Momentum | ⚠️ **自造，2026-09-18 补登记，2026-09-21 拆分详列**（T-0921-07）。两套消费者、与 RRG 的具体差异、页面自查结果，见下方「[组四态双系统口径](#组四态双系统口径2026-09-21-补登记任务-t-0921-07)」节，不再合并在本行 |
| `tml`（watchlist 面板 True Market Leaders + `leaders_log.tml`） | Richard Moglen（TraderLion）**True Market Leader**，[X 2020-11-06](https://x.com/RichardMoglen/status/1324813953474678787)；概念源于 O'Neil 的 Model Book Stocks | 硬条件：美元成交额 > $30M（20 日均价 × 20 日均量）、`rs_rating` ≥ 97、站上向上的 30 周线、`weinstein_stage` = 2、close > EMA10 / EMA21 / SMA50、`ud_vol_ratio_50` > 1.2；基本面 5 项（季度营收 >25%、季度盈利 >25%、净利率 >20%、ROE >17%、明年预估 >25%）至少 3 项；前 20 行业只标记（`top20_industry`） | ✅ **2026-09-18 实现**（Andy「照 Moglen 2020（建议）可以」）。操作化：RS「ideal」做成硬条件、「most」= 3/5（缺值不计入分母但仍须满 3 项）、「10」取 EMA、利润率取税后 TTM（yfinance 无税前）、行业排名按 `rs_3m` 中位（IBD 是 197 组按 6 个月涨幅）。未做：底部量价收缩、财报后放量跳空（行里无财报日）、Story。另过整页 $1B / $20M / ADR ≥3.5 闸。**Alex 没有定义过 TML**；Steve Jacobs 也在用 TML，门槛专有不公开 |
| `ud_vol_ratio_50` | IBD **Up/Down Volume Ratio** | 50 日内上涨日成交量之和 ÷ 下跌日之和，平盘日不计；无下跌日为 null——[IBD via Yahoo](https://finance.yahoo.com/news/down-volume-ratio-gauge-demand-212800062.html)、[Linn Software UDVR](https://www.linnsoft.com/techind/updown-volume-ratio-udvr) | ✅ 一致（2026-09-18） |
| `profit_margin` / `roe` | yfinance `profitMargins` / `returnOnEquity`（TTM） | 与现有基本面同一次调用取得，不新增抓取 | ✅ 厂商直给（2026-09-18 新存）；每晚轮换 700 只，约 8 晚覆盖全库 |
| `industry_rank` / `top20_industry` | 近 IBD **Industry Group Rank**（197 组） | 行业内 tradeable 成员 `rs_3m` 中位数排名；前 20 标记 | ⚠️ **自造**：IBD 公式不公开，且按 6 个月涨幅排 197 组，我们按 3 个月 RS 中位排 Finviz 行业 |
| Watchlist 整页流动性闸 $1B ∧ $20M（`passes_gate`） | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（自造数字复查 C 表 #1；Andy 2026-09-21「ok的。」）：市值 ≥ $1B（`MIN_CAP`，`watchlist.py:40`）**且** `avg_volume × close` ≥ $20M（`MIN_DOLLAR_VOL`，`:45`），三值缺一即不过（`:106-110`）；`avg_volume` 是 20 日均量（`pipeline/themes/__init__.py:34`）。理由已留档：2026-08-18 从 oratnek 的「1M 股」改成美元量（Andy「改可以的」）——股数闸对高价股太紧、对 $2 股太松（CBRL $58×86.2 万股＝$50M/日被挡，$2×110 万股＝$2M/日反而过，`:42-44`）。**$20M 这个数本身、$1B 这个数的理由未留档**。与 `is_tradeable`（第 83 行）是两把不同的尺子；Short List 的 coiling 席与 TML 行也过这道闸 |
| ADR 全局下限 3.5（`MIN_ADR_PCT`，trouble 区豁免） | ⚠️ 代码注释说是「Stockbee's adr 3.5-10」，`adr_pct` 行（第 58 行）与 `843d527d` 说是「从 Qullamaggie 借的」——**两个作者名都查不到** | [qullamaggie.com/faq](https://qullamaggie.com/faq/) 只给 ADR 定义（20 日平均日内振幅），**没有任何阈值**（2026-09-21 现场取页核过）；Stockbee 的扫描公式里没有 ADR 条件（审计 C 表 #2），检索「stockbee ADR 3.5」无果 | ⚠️ **自造，2026-09-21 登记**（C 表 #2）：`adr_pct ≥ 3.5`，缺值放行（`watchlist.py:56,83-86`），trouble 区（stop_hit / ll_break / extended）豁免（`:61,100-103`）。**3.5 最早出现在 `9ff050a1`（2026-03-15）预设的 `adrPct: {min: 3.5}`，commit 没写来源——源头理由未留档**。升为整页地板的理由已留档（`e260757d` / `e3c046e3`，2026-08-25，Andy「接上 ADR 闸」）：在 oratnek 四个存档交易日上它砍掉我们 57% 的面板宽度、一个他的名字都不丢（14/14、16/16、11/11、35/35），以及止损框架 R＝ATR 下 1% ADR 的票要 3 倍仓位（`:46-55`）。**结论：3.5 是我们的，按 oratnek 页面拟合过，不是 Stockbee 或 Qullamaggie 的数**；第 58 行「阈值从 Qullamaggie 借」的说法由本行更正（公式照抄 Qullamaggie 仍成立） |
| Watchlist 每格最多 25 只 / 跨区 ≥3 才列 | *(无标准，展示规则)* | — | ⚠️ **自造，2026-09-21 登记**（C 表 #3）：每个面板 `tickers[]` 截到 `MAX_PER_PANEL = 25`，另报 `truncated` 与全量 count（`watchlist.py:62,591-592`）；跨区表只列出现在 ≥`MIN_CROSS_ZONES = 3` 个**区**（不是面板）的名字（`:65,601`）。3 的理由已留档：08-14 用 ≥2 列出 177 只（其中 143 只正好两区，多是 leaders×moving），3 区才短到读得完（`:63-64`）。**25 的理由未留档**（`465036ca` 2026-08-17 引入时没写） |
| chase 标记（当日 ≥15%） | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（C 表 #4）：`change_pct ≥ CHASE_PCT = 0.15`（`watchlist.py:67,365`），页面置灰沉底，不过滤。理由已留档（`:618` 规则文本）：2026-08 验证里「4% Bullish × 当日 ≥15%」20 日 −9.3%、胜率 36%。Short List 名片判词另写死一份 `0.15`（`name_cards.py:110,166`），两处须同改 |
| top_3m 标记（3 月表现全池分位 ≥0.85） | *(无标准)* | — | ⚠️ **自造，2026-09-21 登记**（C 表 #5）：`perf_3m_pctile ≥ TOP_3M_PCTILE = 0.85`（`watchlist.py:69,359`），只标记不过滤。理由：拟合 oratnek 的候选池，用 08-11 / 13 / 14 三天（`:69`、`:617`）。⚠️ **拟合已被新数据反证**：`e3c046e3`（2026-08-25）实测 08-24 用它会丢掉他 30 个名字里的 11 个；因为只做标记，没有下线 |
| rs_high 标记 | 近 IBD「RS 线创新高」说法（通行读法看更长窗口，**本行未核一手**） | — | ⚠️ **自造标记，2026-09-21 登记**（C 表 #6）：`rs_line_pctl_21 ≥ 100`，即 RS 线（close/SPY）今天不低于最近 21 个交易日里任何一天（`watchlist.py:353`；底层量是已登记 ✅ 的 oratnek RS 1M 自百分位，第 81 行）。只检测、不过滤（`fbf2c0fb` 2026-08-18、`:616`）；Short List asset 席读同一个量。21 日窗口的**理由未留档**（跟随底层量的窗口） |
| MA Reclaim 面板 | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（C 表 #11）：`cross_ema21_up ∨ cross_sma50_up`——昨收在线下、今收在线上或线上，不设量条件（`watchlist.py:185-194`）。去掉量闸的理由写在 recipe 里（2026-08-20 Andy OK）：≥1 的量闸挡掉了 MU 08-04（rv 0.7）与 MRNA 三次收复（0.85–0.93）——崩盘后的反转常在低相对量上走，因为崩盘把均量抬高了；两把量尺（Finviz 与 50 日）同日差 0.3–0.6，任何地板都画在噪声里 |
| VCS 面板组合（vcs ≥60 ∧ rs_3m ≥80 ∧ >SMA50 ∧ adr ≥3） | vcs 本体照抄 oratnek（第 98 行 ✅）；组合是我们的 | — | ⚠️ **自造组合，2026-09-21 登记**（C 表 #13）：`watchlist.py:245-252`。理由写在 recipe：08-14 单用 VCS ≥70 列出 33 只、一半是弱票（rs_1m <30），oratnek 同日面板只有 2 只；抬 VCS 门槛不管用（≥90 仍 8 只、全弱），加领导力闸才管用。**60 标称「他的 developing 档边」**（出自 `screener_methods.md`，一手本轮未见）。⚠️ **`adr ≥3` 这条腿实际不起作用**：compression 区不在 ADR 豁免之列，面板池已经过了 3.5 的整页地板（`panel_pool`，`:89-103`），Anticipation 面板的 `adr_pct ≥3` 同理 |
| 4% Bullish（面板 + 预设） | `screener_methods.md:166` 写「原型：**Stockbee 的 4% 突破扫描**」——原型的公式引对了，**我们的规则不是他的** | Stockbee：`c/c1>=1.04 and v>v1 and v>=100000`——[How I get the Market Monitor Numbers](https://stockbee.blogspot.com/2014/08/how-i-get-market-monitor-numbers.html) | ⚠️ **自造，2026-09-21 登记**（C 表 #19）：`change_pct ≥4%` ∧ `rel_volume ≥1` ∧ `from_open_pct ≥0` ∧ `rs_21d ≥60` ∧ ADR 3.5–10 ∧ 非医疗（`watchlist.py:303-308`；预设 `screener-presets.json:42`，另加 $1B）。与 Stockbee 的差别：`v>v1`（比昨日放量）换成了 `rel_volume ≥1`（比均量），`v ≥100k` 没有，另加四条。「看从开盘」`screener_methods.md` 记在 Qullamaggie 名下，**未核一手**。rs_21d 60 与其余几条的**理由未留档**。面板名不挂作者，**Stockbee 的名字只在方法文档里，归属说成「原型」可以，说成他的扫描不行**；三条件原版就是已登记的 `up_4pct_stockbee` |
| Weekly 20%+ Gainers（面板 `perf_5d` ≠ 预设 `weeklyPct`） | *(查过，无标准)*；Stockbee momentum burst（3–5 天 8–20%）是另一个量 | — | ⚠️ **自造，同名两套口径，2026-09-21 登记**（C 表 #20）：面板 `perf_5d` 20%–500%（5 个**交易日**，由 K 线算，`watchlist.py:309-314`，`yfinance_adapter.py:1161-1165`）；预设 `weeklyPct` 20–500 读 Finviz `perf_1w`（**自然周**，`screener-presets.json:209`，`screenerFilter.js:56`）；两边都加 ADR 3.5–10、非医疗，预设另加 $1B。面板改 5 日的理由已留档：自然周 08-14 只含 4 个交易日，5 日才是 oratnek 读的那根周 K（recipe 原文）。**20% 这个门槛理由未留档**；预设还没改，所以同名两义仍在 |
| Short List 六席规则与替补链（burning · new_leader · entry · v_reversal · coiling · asset） | *(无标准)* | — | ⚠️ **自造，2026-09-21 登记**（C 表 #23）：规则是 Andy 2026-08-20 定的 v2（`name_cards.py:177-356`，docstring `:188-197`）：所有席位 ATR 位 <7（`atr_from_sma50`，缺值放行，「我不想交易任何已经 extended 的股票」）；席 1/2/3/5 先挑 Leading 主题、再 Improving、再其余（两轮排序不硬切，`state_rank`）；席 4 与 6 豁免主题；每席有替补链，只有真干了才空。各席：burning＝heat 前 50 里排最高；new_leader＝今日新进 TML，否则在册 TML 中 ATR 位最低；entry＝今日 EP（Stockbee ∪ Qullamaggie）按 rel_volume，否则 Leading 主题里的 Liquid Leader Pullback；v_reversal＝52wh ≤60 天且离高 3–20%（缺 `days_since_52wh` 时用 ≥−15% 代理），再深 V（离高 ≤−25%），再 MA Reclaim 里 rs_3m 最高；asset＝RS 线 21 日＝100 ∧ 20 日新高，否则 RS 线自百分位最高。60 天 / 3–20% / −15% / −25% 与 heat 前 50 的**具体数字理由未留档**。⚠️ **代码与 docstring 不一致**：asset 席第一条路（`lead_assets`，`:335-339`）**没过 ATR<7 闸**，只有替补那条过了——「ATR gate everywhere」对 asset 席不成立 |
| Short List「Sugar Babies 名册 ≥5 次＝反指」 | 名册本身挂 Stockbee **Sugar Babies**（一手定义未找到，见审计 C 表 #46） | — | ⚠️ **自造，2026-09-21 登记**（C 表 #25）：`roster` = 最近 10 个事件日里命中 `P:sugar_babies` 的天数（`name_cards.py:135`），`≥5` 时名片加「⚠Sugar Babies 名册 N 连(反指)」（`:112-113`）。「反指」的依据已留档：2026-08 扫描器验证里该预设 20 日前瞻 −9.5%（`data/research/case_mrna_2026-08-19/six_names_2026-08-20.md:20`；半字母表重算后 −11.4%，`half_alphabet_reach_2026-09-17/README.md:20`），且 heat 不给它权重。**5 这个门槛理由未留档**。⚠️ 标签写「连」，代码数的是 10 天里的次数，不要求连续 🗑 **2026-09-21 撤下**（Andy「B 照建议做」）：他的 Sugar Babies 是**做多的盯盘池**，把名册常客读成反指与原意相反；`roster_streak` 仍记入席位归档（次数本身无害），页面不再据此打「⚠反指」。 |
| preset `Sugar Babies`（`sugar_rank` 1–30） | Stockbee **Sugar Babies**：Investors Underground 访谈（YouTube `A_0ep4ekGWM`）「stocks which have high number of 9 million EPs in a given period」，6 个月或 1 年，盯 25–30 只 | 按 `ep9m_count_6m` 降序（并列看 `ep9m_count_1y`、再看代码）取前 30，$1B 市值以上；一次 9M EP＝c/c1>1.04 ∧ v>3×avgv50.1 ∧ v≥8,900,000（`yfinance_adapter.ep9m_days`） | ✅ **单位、窗口、按次数排名照原文（2026-09-21，Andy「B 照建议做」）**。⚠️ **自造部分**：①9M EP 的公式——他没给，这里把他两个成文扫描拼起来（2014-07 EP 扫描 + 2019-09 9M 扫描，量能下限 30 万换成 890 万）；3×均量那条让「被冷落后放出 9M」与天天 9M 的大票分开（裸 9M 规则下日均量 >9M 的票 98.8% 有计数，09-03 实测）②TOP_N=30（取他 25–30 的上沿）③6 个月为主序、1 年只破并列：日线只下载 1 年，前 50 根无均量，「1y」实际只覆盖约 200 个交易日④$1B 市值闸（universe 规则）。退役：09-04 起的 `bo_count_1y≥10 ∧ bo_count_3m≥2`（单位 4% breakout、两个阈值都是我们的）与预设里的 `excludeHealthcare`（他的名单不排医疗） |
| Short List coiling 席的日线 coil（5 日幅 ≤5% ∧ 距 20 日收盘高 ≥−3%） | *(查过，无同名标准)*（近亲见 `range5_pct`、`dist_hi20_pct` 两行） | — | ⚠️ **自造，2026-09-21 登记**（C 表 #27）：`range5_pct ≤5` ∧ `dist_hi20_pct ≥−3` ∧ 站上 SMA50 ∧ 过 $1B/$20M 闸（`name_cards.py:314-322`）；排在 3WT 之后、VCS 之前。链的顺序是 Andy 2026-08-20 的决定（「蓄势席换成 3WT/COIL 吧」），**不是研究结果**：08-23 独立池 holdout 里日线 COIL 无优势（edge −0.42pp，claims.jsonl `tightness-coil-daily`，`:303-311`）；席位只当雷达，判词不许引优势数字。**5 与 −3 两个数字理由未留档** |
| 组层辅助量：`rs_accel_rate` · `persistence` · `ext_share_4/7` · 成员 ≥5 · 丢弃 >500% 读数（`groups.json`） | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（C 表 #30），理由基本都已留档（`pipeline/themes/rs_engine.py`）：**`rs_accel_rate`**＝近 1 月超额 − 前 2 月超额折成月率（几何折算），匀速读 0，是「加速/减速」文字的唯一读数，不进四态分类——作闸时它在每一刀上都不如不等窗的 `rs_accel`（V7，`:147-178`）· **`persistence`**＝五个窗口（1w/1m/3m/6m/1y）里处于同组前 25% 的个数，无同组时退回「跑赢基准」且只数基准有的窗口，分母随值一起发（`:194-247`）；前 25% 的理由只写了「按组表排序时交易者读到的横截面」· **`ext_share_4` / `ext_share_7`**＝成员 `atr_from_sma50` ≥4 / ≥7 的占比（`:366-388`），依据 2026-08-17 研究（48 主题×293 场）：Leading 主题 21 日后仍 Leading 的概率随 ≥4 占比单调下降（<20%: 28% → >60%: 0%），而下期超额不降——是「Leading 标签快到期」的预警，不是跑输预测 · **成员 ≥5**（`min_members`，`:402-411`）：三只票的「行业」读的其实是一家公司的新闻 · **丢弃绝对收益 >500% 的读数**（`_MAX_PLAUSIBLE_RETURN = 5.0`，`:67-72`）：Finviz 偶尔把公司行为伪影报成数百倍收益（一只航空股 perf_1m +31,192%） |
| theme_ladder `lagging_share` / `lagging_share_d5` | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（C 表 #32）：每档窗口里 Lagging 主题占可测主题的比例，及其 5 个交易日的变化（`short_window.py:190-202`）。为 Andy 2026-08-28 要看「4 态的数量变化」而发（`:203-206`）。**只是读数不是信号**：它要检验的「Lagging 占比上升先于回撤」样本内 20% vs 基准 12%、holdout 17% vs 12%，方向一致但都不显著，触发只有 10 / 6 次、命中率低于 40% 时到不了 p<0.05（`:172-178`，claims.jsonl `canary-lagging-share`）；payload note 自认「unproven and underpowered」（`:275`）。5 日差分窗口的**理由未留档** |
| rotation 三刀投票（`rotation.json`） | *(查过，无标准)*；风格篮子 risk-on/off 没有公认合成口径 | — | ⚠️ **自造，2026-09-21 登记**（C 表 #33）：三刀 SPHB/SPLV、IVW/IVE、(IPO, IWC, ARKK)/(XLV, XLP)（`pipeline/rotation/baskets.py:53-75`）；每刀＝长边对 SPY 超额 − 短边对 SPY 超额（多只取等权平均），读两个窗口：10 个交易日的符号为本期票、21 日的符号为月度票（`engine.py:32-35,124-163`）；两窗同向＝established、只有两周翻了＝turning、三刀不一致＝split，只报票数、不换算成置信度（`:178-235`）。理由已留档：三刀用互不重叠的工具才算三份证据（但 IVW 与 SPHB 共享大盘科技，承认相关、不当独立样本）；两周窗口单独不可靠，所以从不单发。ribbon 用 `rs_engine.classify` 的 (63, 21) 月尺度四态（`:74-95`）。10 / 21 两个窗口外的具体组合**理由未留档** |
| heat 分 / Confluence 扫描（`heating_up.json`，Screener 默认扫描） | *(查过，无标准)* | — | ⚠️ **自造，2026-09-21 登记**（C 表 #34）：窗口最近 15 个存档日；权重 EP（两家）/ VCP / momentum_97＝3，gainers_4pct / vol_up_gainers / ema21_watch / healthy_charts＝1；同一筛子重复一次 ×0.25、封顶 1.5×；同日 ≥4 个不同加权筛子另 +2.0；取前 50（`ticker_heat.py:35-66,132`）；两家 EP 与退役的 `episodic_pivot` 归一族，同族只计一次（`FAMILY`，`:70-74`）。理由已留档：重复封顶是为了让单一筛子的重复噪声永远赢不了真正的多筛共振（`docs/plans/2026-07-31-ticker-events-design.md:88-92`）；confluence 门槛 3→4 是因为 ≥3 在档案上每天触发 23.5 次（4% / Vol Up / Momentum 相关，任何大涨日都亮三个），≥4 每天 4.2 次、正好是 MRNA 那种单日炸弹的形状（`:52-63`）。**3:1 权重比与 15 日窗口理由未留档**（设计文档只写「quality ×3 / participation ×1」）。`:36-38` 注释「a name on BOTH on one day scores both」已被 `FAMILY` 推翻，过期 |
| asset 层 `hi20` | 近亲 Donchian 20 日上轨（用 **High**） | — | ⚠️ **自造，2026-09-21 登记**（C 表 #36）：`close ≥ 最近 20 根收盘的最大值`（含今天，即今天的收盘是 20 日最高收盘，`asset_signals.py:106`），用收盘不用 High，与股票侧 `dist_hi20_pct`（第 112 行）同样用收盘。喂 Short List asset 席的「RS 线 21 日=100 ∧ 20 日新高」。**理由未留档**（`1bedf1aa` 2026-08-20 引入时没写） |
| `gainers_4pct.json`（扫描条「4% gainers」） | *(查过，无标准)*；docstring 称它是「Stockbee breadth ratio 的输入」——**不成立** | Stockbee 4% 计数要求 `V > V1 AND V >= 100000`（见 `up_4pct_stockbee` 行） | ⚠️ **自造，2026-09-21 登记**（C 表 #39）：只看 `change_pct ≥ 4%`，不设任何量条件（`gainers_4pct.py:30,58`）；docstring 明说这是「今天谁在动」的普查，要看量就读 `vol_up_gainers`（`:9-13`）。⚠️ `:15-17` 说它的计数是 Stockbee breadth ratio 的输入：投票用的 `ratio_*_stockbee` 读三条件计数、不读这个文件，这句已过期。4% 取自 Stockbee 的涨幅线，其余是我们的 |
| `vol_up_gainers.json`（chg ≥4%）≠ 预设「Vol Up Gainers」（chg ≥0%） | *(查过，无标准)* | — | ⚠️ **自造，同名两套口径，2026-09-21 登记**（C 表 #40）：文件＝`change_pct ≥4%` ∧ `rel_volume ≥1.5`（`vol_up_gainers.py:29,32,60-62`）；预设＝`dailyPct ≥0` ∧ `relVolume ≥1.5` ∧ ADR 3.5–10 ∧ $1B ∧ 非医疗（`screener-presets.json:75`）——同名，涨幅门槛差 4 个点。1.5 倍量的理由写在 docstring（多出 50% 的量意味着有人吃下了大单，`:3-6`）；**预设为什么是 0%、两边为何不同，理由未留档** |
| `healthy_charts.json`（扫描条「Healthy charts」） | *(查过，无标准)*；一部分像 Minervini Trend Template 的「距高点 25% 以内」，**不是他的扫描** | — | ⚠️ **自造，2026-09-21 登记**（C 表 #42）：站上 SMA50 与 SMA200 ∧ 距 52 周高 −25%..−5% ∧ `perf_1m >0` ∧ `rel_volume ≥0.5` ∧ 3 月表现全池分位档 ≥80（`healthy_charts.py:35-45,126-146`）。5–25% 这条带的理由在 docstring（`:7-12`）：离高 <5% 已延伸、止损太贵，>25% 的「上升趋势」需要另作解释，中间才是可以打紧止损、上正常仓位的休整区。**0.5 倍量与 80 档理由未留档** |
| 预设 Monthly Leader 97（原「97 Club」） | `screener_methods.md:185` 称原型是「IBD 的 RS 97+ 俱乐部」——**未核一手** | — | ⚠️ **自造，2026-09-21 登记**（C 表 #48）：`hScore` 80–99 ∧ `rs21d` 97–99 ∧ ADR 3.5–6 ∧ trend_base ∧ $1B ∧ 非医疗（`screener-presets.json:122`）。⚠️ `hScore` 映射到**原始 `h_score`**（`screenerFilter.js:190`），而第 63 行写明原始 h_score 不是百分位（顶档 0.6%、IQR 29）——**80 这条线实际约在顶部 1% 附近，读起来却像「前 20%」**。ADR 上限 6 的理由已留档：2026-08-17 定持仓型预设上限 6、扫描型 10（`screener_methods.md:90`）。**80 / 97 两个门槛理由未留档**（97 = 「前 3%」同一把尺，是 Andy 08-17 的定名约定，`screener_methods.md:228`） |
| 预设 PP Count（30 日内 Morales PP ≥3） | 判定照抄 Morales/Kacher（第 79 行 ✅）；**「≥3 次」不是他的** | Kacher Ten Rules 没给次数（见 `morales_pp_10d` 行） | ⚠️ **自造阈值，2026-09-21 登记**（C 表 #50）：`ppCount ≥3` → `pp_count_30d`（`preset_hits.py:46`；`screener-presets.json:190`）∧ trend_base ∧ ADR 3.5–6 ∧ $1B ∧ 非医疗。**3 与 30 日窗口理由未留档**。2026-09-18 面板那边已删掉「10 日 ≥3＝他的 cluster」（原文无此数，现为 10 日内 ≥1），预设这边的 3 仍在；trend_base 也不是 Morales 的条件（他的规则 7 是站上 50/200 日线） |

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

## 组四态双系统口径（2026-09-21 补登记，任务 T-0921-07）

**起因**：Andy 09-21 原话「dashboard数据还需要继续验证或者补全，我会和你讲哪些，特别是theme的4态读数」。查代码后发现系统里同名的 Leading / Weakening / Improving / Lagging 其实是**两套独立实现**，轴的阶数不同、消费者也不同，此前只在一行表格里含糊带过，这里拆开逐一核实。

### 系统一：`groups.json` 四态（`pipeline/themes/rs_engine.py::classify`）
- 轴：`excess_3m`（3 个月累计超额，一阶量级）× `rs_accel`（上月超额 − 前两月合计超额，**不等窗口二阶加速度**，验证过的判据，rs_engine.py 头部注释与 FOUR_STATE_DESIGN.md）。
- 分类：`excess_3m>0` 且 `rs_accel>0` → Leading；`excess_3m>0` 且 `rs_accel<=0` → Weakening；`excess_3m<=0` 且 `rs_accel>0` → Improving；否则 Lagging。
- 写入方：`pipeline/themes/build_groups.py`（调用 `score_groups`）→ `data/output/groups.json`。
- **消费者（2026-09-21 现场核实，非转抄旧文档）**：
  1. `#/groups`（nav key `groups`，i18n 标「Themes (old)」/「主题（旧）」）——**已从左侧导航栏移除，但路由仍可直接访问**（`Rail.jsx` 注释：「Themes IS the Rotation page from 2026-09-07」「old Themes is off the rail but its route still resolves」）。页面大卡 `StateField.jsx` 源码注释自称是 `classify(excess_3m, rs_accel)` 的可视化复现（「75 of 75」），`GroupTable.jsx` / `CompareReading` 同源展示该 `state` 字段。
  2. Short List（`pipeline/screeners/name_cards.py`）：`verdict()` 把 state 译成名片上的「水域✓ / ～(Improving) / ✗」；`state_rank()`（Leading=0、Improving=1、其余=2）是**全部六个席位**候选排序（`prefer()`）的第一优先级；"entry" 席位的替补链另外硬性过滤 `states.get(t)=='Leading'`。
  3. Watchlist（`pipeline/screeners/watchlist.py::load_group_states` → `_with_groups` → 逐行 `group_state` 字段）：喂 `WatchlistPage.jsx`（`row.group_state==='Leading'||'Improving'` 徽标）、`ShortlistTray.jsx`（tooltip / 复制文本）、`PickedChart.jsx`（个股页副标题）、`useShortlist.js`。
  4. **不再消费的地方（核实到位，避免误传）**：`true_market_leaders`（TML）面板 2026-09-18 换成 Moglen 定义后**不再**用 home-group Leading 做硬闸（此前是「`liquid_leader` and home group=Leading and `rs_1m`>=80」，`watchlist.py:157` 注释自述已替换）；`tml_moglen.py` 的 `top20_industry` 用的是 `industry_rank`（行业 3 个月 RS 中位排名），与这套四态无关，是另一套自造口径（见本表 139 行）。

### 系统二：`theme_ladder.json` 四态（`pipeline/themes/short_window.py::classify`）
- 轴：`level`（L 个交易日累计超额）× `momentum`（M 个交易日累计超额，**一阶**）——五档窗口 2w/4w/6w/8w/10w，外加 1m/3m 两个命名别名（同一形状，只换常数）。
- 分类：同符号判据（level>0 且 momentum>0 → Leading，以此类推），动量恰好为 0 判给弱态（Weakening/Lagging），与系统一分类的形状相同，但轴的构造是一阶动量不是二阶加速度。
- 写入方：`pipeline/screeners/run_all.py`（夜间调用 `short_window.build`）→ `data/output/theme_ladder.json`。
- **消费者**：`#/rotation`（nav key `rotation`，**现在导航栏里名叫「Themes」/「主题」，是唯一在导航栏可达的主题页**）——`TerrainCard`（HowToRead 称「Terrain」，五档面积图）直接读 `history` / `states_2w` 展示这套四态；`FluxCard`（折线下方逐日态迷你条）读 `series[name].states_2w`。**`PointsCard`（「Momentum & Acceleration」三条 strip）不读这套、也不读系统一的 `state` 字段**——它只用 `groups.json` 的连续量（`rs_0_1w` / `rs_1w_1m` / `excess_3m`）另外重算三条轴（`rs2w` / `acc` / `long`），不落回四态标签，`rotationLogic.js::boardsOf` 可见。
- `market_light.py`（Market State 页 L7-Q2「龙头在带头吗」，`brightness.leaders`）读的也是这套——本表 73 行已登记：2 周档、`kind=='theme'`、Leading 状态。

### 与 RRG 原口径的差异（两套都借了 JdK 的四象限**名字**，都不是同一算法）
- JdK RRG 官方轴是 **RS-Ratio**（相对强度水平，对标基准归一到 100）× **RS-Momentum**（RS-Ratio 的一阶变化率），两轴都在**同一把尺子**（归一化的 RS-Ratio）上取值和取导数，且 RS-Ratio 本身是一条连续轨迹，能画出「旋转」式运动路径。
- 系统一的两轴不在同一把尺子上：第一轴是原始超额收益（百分比），第二轴是超额收益的**二阶**加速度（不等窗口，刻意设计成「跑赢平均配速也可能判负」），不是 RS-Ratio 的一阶动量。
- 系统二的两轴构造上更接近 RRG 的形状（都是一阶超额），但仍不是同一尺子——没有 RRG 式的到 100 基准的归一化，也不产出连续轨迹，只在四个象限里离散判态。
- **代码与文案自查（2026-09-21，`git grep -in RRG` 限定 `pipeline/**/*.py` `frontend/src/**/*.{js,jsx}` `data/reference/*.md` `docs/**/*.md`）**：命中的是 `short_window.py` 的模块/函数文档字符串（自陈 `momentum` 是「the RS line's slope; RRG RS-Momentum」）、`DATA_CONTRACTS.md`（「这是 RRG 给不出的『速度量级』」）、脑暴期 `docs/plans/2026-09-02-themes-screener-brainstorm-brief.md`（构思阶段的口径来源说明，非最终实现）与本表——**都是开发者可见的代码注释/内部文档，前端没有任何用户可见页面把这套读数打上「RRG」字样或声称是 RRG**，`RotationPage.jsx` 的 HowToRead 用的是「level/momentum」而非 RRG 术语。未发现冒充 RRG 读数的地方。

### 待办（不在本轮范围，留给下一轮或 Andy 指定项）
- Andy 09-21 原话只说了「特别是 theme 的 4 态读数」，还没给出具体要核对的个例/日期——**本任务验收第三条（逐条对/错判定）暂缺输入，等他在会话里点出具体项**；上面两套的口径与消费者清单已经是可核对的基准，下一轮拿到具体项后可以直接对照本节查。
- `#/groups`（系统一的展示页）仍在路由里活着但不在导航栏——如果确认它彻底不再需要，应该拆除而不是留着一条「死链接但代码还在跑」的收尾；这是产品决定，不在本次数据口径核对范围内，列此仅作记录。

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
