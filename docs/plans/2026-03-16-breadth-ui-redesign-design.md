# Breadth Page UI Redesign — Design

**Goal:** Replace the current card-based Breadth page with a dense Stockbee-style historical data table + charts below.

## Layout

Two sections, vertically stacked:
1. **Historical Data Table** — rows = dates (newest first, up to 100 days), columns = all breadth metrics
2. **Charts** — existing % Above MAs line chart + McClellan histogram (unchanged)

## Table Design

### Structure
- Horizontally scrollable `<table>` inside `overflow-x-auto` container
- Date column sticky/first
- Today's row highlighted with `bg-stone-50` and left border accent
- Font: `font-mono text-[11px]` for data cells (matches project pattern)
- Headers: `text-[10px] font-medium uppercase tracking-wide text-stone-500`
- Rows: `border-b border-stone-100 hover:bg-stone-50`

### Columns (grouped with column group headers)

| Group | Columns |
|-------|---------|
| **Primary** | Date · Up 4% · Down 4% · 5D Ratio · 10D Ratio |
| **Quarterly/Monthly** | Up 25% Qtr · Down 25% Qtr · Up 25% Mo · Down 25% Mo · Up 50% Mo · Down 50% Mo |
| **Classic Breadth** | T2108 · % > 200 · % > 50 · % > 20 |
| **A/D** | Advances · Declines · NH · NL · McClellan |
| **Reference** | SPX Close · Worden |

### Conditional Cell Coloring (anti-dopamine palette)

Uses project's subtle `bg-*-50` backgrounds — same approach as ATR badge system.

- **Ratios (5D, 10D):** `≥1.0` green-50, `0.5–1.0` amber-50, `<0.5` red-50
- **% Above MAs (T2108, >200, >50, >20):** `≥60` green-50, `40–60` amber-50, `<40` red-50
- **McClellan Oscillator:** positive → green-50, negative → red-50
- **Up/Down counts:** plain `font-mono` text, no cell backgrounds
- **SPX, Worden:** plain text, no coloring

## Data Flow

The history JSON already contains all fields per day. The table just maps `data.breadth.history` entries into rows. Current history stores arrays by field — the table component will zip them into row objects.

No pipeline changes needed. The existing `breadth_metrics.py` already persists all required fields in the 100-day rolling history.

## Components Changed

- **Replace:** `MarketMonitor.jsx` + `ClassicBreadth.jsx` → new `BreadthTable.jsx`
- **Keep:** `BreadthCharts.jsx` (unchanged)
- **Update:** `BreadthPage.jsx` (swap component imports)

## What Stays the Same
- Charts (% Above MAs, McClellan histogram) stay below the table
- Pipeline code unchanged
- Data loading in `useMarketData.js` unchanged
