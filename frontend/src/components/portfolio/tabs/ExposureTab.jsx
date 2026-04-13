import { useState, useMemo, Fragment } from 'react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { usePortfolio } from '../context/PortfolioContext'
import { fmtCur, fmtPct, fmt, clr, SECTOR_COLORS, MASK } from '../lib/portfolioFormat'

export default function ExposureTab({ openTrades, sectorData, holdingsData, mergedHoldingsData }) {
  const { state, dispatch } = usePortfolio()
  const pm = state.privacyMode
  const [editingSector, setEditingSector] = useState(null)
  const [sectorInput, setSectorInput] = useState('')

  if (openTrades.length === 0) {
    return <div className="text-center py-16 text-[var(--color-text-muted)]">No open positions.</div>
  }

  const startEditSector = (tradeId, currentSector) => {
    setEditingSector(tradeId)
    setSectorInput(currentSector || '')
  }

  const saveSector = (tradeId) => {
    const trimmed = sectorInput.trim()
    if (trimmed) {
      dispatch({ type: 'UPDATE_TRADE', id: tradeId, updates: { sector: trimmed } })
    }
    setEditingSector(null)
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

  // Privacy-aware currency
  const cur = (v) => pm ? MASK : fmtCur(v)

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
        <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
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
                stroke="#fff"
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
          <div className="font-semibold mb-3 text-sm">Sectors</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={sectorData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                type="number"
                tick={{ fontSize: 11 }}
                tickFormatter={v => pm ? '' : `$${(v / 1000).toFixed(0)}k`}
              />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={130} />
              <Tooltip formatter={v => pm ? MASK : fmtCur(v)} />
              <Bar dataKey="value" fill="#5b8fa8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
        <div className="font-semibold mb-3 text-sm">Detail</div>
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              {['Ticker', 'Sector', 'Dir', 'Qty', 'Entry', 'Last', 'Wt%', 'Mkt Val', 'P/L', 'P/L%'].map(h => (
                <th key={h} className="text-left px-2.5 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {groupedTrades.map((g, idx) => {
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
                      {!g.isGroup && editingSector === g.trades[0].id ? (
                        <input
                          type="text"
                          value={sectorInput}
                          onChange={e => setSectorInput(e.target.value)}
                          onBlur={() => saveSector(g.trades[0].id)}
                          onKeyDown={e => {
                            if (e.key === 'Enter') saveSector(g.trades[0].id)
                            if (e.key === 'Escape') setEditingSector(null)
                          }}
                          autoFocus
                          className="w-full px-1 py-0.5 border border-[var(--color-accent)] rounded text-xs bg-[var(--color-input-bg)] outline-none"
                        />
                      ) : (
                        <span
                          onClick={(e) => { e.stopPropagation(); startEditSector(g.trades[0].id, g.sector) }}
                          className="cursor-pointer hover:text-[var(--color-accent)] hover:underline decoration-dotted"
                          title="Click to edit sector"
                        >
                          {g.sector || 'Unknown'}
                        </span>
                      )}
                    </td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
                      <span className={g.direction === 'long' ? 'text-green-600' : 'text-red-500'}>{g.direction.toUpperCase()}</span>
                    </td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{pm ? MASK : g.totalQty}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(g.avgEntry)}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(g.lastPrice)}</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(g.weight, 1)}%</td>
                    <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{cur(g.marketVal)}</td>
                    <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${pm ? '' : clr(g.totalPL)}`}>{cur(g.totalPL)}</td>
                    <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(g.totalReturnPct)}`}>{fmtPct(g.totalReturnPct)}</td>
                  </tr>
                  {/* Expanded child rows */}
                  {g.isGroup && expanded && g.trades.map((t) => (
                    <tr key={t.id} className="bg-[var(--color-surface-raised)]">
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] pl-7 text-[var(--color-text-muted)]">{t.ticker}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)]">
                        {editingSector === t.id ? (
                          <input
                            type="text"
                            value={sectorInput}
                            onChange={e => setSectorInput(e.target.value)}
                            onBlur={() => saveSector(t.id)}
                            onKeyDown={e => {
                              if (e.key === 'Enter') saveSector(t.id)
                              if (e.key === 'Escape') setEditingSector(null)
                            }}
                            autoFocus
                            className="w-full px-1 py-0.5 border border-[var(--color-accent)] rounded text-xs bg-[var(--color-input-bg)] outline-none"
                          />
                        ) : (
                          <span
                            onClick={() => startEditSector(t.id, t.sector)}
                            className="cursor-pointer hover:text-[var(--color-accent)] hover:underline decoration-dotted"
                            title="Click to edit sector"
                          >
                            {t.sector || 'Unknown'}
                          </span>
                        )}
                      </td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)]">
                        <span className={t.direction === 'long' ? 'text-green-600' : 'text-red-500'}>{t.direction.toUpperCase()}</span>
                      </td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{pm ? MASK : t.currentQty}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.entryPrice)}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.lastPrice)}</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{fmt(t.weight, 1)}%</td>
                      <td className="px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums">{cur(t.marketVal)}</td>
                      <td className={`px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${pm ? '' : clr(t.totalPL)}`}>{cur(t.totalPL)}</td>
                      <td className={`px-2.5 py-1 border-b border-[var(--color-border-light)] tabular-nums ${clr(t.totalReturnPct)}`}>{fmtPct(t.totalReturnPct)}</td>
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
