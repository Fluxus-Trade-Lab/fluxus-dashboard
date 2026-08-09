# I Lose More Often Than I Win

*Section: Method  ·  Audience: everyone  ·  Day 1*
*所有数字口径:**2025-12-31 → 2026-07-22,331 笔已平仓**。源 `data/portfolio/reviews/h1_2026.md` + `h1_2026_full.json`;exit style 与 R 分桶由 `portfolio_2026-07-26.csv` 重算。*
*⚠️ 7/22–7/31 无交易,所以「到七月底」与「到 7/22」数值相同 —— 可以放心写 "this year so far"。*
*✅ 基准已补(2026-08-03,**IBKR TWS 实取**,非 TradingView):同窗口 **SPY +9.60%**(681.92→747.41)· **QQQ +14.82%**(614.31→705.35),价格口径。*

---

*[块 A:开头免责块]*

---

This year so far I have taken 331 trades to completion. Fewer than half of them made money.

The account is up 90.5%. Both of those sentences are true at the same time, and the space between them is the only thing in this letter worth learning.

## The number

Through July 22nd the account is **+90.5%**. SPY did **+9.6%** over the same window — and QQQ, which is the fairer benchmark for what I actually trade, did **+14.8%**. Max drawdown along the way was **11.1%** — marked to market, daily, not the flattering closed-trade version. Which is to say there was a week in June where the account gave back a ninth of its high and the only correct response was to keep doing the same boring thing.

That's the flex, and I'm going to spend the rest of this piece taking it apart, because the number is the result and the method is the product. A number without its shape is just a lottery ticket someone is waving at you.

## The shape

| | |
|---|---|
| Closed trades | 331 |
| Win rate | **39.9%** |
| Average winner | **+3.22R** |
| Average loser | **–0.75R** |
| Payoff ratio | **3.40×** |
| Profit factor | 2.48 |
| Expectancy per trade | **+0.88R** |

*Everything here is in R — multiples of what I'd decided to risk before entering. R is the only unit that travels. Dollar figures tell you about the size of my account, which is none of your business and no use to you; R tells you about the shape of the method, which is the entire point.*

Read the first two rows together and the year looks broken. Read all six and it's arithmetic. I am wrong more often than I'm right, and each time I'm right it's worth a little over three times what it costs me to be wrong. You don't need a high hit rate. You need the losers to stay small enough that the hit rate stops mattering.

That is the entire trade. Everything else in this letter is bookkeeping around it.

## Where the trades actually landed

Sorted by R — that is, by multiples of what I'd decided to risk before I entered:

| Bucket | Trades |
|---|---|
| Worse than –1R | **31** |
| –1R to 0 | 150 |
| 0 to 1R | 53 |
| 1R to 2R | 31 |
| 2R to 3R | 19 |
| **Better than 3R** | **47** |

Two rows in that table are the whole shield.

**Thirty-one.** Out of 331 trades, thirty-one got away from me — a gap, a gut call, a stop I moved because I had a feeling. Nine percent. The other ninety-one percent stopped where I said they'd stop, before I felt anything about it. That number is the defense, and it's the only number on this page I'd actually defend in a fight.

**Forty-seven.** Forty-seven trades better than 3R. My average winning trade is 3.22R and my average loser is –0.75R, which means the fat right tail isn't a bonus sitting on top of the year — it *is* the year. Cut those 47 and the whole thing goes flat.

So the job is not being right. The job is surviving the 150 mediocre losses cheaply enough to still be holding size when one of the 47 shows up.

## How the trades ended

This is the row nobody puts in their marketing:

Indexed so that a clean sell-into-strength exit = 1.0:

| Exit | Trades | Relative outcome |
|---|---|---|
| Stop only | **130** | **–0.36** |
| Sold into weakness | 108 | +0.23 |
| Sold into strength | 73 | +1.00 |
| Scaled out in pieces | 20 | **+3.14** |

A hundred and thirty times this year, the entire event was: I bought something, it didn't work, the stop fired, and I went and did something else. Roughly once every business day. No insight in it, no story to tell afterward, nothing to post about.

Meanwhile the 20 trades where I scaled out in pieces returned about **3× what a clean single exit did** — and roughly nine times the average trade. Twenty out of 331. Same trader, same seven months, same ideas. The difference was whether the position was worth managing in stages.

The Herd looks at a year like this and sees the 47. The job is mostly the 130.

## What this means for you

If you take one thing: **your win rate is not the dial.** It's the one everybody stares at because it's the one that feels like being smart. The dials that actually move the year are how much you put on and where you get off — and those two are yours, fully, before you ever enter. Being right is the market's business. Size and stop are yours.

I lose more often than I win. The year works anyway. That's not a paradox and it's not a humblebrag, it's just what the arithmetic does when you refuse to let a loser get big.

---

*[块 B:结尾持仓块]*

---

*P.S. — The drawdown was 11.1%, and I reported it in my own channel while it was happening — "60% invested and down 1.5%, 12% drawdown from peak" — which is the only version of a drawdown number worth anything. I'd love to tell you I was serene through it. What actually kept me in was that the size was decided when I was calm and the stops were already sitting where I'd put them, so there was nothing left to decide while I was scared. That's the whole reason to do the arithmetic first — not because it makes you smarter, but because it means the frightened version of you has no buttons left to press.*

---

## 发布前必做

- [x] ~~补 SPY 同窗口涨幅~~ ← 已取:SPY +9.60% / QQQ +14.82%(IBKR)
- [ ] `r_distribution` 画成柱状图配进「Where the trades actually landed」(用 `h1_2026_rr.png`)
- [ ] equity curve vs SPY **和 QQQ** 配进「The number」(两条基准都画,QQQ 那条才是硬的)
- [ ] 决定要不要贴具体标的(建议**不贴** —— 这篇讲形状不讲名字,贴了会被读成荐股)
- [ ] 七道闸:**收藏闸**已过(给了判据「你的胜率不是那个旋钮」+ 31/331 的具体口径);**AI 味闸**注意表格后不要每段都是双拍对称句
- [ ] 口径一致性:全文窗口 = **12/31 → 7/22**;胜率 39.9% = 132 胜 /331(18 笔打平算不赢,保守口径,被人核也站得住)
