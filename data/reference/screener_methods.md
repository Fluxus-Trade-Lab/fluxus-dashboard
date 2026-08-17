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

### Pocket Pivot —— 两个定义,两个名字(2026-08-17 起)
- **`pocket_pivot` / `pp_count_10d` / `pp_count_30d` = Morales / Kacher 原定义**:上涨日(close > 昨收)且量 > 前 10 根**下跌日**的最大量 —— 买盘 vs 卖盘。审计:与 A/D 量比相关 +0.71。预设 Pocket Pivot / PP Count 读这一族。
- **`vol10_green` / `_count_10d` / `_count_30d` = oratnek 的 "PP (Vol > 10D)"**:阳线且量 > 前 10 根**全部**的最大量 —— 量能突增。这是 08-17 前 `pocket_pivot` 的算法,换名不换数;晨报 oratnek 那两格读它。
- 同一只票两个答案很常见(AEHR 08-14:Morales 10 日 4 次,oratnek 0 次)—— 不是细节差异,是两个量。
- **原用法(oratnek)**:"最近 10 个交易日里有一天出现 PP"是他的选股前提之一;"2nd Pivot 当天出现 PP 最理想"。
- **在找什么**:**有人在安静的整理里放量买了一天** —— 机构脚印。
- **组合**:× VCS(收缩里的一次放量)是它最好的搭档;× Structure Pivot 的 2nd Pivot 是 oratnek 的加仓信号;`pp_count_30d ≥ 3` 单独成一个预设(PP Count)。
- **吸筹因子 `ad_ratio_20` / `cmf21`**(08-17 加):上涨日量占比(20 日)+ Chaikin Money Flow 21 —— 审计说我们之前**没有一个字段真的在测吸筹**(rel_volume 无方向,abc_rating 无量);这两条是持续流向,PP 是离散事件,相关但不重复。**未做前瞻检验**(面板无成交量),先当描述用。

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
- **Liquid Leader(RS 前 20%)当 20 日收益预测** —— 9 期里 3 期赢过"只要流动性",中位 +0.41% vs +0.71%(第七节);当资格名单用,别当信号
- **主题四态的 `rs_accel` 当"减速"讲** —— 它是门槛不是斜率,匀速跑赢也读负(FOUR_STATE_DESIGN §8)

---

## 六、十个预设 + 五个 Python 筛选器,逐个说

先说一件容易踩的事:**我们有两套东西名字重叠、定义不同。**
- **预设**(`frontend/public/data/screener-presets.json`,10 个):在浏览器里对 universe.json 做过滤,Screener/Watchlist 两页用
- **Python 筛选器**(`pipeline/screeners/*.py`,每晚跑,出 `data/output/*.json`,Screeners 页用):`momentum_97` / `vol_up_gainers` / `episodic_pivot` / `healthy_charts` / `ema21_watch` …

"Momentum 97"和"21EMA Watch"两边都有,**不是同一个定义**(下面标出)。写文案、做对照时先说清是哪一个。

### 预设(按"强 × 位 × 态"拆)

**1 · 21EMA Watch** —— *强*:trend_base · *位*:离 21EMA −0.5~+1 ATR、离 50SMA 0~3 ATR(08-17 起真 ATR 口径) · *态*:周涨 0–15%、DCR ≥20、10/30 日内 PP ≥1、ADR 3–6
- **原型**:Qullamaggie / oratnek 的"回踩 21EMA 再上车" —— 领头股第一波之后回到均线,止损可以放很近,仓位才做得大。oratnek 的 1st Pivot 入场本质上就是这个。
- **在找什么**:**趋势里的第二次入场机会**,不是新趋势。
- **它看不到的**:方向 —— 见顶的票下来时也会穿过这个带子,和上行中歇脚的票在数字上一样;这就是为什么要配 trend_base、周涨为正、有 PP。
- **Python 同名兄弟 `ema21_watch.py`**:SMA20 距离 −2%~+3% + RS 分位 ≥80,粗得多,只做候选表。

**2 · 4% Bullish** —— *态*:日涨 ≥4%、RelVol ≥1、从开盘为正 · *强*:rs_21d ≥60 · ADR 3.5–10
- **原型**:**Stockbee 的 4% 突破扫描** `c/c1≥1.04 and v>v1 and v≥100000`(原话)+ Qullamaggie 的"看从开盘"—— 开盘之后还在涨才是当天真有买盘,高开低走不算。
- **在找什么**:**今天启动的动量爆发**(Stockbee:3–5 天、8–20% 的一段)。
- **原用法的后半段我们没有**:突破前不能已连涨 3 天、前一日窄幅、有收缩、第 1–3 个 setup —— 这些是"哪种 4% 才值得买",在我们这里要靠 VCS(收缩)和 sp_days(第几个 setup)去补,或者靠眼睛。
- **组合**:× VCS ≥60 = "收缩之后的启动日"(最有价值的一种 4% 日);× Structure Pivot 的 1st/2nd_break = oratnek 的入场日。

**3 · Vol Up Gainers** —— *态*:日涨 ≥0、RelVol ≥1.5 · ADR 3.5–10
- **原型**:同 Stockbee,但把重心从"涨多少"移到"**量有没有人付**"。价格可以空涨,1.5 倍量意味着有 size 被吸收。
- **在找什么**:**机构脚印**,不管涨幅。
- **它看不到的**:RelVol 是对自己的均量,一只平时死水的票很小的钱就过 1.5x —— 要看美元成交额;也分不清吸筹和派发。
- **Python 兄弟 `vol_up_gainers.py`**:日涨 ≥4% 且 RelVol ≥1.5(比预设严)。

**4 · Weekly Momentum 97**(原 Momentum 97)—— *强*:1 周分位 ≥.97 **且** 3 月分位 ≥.85 · trend_base · ADR 3.5–10(**无市值门槛**,Watchlist 页会叠 $1B)
- **原型**:Qullamaggie 式"只看动量最强的 3%"。
- **在找什么**:**现在正在跑的票** —— 一周和一季同时在顶部。
- **⚠️ 同名不同物**:Python 的 `momentum_97.py` 是 perf_1w/1m/3m/6m **四窗口等权综合分位的前 3%**,一周和两季同权 —— 它的设计是"找刚开始的",一个月前平平的票只要这几周飞了就能进榜。两者共享大约一半的名单。`rs_ibd` 又是第三个问题("谁一直在赢")。**三个不是优劣,是三个不同的问题**,别混用。
- **它看不到的**:新趋势的起点、下跌途中的反弹、第五次冲同一位置 —— 数字上一模一样。榜上的票通常已经走了一大段;当候选看,不当入场看。
- **组合**:它是热度榜,**故意不加位置**;要变成可下单名单就叠 ATR Matrix ≤4 或 ema21_atr_dist。

**5 · Monthly Leader 97**(原 97 Club)—— *强*:h_score ≥80 且 rs_21d ≥97 · trend_base · ADR 3.5–6
- **原型**:IBD 的 RS 97+ 俱乐部;Steve 的 Qullamaggie 筛(RS ≥97 任一窗口)。
- **在找什么**:**近一个月最强的 3% 且综合分也高的票**。h_score 里 f_score 恒 50,所以实际是 i_score(行业)+ RS 三窗口。
- **组合**:缺位置项;加 ATR Matrix ≤4 就是 Steve 的整套。

**6 · Stockbee 9M Setup** —— *态*:均量 ≥9M、RelVol ≥1.5、日涨 ≥5%、DCR ≥60 · 剔医疗
- **原型**:**Stockbee EP9M(Episodic Pivot 9 Million)** —— 当天 ≥900 万股成交、有明确触发、最好有可辨识的催化剂,持 2–5 周。EP 的原始定义:`v>3×avgv50 and v≥300000`,财报 QoQ +100% 且 EPS ≥5 分、营收 +5%,**neglect + 改变游戏的财报**,跳空 5–300%。
- **在找什么**:**故事变了的那一天** —— 市场把它按另一套事实重新定价,而估值要几周才追上,所以这常是一段的开头不是结尾。
- **它看不到的**:跳空守不守得住(开盘就触发,收盘红了也是同一行);同一个失败两次的题材第三次跳空看起来和第一次一样;催化剂本身(我们没有财报数据进 universe)。
- **Python 兄弟 `episodic_pivot.py`**:跳空 ≥10% 且 RelVol ≥3 且市值 ≥$500M。
- **组合**:EP 天然不配 VCS(它是扩张不是收缩);配的是 `sp_days`(是不是新结构)和主题四态(题材是不是 Leading)。

**7 · Sugar Babies** —— bo_count_1y ≥10 且 bo_count_3m ≥2
- **原型**:Pradeep(Stockbee)的 "sugar babies" —— **惯于放量大涨的体质股**,原规则:量 ≥9M 且涨幅 ≥4% 的天数。
- **在找什么**:不是今天,是**这只票的性格** —— 一年里有 10 天以上这种日子,近三个月还有。做爆发型交易时,先挑会爆发的票。
- **组合**:× VCS = "会爆的票正在蓄";× 4% Bullish = "会爆的票今天爆了"。它是唯一一个"过去状态统计"型的强弱代理。

**8 · Pocket Pivot** —— *态*:当日 PP · *强*:trend_base · ADR 3.5–6
**9 · PP Count** —— *态*:30 日 PP ≥3 · trend_base · ADR 3.5–6
- **原型**:Gil Morales / Chris Kacher 的口袋支点 —— 阳线且量 > 前 10 根阴线的最大量;我们比全部 10 根(更严,已知偏离)。oratnek 把"10 日内出过 PP"当选股前提、"2nd Pivot 当天出 PP"当最佳加仓日。
- **在找什么**:**安静整理里的一天放量买入** —— 机构在建仓的痕迹;PP Count 找的是反复出现这种痕迹的票。
- **组合**:× VCS 是最好的一对(收缩里的一次放量);× sp_signal = 2nd_break 是 oratnek 的最佳日。

**10 · Weekly 20%+ Gainers** —— 周涨 20–500% · ADR 3.5–10
- **原型**:Stockbee 的"动量爆发"尺度 —— 3–5 天 8–20%,一周 20% 以上就是**极端爆发**;也是 Qullamaggie 找"第一波"的方式(先大涨,再等它回踩/收缩)。
- **在找什么**:**上周发生了大事的票**。它本身不是入场信号,是**加入观察池的信号** —— 接下来看它是收缩(VCS 上升)还是散掉。
- **组合**:这周进池 → 之后两三周看 VCS 和 ATR Matrix 回落到 0–4 → 那时是 21EMA Watch 或 Structure Pivot 的活。三个预设其实是**同一只票的三个阶段**。

### 五个 Python 筛选器(Screeners 页,每晚跑,不进预设)
| 筛选器 | 定义 | 在找什么 | 和预设的关系 |
|---|---|---|---|
| `momentum_97`(显示名 **Composite 97**) | perf 1w/1m/3m/6m 等权综合分位前 3%,分 100/99/98/97 桶 | 现在正在跑的(含刚起步的) | 与预设 Weekly Momentum 97 定义不同(08-17 前两者同名) |
| `vol_up_gainers` | 日涨 ≥4% 且 RelVol ≥1.5 | 有人付钱的一天 | 比预设 Vol Up 严 |
| `episodic_pivot` | 跳空 ≥10% 且 RelVol ≥3 且市值 ≥$500M | 重新定价日 | Stockbee 9M 的另一种写法 |
| `healthy_charts` | 在 50/200SMA 上、离 52 周高 5–25%、1 月为正、RS ≥80、RelVol ≥0.5 | 在歇的上升趋势(不是在跑的) | 无预设对应;是"名单该保存"型 |
| `ema21_watch` | SMA20 距离 −2%~+3% + RS 分位 ≥80 | 回到均线的强势票 | 与预设 21EMA Watch **同名不同定义**,粗 |

**这五个的共同点**:每个的 docstring 里都写了"它看不到什么" —— 那是文案的原料,也是组合时该补的那一维。08-12 那次三个筛选器同时崩(`na_option`)就是在这套里。

---

## 七、三个补充问题(2026-08-17 Andy 追问)

### Monthly Leader 97(原 97 Club)和 Weekly Momentum 97(原 Momentum 97)到底差在哪
*2026-08-17 Andy 定名:预设 **Monthly Leader 97** / **Weekly Momentum 97**,Python 筛选器 `momentum_97` 显示名 **Composite 97**。三个都保留 97(前 3% 同一把尺),前缀说时间窗。*
两个都是"强弱榜",但问的是**两个不同的时间问题**:

| | 97 Club | Momentum 97(预设) |
|---|---|---|
| 条件 | rs_21d ≥97 **且** h_score ≥80 | perf_1w 分位 ≥.97 **且** perf_3m 分位 ≥.85 |
| 问的是 | **近一个月**最强的 3%,而且综合分(行业+3 个 RS 窗口)也高 | **这一周**最强的 3%,而且**这一季**也在前 15% |
| 时间重心 | 一个月 | 一周(+一季做资格) |
| 08-14 命中 | 16 只 | 23 只 |
| 交集 | **3 只** | |
| 97 Club 里这周不在前 3% 的 | **11/16** | —— 说明它抓的是"这个月一直强",不要求这周正在冲 |

一句话:**97 Club = 这个月的领头(可能这周在歇);Momentum 97 = 这周在冲的(可能上个月还平)。** 前者独有 APPS / ESTC / FSLY / NBIS / TEAM / U(月度强、本周未冲),后者独有 ATRO / GRWG / LPTH / NMAX(本周爆、月度分不够)。**它们不是重复,是同一张地图上的两个时刻**;想找"既是本月领头、这周又在动"就取交集(今天 3 只)。
再提醒一次:Python 的 `momentum_97.py`(四窗口等权综合前 3%)是第三个问题,今天 61 只,预设那 23 只全在其中。

### Delayed (Reaction) EP —— Stockbee 的,我们没写过、也没做过
- **是什么**:EP 当天(财报/催化剂跳空 + 巨量)**不进**;因为"不相信第一天的走势会强"。等几天:第 1 天常常冲高回落,3–4 天后市场以为消息消化了、股价往往**还会再往下漂一段**;等它在 EP 日区间里收缩、守住,再在**第二次突破**进场 —— 消息被消化、二级市场增发之类的供给出清之后。他说这个思路"在空头侧也很好用"(反过来:利空 EP 后的反弹做空)。他的 Marketsurge 扫描是分桶的图,正文没给数值;能确定的原则:**入场推迟到 EP 后的整理突破,不是 EP 当天**。
- **它在找什么**:**消息是真的、但第一天的价格已经把它算完了** —— 那之后如果票不跌回去、反而收着,说明有人在接;第二次突破的风险回报比第一天好得多(止损可以放在整理低点,而不是 EP 日的巨大区间下沿)。
- **和普通 EP 的关系**:同一只票、同一个催化剂,**两个不同的入场日**。我们的 `episodic_pivot.py` / Stockbee 9M 预设抓的是第一天;Delayed EP 抓的是第一天之后 3–15 个交易日里的那次突破。
- **我们怎么做(有材料,还没做)**:`data/history/ticker_events.csv` 里存着每一次 `episodic_pivot` 触发(477 条),所以每只票的"距上次 EP 几天"能算出来。Delayed EP 候选 = `days_since_ep ∈ [3, 15]` × 现价仍在 EP 日收盘 ±10% 内(没跌回去)× VCS 上升或 ADR 收窄(在收缩)× 今天 `change_pct` > 0 且 RelVol > 1(第二次突破)。**这是一个"位置 = 相对 EP 日"的新位置项**,配上现有的态,不需要新数据源;工作量:一个 tool + 一列 `days_since_ep`。**2026-08-17 已做**(`pipeline/tools/delayed_ep_scan.py`,阈值可调,纯分类函数有 7 个测试)。四态:`failed`(EP 日低点被击穿)/ `breaking`(守住 + 今天放量阳线突破 EP 后整理高点 = 第二次入场)/ `basing`(守住 + 近 5 日振幅 ≤ EP 日的 60%,观察)/ `drifting`(守住但没收)。**首跑(08-14 数据,财报季 7/28–8/6 那批)**:62 只 —— breaking 1(IOVA)、basing 31、drifting 4、failed 26。三条观察:①**42% 的 EP 在 3–15 天内击穿 EP 日低点** —— 这就是 Pradeep "第一天别进"的数据版;②basing 里 FBRX/ATKR 那种 EP 日振幅 0.3%、之后 0.1% 的,是**并购公告**(EP=deal 消息,价格钉死),不是收缩,读表时看 EPrng%;③"held"用的是"从没击穿 EP 日低点",AXTI/LIFE 那种短暂击穿后大涨的会被判 failed —— 阈值是我们定的,先看几天再调。

### Parabolic Short —— 怎么找候选(教材 M2_L12 有完整一节)
教材的机械定义 + 我们自己的回测(28 只动能股、2020–2026、**83 个事件**):
- **形态**:几个月 5–10 倍;价格**高出 10EMA/20SMA 30–50%**;**RSI(14) > 85–90**;RVOL > 3× 连续数周;冲顶天量收阴(流星/看跌吞没);随后几天**盘中丢 VWAP、反弹一次比一次浅**("坏掉的老虎机")
- **机械代理**:**60 个交易日翻倍 + 高出 20SMA 30%+**
- **回测结论**:正面做空 20 日中位 **−6.8%**、71% 的情况曾逆行 20%+;等首次收盘破 10EMA(V 的右侧)再空 → 中位 **−0.7%**、逆行 20%+ 降到 59%。**两个版本中位都是负的** —— 全课唯一一个机械形态为负的 setup。教材原话:**小白别做。**
- **规则(准备好那天)**:绝不空正面、绝不空阳线;入场分段(① 放量破 VWAP,② 破日低加第二份,Lower High 反弹补进);止损 HOD 或反弹前高;收回 VWAP 立刻出;仓位极小;**先查流通盘和空头持仓**(CAR 2026:$148 → $848,空头一个月亏 $40.9 亿)
- **在我们池子里怎么找候选**(只是"认出它",不是下单名单):
  - 现有字段能做的:`perf_3m ≥ 1.0`(翻倍代理)× `sma20_dist ≥ 0.30` × `atr_from_sma50`(越大越延伸,Steve 的 ≥7 是"开始减"的线)× `rel_volume`、`adr_pct`(RVOL 和振幅) —— **08-14 只有 4 只 $1B+ 满足机械定义**(QMCO / ABCL / UMAC / REPL),没有一只 ATR Matrix ≥7,说明今天没有教科书式抛物线
  - **缺的三样**:RSI(14)(日线可算,一列的事)、**流通盘、空头持仓比**(Finviz Elite 有,免费版没有 —— 这两样恰恰是"能不能空"的第一道闸)。没有后两样,候选名单只能标"形态像",不能标"可做"
  - "V 的右侧"(首次收盘破 10EMA)是当天状态,可以从 `ema10` 列判 —— `close < ema10` 且前一日 `close ≥ ema10`
- **和别的工具的关系**:它是 ATR Matrix 的**上尾**、VCS 的**反面**(极度扩张)、Weekly 20%+ 榜的**极端版**;Sugar Babies 的体质股最容易走成它。**它是持仓者的减仓信号(Steve 的 7–11x 阶梯)远多于是空头的入场信号** —— 教材的结论也是如此。

### Liquid Leaders / True Market Leaders(2026-08-17 追问,已入晨报)
- **Liquid Leaders**:Alex/TradersLab 的核心名单;**我们教材 M2_L09** 定义:ADV ≥2M 股 · 站上 50SMA · RS 排名前 20% → 字段 `liquid_leader`(rs_3m ≥80)。是**资格名单**不是入场。08-14:181 只。
- **Liquid Leader Pullback RS**(教材 L09):liquid leader · 周涨 <12% · 离 21EMA 0.5–1 ADR · 离 50 0–3 ADR(· 5 日对 20 日收缩 · 财报 7 天外 —— 后两条我们读不到,未施加)→ 晨报 entries 区一格。**这就是 21EMA Watch 预设的 ATR 语义**,教材早写对了。
- **True Market Leaders**:教材 M2 第二阶段的名字;业界(Minervini/TraderLion 系)= 技术面 + 基本面 + **所在主题**都在领跑。我们的可测定义:`liquid_leader` × 所属主题/行业四态 = **Leading** × rs_1m ≥80 → 晨报 leaders 区第一格。08-14:26 只(DELL / RBRK / GTLB / NTNX / PATH…);181 只 Liquid Leaders 里 **116 只的所属组在 Weakening** —— 这一维是我们独有的,四家都没有。
- **回测(2026-08-17,价格面板 4,060 只 × 167 日,2026-03→07 九期,每 10 日重选,流动性用今天 ADV≥2M 名单近似)**:Liquid Leader fwd20 中位 **+0.41%** / 赢率 51%;只要 ADV≥2M · >SMA50 是 +0.46%;**只要 ADV≥2M 是 +0.71%**;SPY +2.49%。逐期比"只要流动性"9 期只赢 3 期,6 月底那期 −11.2%。**结论:RS 前 20% 这道闸在这段样本上不加 20 日前瞻收益,回撤期还放大伤害** —— 与 52WH、sequence 两次 NULL 同形状。限制:8 个月一种格局、9 期不独立、生存偏差、无成交量。**所以 Liquid Leaders 是资格名单/水域,不是入场信号,更不是 alpha** —— 教材本来也是这么写的;晨报把它放"谁在领跑"区是对的,当信号用就错。
- **认证方式**:主题四态归档 08-07 才起,TML 那一维历史回测做不了;`data/history/leaders_log.csv` 每晚记一行/只(tml 标志、组态、close),几周后比 TML vs 非 TML 的 Liquid Leaders 的前瞻收益 —— 验的正是"主题那一维值不值钱"。价格口径的 Liquid Leader 本身可回测(价格面板重建中)。

## 五、四家对标的完整体系(压缩版,细节见 `screener_competitors_2026-08-17.md`)

| | 强弱 | 位置 | 状态 | 出场 |
|---|---|---|---|---|
| **Stockbee** | TI65 / DT / MDT;4% 突破;EP 财报 | —(形态肉眼) | 安静日;窄幅;缩量;第 1–3 个 setup | 3 天出一半;+8% 出一半;跳空 20% 全出;止损=突破日低 |
| **oratnek** | RS21>70 & RS63>80 | ATR-from-50SMA <5(理想 <4);LL-HL 结构 1st/2nd | PP 10 日内;VCS(他的另一支) | 5 根内到 2nd 否则清;+25% 落袋;R:R 3 或 ATR≥7 减 33%;收盘破 21EMA Low 清 |
| **Steve Jacobs** | RS ≥97;均线序列 Price≥MA20≥50≥100≥200 | ATR Matrix 0–4 建仓 | ADR 3–6% | 5–7x 持有;≥7x 每整数卖 20% 到 11x;止损 1.5–2 ATR |
| **Alex Desjardins** | 漏斗 500→10–100→0–10;RS 排名 | 20dma>50dma、在 200 上;reversal pivot(下降结构最后一个日线高点) | Liquid Leaders;21dma pullback | LOD 止损;+10–15% 卖半;破 10DMA 卖 1/4;破 21DMA 清 |
| **我们** | RS 百分位(可审计)、TI65/DT/MDT、trend_base | ATR Matrix、ema21_atr_dist、Structure Pivot | VCS v2、PP、ADR、DCR、RelVol、bo_count | (交易端在 IB Order Panel,不在 screener) |

**我们独有的**:主题/行业层(76 个主题带共动性验证、四态、色带、归档)、广度/环境层(15 条件、五档、min-of-voters)、每一个字段可回到代码和测试。**四家都没有的东西不该被四家的框架遮住** —— 组合时记得先问"这票的主题在 Leading 还是 Weakening",那是他们没有的一维。
