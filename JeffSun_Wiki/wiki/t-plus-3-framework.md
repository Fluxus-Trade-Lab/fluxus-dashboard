---
title: "T+3 Framework"
aliases: ["T+3", "t plus 3", "day-by-day stops", "T+3 decision framework"]
category: "Core System"
tags: [stop-loss, risk-management, trade-management, core-system, glossary-term]
sources:
  - "jfsrev-1841852289742733701"
  - "jfsrev-1855927716404761065"
  - "substacks/risk-and-position-management"
  - "notion/swing-trade-system-snapshot"
related:
  - "[[3-stop-strategy]]"
  - "[[trailing-stops]]"
  - "[[sell-rules]]"
  - "[[inverse-pyramid]]"
notion_ref: "1555bc7910f780bba6cef7c4a372243c"
created: 2026-04-03
updated: 2026-04-03
---

# T+3 Framework

> [!summary]
> Jeff Sun's day-by-day decision framework for managing stops and profit-taking after trade execution. T = execution day; each subsequent "day" counts only trading sessions (weekends and market holidays excluded). By Day 3, the trade must have proven itself — otherwise, size is reduced and the stop moves to breakeven.

## Core Concept

The T+3 framework is the operational layer built on top of the [[3-stop-strategy]]. Where the 3-stop strategy defines *how* stops are placed at entry, the T+3 framework defines *when and how* those stops evolve over the life of the trade.

The underlying philosophy is time-based accountability: a trade has roughly three days to prove itself. If by Day 3 price hasn't moved meaningfully in your favor, the position is trimmed and risk is eliminated. Conversely, if a trade moves strongly in the first few days, profits are locked in progressively.

> "T = execution day; +1 = Day 1 after execution; +3 = Day 3 after execution. 'Day' does not include weekends or market holiday."
> — Glossary, Complete Guide

## Rules / Details

### Day 0 — Execution Day

- Place 3 stops at 33% each to LoD (Low of Day) per the [[3-stop-strategy]]

### Days 0-2 — Early Profit Checkpoints

- **If profit exceeds 2R:** Shave 33% of the position (sell into strength)
- **If profit exceeds 4R:** Shave another 33% of net size + move the single remaining stop to the average entry price (breakeven)

### Day 3 — Decision Day

- **If no prior profit-taking or stop-loss has occurred:** Reduce position by 33%
- Move all remaining stops to a single stop at breakeven
- If partially stopped out before Day 3, move the stop to the LoD of Day 3

### Day 4+ — Trailing Phase

- **If profit exceeds 3R:** Reduce 30% of net size, adjust stop sizes accordingly
- **If 8-10x ATR% extension from 50-MA:** Reduce 30% of net size (selling into extreme extension)
- Use the 10-day MA as a mental stop (see [[trailing-stops]] for the ORL technique)
- Hard stop remains at breakeven until the 10-MA trailing process kicks in

## How Jeff Applies It

The framework creates a natural filter: trades that survive T+3 without hitting any stop layers tend to be strong runners.

> "When I'm positioned in a trade that doesn't hit layer 1 (33%) or layer 2 (66%) stops within T+3, it's typically a strong runner, often yielding 5R+ based on my sell rules."
> — [[sources/tweets/jfsrev-1855927716404761065|Tweet]]

Jeff's KC trade (+180% gain) exemplifies the framework in action: the position survived the initial T+3 window, partials were taken into strength at 2R and at ATR% extension thresholds, and the remainder was trailed with the 10-day MA for weeks.

The framework also integrates with [[inverse-pyramid]] logic: if a stop is hit before Day 4, the trader sets an alert at the High of the stop day and can add 50% back on a reclaim — a re-entry technique that keeps total R risk within bounds.

### Key Nuance: Day 3 as Automatic Trim

Even if a trade is profitable but has not exceeded the 2R or 4R thresholds, Day 3 forces a 33% reduction. This rule ensures that no position lingers at full size without having demonstrated meaningful momentum. Being above the average entry price on Day 3 is the minimum bar — and even then, size comes off.

## Related Concepts

- [[3-stop-strategy]] — The initial stop placement that the T+3 framework modifies over time
- [[trailing-stops]] — The 10-MA and ORL trailing methodology used from Day 4 onward
- [[sell-rules]] — The broader profit-taking philosophy (Qullamaggie's 3 golden rules) that the T+3 framework implements
- [[inverse-pyramid]] — Re-entry and adding strategies triggered by stop events within the T+3 window

## Sources

- [[sources/tweets/jfsrev-1841852289742733701|Tweet: "My Systemized Approach to 3-Level Stop Exits (and Profit-Taking)..."]]
- [[sources/tweets/jfsrev-1855927716404761065|Tweet: ITA Trade Example with T+3 walkthrough]]
- [[sources/notion/swing-trade-system-snapshot|Notion: Swing Trade Risk Management System — day-by-day rules]]
- [[sources/substacks/risk-and-position-management|Substack: Risk and Position Management by Kyna Kosling]]
