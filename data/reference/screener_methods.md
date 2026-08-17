# Screener 方法档案 —— 每个指标 / 扫描:谁的、原用法、我们的用法、在找什么、怎么组合

*2026-08-17 建。这是"为什么这些字段存在"的一份总账,补 `DATA_CONTRACTS.md`(字段是什么)和 `screener_inventory_2026-08-17.md`(筛选键怎么映射)之间的空。*
*出处:`screener_competitors_2026-08-17.md`(四家对标原话)、`indicators/third_party/`(移植的原版源码)、Stockbee 博客、Steve Jacobs / oratnek / Alex Desjardins 的 X 帖。原话数值全部按他们本人写的。*

读法约定:**「原用法」= 作者怎么用;「我们的用法」= 字段在我们池子里怎么算、进了哪个预设;「在找什么」= 这个数回答的那一个问题;「组合」= 和谁配、为什么配、为什么不配。**

---

## 〇、先分清三类东西

| 类 | 回答的问题 | 例子 |
|---|---|---|
| **强弱**(strength) | 这票过去一段时间比别人/比自己强多少 | RS 百分位、rs_ibd、TI65、Double Trouble、MDT、trend_base |
| **位置**(location) | 这票现在站在哪 —— 离均线几个 ATR、在结构的哪一段 | ATR Matrix、ema21_atr_dist、Structure Pivot 的 1st/2nd/phase、high_52w_dist |
| **状态**(condition) | 这票此刻是收着还是放着、有没有人在买 | VCS、pocket pivot、DCR、rel_volume、ADR、from_open、bo_count、change_pct |

**组合的基本语法是"一个强弱 × 一个位置 × 一个状态"。** 同一类里叠两个几乎不加信息(两个 RS 窗口高度相关);跨类叠一个就是一次真正的过滤。四家对标里没有一家违反这条 —— oratnek 是 RS(强)× ATR-from-50SMA(位)× PP(态);Steve 是 RS≥97(强)× ATR Matrix 0–4(位)× ADR 带(态);Stockbee 是 TI65/DT/MDT(强)× 安静日(态)× 形态肉眼(态)。

---

## 一、强弱类

### RS 百分位 `rs_1m / rs_3m / rs_6m`(别名 rs_21d/63d/126d)
- **原型**:IBD RS Rating 的思路 —— 相对同侪的收益排名,不是相对指数。
- **我们**:perf_1m/3m/6m 在 **tradeable 集(≥$1B 且 ≥$2M 日成交额,~2,557 只)内**的百分位 ×99;非 tradeable 为 null;缺失不得分(`na_option='top'`,08-12 事故后统一)。
- **在找什么**:这段时间它比 tradeable 池里多少票强。
- **原用法参照**:oratnek 门槛 **RS21 > 70 且 RS63 > 80**;Steve 的 Qullamaggie 筛 **RS ≥ 97(1W/1M/3M/6M 任一)**。
- **组合**:× ATR Matrix(位)× PP/VCS(态)是标准三件套。**别叠 rs_1m 和 rs_3m 当两条独立条件**,一个是另一个的近似;要两个窗口的意义应看它们的差(加速),那是 groups.json 的 `rs_accel_rate` 在做的事。

### `rs_ibd`
- 0.4·rs_3m + 0.4·rs_6m + 0.2·rank(perf_1y)。**记录型**:量过去一年的成绩单,不是当下;IPO/新票、刚启动的票、已经停下的老领头都会读错。旁边一定要看 rs_1m。

### `h_score`(hybrid)/ `i_score` / `f_score`
- (2·f + 3·i + 1·rs_1m + 2·rs_3m + 2·rs_6m)/10。`i_score` = 行业内 tradeable 成员 rs_3m 中位数的分位(行业强弱);`f_score` **当前恒 50**(源头两列空),等于 2/10 权重是常量。97 Club 用 h ≥ 80。oratnek 的 "Hybrid RS" 排序是同一思路。

### `trend_base`
- close > SMA50 且 **周线 WMA10 > WMA30**(需 ≥30 周历史)。Stan Weinstein 式的"在 Stage 2"闸,是我们 6 个预设的前置条件。
- **在找什么**:中期趋势朝上、周线结构没坏。
- **组合**:几乎所有"持仓型"预设的第一道门;和 Structure Pivot 的 setup 高度重叠(LL-HL 本来就要求上升结构),叠一起可以但别把它当第二条独立证据。

### Stockbee 的三个 anticipation 强弱条件(2026-08-17 加列)
| 列 | Telechart 原文 | 阈值 | 在找什么 |
|---|---|---|---|
| `ti65` | `avgc7/avgc65` | **> 1.05** | 近一周比近三个月的均价高 5%+:**刚刚变强** |
| `c_low52w` | `c/minl252` | **≥ 1.8** | 一年里从底部翻了 80%+:**已经是大赢家** |
| `mdt` | `c/avgc126` | **> 1.19** | 比半年均价高 19%+:**中期趋势够陡** |
- **原用法(Stockbee)**:三条各配 `minv3.1 > 100000`(3 日最低量)+ **当日涨跌在 ±1% 内**(安静日),扫出几十只,再人工看形态 —— 3–10 天窄幅整理、回调没出 4% 阴线、缩量。核心思想:**突破那天买已经晚了半天,要在还没动的时候把名单圈好**,预定入场价,止损可以极近。
- **我们的用法**:三列 + `min_vol_3d` 进 universe;`pipeline/tools/anticipation_scan.py` 出名单;详见第四节的组合。
- **注意**:`low_52w` 在我们池里是**分数距离**(close/min(low) − 1),不是价格,`c_low52w = 1 + low_52w`。08-14 正确口径的 Double Trouble 是 303 只($1B+ 189),之前一次估算把它当价格除、算成 1,675,已勘误。

---

## 二、位置类

### ATR Matrix `atr_from_sma50`(= 每个 ticker 徽章的 `atr_ext`、ETF 行的 `dist_sma50_atr`,三处一个函数)
- **血缘**:@jfsrev + @RealSimpleAriel → Steve Jacobs 系统化 → oratnek 写进 LL-HL 体系。
- **定义**:(close − SMA50)/ATR14 —— 股价高于 50 日线几个 ATR。有符号。
- **原用法(Steve)**:`<0` 忽略 · **0–4x 建仓区** · 5–7x 持有不动(除非跌破 MA10/20)· **≥7x 开始减**,7/8/9/10/11x 各卖 20%。止损 = 成本下方 1.5–2x ATR。
- **原用法(oratnek)**:选股前提 **<5(理想 <4)**;离场触发 **≥7 减 33%**。他自己那列是 `dist·close/atr`(漏 (1+dist)),他的阈值换算到我们的要除以 (1+dist)。
- **我们**:0.5% 价格的 ATR 地板以下判 null(全是 $10 SPAC 壳和并购锁价票);`≥7` 尾巴里会有近 60 天跳空后钉价的并购标的(Wilder-14 记得跳空日),看榜要配行业/成交量。
- **在找什么**:**现在追它要付多少"延伸溢价"**。它是位置不是方向 —— 一只 −3 ATR 的票可能在筑底也可能在崩。
- **组合**:× RS(强)是最经典的一对 —— 强的票、还没跑远。× VCS:VCS 高 + ATR Matrix 0–3 = "强势后的收缩、还贴着均线";VCS 高 + ATR Matrix 15+ = **钉价的并购票**,不是机会(见第四节的教训)。

### `ema21_atr_dist`(2026-08-17 加)
- (close − EMA21)/ATR,同一 helper。**21EMA Watch 预设的本意**:离 21EMA **−0.5~+1 ATR** 且离 50SMA **0~3 ATR** = "回踩到 21 日线附近、还没离 50 日线太远"。这个预设 5 个月里一直指向比值列,实际筛的是"价格在 SMA20 之下",08-17 Andy 拍板改回 ATR 口径。

### Structure Pivot `sp_*`(oratnek Advanced Structure Pivot,移植,黄金对照 5/5)
- **在找什么**:**Dow 理论意义上的趋势确认** —— 一个 Lower Low 之后出现 Higher Low,供需翻转成立;然后把 LL→2nd Pivot 这段当尺子量出入场和目标。
- **原用法(oratnek)**:1st Pivot(HL 到 2nd 的 Fib 0.618)建半仓,止损 21EMA Low;**5 根内(理想 3 根)必须到 2nd Pivot**,10 根没到即使没破 21EMA 也清;到 2nd 加仓、止损上移到 1st;+25% 优先落袋,否则 R:R 3 或 ATR-from-50SMA ≥7 减 33%;收盘跌破 21EMA Low 清剩余。偏好在 10/20/21 日线上获得支撑的干净图。他的 Today's Watchlist 四栏 = 昨天触发 1st / 2nd / Trend Line Break 的票 + PP(10 日内)的票,按 Hybrid RS 排序。
- **我们**:字段见契约;`sp_signal ∈ {1st_break, 2nd_break, counter_break}` + `pp_count_10d ≥ 1` 就是那四栏。
- **组合**:它自带位置(1st/2nd/phase)和状态(signal),配一个强弱即可 —— oratnek 自己配的是 RS21>70 & RS63>80 & ATR-from-50SMA<5。**别再叠 trend_base**(重复)。

### `high_52w_dist`
- (close − 52 周高)/52 周高,≤0。**注意我们的 NULL 结论**:「离 52 周高 10% 以内 + 3 月涨 30%」那个网红筛在 1,813 只上是负 alpha,52WH 这道闸砍掉了 5/6 的动量优势(见 memory `project_52wh_momentum_filter_null`)。它当"位置"看可以,当"筛选闸"用要小心。

---

## 三、状态类

### VCS `vcs`(oratnek VCS v2,忠实移植,黄金对照通过;2026-08-17 换尺)
- **在找什么**:**波动是不是在收缩、能量在不在蓄** —— 不判方向。0.4·ATR 压缩 + 0.4·标准差压缩 + 0.2·缩量,× 效率过滤(直线不算收缩),EMA3 平滑,连续 ≥70 天数加分 ≤15,近 13 日低点破 63 日低点 ×0.75。
- **原用法(oratnek)**:**80+ 临界压缩、60–80 发展中、<60 扩张**;Screener 里 VCS >60/70 + 均量 + RS。"VCS 过 80 就盯着那个整理区,放量决定性突破才确认。"
- **我们**:老版(改造过、无测试)已换;新尺**明显更严**(134 只样本中位 50→35,≥70 减半)。**读它时永远配 ADR** —— 见下一条。
- **组合**:× 强弱(RS/TI65/DT/MDT)= "有资格蓄势的票在蓄势";× ATR Matrix 0–4 = "蓄势且没跑远"。**× ADR ≥3% 是必须的**:08-14 首跑,不带 ADR 下限时榜首全是并购锁价票(APGE/CRNX/UTZ/FBRX…VCS 90–100、ADR 0.6–2%)—— **钉住不是收缩**。

### ADR `adr_pct`
- ATR/close×100(Finviz ATR14)。Qullamaggie:"High ADR is gold, low ADR is …",他偏好 5%+;Steve:下限"高于平均"(约 3%),**上限 = 最大可承受亏损 ÷ 1.5**(止损 −9% → 上限 6%),他在 3–6% 里选。
- **在找什么**:这票一天正常能动多少 —— 既是"值不值得做"(太低不动),也是"止损能不能扛"(太高被噪声打掉)。
- **我们(08-17 拍板)**:持仓型预设上限 **6**(21EMA Watch / Pocket Pivot / PP Count / 97 Club),扫描型保留 **10**;表里按热度着色,越高越热,6 是可辨线。08-14:$1B+ 非医疗里 3.5–6 有 820 只、6–10 有 253 只(半导体/软件/航空防务)。
- **组合**:它是所有"状态"里最该常驻的一个 —— VCS 没它会被钉价票骗,RS 没它会选到不动的票,ATR Matrix 没它不知道 1 个 ATR 是 1% 还是 8%。

### Pocket Pivot `pocket_pivot` / `pp_count_10d` / `pp_count_30d`(一个实现三个窗口)
- **原型**:Gil Morales / Chris Kacher —— 阳线且当日量 **> 前 10 根里阴线的最大量**。**我们的定义比原版严**:比前 10 根**全部**的最大量(审计过,Andy 说先不改)。
- **原用法(oratnek)**:"最近 10 个交易日里有一天出现 PP"是他的选股前提之一;"2nd Pivot 当天出现 PP 最理想"。
- **在找什么**:**有人在安静的整理里放量买了一天** —— 机构脚印。
- **组合**:× VCS(收缩里的一次放量)是它最好的搭档;× Structure Pivot 的 2nd Pivot 是 oratnek 的加仓信号;`pp_count_30d ≥ 3` 单独成一个预设(PP Count)。

### DCR `dcr_pct`、`from_open_pct`、`rel_volume`、`change_pct`
- 都是**当日盘面**:收在日内区间的哪一段 / 从开盘涨了多少 / 量比 50 日均量 / 涨跌幅。
- **原用法(Stockbee 4% 突破)**:`c/c1 ≥ 1.04 and v > v1 and v ≥ 100000` + 收盘离最高 <30%(DCR ≥ 70)、突破前不能已连涨 3 天、前一日窄幅、突破前有收缩、第 1–3 个 setup、年轻趋势。止损=突破日最低;第 3 天出一半;3 天无跟进走。
- **原用法(Stockbee EP / 9M)**:`v > 3×avgv50 and v ≥ 300000`,财报 QoQ +100% 且 EPS ≥5 分、营收 +5%,跳空 5–300%;要 **neglect + 改变游戏的财报**。持 2–6 周。
- **我们**:4% Bullish(日涨≥4 · RelVol≥1 · from-open≥0 · rs_21d≥60)、Vol Up Gainers、Stockbee 9M Setup(均量≥9M · RelVol≥1.5 · 日涨≥5 · DCR≥60)。
- **组合**:这几个是"**今天发生了什么**",天然配"**之前是什么状态**"(VCS 高 + 今天 4% 放量 = 收缩后的启动);单独用是热度榜。

### `bo_count_1m/3m/6m/1y`(Sugar Babies)
- Pradeep 的原规则:窗口内 **量 ≥ 9M 且涨幅 ≥ 4%** 的天数。**在找什么**:惯于放量大涨的"体质"。Sugar Babies 预设 = 一年 ≥10 天且近三月 ≥2 天。它是"过去的状态"统计,更像强弱类的边缘。

---

## 四、组合(已在用的、新加的、明确不该做的)

### 已在用(10 个只读预设)
见 `screener_inventory_2026-08-17.md` 第二节。按上面的语法读它们:
- **21EMA Watch** = trend_base(强)× ema21_atr −0.5..1 & sma50_atr 0..3(位)× 周涨 0–15%、DCR ≥20、PP≥1、ADR 3–6(态)—— 最完整的三件套,08-17 起位置那半才真正生效
- **97 Club** = h_score ≥80 & rs_21d ≥97(强)× trend_base × ADR 3.5–6 —— 缺位置项,可考虑加 ATR Matrix ≤4
- **Pocket Pivot / PP Count** = 态 × trend_base(强)× ADR —— 缺位置项
- **4% Bullish / Vol Up / Weekly 20%+ / Momentum 97** = 态或强,单维热度榜,**故意不加位置**(它们是"看谁在动")

### 新加:Stockbee anticipation × VCS(2026-08-17)
```
强:  ti65 > 1.05  或  c_low52w ≥ 1.8  或  mdt > 1.19      (三选一,谁的资格都行)
态:  |change_pct| ≤ 1%   (Stockbee 的安静日)
     min_vol_3d > 100k     (他的流动性底线;我们默认再叠 $1B 市值)
     vcs ≥ 60              (他"人工看形态"那步的量化;70 更严)
     adr_pct ≥ 3           (⚠️ 必须,否则并购锁价票霸榜)
位:  可选 atr_from_sma50 ∈ [0, 4]  (Steve 的建仓区;不加也行,VCS 高的票通常已经贴回均线)
```
- **原版和我们的差别**:Stockbee 是三条独立扫描 + 眼睛;我们合成一条 + VCS 代眼睛 + 加了 ADR 下限(他的 Telechart 池子里没有 SPAC 壳和锁价票这个问题,我们的有)。
- **今天(08-14 数据,只有 DT 一条腿、VCS 旧尺)**:36 只 —— PL / MRVL / ARM / RKLB / ASTS / ALAB / NRIX / IRDM / KMX …;不带 ADR 下限时是 48 只且前 7 名全是并购票。
- **工具**:`python -m pipeline.tools.anticipation_scan [--vcs 60] [--adr-min 3] [--all]`。ti65/mdt 明天 cron 后有值,VCS 换新尺后名单会更短。
- **前端接法**:三个 `strong` 键 + `minVol3d` 键需要进 `screenerFilter.js`;或先不做预设,把这个工具的输出当一张单看几天再定。

### 明确不该做的组合(实测过的)
- **RS 两个窗口当两条独立条件** —— 高度相关,不加信息(要用它们的差:`rs_accel_rate`)
- **52WH ≤10% + 3M ≥30%** —— 1,813 只上负 alpha(memory `project_52wh_momentum_filter_null`)
- **VCS 不带 ADR** —— 钉价票霸榜(08-14 实测)
- **ATR Matrix 单独当"最延伸"排行** —— 尾巴是跳空后钉价的并购标的,要配行业/成交量
- **screener 信号序列当预测** —— 42 个序列 0 个跑赢匹配随机基线(memory `project_sequence_mining`)
- **主题四态的 `rs_accel` 当"减速"讲** —— 它是门槛不是斜率,匀速跑赢也读负(FOUR_STATE_DESIGN §8)

---

## 五、四家对标的完整体系(压缩版,细节见 `screener_competitors_2026-08-17.md`)

| | 强弱 | 位置 | 状态 | 出场 |
|---|---|---|---|---|
| **Stockbee** | TI65 / DT / MDT;4% 突破;EP 财报 | —(形态肉眼) | 安静日;窄幅;缩量;第 1–3 个 setup | 3 天出一半;+8% 出一半;跳空 20% 全出;止损=突破日低 |
| **oratnek** | RS21>70 & RS63>80 | ATR-from-50SMA <5(理想 <4);LL-HL 结构 1st/2nd | PP 10 日内;VCS(他的另一支) | 5 根内到 2nd 否则清;+25% 落袋;R:R 3 或 ATR≥7 减 33%;收盘破 21EMA Low 清 |
| **Steve Jacobs** | RS ≥97;均线序列 Price≥MA20≥50≥100≥200 | ATR Matrix 0–4 建仓 | ADR 3–6% | 5–7x 持有;≥7x 每整数卖 20% 到 11x;止损 1.5–2 ATR |
| **Alex Desjardins** | 漏斗 500→10–100→0–10;RS 排名 | 20dma>50dma、在 200 上;reversal pivot(下降结构最后一个日线高点) | Liquid Leaders;21dma pullback | LOD 止损;+10–15% 卖半;破 10DMA 卖 1/4;破 21DMA 清 |
| **我们** | RS 百分位(可审计)、TI65/DT/MDT、trend_base | ATR Matrix、ema21_atr_dist、Structure Pivot | VCS v2、PP、ADR、DCR、RelVol、bo_count | (交易端在 IB Order Panel,不在 screener) |

**我们独有的**:主题/行业层(76 个主题带共动性验证、四态、色带、归档)、广度/环境层(15 条件、五档、min-of-voters)、每一个字段可回到代码和测试。**四家都没有的东西不该被四家的框架遮住** —— 组合时记得先问"这票的主题在 Leading 还是 Weakening",那是他们没有的一维。
