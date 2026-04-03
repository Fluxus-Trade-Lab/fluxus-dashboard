---
title: "Pocket Pivot Volume"
aliases: [Pocket Pivot, Simple Volume with Pocket Pivots]
category: "Indicators & Tools"
tags: [indicators]
sources:
  - "https://www.tradingview.com/script/JkB0iCFp-Simple-Volume-with-Pocket-Pivots/"
  - "https://x.com/finallynitin/status/1516415566936182793"
  - "https://x.com/jfsrev/status/1959451625145434489"
  - "https://x.com/jfsrev/status/1950202147787977058"
related:
  - "[[rvol]]"
  - "[[atr-volatility]]"
  - "[[adr-percent]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# Pocket Pivot Volume

> [!summary]
> Jeff uses @finallynitin's "Simple Volume with Pocket Pivots" as his primary volume script on TradingView. The pocket pivot concept identifies days of institutional accumulation within a base, and Jeff pairs it with projected volume analysis and a 50% haircut rule to define actionable high-volume signals.

## Core Concept

A **pocket pivot** is a volume signature that identifies institutional buying within a consolidation or base pattern -- before a traditional breakout occurs. The concept, originally developed by Gil Morales and Chris Kacher, looks for a day where volume exceeds the highest down-volume day over the prior 10 sessions, signaling that buyers are stepping in while sellers are still dominant.

Jeff uses **@finallynitin's Simple Volume with Pocket Pivots** script as his go-to volume indicator:

**TradingView Script**: [Simple Volume with Pocket Pivots](https://www.tradingview.com/script/JkB0iCFp-Simple-Volume-with-Pocket-Pivots/)

> I've tried many great free volume scripts on TradingView, but this one is simple and has everything I need.

The full script introduction was [written by @finallynitin in 2022](https://x.com/finallynitin/status/1516415566936182793).

## Single Day Volume Reshaping Narrative

> A single day of strong price move supported by heightened volume can reshape the narrative and bias of three months of price action.

This principle underscores why Jeff monitors volume so closely. One day of genuine institutional accumulation can fundamentally alter the supply/demand balance that took months to establish. A pocket pivot within a base is often the earliest detectable signal that this shift is occurring.

## Projected Volume with 50% Haircut

> If you find it hard to define what qualifies as high RVOL, use Projected Volume in the script with a 50% haircut.

Jeff's practical approach to filtering volume signals: take the indicator's **Projected Volume** (estimated total volume based on the current session's run rate) and apply a **50% haircut** (discount). If the discounted projection still exceeds the 50-day average volume, the volume is genuinely elevated -- not just an early-session spike that will fade by close. This method reduces false positives from morning volume surges that don't sustain.

## TraderLion's Enhanced Volume

For traders wanting more features, Jeff also references **TraderLion's Enhanced Volume** script, which includes 6 features:

1. **High Relative Volume Bars** -- highlight high RVOL bars with a high closing range in lime green
2. **Low Relative Volume Bars** -- label low RVOL days with a down arrow
3. **Volume Labels** -- high volume days show total shares traded and percent above average
4. **Highest Volume in Over a Year** -- "HV" marker on top of the volume bar
5. **Simple Moving Average** -- SMA overlay on volume without using an indicator slot
6. **High Relative Volume Alerts** -- set alerts when volume surpasses a configurable threshold

## How Jeff Applies It

- **Base analysis**: Identifies pocket pivots within consolidation patterns as early accumulation signals
- **Entry timing**: Uses volume confirmation alongside RVOL and price action before committing capital
- **Narrative assessment**: A single high-volume day can change his bias on a stock that has been basing for months
- **RVOL threshold**: Projected volume with 50% haircut defines the practical bar for "high volume"

## Related Concepts

- [[rvol]] -- RVOL as the broader relative volume framework
- [[atr-volatility]] -- ATR for risk sizing once volume confirms the setup
- [[adr-percent]] -- ADR% for screening high-volatility names to monitor

## Sources

- [Simple Volume with Pocket Pivots (TradingView script)](https://www.tradingview.com/script/JkB0iCFp-Simple-Volume-with-Pocket-Pivots/)
- [@finallynitin's script introduction (2022)](https://x.com/finallynitin/status/1516415566936182793)
- [Single day of volume reshaping 3 months of action](https://x.com/jfsrev/status/1959451625145434489)
- [Projected Volume with 50% haircut as RVOL threshold](https://x.com/jfsrev/status/1950202147787977058)
