import { useState } from 'react'
import { usePortfolio } from '../context/PortfolioContext'
import EditablePrice from '../ui/EditablePrice'
import { fmtCur, fmtPct, fmt, clr, todayStr, MASK } from '../lib/portfolioFormat'

export default function PLTab({ enrichedTrades, onTrim }) {
  const { state, dispatch } = usePortfolio()
  const pm = state.privacyMode

  if (enrichedTrades.length === 0) {
    return <div className="text-center py-16 text-[var(--color-text-muted)]">No trades. Click "+ Trade" to start.</div>
  }

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

  const HEADERS = ['Ticker', 'Dir', 'Status', 'Open', 'Qty', 'Entry', 'Wt%', '1D%', 'P/L 1D', 'Last', 'T1 $', 'T1 Date', 'T2 $', 'T2 Date', 'T3 $', 'T3 Date', 'Stop', 'Unrl%', 'Rlzd%', 'Mkt Val', 'P/L', 'Tot%', 'Days', 'RR', '']

  // Privacy-aware currency formatter
  const cur = (v) => pm ? MASK : fmtCur(v)

  return (
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
            {HEADERS.map((h, i) => (
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
  )
}
