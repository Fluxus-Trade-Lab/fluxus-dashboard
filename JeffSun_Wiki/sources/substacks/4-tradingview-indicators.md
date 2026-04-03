---
title: "Improve Your Market Performance with These 4 TradingView Indicators Available for Free"
author: "@jfsrev"
url: "https://jfsrev.substack.com/p/improve-your-market-performance-with"
source: "substack"
tags: [indicators, tradingview, adr, atr, rvol, pocket-pivot, esv-dashboard]
referenced_by:
  - "[[wiki/adr-percent]]"
  - "[[wiki/rvol]]"
  - "[[wiki/pocket-pivot-volume]]"
  - "[[wiki/tradingview-setup]]"
---

# Improve Your Market Performance with These 4 TradingView Indicators Available for Free

This is my standard US stock indicator setup. #Indicator

## 1. ESV Dashboard by @JohnMuchow, also provided by @DumbleDax

View quarterly earnings per share (EPS) and sales data. Optional visual icons can be shown comparing data on a Year-over-Year (YoY) and/or Quarter-on-Quarter (QoQ) basis.

Note: This indicator uses basic EPS data to calculate earnings. For relatively new issues (IPOs, etc), some platforms/tools may use diluted EPS data as a means to account for outstanding stock options, convertible preferred shares, etc. In this scenario, you will notice differences in the earnings information.

## 2. ADR% / ATR / LoD dist. Table

- **ADR%**: Average daily range (in percent)
- **ATR**: Average true range (hidden by default)
- **LoD dist.**: Distance of current price to low of the day as a percentage of ATR

I have been communicating with ArmerSchlucker over TV platform for some tweak as I felt this is a simple yet powerful tool that have plenty of potential to explore further. This is specially helpful for traders that screen for high momentum names, and seeking tight entries for high risk-reward.

> **Discussion on how I utilize LoD, ATR and ADR%:**
>
> The smaller the cap, the more violent the % move when range starts expanding. Most stocks in my watchlist have daily avg $ vol of at least 5% to their market cap.
>
> Entries are also extremely important. I refined to only take trades that can bid up BO lvl without LoD exceeding 60% ATR.
>
> The tightness of your entry makes a lot of difference to the outcome for a winning trade, but fixed loss for trades that don't work.
>
> Example: Trader A buying TSLA on 1st Jan at $100 with fixed risk of $500 may not necessarily make more (R multiples) than Trader B buying TSLA at $120 with the same fixed $ risk, on a later date and higher price.
>
> This is how I trade — I'm looking to size at the lucrative entry.
>
> Q: What percent of your entries are pre/post market?
> A: 0. Back to your question, yes bid/ask spread is top of my consideration largely because u already lose some sort of edge at entry and eventual exit (bigger loss or lesser profit)

## 3. MarketSmith Setup in TradingView

[@DumbleDax](https://x.com/DumbleDax) (also IBD RS Rating), and [@amphtrading](https://x.com/amphtrading)

Over 100+ hours spent coding every indicators to save your $150/month. 2 different versions below:

- @DumbleDax version: [YouTube](https://youtube.com/watch?v=XKyfIvSUgpQ&list=PL_sevQJe2aDN3irUl-qLwD69d9TwwL-EW&index=17&t=247s)
- @amphtrading version: [YouTube](https://youtube.com/watch?v=92QStI_Gda4)

## 4. Pocket Pivot Volume

[@finallynitin](https://x.com/finallynitin), and also [@TraderLion_](https://x.com/TraderLion_)

@finallynitin version: search for 'Simple Volume with Pocket Pivots'

> Explanation: [https://x.com/finallynitin/status/1516415566936182793](https://x.com/finallynitin/status/1516415566936182793)

@TraderLion_ version carries more features. TraderLion's Enhanced Volume features:
1. **High Relative Volume Bars**: Highlight high relative volume bars with a high closing range lime green
2. **Low Relative Volume Bars**: Labels low relative volume days with a down arrow
3. **Volume Labels**: High volume days show total shares traded and percent above average
4. **Highest Volume in Over a Year**: Look for "HV" on top of the volume bar
5. **Simple Moving Average**: SMA overlay on volume without taking up indicator slots
6. **High Relative Volume Alerts**: Set alerts when volume surpasses threshold

## Additional Update

[https://x.com/jfsrev/status/1650352348848607232](https://x.com/jfsrev/status/1650352348848607232)

@DumbleDax have upgraded the existing ADR% tool for me, and after making some minor adjustments, I have decided to publish and share the script on @tradingview as open source.

The data includes:
1. **Market Capitalization** — total value of outstanding shares
2. **Float %** — percentage of shares available for open market trading (lower float = more volatility)
3. **ADR%** — average daily price movement as percentage of current price (higher = more volatile)
4. **ATR** — average true range over specified period
5. **LoD dist.** — Low of Day distance as range level gauge based on ATR
   - Example: LoD dist. = 104%: Current price $24.49, Low $22.16, Diff $2.33, ATR $2.25, LoD dist = $2.33/$2.25 = 104%
6. **Average Daily $ Volume** — average money traded per day
7. **Average Daily Volume** — average shares traded per day
8. **Projected Volume** — estimated total volume for the day based on current run rate
9. **Relative Volume** — current volume vs average, expressed as percentage

Script: [Swing Data - ADR% / RVol / PVol / Float % / Avg $ Vol](https://www.tradingview.com/script/uloAa2EI-Swing-Data-ADR-RVol-PVol-Float-Avg-Vol/)

## LATEST Update 7/2024 (start from here)

[https://x.com/jfsrev/status/1818297619338395847](https://x.com/jfsrev/status/1818297619338395847)
