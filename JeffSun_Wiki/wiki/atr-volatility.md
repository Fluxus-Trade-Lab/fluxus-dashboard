---
title: "ATR (Average True Range)"
aliases: [ATR, Average True Range]
category: "Indicators & Tools"
tags: [indicators, glossary-term]
sources:
  - "https://www.tradingview.com/support/solutions/43000734653-how-are-adr-and-atr-calculated/"
  - "https://x.com/jfsrev/status/1788583106418541011"
  - "https://x.com/jfsrev/status/1788135099273281737"
  - "https://x.com/jfsrev/status/1648131096901726209"
related:
  - "[[adr-percent]]"
  - "[[atr-extension-from-50ma]]"
  - "[[rvol]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# ATR (Average True Range)

> [!summary]
> ATR measures the average true range of a security over a specified period, capturing gaps and intraday extremes that the simpler ADR misses. Jeff uses ATR as a core unit of risk measurement -- defining stop placement, entry tightness, and position sizing around it.

## Core Concept

**Average True Range (ATR)** calculates the average of the "true range" over N periods. The true range for any given day is the greatest of:

1. Current high minus current low
2. Absolute value of current high minus previous close
3. Absolute value of current low minus previous close

This differs from **ADR (Average Daily Range)**, which only measures the average of high-minus-low without accounting for overnight gaps. TradingView provides a detailed breakdown of [how ATR and ADR are calculated and how they differ](https://www.tradingview.com/support/solutions/43000734653-how-are-adr-and-atr-calculated/).

## The Spring Coil Metaphor

Jeff visualizes ATR as a **spring coil** when evaluating entries. A stock that has not yet stretched its daily range (i.e., the Low of Day distance is small relative to ATR) still has coiled energy -- potential to move further in either direction within the session.

> Hard rule: I do not enter trade if LoD already exceeds 60% ATR.

When LoD distance is already large relative to ATR, the spring has already uncoiled -- the favorable risk/reward window for entry has passed.

## ATR in Stop Placement

ATR is the foundational unit behind Jeff's **3-stop strategy**, where stops are calibrated to keep R-loss within -0.67R per trade:

- **LoD dist.** in Jeff's Swing Data indicator displays the current price distance from the Low of Day as a percentage of ATR (e.g., LoD dist. = 104% means price is 1.04x ATR above the day's low)
- Entries are only taken when the LoD distance remains below 60% ATR -- ensuring tight risk
- The tighter the entry relative to ATR, the larger the position size for the same dollar risk

> The tightness of your entry makes a lot of difference to the outcome for a winning trade, but fixed loss for trades that don't work.

## ATR% from 50-MA

ATR is also used in Jeff's most popular indicator -- **ATR% multiple from 50-MA** (30k+ TradingView users) -- which measures how extended a stock's price is from its 50-day moving average, expressed in ATR% multiples. This concept is covered in detail in [[atr-extension-from-50ma]].

## How Jeff Applies It

- **Entry filter**: Will not enter if LoD exceeds 60% ATR at the time of execution
- **Position sizing**: Tighter ATR-based entries allow larger position sizes for the same fixed dollar risk
- **Competition edge**: Jeff kicked off USIC 2023 in 2nd place by targeting small caps with high volume turnover and entries where LoD did not exceed 60% ATR
- **Trade management**: ATR defines the risk unit (R) that all subsequent stop adjustments and profit targets reference

> This is why you should trade tight.

## Related Concepts

- [[adr-percent]] -- ADR% as a complementary volatility measure
- [[atr-extension-from-50ma]] -- ATR% multiple extension from the 50-MA
- [[rvol]] -- Volume confirmation at entry

## Sources

- [How are ADR and ATR calculated? (TradingView)](https://www.tradingview.com/support/solutions/43000734653-how-are-adr-and-atr-calculated/)
- [Visualizing ATR as Spring Coil -- LoD 60% ATR rule](https://x.com/jfsrev/status/1788583106418541011)
- [Perks of <60% LoD Execution](https://x.com/jfsrev/status/1788135099273281737)
- [This is why you should trade tight](https://x.com/jfsrev/status/1648131096901726209)
- [USIC 2023 entry methodology](https://x.com/jfsrev/status/1628559711917473793)
