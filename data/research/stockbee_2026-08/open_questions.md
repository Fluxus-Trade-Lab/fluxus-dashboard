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
