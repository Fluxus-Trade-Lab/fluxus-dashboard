---
title: "ETF and Mega Cap Liquid Screeners"
aliases: ["etf screener", "liquid etf screener", "mega cap watchlist", "leveraged etf list"]
category: "Screeners"
tags: ["screeners", "etf", "leveraged-etf"]
sources: ["https://x.com/jfsrev/status/1866039252477444166", "https://x.com/jfsrev/status/1757662271994835388", "https://x.com/jfsrev/status/1962458102709837975", "https://x.com/jfsrev/status/1962094789068996858", "https://x.com/jfsrev/status/1960873535687286891", "https://x.com/jfsrev/status/1966505551040225362", "Complete Guide Chapter 3-4"]
related: ["screener-overview", "high-adr-screener", "focus-list", "atr-volatility"]
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# ETF and Mega Cap Liquid Screeners

> [!summary]
> Jeff's Liquid ETF screener and fixed Mega Cap watchlist extend his universe beyond US equities into non-correlated asset classes. Available on both TradingView and Finviz, these screens incorporate leveraged ETFs for higher ADR% opportunities and use a "screen within screen" technique for efficient monitoring. Key nuances apply to futures-tracking and crypto ETFs.

## Core Concept

> "Exploring ideas in tradable asset classes beyond correlated equities can provide a valuable edge." -- Stanley Druckenmiller

Jeff trades outside of US-listed equities regularly. The Liquid ETF screener identifies tradable ETFs across commodities, currencies, fixed income, international markets, and crypto. Diversifying into non-correlated assets helps manage portfolio correlation risk, especially when equity markets are range-bound or in correction.

> "Quallamaggie will always choose the leveraged ETF of the underlying securities, if available, for its higher ADR%."

## Rules / Details

### Liquid ETF Screener

**TradingView Version**: Screens liquid ETFs with sufficient average dollar volume for swing trading. Updated in 2025 with refined criteria.

**Finviz Version (2025)**: Parallel Finviz implementation capturing the same ETF universe with Finviz-specific filters.

Both versions filter for liquidity (average dollar volume), ADR%, and relative strength characteristics. The goal is to surface ETFs exhibiting trending behavior that can be traded with the same swing methodology applied to individual stocks.

### Screen Within Screen (Watchlist)

The TradingView "screen within screen" technique applies screener filters to an existing watchlist rather than the full market universe. This allows Jeff to run his standard screener criteria (ADR%, volume, momentum) against a curated ETF watchlist, rapidly identifying which ETFs within his universe are currently actionable.

### Mega Cap Liquid Watchlist

Jeff maintains a **fixed watchlist of Liquid Mega Cap names exceeding $1B average dollar volume on a constant basis**. For each name, he lists the corresponding synthetic leveraged ETFs to provide higher ADR% opportunities.

> "Here is where I get my full leveraged ETF list, and update them on monthly basis."

To identify opportunities within this list, Jeff applies the same relative strength and technical criteria used for individual stocks, looking for VCP-like setups, breakout levels, and volume confirmation within the mega cap universe. An example is his short on AMZN executed via the leveraged inverse ETF AMZD.

### Nuances for Futures-Tracking ETFs

> "Key nuances when trading US listed ETFs that track futures with 24-hour underlying markets."

ETFs that track continuously traded futures require special attention because their underlying assets trade outside US market hours:

- **GLD** (tracks XAUUSD gold futures)
- **SPXL** (tracks ES S&P 500 futures)
- **IBIT** (tracks BTCUSD bitcoin)
- **SOLT** (tracks SOLUSD solana)
- **BOIL** (tracks natural gas futures)
- **FXI** (tracks China A50)
- **UCO** (tracks WTI crude oil)

The 24-hour underlying market means these ETFs can gap significantly at the US open based on overnight moves in the underlying. Entry and stop placement must account for this gap risk.

### Crypto ETFs on Fridays

> "Another caveat on executing US listed crypto ETFs on Friday session."

Crypto ETFs like IBIT present an additional risk on Fridays: crypto markets trade 24/7 through the weekend, but the ETF is closed Saturday and Sunday. A Friday entry carries two full days of unhedgeable gap risk from weekend crypto price movement. Jeff flags this as a specific execution caveat.

## How Jeff Applies It

The ETF screener runs daily alongside the equity screeners during post-market analysis. The mega cap liquid watchlist is a fixed reference list updated monthly for leveraged ETF additions. Jeff uses the screen-within-screen technique on TradingView to quickly filter this list for actionable setups.

Diversifying correlation risk with lower-beta ETF ideas is an explicit part of Jeff's portfolio construction, particularly during volatile equity environments.

## Related Concepts

- [[screener-overview]] -- Full list of all 14 post-market screeners
- [[high-adr-screener]] -- ADR% philosophy applies equally to ETFs
- [[focus-list]] -- How ETF ideas are promoted to actionable trades
- [[atr-volatility]] -- ADR% and ATR understanding for position sizing

## Sources

- [Druckenmiller quote on non-correlated assets](https://x.com/jfsrev/status/1866039252477444166)
- [Liquid ETF TradingView Version](https://x.com/jfsrev/status/1757662271994835388)
- [Liquid ETF Finviz Version 2025](https://x.com/jfsrev/status/1962458102709837975)
- [Liquid ETF TradingView Version 2025](https://x.com/jfsrev/status/1962458397380632874)
- [Screen within Screen](https://x.com/jfsrev/status/1770337966814363698)
- [Mega Cap Liquid watchlist with leveraged ETFs](https://x.com/jfsrev/status/1962094789068996858)
- [How to identify opportunities within the list](https://x.com/jfsrev/status/1912034116465545492)
- [Futures-tracking ETF nuances](https://x.com/jfsrev/status/1960873535687286891)
- [Crypto ETF Friday caveat](https://x.com/jfsrev/status/1966505551040225362)
- [Full leveraged ETF list source](https://x.com/jfsrev/status/1986252984481960281)
- Complete Guide, Chapters 3-4
