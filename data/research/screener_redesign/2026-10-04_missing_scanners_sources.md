# 漏斗「今天做哪种形态」里 12 个虚线扫描器：出处核对

- 写于：2026-10-04 03:59 JST（2026-10-03 18:59 UTC）
- 任务：Andy 2026-10-04 说「有些扫描清单还没有pipeline要加上，不要乱造，去找来源，有一些我的tradingview上已经做好了screener…看看能否搬进来」，又补了一句「大部分scanner来自jeff sun, ALEX PRIMETRADING，STEVE JACOBS， oratnek等」。
- 规则：每条判据都要引原文并写出处；找不到原文就写「查过，无标准」。本文件只做核对，不改代码。
- 清单出处：`frontend/src/components/screener/funnel/funnelMath.js:24-27` 的 `PENDING_SETUPS`，中文名在 `frontend/src/i18n/translations.js:770-781`，读的是 origin/main。

## 〇、最重要的发现

1. **Andy 自己的 Notion 页里已经有这些扫描器的 TradingView 筛选面板截图。** 页面是 `Fluxus Trading Hub / Swing Trading Masterclass 2025 / DAY 2 True Market Leader`（ID `2b35bc79-10f7-806e-b85c-d4cc2d9a6d1b`，最后编辑 2025-11-30）。在「How to identify? → 10+ Types of Screeners and primary screeners I use」这一节，每个扫描器有一个折叠块。其中 Key ETF、EP、Liquid Leaders、High ADR%+ Inside Day、Long base consolidation、Bull Snort、VCP、Strongest Mover（2 张）、Pre-Market Screener、Scan within watchlists 这些块**只放了截图，没有文字**。CAN SLIM 周频那一个还附了 TV 共享链接 `https://www.tradingview.com/screener/GTqzft1p/`（名字是 "CAN-SLIM Style Strong Growth Weekly Screener"），但链接的 HTML 里读不到筛选条件。
   - 截图存在 Notion 的 S3 上，链接 5 分钟就过期。要看图就得下载，**这需要 Andy 点头**，本轮没有下载。他点头后，一次就能把 10 张面板全读下来，**不用他自己再去 TradingView 截图**。
2. Notion 页里**有文字原文的只有 3 个**：Darvas、Liquid Leader Pullback（已经上线）、Scan within watchlists。原文见下表。
3. 课程 §5.5 这张表是从 Notion 页传抄过来的（09-23 溯源已经证明「龙头回踩」那一行抄丢了 closing 一个词，见 `FluxusTrading_Obsidian/90_Inbox/2026-09-23_龙头回踩扫描器_日振幅20_溯源.md`）。所以**课程里的数字不能当原件用**，原件是 Notion 截图。课程数字和原作者对不上的地方，下表逐条标出。
4. 已经有 2 个扫描器在别的名字下跑着：「流动性龙头」（`universe.liquid_leader` + watchlist 面板 `liquid_leaders`）和「板块与主题 ETF」（`etf_data.json`，168 只，11 个 XL 板块 ETF 全在）。
5. `pipeline/screeners/jeff_sun.py` 已经把 Jeff Sun 的 13 个 TV 扫描和 7 个 Finviz 扫描**逐字转成了数据**（不在 cron 里）。Andy 的 TV 清单里「Strongest Stock(Weekly Scan)」「Watchlist Scan (5ema <5%/>5%)」「weekly 20%+」「🔥HOTTEST」和 Jeff 的扫描名一一对得上。
6. 与 09-26 的盘点（`data/research/screener_redesign/2026-09-26_data_inventory_and_survey.md:92-108`）对账：那份查的是**字段**，本份查的是**出处**。两份在字段判断上一致，本份新增的是：Oliver Kell 的 Bull Snort 和 52 周新高原文（带数字）、Jeff 的 IPO 与表内再筛原文，以及 Notion 截图这条线索。

## 一、总表（12 个虚线扫描器）

字段一栏说的是 `data/output/universe.json`（2026-10-02 收盘那一版，5,618 行）里有没有。

| # | 扫描器 | 作者 / 出处 | 原文判据（逐字） | 已有字段 ／ 缺的字段 | 对应的 TV 清单 | 状态 |
|---|---|---|---|---|---|---|
| 1 | 成长股周频池 | ①Andy Notion DAY 2：TV 共享筛选 `GTqzft1p`（截图）。文字只列了参数名：「基本面：market cap, EPS growth Quarterly YoY, Revenue growth, Quarterly YoY · 技术分析：Price>50sma; 10ema > 20ema/20sma; ADR · 成交量：Avg Volume 60D，Volume · 最近表现：Performance 1W，这是个weekly scanner」②课程 `SwingMasterclass/_audit/drafts/CH05_扫描.md:170`、`M2_L09_Scanning_Routines.md:130` ③Jeff Sun `jeff_sun.py` `1_Fundamental_Growth`，推文 https://x.com/jfsrev/status/1796806706028302775 | 课程：「EPS Q ≥ 20% YoY, Rev Q ≥ 20% YoY, above 50 SMA, 10EMA > 20EMA, weekly」。Jeff：「latest quarterly sales and EPS growth exceeding 25% year-over-year … Only a 50-day MA filter … volatility 1M 3% filter」。Notion 页只写了参数名，**阈值在截图里** | 有：`eps_growth_this_y`（yfinance `earningsGrowth`）、`revenue_growth`（`revenueGrowth`）、`sma50_dist`、`ema10`、`ema20`、`adr_pct`、`perf_1w`。⚠️覆盖率：EPS 只有 1,837/5,618，营收 3,389/5,618。缺：60 日均量（我们的 `avg_volume` 是 20 日） | 「Strongest Stock(Weekly Scan)」可能是它，也可能是 Julian Komar 的 Strongest Stock（见第三节） | 缺字段（EPS 覆盖率太低）；阈值以截图为准 |
| 2 | 板块与主题 ETF | ①Notion「Key ETF」（只有截图）②课程 `CH05_扫描.md:171`、`M2_L09:131` ③Jeff Liquid ETF，https://x.com/jfsrev/status/1962458102709837975 | 课程：「XLK/XLE/XLF/XLB/XLV/XLY/XLU/XLI/XLRE/XLP/XLC + custom themes」，没有筛选条件。Jeff Finviz 版：`ind_exchangetradedfund, sh_avgvol_o1000, ta_volatility_w>3`（`jeff_sun.py` `FV_Liquid_ETF`） | **已经有**：`etf_data.json` 168 只，11 个板块 ETF 全在，带 `perf_1w/1m/3m`、`rrs_rank`、`abc`；另有 `rotation.json` 和 `baskets/` | 无 | **已有，换了名字**（只差把面板接进漏斗） |
| 3 | 流动性龙头 | ①课程旧版 `M2_L09:133` ②课程新稿 `CH05_扫描.md:173` ③Notion「Liquid Leaders」（只有截图）④Alex（TradersLab）同名扫描 `SwingMasterclass/_vendor/PrimeTrading/27_Screener_Scans.md:19-55` | 旧版：「ADV ≥ 2M shares, above 50 SMA, RS rank top 20%」。**新稿多了一条**：「距 52 周低点 +70%」。Alex 的版本完全是另一套：「Minimum $250 million daily liquidity · 1M+ average daily volume · Price above $10 · Market cap exceeding $10 billion · ADR between 2.5-10%」，并排除医疗、能源、金融等板块 | **已经有**：`universe.liquid_leader`（`run_all.py:690`，按旧版课程写，Andy 09-18 定「9 用课程版」，登记在 `METRIC_SOURCES.md:155`）；watchlist 面板 `liquid_leaders`（`watchlist.py:185`）。新稿的 +70% 可以用 `low_52w` 算，代码里还没有 | 「🐉Liquid Leader」 | **已有**；⚠️新稿比代码多一条 +70%，要 Andy 定用哪一版 |
| 4 | 52 周新高 | ①课程 `CH05_扫描.md:175`、`M2_L09:135` ②Oliver Kell《The Swing Report Screening Guide》第 6 页，https://theswingreport.com/wp-content/uploads/2023/12/The-Swing-Report-Screening-Guide.pdf ③Notion：**没有这一块** | 课程：「New 52-wk high in last 5 days, volume ≥ 1.5× avg」（均量窗口没写，`CH05_扫描.md:191` 的批注已经指出）。Kell：「New 52 Week High · Beta > 1 · Price > $20/Share · Average Volume > 500k」，Deepvue 预设写的是「Avg. Vol. 20D: > 500K」 | 有：`days_since_52wh`、`rel_volume`（20 日）、`close`、`avg_volume`（20 日）。缺：`beta`（只有 Kell 版要用） | 无 | **可以直接做**（课程版）；Kell 版缺 beta |
| 5 | 高 ADR 加内包日 | ①课程 `CH05_扫描.md:176`、`M2_L09:136` ②Notion「High ADR%+ Inside Day」（只有截图）③Jeff Sun，https://x.com/jfsrev/status/1826136493452308698 | 课程：「ADR ≥ 5%, today's range inside yesterday's」。Jeff：「I've replaced the 'Volatility Month' filter with 'ADR%' … 'inside day candle' you may find the same with japanese candlestick pattern term 'Bullish Harami'」（他没在文字里写 ADR 的阈值） | 有：`adr_pct`。缺：内包日标记（需要前一天的最高价和最低价；adapter 手上有 K 线，但没往外发） | 无（Andy 的「🔥HOTTEST」是 Jeff 的另一个扫描，见第三节） | 缺字段（内包日标记，可以从现有 K 线算） |
| 6 | 长期平台 | ①课程 `CH05_扫描.md:177`、`M2_L09:137` ②Notion「Long base consolidation」：文字只有「more on this later」，加一张截图 ③Jeff「KC-inspired Extended Base」，https://x.com/jfsrev/status/1965598848761700696（Finviz 链接没存档） | 课程：「≥ 10-wk sideways within 15% band, tightening」。**「tightening」（持续收窄）没有数字**。Jeff 的推文只有选出的票和「cup-and-handle … positive institutional accumulation over the past 3 months」，没有条件 | 缺：10 周价格带宽（现有的 `wk_band_3` 只有 3 周，而且是我们自造的，见 `METRIC_SOURCES.md:66`）；「收窄」没法判 | 无 | **要 Andy 的截图**（Notion 里那张就行）；「收窄」查过，无标准 |
| 7 | 多头狂奔（Bull Snort） | ①课程 `CH05_扫描.md:178`、`M2_L09:138` ②Oliver Kell 同一份 PDF 第 5 页（作者原件）③Notion「Bull Snort」（只有截图） | 课程：「Large candle body + massive volume + closing near high」，没有数字。Kell：「Price over $20/Share · Over 500k in Average Volume · Stock Up on the Day · At least 2X Relative Volume (ideally 3X+)」，Deepvue 预设写的是「Last > $20 · Avg. Vol. 20D > 500K · RV 20D > 3.00 · Price % Change Today > 0.01%」 | **全有**：`close`、`avg_volume`（20 日）、`rel_volume`（20 日，和 Kell 的「RV 20D」口径一致）、`change_pct` | 无 | **可以直接做**（Kell 版）。⚠️课程的「收在最高附近」Kell 原文里没有；Andy 截图可能另有设置 |
| 8 | 当日最强 | ①课程 `CH05_扫描.md:180`、`M2_L09:140` ②Notion「Strongest Mover」（两张截图）③Jeff Sun「Strongest Mover」，`jeff_sun.py` `Mom_1W…6M` 和 Finviz 链接 https://x.com/jfsrev/status/1659786288067928064 | 课程：「Top 20 by (RVOL × 1-day price change), price > $5, ADV > 500k」，**出处不明**。Jeff 用同一个名字，规则却是看多周期涨幅：1 周 >20%、1 月 >30%、3 月 >50%、6 月 >100%，另加 `ta_volatility` 和 `sh_avgvol_o300` | 课程版的字段全有：`rel_volume`、`change_pct`、`close`、`avg_volume`。Jeff 版的 TV 条件缺流通股（float）和 60 日均量 | 「weekly 20%+」＝Jeff 的 1 周 >20% | **可以直接做**（课程版）；⚠️和 Jeff 同名不同规则，要先看 Andy 那两张截图 |
| 9 | 盘前扫描 | ①课程 `CH05_扫描.md:181`、`M2_L09:141` ②Notion「Pre-Market Screener」（只有截图）③Jeff「Live Pre-market Screener」，https://x.com/jfsrev/status/1810643031592497162（条件「refer to screenshot」） | 课程：「Pre-market ≥ 3% + volume ≥ 100k pre-market shares」 | 缺：完全没有盘前数据。管线在美东 04:00–16:15 之间会主动拒跑（`run_all.py:824-835`） | 「⚓️Stocks in Play」可能是它，没法确认 | 缺字段（要新数据源，而且要在盘前跑） |
| 10 | 次新股 | ①课程 `CH05_扫描.md:182`、`M2_L09:142`（出自 Minervini 五特征之四）②Notion「IPO list」：**块是空的** ③Jeff Finviz IPO 链接，https://x.com/jfsrev/status/1941836386904285491 ④Andy Notion「Darvas」里的「Recent IPO (1-5 years)」 | 课程：「Public 6mo–5yrs, forming first base」。Jeff：`cap_midover, fa_epsyoy1_pos, ipodate_prevyear, sh_avgvol_o1000`（「Just do it once a week」）。「first base」（第一个平台）查过，无可计算的标准 | 缺：IPO 日期（`jeff_sun.py` 的 docstring 也写明 universe 没有 IPO date） | 无 | 缺字段（IPO 日期） |
| 11 | 箱体龙头（Darvas） | ①**Andy Notion「Darvas Stock Scan」，有文字原文** ②课程 `CH05_扫描.md:183`、`M2_L09:143` | Notion 逐字：「Stocks made +100% from the low in the last 52wks, on increased overall volume · near or at all time high · Recent IPO (1-5 years) · In an infant sector/industry · New product or service · Very good earning or forecast or story · Low cap stock」。机器能判的只有前三条；「increased overall volume」没写窗口 | 有：`low_52w`（+100% 就是 `low_52w ≥ 1.0`）、`high_52w_dist`。缺：历史最高价（ATH，不是 52 周高）、IPO 日期；放量的窗口查过，无标准 | 无 | 缺字段（ATH、IPO 日期）；后四条要人看 |
| 12 | 表内再筛 | ①**Andy Notion「Scan within watchlists」，有文字原文** ②课程 `CH05_扫描.md:184`、`M2_L09:144` ③Jeff「Watchlist Scan」，https://x.com/jfsrev/status/1770337966814363698 ；`jeff_sun.py` `Daily_Tightness_Swing` | Notion 逐字：「在自己已经建立的强势股watchlist里面加上一个条件：EMA below price by 0-5%」（**EMA 是几日的没写**，截图里有）。Jeff：「two separate scan parameters, 'Watchlist Scan,' for tightness of swing trading setups within the range of above and below 5% of the 5-EMA」 | 缺：5 日 EMA（现在只有 `ema10/20/21`）；缺输入名单——要先有 Andy 的 Focus 或 Almost Ready 名单，管线里没有 | 「Watchlist Scan (5ema <5%)」「Watchlist Scan (5ema >5%)」——和 Jeff 的两个参数一一对上 | **要 Andy 的截图**（确认是不是 5 日 EMA），外加名单来源 |

## 二、状态计数

| 状态 | 个数 | 是哪几个 |
|---|---|---|
| 已有，换了名字 | 2 | 板块与主题 ETF、流动性龙头 |
| 可以直接做 | 3 | 52 周新高、多头狂奔、当日最强 |
| 缺字段 | 5 | 成长股周频池（EPS 覆盖率）、高 ADR 加内包日（内包日标记）、盘前扫描（盘前数据）、次新股（IPO 日期）、箱体龙头（ATH＋IPO 日期） |
| 要 Andy 的截图 | 2 | 长期平台、表内再筛 |
| 整条查过、无标准 | 0 | 没有整条都找不到出处的；但有 4 处子条件查过、无标准：长期平台的「持续收窄」、次新股的「第一个平台」、箱体龙头的「量在放大」窗口、52 周新高的「1.5 倍均量」窗口 |

⚠️ 「可以直接做」的 3 个里，有 2 个和 Andy 自己的版本可能不一样：当日最强和 Jeff 同名不同规则；多头狂奔用的是 Kell 原文，课程那句「收在最高附近」Kell 原文里没有。Andy 的 Notion 截图才是他自己的版本，做之前最好先看一眼。

## 三、Andy 的 TradingView 清单 → 出处对照

TV 的 MCP 读不到筛选条件，只能读清单名。下面是按名字对出来的，**都没核过实际条件**。

| TV 清单 | 最可能的来源 | 依据 | 要 Andy 给什么 |
|---|---|---|---|
| Strongest Stock(Weekly Scan) | Julian Komar 的 Strongest Stock Scan（Jeff 在 TV 上做了增强版），或者 Andy 自己的 CAN SLIM 周频筛选 `GTqzft1p` | Jeff 推文 https://x.com/jfsrev/status/1704767941835936037 （Finviz：`cap_smallover, ind_stocksonly, sh_avgvol_o100, sh_price_o7, ta_highlow52w_a70h, ta_sma50_pa`）；`jeff_sun.py` `4_/5_Strongest_Stock_JK` | 筛选面板截图，或一句「是 GTqzft1p 那个」 |
| Watchlist Scan (5ema <5%) / (5ema >5%) | Jeff「Watchlist Scan」＝漏斗的「表内再筛」 | https://x.com/jfsrev/status/1770337966814363698 | 截图（确认是 5 日 EMA，以及是在哪张名单里扫） |
| weekly 20%+ | Jeff「1-Week Mover Exceeding 20%」 | https://x.com/jfsrev/status/1659789002814414850 ；`jeff_sun.py` `Mom_1W_*` | 截图（市值档、float 设了没有） |
| 🔥HOTTEST | Jeff「Hottest Stock」（High ADR%） | https://x.com/jfsrev/status/1789602959782977668 ：「stocks that have exhibited significant momentum over the past month of trading, while also consolidating within a defined range」，条件在截图里 | 截图。⚠️它不在课程 §5.5 的清单里 |
| VCP | 已经上线（`vcp_detector.py`） | — | 不用给 |
| Liquid Leader Pullback | 已经上线（watchlist 面板 `liquid_leader_pullback`） | `METRIC_SOURCES.md:156` | 不用给 |
| 🐉Liquid Leader | 漏斗的「流动性龙头」 | 见总表第 3 行 | 截图（用来定是课程版、+70% 新稿版，还是 Alex 版） |
| ☄️EP | 已经上线（`ep_qullamaggie.py`、`ep_stockbee.py`） | — | 不用给 |
| ⚓️Stocks in Play | 没找到出处；可能是盘前扫描 | 查过，无标准 | 截图，加一句话说明用途 |
| 🉑Almost Ready | 这是一层名单，不是扫描器：Notion「Almost Ready List — need a few more days; above 10/20ema and 50sma; up to 50」 | Andy Notion DAY 2 的 List organization 一节；课程 `M2_L09:174` | 不用给（判据有文字原文） |

## 四、四位作者各自的覆盖情况（Andy 10-04 点名的）

| 作者 | 本机或网上的原件 | 覆盖了漏斗里哪几个 |
|---|---|---|
| Jeff Sun (@jfsrev) | `JeffSun_Wiki/`（309 条推文存档）＋ `pipeline/screeners/jeff_sun.py`（逐字转成的数据） | 成长股周频池、板块 ETF、当日最强（同名不同规则）、次新股、高 ADR 加内包日、表内再筛、盘前（只有截图） |
| Alex · PrimeTrading / TradersLab | `SwingMasterclass/_vendor/PrimeTrading/27_Screener_Scans.md`；https://traderslab.gitbook.io/primetrading/alexs-scans-and-workflow-traderslab | 流动性龙头（另一套）、龙头回踩（已上线）、EP（已上线） |
| Steve Jacobs (@SteveDJacobs) | 「Qullamaggie Screener」：https://x.com/SteveDJacobs/status/1944727946029097423 ；「Stockbee 9M Movers」TV 版：https://x.com/SteveDJacobs/status/1944413811684815002 （「Cap $1B+ · Rel Vol 1.25+ · Volume 9M + · Change from open > 0.01%」） | 和 12 个虚线扫描器都对不上名字；他的 Qullamaggie 扫描最接近已有的 momentum_97 一类 |
| oratnek | 「21EMA Scan for Pine Screener」：https://x.com/oratnek_ill/status/2003659131312587086 （字段列表：Price、ADR%、21 EMA、ATR Distance from 21 EMA、RS(21) 等） | 对应已上线的龙头回踩，对 12 个虚线扫描器没有新的定义 |
| （补充）Oliver Kell | 《The Swing Report Screening Guide》PDF 第 5–9 页 | 多头狂奔、52 周新高；他还有 Doublers（「Performance YTD > 100%」），和箱体龙头相近 |

## 五、建议的下一步

1. **建议先办这件**：请 Andy 允许我从 Notion「DAY 2 True Market Leader」下载那 11 张筛选面板截图（只存本机 scratchpad，不进仓库）。这一步能补齐总表里所有「阈值在截图里」的格子，他不用再去 TradingView 截图。
2. 「可以直接做」的 3 个（52 周新高、多头狂奔、当日最强）等第 1 步看完截图、确认 Andy 的版本以后，交给 DATA ALEX 写进管线；「已有」的 2 个只需要前端把面板接进漏斗。
3. 缺字段的 5 个里，内包日标记和 5 日 EMA 能从现有 K 线直接算（成本低）；IPO 日期、ATH、盘前数据要新数据源，按 MVP 闸先问「两周内对外发布什么」。
