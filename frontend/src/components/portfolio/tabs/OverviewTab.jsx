import { useMemo, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { usePortfolio } from '../context/PortfolioContext'
import { usePrices } from '../hooks/usePrices'
import StatCard from '../ui/StatCard'
import Button from '../ui/Button'
import EditablePrice from '../ui/EditablePrice'
import SortableHeader from '../ui/SortableHeader'
import LegStateBadge from '../ui/LegStateBadge'
import StopCell from '../ui/StopCell'
import TickerLink from '../../ticker/TickerLink'
import { derive as deriveLegState } from '../lib/legState'
import { suggest as suggestStop } from '../lib/stopSuggestion'
import { useUniverse } from '../../../hooks/useUniverse'
import { fmtCur, fmtPct, fmt, clr, todayStr, MASK } from '../lib/portfolioFormat'
import { useLanguage } from '../../../i18n/LanguageContext'

export default function OverviewTab({
  performanceData, totalReturnPct,
  monthlyStats, ytdStats,
  enrichedTrades, onTrim,
}) {
  const { state, dispatch } = usePortfolio()
  const { fetchFullHistory } = usePrices()
  const { universe } = useUniverse()
  const { t: tr } = useLanguage()
  const pm = state.privacyMode
  const [showMA20, setShowMA20] = useState(true)

  // 20-day moving average of the equity return curve — a smoothed performance
  // trend for sizing: equity above its 20d MA = uptrend (size up), below = cool
  // off. Null for the first 19 points (not enough window).
  const chartData = useMemo(() => {
    const W = 20
    return (performanceData || []).map((p, i) => {
      if (i < W - 1) return { ...p, ma20: null }
      const win = performanceData.slice(i - W + 1, i + 1)
      const avg = win.reduce((s, x) => s + (x.returnPct || 0), 0) / W
      return { ...p, ma20: Math.round(avg * 100) / 100 }
    })
  }, [performanceData])

  // Per-ticker EMA + ATR lookup from universe.json (Phase 1)
  const universeByTicker = useMemo(() => {
    const out = {}
    if (!universe) return out
    for (const r of universe) {
      out[r.ticker] = {
        ema10: r.ema10, ema20: r.ema20,
        wk_ema10: r.wk_ema10, wk_ema20: r.wk_ema20,
        atr_pct: r.adr_pct,  // ADR is the closest proxy already on universe
      }
    }
    return out
  }, [universe])

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

  const TRADE_HEADERS = [
    'ticker', 'direction', 'status', 'entryDate', 'currentQty', 'entryPrice',
    'weight', 'change1D', 'pl1D', 'lastPrice', 't1Price', 't1Date',
    't2Price', 't2Date', 't3Price', 't3Date', 'stopPrice', 'unrealizedPLPct',
    'realizedPLPct', 'marketVal', 'totalPL', 'totalReturnPct', 'holdingDays', 'rr',
  ].map((key) => ({ label: tr(`pf.col.${key}`), key })).concat([{ label: '', key: null }])
  const MONTHLY_HEADERS = ['', tr('pf.mh.return'), tr('pf.mh.trades'), tr('pf.mh.avgRet'), tr('pf.mh.win'), tr('pf.mh.avgGain'), tr('pf.mh.avgLoss'), tr('pf.mh.maxGain'), tr('pf.mh.maxLoss'), tr('pf.mh.daysW'), tr('pf.mh.daysL')]

  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'desc' })

  const sortValue = (t, key) => {
    switch (key) {
      case 'ticker': return t.ticker
      case 'direction': return t.direction
      case 'status': return t.isClosed ? 'z-closed' : (t.trims?.length ? 'm-trimmed' : 'a-open')
      case 'entryDate': return t.entryDate || ''
      case 'currentQty': return t.currentQty
      case 'entryPrice': return t.entryPrice
      case 'weight': return t.weight
      case 'change1D': return t.change1D
      case 'pl1D': return t.pl1D
      case 'lastPrice': return t.lastPrice || t.entryPrice
      case 't1Price': return t.trims?.[0]?.price
      case 't1Date': return t.trims?.[0]?.date
      case 't2Price': return t.trims?.[1]?.price
      case 't2Date': return t.trims?.[1]?.date
      case 't3Price': return t.trims?.[2]?.price
      case 't3Date': return t.trims?.[2]?.date
      case 'stopPrice': return t.stopPrice
      case 'unrealizedPLPct': return t.unrealizedPLPct
      case 'realizedPLPct': return t.realizedPLPct
      case 'marketVal': return t.marketVal
      case 'totalPL': return t.totalPL
      case 'totalReturnPct': return t.totalReturnPct
      case 'holdingDays': return t.holdingDays
      case 'rr': return t.rr
      default: return null
    }
  }

  const handleSort = (key) => {
    setSortConfig(prev => {
      if (prev.key === key) return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
      const stringCol = ['ticker', 'direction', 'status'].includes(key)
      return { key, direction: stringCol ? 'asc' : 'desc' }
    })
  }

  const sortedFiltered = useMemo(() => {
    if (!sortConfig.key) return filtered
    const arr = [...filtered]
    arr.sort((a, b) => {
      const av = sortValue(a, sortConfig.key)
      const bv = sortValue(b, sortConfig.key)
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
  }, [filtered, sortConfig])

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
            <span className="text-[11px] text-[var(--color-text-muted)]">{tr('pf.hint.editPrice')}</span>
            <button
              onClick={() => dispatch({ type: 'TOGGLE_SHOW_CLOSED' })}
              className="bg-transparent border border-[var(--color-input-border)] rounded px-2.5 py-0.5 text-[11px] cursor-pointer text-[var(--color-text-secondary)] hover:bg-[var(--color-hover-bg)]"
            >
              {state.showClosed ? tr('pf.showOpenOnly') : `${tr('pf.showAll')} (${closedCount} ${tr('pf.closedCount')})`}
            </button>
          </div>

          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                {TRADE_HEADERS.map((h, i) => (
                  <SortableHeader
                    key={i}
                    label={h.label}
                    sortKey={h.key}
                    sortConfig={sortConfig}
                    onSort={handleSort}
                  />
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedFiltered.map((t, idx) => {
                const legState = deriveLegState({
                  currentQty: t.currentQty,
                  originalQty: t.originalQty,
                  trims: t.trims,
                })
                const u = universeByTicker[t.ticker] || {}
                const px = t.lastPrice || t.entryPrice
                const atrDollars = (u.atr_pct ?? 0) * 0.01 * px
                const stopSugg = suggestStop(
                  { state: legState, stopPrice: t.stopPrice, entryPrice: t.entryPrice, direction: t.direction },
                  u,
                  { atr: atrDollars },
                )
                return (
                <tr key={t.id} className={`group ${t.isClosed ? 'bg-[var(--color-closed-row)] opacity-55' : idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'}`}>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold whitespace-nowrap">
                    <TickerLink symbol={t.ticker} />
                  </td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
                    <span className={`font-semibold text-[11px] text-[var(--color-text-secondary)]`}>
                      {t.direction === 'long' ? tr('pf.dir.long') : tr('pf.dir.short')}
                    </span>
                  </td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)]">
                    {t.isClosed ? (
                      <span className="px-2 py-0.5 rounded-full text-[11px] bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]">
                        {tr('pf.closed')}
                      </span>
                    ) : (
                      <LegStateBadge state={legState} />
                    )}
                  </td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] opacity-78 group-hover:opacity-100 transition-opacity text-[11px] text-[var(--color-text-secondary)]">{t.entryDate?.slice(0, 10).replace(/-/g, '/')}</td>
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
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] opacity-78 group-hover:opacity-100 transition-opacity tabular-nums">{t.trims?.[0] ? fmtCur(t.trims[0].price) : '—'}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] opacity-78 group-hover:opacity-100 transition-opacity text-[10px] text-[var(--color-text-muted)]">{t.trims?.[0]?.date || ''}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] opacity-78 group-hover:opacity-100 transition-opacity tabular-nums">{t.trims?.[1] ? fmtCur(t.trims[1].price) : '—'}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] opacity-78 group-hover:opacity-100 transition-opacity text-[10px] text-[var(--color-text-muted)]">{t.trims?.[1]?.date || ''}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{t.trims?.[2] ? fmtCur(t.trims[2].price) : '—'}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] text-[10px] text-[var(--color-text-muted)]">{t.trims?.[2]?.date || ''}</td>
                  <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">
                    <StopCell stopPrice={t.stopPrice} initialStop={t.initialStop} suggestion={stopSugg} onChange={v => updateStop(t.id, v)} />
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
                      <button onClick={() => dispatch({ type: 'DELETE_TRADE', id: t.id })} className="bg-transparent border border-[color-mix(in_srgb,var(--color-loss)_15%,transparent)] rounded px-1.5 py-0.5 text-[11px] cursor-pointer text-[var(--color-loss)] hover:bg-[color-mix(in_srgb,var(--color-loss)_15%,transparent)]">&times;</button>
                    </div>
                  </td>
                </tr>
              )})}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Performance Curve + Monthly Stats (side by side) ── */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-[5fr_7fr] gap-4">
        {/* Left: Equity Curve */}
        <div className="min-w-0">
          {!hasSPY && (
            <div className="p-3 bg-[var(--color-accent-light)] border border-[var(--color-border)] rounded-md mb-4 text-xs text-[var(--color-accent)] flex items-center justify-between">
              <span>{tr('pf.chart.loadHistoryHint')}</span>
              <Button onClick={fetchFullHistory} disabled={state.loading}>
                {state.loading ? tr('pf.chart.loading') : tr('pf.chart.loadHistory')}
              </Button>
            </div>
          )}

          {performanceData.length > 2 ? (
            <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5 relative">
              <div className="font-semibold mb-3 text-sm flex justify-between items-center">
                <span>{tr('pf.chart.vsSpy')}</span>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowMA20(v => !v)}
                    className={`text-[11px] font-medium px-2 py-1 rounded border transition-colors ${showMA20 ? 'border-[#c98a2b] text-[#c98a2b]' : 'border-[var(--color-border)] text-[var(--color-text-muted)]'}`}
                    aria-pressed={showMA20}
                  >
                    20d MA
                  </button>
                  {hasSPY && (
                    <Button variant="ghost" onClick={fetchFullHistory} disabled={state.loading}>
                      {state.loading ? tr('pf.chart.loading') : tr('pf.chart.refreshHistory')}
                    </Button>
                  )}
                </div>
              </div>
              <div className="absolute top-12 left-14 z-10 flex gap-3 text-[11px]">
                <div><span className="text-[var(--color-text-muted)]">{tr('pf.chart.portfolio')} </span><span className={`font-bold ${clr(totalReturnPct)}`}>{fmtPct(totalReturnPct)}</span></div>
                {spyYtd != null && <div><span className="text-[var(--color-text-muted)]">{tr('pf.chart.spyYtd')} </span><span className={`font-bold ${clr(spyYtd)}`}>{fmtPct(spyYtd)}</span></div>}
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10 }}
                    tickFormatter={d => d.slice(5)}
                    interval={Math.max(1, Math.floor(chartData.length / 10))}
                  />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${Number(v).toFixed(0)}%`} />
                  <Tooltip formatter={v => `${Number(v).toFixed(2)}%`} />
                  <Legend />
                  <Line type="monotone" dataKey="returnPct" stroke="#2d5f8a" strokeWidth={2.5} dot={false} name="Portfolio" />
                  {showMA20 && (
                    <Line type="monotone" dataKey="ma20" stroke="#c98a2b" strokeWidth={1.5} dot={false} name="20d MA" connectNulls />
                  )}
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
              <div className="font-semibold mb-3 text-sm">{tr('pf.monthly.title')}</div>
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
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-profit)]">{m.avgGain ? fmtPct(m.avgGain) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-loss)]">{m.avgLoss ? fmtPct(m.avgLoss) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-profit)]">{m.largestGain ? fmtPct(m.largestGain) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-loss)]">{m.largestLoss ? fmtPct(m.largestLoss) : '—'}</td>
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
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-profit)]">{m.avgGain ? fmtPct(m.avgGain) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-loss)]">{m.avgLoss ? fmtPct(m.avgLoss) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-profit)]">{m.largestGain ? fmtPct(m.largestGain) : '—'}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-loss)]">{m.largestLoss ? fmtPct(m.largestLoss) : '—'}</td>
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
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-[var(--color-profit)]">{fmtPct(ytdStats.avgGain)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-[var(--color-loss)]">{fmtPct(ytdStats.avgLoss)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-[var(--color-profit)]">{fmtPct(ytdStats.largestGain)}</td>
                      <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-[var(--color-loss)]">{fmtPct(ytdStats.largestLoss)}</td>
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
