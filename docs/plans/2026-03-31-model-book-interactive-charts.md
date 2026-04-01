# Model Book Interactive Charts — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the existing Model Books page from a static card gallery into a Big Movers-style interactive chart browser with OHLCV candlestick charts, moving averages, per-tag performance stats, and SPY overlay.

**Architecture:** Pipeline script fetches OHLCV data for curated model book entries via yfinance, saves per-entry JSON files. Frontend replaces card placeholders with real lightweight-charts candlestick charts in a two-panel layout (sortable table left, interactive chart right). Existing `index.json` metadata is enriched with OHLCV file paths and performance metrics.

**Tech Stack:** Python 3.11 + yfinance (pipeline), React 19 + lightweight-charts v5 + Tailwind CSS 4 (frontend)

---

## Task 1: Pipeline — OHLCV Data Fetcher for Model Book Entries

**Files:**
- Create: `pipeline/tools/fetch_model_book_ohlcv.py`
- Modify: `frontend/public/data/modelbooks/index.json` (add `ohlcv_file`, `gain_pct`, `duration_days`)

**Context:** Each model book entry in `index.json` has `{id, ticker, year, source, patterns, key_lessons, outcome, image}`. We need OHLCV data around the breakout window for each entry. Since these are historical setups (some from the 1960s), yfinance won't have data for all. The script should handle missing data gracefully.

**Step 1: Create the OHLCV fetcher script**

```python
# pipeline/tools/fetch_model_book_ohlcv.py
"""
Fetch OHLCV data for model book entries and save as individual JSON files.
Usage: python -m pipeline.tools.fetch_model_book_ohlcv
"""
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

import yfinance as yf
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = PROJECT_ROOT / 'frontend' / 'public' / 'data' / 'modelbooks' / 'index.json'
OHLCV_DIR = PROJECT_ROOT / 'frontend' / 'public' / 'data' / 'modelbooks' / 'ohlcv'


def fetch_ohlcv_for_entry(ticker: str, year: int) -> list[dict] | None:
    """Fetch ~18 months of OHLCV around the entry's year.
    Returns list of {time, open, high, low, close, volume} dicts
    for lightweight-charts consumption.
    """
    try:
        start = f"{year - 1}-01-01"
        end = f"{year + 1}-06-30"
        hist = yf.download(ticker, start=start, end=end, progress=False)
        if hasattr(hist.columns, 'levels') and hist.columns.nlevels > 1:
            hist.columns = hist.columns.get_level_values(0)
        if hist.empty or len(hist) < 20:
            return None

        records = []
        for date, row in hist.iterrows():
            records.append({
                'time': date.strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume']),
            })
        return records
    except Exception as e:
        logger.warning(f"Failed to fetch {ticker} for {year}: {e}")
        return None


def compute_move_stats(ohlcv: list[dict]) -> dict:
    """Compute gain % and duration from OHLCV data.
    Uses simple min-close-to-max-close for the gain window.
    """
    if not ohlcv or len(ohlcv) < 5:
        return {'gain_pct': None, 'duration_days': None}

    closes = [bar['close'] for bar in ohlcv]
    min_idx = closes.index(min(closes))
    # Find max after the min
    after_min = closes[min_idx:]
    max_after = max(after_min)
    max_idx = min_idx + after_min.index(max_after)

    if closes[min_idx] <= 0:
        return {'gain_pct': None, 'duration_days': None}

    gain_pct = round((max_after / closes[min_idx] - 1) * 100, 1)
    duration = max_idx - min_idx
    return {'gain_pct': gain_pct, 'duration_days': duration}


def main():
    OHLCV_DIR.mkdir(parents=True, exist_ok=True)

    with open(INDEX_PATH) as f:
        entries = json.load(f)

    updated = 0
    for entry in entries:
        entry_id = entry['id']
        ohlcv_path = OHLCV_DIR / f"{entry_id}.json"

        # Skip if already fetched
        if ohlcv_path.exists():
            logger.info(f"  Skipping {entry_id} (already exists)")
            # Still compute stats if missing
            if entry.get('gain_pct') is None:
                with open(ohlcv_path) as f:
                    ohlcv = json.load(f)
                stats = compute_move_stats(ohlcv)
                entry.update(stats)
                entry['ohlcv_file'] = f"ohlcv/{entry_id}.json"
                updated += 1
            continue

        ohlcv = fetch_ohlcv_for_entry(entry['ticker'], entry['year'])
        if ohlcv:
            ohlcv_path.write_text(json.dumps(ohlcv))
            stats = compute_move_stats(ohlcv)
            entry.update(stats)
            entry['ohlcv_file'] = f"ohlcv/{entry_id}.json"
            updated += 1
            logger.info(f"  Saved {entry_id}: {len(ohlcv)} bars, {stats['gain_pct']}% gain")
        else:
            entry['ohlcv_file'] = None
            logger.info(f"  No data for {entry_id}")

    # Write updated index
    INDEX_PATH.write_text(json.dumps(entries, indent=2))
    logger.info(f"Done. Updated {updated}/{len(entries)} entries.")


if __name__ == '__main__':
    main()
```

**Step 2: Run the script**

```bash
cd /path/to/AI-Trading-System
python -m pipeline.tools.fetch_model_book_ohlcv
```

Expected: OHLCV JSON files in `frontend/public/data/modelbooks/ohlcv/`, updated `index.json` with `ohlcv_file`, `gain_pct`, `duration_days`.

**Step 3: Commit**

```bash
git add pipeline/tools/fetch_model_book_ohlcv.py frontend/public/data/modelbooks/
git commit -m "feat(pipeline): add OHLCV fetcher for model book entries"
```

---

## Task 2: Frontend — Reusable OHLCV Chart Component

**Files:**
- Create: `frontend/src/components/modelbooks/OhlcvChart.jsx`

**Context:** The breadth page uses lightweight-charts `LineSeries` (see `BreadthCharts.jsx:40-91`). We need a `CandlestickSeries` chart with configurable MA overlays. This component will be reused in both the browse view and detail modal.

**Step 1: Create the OhlcvChart component**

```jsx
// frontend/src/components/modelbooks/OhlcvChart.jsx
import { useRef, useEffect } from 'react'
import { createChart, ColorType, CandlestickSeries, LineSeries } from 'lightweight-charts'

const MA_CONFIGS = [
  { period: 21, color: '#3b82f6', label: '21 EMA', type: 'ema' },
  { period: 50, color: '#f59e0b', label: '50 SMA', type: 'sma' },
  { period: 200, color: '#a8a29e', label: '200 SMA', type: 'sma' },
]

function computeMA(data, period, type) {
  const closes = data.map(d => d.close)
  const result = []

  if (type === 'sma') {
    for (let i = 0; i < closes.length; i++) {
      if (i < period - 1) continue
      const slice = closes.slice(i - period + 1, i + 1)
      const avg = slice.reduce((a, b) => a + b, 0) / period
      result.push({ time: data[i].time, value: Math.round(avg * 100) / 100 })
    }
  } else {
    // EMA
    const k = 2 / (period + 1)
    let ema = null
    for (let i = 0; i < closes.length; i++) {
      if (ema === null) {
        if (i < period - 1) continue
        ema = closes.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period
      } else {
        ema = closes[i] * k + ema * (1 - k)
      }
      result.push({ time: data[i].time, value: Math.round(ema * 100) / 100 })
    }
  }
  return result
}

export default function OhlcvChart({ data, height = 350, showMAs = true, spyData = null }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !data?.length) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const w = containerRef.current.clientWidth
    const isDark = document.documentElement.classList.contains('dark')

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: isDark ? '#1c1917' : '#ffffff' },
        textColor: isDark ? '#a8a29e' : '#78716c',
        fontSize: 10,
      },
      grid: {
        vertLines: { color: isDark ? '#292524' : '#f5f5f4' },
        horzLines: { color: isDark ? '#292524' : '#f5f5f4' },
      },
      width: w,
      height,
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
      crosshair: { horzLine: { visible: true, labelVisible: true } },
    })

    // Candlestick series
    const candlestick = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })
    candlestick.setData(data)

    // Moving averages
    if (showMAs) {
      for (const ma of MA_CONFIGS) {
        if (data.length < ma.period) continue
        const maData = computeMA(data, ma.period, ma.type)
        const series = chart.addSeries(LineSeries, {
          color: ma.color,
          lineWidth: 1,
          crosshairMarkerVisible: false,
          priceLineVisible: false,
          lastValueVisible: false,
        })
        series.setData(maData)
      }
    }

    chart.timeScale().fitContent()
    chartRef.current = chart

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
      }
    }
  }, [data, height, showMAs, spyData])

  if (!data?.length) {
    return (
      <div className="flex items-center justify-center bg-[var(--color-surface-raised)] rounded"
           style={{ height }}>
        <span className="text-xs text-[var(--color-text-muted)]">No chart data</span>
      </div>
    )
  }

  return <div ref={containerRef} />
}
```

**Step 2: Verify it renders**

Open the app, import the component in the console or a test page, confirm candlestick + MA lines render correctly.

**Step 3: Commit**

```bash
git add frontend/src/components/modelbooks/OhlcvChart.jsx
git commit -m "feat(modelbooks): add reusable OHLCV candlestick chart component"
```

---

## Task 3: Frontend — Two-Panel Layout (Table + Chart)

**Files:**
- Modify: `frontend/src/components/modelbooks/BrowseView.jsx` (major rewrite)

**Context:** Replace the card grid with a Big Movers-style two-panel layout: sortable table on the left listing all entries, interactive chart on the right showing the selected entry. Follow the ResultsTable pattern from `screener/ResultsTable.jsx` for sorting.

**Step 1: Rewrite BrowseView to two-panel layout**

The new layout:
- **Left panel (40% width):** Compact table with columns: Ticker, Year, Pattern(s), Gain%, Duration, Source
- **Right panel (60% width):** OhlcvChart + entry details (key lessons, outcome)
- Click a table row → loads OHLCV JSON → renders chart
- Table header click → sorts by that column

```jsx
// frontend/src/components/modelbooks/BrowseView.jsx
import { useState, useMemo, useEffect } from 'react'
import OhlcvChart from './OhlcvChart'

const PATTERN_COLORS = {
  cup_with_handle: 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  flat_base: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300',
  vcp: 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300',
  high_tight_flag: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  pocket_pivot: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300',
  episodic_pivot: 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300',
  range_breakout: 'bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300',
  base_on_base: 'bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300',
  double_bottom: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300',
  ipo_base: 'bg-lime-50 text-lime-700 dark:bg-lime-950 dark:text-lime-300',
  faulty_base: 'bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400',
  cup_without_handle: 'bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-300',
}

function formatPattern(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function PatternBadge({ pattern }) {
  const colors = PATTERN_COLORS[pattern] || 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
  return (
    <span className={`inline-block px-1.5 py-0.5 text-[9px] font-medium rounded-full ${colors}`}>
      {formatPattern(pattern)}
    </span>
  )
}

const COLUMNS = [
  { key: 'ticker', label: 'Ticker' },
  { key: 'year', label: 'Year' },
  { key: 'gain_pct', label: 'Gain %' },
  { key: 'duration_days', label: 'Days' },
  { key: 'source', label: 'Source' },
]

export default function BrowseView({ cards }) {
  const [selected, setSelected] = useState(null)
  const [ohlcv, setOhlcv] = useState(null)
  const [loadingChart, setLoadingChart] = useState(false)
  const [sortKey, setSortKey] = useState('year')
  const [sortDir, setSortDir] = useState('desc')
  const [patternFilter, setPatternFilter] = useState('all')
  const [search, setSearch] = useState('')

  // Derive unique patterns
  const allPatterns = useMemo(() => {
    const set = new Set()
    cards.forEach(c => c.patterns.forEach(p => set.add(p)))
    return [...set].sort()
  }, [cards])

  // Filter
  const filtered = useMemo(() => {
    return cards.filter(card => {
      if (patternFilter !== 'all' && !card.patterns.includes(patternFilter)) return false
      if (search) {
        const q = search.toLowerCase()
        const matchesTicker = card.ticker.toLowerCase().includes(q)
        const matchesLessons = card.key_lessons?.some(l => l.toLowerCase().includes(q))
        const matchesOutcome = card.outcome?.toLowerCase().includes(q)
        if (!matchesTicker && !matchesLessons && !matchesOutcome) return false
      }
      return true
    })
  }, [cards, patternFilter, search])

  // Sort
  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      let av = a[sortKey], bv = b[sortKey]
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === 'string') {
        return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
      }
      return sortDir === 'asc' ? av - bv : bv - av
    })
  }, [filtered, sortKey, sortDir])

  // Load OHLCV when selected changes
  useEffect(() => {
    if (!selected?.ohlcv_file) {
      setOhlcv(null)
      return
    }
    setLoadingChart(true)
    fetch(`/data/modelbooks/${selected.ohlcv_file}`)
      .then(r => r.json())
      .then(data => { setOhlcv(data); setLoadingChart(false) })
      .catch(() => { setOhlcv(null); setLoadingChart(false) })
  }, [selected])

  // Auto-select first entry
  useEffect(() => {
    if (sorted.length > 0 && !selected) {
      setSelected(sorted[0])
    }
  }, [sorted])

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  return (
    <div className="flex flex-col lg:flex-row gap-3">
      {/* Left panel: filters + table */}
      <div className="lg:w-[40%] flex flex-col gap-2">
        {/* Filters */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 text-[11px] text-[var(--color-text)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
          />
          <select
            value={patternFilter}
            onChange={e => setPatternFilter(e.target.value)}
            className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-2 py-1.5 cursor-pointer focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
          >
            <option value="all">All Patterns</option>
            {allPatterns.map(p => (
              <option key={p} value={p}>{formatPattern(p)}</option>
            ))}
          </select>
        </div>

        <span className="text-[10px] text-[var(--color-text-muted)]">
          {filtered.length} result{filtered.length !== 1 ? 's' : ''}
        </span>

        {/* Table */}
        <div className="overflow-y-auto max-h-[calc(100vh-220px)] border border-[var(--color-border)] rounded">
          <table className="w-full text-[11px]">
            <thead className="sticky top-0 bg-[var(--color-surface-alt)]">
              <tr>
                {COLUMNS.map(col => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    className="px-2 py-1.5 text-left font-medium text-[var(--color-text-secondary)] cursor-pointer hover:text-[var(--color-text)] select-none"
                  >
                    {col.label}
                    {sortKey === col.key && (
                      <span className="ml-0.5">{sortDir === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map(card => (
                <tr
                  key={card.id}
                  onClick={() => setSelected(card)}
                  className={`cursor-pointer transition-colors ${
                    selected?.id === card.id
                      ? 'bg-[var(--color-active-tab-bg)]'
                      : 'hover:bg-[var(--color-hover-bg)]'
                  }`}
                >
                  <td className="px-2 py-1.5 font-semibold text-[var(--color-text)]">
                    {card.ticker}
                  </td>
                  <td className="px-2 py-1.5 text-[var(--color-text-secondary)]">
                    {card.year}
                  </td>
                  <td className="px-2 py-1.5 text-[var(--color-text)]">
                    {card.gain_pct != null ? `${card.gain_pct}%` : '—'}
                  </td>
                  <td className="px-2 py-1.5 text-[var(--color-text-secondary)]">
                    {card.duration_days ?? '—'}
                  </td>
                  <td className="px-2 py-1.5 text-[var(--color-text-muted)]">
                    {card.source}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Right panel: chart + details */}
      <div className="lg:w-[60%] flex flex-col gap-3">
        {selected ? (
          <>
            {/* Chart header */}
            <div className="flex items-baseline justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-[var(--color-text-bold)]">
                  {selected.ticker}
                </span>
                <span className="text-xs text-[var(--color-text-muted)]">{selected.year}</span>
              </div>
              <div className="flex gap-1.5">
                {selected.patterns.map(p => (
                  <PatternBadge key={p} pattern={p} />
                ))}
              </div>
            </div>

            {/* Chart */}
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded p-2">
              {loadingChart ? (
                <div className="flex items-center justify-center h-[350px]">
                  <span className="text-xs text-[var(--color-text-muted)] animate-pulse">
                    Loading chart...
                  </span>
                </div>
              ) : (
                <OhlcvChart data={ohlcv} height={350} />
              )}
            </div>

            {/* Details */}
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded p-4 space-y-3">
              <div className="flex items-center gap-4 text-xs">
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">
                    Gain
                  </span>
                  <span className="font-semibold text-[var(--color-text)]">
                    {selected.gain_pct != null ? `${selected.gain_pct}%` : '—'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">
                    Duration
                  </span>
                  <span className="text-[var(--color-text)]">
                    {selected.duration_days != null ? `${selected.duration_days} days` : '—'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">
                    Source
                  </span>
                  <span className="text-[var(--color-text)]">{selected.source}</span>
                </div>
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">
                    Outcome
                  </span>
                  <span className="font-medium text-[var(--color-text)]">{selected.outcome}</span>
                </div>
              </div>

              <div>
                <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1.5">
                  Key Lessons
                </span>
                <ul className="space-y-1">
                  {selected.key_lessons.map((lesson, i) => (
                    <li key={i} className="text-xs text-[var(--color-text-secondary)] flex gap-2">
                      <span className="text-[var(--color-text-muted)] select-none shrink-0">•</span>
                      {lesson}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-64 rounded-lg border border-dashed border-[var(--color-border)]">
            <span className="text-xs text-[var(--color-text-muted)]">Select an entry to view chart</span>
          </div>
        )}
      </div>
    </div>
  )
}
```

**Step 2: Verify the two-panel layout renders**

Run `npm run dev` in the frontend directory, navigate to `#/modelbooks`, confirm:
- Table shows all entries with sorting
- Clicking a row loads the chart
- MAs render on the candlestick chart
- Responsive: stacks vertically on mobile

**Step 3: Commit**

```bash
git add frontend/src/components/modelbooks/BrowseView.jsx
git commit -m "feat(modelbooks): two-panel layout with sortable table + interactive chart"
```

---

## Task 4: Frontend — Per-Tag Performance Stats Panel

**Files:**
- Create: `frontend/src/components/modelbooks/TagStats.jsx`
- Modify: `frontend/src/components/modelbooks/ModelBooksPage.jsx` (add stats tab)

**Context:** Like Koblich Chronicles' tag-based performance tracking: for each pattern tag, show win rate, avg gain %, avg duration, count. This uses the enriched `index.json` data (after Task 1).

**Step 1: Create TagStats component**

```jsx
// frontend/src/components/modelbooks/TagStats.jsx
import { useMemo } from 'react'

const PATTERN_COLORS = {
  cup_with_handle: 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  flat_base: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300',
  vcp: 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300',
  high_tight_flag: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  pocket_pivot: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300',
  episodic_pivot: 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300',
  range_breakout: 'bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300',
  base_on_base: 'bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300',
  double_bottom: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300',
  ipo_base: 'bg-lime-50 text-lime-700 dark:bg-lime-950 dark:text-lime-300',
  faulty_base: 'bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400',
  cup_without_handle: 'bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-300',
}

function formatPattern(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function TagStats({ cards }) {
  const stats = useMemo(() => {
    const byPattern = {}
    for (const card of cards) {
      for (const p of card.patterns) {
        if (!byPattern[p]) byPattern[p] = []
        byPattern[p].push(card)
      }
    }

    return Object.entries(byPattern)
      .map(([pattern, entries]) => {
        const withGain = entries.filter(e => e.gain_pct != null)
        const avgGain = withGain.length
          ? Math.round(withGain.reduce((s, e) => s + e.gain_pct, 0) / withGain.length)
          : null
        const withDuration = entries.filter(e => e.duration_days != null)
        const avgDuration = withDuration.length
          ? Math.round(withDuration.reduce((s, e) => s + e.duration_days, 0) / withDuration.length)
          : null

        return { pattern, count: entries.length, avgGain, avgDuration }
      })
      .sort((a, b) => b.count - a.count)
  }, [cards])

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {stats.map(({ pattern, count, avgGain, avgDuration }) => {
          const colors = PATTERN_COLORS[pattern] || 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
          return (
            <div key={pattern} className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 space-y-2">
              <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded-full ${colors}`}>
                {formatPattern(pattern)}
              </span>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-sm font-semibold text-[var(--color-text)]">{count}</div>
                  <div className="text-[9px] text-[var(--color-text-muted)] uppercase">Setups</div>
                </div>
                <div>
                  <div className="text-sm font-semibold text-[var(--color-text)]">
                    {avgGain != null ? `${avgGain}%` : '—'}
                  </div>
                  <div className="text-[9px] text-[var(--color-text-muted)] uppercase">Avg Gain</div>
                </div>
                <div>
                  <div className="text-sm font-semibold text-[var(--color-text)]">
                    {avgDuration != null ? `${avgDuration}d` : '—'}
                  </div>
                  <div className="text-[9px] text-[var(--color-text-muted)] uppercase">Avg Days</div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

**Step 2: Add "Stats" tab to ModelBooksPage**

In `ModelBooksPage.jsx`, add a third mode `'stats'` alongside `'browse'` and `'study'`:

```jsx
// In the mode toggle buttons array, add 'stats'
// And render:
{mode === 'stats' && <TagStats cards={cards} />}
```

Import: `import TagStats from './TagStats'`

**Step 3: Verify stats render**

Navigate to `#/modelbooks`, click "Stats" tab. Confirm pattern cards show count, avg gain, avg duration.

**Step 4: Commit**

```bash
git add frontend/src/components/modelbooks/TagStats.jsx frontend/src/components/modelbooks/ModelBooksPage.jsx
git commit -m "feat(modelbooks): add per-pattern performance stats panel"
```

---

## Task 5: Frontend — SPY Overlay on Chart

**Files:**
- Modify: `frontend/src/components/modelbooks/OhlcvChart.jsx`
- Modify: `frontend/src/components/modelbooks/BrowseView.jsx`

**Context:** Add a toggle to overlay SPY price on the chart for comparison. Fetch SPY OHLCV for the same date range as the selected entry. Use a second price scale (right side) for SPY to handle different price ranges.

**Step 1: Add SPY data fetching in BrowseView**

When an entry is selected and its OHLCV is loaded, also fetch SPY for the same date range:

```jsx
// In BrowseView.jsx, alongside the ohlcv fetch:
const [spyData, setSpyData] = useState(null)
const [showSpy, setShowSpy] = useState(false)

// Fetch SPY for same date range when ohlcv loads
useEffect(() => {
  if (!ohlcv?.length || !showSpy) { setSpyData(null); return }
  const startDate = ohlcv[0].time
  const endDate = ohlcv[ohlcv.length - 1].time
  // Use pre-fetched SPY OHLCV (pipeline should generate spy.json)
  fetch(`/data/modelbooks/ohlcv/spy-${selected.year}.json`)
    .then(r => r.json())
    .then(data => {
      // Filter to same date range
      const filtered = data.filter(d => d.time >= startDate && d.time <= endDate)
      setSpyData(filtered)
    })
    .catch(() => setSpyData(null))
}, [ohlcv, showSpy, selected])
```

Add a toggle button next to the chart header:
```jsx
<button onClick={() => setShowSpy(s => !s)}
  className={`text-[10px] px-2 py-1 rounded ${showSpy ? 'bg-blue-50 text-blue-700' : 'text-[var(--color-text-muted)]'}`}>
  SPY Overlay
</button>
```

**Step 2: Update OhlcvChart to render SPY line**

Add SPY as a `LineSeries` on a separate right price scale:

```jsx
// In OhlcvChart.jsx, after candlestick series:
if (spyData?.length) {
  // Normalize SPY to percentage change from first bar
  const spyBase = spyData[0].close
  const normalizedSpy = spyData.map(d => ({
    time: d.time,
    value: ((d.close / spyBase) - 1) * 100,
  }))

  const spySeries = chart.addSeries(LineSeries, {
    color: '#6366f1',
    lineWidth: 1.5,
    lineStyle: 2, // dashed
    priceScaleId: 'spy',
    lastValueVisible: true,
    priceLineVisible: false,
    title: 'SPY %',
  })
  spySeries.setData(normalizedSpy)

  chart.priceScale('spy').applyOptions({
    scaleMargins: { top: 0.7, bottom: 0 },
    borderVisible: false,
  })
}
```

**Step 3: Update pipeline to also fetch SPY OHLCV**

Add to `fetch_model_book_ohlcv.py`: for each unique year in the index, fetch SPY OHLCV and save as `spy-{year}.json`.

**Step 4: Verify SPY overlay**

Toggle SPY overlay on, confirm dashed indigo line appears with its own scale.

**Step 5: Commit**

```bash
git add frontend/src/components/modelbooks/OhlcvChart.jsx frontend/src/components/modelbooks/BrowseView.jsx pipeline/tools/fetch_model_book_ohlcv.py
git commit -m "feat(modelbooks): add SPY overlay comparison on charts"
```

---

## Task 6: Expand Model Book Entries with Real Curated Data

**Files:**
- Modify: `frontend/public/data/modelbooks/index.json`

**Context:** The current index has only 10 entries. Expand to ~50 curated entries covering the major Qullamaggie/O'Neil/Minervini setups from various eras. Each entry needs: ticker, year, patterns, key_lessons, outcome, source.

**Step 1: Curate entries**

Add entries for well-known setups like:
- AAPL 2004 (cup with handle), GOOG 2004 (IPO base), NFLX 2013 (VCP + flat base)
- NVDA 2016, 2023 (multiple bases), AMD 2019 (cup with handle)
- Classic O'Neil: MSFT 1986, CSCO 1990, DELL 1996, YHOO 1998
- Minervini: SWKS 2013, CELG 2013, FB 2013
- Modern: TSLA 2020, ENPH 2019, DDOG 2020, NET 2020

Structure each as:
```json
{
  "id": "lastname-ticker-year",
  "ticker": "NVDA",
  "year": 2016,
  "source": "Qullamaggie",
  "patterns": ["vcp", "flat_base"],
  "key_lessons": ["3 contractions before breakout", "Volume dried up in right side of base"],
  "outcome": "150% move in 8 months",
  "image": null
}
```

**Step 2: Run OHLCV fetcher**

```bash
python -m pipeline.tools.fetch_model_book_ohlcv
```

**Step 3: Commit**

```bash
git add frontend/public/data/modelbooks/
git commit -m "feat(modelbooks): expand to 50 curated historical setups"
```

---

## Task 7: Mobile Responsive + Polish

**Files:**
- Modify: `frontend/src/components/modelbooks/BrowseView.jsx`
- Modify: `frontend/src/components/modelbooks/StudyMode.jsx`

**Context:** The two-panel layout needs to stack on mobile. Study mode should show the chart instead of just the ticker text placeholder.

**Step 1: Mobile responsiveness for BrowseView**

The `flex-col lg:flex-row` is already in the plan (Task 3), but verify:
- On mobile: table full-width on top, chart below
- Table gets horizontal scroll if needed
- Chart height reduces to 250px on mobile

**Step 2: Update StudyMode with interactive charts**

Replace the ticker placeholder in StudyMode with `OhlcvChart`:
- Before reveal: show chart without ticker label (mystery mode)
- After reveal: show chart with MAs and ticker label

```jsx
// In StudyMode.jsx, replace the chart placeholder div with:
import OhlcvChart from './OhlcvChart'

// Fetch OHLCV when card changes
const [ohlcv, setOhlcv] = useState(null)
useEffect(() => {
  if (!card?.ohlcv_file) { setOhlcv(null); return }
  fetch(`/data/modelbooks/${card.ohlcv_file}`)
    .then(r => r.json())
    .then(setOhlcv)
    .catch(() => setOhlcv(null))
}, [card])

// Render chart (hide MAs before reveal for harder guessing)
<OhlcvChart data={ohlcv} height={220} showMAs={revealed} />
```

**Step 3: Commit**

```bash
git add frontend/src/components/modelbooks/BrowseView.jsx frontend/src/components/modelbooks/StudyMode.jsx
git commit -m "feat(modelbooks): mobile responsive layout + interactive study mode charts"
```

---

## Dependency Graph

```
Task 1 (Pipeline OHLCV) ──→ Task 2 (Chart Component) ──→ Task 3 (Two-Panel Layout)
                         ──→ Task 4 (Tag Stats)
                         ──→ Task 5 (SPY Overlay) ──→ depends on Task 2 + 3
                         ──→ Task 6 (Expand Data) ──→ depends on Task 1
                                                   ──→ Task 7 (Polish) ──→ depends on Task 3
```

**Parallelizable:** Tasks 2 + 4 can run in parallel after Task 1. Task 6 can run anytime after Task 1.

**Critical path:** Task 1 → Task 2 → Task 3 → Task 5 → Task 7
