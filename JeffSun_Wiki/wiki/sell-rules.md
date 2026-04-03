---
title: "Sell Rules"
aliases: ["selling rules", "profit taking rules", "golden rules", "exit rules"]
category: "Core System"
tags: [sell-rules, profit-taking, risk-management, core-system]
sources:
  - "jfsrev-1866483247930306837"
  - "jfsrev-1841852289742733701"
  - "jfsrev-1866377222925553743"
  - "jfsrev-1946774369575047638"
  - "substacks/risk-and-position-management"
related:
  - "[[3-stop-strategy]]"
  - "[[trailing-stops]]"
  - "[[progressive-exposure]]"
  - "[[t-plus-3-framework]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# Sell Rules

> [!summary]
> Jeff Sun's sell discipline is built on Qullamaggie's three "golden rules": always sell some into strength, respect the 10- and 20-day moving averages, and honor your stops without hesitation. Jeff operationalizes these principles through his [[t-plus-3-framework]] and [[3-stop-strategy]], creating a systematic approach that locks in profits while preserving exposure to outsized winners.

## Core Concept

Sell rules are arguably the most important — and most psychologically difficult — part of any trading system. Jeff identifies the core tension: you must sell some into strength to protect profits, but you must also hold long enough to capture the outlier trades that drive annual performance. Getting this balance wrong in either direction is costly.

As Oliver Kell puts it: **"If you don't sell into strength, you'll sell into weakness."**

Jeff adds a complementary constraint: **"Never lose two weeks' gains in a day."** These two principles form the guardrails of his sell discipline.

## Rules / Details

### Rule 1: Always Sell Some Into Strength

Jeff's specific implementation:

1. **Days 0-2, profit > 2R:** Shave 33% of the position
2. **Days 0-2, profit > 4R:** Shave another 33% of net size, move to breakeven stop
3. **Day 3:** Reduce 33% if still holding full size (stock is above average entry)
4. **10x ATR% extension from 50-MA (at entry day):** Take a further 33% off
5. **Day 4+, 8-10x ATR% extension:** Another 30% partial

The purpose of selling into strength is twofold:
- Lock in realized profit to reduce unrealized profit volatility
- Free up capital for new opportunities as the market continues to develop

> "But Don't Sell Too Aggressively Into Strength"
> — [[sources/tweets/jfsrev-1946774369575047638|Tweet]]

### Rule 2: You Can't Outsmart the 10- and 20-Day MAs

This is Qullamaggie's most emphatic rule:

> "The second you think you're smarter than the 10- and 20-day moving average, that's when you're doomed for mediocrity. Trust me. I talk from experience."

Jeff's application:

> "You do not sell everything until the market proves you wrong. Who'd have thought $KC could make a 200% gain in a month? Learn to hold your position and ride winners. The outlier positions that can make an impact on your % performance are often those that you do not expect to make a huge move."
> — [[sources/tweets/jfsrev-1866483247930306837|Tweet]]

The practical implementation: after taking partials into strength, trail the remaining position with the 10-day MA (see [[trailing-stops]]). Do not sell the core position until the MA is violated.

### Rule 3: If Your Stop Is Hit, Just Sell

No thinking, no hoping, no second-guessing.

> "I've seen too many scenarios when things just keep going lower and you hesitate, and now suddenly your stop is twice as big as it would've been, and now it's three times as big..."
> — Qullamaggie, Chat With Traders

Jeff enforces this mechanically through the [[3-stop-strategy]] — the stops are placed as live orders, not mental levels.

## How Jeff Applies It

### The Psychological Reality of Holding Size

Jeff is transparent about the emotional difficulty of holding large positions:

> "As your equity grows (especially when it surpasses your absolute dollar risk tolerance relative to your monthly expenses), seeing unrealized profit drop from, say, +$500,000 to +$280,000 in a single session can be hard to handle, even if you're following textbook rules."
> — [[sources/tweets/jfsrev-1841852289742733701|Tweet]]

> "I believe not many can emotionally withstand holding 8-10 full-sized trades with 80% portfolio utilization, especially when trading with a bankroll that significantly impacts their quality of life and that of their dependents."

This is precisely why the partial-selling discipline exists — it makes holding the remaining position psychologically sustainable.

### The Math of Sell Rules and R

> "If You Designed Exit Rules That Lift Your Average R, You've Built Yourself A Printing Machine"
> — @LoneStockTrader

Jeff's sell rules compress losses (via 3-stop at -0.67R) while allowing winners to compound (via 10-MA trailing). The result: a 31.6% win rate produces outsized annual returns because average R on winners vastly exceeds average R on losers.

## Related Concepts

- [[3-stop-strategy]] — The mechanical implementation of Rule 3 (honor your stops)
- [[trailing-stops]] — The mechanical implementation of Rule 2 (respect the MAs)
- [[t-plus-3-framework]] — The timeline that governs when Rule 1 partials occur
- [[progressive-exposure]] — How sell rules interact with overall portfolio exposure management

## Sources

- [[sources/tweets/jfsrev-1866483247930306837|Tweet: "You do not sell everything until the market proves you wrong..."]]
- [[sources/tweets/jfsrev-1841852289742733701|Tweet: "My Systemized Approach to 3-Level Stop Exits (and Profit-Taking)..."]]
- [[sources/tweets/jfsrev-1866377222925553743|Tweet: "Never Lose Two Weeks' Gains in a Day"]]
- [[sources/tweets/jfsrev-1946774369575047638|Tweet: "But Don't Sell Too Aggressively Into Strength"]]
- [[sources/tweets/jfsrev-1649042480162295808|Tweet: "Sell Some Into Strength, Or Death By Thousand Cuts"]]
- [[sources/substacks/risk-and-position-management|Substack: Risk and Position Management by Kyna Kosling]]
