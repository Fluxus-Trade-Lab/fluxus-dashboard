# 审计 B：市场层口径（只读）

基准：`$W` = `wt-audit`，HEAD `30b745bb`（origin/main，2026-09-18）。输出 JSON 是 09-17 夜跑的产物，**早于**今天的 thrust 修复 `05319404`，所以 `breadth.json` 里 thrust 的 `line` 仍是 634.495；下文引用的代码行号都来自 HEAD。
范围：10 个文件。**页面上根本不显示的**另列在文末（stockbee_ratio.json、quality.json，以及 etf_data 的 rrs/abc 字段）。

## 汇总

- **上页项目 49 个**（同一个量在多处显示只算一次，挂在它的判定那一行）
- **照抄原文 6**：thrust 投票、A/D line、基准 K 线/SMA、Power Trend 四条件、L6 交通灯、L6B 油门
- **自造已登记 6**：%above-MA（宇宙问题已登记）、Market Conditions 0-100、market_light Q1/Q2/Q3/verdict
- **自造未登记 27**：投票卡的合成规则（±4、risk、state、exposure）、各投票自己的阈值（T2108 40/60、pct200 50/30、danger ≤1/≥4、McClellan ±70）、state_board 九行的切点与 chain、regime 分档、RegimeBand 前端两套切点、Power 3、五个 danger 信号、correction_risk 的整套 + 三条旁注、tick_cycle 分档……
- **挂标准名但口径没对过原文 / 已经偏离原文 10**
- **和 thrust 同一形状（原作者有明确数字或条件，我们自己改了）：严格算 7 个**——ratio_5d、ratio_10d、25%/季、13%/34 天、25%·50%/月、「Up 4% / Down 4%」牌面、state_board 的 thrust 行。**另有 3 个变体**：原作者的池子是 NYSE 或普通股，我们换成了 Finviz 全池——T2108、McClellan、NH/NL 投票。

最要命的一条：今天的 thrust 修复**只修了投票**。`state_board.py:127-139`（上页：Board 卡、Chain 卡「Buyers show up」，并通过 regime.score 进 regime 带）还在用**只看价格的 `up_4pct`、单日、外加 up>down**，去对 `thrust_count()` 新返回的 300。注释（:27-28、:129-130）还写着「scales to each session's own universe」。有 Stockbee 列的 9 个交易日里，这一行判「good」3 天，引擎判 bull 0 天。

## 全表

记号：A＝照抄原文 · B＝自造已登记 · C＝自造未登记 · D＝挂标准名但口径未核对或已偏离 · ⚡＝与 thrust 同形状

| # | 项目 | 文件·字段 | 算在哪 | 页面组件 | 来源 / 自造 | 登记 | 代码声明 | 原文定义与偏离 |
|---|---|---|---|---|---|---|---|---|
| M1 | thrust 投票 | breadth `verdict.votes.thrust` / `vote_detail` | `breadth_signals.py:32,86-106,217-221` | VoteCard、VerdictCard（dashboard） | A，Stockbee「back-to-back 300-plus days」 | ✅ 第 86 行 | 有 | 一致。已知差异（宇宙没逐票对账）已登记 |
| M2 ⚡ | 5 日比值投票（bull ≥1.0 / bear <0.5）+ 牌面 + Archive 配色 | `mm.ratio_5d`、`votes.ratio_5d` | 比值 `breadth_store.py:82-83,136-141`（分子是**只看价格**的 `up_4pct`）；阈值 `breadth_signals.py:19` | VoteCard、MarketStateSummary:53-57、BreadthTable:74,159、RatioChart、Board「confirmation」 | D。设计文档 `2026-07-31-breadth-signal-engine-design.md:17` 自称「Stockbee absolutes decide」 | 无 | 无 | Stockbee MM 页：「ratio of 5 days of 4% b/o /5 days 4% b/d」，其中 4% b/o 是三条件扫描 `(100*(C-C1)/C1)>=4 AND V>=100000 AND V>V1`（[MM](https://stockbee.blogspot.com/p/mm.html)、[扫描公式](https://stockbee.blogspot.com/2014/08/how-i-get-market-monitor-numbers.html)）。**偏离①分子**：我们只看价格。实测最近 5 天，Stockbee 计数比值 1.014，我们发布 0.8475——投票会从 neutral 翻成 bull。**偏离②阈值**：5 日比值原文没给数（查过）；1.0 是自造 |
| M3 ⚡ | 10 日比值投票（bull ≥1.0 / bear <0.5） | `votes.ratio_10d` | 同 M2，`breadth_signals.py:20` | VoteCard、MarketStateSummary、BreadthTable、RatioChart | D | 无 | 无 | 原文：「When the 10 day ratio goes above 2 after market has been in bearish phase… bullish breadth thrust」「below .5… bearish thrust」（[What you need to know about market breadth](https://stockbee.blogspot.com/2010/05/what-you-need-to-know-about-market.html)）。**偏离**：bull 线 2→1.0；分子只看价格；原文的前提「after bearish phase for sometime」没实现 |
| M4 ⚡ | 25%/季 spread 投票（按符号）+ 季度牌面「structural bull intact」+ SpreadChart | `mm.up/down_25pct_qtr`、`votes.qtr_spread` | `breadth_metrics.py:134-135`（`perf_3m >= 0.25`，Finviz `Perf Quart` 点到点，`finviz_adapter.py:34`）；投票 `breadth_signals.py:145` | VoteCard、MarketStateSummary:59-65、SpreadChart、BreadthTable、Board「damage」 | D | 无 | 注释只写「sign-based」 | 原文 v12.4：`100*((C+.01)-(MINC65+.01))/(MINC65+.01) >= 25 and AVGC20*AVGV20 >= 250000`；跌方向用 `MAXC65`（[扫描公式](https://stockbee.blogspot.com/2014/08/how-i-get-market-monitor-numbers.html)）。**偏离①锚点**：原文从 65 日**最低收盘**起算（跌方向从最高收盘），我们是 3 个月前那天的点到点；**②**原文的流动性条件被丢掉；**③读法**：原文看的是水平——「up>25% in a quarter goes below 200 (bullish)」「down>25% … below 200 (bearish)」，MM 页写的是 <300/<200；我们改成了两者之差的符号 |
| M5 ⚡ | 13%/34 天 spread 投票 | `votes.spread_13_34` | `breadth_metrics.py:140-141`；`perf_34d` = `yfinance_adapter.py:1195` 点到点 34 根前；投票 `breadth_signals.py:146` | VoteCard（Archive 不显示） | D | 无 | 无 | 原文：`100*((C+.01)-(MINC34+.01))/(MINC34+.01) >= 13 and AVGC20*AVGV20 >= 250000`，跌方向用 `MAXC34`。**偏离**：锚点从最低/最高收盘换成了点到点，流动性条件丢掉。按符号投票这一读法原文没有（查过） |
| M6 ⚡ | 25%/月、50%/月 计数 | `up/down_25pct_month`、`up/down_50pct_month` | `breadth_metrics.py:136-139`（`perf_1m` = Finviz `Perf Month`，按日历月） | BreadthTable（Archive） | D | 无 | 无 | 原文：`C20 >= 5 AND (AVGC20*AVGV20) >= 250000 AND 100*(C-C20)/C20 >= 25`（50% 同形）。**偏离**：丢了 `C20≥$5` 和流动性两个条件；窗口是日历月，不是 20 根。原文读法「up>50% in a month goes above 20 (bearish)」没用上 |
| M7 ⚡ | 「Up 4% / Down 4%」牌面 + thrust 文字标签 | `mm.up_4pct/down_4pct` | 前端 `MarketStateSummary.jsx:21-32`（注释还写 0.113×universe） | MarketStateSummary（Breadth 页折叠区） | D | 无 | 注释过期 | 原文是三条件计数 + 连续两天。**偏离**：数值只看价格（09-17：781/213，Stockbee 计数 384/88），单日判 thrust，还多加了 `up > down`。`30b745bb` 已挂单给 UI Claire，还没改 |
| M8 ⚡ | state_board「thrust」行 → Chain「Buyers show up」→ regime.score | `state_board.rows[thrust]` | `state_board.py:127-139` | BoardCard、ChainCard，并经 regime 进入 | D（修了一半） | 无 | 注释 :27-28、:129-130 说「scales to universe」，已经错了 | 引擎（M1）已按原文改；这一行仍是单日、只看价格、外加 up>down，门槛却换成了 300。实测 9 天：这一行判 good 3 天，引擎 bull 0 天。Universe 5,600 下，只看价格的计数过 300 很容易，regime 分数会被系统性抬高 |
| M9 | Conditions 里名叫「thrust」的条件（`up_4pct − down_4pct > 0`） | `conditions` | `breadth_signals.py:536-552` | RegimeBand 线、VerdictCard（dashboard） | C，撞名：它只是净 4% 计数的符号 | 无 | 注释称「natural boundary」 | 叫 thrust，但和 Stockbee thrust 没有共同定义 |
| M10 变体 | NH/NL 投票 + Board「extremes」行 | `votes.nh_nl`、`state_board.extremes` | `breadth_signals.py:147`；`state_board.py:141-149`（切点 nh>2nl 等） | VoteCard、BoardCard、Chain、BreadthTable | D | 原始计数行写「保留不动」，**没说它在投票** | 无 | 标准池只含普通股（登记表第 55 行），标准比值 Record High Percent 50 线（[ChartSchool](https://chartschool.stockcharts.com/table-of-contents/market-indicators/high-low-index)）。我们已经在算 `new_highs_common` / `record_high_pct`，但投票和页面用的是被 SPAC 污染的原始计数（09-17：原始 28/30，普通股 4/28）。标准版做了，没上页 |
| M11 变体 | McClellan 值、符号投票、图 | `breadth.mcclellan_osc` | `breadth_store.py`（RANA、19/39 EMA） | VoteCard、BreadthCharts、BreadthTable | D | ✅ 第 50 行（没提池子） | 有 | 公式一致（[ChartSchool](https://chartschool.stockcharts.com/table-of-contents/market-indicators/mcclellan-oscillator)：19/39 EMA、0.10/0.05）。池子：标准口径是 NYSE（或 Nasdaq）涨跌家数，我们用的是 5,615 支 Finviz 池——和 %above-MA 同一个问题，那一行登记成 ⚠️，这一行登记成 ✅ |
| M12 | McClellan「extreme」注记 ±70 | `verdict.notes` | `breadth_signals.py:35,709-711` | VoteCard 注记 | C | 无 | 无 | ChartSchool 用的是 ±50/±100 做 thrust，±30 为犹豫区；±70 只见于二手科普（[commodity.com](https://commodity.com/technical-analysis/mc-clellan-oscillator/)）。McClellan 官网说这些阈值随时代变宽 |
| M13 变体 | T2108 值 + OVERSOLD(<20) / OVERBOUGHT(>80) 覆盖 | `breadth.t2108`、`verdict.env` | `breadth_metrics.py:150`；`breadth_signals.py:697-704` | VoteCard、VerdictCard、MarketStateSummary、BreadthTable「Worden」列、HealthChart 叠加 | D | ✅ 第 52 行 | 无 | TC2000 官方：「every stock on the NYSE」上方 40 日均线的占比（[TC2000 Help](https://help.tc2000.com/m/69404/l/755052-t2108-of-stocks-above-40-day-pma-also-t2s-110-112-114-116)）。20/80 与 Stockbee MM「below 20 lead to bottoms… 80s overbought」一致，但池子是 Finviz 全池不是 NYSE，登记成 ✅ 不对 |
| M14 | T2108 zone 投票 60/40（strong/weak）+ 牌面 zone | `votes.t2108_zone` | `breadth_signals.py:38,163-172`；前端再抄一份 `MarketStateSummary.jsx:35-37`、`BreadthTable.jsx:166` | VoteCard、MarketStateSummary、BreadthTable | C | 无 | 无 | 原文只有 20/80；40/60 自造，而且前端存着第二份 |
| M15 | pct200 投票 50/30 | `votes.pct200` | `breadth_signals.py:37,152-161` | VoteCard | C（池子问题已登记，阈值没登记） | 部分 | 无 | 查过，无标准切点 |
| M16 | %above 20/50/200 图与表 | `breadth.pct_above_*` | `breadth_metrics.py:149-152` | BreadthCharts、BreadthTable、Board「breadth/trend」 | B | ⚠️ 第 53 行 | 有 | 标准版 `*_sp500` 已经在算，**没上页** |
| M17 | A/D line | `ad_line` | `breadth_store.py` | BreadthTable | A | ✅ | — | 一致 |
| M18 | spy/qqq_danger 投票 ≤1 bull / ≥4 bear | `votes.spy_danger` | `breadth_signals.py:39-40,464-472` | VoteCard | C | 无 | 无 | 查过，无标准 |
| M19 | 五个 danger 信号（below 20SMA / 随机指标交叉 / 随机指标下弯 / 3 连低 / 收破前 3 低） | `market_health.*.danger` | `breadth_signals.py:253-279` | BenchmarkPanel | C。设计文档说来源是「the reference screenshot」，没写是谁的 | 无 | 无 | 随机指标 14,3,3 是 Lane 的通行设定；五条的组合没有出处。检索「danger signals 3 lower lows below 20 sma stochastic」无果 |
| M20 | bench_trend（SPY 和 QQQ 都在 SMA50 上方） | `votes.bench_trend` | `breadth_signals.py:687-691` | VoteCard | C | 无 | 无 | — |
| M21 | env：BULLISH/MIXED/BEARISH（score ≥+4 / ≤−4），12 票等权 | `verdict.env/score` | `breadth_signals.py:693-694` | VerdictCard（dashboard 头牌）、VoteCard，并经 Q3 进入 market_light | C。设计文档把它写成 Stockbee，这是**冒充** | 无 | 无 | Stockbee 原文：「It is total picture not just one thing」，没有给过合成打分 |
| M22 | risk：Low/Elevated/High（warn 合计 ≤2 / ≤6） | `verdict.risk` | `breadth_signals.py:715-716` | VerdictCard | C | 无 | 无 | — |
| M23 | spy_state / qqq_state / alignment | `verdict.*_state` | `breadth_signals.py:452-461` | BenchmarkPanel、RegimeBand structure 投票者 | C | 无 | 注释只说 fail bearish | — |
| M24 | confirmation 文案 | `verdict.confirmation` | `breadth_signals.py:722-734` | VoteCard | C | 无 | 无 | — |
| M25 | exposure / playbook / guidance 建议文案 | `verdict.*` | `breadth_signals.py:393-435` | VoteCard、VerdictCard | C（仓位建议文字） | 无 | 无 | OVERSOLD 那句引 Stockbee 300 连续两天，与原文一致；其余是自撰 |
| M26 | 百分位 context（按宇宙时代分段） | `verdict.context` | `breadth_signals.py:752-812` | MarketStateSummary、VoteCard | C | 无 | 有（自造已写明） | 自己历史里的归一化，不是标准读数 |
| M27 | Market Conditions 0-100 | `conditions.today/history` | `breadth_signals.py:588-668` | VerdictCard / RegimeBand 线 | B | ⚠️ 第 101 行 | 有 | 从没和 oratnek 的页面对过数；另见 M9 |
| M28 | RegimeBand 五档 18/40/62/84（Defence…Euphoria） | 前端 | `RegimeBand.jsx:68-71` | Dashboard RegimeBand | C（按档位占比调出来的） | 无 | 有（注释） | — |
| M29 | RegimeBand breadth 投票者切点 8/4/−3/−7 | 前端 | `RegimeBand.jsx:87-99` | 同上 | C | 无 | 无 | — |
| M30 | RegimeBand power 投票者 | 前端 | `RegimeBand.jsx:72,115-129` | 同上 | C。档位来自 Power 3，「binding」文字却列 Webster Power Trend 四条件，把两个指标混在一处 | 无 | 部分 | — |
| M31 | state_board 其余 7 行的切点（damage 0.55/0.45/0.35 · selling 0.5/0.8 · breadth 60/50/35 · trend 50/40/30 · extremes 2× · confirmation 1.2 · index repair） | `state_board.rows` | `state_board.py:82-125,141-180,189-209` | BoardCard | C | 无 | 无（只写了设计出处 `Fluxus_Operator_Model.md`） | — |
| M32 | chain 的 lit / partial（0.75 / 0.05） | `state_board.chain` | `state_board.py:245` | ChainCard | C | 无 | 无 | — |
| M33 | regime.score + 分档 47/63/75 | `breadth.regime` | `regime.py:95-104,116-165` | ⚠️ 前端没找到 `regime.score` 的渲染方（RegimeBand 注释说 08-24 起不再印），只在 JSON 里 | C | 无 | 有（经验四分位） | 分档是 08-09 用**旧** thrust 行冻结的；M8 的输入今天变了，档位和「27%→6%」回撤验证描述的已经是另一个分数 |
| M34 | Power 3 信号（POWER_3/CAUTION/WARNING/RISK_OFF）+ 「RISK OFF」标签 | `signals.*.signal` | `calc_signals.py:71-77`；`yfinance_adapter.py:1353-1362` | TickerCard（Dashboard 条）、RegimeBand power 投票者 | C | 无 | 无（没声明是自造） | 检索「Power 3 8 EMA 21 EMA 50 SMA」：只有通用的「stacked MAs」说法，**查过，无标准** |
| M35 | trend_status 距离（9E/21E/50S/200S/52wH） | `signals.*.trend_status` | `yfinance_adapter.py:1388-1394` | BenchmarkPanel 标尺 | C（轻） | 无 | 注释「Oratnek style」 | 52w 高用的是**收盘**最高，不是盘中最高 |
| M36 | Power Trend 四条件（作为 binding 文字） | `signals.*.power_trend` | `calc_signals.py:146-213` | RegimeBand binding（PowerTrend.jsx 没挂路由） | A | ⚠️ 第 99 行**过期**：仍写「五项检查与标准口径无一条对上」，代码 09-06（`6e76861a`）已按 Webster 对齐 | 有 | 两条提前失效条件没实现（已声明） |
| M37 | 基准 K 线 + SMA20/50/200 | `market_health` | `breadth_signals.py:342-368` | HealthChart | A | — | — | 标准 |
| M38 | L6 交通灯 SPY（QQQ 作旁灯） | `market_light.spy/qqq` | `market_light.py:117-192` | CourseRead | A | ✅ 第 69 行 | 有 | 一致（「上倾」的操作化是自造，已登记） |
| M39 | L6B 油门七档 | `*.gear` | `market_light.py:136-154` | CourseRead | A | ✅ 第 71 行 | 有 | 一致 |
| M40 | Q1 setups 指数 | `brightness.setups` | `market_light.py:195-249` | CourseRead | B | 🚫 第 72 行 | 有 | — |
| M41 | Q2 leaders（50 日线二元 + 0.2/0.5 分档） | `brightness.leaders` | `market_light.py:272-362` | CourseRead | B | ⚠️ 第 73 行 | 有 | — |
| M42 | Q3 breadth（= verdict.env 映射） | `brightness.breadth` | `market_light.py:365-382` | CourseRead | B | ⚠️ 第 74 行 | 有 | **继承了 M2–M5、M10–M24 的全部问题**：登记表说「口径见 breadth 各行」，可那些行大多不存在 |
| M43 | market_light verdict | `verdict` | `market_light.py:385-406` | CourseRead | B | ⚠️ 第 75 行 | 有 | — |
| M44 | Correction risk 主读数（VIX 五分位 × 200 日线的条件频率；21 日、−5%） | `correction_risk.prob/today/table` | `correction_risk.py:52-54,100-150,285-300` | CorrectionRiskPanel | C（自建统计表，是否有同类公开口径没写） | 无 | 有（docstring 写清是表不是模型） | 这是我们自己的研究产出，不冒充任何标准；只是缺登记行 |
| M45 | VIX/VIX3M 3EMA 三态 <0.8 / 0.8–1.0 / >1.0 | `ts_dimension` | `correction_risk.py:78-81,153-157` | CorrectionRiskPanel CondGrid | C（第三方 @turintrader） | 无 | 注释写「turin thresholds verbatim」 | 他的原文是 **0.8/1.0/1.1** 三个切点（`data/research/turin_trky_study.md:57,77`），我们丢了 1.1，注释里的「verbatim」不准确 |
| M46 | 旁注 NH/NL「Breadth washout」：NH/(NH+NL) 的 10-EMA，<0.30 / >0.85 | `side_readings.nhnl` | `correction_risk.py:244-270` | CorrectionRiskPanel SideNotes | C（第三方 KaibaraYuzan「KY」） | 无 | 部分 | 标准 High-Low Index 是 **10 日 SMA**，读 30/50/70（[ChartSchool](https://chartschool.stockcharts.com/table-of-contents/market-indicators/high-low-index)）；我们用 EMA 和 0.85。页面没用标准名，所以不算冒充，但没登记 |
| M47 | 旁注 GEX：252 日分位的五分位 | `side_readings.gex` | `correction_risk.py:271-283` | 同上 | C | 无 | 部分 | — |
| M48 | TICK cycle：band grind/washout（spread 252 日分位 ≤0.10 / ≥0.90）、SMA15、证据常数 | `tick_cycle.json` | `regime_ledger.py:73,265-326` | CorrectionRiskPanel（tick 那一层） | C（逆向 Raschke 的私有指标；n≈15 是猜的；分位分档按 spec 自认「我们自己的改造」） | 无 | 部分（spec 在 `indicators/fluxus-lbr-tick-cycle.txt`，代码 docstring 没写「自造」） | Raschke 没公开参数，**查过，无公开口径** |
| M49 | LeadersLaggards「RS 0-99」（组内按窗口收益排百分位） | `etf_data.change_pct/perf_1w` → 前端 | `lib/etfRank.js` | LeadersLaggards（Dashboard） | C（轻；「RS」是泛称，但本仓已有 `rs_rating` 那条撞名规矩） | 无 | 有 | — |

### 不上页的（不计入 49）

- `stockbee_ratio.json`：唯一的渲染方 `ScreenersSection.jsx` 没被任何路由引用。它的 `signal: THRUST` = 5 日比值 >3.0（`stockbee_ratio.py:41,175`）是自造的，而且和 Stockbee「thrust」撞名（原文：10 日比值 >2）。死输出，建议删或改名。
- `quality.json`：内部闸，无前端读者。
- `etf_data` 的 `rrs_*` / `abc` / `atr_pct` / `dist_sma50_atr`：只有 `EquitiesSection` / `EtfSection` 在读，两者都没挂路由。
- `signals.*.ma_structure`：PowerTrend.jsx 没挂路由。
- **标准版做了却没上页**：`record_high_pct`、`high_low_index`、`new_highs_common`、`up_4pct_stockbee`（只进了 thrust 投票）、`*_sp500`。页面上显示的全是对应的非标准版。
- `breadth_replay.json`：Time Machine 用的是同一个 `evaluate()`，问题与上表相同；09-05 之前 thrust 测不了。

## 最该处理的前 10 个

1. **M8 state_board 的 thrust 行**：今天的修复漏了它。它还在用只看价格、单日、外加 up>down 的规则，门槛却换成了 300，注释写的仍是旧说法。它经 Chain 和 regime 进入页面，9 天里判 good 3 天，引擎判 0 天。
2. **M2 / M3 5 日、10 日比值**：原文分子是三条件的 4% 计数，我们只看价格。10 日比值的 bull 线原文是 2，我们用 1.0。只换分子这一项，今天的 5 日比值就从 0.85 变成 1.01，投票翻面。
3. **M4 25%/季**：原文锚在 65 日最低/最高收盘，外加流动性条件，读水平（<200）；我们三处都改了——点到点、没有流动性、读符号。它同时驱动投票、「structural bull」牌面和 Board damage 行。
4. **M7 「Up 4% / Down 4%」牌面**：页面上印的是只看价格的计数，还用它判 thrust（09-17：781 对 Stockbee 的 384）。挂单已写，但没合。
5. **M21 env ±4 合成与设计文档里的「Stockbee absolutes decide」**：12 票等权、±4 分档全是自造，却以 Stockbee 名义写在设计里；它是 dashboard 头牌，也是 market_light Q3 的唯一输入。
6. **M5 13%/34 天**：同 M4 形状，MINC34/MAXC34 与流动性条件被丢掉。
7. **M13 / M11 T2108 与 McClellan 登记成 ✅**：官方池子是 NYSE，我们是 Finviz 全池，和 %above-MA 那一行（⚠️）同一个问题，状态却写成一致。20/80 与 ±阈值是在另一个池子上读的。
8. **M10 NH/NL 投票用原始（SPAC 污染）计数**：普通股版和 Record High Percent 都已经建好，也登记成 ✅，但投票、Board 和页面都没换过去。
9. **M6 25%·50%/月**：原文有 `C20≥$5` 与流动性两个条件，我们都没实现；窗口是日历月，不是 20 根。
10. **M36 登记表 Power Trend 行过期，且 M33 regime 分档的前提变了**：登记表仍说「无一条对上」，代码 09-06 已经对齐。regime 47/63/75 是按旧 thrust 行冻结的，M8 一改，分档和那句回撤验证文案就不再描述当前的分数。

来源（本次检索）：[Stockbee — How I get the Market Monitor Numbers](https://stockbee.blogspot.com/2014/08/how-i-get-market-monitor-numbers.html) · [Stockbee MM](https://stockbee.blogspot.com/p/mm.html) · [Stockbee — What you need to know about market breadth](https://stockbee.blogspot.com/2010/05/what-you-need-to-know-about-market.html) · [Stockbee — 5 day breadth ratio](https://stockbee.blogspot.com/2011/10/5-day-breadth-ratio-see-big-improvement.html)（没给阈值）· [TC2000 Help — T2108](https://help.tc2000.com/m/69404/l/755052-t2108-of-stocks-above-40-day-pma-also-t2s-110-112-114-116) · [ChartSchool — McClellan Oscillator](https://chartschool.stockcharts.com/table-of-contents/market-indicators/mcclellan-oscillator) · [ChartSchool — High-Low Index](https://chartschool.stockcharts.com/table-of-contents/market-indicators/high-low-index) · [commodity.com McClellan](https://commodity.com/technical-analysis/mc-clellan-oscillator/) · [dcimring/stockbee-dashboard](https://github.com/dcimring/stockbee-dashboard)（阈值在付费区，没取到）
