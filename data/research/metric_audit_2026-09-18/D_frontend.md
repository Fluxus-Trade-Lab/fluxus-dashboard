# 审计 D · 前端自己算 / 写死的市场读数与判定

- 审计对象：`$W = …/wt-audit`（HEAD `30b745bb`，基于 origin/main），`frontend/src/**` 全部组件、hooks、lib。
- 只读。行号均为本次现场 `sed -n` / `grep -n` 读到的。
- **跳过**：`portfolio/`、`journal/`（Andy 个人账户页）；`TickerTrades` / `TickerStatusPanel` / `TickerPage` 中的持仓、胜率部分；`public/ResultsPage.jsx` 与 `public/publicStats.js` 的业绩兜底数字（H1 业绩，属个人账户。附一句：这两处是**同一组数的两份拷贝**，且 `maxDrawdown −17.9` 与 `h1_report.py` 标为 canonical 的 −11.1 不同，注释自认「是待裁决不是 bug」）。纯显示/工程常量（像素、动画、超时、数据新鲜度 `dataFreshness.js WARN_AT 2 / ALARM_AT 4`、`TickerProvenance` 的 ≥3 天陈旧）不计入。
- **死代码**（`grep` 全仓无 import）：`dashboard/MarketPosture.jsx`、`dashboard/MacroGrid.jsx`、`dashboard/TickBand.jsx`、`macro/MacroSection.jsx`（连带 `PowerTrend/TrendStatus/SignalLights/MarketConditions` 只被它和 MacroGrid 引用）、`screeners/ScreenersSection.jsx`（连带 `StockbeeRatio`、`TickerGrid` → `format.js atrBadgeColor` 唯一调用方）、`screeners/Momentum97.jsx`、`screener/WatchlistTab.jsx`、`equities/EquitiesSection.jsx`。死代码里的规则仍列出（标「死」），因为一旦被重新挂上它们就会上页。

## 汇总

- **项目总数：40 项**（活代码 36、死代码 4）。
- **双份规则（前端重算了后端已有的规则）：21 项**；另有 **1 项前端内部双份**（`Reading.jsx` 抄了 `VoteGlyphs.jsx` 的 RANGE/ON_LINE，已经分叉）。
  - **其中已经不一致：7 项**（活 5、死 2）+ 前端内部 1 项：
    1. thrust 牌面（`MarketStateSummary.jsx:26-32`）——引擎已改 Stockbee 两日连续 + 带量分子，前端仍按单日、只看价格的 `up_4pct`。用 `data/output/breadth.json` 最近 100 行回放：**引擎能判的 8 个交易日里 6 天前端读数与引擎相反**（09-08/10/11/14/16/17；例 09-17 前端「bullish thrust」、引擎 `none`）。
    2. `BreadthTable.jsx:164-167` 拿 T2108 的 60/40 给 `%>200` 上色，引擎 `pct200` 是 50/30——**100 行里 33 行颜色和引擎投票不一致**。
    3. Screener「Liquid」闸 `ScreenerPage.jsx:54`：$1B 市值 + **100 万股**均量；后端 08-18 起已改成美元成交额（`is_tradeable` $2M/天、watchlist $20M/天），前端还留着已退役的按股数算的规则。
    4. ATR 位在恰好 7.0 处：`WatchlistPage.jsx:402` 标「5–7 持有」，后端 `watchlist.py:246` 的 Extended 面板是 `>= 7`。
    5. `MarketStateSummary.jsx:55`「ratios agree」用 ≥1 二分，引擎 `confirmation` 用三档投票——100 行里 1 行不一致。
    6. （死）`format.js:31-33` 的 ATR 徽章 ≤4/≤6/>6，后端与登记表都是 ≥7。
    7. （死）`StockbeeRatio.jsx:10` 把 ratio = 1.0 画成黄色，引擎 ≥1.0 就判 bull。
    - 前端内部：`Reading.jsx:85` 的 thrust 量程写死 300，`VoteGlyphs.jsx:97` 已改成读引擎的线——同一个「压线」判据有两份。
- **自造且未声明（页面上当读数用、代码/登记表里没写明是自造）：18 项**（见全表「来源」列中的「前端发明」「自造未声明」）。其中最重的一族是首页 **Regime 条**：五档 18/40/62/84、breadth 投票 8/4/−3/−7、Power 映射、结构映射、「取最弱」合成——**整条首页结论是前端算出来的，后端没有，METRIC_SOURCES 也没登记**。
- **与原作者原文不符：8 项**
  - thrust（Stockbee「back-to-back 300-plus」+ 带量分子；前端单日、只看价格）
  - 5/10 日 ratio 的 bull 线 1.0 ×3 处（`BreadthTable:161`、`RatioChart:19`、`MarketStateSummary:55/57`）——Stockbee 原文 bull 线是 **2**，bear 线 **0.5**（后者一致）
  - 季度 25% 用「涨减跌的符号」配文 structural bull/bear——Stockbee 原文看的是 25%-up 的**绝对数**（<200 极端，反向看多）
  - `RS_BANDS.rs_1m ≥80`——IBD 的 80 是 12 个月加权 RS 的门槛，被搬到了 1 个月截面百分位上
  - ATR 7.0 边界（TradeDudeNYC / 后端都是 ≥7 减仓）
  - （死）ATR 徽章 6
- **登记情况**：METRIC_SOURCES.md 里 `t2108` 行只登记了**值**、没登记分档；5/10 日 ratio、季度 spread、Regime 五档、VIX 期限结构 0.8/1.0、RS 三分位 67/33、rotation 的 rs2w/wkAccel、group `expiring` 都**零登记**。登记表里唯一提到 `.jsx` 的一行是 `PowerTrend.jsx`，而它是死代码。

## 原文检索留痕（第 3 步）

| 分档 | 原文 | 我们（前端） | 偏离 |
|---|---|---|---|
| T2108 超卖 | <20：Stockbee MM 页「Readings below 20 lead to bottoms」、Dr. Duru「below 20% … oversold」 | <20 oversold | ✅ 一致 |
| T2108 超买 | Stockbee MM 页：80 多为超买；Dr. Duru（[AT50 resource page](https://drduru.com/onetwentytwo/t2108-resource-page/)）：>70 | >80 overbought | ⚠️ 跟 Stockbee 一致，跟 Duru 不一致；两个原作者口径不同，页面没说用的是谁的 |
| T2108 weak 20–40 / neutral 40–60 / strong 60–80 | **查过，无标准**（搜了「T2108 oversold overbought Worden definition」、Stockbee MM、Duru；Worden 官方没给分档） | 自造 | ⚠️ 自造未声明 |
| 10 日 ratio | [Stockbee 2011](https://stockbee.blogspot.com/2011/08/how-to-use-market-breadth-to-avoid.html)：「2 plus readings are good for swing trading on long side」「.5 or less … short side」 | bull ≥1.0、bear <0.5 | ❌ bull 线 1.0 ≠ 2；bear 线一致 |
| 5 日 ratio | [Stockbee MM 页](https://stockbee.blogspot.com/p/mm.html)：「above 2.0」为强（经摘要工具转述，需原文复核） | 同 10 日 | ❌ 同上 |
| 季度 25% | Stockbee 2011：「Numbers below 200 are considered extreme」「below 200 it is extremely bullish」——看 25%-up 的绝对数，反向读 | up−down 的符号 → 「structural bull intact」 | ❌ 口径与方向语义都不同 |
| 4% 单日家数 | Stockbee 2011：300–500 high、500–1000 very high、1000+ extreme | 牌面只用一条 300 线 | ⚠️ 分档被压成一条线（引擎也这样） |
| McClellan 极值 | 通行 ±100（另有 ±70、+150 的说法；[McClellan Financial](https://www.mcoscillator.com/learning_center/weekly_chart/overbought_mcclellan_oscillator/)）；我们用的是 ratio-adjusted（RANA×1000） | 前端只在 `VoteGlyphs RANGE mcclellan: 70` 当绘图量程用，不判定 | — 不构成读数 |
| IBD RS | O'Neil：RS Rating ≥80（12 个月、最近一季 40% 加权，1–99） | `rs_1m`（1 个月截面百分位）≥80 标蓝、RS 三分位 67/33 | ⚠️ 数字借用到了另一个量上；67/33 查过，无标准 |
| ATR from SMA50 | 登记表：≥7 减仓 / ≥11 衰竭（本机 Candles Stage Analysis.txt，@TradeDudeNYC）；0–4 / 5–7 出自 `atr_enrichment.py:66`「Jacobs/Jeff Sun bands」，登记表没有 | 0–4 / (4,7] / >7；色阶停点 10 | ⚠️ 7.0 归属错一格；11 没用；0–4/5–7 未登记 |
| VIX/VIX3M 期限结构 | >1.0 = backwardation 是通用定义；0.8「complacent」**没查到权威出处** | 抄了后端 <0.8 / 0.8–1.0 / >1.0 | ⚠️ 0.8 未登记 |
| Regime 五档 18/40/62/84 | 我们的 `conditions` 复刻的是 oratnek Market Conditions；**没查到 oratnek 公开的分档**，代码注释自认「均分 + 占用率审计后上移 6」 | 页面最上方那个词 | ⚠️ 自造，未登记 |

## 全表

记号：**双**＝后端已有同一规则；**不一致**＝现场核实分叉；**死**＝组件未挂载。

| # | 文件:行 | 规则与数字 | 后端对应 | 是否一致 | 来源 | 登记 |
|---|---|---|---|---|---|---|
| 1 | `components/breadth/MarketStateSummary.jsx:26-32`（线取自 `:11-14`，兜底 300） | thrust 牌面：`mm.up_4pct`/`down_4pct` **单日** ≥ line → bullish/bearish/churn/no thrust；四分支 | `pipeline/screeners/breadth_signals.py:32` `{count:300, days:2}`，`:91-107` 用 `up_4pct_stockbee`，**今日与前一日都** ≥300 | **双 · 不一致**：引擎能判的 8 天里 6 天相反。`:21-25` 注释还写着「0.113 × universe」，已过时 | Stockbee 原文（双日 + 带量分子）；前端两条都违背 | 引擎那行登了；前端这份没登 |
| 2 | `MarketStateSummary.jsx:35-37` | T2108：<20 oversold · ≤40 weak · <60 neutral · ≤80 strong · >80 overbought | `breadth_signals.py:38` `t2108_zone {20,40,60,80}`，`:163-172`、`:697-703` | 双 · 一致 | 20 = 原文；80 = Stockbee（Duru 用 70）；40/60 自造 | 只登了值，分档没登 |
| 3 | `MarketStateSummary.jsx:55` | 5D/10D 各自按 ≥1 二分，相同 → 「ratios agree」 | `breadth_signals.py:722-735` 按三档投票（1.0/0.5）比较 | 双 · **1/100 行不一致** | 1.0 自造（Stockbee 2.0） | 否 |
| 4 | `MarketStateSummary.jsx:57` | tone：两个都 ≥1 → up，两个都 <0.5 → down | THRESHOLDS ratio 1.0/0.5 | 双 · 一致（`Tile` 不渲染 `tone`，`:78`，这个参数是死的） | 1.0 与原文不符 | 否 |
| 5 | `MarketStateSummary.jsx:62-64` | 季度 25% up−down 的符号 → 「structural bull intact / structural bear」 | `breadth_signals.py:136-145` `_sign_vote` | 双 · 一致 | **与原文不符**（Stockbee 看绝对数 <200，反向读）；「structural bull」措辞是前端发明的 | 否 |
| 6 | `components/breadth/BreadthTable.jsx:159-162`（用在 `:74-75`） | ratio 着色：≥1.0 高 / ≥0.5 中 / <0.5 低 | THRESHOLDS `ratio_5d/10d {bull 1.0, bear 0.5}` | 双 · 一致 | 1.0 与原文不符（2.0） | 否 |
| 7 | `BreadthTable.jsx:164-167`（用在 `:84-87`：T2108、%>200、%>50、%>20） | 着色：≥60 高 / ≥40 中 / <40 低，一把尺子套四列 | T2108 60/40 ✅；`pct200 {bull 50, bear 30}`（`:37`）；%>20 在 `state_board.py:113` 用 60/50/35 | 双 · **不一致**：%>200 这列 33/100 行颜色 ≠ 引擎投票 | 自造未声明 | 否 |
| 8 | `BreadthTable.jsx:169-172` | McClellan 着色：≥0 高 / <0 低 | `breadth_signals.py:148-149` 按符号投票 | 双 · 一致 | 符号，无须出处 | 值已登 |
| 9 | `components/breadth/HealthChart.jsx:40-41,66` | T2108 参考线画在 20 / 80 | THRESHOLDS oversold 20 / overbought 80 | 双 · 一致（写死的拷贝） | 20 原文；80 见 #2 | 否 |
| 10 | `components/breadth/RatioChart.jsx:19` | ratio 图 1.0 参考线 | ratio bull 1.0 | 双 · 一致 | 与原文不符（2.0） | 否 |
| 11 | `components/breadth/VoteGlyphs.jsx:31,35-40,97` | 压线判据 `ON_THE_LINE 0.08`；每票量程：ratio 1.5、thrust 取 `d.line`（否则 300）、spread 400、nh_nl 200、McClellan 70、pct200 20、t2108 20、danger 5 | 无（后端只给 margin） | — | 前端发明（注释说是「够宽」） | 否 |
| 12 | `components/Reading.jsx:83-88,100-102` | 同一套 ON_LINE 0.08 + RANGE，**thrust 写死 300**；数出「N 票压在自己的线上」当页面首句 | 无 | **前端内部双份，已分叉**（`VoteGlyphs:97` 已改读线） | 前端发明 | 否 |
| 13 | `Reading.jsx:96-97,106` | score ≥0 → 「N signals say yes」 | 引擎 env：≥+4 BULLISH、≤−4 BEARISH、中间 MIXED（`breadth_signals.py:692`） | 语义不一致：score +1..+3 时引擎是 MIXED，首句却说「yes」 | 前端发明 | 否 |
| 14 | `components/breadth/VoteCard.jsx:41-49` | 证伪句：BULLISH 守 ≥+4、BEARISH 守 ≤−4、`flips = ceil(need/2)` | `breadth_signals.py:692` ±4 | 双 · 一致；但 env=OVERSOLD/OVERBOUGHT 会落进 MIXED 分支，说「+4 翻多」，而引擎只要 T2108<20 就一直是 OVERSOLD（`:697-699`） | 抄引擎 | 否 |
| 15 | `components/dashboard/RegimeBand.jsx:68-71` | Market Conditions 0–100 → Defence/Caution/Neutral/Constructive/Euphoria，切点 **18/40/62/84** | 无。后端 `regime.py:96-102` 是另一套（47/63/75，分母也不同） | 仅前端 | 自造（注释写了推导，页面没写） | 否 |
| 16 | `RegimeBand.jsx:87-99` | breadth 投票分档：≥8 → 4、≥4 → 3、≥−3 → 2、≥−7 → 1、否则 0；「差 N 票到下一档」 | 引擎只有 ±4 | 部分双：±4 一致，**8 与 −7/−8 是前端加的** | 前端发明 | 否 |
| 17 | `RegimeBand.jsx:73,114-128` | Power 映射 POWER_3=4、CAUTION=3、WARNING=1、RISK_OFF=0；SPY/QQQ 取弱 | 后端出 signal；映射没有 | 仅前端 | 前端发明（跳过 2 档没写理由） | 否 |
| 18 | `RegimeBand.jsx:101-113` | 结构投票：两个都 Downtrend=0、一个=1、两个 Uptrend=4、一个=3、否则 2 | 后端出 spy/qqq_state；映射没有 | 仅前端 | 前端发明 | 否 |
| 19 | `RegimeBand.jsx:356-364` | 首页 regime 词 = min(分数档, 三个投票的最弱档) | 无 | 仅前端 | 前端发明——**首页最显眼的结论** | 否 |
| 20 | `components/breadth/BoardCard.jsx:34-46` | 迷你图序列：damage = 100·qd/(qu+qd)；thrust 迷你图用 `up_4pct` | `state_board.py:87` 同公式；`:128` 也用 `up_4pct` | 双 · 一致（但 thrust 行和引擎投票用的不是同一个分子，见附带发现） | 抄后端 | 否 |
| 21 | `BoardCard.jsx:60-61` | 档位 ≤1 画红斜纹、≥3 画绿 | 档位是后端的；配色切点没有 | 仅前端 | 自造（显示） | 否 |
| 22 | `components/breadth/CorrectionRiskPanel.jsx:71` | 期限结构标签 complacent <0.8 / neutral 0.8–1.0 / backwardation >1.0 | `pipeline/risk/correction_risk.py:157` `TS_LABELS`，**payload 里就有** `ts_state_labels`（`:194`） | 双 · 一致（写死的拷贝，本该读 payload） | >1.0 通用；0.8 未查到出处 | 否 |
| 23 | `CorrectionRiskPanel.jsx:28-29` | 落后 >2 个交易日判 not measured；格子 n<100 画浅 | 无 | 仅前端 | 自造（显示质量闸） | 否 |
| 24 | `components/watchlist/WatchlistPage.jsx:237-245,247-253` | RS 墨色：`rs_1m` ≥80 蓝 / ≤40 红；`rs_line_pctl_21` 100 / 7.14 | `watchlist.py:14,153` TML 用 `rs_1m >= 80` | 80 双 · 一致；40 仅前端 | 80 借自 IBD（但量不一样，**与原文不符**）；40 自造 | 否 |
| 25 | `WatchlistPage.jsx:525,556` | 强度下限 `RS_FLOOR 80`（作用于 `rs_line_pctl_21`），compression/trouble 豁免 | 无 | 仅前端 | Andy 定的（`:507` 注释），自造 | 否 |
| 26 | `WatchlistPage.jsx:291-296,398-403`；页面文案 `:98,101,115` | ATR 位：色阶停点 0/4/7/10；tooltip `v<=4` 建仓、`v<=7`「5–7 持有」、否则「≥7 只减不买」；文案「0–4 / 5–7 / ≥7」 | `atr_enrichment.py:66` 同样的带；`watchlist.py:246` Extended `>= 7` | 双 · **在 7.0 处不一致**（前端算持有，后端算 Extended）；文案里 4–5 有空档 | 7/11 出自 TradeDudeNYC（已登）；0–4/5–7 出自 Jacobs/Jeff Sun（未登）；11 前端没用 | ≥7 已登；0–4/5–7 没登 |
| 27 | `WatchlistPage.jsx:707`；`watchlist/shortlist/NameCard.jsx:81` | 文案「当日 ≥15% 不追」 | `watchlist.py:65` `CHASE_PCT = 0.15`，payload 里有 `chase_rule` | 双 · 一致（数字写死在文案里） | 内部回测（−9.3% / 36%） | 否 |
| 28 | `lib/format.js:30-33`（死：只有 `TickerGrid` 调用） | ATR 徽章：<0 灰、≤4 绿、≤6 黄、>6 红 | ≥7 | 双 · **不一致**（6 对 7） | 与已登记的 ≥7 不符 | ≥7 已登 |
| 29 | `components/screener/ScreenerPage.jsx:53-55`；`i18n/translations.js:372,767` | Liquid 闸：cap ≥$1B **且** avg_volume ≥1,000,000 股 | `pipeline/themes/__init__.py:31-32,87` $1B + $2M 美元成交额；`watchlist.py:38-43` $20M，注释写明 08-18 起弃用 100 万股 | 双 · **不一致** | 前端还留着已退役的规则 | 否 |
| 30 | `components/screener/StockTable.jsx:94-98,114`；`lib/etfRank.js:105-109` | RS 分位上色：≥67 加粗 / ≤33 淡；对齐点 `rs3 ≥ 67` 才算实心 | 无 | 仅前端 | 自造（三分位）；IBD 用 80 | 否 |
| 31 | `lib/etfRank.js:44,54-81` | **前端算 ETF 的 RS 0–99**（组内百分位 ×99，缺值记 0），标签写 RS | 仿 `run_all.py:343 rank_tradeable`（后端已改 `na_option='top'`，前端注释还写 `'bottom'`） | 双（仿写）· 行为一致、注释过时 | 前端发明的量，**用了 IBD 的 RS 名字**（撞了登记表的命名规矩） | 否 |
| 32 | `components/rotation/rotationLogic.js:55,74,101-104,106-113,127-141` | rs2w = rel[t]/rel[t−10]−1；wkAccel = rs_0_1w − rs_1w_1m/**3.2**；三块榜排名；没序列时 `rs_0_1w + rs_1w_1m/3.2` 近似 | 无 | 仅前端 | 前端发明，卡片标题「RS Last 2 weeks / RS This week vs prior 3」 | 否 |
| 33 | `components/groups/GroupTable.jsx:179-181` | `expiring` = `ext_share_4 ≥ 0.4` 且 state = Leading；量程 0.6 | 无（后端只出 `ext_share_4/7`） | 仅前端 | 自造（来自内部研究，n=31） | 否 |
| 34 | `components/groups/GroupsPage.jsx:98` | 超额 >+1% 「leads SPY」、<−1% 「trails」、否则「even」 | 无 | 仅前端 | 自造（叙事） | 否 |
| 35 | `Reading.jsx:148,161-167,186,189` | 主题句：≥8 行才说、≥5 个追赶才点名；筛选句：7 天内算新、单行业 ≥25% 才说集中 | 无 | 仅前端 | 自造（叙事） | 否 |
| 36 | `components/groups/StateField.jsx:68-73` | persistence ≥3 标名 + Improving 加速前三 | 无 | 仅前端 | 自造（显示规则，图下有写） | 否 |
| 37 | `components/ticker/TickerRelativeStrength.jsx:5-10,51-60` | 前端从 K 线自己算 1M/3M/6M/1Y 涨幅（21/63/126/252 根）对 SPY/QQQ | universe.json 有 `perf_*`/`rs_*`（Finviz 口径） | 双（同名量两个算法） | 交易日窗口是通行做法 | 否 |
| 38 | `components/modelbooks/TradingGym.jsx:288,351-353` | 练习评分：buy 且之后涨 ≥20% 才算对；pass 要 <20%；fade 要 <0；easy 池只取涨幅 ≥100% | 无 | 仅前端 | 自造（教学用） | 否 |
| 39 | `components/dashboard/MarketPosture.jsx:3,20-24`（死） | 4 支 ETF 信号均分，≥2.5 Full Size、≥1.5 Selective、否则 Defensive + 仓位建议 | 无 | 仅前端 | 前端发明的仓位建议 | 否 |
| 40 | `components/screeners/StockbeeRatio.jsx:5-11`（死） | ratio_5d：<0.5 红 / ≤1.0 黄 / >1 绿 | ratio ≥1.0 就是 bull | 双 · **不一致**（1.0 处） | 1.0 与原文不符 | 否 |

## 附带发现（不在前端边界，路由给 DATA ALEX）

- `pipeline/screeners/state_board.py:128-139`：Market State 板的 thrust 行**后端自己**还在用单日、只看价格的 `up_4pct`，配文「a thrust needs {need} of today's {universe}」——跟同一文件引用的 `thrust_count`（现在 300、双日、Stockbee 分子）不是一个规则。所以就算前端改成读引擎，板上那一行仍然是另一套判据。
- `data/output/breadth.json` 里的 `vote_detail.thrust.line` 现在还是 634.495（旧规则 0.113×universe）——09-18 的引擎改动还没跑出新数据。等下一次正班跑完，`line` 会变成 300，而前端 #1 仍然读单日 `up_4pct`，分歧会延续（见上面回放）。

## 最该处理的前 10 个

1. **#1 thrust 牌面**：双份规则，而且已经在 8 天里错了 6 天，这是今天事故的本体。改法：读 `verdict.votes.thrust` 或 `thrust_state`，不再用自己的四个分支。
2. **#19 + #15-18 首页 Regime 条**：首页最显眼那个词是前端用五个自造的映射拼出来的，后端没有、登记表没有；应该搬进管线、登记，或者在页面上写明是自造的。
3. **#29 Screener Liquid 闸**：还在用 08-18 已经弃用的「100 万股」，页面文案也照着写；和后端 `tradeable` 的定义不一样。
4. **#7 BreadthTable 一把 60/40 尺子套四列**：%>200 这列 33% 的行颜色和引擎投票相反，读者看到的颜色不是引擎的判定。
5. **ratio 1.0 这条线（#3/#4/#6/#10/#40）**：Stockbee 原文 bull 线是 2（bear 0.5 一致）；前端五处写死 1.0，而且和后端 `THRESHOLDS` 同错——要改就一起改，改前先把原文加进登记表。
6. **#12 Reading.jsx 的 RANGE 拷贝**：前端内部双份，已经分叉（thrust 写死 300），生成的是页面首句「N 票压在线上」。应该删掉，改从 VoteGlyphs（或后端 margin）取。
7. **#5 季度 spread 的「structural bull intact」**：口径和方向语义都跟 Stockbee 原文不符（原文看 25%-up 的绝对数、<200 反向看多），措辞是前端发明的。
8. **#26 ATR 位 7.0 边界 + 0–4/5–7 未登记**：7.0 前端叫「持有」、后端叫 Extended；带的出处（Jacobs/Jeff Sun）没进 METRIC_SOURCES；4–5 的文案有空档。
9. **#2 T2108 分档**：20 对得上原文；80 与 Duru 的 70 两说；40/60 查无标准——应该登记「20/80 取 Stockbee、40/60 自造」，否则页面上的 weak/strong 看起来像标准读数。
10. **#31/#32 前端自造的「RS」**（ETF 组内 RS、rotation 的 rs2w/wkAccel/3.2）：都挂着 RS 名字，而且只在浏览器里算；按登记表的命名规矩要么改名，要么搬到后端并登记。

来源：[Stockbee MM](https://stockbee.blogspot.com/p/mm.html) · [Stockbee 2011 breadth](https://stockbee.blogspot.com/2011/08/how-to-use-market-breadth-to-avoid.html) · [Dr. Duru AT50/T2108](https://drduru.com/onetwentytwo/t2108-resource-page/) · [McClellan Financial](https://www.mcoscillator.com/learning_center/weekly_chart/overbought_mcclellan_oscillator/) · [CAN SLIM (RS ≥80)](https://en.wikipedia.org/wiki/CAN_SLIM)
