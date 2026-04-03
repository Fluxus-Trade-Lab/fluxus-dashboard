---
title: "Price Alerts"
aliases: ["alerts", "TradingView alerts", "price alert ritual"]
category: "Daily Process"
tags: ["process", "price-alerts", "tradingview"]
sources: ["https://x.com/jfsrev/status/1772992258020626581", "https://x.com/jfsrev/status/1909463269863309707", "https://x.com/jfsrev/status/1912710000260313595", "https://x.com/jfsrev/status/1648153400603975680", "Complete Guide Chapters 5-6"]
related: ["pre-market-routine", "focus-list", "daily-workflow", "entry-rules"]
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# Price Alerts

> [!summary]
> Setting price alerts on TradingView is a pre-market ritual in Jeff Sun's workflow. Alerts serve two purposes: they trigger execution opportunities on Focus List names at key levels, and they provide a real-time feel of the overall market. Rather than watching screens all day, Jeff lets alerts bring the market to him, then evaluates conditions at the moment of notification.

## Core Concept

Price alerts are the connective tissue between the Focus List (prepared post-market) and live execution. Instead of monitoring every stock continuously, Jeff sets alerts at specific price levels on his Focus List names. When an alert fires, it is both a signal to evaluate a potential trade and a data point about market behavior.

> "Price alerts can give you a feel of the market."

When multiple alerts fire on the long side, it signals broad strength. When alerts stay silent or fire on the short side, the market is telling you something different. The pattern of alerts throughout the session becomes a qualitative market indicator in itself.

## Rules / Details

### Setting Alerts as a Pre-Market Ritual

Price alert setup is explicitly a **pre-market ritual** -- not an afterthought. Each morning, Jeff reviews his Focus List and sets alerts at key levels before the market opens. This ensures he is prepared to act when conditions align, without needing to watch every chart in real time.

### TradingView Alert Setup

Jeff uses TradingView for all price alerts. TradingView provides a full alert system including:
- Price crossing a specific level
- Price entering/exiting a range
- Alerts on indicator conditions
- Push notifications to mobile and desktop

TradingView offers a walkthrough of their alert system for those unfamiliar with the setup process. A TradingView Pro subscription or higher is required for a meaningful number of server-side alerts.

### What to Look For Upon Alert

When a price alert fires from a Focus List name, Jeff does not blindly execute. He evaluates the situation at that moment using his execution framework:

1. **RVOL confirmation** -- Is relative volume substantial? Price always fades outside of RVOL.
2. **LoD within 60% ATR** -- Has the low of the day already consumed too much of the stock's volatility range?
3. **ATR% from 50-MA** -- Is the stock already extended beyond 4x multiples from its 50-day moving average?
4. **Market context** -- Are other alerts confirming broad market participation, or is this name acting alone?
5. **Entry timing** -- Is it within the first 30 minutes (delay unless extreme RVOL), or past the initial noise period?

The alert is the trigger to look; the hard rules determine whether to act.

## How Jeff Applies It

Jeff's execution flow is: price alerts fire, then he uses a simple position sizing spreadsheet to calculate size, then executes via market order or buy stop order. The process is deliberately simple -- complexity is in the preparation, not the execution.

The alerts also serve a portfolio management function. For existing positions, alerts at stop levels or profit-taking zones (e.g., ATR% extension multiples from 50-MA) provide automated reminders to manage the trade without constant screen watching.

During periods of high market volatility, the frequency and pattern of alert triggers gives Jeff an immediate sense of whether the market is offering opportunity or demanding caution. This "feel" is not gut instinct -- it is a direct consequence of having systematically placed alerts on the highest-quality names in the market.

## Related Concepts

- [[pre-market-routine]] -- Alert setup is a core component of the 30-minute pre-market window
- [[focus-list]] -- Alerts are set exclusively on Focus List names at key levels
- [[entry-rules]] -- Every alert-triggered evaluation must pass the 15 hard rules before execution
- [[daily-workflow]] -- Alerts connect the post-market preparation pipeline to live market action

## Sources

- [Price alerts as pre-market ritual](https://x.com/jfsrev/status/1772992258020626581)
- [Alerts give you a feel of the market](https://x.com/jfsrev/status/1909463269863309707)
- [What to look for upon alert from Focus List](https://x.com/jfsrev/status/1912710000260313595)
- [Alerts, position sizing spreadsheet, execution](https://x.com/jfsrev/status/1648153400603975680)
- [TradingView alert introduction](https://www.tradingview.com/support/solutions/43000520149-introduction-to-tradingview-alerts/)
