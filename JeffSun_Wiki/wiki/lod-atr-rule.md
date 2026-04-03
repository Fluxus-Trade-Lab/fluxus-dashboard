---
title: "LoD ATR Rule"
aliases: ["60% ATR rule", "LoD ATR filter", "low of day ATR"]
category: "Entry & Execution"
tags: ["glossary-term", "ATR", "LoD", "execution", "risk-management"]
sources: ["https://x.com/jfsrev", "Complete Guide Chapters 2 & 6"]
related: ["entry-rules", "execution-quality", "rvol-based-entry"]
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# LoD ATR Rule

> [!summary]
> Jeff Sun's first hard rule: do not enter a trade if the low of the day (LoD) already exceeds 60% of the stock's ATR below the current price. This rule quantifies how much of the day's volatility range has been consumed, ensuring entries retain sufficient "spring coil" energy for the intended move.

## Core Concept

The LoD ATR rule is a concept frequently emphasized in Qullamaggie's streams and formalized by Jeff Sun as Hard Rule #1 in his [[entry-rules]]. It measures the distance from the current price to the intraday low, expressed as a percentage of the stock's Average True Range.

If a stock has already traveled a large portion of its daily ATR downward before your entry, the remaining range available for an upward move within the session is compressed. You are entering a stretched spring with no snap-back energy.

## Full Calculation

**Formula:**

```
LoD ATR% = (Current Price - Low of Day) / ATR x 100
```

**Example from Jeff's material:**

| Variable       | Value   |
|----------------|---------|
| Current Price  | $24.49  |
| Low of Day     | $22.16  |
| ATR (14-day)   | $2.25   |

```
LoD ATR% = ($24.49 - $22.16) / $2.25 x 100 = 104%
```

At 104%, the LoD distance has consumed more than the stock's entire average daily range. This trade is a hard pass -- the spring is fully extended.

**The rule: only enter when LoD ATR% is below 60%.**

In the example above, for a $24.49 entry to qualify, the LoD would need to be no lower than:

```
Maximum LoD = $24.49 - (0.60 x $2.25) = $24.49 - $1.35 = $23.14
```

Since the actual LoD of $22.16 is well below $23.14, the entry is rejected.

## Visualizing ATR as Spring Coil

Jeff visualizes ATR as a compressed spring:

- **Coiled tight (LoD < 60% ATR):** The stock has not consumed much of its daily range. There is stored energy for the breakout to expand within the day's volatility envelope. The spring can still snap.
- **Extended (LoD > 60% ATR):** The stock has already used most of its range. Entering now means buying into a move that has already consumed its expected daily energy. The spring is stretched out.

This metaphor makes the rule intuitive during fast-moving live market conditions, when there is no time for deliberation.

## Perks of <60% LoD Execution

Entering within the 60% ATR threshold provides multiple structural advantages:

1. **Tighter stops:** The stop loss (typically at or near LoD) is closer to the entry price, reducing position risk in dollar terms
2. **Higher R-multiples:** With a tighter initial risk, any given price target produces a larger R-multiple (see [[execution-quality]] for the parabolic R effect)
3. **Better position sizing:** Tighter risk allows larger position sizes within the same % risk-to-equity budget
4. **Reduced drawdown duration:** Tighter stops mean faster loss recognition on failed trades

## "This Is Why You Should Trade Tight"

Jeff's thread on trading tight connects the LoD ATR rule to the broader execution philosophy: the compound effect of tight entries across hundreds of trades creates a fundamentally different equity curve than loose entries on the same setups. The math is not linear -- it is parabolic (see [[execution-quality]]).

## USIC 2023: 2nd Place From Small Caps + Tight Entries

Jeff kicked off the US Investing Championship (USIC) 2023 in 2nd place using a strategy built on:

- **Small caps** with high volume turnover relative to market cap
- **Entry at breakout level** without LoD exceeding 60% ATR

This result validated the LoD ATR rule under competitive conditions, where every basis point of edge matters. The combination of high-ADR% small caps and disciplined LoD ATR filtering produced outsized returns relative to risk taken.

## How Jeff Applies It

The LoD ATR rule is checked in real-time at the moment of execution:

1. A price alert fires on a Focus List name at its breakout level
2. Jeff checks the current LoD distance relative to ATR using his Swing Data indicator
3. If LoD exceeds 60% ATR: **no entry**, regardless of how strong the setup appears
4. If LoD is within 60% ATR: proceed to evaluate remaining [[entry-rules]] (RVOL, gap resistance, 200-MA, etc.)

The rule is binary and non-negotiable. There is no "close to 60%" exception.

## Related Concepts

- [[entry-rules]] -- LoD ATR is Hard Rule #1
- [[execution-quality]] -- The parabolic R-multiple effect of tight entries
- [[rvol-based-entry]] -- Complementary volume confirmation filter
- [[three-stop-strategy]] -- Post-entry risk compression

## Sources

- [What does "60% ATR below LoD" mean at execution level](https://x.com/jfsrev/status/1788583106418541011)
- [Perks of <60% LoD Execution](https://x.com/jfsrev/status/1788135099273281737)
- [This is why you should trade tight](https://x.com/jfsrev/status/1648131096901726209)
- [USIC 2023 2nd place from small caps + tight entries](https://x.com/jfsrev/status/1628559711917473793)
- [Swing Data indicator (ADR% / RVol / Float %)](https://www.tradingview.com/v/uloAa2EI/)
