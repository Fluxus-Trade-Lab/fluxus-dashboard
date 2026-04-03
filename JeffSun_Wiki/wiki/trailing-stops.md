---
title: "Trailing Stops"
aliases: ["trailing stop methodology", "10-MA trailing", "ORL technique", "opening range low"]
category: "Core System"
tags: [stop-loss, trailing-stops, trade-management, core-system]
sources:
  - "jfsrev-1841852289742733701"
  - "jfsrev-1855927716404761065"
  - "substacks/risk-and-position-management"
  - "notion/swing-trade-system-snapshot"
related:
  - "[[t-plus-3-framework]]"
  - "[[sell-rules]]"
  - "[[3-stop-strategy]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# Trailing Stops

> [!summary]
> After the initial T+3 period, Jeff Sun transitions from fixed LoD stops to a trailing methodology anchored by the 10-day moving average. For his Singapore timezone, he uses a specific 5-minute Opening Range Low (ORL) technique to manage the gap between the MA close signal and the next session's execution. The overriding goal: hold winners as long as possible with minimal sacrifice of unrealized profit.

## Core Concept

The trailing stop methodology is the third phase of Jeff's trade management, following the [[3-stop-strategy]] (Day 0) and the [[t-plus-3-framework]] (Days 0-3). Once a trade has survived T+3 and the hard stop is at breakeven, the question shifts from "is this trade working?" to "how long can I ride it?"

Jeff's answer: trail with the 10-day MA as a mental stop, but use a precise intraday process (ORL) to avoid getting whipsawed by a single bad close.

> "The rationale is to hold onto your winning trade as long as possible with minimal sacrifice of unrealized profit."
> — [[sources/substacks/risk-and-position-management|Substack: Risk and Position Management]]

## Rules / Details

### Phase 1: Breakeven Stop (Day 3 or Earlier)

- **Day 3:** Move all remaining stops to breakeven (average entry price)
- **Before Day 3, profit > 4R:** Also move to breakeven early
- The breakeven stop is a hard order, not a mental level

### Phase 2: 10-Day MA as Mental Stop (Day 4+)

- From Day 4 onward, the 10-day MA becomes the primary trailing reference
- This is a **mental stop**, not a hard order — Jeff watches for a daily close below the 10-MA before acting

### Phase 3: ORL Execution Process (Singapore Timezone Adaptation)

When the stock closes below the 10-day MA, Jeff does not sell immediately. Instead:

1. **Close below 10-MA detected:** Keep hard stop at breakeven. Let the market open the next day.
2. **Next session open:** Wait for the first 5 minutes of trading to establish the Opening Range Low (ORL).
3. **Set hard stop at 5-minute ORL:** If this level is taken out during the session, the position is exited.
4. **ORL holds all day:** Before the next market open, move the hard stop back to breakeven.
5. **Repeat:** Set the stop at the new session's 5-minute ORL the following day.
6. **Continue until stopped out:** This ORL process repeats day after day until the stop is eventually triggered.

### Big Gap Down Scenario

- If the stock has a significant gap down after closing below the 10-MA, Jeff uses the **15-minute ORL** instead of the 5-minute ORL for a slightly wider reference range.

### ATR% Extension Trailing

Separately from the MA-based trailing:
- **8-10x ATR% extension from the 50-MA:** Reduce 30% of net size regardless of day count
- This is a sell-into-strength rule (see [[sell-rules]]) rather than a stop-loss rule

## How Jeff Applies It

### Why ORL Instead of Closing Below the 10-MA?

Jeff trades from Singapore, which means the US market close occurs in the early morning hours. A stock closing below the 10-MA could reverse the next day — selling at the close or on the next open would sacrifice profit on a whipsaw. The ORL technique gives the trade one more chance: if the stock can hold above its opening range low the next session, it may be recovering. Only a break of the ORL confirms the weakness.

This process can extend a winning trade significantly. Jeff notes that a 10-MA sell rule can keep you in a position for as long as 5 months:

> "Don't second guess your partial profit-taking or your eventual exit. A 10-MA sell rule can sit you as long as 5 months."
> — [[sources/tweets/jfsrev-1973655851937476920|Portfolio Update, October 2025]]

### The KC Trade

Jeff's +180% KC trade in 2024 exemplifies the full trailing methodology: after surviving T+3, the position was trailed with the 10-MA for weeks. Partials were taken at ATR% extension thresholds, but the core position rode the MA until it was finally violated.

> "Who'd have thought $KC could make a 200% gain in a month? Learn to hold your position and ride winners."
> — [[sources/tweets/jfsrev-1866483247930306837|Tweet]]

## Related Concepts

- [[t-plus-3-framework]] — The day-by-day rules that precede the trailing stop phase
- [[sell-rules]] — The broader philosophy of when and why to exit (Qullamaggie's "you can't outsmart the 10- and 20-day MAs")
- [[3-stop-strategy]] — The initial stop structure from which trailing stops evolve
- [[inverse-pyramid]] — If the trailing stop is hit, the re-entry process may begin

## Sources

- [[sources/tweets/jfsrev-1841852289742733701|Tweet: "My Systemized Approach to 3-Level Stop Exits (and Profit-Taking)..."]]
- [[sources/tweets/jfsrev-1866483247930306837|Tweet: "You do not sell everything until the market proves you wrong..."]]
- [[sources/notion/swing-trade-system-snapshot|Notion: Swing Trade Risk Management System — Day 4+ rules with ORL]]
- [[sources/substacks/risk-and-position-management|Substack: Risk and Position Management — Jeff's Rules on Trailing]]
