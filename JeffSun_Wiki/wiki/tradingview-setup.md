---
title: "TradingView Setup"
aliases: [TradingView, charting setup, Jeff's indicators, TV setup]
category: "Resources"
tags: [resources, tradingview, indicators, setup]
sources:
  - "[[sources/notion/complete-guide-snapshot]]"
related:
  - "[[free-tools]]"
  - "[[screener-overview]]"
  - "[[adr-percent]]"
  - "[[rvol]]"
  - "[[vars-relative-strength]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# TradingView Setup

> [!summary]
> Jeff uses TradingView as his primary charting platform and has evolved his template across three versions (2023, 2024, 2025). He relies on 5 key indicator scripts — Swing Data (60k+ users), ATR% from 50-MA (30k+ users), VARS Histogram, Simple Volume with Pocket Pivots, and several worthy mentions — with a nostalgic nod to the 2000s-era tools he started with.

## Core Concept

Jeff's charting setup is built on free, publicly available TradingView scripts. He does not use proprietary or paid indicators. His template has evolved over three years, with each version refining the layout while maintaining the same core indicators.

## Templates

### Version History

1. **2023 Version** [[sources/tweets/jfsrev-1649333754215948290]] — Original template shared publicly
2. **2024 Version** [[sources/tweets/jfsrev-1818297619338395847]] — Refined layout and updated configurations
3. **2025 Version** — Free indicators that have remained consistent pillars, with direct TradingView script links

Jeff also demonstrated his setup on mobile [[sources/tweets/jfsrev-1744564021565767816]], showing that the core indicators work across devices.

## The 5 Indicator Scripts

### 1. Swing Data — ADR% / RVol / PVol / Float % / Avg $ Vol

**[TradingView Link](https://www.tradingview.com/v/uloAa2EI/) — Over 60,000 users**

Jeff's most popular indicator, providing a consolidated view of the key data points he checks on every chart. Understanding each component:

- **ADR%**: Examining trend-following vs. range-expansive behavior [[sources/tweets/jfsrev-1852994791795282188]]. Higher ADR% securities require less capital allocation for the same R-risk [[sources/tweets/jfsrev-1856232860107350147]]. See [[adr-percent]].
- **RVOL**: Relative volume for entry confirmation. RVOL-based entries have proven statistical edge [[sources/tweets/jfsrev-1809139555041518052]]. See [[rvol]].
- **Average $ Volume**: Slippage and widened spreads at execution cost Jeff 6-7% of his 2021 total equity [[sources/tweets/jfsrev-1591446897100824577]].
- **Low Float %**: The best percentage performers almost always have specific market cap, low float, and short float characteristics [[sources/tweets/jfsrev-1944595506853970049]].

### 2. ATR% Multiple from 50-MA

**[TradingView Link](https://www.tradingview.com/script/oimVgV7e-ATR-multiple-from-50-MA/) — Over 30,000 users**

Jeff's tool for quantifying price extension objectively:

> "How can stock price extension be quantified objectively?" [[sources/tweets/jfsrev-1671541248044457986]]

Used for partial profit-taking (his favorite indicator for this purpose [[sources/tweets/jfsrev-1673515883271159809]]), entry avoidance when overextended, and index-level situational awareness. Employs 6-7x ATR% for indexes [[sources/tweets/jfsrev-1673518673318002688]].

A 13-year study (2012-2025) across 5,506 US stocks (~50M stock-days) by Denis Hamel validated the concept [[sources/tweets/denis__hamel-1970963942920077326]].

### 3. Volatility Adjusted Relative Strength (VARS) Histogram

**[TradingView Link](https://www.tradingview.com/script/nbgyYwu1-Volatility-Adjusted-Relative-Strength-VARS-Histogram-Option/)**

Jeff's enhancement to traditional relative strength, factoring in volatility unique to each security:

> "It began as an idea to enhance the accuracy of traditional RS by factoring volatility that is unique to each different stock/securities." [[sources/tweets/jfsrev-1909486454260351162]]

Inspired by a 2023 Reddit thread by mattishenner. Jeff published his VARS with histogram in October 2025 [[sources/tweets/jfsrev-1976121442086564329]]. See [[vars-relative-strength]].

For traditional RS, Jeff recommends IBD RS Indicator by @Fred6724 [[sources/tweets/jfsrev-1649338005302415360]].

### 4. Simple Volume with Pocket Pivots — by @finallynitin

**[TradingView Link](https://www.tradingview.com/script/JkB0iCFp-Simple-Volume-with-Pocket-Pivots/)**

> "I've tried many great free volume scripts on TradingView, but this one is simple and has everything I need."

Key volume principles:
- A single day of strong price move with heightened volume can reshape the narrative of three months of price action [[sources/tweets/jfsrev-1959451625145434489]]
- Use Projected Volume with a 50% haircut to define high RVOL [[sources/tweets/jfsrev-1950202147787977058]]

### 5. Worthy Mentions

Applied on a separate template, not the main daily one:

- **EPS & Sales** by @Fred6724 — [TradingView](https://www.tradingview.com/script/WiaFmLGR/)
- **Industry Group Strength** by @amphtrading — [TradingView](https://www.tradingview.com/script/5NsvcOVp-Industry-Group-Strength/), with Jeff's usage discussion [[sources/tweets/jfsrev-1845744867047354535]]
- **Best 8 Free TradingView Public Scripts (2024)** [[sources/tweets/jfsrev-1858822375015661742]]
- **TradingView Seasonality Table (2025)** [[sources/tweets/jfsrev-1971824458341274083]]

## The 2000s Nostalgia

> "On a fun note, I relied on something like this back in 2000s" [[sources/tweets/jfsrev-1858842565296222636]]

Jeff shared a glimpse of the charting tools he used when he started trading — a far cry from modern TradingView, and a reminder of how far freely available tools have come.

## Related Concepts

- [[free-tools]] — The broader ecosystem of free tools Jeff uses
- [[screener-overview]] — TradingView screeners that complement the charting setup
- [[adr-percent]] — Deep dive into ADR% from the Swing Data indicator
- [[rvol]] — Deep dive into RVOL concepts
- [[vars-relative-strength]] — Deep dive into VARS methodology

## Sources

- Chapter 2: Charting — I use TradingView [[sources/notion/complete-guide-snapshot]]
