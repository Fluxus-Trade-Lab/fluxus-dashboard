# Stockbee 方法 —— 写成可执行参数

> **读法**：引用块 = Pradeep Bonde 原文（一字不改，含原拼写），链接指到那一篇。引用块外的正文和表格 = 我们的整理。
> 一条规则在他文章里反复出现且措辞漂移时，**列出全部版本并标日期**——漂移本身就是 nuance。

---

## 0. 他的世界观（所有三个 setup 的同一个母题）

> "The basic structural phenomenon behind most ideas discussed on this site is ' Stocks move in short term Momentum Bursts'"
> — [Swing trading using momentum bursts, 2014-01-28](https://stockbee.blogspot.com/2014/01/swing-trading-using-momentum-bursts.html)

> "Range Expansion, range contraction, Range Expansion, range contraction. that is the cycle. If you understand that you will be able to find anticipation setups."
> — [Key to understanding anticipation setup, 2019-01-18](https://stockbee.blogspot.com/2019/01/key-to-understanding-anticipation-setup.html)

三个题目不是三个策略，是**同一个循环的三个进场时点**：

| | 进场在循环的哪一段 | 他的原话定位 |
|---|---|---|
| **Anticipation** | 收缩段末尾，扩张之前 | "Buy before momentum burst in anticipation" |
| **Momentum Burst / 4% b/o** | 扩张的第一天 | "buy on first day of momentum burst" |
| **Episodic Pivot** | 由**消息**驱动的那次扩张 | "Episodic Pivots offers an entry into the move right at the beginning" |

> "Buy before momentum burst in anticipation (Stockbee Anticipation setup) or buy on first day of momentum burst (Stockbee 4% and $ breakouts setup)"
> — [Understanding nature of stock moves, 2018-05-09](https://stockbee.blogspot.com/2018/05/understanding-nature-of-stock-moves.html)

**关键的量化断言**（这是可被我们的归档证伪的部分）：

> "In this kind of momentum burst move in a stock , the first day is range expansion which is immediately followed by follow through. The sequence looks like: Range expansion day / Up day (follow through) / Up day (follow through) / pullback / followed by end of momentum"

> "During this 3 to 5 days period stock would go up 8 to 20% ( lower priced stock can even have bursts of up to 40%)."

> "In a year you will probably find 5000 to 10000 such 3 to 5 day setups when both bullish and bearish setups are combined."

> "If you study the stocks up 25% or more in a month you will see that they make bulk of their move in 3 to 5 days out of 21 trading days in a month."
> — [My process loop to trade 4% b/o and $ b/o, 2017-07-13](https://stockbee.blogspot.com/2017/07/my-process-loop-to-trade-4-bo-and-bo.html)

---

## 1. Momentum Burst / 4% 突破

### 1.1 扫描（他给了确切公式，且 2014→2017 只改了一处）

| 版本 | 公式（Telechart/TC2000） | 出处 |
|---|---|---|
| 2014-01 | `c/c1>=1.04 and v>v1 and v>100000` | [Swing trading using momentum burst, 2014-01](https://stockbee.blogspot.com/2014/01/swing-trading-using-momentum-burst.html) |
| 2015-11 | `c/c1>=1.04 and v>v1 and v>=100000` | [How to use the 4% breakout scan, 2015-11-18](https://stockbee.blogspot.com/2015/11/how-to-use-4-breakout-scan-to-make-money.html) |
| 2017-07 / 2017-10 | `c/c1>=1.04 and v>v1 and v>100000` | [Process loop, 2017-07](https://stockbee.blogspot.com/2017/07/my-process-loop-to-trade-4-bo-and-bo.html) |

拆成三个条件：

| 参数 | 值 | 他的说明（原文） |
|---|---|---|
| 涨幅 | `c/c1 >= 1.04` | "The stock should be up 4%," |
| **量比昨日** | `v > v1` | "volume should be higher than yesterday" |
| 量地板 | `v > 100,000` 股 | "volume should be greater than 100000" |

**⚠️ 口径陷阱（我们踩过的那类）**：Telechart 的 `V` 单位是**百股**。他 2010 年的 EP 扫描里 `V > 10000` = 100 万股。但 4% 扫描里他自己用文字确认了是「100000」股面值。引用他任何含 `V` 的公式前，先看他有没有配文字说明。

**姊妹扫描 —— $ breakout**（高价股用，因为高价股很少一天涨 4%）：

> "c-o>=.90 and v>100000 ... The scan looks for a stock up 90 cents plus. It is more useful on high priced stocks above 40 as they do not often breakout with 4% move."
> — [Process loop, 2017-07](https://stockbee.blogspot.com/2017/07/my-process-loop-to-trade-4-bo-and-bo.html)

注意 `c-o`（收盘−**开盘**），不是 `c-c1`。这是当日实体，不是隔夜跳空——**他的 $ 突破明确排除跳空**。

### 1.2 setup 质量闸（扫描给候选，这七条才是他挑票的地方）

> "Once you run the scan you will get several stocks meeting the scan conditions , but they are all not buy candidate."

他 2017 年两篇一字不差地列了同一张单子（原文逐条）：

> - stock should close near high
> - prior to b/o day there should be a narrow range or negative bar
> - stock should not be up 3 days in a row
> - stock should have a narrow range sideways consolidation or narrow range orderly shallow pullback prior to b/o day
> - the previous leg of up move should be linear
> - the breakout should be first to third setup since start of the move
> - as far as possible look for young trend and not extended trend ( youngsters defined by number of days stock has been rallying in overall move)
> - first and second pullback/consolidation in rally are preferable
> - extended rallies are vulnerable to correction and b/o failure
>
> — [How to find good breakouts daily, 2017-10-19](https://stockbee.blogspot.com/2017/10/how-to-find-good-breakouts-daily.html)

2014 年版本多两条**票性**要求：

> - Low float below 25 million is good. Below 10 million float leads to explosive moves
> - Low priced stocks (below 5 dollar) tend to make very explosive moves of 40% kind in 3 to 5 days.
> - A very volatile stock exhibiting drunken man walk kind moves should be avoided
> - The stock will have 3 to 20 days consolidation prior to range expansion day
>
> — [How to Identify good momentum burst, 2014-01-04](https://stockbee.blogspot.com/2014/01/how-to-identify-good-momentum-burst-and.html)

2016 年版本多一条**量的形状**：

> - volume during consolidation should be preferably orderly and lower
>
> — [Guidelines to find good momentum burst setups, 2016-07-12](https://stockbee.blogspot.com/2016/07/guidelines-to-find-good-momentum-burst.html)

**整理成可执行参数**（我们的编号，用于 `diff.md` 逐格对照）：

| # | 闸 | 可执行化 | 阈值来源 |
|---|---|---|---|
| B1 | 收盘接近当日高 | `(c−l)/(h−l) >= ?` | **他没给数字**（"at or near its high"） |
| B2 | 前一日窄幅或阴线 | `range[−1] < 近N日中位` 或 `c[−1] < c[−2]` | **窄幅无数字** |
| B3 | 不得连涨 3 天 | `not (c1>c2 and c2>c3 and c3>c4)` | 有确切数字 **3** |
| B4 | 突破前有整理/浅回撤 | 3–20 日（2014）/ 3–10 日（anticipation 版） | **两处不同，见下** |
| B5 | 前一段上涨要线性 | Kaufman ER（他 2011 年给了公式，见 §4.1） | 有公式，**无阈值** |
| B6 | 是本轮的第 1–3 次突破 | 需要「本轮起点」定义 | **他没给起点定义** |
| B7 | 趋势要年轻不能延展 | "youngsters defined by number of days stock has been rallying" | **无数字** |
| B8 | 低 float | `<25M` 好，`<10M` 爆炸 | 有确切数字 |
| B9 | 整理期量要低且有序 | — | **无数字** |

**⚠️ 九条里只有 B3 / B8 有硬数字。** 剩下七条他明确说是靠练出来的眼力：

> "Identifying good setup is a skill developed through practice. If you go through 5000 to 10000 old setups and identify good from bad and see what worked and how it worked, you will gain expertise"
> — [2014-01-04](https://stockbee.blogspot.com/2014/01/how-to-identify-good-momentum-burst-and.html)

### 1.3 入场时点

> "Scan should be run from market opening onwards and once a good setup shows up should be entered as soon as you identify it. That will help you capture rest of the days move. You can also use it for end of the day scanning and enter next day."
> — [2015-11-18](https://stockbee.blogspot.com/2015/11/how-to-use-4-breakout-scan-to-make-money.html)

> "In process term I run the above scan from 9:30 onward and look for candidates meeting setup definition. As and when they show up I enter."

**盘中反复跑**，不是收盘一次。他承认这吃掉了一部分涨幅：

> "By the time you enter on breakout day the stock might be up 4 to 10 %, so you will not be able to capture that part of the range expansion move."

### 1.4 止损

| 情形 | 止损 | 出处 |
|---|---|---|
| 默认 | **入场当日的低点** | "That logically makes our stop the low of entry day."（[2015-11](https://stockbee.blogspot.com/2015/11/how-to-use-4-breakout-scan-to-make-money.html)） |
| 视入场位置 | 入场日**半个日内区间** | "Stop is low of the entry day or half the days range depending on where I enter."（[2018-07-27](https://stockbee.blogspot.com/2018/07/my-exit-guidelines-for-momentum-burst.html)） |
| 硬上限 | **≤4%，理想 ≤2%**；高价股更近 | 同上 |

> "As far as possible I try and keep stop less than 4% and ideally less than 2%. On high priced stocks my stops are even closer."

**止损逻辑的推理链他写清楚了**——止损位不是画出来的，是**从持仓理由推出来的**：

> "The only reason to buy a 4% breakout is that we expect immediate follow through on the move. That logically makes our stop the low of entry day."

### 1.5 退出（最细的一节，全是数字）

原文逐条（[My exit guidelines for momentum burst swing trades, 2018-07-27](https://stockbee.blogspot.com/2018/07/my-exit-guidelines-for-momentum-burst.html)）：

> - Exit if a stop is hit. Stop is low of the entry day or half the days range depending on where I enter. As far as possible I try and keep stop less than 4% and ideally less than 2%. On high priced stocks my stops are even closer.
> - Exit on 3rd or 5th day (for $ b/o) if stock does not move much post entry. This indicates momentum burst got aborted after one day move
> - Exit at least 50% of position on third or fifth day at close. 80% of trades would be 3 days hold. By third day the moment stocks goes up start protecting profit by moving stop 25 to 50 cents below the high. This needs to be done intraday as many big impulse move can fade quickly.
> - After your entry next day or same day if the stock goes up 8% or more exit 50% of the position and move stop 25 to 50 cents below the high of the day to protect profits.
> - Exit a stock in pre market or at open if it gaps up 20% or more after your entry next day or third day.
> - After 3rd day if you want to keep holding keep moving stop to low of day everyday after that.

**参数表**：

| 触发 | 动作 | 数字 |
|---|---|---|
| 涨 **≥8%**（同日或次日） | 减 **50%**，止损移到当日高点下 **25–50 美分** | 8% / 50% / $0.25–0.50 |
| 第 **3 或 5** 日收盘 | 至少减 **50%** | 80% 的交易是 **3 日持仓** |
| 3 日内不动 | 全出 | — |
| 跳空 **≥20%** | 盘前或开盘全出 | 20% |
| 过第 3 日仍持有 | 止损每日上移到**当日低点** | — |
| 加仓 | **他从不提加仓** | 见 [open_questions.md](open_questions.md) |

利润目标（更早的口径）：

> "I am typically looking at 8 to 20% profit target on my swing trades and 40 to 50% target on my Episodic Pivots trade. I sell when stock reaches my profit objective. I sell in parts so most of the time I peel off positions in units of 1/4th."
> — [Q&A with Pradeep Bonde, 2011-06-27](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)

**⚠️ 分批口径漂移**：2011 年是**四分之一**分批，2018 年是**一半**。日期在，别当成同一条。

### 1.6 他自己说什么情况下**不做**

> "There are periods in market where these kind of setups are prone to failure. This happens near market turns where in short period lot of breakouts fail. **The bullish breakout trade needs to be avoided during fast selling phases in market.**"
> — [2018-05-09](https://stockbee.blogspot.com/2018/05/understanding-nature-of-stock-moves.html)

> "The bearish breakdown trade works best after a downtrend is clearly established on 10 plus day time frame. In a bull market trading 3 day bearish setups will lead to lot of failed breakdowns."

> "Breakouts fail during certain market phases. Even the best looking breakout with catalyst does not work in bearish phases."
> — [Q&A, 2011](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)

> "This market has not been very favorable to trading breakouts currently. ... Personally I have been in cash for some time as I do not see the kind of setups I look for."
> — 同上

**这就是 Market Monitor 的用途**（见 §3）：不是选股，是决定**今天做不做突破**。

### 1.7 他怎么判「失败」

> "Once you are in the trade either the stock will follow through or fail. If it fails your stop will take you out. **If it follows though but the follow through is weak then by 3rd day you can be out.**"
> — [2015-11](https://stockbee.blogspot.com/2015/11/how-to-use-4-breakout-scan-to-make-money.html)

失败有**两种**，各有各的出法：① 打止损；② **跟进无力**——不打止损，靠第 3 日时间闸出。

他自己的胜率与赔率（他写了真实数字）：

> "Last year only 50.5% of my trade in this method were profitable but the winning trade produced more profit than losing trades." … "That 1.62/1 ratio still produced 73.75% return for the year."
> — [When breakouts fail, 2014-01-24](https://stockbee.blogspot.com/2014/01/when-breakouts-fail.html)

> "As of now 56% of the trades have worked ... on a longer term 14 years time frame also the batting average of kind of swing trading methods I trade is above 50%."
> — [When breakout fails, 2014-06-11](https://stockbee.blogspot.com/2014/06/when-breakout-fails.html)

以及一个仓位/风险的实例（**这是他唯一一次给出具体仓位百分比**）：

> "In LM trade I had 20% of account invested, but my risk was only .25%. Risk = entry-stop. So the trade not working resulted in just .28% loss on overall capital"
> — [2014-01-24](https://stockbee.blogspot.com/2014/01/when-breakouts-fail.html)

→ 20% 仓位 × 1.25% 止损距离 = 0.25% 账户风险。**仓位由止损距离反推**，不是固定比例。

---

## 2. Anticipation（蓄势）

### 2.1 两步：先「有动量」，再「今天很静」

**第一步 —— 强度扫描（三选一，OR 关系）**

| 名 | 公式 | 含义 | 出处 |
|---|---|---|---|
| **Double Trouble (DT)** | `c/minl252>=1.8 and minv3.1>=100000` | 离 252 日最低点涨了 80%+ | [2014-03-04](https://stockbee.blogspot.com/2014/03/how-to-anticipate-breakout.html) |
| **TI65** | `avgc7/avgc65>1.05 and minv3.1>100000` | 7 日均价 / 65 日均价 | [2014-08-14](https://stockbee.blogspot.com/2014/08/how-i-generate-my-breakout-anticipation.html) |
| **MDT** | `c/avgc126>1.19 and minv3.1>100000` | 收盘 / 126 日均价 | [2016-04](https://stockbee.blogspot.com/2016/04/how-to-find-bullish-anticipation-setups.html) |

他自己给了符号表：

> "c= close today / minl252= lowest close in 252 days / minv3.1= minimum volume in last 3 days"
> — [How to anticipate a breakout, 2014-03-04](https://stockbee.blogspot.com/2014/03/how-to-anticipate-breakout.html)

**⚠️ 注意 `minl252` 他自己注成「lowest CLOSE in 252 days」**，不是最低**低点**。Telechart 里 `minl` 字面是 min low——**他的注解和函数名不一致**。用哪个口径会改变门槛，见 [open_questions.md](open_questions.md)。

**⚠️ TI65 阈值三个版本**（时间上在漂）：

| 日期 | 阈值 | 出处 |
|---|---|---|
| 2014-08 / 2015-05 / 2015-10 / 2016-04 / 2017-03 / 2017-04 | `avgc7/avgc65 > 1.05` | 多篇一致 |
| **2018-08** | `avgc7/avgc65 > 1.04` | [How to scan for anticipation setups](https://stockbee.blogspot.com/2018/08/how-to-scan-for-anticipation-setups.html) |
| 2018-08（$39+ 高价股专用扫描） | **`.95 到 1.05` 之间** | 同上 |

最后一行是个**反直觉的 nuance**：高价股的蓄势扫描里 TI65 要求**在 0.95–1.05 区间内**——即「不强不弱」，和低价股要求「>1.04 才算强」是**相反方向**。

**第二步 —— 今天很静**

| 日期 | 静的定义 | 出处 |
|---|---|---|
| 2014-08 / 2015 | Price % change today 在 **−1% 到 +1%** | [2014-08-14](https://stockbee.blogspot.com/2014/08/how-i-generate-my-breakout-anticipation.html) |
| **2018-08 多头版** | **−0.4% 到 +0.4%**，且 Price History Net change 在 **−0.2 到 0.2**，且 price > **$3** | [2018-08-10](https://stockbee.blogspot.com/2018/08/how-to-scan-for-anticipation-setups.html) |
| 2018-08 空头版 | −1% 到 1%，`minv3.1>=300000`，TI65 **< 0.95**，price > **$15** | 同上 |
| 2018-08 $39+ 版 | −0.4% 到 0.4%，`minv3.1>=300000`，price > **$39** | 同上 |

**静的口径 4 年里收紧了 2.5 倍**（±1% → ±0.4%）。他没解释为什么。

### 2.2 图形闸（他 2014/2015/2018 三次一字不差地重复同一张单子）

> - series of narrow range days in pullback/consolidation
> - orderly pullback with no 4% b/d during the pullback or consolidation
> - low volume pullback
> - low volatility during pullback
> - linear first leg if looking as continuation setup
> - Stock should go up smoothly and not in volatile manner
> - 3 to 10 days consolidation/pullback
> - not up 3 days in a row
>
> — [How to find Anticipation setups, 2015-02-19](https://stockbee.blogspot.com/2015/02/how-to-find-anticipation-setups.html)（2014-08、2018-05 逐字相同）

**其中第 2 条是可执行的硬数字，而且是个巧妙的自指闸**：整理期内**不许出现一根 4% 下跌日**——他用自己的 4% 扫描当质量过滤器。

**额外的两条排除**（2015-02）：

> "Avoid Anticipation setups on extended stocks. First or second anticipation setup in established trend is best. As stock goes further and further from its rally start point the probability of anticipation setup working decreases. Extended trends needs to be avoided for anticipation as failure is high on them"

> "To anticipate a breakout look at stocks currently not undergoing momentum burst. That means stock should not be going up or down fast. Stock should be in extremely low momentum phase for anticipation ."

### 2.3 入场与止损（他给了确切的美分）

> "Ideal entry is where you risk just few cents or less than 2% to get in early. This requires either entering before breakout or entering with a order few cents above yesterday's action."
> — [2015-02-19](https://stockbee.blogspot.com/2015/02/how-to-find-anticipation-setups.html)

> "Anticipating a breakout gives you an opportunity to enter potential breakout stock ahead of actual breakout or **within first 10 to 40 cents of its breakout** depending on price."
> — [How to profit from good anticipation setups daily, 2018-05-03](https://stockbee.blogspot.com/2018/05/how-to-profit-from-good-anticipation.html)

实例（ARNA）：

> "I entered it in first 7 minutes with very close 20 cents stop."

**时间窗**：

> "Most good anticipation setups breakout in first 10 to 15 minutes of open."
> — 同上

**执行细节**（他明确说执行本身是 edge）：

> "for select few stocks out of the above watchlist I already had 2 orders ready one a limit order at predetermined price slightly above their current price and another market order. that way if a stock goes up quickly and barrels through your limit price I can quickly trigger market price."
> — [How to use your anticipation watch list to make money, 2017-02-09](https://stockbee.blogspot.com/2017/02/how-to-use-your-anticipation-watch-list.html)

或用 Buy Stop Limit Order：

> "Identifying this stock previous night allows you to watch it intently next day or create a Buy Stop Limit Order (BSLO) and enter as it breaks out of the narrow consolidation."

### 2.4 漏斗的确切宽度（这是他给的最有用的一组数字）

> "It takes me around 15 minutes to generate my list of candidates daily. I look at around 100 to 300 candidates to boil down to just 1 to 3 good candidates for entry next day."（2015-02）

> "…to boil down to just 1 to 5 good candidates"（2018-05，同一句话，上限从 3 改成 5）

> "Once a list is generated I reduce it to 3 to 5 candidates to focus on."（2014-08）

> "Only 3 to 5 quality ideas should be tracked ... Focusing on too many often leads to missing out on some very good low risk entries."（2015-02）

> "These scans should give you around 600 to 800 A quality anticipation setups in a year once you know what to look for in a good setup"（2018-08）

**漏斗**：扫描 → **100–300** 看 → **1–5** 下单 → 一年 **600–800** 个 A 级。

---

## 3. Episodic Pivot（EP）

### 3.1 定义

> "Episodic Pivots is a news or catalyst based setup. When a company announces surprisingly good or bad news the market reacts to it. Because markets are not efficient the move does not end in a day. The stock continues to go up or down for weeks or months post such big news."
> — [Q&A, 2011-06-27](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)

理论根基他点名了：

> "Ball and Brown in 1968 first documented the PEAD anomaly."
> — [What are Episodic Pivots and how to find them, 2010-02-12](https://stockbee.blogspot.com/2010/02/what-are-episodic-pivots-and-how-to.html)

### 3.2 扫描（**三个不同版本，阈值差一倍**）

| 日期 | 公式 | 门槛 |
|---|---|---|
| 2007-02 | 五条 OR：`(100*(C-C1)/C1)>=20 & V>10000 & C>=5` … `>=30 & V>3000` … `(C-C1)>=5 & V>10000` … `>=10 & V>1000` … `C>C1 AND V>5*AVGV50.1 AND V>3000 AND C>5` | 极宽，**日出 20–25 只** |
| 2010-02 | `((C-C1)>=5 AND V>10000 AND C>=62.50 AND V>V1) OR (((100*(C-C1)/C1)>=8 AND V>3000 AND (100*V/AVGV100)>=300) AND C>1)` | **8%** + **3× AVGV100** |
| **2014-07** | `c/c1>1.04 and v>3*avgv50.1 and v>=300000` | **4%** + **3× AVGV50** + 30 万股 |

> "During the day Run EP scan c/c1>1.04 and v>3*avgv50.1 and v>=300000 multiple times , see if there is stock with neglect+ game changing earnings"
> — [My process flow for Episodic Pivots (EP), 2014-07-30](https://stockbee.blogspot.com/2014/07/my-process-flow-for-episodic-pivots-ep.html)

**⚠️ 最重要的一条 nuance**：他 2014 年的 EP 扫描门槛是 **4%**，不是 8%、更不是 10%。**大跳空不是 EP 的定义**——「surprise」的证据是**量**（3× 均量），价格只要 4%。价格阈值高只是在**筛掉小的 surprise**，代价是漏掉起点。

### 3.3 扫描之后才是 EP（他明说不是机械策略）

> "So a stock appearing in such a scan has a volume surge and the price surge. We then investigate what caused this price and volume surge or what was 'the surprise' that caused such a big move and what is 'the nature' of such surprise."

四问（原文）：

> - Context of the earnings. Is this a first major earnings acceleration.
> - What caused this acceleration. Is it one time or likely to persist.
> - Does this earnings trend represent a structural change in the industry or the position of this company.
> - Is this surprise reflected in current price level.

> "Studying episodic pivots on daily basis can be profitable strategy. **It is not a purely mechanical strategy.**"
> — [Episodic Pivots and "Idea Pickle", 2007-02-26](https://stockbee.blogspot.com/2007/02/episodic-pivots-and-idea-pickle.html)

### 3.4 什么样的票（**全是硬数字，且和「大盘股更安全」的直觉相反**）

**float**：

> "Earnings Breakouts and low float — This is an ideal combination. In such situation you can have really explosive move. **Float below 25 million is ideal** for this. **The best moves happen on float below 10 million.** Earnings breakouts on **companies with 100 million plus float tend to have pullbacks**. Earnings breakout on stock with **500 million plus float is something which I not really very enthusiastic about** unless they are trading near their historic lows or are in single digits."
> — [2010-02-12](https://stockbee.blogspot.com/2010/02/what-are-episodic-pivots-and-how-to.html)

**是否有分析师覆盖**（他的「neglect」概念）：

> "Stocks with no analyst coverage are typically smaller companies or companies which are out of favor. On such stocks a significant earnings acceleration compared to last year same quarter as well as quarter over quarter is what to look for. **I like to look for companies which had earnings acceleration of 100% plus in such cases.**"

> "**Earnings breakout on companies with significant analyst coverage do not do as well as the first kinds.** Genuine analyst surprises are rare and in many cases company pre announce and manage earnings expectations to avoid significant surprise. Established companies also often time secondaries and other capital raising events to time with such surprises and so often you find the EP on such stocks tend to have a pullback."

**量的量级**：

> "If volume is very high, you can assume move has legs. You will see that most earnings breakouts which go on to make really big (like say 100% plus kind of) moves in next 1 to 2 months post an earnings, will have **huge volume surge, typically of 10 times or more compared to average volume**. In many cases the volume on earnings day might be the **highest volume in the history of the stock** or multi year high volume."

**2025 年新增的「年轻 EP」筛子**（他 2025-09 给的确切参数）：

> "The most explosive Episodic Pivots occur in stocks that have Gone Public in the last 10 years and have a capitalization of less than $ 10 billion once they enter their growth phase."

> "This scan finds stocks incorporated or IPOed in last 10 years that have a market capitalization below 11 billion and have **two quarters of revenue growth of 39% plus**."
> — [Find the young Episodic Pivots, 2025-09-01](https://stockbee.blogspot.com/2025/09/find-young-episodic-pivots.html)

（注意他自己文中 `$10 billion` 和扫描里 `11 billion` 不一致——原样保留。）

**20 类催化剂**（原文清单，2010-02）：

> Earnings Growth 100% plus / Earnings 40% plus / Earnings Beats by wide margin / Earnings Other / Sales 100% plus but no earnings / IPO Breakout / Retail / Top Sector / New order or contract /new order rumor / Buyout/buyout rumor/mergers/ tie ups/division sale / New product launch/news / Regulatory Changes / Drug Approval / Drug /marketing Tie Up / Natural disaster/ war/ disease / Shortages / Rate Increase / Media Mention / Analyst upgrade/downgrade / Declares Dividend / Financial Engineering / Junk of the bottom rally

他自己给催化剂**分了高低概率**：

> "Earnings, new product, analyst earnings change, increased earnings guidance, sector moves etc **have high probability** to trigger multi month rallies. James Crammer, Barron's, WSJ, and other publication mentions, analyst upgrade etc. **have a low probability of follow through.**"
> — [2007-02-26](https://stockbee.blogspot.com/2007/02/episodic-pivots-and-idea-pickle.html)

**⚠️ 自相矛盾**：analyst upgrade 同时出现在 2010 的 20 类清单里和 2007 的「低概率」里。原样保留。

### 3.5 日内流程（他给了完整时刻表）

> - After market close earnings: … I track Briefings earnings page and IBD earnings summary
> - After Market Earnings Guidance: Earnings Whisper email
> - After market close price gainers: … WSJ page
> - Before open earnings: … Briefings calendar
> - Before Market Price gainers: I use IB scanner … **This scanner I open from 7 AM onwards**
>
> — [How to become good at trading Episodic Pivots, 2010-02-12](https://stockbee.blogspot.com/2010/02/how-to-become-good-at-trading-episodic.html)

2014 版流程（三个时段的三个不同门槛）：

> "Analyse all **after hours movers up 4% plus on 50k volume** … Pre market Run IB scanner to find stock **up on 50k plus volume and up at least 2%** … During the day Run EP scan `c/c1>1.04 and v>3*avgv50.1 and v>=300000`"

**盘后 4%/50k → 盘前 2%/50k → 盘中 4%/3×量/300k**。门槛按时段变，盘前最松。

### 3.6 EP 的进出

> "If I find a good EP I buy immediately in pre or post market. **Most EP where I made big money I bought in pre market.**"
> — [2014-07-30](https://stockbee.blogspot.com/2014/07/my-process-flow-for-episodic-pivots-ep.html)

> "I am typically looking at 8 to 20% profit target on my swing trades and **40 to 50% target on my Episodic Pivots trade**."
> — [Q&A, 2011](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)

> "At other spectrum I trade a different earnings breakout based method where my objective is to have **greater than 70% win rates** and also to have very high return per trade. In that kind of setups I look for **several multiples of my initial risk**. Obviously you do not find many trades like that on day to day basis and you have to be extremely selective"
> — [When momentum bursts fail, 2014-01-08](https://stockbee.blogspot.com/2014/01/when-momentum-bursts-fail.html)

**两套完全不同的期望**：Momentum Burst 50–56% 胜率 / 8–20% 目标；EP >70% 胜率 / 40–50% 目标 / 数倍 R。

**⚠️ Delayed EP（我们 `delayed_ep_scan.py` 的立论来源）在博客文字里查无实据。** 2023-05-03 的 [Episodic Pivots Delayed Entry](https://stockbee.blogspot.com/2023/05/episodic-pivots-delayed-entry.html) 正文是**空的**（只有视频）。2025-09 那篇只顺带提了一句：

> "It also helps to enter them as delayed reactions EP."

见 [open_questions.md](open_questions.md) §1。

---

## 4. 贯穿三个 setup 的两条底层规矩

### 4.1 相对线性 —— 他的第一否决项

> "The most important thing I look for any stocks chart is relative linearity. I always look for stocks that are trending smoothly. I pass on volatile stocks that jump all over the place."

> "**Relative linearity is my most important criteria for eliminating stocks. If a stock does not have relative linearity, I do not even look at rest of the criteria and will not buy a breakout on it.**"
> — [Q&A, 2011-06-27](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)

度量方法他给了（Kaufman / Fractal Efficiency Ratio，60 日）：

> "Fractal Efficiency ratio is derived by dividing the net change in price movement over n periods by the sum of all component moves, taken as positive numbers, over the same n periods. If the ratio approaches the value 1, then the movement is smooth, if the ratio approaches 0, then there is great inefficiency or chaos."

Telechart 公式（60 日版，他原文给了展开式，此处只记结构）：

```
(C - C60) / ( Σ_{i=0..59} ABS(C_i - C_{i+1}) + 0.001 )
```

> "The above formula scan will give you values between 1 to -1. If you sort by this scan, the higher ratio stocks will have smoother trends lower readings will show very volatile stocks."

> "My general observation is that smoother trends continue to be smooth and volatile trends continue to be volatile."

**⚠️ 他没给阈值**——他用它**排序**再用眼睛砍，不是设一个数。

### 4.2 动量周期：130 天 → 65 天

> "Primarily I have reduced the period used for calculating momentum from 130 days to 65 days. **Markets are faster and a shorter momentum period can help you find new trends faster.**"
> — [Q&A, 2011-06-27](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)

TI**65** 的 65 就是这么来的。他把「市场变快了」当成可以调参数的事实——2011 年的话，到 2026 年这个方向大概率只会更极端。

---

## 5. Market Monitor（他的择时层，管「今天做不做」）

十个计数（[Market Monitor Scans, 2022-12-24](https://stockbee.blogspot.com/2022/12/market-monitor-scans.html) 原文标题逐条）：

> Number of stocks up 4% plus today / down 4% plus today / up 25% plus in a quarter / down 25% plus in a quarter / up 25% plus in a month / down 25% plus in a month / up 50% plus in a month / down 50% plus in a month / up 13% plus in a 34 days / down 13% plus in a 34 days

用法：

> "The Market Monitor is currently in bearish mode. From around December of 2010 we have seen rallies on progressively lower breadth. As of now we have not reached extreme bearish readings on Market Monitor. **Extreme bearish readings on MM are bullish.**"
> — [Q&A, 2011](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)

**2026 年他给了「thrust」的确切形状**：

> "When funds pour in money, you see blocks of buying like this, **back-to-back 300-plus days**. This is not driven by retail."

> "This is what a breadth thrust is. Funds coming every day and buying. **This is where breakouts work and follow through.**"

> "Market breadth is market-derived information that tells you when buying or selling is dominating in the market. Using this information to time breakouts helps us **improve win rates and avoid drawdowns**."
> — [Understand market breadth, 2026-07-23](https://stockbee.blogspot.com/2026/07/understand-market-breadth.html)

**关键 nuance**：thrust 不是「某一天 300+」，是「**连着几天** 300+」。单日 300 在他这里不构成资金进场的证据。
