# Breadth Metrics Design

**Date**: 2026-03-16
**Status**: Approved

## Goal

Build self-calculated market breadth metrics combining Stockbee Market Monitor scans with classic breadth indicators. Replace the deferred Phase 2 placeholder with a real breadth module.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Universe | Full Finviz (~2,485 stocks, market cap >= $1B) | Already fetched daily, no extra pull |
| Data source | Finviz-primary + yfinance enrichment for 40-day SMA | Zero extra runtime for most metrics; one additional `rolling(40)` in existing enrichment step for true T2108 |
| History depth | 100 trading days (~5 months) | Matches Oratnek's 100-day chart reference; sufficient for medium-term breadth cycles |
| Chart library | TradingView Lightweight Charts (open source) | Renders our own data, looks like TradingView, ~40KB bundle |
| SPX price | ^GSPC via yfinance (actual index, not SPY proxy) | Added to fetch_ma_data() tickers |
| CSV archive | Append daily row to `data/history/breadth_archive.csv` | Google Apps Script pulls from raw GitHub URL for automatic Sheets sync |
| Stockbee ratio | Existing `stockbee_ratio.py` stays untouched | New module computes its own counts independently |

## Metrics

### Stockbee Market Monitor Scans

**Primary Breadth Indicators:**

| Metric | Source Column | Calculation |
|--------|-------------|-------------|
| Stocks up 4% today | `change_pct` | `count(change_pct >= 0.04)` |
| Stocks down 4% today | `change_pct` | `count(change_pct <= -0.04)` |
| 5-day ratio | history | `sum(up_4pct, 5d) / sum(down_4pct, 5d)` |
| 10-day ratio | history | `sum(up_4pct, 10d) / sum(down_4pct, 10d)` |
| Stocks up 25% in quarter | `perf_3m` | `count(perf_3m >= 0.25)` |
| Stocks down 25% in quarter | `perf_3m` | `count(perf_3m <= -0.25)` |

**Secondary Breadth Indicators:**

| Metric | Source Column | Calculation |
|--------|-------------|-------------|
| Stocks up 25% in month | `perf_1m` | `count(perf_1m >= 0.25)` |
| Stocks down 25% in month | `perf_1m` | `count(perf_1m <= -0.25)` |
| Stocks up 50% in month | `perf_1m` | `count(perf_1m >= 0.50)` |
| Stocks down 50% in month | `perf_1m` | `count(perf_1m <= -0.50)` |

**Reference:**

| Metric | Source | Notes |
|--------|--------|-------|
| Worden Universe size | `len(universe)` | Number of stocks in dataset |
| T2108 | `sma40_dist > 0` | % above 40-day SMA (true T2108, computed via yfinance enrichment) |
| SPX EOD price | `^GSPC` close via yfinance | Added to fetch_ma_data() |

### Classic Breadth

| Metric | Source | Calculation |
|--------|--------|-------------|
| % above 200 SMA | `sma200_dist > 0` | `count / total * 100` |
| % above 50 SMA | `sma50_dist > 0` | `count / total * 100` |
| % above 20 SMA | `sma20_dist > 0` | `count / total * 100` |
| Advances | `change_pct > 0` | Count |
| Declines | `change_pct < 0` | Count |
| New 52w highs | `high_52w_dist` within 2% of 0 | Count |
| New 52w lows | `low_52w` within 2% of 0 | Count |
| A/D line | history | Cumulative `sum(advances - declines)` |
| McClellan Oscillator | history | `EMA19(net_advances) - EMA39(net_advances)` |

## Architecture

### Pipeline

```
run_all.py orchestrator
    |
    +-- fetch Finviz universe (2,485 stocks)
    +-- yfinance enrich_universe()  <-- adds sma40_dist (1 line)
    +-- fetch_ma_data(['SPY','QQQ','IWM','RSP','^GSPC'])  <-- adds ^GSPC
    +-- run existing screeners...
    +-- run stockbee_ratio()        <-- stays as-is
    |
    +-- run breadth_metrics()       <-- NEW
            |
            +-- Input: scored universe DataFrame + history file
            +-- Compute today's snapshot (all counts/percentages)
            +-- Load history (up to 99 prior days from JSON)
            +-- Compute cumulative metrics (A/D line, McClellan)
            +-- Save updated history (100-day rolling JSON)
            +-- Append row to breadth_archive.csv
            +-- Output: dict -> breadth.json
```

### New/Modified Files

**New:**
- `pipeline/screeners/breadth_metrics.py` -- main breadth calculation module
- `data/output/breadth.json` -- frontend-facing output
- `data/history/breadth_metrics_history.json` -- 100-day rolling history
- `data/history/breadth_archive.csv` -- append-only CSV for Google Sheets
- `frontend/src/components/breadth/BreadthPage.jsx` -- breadth page container
- `frontend/src/components/breadth/MarketMonitor.jsx` -- Section 1: MM scans
- `frontend/src/components/breadth/ClassicBreadth.jsx` -- Section 2: classic metrics
- `frontend/src/components/breadth/BreadthCharts.jsx` -- Section 3: Lightweight Charts

**Modified:**
- `pipeline/adapters/yfinance_adapter.py` -- add `sma40_dist` in enrich_universe(), add `^GSPC` to fetch_ma_data()
- `pipeline/screeners/run_all.py` -- call breadth_metrics.run(), save breadth.json
- `frontend/src/hooks/useMarketData.js` -- add 'breadth' to FILES array
- `frontend/src/App.jsx` (or router) -- add breadth page/tab

## Output Schema

### `data/output/breadth.json`

```json
{
  "timestamp": "2026-03-14T20:30:00Z",
  "universe_size": 2485,
  "spx_close": 5638.94,

  "mm": {
    "up_4pct": 60,
    "down_4pct": 146,
    "ratio_5d": 0.3589,
    "ratio_10d": 0.4102,
    "up_25pct_qtr": 87,
    "down_25pct_qtr": 312,
    "up_25pct_month": 22,
    "down_25pct_month": 95,
    "up_50pct_month": 3,
    "down_50pct_month": 18
  },

  "breadth": {
    "t2108": 39.8,
    "pct_above_200sma": 58.3,
    "pct_above_50sma": 42.1,
    "pct_above_20sma": 35.6,
    "advances": 1420,
    "declines": 1065,
    "new_highs": 34,
    "new_lows": 89,
    "ad_line": 1842,
    "mcclellan_osc": -45.2
  },

  "history": {
    "dates": ["2025-10-15", "2025-10-16", "...100 entries"],
    "pct_above_200sma": [62.1, 61.8],
    "pct_above_50sma": [48.3, 47.9],
    "pct_above_20sma": [40.1, 39.5],
    "mcclellan_osc": [-12.3, -18.1]
  }
}
```

### `data/history/breadth_archive.csv`

One row per trading day. Columns:

```
date,universe_size,spx_close,up_4pct,down_4pct,ratio_5d,ratio_10d,up_25pct_qtr,down_25pct_qtr,up_25pct_month,down_25pct_month,up_50pct_month,down_50pct_month,t2108,pct_above_200sma,pct_above_50sma,pct_above_20sma,advances,declines,new_highs,new_lows,ad_line,mcclellan_osc
```

## Frontend Layout

Three sections in a single page/tab:

```
+-----------------------------------------------------------------------+
| SECTION 1: STOCKBEE MARKET MONITOR                                     |
+-----------------------------------------------------------------------+
|                                                                        |
|  +- Primary ----------+ +- Secondary --------+ +- Reference ---------+|
|  | Up 4%      60      | | Up 25% Mo    22    | | Worden    2,485     ||
|  | Down 4%   146      | | Down 25% Mo  95    | | T2108     39.8%     ||
|  | Ratio 5D   0.36    | | Up 50% Mo     3    | | SPX    5,638.94     ||
|  | Ratio 10D  0.41    | | Down 50% Mo  18    | |                     ||
|  | Up 25% Qtr   87    | |                    | |                     ||
|  | Down 25% Qtr 312   | |                    | |                     ||
|  +---------------------+ +--------------------+ +---------------------+|
|                                                                        |
+-----------------------------------------------------------------------+
| SECTION 2: CLASSIC BREADTH                                             |
+-----------------------------------------------------------------------+
|                                                                        |
|  % > 200 SMA   58.3%      Advances   1420      NH    34              |
|  % > 50 SMA    42.1%      Declines   1065      NL    89              |
|  % > 20 SMA    35.6%      A/D Line   1842                            |
|                            McClellan  -45.2                           |
|                                                                        |
+-----------------------------------------------------------------------+
| SECTION 3: 100-DAY HISTORY (TradingView Lightweight Charts)            |
+-----------------------------------------------------------------------+
|                                                                        |
|  +- % Above MAs ---------------------------------------------------+ |
|  |  ~~~~ 200 SMA    ~~~~ 50 SMA    ~~~~ 20 SMA                     | |
|  +------------------------------------------------------------------+ |
|                                                                        |
|  +- McClellan Oscillator -------------------------------------------+ |
|  |  histogram (green > 0, red < 0)                                  | |
|  +------------------------------------------------------------------+ |
|                                                                        |
+-----------------------------------------------------------------------+
```

## Google Sheets Sync

- Pipeline appends one row per day to `data/history/breadth_archive.csv`
- CSV is committed to GitHub via daily Actions workflow (already commits `data/history/`)
- Google Apps Script with daily time-trigger fetches raw CSV from GitHub and appends new rows to a Google Sheet
- No secrets or API keys needed in the pipeline

## Sources

- [Stockbee Market Monitor](https://stockbee.blogspot.com/p/mm.html)
- [Stockbee MM Scans (formulas)](https://stockbee.blogspot.com/2018/08/market-monitor-scans.html)
- [Understanding Market Monitor Part 1](https://stockbee.blogspot.com/2010/08/understanding-market-monitor-part1.html)
- [TradingView Lightweight Charts](https://github.com/nicholasgasior/lightweight-charts)
- [T2108 / TC2000 definition](https://help.tc2000.com/m/69404/l/755052-t2108-of-stocks-above-40-day-pma-also-t2s-110-112-114-116)
- [INDEX:MMFI (TradingView % above 50DMA)](https://www.tradingview.com/symbols/INDEX-MMFI/)
