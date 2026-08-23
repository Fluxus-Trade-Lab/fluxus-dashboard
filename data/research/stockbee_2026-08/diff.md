# 逐格对照 —— 他的口径 vs 我们已建的实现

体例照 [`data/research/oratnek_diff/`](../oratnek_diff/README.md)：**一致 / 不一致 / 我们没有 / 他没有**，四栏各自成节。
每格给我们的文件行号。他的原文和出处在 [method.md](method.md)，这里只引结论。

**基准数据**：`data/output/universe.json`，session **2026-08-21**（5,627 行）。归档口径的数字标了归档范围。
⚠️ 单日快照的计数**会过期**（[[pitfall_a_measurement_expires]]）——下面凡是「今天多少只」的都标了 session，会动的读数我尽量报成**机制**（子集/超集关系）而不是计数。

---

## ✅ 一致 —— 已经对上了，别重做

| 项 | 他 | 我们 | 位置 |
|---|---|---|---|
| **TI65 定义** | `avgc7/avgc65` | `close[-7:].mean() / close[-65:].mean()` | [yfinance_adapter.py:375](../../../pipeline/adapters/yfinance_adapter.py#L375) |
| **TI65 阈值** | `>1.05`（2014–2017 主口径） | `>1.05` | [watchlist.py:96](../../../pipeline/screeners/watchlist.py#L96) |
| **Double Trouble** | `c/minl252>=1.8` | `c_low52w >= 1.8` | [run_all.py:395](../../../pipeline/screeners/run_all.py#L395)、[watchlist.py:96](../../../pipeline/screeners/watchlist.py#L96) |
| **MDT** | `c/avgc126>1.19` | `mdt > 1.19` | [yfinance_adapter.py:375](../../../pipeline/adapters/yfinance_adapter.py#L375) |
| **三条是 OR 不是 AND** | "merge them together as some stocks will be common" | `_strong()` = `or` | [watchlist.py:96](../../../pipeline/screeners/watchlist.py#L96) |
| **流动性地板** | `minv3.1 >= 100,000` | `min_vol_3d > 100_000` | [anticipation_scan.py:50](../../../pipeline/tools/anticipation_scan.py#L50) |
| **Market Monitor 十个计数** | 4% up/dn、25% 季、25% 月、50% 月、13%/34d | 全部十个都在算 | [breadth_metrics.py:76-83](../../../pipeline/screeners/breadth_metrics.py#L76) |
| **300 = thrust 的量级** | "back-to-back 300-plus days" | `thrust_count()` 上限 300 | [breadth_signals.py:79](../../../pipeline/screeners/breadth_signals.py#L79) |
| **4% 双计当广度用** | Market Monitor 第 1、2 行 | `stockbee_ratio` 5 日比 | [stockbee_ratio.py](../../../pipeline/screeners/stockbee_ratio.py) |
| **突破前收缩是必要条件** | "range expansion preceded by series of range contraction days" | VCS v2 / `range5_pct` / `atr_pctl_252` | [vcs.py](../../../pipeline/screeners/vcs.py) |

**结论**：Anticipation 的**强度层三条 ratio 我们是忠实移植，阈值一字不差**；Market Monitor 的**十个计数一个不缺**。
这两块 Andy 不用再投时间——真正的差在下面两节。

---

## ⚠️ 不一致 —— 同一个东西，我们的口径和他不同

### D1. 【最重要】EP 的价格门槛：他 **4%**，我们 **10%**

| | 他（2014-07 盘中版） | 我们 |
|---|---|---|
| 涨幅 | `c/c1 > 1.04` | `change_pct >= 0.10` |
| 量 | `v > 3*avgv50.1` **且** `v >= 300,000` 股 | `rel_volume >= 3.0`（无股数地板） |
| 市值 | **无** | `market_cap >= $500M` |
| 之后 | **人工研究催化剂**（neglect + game changing earnings） | 无 |

实测（2026-08-21 session）：

```
他的口径 (4% & rvol>=3 & vol>=300k):   55 只
我们的   (10% & rvol>=3 & cap>=500M):   8 只
交集 8 · 我们独有 0 · 他独有 47
```

**我们的 EP 是他的真子集，漏掉 85%（47/55）。** 而且不是「更精」——是**在两个正交方向上同时收紧**：
- 涨幅 4%→10%：他明说 EP 的证据是**量**（3× 均量），价格只要 4%。抬到 10% 等于**只收跳空**，把「消息出来后当天温和放量走强」这一整类切掉了。
- 市值 ≥$500M：**方向和他相反**。他原话「500 million plus float 我不太热衷」「best moves happen on float below 10 million」。我们把他认为最爆的那一段整个排除了。今天 universe 里 **2,520 只（44.8%）市值 <$500M**。

（口径注：他的 float ≠ 我们的 market_cap，见 §「我们没有」G1。但方向相反这一点两个口径都成立。）

**归属**：EP 阈值在 `pipeline/screeners/episodic_pivot.py` = **DATA ALEX 的文件**，我不动。这是一条建议，见 [open_questions.md](open_questions.md) §建议。

### D2. 4% 突破缺 `v > v1`

| | 他 | 我们 |
|---|---|---|
| 公式 | `c/c1>=1.04 and v>v1 and v>100000` | `change_pct >= 0.04` |

我们的 [gainers_4pct.py](../../../pipeline/screeners/gainers_4pct.py) **两个量条件都没有**，docstring 自己也承认「There is no volume requirement here」，并指向 `vol_up_gainers`。但 `vol_up_gainers` 用的是 `rel_volume >= 1.5`——**那是「比 3 个月均量高 50%」，不是他的「比昨天高」**。这是两个不同的问题：

- 他的 `v > v1`：今天的买盘**比昨天大**（突破日相对前一日放量）
- 我们的 `rel_volume >= 1.5`：今天的量**比常态大**

一根缩量整理后的突破日，可能 `v > v1` 成立而 `rel_volume < 1.5`——**恰恰是他要的那一类**（"volume during consolidation should be preferably orderly and lower"）。

实测（2026-08-21）：我们 `gainers_4pct` 收 **642** 行，加上他的 `v>100000` 地板后剩 **513** 行，**129 行（20.1%）是 10 万股以下的**。`v > v1` 我们的 universe 没有昨日量字段，量不了——见 [open_questions.md](open_questions.md)。

⚠️ 但注意：`gainers_4pct` 的**用途是广度计数**（喂 `stockbee_ratio`），加闸会改变广度口径。他的 Market Monitor 第一行也是**裸计数**（"Number of stocks up 4% plus today"），**没有量条件**。所以：
- 当**广度**用 → 我们和他一致，别加闸 ✅
- 当**选股**用 → 他有 `v>v1 and v>100000`，我们没有这条路 ❌

**一个 token 两个职责**（[[pitfall_one_token_two_jobs]]）：`gainers_4pct` 按广度口径量对了，按选股口径不及格。

### D3. Anticipation 的「静」：他 **±0.4%**，我们 **±1%**

| 日期 | 他 | 我们 |
|---|---|---|
| 2014–2015 | `-1% ~ +1%` | `abs(change_pct) <= 0.01` ✅ 对上 |
| **2018-08** | **`-0.4% ~ +0.4%`** | 仍是 1% ❌ |

我们抄的是他 2014 年的版本。他 2018 年把这个闸**收紧了 2.5 倍**，还加了两条我们没有的（`Price History Net change ±0.2`、`price > $3`）。

### D4. Anticipation 的市值默认闸：他没有，我们 **$1B**

[anticipation_scan.py:44](../../../pipeline/tools/anticipation_scan.py#L44) `--cap` 默认 `1e9`。他的四个 anticipation 扫描**一个都没有市值条件**，只有 `minv3.1` 流动性和 **price 地板**（$3 / $15 / $39）。

他的地板是**价格**，我们的是**市值**——量的不是同一件事。低价高流动性的小票（他明确说是最肥的那类）被我们的 $1B 直接排除。

### D5. 相对线性：他当**第一否决项**，我们埋在 VCS 里当一个加权项

> "Relative linearity is my most important criteria for eliminating stocks. If a stock does not have relative linearity, I do not even look at rest of the criteria"

我们的 Kaufman ER **只作为 VCS v2 内部的一个效率过滤项**存在（[vcs.py:5](../../../pipeline/screeners/vcs.py#L5)、[yfinance_adapter.py:450](../../../pipeline/adapters/yfinance_adapter.py#L450)）——**没有独立字段、不能排序、不能当闸**。

差别是**结构性**的：他是 `if not linear: return`（先砍再看），我们是 `score += w * efficiency`（可以被别的项补偿）。一只「drunken man walk」的票在他那里第一步就出局，在我们这里只要压缩项够高仍能进 VCS 高分区。

他给了 60 日 ER 的完整公式（[method.md §4.1](method.md#41-相对线性--他的第一否决项)），我们把它做成独立字段是**低成本**的。

### D6. Delayed EP 的立论

我们 [delayed_ep_scan.py](../../../pipeline/tools/delayed_ep_scan.py) 的 docstring 写：

> "He gives no numeric thresholds in the sources we can read (his scan is published as images)."

**核实结果：这句话准确，可以留着。** 他 2023-05-03 的 [Episodic Pivots Delayed Entry](https://stockbee.blogspot.com/2023/05/episodic-pivots-delayed-entry.html) 正文**是空的**（纯视频帖）。全站 101 篇方法帖里 delayed EP 只在 2025-09 出现过一句 "It also helps to enter them as delayed reactions EP."。

但 docstring 里那段**行为描述**（day 1 反转 / day 3-4 认为消息 priced in / 二次突破更好 / 空头镜像）在**博客文字里找不到出处**。它可能来自视频。建议把 docstring 那段改成「来源：视频，未经文字核实」，别让它读起来像有出处的引用。

---

## ❌ 我们没有 —— 他有，且是可执行的

| # | 他的东西 | 数字 | 我们缺什么 |
|---|---|---|---|
| **G1** | **float** 分档：`<10M` 爆炸 / `<25M` 理想 / `>100M` 易回撤 / `>500M` 不做 | 有四档硬数字 | universe **105 个字段里没有 float / shares outstanding**（我核过）。我们只有 market_cap。这是**数据源缺口**不是逻辑缺口 |
| **G2** | **分析师覆盖 = neglect** —— 无覆盖的 EP 比有覆盖的好 | 定性 + "acceleration 100%+" | universe 无分析师覆盖字段 |
| **G3** | **年轻 EP 筛子**：IPO ≤10 年 & 市值 <$11B & **连续两季度营收增长 ≥39%** | 三条全是硬数字 | 有 `revenue_growth`（单值，79.8% 覆盖，**不是「连续两季」**）、有 market_cap（<$11B 有 4,718 只）、**没有 IPO 日期**。三缺一 |
| **G4** | **B3 不得连涨 3 天** | 数字 3 | 全仓无实现。这是**九条 setup 闸里唯二有硬数字的一条**，且我们有 OHLC 算得出来 |
| **G5** | **整理期内不许有 4% 下跌日** | 数字 4% | 无实现。**自指闸**：用他自己的 4% 扫描当质量过滤器；我们两个部件都有，没接起来 |
| **G6** | **收盘在当日高附近** | 无数字（"at or near"） | 有 `dcr_pct`（日内收盘位置）字段，**没有当闸用** |
| **G7** | **前一日窄幅或阴线** | 无数字 | 有 `range5_pct` / `wk_tight_3`，**没有「前一日 vs 近 N 日」这个比较** |
| **G8** | **本轮第 1–3 次突破** | 数字 1–3 | 有 `bo_count_1m/3m/6m/1y`（突破计数）**但没有「本轮起点」的定义**，所以数不出「第几次」 |
| **G9** | **$ breakout**：`c-o>=.90 and v>100000`，高价股专用 | $0.90 | 无实现。注意是 `c-o`（**排除跳空**），我们所有 4% 类都用 `c-c1` |
| **G10** | **thrust = 连续多日 300+**，不是单日 | "back-to-back" | [breadth_signals.py](../../../pipeline/screeners/breadth_signals.py) 逐日打分，**没有连续天数读数** |
| **G11** | **退出全套参数**（8% 减半 / 3–5 日 / 20% 跳空全出 / 止损 ≤4% 理想 ≤2%） | 全是硬数字 | 我们**只做扫描不做交易管理**——这是设计选择，不是遗漏。但 Pine 侧 `fluxus-trading-risk-manager.pine` 有 N-stop/R-targets，两边没有对话 |
| **G12** | **60 日 Kaufman ER 独立字段** | 公式给全了，无阈值 | 见 D5 |

---

## 🚫 他没有 —— 我们有，他从不用

这一栏值钱，因为它标出**我们在往哪个方向偏离他**：

| 我们的 | 他的立场 |
|---|---|
| **市值闸**（EP $500M、anticipation $1B） | 他用 **price 地板 + minv3.1 流动性**，从不用市值当闸。且他偏好方向相反（小 float 更肥） |
| **VCS 0–100 压缩分**、`atr_pctl_252` | 他明说不用带阈值的压缩指标：*"You can look for stocks with bollinger band squeeze. I do not use them, I find it easier to just look for series of narrow range consolidation periods."*（[2015-02](https://stockbee.blogspot.com/2015/02/how-to-find-anticipation-setups.html)） |
| **ADR% 地板 3%** | 无对应。他要的是「不要 drunken man walk」= 线性，**不是波动率下限** |
| **h_score / f_score / i_score 等复合分** | 无。他所有闸都是单条件，可手算 |
| `rs_ibd` / `momentum_97` 百分位排名 | 他用**绝对比值**（c/minl252、avgc7/avgc65），不用横截面百分位 |
| **RS line / rs_line_pctl** | 无 |
| 前端每日名片、六席 | 他的输出是**每天 3–5 个名字 + 手写理由**，不是面板 |
| **排除 Healthcare** 的 preset 口径 | 无。他反而列 **Drug Approval** 为高概率催化剂 |
| **ETF** | *"I do not trade ETFs ... stocks make bigger moves than ETFs"* |
| **期权** | *"No. In the initial years I spent a lot of time on option strategies but abandoned those efforts"* |
| **盘中图** | *"I have not looked at an intraday chart in last 5 years or so. Everything I do is based on daily or weekly charts."*（注意这和他「盘中反复跑扫描」并存——他看**扫描结果**不看**盘中 K 线**） |

---

## 一句话总结

**强度层（TI65/DT/MDT）和广度层（Market Monitor）我们抄得很准，选股层几乎全是我们自己加的。**
我们加的东西（市值闸、VCS 分数、ADR 地板、复合评分、百分位）**每一件他都明确不用**；
他有而我们没有的东西（float、neglect、不连涨 3 天、整理期无 4% 下跌日、$ 突破、线性否决）**几乎全是免费的**——要么已有零件没接起来（G4/G5/G6/G8），要么只差一个数据字段（G1/G3）。

**最大的单点分歧是 EP：我们是他的真子集，今天漏 47/55。** 而且漏的方向正是他反复强调最肥的那一段。
