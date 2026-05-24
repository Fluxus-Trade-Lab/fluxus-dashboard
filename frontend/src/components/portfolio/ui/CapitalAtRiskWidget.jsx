import { useMemo } from 'react'
import { aggregate } from '../lib/openRisk'
import { fmtCur, MASK } from '../lib/portfolioFormat'

const FIXED_R = 2500

/**
 * Capital-at-Risk widget — sits in the Exposure tab next to Holdings.
 * Shows per-position $ at risk (or locked-in gain) as horizontal bars,
 * sorted by exposure. Totals at the top.
 *
 * @param {Array} openTrades
 * @param {boolean} pm  privacyMode
 */
export default function CapitalAtRiskWidget({ openTrades, pm = false }) {
  const data = useMemo(() => aggregate(openTrades, FIXED_R), [openTrades])

  if (!data.perTrade.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
        <div className="font-semibold mb-3 text-sm">Open Risk</div>
        <div className="text-center py-8 text-[var(--color-text-muted)] text-sm">No open positions.</div>
      </div>
    )
  }

  // Scale for bar widths: widest bar = widest of (risk, gain)
  const maxAmount = Math.max(
    ...data.perTrade.map(p => Math.max(p.riskDollars, p.gainDollars)),
    1,
  )

  const visible = data.perTrade.slice(0, 10)
  const hiddenCount = data.perTrade.length - visible.length

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
      <div className="flex items-center justify-between mb-1">
        <div className="font-semibold text-sm">Open Risk (to stop)</div>
        <div className="text-xs tabular-nums">
          <span className="text-[var(--color-signal-caution)] font-semibold">
            {pm ? MASK : fmtCur(data.totalRiskDollars)}
          </span>
          <span className="text-[var(--color-text-muted)]"> · </span>
          <span className="text-[var(--color-text)] font-semibold">{data.totalRiskR.toFixed(2)}R</span>
        </div>
      </div>
      {data.totalLockedDollars > 0 && (
        <div className="flex items-center justify-between mb-3 text-[11px]">
          <span className="text-[var(--color-text-muted)]">Locked-in gain (stops above entry)</span>
          <span className="text-[var(--color-profit)] font-semibold tabular-nums">
            {pm ? MASK : fmtCur(data.totalLockedDollars)}
          </span>
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        {visible.map(row => {
          const amount = row.atRisk ? row.riskDollars : row.gainDollars
          const widthPct = Math.max(2, (amount / maxAmount) * 100)
          const barColor = row.atRisk
            ? 'bg-[var(--color-signal-caution)]'
            : 'bg-[var(--color-profit)]'
          return (
            <div key={row.id} className="flex items-center gap-2 text-[11px]">
              <span className="w-12 font-semibold truncate" title={row.ticker}>{row.ticker}</span>
              <div className="flex-1 bg-[var(--color-surface-raised)] h-3.5 rounded-sm overflow-hidden">
                <div className={`h-full ${barColor} rounded-sm`} style={{ width: `${widthPct}%` }} />
              </div>
              <span className={`w-20 text-right tabular-nums ${row.atRisk ? 'text-[var(--color-signal-caution)]' : 'text-[var(--color-profit)]'}`}>
                {pm ? MASK : (row.atRisk ? `-${fmtCur(amount)}` : `+${fmtCur(amount)}`)}
              </span>
            </div>
          )
        })}
        {hiddenCount > 0 && (
          <div className="text-[10px] text-[var(--color-text-muted)] text-center mt-1">
            +{hiddenCount} more position{hiddenCount === 1 ? '' : 's'}
          </div>
        )}
      </div>
    </div>
  )
}
