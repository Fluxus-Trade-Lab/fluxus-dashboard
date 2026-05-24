# Ticker Tear-Sheet Design

**Date:** 2026-05-24
**Status:** Draft for user review
**Replaces:** Inline Phase 1 detail on Tracker rows (to be slimmed down)
**Sequence:** Phase 3 of the portfolio overhaul (Phase 1 = inline UI shipped, Phase 2 = Capital-at-Risk shipped, this is the consolidation play)

## Problem

Phase 1 packed leg state, trim targets, EMA proximity chips, and stop suggestions into every Tracker row. That made the Tracker information-dense at the cost of visual cleanliness. The right home for that detail is a **per-ticker tear-sheet page** — one click from any ticker on the Tracker, Screener, or Screener watchlist gets you the full picture: trade history, current status, stop suggestions, chart, fundamentals. The Tracker row goes back to a clean glance.

## Scope

In scope (Phase 3):
1. **Hash-based route**: `#/ticker/<SYMBOL>` opens a dedicated page
2. **Tear-sheet page layout**: header + chart + status panel + trades table + key stats
3. **TradingView Advanced Chart widget** embedded for the symbol
4. **Trades section**: all of the user's open + closed trades on this ticker, grouped by campaign, with per-trade stats and aggregate stats
5. **Status panel**: for the most recent open layer (if any) — leg state, current stop, suggested stop with Accept, EMA reference levels, trim target levels
6. **Stats section**: from universe.json — sector, market cap, ATR%, RS scores, performance metrics
7. **Linking from Tracker**: ticker text in Portfolio Tracker rows becomes a click-link
8. **Linking from Screener + Watchlist**: same for those tables
9. **Tracker simplification**: drop the inline trim-targets line, drop the EMA proximity chips (move to tear-sheet). Keep the leg-state badge (small, glanceable). Keep the StopCell suggestion line (it's actionable inline).

Out of scope (Phase 3b, separate):
- Persisted stop-change history per trade (would need a new array field on Trade)
- Auto-trailing-stop toggle that writes per-ticker preferences honored by the daily cron
- Detailed fundamentals (P/E ratio, revenue, EPS growth) — universe.json doesn't have them; would need a pipeline addition
- News feed for the ticker
- Editing trades from inside the tear-sheet (use the existing trade form via "+ Trade")

## Routing

Hash-based, consistent with existing `#/portfolio`, `#/screener`, etc.

| Hash | Page |
|---|---|
| `#/ticker/AAPL` | AAPL tear-sheet |
| `#/ticker/MU` | MU tear-sheet |

Implementation: extend `Layout.jsx` to recognize hashes matching `#/ticker/<SYMBOL>` and render `<TickerPage symbol={SYMBOL} />`. The `useHash` hook already returns the raw hash; parse the symbol out of it inline (no hook change needed).

Navigation helper: a small `lib/tickerUrl.js` exports `tickerHref(symbol) → "#/ticker/AAPL"` so all link sources use it consistently.

Back-navigation: header has a "← Back" link that does `window.history.back()` (works for both Tracker → Tearsheet → Tracker and Screener → Tearsheet → Screener flows).

## Page layout

```
┌────────────────────────────────────────────────────────────────────┐
│  ← Back   AAPL · Apple Inc.   $185.20 +1.2%      [Sector] [ATR 2.5%]
├────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐  ┌──────────────────────┐
│  │                                      │  │  STATUS              │
│  │     TradingView Chart Widget         │  │  POST-T1             │
│  │                                      │  │                      │
│  │     (440px tall)                     │  │  Current stop $93.50 │
│  │                                      │  │  Suggested $108.25   │
│  │                                      │  │  → Accept            │
│  │                                      │  │                      │
│  │                                      │  │  Targets             │
│  │                                      │  │  +4R $115 ✓          │
│  │                                      │  │  +8R $135            │
│  │                                      │  │                      │
│  │                                      │  │  EMAs                │
│  │                                      │  │  10EMA $98.40        │
│  │                                      │  │  20EMA $95.20        │
│  │                                      │  │  wk-10EMA $92.10     │
│  │                                      │  │  wk-20EMA $89.30     │
│  └──────────────────────────────────────┘  └──────────────────────┘
├────────────────────────────────────────────────────────────────────┤
│  TRADES — 3 layers · 2 open · +18.4R captured · 67% WR             │
│  ┌────────────────────────────────────────────────────────────────┐
│  │  Open: 2026-04-08  Entry $147  Qty 990  Stop $93  R$ $53.4k    │
│  │   ├ Trim 04-14  $204  330 sh                                   │
│  │   ├ Trim 04-23  $237  330 sh                                   │
│  │   └ (residual)  330 sh                                         │
│  │  Open: 2026-05-19  Entry $267  Qty 276  Stop $260  R$ $1.9k    │
│  │   └ Trim 05-21  $309  55 sh                                    │
│  │  Closed: 2026-03-01  Entry $158  +1.2R                         │
│  └────────────────────────────────────────────────────────────────┘
├────────────────────────────────────────────────────────────────────┤
│  STATS                                                              │
│  Sector: Tech  ·  Mkt Cap: $2.8T  ·  ADR%: 2.5%  ·  Hybrid RS: 87  │
│  Perf 1W: +2.1%  ·  1M: +8.5%  ·  3M: +14.2%  ·  YTD: +22.0%       │
│  Distance from 21EMA: +1.2%  ·  50SMA: +5.4%  ·  200SMA: +18.0%    │
│  Volume: 52M  ·  Avg Vol: 48M  ·  Rel Vol: 1.08                    │
└────────────────────────────────────────────────────────────────────┘
```

Sections, in order:

1. **Header**: ticker, company name (where we can get it), live price, % change today, sector chip, ATR% chip, back link
2. **Chart + Status row**: TradingView Advanced Chart (left, ~⅔ width) + Status panel (right, ~⅓ width)
3. **Trades**: grouped-by-campaign list of all open + closed trades on this ticker, with aggregate stats at the top
4. **Stats**: flat row of universe-data fields, no chart

## TradingView widget

Drop in the free Advanced Chart widget. No API key. One-time `<script>` tag loaded via React useEffect.

```jsx
<div id={`tv-${symbol}`} className="h-[440px]" />
// in useEffect, append:
<script src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" />
// with stringified config including symbol, theme matching the app, etc.
```

Config: dark theme (matches the app's dark mode), 1D interval default, ~440px height, hide the toolbar's "save" actions (we're not a TV user).

If symbol changes (route from `#/ticker/AAPL` to `#/ticker/MU`), the component remounts with a new container id; the widget re-initializes cleanly.

## Status panel content

For the **most recent open layer** of the ticker (if any):
- Leg-state badge
- Current stop + (if different) suggested stop + Accept link → dispatches `UPDATE_TRADE`
- Re-uses `stopSuggestion.suggest()` from Phase 1
- Trim target levels (+4R, +8R, +12R), strike-through if hit
- EMA reference values: ema10, ema20, wk_ema10, wk_ema20

If **no open position**:
- Show "No open position" + most recent closed trade summary (if any)

## Trades section content

Filter all user trades by `ticker === symbol`. Apply existing `groupByCampaigns` helper.

Per campaign:
- Header row: layer count, "open" or "closed" count, total realized R (campaign-level), aggregate cost basis
- Per-layer detail (expandable): entry date/price/qty, stop, current qty, trims, realized R, current state

Aggregate stats at top of section:
- Total trades on this ticker (across all campaigns)
- Win rate (% of closed trades with positive R)
- Total realized R captured

## Stats section content

Just key fields from `universe.json[symbol]`, displayed as a labeled flat row. No charts. The TradingView widget covers chart concerns.

Fields:
- Sector, market cap
- ADR%, ATR
- Hybrid RS (`h_score`), F Score, I Score, IBD RS
- Perf 1W / 1M / 3M / YTD
- Distance from 21EMA, 50SMA, 200SMA, 52W high
- Volume, avg volume, relative volume
- (Phase 1 plumbed) ema10/ema20/wk_ema10/wk_ema20

## Tracker simplification

Reduce noise in Portfolio Tracker rows now that the tear-sheet absorbs the detail:

| Element | Phase 1 | Phase 3 |
|---|---|---|
| Ticker text | bold + badge + chips + targets line | **bold + badge + click-link** |
| LegStateBadge | KEEP next to ticker | KEEP |
| ProximityChips | next to ticker | **REMOVE** (move to tear-sheet status panel) |
| TrimTargetsLine | below ticker | **REMOVE** (move to tear-sheet status panel) |
| StopCell suggestion | KEEP inline | KEEP (actionable in place) |

Net effect: each Tracker row goes from a 2-line ticker cell with multiple visual elements back to a clean single-line bold ticker (still color-badged for leg state), but now clickable to drill down.

## Linking sources

Use `tickerHref(symbol)` helper everywhere:

1. **Portfolio Tracker** (`OverviewTab.jsx`) — wrap ticker text in `<a href={tickerHref(t.ticker)}>`
2. **Exposure tab Detail table** (`ExposureTab.jsx`) — wrap ticker text in `<a>`
3. **Screener results table** (`ResultsTable.jsx`) — wrap ticker text in `<a>`
4. **Screener Watchlist tab** (`WatchlistTab.jsx`) — same

All open in same window (regular hash navigation). Back button works as expected.

## File-level changes

```
frontend/src/components/portfolio/lib/tickerUrl.js       NEW  tiny — exports tickerHref(symbol)
frontend/src/components/ticker/                          NEW dir
  TickerPage.jsx                                          NEW  top-level page
  TickerHeader.jsx                                        NEW  symbol/name/price/back
  TickerChart.jsx                                         NEW  TradingView widget wrapper
  TickerStatusPanel.jsx                                   NEW  leg state + stop + targets + EMAs
  TickerTrades.jsx                                        NEW  grouped trade history + aggregate stats
  TickerStats.jsx                                         NEW  universe field display
  TickerLink.jsx                                          NEW  <a href={tickerHref(s)}>{children}</a>

frontend/src/components/Layout.jsx                       MODIFY  add #/ticker/<SYM> route
frontend/src/components/portfolio/tabs/OverviewTab.jsx   MODIFY  ticker → TickerLink; drop chips + targets line
frontend/src/components/portfolio/tabs/ExposureTab.jsx   MODIFY  ticker → TickerLink
frontend/src/components/screener/ResultsTable.jsx        MODIFY  ticker → TickerLink
frontend/src/components/screener/WatchlistTab.jsx        MODIFY  ticker → TickerLink (if a ticker col exists)
```

## Testing strategy

- Unit: `tickerUrl.tickerHref(symbol)` — pure function, trivial
- Visual: load `#/ticker/MU` in dev preview, confirm chart renders, trades list shows real data, status panel matches Tracker row
- Click flow: from Tracker click on MU → tear-sheet opens; click "← Back" → returns to Tracker preserving scroll position

## Risks / open questions

1. **TradingView widget reliability**: third-party iframe; if their CDN is slow, the chart loads slowly. Not blocking — page renders without it.
2. **Symbol case sensitivity**: hashes like `#/ticker/aapl` vs `#/ticker/AAPL`. Normalize to uppercase in `tickerHref` and the route parser.
3. **Company name source**: not currently in universe.json. For Phase 3, show just the ticker; add company_name in a later pipeline pass if useful.
4. **"Most recent open layer" definition**: if there are multiple open layers (campaign), use the one with the largest current_qty as the "primary" for the status panel. Alternative is showing a small per-layer status mini-table; can iterate.

## Acceptance criteria

- [ ] `#/ticker/AAPL` loads a page with header + chart + status panel + trades + stats
- [ ] TradingView Advanced Chart widget renders for the symbol (dark theme)
- [ ] Trades section lists all user trades on the ticker, grouped by campaign with aggregate stats
- [ ] Status panel shows leg state, current/suggested stop with Accept, trim targets, EMA refs (when an open position exists)
- [ ] "No open position" state renders when applicable
- [ ] Stats section shows ≥10 universe fields
- [ ] Clicking a ticker in Portfolio Tracker / Exposure Detail / Screener Results / Watchlist opens the tear-sheet
- [ ] "← Back" returns to the previous page
- [ ] Tracker rows no longer show inline ProximityChips or TrimTargetsLine (moved to tear-sheet)
- [ ] LegStateBadge still shows on Tracker (it's glanceable)
- [ ] StopCell still shows suggestion + Accept inline (it's actionable)
- [ ] All existing tests still pass; build still clean
