# I Tested 42 Signal Sequences. Zero Beat a Coin Flip.

*Section: Method  ·  Audience: everyone  ·  Day 1*
*素材:`project_sequence_mining`(2026-08-01 shipped)。数字全部来自 `data/research/` 报告。*

---

*[块 A:开头免责块]*

---

I spent a month building a tool to answer one question: when a stock shows up on one of my screens and then shows up on a second one a few days later, does that sequence pay?

It doesn't. Not one of them. I'm publishing it anyway, and the reason I'm publishing it is the interesting part.

## The setup

I keep an archive of everything my screens have flagged, going back months. That gives me ordered pairs — a stock triggers a VCP setup, then eleven sessions later it triggers a momentum screen. Forty-two such pairs had enough history to test.

For each one I measured forward returns against SPY, entering at the next session's open so there's no peeking. Then — and this is the part that mattered — I compared each sequence against **random entries into the same pool of stocks on random dates**. Not against cash. Not against the index. Against a coin flip that had access to exactly the same names.

Eighteen of the 42 survived the stability and sample-size filters.

**Zero of the 18 had positive net edge.** The best result anywhere in the table was **–0.41%**.

## The part I got wrong first

The first version of this told me `vcp → momentum` paid **+4.38%**. I was pleased with it for about a day.

It was wrong three separate ways, and each one is a mistake I'd bet is sitting inside a backtest somebody is selling right now.

**The baseline was drawn from the wrong universe.** It sampled all 3,872 tickers in the archive, so what I'd actually measured was *screener stocks versus random stocks* — a composition effect. It said nothing about timing, which was the only thing I'd asked.

**All 42 baselines shared one random seed.** They were nested prefixes of a single draw. When I re-ran with different seeds the table moved 4.1 percentage points — a swing wider than the entire result I was celebrating.

**Duplicate dates inflated the sample.** The same first leg mapping to one confirmation got counted repeatedly. What looked like 110 instances was 52 real ones. A 2.12× overcount.

Corrected, that sequence came in at **–1.45%**, flagged unstable. And its winners were almost all AI and semis, which in that window means I hadn't found a sequence at all. I'd found the spring chip run wearing a costume.

## The tell

Here's the number that convinced me the null was real rather than a bug.

I split every sequence in half and checked whether the first half's result held up in the second. **46% passed.** Under pure noise you'd expect about 50%.

So my stability filter wasn't finding edge and screening out noise. It was screening out coin flips at very slightly worse than the rate you'd get from screening out coin flips. There was nothing underneath.

## Why you're reading this

Because the alternative was to not tell you.

I could have shipped the +4.38%. It came out of a real tool, on real data, with real code behind it. Nobody would have checked. That number would have been perfectly serviceable marketing and it would have been false, and some of you would have traded it.

The reason I don't is not that I'm honest, it's that I have to trade this stuff. A number I've flattered is a number that will find me later, in size, on a day I can't afford it. The audience gets the truth as a side effect of my needing it first.

There's a version of this business where research exists to justify the subscription. I'd rather run the version where research occasionally comes back and says *you were wrong, there's nothing here, go do something else*. You should expect that from me a few times a year. If a letter never publishes a null, it isn't testing anything.

## What I'd actually take from it

Three things, and none of them is about sequences.

**Always benchmark against the pool, not against cash.** Most edges evaporate the moment the baseline is allowed to buy the same names you did. If a backtest compares your picks to the index, it's measuring your universe, not your timing.

**One seed is not a test.** If your result moves more when you change the random seed than it does when you change the strategy, you don't have a result.

**89 sessions of one regime supports one claim and only one.** Mine is narrow on purpose: *these sequences, in this window, among these names, were indistinguishable from random entry.* It is not "screeners don't work." I'll run it again in a year when the archive covers more than one kind of market, and I'll publish that too, whichever way it lands.

The tool was worth building. The answer was no. Both of those are fine.

---

*[块 B:结尾持仓块]*

---

*P.S. — The thing I keep noticing is that the wrong version and the right version were the same amount of work. The +4.38% and the –1.45% took equal effort to produce. All that separated them was whether I went looking for reasons the good number might be fake, which took an afternoon, and which is the only part of the process anyone should trust.*

---

## 发布前必做

- [ ] 复核 42 / 18 / –0.41% / 46% vs 50% / 3,872 / 110→52 / 2.12× / 4.1pt / –1.45% 全部数字对得上 `data/research/` 报告
- [ ] 考虑贴一张 half-sample pass rate 的图
- [ ] 七道闸:**平庸闸**已过(fintwit 几乎无人发 null result);**AI 味闸**注意「三个 takeaway」那节每条里都要有刺,现在有(seed 那条)
- [ ] 这篇是**差异化最强的一篇**,建议排在 Day 1 的第 2 或第 3 位,不要压在最后
