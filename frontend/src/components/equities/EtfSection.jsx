import { useState, useMemo } from 'react'
import EtfRow from '../shared/EtfRow'

const COLUMNS = [
  { key: 'abc', label: 'ABC', sortable: true },
  { key: 'ticker', label: 'TICKER', sortable: true },
  { key: 'change_pct', label: '1D', sortable: true },
  { key: 'perf_1w', label: '5D', sortable: true },
  { key: 'perf_1m', label: '20D', sortable: true },
  { key: 'dist_sma50_atr', label: 'ATR', sortable: true },
  { key: 'rs', label: 'RS', sortable: true },
  { key: 'sparkline', label: 'CHART', sortable: false },
]

function compareFn(a, b, key) {
  const aVal = a[key]
  const bVal = b[key]
  if (aVal == null && bVal == null) return 0
  if (aVal == null) return 1
  if (bVal == null) return -1
  if (typeof aVal === 'string') return aVal.localeCompare(bVal)
  return aVal - bVal
}

export default function EtfSection({ title, etfs, defaultSort = 'perf_1w' }) {
  const [sortKey, setSortKey] = useState(defaultSort)
  const [sortDir, setSortDir] = useState('desc')

  const sorted = useMemo(() => {
    if (!etfs) return []
    return [...etfs].sort((a, b) => {
      const result = compareFn(a, b, sortKey)
      return sortDir === 'desc' ? -result : result
    })
  }, [etfs, sortKey, sortDir])

  const handleSort = (key, sortable) => {
    if (!sortable) return
    if (sortKey === key) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  if (!etfs || etfs.length === 0) return null

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded overflow-x-auto">
      {/* Section title */}
      <div className="px-3 py-1.5 border-b border-[var(--color-border)]">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          {title}
        </span>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-[1.5rem_3.5rem_3.5rem_3.5rem_3.5rem_3rem_3rem_4rem] items-center px-2 py-1 border-b border-[var(--color-border)] bg-[var(--color-surface-alt)]/50">
        {COLUMNS.map((col) => (
          <span
            key={col.key}
            onClick={() => handleSort(col.key, col.sortable)}
            className={`text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] ${
              col.sortable ? 'cursor-pointer select-none hover:text-[var(--color-text-secondary)]' : ''
            } ${sortKey === col.key ? 'text-[var(--color-text-secondary)]' : ''}`}
          >
            {col.label}
            {sortKey === col.key && (
              <span className="ml-0.5">{sortDir === 'desc' ? '\u2193' : '\u2191'}</span>
            )}
          </span>
        ))}
      </div>

      {/* Rows */}
      {sorted.map((etf) => (
        <EtfRow key={etf.ticker} etf={etf} />
      ))}
    </div>
  )
}
