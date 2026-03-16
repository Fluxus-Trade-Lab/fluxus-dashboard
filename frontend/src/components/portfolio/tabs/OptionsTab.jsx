import { useState, useMemo } from 'react'
import { usePortfolio } from '../context/PortfolioContext'
import { fmtCur, fmtPct, fmtPctSigned, clr, clrHex, todayStr, daysBetween, MASK, priv } from '../lib/portfolioFormat'
import StatCard from '../ui/StatCard'
import Button from '../ui/Button'
import InputField from '../ui/InputField'
import OptionsTradeForm from '../OptionsTradeForm'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

/* ── Weight label map ── */
const WEIGHT_LABELS = { 0.25: 'Bird', 1: 'Cat', 2: 'Goat', 4: 'Elephant' }
function weightBadge(w) {
  const label = WEIGHT_LABELS[w] || w
  const col =
    w >= 4 ? 'bg-green-100 text-green-700' :
    w >= 2 ? 'bg-amber-100 text-amber-700' :
    w >= 1 ? 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]' :
    'bg-[var(--color-bg)] text-[var(--color-text-muted)]'
  return <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${col}`}>{w} — {label}</span>
}

/* ── P/L helpers ── */
/** Raw per-trade return % */
function plPct(t) {
  if (t.exitDate == null || t.exitPrice == null || !t.costAvg) return null
  return ((t.exitPrice - t.costAvg) / t.costAvg) * 100
}
/** Weight-adjusted contribution: raw% × weight */
function weightedPL(t) {
  const raw = plPct(t)
  if (raw == null) return null
  return raw * (t.weight || 1)
}

/* ── Sample data matching user's Q1 2026 log ── */
const SAMPLE_OPTIONS = [
  { id: 's1', ticker: 'VNET', strike: '11C', expiry: '2026-03-20', entryDate: '2025-01-05', weight: 1, costAvg: 0.6, exitPrice: 1.2, exitDate: '2025-01-14', notes: 'sold half 2x on 1/9, out 1/3 for 2x on 1/13, out rest at 1.4 on 1/14' },
  { id: 's2', ticker: 'KWEB', strike: '40C', expiry: '2026-08-21', entryDate: '2025-01-05', weight: 2, costAvg: 2.62, exitPrice: null, exitDate: null, notes: '' },
  { id: 's3', ticker: 'MSTR', strike: '170C', expiry: '2026-01-23', entryDate: '2025-01-07', weight: 0.25, costAvg: 6.7, exitPrice: 21, exitDate: '2025-01-13', notes: '' },
  { id: 's4', ticker: 'LEN', strike: '125C', expiry: '2026-02-20', entryDate: '2025-01-09', weight: 1, costAvg: 2.2, exitPrice: null, exitDate: null, notes: 'sold half on 1/12' },
  { id: 's5', ticker: 'IWM', strike: '265C', expiry: '2026-01-30', entryDate: '2025-01-12', weight: 1, costAvg: 2.43, exitPrice: 2.62, exitDate: '2025-01-13', notes: '' },
  { id: 's6', ticker: 'LITE', strike: '410C', expiry: '2026-01-23', entryDate: '2025-01-12', weight: 0.25, costAvg: 2.9, exitPrice: 0, exitDate: '2025-01-23', notes: '' },
  { id: 's7', ticker: 'SPX', strike: '6900/6800P', expiry: '2026-03-31', entryDate: '2025-01-13', weight: 1, costAvg: 24.8, exitPrice: null, exitDate: null, notes: 'to sell half when 2x' },
  { id: 's8', ticker: 'GFS', strike: '40C', expiry: '2026-01-16', entryDate: '2025-01-13', weight: 0.25, costAvg: 1.09, exitPrice: 1.95, exitDate: '2025-01-13', notes: 'roll up 45c april' },
  { id: 's9', ticker: 'GFS', strike: '45C', expiry: '2026-04-17', entryDate: '2025-01-13', weight: 1, costAvg: 2.6, exitPrice: null, exitDate: null, notes: 'sold 1/3 for 5 on 1/21' },
  { id: 's10', ticker: 'IBIT', strike: '57C', expiry: '2026-02-20', entryDate: '2025-01-13', weight: 1, costAvg: 1.4, exitPrice: null, exitDate: null, notes: '' },
  { id: 's11', ticker: 'DAL', strike: '65P', expiry: '2026-02-06', entryDate: '2025-01-13', weight: 0.25, costAvg: 1.2, exitPrice: null, exitDate: null, notes: '' },
  { id: 's12', ticker: 'EOSE', strike: '20C', expiry: '2026-02-20', entryDate: '2025-01-14', weight: 1, costAvg: 1.15, exitPrice: null, exitDate: null, notes: '' },
  { id: 's13', ticker: 'VKTX', strike: '35C', expiry: '2026-01-16', entryDate: '2025-01-14', weight: 0.25, costAvg: 1, exitPrice: 0, exitDate: '2025-01-16', notes: '' },
  { id: 's14', ticker: 'AAPL', strike: '275C', expiry: '2026-02-20', entryDate: '2025-01-15', weight: 1, costAvg: 2.95, exitPrice: 1.4, exitDate: '2025-01-20', notes: '' },
  { id: 's15', ticker: 'LAES', strike: '5C', expiry: '2026-03-20', entryDate: '2025-01-15', weight: 1, costAvg: 0.58, exitPrice: null, exitDate: null, notes: '' },
  { id: 's16', ticker: 'TSM', strike: '380/400/420C', expiry: '2026-03-20', entryDate: '2025-01-15', weight: 1, costAvg: 1.2, exitPrice: null, exitDate: null, notes: 'call butterfly, bidding to sell half for 2x' },
  { id: 's17', ticker: 'SNDK', strike: '400P', expiry: '2026-01-16', entryDate: '2025-01-16', weight: 0.25, costAvg: 2.16, exitPrice: 3.2, exitDate: '2025-01-16', notes: '' },
  { id: 's18', ticker: 'CRML', strike: '23C', expiry: '2026-02-20', entryDate: '2025-01-26', weight: 0.25, costAvg: 1.63, exitPrice: 0.84, exitDate: '2025-01-27', notes: '' },
  { id: 's19', ticker: 'SNOW', strike: '220C', expiry: '2026-02-06', entryDate: '2025-01-26', weight: 1, costAvg: 3.9, exitPrice: 6.4, exitDate: '2025-01-28', notes: '' },
  { id: 's20', ticker: 'ORCL', strike: '190C', expiry: '2026-01-30', entryDate: '2025-01-26', weight: 0.25, costAvg: 2.76, exitPrice: 0.6, exitDate: '2025-01-27', notes: '' },
  { id: 's21', ticker: 'EWY', strike: '135C', expiry: '2026-04-17', entryDate: '2025-01-27', weight: 1, costAvg: 4.1, exitPrice: null, exitDate: null, notes: '' },
  { id: 's22', ticker: 'CORZ', strike: '22C', expiry: '2026-03-20', entryDate: '2025-01-28', weight: 1, costAvg: 2.05, exitPrice: null, exitDate: null, notes: '' },
  { id: 's23', ticker: 'LEU', strike: '440/500/560', expiry: '2026-06-16', entryDate: '2025-01-28', weight: 0.25, costAvg: 3, exitPrice: null, exitDate: null, notes: '' },
]

/* ── Format short date ── */
function shortDate(d) {
  if (!d) return '—'
  const [, m, day] = d.split('-')
  return `${parseInt(m)}/${parseInt(day)}`
}

export default function OptionsTab() {
  const { state, dispatch } = usePortfolio()
  const [showForm, setShowForm] = useState(false)
  const [closingId, setClosingId] = useState(null)
  const [closeForm, setCloseForm] = useState({ exitDate: todayStr(), exitPrice: '' })
  const [editingCapital, setEditingCapital] = useState(false)
  const [capitalInput, setCapitalInput] = useState('')
  const [showOpenOnly, setShowOpenOnly] = useState(false)

  const pm = state.privacyMode
  const allTrades = state.optionsTrades

  const openTrades = useMemo(() => allTrades.filter(t => t.exitDate == null), [allTrades])
  const closedTrades = useMemo(() => {
    const ct = allTrades.filter(t => t.exitDate != null)
    return ct.sort((a, b) => (a.exitDate || '').localeCompare(b.exitDate || ''))
  }, [allTrades])

  // Displayed trades (filtered by open-only toggle)
  const trades = showOpenOnly ? openTrades : allTrades

  // Weighted realized P&L (sum of raw% × weight for each closed trade)
  const realizedPL = useMemo(() =>
    closedTrades.reduce((sum, t) => sum + (weightedPL(t) || 0), 0),
    [closedTrades]
  )

  // Win rate (based on raw P/L direction, weight doesn't change win/loss)
  const winRate = useMemo(() => {
    if (closedTrades.length === 0) return null
    const wins = closedTrades.filter(t => (plPct(t) || 0) > 0).length
    return (wins / closedTrades.length) * 100
  }, [closedTrades])

  // Equity curve — weight-adjusted cumulative P&L
  const equityCurve = useMemo(() => {
    let cumPL = 0
    return closedTrades.map(t => {
      cumPL += weightedPL(t) || 0
      return { date: shortDate(t.exitDate), cumPL: Math.round(cumPL * 100) / 100 }
    })
  }, [closedTrades])

  const handleClose = (id) => {
    const price = parseFloat(closeForm.exitPrice)
    if (isNaN(price) || !closeForm.exitDate) return
    dispatch({
      type: 'CLOSE_OPTIONS_TRADE',
      id,
      exitDate: closeForm.exitDate,
      exitPrice: price,
    })
    setClosingId(null)
    setCloseForm({ exitDate: todayStr(), exitPrice: '' })
  }

  const handleDelete = (id) => {
    dispatch({ type: 'DELETE_OPTIONS_TRADE', id })
  }

  const handleCapitalSave = () => {
    const val = parseFloat(capitalInput)
    if (!isNaN(val) && val > 0) {
      dispatch({ type: 'SET_OPTIONS_CAPITAL', capital: val })
    }
    setEditingCapital(false)
  }

  const handleLoadSample = () => {
    SAMPLE_OPTIONS.forEach(trade => {
      dispatch({ type: 'ADD_OPTIONS_TRADE', trade })
    })
  }

  const thStyle = 'text-left px-2.5 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide whitespace-nowrap'
  const tdStyle = 'px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-xs'

  return (
    <div>
      {/* Stats row */}
      <div className="flex gap-3 flex-wrap mb-5">
        <div
          className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] px-4 py-3 min-w-[130px] cursor-pointer group"
          onClick={() => {
            setEditingCapital(true)
            setCapitalInput(state.optionsCapital.toString())
          }}
        >
          <div className="text-[10px] uppercase tracking-wide text-[var(--color-text-secondary)] font-semibold mb-0.5">
            Options Capital
            <span className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity text-[var(--color-text-muted)]">edit</span>
          </div>
          {editingCapital ? (
            <div className="flex gap-1 items-center mt-1">
              <span className="text-[var(--color-text-muted)] text-sm">$</span>
              <input
                type="number"
                value={capitalInput}
                onChange={e => setCapitalInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleCapitalSave(); if (e.key === 'Escape') setEditingCapital(false) }}
                autoFocus
                className="w-[100px] text-lg font-bold bg-[var(--color-input-bg)] border border-[var(--color-input-border)] rounded px-1.5 py-0.5 font-mono tabular-nums outline-none focus:border-[var(--color-text-secondary)]"
              />
              <button onClick={handleCapitalSave} className="text-green-600 font-bold text-sm cursor-pointer bg-transparent border-none">OK</button>
            </div>
          ) : (
            <div className="text-lg font-bold font-mono tabular-nums">{pm ? MASK : fmtCur(state.optionsCapital)}</div>
          )}
        </div>
        <StatCard
          label="Open"
          value={openTrades.length}
        />
        <StatCard
          label="Closed"
          value={closedTrades.length}
        />
        <StatCard
          label="Win Rate"
          value={winRate != null ? fmtPct(winRate) : '—'}
          sub={closedTrades.length > 0 ? `${closedTrades.filter(t => (plPct(t) || 0) > 0).length}/${closedTrades.length} wins` : null}
        />
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 items-center flex-wrap mb-1">
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Trade'}
        </Button>
        {allTrades.length > 0 && (
          <button
            onClick={() => setShowOpenOnly(!showOpenOnly)}
            className={`px-3 py-1.5 rounded text-[11px] font-semibold cursor-pointer border transition-colors ${
              showOpenOnly
                ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] border-[var(--color-active-tab-bg)]'
                : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-input-border)] hover:bg-[var(--color-hover-bg)]'
            }`}
          >
            Open Only
          </button>
        )}
        {allTrades.length === 0 && (
          <Button variant="ghost" onClick={handleLoadSample}>Try Sample</Button>
        )}
      </div>

      {showForm && <OptionsTradeForm onClose={() => setShowForm(false)} />}

      {/* ── Main trade log table (all trades) ── */}
      {trades.length > 0 && (
        <div className="mt-5">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  {['Ticker', 'Strike', 'Exp', 'Status', 'Weight', 'Entry', 'Cost Avg', 'Exit Price', 'Exit Date', '% P/L', 'Wtd', 'Days', 'Notes', ''].map(h => (
                    <th key={h} className={thStyle}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {trades.map((t, idx) => {
                  const isOpen = t.exitDate == null
                  const pct = plPct(t)
                  const wtd = weightedPL(t)
                  const days = t.exitDate
                    ? daysBetween(t.entryDate, t.exitDate)
                    : daysBetween(t.entryDate, todayStr())
                  return (
                    <tr key={t.id} className={idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-surface-alt)]/50'}>
                      <td className={`${tdStyle} font-bold whitespace-nowrap`}>{t.ticker}</td>
                      <td className={`${tdStyle} font-mono text-[11px]`}>{t.strike}</td>
                      <td className={`${tdStyle} text-[11px] text-[var(--color-text-secondary)]`}>{shortDate(t.expiry)}</td>
                      <td className={tdStyle}>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${isOpen ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                          {isOpen ? 'OPEN' : 'CLOSED'}
                        </span>
                      </td>
                      <td className={tdStyle}>{weightBadge(t.weight)}</td>
                      <td className={`${tdStyle} text-[11px] text-[var(--color-text-secondary)]`}>{shortDate(t.entryDate)}</td>
                      <td className={tdStyle}>{pm ? MASK : t.costAvg?.toFixed(2)}</td>
                      <td className={tdStyle}>{t.exitPrice != null ? (pm ? MASK : t.exitPrice.toFixed(2)) : '—'}</td>
                      <td className={`${tdStyle} text-[11px] text-[var(--color-text-secondary)]`}>{t.exitDate ? shortDate(t.exitDate) : '—'}</td>
                      <td className={`${tdStyle} font-semibold ${pct != null ? clr(pct) : ''}`}>
                        {pct != null ? (
                          <span className={`px-1.5 py-0.5 rounded text-[11px] ${pct > 0 ? 'bg-green-50' : pct < 0 ? 'bg-red-50' : ''}`}>
                            {pm ? MASK : fmtPctSigned(pct)}
                          </span>
                        ) : '—'}
                      </td>
                      <td className={`${tdStyle} text-[11px] ${wtd != null ? clr(wtd) : 'text-[var(--color-text-muted)]'}`}>
                        {wtd != null ? (pm ? MASK : fmtPctSigned(wtd)) : '—'}
                      </td>
                      <td className={`${tdStyle} text-[var(--color-text-secondary)]`}>{days}</td>
                      <td className={`${tdStyle} text-[11px] text-[var(--color-text-muted)] max-w-[220px] truncate`} title={t.notes}>{t.notes || '—'}</td>
                      <td className={tdStyle}>
                        {isOpen ? (
                          closingId === t.id ? (
                            <div className="flex gap-1 items-end">
                              <InputField
                                label="Exit Date"
                                type="date"
                                value={closeForm.exitDate}
                                onChange={e => setCloseForm({ ...closeForm, exitDate: e.target.value })}
                                className="w-[120px]"
                              />
                              <InputField
                                label="Exit Price"
                                type="number"
                                step="0.01"
                                value={closeForm.exitPrice}
                                onChange={e => setCloseForm({ ...closeForm, exitPrice: e.target.value })}
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
                                  setCloseForm({ exitDate: todayStr(), exitPrice: '' })
                                }}
                                className="bg-transparent border border-[var(--color-input-border)] rounded px-2 py-0.5 text-[11px] cursor-pointer hover:bg-[var(--color-hover-bg)]"
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
                          )
                        ) : (
                          <button
                            onClick={() => handleDelete(t.id)}
                            className="bg-transparent border border-red-200 rounded px-1.5 py-0.5 text-[11px] cursor-pointer text-red-500 hover:bg-red-50"
                          >
                            &times;
                          </button>
                        )}
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
          <div className="text-[11px] uppercase tracking-wide text-[var(--color-text-secondary)] font-semibold mb-2">Cumulative Weight-Adjusted P&L</div>
          <div className="bg-[var(--color-bg)] rounded-md border border-[var(--color-border)] p-4">
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
                  tickFormatter={v => `${v}%`}
                />
                <Tooltip
                  formatter={(v) => [pm ? MASK : `${v}%`, 'Cumulative P&L']}
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
        <div className="text-center py-16 text-[var(--color-text-muted)]">
          No options trades yet. Click "+ New Trade" to start logging.
        </div>
      )}
    </div>
  )
}
