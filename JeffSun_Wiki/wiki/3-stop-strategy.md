---
title: "3-Stop Strategy"
aliases: ["3-stop", "three stop strategy", "layered stops", "3-level stops"]
category: "Core System"
tags: [stop-loss, risk-management, position-sizing, core-system, glossary-term]
sources:
  - "jfsrev-1823633361149288749"
  - "jfsrev-1841852289742733701"
  - "jfsrev-1855927716404761065"
  - "jfsrev-1937402718278369337"
  - "jfsrev-1647931380033257475"
  - "substacks/risk-and-position-management"
related:
  - "[[t-plus-3-framework]]"
  - "[[sell-rules]]"
  - "[[trailing-stops]]"
  - "[[entry-rules]]"
  - "[[position-sizing]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# 3-Stop Strategy

> [!summary]
> Jeff Sun's core innovation for managing downside risk: splitting the initial stop-loss into three separate orders, each covering 33% of the position, all set to the Low of Day (LoD). This structure caps average losses at approximately -0.67R instead of the typical -1R, because slippage and spread on a full-position stop almost always result in worse-than-planned execution.

## Core Concept

The 3-stop strategy addresses a fundamental reality: getting stopped out of your full position at your original stop level is rarely just -1R. Slippage, spread, and market conditions routinely push the actual loss beyond -1R. By segregating the stop into three layers at 33% each, the position gets peeled off in stages as price deteriorates, reducing the realized loss to approximately -0.6R to -0.8R per trade.

Jeff developed the 3-stop strategy before the [[t-plus-3-framework]] and notes it has since been widely adopted, including by several quantitative funds.

The strategy produces a distinctive equity curve shape: **gradual decline** during losing streaks (since each loss is capped below -1R) and **parabolic growth** during winning streaks (since winners are held for outsized gains via the T+3 framework).

> "If your win rate is below 40%, your main focus should be on controlling losses. That's why I developed the 3-Stop Strategy — to cap losses at -0.67R instead of -1R, without significantly impacting the trade's overall outcome."
> — [[sources/tweets/jfsrev-1823633361149288749|Tweet]]

## Rules / Details

1. **Day 0 (execution day):** Place 3 stop-loss orders, each at 33% of total position size, all at the Low of Day (LoD).
2. **Layer 1 (33%):** The tightest effective stop — first to trigger if price reverses.
3. **Layer 2 (66% cumulative):** Second layer exits if decline continues.
4. **Layer 3 (100%):** Final layer clears the full position.
5. The three stops are placed at the same price level (LoD) but as separate orders, allowing partial fills at different prices during rapid moves.
6. In gap-down scenarios, the layered approach mitigates the risk of a multiple-R loss that would occur with a single full-size stop.

### Why Not a Single Stop?

A single stop on the full position concentrates execution risk. In fast markets, the fill on a large single order is typically worse than the fill on three smaller orders. The net effect: three segregated stops consistently produce better average exit prices than one aggregated stop.

## How Jeff Applies It

Jeff's 2024 trading stats demonstrate the asymmetry this system creates:

> "When I'm positioned in a trade that doesn't hit layer 1 (33%) or layer 2 (66%) stops within T+3, it's typically a strong runner, often yielding 5R+ based on my sell rules. This year [2024], I've had winning trades as high as 51R, 4 trades at 20R+, and 11 at 10R+, with my max monthly win rate at a low of 31.6%."
> — [[sources/tweets/jfsrev-1855927716404761065|Tweet: ITA Trade Example]]

The math is clear: with losses capped at -0.67R and winners reaching 10-51R, even a 31.6% win rate produces exceptional returns. Jeff frames this as the overlooked core principle:

> "The Overlooked Core Principle of the 3-Stop Strategy: Managing Your Long-Term Average R Losses to Boost Profit Factor."
> — [[sources/tweets/jfsrev-1937402718278369337|Tweet]]

He illustrates the compounding effect by asking traders to imagine 10 consecutive losing trades — the difference between losing 10R (at -1R each) versus 6.7R (at -0.67R each) is substantial over hundreds of trades.

### Tools and Visual Resources

- **TWS Auto Order Panel** by [@traderwillhu](https://x.com/traderwillhu/status/1982846945266680284) — automates the 3-stop placement on Interactive Brokers
- **Graphical displays** by [@RomanBreakouts](https://x.com/RomanBreakouts/status/1842126821308981566) and [@shrederickson](https://x.com/shrederickson/status/1853290307976085957) — visual walkthroughs of the layered stop mechanics
- **Spreadsheet template** with columns and formulas for tracking: [[sources/tweets/jfsrev-1855496538644234475|Tweet]]

## Related Concepts

- [[t-plus-3-framework]] — The day-by-day decision framework that governs when stops are adjusted after initial placement
- [[sell-rules]] — How the 3-stop strategy integrates with profit-taking rules to create asymmetric R outcomes
- [[trailing-stops]] — How stops evolve from LoD to breakeven to the 10-day MA after the initial T+3 period
- [[inverse-pyramid]] — Re-entry sizing methodology that keeps R loss within -1R even when adding back
- [[position-sizing]] — How fixed % risk per trade interacts with the 3-stop structure

## Sources

- [[sources/tweets/jfsrev-1823633361149288749|Tweet: "If your win rate is below 40%, your main focus should be on controlling losses..."]]
- [[sources/tweets/jfsrev-1841852289742733701|Tweet: "My Systemized Approach to 3-Level Stop Exits..."]]
- [[sources/tweets/jfsrev-1855927716404761065|Tweet: "When I'm positioned in a trade that doesn't hit layer 1..."]]
- [[sources/tweets/jfsrev-1937402718278369337|Tweet: "The Overlooked Core Principle of the 3-Stop Strategy..."]]
- [[sources/tweets/jfsrev-1647931380033257475|Tweet: "Imagine the approach with reduction in impact on equity with 10 consecutive losing trades"]]
- [[sources/tweets/jfsrev-1866778428709671171|Tweet: "The Benefits of Maintaining Fixed % Risk Relative to Equity..."]]
- [[sources/substacks/risk-and-position-management|Substack: Risk and Position Management by Kyna Kosling]]
