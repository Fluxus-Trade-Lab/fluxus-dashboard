# Demon Finder — Design Doc

**Date:** 2026-04-21

## Problem
No automated way to detect behavioral trading mistakes in context. Existing analytics show aggregate stats (win rate, R-multiple) but don't answer: "Am I trading poorly because of my behavior, and when should I stop?"

## Solution
A new "Demon Finder" sub-tab under AI Coach → Analytics that tags each trade with behavioral demons, tracks streaks, and triggers a circuit breaker when a demon fires 6 times in a row.

## Account Rules (configurable, persisted)

- Starting capital: $1,000,000
- Risk per trade: 0.25% ($2,500)
- Buffer: 0.25%
- Min R/R at entry: 3:1
- Overtrading threshold: 8 entries per 5 trading days
- Sizing tolerance: 60%-140% of target risk
- Circuit breaker streak: 6

Stored in localStorage + synced to Google Sheets via meta payload.

## Seven Demons

| # | Demon | Detection | Data Source |
|---|-------|-----------|-------------|
| 1 | Bad Environment | Entry when SPY signal = WARNING or RISK_OFF | dailyPrices → reconstruct Power 3 |
| 2 | Fighting the Trend | Long when SPY < 21EMA, short when SPY > 21EMA | dailyPrices → compute EMA |
| 3 | Overtrading | >8 new entries in rolling 5-day window | trade entry dates |
| 4 | Poor R/R | Entry R/R < 3:1 (entryPrice to stopPrice distance vs target) | entryPrice, stopPrice |
| 5 | Bet Too Big | Position risk > 140% of 0.25% target (>0.35%) | qty × (entry - stop) / capital |
| 6 | Bet Too Small | Position risk < 60% of 0.25% target (<0.15%) | same |
| 7 | Not In Plan | Ticker not on screener/watchlist at entry time | future — placeholder, always false for now |

## Circuit Breaker
If any single demon fires on 6 consecutive trades, surface a hard warning banner:
"STOP — [Demon] triggered 6 times in a row. Review these trades before taking new entries."

## Market Signal Reconstruction

`reconstructSignal(date, dailyPrices)` computes SPY's Power 3 signal for any historical date:
- Collects 200+ days of SPY prices up to `date`
- Computes EMA8, EMA21, SMA50, SMA200
- Returns signal (POWER_3 / CAUTION / WARNING / RISK_OFF)

Pure function, no API calls. ~700 lookups for 141 trades — sub-millisecond.

## UI Layout

### Top: Circuit Breaker Banner
- Red banner, only visible when a 6-streak is active
- Names the demon + links to the offending trades

### Middle: Demon Scorecard
- 7 cards in a grid
- Each: fire count (last 30 trades), fire rate %, current streak, longest streak
- Amber border at 3-streak, red at 6-streak
- Click to filter trade list

### Bottom: Trade List with Demon Tags
- Chronological, most recent first
- Each row: ticker, date, direction, R/R, P/L result, demon badges (colored pills)
- Clean trades get a checkmark
- Filterable by demon (click scorecard) or "clean only" / "flagged only"

## Overlap with Existing Features

- Reuses `enrichTrades()`, `lookupPrice()`, `computePortfolioHeat()` from existing libs
- No duplication: Summary = aggregate stats, Demon Finder = per-trade behavioral tagging
- Monthly Review = narrative reflection, Demon Finder = real-time circuit breaker

## New Files
- `frontend/src/components/portfolio/lib/demonFinder.js` — detection logic (~200 lines)
- `frontend/src/components/journal/analytics/DemonFinderSection.jsx` — UI (~300 lines)
- `frontend/src/components/journal/analytics/DemonRulesConfig.jsx` — rules panel (~100 lines)

## Modified Files
- `frontend/src/components/journal/AnalyticsTab.jsx` — add sub-tab
- `frontend/src/components/portfolio/context/PortfolioContext.jsx` — add demonRules to state/sync
