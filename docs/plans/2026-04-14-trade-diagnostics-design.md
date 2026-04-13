# Trade Diagnostics — AI Coach Analytics Tab Upgrade

**Date:** 2026-04-14
**Status:** Design approved, pending implementation

## Overview

Upgrade the existing Analytics tab in the AI Coach page (`#/journal`) from basic summary stats to a full trade diagnostics dashboard. Four sub-tabs provide risk management, volatility analysis, and trim/stop optimization — all computed client-side from existing portfolio data.

**Primary goals (in priority order):**
1. Control portfolio volatility and open risk (high-beta name awareness)
2. Improve trim timing (stop trimming too early)
3. Optimize stop placement (stops too tight for high-beta names)

## Architecture

### Data source
Everything computes client-side from existing state:
- `state.trades` — full trade history (entries, trims, stops, directions)
- `state.dailyPrices` — daily close prices keyed as `TICKER:YYYY-MM-DD`
- `state.benchmarkHistories` — SPY daily close history

No new API calls or backend changes needed.

### New calculation module
**File:** `frontend/src/components/portfolio/lib/diagnostics.js`

Core functions:
- `computeBeta(ticker, dailyPrices, spyHistory)` — 60-day rolling beta from daily returns vs SPY
- `computePortfolioHeat(openTrades, dailyPrices)` — sum of (position size × distance-to-stop%)
- `computeTrimAnalysis(closedTrades, dailyPrices)` — compare trim price vs max price in N days after trim
- `computeStopAnalysis(closedTrades, dailyPrices)` — identify stopped-out trades where stock recovered
- `computeVolContribution(openTrades, dailyPrices, spyHistory)` — each position's contribution to portfolio variance
- `computeInsights(trades, stats)` — rule-based actionable observations

### UI structure
Replace `AnalyticsTab.jsx` content. `JournalPage.jsx` tab routing unchanged.

Internal sub-tabs within Analytics:
```
[Summary]  [Risk]  [Volatility]  [Trim & Stops]
```

Each sub-tab is a section component rendered conditionally via local state, not a separate route.

### Component files
```
frontend/src/components/journal/
  AnalyticsTab.jsx          — sub-tab router, data wiring
  analytics/
    SummarySection.jsx      — headline stats, equity curve, monthly table, insights
    RiskSection.jsx         — portfolio heat, concentration, beta-weighted exposure
    VolatilitySection.jsx   — portfolio vol, per-position vol, high-beta watchlist
    TrimStopsSection.jsx    — trim analysis, stop analysis, per-trade detail
```

### Reusable dependencies
- `lib/equityCurve.js` — `buildEquityCurve()` (already computed in PortfolioLayout)
- `lib/calculations.js` — `computeMonthlyStats()`, `enrichTrades()`, `lookupPrice()`
- `lib/portfolioFormat.js` — `fmtCur`, `fmtPct`, `fmt`, `clr`, `daysBetween`
- Recharts — LineChart, BarChart, PieChart (already imported in portfolio tabs)

---

## Sub-tab 1: Summary

The landing view. Quick health check.

### Top row — 6 stat cards
| Stat | Source |
|------|--------|
| Total Trades (closed) | `closedTrades.length` |
| Win Rate | `winners / closedTrades` |
| Avg R-Multiple | `avg(trade.rr)` from enriched trades |
| Expectancy ($) | `avg P/L per trade` |
| Avg Hold (days) | `avg(exitDate - entryDate)` |
| Profit Factor | `gross gains / gross losses` |

### Equity curve
Reuse `performanceData` already computed and passed from PortfolioLayout.

### Monthly performance table
Reuse `computeMonthlyStats`. Columns:
- Month | Return% | # Trades | Win% | Avg R | Max Gain% | Max Loss% | Days(W) | Days(L)

### Auto-generated insights
Rule-based observations (not AI). Examples:
- Win rate vs profit factor relationship
- Trade frequency vs returns correlation across months
- Holding period patterns (winners held longer than losers?)
- Consecutive loss streaks

Implementation: `computeInsights(trades, monthlyStats)` returns array of `{ type: 'positive'|'warning'|'neutral', text: string }`.

---

## Sub-tab 2: Risk

### Portfolio Heat panel
- **Total Heat %** = `sum(positionSize × abs(currentPrice - stopPrice) / portfolioValue)` for each open position
- Horizontal bar chart of heat per position, sorted largest → smallest
- Color coding: green (<1%), yellow (1-2%), red (>2%) per position
- Warning banner if total heat > 6-8%
- Flag positions with no stop set: "3 positions have no stop set"

### Concentration panel
- **By ticker** — horizontal bar chart of position weight%. Flag >15% single name
- **By sector** — horizontal bar chart. Flag >30% single sector
- **By direction** — long vs short exposure (net and gross % of portfolio)
- Reuse sector data from ExposureTab computation

### Beta-weighted exposure
- Table: Ticker | Qty | Mkt Val | Beta | Beta-Adjusted Exposure
- **Portfolio beta** = `sum(weight_i × beta_i)`
- **Beta-adjusted net exposure** = `sum(mktVal_i × beta_i × dir_i)`
- Callout: "Your portfolio has Xβ — a 1% SPY move ≈ X% portfolio move"

### Beta calculation
- 60 trading days of daily returns for ticker and SPY
- `beta = covariance(ticker_returns, spy_returns) / variance(spy_returns)`
- Computed from `dailyPrices` and `benchmarkHistories`
- Cache results per ticker to avoid recomputation

---

## Sub-tab 3: Volatility

### Portfolio Vol panel
- **Annualized daily vol** = `stddev(daily_returns) × sqrt(252)`
- **SPY vol** over same period
- **Vol ratio** = portfolio vol / SPY vol
- **Rolling 20-day vol chart** — two lines (portfolio vs SPY) over time using equity curve data

### Per-position vol contribution
- Table: Ticker | Weight% | Daily Vol | Beta | Vol Contribution% | Marginal Risk
- Sorted by vol contribution (highest first)
- **Vol contribution** = `weight_i × vol_i × correlation_i` (simplified marginal contribution)
- Highlight top 3 contributors with callout

### High-beta watchlist
- Auto-filter: positions with beta > 1.5
- Table: Ticker | Beta | Weight% | Equivalent SPY Exposure
- Equivalent SPY Exposure = `mktVal × beta`
- Actionable callout: sizing recommendations, hedging suggestions

---

## Sub-tab 4: Trim & Stops

### Trim Analysis — Summary
Stat cards:
- Trims Analyzed (total trim events across all closed trades)
- Too Early % — trims where stock ran 5%+ higher within 10 trading days after
- Avg Left on Table — average additional gain% after trim
- Avg Captured % — `(trimPrice - entryPrice) / (peakPrice - entryPrice) × 100`

### Trim Analysis — Per-trade detail
Table of closed trades with trims, sorted by "left on table" descending:
- Ticker | Entry | Trim Price | Trim Date | Peak After Trim | Peak Date | Left on Table% | Captured%
- Click row to expand: shows timeline of entry → each trim → actual peak
- Peak computed from `dailyPrices`: max close price in 10 trading days after trim date

### Stop Analysis — Summary
Stat cards:
- Total Stopped Out (trades where exit price ≈ stop price, within 1%)
- Stop Too Tight % — stopped-out trades where stock recovered 5%+ within 10 days
- Avg Stop Distance % — `avg(abs(stopPrice - entryPrice) / entryPrice)`

### Stop Analysis — Per-trade detail
Table of stopped-out trades that recovered, sorted by recovery%:
- Ticker | Entry | Stop | Exit Date | Low After | Recovery Peak | Recovery%
- Recovery = max price within 10 trading days after stop-out

### Actionable callouts
Rule-based, examples:
- "Avg stop distance is X% but avg beta is Y — consider widening stops to Z% for high-beta names"
- "You trimmed 1/3 at +X% avg, but winners that you held ran +Y% avg — consider delaying first trim"
- "Stocks with beta > 1.5 had Z% stop-out rate vs W% for lower-beta — use wider stops for volatile names"

---

## Styling

- Follow existing dark theme with CSS variables (`--color-*`)
- Stat cards reuse `StatCard` pattern from portfolio
- Tables match portfolio table styling (10px uppercase headers, tabular-nums, alternating rows)
- Charts use Recharts with existing color palette
- Sub-tab switcher matches existing tab pattern in JournalPage (underline active tab)
- Color coding for callouts: green (positive insight), amber (warning), neutral (observation)

---

## Scope boundaries

**In scope:**
- All calculations client-side from existing data
- Beta from dailyPrices + SPY benchmark
- Trim/stop analysis using dailyPrices for post-exit price lookup
- Rule-based insights (conditional logic)

**Out of scope (future):**
- AI-powered insights via Claude API (Phase 2 of CoachTab)
- Position sizing recommendations
- Forward-looking predictions
- Correlation matrix / portfolio optimization
- Custom date range filtering (could add later)
