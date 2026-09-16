# I Lose More Often Than I Win

*Section: Method  ·  Audience: everyone  ·  Day 1*
*口径以 `06_h1_flagship_DOSSIER.md` 为准:窗口 2025-12-31 → 2026-07-22,331 笔已平仓。*
*✅ 2026-08-09 全套数字已按 DOSSIER 重写(旧稿的 303/42.7%/3.15×/18% 全部作废)。*
*✅ 2026-09-17 Writer Mia：回撤与基准改按 `PERFORMANCE_TRUTH.md` Period 1——最大回撤 **−17.9%（01-28 → 03-19，MTM）**；11.1% 是 08-03 已公开撤回的 bug（选了美元最大跌幅，那是六月一段）。SPY **+9.60%** / QQQ **+14.82%**（IBKR），08-09 版写的 +9.31% 作废。*
*⚠️ P.S. 的叙事原本建在「六月那八个交易日」上，现只替换了事实（数与时段），情绪那几句没动——**发前请 Andy 读一遍这段是不是还是他的话**。*

---

*[块 A:开头免责块]*

---

In the first half of this year I took 331 trades to completion. Fewer than two in five made money.

The account finished up 90.5%. Both of those sentences are true at the same time, and the space between them is the only thing in this letter worth learning.

## The number

H1 2026 closed **+90.5%**. SPY did **+9.60%** over the same window — and QQQ, the fairer benchmark for what I actually trade, did **+14.82%**. Along the way the account gave back **17.9%** from its peak, marked to market, between late January and mid-March.

That's the flex, and I'm going to spend the rest of this piece taking it apart, because the number is the result and the method is the product. A number without its shape is just a lottery ticket someone is waving at you.

## The shape

| | |
|---|---|
| Closed trades | **331** |
| Average hold | 7.5 days |
| Win rate | **39.9%** (132 winners) |
| Payoff ratio | **3.40×** |
| Profit factor | 2.48 |
| Expectancy | **+0.88R per trade** |
| Cumulative | **+290.6R** |

*Everything here is in R — multiples of what I'd decided to risk before entering. R is the only unit that travels. Dollar figures tell you about the size of my account, which is none of your business and no use to you; R tells you about the shape of the method, which is the entire point.*

Read the first two rows together and the year looks broken. Read all of them and it's arithmetic. I am wrong three times out of five, and each time I'm right it's worth about three and a half times what being wrong costs me. You don't need a high hit rate. You need the losers to stay small enough that the hit rate stops mattering.

That is the entire trade. Everything else in this letter is bookkeeping around it.

## Where the trades actually landed

Sorted by R — by multiples of what I'd decided to risk before I entered:

| Bucket | Trades |
|---|---|
| Worse than –1R | **31** |
| –1R to 0 | 150 |
| 0 to 1R | 53 |
| 1R to 2R | 31 |
| 2R to 3R | 19 |
| **Better than 3R** | **47** |

Two rows in that table are the whole shield.

**Thirty-one.** Out of 331 trades, thirty-one got away from me — a gap, a gut call, a stop I moved because I had a feeling. Nine percent. The other ninety-one percent stopped where I said they'd stop, before I felt anything about it. That number is the defense, and it's the only one on this page I'd defend in a fight.

**Forty-seven.** Forty-seven trades better than 3R, out of 331. The fat right tail isn't a bonus sitting on top of the year — it *is* the year. Cut those 47 and the whole thing goes flat.

So the job is not being right. The job is surviving the 150 mediocre losses cheaply enough to still be holding size when one of the 47 shows up.

## How the trades ended

This is the row nobody puts in their marketing:

| Exit | Trades | Average | Total |
|---|---|---|---|
| Stop fired, nothing else | 46 | **–1.25R** | –57R |
| Sold into weakness | 85 | –0.33R | –28R |
| Sold into strength | 44 | +2.63R | +116R |
| **Scaled out in pieces** | **156** | **+1.67R** | **+260R** |

Read the last column, not the third. The 44 trades I sold into strength had the best *average* — but the 156 I scaled out of produced more than twice as much total return, because there were three and a half times as many of them.

That is the whole argument for the two-leg structure. Scaling out isn't the highest-scoring exit per trade. It's the one that happens often enough to matter, because a position you've already trimmed to break-even is one you can keep holding without needing to be right about it.

And 46 times this half, the entire event was: I bought something, it didn't work, the stop fired at about –1R, and I went and did something else. No insight, no story, nothing to post about. Those 46 cost 57R in total — less than a quarter of what the scaled exits made back.

## What this means for you

If you take one thing: **your win rate is not the dial.** It's the one everybody stares at because it's the one that feels like being smart. The dials that actually move the year are how much you put on and where you get off — and those two are yours, fully, before you ever enter. Being right is the market's business. Size and stop are yours.

I lose more often than I win. The year works anyway. That's not a paradox and it's not a humblebrag, it's just what the arithmetic does when you refuse to let a loser get big.

---

*[块 B:结尾持仓块]*

---

*P.S. — The drawdown was 17.9%, and it ran from late January into March. I'd love to tell you I was serene through it. What actually kept me in was that the size was decided when I was calm and the stops were already sitting where I'd put them, so there was nothing left to decide while I was scared. That's the whole reason to do the arithmetic first — not because it makes you smarter, but because it means the frightened version of you has no buttons left to press.*

---

## 发布前必做

- [x] 数字按 `06_h1_flagship_DOSSIER.md` 重写(2026-08-09)
- [x] 离场方式表已用 `performance_review.py` 的 `parse_csv` 重算(2026-08-09,portfolio_2026-08-09.csv,331 笔 / 平均 +0.878R,与 DOSSIER 对齐)
- [ ] `r_distribution` 画成柱状图配进「Where the trades actually landed」
- [ ] equity curve vs SPY + 回撤曲线配进「The number」
- [ ] 七道闸:**收藏闸**已过(给了判据「你的胜率不是那个旋钮」+ 31/331 的具体口径)
