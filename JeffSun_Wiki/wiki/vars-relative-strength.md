---
title: "VARS (Volatility Adjusted Relative Strength)"
aliases: [VARS, Volatility Adjusted Relative Strength, VARW]
category: "Indicators & Tools"
tags: [indicators, glossary-term]
sources:
  - "https://x.com/jfsrev/status/1909486454260351162"
  - "https://www.reddit.com/r/RealDayTrading/comments/1ej6niy/volatility_adjusted_rs_indicator/"
  - "https://x.com/jfsrev/status/1956894936185614378"
  - "https://x.com/jfsrev/status/1976121442086564329"
  - "https://x.com/jfsrev/status/1649338005302415360"
related:
  - "[[adr-percent]]"
  - "[[rvol]]"
  - "[[atr-volatility]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# VARS (Volatility Adjusted Relative Strength)

> [!summary]
> VARS enhances traditional Relative Strength by factoring in the unique volatility of each security. Jeff developed his own TradingView script with a histogram option, inspired by a 2023 reddit thread by mattishenner. VARW (Volatility Adjusted Relative Weakness) is its inverse counterpart for short setups.

## Core Concept

Traditional Relative Strength (RS) compares a stock's price performance against a benchmark (typically the S&P 500). The limitation is that it treats all percentage moves equally, regardless of the underlying volatility profile of the stock.

**VARS** adjusts for this by factoring in each security's unique volatility. A 3% move in a low-volatility utility stock is far more significant than a 3% move in a high-volatility small-cap biotech. By normalizing relative strength against volatility, VARS provides a more accurate signal of genuine outperformance.

**VARW** (Volatility Adjusted Relative Weakness) applies the same concept in reverse, identifying securities showing unusual weakness relative to their normal volatility profile.

## Origin

> It began as an idea to enhance the accuracy of traditional RS by factoring volatility that is unique to each different stock/securities, until I found a [2023 reddit thread](https://www.reddit.com/r/RealDayTrading/comments/1ej6niy/volatility_adjusted_rs_indicator/) with similar discussion by Matt.

Jeff discovered a 2023 reddit thread by **mattishenner** on r/RealDayTrading that explored a similar concept of volatility-adjusted relative strength. This validated the approach and informed the development of his published indicator.

## Jeff's VARS Settings

Jeff published his [VARS settings for swing trading](https://x.com/jfsrev/status/1956894936185614378), calibrated for the timeframes and hold periods he typically trades. The indicator settings are optimized for identifying stocks with genuine relative strength (not just high-beta noise) against the benchmark.

## Published TradingView Script

In October 2025, Jeff published his own VARS indicator with a histogram visualization option:

**[Volatility Adjusted Relative Strength (VARS) - Histogram Option](https://www.tradingview.com/script/nbgyYwu1-Volatility-Adjusted-Relative-Strength-VARS-Histogram-Option/)**

The histogram format makes it easier to visually identify inflection points where relative strength is accelerating or decelerating.

## IBD RS Alternative

For traders who prefer a more traditional approach:

> If you want traditional Relative Strength line similar to IBD with RS Rating, I highly recommend this by Fred6724. He have customized the full MarketSmith model on Tradingview and it's available for free.

**Fred6724** ([@DumbleDax](https://x.com/DumbleDax)) has built a comprehensive free MarketSmith-style RS indicator on TradingView, including IBD-style RS Rating. Jeff recommends this as the "old school" alternative for traders who want the classic IBD methodology.

## How Jeff Applies It

- **Focus List priority**: Relative Strength first, setup second -- VARS helps identify genuine leaders
- **Entry qualification**: A stock must show VARS strength before being upgraded from watchlist to focus list
- **Short ideas**: VARW identifies relative weakness candidates for inverse ETF trades
- **Histogram reading**: Acceleration in the VARS histogram signals strengthening leadership; deceleration warns of fading momentum

> My Rule: Relative Strength First, Setup Second.

## Related Concepts

- [[adr-percent]] -- ADR% provides the volatility context VARS adjusts for
- [[rvol]] -- Volume confirmation layered on top of VARS signals
- [[atr-volatility]] -- ATR as the volatility input for adjustment

## Sources

- [VARS concept: enhancing traditional RS with volatility adjustment](https://x.com/jfsrev/status/1909486454260351162)
- [mattishenner reddit thread (2023)](https://www.reddit.com/r/RealDayTrading/comments/1ej6niy/volatility_adjusted_rs_indicator/)
- [Jeff's VARS settings for swing trading](https://x.com/jfsrev/status/1956894936185614378)
- [Published VARS with histogram (October 2025)](https://x.com/jfsrev/status/1976121442086564329)
- [TradingView script](https://www.tradingview.com/script/nbgyYwu1-Volatility-Adjusted-Relative-Strength-VARS-Histogram-Option/)
- [IBD RS by Fred6724 (@DumbleDax)](https://x.com/jfsrev/status/1649338005302415360)
