# 只能前瞻验 / 现在验不了的项

分三类：**① 文字里根本没有**（要么在视频里，要么他从不说）· **② 我们缺数据**（不是逻辑问题）· **③ 可以验，但必须前瞻**。
末尾一节是**给 ALEX / Andy 的建议**——不属于我的文件边界的动作，只提不做。

---

## ① 他的文字里没有 —— 别再去博客找了

抓了 101 篇方法帖（sitemap 全站 5,154 篇里的方法类），下面这些**确认查无实据**：

| 缺什么 | 现状 | 影响谁 |
|---|---|---|
| **Delayed EP 的任何数字** | [Episodic Pivots Delayed Entry (2023-05-03)](https://stockbee.blogspot.com/2023/05/episodic-pivots-delayed-entry.html) 正文**是空的**（纯视频帖）。全站只在 2025-09 出现过一句 "It also helps to enter them as delayed reactions EP." | 我们 `delayed_ep_scan.py` 的 3–15 日窗口、±10% near、60% 收缩比 **全是我们自己定的**，docstring 已诚实说明。但 docstring 里那段行为描述（day 1 反转 / day 3-4 消息被 priced in / 二次突破更好 / 空头镜像）**在文字里也找不到出处**，建议标注「来源：视频，未文字核实」 |
| **「窄幅日」的数字** | 反复出现 "narrow range day"，**从没给过定义** | B2 闸无法机械化 |
| **「收盘接近高点」的数字** | "at or near its high"，无阈值 | B1 闸无法机械化 |
| **「本轮起点」的定义** | "first to third setup since start of the move"，**起点怎么定他没说** | B6 闸无法机械化 |
| **「延展」的数字** | "youngsters defined by number of days stock has been rallying"，**没给天数** | B7 闸无法机械化 |
| **线性的阈值** | 公式给全了，**阈值没有**——他用它排序不用它当闸 | W1 只能做成排序器 |
| **加仓** | 全部 101 篇里**一次都没提过加仓**。只有减仓（8% 减半、第 3/5 日减半、跳空 20% 全出） | 我们别假设他有金字塔加仓 |
| **2018 年三篇 4% 关键帖** | [where-to-exit](https://stockbee.blogspot.com/2018/01/where-to-exit-4-breakout.html)、[where-to-put-stop](https://stockbee.blogspot.com/2018/01/where-to-put-stop-on-4-breakout-or.html)、[when-should-you-enter](https://stockbee.blogspot.com/2018/01/when-should-you-enter-4-or-breakout.html)、[how-to-select-best](https://stockbee.blogspot.com/2018/01/how-to-select-best-4-breakout-setups.html) **正文全是空的**（纯视频） | 标题正是我们最想要的四个问题。**文字答案在 2015/2017 那几篇里**（已收进 method.md），2018 版有没有改口无从得知 |
| **Three sector produce best EP** | [2024-05-06](https://stockbee.blogspot.com/2024/05/three-sector-produce-best-episodic.html) 正文空。**哪三个板块不知道** | 一个具体且可测的断言，但拿不到 |

**一句结论**：**他 2018 年之后的方法细节大量迁到了 YouTube 和会员站。** 博客文字的方法密度在 2010–2017 最高，2018 之后主要是每日盘面帖和视频链接。要更深只能看视频（不在本轮范围）或进会员站（付费，红线）。

---

## ② 我们缺数据 —— 逻辑清楚，字段没有

| # | 他的规则 | 我们缺的字段 | 能不能补 |
|---|---|---|---|
| Q1 | float `<10M` / `<25M` / `>100M` / `>500M` 四档 | **float / shares outstanding**（universe 105 字段里没有） | Finviz 有 `Shs Float` 列，取决于我们的抓取口径。**归 DATA ALEX** |
| Q2 | 「neglect」= 无分析师覆盖 | 分析师覆盖数 | yfinance `info` 有 `numberOfAnalystOpinions`，但 `info` 已是 429 重灾区（[[project_fundamentals_store]]：每晚预算 700 次）。**成本高** |
| Q3 | 年轻 EP：IPO ≤10 年 | **IPO 日期** | 我们有 2 年 OHLC，看不到 IPO。yfinance `info` 有 `firstTradeDateEpochUtc` |
| Q4 | 年轻 EP：**连续两季**营收增长 ≥39% | 我们只有单值 `revenue_growth`（79.8% 覆盖），**不是连续两季** | 需要季度序列，不是快照 |
| Q5 | 4% 突破的 `v > v1` | **昨日成交量** | universe 有 `volume` 和 `rel_volume`，**没有 v1**。但 `data/output/tickers/<T>.json` 的 ohlc 里有——只是没进 universe 行 |
| Q6 | `minl252` = 最低**收盘** 还是最低**低点**？ | 他自己注成 "lowest close"，但 Telechart 函数名是 min**l**（low） | 我们 `c_low52w` 用的是 `low_52w`（低点）。**两个口径的门槛不同**，值得量一次差多少 |

Q5 和 Q6 是**零外部依赖**的：数据都在本地 OHLC 里。Q1/Q2/Q3/Q4 需要新的数据源接入。

---

## ③ 可以验，但结论只能前瞻 —— 或需要专门的预注册

下面每条都是**可证伪的断言**，我们有数据。按 [`RESEARCH_PROTOCOL.md`](../../reference/RESEARCH_PROTOCOL.md) 必须**先预注册再跑**，且样本内正向结论默认当噪声（D 级证据）。

### V1. 「不连涨 3 天」到底有没有用（他唯二的硬数字之一）

> "They are not up 3 days in a row before start of the move." — [2018-02-14](https://stockbee.blogspot.com/2018/02/develop-your-setup-understanding-daily.html)

**为什么这条值得先测**：
- 它是九条 setup 闸里**唯二有确切数字**的（另一条是 float，我们没数据）；
- 它**没被 [[project_b4_gates_null]] 测过**——那轮测的是 ATR≤4 和涨幅≤8%，是**幅度类**闸，和「前置形态」正交；
- 完全用本地 OHLC 算得出，零外部依赖。

**预注册要点**：holdout 必须**开工前**划（[[pitfall_shipped_before_out_of_sample]]）。建议按**票池**划而不是按时段——`preset:4_bullish` 归档 88 个交易日的样本，按时段划会撞市况分层。

⚠️ 已知的坑：`b4_gates_null` 那轮的教训是「闸分得开 ≠ 跑赢 SPY」。**这次的度量应该直接钉死成「vs 同日 SPY 的超额」**，别再量绝对中位。

### V2. 整理期内「无 4% 下跌日」

同上，且这条更便宜——**我们已经有 4% 下跌日的归档**（`gainers_4pct` 的镜像已在 breadth 里逐日计数），只需按票回溯。

### V3. 「thrust 之后突破更好使」—— 他 2026 年的核心断言

> "This is what a breadth thrust is. Funds coming every day and buying. **This is where breakouts work and follow through.**"

**这是我们能验而他验不了的地方**：他手工看图，我们有 `breadth_store` 的逐日归档 + `ticker_events.csv` 的逐日筛子触发。
问法：**在「连续 N 日 up4 ≥300」之后 1–5 日内触发的 4% 突破，前瞻收益是否高于其他日子触发的？**

⚠️ 分层要求：这必须**按市况分层**跑（协议 §三 检查单）。thrust 天然发生在上涨初期，不分层就是在量「上涨时买涨会赢」。**对照组**：同期 SPY 自身的同窗口收益。

### V4. 「momentum burst 是 3–5 天」的形状检验

他给了明确的序列断言：range expansion → 跟进 → 跟进 → 回撤 → 结束，且 3–5 日内 8–20%。
这是**描述性**的，可以直接在归档上画分布：4% 突破日之后 1/2/3/5/10 日的累计收益分布，看峰在第几日。

**这条不需要 holdout**——它不是「有没有优势」的主张，是「形状长什么样」的描述。但**报出来时不能变成信号主张**（协议 铁律 2）。

### V5. 相对线性（ER-60）的自相关

> "smoother trends continue to be smooth and volatile trends continue to be volatile"

问法：ER-60 的 20 日自相关是多少？以及 **ER 高的票后续 20 日最大回撤是否更浅**（风险口径，不是收益口径）。

---

## 建议（不属我文件边界，只提不做）

| # | 建议 | 归谁 | 依据 |
|---|---|---|---|
| S1 | **EP 阈值重议**：我们 10%+$500M 是他 4%+3×量+30 万股的真子集，今天漏 47/55（85%），且市值方向与他相反 | **DATA ALEX**（`pipeline/screeners/episodic_pivot.py`） | [diff.md](diff.md) D1 |
| S2 | 给 universe 补 `prev_volume`（`v1`），使 `v>v1` 可算 —— 数据已在本地 OHLC 里 | **DATA ALEX** | Q5 |
| S3 | 评估补 `float` 字段（Finviz `Shs Float`）—— 他四档 float 规则全靠它 | **DATA ALEX** | Q1 |
| S4 | `delayed_ep_scan.py` docstring 那段行为描述标注「来源：视频，未文字核实」 | **DATA ALEX**（`pipeline/tools/` 里但属 EP 链） | ① 表第 1 行 |
| S5 | ER-60 做成独立字段（我在 `pipeline/tools/` 下做原型不进 universe） | 原型归我，入 universe 归 ALEX | [worth_learning.md](worth_learning.md) W1 |
| S6 | 「连续 N 日 up4 ≥300」读数加进 breadth —— 纯计算，数据全在 `breadth_store` | **DATA ALEX** | [diff.md](diff.md) G10 |

**Andy 要决定的**：S1 是**行为改动**（会改变每天看到的名字）。按 [[pitfall_shipped_before_out_of_sample]] 和研究协议，我的建议是**不要直接改阈值**，而是**先并排跑一个影子清单**（他的口径 vs 我们的口径，每晚各出各的），攒 4–6 周前瞻样本再谈。理由：EP 阈值这件事我们**从来没有验过**，现在这个 10% 也不是测出来的。

---

# ✅ 视频转录之后（2026-08-25 夜间轮）—— 五个优先问题的结算

Andy 08-24 批准做转录，点名优先补五个「文字里确认没有」的问题。**转录五支纯视频帖后，结算如下。**
全部参数与原话出处在 [`method_video.md`](method_video.md)。

| # | 优先问题 | 结算 | 答案 |
|---|---|---|---|
| 1 | **窄幅日的数字** | ✅ **答掉** | 「a narrow range day of **less than 2%**」；现场把 **2.1%** 判为不合格 → **2% 是硬线**。<br>⚠️ 我们 08-24 预注册用的是「窄于前 9 日中位」——**口径不同**（绝对 vs 相对） |
| 2 | **收盘接近高点的阈值** | ✅ **答掉** | 「close near high or **within 20% of high**」→ `(C−L)/(H−L) ≥ 0.80`。<br>⚠️ 我们用的是 **0.70，比他松**。08-24 那轮 B∧ 的结论是在松闸下测的 |
| 3 | **「本轮起点」怎么定** | ⚠️ **半答** | 他不给公式，**给判据**：C2 看「累计涨幅」而非天数——现场那只 up 3 天的票他算的是「already **11%** move」。<br>另有 C5「底 **5–40 天**」+ C6「底部期间不得有 4% 下破」把起点框住。**可机械化，但阈值是他的例子不是他的规则** |
| 4 | **「延展」几天算** | ✅ **答掉**（出场口径） | 出场 **3–5 天**为主，整体 **1–10 天**；「give it **2 days**，没跟进就出」。<br>持有窗口本身就是他对「延展」的定义：**超过 10 天这个方法不适用** |
| 5 | **哪三个板块出最好的 EP** | ❌ **仍无解** | 该视频（`Three sector produce best EP`）**不在本轮五支之内**——我只转了 `open_questions` 里点名的那五个帖对应的视频。**留着，下轮可补** |

## 新答掉的（不在那五个之内，但是本轮最有价值的两条）

- ✅ **止损放哪**：**入场日的当日低点**（全片重复六次），有经验可上移 20–25%；**明确否定 3 日宽止损**。
  他自报的实际单笔亏损是 −1.17% / −8 美分量级——**靠的是第二天没跟进就激进移损，不是靠初始止损宽度**。
- ✅ **`dollar = C − O` 这个零件**（文字帖里完全没有）：他把扫描结果按 `C−O` 排序，一次同时做
  「剔高开低走」+「过滤低价股」，并把**低价股占比**当情绪读数（多 = 投机、常在回调前）。

## ⭐ 两条本轮新发现的实质出入（不是「他没说」，是「我们做的和他说的不一样」）

### ① Delayed EP：主次颠倒 + 窗口几乎不重叠

- **主次**：视频里他说「especially in this video **I'm going to focus on short side**」，长边是最后一句附注
  （"can work **even** on the long side"）。**我们的 docstring 写反了，且扫描器只跑长边——我们实现的是他的附注。**
- **窗口**：我们 `--min-days 3 --max-days 15`；他的例子集中在 **次日 / 第 2 天 / 反弹 3–4 天**。
  **`--min-days 3` 恰好排掉了他最强调的那一天。**

### ② 入场口径：我们所有回测测的都不是他的交易

他 **从不在收盘入场**：「enter in the **first five, ten or twenty minutes**」，理由是**止损距离**不是收益。
我们的 `gainers_4pct` 是收盘后日线扫描，08-24 的 [`gate_results.md`](gate_results.md) 与今晚的
[`amplitude_2026-08`](../amplitude_2026-08/results.md) **全部以事件日收盘为入场点**。
**这不是参数差异，是口径差异**——任何引用那些数字的地方都该带这句话。

## 给 DATA ALEX 的建议（追加，仍不属我的文件边界，只提不做）

| # | 建议 | 归谁 | 依据 |
|---|---|---|---|
| **S7** | `delayed_ep_scan.py` docstring 的 **long/short 主次改回来**，并把 S4 那条「未文字核实」标注**升级为「已由视频核实，来源：Rm9f2E-mygM」** | **DATA ALEX** | §六 ① |
| **S8** | `delayed_ep_scan.py` 的 `--min-days` 默认值从 **3 改到 1**（或至少并排跑一版 1–4 天窗口的影子清单）——他最强调的次日入场现在被默认值排掉了 | **DATA ALEX** | §六 ① |
| **S9** | `gainers_4pct` / `stockbee_ratio` 的 docstring 加一句**入场口径声明**：「我们的事件日=收盘，他的入场=开盘后 5–20 分钟；两者的前瞻收益不可互相引用」 | **DATA ALEX** | §六 ② |
| **S10** | 4% 扫描结果里的**低价股占比**做成每日读数进 breadth（纯计算，数据已在归档里）——他把这个当回调前兆 | **DATA ALEX** | `method_video.md` §五 |

**我自己能做且已排队的**（`data/research/` 内，不碰 ALEX 的文件）：用**他的** B1=0.80 与 B2=「绝对 <2%」重跑
08-24 那轮闸研究，看结论会不会变。⚠️ **那轮的 holdout 已烧**，重跑只能算 discovery，需要新的 holdout 划分——
下一轮开工前先写预注册。
