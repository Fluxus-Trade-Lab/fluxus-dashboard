import { useMemo } from 'react'
import { groupByCampaigns } from '../portfolio/lib/campaign'
import { fmtCur, fmtPct } from '../portfolio/lib/portfolioFormat'

/**
 * All user trades on this ticker, grouped by campaign with aggregate stats.
 */
export default function TickerTrades({ symbol, trades }) {
  const onTicker = useMemo(
    () => (trades || []).filter(t => t.ticker === symbol),
    [trades, symbol],
  )

  const stats = useMemo(() => {
    if (!onTicker.length) return null
    const closed = onTicker.filter(t => t.isClosed)
    const open = onTicker.filter(t => !t.isClosed)
    const totalRealizedR = closed.reduce((s, t) => s + (t.totalReturnPct || 0), 0) / 100  // not real R; placeholder
    const wins = closed.filter(t => (t.totalPL || 0) > 0).length
    const winRate = closed.length > 0 ? wins / closed.length * 100 : 0
    const totalRealizedDollars = closed.reduce((s, t) => s + (t.totalPL || 0), 0)
    return {
      total: onTicker.length,
      open: open.length,
      closed: closed.length,
      winRate,
      totalRealizedDollars,
    }
  }, [onTicker])

  if (!onTicker.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[13px]">Trades</div>
        <div className="text-[var(--color-text-muted)] text-[13px]">No trades recorded for {symbol}.</div>
      </div>
    )
  }

  const campaigns = groupByCampaigns(onTicker)

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="font-semibold text-[13px]">Trades</div>
        <div className="text-[11px] text-[var(--color-text-muted)] tabular-nums">
          {stats.total} trade{stats.total === 1 ? '' : 's'} ·{' '}
          {stats.open} open · {stats.closed} closed · {stats.winRate.toFixed(0)}% WR ·{' '}
          <span className={stats.totalRealizedDollars >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}>
            {fmtCur(stats.totalRealizedDollars)} realized
          </span>
        </div>
      </div>

      <table className="w-full border-collapse text-[13px]">
        <thead>
          <tr className="text-left text-[11px] text-[var(--color-text-muted)] uppercase tracking-wide">
            <th className="px-2 py-1.5">Entry date</th>
            <th className="px-2 py-1.5">Dir</th>
            <th className="px-2 py-1.5 text-right">Entry</th>
            <th className="px-2 py-1.5 text-right">Qty</th>
            <th className="px-2 py-1.5 text-right">Stop</th>
            <th className="px-2 py-1.5 text-right">Cur Qty</th>
            <th className="px-2 py-1.5">Trims</th>
            <th className="px-2 py-1.5 text-right">P/L</th>
            <th className="px-2 py-1.5 text-right">Tot%</th>
          </tr>
        </thead>
        <tbody>
          {campaigns.map(c => (
            <CampaignRows key={c.id} campaign={c} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function CampaignRows({ campaign }) {
  return (
    <>
      {campaign.layers.length > 1 && (
        <tr className="bg-[var(--color-surface-raised)] text-[11px]">
          <td colSpan={9} className="px-2 py-1 text-[var(--color-text-muted)]">
            Campaign · {campaign.layers.length} layers · {campaign.firstEntry} → {campaign.lastEntry}
          </td>
        </tr>
      )}
      {campaign.layers.map((t, idx) => (
        <tr
          key={t.id}
          className={`${t.isClosed ? 'opacity-60' : ''} ${idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'} border-b border-[var(--color-border-light)]`}
        >
          <td className="px-2 py-1.5 whitespace-nowrap">{t.entryDate?.slice(0, 10).replace(/-/g, '/')}</td>
          <td className="px-2 py-1.5">
            <span className={'text-[var(--color-text-secondary)]'}>
              {t.direction === 'long' ? 'LONG' : 'SHORT'}
            </span>
          </td>
          <td className="px-2 py-1.5 text-right tabular-nums">{fmtCur(t.entryPrice)}</td>
          <td className="px-2 py-1.5 text-right tabular-nums">{t.originalQty}</td>
          <td className="px-2 py-1.5 text-right tabular-nums">{fmtCur(t.stopPrice)}</td>
          <td className="px-2 py-1.5 text-right tabular-nums">{t.currentQty}</td>
          <td className="px-2 py-1.5 text-[11px] text-[var(--color-text-muted)]">
            {t.trims?.length
              ? t.trims.map(tr => `${tr.date} ${fmtCur(tr.price)} (${tr.qty})`).join(' · ')
              : '—'}
          </td>
          <td className={`px-2 py-1.5 text-right tabular-nums ${(t.totalPL || 0) >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
            {fmtCur(t.totalPL)}
          </td>
          <td className={`px-2 py-1.5 text-right tabular-nums ${(t.totalReturnPct || 0) >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
            {fmtPct(t.totalReturnPct)}
          </td>
        </tr>
      ))}
    </>
  )
}
