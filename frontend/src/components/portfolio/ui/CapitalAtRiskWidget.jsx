import { useMemo } from 'react'
import { aggregate } from '../lib/openRisk'
import { fmtCur, MASK } from '../lib/portfolioFormat'

const FIXED_R = 2500

/**
 * The account's own limits, so the page can say what would break the reading
 * instead of only what it is (DESIGN.md §5.1: current value against required
 * value). These are policy, not measurement — edit them here when the policy
 * changes, and nowhere else.
 *
 *   per-trade  0.25% is the fixed-R target ($2,500 on $1M, matching FIXED_R
 *              above); 0.47% is the top of the stated 1/75–1/40 Kelly band
 *   book       3% total open risk is the ceiling
 */
const LIMITS = { perTradeTarget: 0.25, perTradeMax: 0.47, bookMax: 3.0 }

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
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="text-[10px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
          Open risk
        </div>
        <div className="text-center py-8 text-[var(--color-text-muted)] text-[14px]">
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
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="flex items-baseline justify-between pb-2 border-b border-[var(--color-v2-ink)]">
        <span className="text-[10px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
          Open risk · what can be lost
        </span>
        <span className="text-[11px] text-[var(--color-text-secondary)]">
          Bars are distance to stop, not position size
        </span>
      </div>

      {/* The headline is the number he sets, not the one the market sets. Stacked
          rather than set beside the sentence: this card is half of a two-column
          grid — 594px at desktop — and side by side the sentence was crushed into
          three lines against a 38px number. */}
      <div className="mt-3">
        <div className="text-[42px] leading-none font-bold tabular-nums text-[var(--color-text)]"
             style={{ fontFamily: 'var(--font-cond)' }}>
          {pm ? MASK : riskPct != null ? `${riskPct.toFixed(2)}%` : fmtCur(data.totalRiskDollars)}
          <span className="text-[11px] font-normal tracking-[.16em] uppercase
                           text-[var(--color-text-muted)] ml-2"
                style={{ fontFamily: 'var(--font-mono)' }}>at risk</span>
        </div>
        <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-2 mb-0">
          {data.perTrade.length} position{data.perTrade.length === 1 ? '' : 's'} in {names} name
          {names === 1 ? '' : 's'}, {pm ? MASK : fmtCur(data.totalRiskDollars)} between here and
          every stop.{' '}
          <b className="text-[var(--color-text)]">Size is the decision; the rest is the market's.</b>
        </p>
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
                  // v3 pair: what the stop would take (adverse) against what
                  // it already locked (favourable) — both poles of one number
                  background: row.atRisk
                    ? 'var(--color-loss)'
                    : 'var(--color-profit)',
                }} />
              </div>
              <span className={`w-[116px] shrink-0 text-right tabular-nums ${
                row.atRisk ? 'text-[var(--color-loss)]' : 'text-[var(--color-profit)]'}`}>
                {pm ? MASK : `${row.atRisk ? '−' : '+'}${fmtCur(amount)}`}
                {!pm && pct != null && (
                  <span className="text-[var(--color-text-muted)]"> · {pct.toFixed(2)}%</span>
                )}
              </span>
            </div>
          )
        })}
        {hiddenCount > 0 && <Hidden rows={data.perTrade.slice(10)} pm={pm} />}
      </div>

      <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-3 pt-3
                    border-t border-[var(--color-border-light)] mb-0">
        <span className="text-[10px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mr-2">
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

      {riskPct != null && (
        <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-2 mb-0">
          <span className="text-[10px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mr-2">
            Against the rule
          </span>
          Book risk <b className={riskPct > LIMITS.bookMax ? 'text-[var(--color-signal-caution)]'
                                                            : 'text-[var(--color-text)]'}>
            {riskPct.toFixed(2)}%
          </b> against a {LIMITS.bookMax.toFixed(0)}% ceiling —{' '}
          {riskPct > LIMITS.bookMax
            ? <b className="text-[var(--color-signal-caution)]">over by {(riskPct - LIMITS.bookMax).toFixed(2)} points.</b>
            : <>{(LIMITS.bookMax - riskPct).toFixed(2)} points of room.</>}
          {worstPct != null && (
            <> Largest single risk <b className={worstPct > LIMITS.perTradeMax
                  ? 'text-[var(--color-signal-caution)]' : 'text-[var(--color-text)]'}>
                {worstPct.toFixed(2)}%
              </b> against a {LIMITS.perTradeTarget}% target
              {worstPct > LIMITS.perTradeMax
                ? <> — <b className="text-[var(--color-signal-caution)]">past the {LIMITS.perTradeMax}%
                    top of the band</b>, which is the sizing leak the H1 audit named.</>
                : <> and a {LIMITS.perTradeMax}% band top.</>}
            </>
          )}
        </p>
      )}
    </div>
  )
}

/**
 * What the tenth row cuts off. A hidden remainder reads as a small one, so it
 * gets stated — but stated by what it actually is. The rows below the cut are
 * the smallest risks and then the positions with no risk left at all, so
 * summing their risk can legitimately come to nothing. Printing "$0.00 of the
 * total" for that case looks like a broken number rather than a true one.
 */
function Hidden({ rows, pm }) {
  const risky = rows.filter(r => r.atRisk)
  const risk = risky.reduce((s, r) => s + r.riskDollars, 0)
  const n = rows.length
  return (
    <div className="text-[10px] text-[var(--color-text-muted)] mt-1">
      {n} more position{n === 1 ? '' : 's'} below the tenth, not drawn —{' '}
      {risky.length === 0
        ? <>none of {n === 1 ? 'it' : 'them'} has any open risk left.</>
        : <>
            {risky.length === n ? (n === 1 ? 'it carries' : 'they carry') : `${risky.length} of them carry`}{' '}
            {pm ? MASK : fmtCur(risk)} of the total.
          </>}
    </div>
  )
}
