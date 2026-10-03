# Andy 的 11 张 TradingView 筛选面板（逐字转录）＋ TSF 漏斗预设

- 写于：2026-10-04。接 `2026-10-04_missing_scanners_sources.md`（下称「出处报告」）。
- 规则（Andy）：「不要乱造，去找来源」。下面的筛选条件**只抄截图上看得到的**；截图上没有的，写「截图上没有」。
- 截图原件：只在本机 `~/Documents/Trading/_scanner_screenshots/2026-10-04/01_start.png … 11_start.png`，**不进仓库**（仓库是公开的）。本文件只有文字转录。
- 字段对照读的是 `origin/main` 的 `data/output/universe.json`（2026-10-02 收盘那一版，5,618 行）和 `pipeline/screeners/*.py`。

## 〇、先看这里

1. **当日最强：Andy 自己的版本用的是 Jeff Sun 的规则，不是课程的规则。** 截图 08 的标题是「Strongest Mover (1W, 1M, 3M, 6M)」，条件是 1 周涨幅 > 20%、1 月 > 30%、3 月 > 50%、6 月 > 100%。截图里**没有**课程写的「RVOL × 当日涨幅」。⚠️ 有两处和 Jeff 不一样：3 月门槛是 50%（`jeff_sun.py` 抄的 Jeff 原版是 70%）；四个周期的条件**同时开着**，而 TV 的条件是全部同时满足（AND）。Jeff 是把四个周期拆成四个扫描。所以要问 Andy：平时是四个一起开，还是每次只开一个？
2. **截图 09 不是 Strongest Mover。** 它的标题是「7. Julian Komar's Strongest Stock Scan」。这回答了出处报告第三节「Strongest Stock(Weekly Scan) 是哪个」的问题：就是 Julian Komar 的扫描，但 Andy 把营收和 EPS 门槛设成 20%（Jeff 的版本是 25%），也没有设 float、52 周低点和 SMA10 这几条。
3. **6 处出处报告没定的事，截图定了**（详见第二节）：流动性龙头用的是 Alex 那一套（市值 ≥ 10B、ADR 3%–15%），不是课程版；高 ADR 加内包日用的是 ADR ≥ 3% 和 TV 形态「Bullish Harami」；长期平台**没有**「10 周、15% 区间、持续收窄」，而是「今年以来下跌 + 站上 50 日均线 + 低于 200 日均线 20% 以上」；表内再筛的 EMA 是 **5 日**；盘前扫描是盘前涨幅 > 5%、盘前量 > 10K；多头狂奔**没有**「收在最高附近」，也没有「当天上涨」。
4. 11 张截图都**没有排序列，也没有列组**。截图只截到筛选条这一块。要排序和列组，得请 Andy 再截一次表头。
5. TSF 的漏斗预设一共找到 9 个名字：截图上 6 个，TSF 文章里另有 3 个。建议加 4 个，都是按「组内 RS」排序，并且共用同一个新字段。另外 5 个不加。

## 一、11 张截图逐字转录

读法：
- 白底的条件块＝已经设了值的条件。黑底、只有字段名的块＝没设值，不算条件。
- `>` 和 `≥`：TV 用两个不同的符号。我把截图放大看过，带一道小尾巴的那个是 `≥`（above or equal）。小于号同理，`≤`。
- 「Sector 20」：TV 自己的板块分类一共 20 个。块上的 20 表示选了 20 个，看起来是全选，也就是不过滤。⚠️ 这一点没有核实，因为截图里看不到选了哪几个。
- 「Exchange 3」：选了 3 个交易所。截图里看不到是哪 3 个。`jeff_sun.py` 的美股清单是 NYSE、NASDAQ、AMEX。
- 每张图都有 `Market = US`，下表不再重复写。

| # | TV 上的名字 | Andy Notion 里的名字 | 设了值的条件（逐字，按截图顺序） |
|---|---|---|---|
| 01 | 5. LIQUIDITY ETF | Key ETF | Leveraged = Non-leveraged · Avg Volume 60D > 1 M · ADR ≥ 3% · Volatility 1W > 3% |
| 02 | 9. EP | EP | Market cap ≥ 500 M USD · Sector (20) · Avg Volume 60D > 1 M · Volume > 20 M · ADR ≥ 3% · Exchange (3) · Price ≥ 5 USD · Rel Volume > 2.5 |
| 03 | 10. Liquid Leader Scan | Liquid Leaders | Market cap ≥ 10 B USD · Sector (20) · Avg Volume 60D > 1 M · Volume > 1 M · ADR 3% to 15% · Exchange (3) · Common stock · Price > EMA (50) · Price ≥ EMA (20) · Price ≥ 10 USD |
| 04 | 2. High ADR% + Inside Day Quallamaggie Style | High ADR%+ Inside Day | Market cap 10 B to 200 B USD · Sector (20) · Perf 6M > 30% · Avg Volume 60D > 500 K · Volume > 100 K · ADR ≥ 3% · Price > 1 USD · Pattern = Bullish Harami |
| 05 | 3. Long Base & Consolidation | Long base consolidation | Market cap ≥ 300 M USD · Sector (20) · Perf YTD < 0% · Avg Volume 60D > 1 M · Volatility 1W > 4% · Price > SMA (50) · Volume > 500 K · Price > 1 USD · Price below SMA (200) by 20% or more |
| 06 | 13. Bull Snort | Bull Snort | Market cap ≥ 500 M USD · Sector (20) · Price ≥ 20 USD · Volume > 500 K · Rel Volume > 3 · Common stock |
| 07 | 6. VCP | VCP | Market cap ≥ 300 M USD · Sector (20) · Price ≥ 10 USD · Perf 1W −5% to 5% · Exchange (3) · Perf 1M −20% to 20% · EMA (10) < Price · Common stock · Price ≥ SMA (50) · Price ≥ SMA (21) · Price ≥ SMA (200) · Revenue growth, Quarterly YoY > 20% · EPS dil growth, Quarterly YoY > 20% |
| 08 | 4. Strongest Mover (1W, 1M, 3M, 6M) | Strongest Mover（第 1 张） | Market cap ≥ 300 M USD · Sector (20) · Avg Volume 30D > 500 K · Volatility 1W > 4% · Volume > 500 K · Perf 1W > 20% · Exchange (3) · Perf 1M > 30% · Perf 3M > 50% · Perf 6M > 100% |
| 09 | 7. Julian Komar's Strongest Stock Scan | Strongest Mover（第 2 张） | Market cap ≥ 300 M USD · Sector (20) · Avg Volume 60D > 500 K · Exchange (3) · Common stock · Price ≥ SMA (50) · Revenue growth, Quarterly YoY > 20% · EPS dil growth, Quarterly YoY > 20% |
| 10 | 8. Pre-Market Screener | Pre-Market Screener | Market cap ≥ 25 M USD · Sector (20) · Avg Volume 60D > 500 K · Float ≤ 150 M · Exchange (3) · Pre-market Vol > 10 K · Pre-market Chg > 5% |
| 11 | 5. Watchlist Scan (5ema below <5%) | Scan within watchlists | Watchlist = 「STRONG MOVE」（前面有一个龙头表情图标）· Market cap ≥ 300 M USD · Sector (20) · Volatility 1M > 3.5% · Perf 1W < 5% · EMA (5) below Price by 0% to 5% · EMA (10) ≥ SMA (20) |

看不清的值：没有。唯一要放大才能判断的是 `>` 和 `≥` 两个符号，上面已经说明。

截图里的编号（5、9、10、2、3、13、6、4、7、8、5）是 TV 里清单的编号。01 和 11 都编为 5，应该是两个不同的清单分组。

### 只有文字、没有截图的两个（Notion 原文照抄）

- **Darvas Stock Scan**：「Stocks made +100% from the low in the last 52wks, on increased overall volume / near or at all time high / Recent IPO (1-5 years) / In an infant sector/industry / New product or service / Very good earning or forecast or story / Low cap stock」
- **Liquid Leader Pullback Relative Strength**：「All of Liquid Leaders Scan filters; plus. / Daily closing range > 20% / Price contraction (last 5 days over 20 days lookback) / Weekly return < 12% / 0.5 to 1 x ADR from the 21ema / 0 to 3 x ADR from the 50ema / Earnings in 7+ days」
  - ⚠️ 它写的是「All of Liquid Leaders Scan filters」。现在截图 03 告诉我们 Liquid Leaders 是哪些条件了（市值 ≥ 10B、ADR 3%–15% 等），而线上的 `liquid_leader_pullback` 用的是课程版的龙头定义（见第二节第 3 行）。两边的底层名单对不上。

## 二、截图定了出处报告里哪些悬而未决的事

| 出处报告的行 | 出处报告当时的说法 | 截图里 Andy 自己的版本 | 定了什么 |
|---|---|---|---|
| 8 当日最强 | 课程「RVOL × 当日涨幅，价 > 5，均量 > 500k」和 Jeff 的多周期涨幅同名不同规则，要看截图 | 08：多周期涨幅，1W > 20 / 1M > 30 / 3M > 50 / 6M > 100，另加市值 ≥ 300M、30 日均量 > 500K、Volatility 1W > 4%、当日量 > 500K | **用 Jeff 的规则**，课程那句出处不明的规则不要。3M 门槛是 50% 不是 70%；四个周期同时开着（见〇-1） |
| 三 TV 清单「Strongest Stock(Weekly Scan)」 | 可能是 Julian Komar 的扫描，也可能是 CAN SLIM `GTqzft1p` | 09：标题就是 Julian Komar's Strongest Stock Scan；营收和 EPS 季度同比 > 20%，价格 ≥ SMA50 | 是 Julian Komar 的扫描。没有 float、没有「离 52 周低点 +70%」、没有 SMA10 区间（这三条在 `jeff_sun.py` 的 JK 版里有） |
| 3 流动性龙头 | 课程旧版（日均量 ≥ 2M、站上 50 日线、RS 前 20%）、课程新稿（再加 +70%）、Alex 版，三套里选哪套要 Andy 定 | 03：市值 ≥ 10B、60 日均量 > 1M、当日量 > 1M、ADR 3%–15%、普通股、价 > EMA50、价 ≥ EMA20、价 ≥ 10 | **接近 Alex 版**：市值 10B、ADR 区间、价格 10、1M 均量都对得上。Alex 的 $250M 日成交额和板块排除，截图里没有（Sector 选了 20 个）。截图里**没有 RS 条件，也没有 +70%**。线上 `universe.liquid_leader`（`run_all.py:690`）是课程旧版，和 Andy 的 TV 版不一样 |
| 5 高 ADR 加内包日 | 课程「ADR ≥ 5%，今天的区间在昨天之内」；Jeff 说用 Bullish Harami | 04：ADR ≥ 3%、Pattern = Bullish Harami、市值 10B–200B、Perf 6M > 30% | ADR 门槛是 **3%**；内包日用 TV 的 **Bullish Harami 形态**。⚠️ Harami 看的是实体（开盘和收盘），内包日看的是最高价和最低价，两者不是同一件事。要照抄就得照 TV 的 Harami 定义算 |
| 6 长期平台 | 课程「≥ 10 周横盘、15% 区间、持续收窄」；「收窄」查过，无标准 | 05：今年以来涨幅 < 0、价 > SMA50、价低于 SMA200 至少 20%、Volatility 1W > 4%、60 日均量 > 1M、当日量 > 500K | Andy 的版本**没有区间宽度，也没有「收窄」**。他选的是「深跌之后刚站回 50 日线」的票。出处报告「要 Andy 的截图」这一格可以关掉 |
| 7 多头狂奔 | Kell 原文：价 > 20、均量 > 500k、当天上涨、相对量 ≥ 2（最好 3+）。课程多一句「收在最高附近」 | 06：市值 ≥ 500M、价 ≥ 20、当日量 > 500K、Rel Volume > 3、普通股 | 相对量取 **3**。截图里**没有「当天上涨」**（Change % 那块没设值），也**没有「收在最高附近」**。均量条件也没设，用的是当日量 > 500K |
| 9 盘前扫描 | 课程「盘前 ≥ 3%、盘前量 ≥ 100k」 | 10：盘前涨幅 > 5%、盘前量 > 10K、float ≤ 150M、市值 ≥ 25M、60 日均量 > 500K | 门槛是 **5% / 10K**，不是课程的 3% / 100k。另加 float 上限 |
| 12 表内再筛 | Notion 只写「EMA below price by 0-5%」，没写几日 EMA | 11：EMA (5) below Price by 0% to 5% | **是 5 日 EMA**。另外还有 Volatility 1M > 3.5%、Perf 1W < 5%、EMA10 ≥ SMA20、市值 ≥ 300M。和 Jeff 的 `Daily_Tightness_Swing`（`jeff_sun.py`）几乎一样，只有一处不同：Jeff 用 SMA10 > SMA20，Andy 用 EMA10 ≥ SMA20。输入名单是 Andy 在 TV 上的「STRONG MOVE」清单 |
| 2 板块与主题 ETF | 已有 `etf_data.json`（168 只固定名单） | 01：非杠杆、60 日均量 > 1M、ADR ≥ 3%、Volatility 1W > 3% | Andy 的版本是**全市场 ETF 的筛选**，不是固定名单。和 Jeff 的 Finviz Liquid ETF（`sh_avgvol_o1000, ta_volatility_w>3`）几乎一样，多一条 ADR ≥ 3%。我们的 `etf_data.json` 是固定的 168 只，没有成交量、ADR、杠杆标记 |
| （已上线）EP | 线上是 Stockbee 和 Qullamaggie 两个原作者版本 | 02：市值 ≥ 500M、60 日均量 > 1M、**当日量 > 20M**、ADR ≥ 3%、价 ≥ 5、Rel Volume > 2.5 | Andy 的 TV EP 是**第三套**，和两位原作者都不一样。当日量 > 20M 是很高的门槛。只记录，不建议改线上那两个 |
| （已上线）VCP | 线上 `vcp_detector.py`：趋势模板 + 收缩形态检测 | 07：涨跌区间（1W ±5%、1M ±20%）+ 站上 SMA21/50/200 + EMA10 < 价 + 营收和 EPS 季度同比 > 20% | Andy 的 TV 版**没有收缩检测**，靠「近期波动小」来近似，并且加了基本面门槛。线上版没有基本面门槛 |

## 三、每个条件对我们的数据：有字段 / 能从 K 线算 / 缺

字段名都是 `universe.json` 的列名。

### 通用字段（多张图都用到，只说一次）

| TV 条件 | 我们 | 状态 |
|---|---|---|
| Market cap | `market_cap`（5,618/5,618） | 有 |
| Sector (20) | `sector`（Finviz 的 11 个板块，不是 TV 的 20 个） | 有（如果确实是全选，就等于不过滤） |
| Exchange (3) | 没有交易所列；universe 来自 Finviz 美股 | 有（等价，没核实） |
| Price | `close` | 有 |
| Volume | `volume` | 有 |
| Avg Volume 60D / 30D | `avg_volume` 是 20 日；`avg_vol50_prev` 是截至昨天的 50 日 | 能算（`volume_enrichment.py` 已经抓 3 个月日线） |
| ADR / ADR % | `adr_pct`（20 日，`yfinance_adapter.adr_pct_20`） | 有。⚠️ 截图没显示 TV 的 ADR 用几日 |
| Rel Volume | `rel_volume`（20 日） | 有。⚠️ TV 的字段是 `relative_volume_10d_calc`（`jeff_sun.py` 引用），10 日，窗口不同 |
| Volatility 1W / 1M | 没有 | 能算。⚠️ 要先从 TV 帮助页抄它的公式，不能自己定 |
| Perf 1W / 1M / 3M / 6M | `perf_1w` `perf_1m` `perf_3m` `perf_6m` | 有 |
| Perf YTD | `perf_ytd` 这一列存在，但 0/5,618 有值（`yfinance_adapter.py:1334` 写死 None） | 能算 |
| Common stock / Symbol type | 没有证券类型列 | 缺 |
| Revenue growth, Quarterly YoY | `revenue_growth`（yfinance `revenueGrowth`） | 有，但只有 3,389/5,618 |
| EPS dil growth, Quarterly YoY | `eps_growth_this_y`（yfinance `earningsGrowth`） | 有，但只有 1,837/5,618 |
| Price vs SMA50 / SMA200 / SMA20 | `sma50_dist` `sma200_dist` `sma20_dist` | 有 |
| Price vs EMA20 / EMA10 | `ema20` `ema10` | 有 |
| Price vs EMA50 / SMA21 / EMA5 | 没有 | 能算 |
| Float | 没有（`jeff_sun.py` 的 docstring 也写明 universe 没有 float） | 缺 |
| Pre-market Vol / Chg | 没有；管线在美东 04:00–16:15 拒跑 | 缺 |
| Pattern = Bullish Harami | 没有 | 能算（要照抄 TV 的 Harami 定义） |
| Leveraged | `etf_data.json` 没有杠杆标记 | 缺 |
| Watchlist（TV 上的自建清单） | 没有 | 缺（输入名单） |

### 每张截图的计数

`Market = US` 不计入。

| # | 扫描器 | 条件数 | 有 | 能算 | 缺 | 缺的是什么 |
|---|---|---|---|---|---|---|
| 01 | Key ETF | 4 | 0 | 3 | 1 | 杠杆标记；另外 `etf_data.json` 是固定 168 只，不是全市场 ETF |
| 02 | EP | 8 | 7 | 1 | 0 | — |
| 03 | Liquid Leaders | 10 | 7 | 2 | 1 | 普通股标记 |
| 04 | High ADR% + Inside Day | 8 | 6 | 2 | 0 | — |
| 05 | Long base | 9 | 6 | 3 | 0 | — |
| 06 | Bull Snort | 6 | 5 | 0 | 1 | 普通股标记 |
| 07 | VCP | 13 | 11 | 1 | 1 | 普通股标记（营收、EPS 有字段，但覆盖率低） |
| 08 | Strongest Mover | 10 | 8 | 2 | 0 | — |
| 09 | Julian Komar Strongest Stock | 8 | 6 | 1 | 1 | 普通股标记（营收、EPS 覆盖率低） |
| 10 | Pre-Market | 7 | 3 | 1 | 3 | float、盘前量、盘前涨幅 |
| 11 | Watchlist Scan | 7 | 4 | 2 | 1 | 输入名单「STRONG MOVE」 |

整体看：只缺**一次补齐就能解锁好几张**的三样东西：
1. 普通股标记：解锁 03、06、07、09。
2. 60 日和 30 日均量、Volatility 1W/1M：从现有 K 线算。用到它的有 01、02、03、04、05、08、09、10、11。
3. EMA5、EMA50、SMA21、Perf YTD：从现有 K 线算。

真正要新数据源的只有两张：盘前扫描（10）要 float 和盘前数据；Key ETF（01）要全市场 ETF 的名单和杠杆标记。

### 两个只有文字的扫描

| 扫描 | 条件 | 状态 |
|---|---|---|
| Darvas | +100% from 52w low | 有（`low_52w`） |
| | on increased overall volume | 窗口没写，查过，无标准 |
| | near or at all time high | 缺（只有 52 周高 `high_52w_dist`，没有历史最高） |
| | Recent IPO (1-5 years) | 缺（没有 IPO 日期） |
| | infant sector / new product / earning story / low cap | 要人看；low cap 没写门槛 |
| Liquid Leader Pullback | All of Liquid Leaders Scan filters | 见截图 03；⚠️ 线上用的是课程版龙头，不是截图 03 |
| | Daily closing range > 20% | 有（`dcr_pct`） |
| | Price contraction (last 5 days over 20 days lookback) | 能算（`range5_pct` 是相关的量，口径要核） |
| | Weekly return < 12% | 有（`perf_1w`） |
| | 0.5 to 1 x ADR from the 21ema / 0 to 3 x ADR from the 50ema | 能算（`ema21_atr_dist`、`sma50_atr_dist` 用的是 ATR 和 SMA，原文是 ADR 和 EMA，口径不同） |
| | Earnings in 7+ days | 缺（`universe.json` 没有下次财报日） |

## 四、TSF 的漏斗预设

### TSF 是什么

TSF ＝ The Setup Factory（`thesetupfactory.substack.com`）。作者 Jonas 是瑞典的全职儿科 ICU 医生，业余做这个（`memory/project_tsf_teardown.md`）。它的网页平台叫「TSF - Analytics」，选股引擎在 2026-05-12 上线。

它的 Stock Screener 页有四个选择框：Select category（四态）、Select theme（主题）、**TSF Scans**（预设）、Search stock。四个框的结果取交集。Andy 2026-08-11 在会话里说：「TSF scan（预设的watchlists）」。他说的「漏斗 preset」就是 **TSF Scans 这个下拉框**。

### 出处

- **Andy 的截图**：会话 `2e8ec6fd`，2026-08-11 10:08 UTC 发的 1 张，07:28 UTC 发的 4 张；另外 2026-08-09 14:46 UTC 发的 12 张里，第 11 张也展开了同一个下拉框。图里能读出：
  - TSF Scans 下拉框（可以往下滚，截图只露出前 6 项）：**Leaderboard · Recent RS on volume · Recent Strength · Biggest One Month Gainers · Sustained Leaders · Leaders Near Highs On Low Volume**
  - 表的列：Stock · History · Category · RS 0–2W · RS 0–4W · RS 0–10W · RS Accel · 52W High · Vol Surge · Accumulation · COC · Score
  - 图例原文：「Top 25% within theme」（绿点）· 「Change of Character confirmed」（勾）· 「Score — Count of green dots on checked signals」
  - Focus Stocks 页另有 4 个分类按钮：Weekly Focus List · TSF-Leaders · TSF - Universe List · High Octane。这几个是编辑手选的名单，不是扫描。
- **TSF 文章**：课程仓 `SwingMasterclass/_private/tsf_archive/full_clean.json`（392 篇）。下面引的原文都出自这里。截图之外，文章里还出现了 3 个预设：**Resting Leaders**、**Resisting Correction**、**Accelerating Momentum**，应该就在下拉框往下滚的部分。

### 逐个预设

| 预设 | TSF 原文定义（逐字） | 出处 | 我们有没有 | 建议 |
|---|---|---|---|---|
| Leaderboard（默认） | 「The default view shows you stocks scored highest according to my proprietary method.」；图例：Score =「Count of green dots on checked signals」，绿点 =「Top 25% within theme」 | `2026-05-10_gamma-squeeze-with-a-vol-springboard`；截图 | **已有**：Screener 的 Confluence（`frontend/src/lib/scanSets.js:17`，默认项）。TSF 的 6/6 和我们的 `persistence` 是同一种构造（`Fluxus_Brand/visual/2026-08-10_TSF_PAGE_MAP.md:18`） | 不加 |
| Sustained Leaders | 「it shows us relative performance of a stock compared to it's theme across several timeframes, and secondary sorts with proximity to 52w highs.」「Top 25% in RS across all timeframes and proximity to highs」 | `2026-08-16_tsf-focus-stocks-168-2026`；`2026-07-05_point-of-control` | 部分有：组内百分位只有 3 个月一个窗口（`group_pctile`，`pipeline/themes/rs_engine.py:455-490`，按 `excess_3m`）；`high_52w_dist` 有 | **加**。它补的是「在自己组里，各个周期都排前 25%」，我们现在只看 3 个月。窗口用 TSF 表头写明的 0–2W / 0–4W / 0–10W，阈值用它写明的 25%，不用自己定 |
| Resting Leaders | 「It shows us those scoring highest in longterm RS against their theme, but showing weaker short term RS — a leader resting.」「it specifically focuses on recent weakness in longterm term RS leaders.」 | `2026-06-07_tsf-focus-stocks-75-2026`；`2026-05-29_tsf-guide-on-developing-a-trading` | 没有。课程第 3 章 §3.10「休息的龙头还是龙头」讲了这件事，但没有扫描能把它找出来。`liquid_leader_pullback` 最接近，可它看的是绝对价格，不是组内 RS | **加**。⚠️ TSF 没写「长期」「短期」各用几周，也没写门槛。所以只做成**排序**（长期组内 RS 高 × 短期组内 RS 低），不设门槛；窗口取它表头的 0–10W 和 0–2W，并在代码里写明这个对应是我们定的 |
| Resisting Correction | 「this ranks stocks that are recently outperforming their own group and are sitting close to their highs — and it prioritizes proximity to highs.」「it scores stocks with recent RS compared to it's theme and secondary sorts with proximity to 52w highs.」 | `2026-06-14_trap-or-new-beginning`；`2026-06-24_focusing-on-the-leaders-ffc`；`2026-08-23_tsf-focus-stocks-238-2026` | 没有 | **加**，适合用在走弱的主题里（他原话 "in weakening themes"）。⚠️ 两处原文的主次排序**相反**：06-14 和 06-24 说「离高点近」优先，08-23 说「离高点近」是第二排序。照最新的 08-23 版做，并把另一版写进注释 |
| Recent Strength | 「now screen I like is recent strength — sorts top RS 0-2 weeks」「it just ranks recent RS only」 | `2026-07-29_semiconductors-deep-dive`；`2026-08-26_follow-the-money` | 部分有：`rs_0_1w` 是 1 周对 SPY，不是 2 周组内 | **加**，成本最低：它和上面三个共用同一个新字段，只是换一个排序 |
| Biggest One Month Gainers | 只有名字，没找到文字定义 | 截图 | 有 `perf_1m`；Andy 的 Strongest Mover（截图 08）已经含 1M > 30% | 不加，按 `perf_1m` 排序就是它 |
| Recent RS on volume | 只有名字，没找到文字定义 | 截图 | — | 不加。查过，无定义；照名字猜条件就是乱造 |
| Leaders Near Highs On Low Volume | 只有名字，没找到文字定义 | 截图 | 原料都有（`high_52w_dist`、`vol_5d_50d` 5,504/5,618） | 不加。理由同上；要做就得标明是自造的 |
| Accelerating Momentum | 只有名字和一句用法：「you can sometimes find nice turns with the "accelerating momentum scan"」 | `2026-05-19_shakeout-and-rotation` | 有 `rs_accel` | 不加。没有定义；最多在表里加一个按 `rs_accel` 排序 |

### 对我们的漏斗意味着什么

1. TSF 的预设**不是形态扫描**，是在**同一个池子**里按「组内 RS」换不同的排序。所以它们不该进漏斗「今天做哪种形态」那一层，而是放在 Screener 的 Scan 词表里（和 Confluence 并列）；或者做成漏斗 Focus 层的排序开关。
2. 建议加的 4 个（Sustained Leaders、Resting Leaders、Resisting Correction、Recent Strength）**共用一个新字段**：每只票在自己主题里、在 0–2W / 0–4W / 0–10W 三个窗口上的 RS 百分位。现在 `group_pctile` 只有 3 个月一个窗口，而且分组用的是行业，不是主题。补了这一个字段，四个预设就都只是排序，不需要自己定任何门槛。
3. ⚠️ TSF 2026-09-16 说他在测试新的「Full Freedom Screening」筛选器，预设可能会变。本节读的是 Andy 08-11 的截图和 09 月之前的文章。

## 五、建议的下一步

1. **请 Andy 确认 3 件事**：
   - 截图 08 的四个周期是一起开，还是每次只开一个？
   - 「Sector 20」是不是全选？
   - TV 上的「STRONG MOVE」清单是从哪个扫描来的？
2. 交给 DATA ALEX：补普通股标记、60 日和 30 日均量、Volatility 1W/1M（先抄 TV 的公式）、EMA5/EMA50/SMA21、Perf YTD。这几样都来自现有 K 线，不需要新数据源；补完之后，11 张里有 8 张不再缺字段（02、03、04、05、06、07、08、09）。剩下的 01、10、11 要新数据源或输入名单。
3. 流动性龙头要 Andy 拍板：线上是课程旧版，他自己的 TV 是 Alex 那一套，两边不一致。这也会改变「龙头回踩」的底层名单。
4. TSF 那 4 个预设：先补「主题内三窗口 RS 百分位」这一个字段，再做四个排序。
