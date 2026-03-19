import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { usePortfolio } from '../context/PortfolioContext'
import { usePrices } from '../hooks/usePrices'
import StatCard from '../ui/StatCard'
import Button from '../ui/Button'
import EditablePrice from '../ui/EditablePrice'
import { fmtCur, fmtPct, fmt, clr, todayStr, MASK } from '../lib/portfolioFormat'

export default function OverviewTab({
  performanceData, totalReturnPct,
  monthlyStats, ytdStats,
  enrichedTrades, onTrim,
}) {
  const { state, dispatch } = usePortfolio()
  const { fetchFullHistory } = usePrices()
  const pm = state.privacyMode

  // --- Performance section ---
  const spyYtd = (() => {
    const hist = state.benchmarkHistories?.SPY
    if (!hist?.length) return null
    const sorted = [...hist].sort((a, b) => a.date.localeCompare(b.date))
    const currentYear = new Date().getFullYear().toString()
    const ytdStart = sorted.find(h => h.date >= currentYear + '-01-01') || sorted[0]
    const ytdEnd = sorted[sorted.length - 1]
    return ytdStart.close > 0 ? ((ytdEnd.close - ytdStart.close) / ytdStart.close) * 100 : 0
  })()

  const hasSPY = state.benchmarkHistories?.SPY?.length > 0

  // --- P/L section ---
  const closedCount = enrichedTrades.filter(t => t.isClosed).length
  const filtered = state.showClosed ? enrichedTrades : enrichedTrades.filter(t => !t.isClosed)

  const updatePrice = (id, price) => {
    const today = todayStr()
    const trade = state.trades.find(t => t.id === id)
    if (trade) {
      dispatch({ type: 'SET_DAILY_PRICES', prices: { [`${trade.ticker}:${today}`]: price } })
    }
  }

  const updateStop = (id, stopPrice) => {
    dispatch({ type: 'UPDATE_TRADE', id, updates: { stopPrice } })
  }

  const cur = (v) => pm ? MASK : fmtCur(v)

  const TRADE_HEADERS = ['Ticker', 'Dir', 'Status', 'Open', 'Qty', 'Entry', 'Wt%', '1D%', 'P/L 1D', 'Last', 'T1 $', 'T1 Date', 'T2 $', 'T2 Date', 'T3 $', 'T3 Date', 'Stop', 'Unrl%', 'Rlzd%', 'Mkt Val', 'P/L', 'Tot%', 'Days', 'RR', '']
  const MONTHLY_HEADERS = ['', 'Return%', '# Trades', 'Avg Ret%', 'Win%', 'Avg Gain%', 'Avg Loss%', 'Max Gain%', 'Max Loss%', 'Days(W)', 'Days(L)']

  // Last 10D / 20D rolling window stats
  const recentWindowStats = useMemo(() => {
    const today = new Date()
    const closedTrades = enrichedTrades.filter(t => t.isClosed)

    return [10, 20].map(days => {
      const cutoff = new Date(today)
      cutoff.setDate(cutoff.getDate() - days)
      const cutoffStr = cutoff.toISOString().split('T')[0]

      const tds = closedTrades.filter(t => {
        const trims = t.trims || []
        const lastTrim = trims[trims.length - 1]
        return lastTrim?.date >= cutoffStr
      }).map(t => ({
        retPct: t.totalReturnPct || 0,
        holdingDays: t.holdingDays || 0,
      }))

      const wins = tds.filter(x => x.retPct > 0)
      const losses = tds.filter(x => x.retPct <= 0)

      // Period return from equity curve
      let periodRetPct = 0
      if (performanceData.length > days) {
        const endPt = performanceData[performanceData.length - 1]
        const startPt = performanceData[performanceData.length - 1 - days]
        const endF = 1 + endPt.returnPct / 100
        const startF = 1 + startPt.returnPct / 100
        periodRetPct = startF > 0 ? (endF / startF - 1) * 100 : 0
      }

      return {
        month: `Last ${days}D`, totalTrades: tds.length,
        monthlyRetPct: periodRetPct,
        returnPct: tds.length ? tds.reduce((s, x) => s + x.retPct, 0) / tds.length : 0,
        winPct: tds.length ? (wins.length / tds.length) * 100 : 0,
        avgGain: wins.length ? wins.reduce((s, x) => s + x.retPct, 0) / wins.length : 0,
        avgLoss: losses.length ? losses.reduce((s, x) => s + x.retPct, 0) / losses.length : 0,
        largestGain: wins.length ? Math.max(...wins.map(x => x.retPct)) : 0,
        largestLoss: losses.length ? Math.min(...losses.map(x => x.retPct)) : 0,
        avgHoldWin: wins.length ? wins.reduce((s, x) => s + x.holdingDays, 0) / wins.length : 0,
        avgHoldLoss: losses.length ? losses.reduce((s, x) => s + x.holdingDays, 0) / losses.length : 0,
      }
    })
  }, [enrichedTrades, performanceData])

  return (
    <div className="overflow-x-hidden">
      {/* ── Trade Detail (top) ── */}
      {enrichedTrades.length > 0 && (
        <div className="overflow-x-auto">
          <div className="mb-2 flex justify-between items-center">
            <span className="text-[11px] text-[var(--color-text-muted)]">Click Last Price or Stop to edit. Hit Refresh to auto-fetch.</span>
            <button
              onClick={() => dispatch({ type: 'TOGGLE_SHOW_CLOSED' })}
              className="bg-transparent border border-[var(--color-input-border)] rounded px-2.5 py-0.5 text-[11px] cursor-pointer text-[var(--color-text-secondary)] hover:bg-[var(--color-hover-bg)]"
            >
              {state.showClosed ? 'Show Open Only' : `Show All (${closedCount} closed)`}
            </button>
          </div>

          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                {TRADE_HEADERS.map((h, i) => (
                  <th key={i} className="text-left px-2.5 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((t, idx) => (
                <tr key={t.id} className={`${t.isClosed ? 'bg-[var(--color-closed-row)] opacity-55' : idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'}`}>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold whitespace-nowrap">{t.ticker}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
                    <span className={`font-semibold text-[11px] ${t.direction === 'long' ? 'text-green-600' : 'text-red-500'}`}>
                      {t.direction === 'long' ? 'LONG' : 'SHORT'}
                    </span>
                  </td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
                    <span className={`px-2 py-0.5 rounded-full text-[11px] ${
                      t.isClosed ? 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]' :
                      t.trims?.length > 0 ? 'bg-amber-50 text-amber-700' : 'bg-green-50 text-green-700'
                    }`}>
                      {t.trimStatus}
                    </span>
                  </td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] text-[11px] text-[var(--color-text-secondary)]">{t.entryDate}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">
                    {pm ? MASK : (
                      <>
                        {t.currentQty}
                        {t.currentQty !== t.originalQty && <span className="text-[var(--color-text-muted)] text-[10px]">/{t.originalQty}</span>}
                      </>
                    )}
                  </td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.entryPrice)}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(t.weight, 1)}%</td>
                  <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(t.change1D)}`}>{fmtPct(t.change1D)}</td>
                  <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${pm ? '' : clr(t.pl1D)}`}>{cur(t.pl1D)}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">
                    <EditablePrice value={t.lastPrice || t.entryPrice} onChange={v => updatePrice(t.id, v)} />
                  </td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{t.trims?.[0] ? fmtCur(t.trims[0].price) : '—'}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] text-[10px] text-[var(--color-text-muted)]">{t.trims?.[0]?.date || ''}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{t.trims?.[1] ? fmtCur(t.trims[1].price) : '—'}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] text-[10px] text-[var(--color-text-muted)]">{t.trims?.[1]?.date || ''}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{t.trims?.[2] ? fmtCur(t.trims[2].price) : '—'}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] text-[10px] text-[var(--color-text-muted)]">{t.trims?.[2]?.date || ''}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">
                    <EditablePrice value={t.stopPrice} onChange={v => updateStop(t.id, v)} />
                  </td>
                  <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(t.unrealizedPLPct)}`}>{fmtPct(t.unrealizedPLPct)}</td>
                  <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(t.realizedPLPct)}`}>{fmtPct(t.realizedPLPct)}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{cur(t.marketVal)}</td>
                  <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${pm ? '' : clr(t.totalPL)}`}>{cur(t.totalPL)}</td>
                  <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(t.totalReturnPct)}`}>{fmtPct(t.totalReturnPct)}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{t.holdingDays}</td>
                  <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${clr(t.rr)}`}>{fmt(t.rr, 1)}R</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
                    <div className="flex gap-1">
                      {!t.isClosed && (
                        <button onClick={() => onTrim(t)} className="bg-transparent border border-[var(--color-input-border)] rounded px-2 py-0.5 text-[11px] cursor-pointer hover:bg-[var(--color-hover-bg)]">Trim</button>
                      )}
                      <button onClick={() => dispatch({ type: 'DELETE_TRADE', id: t.id })} className="bg-transparent border border-red-200 rounded px-1.5 py-0.5 text-[11px] cursor-pointer text-red-500 hover:bg-red-50">&times;</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Performance Curve + Monthly Stats (side by side) ── */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-[5fr_7fr] gap-4">
        {/* Left: Equity Curve */}
        <div className="min-w-0">
          {!hasSPY && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md mb-4 text-xs text-[var(--color-accent)] flex items-center justify-between">
              <span>Load historical prices for the equity curve and SPY comparison.</span>
              <Button onClick={fetchFullHistory} disabled={state.loading}>
                {state.loading ? 'Loading...' : 'Load History'}
              </Button>
            </div>
          )}

          {performanceData.length > 2 ? (
            <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5 relative">
              <div className="font-semibold mb-3 text-sm flex justify-between items-center">
                <span>Portfolio vs SPY</span>
                {hasSPY && (
                  <Button variant="ghost" onClick={fetchFullHistory} disabled={state.loading}>
                    {state.loading ? 'Loading...' : 'Refresh History'}
                  </Button>
                )}
              </div>
              <div className="absolute top-12 left-14 z-10 flex gap-3 text-[11px]">
                <div><span className="text-[var(--color-text-muted)]">Portfolio </span><span className={`font-bold ${clr(totalReturnPct)}`}>{fmtPct(totalReturnPct)}</span></div>
                {spyYtd != null && <div><span className="text-[var(--color-text-muted)]">SPY YTD </span><span className={`font-bold ${clr(spyYtd)}`}>{fmtPct(spyYtd)}</span></div>}
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10 }}
                    tickFormatter={d => d.slice(5)}
                    interval={Math.max(1, Math.floor(performanceData.length / 10))}
                  />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${Number(v).toFixed(0)}%`} />
                  <Tooltip formatter={v => `${Number(v).toFixed(2)}%`} />
                  <Legend />
                  <Line type="monotone" dataKey="returnPct" stroke="#2d5f8a" strokeWidth={2.5} dot={false} name="Portfolio" />
                  {hasSPY && (
                    <Line type="monotone" dataKey="SPY" stroke="#d4a574" strokeWidth={1.5} dot={false} name="SPY" strokeDasharray="4 4" />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center py-10 text-[var(--color-text-muted)] text-sm border border-[var(--color-border)] rounded-lg">Need trades to build equity curve.</div>
          )}
        </div>

        {/* Right: Monthly Stats */}
        <div className="min-w-0">
          {monthlyStats.length > 0 && (
            <div className="overflow-x-auto bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
              <div className="font-semibold mb-3 text-sm">Monthly Performance</div>
              <table className="w-full border-collapse text-xs">
                <thead>
                  <tr>
                    {MONTHLY_HEADERS.map(h => (
                      <th key={h} className="text-left px-2.5 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recentWindowStats.map((m, idx) => (
                    <tr key={m.month} className={idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-surface-alt)]'}>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-semibold tabular-nums">{m.month}</td>
                      <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold tabular-nums ${clr(m.monthlyRetPct)}`}>{fmtPct(m.monthlyRetPct)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.totalTrades || '—'}</td>
                      <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(m.returnPct)}`}>{m.totalTrades ? fmtPct(m.returnPct) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.totalTrades ? fmtPct(m.winPct) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-green-600">{m.avgGain ? fmtPct(m.avgGain) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-red-500">{m.avgLoss ? fmtPct(m.avgLoss) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-green-600">{m.largestGain ? fmtPct(m.largestGain) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-red-500">{m.largestLoss ? fmtPct(m.largestLoss) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.avgHoldWin ? fmt(m.avgHoldWin, 2) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.avgHoldLoss ? fmt(m.avgHoldLoss, 2) : '—'}</td>
                    </tr>
                  ))}
                  <tr><td colSpan={11} className="border-b-[3px] border-[var(--color-border)]" /></tr>
                  {monthlyStats.map((m, idx) => (
                    <tr key={m.month} className={idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-surface-alt)]'}>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-semibold tabular-nums">{m.month}</td>
                      <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold tabular-nums ${clr(m.monthlyRetPct)}`}>{fmtPct(m.monthlyRetPct)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.totalTrades || '—'}</td>
                      <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(m.returnPct)}`}>{m.totalTrades ? fmtPct(m.returnPct) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.totalTrades ? fmtPct(m.winPct) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-green-600">{m.avgGain ? fmtPct(m.avgGain) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-red-500">{m.avgLoss ? fmtPct(m.avgLoss) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-green-600">{m.largestGain ? fmtPct(m.largestGain) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-red-500">{m.largestLoss ? fmtPct(m.largestLoss) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.avgHoldWin ? fmt(m.avgHoldWin, 2) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.avgHoldLoss ? fmt(m.avgHoldLoss, 2) : '—'}</td>
                    </tr>
                  ))}
                  {ytdStats && (
                    <tr className="bg-[var(--color-surface-raised)] font-bold">
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)]">YTD</td>
                      <td className={`px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums ${clr(totalReturnPct)}`}>{fmtPct(totalReturnPct)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums">{ytdStats.totalTrades}</td>
                      <td className={`px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums ${clr(ytdStats.returnPct)}`}>{fmtPct(ytdStats.returnPct)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums">{fmtPct(ytdStats.winPct)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-green-600">{fmtPct(ytdStats.avgGain)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-red-500">{fmtPct(ytdStats.avgLoss)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-green-600">{fmtPct(ytdStats.largestGain)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-red-500">{fmtPct(ytdStats.largestLoss)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums">{fmt(ytdStats.avgHoldWin, 2)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums">{fmt(ytdStats.avgHoldLoss, 2)}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
