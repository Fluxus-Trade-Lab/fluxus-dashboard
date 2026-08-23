# 三题之外，他站上值得学的东西

Andy 说三个题目是起点不是边界，让我主动列。每条：**是什么 / 为什么值得 / 我们能拿它干嘛**。
按「能不能立刻变成我们仓库里的东西」排序。

---

## W1. 相对线性（Kaufman Efficiency Ratio）当**第一否决项**

**是什么** —— 他把「这只票走得顺不顺」放在所有条件之前：

> "Relative linearity is my most important criteria for eliminating stocks. **If a stock does not have relative linearity, I do not even look at rest of the criteria** and will not buy a breakout on it."
> — [Q&A, 2011-06-27](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)

度量给全了：60 日 Kaufman/Fractal Efficiency Ratio = 净变化 ÷ 逐日绝对变化之和，取值 −1~1。他不设阈值，用它**排序**再用眼睛砍。

**为什么值得** —— 这是**排除性**知识，比选择性知识稀缺。他给的机制解释是可证伪的：

> "My general observation is that smoother trends continue to be smooth and volatile trends continue to be volatile."

**"平滑性有自相关"** 是个干净的、能在我们 2 年 OHLC 上直接测的假设。而且他给了**为什么**：线性 = 有持续买盘在托，回撤浅、止损位逻辑清楚。

**我们能拿它干嘛**
1. 加一个独立字段 `er_60`（我们已有 2 年 OHLC，零外部依赖）。目前 Kaufman ER 只作为 VCS v2 内部一个加权项存在，**不能排序、不能当闸**（见 [diff.md](diff.md) D5）。
2. 直接可测的问题：**ER 高的票，后续 20 日回撤是不是真的更浅？** 这是「风险口径」的问题，不是「收益口径」——恰好绕开了 [[project_b4_gates_null]] 撞的那堵墙（闸分得开但中位跑不赢 SPY）。
3. 和我们已有的 `adr_pct` 是**正交**的：ADR 量「一天动多少」，ER 量「动得顺不顺」。一只 ADR 8% 的票可以 ER 很高（天天涨一点）或很低（上下乱甩）。

---

## W2. 每日深潜（Daily Deep Dive）—— 把学习做成扫描

**是什么** —— 他每天早上第一件事不是找交易，是**研究上周的赢家**：

> "First thing in the morning I obsessively study stocks that make 8% moves and 5 dollar plus moves in 5 days. Those are the kind of stocks I want to be in next week."
> — [Develop your setup understanding daily, 2018-02-14](https://stockbee.blogspot.com/2018/02/develop-your-setup-understanding-daily.html)

扫描（他给了公式）：

```
Bullish 8%+/5 日:  c/c5>=1.08 or c-c5>5 and minv3.1>100000 and c>=5
Bullish 20%+/1 周: c/c5>=1.2  and minv3.1>100000 and c>=5
Bullish 50%+/40 日: c/c40>=1.5 and c>=5 and minv3.1>=100000
```
（后两条见 [How to improve your momentum burst understanding, 2024-07-21](https://stockbee.blogspot.com/2024/07/how-to-improve-your-momentum-burst.html)，均有对应的 bearish 版）

要回答的问题他列了一整串（原文）：

> What was the setup before the start of the move / What was the 5 day action before start of this move / Was the stock up or down before start of the move / Was it near 52 week high or low / what kind of Trend Intensity it had / what triggered the move / what kind of breakout / How much was it up on first day of breakout / what kind of volume on breakout and pre breakout and post breakout / how did the move progress / what was the magnitude of move in first 3 days

**为什么值得** —— 这是**回看式**的学习循环：不是「我的规则对不对」，是「过去 5 天真正发生了什么，我的规则解释得了吗」。他明说这会**推翻自己的规则**：

> "Sometime while going through them you start questioning some of your own guidelines for selecting trades or you start questioning commonly touted market rules."

> "it is based on actual past winners in immediate time frame. It gives you lot of information on **what is working currently**."

对我们尤其对症：我们的归档 61,801 行有**确切的首现日期**，能回答「这只票第一次出现在哪个筛子上」——他手工翻图翻不出来的东西。

**我们能拿它干嘛**
1. **直接接进 Selection Lab**（[[project_selection_lab]]）：现在的出题是「给一个 setup 让 Andy 判断」，这是**前瞻**的。深潜是**回溯**的——「这只上周涨 20%，它上周一长什么样」。同一套素材，两个方向的练习，回溯那个门槛低得多。
2. **接进临帖 Copybook**（[[project_copybook]]）：每日 25 张卡片如果换成「昨天/上周最爆的 10 只 + 它们爆发前一天的样子」，Claude 先写死预测再对照的机制原样能用。
3. 他每天 10–15 分钟。这是个**可以做成定时任务**的东西——我们的归档能自动回答他手工问的十一个问题里的至少七个（trend intensity、离 52 周高低、突破日涨幅、突破前后量、前 3 日幅度）。

---

## W3. 「Idea Pickle」—— 把废弃的想法腌起来

**是什么**：

> "Most of the time when I abandon a concept, I put it in 'Idea Pickle' jar. This is a long term practice I have used for several years, where I put half baked or promising ideas in a jar to pickle. Revisiting them after some days or months sometimes gives you a completely new idea. **I have several of such 'Idea Pickle' jars to ensure I never run out of ideas.**"
> — [Episodic Pivots and "Idea Pickle", 2007-02-26](https://stockbee.blogspot.com/2007/02/episodic-pivots-and-idea-pickle.html)

而 EP 这整套方法**就是从坛子里捞出来的**——他先是把「一日大涨能否预测未来」当纯机械的东西试，失败，扔进坛子；几个月后读到 Markman 书里 Fontanills 的系统，想起坛子；再后来看到 Minervini 的历史交易全是新闻驱动的，第三次捞出来，最后合成了 EP。**三次捞才成。**

**为什么值得** —— 我们仓库里已经有一堆 NULL 结果（[[project_52wh_momentum_filter_null]]、[[project_sequence_mining]]、[[project_b4_gates_null]]、RMV/VCS/h_score），处理方式是「记进台账，别重测」。**这是对的但只对了一半**：台账防重测，坛子管复活。区别是坛子里的条目带着**当初为什么失败的诊断**，而不只是「无优势」。

「4% 两道闸」那条尤其像该进坛子的：闸**分得开**（p=0.0022）但中位跑不赢 SPY。这不是「无效」，是「量对了收益口径不对」——正是几个月后换个问法可能复活的形状。

**我们能拿它干嘛** —— 在 `data/research/claims/` 旁边加一个 `pickle.md`：每条 NULL 结论追一行「**当初卡在哪**」。`claims.jsonl` 记状态（科学），pickle 记诊断（下一轮的入口）。**成本一行，防的是把「测过了」当成「这条路死了」。**

---

## W4. 仓位从止损距离反推，而不是固定比例

**是什么**：

> "In LM trade I had **20% of account invested, but my risk was only .25%**. Risk = entry-stop. So the trade not working resulted in just .28% loss on overall capital"
> — [When breakouts fail, 2014-01-24](https://stockbee.blogspot.com/2014/01/when-breakouts-fail.html)

配上他的止损纪律（≤4%，理想 ≤2%，高价股更近），算式是：`仓位% = 账户风险% / 止损距离%`。0.25 / 1.25 = 20%。

**为什么值得** —— Andy 的行为诊断里写着「**sizes 2× the 0.25% target**」（[[project_behavioral_diagnosis]]）。Bonde 的 0.25% 和我们的 0.25% 目标是**同一个数字**，但他达成的方式是**先钉死止损再算股数**，而不是先定股数。他还给了工具形态：

> "The trade size tool is a simple tool to calculate how many shares you should buy for 1% risk."

**我们能拿它干嘛** —— `~/ibkr_order_panel` 就是「sized-order entry」的面板，`fluxus-trading-risk-manager.pine` 有 N-stop/sizing。**两边都在，但没有把「止损 ≤2–4%」当成硬约束**。Bonde 的版本给了一个可以直接抄的**拒绝条件**：如果按目标风险算出来的股数需要 >X% 仓位，说明止损太远，**这笔不该做**，而不是缩小股数。

---

## W5. 两套策略配两套完全不同的期望

**是什么** —— 他明确把自己的两个方法放在期望值光谱的两端：

| | Momentum Burst / 4% b/o | Episodic Pivot |
|---|---|---|
| 胜率 | **50.5%**（2013 实测）/ 56% / 14 年 >50% | **>70%** |
| 每笔目标 | 8–20% | 40–50% |
| 赔率 | 2.21:1 / 1.62:1（1.62 那年 **+73.75%**） | "several multiples of my initial risk" |
| 频率 | 一年 200–1000 笔 | "you do not find many trades like that on day to day basis" |
| 选择性 | "I am happy with even 50% success rate" | "you have to be extremely selective" |

> "At other spectrum I trade a different earnings breakout based method where my objective is to have greater than 70% win rates ... In that kind of setups I look for several multiples of my initial risk."
> — [When momentum bursts fail, 2014-01-08](https://stockbee.blogspot.com/2014/01/when-momentum-bursts-fail.html)

**为什么值得** —— 这是「[[feedback_judgment_frame]] 胜率衡量探针，判断力衡量杠杆」的一个具体实例：**同一个人，两个方法，两个胜率目标，而且他知道哪个是哪个**。多数人只有一套期望然后拿它衡量所有交易。

对 Andy 的两腿系统（tactical + core）**结构完全同构**。他的 H1 是 39.9% 胜率 × 3.40 赔付——那是 Momentum Burst 那一侧的形状。问题变成：**core 那条腿有没有被按 >70%/数倍 R 的标准要求过？**

**我们能拿它干嘛** —— `performance_review.py` 现在按账户整体出胜率/赔付。按**两腿分别**出，才看得出哪条腿在按错误的期望运行。

---

## W6. 广度 = 资金脚印，不是情绪指标

**是什么**：

> "Breadth thrusts are created by fund buying and selling. When funds pour in money, you see blocks of buying like this, **back-to-back 300-plus days**. This is not driven by retail."

> "Funds cannot hide their buying. This is what it looks like."

> "Market breadth is market-derived information that tells you when buying or selling is dominating in the market. Using this information to time breakouts helps us **improve win rates and avoid drawdowns**."
> — [Understand market breadth, 2026-07-23](https://stockbee.blogspot.com/2026/07/understand-market-breadth.html)

**为什么值得** —— 两层：
1. **因果解释**：4% 双计不是「情绪」，是「机构下单被计数了」。这解释了为什么**连续性**比单日读数重要——一天 300 只可以是一次事件，连着五天 300 只必须有人天天在买。
2. **用途限定**：他说广度的用途是 **timing breakouts**（今天做不做突破），**不是**预测指数。我们的 `breadth_signals` 现在输出 regime/verdict，更像后者。

**我们能拿它干嘛** —— [diff.md](diff.md) G10：加一个「连续 300+ 天数」的读数（数据全在 `breadth_store`，纯计算）。以及一个可测的问题：**4% 突破的成功率在「连续 N 天 300+」之后是否更高？** 这正是他声称的机制，而我们**两边的数据都有**（4% 归档 + 广度归档），**是我们能验他而他验不了自己的地方**。

---

## W7. 他的「不做」清单（负面知识）

散在各处，集中列一下——**这类知识最难自己攒**：

| 不做 | 原话出处 |
|---|---|
| 快速杀跌期不做多头突破 | "The bullish breakout trade needs to be avoided during fast selling phases" ([2018-05](https://stockbee.blogspot.com/2018/05/understanding-nature-of-stock-moves.html)) |
| 牛市里不做 3 日空头 | "In a bull market trading 3 day bearish setups will lead to lot of failed breakdowns." |
| 延展趋势不做蓄势 | "Extended trends needs to be avoided for anticipation as failure is high on them" ([2015-02](https://stockbee.blogspot.com/2015/02/how-to-find-anticipation-setups.html)) |
| 不线性的票直接跳过 | "I do not even look at rest of the criteria" |
| 大 float 的 EP 不太做 | "500 million plus float ... not really very enthusiastic" ([2010-02](https://stockbee.blogspot.com/2010/02/what-are-episodic-pivots-and-how-to.html)) |
| 有分析师覆盖的 EP 次一等 | "do not do as well as the first kinds" |
| 媒体提及/分析师升级当催化剂 = 低概率 | "have a low probability of follow through" ([2007-02](https://stockbee.blogspot.com/2007/02/episodic-pivots-and-idea-pickle.html)) |
| 没 setup 就空仓 | "Personally I have been in cash for some time as I do not see the kind of setups I look for." ([Q&A 2011](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)) |
| 不用 bollinger squeeze | "I do not use them" |
| 不用期权、不做 ETF、不看盘中图 | Q&A 2011 |

**我们能拿它干嘛** —— 这是**内容素材**。一篇「一个做了 20 年的人明确不做的十件事」比任何 setup 讲解都好读，而且零方法、全是「指认」——正是 [[content_idea_p_zhirenti]] 要的文体。

---

## W8. 他的自我诊断

> "I have many weaknesses. One of the key one is **very few methods**. Not having methods for non-trending periods and intraday trading. I do not have the patience to day trade."

> "The common mistakes most traders make ... Traders are not clear about their time frame. They don't want to commit to a timeframe. They want to be day traders, swing traders, position traders and macro traders. Even if they commit to a timeframe then they do not stick with one setup idea. **They trade too many and ill-defined setups.**"
> — [Q&A, 2011](https://stockbee.blogspot.com/2011/06/q-with-pradeep-bonde.html)

**为什么值得** —— 「方法太少」被他当**弱点**，而「setup 太多且定义不清」被他当**新手通病**。这两句并置很有意思：他知道自己的窄是有代价的，但仍然选窄。

**我们能拿它干嘛** —— 直接对照我们的筛子清单：`pipeline/screeners/` 下 **24 个模块**。按他的标准，这是「too many and ill-defined」还是「一个引擎多个出口」？[[project_shortlist_cards]] 的「一引擎三出口」正面回答了这个问题，值得把他这段当**外部对照**引进去。

---

## 我看过但判定不值得单开一条的

- **401k / Lemonade 共同基金择时**（`AVGC4/AVGC42` 那套）——我们不做基金，且逻辑就是 4/42 均线交叉，无新意。
- **IBD 200 / MarketSmith 工作流**——工具依赖，且我们已有自己的 RS 体系。
- **会员站推销段落**——每篇文末几乎都有，无信息。
- **Bluefin / Trade Logger 等会员工具**——都在登录墙后，不碰。
