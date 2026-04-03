---
title: "Live-Market RVOL Screeners"
aliases: ["live market screeners", "rvol screeners", "pre-market gapper screener", "focus list screener"]
category: "Screeners"
tags: ["screeners", "rvol", "live-market", "tradingview"]
sources: ["https://x.com/jfsrev/status/1801498691746021731", "https://x.com/jfsrev/status/1810643031592497162", "https://x.com/jfsrev/status/1798726526961405954", "https://x.com/jfsrev/status/1946214673482969302", "https://x.com/jfsrev/status/1808502472606134494", "Complete Guide Chapter 3"]
related: ["screener-overview", "entry-rules", "focus-list"]
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# Live-Market RVOL Screeners

> [!summary]
> Jeff runs 2 live-market screeners on TradingView during trading hours, both centered on RVOL (Relative Volume). The Focus List Based screener monitors his curated watchlist for volume surges. The Pre-market Gapper Based screener catches names gapping up on high pre-market volume. Together they provide real-time execution signals during the trading session.

## Core Concept

While Jeff's 14 post-market screeners build the watchlist, the 2 live-market screeners serve a fundamentally different purpose: they provide **real-time execution signals** based on RVOL. Relative volume -- the current session's volume run-rate compared to the 50-day average -- is Jeff's primary confirmation tool for entry.

> "RVOL based entry on ORH have proven statistical edge in the market."

> "RVOL based entry rules have saved me from countless unnecessary stop losses year after year."

High RVOL at the open signals strong buying interest and serves as the first proof of institutional participation. Without volume confirmation, even the best-screened setup remains a watchlist idea rather than an actionable trade.

## Rules / Details

### 1. Focus List Based RVOL Screener

This screener monitors Jeff's curated Focus List (the output of his post-market process) for real-time RVOL spikes during the trading session. It applies RVOL thresholds to stocks already vetted through the full screening -> watchlist -> focus list pipeline.

The advantage of this approach is that every name surfaced has already passed fundamental, technical, and relative strength filters. The RVOL signal is the final confirmation trigger for execution.

### 2. Pre-Market Gapper Based RVOL Screener

This screener targets stocks gapping up on elevated pre-market volume, regardless of whether they appear on the Focus List. It captures catalyst-driven moves (earnings, news, sector rotation) that may not have been anticipated during post-market analysis.

Pre-market gappers with high RVOL into the open are evaluated for the same entry criteria (LoD < 60% ATR, extension from 50-MA < 4x, etc.) before execution.

### 2025 Relocation Update

> "This is 2025 update to relocation of screener based on our feedback in 2024."

In 2025, Jeff relocated the screener panel placement within TradingView based on community feedback from 2024. The updated layout optimizes the screen real estate for monitoring multiple names simultaneously alongside the primary chart.

## Mainframe Setup

Jeff's mainframe for live market trading integrates the RVOL screeners directly into his multi-monitor TradingView workspace. The setup provides:

- Primary chart with indicators (Swing Data, ATR% from 50-MA, VARS, Volume with Pocket Pivots)
- Live RVOL screener panel showing real-time volume run-rates
- Focus List watchlist for quick chart switching
- Pre-market gapper list for morning catalysts

This configuration allows Jeff to see RVOL alerts across his full universe while maintaining detailed chart analysis on the primary screen.

## The KOSS Example

> "An example of High RVOL I am seeking at open, KOSS on 3rd July 2024."

KOSS on July 3, 2024 demonstrated the type of high RVOL signal Jeff's live screeners are designed to catch. The stock showed an extreme volume run-rate at the open, flagging it immediately on the screener. This kind of RVOL spike -- multiples above the 50-day average within the first minutes of trading -- is the precise signal that triggers Jeff's execution process.

## How Jeff Applies It

The two live screeners complement each other: the Focus List screener ensures prepared ideas are not missed when they trigger, while the Pre-market Gapper screener captures unexpected opportunities. Jeff monitors both panels simultaneously on his mainframe during market hours.

When a name appears on the RVOL screener with sufficient volume confirmation, Jeff evaluates it against his 15 hard entry rules before executing. The RVOL signal alone is necessary but not sufficient -- it must combine with favorable price action, acceptable LoD-to-ATR ratio, and manageable extension from the 50-MA.

## Related Concepts

- [[screener-overview]] -- Full list of all 16 screeners (14 post-market + 2 live)
- [[entry-rules]] -- The 15 hard rules applied after RVOL confirmation
- [[focus-list]] -- How the Focus List feeds the live screener

## Sources

- [Focus List Based RVOL screener](https://x.com/jfsrev/status/1801498691746021731)
- [Pre-market Gapper Based RVOL screener](https://x.com/jfsrev/status/1810643031592497162)
- [2025 relocation update](https://x.com/jfsrev/status/1798726526961405954)
- [Mainframe setup for live market trading](https://x.com/jfsrev/status/1946214673482969302)
- [KOSS RVOL example, 3rd July 2024](https://x.com/jfsrev/status/1808502472606134494)
- [Using RVOL for entry confirmation](https://x.com/jfsrev/status/1946777562648383700)
- [RVOL based entry statistical edge](https://x.com/jfsrev/status/1809139555041518052)
- Complete Guide, Chapter 3
