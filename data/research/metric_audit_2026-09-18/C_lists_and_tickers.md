# 审计 C：名单层与个股层的判定口径（只读）

- 审计树：`$W` = `/var/folders/ck/n06ysb_13c1367dlllfzn6yw0000gn/T/tmp.wrjtB0Fm5m/wt-audit`，HEAD `30b745bb`（origin/main）
- 输出数据读的是树里 `data/output/`（as_of 2026-09-17）
- 登记表：`$W/data/reference/METRIC_SOURCES.md`（下称 MS）；方法说明：`$W/data/reference/screener_methods.md`（下称 SM）
- 原作者一手核对：WebSearch/WebFetch（Stockbee 博客、TradersLab gitbook、Qullamaggie FAQ、LuxAlgo 的 Morales/Kacher 条目、StockCharts RRG）＋本机课程仓 `~/Documents/SwingMasterclass/`（M2_L09、`_vendor/PrimeTrading/27_Screener_Scans.md`）

---

## 汇总

**项目总数 55**（同一条规则在 panel / preset / 筛子单三处重复出现的，合成一项计）

| 类别 | 数量 | 说明 |
|---|---|---|
| 照抄原文 | **3** | Structure Pivot 五个信号（oratnek Pine 逐行移植）· PP (Vol>10D) 系列（oratnek 口径）· 个股页 technicals（RSI14 / MA / ATR14） |
| 自造·已登记 | **5** | Composite Score 排序 · Extended ≥7 ATR · 名片 ATR 分档与 ATR<7 闸 · 3WT 蓄势席 · 个股页原始 H/I/F 分（登记了，但登记写的是「不上页」，实际上了页） |
| 自造·未登记 | **33** | 闸与展示规则、TML、MA Reclaim、trend_base、Weekly Momentum 97、4% Bullish、Weekly 20%+、六席规则、heat/Confluence、组层四态的辅助量、rotation、七个筛子单里的五个、三个预设、个股页三处标签…… |
| **挂原作者名但有偏离** | **14** | Stockbee 9M Setup · Liquid Leaders · Liquid Leader Pullback · 21EMA Watch 预设 · Episodic Pivot（筛子单＋面板）· VCP · Pocket Pivot（Morales 3+）· Pocket Pivot 预设 · Sugar Babies · Anticipation · asset 层 ATR Matrix · 组层四态（RRG 撞名）· theme_ladder（自称 RRG RS-Momentum） |

**和 thrust 同形状的**（原作者有明确数字/条件，我们改了）：**9 项**，按严重程度排如下。全表里标了 🔴 的是 11 行：其中 #12 就是 #44 的面板版；#46 Sugar Babies 因为找不到一手原文，暂标 🔴 待裁定。
1. **Stockbee 9M Setup**：原文 `v>=8900000` 看的是**当日量**，我们改成了 20 日**均量** ≥9M，另外加了三个条件。另外 MS 第 60 行说「9M 在那个扫描里指 maxv65」，和 2019 年那篇原文对不上。
2. **Liquid Leaders**：Alex 原文的门槛是 $100M/日、≥1M 股、ADR 3–15%、价 >$10、组/主题 RS >50，还剔掉了一批板块。我们的是 ≥2M 股、站上 SMA50、rs_3m≥80，跟原文一条都对不上。代码注释却写着「Alex 和课程教的是同一件事」。
3. **Liquid Leader Pullback**：原文是离 21EMA 0–1×ATR、离 50SMA −0.5–4×ATR、周涨 <15%、DCR >10%、21EMA 上行。我们的是 0.5–1、0–3（而且用的是 Jeff Sun 的 B/A 单位）、<12%，DCR 和 21EMA 上行两条都没有。
4. **21EMA Watch 预设**：来源同上，数字也改了（−0.5–1 / 0–3 / DCR≥20）。
5. **VCP**：Minervini 的定义里「成交量收缩」和「每次约减半」是构成条件，我们只把它们当标记位，不参与筛选。今天 27 只命中里，两条都满足的只有 4 只。
6. **Episodic Pivot**：Stockbee 原文是 `c/c1>1.04 and v>3*avgv50 and v>=300000` 加上 neglect 和改变游戏的财报；Alex 原文是 RVOL>2.5、DCR>20%、距 52 周高点 20% 以内。我们的是收盘涨幅 ≥10%、RVOL≥3、市值 ≥$500M，而 docstring 却写的是「gap」。
7. **Pocket Pivot（面板＋预设）**：Morales/Kacher 要求在 10 日或 50 日均线附近、不能延伸、处在建设性平台里，我们全部去掉了，换成 trend_base。面板上的「3+ in 10D = his cluster」原文里没有这个数。
8. **Anticipation**：Stockbee 三条扫描都要求 `minv3.1>100000`，我们去掉了，换成 $1B/$20M 闸，又加了 vcs≥60、adr≥3。
9. **asset 层 ATR Matrix**：MS 登记的是 Jeff Sun 的 B/A 口径，asset_signals 用的还是 08-24 之前那个被判为 misport 的旧公式，同时注释写的是「same definitions」。

---

## 全表

图例：🔴 = thrust 同形状 · ⚠️ = 撞名/标签错 · 页面组件路径省略前缀 `frontend/src/components/`

### A. watchlist.json（页面：`watchlist/WatchlistPage.jsx`，panel.label 与 panel.recipe 都会显示，见 :643/:688/:783）

| # | 项目 | 输出文件 | 算在哪 | 页面组件 | 条件与数字 | 来源或自造 | 登记状态 | 原文定义与偏离 |
|---|---|---|---|---|---|---|---|---|
| 1 | 全局流动性闸 | watchlist.json | `pipeline/screeners/watchlist.py:38,43,104-108` | WatchlistPage（gate 数显示） | 市值 ≥$1B **且** 均量×价 ≥$20M | 自造（注释：oratnek 原是 1M 股，08-18 改成美元量） | 未登记（MS 登记的 `is_tradeable` 是 $2M，这里的 $20M 是另一把尺子） | 无标准；注释有声明 |
| 2 | ADR 全局下限 3.5（trouble 区豁免） | watchlist.json | `watchlist.py:54,59,81-101` | WatchlistPage | `adr_pct ≥3.5`，缺值放行 | 借来的阈值：`watchlist.py:46` 说是「Stockbee's adr 3.5-10」，MS:58 说是「从 Qullamaggie 借的」，**出处互相矛盾** | 公式 ✅（MS:58）；**阈值未登记** | 查过：[qullamaggie.com/faq](https://qullamaggie.com/faq/) 只给了 ADR 的定义（20 日平均日内振幅），**没给阈值**；Stockbee 的扫描公式里也没有 ADR 3.5 → 按自造处理 |
| 3 | 每格最多 25 只 / 跨区 ≥3 才列 | watchlist.json | `watchlist.py:60,63,515-518` | WatchlistPage | 25 / 3 | 自造（展示规则） | 未登记 | — |
| 4 | chase 标记 | watchlist.json | `watchlist.py:65,289` | WatchlistPage（置灰沉底） | 当日涨幅 ≥15% | 自造（08 月验证） | 未登记 | — |
| 5 | top_3m 标记 | watchlist.json | `watchlist.py:67,283` | WatchlistPage（池开关） | perf_3m 全池百分位 ≥0.85 | 自造（用 3 天 oratnek 页面拟合出来的） | 未登记 | — |
| 6 | rs_high 标记 | watchlist.json | `watchlist.py:277` | WatchlistPage | rs_line_pctl_21 == 100 | 自造标记，建在已登记量之上 | 底层量 ✅（MS:81）；标记未登记 | — |
| 7 | 排序 = Composite Score | watchlist.json | `watchlist.py:298,498`；`run_all.py:501-535` | WatchlistPage、`ticker/TickerStats.jsx:27` | h_score = (2F+3I+1·rs1m+2·rs3m+2·rs6m)/10，再排百分位 | 形状仿 IBD Composite，权重自造 | ✅ 已登记（MS:62，权重声明为自造） | IBD 系数不公开，已声明 |
| 8 | True Market Leaders | watchlist.json | `watchlist.py:152-155` | WatchlistPage；shortlist `new_leader` 席 | liquid_leader ∧ 所属组 state==Leading ∧ rs_1m≥80 | 自造（名字取自课程 Phase 2 的标题） | 未登记 | 查过：课程仓 `00_START_HERE.md:85`、`M2_L08/L09` 的 frontmatter 里只有章节名「Phase 2 · True Market Leaders」，**没有判据** → 无标准 |
| 9 🔴 | **Liquid Leaders**（`liquid_leader`） | watchlist.json / universe | `run_all.py:538-547` | WatchlistPage；个股页「资格」`ticker/tickerReadings.js:112` | 均量 ≥2M 股 ∧ sma50_dist>0 ∧ rs_3m≥80 ∧ tradeable | 挂 **Alex Desjardins / TradersLab** 的名＋课程 M2_L09 | 未登记 | **原文**（[TradersLab · Alex's scans & workflow](https://traderslab.gitbook.io/primetrading/alexs-scans-and-workflow-traderslab)）：「Top RS Rank, Group & Theme RS score > 50, 100mil$/daily liquidity, Minimum 1mil shares avrg. daily volume, 15% > ADR > 3%, Price > 10$, Market cap > $1 Billion」，剔除 China/HK/Biotech/Defensive/Real Estate/Energy/Financials。**偏离**：①流动性 $100M/日 → 我们实际是 $2M（tradeable）或 $20M（面板闸）②1M 股 → 2M 股 ③ADR 3–15 → 只有 ≥3.5 下限、没有上限 ④价格 >$10 → 没有 ⑤Group & Theme RS>50 → 没有 ⑥七类板块剔除 → 没有 ⑦「站上 SMA50」原文里没有，是课程转写时加的 ⑧「RS 前 20%」原文写的是 Top RS Rank（数字没给）。课程本机抄本 `_vendor/PrimeTrading/27_Screener_Scans.md:19-55` 是更早的版本（$250M/日、≥1M 股、>$10B、ADR 2.5–10），也对不上。`run_all.py:541-542` 的注释写着「Alex Desjardins's "Liquid Leaders" and Andy's course teach the same thing」——**这句不成立** |
| 10 🔴 | **Liquid Leader Pullback** | watchlist.json | `watchlist.py:186-191` | WatchlistPage；shortlist `entry`/`v_reversal` 席 | liquid_leader ∧ perf_1w≤12% ∧ ema21_atr_dist 0.5–1 ∧ atr_from_sma50 0–3 | 挂 Alex / 课程 M2_L09 | 未登记 | **原文**（同上链接）：「all Liquid Leaders filters, plus: Daily closing range > 10%, Price contraction (last 5 days), Weekly return < 15%, 0 to 1 x ATR from the 21ema, -0.5 to 4 x ATR from the 50sma, Advancing 21ema, Earnings in 7+ days」。**偏离**：12% ↔ 15%；0.5–1 ↔ 0–1；0–3 ↔ −0.5–4，而且我们的 50 线距离用的是 Jeff Sun 的 B/A（dist%/ATR%，`run_all.py:595-596`），不是原文的「x ATR」；DCR>10% 和 21EMA 上行两条没做。课程版 `M2_L09:135` 写的是「0.5-1× ADR from 21 EMA, 0-3× ADR from 50 EMA」（ADR、EMA50），我们实际用的是 ATR、SMA50。recipe 里只承认缺了「5d/20d 收缩、财报」两条 |
| 11 | MA Reclaim | watchlist.json | `watchlist.py:169-178` | WatchlistPage；`v_reversal` 席 | cross_ema21_up ∨ cross_sma50_up，不设量条件 | 自造（08-20 Andy OK） | 未登记 | recipe 里写明了是自造 |
| 12 🔴 | **Episodic Pivot（面板）** | watchlist.json | `watchlist.py:179-185` | WatchlistPage；`entry` 席的第一候选 | change_pct≥10% ∧ rel_volume≥3，在 $1B/$20M 闸＋ADR≥3.5 之内，**不剔除医疗** | 挂 EP 的名 | 未登记 | 见 #44（同一套配方） |
| 13 | VCS 面板组合 | watchlist.json | `watchlist.py:193-200` | WatchlistPage | vcs≥60 ∧ rs_3m≥80 ∧ >SMA50 ∧ adr≥3 | vcs 本体照抄 oratnek（MS:98 ✅）；组合和 60 这条线是自造（说是取 oratnek「developing」档的边） | vcs ✅；组合未登记 | 60–80 分档出自 SM:79（oratnek 页面），本次没找到一手 |
| 14 🔴 | **Anticipation** | watchlist.json | `watchlist.py:134-147,201-204` | WatchlistPage；`coiling` 席替补 | (ti65≥1.05 ∨ c_low52w≥1.8 ∨ mdt≥1.19) ∧ \|chg\|≤1% ∧ vcs≥60 ∧ adr≥3 | 挂 **Stockbee** 的名 | 未登记（只写在 SM:42-48） | **原文**（[Stockbee: Anticipation scans that can make you lots of money](https://stockbee.blogspot.com/2019/10/anticipation-scans-that-can-make-you.html)）：Double Trouble `c/minl252>=1.8 and minv3.1>=100000`、TI65 `avgc7/avgc65>1.05 and minv3.1>100000`、MDT `c/avgc126>1.19 and minv3.1>100000`，当日涨跌都在 ±1%。三个阈值**一致**；**偏离**：①`minv3.1>100000` 去掉了，换成 $1B/$20M 闸 ②加了 vcs≥60、adr≥3（SM:133 有声明）③原文是三条独立扫描，我们合成一条 OR ④TI65 原文是 `>`，我们用的是 `_ge`（≥），边界值差一点 |
| 15 | PP (Vol>10D) / PP 2+ (10D) | watchlist.json | `watchlist.py:211-216`；`yfinance_adapter.py:530-551` | WatchlistPage | 阳线 ∧ 量 > 前 10 根**全部**的最大量；10 日内 ≥2 次；都要 trend_base | 照抄 oratnek（自述），叠加的 trend_base 是自造 | MS:79 注明它和 pocket_pivot 是两个量 | ⚠️ 标签「PP」是 Pocket Pivot 的通用缩写，但算的不是 Morales 的量（SM:95 有说明，页面上没有） |
| 16 🔴 | **Pocket Pivot (Morales, 3+ in 10D)** | watchlist.json | `watchlist.py:217-220`；`yfinance_adapter.py:554-578` | WatchlistPage（中文标签 `i18n/translations.js:457` 写的是「Morales 口径，10 日」，**「3+」被丢了**） | 上涨日量 > 前 10 根下跌日的最大量；10 日内 ≥3 次；trend_base | 挂 **Gil Morales / Chris Kacher** 的名 | 核心判定 ✅（MS:79）；「3+」和语境条件未登记 | **原文**（Morales & Kacher《Trade Like an O'Neil Disciple》2010，转引 [LuxAlgo](https://www.luxalgo.com/library/concept/pocket-pivot/)）：「price is at or moving up through SMA_10 (or SMA_50) … and not extended above those averages」，并且排除「extended above its base or moving average … below a declining 50-day line … right after a climactic advance」的信号。**偏离**：①均线附近/不延伸/建设性平台这些条件全没做，只拿 trend_base（>SMA50 ∧ 周 10>30）代替 ②recipe 写着「three in ten sessions is his 'cluster'」——查过，Morales 原文只说 cluster 比单个信号更有意义，**没给次数**，3 是我们定的，却记在了他名下 |
| 17 | trend_base | universe → 6 个预设＋3 个面板 | `yfinance_adapter.py:1114-1122` | 个股页「资格」、所有 trendBaseOnly 预设 | close>SMA50 ∧ 周收盘 10 周均 > 30 周均（简单均线） | 自造；SM:33 自称「Stan Weinstein 式 Stage 2 闸」 | 未登记 | Weinstein 原书看的是 30 周均线的斜率＋价格和它的相对位置（MS:96 已登记为 🔲 没做）；10/30 交叉**不是**他的判据。变量名 `wma10/30` 里的 W 指 weekly，不是加权 |
| 18 | Weekly Momentum 97（面板＋预设＋universe 的 `momentum_97` 列） | watchlist.json / preset / universe | `watchlist.py:222-226`；`run_all.py:637-644`；preset `screener-presets.json:98` | WatchlistPage、Screener 预设、个股页「资格: momentum 97」 | perf_1w 全池百分位 ≥0.97 ∧ perf_3m 百分位 ≥0.85 ∧ trend_base ∧ ADR 3.5–10 ∧ 非医疗 | 自造（反推拟合 oratnek 的截图，`watchlist.py:417-428` 至今还留着 shadow 对照） | 未登记 | 查过：「Momentum 97」检索不到公开口径（Deepvue/Qullamaggie 页面只写「top 1–2% performers over 1–6 months」，[Deepvue](https://deepvue.com/screener/qullamaggie-screens/)）→ 无标准 |
| 19 | 4% Bullish（面板＋预设） | watchlist.json / preset | `watchlist.py:227-232`；preset `:42` | WatchlistPage、Screener | chg≥4% ∧ rel_volume≥1 ∧ from_open≥0 ∧ rs_21d≥60 ∧ ADR 3.5–10 ∧ 非医疗 | 自造；SM:166 说原型是「Stockbee 4% 突破」 | 未登记 | 名字里没挂作者，但 SM 里挂了。Stockbee 原文是 `c/c1>=1.04 and v>v1 and v>=100000`（[How I get the Market Monitor Numbers](https://stockbee.blogspot.com/2014/08/how-i-get-market-monitor-numbers.html)）：我们把 v>v1（比昨天放量）换成了 rel_volume≥1（比均量），v≥100k 没有 |
| 20 | Weekly 20%+ Gainers（面板≠预设） | watchlist.json / preset | `watchlist.py:233-238`；preset `:222` | WatchlistPage、Screener | 面板：perf_5d≥20%（5 个交易日）；预设：perf_1w≥20%（自然周） | 自造 | 未登记 | ⚠️ **同名两套口径**（recipe 里自己承认了）。Stockbee 的 momentum burst 是「3–5 天 8–20%」（[Stockbee 2017-07](https://stockbee.blogspot.com/2017/07/swing-trading-using-momentum-burst.html)），和这个不是同一个量 |
| 21 | Extended ≥7 ATR | watchlist.json | `watchlist.py:246-248` | WatchlistPage | atr_from_sma50≥7 | 已登记 | ✅ MS:80 | ⚠️ 标签写的是「Jacobs's scale-out zone」，MS:80 却说 ≥7× 出自 @TradeDudeNYC、「不是 Weinstein 原书」——**出处写法不一致** |
| 22 | LL-HL 1st/2nd/Trend Line Break、Stop Hit、LL Break | watchlist.json | `watchlist.py:160-168,240-245`；`structure_pivot.py` | WatchlistPage | sp_signal ∈ {1st_break, 2nd_break, counter_break, stop_hit, ll_break} | 照抄：逐字移植 `indicators/third_party/oratnek_advanced_structure_pivot.pine`（黄金对照 5/5） | **未登记**（MS 只在撞名机制里提了 `sp_phase`） | 一致。小问题：`structure_pivot.py:36-38` 说 oratnek 的 ATR% 50SMA「和我们的 atr_from_sma50 单位略有不同」，08-24 我们已经切到同一个 B/A 形式，**这句注释过期了** |

### B. shortlist.json（页面：`watchlist/shortlist/ShortListPage.jsx`、`NameCard.jsx`）

| # | 项目 | 输出文件 | 算在哪 | 页面组件 | 条件与数字 | 来源或自造 | 登记状态 | 原文定义与偏离 |
|---|---|---|---|---|---|---|---|---|
| 23 | 六席规则与替补链 | shortlist.json | `pipeline/screeners/name_cards.py:33-40,177-350` | ShortListPage | burning＝heat 前 50 里排最高；new_leader＝今日新进 TML，否则 ATR 位最低；entry＝今日 EP 按 rel_volume，否则 Leading 组里的 LL 回踩；v_reversal＝52wh≤60 天且回撤 3–20%（缺字段时用 ≥−15% 代理），深 V ≤−25%；asset＝RS 线 21 日=100 ∧ 20 日新高 | 自造（Andy 08-20 定的规则） | 未登记 | — |
| 24 | ATR<7 全席闸 ＋ 名片判词分档 | shortlist.json | `name_cards.py:201-203,96-105` | NameCard | <0 为 50 线下；≤4 建仓区；<7 持有区；≥7 减仓区 | 借 ATR Matrix | ✅ MS:80 | Jacobs 的分档是 0–4 / 5–7 / ≥7（SM:56），我们把 4–5 并进了「持有」，小偏离 |
| 25 | 「Sugar Babies 名册 ≥5 连＝反指」 | shortlist.json（verdict） | `name_cards.py:111-112` | NameCard | roster_streak≥5 | 自造 | 未登记 | — |
| 26 | coiling 席 · 3WT | shortlist.json | `name_cards.py:311-330` | ShortListPage | three_weeks_tight ∧ >SMA50 ∧ high_52w≥−15% | 3WT 照抄 IBD；额外两条是自造 | 3WT ✅（MS:64）；额外条件未登记 | ⚠️ 席位说明写「周K三连1.5%带」——「带」描述的是 `wk_band_3`（全域带宽）的语义，MS:64-65 刚把这两个区分开 |
| 27 | coiling 席 · 日线 coil | shortlist.json | `name_cards.py:318-320` | ShortListPage | range5_pct≤5 ∧ dist_hi20_pct≥−3 ∧ >SMA50 ∧ 过闸 | 自造 | 未登记 | — |
| 28 | legend（EP / 4% / NH+RS / x21 / x50） | shortlist.json | `shortlist.json.legend` | NameCard 图上标记 | EP「≥10%×量≥3×」；4%「≥4%×量≥1」；NH+RS「20 日新高＋RS 线新高同日」 | 自造 | 未登记 | EP 的问题同 #44 |

### C. groups.json / groups_history.json / theme_ladder.json / rotation.json

| # | 项目 | 输出文件 | 算在哪 | 页面组件 | 条件与数字 | 来源或自造 | 登记状态 | 原文定义与偏离 |
|---|---|---|---|---|---|---|---|---|
| 29 ⚠️ | **组四态 Leading/Weakening/Improving/Lagging** | groups.json、groups_history.json | `pipeline/themes/rs_engine.py:181-191`（classify）、`:124-141`（rs_accel） | `groups/GroupsPage.jsx`、`StateField.jsx`、`GroupTable.jsx`；TML 与 market_light 都读它 | excess_3m>0 × rs_accel>0，rs_accel ＝ 近 1 月超额 − 前 2 月**总**超额（窗口不等长） | 自造（内部验证 V4，见 FOUR_STATE_DESIGN.md） | **未登记** | 四个名字**原样沿用了 JdK Relative Rotation Graph 的四个象限**。原文（[StockCharts ChartSchool · RRG](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-types/relative-rotation-graphs-rrg-charts)）：「leading quadrant … when RS-Ratio and RS-Momentum are above 100」，两条轴都是 de Kempenaer 的专有归一化指标。我们的横轴是 3 月原始超额，纵轴是二阶加速度 → 口径不同，名字相同，按 MS 撞名规则应当改名或登记偏离 |
| 30 | rs_accel_rate / persistence / ext_share_4·7 / 组规则 | groups.json | `rs_engine.py:160-178`、`:208-247`（前 25% × 5 个周期）、`:366-388`（≥4、≥7 ATR 的占比）、`:402`（≥5 只成员）、`:72`（丢掉 >500% 的读数） | GroupTable（Persist 方块）、StateField | 同左 | 自造 | 未登记 | — |
| 31 ⚠️ | **theme_ladder 2w–10w 四态** | theme_ladder.json | `pipeline/themes/short_window.py:42-50,67-80,90-118` | `rotation/RotationPage.jsx`（`useThemeLadder`） | 窗口 (L,M) ＝ (10,5)(20,10)(30,15)(40,20)(50,25)；等权篮子，≥3 只；动量＝M 日超额（一阶） | 自造（为了对上 Clement_Ang17 的看板） | 未登记 | docstring `:17,94` 写着动量是「RRG RS-Momentum」。但 RRG 的 RS-Momentum 是 RS-Ratio 的变化率，并且归一到 100，我们的是原始超额。另外**同一组四个名字在 Groups 页用二阶加速度，在 Rotation 页用一阶超额**，两页的 Leading 不是同一个定义；`WINDOWS["3m"]=(63,21)` 的注释说它是「the validated … board (rs_engine)」，但算法和 rs_engine 不同 |
| 32 | lagging_share / d5 canary | theme_ladder.json | `short_window.py:190-202` | RotationPage | Lagging 占比及其 5 日变化 | 自造（payload note 自认「未证实」） | 未登记 | — |
| 33 | rotation 三刀投票 | rotation.json | `pipeline/rotation/baskets.py:53-75`、`engine.py:32-35,118-200` | `breadth/RotationPanel.jsx`、`shared/StateRibbon.jsx` | SPHB/SPLV、IVW/IVE、(IPO,IWC,ARKK)/(XLV,XLP)；2 周价差的符号投票＋月度确认；ribbon 用 rs_engine classify (63,21) | 自造 | 未登记 | 查过，无标准（风格篮子 risk-on/off 没有公认的合成口径） |

### D. heating_up.json / ticker_events.json / asset_signals.json

| # | 项目 | 输出文件 | 算在哪 | 页面组件 | 条件与数字 | 来源或自造 | 登记状态 | 原文定义与偏离 |
|---|---|---|---|---|---|---|---|---|
| 34 | heat 分 / Confluence 扫描 | heating_up.json | `pipeline/screeners/ticker_heat.py:35-61,64-111` | `screener/ScreenerPage.jsx:82,159`（**默认扫描**就是 Confluence）；shortlist `burning` 席 | 权重 EP/VCP/M97=3，其余=1；窗口 15 日；同一筛子重复一次 ×0.25，封顶 1.5；同日 ≥4 个筛子 +2.0；取前 50 | 自造 | 未登记 | —（QUALITY 集合 `ticker/TickerSignalHistory.jsx:47` 和这组权重对应） |
| 35 🔴 | **asset 层 ATR Matrix** | asset_signals.json | `pipeline/screeners/asset_signals.py:87` | 不直接上页；喂 shortlist `asset` 席的 ATR<7 闸 | (close−SMA50)/ATR | 挂 ATR Matrix（Jacobs / Jeff Sun）的名 | MS:80 ✅ 登记的是**另一个公式** | 股票侧 08-24 已改成 Jeff Sun 的 B/A = dist%/ATR%（`run_all.py:590-598`，MRNA 旧 5.2 → 新 11.2），asset 侧还是旧公式；`:114` 的 note 却写着「same definitions as universe rows … atr_from_sma50 is the ATR Matrix position」。另外 `high_52w_dist` 在这里是 1 年**最高收盘**（`:89`），股票侧用的是最高价 |
| 36 | asset hi20 | asset_signals.json | `asset_signals.py:88` | asset 席 | close ≥ 20 日最高收盘 | 自造 | 未登记 | — |

### E. 七个筛子单（页面：`screener/ScreenerPage.jsx` 扫描条 `lib/scanSets.js:15-25`；个股页 `ticker/TickerSignalHistory.jsx:28-44`；`screeners/ScreenersSection.jsx` 没有任何地方 import，是死组件）

| # | 项目 | 输出文件 | 算在哪 | 页面组件 | 条件与数字 | 来源或自造 | 登记状态 | 原文定义与偏离 |
|---|---|---|---|---|---|---|---|---|
| 37 | 5 个筛子的市值地板 | 5 个 json | `pipeline/screeners/universe_gate.py:32-40` | — | 市值 ≥$1B，缺值视为不过 | 自造（09-18 Andy「市值这个闸是要加上的」） | 未登记（代码里有声明） | — |
| 38 ⚠️ | momentum_97.json「Composite 97」 | momentum_97.json | `pipeline/screeners/momentum_97.py:44-149` | 扫描条标签「**Composite 97**」（`scanSets.js:18`、`TickerSignalHistory.jsx:40`） | 4 个百分位（1w/1m/3m/6m）等权平均 ≥ 第 97 百分位；分桶 100/99/98/97 | 自造 | 未登记 | ⚠️ **同名三义**：①这个文件（等权复合）②universe 的 `momentum_97` 列（1w≥.97 ∧ 3m≥.85，`run_all.py:644`，个股页「资格」显示的是它）③「Weekly Momentum 97」面板/预设。页面标签「Composite」又和 Composite Score（h_score_pctl）、IBD Composite Rating 撞名。docstring `:23` 还在引用已改名的 `rs_ibd` |
| 39 | gainers_4pct | gainers_4pct.json | `gainers_4pct.py:30,58` | 扫描条「4% gainers」 | chg≥4%，不设量条件 | 自造 | 未登记 | docstring `:15-17` 说它是「input to the Stockbee breadth ratio」。Stockbee 的 4% 计数要求 `V>V1 AND V>=100000`（v12.4），这里没有 |
| 40 | vol_up_gainers ≠ 预设「Vol Up Gainers」 | vol_up_gainers.json / preset | `vol_up_gainers.py:29,32,60-62`；preset `:75` | 扫描条「Vol-up」、Screener 预设 | 文件：chg≥4% ∧ rvol≥1.5；**预设：chg≥0%** ∧ rvol≥1.5 ∧ ADR 3.5–10 | 自造 | 未登记 | ⚠️ 同名两个定义 |
| 41 ⚠️ | ema21_watch | ema21_watch.json | `ema21_watch.py:32-33,99-116` | 扫描条「EMA21」、「21 EMA watch」 | **sma20_dist** 在 −2%..+3% ∧ >SMA50 ∧ >SMA200 ∧ perf_3m 百分位档 ≥80 | 自造 | 未登记 | 名字叫 EMA21，算的是 SMA20（docstring 自称「~90% proxy」），可 universe 里早就有真的 `ema21` / `ema21_atr_dist`。和同名的「21EMA Watch」预设（#47）是两个东西 |
| 42 | healthy_charts | healthy_charts.json | `healthy_charts.py:35-45,126-146` | 扫描条「Healthy charts」 | >SMA50 ∧ >SMA200 ∧ 距 52 周高 −25%..−5% ∧ perf_1m>0 ∧ rvol≥0.5 ∧ perf_3m 档 ≥80 | 自造（有一部分像 Minervini TT 的第 7 条） | 未登记 | — |
| 43 🔴 | **VCP** | vcp.json | `vcp_detector.py:54-77`（L1）、`:85-164`（L2） | 扫描条「VCP」；TickerSignalHistory QUALITY；heat 权重 3 | L1：close>$10 ∧ 市值≥$1B ∧ >SMA50 ∧ >SMA200 ∧ 距 52 周低 ≥30% ∧ 距 52 周高 ≤25% ∧ perf_1m>0 ∧ \|1w\|<\|1m\|；L2：90 天、5 根 swing、≥2 次收缩、最近 4 次深度不增、pivot 距离 −2..+10%；**`ratios_healthy`（0.3–0.75）和 `volume_declining` 只算不筛** | 挂 **Minervini** 的名（docstring「Minervini's pattern, not ours」） | MS:97 只有一行「拟 `vcp_contractions` ⚠️」——**已经在页上发布的 vcp.json 没登记** | **原文**（Minervini《Trade Like a Stock Market Wizard》2013；MS:97 已转述）：2–6 次逐次变浅的回撤、每次约为前一次的一半、**成交量随之收缩、末端 volume dry-up**、放量突破 pivot。Trend Template（[Deepvue 转引](https://deepvue.com/screener/minervini-trend-template/)）8 条：价 >150/200 日均线、150>200、200 日线上行 ≥1 个月、50>150/200、价 >50、距低 ≥30%、距高 ≤25%、**IBD RS≥70**。**偏离**：①量缩和减半是 VCP 的构成条件，我们不筛——**今天 27 只里 volume_declining 只有 9 只，ratios_healthy 只有 10 只，两者都满足的 4 只** ②TT 缺 150 日均线、200 日上行、RS≥70；多了 $10、$1B、1w/1m 比较 ③收缩次数没设上限 6（今天有 1 只是 6 次）④90 个日历日窗口，原文的平台可以长达数十周 ⑤pivot 距离窗口是自造的 |
| 44 🔴 | **Episodic Pivot** | episodic_pivot.json | `episodic_pivot.py:31-33,65-69` | 扫描条「EP」、TickerSignalHistory、heat 权重 3、`entry` 席 | change_pct≥10% ∧ rel_volume≥3 ∧ 市值≥$5亿 | 挂 EP 的名（SM:217 说是「Stockbee 9M 的另一种写法」） | 未登记 | 三份原文，没有一份和我们一致：**Stockbee**（[My process flow for EP, 2014-07](https://stockbee.blogspot.com/2014/07/my-process-flow-for-episodic-pivots-ep.html)）「c/c1>1.04 and v>3*avgv50.1 and v>=300000」，另加 neglect＋改变游戏的财报；**Qullamaggie**（[How to master a setup: EP](https://qullamaggie.com/how-to-master-a-setup-episodic-pivots/)）开盘跳空 ≥10%、开盘后放出巨量；**Alex**（TradersLab，同 #9 的链接）「ADR > 3%, Price > 5$, Market cap > 500mil$, Daily return > 10%, Daily closing range > 20%, 20% from 52w high, Relative Volume > 2.5 … 20mil$/daily liquidity, Minimum 1mil shares」。**偏离**：①docstring 写 gap，代码算的是收盘涨幅（close/prev close），不是开盘跳空 ②RVOL 3 ↔ 2.5（Alex）/ 3×avgv50（Stockbee 相当于 3，而且他的涨幅门槛只有 4%）③DCR>20%、距 52 周高 20% 以内、价 >$5、ADR>3、流动性，全都没做 ④没有催化剂和 neglect 条件（数据端做不到，可以理解，但要写明） |

### F. 预设 `frontend/public/data/screener-presets.json`（页面：Screener 预设；`pipeline/screeners/preset_hits.py` 每晚按同一口径回放进 ticker_events）

| # | 项目 | 输出文件 | 算在哪 | 页面组件 | 条件与数字 | 来源或自造 | 登记状态 | 原文定义与偏离 |
|---|---|---|---|---|---|---|---|---|
| 45 🔴 | **Stockbee 9M Setup** | preset（+ticker_events） | `screener-presets.json:146`；`lib/screenerFilter.js:25-28`；`preset_hits.py:108-111` | Screener | `vol50dMin 9`（实际比较的是 `avg_volume`，**20 日**均量，见 `pipeline/themes/__init__.py:36-43`）∧ relVol≥1.5 ∧ 日涨≥5% ∧ DCR≥60 ∧ 市值≥$1B ∧ 非医疗 | 挂 **Stockbee** 的名 | 未登记 | **原文**（[Stockbee: Simple scan that can make you millions, 2019-09](https://stockbee.blogspot.com/2019/09/simple-scan-that-can-make-you-millions.html)）：「v>=8900000」——**当日**成交量，只有这一条。**偏离**：①当日量 → 20 日均量（定义量被换了；键名 `vol50dMin` 还把 20 日写成了 50 日）②另加了 relVol≥1.5、+5%、DCR≥60、$1B、剔医疗 ③MS:60 称「9M … 在那里指 `maxv65` 不是当日量」，**和这篇原文对不上**，需要回头核实 MS:60 那句话的出处 |
| 46 🔴 | **Sugar Babies** | preset | `screener-presets.json:170`；bo_count 在 `yfinance_adapter.py:60-95,1179-1184` | Screener | bo_count_1y≥10 ∧ bo_count_3m≥2；每一次「bo」＝chg≥4% ∧ v>v1 ∧ v>100k（09-04 起） | 挂 **Stockbee** 的名 | 判定 ✅（MS:60）、聚合 ⚠️ 自造（MS:61）；**10/2 两个阈值未登记** | 查过：Stockbee 博客检索不到 sugar babies 的一手定义（搜「stockbee blogspot "sugar babies"」只有 bootcamp 帖和他的推文 [x.com/PradeepBonde/status/1752165304736645393](https://x.com/PradeepBonde/status/1752165304736645393)，都没给公式）。社区复刻（[TradingView · QuadrantLower](https://www.tradingview.com/script/GUmWmvZn-Stockbee-Sugar-Babies-Pine-Screener-by-QuadrantLower/)）写的是「4%+ breakouts with institutional volume (9M+ on the day)」。也就是说 09-04 把 9M 换成 100k 这次「修正」，对 Sugar Babies 这个**名字**来说可能是改反了——需要找一手来源裁定。SM:111、SM:197 仍写「量 ≥9M」，和代码不一致 |
| 47 🔴 | **21EMA Watch** | preset | `screener-presets.json:3` | Screener | ema21_atr −0.5..1 ∧ sma50Atr 0..3（B/A）∧ 周涨 0–15 ∧ DCR≥20 ∧ pp_count_30d≥1 ∧ ADR 3–6 ∧ trend_base ∧ $1B ∧ 非医疗 | 来源是课程 M2_L09 / Alex（SM:263 写着「这就是 21EMA Watch 预设的 ATR 语义」） | 未登记 | 和 Alex 原文（#10）比：0–1 ↔ −0.5–1；−0.5–4 ↔ 0–3；DCR>10 ↔ ≥20；周 <15 一致；21EMA 上行、5 日收缩、财报三条没做；ADR 上限 6 是 Steve 的（SM:88） |
| 48 | Monthly Leader 97（SM 里叫「97 Club」） | preset | `screener-presets.json:122` | Screener | **hScore（原始 h_score）** 80–99 ∧ rs21d 97–99 ∧ ADR 3.5–6 ∧ trend_base | 自造；SM:185 说原型是「IBD 的 RS 97+ 俱乐部」 | 未登记 | 阈值打在原始 h_score 上，而 MS:63 说原始 h_score「不是百分位、不上页」——80 这条线等于顶档 1% 左右，读起来却像「前 20%」 |
| 49 | Pocket Pivot 预设 | preset | `screener-presets.json:188` | Screener | pocket_pivot 当日 ∧ trend_base ∧ ADR 3.5–6 | 挂 Morales 的名 | 核心 ✅ MS:79 | 语境条件缺失，同 #16。SM:203 写「我们比全部 10 根（更严，已知偏离）」——**过期了**，代码 08-17 起比的是下跌日 |
| 50 | PP Count 预设 | preset | `screener-presets.json:203`；`preset_hits.py:42`（ppCount→`pp_count_30d`） | Screener | 30 日内 Morales PP ≥3 ∧ trend_base ∧ ADR 3.5–6 | 自造阈值 | 未登记 | 面板用的是「10 日 ≥3」（#16），预设用的是「30 日 ≥3」，同一个「3」配了两个窗口 |

（4% Bullish、Weekly Momentum 97、Weekly 20%+、Vol Up Gainers 四个预设已并进 #19、#18、#20、#40）

### G. 个股页（`tickers/*.json` ＋ universe 行；抽看了 AA/AAOI/AAPU，结构相同：`technicals / ohlc / options_implied_move / ai_synthesis / news …`）

| # | 项目 | 输出文件 | 算在哪 | 页面组件 | 条件与数字 | 来源或自造 | 登记状态 | 原文定义与偏离 |
|---|---|---|---|---|---|---|---|---|
| 51 | technicals（rsi14 / ma20/50/200 / atr14 / 52 周位置） | tickers/*.json | `pipeline/tickers/ticker_data_fetcher.py` | `ticker/TickerTrendIndicators.jsx`、`TickerKeyLevels.jsx` | 标准量 | 照抄（Wilder RSI/ATR），这次没有逐行复算 | 未单独登记 | — |
| 52 ⚠️ | TickerStats 三处标签/显示错误 | universe → 个股页 | `ticker/TickerStats.jsx:24,34,35` | TickerStats | ①「Avg Vol (50D)」显示的是 avg_volume，而它实测是 **20 日**均量 ②「Dist 20EMA%」显示的是 **sma20_dist** ③「52W High%」对小数直接 `.toFixed(1)%`，**没乘 100**：NVDA 的 high_52w_dist=−0.0706，页面显示「−0.1%」 | 显示层问题 | — | 标签和量不一致；③ 是实打实的 bug |
| 53 | 「H / I / F 分」显示原始 h_score | universe → 个股页 | `ticker/tickerReadings.js:115-116` | TickerTrendIndicators / Provenance | 原始 h_score | — | MS:63 写的是「保留仅为归档连续性，**不上页**」 | 登记和实际相反 |
| 54 ⚠️ | 「资格: momentum 97」 | universe → 个股页 | `tickerReadings.js:112-114` | 同上 | universe 的 momentum_97 列（1w≥.97 ∧ 3m≥.85） | 自造 | 未登记 | 和扫描条上的「Composite 97」不是同一个定义，见 #38 |
| 55 | RS 21D / RS 63D 标签 | universe → 个股页 | `TickerStats.jsx:28-29`；`run_all.py:396-416` | TickerStats | 实际是自然月的 perf_1m/perf_3m 在 tradeable 池内的百分位 ×99 | 自造（形状仿 IBD） | 部分登记（MS:76 登记的是 rs_rating） | `run_all.py` 的注释自己承认「these say sessions and mean calendar months」，页面上还在用 21D/63D 这两个名字 |

---

## 最该处理的前 10 个

1. **#45 Stockbee 9M Setup**：挂着作者名，但定义量被换掉了——原文是当日 `v>=8900000`，我们用的是 20 日均量，另外加了三个条件。而且 MS:60 的「maxv65」说法和原文冲突，登记表本身可能写错了。这和 thrust 是同一种错。
2. **#9 Liquid Leaders**：Alex 原文的七项门槛（$100M/日、1M 股、ADR 3–15、>$10、组/主题 RS>50、板块剔除）一条都没对上，代码注释却写着「教的是同一件事」。它还往下喂 TML、new_leader 席和 leaders_log 研究。
3. **#43 VCP**：页面上叫 VCP，可 Minervini 的两个构成条件（量缩、逐次减半）只标不筛，今天 27 只里只有 4 只真满足；登记表把 VCP 列为「拟」，实际早就上页了，而且在 heat 里权重是 3。
4. **#44 Episodic Pivot**：说的是 gap，算的是收盘涨幅；三份原文（Stockbee / Qullamaggie / Alex）没有一份对得上，却是 entry 席的第一候选，heat 权重也是 3。
5. **#10 / #47 Liquid Leader Pullback 与 21EMA Watch 预设**：Alex 给了精确的 ATR 带（0–1 / −0.5–4 / 周<15 / DCR>10），我们三处改了数字、把单位换成了 B/A，还漏掉了 21EMA 上行；recipe 只承认漏了两条。
6. **#29 / #31 四态撞 RRG**：Leading/Weakening/Improving/Lagging 是 JdK RRG 的象限名，而我们在 Groups 页和 Rotation 页用的还是两套不同的公式，都没登记——正是 MS 撞名规则要管的情况。
7. **#38 / #54 「Composite 97」同名三义**：一个 momentum_97 有三个定义，页面标签又撞上 Composite Score 和 IBD Composite，用户在扫描条和个股页看到的「97」不是同一件事。
8. **#16 / #49 Pocket Pivot**：「3 次＝Morales 的 cluster」原文里没有；原文要求的均线附近/不延伸语境全被 trend_base 替掉；中文标签还把「3+」丢了。
9. **#46 Sugar Babies**：社区复刻的定义要求 9M 当日量，09-04 被改成了 100k 的 4% 突破计数，一手来源没找到，需要 Andy 或原文来裁定；10/2 两个阈值没登记，SM 文档和代码也不一致。
10. **#52 / #53 个股页显示错误**：52W High% 少乘了 100（真实 −7.1%，显示 −0.1%）、「50D」实际是 20 日、「20EMA」实际是 SMA20，原始 h_score 违反登记上了页。都是一行就能修的，而且眼下就在误导读者。

（紧接着的：#35 asset 层 ATR Matrix 还在用旧的 misport 公式，却自称「same definitions」；#41 ema21_watch 叫 EMA21 却算 SMA20；#34 heat/Confluence 是 Screener 的默认扫描，却整套没登记。）

---

## 越界顺带（不在本线范围，只记下来）

- `pipeline/screeners/stockbee_ratio.py:37-41,147-148`：「Stockbee 5-day ratio」的分子只看 change_pct，没有 `V>V1 AND V>=100000`；阈值 3.0/0.5 也没核实出处。前端没有读者，归广度线。
- `data/reference/screener_methods.md` 有三处过期：:88 ADR 还写成 ATR/close；:111 和 :197 的 bo_count 还写着 9M；:203 的 Pocket Pivot 还写着「比全部 10 根」。
- `frontend/src/components/screeners/ScreenersSection.jsx` 没有任何地方 import。
- `pipeline/screeners/structure_pivot.py:36-38` 的单位注释在 08-24 之后已经过期。
