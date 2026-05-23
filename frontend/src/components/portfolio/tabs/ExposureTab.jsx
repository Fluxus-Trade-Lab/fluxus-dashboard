import { useState, useMemo, Fragment } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { usePortfolio } from '../context/PortfolioContext'
import SortableHeader from '../ui/SortableHeader'
import { fmtCur, fmtPct, fmt, clr, SECTOR_COLORS, MASK } from '../lib/portfolioFormat'

export default function ExposureTab({ openTrades, mergedHoldingsData }) {
  const { state } = usePortfolio()
  const pm = state.privacyMode

  if (openTrades.length === 0) {
    return <div className="text-center py-16 text-[var(--color-text-muted)]">No open positions.</div>
  }

  const [expandedTickers, setExpandedTickers] = useState({})

  const toggleTicker = (ticker) => {
    setExpandedTickers(prev => ({ ...prev, [ticker]: !prev[ticker] }))
  }

  // Group trades by ticker for the Detail table
  const groupedTrades = useMemo(() => {
    const groups = {}
    openTrades.forEach(t => {
      if (!groups[t.ticker]) groups[t.ticker] = []
      groups[t.ticker].push(t)
    })
    return Object.entries(groups).map(([ticker, trades]) => ({
      ticker,
      trades,
      isGroup: trades.length > 1,
      // Aggregated values
      sector: trades[0].sector,
      direction: trades[0].direction,
      totalQty: trades.reduce((s, t) => s + t.currentQty, 0),
      avgEntry: trades.reduce((s, t) => s + t.entryPrice * t.currentQty, 0) / trades.reduce((s, t) => s + t.currentQty, 0),
      lastPrice: trades[0].lastPrice,
      weight: trades.reduce((s, t) => s + t.weight, 0),
      marketVal: trades.reduce((s, t) => s + t.marketVal, 0),
      totalPL: trades.reduce((s, t) => s + t.totalPL, 0),
      totalReturnPct: trades.reduce((s, t) => s + t.totalPL, 0) / trades.reduce((s, t) => s + t.entryPrice * t.currentQty, 0) * 100,
    }))
  }, [openTrades])

  const DETAIL_HEADERS = [
    { label: 'Ticker', key: 'ticker' },
    { label: 'Dir', key: 'direction' },
    { label: 'Entry', key: 'avgEntry' },
    { label: 'Last', key: 'lastPrice' },
    { label: 'Wt%', key: 'weight' },
    { label: 'P/L%', key: 'totalReturnPct' },
    { label: 'Qty', key: 'totalQty' },
    { label: 'Mkt Val', key: 'marketVal' },
    { label: 'P/L $', key: 'totalPL' },
  ]

  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'desc' })

  const handleSort = (key) => {
    setSortConfig(prev => {
      if (prev.key === key) return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
      const stringCol = ['ticker', 'direction'].includes(key)
      return { key, direction: stringCol ? 'asc' : 'desc' }
    })
  }

  const sortedGroupedTrades = useMemo(() => {
    if (!sortConfig.key) return groupedTrades
    const arr = [...groupedTrades]
    arr.sort((a, b) => {
      const av = a[sortConfig.key]
      const bv = b[sortConfig.key]
      const aNull = av == null || av === ''
      const bNull = bv == null || bv === ''
      if (aNull && bNull) return 0
      if (aNull) return 1
      if (bNull) return -1
      if (typeof av === 'string' && typeof bv === 'string') {
        return sortConfig.direction === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
      }
      return sortConfig.direction === 'asc' ? av - bv : bv - av
    })
    return arr
  }, [groupedTrades, sortConfig])

  // Privacy-aware currency
  const cur = (v) => pm ? MASK : fmtCur(v)

  return (
    <div>
      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5 mb-5">
        <div className="font-semibold mb-3 text-sm">Holdings</div>
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={mergedHoldingsData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={90}
              label={({ name, weight }) => `${name} ${weight}%`}
              labelLine={{ strokeWidth: 1 }}
              stroke="var(--color-surface)"
              strokeWidth={2}
            >
              {mergedHoldingsData.map((_, i) => (
                <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(v) => pm ? MASK : fmtCur(v)} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
        <div className="font-semibold mb-3 text-sm">Detail</div>
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              {DETAIL_HEADERS.map(h => (
                <SortableHeader
                  key={h.key}
                  label={h.label}
                  sortKey={h.key}
                  sortConfig={sortConfig}
                  onSort={handleSort}
                />
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedGroupedTrades.map((g, idx) => {
              const expanded = expandedTickers[g.ticker]
              const rowBg = idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'
              return (
                <Fragment key={g.ticker}>{/* Group header row */}
                  <tr key={g.ticker} className={`${rowBg} ${g.isGroup ? 'cursor-pointer hover:bg-[var(--color-surface-raised)]' : ''}`} onClick={() => g.isGroup && toggleTicker(g.ticker)}>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold">
                      {g.isGroup && <span className="inline-block w-3.5 text-[var(--color-text-muted)] text-[10px]">{expanded ? '▼' : '▶'}</span>}
                      {g.ticker}
                      {g.isGroup && <span className="ml-1 text-[10px] text-[var(--color-text-muted)]">({g.trades.length})</span>}
                    </td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
                      <span className={g.direction === 'long' ? 'text-green-600' : 'text-red-500'}>{g.direction.toUpperCase()}</span>
                    </td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(g.avgEntry)}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(g.lastPrice)}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(g.weight, 1)}%</td>
                    <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(g.totalReturnPct)}`}>{fmtPct(g.totalReturnPct)}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{pm ? MASK : g.totalQty}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{cur(g.marketVal)}</td>
                    <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${pm ? '' : clr(g.totalPL)}`}>{cur(g.totalPL)}</td>
                  </tr>
                  {/* Expanded child rows */}
                  {g.isGroup && expanded && g.trades.map((t) => (
                    <tr key={t.id} className="bg-[var(--color-surface-raised)]">
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] pl-7 text-[var(--color-text-muted)]">{t.ticker}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)]">
                        <span className={t.direction === 'long' ? 'text-green-600' : 'text-red-500'}>{t.direction.toUpperCase()}</span>
                      </td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.entryPrice)}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.lastPrice)}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{fmt(t.weight, 1)}%</td>
                      <td className={`px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums ${clr(t.totalReturnPct)}`}>{fmtPct(t.totalReturnPct)}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{pm ? MASK : t.currentQty}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{cur(t.marketVal)}</td>
                      <td className={`px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${pm ? '' : clr(t.totalPL)}`}>{cur(t.totalPL)}</td>
                    </tr>
                  ))}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
