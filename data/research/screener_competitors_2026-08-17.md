# 四个对标来源的筛选口径拆解 · 与我们 screener 的优劣比较

*2026-08-17。来源:Stockbee 博客原文(WebFetch)、@oratnek_ill / @SteveDJacobs / @PrimeTrading_ 的 X 帖(登录态 Chrome,照 `README_x_account_scrape.md` 的 handle 作用域抓法)。*
*所有数值都是他们本人写的原话,不是二手转述;落地影响都在 2026-08-14 的 universe(5,614 行)上实算过。*

---

## 〇、一句话结论

**他们四个人共用同一个核心数字,而我们没有这个数字:**

> **ATR Matrix = (close − SMA50) / ATR** —— 股价高于 50 日线多少个 ATR。

Steve Jacobs 用它决定建仓/持有/减仓的全部三段;oratnek 把它写进选股前提(<5,理想 <4)又写进离场(≥7 减 33%);Alex 的 21dma-structure pullback 是它的近亲。我们的 `sma50_r` 字段**名字像它,算的却是 close/SMA50 的比值**(见 `screener_inventory_2026-08-17.md` 第四节 A)。补上这一个字段,四家的口径我们才接得住。

血缘链:**@jfsrevg(Jeff Sun,我们已有 wiki)+ @RealSimpleAriel → Steve Jacobs(ATR Matrix 系统化)→ oratnek(纳入 LL-HL 体系)→ 我们的 21EMA Watch 预设(想抄但字段错了)**。

---

## 一、Stockbee —— 扫描语法最精确的一家

Telechart 语法,原文照抄:

| 扫描 | 语法 | 附加条件 |
|---|---|---|
| **4% 突破** | `c/c1>=1.04 and v>v1 and v>=100000` | 盘中持续跑 |
| **$ 突破** | `c-o>=.90 and v>100000` | 主要针对 >$40 的票 |
| **EP(Episodic Pivot)** | `v>3*avgv50.1 and v>=300000` | 财报 QoQ **+100%** 且 EPS ≥5 分;营收 +5%;跳空 5–300% |
| **TI65(anticipation)** | `avgc7/avgc65>1.05 and minv3.1>100000` | 当日涨跌在 **±1%** 内 |
| **Double Trouble** | `c/minl252>=1.8 and minv3.1>=100000` | 当日 ±1% |
| **MDT** | `c/avgc126>1.19 and minv3.1>100000` | 当日 ±1% |
| **Ants TTT** | 3 根 K 线幅度 ≤1.5%,当日 ≤0.3% | 无大跳空 |

**选股后的人工闸(他反复强调这才是关键)**:突破前不能已连涨 3 天 · 前一日窄幅 · 突破前有区间收缩或浅回调 · 前一段上涨要"有序线性" · 是本轮行情的第 1–3 个 setup · 偏好年轻趋势。

**离场**:第 3 天收盘出一半 · 同日/次日 +8% 出一半并把止损移到高点下 25 分 · 跳空 +20% 全出 · 3 天无跟进就走。止损=突破日最低。

> **对我们的意义**:`anticipation` 那三个扫描(TI65 / Double Trouble / MDT)**全是我们没有的**,而且都极易实现 —— 三条都只用 `avgc*`、`minl252`、`minv3` 这类可从日线直接算的量,加上"当日 ±1%"这个安静日闸。我们的 Stockbee 9M Setup 预设只抄了他的 EP 那一支。

---

## 二、@oratnek_ill —— 我们 watchlist 的原型(最完整的一份)

他 2026-06-13 那条长贴把整套写全了,以下是原话数值。

### 选股前提(= 他的 screener)

| 条件 | 阈值 | 我们有没有 |
|---|---|---|
| RS21 | **> 70** | ✅ `rs_21d` |
| RS63 | **> 80** | ✅ `rs_63d` |
| 市值 | **> $1B** | ✅ |
| 50 日均量 | **> 1M** | ✅ `avg_volume` |
| **PP** | 最近 **10 个交易日内**有一天:阳线 且 当日量为 10 日最高 | ⚠️ 我们有 `pocket_pivot`(仅当日)和 `pp_count_30d`(30 日),**没有 10 日窗** |
| **ATR% from 50SMA** | **< 5,理想 < 4** | ❌ **没有**(`sma50_r` 是比值) |

### 进出场(LL-HL Structure)

1. LL-HL 结构成立 → **1st Pivot 建半仓**,止损 = **21EMA Low**
2. 必须在 **5 根(理想 3 根)**内触及 2nd Pivot;10 根还没到就算仍在 21EMA 上方也**清仓**
3. 触及 2nd Pivot → 加仓,止损上移到 1st Pivot;**2nd Pivot 当天出现 PP 最理想**
4. 离场:**+25% 优先落袋**;否则以 21EMA Low 为风险单位,**R:R 到 3 或 ATR% from 50SMA ≥ 7** → 减 33%;剩余在**收盘跌破 21EMA Low** 时清
5. 偏好在 10SMA/20SMA/21EMA 上获得支撑的"干净图"

### 他的日更栏目(我们 watchlist 页的原型)

- **Today's Watchlist** —— 四类:`LL-HL 1st Pivot` / `LL-HL 2nd Pivot` / `LL-HL Trend Line Break` / `PP (Vol > 10D)`,**按 Hybrid RS 排序**
- **Weekly chart Watchlist** —— 周线版:`LL-HL 1st Break` / `2nd Break`
- **RS Radar** —— ETF 的 `Daily Rank Up/Down` + `Weekly Rank Up/Down`(这是他的"轮动")
- **Portfolio** —— 每日持仓明列

### 他的开源 TradingView 指标

| 指标 | 内容 |
|---|---|
| **Structure Pivot (LL-HL / HH-LH)** | 多长度同时扫描,自动画 pivot 线;跌破自动作废;默认 "Tightest Structure" 优先(压缩最紧 = R/R 最好) |
| **Relative Strength Table** | 最多 20 个标的对 SPY,回看 5/21/63/126 bar |
| Portfolio Management Spreadsheet | ATR 仓位表,**他自己写明是 Steve Jacobs 的 ATR Matrix 改版** |

---

## 三、@SteveDJacobs —— ATR Matrix 的完整定义

**ATR Matrix = 股价相对 SMA50 的距离,以 ATR 为单位。** 他学自 @jfsrevg 与 @RealSimpleAriel。

| 区间 | 含义 | 动作 |
|---|---|---|
| < 0 | 低于 SMA50 | **直接忽略** |
| **0–4x** | 建仓区 | 用任意入场战术(Darvas 突破 / PEG / U&R / VCP) |
| 5–7x | 获利持有 | 不动,除非跌破 MA10/MA20 |
| **≥7x** | 过度延伸 | 开始减仓:7x/8x/9x/10x/11x 各卖 20%,11x 清空 |

**配套规则:**
- 止损 = 成本下方 **1.5–2x ATR**,且 ≤ 平均盈利的 1/3
- **ATR% 带**:下限"高于平均"(当前约 **3%**),上限 = 最大可承受亏损 ÷ 1.5(例:止损 −9% → 上限 **6%**)。所以他在 **3%–6%** 之间选票
- 强烈建议 **Price ≥ MA20 ≥ MA50 ≥ MA100 ≥ MA200**,且价格在上升的 EMA10/SMA20/SMA50 之上
- 他的 **Qullamaggie Inspired Screener**:RS ≥ **97**(1W/1M/3M/6M 任一)· 上述均线序列 · ATR RS ≥ 50
- **开源指标**:`ATR multiple from 50 MA`(Jeff & @DumbleDax 作)—— **就是我们该移植的那一支**

他自述做了 20 年系统化/算法交易,不做主观单,每天用自研 Python 全市场分析。

---

## 四、@PrimeTrading_(Alex Desjardins)—— 漏斗与流动性

**四段漏斗**:UniverseList(约 **500** 只)→ WatchList(**10–100**)→ FocusList(**0–10**)→ 执行。

- **WatchList 技术闸**:价格在 200dma 之上 · 在 50dma 之上 · **20dma 在 50dma 之上**
- **Reversal pivot(他的原创定义)**:价格进入短期回调、日线开始走**低高点**;那段下降结构里的**最后一个日线高点**就是 reversal pivot;**收复它 = 结构翻转**
- **形态词典**:WB(楔形突破)· WBPB(楔破回踩)· BORS(突破回踩做空)· BORL(突破回踩做多)· BO10PB(突破后 10ema 回踩)· BO21PB(突破后 21ema 回踩)
- **离场**:止损 = 突破日最低(LOD);初段 +10–15% 卖一半;跌破 10DMA 卖 1/4;跌破 21DMA 清剩余
- **日更两张单**(工具是 @TradersLab_,付费):`Liquid Leaders Scan sorted by RS Rank`(约 20 只)· `Liquid Leaders 21dma-structure Pullback sorted by RS Rank`

> 他自己说:以前手工找 liquid leaders 要 2 小时,现在用 TradersLab 2 分钟。**这正是我们 screener 存在的理由**,只是我们的免费且可审计。

---

## 五、我们 vs 他们

### 我们更强的地方(五条,都不是嘴上说的)

1. **全池横截面 RS,口径可审计。** 他们的 RS 来自各自工具的黑盒;我们的 `rs_1m/3m/6m` 是在 2,557 只 tradeable 集内的百分位,`na_option='top'` 已修并有跨缺失率的属性测试。**08-12 那次事故证明这条链是可验证的 —— 他们的出了同样的错没人会发现。**
2. **主题/行业层。** 76 个主题带共动性验证、四态、色带、每日归档。四家**没有一家**有这个。oratnek 的 RS Radar(ETF 涨跌排名)是它的粗糙版。
3. **归档 = 我们说过的话。** `groups_archive.csv` 存的是当天发布的 state,不能事后重算。他们发完就散在时间线里。
4. **广度/环境层。** 15 条件分数、五档牌面、min-of-voters。四家都没有。
5. **零边际成本 + 可证伪。** TradersLab 是付费产品;我们的每个断言都能回到代码和测试。

### 我们缺的(七条,按可落地性排序)

| # | 缺什么 | 谁在用 | 难度 | 影响(2026-08-14 实算) |
|---|---|---|---|---|
| **1** | **ATR Matrix** `(close−SMA50)/ATR` | 三家都用 | **极低**(现有 `close/atr/sma50_dist` 直接算) | 全池 5,476 行可算:**41.2% 低于 SMA50(该忽略)· 49.6% 在 0–4x 建仓区 · 7.9% 4–7x · 1.3% ≥7x 过度延伸** |
| 2 | **PP 10 日窗** `pp_count_10d` | oratnek | 极低(改一个 lookback) | 他的 "PP (Vol > 10D)" 栏目直接可复现 |
| 3 | **均线序列布尔** `ma_stack` | Steve、Alex | 低 | Price≥EMA10≥SMA20≥SMA50≥SMA100≥SMA200 |
| 4 | **ADR 上限口径错** | Steve | 零(改预设) | 我们 8 个预设用 `adrPct max 10`;Steve 的上限是 **maxLoss÷1.5 ≈ 6**。10 会放进注定打穿止损的票 |
| 5 | **Stockbee anticipation 三扫描** | Stockbee | 低 | TI65 / Double Trouble / MDT,全是日线可算量 + 当日 ±1% |
| 6 | **Hybrid RS 排序退化** | oratnek | 中 | 我们的 `h_score` 里 `f_score` 恒 50(源头两列空),等于 2/10 权重是死的 |
| 7 | **结构识别(LL-HL / reversal pivot)** | oratnek、Alex | **高** | 他们体系的核心,我们完全没有。移植 `Structure Pivot` 是唯一路径 |

### 两家完整口径套到我们池子上

| 口径 | 今日命中 |
|---|---|
| **Steve**(ATR% 3–6% 且 ATR Matrix 0–4x) | **1,179 只** |
| **oratnek**(mcap>$1B · avgvol>1M · RS21>70 · RS63>80 · ATR-from-50SMA<5) | **134 只** — UMAC, AEHR, ALOY, APPS, SMCI, BLZE, FSLY, LPTH, REPL, BETA, IOVA, TNDM … |

oratnek 那 134 只是**今天就能出的一张单**,只差 ATR Matrix 这一个字段。

> **勘误(同日)**:本文首版的速算用了 `close×dist/atr`,漏了 `(1+dist)` 分母,把延伸度整体高估了 (1+dist) 倍 —— 30% 以上的票高估 30%,恰好是这个数存在要抓的那条尾巴。已按 `sma50_dist=(close−SMA50)/SMA50` 的口径(6 只逐位核对)修正,字段 `atr_from_sma50` 已上线并有回归测试钉住这个分母。

---

## 六、建议的动手顺序

1. **加 `atr_from_sma50`**(= ATR Matrix)。一行公式,配黄金样本对照 Jeff 的开源指标 `ATR multiple from 50 MA`。**这一步解锁上表 7 条里的 4 条**
2. **加 `pp_count_10d`** —— 改一个 lookback
3. **加 `ma_stack`** 布尔
4. **改预设的 adrPct 上限** 10 → 6(等 Andy 拍板)
5. 之后再谈 Stockbee 三扫描和结构识别

**未决(等 Andy)**:①要不要把 21EMA Watch 从"比值口径"改成"ATR Matrix 口径";②adrPct 上限;③要不要移植 `Structure Pivot`(工程量最大的一件)。
