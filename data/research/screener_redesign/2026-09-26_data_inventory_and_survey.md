---
type: research
status: handoff
source: T-0926-62（claire 09-26 出方案，Andy 交办 alex 盘数据 + 查设计）
evidence: 全部字段现场读 data/output/*.json、pipeline/*.py 源码、courses drafts 逐字核对；X 未能现场抓取（见「B 来源与限制」说明），改用课程稿已收录的外部访谈/对照表替代
---

# Screener 合页：数据盘点 + 设计调研（T-0926-62）

真数据预览：https://claude.ai/artifact/TTVDd4Jd8n2e6bRgrMxb1N
方向定案：Andy 2026-09-26，六层漏斗（宇宙闸→大名单→§11.1资格→setup→主题+大盘→Focus≤15）

## 摘要

六层里三层（大名单、setup、Focus 骨架）已经在跑，两层（宇宙闸、主题+大盘）字段齐全只差拼一页，唯独 §11.1 资格门槛的核心两条（50 日线上倾、10/20 EMA 上倾）——**位置有，斜率没有**：universe.json 每天只发布均线的最新值，不发布它前几天的值，所以"有没有上倾"现在**算不出来**，不是"字段缺"，是"没往外吐"。另外两处硬伤：healthy_charts 的 104 只只有 49 只过 Today's List 的三道闸（两套闸口径不同），以及个股→主题的映射只覆盖 20%（1132/5611 只），其余 273 只还挂在不止一个主题下。15 个扫描器里 5 个已有对应产出，10 个要么缺数据源（财报日历、IPO 日期、盘中报价）要么只是没人写这行代码。

---

# A · 数据盘点（六层漏斗）

## 层① 宇宙闸（Today's List 紧闸）

**判据**（`pipeline/screeners/watchlist.py` 的 `gate`，`data/output/watchlist.json`）：市值 ≥ $10 亿、日成交额 ≥ $2,000 万、ADR ≥ 3.5%（`trouble` 区豁免 ADR）。

| 判据 | 字段 | 状态 |
|---|---|---|
| 市值 | `universe.json` rows[].market_cap | ✅ 有 |
| 日成交额 | close × avg_volume（无现成字段，两个都在） | ✅ 用现有字段可算 |
| ADR | `universe.json` rows[].adr_pct（20 日口径，(最高/最低-1)均值） | ✅ 有 |

实测（09-25 收盘，5,611 只）：过闸 2,049 只（`watchlist.json.gate.gated_rows`）。**这一层齐全，直接能用。**

⚠️ **同名不同闸**：`pipeline/screeners/run_all.py` 里另有一个更松的 `cap_floor`（只卡市值 ≥ $1B，不查成交额和 ADR），`healthy_charts`/`ema21_watch` 两个扫描器跑在这个松闸上，不是 Today's List 的紧闸。合页时统一用哪一个，见下面层②的证据。

## 层② 大名单（healthy_charts）

**判据**（`pipeline/screeners/healthy_charts.py`，课程 §5.4）：站上 50/200 日线、离 52 周高 5%–25%、近一月上涨、RS ≥ 80、相对成交量 ≥ 0.5。

字段全部齐全（`sma50_dist`、`sma200_dist`、`high_52w_dist`、`perf_1m`、`rs_3m`/`rs_rating`、`rel_volume`），今天 104 只，`healthy_charts.json`。

⚠️ **实测证据**（层①提到的两套闸口径差）：把 104 只健康图形拿去过层①的紧闸——**只有 49 只过**（现场跑 `market_cap≥1e9 且 close×avg_volume≥2e7 且 adr_pct≥3.5`）。这不是数据缺口，是两套闸本来就不是同一批股票在跑。合页前二选一：①把 healthy_charts 也改跑在紧闸上（104→49，名单变薄）；②两个数字并排显示，标清楚"共 104，其中过紧闸 49"。**这个决定影响下面每一层的分母，建议先定。**

## 层③ §11.1 资格门槛（五条）

课程原文（`CH11_什么时候不买.md` §11.1）：
（1）股价在 50 日线上方，50 日线上倾。（2）10 日 EMA 在 20 日 EMA 上方，两条都上倾。（3）离 52 周高点 25% 以内。（4）离 52 周低点 30% 以上。（5）市场绿灯、情境热。

| 条 | 拆开看 | 字段 | 状态 |
|---|---|---|---|
| (1) 位置 | 价 > 50 日线 | `sma50_dist`（=(close-sma50)/sma50，>0 即过） | ✅ 有 |
| (1) **斜率** | **50 日线上倾** | 无——universe.json 只发布 sma50 的当前值，不发布它前几天的值 | ❌ **要新字段，但不要新数据源**：pipeline 内部（`yfinance_adapter.py`）已经算出了完整的 SMA50 时间序列，只是收窄成一行时把历史值扔了。补一个 `sma50_rising`（比如"5 日前的 sma50 值 vs 今天"）工程量很小 |
| (2) 位置 | 10EMA > 20EMA | `ema10`、`ema20` 两个都在 | ✅ 用现有字段可算 |
| (2) **斜率** | **两条都上倾** | 同上，无历史值 | ❌ 同上，要新字段（`ema10_rising`、`ema20_rising`），不要新数据源 |
| (3) | 离 52 周高 25% 内 | `high_52w_dist` | ✅ 有，直接判 `abs(high_52w_dist) <= 0.25` |
| (4) | 离 52 周低 30% 外 | `low_52w`（=(close-低点)/低点，样本值 0.598=+59.8%） | ✅ 有，直接判 `low_52w >= 0.30` |
| (5) | 大盘绿灯+情境热 | `market_light.json.verdict`、`regime.py` 产出 | ✅ 有，个股层不用管，一次性接market_light |

**唯一真缺口是斜率**，且缺口比想象的窄：均线的"位置"全部现成，"方向"目前只在 pipeline 内部算过一次就丢了。这条建议直接开数据契约任务补两个布尔字段，不必等新数据源。

⚠️ **命名要避坑**：dashboard 现有的 shortlist 卡片文案里已经在用「资格✓/资格✗」这个词（`pipeline/screeners/name_cards.py:105`），但它判的是 `liquid_leader`（流动性龙头）或 TML 命中，跟 §11.1 这五条完全是两回事。合页如果沿用"资格"两个字，要么改名，要么在文案里分清楚是哪一种资格。

## 层④ 今天想做的 setup（首批：龙头回踩 / EP / VCP）

| setup | 产出文件 | 定义来源 | 状态 |
|---|---|---|---|
| 龙头回踩 | `ema21_watch.json`（尺子 A，Andy 定不改） | Alex Desjardins（TradersLab）21EMA 回踩扫 + 页面 preset 加的 4 条附加条件（≥$1B、非医疗、trend_base、ppCount≥1、ADR 3-6） | ✅ 有，67 只 |
| EP | `ep_qullamaggie.json` + `ep_stockbee.json` | 两家各自的 EP 定义，`unmeasured` 字段里各自标了没法量化的部分（Stockbee 的"neglect + 变盘财报"是人工读，无数据） | ✅ 有 |
| VCP | `vcp.json` | oratnek VCS v2 verbatim port | ✅ 有 |

⚠️ **ema21_watch 与课程 §5.5 表里的"龙头回踩"定义有一处差**：课程原文要求"财报在 7 天以外"，`ema21_watch.py` 的注释明确写了它**不检查财报日期**（因为个股财报字段本来就没有全覆盖，见下面层⑥前的"财报"节）。Andy 说尺子不改，这里只是记一笔：现在过这个 setup 的名字，理论上可能财报就在后天。

## 层⑤ 主题状态 + 大盘读数

| 判据 | 字段 | 状态 |
|---|---|---|
| 大盘读数 | `market_light.json`（verdict/brightness）、`market_health.json`、`regime.py` | ✅ 有 |
| 主题状态（30 个 theme-kind 组的 state/accel/ribbon） | `groups.json.themes[kind=theme]` | ✅ 有 |
| **个股→主题的映射** | 需要反查 `groups.json` 的 `tickers` 数组 | ⚠️ **覆盖窄且有歧义**：56 组里只有 30 组 kind=theme；5,611 只 universe 股票里只有 1,132 只（20%）落在至少一个 theme 组里，**其中 273 只同时落在 ≥2 个 theme 组**（哪个算它的"所属主题"没有唯一答案）；剩下 80% 的票没有主题只有 139 个 industry 分组里的一个（`universe.json` 的 `industry` 字段本身倒是 100% 覆盖） |

合页要显示"个股所属主题·状态"，建议规则写清楚：①优先取 theme-kind 归属，②同时属于多个主题时怎么选（比如按主题里权重最大或 RS 最高的那个），③没有 theme 归属的票 fallback 到 industry 分组显示。这三条现在都没有正式实现。

## 层⑥ Focus ≤15（最后一步归 Andy）

`shortlist.json`（"seats" 6 个位置：burning/new_leader/entry/v_reversal/coiling/asset，`cards` 明细）已经是一个可以借的骨架——`pick_seats()`（`pipeline/screeners/name_cards.py`）已经在做"从各扫描器里各挑一两只拼一张短名单"这件事，只是挑法（heat 排名/新进 TML/新 EP 等）跟这次要的"过完四层漏斗剩下的"不是同一套判据。**不用从零建**，改判据比新写方便。

---

## 15 个扫描器全家桶（§5.5）现状

| 扫描器 | 课程判据 | dashboard 现状 |
|---|---|---|
| 成长股周频池 | EPS/营收 yoy≥20%、站上 50 日线、10/20EMA 上 | ⚠️ `eps_growth_this_y`/`revenue_growth` 字段在，但样本行里几乎全是 `None`（fundamentals_store 覆盖率低）；均线位置条件可算，斜率同层③缺口 |
| 板块与主题 ETF | 11 行业+自定义主题 | ✅ `etf_data.json` + `theme_board.json` |
| 事件驱动跳空 | 财报缺口≥10%，缺口守住 1 天 | ❌ 要新数据源：全 universe 的财报日历现在只覆盖 245/5,611 只（`data/output/tickers/*.json` 的 `next_earnings`，只给 tearsheet 追踪的票），5,611 只普查级别没有 |
| 流动性龙头 | 距 52 周低+70%、日均量≥200 万股、站上 50 日线、RS 前 20% | 🔶 有但口径不同：`universe.json.liquid_leader` 实现是 avg_volume≥200万且 sma50_dist>0 且 rs_3m≥80，**没有"距 52 周低+70%"这一条**（引用见 `run_all.py:635` 注释，实现依据是 TradersLab Alex 的扫描说明，非课程原文） |
| 龙头回踩 | 见层④ | ✅ `ema21_watch.json` |
| 52 周新高 | 5 天内创新高，量≥1.5倍均量 | ⚠️ 无独立产出，但 `days_since_52wh`+`rel_volume` 两个字段都在，用现有字段可算 |
| 高 ADR 加内包日 | ADR≥5%，今日振幅落在昨日之内 | ❌ "内包日"（今日高低落在昨日高低区间内）没有对应字段，需要昨日 OHLC 对比，工程量不大但要新写 |
| 长期平台 | 横盘≥10周，15%带内收窄 | ❌ 现有 `wk_band_3` 是 3 周口径不是 10 周，需要新计算 |
| 多头狂奔 | 大实体、天量、收在最高附近 | ❌ 无对应字段组合，需要新计算（K 线实体比例目前没有发布） |
| VCP | 见层④ | ✅ `vcp.json` |
| 当日最强 | 相对成交量×涨幅前20，价>$5，日均量>50万股 | ⚠️ 无独立产出，但用现有字段（`rel_volume`、`change_pct`、`close`、`avg_volume`）可直接算，工程量小 |
| 盘前扫描 | 盘前涨跌≥3%，盘前量≥10万股 | ❌ 要新数据源：现有管线是隔夜批跑（收盘后），没有盘前实时报价；`pipeline/discord/premarket_digest.py` 存在但产出到 Discord 不落 `data/output` |
| 次新股 | 上市 6 个月到 5 年，在筑第一个平台 | ❌ 要新数据源：universe 没有 IPO 日期字段 |
| 箱体龙头 | 距 52 周低+100%，量放大，贴近新高 | ⚠️ 类似流动性龙头，字段都在（`low_52w`、`rel_volume`、`high_52w_dist`），用现有字段可算，只是没人写这行代码单独发布 |
| 表内再筛 | Focus 与准备就绪名单，均线在价下方 0-5% | ✅ `watchlist.json`/`shortlist.json` 已有类似结构 |

**统计**：15 个里 5 个✅已有对应产出，4 个⚠️用现有字段能算只是没写代码，2 个🔶有但口径对不上课程原文，4 个❌真缺数据源（财报日历全覆盖、内包日/长平台的历史K线比较未发布、IPO日期、盘中实时报价）。

---

## 单位不统一（合页前端要注意）

现场读 `universe.json` 一行样本：

| 字段 | 样本值 | 实际单位 |
|---|---|---|
| `adr_pct` | 2.9391 | **百分数**（2.94 即 2.94%） |
| `change_pct` | -0.0003 | **小数**（-0.0003 即 -0.03%） |
| `gap_pct` | -0.0050 | **小数** |
| `high_52w_dist` | -0.0113 | **小数** |
| `dcr_pct` | 0.9782 | ⚠️ **不是百分比，是 0–1 的比值**（收盘价在当日高低区间的位置，名字里的 `_pct` 是历史遗留误导） |

合页如果同屏展示这几个字段，要么前端统一转换单位，要么在表头分别标注，否则会出现"adr_pct 显示 2.9%，change_pct 也显示 -0.03（漏乘 100 变成看着比 adr 还小）"这类误读。

---

# B · 调研：screener 与 setup 该怎么设计

## 来源与限制的诚实说明

本单要求的来源包括「X（Alex Desjardins/TradersLab、Qullamaggie、Stockbee、Oliver Kell、TraderLion、Jeff Sun 等）」——**alex 是无人值守 worker，这次没有可用的真实浏览器/X 登录会话**（宪法 `feedback_pull_x_yourself.md`：X 调研需要真 Chrome Connect，这条能力只在交互会话上有）。本报告改用两类已经在仓库里、经过核实的替代材料：①课程书稿里逐条标注页码/时间戳的外部访谈转录与对照表（本身就是从 TraderLion/Qullamaggie/Stockbee 原始材料摘录的）；②`pipeline/screeners/*.py` 源码注释里对 TradersLab/Qullamaggie 原始定义的直接引用（含出处 URL）。凡是下面标了"未核实"的，是转述二手材料，不是我自己去源头验证过。**如果 Andy 需要真的去 X 上刷这几个人最近的推文，需要一个交互会话或专门开一次 x-watch 任务。**

## ① 来源清单（5 个）

1. **TradersLab / Alex Desjardins 的扫描说明**（`traderslab.gitbook.io/primetrading/alexs-scans-and-workflow-traderslab`，引用于 `pipeline/screeners/run_all.py:635` 和 `ema21_watch.py` 注释）——21EMA 结构回踩扫描、流动性龙头扫描的原始定义，已经是 dashboard 两个扫描器的直接来源。
2. **The Setup Factory (TSF) / Alex Desjardins 付费 RS 指南**（`thesetupfactory.substack.com/p/tsf-guide-for-assessing-relative`，2026-05-05，Andy 登录读过，摘要见 `data/research/tsf_substack_2026-09/RS_GUIDE_FINDING.md`）——核心可用思路：**个股不只比大盘，还要比它自己所在的组**（原文："We will measure stocks relative performance against their own industry group, theme or sector"）；Screener 列设计是 `RS 0-2W / 0-4W / 0-10W` 累计窗口 + 单独一列 `RS Accel` 加速度。
3. **TraderLion《模型册》两本书 379 张图 + Shake Pryzby 访谈**（`FluxusTrading_Obsidian/30_References/traderlion/07_共同交易语言对照表.md`，38 条缺口逐条标了原文出处页码；`09_Shake_Pryzby_Rotation_对照.md`，TraderLion 播客 2026-08-25，逐分钟摘要）——最大的一块材料，见下面②③。
4. **课程书稿自己收录的外部访谈逐字稿**（`CH05_扫描.md`§5.2-5.5、`CH11_什么时候不买.md`§11.1，标注了具体时间戳如 `00:52:16`、`00:59:39`），这些访谈是 Qullamaggie/Stockbee 一路方法论在课程写作时已经摘录过的原始材料。
5. **课程自己的实测账本**（`SwingMasterclass/_bench/l9_combo.json`，123 天存档、246 笔入场）——不是外部来源，但回答了"这些扫描器里哪个真的有用"这个问题：健康图形单独入场前 7 天命中率最高（52.4% 胜率，+2.06R），是**唯一**样本量够大且实测过的正向证据；与 momentum_97 组合反而更差（Andy 已否决这个组合方向）。

## ② 别人的 screener 页怎么组织：三种范式

| 范式 | 代表 | 特点 |
|---|---|---|
| **条件搭配器（clause composer）** | Jeff Sun（`pipeline/screeners/jeff_sun.py` 已经是这种：`Clause("earnings_per_share_diluted_yoy_growth_fq", ">", 25)` 式的可拼接子句） | 用户自己选字段+比较符+阈值拼查询，灵活但要求用户懂每个字段的含义，容易拼出自相矛盾或口径不一致的条件（本单发现的单位不统一问题，正是这种范式最容易踩的坑） |
| **命名 setup（named setup）** | TradersLab 的"21dma-structure Pullback"、Qullamaggie 的 EP、Minervini 的 VCP | 每个 setup 是一整套逻辑打包成一个名字，用户不用懂内部字段，只看"过没过"；缺点是不透明，出了误判很难定位是哪一条子条件不满足 |
| **漏斗（funnel）** | 课程 §5.2 图 5-1、TSF 的分级 RS（0-2W→0-4W→0-10W 层层收窄）、Andy 这次定的六层方向 | 每层减法，天然带"为什么剩下这些"的可追溯性；缺点是层数一多，字段一多，就是本单 A 部分在盘的这些账——每层都要有实体字段撑住，不然就是自造 |

Andy 定的六层方向属于第三种，**这也是这次数据盘点里发现"斜率字段缺口""主题映射覆盖率低"这类问题的原因**——漏斗范式对字段完整度的要求比命名 setup 高，因为每一层都要能独立验证。

## ③ TraderLion 对照表：38 条缺口里，跟这次合页直接相关的几条

（完整 38 条见 `FluxusTrading_Obsidian/30_References/traderlion/07_共同交易语言对照表.md`，本报告只摘和 screener/setup 设计强相关的）

- **缺口 2「21ema Reclaim」（收复态）**：Ross 的模型册用三态状态机 `Respect → Breaks → Reclaim`，我们现在 ema21_watch 只有"在 0-1 ATR 内"这一个静态判据，没有"刚跌破又收复"这一态。如果合页要做"回踩"setup 的细分，这是现成的三态设计可以抄。
- **缺口 15/31「RS 线新高早于/晚于价格新高」**：RS 线先创新高是加分，价格先创新高反而是**否决闸**（原文 "RS line fails to make a new high as RNA breaks out. Do not buy."）。可实现：`rs_line_pctl_21`/`rs_line_pctl_63` 已经在 universe 里，只差"RS 新高日 vs 价格新高日"这个日期比较没人写。
- **缺口 4「仓位随结构质量缩放」**：不是选股判据，但如果合页要给 Focus 候选打分/排序，"结构够不够格"本身可以是一个连续分数（VCS 已经是，`vcs` 字段），不必是通过/不通过的二元判定。
- Shake Pryzby 访谈里"每季财报'性格突变'名单按族群汇总，当轮动读数"——和本单层⑤的"主题状态"是同一件事的另一种做法：**事件量**（财报后跳空且守住，按主题计数）比**价格滞后量**（四态 state，要 1-3 个月超额累积）更早反应轮动，`09_Shake_Pryzby_Rotation_对照.md` 已经指出 dashboard 缺"按季汇总 EP 到主题"这一层，可以作为层⑤未来的补充方向。

## ④ "更偏人工智能"的方向（3 个，各带数据可行性）

1. **用文字总结每只候选的"板块在变强/变弱 + 大盘支不支持"** —— **可行性最高**。`groups.json`（state/ribbon/accel）+ `market_light.json`（verdict/brightness）两个数据源都已 100% 覆盖 universe，缺的只是一层 LLM 生成文案。基础设施已经存在但目前空转：`data/output/tickers/*.json` 的 `ai_synthesis` 字段和对应的 `tearsheet` skill 已经上线，可现场核实——**245 个 tearsheet 文件里，`ai_synthesis` 目前 0 个非空**（skill 有，还没被真正跑过）。合页要的"每只候选一句话解释"可以直接复用这套已建好但闲置的管线，不用另起。
2. **用模型读图给回踩候选打"形态干净度"分** —— **可行性中等，卡在数据覆盖**。`ohlc_2y`/K 线数据目前只在 245 只 tearsheet 追踪票里有（per-ticker JSON），5,611 只 universe 级别没有逐票 K 线快照；要覆盖全部候选（哪怕只是过了层③④剩下的几十只，不是全宇宙），需要现抓这几十只的 K 线再渲染成图给视觉模型看，工程上是"临时抓取+渲染+调用"三步都要新写，不是接现成数据。VCS（`vcs` 字段）已经是一个不靠视觉、纯数值算的"干净度"分，如果只是要一个连续分数排序，VCS 可以先顶上，不必等视觉管线。
3. **按 Andy 历史成交学他实际会挑哪 5 只** —— **可行性低，缺监督信号**。`data/output/trades/`（每笔交易 JSON）和 `data/history/leaders_log.csv`/`groups_archive.csv`（历史归档）都在，理论上能拼出"某天 Focus 候选池 vs 他实际开的仓位"这样的训练对；但现在没有"每天的候选池快照"这个中间产物留存（`shortlist.json` 是当前一天的，没有归档到 `data/history/`），要先补一条"每天存一份候选池快照"的数据契约，才能回头学历史——**这个方向的第一步不是建模型，是先攒数据**。

（第四个未列入"3 个"但顺手记一笔：TSF 的"个股 RS 要比自己所在的组，不比大盘"——这不算"更 AI"，是一个更朴素的口径升级，但如果合页要给"回踩"候选打分，用组内 RS 而不是全市场 RS 排序，实现成本很低，`groups.json` 已经有组内清单，缺的是"个股在组内的百分位"这一个新计算列。）

---

## 参考

- 真数据预览：https://claude.ai/artifact/TTVDd4Jd8n2e6bRgrMxb1N
- 课程原文：`~/Documents/SwingMasterclass/_audit/drafts/CH05_扫描.md`（§5.2-5.6）、`CH11_什么时候不买.md`（§11.1-11.5）、`CH01_风险开关.md`（§1.7）
- TraderLion 材料：`FluxusTrading_Obsidian/30_References/traderlion/07_共同交易语言对照表.md`、`09_Shake_Pryzby_Rotation_对照.md`
- TSF 来源：`data/research/tsf_substack_2026-09/RS_GUIDE_FINDING.md`
- 实测账本：`~/Documents/SwingMasterclass/_bench/l9_combo.json`
- 现场核实用的文件：`data/output/{universe,healthy_charts,ema21_watch,groups,watchlist,shortlist,market_light,etf_data}.json`、`pipeline/screeners/{run_all,universe_gate,healthy_charts,ema21_watch,name_cards}.py`、`pipeline/adapters/yfinance_adapter.py`、`pipeline/tickers/ticker_data_fetcher.py`
