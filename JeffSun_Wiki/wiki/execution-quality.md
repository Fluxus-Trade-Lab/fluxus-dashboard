---
title: "Execution Quality"
aliases: ["tight entries", "A-rated setup C-rated execution"]
category: "Entry & Execution"
tags: ["execution", "risk-reward", "ATR", "monte-carlo"]
sources: ["https://x.com/jfsrev", "Complete Guide Chapters 6 & 9"]
related: ["entry-rules", "lod-atr-rule", "rvol-based-entry"]
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# Execution Quality

> [!summary]
> An A-rated setup can produce C-rated execution if the entry is sloppy. Jeff Sun treats execution quality as the single highest-leverage variable in swing trading -- tighter risk at entry produces parabolically better R-multiple returns, not linearly better ones.

## Core Concept

The central thesis: **the quality of your entry determines the quality of your trade**, independent of how good the setup looked on a chart the night before. A stock that met every Focus List criterion can still produce a mediocre trade if you enter with loose risk.

> "An astounding trading idea, when it comes up for execution in the live market, must be reassessed by its risk-to-reward potential based on the price action at that *moment*."

## ATR as Spring Coil

Jeff visualizes ATR (Average True Range) as a **compressed spring coil**. When a stock has consumed most of its daily ATR range before your entry, the spring is already extended -- there is little energy left for the move you are trying to capture.

- A stock with 60%+ of its ATR already consumed below LoD has a stretched spring -- minimal snap-back potential
- A stock with less than 60% ATR consumed below LoD has a coiled spring -- stored energy for the breakout move

This is why the [[lod-atr-rule]] exists: it quantifies exactly how much spring tension remains at the moment of entry.

## ATR% from 50-MA as Launchpad

The ATR% multiple from the 50-day moving average serves as a **launchpad metaphor**. The 50-MA is the launch platform; the number of ATR% multiples above it represents how far the rocket has already traveled.

- At 1-2x ATR% from 50-MA: still on the launchpad, maximum thrust available
- At 4x+ ATR% from 50-MA: already in orbit, diminishing returns on new entries

> Hard rule: Jeff does not enter a trade if ATR% from 50-MA extension exceeds 4x multiples.

The combination of the two metaphors creates a dual filter: the spring coil governs intraday entry precision, while the launchpad governs multi-day extension risk.

## Tighter Risk Produces Parabolic R Returns

Chapter 9 Graphic #1 (attributed to Marios Stamatoudis) demonstrates that executing trades at tighter risk does not produce a linear improvement in R-multiples -- the effect is **parabolic**.

If a stock moves +10% from a breakout level:
- A 5% stop produces +2R
- A 2.5% stop produces +4R
- A 1.25% stop produces +8R

Halving the risk doubles the R, but the compounding effect across a portfolio of trades creates exponential equity curve improvement. This is the mathematical backbone behind Jeff's obsession with tight entries.

## Monte Carlo Simulation: 500 Trades

Chapter 9 Graphic #2 presents a comparative Monte Carlo simulation based on 500 trades, comparing standard entries versus 50% tighter entries. The simulation demonstrates that even a modest improvement in entry tightness -- achieved without changing setups, win rate, or position sizing -- produces dramatically different equity curves over a large sample of trades.

The key insight: **you do not need better setups to trade better. You need tighter entries on the same setups.**

## How Jeff Applies It

Jeff's entire execution framework is built around this principle:

1. **Pre-market**: Focus List is prepared with ideal entry levels and stop distances
2. **At execution**: Hard rules (see [[entry-rules]]) filter for conditions that allow tight entries
3. **If conditions degrade**: The trade is passed entirely rather than entered with loose risk
4. **Post-entry**: The [[three-stop-strategy]] further reduces average R loss to -0.67R per trade

The willingness to miss a trade entirely -- rather than enter it with suboptimal risk -- is what separates professional from amateur execution.

## Related Concepts

- [[entry-rules]] -- The 15 hard rules that enforce execution quality
- [[lod-atr-rule]] -- The spring coil in practice
- [[rvol-based-entry]] -- Volume confirmation for tight entries
- [[three-stop-strategy]] -- Post-entry risk compression

## Sources

- [A-Rated Setup Can Result in C-Rated Execution](https://x.com/jfsrev/status/1851226250553217242)
- [Tighter Risk Has Parabolic Effect on R Returns -- Marios Stamatoudis](https://x.com/jfsrev/status/1948260986143801469)
- [Monte Carlo Simulation: 500 Trades vs 50% Tighter Entries](https://x.com/jfsrev/status/1948612229240410184)
- [ATR% from 50-MA extension rule](https://x.com/jfsrev/status/1763489489652212091)
- [Visualizing ATR as Spring Coil](https://x.com/jfsrev/status/1788583106418541011)
