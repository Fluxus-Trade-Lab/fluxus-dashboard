---
title: "ADR% (Average Daily Range Percentage)"
aliases: [ADR%, Average Daily Range]
category: "Indicators & Tools"
tags: [indicators, glossary-term]
sources:
  - "https://x.com/jfsrev/status/1852994791795282188"
  - "https://x.com/jfsrev/status/1856232860107350147"
  - "https://x.com/jfsrev/status/1939966489475547529"
  - "https://x.com/jfsrev/status/1970761700472430903"
  - "https://x.com/jfsrev/status/1986252984481960281"
related:
  - "[[atr-volatility]]"
  - "[[atr-extension-from-50ma]]"
  - "[[rvol]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# ADR% (Average Daily Range Percentage)

> [!summary]
> ADR% expresses the average daily price range as a percentage of the current price. Jeff uses it to classify securities by volatility behavior, determine position sizing, and decide capital allocation. Higher ADR% securities allow for tighter percentage-based risk and larger R-multiples on winners.

## Core Concept

**ADR%** = (Average Daily Range / Current Price) x 100

Where the Average Daily Range is simply the average of (High - Low) over a specified number of sessions. Unlike ATR, ADR does not account for overnight gaps -- it measures only intraday range. ADR% normalizes this range as a percentage of price, making it comparable across stocks at different price levels.

ADR% is displayed in Jeff's **Swing Data** indicator ([TradingView script, 60k+ users](https://www.tradingview.com/v/uloAa2EI/)), alongside RVOL, Projected Volume, Float %, and Average $ Volume.

## Trend-Following vs. Range-Expansive Behavior

Jeff distinguishes between two types of ADR% behavior:

- **Trend-following securities**: Lower ADR% stocks that grind higher over time with controlled daily ranges
- **Range-expansive securities**: Higher ADR% stocks that move in violent bursts, offering larger intraday and swing opportunities

Understanding which behavior a security exhibits is critical for setting realistic expectations on hold time and target multiples.

## Position Sizing Benefits of High ADR%

High ADR% securities offer a structural advantage for position sizing:

> The smaller the cap, the more violent the % move when range starts expanding. Most stocks in my watchlist have daily avg $ vol of at least 5% to their market cap.

With a fixed dollar risk per trade, a high ADR% stock requires a smaller position size (fewer shares) to reach the same stop distance -- but the potential R-multiple on the upside is magnified because the stock can cover more percentage ground per day.

## Capital Allocation by ADR% Level

Jeff provides ballpark estimates of the percentage of capital allocation needed for executing securities based on different ADR% levels. Lower ADR% names require proportionally more capital to achieve meaningful R returns, while higher ADR% names can generate outsized returns with smaller capital allocation.

## Leveraged ETFs for Higher ADR%

> Qullamaggie will always choose the leveraged ETF of the underlying securities, if available, for its higher ADR%.

When trading liquid mega-cap names or broad market themes, Jeff (following Qullamaggie's approach) prefers the leveraged ETF version for its amplified ADR%. For example, rather than trading the underlying index or commodity ETF, trading its 2x or 3x leveraged counterpart provides greater daily range for the same chart setup.

Jeff maintains and updates a [full leveraged ETF list on a monthly basis](https://x.com/jfsrev/status/1986252984481960281).

## How Jeff Applies It

- **Screening**: ADR% is a key filter in his "High ADR% Hottest Stock" screener
- **Position sizing**: ADR% level determines how much capital to allocate per trade
- **Trade selection**: Prefers high ADR% names for swing trading -- they offer better R potential
- **ETF substitution**: Uses leveraged ETFs to synthetically increase ADR% on liquid underlyings
- **Watchlist criteria**: Most watchlist stocks have daily average dollar volume of at least 5% relative to market cap

## Related Concepts

- [[atr-volatility]] -- ATR as the true range measure including gaps
- [[atr-extension-from-50ma]] -- Extension measurement using ATR% multiples
- [[rvol]] -- Volume confirmation for high-ADR% entries

## Sources

- [ADR%: Trend-Following vs. Range-Expansive Behavior](https://x.com/jfsrev/status/1852994791795282188)
- [Benefits of High ADR% Securities Relative to Position Sizing](https://x.com/jfsrev/status/1856232860107350147)
- [Capital allocation by ADR% level](https://x.com/jfsrev/status/1939966489475547529)
- [Qullamaggie leveraged ETF preference for higher ADR%](https://x.com/jfsrev/status/1970761700472430903)
- [Full leveraged ETF list source](https://x.com/jfsrev/status/1986252984481960281)
- [Swing Data TradingView script](https://www.tradingview.com/v/uloAa2EI/)
