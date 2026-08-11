# Trade Data Analysis · A Working Guide

How to turn a trade log into something that improves your next decision.

Read it in two tiers:
- **Beginner** — your first real review. No coding needed; you just need a complete trade log.
- **Advanced** — you already read win rate and payoff. This is about when those numbers lie to you.

Companion: [`TRADE_ANALYSIS_PROMPTS.en.md`](./TRADE_ANALYSIS_PROMPTS.en.md) (copy-paste prompts) · 中文版: [`TRADE_ANALYSIS_GUIDE.zh.md`](./TRADE_ANALYSIS_GUIDE.zh.md)

---

# Beginner

## 1. Decide what a review is for

Most reviews stop at "I made a bunch of charts." A useful one answers **three layers**, and every layer must land on *what to do next time*:

| Layer | Question | Example |
|---|---|---|
| **Descriptive** | What happened | 39.9% win rate, 3.40× payoff, +0.88R expectancy |
| **Diagnostic** | Why | The losses weren't bottom-fishing — they were oversizing the failed add-ons |
| **Prescriptive** | What to change | Switch to equal risk: the same trades return +67% more |

**Only the third layer changes tomorrow's order.** The first two exist to earn it.

## 2. Data: no stop, nothing works

Export a CSV. Each trade needs at least:

```
ticker · direction · entry date · entry price · qty · initial stop · each scale-out (price/qty/date)
```

**The initial stop is the foundation.** Without it you can only compute "how much money did I make", never "how much risk bought that" — and only the second one is comparable across trades.

> ⚠ **Keep two stop fields.** `initial stop` (frozen, the denominator of R) and `current stop` (updates as you trail).
> Collapse them and the moment you move a stop, every historical R is rewritten — silently, while the numbers still look like numbers.

## 3. R-multiples: convert money into "units"

**R = this trade's P&L ÷ this trade's initial risk**

Initial risk = |entry − initial stop| × qty.

Example: a trade risking $2,500 that makes $7,500 is **+3R**.

Why this is mandatory: making $500 on a $10,000 position and $500 on a $100,000 position are **completely different events**. Converted to R, trades of different sizes finally belong in the same distribution.

**This is the foundation of Van Tharp's whole framework**: a system *is* its R-distribution.

## 4. The metrics you must know

| Name | How it's computed | How to read it |
|---|---|---|
| **Expectancy** | Mean R per trade | **>0 means you have an edge.** +0.88R = every 1 unit of risk returns 0.88 on average |
| **Win rate** | Wins ÷ total | **Meaningless alone** — always read it with payoff |
| **Payoff** | Avg win R ÷ avg loss R | 39.9% win rate + 3.40× payoff = a healthy right-tail style |
| **Profit factor** | Gross profit ÷ gross loss | >1 to make money, >2 is good |
| **Max drawdown** | Largest peak-to-trough fall | **By percentage, not dollars** (see below) |
| **Sharpe** | Excess return ÷ volatility | >1 good, >2 excellent. **Punishes upside volatility too** |
| **Sortino** | Only punishes downside | Fairer than Sharpe for right-tail strategies |
| **Calmar** | CAGR ÷ max drawdown | "Return earned per 1% of drawdown endured" |
| **SQN** | √min(N,100) × expectancy_R ÷ stdev(R) | Van Tharp's system-quality grade — see Advanced |

## 5. The three mistakes that bite first

**① Select drawdown by percentage, not dollars.**
While an account grows $1M → $2M: an early $200k fall is −20%; a later $220k fall is only −11%. **Searching for the largest dollar drop picks the later one and misses the genuinely more painful earlier one.** (We actually made this mistake.)

**② Mark open positions to market (MTM).**
Counting only closed trades = pretending unrealised losses don't exist. A real equity curve values open positions at each day's close — only then is the drawdown real.

**③ Compound monthly returns; don't divide by fixed capital.**
`month-end equity ÷ prior month-end equity − 1`, not `realised P&L ÷ starting capital`. The latter distorts badly once the account grows, and it won't reconcile with your dashboard.

---

# Advanced

## 6. SQN and its trap

```
SQN = √min(N, 100) × (mean R ÷ stdev R)
```

Bands: <1.6 poor · 1.6–2.0 below average · 2.0–2.5 average · **2.5–3.0 good** · 3.0–5.0 excellent · 5.0–7.0 superb · ≥7.0 holy grail

**⚠ N must be capped at 100.** That cap is exactly what calibrates the bands. With an uncapped √N, a 331-trade record gets promoted to 4.99 "excellent" — when the true value is **2.74 "good"**. (We made this one too.)

**A high SQN does not mean high returns.** It rewards the *consistency* of the R-stream. To raise it: tighten the loss tail and let winners run — **not bet bigger** (betting bigger scales numerator and denominator alike; SQN doesn't move).

## 7. When Kelly lies to you

Kelly gives the growth-optimal bet fraction. In live trading it is almost always **too large**, for three reasons:

1. **Fat right tail** — a few +20R trades drag f\* to absurd levels
2. **One-sided sample** — an edge measured in a bull run isn't a stationary edge
3. **The edge itself is an estimate**, not a known constant

Real example from this account: **f\* = 15.9% per 1R, portfolio leverage λ\* = 5.8×**. Following that is suicide.

**So: half-Kelly or less, and treat Kelly as a ceiling, not a target.**
"Bet double Kelly and you eliminate 100% of your gain" — that isn't rhetoric, it's arithmetic.

## 8. Sizing: the most underrated discipline

Three questions to ask in every review (most people ask none of them):

**① Is my position size correlated with my results?**
Compute `corr(size %, R)`. Our answer was **−0.00** — how much was bet had *no relationship* to how the trade turned out. Meaning the sizing layer contributed **no alpha, only variance**.

**② What if every trade carried equal risk?**
Reallocate the same total risk budget evenly and re-run. Our answer: **+66.7%**. So the problem wasn't the *level* of risk, it was its *allocation*.

**③ How many positions should I hold?**
```
N* = total risk budget ÷ per-trade risk, then min(N*, empirical hard line)
```
Example: 3% budget ÷ 0.25% per trade = **12 names**. Interestingly, this computed number often coincides with the hard line you'd set from experience — which means the empirical threshold isn't folklore, it's the shadow of the risk arithmetic.

**The rule produces the number; the hard line caps it** — two layers, not an either/or.

## 9. Portfolio heat: one number isn't enough — you need three

Most people watch only the first, and it's the smallest:

```
① Committed risk      = Σ |entry − stop| × open qty ÷ equity that day
② True open exposure  = Σ max(0,(mark − stop)·dir) × open qty ÷ equity that day
③ Open profit at risk = ② − ①
```

Our measurements: ① median 3.53%, but ② median **7.45%**, peak ceiling **30%**.

**Root cause**: winners run while the stop stays put → the distance from mark down to stop keeps widening → **all the accumulated open profit rides unprotected.**

Add a **concentration** row too (top 3 names as a share of exposure) — on our peak day that was 54%, with a single ticker at 8.6%.

> This is why the max drawdown was −17.9%: carrying 30% exposure into a month, that number is arithmetic, not bad luck.

## 10. Regime attribution (if you have market-state data)

Bucket each trade by the market-condition score on its **entry day**, then compare win rate and mean R per bucket.

What we found: **the hottest regime held the most trades (47% of them) at the worst quality** (34.6% win rate); the real sweet spot was the "constructive" band.

Three warnings that must travel with the result:
1. Bucketing is by **entry day**, but P&L is realised later — trades entered in a bad regime and closed in the rally flatter that bad regime
2. The sample is usually a single market phase
3. **The score very likely has no predictive power over returns** (we verified: over 558 sessions it did not predict next-month return) — it is far more likely to separate **drawdown risk**

**So it's a risk-budget reading, not a timing signal.** Use it to decide *how much risk to spend*, never *which way to lean*.

## 11. The honesty discipline

These matter more than any metric:

- **Report NULL results.** "The thing you feared isn't real" is as valuable as finding a problem. We tested whether re-attacking a name was the biggest leak — it **wasn't** (those trades averaged +1.21R). The real problem was oversizing the few that failed.
- **Label every number's scope.** The same word (expectancy) over two samples is two different numbers. Two adjacent panels showing different "expectancy" with no label is manufactured confusion.
- **Forward-looking numbers get ranges, not point estimates.** Monte Carlo, Kelly, expected growth — all must carry sample size and a pessimistic case.
- **Separate market risk from your own behaviour.** Sometimes the market is fine and you simply trade badly in that environment — the prescription is completely different.
- **Reconcile across surfaces.** A report and a dashboard computing the same metric must use the same formula. Cross-checking is how we caught our own miscomputed SQN.

---

## Appendix: glossary

| Term | One line |
|---|---|
| R-multiple | P&L ÷ initial risk — money converted into "units" |
| Expectancy | Mean R per trade; >0 means an edge |
| MTM | Mark-to-market — open positions valued at the day's close |
| Drawdown | Fall from the running peak — **by %, not $** |
| Profit factor | Gross profit ÷ gross loss |
| Sharpe / Sortino | Risk-adjusted return; the latter punishes only downside |
| Calmar | CAGR ÷ max drawdown |
| SQN | System Quality Number, N capped at 100 |
| Kelly | Growth-optimal bet fraction; use half or less live |
| Percent-risk | Risk a fixed % of equity per trade (Tharp's professional standard) |
| Percent-volatility | Size by ATR so every position risks equal volatility |
| Anti-martingale | Press winners, cut losers (the opposite of averaging down) |
| Position heat | Total open risk as a share of equity |
