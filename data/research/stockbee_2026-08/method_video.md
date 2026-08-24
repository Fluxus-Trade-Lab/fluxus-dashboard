# 方法参数（来源＝视频）—— Stockbee 的五支纯视频帖，转录后逐条

**这份文件里的每一条来源都是视频，与 [`method.md`](method.md)（来源＝博客文字）分开放。**
08-24 那轮的头条结论之一是「**他 2018 之后的方法细节迁去了 YouTube**，那几篇标题最对味的博客正文全是空的」。
Andy 08-24 批准投一晚做转录。**这一晚把那几篇的正文补回来了。**

## 出处与做法

| 视频 | 时长 | 发布 | 对应的空博客帖 |
|---|---|---|---|
| [Where to exit a 4% breakout](https://www.youtube.com/watch?v=w-uiAdQ_6Uw) | 12:47 | 2018-01-18 | [where-to-exit-4-breakout](https://stockbee.blogspot.com/2018/01/where-to-exit-4-breakout.html) |
| [Where to put stop on a 4% breakout or $ breakout](https://www.youtube.com/watch?v=jpmZrIyuP74) | 13:09 | 2018-01-17 | [where-to-put-stop](https://stockbee.blogspot.com/2018/01/where-to-put-stop-on-4-breakout-or.html) |
| [When should you enter a 4% or $ breakout](https://www.youtube.com/watch?v=ub6nkIyjJQs) | 5:07 | 2018-02-01 | [when-should-you-enter](https://stockbee.blogspot.com/2018/01/when-should-you-enter-4-or-breakout.html) |
| [How to select the best 4% breakout setups](https://www.youtube.com/watch?v=wihFo3IehgI) | 21:22 | 2018-01-24 | [how-to-select-best](https://stockbee.blogspot.com/2018/01/how-to-select-best-4-breakout-setups.html) |
| [Episodic Pivots Delayed Entry](https://www.youtube.com/watch?v=Rm9f2E-mygM) | 4:05 | 2023-05-03 | [episodic-pivots-delayed-entry](https://stockbee.blogspot.com/2023/05/episodic-pivots-delayed-entry.html) |

**做法**：`yt-dlp`（音轨）→ `mlx-whisper large-v3-turbo`（本机 GPU，56 分钟音频约 6 分钟）。
**转录全文只在会话 scratchpad，不入库**——照 08-24 立的规矩：仓库里只放带时间戳的逐条引用 + 链接，不做镜像式搬运。
时间戳可直接跳转：`https://www.youtube.com/watch?v=<id>&t=<秒>s`。

---

## ⭐ 一、两个我们当初只能猜的阈值，他给了数字

08-24 的 [`prereg_setup_gates.md`](prereg_setup_gates.md) 机械化他的三条闸时，有两条**他文字里没给数字**，
我们自己定了阈值并"记一次 spec"。**视频里两个数字都有。**

| 闸 | 我们猜的 | **他的原话** | 差多少 |
|---|---|---|---|
| **B2「窄幅日」** | 「窄于前 9 日中位」（我的判断） | 「**a narrow range day of less than 2%**」 <br>——[wihFo3IehgI 02:36](https://www.youtube.com/watch?v=wihFo3IehgI&t=156s) | **他是绝对阈值 2%，我们是相对分位。**且他在 [10:11](https://www.youtube.com/watch?v=wihFo3IehgI&t=611s) 现场把一个 **2.1%** 的日子判为「this is not really a narrow range day」——**2% 是硬线不是软线** |
| **B1「收盘在高位」** | `(C−L)/(H−L) >= 0.70`（我的判断） | 「close near high or **within 20% of high**」<br>——[wihFo3IehgI 03:50](https://www.youtube.com/watch?v=wihFo3IehgI&t=230s) | **他的是 0.80，我们用了 0.70——我们比他松** |

> 「Ideally you should have a **negative day or a narrow range day of less than 2%** pre breakout day.」
> —— [wihFo3IehgI 02:36](https://www.youtube.com/watch?v=wihFo3IehgI&t=156s)

> 「stock negative day or a narrow range day, **close near high or within 20% of high**.」
> —— [wihFo3IehgI 03:50](https://www.youtube.com/watch?v=wihFo3IehgI&t=230s)

**这对 08-24 的实测意味着什么**：那轮的结论（B∧ 通过、+1.25pp、但过闸中位仍≈0）是在**比他松的 B1** 下测出来的。
用 0.80 重测是**零新数据**的一件事。⚠️ 但注意：那轮的 holdout 已经烧过，重测只能算 discovery。

---

## 二、出场（第一次有确切规则）

> 「if you are going to be trading 4% breakout as a swing trading method then **the ideal exit is 3 to 10 days**...
> the most of the time you will be exiting in **3 to 5 days**」——[w-uiAdQ_6Uw 00:14](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=14s)

他的出场规则，逐条（[w-uiAdQ_6Uw 04:20–09:56](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=260s)）：

| # | 规则 | 原话出处 |
|---|---|---|
| E1 | **第 3 天或第 5 天出**，整体窗口 1–10 天 | [00:14](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=14s), [09:34](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=574s) |
| E2 | **没有即时跟进就出**：「give it 2 days. And if it doesn't take off it's not likely to take off with speed」 | [11:40](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=700s) |
| E3 | **异常大涨 → 部分了结**：当天涨 30–40% 就减 30/40/50%，有时 75%，留小仓 | [04:30](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=270s), [09:48](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=588s) |
| E4 | 盘中涨到 10–20% 就**一路上移止损锁利** | [09:56](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=596s) |
| E5 | **一旦转盈就不许再变成亏损** | [05:57](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=357s) |
| E6 | **4% 突破 ≠ dollar 突破**——后者更慢，出场规则不同，他单开一支视频讲 | [00:09](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=9s), [11:23](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=683s) |

**机制他说得很直白**：「the entire logic behind 4% breakout is based on a market tendency of **momentum burst** —
when a stock which has not been going anywhere suddenly has a range expansion then the stock moves in the near term
time frame of **3 to 10 days** in the direction of the range expansion」——[01:04](https://www.youtube.com/watch?v=w-uiAdQ_6Uw&t=64s)

---

## 三、止损

> 「the stop goes at **the low of the day**」——[jpmZrIyuP74 00:14](https://www.youtube.com/watch?v=jpmZrIyuP74&t=14s)（全片重复六次）

| # | 规则 | 出处 |
|---|---|---|
| S1 | 初始止损 = **入场日的当日低点** | [00:14](https://www.youtube.com/watch?v=jpmZrIyuP74&t=14s) |
| S2 | 有经验后可以**放在低点之上**：「25% above the low of the day or 20% above the low of the day」 | [04:00](https://www.youtube.com/watch?v=jpmZrIyuP74&t=240s) |
| S3 | 若突破日的涨幅**回吐 8%**，「that breakout has failed」——止损可提到远高于低点处 | [02:56](https://www.youtube.com/watch?v=jpmZrIyuP74&t=176s) |
| S4 | **明确否定宽止损**：「if you are going to be using a larger stop like three days and all — **don't use that, that's too wide**」 | [02:36](https://www.youtube.com/watch?v=jpmZrIyuP74&t=156s), [07:19](https://www.youtube.com/watch?v=jpmZrIyuP74&t=439s) |
| S5 | 第二天没跟进就**激进上移止损**，不要坐等被打 | [05:33](https://www.youtube.com/watch?v=jpmZrIyuP74&t=333s) |

他给的实际亏损量级（自己的交易）：LOMA **−1.17%**、HIIQ **<1%**、STAR **−8 美分**。
——**他的实际单笔亏损远小于 4% 突破的名义止损宽度**，靠的全是 S5。

---

## 四、入场时点

> 「You should be entering **as soon as you find a good breakout**... Most of my breakouts, I enter them in the
> **first half an hour**... Many of them I enter in the **first five, ten or twenty minutes**.」
> ——[ub6nkIyjJQs 04:03](https://www.youtube.com/watch?v=ub6nkIyjJQs&t=243s)

| # | 规则 | 出处 |
|---|---|---|
| N1 | **同日入场**，越早越好；扫描一出结果就进 | [00:13](https://www.youtube.com/watch?v=ub6nkIyjJQs&t=13s) |
| N2 | **理由是止损距离，不是收益**：「because your stop is low of the day, you will get a stop which will be much closer」 | [02:57](https://www.youtube.com/watch?v=ub6nkIyjJQs&t=177s) |
| N3 | **明确反对等确认**：「If you are going to be putting it above the breakout level, **what were you doing yesterday?**」 | [03:40](https://www.youtube.com/watch?v=ub6nkIyjJQs&t=220s) |
| N4 | 若因上班只能次日进 → **只挑没走远的**（"not extended"） | [01:58](https://www.youtube.com/watch?v=ub6nkIyjJQs&t=118s) |
| N5 | **anticipation 存在的全部理由就是把止损做窄**，不是为了多赚 | [03:15](https://www.youtube.com/watch?v=ub6nkIyjJQs&t=195s) |

⚠️ **N1–N3 和我们的实现结构性冲突**：我们的 `gainers_4pct` 是**收盘后**的日线扫描，
所有回测（含 08-24 那轮和今晚的 [`amplitude_2026-08`](../amplitude_2026-08/results.md)）都是**事件日收盘入场**。
**他从不在收盘入场。** 这不是参数差异，是**口径差异**——我们测的从来不是他的交易。
这一条应该写进任何引用那些回测数字的地方。

---

## 五、选 setup 的完整清单（这支视频是他的选股实况）

| # | 条件 | **数字** | 出处 |
|---|---|---|---|
| C1 | 扫描本体 | 涨 ≥4% **且** 量 > 昨日量 **且** 量 > 100,000 | [00:14](https://www.youtube.com/watch?v=wihFo3IehgI&t=14s) |
| C2 | 不得连涨 3 天 | 「up 3% three days in a row → **should not even look at it**」；但**零点几个百分点的连涨可以接受** | [00:36](https://www.youtube.com/watch?v=wihFo3IehgI&t=36s), [01:49](https://www.youtube.com/watch?v=wihFo3IehgI&t=109s) |
| C3 | 突破前一日 | 阴线 **或** 窄幅日 **<2%** | [02:36](https://www.youtube.com/watch?v=wihFo3IehgI&t=156s) |
| C4 | 收盘位置 | **within 20% of high** | [03:50](https://www.youtube.com/watch?v=wihFo3IehgI&t=230s) |
| C5 | 底部 | 有序回调或**5–40 天**的底 | [05:02](https://www.youtube.com/watch?v=wihFo3IehgI&t=302s) |
| C6 | 底部质量 | **底部期间不得出现 4% 下破**（有=派发） | [05:09](https://www.youtube.com/watch?v=wihFo3IehgI&t=309s) |
| C7 | 已有趋势的票 | 要**线性的第一腿**，拒绝 choppy | [05:19](https://www.youtube.com/watch?v=wihFo3IehgI&t=319s) |
| C8 | 突破日成交量 | 越高越好，**看相对量**（「one of the highest volume in this entire move of last 2-3 months」） | [05:58](https://www.youtube.com/watch?v=wihFo3IehgI&t=358s) |
| C9 | **历史突破记录** | 「**always check last three or four breakouts**」——前 3–4 次突破都失败就避开 | [11:21](https://www.youtube.com/watch?v=wihFo3IehgI&t=681s) |
| C10 | **财报** | 「you don't want to be holding it into earnings」——离财报 <3–4 个交易日就不进 | [13:43](https://www.youtube.com/watch?v=wihFo3IehgI&t=823s) |
| C11 | float | 低 float 是加分（例：float 10.7M，当日成交 13.9M = **换手 >100%**） | [14:36](https://www.youtube.com/watch?v=wihFo3IehgI&t=876s) |

### ⭐ C4 的可操作版：`dollar = C − O`

这是视频里最实用的一个零件，**文字帖里完全没有**：

> 「I am going to sort it by **dollar**, and what is dollar — dollar is basically **C minus O**, so close minus opening price.
> ... Netflix for the day is up 9.98 but from the opening price it actually went down 4.76,
> **so you don't want to be looking at stocks like this because they didn't close near the high**.」
> ——[wihFo3IehgI 06:30](https://www.youtube.com/watch?v=wihFo3IehgI&t=390s)

**他把 171 只的扫描结果按 `C−O` 排序**，用它一次性同时做两件事：① 剔掉"高开低走"的假突破；② 用 `C−O > $0.25` 过滤低价股。
他还把低价股在扫描里的**占比**当市场情绪读数：「lot of low price stocks showing up... tells you that the market
is becoming more speculative」，并说这**通常出现在回调之前**——[07:11 / 07:56](https://www.youtube.com/watch?v=wihFo3IehgI&t=431s)。

**这是我们 `breadth_metrics` 家族里没有的一个读数，且零新数据**：4% 扫描结果里低价股占比的时间序列。

### C2 的例外（低价股）

> 「if you have very low price stocks especially **stocks below $5**... there you will find that they might be up
> 3 or 4% and then they can still break out and they can still work. They have higher volatility so they operate
> very differently.」——[wihFo3IehgI 02:16](https://www.youtube.com/watch?v=wihFo3IehgI&t=136s)

⚠️ 这条和今晚 [`amplitude_2026-08`](../amplitude_2026-08/results.md) 的 H3 **说的是同一件事**：
高波动的票行为不同，所以闸的阈值不该对它们一视同仁。他是靠眼睛发现的，我们量出来是 **Q1→Q5 幅度差 2.4×**。

---

## ⭐ 六、Delayed EP：我们把主次搞反了

这支视频是我们 `delayed_ep_scan.py` 那段行为描述的**唯一来源**，08-24 只能标「来源：视频，未文字核实」。**现在核实了。**

**我们的 docstring 描述基本准确**——「day 1 tends to reverse」「by day 3-4 the news is priced in」
「the mirror works on the short side」三条视频里都有。**但有两处实质出入：**

### 出入一：主次颠倒

> 「especially in this video **i'm going to focus on short side**」——[Rm9f2E-mygM 00:45](https://www.youtube.com/watch?v=Rm9f2E-mygM&t=45s)
> 「and this can work **even on the long side**」——[04:03](https://www.youtube.com/watch?v=Rm9f2E-mygM&t=243s)（全片最后一句）

**他这套 delayed 入场主要是做空的**（财报 miss → 跳空低开 → 反弹 2–4 天 → 真正的破位开始）。
**长边是他一句带过的附注。** 我们的 docstring 写成了「He says the mirror works on the short side」，
**把主句和附注写反了**，而我们的扫描器只跑长边——**我们实现的是他的附注。**

### 出入二：窗口几乎不重叠

| | 我们 | 他 |
|---|---|---|
| 窗口 | **EP 后 3–15 个交易日**（`--min-days 3 --max-days 15`） | 「**second day entry was very good**」[01:32](https://www.youtube.com/watch?v=Rm9f2E-mygM&t=92s)<br>「sometimes it is just a **two or three days bounce**」[01:03](https://www.youtube.com/watch?v=Rm9f2E-mygM&t=63s)<br>「after a rally of **three to four days**, or sometimes the best entry is **on the next day**」[03:09](https://www.youtube.com/watch?v=Rm9f2E-mygM&t=189s) |

**他的窗口大约是 1–4 天，我们的是 3–15 天——只在第 3–4 天重叠。**
我们的 `--min-days 3` **恰好排掉了他反复强调的那一天（次日 / 第 2 天）**，而 `--max-days 15` 延伸到他从未展示过的区间。

他给的结果量级：SMTC 之后 −15~18%、CRDO 破位后 −20%。并明确说空边收益比长边小：
「on the short side you will have to be happy with the smaller profit」——[03:30](https://www.youtube.com/watch?v=Rm9f2E-mygM&t=210s)

**⚠️ 这两条我不动代码**（`pipeline/tools/` 的 EP 链归 DATA ALEX）。建议列在 [`open_questions.md`](open_questions.md) 末节。
