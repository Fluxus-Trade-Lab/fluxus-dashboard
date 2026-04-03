---
title: "ATR% Multiple from 50-MA"
aliases: [ATR% from 50-MA, X x ATR% from 50-MA, ATR extension]
category: "Indicators & Tools"
tags: [indicators, glossary-term]
sources:
  - "https://www.tradingview.com/script/oimVgV7e-ATR-multiple-from-50-MA/"
  - "https://x.com/jfsrev/status/1671541248044457986"
  - "https://x.com/jfsrev/status/1673515883271159809"
  - "https://x.com/jfsrev/status/1673518673318002688"
  - "https://x.com/jfsrev/status/1944301326453944377"
  - "https://x.com/denis__hamel/status/1970963942920077326"
  - "https://x.com/jfsrev/status/1971067014346310018"
related:
  - "[[atr-volatility]]"
  - "[[adr-percent]]"
  - "[[rvol]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# ATR% Multiple from 50-MA

> [!summary]
> Jeff's most popular TradingView indicator (30k+ users) measures how extended a stock's price is from its 50-day moving average, expressed in ATR% multiples. It provides an objective, volatility-adjusted framework for partial profit-taking into strength, entry avoidance on extended names, and identifying compression setups that precede continuation moves.

## Core Concept

**X x ATR% from 50-MA** quantifies how far a stock's current price has stretched from its 50-day moving average, normalized by the stock's own ATR%. This volatility adjustment is critical:

> ATR% Multiple to MA Accounts For Volatility vs % Extension From MA.

A stock trading 20% above its 50-MA might be dangerously extended if it is a low-volatility utility, but perfectly normal if it is a high-ADR% momentum name. By expressing extension in ATR% multiples, the indicator makes comparisons meaningful across securities with different volatility profiles.

**TradingView Script**: [ATR% multiple from 50-MA](https://www.tradingview.com/script/oimVgV7e-ATR-multiple-from-50-MA/)

## Profit-Taking Into Strength

> My favorite indicator for partial profit taking into strength.

Jeff uses ATR% extension levels as objective triggers for scaling out of winning positions. Rather than relying on gut feel or arbitrary percentage targets, the indicator tells him when a stock has stretched to historically significant levels relative to its own volatility -- the zone where mean reversion risk increases.

## Rules and Thresholds

- **4x ATR% from 50-MA**: Jeff's hard rule ceiling for new entries -- he will not enter a trade if extension exceeds 4x multiples
- **6-7x ATR% for indexes**: When broad market indexes reach 6-7x ATR% extension from their 50-MA, this signals stretched conditions at the index level
- **10x ATR% compression**: A stock can show 10x ATR% compression at elevated prices and continue higher without any pullback -- the compression signals the stock is absorbing selling pressure and building a new base at high levels

> 10x ATR% compression can unfold at higher prices without any pullback.

Jeff demonstrated this with $LIF, where 10x ATR% compression preceded a continuation move. After 10 weeks, the thesis played out as projected.

## Denis Hamel's 13-Year Study

In September 2025, **Denis Hamel** shared a comprehensive 13-year study (2012-2025) analyzing ATR extensions across **5,506 US stocks (~50 million stock-days)**. This large-scale empirical research validated the statistical significance of ATR% extension levels as mean-reversion signals and profit-taking zones.

## Complementary Tools

- **Will Hu's Historical ATR% Script**: [ATR% multiple history](https://www.tradingview.com/script/pAUEytKL-ATR-multiple-history/) -- useful for recalibrating entry multiples into micro meme stocks and short squeeze rallies with eccentric extensions (e.g., FFIE, OPEN, AMC, BB)
- **Cotton Dog's (f/k/a Goosifer) ATR% Band**: A projection band indicator that projects ATR% multiples forward from the current share price, useful for visualizing where future extension levels would fall

## How Jeff Applies It

- **Hard entry rule**: Will not enter if ATR% from 50-MA exceeds 4x multiples
- **Partial profit-taking**: Uses extension levels as objective scale-out triggers
- **Index situational awareness**: Monitors index-level ATR% extension (6-7x) as a caution signal; also uses extreme negative extension as an oversold signal (went long April 7th 2025 at the bottom using this)
- **Compression identification**: Watches for 10x ATR% compression at high prices as a continuation signal
- **Patience discipline**: Uses the indicator to resist chasing

> Never chase an extended trade that already moved, it will come back.

Jeff demonstrated this with MSOS: a trade that appeared extended in August 2025 pulled back and offered a proper entry in September 2025.

## Related Concepts

- [[atr-volatility]] -- ATR as the foundational volatility measure
- [[adr-percent]] -- ADR% for classifying securities by volatility
- [[rvol]] -- Volume confirmation at entry points

## Sources

- [TradingView script: ATR% multiple from 50-MA](https://www.tradingview.com/script/oimVgV7e-ATR-multiple-from-50-MA/)
- [How stock price extension can be quantified objectively](https://x.com/jfsrev/status/1671541248044457986)
- [Favorite indicator for partial profit-taking](https://x.com/jfsrev/status/1673515883271159809)
- [Advantage of ATR% extension for scaling out](https://x.com/jfsrev/status/1671543338422640641)
- [6-7x ATR% for indexes](https://x.com/jfsrev/status/1673518673318002688)
- [10x ATR% compression -- $LIF example](https://x.com/jfsrev/status/1944301326453944377)
- [$LIF after 10 weeks](https://x.com/jfsrev/status/1971841529808670905)
- [ATR% Multiple to MA vs % Extension From MA](https://x.com/jfsrev/status/1763496767579103718)
- [Denis Hamel 13-year study](https://x.com/denis__hamel/status/1970963942920077326)
- [Never chase -- MSOS example](https://x.com/jfsrev/status/1971067014346310018)
- [Will Hu's historical ATR% script](https://www.tradingview.com/script/pAUEytKL-ATR-multiple-history/)
- [Cotton Dog's projection band](https://x.com/jfsrev/status/1972225421438779724)
