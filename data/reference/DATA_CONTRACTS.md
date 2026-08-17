# 数据契约 —— 给 UI session 的交接

*2026-08-09 建,2026-08-10 更新。字段全部从活文件抽取,不是凭记忆写的。*
*生产者是 `pipeline/`,消费者是 `frontend/`。这份文档是两边之间唯一的约定。*

---

## 零、三条必须先读的规矩

**① 有些字段不是装饰,是许可证。**
下面标了 ⚠️ **必须渲染** 的字段,决定了页面有没有资格说那句话。
省掉它们,页面就会说出数据没说过的话。这不是设计偏好,是正确性。

**② 不可测 ≠ 零。**
`null` 一律表示「这一维我们算不出来」,永远不是「这一维是 0」。
UI 要把它画成空框、画在刻度之外,不能画成最低档。

**③ 契约变更走这份文档。**
数据端加字段不会通知你;这份文档更新了才算数。反过来,UI 需要新字段也写在这里再来找我。

---

## 一、`data/output/rotation.json` —— 风格轮动

**产出**:`pipeline/rotation/build_rotation.py`,每日 cron 最后一步
**当前消费方**:`frontend/src/components/breadth/RotationPanel.jsx`

### 顶层

| 字段 | 类型 | 含义 |
|---|---|---|
| `date` | str | 最后一根 K 线的日期。**不是运行日** —— 周末跑会是上周五 |
| `benchmark` | str | `"SPY"`。所有超额都是对它算的 |
| `step_sessions` | int | `10`,一格 = 10 个交易日 |
| `bucket_dates` | str[5] | 每格结束那天,由旧到新 |
| `bucket_labels` | str[5] | `["10–8w ago", …, "Last 2w"]` |
| `baskets` | obj[] | 见下 |
| `cuts` | obj[3] | 见下 |
| `verdict` | obj | 见下 |
| `state_windows` | obj | ⚠️ **必须渲染** |
| `coverage` | obj | `{baskets, of, missing[]}` |

### `verdict` —— 这是产品本身

| 字段 | 含义 |
|---|---|
| `sentence` | ⚠️ **整句直接显示,不要自己拼** 。文案逻辑在引擎里,UI 重拼必然走样 |
| `call` | `"risk_on"` / `"risk_off"` / `null`(切法互相矛盾时) |
| `agree` / `of` | 两周尺度上几票同意 / 共几票 |
| `month_call` / `month_agree` / `month_of` | 一个月尺度同上 |
| `phase` | `"established"`(两尺度一致 = 格局)· `"turning"`(两周翻了、月没翻)· `"split"` · `null` |

> **`phase` 是这个对象最贵的一位。** `turning` 和 `established` 在两周图上长得一模一样,
> 只有这一位能分开。**不显示 `phase` 等于把「刚翻」当成「已成格局」发出去。**

### `cuts[]` —— 三个切法,让那句话可被核对

`key` `label` `question` `long[]` `short[]` `spread`(两周) `month_spread`(一个月) `delta`(速度) `vote` `month_vote`

- 数值单位是**小数**(`0.0667` = +6.67pp),UI 自己乘 100
- `spread = 多头侧超额 − 空头侧超额`,同一窗口
- `delta` = 本两周 spread − 上两周 spread,**这是 RRG 给不出的「速度量级」**
- ⚠️ **`month_spread` 必须和 `spread` 并排显示。** 单独发两周读数,就是发我们自己测出会变号的那个窗口

### `baskets[]` —— 11 个风格篮子

`ticker` `name` `side`(`risk_on`/`risk_off`/`null`) `line`(float|null ×5) `ribbon`(obj ×5) 以及当日的 `state` `level` `accel`

- `line[k]` = 第 k 格那两周的对 SPY 超额,**不相交,不累计**
- `ribbon[k]` = `{state, level, accel}`,`state` ∈ Leading / Weakening / Improving / Lagging / `null`
- 四态配色必须和 `groups/StateBadge` 一致 —— 同样四个词在一个产品里不能有两套色板

### ⚠️ `state_windows` —— 必须渲染

```json
{"level_sessions": 63, "near_sessions": 21}
```

**色带的格子是两周宽,但格子里的态是 63/21 个交易日算出来的。**
两周宽的方块会诱导读者按两周去读,而两周窗口正是我们实测**半样本会变号**的那个
(`pipeline/themes/FOUR_STATE_DESIGN.md` 第六节)。

现在的做法是每格 hover 打出这句话。换个形式可以,**去掉不行**。

---

## 二、`data/output/breadth.json` → `regime` —— 环境分数

**产出**:`pipeline/screeners/regime.py`,由 `state_board.rows` 推出
**当前消费方**:无(UI 待接)

| 字段 | 含义 |
|---|---|
| `score` | 0–100,九维等权。`null` 表示整块不可测 |
| `band` / `band_label` | `damaged` / `mixed` / `healthy` / `extended` |
| `describes` | 该档描述的盘面 |
| `bands[]` | `{key,label,min,max,describes}` ×4,给 UI 画刻度 |
| `measured` / `of` | ⚠️ **必须显示**。8/9 和 6/9 不是同一个声明 |
| `strong[]` / `weak[]` | 满格 / 弱或缺的维度名 |
| `evidence` | 一句话说明这个分是怎么来的 |
| `predicts_return` | 恒为 `false` |
| `separates_tail` | 恒为 `true` |
| `caveat` | ⚠️ **必须显示** |

**档位边界 47 / 63 / 75 是 558 个交易日的经验四分位**,不是拍的整数。
所以「顶档」的意思是「我们真见过的最强那四分之一」。

### ⚠️ 为什么 caveat 是强制的

这个分数**对下个月均值收益无信息**(甚至轻微反向),**但对左尾单调**:
−5% 回撤频率从 Damaged 的 27.2% 单调降到 Extended 的 5.8%,两个半样本各自也单调。

两件事同时为真,方向相反,所以一个布尔值必然误报其中一个 —— 这就是拆成
`predicts_return` / `separates_tail` 两位的原因。

**它是仓位预算的输入,不是方向的输入。**
UI 若把它画成红绿灯,就是在替它做一个它明确做不到的声明。
另外:整个结论底下只有 **10 段独立回撤事件**,读作排序,别读作概率。

---

## 三、`data/output/groups.json` —— 主题与行业

**产出**:`pipeline/themes/build_groups.py`
**当前消费方**:`useGroups.js` → `GroupsPage.jsx`

顶层:`date` `benchmark` `universe_size` `industries[]` `themes[]` `themes_skipped` `audit` `stocks` `summary`

行字段:`group` `members` `tickers[]` `excess_3m` `rs_accel` `rs_accel_rate` `state` `persistence` `persistence_of` `perf_1d` `perf_1w/1m/3m/6m/1y`
`perf_1d`(2026-08-16 加):当日涨跌幅,小数口径,与 `perf_1w` 同族。聚合主题/行业 = 成员 `change_pct` 中位数(与其他 perf 列同一口径,异常值同样剔除);proxy 主题 = 该 ETF 自身的 `change_pct`;`stocks` 行 = 个股 `change_pct`。**不进 RS 桶、不进 persistence 分母**,只供显示。
主题另有:`method` `source` `publish` `measurable` `needs_manual` `validation` `validation_excess`

### 四条陷阱

**`rs_accel` 是门槛,`rs_accel_rate` 才是斜率 —— 「加速/减速」这两个词只能从后者来。**(2026-08-16 加,`stocks` 行同样带)
`rs_accel` = 最近 1 个月超额 − 前面 **2 个月合计**超额。窗口不等长是刻意的:一个匀速跑赢的组在这里是**负数**、被判 Weakening。
它是验证过的 Leading/Weakening 分界(等长版 V7 在四种切法上全面更弱,`FOUR_STATE_DESIGN.md` §8),**保留**。
但它的名字和它做的事不是一回事 —— 76 条主题里 9 条(12%)`rs_accel<0` 而 `rs_accel_rate≥0`,High Octane 就是:gate −0.17,rate +0.01,**匀速不是减速**。
`rs_accel_rate` 把前段几何折成月率再相减,匀速=0。
所以:`state` 徽章按 `rs_accel`;任何写着「decelerating / 减速 / slowing」的文案、以及「四强都在减速」这类汇总句,读 `rs_accel_rate` 的符号。
2026-08-14 的实话是「四强里三个在减速,High Octane 匀速」。

**`publish=false` 不能静默丢掉。** 它表示「这个主题没通过共动性验证」。
悄悄过滤会让「未验证」和「不存在」变成同一件事 —— `useGroups` 现在把它们分开返回,保持这个行为。

**`persistence` 必须连 `persistence_of` 一起显示。** 分母会变(组按同侪 5 个窗口,个股对基准 3 个)。
只印一个整数,等于把两把不同的尺子放进同一列。这个 bug 出过一次。

**`rs_accel` 是描述,不是信号。** 叠在 h_score 之上实测 −0.18pp,半样本一致。
`StateBadge` 的 hover 文案已经写了这句,别去掉。

---

## 四、`data/history/groups_archive.csv` —— 每日快照

**产出**:`build_groups.save()`,与 `groups.json` 同一次写入,不可分离
**消费方**:暂无。**这是为 10 周后的主题色带准备的**

每日 195 行(121 行业 + 74 主题,随分类学变动),按日期幂等替换。
列:`date` `kind`(`industry`/`theme`)`group` `members` `excess_3m` `rs_accel` `state` `persistence` `persistence_of` `perf_1w/1m/3m/6m` `rs_accel_rate` `perf_1d`(末两列,2026-08-14 起有值,更早的行为空)

**存的是当天发布的 `state`,不是原始 perf。** 事后重算会把今天的窗口常数套到昨天的数据上,
等于偷改我们说过的话。UI 要画历史色带,直接读这一列。

**起算日 2026-08-09。** 满 5 格需要 50 个交易日 —— 扣掉劳工节(2026-09-07),
落在 **2026-10-19(周一)**。

### ⚠️ 但主题色带不是「全有或全无」

`groups.json` 的主题行现在带 `ribbon` 字段,值是 5 个 `{state, level, accel}`,
**和 `rotation.json` 里 baskets[].ribbon 完全同一种对象、同一套窗口**,可以共用组件。

| 主题类型 | 数量 | `ribbon` | 为什么 |
|---|---|---|---|
| `method="proxy"` | **16** | ✅ **现在就有** | 成员是一只 ETF,历史是基金自己的价格序列,任意过去窗口今天就能算 |
| `etf` / `industry` / `rule` | 58 | `null` 到 2026-10-19 | 读数是「某一刻对一组股票取中位数」,不写下来就没有;归档从 2026-08-09 才开始 |

**前端不需要为此写分支。** `null` 段照 `StateRibbon` 既有行为画虚线空框,
到 10 月归档满了,那 58 行自己就有值了 —— 契约不变,不用改代码。

**倒推补不了。** 就算把 3000 只成分股的日线全抓来也不行:成分名单本身在变,
而我们没存过它的历史(今天就删了 7 个主题、给 Quantum Computing 加了 IBM、
把市值地板从 3 亿抬到 10 亿)。拿今天的名单去套 6 月的价格,
算的是「今天这批票当时的表现」,不是「当时这个主题的状态」——
带后见之明的数,比没有数更糟。

---

## 四点五、`data/output/universe.json` —— 2026-08-17 新增两列

| 字段 | 定义 | 口径 |
|---|---|---|
| `atr_from_sma50` | **ATR Matrix** = `(close − SMA50) / ATR`,股价高于 50 日线几个 ATR | 浮点 4 位小数,可负(低于 SMA50);ATR ≤ 0 / **ATR < 0.5% 价格**(实测该线以下全是 $10 SPAC 壳与并购锁价票)/ `1+dist ≤ 0` / 缺任一输入 → `null`,**永不 inf**。**不是** `sma50_r`(那是 close/SMA50 的比值,原样保留)。黄金样本:6 只对 Wilder-14 ATR 直算逐位吻合。**与每个 ticker 徽章上的 `atr_ext`、ETF 行的 `dist_sma50_atr` 同一实现**(`atr_enrichment.atr_multiple_from_sma50` / `_from_levels`)。`≥7` 尾巴含近期跳空后钉价的并购标的(Wilder-14 记得跳空日),读榜时配 industry/量 |
| `pp_count_10d` | 最近 10 个交易日里的口袋支点根数 | 与 `pp_count_30d` 同一实现(`pocket_pivot_count`)、不同 lookback;阳线且量 > 前 10 根最大量(NaN 量的根跳过);**历史 < 11 根 → `null`(未测量,不是 0)**,`pp_count_30d` 与当日 `pocket_pivot` 标志同步改为此语义(三者同一实现);首次富集后才有值 |

| `ema21_atr_dist` | `(close − EMA21) / ATR`,离 21 日 EMA 几个 ATR(2026-08-17 加) | 与 `atr_from_sma50` **同一 helper、同一 0.5% 地板、同一 null 规则**;EMA21 = 收盘价 span-21 EMA(富集新导出 `ema21` 列);fallback 池无 EMA21 → null |
| `ema21` | 收盘价 EMA21 水平 | 富集导出;供上面那列和以后的图用 |

⚠️ **21EMA Watch 预设改为 ATR 口径 —— 需要前端改一处映射(Andy 2026-08-17 拍板)**:`frontend/src/lib/screenerFilter.js` 里 `ema21Atr → ema21_r`、`sma50Atr → sma50_r` 改成 **`ema21Atr → ema21_atr_dist`、`sma50Atr → atr_from_sma50`**。预设里的数值(−0.5..1、0..3)本来就是 ATR 语义,不用动;`ema21_r`/`sma50_r` 两个比值列原样保留不删。实测 08-14:比值口径命中 13 只(全在 SMA20 下),ATR 口径 53 只。

⚠️ **三个 97 定名(Andy 2026-08-17)**:预设 `97 Club` → **`Monthly Leader 97`**、`Momentum 97` → **`Weekly Momentum 97`**(已改 `screener-presets.json`,名字无代码引用);Python 筛选器 `momentum_97` 的**显示名**改为 **`Composite 97`** —— 在 `frontend/src/lib/scanSets.js:18` 和 `frontend/src/components/ticker/TickerSignalHistory.jsx:40` 两处,**前端改**;文件名 / 键 `momentum_97` 不动。含义:月度领头(月 RS ≥97 + 综合 ≥80)/ 本周冲刺(周分位 ≥.97 且季 ≥.85)/ 四窗口等权综合前 3%。

⚠️ **adrPct 分两档 + 热度着色(Andy 2026-08-17 拍板)**:持仓型预设(21EMA Watch / Pocket Pivot / PP Count / 97 Club)`adrPct.max` 10→**6**(= 最大单笔亏损 ÷ 1.5,Steve 的算法,和 −7~−9% 止损档对齐);扫描型(4% Bullish / Vol Up / Momentum 97 / Weekly 20%+)保留 10。已改 `frontend/public/data/screener-presets.json`。**前端**:表里 `adr_pct` 列按热度着色,越高越热,>6 明显可辨(6 是"超出止损承受"的线);字段现成,不需要数据端改动。08-14 数据:$1B+ 非医疗 2,224 只里 ADR 3.5–6 有 820 只、6–10 有 253 只(半导体/软件/航空防务最多)。

| `ti65` / `mdt` / `c_low52w` / `min_vol_3d` | Stockbee anticipation 三扫描的输入(2026-08-17 加):`avgc7/avgc65`(TI65 >1.05)· `c/avgc126`(MDT >1.19)· `c/minl252`(Double Trouble ≥1.8,= 1 + `low_52w`,因为 `low_52w` 存的是分数距离不是价格)· 近 3 日最低量(>100k) | 前两个需 65/126 根历史否则 null;`c_low52w` 现在就有。**方法与组合见 `screener_methods.md` 第四节**;名单工具 `python -m pipeline.tools.anticipation_scan` |

⚠️ **`data/history/ticker_events.csv` 的 `atr_ext` 列在 2026-08-17 前后是两个定义**:2026-08-17 之前的 62,692 个非空值是旧式 `|dist|×close/atr`(无符号、无 `(1+dist)`),之后是有符号的 ATR Matrix。归档没存 `close/atr/dist`,**旧行无法重算**。跨日期比较该列时以 `date < 2026-08-17` 为界;目前没有消费方跨日期读它(Signal History 只按日取)。

⚠️ **`atr_ext`(每个 ticker 徽章)口径变更 2026-08-17**:原来是 `|dist|×close/atr`(无符号、漏 `(1+dist)`),现在 = `atr_from_sma50`(有符号)。**低于 SMA50 的票现在是负数**,`atr_color` 多了一档 `"below"`。前端 `lib/format.js:atrBadgeColor` 目前把 `<0` 走进 `≤4` 的绿色分支 —— **需要前端加一行 `if (atrExt < 0) return <中性色>`**,否则 2,247 只线下票继续被涂成入场区绿。这是数据端修正后剩给 UI 的唯一一步。

### `sp_*` —— Structure Pivot(oratnek Advanced Structure Pivot 移植,2026-08-17 加,下次 cron 起有值)

引擎 `pipeline/screeners/structure_pivot.py`,源码 `indicators/third_party/oratnek_advanced_structure_pivot.pine`;**黄金对照 5/5**(AEHR/SMCI/CRWD/NVDA/PLTR,08-14 日线,结构/长度/索引/阶段/信号全同,价位差 ≤0.013 且全部溯源到 bar 数据的 sub-penny 精度),回归夹具在 `pipeline/tests/fixtures/`。

| 字段 | 含义 | 空值语义 |
|---|---|---|
| `sp_setup` | 当前是否有活的 LL-HL 结构 | `null` = 历史 <30 根未测量;`false` = 无结构 |
| `sp_len` | 胜出的检测长度(2–5,Tightest 优先) | 无结构 → null |
| `sp_ll` / `sp_hl` | 低低点 / 高低点价 | 无结构时 `sp_hl` 仍可能有值(最近一个 pivot 或跟踪中的最低 low)—— **只在 `sp_setup` 为 true 时把它当 HL 读** |
| `sp_1st` / `sp_2nd` / `sp_tp1` / `sp_tp2` | Fib 0.618 / 1.0 / 1.764 / 2.618 位 | 无结构 → null |
| `sp_phase` | 1 = 止损跟 MA · 2 = 止损固定 1st(high 触过 2nd) · 3 = max(1st, MA)(high 触过 TP1) | 无结构 → null |
| `sp_stop` / `sp_ma` | 当前阶段的止损 / 21EMA(low) | `sp_ma` 无结构也有 |
| `sp_signal` | 当日**收盘**信号(互斥):`1st_break` `2nd_break` `tp1_hit` `tp2_hit` `stop_hit` `ll_break` `counter_break` | 无 → null |
| `sp_days` | 结构画出以来的交易日数(0 = 今天新出) | |
| `sp_dist_1st_pct` / `sp_dist_2nd_pct` | 1st / 2nd 相对收盘的 % 距离(负 = 已在其上) | |
| `sp_counter` | 无结构期的逆势趋势线在今天的价位 | 有结构 → null |

**读法(oratnek 原话)**:1st 建半仓、止损 21EMA Low;5 根内须到 2nd,到了加仓、止损上移到 1st;+25% 优先落袋,否则 R:R 3 或 ATR-from-50SMA ≥7 减 33%;收盘跌破 21EMA Low 清。他的 Today's Watchlist 四栏 = `sp_signal ∈ {1st_break, 2nd_break, counter_break}` + `pp_count_10d ≥ 1`。
**口径提醒**:①富集用复权日线,与 TV 未复权图相比价位差在分红调整量级(NVDA MA 210.3487 vs 210.3508);②描述说"收盘",代码用 high(升阶)/ low(作废),移植照代码;③他自己的 "ATR% 50SMA" 列是 `dist·close/atr`(漏 `(1+dist)`),他的 `<5` 门槛换算到我们的 `atr_from_sma50` 要除以 `(1+dist)`。

⚠️ **`vcs` 换尺 2026-08-17(下一次 cron 起生效)**:原来是改造过的老版 VCS(min(13,3) 标准差、Kaufman-ER 质量项、.3/.3/.2/.2 权重、无效率过滤,无测试无黄金对照);现在是 **oratnek VCS v2 的忠实移植**(`pipeline/screeners/vcs.py`,源码 `indicators/third_party/oratnek_vcs_v2.pine`):.4/.4/.2 权重 × 效率过滤,EMA3 平滑,连续紧缩加分 ≤15,低点跌破 ×0.75;<76 根 → `null`。**新尺明显更严**:134 只本地样本上中位 50.5 → 35.1,≥70 的占比 11.9% → 7.5%。作者的读法:80+ 临界压缩、60–80 发展中、<60 扩张。`filters.vcs` 的阈值和任何存了旧 vcs 的历史都要按这个日期分界。黄金对照:`indicators/third_party/oratnek_vcs_probe.pine` ↔ `python -m pipeline.tools.vcs_probe`。

Steve Jacobs 的读法:`<0` 忽略 · `0–4` 建仓区 · `5–7` 持有 · `≥7` 分批减;oratnek:选股 `<5`(理想 `<4`),`≥7` 减 33%。出处 `data/research/screener_competitors_2026-08-17.md`。

---

## 四点七、`data/output/watchlist.json` —— 晨报(2026-08-17 加,首份由今晚 cron 产出)

**产出**:`pipeline/screeners/watchlist.py`,run_all 里 groups 之后、rotation 之前;纯函数吃 universe.json,自己的失败域
**当前消费方**:无(Watchlist 页待接)。**这份文件是 Watchlist 页与 Screener 页分工的落点**:Screener = 工作台(全池 + 30 个筛选键 + 可编辑预设);Watchlist = 晨报(每晚算好、按问题分区、只读)。方法见 `screener_methods.md`,分工讨论见 2026-08-17 对话。

```
{ date, gate:{min_market_cap:1e9, min_avg_volume:1e6}, sort, cross_zone_rule, universe_gated,
  zones:[ { key, label, panels:[ { key, label, recipe, measured, count, truncated, preset,
                                    tickers:[ {ticker, rs_1m, hybrid_rs, sector} ] } ] } ],
  cross_zone:[ {ticker, count, zones:[...], rs_1m, hybrid_rs, sector} ] }
```

| 区 `zones[].key` | 问题 | 格 `panels[].key` |
|---|---|---|
| `entries` | 今天可以进的 | `ll_hl_1st` `ll_hl_2nd` `ll_hl_trend_break`(读 `sp_signal`) |
| `compression` | 在蓄势的 | `vcs`(vcs≥70 且 ADR≥3)`anticipation`(强弱三选一 × 安静 × VCS≥60 × ADR≥3) |
| `accumulation` | 有人在买的 | `pp_today`(当日 PP)`pp_2plus_10d` |
| `moving` | 在跑的 | `weekly_momentum_97` `bullish_4pct` `weekly_20_gainers` —— **与同名预设同一配方,测试锁死**;`preset` 字段给出预设名,前端可点进 Screener 载入 |
| `trouble` | 出问题的(持仓视角) | `stop_hit` `ll_break`(读 `sp_signal`)`extended`(ATR Matrix ≥7) |

规则:
- **门槛**固定 $1B + 1M 均量(oratnek 的前提),`universe_gated` 是过门槛的只数;Screener 页不受此约束
- 每格最多 25 只,`truncated` = 被截掉的数;排序 **Hybrid RS 降序**,票旁数字是 **RS 1M**(oratnek 的做法,保留)
- ⚠️ **`measured=false` 必须渲染成"未测量"**(空框 / 灰),不能画成 0 —— 首晚 `sp_*` 未出时三个结构格就是这个状态
- **`cross_zone` 数的是"区"不是"格"**:一只票在 moving 区三个格都出现只算 1;≥2 区才列。这是对 oratnek "Tickers in 3+ watchlists" 的修正 —— 他那栏统计的多半是同义词。前端把它放顶部,替代原来的"出现在 N 张单"
- 配方文字在 `recipe`,直接显示(和 rotation 的 `sentence` 同一原则:文案在引擎里,UI 不重拼)
- 前端通路(待 UI):格标题 → Screener 载入 `preset`;票 → ticker 页(Signal History 里能看它昨天在哪几格);Screener 里用户自建的预设**不进**晨报

首跑(08-14 数据,结构格待 cron):VCS 62 · anticipation 0(ti65/mdt 待 cron)· PP 今日 20 · PP 2+ 183 · Weekly Momentum 97 8 · 4% Bullish 23 · Weekly 20%+ 22 · Extended 16;cross_zone ≥2 共 27 只(NIQ / P / INFQ 三区)。

---

## 五、当前未接入的东西

| 文件 | 状态 |
|---|---|
| `data/output/sentiment.json` | 5 项价格序列已自动化;AAII / NAAIM 走手工录入,**从未录过**。前端无消费方 |
| `data/output/baskets/*.json` | 共享日线仓库(27 只 ETF:轮动 12 ∪ proxy 主题 16),中间产物,UI 不该直接读 |

---

## 六、已知的失败形态

| 现象 | 原因 | 谁负责 |
|---|---|---|
| `rotation.json` 日期不动 | cron 的 rotation 步骤挂了 —— **会让整个构建失败并发 Discord 告警** | 数据端 |
| `groups.json` 里主题变少 | 共动性验证没过,`publish=false` | 数据端(预期行为) |
| 色带某格是虚线空框 | 那一格算不出态(历史不够或数据缺) | UI 照常画空框,**不要填色** |
| `regime.score` 为 `null` | 九维全不可测 | UI 显示「不可测」,**不要显示 0** |
