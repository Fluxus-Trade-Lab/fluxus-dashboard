import { useState, useMemo } from 'react'

const COLUMNS = [
  { key: 'h_score', label: 'H', type: 'rs', width: 'w-10' },
  { key: 'f_score', label: 'F', type: 'rs', width: 'w-10' },
  { key: 'i_score', label: 'I', type: 'rs', width: 'w-10' },
  { key: 'rs_21d', label: '21', type: 'rs', width: 'w-10' },
  { key: 'rs_63d', label: '63', type: 'rs', width: 'w-10' },
  { key: 'rs_126d', label: '126', type: 'rs', width: 'w-10' },
  { key: 'rs_ibd', label: 'IBD', type: 'rs', width: 'w-10' },
  { key: 'ticker', label: 'Ticker', type: 'ticker', width: 'w-16' },
  { key: 'close', label: 'Price', type: 'price', width: 'w-16' },
  { key: 'change_pct', label: 'Chg%', type: 'pct', width: 'w-14' },
  { key: 'from_open_pct', label: 'Open%', type: 'pct', width: 'w-14' },
  { key: 'perf_1w', label: '1W%', type: 'pct', width: 'w-14' },
  { key: 'perf_1m', label: '1M%', type: 'pct', width: 'w-14' },
  { key: 'adr_pct', label: 'ADR%', type: 'num2', width: 'w-14' },
  { key: 'dcr_pct', label: 'DCR%', type: 'pct100', width: 'w-14' },
  { key: 'rel_volume', label: 'RVol', type: 'num2', width: 'w-14' },
  { key: 'avg_volume', label: 'Vol 50d', type: 'vol', width: 'w-16' },
  { key: 'ema21_r', label: '21R', type: 'ratio', width: 'w-12' },
  { key: 'sma50_r', label: '50R', type: 'ratio', width: 'w-12' },
  { key: 'ema21_low_dist', label: '21Low%', type: 'pct', width: 'w-14' },
  { key: 'vcs', label: 'VCS', type: 'vcs', width: 'w-12' },
  { key: 'pp_count_30d', label: 'PP', type: 'int', width: 'w-10' },
  { key: 'high_52w_dist', label: '52W', type: 'pct', width: 'w-14' },
  { key: 'sector', label: 'Sector', type: 'text', width: 'w-24' },
]

function rsColor(val) {
  if (val == null) return 'text-[var(--color-text-muted)]'
  if (val >= 90) return 'bg-green-100 text-green-800 font-semibold'
  if (val >= 80) return 'bg-green-50 text-green-700'
  if (val >= 50) return 'text-[var(--color-text-secondary)]'
  return 'text-[var(--color-text-muted)]'
}

function pctColor(val) {
  if (val == null) return 'text-[var(--color-text-muted)]'
  if (val > 0) return 'text-green-700'
  if (val < 0) return 'text-red-600'
  return 'text-[var(--color-text-secondary)]'
}

function vcsColor(val) {
  if (val == null) return 'text-[var(--color-text-muted)]'
  if (val >= 80) return 'bg-green-100 text-green-800 font-semibold'
  if (val >= 60) return 'text-blue-700'
  return 'text-[var(--color-text-muted)]'
}

function formatCell(val, type) {
  if (val == null || val === '') return '\u2014'
  switch (type) {
    case 'rs': return Math.round(val)
    case 'pct': return `${(val * 100).toFixed(2)}%`
    case 'pct100': return `${(val * 100).toFixed(0)}%`
    case 'price': return `$${Number(val).toFixed(2)}`
    case 'num2': return Number(val).toFixed(2)
    case 'ratio': return Number(val).toFixed(2) + 'R'
    case 'vol': return val >= 1e6 ? (val / 1e6).toFixed(1) + 'M' : (val / 1e3).toFixed(0) + 'K'
    case 'vcs': return Number(val).toFixed(0)
    case 'int': return Math.round(val)
    case 'ticker': return String(val)
    default: return String(val)
  }
}

function cellClass(val, type) {
  if (type === 'rs') return rsColor(val)
  if (type === 'pct' || type === 'pct100') return pctColor(val)
  if (type === 'vcs') return vcsColor(val)
  if (type === 'ticker') return 'text-blue-700 font-semibold'
  return 'text-[var(--color-text)]'
}

export default function ResultsTable({ rows }) {
  const [sortKey, setSortKey] = useState('h_score')
  const [sortDir, setSortDir] = useState('desc')

  const sorted = useMemo(() => {
    if (!rows) return []
    return [...rows].sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
      return sortDir === 'asc' ? av - bv : bv - av
    })
  }, [rows, sortKey, sortDir])

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  return (
    <div className="overflow-x-auto border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)]">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[var(--color-border)] bg-[var(--color-bg)]">
            {COLUMNS.map(col => (
              <th
                key={col.key}
                onClick={() => toggleSort(col.key)}
                className={`px-2 py-1.5 text-left cursor-pointer hover:bg-[var(--color-hover-bg)] font-medium text-[var(--color-text-secondary)] uppercase tracking-wide ${col.width}`}
              >
                {col.label}
                {sortKey === col.key && (sortDir === 'asc' ? ' \u2191' : ' \u2193')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={row.ticker || i} className="border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
              {COLUMNS.map(col => (
                <td key={col.key} className={`px-2 py-1 font-mono text-[11px] ${cellClass(row[col.key], col.type)}`}>
                  {formatCell(row[col.key], col.type)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
