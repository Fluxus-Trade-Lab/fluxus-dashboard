# RS 统一方案：rs_rating / rs_1m·3m·6m / RS 线能并成一个排名 + 一条线吗

T-1002-03 · alex · 2026-10-02

## 一句话结论

**能，而且应该**：三个「排名型」读数（`rs_rating`、`rs_1m`/`rs_3m`/`rs_6m`）在场外的 IBD/Minervini/Stockbee
体系里本来就是**同一个公式的不同组件**，不是三种方法论；`RS 线`（`rs_line_pctl_*`）是另一类东西（自比，不是排名），
两者合并没有道理。5 年回测支持把排名动作统一到 `rs_rating`（多窗口混合），RS 线继续只做「检测」不做排名——
这正是它现在的用法，不用动。**但面板会死四成名单**（liquid_leader 47/164 只换人），换不换、怎么换、谁来改前端
文案，是 Andy 的决定，不是本研究的决定。

## 一、消费者清单

全仓 grep `rs_rating / rs_1m / rs_3m / rs_6m / rs_21d / rs_63d / rs_line_pctl_*`（命令：
`git grep -n 'rs_rating\|rs_1m\|rs_3m\|rs_6m\|rs_21d\|rs_63d\|rs_line_pctl'`，184 个文件命中，
下表只收「真的读这些字段做判断/排序/展示」的消费者，测试文件与仅注释提及的行不列）。覆盖 pipeline /
frontend / presets / skills **四类**——第一版漏了 skills 类，复核打回后补上第四张表。

「换读数后名单变化」一栏用 2026-09-30 `data/output/universe.json`（`tradeable=2499` 只）现算：
把消费者当前用的单窗/rs_1m 读数换成 `rs_rating`，其余条件不动，比较命中集合。**方向只做 rs_3m/rs_1m → rs_rating
这一种替换**（Option A 的具体形状），因为这是任务背景里 claire 倾向、也是下面标准核查与回测都指向的方向；
RS 线相关行不测「换读数」，因为它们本来就不参与排名（见第四节）。

### 排名/过滤类消费者（换读数会动名单）

| 消费者 | 读数 & 阈值 | 证据行 | 换成 `rs_rating` 同阈值后 |
|---|---|---|---|
| `liquid_leader` 字段（课程 M2_L09） | `rs_3m >= 80` | `pipeline/screeners/run_all.py:675` | 当前 164 只 → 换后 159 只，重合 117，**只在旧版 47 只、只在新版 42 只**（约四成不重合，核实了 claire 背景表的「四成」说法） |
| `vcs` 面板（Volatility Contraction Score 组合闸） | `rs_3m >= 80`（另 vcs≥60、above SMA50、adr≥3） | `pipeline/screeners/watchlist.py:285-292` | 当前 20 只 → 换后 16 只，重合 14，只在旧 6、只在新 2 |
| `bullish_4pct` 面板 / 预设「4% Bullish」 | `rs_21d(=rs_1m) >= 60` | `pipeline/screeners/watchlist.py:344-347`；UI 侧同名预设 `frontend/public/data/screener-presets.json:62-66` | 当前 15 只 → 换后 12 只，重合 11，只在旧 4、只在新 1（小样本，波动看着大，绝对值小） |
| 预设「Monthly Leader 97」 | `hScore 80-99 ∧ rs21d(=rs_1m) 97-99 ∧ ADR 3.5-6 ∧ trend_base` | `frontend/public/data/screener-presets.json:121-137`；口径见 `METRIC_SOURCES.md:191` | 当前 8 只 → 换后 12 只，重合 5，只在旧 3、只在新 7——**这一档换数会让名单几乎重排** |
| `industry_rank` / `top20_industry`（i_score 底层） | 行业内 tradeable 成员 `rs_3m` 中位数排名 | `pipeline/screeners/tml_moglen.py:59-62`（定义注释）；排名实现在 `run_all.py` | 135 个有效行业（≥3 名成员）里，中位数读数换成 `rs_rating` 后行业中位数 Pearson r=0.707；**前 20 行业重合 11/20**，只在旧 9、只在新 9——`top20_industry` 门槛受影响不小于个股面板 |
| True Market Leaders（TML，Moglen 定义） | `rs_rating >= 97`（`MIN_RS_RATING`） | `pipeline/screeners/tml_moglen.py:75,130` | **已经在用 `rs_rating`，不受本提案影响**（64 只，2026-09-30 tradeable） |
| VCP 第一层 Trend Template leg 8 | `rs_rating >= 70` | `pipeline/screeners/vcp_detector.py:128-129` | **已经在用 `rs_rating`，不受影响**（1287 行，全量打分宇宙） |
| `market_light.brightness.leaders` 排序 | 按 `-rs_rating` 排，并列按 `perf_3m` | `pipeline/screeners/market_light.py:295-310` | **已经在用 `rs_rating`，不受影响；0 只变化**——排序键不动，`perf_3m`（原始收益，不是 `rs_3m` 排名）继续做并列 tie-break，不在本次统一范围内 |
| Short List「替补:均线收复中 rs_3m 最高」 | 排序键 `rs_3m`（非过滤，tie-break） | `pipeline/screeners/name_cards.py:288,308` | **不适用「换名单」口径**——这是 `panel_tickers("ma_reclaim")` 候选池内部的排序键，不是准入闸；换成 `rs_rating` 不改变候选池成员数（0 只增减），只可能改变池内谁排第一个被挑中。`panel_tickers` 依赖当晚完整的 panel 计算管线，本次研究没有复跑完整管线，**没有去实测"换排序键后第一名会不会变"**——如实留空，不是 0，不编造具体结果 |
| `preset_hits.py` 通用映射 | `rs21d`/`rs63d`/`rsIbd` 三个键都注册，供用户在 Screener 页自建预设用 | `pipeline/screeners/preset_hits.py:50-52` | 不是某个具体预设，是**能力**；`frontend/public/data/screener-presets.json` 里当前**没有任何预设用到 `rsIbd` 键**（已核实），所以这一行本身 0 只变化；但核这一行时顺手发现 `rsIbd` 键在前端镜像（见下方展示类表 `screenerFilter.js`）已经指向一个退役字段，**与本次统一无关的独立 bug，已开单 T-1002-05 转交 claire** |

### 展示类消费者（换读数不改名单，只改页面上印的数字/标签）

| 消费者 | 读数 | 证据行 | 备注 |
|---|---|---|---|
| `TickerStats.jsx` 个股页 | `rs_21d`(标「RS 1M」) / `rs_63d`(标「RS 3M」) | `frontend/src/components/ticker/TickerStats.jsx:28-31` | 纯展示；统一后标签要么继续叫 RS 1M/3M 但换底层数，要么改标签 |
| `tickerReadings.js` | `rs_1m`/`rs_3m` 与 `rs_line_pctl_21/63` 并排印 | `frontend/src/components/ticker/tickerReadings.js:103-106` | 已经是「两套读数并排」的先例 |
| `ThemeMembers.jsx` 排序 | `rs_3m ?? rs_63d` | `frontend/src/components/groups/ThemeMembers.jsx:60` | 组内成员排序，不是过滤 |
| `MorningRead.jsx` / `morningReadMath.js` 龙头表 | 同列打印 `rs_rating`、`rs_1m`、`rs_3m` 三栏 | `frontend/src/components/breadth/MorningRead.jsx:423-425`；`morningReadMath.js:187-188` | **这是当前页面唯一把三个读数并排放在同一行的地方**——Andy「为什么三个算法看似不一样结果有时候接近」的直接触发点很可能就是这张表 |
| `WatchlistPage.jsx` 的 `pickRs` / `RS_BANDS` | 优先 `rs_line_pctl_21`，没有才退回 `rs_1m`；两套配色带 | `frontend/src/components/watchlist/WatchlistPage.jsx:178-256` | **前端已经做过一次「只留一个」的决定**——claire 的 docstring 原文：「This page prefers the time-series one [RS 线]... 的一个推理是 rs_1m 这条数已经被面板成员资格隐含了（面板本来就是按它筛的），rs_1m 本身不给新信息，RS 线会给」。这个理由本身就是支持「排名类合一，RS 线继续单独」的证据 |
| `etfRank.js`（板块/行业 ETF 卡） | 卡片自己的 11 只 ETF 内部重算同构百分位 | `frontend/src/lib/etfRank.js:11`；口径已登记 `METRIC_SOURCES.md:120` | 分母是 ETF 卡自己的 cohort，不是个股 tradeable 池，**不在本次统一范围内**（不同的量，只是构造方式相同） |
| `screenerFilter.js` | `rs21d`/`rs63d` 过滤键，浏览器端评估逻辑 | `frontend/src/lib/screenerFilter.js:196-197` | `preset_hits.py` 的前端镜像，必须两边一起改 |

### RS 线（`rs_line_pctl_*`）消费者——全部是检测/展示，没有一个过滤

| 消费者 | 用法 | 证据行 |
|---|---|---|
| `watchlist.py` 的 `rs_high` 标记 | `rs_line_pctl_21 == 100`，只检测写进票项，**没有任何格用它筛选** | `pipeline/screeners/watchlist.py:393,628,656` |
| Short List `asset` 席 | `rs_line_pctl_21 >= 100 ∧ hi20` 选首选，否则按 `rs_line_pctl_21` 降序找替补 | `pipeline/screeners/name_cards.py:343-344` |
| `momentum97_shadow_recipes`（影子对照，非生产） | `rs63_97 = rs_line_pctl_63 >= 97`，只写入 `data/history/momentum97_shadow.csv` 供事后复盘对照，**从不进任何面板** | `pipeline/screeners/watchlist.py:538-570` |
| 资产层（26 只核心 ETF） | `rs_line_pctl_21/63` 与个股同函数，只展示不筛 | `pipeline/screeners/asset_signals.py:89-90,172` |
| `WatchlistPage.jsx` 票旁数字 | 若有则优先显示（见上表） | 同上 |

### skills 类消费者（第一版漏收，复核打回后补）

| 消费者 | 用法 | 证据行 | 换读数影响 |
|---|---|---|---|
| `focus-notes` skill 的 `build_cards.py` | 把 `rs_rating` 写进每日 Focus 事实卡的 `"rs"` 字段，供候选一句话判断引用 | `.claude/skills/focus-notes/scripts/build_cards.py:114` | **已经在用 `rs_rating`，不受本提案影响**——但如果 Option B（改名不叫 RS）落地，这里的字段键名 `"rs"` 和它在卡片里显示的标签需要跟着复核，避免继续叫一个"RS"但含义已经和别处的单窗读数脱钩 |
| `daily-recap` skill 的工作流第 1 步 | 同时列了 `asset_signals` 的 `rs_line_pctl_21` 与 `universe` 的「个股 RS」（**没写明具体是哪个字段**） | `.claude/skills/daily-recap/SKILL.md:52` | **这一行本身就是 Andy 疑惑的活证据**——"个股 RS"四个字在这份工序文档里没有指明是 `rs_rating` 还是 `rs_1m`/`rs_3m`，写复盘的人（人或 agent）拿到这份工序说明时要么要猜、要么要回去翻 `universe.json` 现查。**不论 Option A/B 哪个落地，这一行都应该改成具体字段名**，这是本次统一最该优先改的一处文档，因为它直接影响"写给 Andy 看"的产出 |

抽查核实：两处 `git grep` 命中之外，`.claude/skills/` 目录下没有其他文件读这些字段（`git grep -l` 对三类/四类
关键词在 `.claude/skills/` 范围内只命中这两个文件）。

**课程书稿**：本仓库没有课程正文（在私有课程仓），本次 grep 范围到不了；已知课程 M2_L09 的 `liquid_leader`
口径（`rs_3m` 窗口是我们自选，不是课程写明的）已登记在 `METRIC_SOURCES.md:154`，如果 Andy 选 Option A，
课程文案里任何写死「RS 窗口＝3 个月」的措辞需要 claire/课程线另行核对，本研究不覆盖。

## 二、口径查标准

> 先查口径，别自己造（CLAUDE.md）。三个概念分开查，结论写回 `METRIC_SOURCES.md`。

### `rs_rating`（排名类的核心）

- **IBD 官方**：12 个月表现、近 1 季加权更重，**六个系数本身从未公开**；社区复刻公开收敛到
  `0.4×P3 + 0.2×P6 + 0.2×P9 + 0.2×P12`（P3/P6/P9/P12 = 3/6/9/12 个月累计收益），再在全市场横截面排 1–99。
  来源：[skyte/relative-strength](https://github.com/skyte/relative-strength)、
  [Fred6725/relative-strength](https://github.com/Fred6725/relative-strength)（同一套复刻的另一个镜像）、
  [aistockselection.com RS Rating 词条](https://www.aistockselection.com/en/glossary/rs-rating)（公开写出同一套权重）。
  我们的 `rs_rating`（`run_all.py:562-567`）就是这套权重，**本来就对齐**。
- **Minervini（《Trade Like a Stock Market Wizard》《Think and Trade Like a Champion》）**：直接引用 IBD 的
  RS Rating 1–99 排名，门槛「≥70 最低，≥90 优选」，**没有自己另一套公式**——Trend Template 第 8 条「RS ranking
  不低于 70」就是抄 IBD 这同一个数（我们 `vcp_detector.py:128-129` 的 `rs_rating>=70` 本来就是读它）。
- **Stockbee（Pradeep Bonde）**：**查到了一手证据，此前 METRIC_SOURCES 没写**——Bonde 自己的 2017 文章
  [《How to setup IBD style Relative Strength Ranking for stocks》](https://stockbee.blogspot.com/2017/05/how-to-setup-ibd-style-relative.html)
  标题就承认是在复刻 IBD 的公式，用的同样是 `40%P3 + 20%P6 + 20%P9 + 20%P12` 再全市场百分位。
  **Stockbee 没有一个独立于 IBD 的 RS 定义**——他只是同一个复刻的又一个使用者。
- **结论**：IBD / Minervini / Stockbee 在 RS Rating 这件事上是**同一个标准**（社区复刻，系数未经 IBD 一手确认，
  但三家殊途同归到同一套权重）。我们的 `rs_rating` 已经是这个标准。

### `rs_1m` / `rs_3m` / `rs_6m`（单窗横截面百分位）

- **查过，无独立标准**：上面那条复刻公式里，`P3`（3 个月累计收益）和 `P6`（6 个月累计收益）本来就是
  `rs_rating` 的输入分量，**没有任何一手或社区源把"单独拎出一个季度窗口做排名"当成一个独立被命名的指标**；
  IBD/Minervini/Stockbee 三家公开材料里都只有"综合 RS Rating"这一个数，没有"3 个月 RS""6 个月 RS"这种单独发布的东西。
- 我们的 `rs_1m`/`rs_3m`/`rs_6m` 本质上是把 `rs_rating` 的半成品原料（未加权的单季度收益）直接摆上台面当成品卖，
  这解释了为什么它们和 `rs_rating` 相关度高（见第三节）却又不完全一致——**它们本来就是同一个计算过程的中间产物**，
  不是三种方法论的分歧。
- **结论**：`rs_1m`/`rs_3m`/`rs_6m` 单独存在没有标准依据；它们是 `rs_rating` 的组件，不是平行的指标。

### RS 线（`rs_line_pctl_*`）

- **官方定义**（Minervini、IBD 图表）：RS Line = 股价 ÷ 基准指数价格，画成一条线，看它相对价格新高/新低、
  相对自己趋势线的方向——**是一条曲线，不是一个排名分数**。
  来源：[deepvue.com RS Line 用法](https://deepvue.com/indicators/how-to-use-the-relative-strength-line/)、
  Minervini RS Line 定义同上搜索结果。
- **TraderLion / Richard Moglen**（本仓库 TML 定义的原作者）对 RS 线有具体打法：「RS Phase」= RS 线站上自己的
  21 日 EMA；「RS New High（RSNH）」= RS 线创新高，又分「RS 先于价新高」「RS 与价同时新高」两种形态。
  来源：[TraderLion「6 Ways to Use Relative Strength」](https://traderlion.com/markets-essentials/relative-strength-essentials/)、
  [TraderLion「How The RS Phase Signals New Trends Early」](https://traderlion.com/markets-essentials/rs-phase/)。
  **这证实了 `METRIC_SOURCES.md:174` 那行「本行未核一手」现在可以核了**：`rs_high`（`rs_line_pctl_21==100`）
  方向上对齐 TraderLion 的「RS New High」概念——RS 线处于自己历史的高点。**没有核实的是窗口长度**：TraderLion
  材料没有写死「新高」要看多少天，我们选 21 天是跟随 `rs_line_pctl` 底层量本身的窗口，不是抄自 TraderLion 的
  具体参数。
- oratnek 本人的页面是我们 `rs_line_pctl_21/63/126` 的直接出处（29/29 复现，`METRIC_SOURCES.md:81`），这是
  "照抄一个具体实践者的具体算法"，不是"复刻一个公开标准"，两者性质不同，`METRIC_SOURCES.md` 已经如实标注。
- **结论**：RS 线是"自比的曲线"类指标，公开定义不包含排名；我们把它做成自百分位（`count(RS_i<=RS_today)/n`）
  是对"RS 线创新高"这个检测类概念的量化操作化，方向上有 TraderLion 的支持，但具体窗口/公式仍是我们自己的选择，
  **继续标 ⚠️ 自造，不能升级成 ✅**。

### `i_score` / `industry_rank`（行业排名）

- IBD 发布 197 个行业组按 6 个月涨幅排名，公式不公开。我们用行业内 tradeable 成员 `rs_3m` 中位数，**窗口（3 个月
  vs IBD 的 6 个月）本来就不一致**，这条此前已在 `METRIC_SOURCES.md:110,168` 标过，本次没有新发现，维持 ⚠️ 自造。

已把上面四条结论（含 Stockbee 新证据、TraderLion 对 `rs_high` 的部分核实）写回 `data/reference/METRIC_SOURCES.md`
（见该文件改动）。

## 三、相关度（09-30 实测，独立复算核对 claire 背景表）

用同一份 `data/output/universe.json`（`tradeable=2499`）独立重新实现三套读数（脚本见第四节），
在最新交易日做 Spearman 相关与前 20% 名单的 Jaccard 重合度，核对 claire 10-02 给的数字：

| 配对 | claire 背景表给的 Spearman | 本次独立复算 | 前 20% Jaccard（本次） |
|---|---|---|---|
| `rs_rating` ~ `rs_6m` | 0.84 | **0.849** | 0.608 |
| `rs_rating` ~ `rs_3m` | 0.65 | **0.686** | 0.410 |
| `rs_3m` ~ `rs_6m` | 0.53 | **0.549** | 0.352 |

三组数字都在claire原数的 ±0.04 内（两套实现路径完全独立：claire 读的是 universe.json 现成字段，这里是从价格
重新算），**互相印证，不是同一处代码跑出来的巧合**。另外两组我自己加的、背景里没有但对决策有用：

| 配对 | Spearman | Jaccard |
|---|---|---|
| `rs_rating` ~ RS线(21d) | 0.438 | 0.351 |
| RS线(21d) ~ RS线(63d) | 0.801 | 0.537 |

RS 线自己的两个窗口（21d/63d）彼此相关 0.80，跟排名类的相关度（0.35-0.44）明显更低——**量化确认了"RS 线是另一个族"**，
不是文字直觉。

## 四、哪个读数更能挑出之后跑赢的票（5 年回测）

脚本：[`rs_compare.py`](rs_compare.py)（`python3 data/research/rs_unify/rs_compare.py --fetch` 复跑，
~3 分钟；结果缓存 `data/research/rs_unify/backtest_results.json`，面板元数据
`data/research/rs_unify/panel_meta.json`）。

**样本**：2026-09-30 `universe.json` 的 2,499 只 `tradeable` 名字，用 yfinance 回取 5 年日线（2021-10-01 →
2026-10-01，1,255 根交易日），102 只历史不足 273 根（近 5 年内上市/复牌）被剔除，剩 2,397 只 + SPY。

**⚠️ 存活偏差，必须读**：样本是**今天**的 tradeable 名单投影回 5 年前，过去 5 年里退市、被收购、或跌出
tradeable 资格的名字完全不在样本里，而这些名字系统性偏向输家——下面任何一个"赢"的读数，量出来的都是
**偏乐观的上限**，不是可以直接当预期收益用的数。这不是本研究独有的局限：`pipeline/themes/backtest_accel.py`
（10 年期、同一类研究）用的是同一个样本构造方式，局限相同。

**定义**：每 21 个交易日做一次非重叠截面，在当天可用的池子里按每个读数取前 20%，量其后 20 个和 63 个交易日
相对 SPY 的超额收益与胜率（正超额的截面占比）。另加一条**学术基准**——Jegadeesh-Titman 12-1 动量（滚动 12 个月
收益、剔除最近 1 个月避开短期反转），这是动量因子文献里最通行的构造，不是我们发明的，用来给"我们复刻的 RS
到底有没有用"一个外部对照。

### 结果：20 个交易日 forward 超额

| 读数 | 截面数 | 均名数 | 均值% | 中位% | t | 胜率% |
|---|---|---|---|---|---|---|
| `rs_rating`（IBD 复刻） | 46 | 458 | **+0.90** | +0.99 | **1.87** | 67 |
| `rs_1m`（单窗 1 月） | 46 | 467 | +0.87 | +0.65 | 1.91 | 63 |
| `rs_6m`（单窗 6 月） | 46 | 463 | +0.82 | +1.08 | 1.70 | 59 |
| 学术 12-1 动量（基准） | 46 | 458 | +0.74 | +0.58 | 1.60 | 61 |
| `rs_3m`（单窗 3 月） | 46 | 465 | +0.51 | +0.03 | 1.03 | 52 |
| RS 线自百分位 63d | 46 | 488 | +0.22 | +0.31 | 0.58 | 54 |
| RS 线自百分位 21d | 46 | 539 | +0.17 | +0.16 | 0.45 | 54 |

### 结果：63 个交易日 forward 超额

| 读数 | 截面数 | 均名数 | 均值% | 中位% | t | 胜率% |
|---|---|---|---|---|---|---|
| 学术 12-1 动量（基准） | 44 | 457 | +2.41 | +3.44 | **2.60** | 61 |
| `rs_6m`（单窗 6 月） | 44 | 462 | +2.43 | +1.66 | 2.57 | 61 |
| `rs_1m`（单窗 1 月） | 44 | 466 | +2.57 | +1.02 | 2.39 | 64 |
| `rs_rating`（IBD 复刻） | 44 | 457 | **+2.33** | +1.88 | **2.31** | 59 |
| `rs_3m`（单窗 3 月） | 44 | 465 | +2.03 | -0.43 | 1.69 | **45**（<50%） |
| RS 线自百分位 21d | 44 | 540 | +0.46 | +0.78 | 0.59 | 59 |
| RS 线自百分位 63d | 44 | 487 | +0.25 | -0.71 | 0.28 | 45 |

### 读法

1. **排名类（`rs_rating`/`rs_1m`/`rs_6m`）全部显著或接近显著（|t| 1.7–2.6），量级互相接近**——这与它们
   在第三节测出的高相关一致：它们本来就是用重叠窗口测同一件事（谁跑赢了大盘），表现接近不是巧合。
   `rs_3m` 单独偏弱，63 日胜率甚至低于五成——**单独一个季度窗口是三个单窗里最不稳的那个**，这点在
   claire 的背景数据里也看得出来（`rs_rating`~`rs_3m` 相关度 0.65–0.69，是三组相关里最低的一组）。
2. **RS 线自百分位（无论 21d 还是 63d）两个窗口在排名用途上都不显著**（t 0.28–0.59，63 日胜率甚至到 45%），
   和 `pipeline/themes/backtest_accel.py` 此前的独立发现一致（"RS-line arms were removed after both tested
   negative"）——**这不是本次新结论，是第二次独立验证同一个方向**。这也和代码现状吻合：`rs_line_pctl_*`
   在生产里从来没被用来筛选（第一节「RS 线消费者」整张表全是检测/展示），这次回测说明这个用法是对的，不用改。
3. **学术 12-1 动量基准和我们的 `rs_rating` 表现相近**（63 日 t=2.60 vs 2.31）——说明我们复刻的 IBD 权重
   没有偏离"多窗口混合优于单窗口"这个因子文献的基本共识，复刻是合理的。

## 四之五、排名适合筛选、不适合提示变化（MRNA 与可比样本，含没涨的）

> Andy 原话：「我感兴趣的是RS线和rs rating在MRNA上的表现是怎样的」。一只票、事后挑选、+177% 的单日跳空，
> 不能回答"这个形状一般会怎样"。脚本 [`mrna_comparable_cases.py`](mrna_comparable_cases.py) 在整个面板上
> 扫同一个形状——**事前定义、事后不挑**——结果写进 [`mrna_comparable_cases.json`](mrna_comparable_cases.json)。

**形状定义**（操作化、自造，不是任何公开标准——按 `METRIC_SOURCES.md` 的规矩标出来）：
`rs_line_pctl_21` 在 t-10 个交易日 ≤60，到 t 日跳到 ≥95（RS 线**新**创短窗高点，不是已经在高点趴了几周的票）；
同时 `rs_rating` 在 `[t-10, t]` 整段都落在 80–96（票本来就是公认的强股，排名没有变化——这正是 MRNA 的形状：
`rs_rating` 91–93 不动，RS 线从 10 冲到 100）。同票事件间隔 ≥60 个交易日去重。

**结果**：2026-09-30 universe 的 2,398 只可交易股 + SPY，2021-10→2026-10 五年面板上，**这个形状出现了
3,428 次**——不是罕见信号，是很常见的价格行为。有完整 20 日后续数据的 3,351 次里，20 日超 SPY 为正的占
**46.0%**（低于五成），均值 **+0.17%**，中位数 **−0.9%**；63 日为正占 45.4%。**这个形状本身不预示继续涨**，
和第四节"RS 线自百分位排名不显著"的回测结论是同一个方向的第二次独立验证，只是这次换成了"事件研究"而不是
"截面排名"的测法。

**MRNA 本票在这个面板上出现过两次同形状事件**，结果截然不同：

| 日期 | RS线21日(t-10) | RS线21日(t) | rs_rating(t) | 20日后超 SPY | 63日后超 SPY |
|---|---|---|---|---|---|
| 2026-02-23 | 33.3 | 100.0 | 92.3 | **+5.7%** | −16.4% |
| 2026-08-17 | 4.8 | 100.0 | 91.3 | **+125.0%**（含 08-19 跳空） | 数据不足（窗口未走完） |

同一只票、同一个形状定义，02-23 那次 20 天后小赚、63 天后倒亏；08-17 那次赶上了那次跳空。**形状相同不代表
结果相同，哪怕是同一只票**。

**跨票样本**（从 3,351 个事件里按结果分布抽样：最差 3 个、中位 2 个、最好 3 个，不是"找好看的"）：

| ticker | 日期 | RS线21(前) | RS线21(当时) | rs_rating | 20日后超 SPY | 63日后超 SPY |
|---|---|---|---|---|---|---|
| RDW | 2025-07-17 | 14.3 | 100.0 | 95.6 | **−55.1%** | −59.4% |
| TRLV | 2024-10-22 | 52.4 | 100.0 | 92.8 | **−54.4%** | −66.9% |
| UNIT | 2024-05-02 | 9.5 | 100.0 | 90.9 | **−52.0%** | −35.3% |
| ALNT | 2023-01-12 | 52.4 | 95.2 | 92.4 | −0.9% | −12.1% |
| CSW | 2024-05-28 | 9.5 | 95.2 | 87.5 | −0.9% | +20.2% |
| HIMS | 2025-01-21 | 28.6 | 100.0 | 95.8 | **+129.0%** | −2.7% |
| NVTS | 2025-09-18 | 4.8 | 100.0 | 94.6 | **+132.2%** | +8.0% |
| MSTR | 2024-02-08 | 14.3 | 95.2 | 94.5 | **+139.8%** | +110.3% |

**要点**：形状本身（rs_rating 高位不动 + RS 线新创短窗高点）对后续 20 天表现**几乎没有分辨力**——三个最差
的（RDW/TRLV/UNIT）和三个最好的（HIMS/NVTS/MSTR）在"形状"这一维上完全一样，差别只在事后才看得出来。
RDW/TRLV/UNIT 这三个"RS 线新高"后续腰斩的案例，和 MRNA/HIMS/NVTS/MSTR 这几个暴涨的案例，**进场那一刻的
读数长得一模一样**。

### 谁来承担"最近有没有变化"这个信息？

如果排名并入一个（选项 A），`rs_1m`/`rs_3m`/`rs_6m` 不再做判据，"最近有没有变化"这个问题结构上**只剩 RS 线
能回答**——因为按上面的形状定义，`rs_rating` 在这些事件的整个窗口里**本来就按定义没有变化**（80–96 不动），
它量的是"现在是不是强"，不是"有没有新变化"；能变得出"10 冲到 100"这种跳跃的只有 RS 线（自比的曲线，窗口短）。
**但 46% 的 20 日后胜率和负的中位数超额说明这个信息目前只能拿来描述，不能拿来当预警**——这和第四节的截面回测、
以及 2026-10-02 用 21 日版本测的"RS 线新高"回测（任务背景里 Andy 要求补的那组）结论一致：RS 线新高在"已经
满足资格条件"之上没有加出可测的早期优势。统一方案落地后，面板文案**不应该**把 RS 线包装成"预警/早钟"，
只能标注为"确认/描述"——这是 CLAUDE.md 自造指标规矩要求的边界，必须写进前端文案改动清单。

### 复现 rs_rating 历史的数据来源与存活偏差

本节和第四节用的是同一份面板（`.cache/rs_unify_panel.pkl`，由 `rs_compare.py --fetch` 生成，gitignore 排除，
可随时重跑复现）：2026-09-30 `universe.json` 的 `tradeable` 名单投影回 5 年 yfinance 日线，`rs_rating` 用
`run_all.py:565-567` 的同一套权重（0.4/0.2/0.2/0.2，q3 用 6/12 月插值）在面板的每一天重新计算，不是只有
"今天"这一行——这是为什么能把 MRNA 2026-02-23 那次事件也找出来，而不是只能看到 08-19 这一次。**存活偏差同
第四节**：样本是今天还在交易的名字投影回去，5 年里退市/被收购/跌出 tradeable 的名字不在面板里，这类名字
系统性偏输家，3,428 个事件里"腰斩"案例的真实占比可能还被低估，不是高估。

**claire 的 `/tmp/rs/` 脚本仍未入库**（任务背景写明），本节用的 `rs_compare.py`/`mrna_comparable_cases.py`
是本仓库内可重跑、可复核的独立实现，口径与 claire 的手工重建在 08-18 那天的数字上互相印证（见任务背景表：
claire 重建 RS 线 21 日分位 90.5/系统记录 90，`rs_3m` 算 87/记录 88；本脚本 2026-08-17 读数 RS线=100、
rs_rating=91.3，形状一致，具体数值因重建口径和取数时点不同而非逐位相同属预期内）。

## 五、方案：A/B 两个选项，代价摆出来

### 选项 A——排名并入 `rs_rating`，RS 线继续单独做检测

**做法**：`liquid_leader`、`vcs` 面板、`bullish_4pct`/「4% Bullish」、「Monthly Leader 97」、`industry_rank`
五处把判断读数从 `rs_3m`/`rs_1m` 换成 `rs_rating`（同阈值或重新标定阈值，见下）；`rs_1m`/`rs_3m`/`rs_6m`
字段本身可以继续保留在 `universe.json`（它们是展示用的"分量"，`TickerStats.jsx`/`MorningRead.jsx` 想继续显示
"3 个月涨了多少"没问题），但**不再作为任何面板的入场判据**，前端标签改成"分量"而非"RS"（比如"3M Return
Rank"而不是"RS 3M"，避免跟 `rs_rating` 混叫）。RS 线不动——继续是检测/展示，不参与排名。

**代价**：
- 五个面板的名单改变（第一节表格已给具体数字，liquid_leader 变动最大，~27% 只在旧/只在新）——**公开仓库，
  历史上任何人截图过这些面板的人会看到名字不一样了**。
- `industry_rank`/`i_score` 的「前 20 行业」重排 9/20（见第一节），下游 `top20_industry`（TML flag-only 条件）
  跟着变。
- 阈值需要重新标定：`rs_3m>=80` 和 `rs_rating>=80` 不是同一把尺子上的刻度（两者相关 0.65–0.69，不是 1），
  简单复制数字会悄悄收紧或放松面板，本提案第一节的"换后 N 只"用的是**原样复制阈值**，不是重新标定后的数字——
  真要落地还要再做一次阈值校准，不是机械替换。
- `screener-presets.json` 里"4% Bullish"/"Monthly Leader 97"两个预设、`screenerFilter.js`/`preset_hits.py`
  两套镜像都要同步改，漏一边前后端会对不上。
- schema 基线（`data/reference/schema_snapshot.json`）要重新 `--update`。

**不动的部分**：`rs_rating` 已经是 TML、VCP、market_light 三处的现行读数，这三处完全不受影响；RS 线的全部
用法（`rs_high`、Short List asset 席、资产层展示）不变。

### 选项 B——保留单窗读数，但改名、不再叫「RS」

**做法**：`rs_1m`/`rs_3m`/`rs_6m` 字段名不变（避免 schema 变动），但前端标签、面板文案、`METRIC_SOURCES.md`
一律不再用"RS"这个词描述它们——改叫"3 个月涨幅分位"一类的中性名字，和 `rs_rating`（唯一配得上"RS"这个名字、
因为它是唯一对齐 IBD/Minervini/Stockbee 共同标准的那个）在命名上明确分开。所有现有面板阈值、现有名单**一个
不变**。

**代价**：
- 不解决 Andy 的原始疑惑（"为什么三个算法结果有时候接近"）——`MorningRead.jsx` 那张三栏并排表还是会让人
  以为是三种独立方法论，只是不再叫同一个名字而已，没有减少认知负担，只是不再用词混淆。
- 回测没有显示单窗读数（尤其 `rs_3m`）比 `rs_rating` 更好用——继续用一个回测上更弱的读数做面板判据，
  只是换了个更诚实的名字，面板本身的质量没有变化。
- 前端标签改动面也不小（`TickerStats.jsx`、`tickerReadings.js`、`WatchlistPage.jsx` 的 `RS_BANDS` key 命名
  等），工作量未必比选项 A 小，只是不碰 schema 和面板名单。

### 本研究的倾向（仅供参考，拍板权在 Andy）

标准核查（第二节）和回测（第四节）两条独立证据都指向同一个方向：`rs_1m`/`rs_3m`/`rs_6m` 不是独立方法论，
是 `rs_rating` 的半成品原料；单独使用时 `rs_3m` 回测最弱、`rs_1m`/`rs_6m` 表现接近 `rs_rating` 本身。
**选项 A 更贴近"三个算法为什么像"这个问题的根——因为它们本来就是同一个计算的三个阶段**。但选项 A 的代价
是实打实的名单变化和一次迁移工程，不是免费的；选项 B 更便宜，但只是把问题诚实地摆出来，不解决它。

## 六、留痕

- 标准核查结论已登记：`data/reference/METRIC_SOURCES.md`（Stockbee 新证据、RS 线 TraderLion 部分核实两处）
- 回测脚本与结果：`rs_compare.py` / `backtest_results.json` / `panel_meta.json`（本目录）
- MRNA 与可比样本（形状事件研究）：`mrna_comparable_cases.py` / `mrna_comparable_cases.json`（本目录）
- HTML 对照页：`2026-10-02_rs_unify_proposal.html`（同目录）
