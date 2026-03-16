import { useState, useMemo } from 'react'
import { usePortfolio } from '../context/PortfolioContext'
import { fmtCur, fmtPct, clr, clrHex, todayStr } from '../lib/portfolioFormat'
import StatCard from '../ui/StatCard'
import Button from '../ui/Button'
import InputField from '../ui/InputField'
import OptionsTradeForm from '../OptionsTradeForm'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const STRATEGY_LABELS = {
  call: 'Call',
  put: 'Put',
  call_spread: 'Call Spread',
  put_spread: 'Put Spread',
  iron_condor: 'Iron Condor',
  straddle: 'Straddle',
  strangle: 'Strangle',
  other: 'Other',
}

function computePL(t) {
  if (t.closeDate == null || t.closePremium == null) return null
  return (t.closePremium - t.premium) * t.contracts * 100 * (t.direction === 'long' ? 1 : -1)
}

export default function OptionsTab() {
  const { state, dispatch } = usePortfolio()
  const [showForm, setShowForm] = useState(false)
  const [closingId, setClosingId] = useState(null)
  const [closeForm, setCloseForm] = useState({ closeDate: todayStr(), closePremium: '' })

  const trades = state.optionsTrades
  const openTrades = useMemo(() => trades.filter(t => t.closeDate == null), [trades])
  const closedTrades = useMemo(() => trades.filter(t => t.closeDate != null), [trades])

  // Realized P&L
  const realizedPL = useMemo(() =>
    closedTrades.reduce((sum, t) => sum + (computePL(t) || 0), 0),
    [closedTrades]
  )

  // Win rate
  const winRate = useMemo(() => {
    if (closedTrades.length === 0) return null
    const wins = closedTrades.filter(t => (computePL(t) || 0) > 0).length
    return (wins / closedTrades.length) * 100
  }, [closedTrades])

  // Equity curve data
  const equityCurve = useMemo(() => {
    const sorted = [...closedTrades].sort((a, b) => a.closeDate.localeCompare(b.closeDate))
    let cumPL = 0
    return sorted.map(t => {
      cumPL += computePL(t) || 0
      return { date: t.closeDate, cumPL }
    })
  }, [closedTrades])

  const handleClose = (id) => {
    const premium = parseFloat(closeForm.closePremium)
    if (isNaN(premium) || !closeForm.closeDate) return
    dispatch({
      type: 'CLOSE_OPTIONS_TRADE',
      id,
      closeDate: closeForm.closeDate,
      closePremium: premium,
    })
    setClosingId(null)
    setCloseForm({ closeDate: todayStr(), closePremium: '' })
  }

  const handleDelete = (id) => {
    dispatch({ type: 'DELETE_OPTIONS_TRADE', id })
  }

  const thStyle = 'text-left px-2.5 py-2 border-b-2 border-stone-200 text-stone-500 font-semibold text-[10px] uppercase tracking-wide whitespace-nowrap'
  const tdStyle = 'px-2.5 py-1.5 border-b border-stone-100 tabular-nums'

  return (
    <div>
      {/* Stats row */}
      <div className="flex gap-3 flex-wrap mb-5">
        <StatCard
          label="Options Capital"
          value={fmtCur(state.optionsCapital)}
        />
        <StatCard
          label="Realized P&L"
          value={fmtCur(realizedPL)}
          colorClass={clr(realizedPL)}
        />
        <StatCard
          label="Open Positions"
          value={openTrades.length}
        />
        <StatCard
          label="Win Rate"
          value={winRate != null ? fmtPct(winRate) : '--'}
          sub={closedTrades.length > 0 ? `${closedTrades.filter(t => (computePL(t) || 0) > 0).length}/${closedTrades.length} wins` : null}
        />
      </div>

      {/* New Trade button */}
      <Button onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Cancel' : '+ New Trade'}
      </Button>

      {showForm && <OptionsTradeForm onClose={() => setShowForm(false)} />}

      {/* Open Positions */}
      {openTrades.length > 0 && (
        <div className="mt-6">
          <div className="text-[11px] uppercase tracking-wide text-stone-500 font-semibold mb-2">Open Positions</div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  {['Date', 'Ticker', 'Strategy', 'Strike', 'Expiry', 'Dir', 'Cts', 'Premium', 'Notes', ''].map(h => (
                    <th key={h} className={thStyle}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {openTrades.map((t, idx) => (
                  <tr key={t.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-stone-50'}>
                    <td className={`${tdStyle} text-[11px] text-stone-500`}>{t.date}</td>
                    <td className={`${tdStyle} font-bold whitespace-nowrap`}>{t.ticker}</td>
                    <td className={tdStyle}>{STRATEGY_LABELS[t.strategy] || t.strategy}</td>
                    <td className={tdStyle}>{fmtCur(t.strike)}</td>
                    <td className={`${tdStyle} text-[11px] text-stone-500`}>{t.expiry}</td>
                    <td className={tdStyle}>
                      <span className={`font-semibold text-[11px] ${t.direction === 'long' ? 'text-green-600' : 'text-red-500'}`}>
                        {t.direction === 'long' ? 'LONG' : 'SHORT'}
                      </span>
                    </td>
                    <td className={tdStyle}>{t.contracts}</td>
                    <td className={tdStyle}>{fmtCur(t.premium)}</td>
                    <td className={`${tdStyle} text-[11px] text-stone-400 max-w-[120px] truncate`}>{t.notes}</td>
                    <td className={`${tdStyle}`}>
                      {closingId === t.id ? (
                        <div className="flex gap-1 items-end">
                          <InputField
                            label="Close Date"
                            type="date"
                            value={closeForm.closeDate}
                            onChange={e => setCloseForm({ ...closeForm, closeDate: e.target.value })}
                            className="w-[120px]"
                          />
                          <InputField
                            label="Close Prem"
                            type="number"
                            step="0.01"
                            value={closeForm.closePremium}
                            onChange={e => setCloseForm({ ...closeForm, closePremium: e.target.value })}
                            placeholder="0.00"
                            className="w-[80px]"
                          />
                          <Button onClick={() => handleClose(t.id)}>OK</Button>
                          <Button variant="ghost" onClick={() => setClosingId(null)}>X</Button>
                        </div>
                      ) : (
                        <div className="flex gap-1">
                          <button
                            onClick={() => {
                              setClosingId(t.id)
                              setCloseForm({ closeDate: todayStr(), closePremium: '' })
                            }}
                            className="bg-transparent border border-stone-300 rounded px-2 py-0.5 text-[11px] cursor-pointer hover:bg-stone-100"
                          >
                            Close
                          </button>
                          <button
                            onClick={() => handleDelete(t.id)}
                            className="bg-transparent border border-red-200 rounded px-1.5 py-0.5 text-[11px] cursor-pointer text-red-500 hover:bg-red-50"
                          >
                            &times;
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Closed Trades */}
      {closedTrades.length > 0 && (
        <div className="mt-6">
          <div className="text-[11px] uppercase tracking-wide text-stone-500 font-semibold mb-2">Closed Trades</div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  {['Date', 'Ticker', 'Strategy', 'Strike', 'Expiry', 'Dir', 'Cts', 'In', 'Out', 'P&L', 'Notes', ''].map(h => (
                    <th key={h} className={thStyle}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {closedTrades.map((t, idx) => {
                  const pl = computePL(t)
                  return (
                    <tr key={t.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-stone-50'}>
                      <td className={`${tdStyle} text-[11px] text-stone-500`}>{t.date}</td>
                      <td className={`${tdStyle} font-bold whitespace-nowrap`}>{t.ticker}</td>
                      <td className={tdStyle}>{STRATEGY_LABELS[t.strategy] || t.strategy}</td>
                      <td className={tdStyle}>{fmtCur(t.strike)}</td>
                      <td className={`${tdStyle} text-[11px] text-stone-500`}>{t.expiry}</td>
                      <td className={tdStyle}>
                        <span className={`font-semibold text-[11px] ${t.direction === 'long' ? 'text-green-600' : 'text-red-500'}`}>
                          {t.direction === 'long' ? 'LONG' : 'SHORT'}
                        </span>
                      </td>
                      <td className={tdStyle}>{t.contracts}</td>
                      <td className={tdStyle}>{fmtCur(t.premium)}</td>
                      <td className={tdStyle}>{fmtCur(t.closePremium)}</td>
                      <td className={`${tdStyle} font-semibold ${clr(pl)}`}>{fmtCur(pl)}</td>
                      <td className={`${tdStyle} text-[11px] text-stone-400 max-w-[120px] truncate`}>{t.notes}</td>
                      <td className={tdStyle}>
                        <button
                          onClick={() => handleDelete(t.id)}
                          className="bg-transparent border border-red-200 rounded px-1.5 py-0.5 text-[11px] cursor-pointer text-red-500 hover:bg-red-50"
                        >
                          &times;
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Equity Curve */}
      {equityCurve.length >= 2 && (
        <div className="mt-6">
          <div className="text-[11px] uppercase tracking-wide text-stone-500 font-semibold mb-2">Cumulative Realized P&L</div>
          <div className="bg-stone-50 rounded-md border border-stone-200 p-4">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={equityCurve}>
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fill: '#78716c' }}
                  tickLine={false}
                  axisLine={{ stroke: '#d6d3d1' }}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#78716c' }}
                  tickLine={false}
                  axisLine={{ stroke: '#d6d3d1' }}
                  tickFormatter={v => `$${v.toLocaleString()}`}
                />
                <Tooltip
                  formatter={(v) => [fmtCur(v), 'Cumulative P&L']}
                  labelStyle={{ fontSize: 11, color: '#78716c' }}
                  contentStyle={{ fontSize: 11, border: '1px solid #d6d3d1', borderRadius: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="cumPL"
                  stroke={clrHex(realizedPL)}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Empty state */}
      {trades.length === 0 && !showForm && (
        <div className="text-center py-16 text-stone-400">
          No options trades yet. Click "+ New Trade" to start logging.
        </div>
      )}
    </div>
  )
}
