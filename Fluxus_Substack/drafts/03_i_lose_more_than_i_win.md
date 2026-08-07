# I Lose More Often Than I Win

*Section: Method  ·  Audience: everyone  ·  Day 1*
*所有数字来自 `data/output/h1_2026_stats.json`(H1 2026,自有交易记录)。发布前用 `pipeline/portfolio/performance_review.py` 复核一次。*

---

*[块 A:开头免责块]*

---

In the first half of this year I took 303 trades to completion. Fewer than half of them made money.

The account finished up 90.8%. Both of those sentences are true at the same time, and the space between them is the only thing in this letter worth learning.

## The number

H1 2026 finished **+90.8%**. SPY did **+9.31%** over the same six months. Max drawdown along the way was **18%** — which is to say there was a stretch where nearly a fifth of the account was gone and the only correct response was to keep doing the same boring thing.

That's the flex, and I'm going to spend the rest of this piece taking it apart, because the number is the result and the method is the product. A number without its shape is just a lottery ticket someone is waving at you.

## The shape

| | |
|---|---|
| Closed trades | 303 |
| Win rate | **39.9%** |
| Average winner | **+3.19R** |
| Average loser | **–0.76R** |
| Payoff ratio | **3.15×** |
| Profit factor | 2.35 |
| Expectancy per trade | **+0.88R** |

*Everything here is in R — multiples of what I'd decided to risk before entering. R is the only unit that travels. Dollar figures tell you about the size of my account, which is none of your business and no use to you; R tells you about the shape of the method, which is the entire point.*

Read the first two rows together and the year looks broken. Read all six and it's arithmetic. I am wrong more often than I'm right, and each time I'm right it's worth a little over three times what it costs me to be wrong. You don't need a high hit rate. You need the losers to stay small enough that the hit rate stops mattering.

That is the entire trade. Everything else in this letter is bookkeeping around it.

## Where the trades actually landed

Sorted by R — that is, by multiples of what I'd decided to risk before I entered:

| Bucket | Trades |
|---|---|
| Worse than –1R | **29** |
| –1R to 0 | 136 |
| 0 to 1R | 48 |
| 1R to 2R | 27 |
| 2R to 3R | 19 |
| **Better than 3R** | **44** |

Two rows in that table are the whole shield.

**Twenty-nine.** Out of 303 trades, twenty-nine got away from me — a gap, a gut call, a stop I moved because I had a feeling. Nine percent. The other ninety-one percent stopped where I said they'd stop, before I felt anything about it. That number is the defense, and it's the only number on this page I'd actually defend in a fight.

**Forty-four.** Forty-four trades better than 3R. My average winning trade is 3.19R and my average loser is –0.76R, which means the fat right tail isn't a bonus sitting on top of the year — it *is* the year. Cut those 44 and the whole thing goes flat.

So the job is not being right. The job is surviving the 136 mediocre losses cheaply enough to still be holding size when one of the 44 shows up.

## How the trades ended

This is the row nobody puts in their marketing:

Indexed so that a clean sell-into-strength exit = 1.0:

| Exit | Trades | Relative outcome |
|---|---|---|
| Stop only | **120** | **–0.35** |
| Sold into weakness | 97 | +0.21 |
| Sold into strength | 69 | +1.00 |
| Scaled out in pieces | 17 | **+2.58** |

One hundred and twenty times this half, the entire event was: I bought something, it didn't work, the stop fired, and I went and did something else. Roughly once every business day. No insight in it, no story to tell afterward, nothing to post about.

Meanwhile the 17 trades where I scaled out in pieces returned about **2.6× what a clean single exit did** — and something like 12× the average trade. Seventeen out of 303. Same trader, same six months, same ideas. The difference was whether the position was worth managing in stages.

The Herd looks at a year like this and sees the 44. The job is mostly the 120.

## What this means for you

If you take one thing: **your win rate is not the dial.** It's the one everybody stares at because it's the one that feels like being smart. The dials that actually move the year are how much you put on and where you get off — and those two are yours, fully, before you ever enter. Being right is the market's business. Size and stop are yours.

I lose more often than I win. The year works anyway. That's not a paradox and it's not a humblebrag, it's just what the arithmetic does when you refuse to let a loser get big.

---

*[块 B:结尾持仓块]*

---

*P.S. — The drawdown was 18%. I'd love to tell you I was serene through it. What actually kept me in was that the size was decided when I was calm and the stops were already sitting where I'd put them, so there was nothing left to decide while I was scared. That's the whole reason to do the arithmetic first — not because it makes you smarter, but because it means the frightened version of you has no buttons left to press.*

---

## 发布前必做

- [ ] 用 `performance_review.py` 复核每一个数字
- [ ] `r_distribution` 画成柱状图配进「Where the trades actually landed」
- [ ] equity curve vs SPY 配进「The number」
- [ ] 决定要不要贴具体标的(建议**不贴** —— 这篇讲形状不讲名字,贴了会被读成荐股)
- [ ] 七道闸:**收藏闸**已过(给了判据「你的胜率不是那个旋钮」+ 29/303 的具体口径);**AI 味闸**注意表格后不要每段都是双拍对称句
