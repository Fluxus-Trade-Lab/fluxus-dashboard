import { useState } from 'react'
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
            {openTrades.map((t, idx) => (
              <tr key={t.id} className={idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'}>
                <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold">{t.ticker}</td>
                <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
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
                <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
                  <span className={t.direction === 'long' ? 'text-green-600' : 'text-red-500'}>{t.direction.toUpperCase()}</span>
                </td>
                <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{pm ? MASK : t.currentQty}</td>
                <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.entryPrice)}</td>
                <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.lastPrice)}</td>
                <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(t.weight, 1)}%</td>
                <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{cur(t.marketVal)}</td>
                <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${pm ? '' : clr(t.totalPL)}`}>{cur(t.totalPL)}</td>
                <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(t.totalReturnPct)}`}>{fmtPct(t.totalReturnPct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
