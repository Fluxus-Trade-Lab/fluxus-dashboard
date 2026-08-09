import { useMemo } from 'react'
import { aggregate } from '../lib/openRisk'
import { fmtCur, MASK } from '../lib/portfolioFormat'

const FIXED_R = 2500

/**
 * Open risk — the v2 positions object.
 *
 * Design: Fluxus_Brand/visual/explorations/2026-08-08/positions.html (scored 95)
 *
 * The refusal this object exists to make: every other product on the market
 * leads with P/L, which is the market's number. This one leads with what can be
 * lost between here and every stop, because that is the number the operator
 * actually sets. Exposure is printed second and smaller, on purpose.
 *
 * The bar is risk, not position size. A position's value tells you how it feels;
 * the distance to its stop tells you what it can cost. Bars are scaled to the
 * largest single risk on the book, so the widest bar is the trade that would
 * hurt most — and the scale is stated rather than left to be inferred.
 *
 * @param {Array}  openTrades
 * @param {number} equity    current mark-to-market equity, for the % of capital
 * @param {string} markDate  the session the marks were struck at
 * @param {boolean} pm       privacyMode
 */
export default function CapitalAtRiskWidget({ openTrades, equity, markDate, pm = false }) {
  const data = useMemo(() => aggregate(openTrades, FIXED_R), [openTrades])

  if (!data.perTrade.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
        <div className="text-[10px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
          Open risk
        </div>
        <div className="text-center py-8 text-[var(--color-text-muted)] text-sm">
          No open positions — nothing is at risk.
        </div>
      </div>
    )
  }

  const maxAmount = Math.max(
    ...data.perTrade.map(p => Math.max(p.riskDollars, p.gainDollars)),
    1,
  )
  const riskPct = equity > 0 ? (data.totalRiskDollars / equity) * 100 : null
  const worst = data.perTrade.reduce((a, b) => (b.riskDollars > a.riskDollars ? b : a))
  const worstPct = equity > 0 ? (worst.riskDollars / equity) * 100 : null
  const names = new Set(data.perTrade.map(p => p.ticker)).size

  const visible = data.perTrade.slice(0, 10)
  const hiddenCount = data.perTrade.length - visible.length

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
      <div className="flex items-baseline justify-between pb-2 border-b border-[var(--color-v2-ink)]">
        <span className="text-[10px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
          Open risk · what can be lost
        </span>
        <span className="text-[11px] text-[var(--color-text-secondary)]">
          Bars are distance to stop, not position size
        </span>
      </div>

      {/* the headline is the number he sets, not the one the market sets */}
      <div className="flex items-baseline gap-4 mt-3">
        <span className="text-[38px] leading-none font-bold tabular-nums text-[var(--color-text)]"
              style={{ fontFamily: 'var(--font-cond)' }}>
          {pm ? MASK : riskPct != null ? `${riskPct.toFixed(2)}%` : fmtCur(data.totalRiskDollars)}
        </span>
        <span className="text-[11px] leading-snug text-[var(--color-text-secondary)]">
          {data.perTrade.length} position{data.perTrade.length === 1 ? '' : 's'} in {names} name
          {names === 1 ? '' : 's'}, {pm ? MASK : fmtCur(data.totalRiskDollars)} between here and
          every stop{riskPct != null && <> — {riskPct.toFixed(2)}% of capital</>}.
          <br />
          <b className="text-[var(--color-text)]">Size is the decision; the rest is the market's.</b>
        </span>
      </div>

      {data.totalLockedDollars > 0 && (
        <div className="flex items-baseline justify-between mt-2 text-[11px]">
          <span className="text-[var(--color-text-muted)]">
            Locked-in gain — {data.lockedCount} stop{data.lockedCount === 1 ? '' : 's'} above entry
          </span>
          <span className="text-[var(--color-profit)] font-semibold tabular-nums">
            {pm ? MASK : fmtCur(data.totalLockedDollars)}
          </span>
        </div>
      )}

      <div className="flex flex-col gap-1.5 mt-4">
        {visible.map(row => {
          const amount = row.atRisk ? row.riskDollars : row.gainDollars
          const widthPct = Math.max(2, (amount / maxAmount) * 100)
          const pct = equity > 0 ? (amount / equity) * 100 : null
          return (
            <div key={row.id} className="flex items-center gap-2 text-[11px]">
              <span className="w-12 font-mono font-medium truncate" title={row.ticker}>
                {row.ticker}
              </span>
              <div className="flex-1 bg-[var(--color-surface-raised)] h-3.5 overflow-hidden">
                <div className="h-full" style={{
                  width: `${widthPct}%`,
                  background: row.atRisk
                    ? 'var(--color-signal-caution)'
                    : 'var(--color-profit)',
                }} />
              </div>
              <span className={`w-24 text-right tabular-nums ${
                row.atRisk ? 'text-[var(--color-signal-caution)]' : 'text-[var(--color-profit)]'}`}>
                {pm ? MASK : `${row.atRisk ? '−' : '+'}${fmtCur(amount)}`}
                {!pm && pct != null && (
                  <span className="text-[var(--color-text-muted)]"> · {pct.toFixed(2)}%</span>
                )}
              </span>
            </div>
          )
        })}
        {hiddenCount > 0 && (
          <div className="text-[10px] text-[var(--color-text-muted)] mt-1">
            {hiddenCount} more position{hiddenCount === 1 ? '' : 's'} below the tenth, not drawn —
            they carry {pm ? MASK : fmtCur(
              data.perTrade.slice(10).reduce((s, p) => s + (p.atRisk ? p.riskDollars : 0), 0))} of
            the total.
          </div>
        )}
      </div>

      <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-3 pt-3
                    border-t border-[var(--color-border-light)] mb-0">
        <span className="text-[9px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mr-2">
          Method
        </span>
        Bars are scaled to the largest single risk on the book, so the widest one is the trade that
        would hurt most{!pm && worstPct != null && (
          <> — {worst.ticker} at <b>{worstPct.toFixed(2)}%</b> of capital</>
        )}. A position with a stop above entry has no risk left in it and is drawn as locked-in
        gain instead, which is why some bars point at a profit.
        {markDate && (
          <> Marks are struck at the <b>{markDate}</b> close, so anything that moved after it is
          not in these numbers.</>
        )}
      </p>
    </div>
  )
}
