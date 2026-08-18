# 每把刀一份档(A 出处 · B 我们的实现 · C 实证 · D 案例 · E 判词)

*C/D/E 段等 `study_*.csv` 出来后填;A/B 段先立。原话引用来自 `data/research/screener_competitors_2026-08-17.md`(Stockbee 博客、@oratnek_ill / @SteveDJacobs / @PrimeTrading_ 的 X 帖,2026-08-17 抓)和 `data/reference/screener_methods.md`。标【待补】的是还没抓到作者原文/案例的。*

---

## 1 · 4% Bullish(预设)/ `gainers_4pct`(Python)

**A 出处**:Pradeep Bonde(Stockbee)。原文扫描(Telechart):`c/c1>=1.04 and v>v1 and v>=100000`,盘中持续跑。他自己的用法——**选股后的人工闸才是关键**:「突破前不能已连涨 3 天 · 前一日窄幅 · 突破前有区间收缩或浅回调 · 前一段上涨要有序线性 · 是本轮行情的第 1–3 个 setup · 偏好年轻趋势」。离场:第 3 天收盘出一半;同日/次日 +8% 出一半并把止损移到高点下 25 分;跳空 +20% 全出;3 天无跟进就走;止损 = 突破日最低。目标:**3–5 天、8–20% 的一段动量爆发**。他配的组合:4% 日 × 前面有收缩(他的 anticipation 扫描找的就是"明天可能出 4% 日的票")。【待补:Stockbee 博客里的具体案例贴】
**B 我们的**:预设 = 日涨 ≥4% · RelVol ≥1 · 从开盘为正(Qullamaggie 的"高开低走不算")· rs_21d ≥60 · ADR 3.5–10 · $1B · 剔医疗。Python `gainers_4pct` = 只要 ≥4% + 量 > 昨日(更接近原文,无 RS/ADR 闸)。差异:我们没有他的"前 3 天没连涨 / 前一日窄幅 / 第几个 setup"三道人工闸——要靠 VCS 和 `sp_days` 去补。

## 2 · Weekly 20%+ Gainers(预设 & 晨报 `weekly_20_gainers`)

**A 出处**:Stockbee 的爆发尺度(3–5 天 8–20% 是一段;一周 20%+ 是极端爆发)+ Qullamaggie 找"第一波"的方式:先大涨,再等它回踩/收缩,第二次入场。它不是入场信号,是**加入观察池的信号**。【待补:Qullamaggie "look for stocks up 20%+ in a week" 原推/直播原话】
**B 我们的**:`perf_5d ≥ 20%`(08-18 起 5 根 bar,原读 Finviz 日历周)· ADR 3.5–10 · 预设加 $1B 剔医疗。

## 3 · Vol Up Gainers(预设)/ `vol_up_gainers`(Python)

**A 出处**:Stockbee 同一脉,重心从"涨多少"移到"量有没有人付"。【待补原话】
**B 我们的**:预设 = 日涨 ≥0 · RelVol ≥1.5 · ADR 3.5–10;Python = 日涨 ≥4% 且 RelVol ≥1.5(严)。RelVol 是对自己均量,要配美元成交额。

## 4 · Weekly Momentum 97(预设,原 Momentum 97)/ Composite 97(`momentum_97` Python)/ Monthly Leader 97(预设,原 97 Club)

**A 出处**:Qullamaggie 式"只看最强的 3%";IBD RS 97+;Steve Jacobs 的 Qullamaggie Inspired Screener 原话:「RS ≥ **97**(1W/1M/3M/6M 任一)· Price ≥ MA20 ≥ MA50 ≥ MA100 ≥ MA200 · ATR RS ≥ 50」。作者们把它当**候选池**不当入场;Jacobs 配 ATR Matrix 0–4x 决定能不能买。
**B 我们的**:三个不同问题——Weekly = 1 周分位 ≥.97 且 3 月 ≥.85 且 trend_base(这周在冲);Composite = 四窗口等权前 3%(含刚起步的);Monthly Leader = rs_21d ≥97 且 h_score ≥80(这个月一直强)。三个不重复,交集才是"本月领头且这周在动"。

## 5 · Stockbee 9M Setup(预设)/ `episodic_pivot`(Python)/ Delayed EP(工具)

**A 出处**:Stockbee **EP(Episodic Pivot)** 原文:`v>3*avgv50.1 and v>=300000`;财报 QoQ **+100%** 且 EPS ≥5 分、营收 +5%;跳空 5–300%;**neglect + 改变游戏的财报**;持 2–5 周。EP9M = 当天 ≥900 万股。**Delayed EP**:第一天不进——「第 1 天常常冲高回落,3–4 天后市场以为消息消化了、往往还会再往下漂;等它在 EP 日区间里收缩、守住,再在第二次突破进场」。
**B 我们的**:9M 预设 = 均量 ≥9M · RelVol ≥1.5 · 日涨 ≥5% · DCR ≥60 · 剔医疗;`episodic_pivot` = 跳空 ≥10% 且 RelVol ≥3 且市值 ≥$500M(第一天);`delayed_ep_scan` 四态(failed/breaking/basing/drifting),日志已连记 08-13/14/17。**缺催化剂/财报字段**。

## 6 · Sugar Babies(预设)

**A 出处**:Stockbee 的 "sugar babies" —— **惯于放量大涨的体质股**,原规则:量 ≥9M 且涨幅 ≥4% 的天数。看的是性格不是今天。【待补原贴】
**B 我们的**:`bo_count_1y ≥10 且 bo_count_3m ≥2`(我们的突破日计数,不是他的 9M×4% 口径——**已知偏离**)。

## 7 · Pocket Pivot(预设)/ PP Count(预设)/ 晨报 `pp_today` `pp_2plus_10d` `morales_pp_10d`

**A 出处**:**Gil Morales / Chris Kacher**《Trade Like an O'Neil Disciple》(2010):口袋支点 = **上涨日,且当日成交量大于前 10 个交易日里任何一个下跌日的成交量**;买点是在 10 日线附近或从下方穿越 10 日线的那天;要求"建设性的整理"作前提,不能是价格已经过度延伸后的放量。【待补:书中原文页码 + 他们的 AAPL/BIDU 案例】oratnek 的 "PP (Vol > 10D)" 是变体:**阳线且量 > 前 10 根全部的最大量**;他把"10 日内出过 PP"当选股前提,"2nd Pivot 当天出 PP"当最佳加仓日。
**B 我们的**:两个定义并存、两个名字——`pocket_pivot`/`pp_count_10d/30d` = Morales;`vol10_green*` = oratnek。三格全带 trend_base 语境门(08-17 事件研究:没有语境门,两种 PP 的左尾都比随机日深 2.7pp——放量阳线里含派发日)。

## 8 · 21EMA Watch(预设)/ 晨报 `liquid_leader_pullback` / `ema21_watch`(Python)

**A 出处**:Qullamaggie / oratnek / Alex 的"回踩 21EMA 再上车":领头股第一波之后回到均线,止损可以放很近,仓位才做得大。**教材 M2_L09(Liquid Leader Pullback RS)**:liquid leader · 周涨 <12% · 离 21EMA 0.5–1 ADR · 离 50 0–3 ADR · 5 日对 20 日收缩 · 财报 7 天外。Alex 的形态词典:BO21PB(突破后 21ema 回踩)。Jacobs:ATR Matrix 0–4x 是建仓区。
**B 我们的**:预设 = trend_base · 离 21EMA −0.5~+1 ATR · 离 50 0~3 ATR(08-17 起真 ATR 口径)· 周涨 0–15% · DCR ≥20 · PP ≥1 · ADR 3–6;晨报格 = 教材四条(缺收缩、财报两条);Python `ema21_watch` = SMA20 距离 −2~+3% + RS ≥80(粗)。

## 9 · LL-HL Structure(晨报三格 `ll_hl_1st / 2nd / trend_break`;`stop_hit / ll_break`)

**A 出处**:@oratnek_ill 2026-06-13 长贴 + 他开源的 TradingView "Advanced Structure Pivot"。原话:「LL-HL 结构成立 → **1st Pivot 建半仓**,止损 = 21EMA Low;必须在 **5 根(理想 3 根)**内触及 2nd Pivot,10 根还没到就算仍在 21EMA 上方也清仓;触及 2nd → 加仓,止损上移到 1st;**2nd Pivot 当天出现 PP 最理想**;离场 +25% 优先落袋,否则 R:R 到 3 或 ATR-from-50SMA ≥7 减 33%;收盘跌破 21EMA Low 清」。选股前提:RS21 >70 · RS63 >80 · $1B · 50 日均量 >1M · 10 日内有 PP · ATR% from 50SMA <5(理想 <4)。作者案例:他每天的 Today's Watchlist(我们抓了 08-11/13/14 三天:OUST、EXPE、AVPT、FIG、KVYO、DELL、NTSK、IOT、FRSH、OKTA、MNDY、FROG、PD、PRCH、GO、PBF、BWIN、AXON、TENB、KLAR、DINO、ACVA、RAL)。
**B 我们的**:`pipeline/screeners/structure_pivot.py`,忠实移植,黄金 5/5;`sp_signal ∈ {1st_break, 2nd_break, counter_break, tp1_hit, tp2_hit, stop_hit, ll_break}`。他的三格 = 我们三格。**已知口径差**:描述说"收盘",代码用 high(升阶)/low(作废),移植照代码。

## 10 · VCS(晨报 `vcs`)/ `vcp`(Python)

**A 出处**:VCS = @oratnek_ill 开源 "VCS v2"(压缩分:13/63 日 ATR 比、13/63 日 stdev 比、5/50 日量比、效率过滤,EMA3 平滑,连续紧缩加分,低点跌破 ×0.75)。他的读法:「**80+ 临界压缩、60–80 发展中、<60 扩张**」;他的用法是"压缩里等 PP 或 1st Pivot"。`vcp` 的出处是 **Mark Minervini** VCP(Volatility Contraction Pattern,《Trade Like a Stock Market Wizard》2013):2–6 次收缩、每次幅度大约减半、量随收缩递减、突破 pivot 放量。【待补书页】
**B 我们的**:`vcs` = v2 忠实移植(黄金 4 位小数);晨报格 08-18 起 = vcs ≥60 且 rs_3m ≥80 且站上 SMA50 且 ADR ≥3(领先里的压缩)。`vcp` Python = 我们自己的收缩计数(`num_contractions`、`pct_to_pivot`),不是 Minervini 的逐字实现。

## 11 · Anticipation(晨报 `anticipation`)

**A 出处**:Stockbee 三个 anticipation 扫描原文:TI65 `avgc7/avgc65>1.05 and minv3.1>100000`、Double Trouble `c/minl252>=1.8 and minv3.1>=100000`、MDT `c/avgc126>1.19 and minv3.1>100000`,**都要当日涨跌在 ±1% 内**(安静日)。用法:找"明天可能出 4% 突破的票"——强势 + 今天安静。
**B 我们的**:三选一 × |change| ≤1% × vcs ≥60 × ADR ≥3(加了 VCS 是我们的组合)。

## 12 · Liquid Leaders / True Market Leaders(晨报 leaders 区)

**A 出处**:Alex Desjardins(@PrimeTrading_ / TradersLab):Liquid Leaders Scan sorted by RS Rank(约 20 只)· 21dma-structure Pullback;漏斗 UniverseList(500)→ WatchList(10–100)→ FocusList(0–10)。**教材 M2_L09** 定义:ADV ≥2M · 站上 50SMA · RS 前 20%。TML = 技术 + 基本面 + 所在主题都在领跑(Minervini/TraderLion 系)。
**B 我们的**:`liquid_leader` = avg_vol ≥2M & >SMA50 & rs_3m ≥80 & tradeable;TML = liquid_leader × 组四态 Leading × rs_1m ≥80。**已回测**:价格口径的 Liquid Leader 当 20 日预测器 NULL(+0.41% vs 流动性基线 +0.71%);TML 那一维只能前瞻验(`leaders_log.csv` 08-14 起)。

## 13 · Extended(晨报 `extended`,ATR Matrix ≥7)

**A 出处**:@SteveDJacobs ATR Matrix 原话:「<0 忽略 · 0–4x 建仓 · 5–7x 持有 · **≥7x 开始减:7/8/9/10/11x 各卖 20%,11x 清空**」;学自 @jfsrevg 与 @RealSimpleAriel;oratnek 用 ≥7 减 33%。ADR 带 3%–6%(上限 = 最大可承受亏损 ÷ 1.5)。
**B 我们的**:`atr_from_sma50 = (close−SMA50)/ATR`(有 (1+dist) 分母,他们的公式漏了),≥7 进 trouble 区。**我们上周实测**:延伸预测的是标签到期不是跑输(21 日仍强,42–63 日转负)——是中期减仓信号。

## 14 · `healthy_charts`(Python)

**A 出处**:我们自己的(无外部原型):在 50/200SMA 上、离 52 周高 5–25%、1 月为正、RS ≥80、RelVol ≥0.5 —— "在歇的上升趋势"。
**B**:同上。

---

# C · 实证汇总(两组样本)

**样本一 · 老 7 个 Python 筛选器**:`ticker_events.csv`,2026-03-09→08-17,100 个交易日,66,121 条命中,可测 43,000 条(有日线的)。截止日收盘买入,持 3/5/20 日;基线 = 同日同数量随机票(重复抽样取中位)。
**样本二 · 17 个晨报面板**:11 个截止日整管线重算(05-22 · 06-05 · 06-12 · 06-26 · 07-02 · 07-10 · 07-31 · 08-07 · 08-11 · 08-13 · 08-14;06-19 休市、07-17/24 限速空跑已剔),闸内命中 8,600 条。**这 11 天覆盖的是 6 月中旬见顶 → 7 月领头股 30–50% 回撤 → 8 月上旬 V 型反转这一段,一个格局,读数要带着这个前提看。**

## C1 · 老 7 个(20 日中位 / 基线 / 胜率 / 20 日内最大有利·不利中位)

| 筛选器 | n | 20d | 基线 | 胜率 | MFE / MAE | 判 |
|---|---|---|---|---|---|---|
| **vcp**(收缩) | 1,408 | **+2.9%** | +0.6% | **64%** | +7.6% / −5.3% | ✅ 唯一稳赢基线的;回撤最浅 |
| healthy_charts | 9,743 | +1.35% | +1.0% | 54% | +9.7 / −8.3 | ≈ 基线,略正 |
| ema21_watch | 7,357 | +0.85% | +1.55% | 55% | +7.0 / −6.3 | 低于基线 |
| episodic_pivot | 288 | −0.3% | +0.4% | 49% | **+11.5 / −10.7** | 高方差、零中位 —— 第一天别进 |
| gainers_4pct | 15,812 | −0.5% | +0.6% | 49% | +12.0 / −9.6 | 追涨日 |
| momentum_97 | 5,572 | −0.65% | +0.9% | 47% | +10.7 / −10.6 | 榜 ≠ 入场 |
| vol_up_gainers | 3,820 | **−1.5%** | +0.15% | 46% | +11.0 / −9.8 | 量增当天买没有边 |

3 日窗口(Stockbee 持仓期)全部在 ±0.3% 内 —— **没有一把刀有 3 天内的中位边**;他的"3 天出一半、+8% 出一半"吃的是尾部(MFE 中位 11–12%),不是中位。

**组合切片(老 7)**:
- momentum_97 **× ATR Matrix ≤4** → **+2.6% / 54%**(榜本身 −0.65%);× ATR >7 → −1.0%。**Jacobs 的"0–4x 才建仓"在我们数据上成立。**
- gainers_4pct × 当日 4–8% → +0.5% / 51%;**× 当日 ≥15% → −9.3% / 36%**(587 条)—— 追暴涨日是全表最差的一件事。
- vcp × 贴着突破位 ≤3% → +2.8% / 64%;× 收缩 ≥3 次 → +2.7% / 65%(各切片都稳)。
- ema21_watch × ATR ≤2 → +1.2%(略好,仍低于基线)。
- vol_up_gainers 任何切片都负。

## C2 · 17 个面板(11 个截止日,20 日中位 / 基线 / SPY / 胜率)

| 面板 | n | 20d | 基线 | SPY | 胜率 | 判 |
|---|---|---|---|---|---|---|
| **ll_hl_trend_break** | 302 | **+3.3%** | +0.35% | +1.4% | **68%** | ✅ |
| **ll_hl_1st** | 512 | **+2.75%** | +0.6% | +1.6% | **65%** | ✅ MAE 中位只有 −3.7% |
| **ll_hl_2nd** | 635 | **+2.2%** | 0.0% | +1.4% | **62%** | ✅ |
| extended(≥7 ATR) | 126 | +1.4% | +0.4% | +1.4% | 76% | 样本含并购钉价票;剔掉后"仍在动的延伸股" +4.7% / 71% —— 延伸不等于马上跌 |
| vcs | 90 | +1.2% | +1.4% | +1.6% | 52% | ≈ 基线 |
| pp_2plus_10d | 997 | −0.8% | 0.0% | +1.4% | 47% | 无边 |
| morales_pp_10d | 1,493 | −0.8% | +0.2% | +1.4% | 47% | 无边 |
| pp_today | 390 | −0.8% | −0.1% | +1.4% | 45% | 无边 |
| bullish_4pct | 379 | −0.8% | −0.5% | +1.4% | 48% | 追涨日;× ATR≤4 × 4–8% 才到 −0.4% |
| weekly_momentum_97 | 150 | −1.3% | +0.3% | +1.4% | 48% | 追延伸(× ATR≤4 也没救,这段样本里 −4.7%) |
| anticipation | 109 | −1.7% | +1.6% | +1.6% | 41% | 这段样本负 |
| liquid_leaders | 1,682 | −2.0% | +0.6% | +1.6% | 45% | 资格名单不是信号(与 08-17 回测同) |
| weekly_20_gainers | 409 | −3.8% | −0.5% | +0.3% | 44% | 上周暴涨的下周均值回归 |
| ll_break | 377 | −3.8% | +1.0% | +1.6% | 39% | 出场信号,理应负 ✅ |
| **liquid_leader_pullback** | 195 | **−4.5%** | +1.1% | +1.6% | **38%** | ❌ 这段样本里"领头股回踩"是领头股在崩 |
| stop_hit | 248 | −0.9% | +1.5% | +1.6% | 49% | 出场信号 |

**面板组合切片**:
- LL-HL 三格 **× top_3m(3M 前 15%)反而更差**(1st −7.7% / 2nd −1.9% / trend −14%):这段是领头股崩塌期,oratnek 的"3M 领先池"在这段会伤人 —— **池子好坏是格局函数**。
- LL-HL 1st × RS 线新高 = +1.9%(不比不加强);× ATR≤4 = +2.0%(1st 本身几乎都在 ≤4)。
- 4% Bullish × ATR≤4 × 4–8% → 10 日 +2.9% 但 20 日 −0.4%:4% 日的边只活 10 天。
- PP × VCS≥60 样本 <5 条(闸内同时满足的太少),测不了。

# D · 案例(六只指定票 + 各面板抽样)见 `cases_six.md`;E · 判词见 `summary.md`
