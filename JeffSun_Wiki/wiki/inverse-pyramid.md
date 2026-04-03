---
title: "Inverse Pyramid"
aliases: ["inverse pyramid", "re-entry strategy", "adding back", "pyramid adds"]
category: "Core System"
tags: [position-sizing, re-entry, trade-management, core-system]
sources:
  - "jfsrev-1957632693413507158"
  - "jfsrev-1841852289742733701"
  - "notion/swing-trade-system-snapshot"
  - "substacks/risk-and-position-management"
related:
  - "[[3-stop-strategy]]"
  - "[[t-plus-3-framework]]"
  - "[[position-sizing]]"
  - "[[trailing-stops]]"
notion_ref: "1555bc7910f780bba6cef7c4a372243c"
created: 2026-04-03
updated: 2026-04-03
---

# Inverse Pyramid

> [!summary]
> Jeff Sun's re-entry and position-adding methodology after stops are triggered or during sideways consolidations. The key constraint: any add-back must keep the total R loss within -1R. By adding at 50% of the original size, Jeff maintains risk discipline while capturing trades that initially shook him out but then resumed their move.

## Core Concept

The inverse pyramid is the complement to the [[3-stop-strategy]]. While the 3-stop strategy manages the initial exit, the inverse pyramid manages the re-entry. The name reflects the sizing logic: re-entries are smaller than the original position (50% of prior size), creating an inverted pyramid shape where the base (initial entry) is largest and subsequent adds are progressively smaller.

This addresses a common scenario in momentum trading: a stock triggers your stop, shakes out weak hands, then resumes the move without you. Rather than chasing at a worse price, Jeff sets systematic alerts and adds back at a reduced size that keeps total portfolio risk controlled.

> "Remember, if the market does not prove the position correct, it is still possible the market has not proven the position wrong."
> — [[sources/tweets/jfsrev-1647920676186251264|Tweet]]

## Rules / Details

### Scenario 1: Stop Hit Before Day 4

When one or more stop layers are triggered within the T+3 window:

1. **Set an alert** at the High of the day the stop was hit
2. **If the high is reclaimed:** Add back 50% of the original position size
3. The new stop is placed per the [[3-stop-strategy]] rules on the new entry
4. Total R exposure from both the realized loss and the new position must remain within -1R

This rule recognizes that early stops often reflect intraday noise rather than genuine trade failure. A stock that reclaims the high of its shakeout day is demonstrating renewed buying interest.

### Scenario 2: Sideways Consolidation

When a position survives T+3 but enters a sideways range rather than trending:

1. **Add 50% of net size** (net size = current remaining position after any partials)
2. **Only if** the stock is below 4x ATR% extension from the 50-day MA
3. The ATR% constraint ensures you are not adding into an already-extended move

### Sizing Methodology for Re-Entries

Jeff's re-entry sizing is designed to keep total R loss within -1R even if the re-entry also fails:

- Original trade loss (via 3-stop): approximately -0.67R
- Re-entry at 50% size with its own stop: maximum additional loss calculated to keep combined loss at or below -1R
- This is documented in Jeff's spreadsheet template for the [[3-stop-strategy]]

## How Jeff Applies It

### The BMNR Trade Example

Jeff shared a detailed example of when he adds into a position using the BMNR trade:

> "When Do I Add Into A Position? BMNR trade example"
> — [[sources/tweets/jfsrev-1957632693413507158|Tweet]]

In this case, the stock consolidated sideways after an initial move, meeting the criteria for a 50% add below the 4x ATR% extension threshold. The add-on position had its own stop structure, and the combined risk remained within Jeff's tolerance.

### Example: HIMS, CBAY, ONON, MBLY (April 2023)

Jeff demonstrated the inverse pyramid across multiple trades in April 2023, showing how stocks that initially stopped him out subsequently reclaimed their highs and offered re-entry opportunities at reduced size. The key lesson: not every shakeout is a failed trade.

### Priority Shift After T+3 Portfolio

Once Jeff has established a durable portfolio (positions beyond T+3), his priority shifts:

> "If I've established a durable portfolio (beyond T+3), my priority shifts to adding onto existing positions, as they're already well above my breakeven stop level, and they've proven to be leading."
> — [[sources/tweets/jfsrev-1968946399740940605|Tweet]]

This means the inverse pyramid is not only a re-entry tool but also a scaling tool for proven winners.

## Related Concepts

- [[3-stop-strategy]] — The initial stop structure that the inverse pyramid responds to when stops are hit
- [[t-plus-3-framework]] — Defines the Day 4 boundary that triggers different re-entry rules
- [[position-sizing]] — The broader sizing framework that constrains inverse pyramid adds
- [[trailing-stops]] — How trailing stops interact with consolidation adds

## Sources

- [[sources/tweets/jfsrev-1957632693413507158|Tweet: "When Do I Add Into A Position? BMNR trade example"]]
- [[sources/tweets/jfsrev-1647920676186251264|Tweet: "Remember, if the market does not prove the position correct..."]]
- [[sources/tweets/jfsrev-1968946399740940605|Tweet: "If I've established a durable portfolio (beyond T+3)..."]]
- [[sources/tweets/jfsrev-1648542848994922496|Tweet: "Example with HIMS, CBAY, ONON, MBLY in April 2023"]]
- [[sources/notion/swing-trade-system-snapshot|Notion: Swing Trade Risk Management System — Inverse Pyramid section]]
- [[sources/substacks/risk-and-position-management|Substack: Risk and Position Management by Kyna Kosling]]
