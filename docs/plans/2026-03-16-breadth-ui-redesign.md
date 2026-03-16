# Breadth Page UI Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the card-based Breadth page with a dense Stockbee-style historical data table + charts, using the project's anti-dopamine palette for conditional cell coloring.

**Architecture:** The pipeline's `breadth_metrics.py` already stores full daily snapshots in rolling history. We change the `breadth.json` output to include complete row objects (not just chart arrays). A new `BreadthTable.jsx` component renders rows as a dense, horizontally-scrollable table with conditional cell backgrounds. Charts remain below.

**Tech Stack:** React 19 / Tailwind 4 (frontend only — no pipeline logic changes, just output reshaping)

---

## Task 1: Update pipeline to include full history rows in breadth.json

**Files:**
- Modify: `pipeline/screeners/breadth_metrics.py:319-327`

**Step 1: Add `rows` array to history output**

In `pipeline/screeners/breadth_metrics.py`, replace the `history_arrays` block (lines 319-327) and the return statement's `'history'` key to include both the existing chart arrays AND full row objects.

Find this block in the `run()` function:

```python
    # 8. Build history arrays for charting
    all_entries = history + [today_entry]
    history_arrays = {
        'dates': [e['date'] for e in all_entries],
        'pct_above_200sma': [e.get('pct_above_200sma', 0) for e in all_entries],
        'pct_above_50sma': [e.get('pct_above_50sma', 0) for e in all_entries],
        'pct_above_20sma': [e.get('pct_above_20sma', 0) for e in all_entries],
        'mcclellan_osc': [e.get('mcclellan_osc', 0) for e in all_entries],
    }
```

Replace with:

```python
    # 8. Build history for frontend (chart arrays + full rows for table)
    all_entries = history + [today_entry]
    history_output = {
        # Chart arrays (used by BreadthCharts.jsx)
        'dates': [e['date'] for e in all_entries],
        'pct_above_200sma': [e.get('pct_above_200sma', 0) for e in all_entries],
        'pct_above_50sma': [e.get('pct_above_50sma', 0) for e in all_entries],
        'pct_above_20sma': [e.get('pct_above_20sma', 0) for e in all_entries],
        'mcclellan_osc': [e.get('mcclellan_osc', 0) for e in all_entries],
        # Full rows (used by BreadthTable.jsx)
        'rows': all_entries,
    }
```

Then update the return statement to use `history_output` instead of `history_arrays`:

Find:
```python
        'history': history_arrays,
```

Replace with:
```python
        'history': history_output,
```

**Step 2: Run tests**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python3 -m pytest pipeline/tests/test_breadth_metrics.py -v`
Expected: All PASS (no tests depend on the history output shape)

**Step 3: Commit**

```bash
git add pipeline/screeners/breadth_metrics.py
git commit -m "feat: include full history rows in breadth.json for table rendering"
```

---

## Task 2: Update sample breadth.json with multi-day history rows

**Files:**
- Modify: `data/output/breadth.json`

**Step 1: Replace sample data**

Replace the entire contents of `data/output/breadth.json` with realistic multi-day sample data (5 days) so the table has rows to render during development:

```json
{
  "timestamp": "2026-03-16T00:00:00Z",
  "universe_size": 2485,
  "spx_close": 5632.19,
  "mm": {
    "up_4pct": 124,
    "down_4pct": 284,
    "ratio_5d": 0.79,
    "ratio_10d": 0.80,
    "up_25pct_qtr": 966,
    "down_25pct_qtr": 1385,
    "up_25pct_month": 131,
    "down_25pct_month": 173,
    "up_50pct_month": 24,
    "down_50pct_month": 25
  },
  "breadth": {
    "t2108": 39.8,
    "pct_above_200sma": 46.4,
    "pct_above_50sma": 34.5,
    "pct_above_20sma": 38.2,
    "advances": 1153,
    "declines": 2379,
    "new_highs": 34,
    "new_lows": 89,
    "ad_line": -1226,
    "mcclellan_osc": -45.2
  },
  "history": {
    "dates": ["2026-03-10", "2026-03-11", "2026-03-12", "2026-03-13", "2026-03-16"],
    "pct_above_200sma": [54.2, 55.6, 48.3, 46.4, 46.4],
    "pct_above_50sma": [40.1, 42.3, 36.8, 34.5, 34.5],
    "pct_above_20sma": [45.3, 47.1, 40.2, 38.2, 38.2],
    "mcclellan_osc": [-12.5, -8.3, -28.7, -45.2, -45.2],
    "rows": [
      {
        "date": "2026-03-10",
        "universe_size": 2485,
        "up_4pct": 244, "down_4pct": 173,
        "ratio_5d": 1.11, "ratio_10d": 1.09,
        "up_25pct_qtr": 1107, "down_25pct_qtr": 1194,
        "up_25pct_month": 129, "down_25pct_month": 164,
        "up_50pct_month": 31, "down_50pct_month": 22,
        "t2108": 54.2, "pct_above_200sma": 54.2, "pct_above_50sma": 40.1, "pct_above_20sma": 45.3,
        "advances": 1350, "declines": 1978, "new_highs": 42, "new_lows": 55,
        "net_advances": -628, "ad_line": -628, "mcclellan_osc": -12.5
      },
      {
        "date": "2026-03-11",
        "universe_size": 2485,
        "up_4pct": 223, "down_4pct": 156,
        "ratio_5d": 0.92, "ratio_10d": 1.01,
        "up_25pct_qtr": 1128, "down_25pct_qtr": 1199,
        "up_25pct_month": 117, "down_25pct_month": 173,
        "up_50pct_month": 33, "down_50pct_month": 21,
        "t2108": 55.6, "pct_above_200sma": 55.6, "pct_above_50sma": 42.3, "pct_above_20sma": 47.1,
        "advances": 1383, "declines": 2056, "new_highs": 38, "new_lows": 67,
        "net_advances": -673, "ad_line": -1301, "mcclellan_osc": -8.3
      },
      {
        "date": "2026-03-12",
        "universe_size": 2485,
        "up_4pct": 152, "down_4pct": 635,
        "ratio_5d": 0.74, "ratio_10d": 0.78,
        "up_25pct_qtr": 1023, "down_25pct_qtr": 1329,
        "up_25pct_month": 112, "down_25pct_month": 208,
        "up_50pct_month": 25, "down_50pct_month": 25,
        "t2108": 48.3, "pct_above_200sma": 48.3, "pct_above_50sma": 36.8, "pct_above_20sma": 40.2,
        "advances": 1226, "declines": 2289, "new_highs": 30, "new_lows": 78,
        "net_advances": -1063, "ad_line": -2364, "mcclellan_osc": -28.7
      },
      {
        "date": "2026-03-13",
        "universe_size": 2485,
        "up_4pct": 124, "down_4pct": 284,
        "ratio_5d": 0.79, "ratio_10d": 0.80,
        "up_25pct_qtr": 966, "down_25pct_qtr": 1385,
        "up_25pct_month": 131, "down_25pct_month": 173,
        "up_50pct_month": 24, "down_50pct_month": 25,
        "t2108": 46.4, "pct_above_200sma": 46.4, "pct_above_50sma": 34.5, "pct_above_20sma": 38.2,
        "advances": 1153, "declines": 2379, "new_highs": 34, "new_lows": 89,
        "net_advances": -1226, "ad_line": -3590, "mcclellan_osc": -45.2
      },
      {
        "date": "2026-03-16",
        "universe_size": 2485,
        "up_4pct": 124, "down_4pct": 284,
        "ratio_5d": 0.79, "ratio_10d": 0.80,
        "up_25pct_qtr": 966, "down_25pct_qtr": 1385,
        "up_25pct_month": 131, "down_25pct_month": 173,
        "up_50pct_month": 24, "down_50pct_month": 25,
        "t2108": 39.8, "pct_above_200sma": 46.4, "pct_above_50sma": 34.5, "pct_above_20sma": 38.2,
        "advances": 1153, "declines": 2379, "new_highs": 34, "new_lows": 89,
        "net_advances": -1226, "ad_line": -4816, "mcclellan_osc": -45.2
      }
    ]
  }
}
```

**Step 2: Verify JSON is valid**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python3 -c "import json; json.load(open('data/output/breadth.json')); print('Valid JSON')"`
Expected: `Valid JSON`

**Step 3: Commit**

```bash
git add data/output/breadth.json
git commit -m "chore: update sample breadth.json with multi-day history rows for table"
```

---

## Task 3: Create BreadthTable component

**Files:**
- Create: `frontend/src/components/breadth/BreadthTable.jsx`

**Step 1: Create the component**

Create `frontend/src/components/breadth/BreadthTable.jsx`:

```jsx
export default function BreadthTable({ data }) {
  const rows = data?.history?.rows
  if (!rows?.length) return null

  // Reverse so newest date is first
  const sorted = [...rows].reverse()

  return (
    <div className="bg-white border border-stone-200 rounded overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-stone-200 bg-stone-50">
              <Th>Date</Th>
              <Th>Up 4%</Th>
              <Th>Dn 4%</Th>
              <Th>5D Ratio</Th>
              <Th>10D Ratio</Th>
              <ThSep />
              <Th>Up 25% Qtr</Th>
              <Th>Dn 25% Qtr</Th>
              <Th>Up 25% Mo</Th>
              <Th>Dn 25% Mo</Th>
              <Th>Up 50% Mo</Th>
              <Th>Dn 50% Mo</Th>
              <ThSep />
              <Th>T2108</Th>
              <Th>% &gt; 200</Th>
              <Th>% &gt; 50</Th>
              <Th>% &gt; 20</Th>
              <ThSep />
              <Th>Adv</Th>
              <Th>Dec</Th>
              <Th>NH</Th>
              <Th>NL</Th>
              <Th>McCl</Th>
              <ThSep />
              <Th>SPX</Th>
              <Th>Worden</Th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr
                key={row.date}
                className={`border-b border-stone-100 hover:bg-stone-50 ${
                  i === 0 ? 'bg-stone-50/50 font-medium' : ''
                }`}
              >
                <Td className="text-stone-600 whitespace-nowrap">{fmtDate(row.date)}</Td>
                <Td>{row.up_4pct}</Td>
                <Td>{row.down_4pct}</Td>
                <Td className={ratioColor(row.ratio_5d)}>{row.ratio_5d?.toFixed(2)}</Td>
                <Td className={ratioColor(row.ratio_10d)}>{row.ratio_10d?.toFixed(2)}</Td>
                <TdSep />
                <Td>{row.up_25pct_qtr}</Td>
                <Td>{row.down_25pct_qtr}</Td>
                <Td>{row.up_25pct_month}</Td>
                <Td>{row.down_25pct_month}</Td>
                <Td>{row.up_50pct_month}</Td>
                <Td>{row.down_50pct_month}</Td>
                <TdSep />
                <Td className={pctAboveColor(row.t2108)}>{row.t2108?.toFixed(1)}</Td>
                <Td className={pctAboveColor(row.pct_above_200sma)}>{row.pct_above_200sma?.toFixed(1)}</Td>
                <Td className={pctAboveColor(row.pct_above_50sma)}>{row.pct_above_50sma?.toFixed(1)}</Td>
                <Td className={pctAboveColor(row.pct_above_20sma)}>{row.pct_above_20sma?.toFixed(1)}</Td>
                <TdSep />
                <Td>{row.advances}</Td>
                <Td>{row.declines}</Td>
                <Td>{row.new_highs}</Td>
                <Td>{row.new_lows}</Td>
                <Td className={mcColor(row.mcclellan_osc)}>{row.mcclellan_osc?.toFixed(1)}</Td>
                <TdSep />
                <Td>{row.spx_close?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '\u2014'}</Td>
                <Td>{row.universe_size?.toLocaleString()}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Helpers ──────────────────────────────────────────────

function Th({ children }) {
  return (
    <th className="px-2 py-1.5 text-right text-[10px] font-medium uppercase tracking-wide text-stone-500 whitespace-nowrap">
      {children}
    </th>
  )
}

function ThSep() {
  return <th className="w-px px-0 bg-stone-200" />
}

function Td({ children, className = '' }) {
  return (
    <td className={`px-2 py-1 text-right font-mono text-[11px] ${className}`}>
      {children ?? '\u2014'}
    </td>
  )
}

function TdSep() {
  return <td className="w-px px-0 bg-stone-100" />
}

function fmtDate(iso) {
  if (!iso) return '\u2014'
  const [, m, d] = iso.split('-')
  return `${parseInt(m)}/${parseInt(d)}`
}

function ratioColor(val) {
  if (val == null) return ''
  if (val >= 1.0) return 'bg-green-50 text-green-700'
  if (val >= 0.5) return 'bg-amber-50 text-amber-700'
  return 'bg-red-50 text-red-600'
}

function pctAboveColor(val) {
  if (val == null) return ''
  if (val >= 60) return 'bg-green-50 text-green-700'
  if (val >= 40) return 'bg-amber-50 text-amber-700'
  return 'bg-red-50 text-red-600'
}

function mcColor(val) {
  if (val == null) return ''
  return val >= 0 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'
}
```

**Step 2: Verify build**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/breadth/BreadthTable.jsx
git commit -m "feat: add BreadthTable component with Stockbee-style dense data table"
```

---

## Task 4: Update BreadthPage to use BreadthTable

**Files:**
- Modify: `frontend/src/components/breadth/BreadthPage.jsx`

**Step 1: Replace card components with table**

Replace the entire contents of `frontend/src/components/breadth/BreadthPage.jsx`:

```jsx
import BreadthTable from './BreadthTable'
import BreadthCharts from './BreadthCharts'

export default function BreadthPage({ data }) {
  const breadth = data?.breadth

  if (!breadth) {
    return (
      <div className="text-stone-400 text-sm font-medium uppercase tracking-wide py-8 text-center">
        No breadth data available
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <BreadthTable data={breadth} />
      <BreadthCharts data={breadth} />
    </div>
  )
}
```

**Step 2: Verify build**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds

**Step 3: Verify in browser**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run dev`
Navigate to `http://localhost:5173/#/breadth` — should see the data table with 5 rows, then charts below.

**Step 4: Commit**

```bash
git add frontend/src/components/breadth/BreadthPage.jsx
git commit -m "feat: replace breadth cards with dense data table layout"
```

---

## Task 5: Clean up unused components

**Files:**
- Delete: `frontend/src/components/breadth/MarketMonitor.jsx`
- Delete: `frontend/src/components/breadth/ClassicBreadth.jsx`

**Step 1: Remove files**

```bash
rm frontend/src/components/breadth/MarketMonitor.jsx
rm frontend/src/components/breadth/ClassicBreadth.jsx
```

**Step 2: Verify build still works**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds (BreadthPage no longer imports these)

**Step 3: Commit**

```bash
git add -u frontend/src/components/breadth/MarketMonitor.jsx frontend/src/components/breadth/ClassicBreadth.jsx
git commit -m "chore: remove unused MarketMonitor and ClassicBreadth components"
```

---

## Task 6: Final validation

**Step 1: Run all Python tests**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python3 -m pytest pipeline/tests/ -v`
Expected: All tests PASS

**Step 2: Run frontend build**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds with no errors

**Step 3: Visual verification**

Navigate to `http://localhost:5173/#/breadth` and verify:
- Dense table with date rows, conditional cell coloring
- Charts render below the table
- Table is horizontally scrollable
- Today's row is highlighted

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Add full history rows to breadth.json output | `breadth_metrics.py` |
| 2 | Update sample breadth.json with multi-day rows | `data/output/breadth.json` |
| 3 | Create BreadthTable component | `BreadthTable.jsx` |
| 4 | Update BreadthPage to use table | `BreadthPage.jsx` |
| 5 | Remove unused card components | `MarketMonitor.jsx`, `ClassicBreadth.jsx` |
| 6 | Final validation | None (verification only) |
