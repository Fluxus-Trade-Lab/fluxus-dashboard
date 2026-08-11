# Trade Review · Ready-to-Use Prompts

Hand a trade log to an AI and get back **conclusions that change your next decision** — not a pile of pretty charts.

Copy any prompt below as-is. Every requirement in them exists because we got it wrong first (see the table at the end).

Companion docs: [`TRADE_ANALYSIS_GUIDE.en.md`](./TRADE_ANALYSIS_GUIDE.en.md) (concepts & method) · 中文版: [`TRADE_ANALYSIS_PROMPTS.zh.md`](./TRADE_ANALYSIS_PROMPTS.zh.md)

---

## 0 · Prepare the data first

Export your trades to CSV. Every trade needs **at minimum**:

| Field | Why it's required |
|---|---|
| Ticker · direction · entry date · entry price · quantity | The basics |
| **Initial stop** | **No stop, no R** — R is the foundation of everything below |
| Each scale-out: price / qty / date | Without the legs you can't get P&L right, or measure trimming behaviour |

> ⚠ **Initial stop and current stop must be two separate fields.**
> The first is frozen and serves as R's denominator; the second updates as you trail.
> Collapse them into one and the moment you move a stop, every historical R is silently rewritten.

---

## 1 · Full review report (with charts)

```
Here is my complete trade log for [period] (CSV with entry price / initial stop /
quantity / each scale-out's price, qty, date).

First convert each trade to an R-multiple (R = P&L ÷ (|entry − initial stop| × qty)),
then produce a chart-rich review containing:
① Mark-to-market equity curve + drawdown (value open positions at each day's close)
② Cumulative-R curve, per-trade R bars, R-distribution histogram
③ Monthly/quarterly returns, contribution by ticker (in R, best and worst side by side)
④ Profit concentration (top N trades = what % of profit), drawdown distribution +
   the N deepest episodes, rolling profit factor, losing-streak analysis

Requirements:
- Select max drawdown by PERCENTAGE, not dollars (as an account grows, a later
  dollar drop is a smaller percentage — a dollar-max search misses the real worst one)
- Monthly return = compounded month-over-month on the equity curve (endEq/prevEq − 1),
  NOT realised P&L ÷ fixed starting capital
- Give me concrete numbers, no generalities
```

## 2 · Behavioural diagnosis (why I win / why I lose)

```
Run a behavioural diagnosis on my trade log. Every conclusion must be backed by data:
1) What do my biggest losses have in common, technically and behaviourally?
   (Bottom-fishing? Counter-trend? Holding losers too long? Re-attacking the same
   broken thesis?)
2) Same question for my biggest winners.
3) In drawdowns, do I size up or size down?
4) How do I trim, and how do I use stops?

Requirements:
- No hindsight platitudes like "avoid Mondays" — it has to be actionable
- If something I'm worried about turns out NOT to be a problem, say so explicitly
  as a NULL result and prove it with data
- Separate the FIRST entry from subsequent add-ons — many leaks hide in the adds,
  not in the initial entry
```

## 3 · Position-sizing audit (the deepest layer)

```
Audit my position sizing:
1) Is position size (notional ÷ equity at entry, %) correlated with the trade's final R?
   Compute the correlation and plot it.
2) What is my real per-trade risk (1R) as a % of equity? Compare it to my stated target.
3) Counterfactual: if every trade had carried EQUAL RISK (same total risk budget,
   reallocated), how much more or less would I have made on these same trades?
4) Per Van Tharp's percent-risk / percent-volatility models and (half) Kelly, how much
   should I be risking? Give the Kelly number, but state honestly how it distorts on a
   bull-market sample with a fat right tail.
5) Bootstrap my R-distribution with Monte Carlo: for each risk-per-trade %, give the
   median ending return, median max drawdown, and P(drawdown > X%)
   (Van Tharp's position-sizing-to-objectives).

Also: compute portfolio heat three ways, not one:
① Committed risk  = Σ |entry − stop| × open qty ÷ equity that day
② True exposure   = Σ max(0,(mark − stop)·dir) × open qty ÷ equity that day
③ Open profit at risk = ② − ①
And give the concentration on the peak day (top 3 names as a share of exposure).
```

## 4 · Counterfactual + the one thing to change

```
Based on everything above: if I could change only ONE thing, which change moves my
total return / drawdown the most?
Quantify it as a counterfactual ("change these trades and the result goes from X to Y").
Give me 2–3 actionable rules in this exact form: "Stop doing X. Do Y instead."
```

## 5 · SQN · System Quality Number

```
Compute my SQN (System Quality Number = √min(N,100) × expectancy_R ÷ stdev(R);
**N must be capped at 100**).
Tell me which Tharp band I fall in (poor / below average / average / good / excellent /
superb / holy grail), and what I'd have to improve to move up a band — tighten the loss
tail, let winners run, or something else. Note that betting bigger does NOT raise SQN.
```

## 6 · Market-regime attribution (advanced — needs a market-state time series)

```
I have a daily market-condition score (0–100). Bucket each trade by the score on its
ENTRY day and report per bucket: trade count / win rate / mean R / total R / total P&L.

Requirements:
- State explicitly which band scheme and cut points you used
- State the available history range — do not silently truncate
- Warn me that entry-day bucketing means P&L may have been realised in a later regime
  (this flatters the "bad" regimes)
- If the score has no predictive power for returns (common), say so plainly; it is far
  more likely to separate DRAWDOWN RISK than direction
```

---

## Universal requirements (append to any prompt above)

```
Also follow these:
- Label every number with its SCOPE and SAMPLE (e.g. "live · this book, 331 trades"
  vs "H1 audit snapshot"). The same word under two scopes is not the same number.
- Forward-looking numbers (Monte Carlo / Kelly / expected growth) must be given as
  RANGES, never point estimates, and must carry the sample size.
- Report NULL results. "The thing you were worried about isn't real" is as valuable
  as finding a problem.
- Distinguish correlation from causation — and distinguish MARKET risk from MY
  behavioural problem. The prescriptions are completely different.
```

---

## Appendix: where each requirement came from

| Requirement | The bug that taught it |
|---|---|
| Select drawdown by percentage | We reported the true −17.9% max drawdown as −11.1% (picked the largest *dollar* drop) |
| Monthly return = compounded MTM | Report and dashboard disagreed — one compounded, one divided by fixed capital |
| Initial stop separate from current stop | Trailing a stop silently rewrote historical R |
| Label the scope | Two panels on one page both said "expectancy" over different samples |
| Cap SQN's N at 100 | Uncapped √N promoted a long record into a band it hadn't earned (4.99 "excellent" vs the true 2.74 "good") |
| Flag Kelly's distortion | A one-sided bull sample produced f\*=15.9%, λ\*=5.8× — following it would be suicide |
| Heat measured three ways | Committed risk read 3.5%; true open exposure was 7.5% (peak ceiling 30%) |
