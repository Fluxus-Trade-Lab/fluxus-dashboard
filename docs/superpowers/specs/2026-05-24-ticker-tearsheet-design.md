# Ticker Tear-Sheet Design (v2 — matched to AAOI reference)

**Date:** 2026-05-24
**Status:** Draft for user review
**Reference:** AAOI · Applied Optoelectronics Trader Tearsheet (2-page PDF the user shared)
**Sequence:** Phase 3 of the portfolio overhaul (Phase 1 + 2 shipped)

## Problem

User wants a per-ticker tear-sheet, one click from anywhere a ticker is shown (Portfolio Tracker, Exposure Detail, Screener Results, Screener Watchlist). The reference AAOI tearsheet sets the bar: **two pages of technical + fundamental + catalyst + analyst depth**, with the user's own execution detail layered on top.

The Tracker simultaneously becomes cleaner — Phase 1's inline detail (proximity chips, trim targets) moves into the tear-sheet's status panel; the Tracker row goes back to a clean glance with a clickable ticker.

## Page structure (matches AAOI reference)

```
─── PAGE 1: TECHNICAL ─────────────────────────────────────────────
[ Header: TICKER · Name · meta · live price + % chg ]
[ Quick-stats strip: Mkt Cap · 52W Range · Avg Vol 20D · ATR(14)/%Px · RSI(14) · Fwd P/S 26E · Next ER ]
[ Price Trend & Technical Setup — TradingView Advanced Chart widget (1Y, MA20/50/200 overlay, volume, RSI) ]
[ Key Levels table (left)         |  Trend & Indicators table (right) ]
[ Relative Strength vs SPY & QQQ — rebased line chart + period table ]
─── PAGE 1.5: MY EXECUTION ────────────────────────────────────────
[ Status Panel — leg state, current stop, suggested stop + Accept, trim targets, EMA refs ]
[ Trades Section — grouped by campaign, aggregate stats at top ]
─── PAGE 2: FUNDAMENTALS & CATALYSTS ──────────────────────────────
[ Earnings — Next + Last 4Q (date, Rev act/est, EPS act/est, beat/miss ✓✗) ]
[ Valuation Snapshot — Mkt Cap, Rev/Fwd Rev, P/S, EV/Sales, P/E, margins, cash, FCF, D/E, Current Ratio ]
[ Key Quarterly Metrics — Period, Revenue, YoY, Gross Profit, GM%, Op Inc, EPS, Cash, Op CF (last 5Q) ]
[ Recent Catalysts & News (left)  |  Analyst Sentiment (right) ]
```

## Section-by-section detail

### 1. Header
- Symbol, company name, sector / industry / exchange / HQ / CEO
- Live price + day change (color-coded)
- "← Back" link (history.back())

### 2. Quick-stats strip
Compact row of 7 stats. Pulled from `universe.json` + per-ticker file:
- Mkt Cap, 52W Range, Avg Vol (20D), ATR(14) / %PX, RSI(14), Fwd P/S (26E), Next ER date

### 3. Price Trend & Technical Setup
TradingView Advanced Chart widget (free, no API key). Config:
- 1Y default range
- MA20/50/200 overlay built-in
- Volume + RSI(14) sub-panes
- Dark theme to match app

### 4. Key Levels table
Left half, below chart. Two columns: Level | Price | Notes.

Rows (derived from existing data + new fields):
- 52W High / Resistance
- 20-day high
- Pivot zone (Mar peak)
- MA20 (current value, computed from price × (1+sma20_dist))
- MA50 (same)
- 10-day low
- Gap-fill zone (manual annotation, defaults to "—")
- MA200 (computed)
- 52W Low

### 5. Trend & Indicators table
Right half, alongside Key Levels.

Rows:
- Trend (price vs MAs) — narrative ("Above MA20/50/200 — stacked bullish")
- MA stack (Golden alignment / mixed / inverted)
- RSI(14) — numeric + qualitative ("strong, not overbought")
- ATR(14) — stop sizing reference
- 1.5×ATR stop ref — computed dollar width
- 20-day avg volume
- Position in 52W range — % from low to high
- Volatility regime (low / normal / high)
- Setup type (Pullback in uptrend post-breakout / Base / Squeeze / N/A)

### 6. Relative Strength vs SPY & QQQ
Line chart rebased to 100 over 1 year (AAOI, SPY, QQQ). Plus a flat table:

| Period | AAOI | SPY | QQQ | vs SPY | vs QQQ |
|---|---|---|---|---|---|
| 1M | +67.9% | +9.5% | +15.6% | **+58.4%** | **+52.2%** |
| 3M, 6M, 1Y | … |

Uses `perf_1m`, `perf_3m`, `perf_6m`, `perf_1y` from universe (already there) and the SPY/QQQ benchmark values from `etf_data.json`.

### 7. Status Panel (user's execution)
For the most recent open layer of the user's position (if any):
- Leg-state badge (PRE_TRIM / POST_T1 / etc.)
- Current stop + suggested stop + "→ Accept" (reuses Phase 1 `stopSuggestion` helper)
- Trim target levels (+4R, +8R, +12R), strike-through if hit
- EMA reference values (ema10, ema20, wk_ema10, wk_ema20)

If no open position: "No open position. Last trade: <date> @ <price> realized +X.XR" if any closed.

### 8. Trades Section
Filter all user trades by ticker. Group by campaign (existing `groupByCampaigns`).

Per campaign — header row with aggregate stats (layer count, open/closed, total realized R, blended cost).
Expanded layers: entry date/price/qty, current qty, trims chain, current state.

Aggregate stats at top of section:
- Total trades on this ticker
- Win rate (closed trades with positive R)
- Total realized R captured
- Best / worst trade

### 9. Earnings — Next + Last 4Q
Pulled from yfinance `.earnings_history` + `.calendar`. Five rows:
- Q1 26 (next) — date, EST rev, EST EPS (highlighted as upcoming)
- Q4-Q1 trailing — date, Rev (Act / Est), EPS (Act / Est), beat (✓) or miss (✗) markers

### 10. Valuation Snapshot
Single 2-column table. Source: yfinance `.info` mostly, with FY estimates from analyst data:
- Market Cap, FY-prior Revenue, FY-next Revenue (est + YoY %), FY+1 Revenue (est + %)
- P/S TTM, EV/Sales TTM, Fwd P/S (next FY), Fwd P/S (FY+1)
- P/E TTM (or "neg." if negative)
- Gross Margin (current FY + est next FY)
- Op Margin
- Cash on hand (latest quarter)
- FY FCF
- Debt/Equity
- Current Ratio

### 11. Key Quarterly Metrics
5-quarter table. Source: yfinance `.quarterly_financials` + `.quarterly_balance_sheet`:
- Period · Revenue · YoY% · Gross Profit · GM% · Op Inc · Diluted EPS · Cash · Op CF

### 12. Recent Catalysts & News
Narrative bullets with footnote refs (per AAOI reference, e.g. "Mar 9, 2026: First volume order for 1.6T transceivers ..."). Two source options:

- **Auto (lossy)**: pull yfinance `.news` (titles, links, dates) and display as a list. Less curated than the AAOI reference but free.
- **AI-curated**: send recent yfinance news + recent earnings transcript excerpts to Claude API, ask it to synthesize 5-8 catalyst bullets. Better quality, costs API tokens, slower.
- **Manual**: a per-ticker editable field stored in Google Sheets or localStorage.

Default for Phase 3: **auto (lossy)** as MVP. Hook for AI-curated added in 3b once we confirm format.

### 13. Analyst Sentiment
Source: yfinance `.recommendations` + `.analyst_price_targets`:
- Consensus rating (Strong Buy / Buy / Hold / Sell)
- Total ratings count
- Bullish / Neutral / Bearish split
- Avg PT / High PT / Low PT
- Implied % vs current price (color-coded)
- Most recent rating change
- Notable upgrade(s) in trailing 60d

## Data architecture

This tear-sheet needs data that doesn't exist in `universe.json` today. New pipeline component:

```
pipeline/tickers/
├── __init__.py
├── ticker_data_fetcher.py     # yfinance-based fetcher (per-ticker JSON)
└── run_tickers.py             # CLI: refresh per-ticker data for a tracker-relevant set
```

Output: `data/output/tickers/{SYMBOL}.json` — one file per ticker, ~5-20 KB each.

Schema:
```json
{
  "ticker": "AAOI",
  "fetched_at": "2026-05-24T...",
  "info": { /* yfinance .info subset */ },
  "earnings": [ { "date": "2026-02-26", "rev_actual": 134.3, "rev_estimate": 132.3, "eps_actual": -0.04, "eps_estimate": -0.12 }, ... ],
  "valuation": { "market_cap": 14.1e9, "ps_ttm": 30.9, "ev_sales_ttm": 30.5, ... },
  "quarterly_financials": [ { "period": "Q4 2025", "revenue": 134.3e6, "yoy_pct": 0.34, ... }, ... ],
  "analyst": { "consensus": "Strong Buy", "n_ratings": 4, "avg_pt": 77.25, "high_pt": 140, "low_pt": 35, "recent": [...] },
  "news": [ { "date": "2026-03-09", "title": "...", "url": "..." }, ... ]
}
```

Which tickers get fetched?
- All tickers in the user's open positions (from `data/portfolio/portfolio_*.csv`)
- All tickers in the user's recent (90d) closed trades
- Optionally all tickers from a "watchlist" of interest (future)

For Phase 3, ~50-100 tickers total. yfinance fetch budget ~2 min for that batch.

Cron addition: `pipeline/tickers/run_tickers.py` runs after the main `run_all`, so fresh data is available every day after market close.

Frontend reads `data/output/tickers/{SYMBOL}.json` lazily when the tear-sheet opens. If the file doesn't exist, the tear-sheet shows "Fundamentals not yet fetched for this ticker — falling back to universe data only."

## Routing

Hash-based, consistent with existing routes:
- `#/ticker/AAPL` → renders `<TickerPage symbol="AAPL" />`
- Symbol normalized to uppercase

Implementation: extend `Layout.jsx` to recognize `#/ticker/<SYM>`. Tiny `tickerUrl.tickerHref(symbol)` helper for consistent link generation.

Back-nav: header "← Back" → `window.history.back()`.

## Sub-phasing

This is bigger than originally scoped. Break into three shippable sub-phases:

### Phase 3a — Skeleton + execution + chart (ships in 1 sitting)
- Hash routing `#/ticker/<SYM>`
- Page skeleton with all section placeholders
- TradingView chart widget
- Status Panel (uses Phase 1 helpers — leg state, stop suggestion, trim targets, EMAs)
- Trades Section (uses existing portfolio data, campaign grouping)
- Stats row (universe.json subset)
- TickerLink component + wire-up in Tracker, Exposure Detail, Screener Results, Watchlist
- Tracker simplification (drop inline chips + targets line)

### Phase 3b — Fundamentals pipeline + tables (ships next, in 1 sitting)
- New `pipeline/tickers/` module
- Per-ticker JSON output
- Quick-stats strip filled in
- Earnings, Valuation Snapshot, Quarterly Metrics, Analyst Sentiment sections
- Hooked into cron

### Phase 3c — Technicals tables + RS chart (small follow-on)
- Key Levels table (derived from existing data + ATR + chart highs/lows)
- Trend & Indicators table (RSI needs pipeline addition; rest computable)
- Relative Strength chart + table (rebased; needs SPY/QQQ historical from etf_data)
- Catalysts & News section (auto = yfinance news; AI-curated comes later if useful)

Total estimated work: 3a ~1 hour, 3b ~1.5 hour, 3c ~1 hour. Plus pipeline runs.

## File-level changes (all sub-phases)

```
data/output/tickers/{SYMBOL}.json         NEW (3b) — fundamentals data per ticker
pipeline/tickers/__init__.py              NEW (3b)
pipeline/tickers/ticker_data_fetcher.py   NEW (3b) — yfinance fetcher
pipeline/tickers/run_tickers.py           NEW (3b) — CLI entry
.github/workflows/daily-data-update.yml   MODIFY (3b) — add run_tickers step

frontend/src/components/portfolio/lib/tickerUrl.js           NEW (3a)
frontend/src/components/ticker/                              NEW dir (3a)
  TickerPage.jsx                                              NEW (3a)
  TickerHeader.jsx                                            NEW (3a)
  TickerQuickStats.jsx                                        NEW (3a)
  TickerChart.jsx                                             NEW (3a) — TradingView widget
  TickerKeyLevels.jsx                                         NEW (3c)
  TickerTrendIndicators.jsx                                   NEW (3c)
  TickerRelativeStrength.jsx                                  NEW (3c)
  TickerStatusPanel.jsx                                       NEW (3a)
  TickerTrades.jsx                                            NEW (3a)
  TickerEarnings.jsx                                          NEW (3b)
  TickerValuation.jsx                                         NEW (3b)
  TickerQuarterlyMetrics.jsx                                  NEW (3b)
  TickerCatalysts.jsx                                         NEW (3b/3c)
  TickerAnalystSentiment.jsx                                  NEW (3b)
  TickerLink.jsx                                              NEW (3a)
frontend/src/hooks/useTickerData.js                          NEW (3b) — fetch per-ticker JSON

frontend/src/components/Layout.jsx                           MODIFY (3a) — add route
frontend/src/components/portfolio/tabs/OverviewTab.jsx       MODIFY (3a) — ticker → TickerLink, drop chips + targets line
frontend/src/components/portfolio/tabs/ExposureTab.jsx       MODIFY (3a)
frontend/src/components/screener/ResultsTable.jsx            MODIFY (3a)
frontend/src/components/screener/WatchlistTab.jsx            MODIFY (3a)
```

## Tracker simplification

Reduce noise in Portfolio Tracker rows:

| Element | Today | After 3a |
|---|---|---|
| Ticker text | bold + badge + chips + targets line | **clickable bold link + badge** |
| LegStateBadge | inline | KEEP |
| ProximityChips | inline | **REMOVE** (move to tear-sheet status panel) |
| TrimTargetsLine | below ticker | **REMOVE** (move to tear-sheet status panel) |
| StopCell suggestion | inline | KEEP (actionable in place) |

## Risks / open questions

1. **yfinance reliability for fundamentals**: free, but rate-limited and sometimes returns stale or missing fields. For Phase 3b, gracefully handle missing fields (show "—" rather than crash). If yfinance proves insufficient over time, can swap to Finnhub / IEX Cloud / Polygon paid tier.
2. **Per-ticker JSON file size + repo bloat**: ~10 KB × 100 tickers × refreshed daily = ~1 MB regenerated per day. Existing data files are larger; OK.
3. **Catalysts section quality**: yfinance news is generic. AAOI-quality narrative bullets need either Claude synthesis (Phase 3c+) or manual curation. Phase 3 ships the auto version; we add Claude synthesis once you've used the auto for a week and we see what's missing.
4. **TradingView widget customization**: free widget has limited theming controls. We get dark mode, MA overlays, volume + RSI sub-panes. Anything more (custom indicators, drawing tools) requires paid subscription.
5. **"Most recent open layer" for status panel**: when a campaign has multiple open layers, default to the layer with largest current_qty.

## Acceptance criteria (Phase 3a — skeleton ships first)

- [ ] `#/ticker/AAPL` loads, shows header + chart + status panel + trades + basic stats row
- [ ] TradingView Advanced Chart widget renders for the symbol with dark theme
- [ ] Status Panel shows leg state, current/suggested stop with Accept, trim targets, EMA refs (or "No open position" alternative)
- [ ] Trades Section lists all user trades on ticker, grouped by campaign with aggregate stats
- [ ] Stats row shows ≥10 universe fields
- [ ] Clicking a ticker in Tracker / Exposure Detail / Screener Results / Watchlist opens the tear-sheet
- [ ] "← Back" returns to previous page
- [ ] Tracker rows no longer show inline ProximityChips or TrimTargetsLine
- [ ] LegStateBadge + StopCell suggestion remain on Tracker
- [ ] All existing tests still pass; build still clean
- [ ] Section placeholders present for Phase 3b/3c content ("loading…" or "coming next phase")

## Acceptance criteria (Phase 3b — fundamentals)

- [ ] `pipeline/tickers/` module written + tested on a small ticker sample
- [ ] Daily cron runs `run_tickers.py` and writes `data/output/tickers/<SYM>.json` for all tracked tickers
- [ ] Quick-stats strip filled in (Fwd P/S, RSI, Next ER from per-ticker JSON)
- [ ] Earnings table renders with last 4Q + next ER
- [ ] Valuation Snapshot renders with all listed fields
- [ ] Quarterly Metrics table renders last 5Q
- [ ] Analyst Sentiment renders with consensus, ratings split, PTs, recent moves
- [ ] Tear-sheet handles missing data gracefully (no crash; shows "—")

## Acceptance criteria (Phase 3c — technicals + RS + catalysts)

- [ ] Key Levels table renders with all rows
- [ ] Trend & Indicators table renders with all rows (RSI from pipeline addition)
- [ ] Relative Strength rebased chart + period table renders
- [ ] Recent Catalysts & News section renders (auto from yfinance news for now)
