# 审计 A · `universe.json` 全字段产地与口径（2026-09-18）

只读审计。底：`origin/main` @ `30b745bb`；`data/output/universe.json` 时间戳 `2026-09-17T22:55:08Z`，5,615 行。
对照底账：09-04 产地台账（artifact `9ef7f967`，108 字段 A9/B7/C41/D51）、`field_audit_2026-09-04.md`、工单 `HANDOFF_DATA_field_audit_2026-09-04.md`；09-04 当时的字段集取自 `git show 15535a6e4:data/output/universe.json`（09-03 00:03Z 那班）。

## 汇总

- **字段总数 108**（与 09-04 同为 108：删 14 个、加 14 个，其中 4 个是改名）。
- **产地**：A 直拉 **7** · B 直拉改写 **4** · C 自算标准口径 **63** · D 自算自造口径 **34**（其中 29 个是度量，5 个是元数据：`bar_date` `bars_stale` `bar_scale_mismatch` `fund_source` `fund_asof`）。
- **D 类 29 个度量里**：已登记进 METRIC_SOURCES **11 个**（全是 ⚠️，没有冒 ✅）；**未登记 18 个**。未登记的 18 个里，代码里**完全没写**自造的 10 个，只有旁证、没写「自造」的 6 个，明写了的 2 个（`ema21_atr_dist`、`liquid_leader`）。
- **前端直接显示、却未登记的 D：12 个**——`rel_volume` `rs_1m` `rs_3m` `rs_6m` `rs_21d` `rs_63d` `f_score` `i_score` `trend_base` `momentum_97` `liquid_leader` `ema21_atr_dist`。
- **另有 1 个已登记的 D 违反自己的登记**：`h_score` 登记行 63 写「**不上页**」，个股页 `tickerReadings.js:115-116`「H / I / F 分」照印原值。
- **撞名（名字是标准名，口径不一致）**：`f_score`（Piotroski F-Score）· `rel_volume`（Finviz Relative Volume，前端 tooltip 还写着「Finviz construction」）· `eps_growth_next_y` / `eps_growth_this_y`（Finviz EPS next Y / this Y）· `momentum_97`（与同名 `momentum_97.json`、oratnek Momentum 97 三个定义）· `trend_base` 注释里的「WMA」（代码是简单均线）。另外个股页 Stats 有 3 处**标签**跟值对不上：「Avg Vol (50D)」实为 20 日、「Dist 20EMA%」实为 SMA20、「52W High%」没乘 100。
- **和 09-04 比**：改成标准口径 3 个（`adr_pct`、`bo_count_*` 判定、新增的 `three_weeks_tight` 取代 `wk_tight_3`）；补登记、补声明 7 个（`rs_rating` `h_score` `tradeable` `wk_band_3` `atr_pct_pctl_252` `range5_pct_pctl_252` `bo_count_*` 聚合）；09-04 后新增 14 个，全部带登记或出处。**09-04 就是 D、到今天仍然既未登记、代码里也没写的 10 个**：`rel_volume` `rs_1m` `rs_3m` `rs_6m` `f_score` `i_score` `range5_pct` `dist_hi20_pct` `trend_base` `momentum_97`。
- **机制缺口**：`pipeline/tools/audit_metric_names.py` 只检查**已登记**的行（docstring「WHAT THIS CHECKS」段），所以没登记的撞名（`f_score`、`momentum_97`）它永远看不见。

> 分类说明：09-04 把「有外部出处的自算量」（Stockbee 的 `ti65/mdt/c_low52w/perf_34d`、TSF 的 `vol_5d_50d`）归 D；本次按「是否照抄具名外部定义」归 C，逐行在「变化」列标了「改判」。09-04 的 D51 → 今天 D34，差额主要来自：删 10 个死字段、这 4 类改判、以及 `adr_pct` 改标准。

缩写：YA=`pipeline/adapters/yfinance_adapter.py` · RA=`pipeline/screeners/run_all.py` · FV=`pipeline/adapters/finviz_adapter.py` · FS=`pipeline/adapters/fundamentals_store.py` · TH=`pipeline/themes/__init__.py` · SP=`pipeline/screeners/structure_pivot.py`。前端（均在 `frontend/src/components/`）：SCR=`screener/ScreenerPage.jsx`+`StockTable.jsx` · TS=`ticker/TickerStats.jsx` · TR=`ticker/tickerReadings.js`（经 TickerTrendIndicators / TickerKeyLevels 渲染）· QS=`ticker/TickerQuickStats.jsx` · SPn=`ticker/TickerStatusPanel.jsx` · HDR=`ticker/TickerHeader.jsx` · TM=`groups/ThemeMembers.jsx` · MC=`watchlist/shortlist/manualCards.js`（手加名卡直接读 universe，经 NameCard 渲染）· OV=`portfolio/tabs/OverviewTab.jsx`。「间接」指经其它 `data/output` 文件（watchlist.json / shortlist.json / groups.json / breadth.json / ticker_events）或预设 `preset_hits.py` 生效。`lib/screenerFilter.js` 与 `screener/WatchlistTab.jsx` 仍无人挂载（grep `WatchlistTab` 只命中自身），**不计为读者**。

## 全表（108 行，按产地排序）

| 字段 | 产地 | 算在哪 | 前端读者 | METRIC_SOURCES 状态 | 代码是否声明 | 09-04 以来变化 | 候选标准与出处 |
|---|---|---|---|---|---|---|---|
| `ticker` | A | FV:24 | 全站 | 无需 | — | 未变 | — |
| `volume` | A | FV:44 | 无直接读者（`quality.py` 只看缺失率） | 无需 | — | 未变 | — |
| `sector` | A | FV:46 | SCR·TS·HDR·MC | 无需 | — | 未变 | — |
| `industry` | A | FV:47 | SCR·TS·HDR | 无需 | — | 未变 | — |
| `revenue_growth` | A | FS:88（yfinance `revenueGrowth`，单季 YoY） | 无前端读者；间接：f_score | 未登记 | FS:26-30 写明与 Finviz「Sales past 5Y」不同窗 | 未变 | — |
| `eps_growth_this_y` | A | FS:89（yfinance `earningsGrowth`，单季 YoY） | 无前端读者 | 未登记 | FS:31 只写「(yoy)」，**没说它不是 Finviz「EPS this Y」** | 09-04 表未列 | ⚠️撞名：Finviz「EPS growth this year」＝当财年 EPS 增速（[Finviz help](https://finviz.com/help/screener)）；我们是单季 YoY |
| `in_sp500` | A | RA:299（Finviz `idx_sp500`） | 无前端读者；间接：breadth.json 的 `*_sp500` 列 | ✅ 行 67-68 | RA:265-283 docstring | **09-04 后新增** | — |
| `close` | B | FV:25 解析 Finviz Price | 全站 | 无需 | — | 未变 | — |
| `change_pct` | B | FV:26-31 解析 + YA:1192 仅补空 | HDR·MC·TickerCard | 无需 | YA:1188-1191 | 未变 | — |
| `market_cap` | B | FV:352 `parse_market_cap` | SCR·TS·QS | 无需 | — | 未变 | — |
| `eps_growth_next_y` | B | FS:84-87 `forwardEps/trailingEps−1` | 无前端读者；间接：f_score（RA:477） | **未登记** | FS:22-25 写明「Finviz 的是分析师预估增速」 | 未变（09-04 ⚠️） | ⚠️撞名：Finviz「EPS next Y」＝分析师下一财年 EPS 预估增速（[Finviz help](https://finviz.com/help/screener)） |
| `perf_1w` | C | YA:1193（c/c[-5]，4 个日收益） | SCR(1W)·TS·TM | 未登记（简单收益，无需） | RA:394-409 注释称「来自 Finviz 日历窗」——但 FV:161-165 写明免费版只抓 Overview、无 Perf 列，**注释与代码路径矛盾** | 未变（09-04 ⚠️） | — |
| `perf_1m` | C | YA:1194（c/c[-21]） | TS·TM | 未登记（简单收益，无需） | RA:394-409 注释称「来自 Finviz 日历窗」——但 FV:161-165 写明免费版只抓 Overview、无 Perf 列，**注释与代码路径矛盾** | 未变（09-04 ⚠️） | — |
| `perf_34d` | C | YA:1195 | 无前端读者；间接 breadth（Stockbee 13%/34d） | 未登记 | 行内无注释 | 未变（09-04 D⚠️，按 Stockbee 窗口改判 C） | — |
| `perf_3m` | C | YA:1196（c/c[-63]） | TS | 未登记（简单收益，无需） | RA:394-409 注释称「来自 Finviz 日历窗」——但 FV:161-165 写明免费版只抓 Overview、无 Perf 列，**注释与代码路径矛盾** | 未变（09-04 ⚠️） | — |
| `perf_6m` | C | YA:1197（c/c[-126]） | groups segments.js | 未登记（简单收益，无需） | RA:394-409 注释称「来自 Finviz 日历窗」——但 FV:161-165 写明免费版只抓 Overview、无 Perf 列，**注释与代码路径矛盾** | 未变（09-04 ⚠️） | — |
| `perf_1y` | C | YA:1198（c/c[0]，≥200 根） | TS | 未登记（简单收益，无需） | RA:394-409 注释称「来自 Finviz 日历窗」——但 FV:161-165 写明免费版只抓 Overview、无 Perf 列，**注释与代码路径矛盾** | 未变（09-04 ⚠️） | — |
| `perf_ytd` | C | YA:1199 恒 None | TS 无；无前端读者 | — | YA:1199「Would need calendar-year start」 | 未变（quality 判 unpopulated，100% 空） | 死列，建议删 |
| `sma20_dist` | C | YA:1200 | TS（**标签写「Dist 20EMA%」，实为 SMA20**）·TR | 未登记（标准） | — | 未变 | — |
| `sma50_dist` | C | YA:1201 | TS·TR | 未登记（标准） | — | 未变 | — |
| `sma40_dist` | C | YA:1202 | 无前端读者（breadth 用） | 未登记（标准） | — | 未变 | — |
| `sma200_dist` | C | YA:1203 | TS·TR | 未登记（标准） | — | 未变 | — |
| `atr` | C | YA:1204 · `calculate_atr` YA:118-127（Wilder RMA 14） | TS·TR·QS·SPn | 未登记（标准） | — | 未变 | — |
| `avg_volume` | C | YA:1039/1206（20 日均量） | SCR·TS（**标签「Avg Vol (50D)」错**）·QS（标签「Avg Vol 20D」但优先读 info.averageVolume10days） | 未登记 | 窗口在 TH:34-43 声明（09-05），产出处无 | 09-04 D❌ → 窗口已声明 | IBD/MarketSmith 常用 50 日均量 |
| `prev_volume` | C | YA:631/1270 | 无前端读者；间接 breadth `*_stockbee` | 未登记（平凡量） | YA:1262-1269 | **09-04 后新增**（79b34cf6） | — |
| `vol_5d_50d` | C | volume_enrichment.py:200 | SCR（Vol 5d/50d 列） | 未登记 | volume_enrichment.py:1-18（TSF 口径）；⚠️ 该 docstring 仍写「rel_volume 是今日/三月均量」，与代码不符 | 未变（09-04 D✅，按 TSF 口径改判 C） | — |
| `three_weeks_tight` | C | YA:1219 · fn YA:406-442 | 无直接；间接 shortlist 席位（name_cards.py:317） | ✅ 行 64 | YA:398-422 | **09-04 后新增** | — |
| `twt_buy_point` | C | YA:1220 | 无前端读者 | ✅ 行 64 | YA:401 | **09-04 后新增** | — |
| `oops_buy` | C | YA:1223 · fn YA:445-482 | 无前端读者 | ✅ 行 87 | YA:446-472 | **09-04 后新增** | — |
| `oops_sell` | C | YA:1224 | 无前端读者 | ✅ 行 87 | 同上 | **09-04 后新增** | — |
| `high_52w` | C | YA:1207（close/max(High)−1，分数） | SCR 仅回落位 | 未登记 | — | 未变（09-04 B❌：名字像价格） | — |
| `low_52w` | C | YA:1227（同上，对 min(Low)） | TR·QS | 未登记 | — | 未变（09-04 B❌） | — |
| `adr_pct` | C | YA:1247 · fn YA:24-56 | TS·SPn（注释）；间接 watchlist 闸/taxonomy | ✅ 行 58 | YA:25-49 | 09-04 D❌ → **已改标准**（843d527d） | — |
| `atr_pct` | C | RA:557 | TR·QS·HDR·OV·EtfRow | ✅ 行 59 | RA:549-556 | **09-04 后新增**（从 adr_pct 拆出） | — |
| `high_52w_dist` | C | RA:617-621（=high_52w 取 4 位） | SCR·TM·TS（**`toFixed(1)+"%"` 未×100，-4.5% 显示成 -0.0%**）·TR·QS·MC | 未登记 | RA:616 | 未变（与 high_52w 同一个数两个名） | — |
| `from_open_pct` | C | YA:1078/1250 | 无前端读者；间接 preset/watchlist | 未登记（平凡量） | YA:1077 | 未变 | — |
| `dcr_pct` | C | YA:1087/1252 | 无前端读者；间接 preset | ✅ 行 78 | YA:1085 | 已登记（09-04 后） | — |
| `pocket_pivot` | C | YA:1253 · fn YA:554-588 | 无前端读者；间接 preset | ✅ 行 79 | YA:555-567 | 已登记（09-04 后） | — |
| `pp_count_10d` | C | YA:1255 | 无前端读者；间接 watchlist | 未登记 | YA:1100-1103（oratnek 10 日窗） | 未变 | — |
| `vol10_green` | C | YA:1256 · fn YA:530-551 | 无前端读者；间接 watchlist | 行 79 仅提及「另一个量」，无独立行 | YA:531-535 | 未变 | — |
| `vol10_green_count_10d` | C | YA:1257 | 无前端读者；间接 watchlist | 未登记 | 同上 | 未变 | — |
| `atr_from_sma50` | C | RA:585（atr_enrichment.py） | TR·WatchlistPage·NameCard/MC | ✅ 行 80 | RA:564-584 | 已登记（09-04 后） | — |
| `ema21` | C | YA:1046/1271 | TR(KeyLevels) | 未登记（标准） | — | 未变 | — |
| `rs_line_pctl_21` | C | YA:1057/1272 · fn YA:190-208 | TR·WatchlistPage·NameCard/MC | ✅ 行 81 | YA:191-203（29/29 复现） | 已登记（09-04 后） | — |
| `rs_line_pctl_63` | C | YA:1063/1273 | TR·MC | ✅ 行 81（合并行） | YA:1058-1062 写明是「假设检验用」延长窗 | 已登记；⚠️ 63/126 窗是我们延长的，21 才是 oratnek 原值 | — |
| `rs_line_pctl_126` | C | YA:1064/1274 | 无前端读者；间接 watchlist | ✅ 行 81（合并行） | 同上 | 同上 | — |
| `perf_5d` | C | YA:1083（5 个交易日） | 无前端读者；间接 watchlist.json | 未登记 | YA:1079-1082 | 未变 | — |
| `cross_ema21_up` | C | YA:1055/1277 · fn YA:308-318 | 无前端读者；间接 watchlist/recap | 未登记 | YA:1047-1053 | 未变 | — |
| `cross_sma50_up` | C | YA:1056/1278 | 无前端读者；间接 watchlist/recap | 未登记 | 同上 | 未变 | — |
| `ti65` | C | YA:1261 · fn YA:604-633 | 无前端读者；间接 watchlist anticipation 面板 | 未登记 | YA:605-612（Telechart 原式） | 未变 | — |
| `mdt` | C | YA:1261 · fn YA:604-633 | 无前端读者；间接 watchlist anticipation 面板 | 未登记 | YA:605-612（Telechart 原式） | 未变 | — |
| `min_vol_3d` | C | YA:1261 · fn YA:604-633 | 无前端读者；间接 watchlist anticipation 面板 | 未登记 | YA:605-612（Telechart 原式） | 未变 | — |
| `c_low52w` | C | RA:611-613 | 无前端读者；间接 watchlist anticipation 闸 | 未登记（仅在删除节提及） | RA:605-609 | 未变（09-04 D✅，按 Stockbee Double Trouble 改判 C） | — |
| `sp_setup` | C | YA:1260 → SP:108-120 | TR | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_len` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_ll` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_hl` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_1st` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_2nd` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_tp1` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_tp2` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_phase` | C | YA:1260 → SP:108-120 | TR（印成「phase N」） | 仅在规则段行 39 被点名（与 Weinstein stage 撞名），无登记行 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_stop` | C | YA:1260 → SP:108-120 | TR(KeyLevels) | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_ma` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_signal` | C | YA:1260 → SP:108-120 | TR·NameCard/MC | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_days` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_dist_1st_pct` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_dist_2nd_pct` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `sp_counter` | C | YA:1260 → SP:108-120 | 无前端读者 | 未登记 | SP:1-20（oratnek Pine 逐字移植） | 未变 | — |
| `vcs` | C | YA:1259 · fn YA:681-696 | TR·NameCard/MC | ✅ 行 98 | YA:682-690 | 已登记（09-06）；撞名风险已在行 39 点名（VCP） | — |
| `ema10` | C | YA:1281 | SPn·OV | 未登记（标准） | — | 未变 | — |
| `ema20` | C | YA:1282 | SPn·OV | 未登记（标准） | — | 未变 | — |
| `wk_ema10` | C | YA:1283（W-FRI 重采样） | SPn·OV | 未登记（标准） | — | 未变 | — |
| `wk_ema20` | C | YA:1284（W-FRI 重采样） | SPn·OV | 未登记（标准） | — | 未变 | — |
| `rel_volume` | D | YA:1205（今日量 / **20 日**均量） | SCR（「Rel vol」列，**表头 tooltip 写「today's volume ÷ 3-month average (Finviz construction)」** StockTable.jsx:31,353）·TS·TM·NameCard/MC | **未登记** | **无**（YA:1205 零注释） | 未变（09-04 D❌） | ⚠️撞名：Finviz Relative Volume ＝ current volume / **3-month** average volume（[Finviz help](https://finviz.com/help/screener)） |
| `days_since_52wh` | D | YA:1211 | 无前端读者；间接 shortlist「52wh 回撤」席（name_cards.py:281-289） | **未登记** | YA:1208-1210 引 Andy 08-20 原话，未写自造 | 未变（09-04 D✅） | 查过：各家只有「N 日内创 52 周高」布尔（如 [TradingView NLS](https://www.tradingview.com/script/lciTJriG-NLS-52W-High-Screener-3-5-7-Days/)），无「距高点根数」标准名 |
| `wk_band_3` | D | YA:1218 | 无前端读者 | ⚠️ 行 65 自造 | YA:1213-1217 | 09-04 `wk_tight_3` D❌ → **改名+登记** | — |
| `range5_pct` | D | YA:1225（5 日 H-L 包络/close×100） | 无前端读者；间接 **shortlist 席位排序**（name_cards.py:318-324） | **未登记** | **无** | 未变（09-04 D❌） | 查过：无同名标准。近亲：Deepvue RMV（[KB](https://deepvue.com/knowledge-base/rmv/)，公式未公开）、Crabel NR7（单根区间） |
| `dist_hi20_pct` | D | YA:1226（对 20 日**收盘**高点的距离%） | 无前端读者；间接 shortlist 席位（name_cards.py:144-147,318） | **未登记** | **无** | 未变（09-04 D❌） | 近亲：Donchian 20 日上轨（[ChartSchool Price Channels](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/price-channels)，用 **High** 不是 Close） |
| `rs_1m` | D | RA:413（tradeable 场内横截面百分位×99，RA:363-392） | SCR(RS 1M)·TR·ShortlistTray·NameCard/MC | **未登记** | RA:394-409 解释了「场」，**没写这是自造口径**；且注释称 perf 来自 Finviz 日历窗，与 FV:161-165 矛盾 | 未变（09-04 D⚠️） | 形状≈IBD RS Rating（单窗横截面 1-99），但 IBD 只公开 12 个月、全市场池；我们是 1/3/6 月 + 自划 tradeable 池 |
| `rs_3m` | D | RA:414（tradeable 场内横截面百分位×99，RA:363-392） | SCR(RS 3M，默认排序键)·TR·TM·NameCard/MC | **未登记** | RA:394-409 解释了「场」，**没写这是自造口径**；且注释称 perf 来自 Finviz 日历窗，与 FV:161-165 矛盾 | 未变（09-04 D⚠️） | 形状≈IBD RS Rating（单窗横截面 1-99），但 IBD 只公开 12 个月、全市场池；我们是 1/3/6 月 + 自划 tradeable 池 |
| `rs_6m` | D | RA:415（tradeable 场内横截面百分位×99，RA:363-392） | SCR(RS 6M) | **未登记** | RA:394-409 解释了「场」，**没写这是自造口径**；且注释称 perf 来自 Finviz 日历窗，与 FV:161-165 矛盾 | 未变（09-04 D⚠️） | 形状≈IBD RS Rating（单窗横截面 1-99），但 IBD 只公开 12 个月、全市场池；我们是 1/3/6 月 + 自划 tradeable 池 |
| `rs_21d` | D | RA:416（=rs_1m 别名） | TS（「RS 21D」）·SCR 回落位 | **未登记** | RA:1072「deprecated aliases」 | 未变 | 同 rs_1m；标签「21D」而值来自 20 根 bar |
| `rs_63d` | D | RA:417（=rs_3m 别名） | TS（「RS 63D」）·SCR/TM 回落位 | **未登记** | 同上 | 未变 | 同 rs_3m |
| `rs_rating` | D | RA:443-460（0.4q1+0.2q2+0.2q3+0.2q4 对 SPY 超额，再排名） | 无前端读者；间接 groups.json 三张主题卡、market_light leaders | ⚠️ 行 76 社区重建 | RA:434-455 | 09-04 `rs_ibd` D❌ → **改名+改式+登记** | — |
| `f_score` | D | RA:477-480（eps_next / revenue 两个百分位取均值，缺则 50） | TR「H / I / F 分」（tickerReadings.js:115-116） | **未登记** | **无**（RA:462-476 讲了为什么取秩，没写自造、没提撞名） | 未变（09-04 D❌） | ⚠️**撞名：Piotroski F-Score**（9 项财报二元打分 0-9，[Wikipedia](https://en.wikipedia.org/wiki/Piotroski_F-score)）——与我们的「增速百分位」毫无共同定义 |
| `i_score` | D | RA:494-496（行业内 tradeable 成员 rs_3m 中位数再排名） | TR「H / I / F 分」 | **未登记** | **无**（RA:482-493 只讲中位数 vs 均值） | 未变（09-04 D⚠️） | IBD **Industry Group Relative Strength Rating**（197 组排名，[William O'Neil+Co](https://www.williamoneil.com/proprietary-ratings-and-rankings/)）——一手公式未公开 |
| `h_score` | D | RA:501-507（2F+3I+1rs1m+2rs3m+2rs6m)/10 | **TR「H / I / F 分」直接印原值**（tickerReadings.js:115-116）·ledger/MC 携带 | ⚠️ 行 63 **写明「不上页」**——**但页面在印它** | RA:526-529 | 09-04 D❌ → 已登记+已声明；**登记与页面矛盾** | — |
| `h_score_pctl` | D | RA:534 | TS「Composite Score」；间接 watchlist.json `composite_score` | ⚠️ 行 62（排名一致、权重自造） | RA:509-529 | **09-04 后新增** | — |
| `tradeable` | D | RA:339 · TH:58-87（$1B 市值 ∧ $2M 美元量，排 Shell） | SCR 过滤·ScanBar·TickerPage·Watchlist | ⚠️ 行 83（`is_tradeable`） | TH:59-80 三条偏离 | 09-04 D❌ → **已登记+已声明** | — |
| `falr_252` | D | RA:338 · TH:90-110 | 无前端读者 | ⚠️ 行 84 | TH:91-105 | **09-04 后新增**；名字带 252 但分子是 20 日均量×252 | — |
| `pp_count_30d` | D | YA:1254 | 无前端读者；间接 preset | **未登记** | YA:1097「30 is what we already shipped」——没说是自造窗 | 未变 | Morales/Kacher 口径是单日事件；30 日滚动计数无标准（查：pocket pivot count 30 day，无） |
| `ema21_atr_dist` | D | RA:593-601（(close−EMA21)/ATR） | TR「EMA21 距离（ATR）」·NameCard/MC | **未登记** | RA:597-600「our own quantity」 | 未变（09-04 D✅） | ATR Matrix（Jacobs/Jeff Sun）的 EMA21 变体；已登记的 atr_from_sma50 用 B/A 式，这个故意不用 |
| `atr_pct_pctl_252` | D | YA:1069/1275 · fn YA:241-305 | 无前端读者；间接 shortlist 名片 readings | ⚠️ 行 77 | YA:242-300（⚠️ docstring 写 `<=`，代码 YA:303 是严格 `<`） | 09-04 `atr_pctl_252` → **改名+登记** | — |
| `range5_pct_pctl_252` | D | YA:1070/1276 · fn YA:211-238 | 无前端读者；间接 shortlist 名片 | ⚠️ 行 77 | YA:212-227 | 09-04 `range5_pctl_252` → **改名+登记** | — |
| `liquid_leader` | D | RA:546-547（ADV≥2M ∧ >SMA50 ∧ rs_3m≥80 ∧ tradeable） | TR「资格」·shortlist 席位 | **未登记** | RA:538-545 引课程 M2_L09 / Alex Desjardins | 未变（09-04 D✅） | 课程定义（本机 SwingMasterclass），「RS 前 20%」用的是我们自造的 rs_3m |
| `bar_scale_jumps` | D | YA:1027/1280 · fn YA:338-403 | 无前端读者；间接 quality 闸 | ⚠️ 行 66 标准形状 | YA:339-370（tol 自造已写明） | **09-04 后新增** | — |
| `trend_base` | D | YA:1113-1122/1258（close>SMA50 ∧ 周线 10 均 > 30 均） | TR「资格」·NameCard/MC；间接 6 个 preset 前置闸 | **未登记** | **无**；YA:1113 注释写「10WMA > 30WMA」，**代码是 `rolling().mean()` 简单均线** | 未变（09-04 D❌） | ⚠️名不副实：WMA 是线性加权均线（[TA-Lib WMA](https://ta-lib.org/functions/wma.html)）。screener_methods.md:38 自称「Weinstein 式 Stage 2 闸」，但 Weinstein 要 30 周线**上升斜率**（本表行 96），[Minervini Trend Template](https://deepvue.com/screener/minervini-trend-template/) 要 150/200 日线排列+200 日线上升 |
| `perf_1w_pctile` | D | RA:637（**全池**分位，非 tradeable 场） | 无前端读者；间接 preset perf1wPctile / watchlist | **未登记** | RA:626-635 只讲 na_option 事故 | 未变（09-04 D⚠️） | 查过，无标准；与 rs_1m 的「场」不同，同页两种分母 |
| `perf_3m_pctile` | D | RA:639 | 无前端读者；间接 watchlist | **未登记** | 同上 | 未变 | 同上 |
| `momentum_97` | D | RA:641-644（1W 全池分位≥0.97 ∧ 3M 分位≥0.85） | TR「资格：momentum 97」 | **未登记** | **无** | 未变（09-04 D❌） | ⚠️撞名×2：①同名文件 `momentum_97.json`（momentum_97.py：四窗等权综合分位前 3%）②oratnek 的「Momentum 97」（外部屏，本仓 RESEARCH_PROTOCOL 称累计复现 98/105）。查「oratnek Momentum 97」无公开定义 |
| `bo_count_3m` | D | YA:1178-1183/1285 · fn YA:64-101 | 无前端读者；间接 preset boCount3m | 判定 ✅ 行 60 / 聚合 ⚠️ 行 61 | YA:1163-1166「THE AGGREGATION IS STILL OURS」 | 09-04 D❌ → **判定改标准，聚合已声明** | — |
| `bo_count_1y` | D | YA:1180/1286 | 同上 boCount1y | 同上 | 同上 | 同上 | — |
| `fund_source` | D元 | FS:256 | 无前端读者 | n/a | FS:17-19 | 09-04 表未列 | — |
| `fund_asof` | D元 | FS:257 | 无前端读者 | n/a | — | 09-04 表未列 | — |
| `bar_date` | D元 | YA:1025/1279 | TR provenance | n/a（元数据） | YA:485-503 | 未变 | — |
| `bars_stale` | D元 | YA:1025/1279 | TR provenance·TickerProvenance | n/a | 同上 | 未变 | — |
| `bar_scale_mismatch` | D元 | YA:1026/1279（容差 SCALE_MISMATCH_TOL=0.20，YA:187 无注释） | 无前端读者 | n/a | YA:494-497 | 未变 | — |

## 口径检索留痕（D 类未登记 + 撞名）

| 字段 | 搜了什么 | 结果 |
|---|---|---|
| `rel_volume` | Finviz Relative Volume definition 3-month | 有标准：Finviz = current / 3-month avg（[Finviz help](https://finviz.com/help/screener)）。我们 20 日；前端表头写的是 Finviz 口径 |
| `f_score` | Piotroski F-Score definition nine criteria | 有同名标准且完全不同物（[Wikipedia](https://en.wikipedia.org/wiki/Piotroski_F-score)） |
| `eps_growth_next_y` / `_this_y` | Finviz "EPS next Y" "EPS this Y" definition | Finviz 是财年口径的 EPS 增速（next Y = 分析师预估）（[Finviz help](https://finviz.com/help/screener)）；我们分别是 fwd/trail−1、yfinance 单季 YoY |
| `i_score` | IBD Industry Group Relative Strength Rating | 有具名标准（[O'Neil+Co](https://www.williamoneil.com/proprietary-ratings-and-rankings/)），一手公式未公开，只能自造 + 声明 |
| `rs_1m/3m/6m` | （09-04 已查 IBD RS）| IBD 只公开 12 个月、全市场池、1–99；多窗口的横截面百分位无具名标准 |
| `trend_base` | Minervini Trend Template criteria；WMA definition | Trend Template（[Deepvue](https://deepvue.com/screener/minervini-trend-template/)）与 Weinstein Stage 2（本表行 96）都要求长均线**上升**；我们只比两条周均线。「WMA」是线性加权（[TA-Lib](https://ta-lib.org/functions/wma.html)），代码不是 |
| `momentum_97` | oratnek "Momentum 97" screener | 查不到公开定义；仓内另有 `momentum_97.py` 第二个定义 |
| `range5_pct` | Deepvue 5-day range tightness | 无同名标准；近亲 RMV 公式未公开（[Deepvue KB](https://deepvue.com/knowledge-base/rmv/)） |
| `dist_hi20_pct` | Donchian 20-day high ChartSchool | 近亲 Price Channel 用 20 日 **High**（[ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/price-channels)）；我们用收盘高 |
| `days_since_52wh` | "days since 52-week high" screener | 查过，无标准名；各家只有「N 日内创新高」布尔 |
| `perf_*_pctile` · `pp_count_30d` | — | 查过，无标准（全池百分位与 30 日滚动计数都是我们的选择） |
| `avg_volume` | IBD 50-day average volume | IBD/MarketSmith 惯用 50 日；我们 20 日（已在 TH:34-43 声明），前端标签却写 50D |

## 最该处理的前 10 个（前端显示 × 未登记 × 撞名）

1. **`f_score`** —— 个股页「H / I / F 分」直接印；未登记、代码零声明；名字撞了 **Piotroski F-Score**，懂行的人读「F 分 50」会当成财报质量分。建议改名（如 `growth_score`）并立行。
2. **`rel_volume`** —— Screener 主表「Rel vol」列、个股 Stats、名卡都在印；未登记、产出处零注释；**表头 tooltip 明写「÷ 3-month average (Finviz construction)」而值是 ÷20 日均量**（StockTable.jsx:31,353；volume_enrichment.py:6 同样的错述）。页面上冒充标准读数的字面例子。
3. **`momentum_97`** —— 个股页「资格：momentum 97」印；未登记、零声明；一个名字三个定义（universe 布尔 / `momentum_97.json` / oratnek 外部屏）。
4. **`h_score`** —— 已登记，但登记写「不上页」，个股页照印原值（tickerReadings.js:115-116）。不改算法，只需撤下或换成 `h_score_pctl`。
5. **`trend_base`** —— 个股页「资格」、名卡、6 个预设的前置闸；未登记、零声明；注释说 WMA、代码是 SMA，方法文档自称「Weinstein Stage 2 闸」却没有斜率条件。
6. **`rs_1m` / `rs_3m` / `rs_6m`（及别名 `rs_21d` / `rs_63d`）** —— Screener 默认排序键就是 `rs3`；未登记；RA:394-409 注释说数据来自 Finviz 日历窗，与 FV:161-165「免费版无 Perf 列」矛盾，需先核实再登记。
7. **`i_score`** —— 个股页印；未登记、零声明；权重 3/10 进 h_score。对应 IBD Industry Group RS，照 h_score 的写法补「形状对齐、公式自造」即可。
8. **个股页 Stats 三处标签错**（`avg_volume`「Avg Vol (50D)」实 20 日 · `sma20_dist`「Dist 20EMA%」实 SMA20 · `high_52w_dist`「52W High%」未 ×100，-4.5% 印成 -0.0%，TickerStats.jsx:24/34/35）—— 字段本身是 C，但页面标签在冒充别的口径。前端一行修。
9. **`eps_growth_next_y` / `eps_growth_this_y`** —— 不上页，但撞 Finviz 同名列，且 `eps_growth_next_y` 喂 f_score；`_this_y` 连 docstring 都没说它是单季 YoY。改名或立行。
10. **`range5_pct` / `dist_hi20_pct` / `days_since_52wh`** —— 不上页，但决定 Short List 席位坐谁（name_cards.py:144-147, 281-289, 317-324）；未登记，前两个零注释。补登记「查过，无标准」即可。

顺带只需补登记行（已在代码里声明、口径无争议）：`ema21_atr_dist` · `liquid_leader` · `pp_count_30d` · `perf_1w_pctile` / `perf_3m_pctile`。死列：`perf_ytd`（100% 空，quality 判 unpopulated）。

## 顺手看到、未深查的

- `atr_pctl` docstring（YA:242-243）写 `count(ATR%_i <= today)`，代码 YA:303 是严格 `<`（METRIC_SOURCES 行 77 说已改严格）——文档落后于代码。
- `perf_1w` = `c/c[-5]`，是 4 个日收益；`perf_5d` 才是 5 个（build_groups.py:83-86 有说明）。
- `bar_scale_mismatch` 的 20% 容差（YA:187）无注释。
