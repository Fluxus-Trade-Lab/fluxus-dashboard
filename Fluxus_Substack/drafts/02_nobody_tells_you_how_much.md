# Everyone Tells You What to Buy. Nobody Tells You How Much.

*Section: Method  ·  Audience: everyone  ·  Day 1*
*框架取自 `user_trading_profile.md`(Account A 实盘规则)。数字是你真实在用的,不是示范用的。*
*✅ 已按你的要求改为**纯百分比口径** —— 全文无任何美元金额、无账户量级。*

---

*[块 A:开头免责块]*

---

Every letter you've ever subscribed to tells you what to buy. Almost none of them tell you how much, and how much is the part that decides your year.

You can be right about the name and finish flat because you sized it like a lottery ticket. You can be right twice and hand it all back on the third because nothing told you where to get off. I've been both of those people and neither of them was short of good ideas.

So this is the one promise I'll make and keep: **every idea in this letter arrives with its size and its stop.** I won't promise to be right — accuracy isn't mine to control, and anyone who promises it is selling you something. The arithmetic is mine to control. You'll never have to ask me how much.

Here's how the arithmetic actually runs.

## Start from the loss, not from the position

Most people size forward: *I like this one, I'll put 10% in.* That's how you end up with a position whose risk you discover afterward.

I size backward. I decide what the trade is allowed to cost me before I decide anything else, and everything downstream falls out of it.

One unit of risk — one R — is **0.25% of the account**. Fixed. Not a range, not "depends how much I like it." A quarter of one percent.

That number strikes most people as absurdly small, so let me put it in context. My full-Kelly number — the mathematically optimal bet given my hit rate and payoff — is about **18.8%**. I trade at 0.25%. That's roughly **one seventy-fifth of Kelly**.

I am not being timid. I'm being solvent. Kelly assumes you know your edge exactly, and nobody knows their edge exactly. It also happily accepts drawdowns that would end your career while being technically correct about them. Running at 1/75 means my estimate of my own edge can be wildly wrong and the account still doesn't care.

## Then the stop sets the position, not the other way round

Once R is fixed, the position size isn't a decision. It's division.

> **Position (% of account) = risk budget ÷ stop distance**

Say a stock's ATR is 2.5% of its price, and I want the stop one ATR below entry. The stop distance is 2.5%.

> 0.25% ÷ 2.5% = **10% of the account.**

A **10% position risking 0.25%.** Notice there's no dollar figure anywhere in that line — the formula is scale-free. Run it on a five-figure account or an eight-figure one and the percentages are identical. That's the only reason it's worth teaching.

Sit with that, because it's the whole trick and almost nobody says it out loud: **a tight stop is not a small position. A tight stop is what buys you a big one.** The people who size by conviction end up with modest positions and sloppy risk. Sizing off the stop gets you a large position and precise risk, from the same account, on the same idea.

Two consequences follow, and they're both features.

A setup that's a mess — wide, gappy, no clear place to be wrong — mechanically gets a tiny position. I don't have to summon discipline to pass on bad structure. The arithmetic passes for me. *No tightness, no trade* isn't willpower, it's division.

And when I'm wrong, I'm wrong for a quarter of a percent. This year I've taken 331 trades. A hundred and thirty of them ended with nothing happening except the stop firing. That's roughly once a business day, all year, and not one of those days mattered.

## The two-leg structure

This is the piece I haven't seen written down elsewhere, and it's where most of my year comes from.

**The tactical leg.** Big position, tight stop — the 10–15% of equity above, stop inside one ATR. Its only job is to be present for the initial burst, when a name breaks out of a proper base and moves fast. Capital efficiency is enormous: I've got serious size on for a quarter percent of risk. At **+1R to +1.5R** I trim, which takes the original risk off the table. From that moment the trade cannot lose me money.

**The core leg.** What's left after the trim — 3–8% of equity — gets re-stopped *wider*, one and a half to two ATR. It's now trading a different thesis. The tactical leg was betting on a burst; the core is betting on a trend, and trends need room to breathe that bursts don't.

Most people run one stop for the entire life of a trade and it's wrong at both ends: too wide to give them size at entry, too tight to let them hold anything through a normal pullback. Running two legs lets each stop answer the question it's actually good at.

This year, the 20 trades where I ran both legs properly averaged **about 3× what a single well-timed exit made me** — and roughly nine times the average trade overall. Twenty trades out of 331. Same trader, same seven months, same ideas. The difference was structure.

## Three caps that sit above all of it

Position sizing alone won't save you, because the fastest way to blow up isn't one bad trade — it's fifteen good ones that turn out to be the same trade.

- **Total risk ≤ 3% of equity.** About twelve R live at once, maximum. If everything stopped simultaneously I'd lose 3%.
- **Any one theme ≤ 1.5%.** Six semis names in a chip run are one position wearing six tickers. The cap makes me count them as one.
- **Drawdown brake.** Rolling three-month drawdown past 20%, or profit factor under 1.3, and R goes down to 0.2% while I stop opening anything new. The rule fires on its own. I don't get a vote, which is the entire point of writing it down while I'm calm.

## What this actually buys you

Not accuracy. My win rate is 39.9% and I don't expect that to improve much.

What it buys is that **the frightened version of me has no buttons left to press.** Size was set when I was calm. The stop was placed before I had a feeling about the position. By the time the trade is going against me there's nothing left to decide, which means there's nothing left to decide badly.

That's the whole product. Everyone will tell you what to buy. This is the letter that tells you how much, and it'll tell you every time, on every idea, including the ones that don't work.

---

*[块 B:结尾持仓块]*

---

*P.S. — People hear "a quarter of one percent" and assume I must be missing the big moves. It's the reverse. Because the risk per trade is tiny, I can carry a dozen at once, and because I can carry a dozen, I'm still holding something when one of them turns into the trade that makes the quarter. Small risk isn't the opposite of big returns. It's the delivery mechanism.*

---

## 发布前必做

- [x] ~~披露口径~~ —— **已定:纯百分比,永不出现账户规模。** 全刊通行规则,写进 `_BOILERPLATE.md`
- [ ] 配图:一张 ATR→仓位 的换算表;一张两腿结构的 R 曲线示意
- [ ] 七道闸:**收藏闸**已过(给了公式、三条硬上限、失效条件);**平庸闸**过(两腿结构 fintwit 罕见);**AI 味闸**注意「三条 caps」是编号列表 —— 每条都带了刺(「六个半导体名字是一个仓位穿了六件马甲」),保留
- [ ] 这篇是全刊的**承诺书**。建议 Day 1 排第 2 位,并把它设为 Substack 置顶
