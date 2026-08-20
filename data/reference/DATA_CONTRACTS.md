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
主题与行业行另有(2026-08-17 加):**`ext_share_4` `ext_share_7` `ext_median` `ext_n`** —— 成员里 `atr_from_sma50` ≥4 / ≥7 的占比、中位数、可测成员数(缺 ATR 的成员不计)。**读法:Leading 标签的到期预警,不是收益预测** —— 48 主题 × 293 日实测,Leading 主题日里 ≥4 占比 <20% → 21 日后仍 Leading 28%,20–40% → 14%,40–60% → 6%,>60% → 0%(单调),但那 21 日的超额中位**没有**变差(+1.6% → +2.5~3.8%)。原因是 `rs_accel` 门槛在两个月大涨后机械翻负。UI 若显示,文案是"标签快到期 · 中期减仓预警":高延伸主题 21 日仍强、**42–63 日转负**(Leading→Weakening 且进入前 ≥4 占比 >40%:21 日 +3.1%,63 日 −4.1%,n=31)—— 不是"现在卖",是"别在延伸段加、一两个月内收一部分"。**Weakening 本身不是"歇一歇再跑"**:四态里 Weakening 的前瞻超额零到负,只有 Leading vs Lagging 这一对稳(FOUR_STATE_DESIGN §6/§9)。Steve 的 ≥7 阶梯是**个股**规则,主题层面这个数说的是"这波已经涨在价格里"。

### `kind` —— 每个主题是什么(2026-08-18 加,今晚 cron 起 groups.json 每个 theme 项都带)

`kind ∈ {theme, sector, factor, proxy}`:`theme` 有共同产业驱动的业务主题(30)· `sector` Finviz 行业联合、驱动是宏观(利率/油价;20:Software / Regional Banks / Oil & Gas / Financials / Industrials / Real Estate / Energy / Insurance / Utilities / Travel & Leisure / Consumer Retail / Chemicals / Transportation / Banks-MC / Electronic Components / IT Services / Agribusiness / Beverages / Household / Tobacco)· `factor` 按属性定义的规则主题(8:Growth / Value / High Beta / Small Caps / Mega Caps / IPOs / High Octane / 52W Leaders)· `proxy` 基金即标的(16)。**Andy 08-18:Small Caps 这类不是"主题"是因子,分类没错,但别和业务主题混一栏**——前端按 `kind` 分组摆,一个都不删。名单在 `taxonomy.SECTOR_NAMES` / `kind_of()`;审计依据 `data/reference/theme_audit_2026-08-18.md`。

### 成员改动 2026-08-18(Andy:"按 TSF 改";今晚 cron 起 groups.json 生效,本地已重建)

依据 `data/reference/theme_audit_2026-08-18.md` + TSF 全 47 主题名单(`data/reference/tsf_themes_2026-08-18/`)。**11 个主题整体换成 TSF 名单 ∩ 我们池子**(每处 taxonomy note 记来源):AI - Datacenters(机房/托管/REIT/转型矿工,25)· AI Power & Infrastructure(设备+电网承包+IPP+核电,88;不再是公用事业)· Robotics & Automation(49,整换)· Uranium & Nuclear Energy(31,TSF 50 去掉 11 只监管公用事业)· Space(17,含 SPCX)· Steel(17,铝出去)· Cybersecurity(31,AVGO/CSCO 出去)· Fintech(72,交易所/评级出去)· Rare Earth Metals(**只剩 3 只过门,暂 publish=false**)· Agribusiness(34,CAT/PCAR 出去)· Homebuilders(61,照 TSF 含 TT/JCI/CARR;数据端保留意见记在 note)。**7 个主题追加 TSF 有我们没有的**:Lithium(+33 含 EV 车厂)· Copper(+5 含 BHP/RIO/VALE)· Drones(+16 含 eVTOL)· Crypto(+13 含 HOOD/XYZ/CRCL)· Memory & Storage(+9)· Semiconductors Broad(+31)· Silver(+20 含 HL)。板块桶不动。**同日追加(Andy:"要的")**:新主题 **Physical AI & Humanoid Robotics**(26,theme)· **Cloud Software**(79,theme)· **Consumer Staples**(102,sector);**Optics & Networking Equipment** 并入 TSF 'Telecom, Optics & Connectivity' 的 64 只(含 CRDO MRVL COHR FN AVGO ANET 和运营商)。主题总数 75 → 79 → **删 6 个(Andy:"不要":Broad AI Theme / Speculative Tech / Grid & Electrification / Reshoring / IT Services / Electronic Components)→ 73**;Rare Earth 单独降门槛($200M / $1M,`Theme.floor`)并 `publish_override`(验证面板里只有 3 只,`validation` 字段照实写 'too few in panel')。再改(Andy 同晚):**16 个 proxy 主题全部删除**(Biotech/Healthcare/China Tech/IBD 50/RSP/Gold/Silver/Bitcoin/TLT/India/Japan/Korea/Taiwan/Brazil/Europe/EM),**Banks - Money Center 删除**,Quantum Computing `publish_override` 发布。**最终 56 个主题、全部发布**:theme 30 / sector 18 / factor 8;`kind` 不再有 `proxy` 值。**前端**:成员数和四态会跳,是换名单不是坏了;`kind` 字段不变。

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

⚠️ **2026-08-18 分界**:这天 11 个主题整体换了名单、7 个大幅追加、3 个新建、22 个删除(proxy/Broad AI 等),归档按**主题名**存,所以 `groups_archive.csv` 里 08-18 之前的 AI - Datacenters / AI Power / Robotics / Uranium / Space / Steel / Cybersecurity / Fintech / Rare Earth / Agribusiness / Homebuilders 行描述的是**旧成员**;`persistence` 是跨这条线数的,这些主题的连续天数要到 09 月才干净。新主题(Physical AI / Cloud Software / Consumer Staples)从 08-18 起有行。

**产出**:`build_groups.save()`,与 `groups.json` 同一次写入,不可分离
**消费方**:暂无。**这是为 10 周后的主题色带准备的**

每日 195 行(121 行业 + 74 主题,随分类学变动),按日期幂等替换。
列:`date` `kind`(`industry`/`theme`)`group` `members` `excess_3m` `rs_accel` `state` `persistence` `persistence_of` `perf_1w/1m/3m/6m` `rs_accel_rate` `perf_1d` `ext_share_4` `ext_share_7` `ext_median`(末五列分别 2026-08-14 / 08-17 起有值,更早的行为空)

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
| `pocket_pivot` / `pp_count_10d` / `pp_count_30d` | **⚠️ 2026-08-17 起 = Morales/Kacher 原定义**:上涨日(close > 昨收)且量 > 前 10 根**下跌日**的最大量(买盘 vs 卖盘;前 10 根无下跌日 → 不算)。审计(`accumulation_audit.md`)测得它与 A/D 量比相关 +0.71,旧式 +0.52,两者 Top10 只重 3 只 —— 是不同的量 | 之前的"全部 K 线最大量"版本改名 `vol10_green`(见下);预设 Pocket Pivot / PP Count 继续读这一族(= Morales) |
| `vol10_green` / `vol10_green_count_10d` / `vol10_green_count_30d` | oratnek 的 "PP (Vol > 10D)":阳线(close > open)且量 > 前 10 根**全部**的最大量 —— 量能突增事件。**就是 08-17 前的 `pocket_pivot` 算法**,换名不换数 | 晨报 accumulation 区两格读它;历史 `pp_count_*` 值(08-17 前)对应的是这一族 |
| `ad_ratio_20` / `cmf21` | 审计判定真正缺的"吸筹因子":近 20 日**上涨日成交量占总量之比**(0.5 = 平衡)· Chaikin Money Flow 21(−1..1) | 需 21 根;两条不重复(A/D 量比与 OBV 斜率 +0.93 近重复,故不做 OBV) |
| ~~`pp_count_10d`~~(旧行) | 最近 10 个交易日里的口袋支点根数 | 与 `pp_count_30d` 同一实现(`pocket_pivot_count`)、不同 lookback;阳线且量 > 前 10 根最大量(NaN 量的根跳过);**历史 < 11 根 → `null`(未测量,不是 0)**,`pp_count_30d` 与当日 `pocket_pivot` 标志同步改为此语义(三者同一实现);首次富集后才有值 |

| `ema21_atr_dist` | `(close − EMA21) / ATR`,离 21 日 EMA 几个 ATR(2026-08-17 加) | 与 `atr_from_sma50` **同一 helper、同一 0.5% 地板、同一 null 规则**;EMA21 = 收盘价 span-21 EMA(富集新导出 `ema21` 列);fallback 池无 EMA21 → null |
| `ema21` | 收盘价 EMA21 水平 | 富集导出;供上面那列和以后的图用 |

⚠️ **21EMA Watch 预设改为 ATR 口径 —— 需要前端改一处映射(Andy 2026-08-17 拍板)**:`frontend/src/lib/screenerFilter.js` 里 `ema21Atr → ema21_r`、`sma50Atr → sma50_r` 改成 **`ema21Atr → ema21_atr_dist`、`sma50Atr → atr_from_sma50`**。预设里的数值(−0.5..1、0..3)本来就是 ATR 语义,不用动;`ema21_r`/`sma50_r` 两个比值列原样保留不删。实测 08-14:比值口径命中 13 只(全在 SMA20 下),ATR 口径 53 只。

⚠️ **三个 97 定名(Andy 2026-08-17)**:预设 `97 Club` → **`Monthly Leader 97`**、`Momentum 97` → **`Weekly Momentum 97`**(已改 `screener-presets.json`,名字无代码引用);Python 筛选器 `momentum_97` 的**显示名**改为 **`Composite 97`** —— 在 `frontend/src/lib/scanSets.js:18` 和 `frontend/src/components/ticker/TickerSignalHistory.jsx:40` 两处,**前端改**;文件名 / 键 `momentum_97` 不动。含义:月度领头(月 RS ≥97 + 综合 ≥80)/ 本周冲刺(周分位 ≥.97 且季 ≥.85)/ 四窗口等权综合前 3%。

⚠️ **adrPct 分两档 + 热度着色(Andy 2026-08-17 拍板)**:持仓型预设(21EMA Watch / Pocket Pivot / PP Count / 97 Club)`adrPct.max` 10→**6**(= 最大单笔亏损 ÷ 1.5,Steve 的算法,和 −7~−9% 止损档对齐);扫描型(4% Bullish / Vol Up / Momentum 97 / Weekly 20%+)保留 10。已改 `frontend/public/data/screener-presets.json`。**前端**:表里 `adr_pct` 列按热度着色,越高越热,>6 明显可辨(6 是"超出止损承受"的线);字段现成,不需要数据端改动。08-14 数据:$1B+ 非医疗 2,224 只里 ADR 3.5–6 有 820 只、6–10 有 253 只(半导体/软件/航空防务最多)。

| `ti65` / `mdt` / `c_low52w` / `min_vol_3d` | Stockbee anticipation 三扫描的输入(2026-08-17 加):`avgc7/avgc65`(TI65 >1.05)· `c/avgc126`(MDT >1.19)· `c/minl252`(Double Trouble ≥1.8,= 1 + `low_52w`,因为 `low_52w` 存的是分数距离不是价格)· 近 3 日最低量(>100k) | 前两个需 65/126 根历史否则 null;`c_low52w` 现在就有。**方法与组合见 `screener_methods.md` 第四节**;名单工具 `python -m pipeline.tools.anticipation_scan` |

⚠️ **`data/history/ticker_events.csv` 的 `atr_ext` 列在 2026-08-17 前后是两个定义**:2026-08-17 之前的 62,692 个非空值是旧式 `|dist|×close/atr`(无符号、无 `(1+dist)`),之后是有符号的 ATR Matrix。归档没存 `close/atr/dist`,**旧行无法重算**。跨日期比较该列时以 `date < 2026-08-17` 为界;目前没有消费方跨日期读它(Signal History 只按日取)。

⚠️ **`atr_ext`(每个 ticker 徽章)口径变更 2026-08-17**:原来是 `|dist|×close/atr`(无符号、漏 `(1+dist)`),现在 = `atr_from_sma50`(有符号)。**低于 SMA50 的票现在是负数**,`atr_color` 多了一档 `"below"`。前端 `lib/format.js:atrBadgeColor` 目前把 `<0` 走进 `≤4` 的绿色分支 —— **需要前端加一行 `if (atrExt < 0) return <中性色>`**,否则 2,247 只线下票继续被涂成入场区绿。这是数据端修正后剩给 UI 的唯一一步。

⚠️ **RS/H 分「全部打分」2026-08-17(Andy:"全部打分";下一次 cron 起生效)**:`rs_1m/3m/6m`(及旧名 `rs_21d/63d/126d`)、`rs_ibd`、`i_score`、`h_score`、`f_score` **对每一行都有值**,不再只给 tradeable 行 —— 08-14 数据上覆盖率从 45% 升到 94–99%。**尺子没变**:场仍是 tradeable 子集(市值 ≥$1B 且日成交额 ≥$2M),tradeable 行的分数逐位不变;非 tradeable 行读的是"它的 perf 落在 tradeable 分布的第几分位"(RS 90 一律 = 会跑赢 90% 的可交易场)。`tradeable` 列照旧输出,**前端想标灰/淡化非 tradeable 行请读它**,不要再用 `rs_* == null` 当替身。perf 缺失的非 tradeable 行仍 `null`。`liquid_leader` 定义里加了 `tradeable`,名单未变(174)。测试 `test_score_all_rows.py` / `test_tradeable_scoring.py`。非 tradeable 行 rs_3m 中位 26(小票落后于场,不是 bug)。

| `bar_date` / `bars_stale` / `bar_scale_mismatch` | 2026-08-17 加:富集用的 yfinance 日线**最新一根的日期** / 该日期早于本次 run 标定的交易日(`marketcal.last_completed_session`)/ yfinance 收盘价与 Finviz 收盘价相差 >20%(复权或代码错配) | stale 的票单独重抓一次;仍 stale 或 scale_mismatch 的行,**所有由 K 线派生的列都置 null**(atr_from_sma50、ema21_atr_dist、sp_*、vcs、pp/vol10、ti65/mdt、ad_ratio/cmf 等),只留这三个标记 —— 宁缺勿旧。前端可把 `bars_stale=true` 渲染成"数据滞后"。 |

⚠️ **quality 守卫的"按设计稀疏"白名单 2026-08-17**:`sp_signal` `sp_counter` `sp_1st/2nd/tp1/tp2` `sp_phase` `sp_stop` `sp_days` `sp_dist_*` `sp_ll/hl` `sp_len` 这些字段本来就是大多数行为 null(无结构 = null 是语义),`quality.py` 现在只在它们**全空**(≥99.9%)且此前不是全空时才报 severe,否则 `ok`,不再因为"空值率高"把 universe 打成 degraded。名单在 `pipeline/quality.py: SPARSE_BY_DESIGN`。

⚠️ **F 分换源 2026-08-17(Andy:"换源,容纳后 finviz 当 backup";今晚 cron 起生效)**:`eps_growth_next_y` / `revenue_growth` / `eps_growth_this_y` 由 **yfinance `Ticker.info` 主供**(`forwardEps/trailingEps − 1`,仅 trailing>0;`revenueGrowth` 同比季度;`earningsGrowth`),Finviz 自己的列(Elite CSV 才有)**只补 yfinance 没有的洞**。单票 0.9 s 且 Yahoo 约 1,100 次后限速,所以是**滚动刷新的本地库** `data/reference/fundamentals.json`(每晚刷最旧的 700 只 ≈ 96 s,一周一轮;撞墙提前停、受害者不记账;首次种库 08-17 本地跑)。新列 `fund_source`(`yfinance` / `finviz` / null)、`fund_asof`(读数日期)。**注意口径**:Finviz 那列叫 "Sales past 5Y"(五年 CAGR),现在的 `revenue_growth` 是**同比一季**;名字没改因为 f_score 读它。覆盖率(种满后估计):营收 ~80%、EPS ~45%(亏损股无增长率,与 Finviz 一致)。
**`f_score` 公式同日改**:两项**各自**在 tradeable 尺子上排名后**平均名次**(原来平均原始增长率,`forward/trailing` 在 trailing 近零时爆到 19× 会压死营收项);只有一项用那一项;**两项都缺 = 50(未知,不是最差)**——原 `na_option='top'` 把未知全塞到最低名次,在覆盖率不满时会把已知票挤到 83–99 那 16 个点。`h_score` 里 F 的 2/10 权重从此是活的;H 分排名会动,是预期。测试 `test_score_all_rows.py::TestFScore`。

| `rs_line_pctl_21` | **oratnek 的 "RS 1M" 破译**(2026-08-18,今晚 cron 起有值):今天的 RS 线(收盘 / SPY 收盘)在**自己**最近 21 个交易日里的百分位 = `count(RS_i ≤ RS_today)/21 × 100`。**时间序列自比**,不是横截面 —— 100 = 相对 SPY 的强度处于一个月新高。他 08-17 页面上 8 个取值全是 k/21,此定义 **29/29 逐一复现**(夹具 `pipeline/tests/fixtures/oratnek_rs1m_*`,测试 `test_rs_line_pctl.py`) | 与 `rs_1m` **不是一个量**:RELY 同日他 100 / 我们 68 都对,一个说"相对强度在自己的月内新高",一个说"月收益跑赢 68% 的可交易场"。watchlist.json 每只票项也带 `rs_line_pctl_21`,前端可选印哪个(印他的那个就跟他页面对得上)。< 21 根 → null |

| `perf_5d` | 最近 **5 个交易日**收益(bar 直算,close/close[-5]−1),2026-08-18 加 | 与 Finviz 的 `perf_1w`(日历周)不同:08-14 周五那天 `perf_1w` 只含 4 根(FSLY 7.9% vs 5 根 30.4%)。oratnek 的 "Weekly 20%+" 读的是周 K = 5 根。晨报 `weekly_20_gainers` 格 08-18 起读 `perf_5d`;Screener 预设 "Weekly 20%+ Gainers" 仍读 `perf_1w`(前端若要对齐,加一个 `perf5d` 筛选键指到本列即可) |

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
{ date, gate:{min_market_cap:1e9, min_dollar_volume:2e7}, sort, cross_zone_rule, universe_gated,
  zones:[ { key, label, panels:[ { key, label, recipe, measured, count, truncated, preset,
                                    tickers:[ {ticker, rs_1m, hybrid_rs, sector} ] } ] } ],
  cross_zone:[ {ticker, count, zones:[...], rs_1m, hybrid_rs, sector} ] }
  # 票项 08-18/19 起还带:rs_line_pctl_21, rs_high, top_3m, chg_pct, chase, atr_from_sma50;格还带 count_rs_high, count_top_3m, count_chase
```

| 区 `zones[].key` | 问题 | 格 `panels[].key` |
|---|---|---|
| `leaders`(08-17 加,排第一) | 谁在领跑 | `true_market_leaders`(liquid_leader × 所属组四态 Leading × rs_1m≥80;票项多 `group` `group_state`)`liquid_leaders`(教材 M2_L09:ADV≥2M · >SMA50 · rs_3m≥80;count 是全表,tickers 取前 25) |
| `entries` | 今天可以进的 | `ll_hl_1st` `ll_hl_2nd` `ll_hl_trend_break`(读 `sp_signal`)`liquid_leader_pullback`(教材 L09:liquid_leader · 周涨<12% · 离 21EMA 0.5–1 ATR · 离 50 0–3 ATR) |
| `compression` | 在蓄势的 | `vcs`(**08-18 改**:vcs≥60 且 rs_3m≥80 且站上 SMA50 且 ADR≥3 —— 领头里的压缩;单靠 vcs≥70 08-14 有 33 只、一半弱势,oratnek 同日只列 2 只且都 rs_3m≥88;新配方闸内 10 只、含他的 COTY;CBRL 被 1M 股闸拦在外面)`anticipation`(强弱三选一 × 安静 × VCS≥60 × ADR≥3) |
| `accumulation` | 有人在买的 | `pp_today`(当日 oratnek PP)`pp_2plus_10d`(oratnek 10 日 ≥2)`morales_pp_10d`(**Morales 口袋支点 10 日 ≥3**;三格都带 trend_base 语境门) |
| `moving` | 在跑的 | `weekly_momentum_97` `bullish_4pct` `weekly_20_gainers` —— **与同名预设同一配方,测试锁死**;`preset` 字段给出预设名,前端可点进 Screener 载入 |
| `trouble` | 出问题的(持仓视角) | `stop_hit` `ll_break`(读 `sp_signal`)`extended`(ATR Matrix ≥7) |

规则:
- **门槛**固定 $1B 市值 + **$20M 日均成交额**(08-18 起,Andy 拍板;原 1M 股是 oratnek 的前提,对高价股偏严、对 $2 票偏松——CBRL $58×862k=$50M 被拦、$2 票 1.1M 股=$2M 却过),`universe_gated` 是过门槛的只数(08-14 数据 1,539 → 2,098);Screener 页不受此约束
- 每格最多 25 只,`truncated` = 被截掉的数;排序 **Hybrid RS 降序**,票旁数字 **08-18 起 = `rs_line_pctl_21`**(oratnek 的 RS 1M,自百分位;Andy:"应该用他的定义"),`rs_1m`(横截面)留作第二读数,两个字段票项里都有
- ⚠️ **`measured=false` 必须渲染成"未测量"**(空框 / 灰),不能画成 0 —— 首晚 `sp_*` / `ema21_atr_dist` 未出时是 **6 格**:三个 LL-HL、`liquid_leader_pullback`、`stop_hit`、`ll_break`(前端已指出我早先说 3 格是少数了)
- **`cross_zone` 数的是"区"不是"格"**:一只票在 moving 区三个格都出现只算 1;**≥3 区才列(08-17 收严,Andy:"改严格一点";≥2 时 08-14 有 177 只、其中 143 只恰两区,多是 leaders×moving 同义;≥3 单独收严剩 34 只,再叠加 Morales 收严后 08-14 数据剩 16 只)**;`cross_zone_rule` 字段写明当前门槛。这是对 oratnek "Tickers in 3+ watchlists" 的修正 —— 他那栏统计的多半是同义词。前端把它放顶部,替代原来的"出现在 N 张单"
- **`rs_high` 探测(08-18 加,Andy:"只做检测,不否定现有的参数")**:每只票项多一个布尔 `rs_high`(= `rs_line_pctl_21 == 100`,RS 线在 21 日新高),每格多一个 `count_rs_high`,顶层 `rs_high_rule` 写规则。**没有任何格用它筛选**;它是给页面做"只看 RS 新高"开关用的。依据:oratnek 08-17 页 29 只里 26 只满足;我们 LL-HL 1st 58 只里 2 只、2nd 67 只里 9 只满足——他没公开的收紧门八成是它
- **`top_3m` 探测(08-18 加,Andy:"只探不筛"):**每只票项 `top_3m` 布尔(= `perf_3m_pctile ≥ 0.85`,全池 3M 表现前 15%),每格 `count_top_3m`,顶层 `top_3m_rule`。**没有格用它筛选**。依据:三天(08-11/13/14)对 oratnek 页面拟合,他的池子是一张 3M 领先名单——开这个开关我们从他的 5.9× 收到 2.5×、他的 112 只只丢 4 只(`data/research/oratnek_diff/README.md`)。前端:与 `rs_high` 一样做成开关,建议叫「池子:全池 / 3M 领先」
- `weekly_20_gainers` 格 08-18 起读 `perf_5d`(5 根),不再读 `perf_1w`;`preset` 字段仍指向 Screener 的同名预设(阈值同、窗口不同,contract 上说明)
- 配方文字在 `recipe`,直接显示(和 rotation 的 `sentence` 同一原则:文案在引擎里,UI 不重拼)
- 前端通路(待 UI):格标题 → Screener 载入 `preset`;票 → ticker 页(Signal History 里能看它昨天在哪几格);Screener 里用户自建的预设**不进**晨报

- **08-19 晚 cron 起**:三个预设双胞胎格(`weekly_momentum_97` / `bullish_4pct` / `weekly_20_gainers`)加 **非 Healthcare** 闸,与 `screener-presets.json` 的 `excludeHealthcare: true` 对齐(08-18 vs oratnek:我们 Momentum 97 七只里五只生物科技,他十一只里零只)。universe.json 多两列 **`rs_line_pctl_63` / `rs_line_pctl_126`**(RS 线自百分位的 3M / 6M 窗;只探不筛——他 Momentum 97 的 11 只全在 126 日新高,我们的零只;见 `data/research/oratnek_diff/README.md` 08-18 节)
- **08-20 加(MRNA +177% 案例,Andy:"三个都同意,尤其是EP")**:entries 区第二格 **`episodic_pivot`**(change_pct ≥10% × rel_volume ≥3,与 EP 筛选器同配方;**故意不排除 Healthcare**——EP 是重定价事件,生物科技是主产区;当日 ≥15% 的照旧带 `chase` 标)。heating_up 每行多 **`confluence_days`**(同日 ≥4 个筛选器齐亮的天数,每天 +2 分——单日核弹不再被"多日合流"设计漏掉;MRNA 案例 9.0 → 11.0 进榜)。案例全文 `data/research/case_mrna_2026-08-19/README.md`
- **08-19 加(验刀报告三件套,Andy:"做起来")**:
  - `entries` 区最左新格 **`ma_reclaim`**(MA Reclaim:`cross_ema21_up` 或 `cross_sma50_up`,且 `rel_volume ≥ 1`;两个新布尔字段今晚 cron 首产,进 universe.json;在此之前 `measured=false`)。它是深回撤 V 反的入口(MU/SNDK/NBIS/RBRK 8 月起涨唯一提前亮的信号),不是趋势入场——在领头股上单看是抛硬币,要配主题四态和 ATR 位读
  - 每只票项多三个字段:**`chg_pct`**(当日涨幅 %,一位小数)、**`chase`**(布尔,= 当日 ≥15%;4% Bullish × 当日 ≥15% 是全场最差一格,20d −9.3%/胜率 36%)、**`atr_from_sma50`**(ATR 位,一位小数——页面上"能不能上车"那个数字:0–4 / 5–7 / ≥7)。每格多 **`count_chase`**,顶层 `chase_rule`。前端:`chase=true` 折到格底灰显,不删
  - **`data/history/watchlist_hits.csv`**:每晚每格**全部**命中(不止页面 25 只),一行 = (date, panel, zone, ticker) + close/chg_pct/rel_volume/atr_from_sma50/ema21_atr_dist/rs_line_pctl_21/rs_1m/rs_3m/h_score/perf_3m_pctile/vcs/sp_signal/group/group_state;按日幂等。三个月后验面板不用再重建 as-of
  - **`data/history/ticker_events.csv` 多了 `preset:*` 行**(`preset:sugar_babies` / `preset:monthly_leader_97` / `preset:vol_up_gainers` / `preset:stockbee_9m_setup` / `preset:4_bullish` / `preset:pp_count` / `preset:pocket_pivot` / `preset:weekly_20_gainers` / `preset:weekly_momentum_97` / `preset:21ema_watch`):Screener 预设由数据端每晚按 `screener-presets.json` 同一配方复算(`pipeline/screeners/preset_hits.py` 是 `screenerFilter.js` 的移植,测试锁死),历史已从 git 回填到 2026-03-16。**`ticker_events.json` 里因此也会出现这些 screener 名**——Signal History 若按名字查标签,请给 `preset:` 前缀一个显示规则(或先按前缀过滤);heat 分数不计它们(WEIGHTS 未列)。实证见 `data/research/scanner_validation_2026-08/presets_backfilled.md`:Sugar Babies −9.5%/31% 是最差一格,建议不上 Today's List

另有 `data/history/leaders_log.csv`(每晚一行/每只 liquid leader:`tml` 标志、所属组与四态、close、ATR 位置)—— **True Market Leader 的前瞻验证记录**:主题四态归档 08-07 才起,历史回测做不了,只能从今天起前瞻记;`liquid_leader` 字段也已进 universe.json。

收严 08-18(Andy:"70 以上有 33 个,太多了"):VCS 格加领先门,33 → 10。

收严 08-17:Morales PP 格由 `pp_count_10d ≥1`(372 只)改 **≥3**(111 只,Morales 的"cluster");cross_zone ≥2 → **≥3**。oratnek 两格与 VCS 未动(11 / 86 / 33)。

首跑(08-14 数据,结构格待 cron):TML 26(DELL / RBRK / GTLB / NTNX / PATH / NTAP…)· Liquid Leaders 181 · VCS 62 · anticipation 0(ti65/mdt 待 cron)· PP 今日 20 · PP 2+ 183 · Weekly Momentum 97 8 · 4% Bullish 23 · Weekly 20%+ 22 · Extended 16;cross_zone ≥2 共 27 只(NIQ / P / INFQ 三区)。

---

## 四点八、`data/output/correction_risk.json` —— Correction Risk 基础层(2026-08-17 加;**同日 Andy 决定暂停,前端先不接** —— 文件照常每晚生成、只当内部记录;开放问题见 memory `project_correction_risk`)

**产出**:`pipeline/risk/correction_risk.py`,run_all 里 rotation 之后;两条 yfinance 序列(^GSPC、^VIX,历史到 1990)。自己的失败域。
**当前消费方**:`CorrectionRiskPage.jsx` 的空槽 —— **这份文件就是那个槽位的标准被满足后的第一份数据**。

```
{ date, question, method, prob, base_rate,
  today:{date, vix, vix_quintile, above_200dma, d200, prob, n_cell, prob_vix_only, n_vix_only, base_rate},
  table:{ sample:{from,to,sessions,episodes,half_split}, base_rate, vix_edges[6],
          by_vix_quintile:{full,first_half,second_half}[q]={rate,n}, monotone_spearman:{full,first_half,second_half},
          by_vix_quintile_x_200dma:{"Q1_above200":{rate,n}, ...} },
  overlay:{note, regime_bands_2024_2026:{damaged,extended,source}},
  predicts_return:false, separates_tail:true, caveats[] }
```

**是什么**:P(未来 21 个交易日内标普收盘比今天低 ≥5%)。**方法是条件基准率表,不是模型**:格子 = (VIX 五分位 × 是否在 200 日线上),值 = 1990 年以来该格的历史频率。样本 9,221 个交易日、**199 段独立回撤事件**(槽位页要求 ~115)。VIX 五分位单看:5.5% / 8.1% / 13.8% / 26.0% / 29.7%,基准 16.6%,**前后半样本各自单调**(ρ 0.9 / 1.0);200 日线下 Q3–Q5 翻倍。首份读数(08-14):VIX 14.25 → Q2、线上 → **8.7%**(n=1,720)。

**为什么不是模型**:9 特征逻辑回归(VIX、期限结构、实现波动、均线距离、回撤状态、HYG/IEF 信用代理)按年走前 2013–2026,**out-of-sample 不如基准率**(Brier 0.133 vs 0.121,AUC 0.52),分位不单调;只有 VIX 与 200 日线两项有微弱 OOS 技能(AUC 0.63)。表把这点技能透明地留下,不加参数。回归留在 `logistic_appendix()` 可复现(`appendix_logistic_oos` 字段,夜间不重跑)。

**渲染规则**:
- ⚠️ `prob` **必须和 `base_rate` 并排**,再显示 `n_cell` —— 这是槽位页自己立的标准("一个数,连同它对照的基准率")
- ⚠️ `predicts_return:false` / `separates_tail:true` 与 `caveats[]` 必须显示(同 regime 的规矩)
- `overlay` 是**分开的一读**(regime.py 的 2.2 年广度结论),**不与 `prob` 平均**;页面上分区显示、标注各自窗口
- 可以画整张 `by_vix_quintile.full` 当刻度(五档 + 今天所在档高亮),`first_half/second_half` 是"它站得住"的证据,建议 hover 显示
- 不画红绿灯:它回答"这里能亏多少",不回答方向

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

---

## 七、待数据端(前端在此追一行当保险 —— 跨会话消息会丢,2026-08-17 就丢过一封)

格式:`- [日期] 一句话 + 你测过什么 + 你要的字段/口径`。数据端处理完把该行改成 ✅ 并写在哪个 commit。

- [08-17] oratnek 同日扫描对照:VCS 刻度 → ✅ 17a2667(领先门,33→15);CBRL 闸 → ✅ 59e3892(成交额闸);RELY 的 RS 1M → ✅ 破译:RS 线 21 日自百分位,29/29 复现,新字段 `rs_line_pctl_21`(universe + watchlist 票项),今晚 cron 起有值

## 八、数据端 → 前端:Today's List 改成"按步骤用"(2026-08-19,来自验刀报告 `data/research/scanner_validation_2026-08/playbook/index.html`)

字段全部现成(watchlist.json 每票 `rs_line_pctl_21` / `rs_high` / `top_3m` / `atr_from_sma50` / `sp_signal`;每格 `count_rs_high` / `count_top_3m`)。要的是**把 17 格按五步重新编组、给小白一条能照着走的路**:

1. 顶部一条**步骤条**:水域 → 脚印 → 位置 → 入场 → 出场;点哪一步,属于这步的格高亮,其余降灰(不隐藏),默认落"脚印"。归属:水域=(Themes 四态、池子开关);脚印=Weekly 20%+ / 4% Bullish / PP 三格 + RS 新高开关;位置=ATR Matrix ≤4 / Extended;入场=第一波(4%×ATR≤4×20d 新高×RS 新高)/ EP / Liquid Leader Pullback(注明"只在 Leading 主题");出场=Structure Pivot(stop_hit / ll_break)/ Extended。
2. 两个全局开关做成一行芯片:`池子:全池 / 3M 领先`(`top_3m`)、`只看 RS 新高`(`rs_high`);开着时格标题旁显示 `count_rs_high/count`。
3. 票项旁两个数字、不多:RS 1M(`rs_line_pctl_21`,现有)+ **ATR 位**(`atr_from_sma50`,一位小数),0–4 / 5–7 / ≥7 三色,≥7 用 trouble 色。
4. 4% Bullish 格:当日 ≥15% 的票折到格底灰显(追高警告),不删。
5. 每格标题旁 ⓘ,三行:这格找什么 · 该配谁 · 别怎么用;文案数据端给(报告第三节)。
6. 预留一格 `均线收复`(entries 区最左),数据端加字段前不显示。
7. 视觉沿用现网格;步骤条+芯片用现有 accent,不新增颜色;ATR 三色是语义色。页面上不加长文。

数据端配套(我做):`均线收复` 字段(↑EMA21/↑SMA50 事件 + 量比)、4% Bullish 的 ≥15% 子标签、预设命中每晚落 ticker_events.csv。

## 九、数据端 → 前端:Regime 显示层(2026-08-19;**Andy 两次拍板,以后一次为准**)

1. 16:40 JST 第一版:改用分析层四档(Damaged/Mixed/Healthy/Extended,47/63/75)。**作废。**
2. 17:20 JST 定稿:**"换回原来的 5 层读数。把 Full 变成 Euphoria"** —— 保留 `RegimeBand.jsx` 现有五档与切点(Defence 0–18 · Caution 18–40 · Neutral 40–62 · Constructive 62–84 · **Euphoria 84–100**),只把顶档的名字 Full → **Euphoria**;power-trend / breadth 两个投票者的绑定逻辑不动。

背景:08-14/15 分数 78.1 显示 Constructive、分析层已是 Extended;08-17 坏数据(过期指数 K 线,数据端已加闸)推到 87.5 显示 Full。Andy 的体感是 euphoria,名字照体感改。`data/research/regime_study_2026-08/README.md`:从 ≥75 一日掉到 ≤60 的 27 次之后 20 日中位 +1.8%、胜率 81%,顶档名字是描述不是预警,**不加任何 euphoria 触发的提示或拟合**。
