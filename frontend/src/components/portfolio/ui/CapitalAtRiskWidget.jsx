import { useMemo } from 'react'
import { aggregate } from '../lib/openRisk'
import { fmtCur, MASK } from '../lib/portfolioFormat'
import { useLanguage } from '../../../i18n/LanguageContext'
import { rich } from '../../screener/richText'

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
  const { t: tr } = useLanguage()
  // One key per count form; the count picks the key, the sentence stays whole.
  const pl = (base, n) => tr(`${base}.${n === 1 ? 'one' : 'other'}`, { n })

  if (!data.perTrade.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="text-[11px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
          {tr('pf.risk.title')}
        </div>
        <div className="text-center py-8 text-[var(--color-text-muted)] text-[13px]">
          {tr('pf.risk.empty')}
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
        <span className="text-[11px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
          {tr('pf.risk.head')}
        </span>
        <span className="text-[11px] text-[var(--color-text-secondary)]">
          {tr('pf.risk.barsAre')}
        </span>
      </div>

      {/* The headline is the number he sets, not the one the market sets. Stacked
          rather than set beside the sentence: this card is half of a two-column
          grid — 594px at desktop — and side by side the sentence was crushed into
          three lines against a 38px number. */}
      <div className="mt-3">
        <div className="text-[46px] leading-none font-bold tabular-nums text-[var(--color-text)]"
             style={{ fontFamily: 'var(--font-cond)' }}>
          {pm ? MASK : riskPct != null ? `${riskPct.toFixed(2)}%` : fmtCur(data.totalRiskDollars)}
          <span className="text-[11px] font-normal tracking-[.16em] uppercase
                           text-[var(--color-text-muted)] ml-2"
                style={{ fontFamily: 'var(--font-mono)' }}>{tr('pf.risk.atRisk')}</span>
        </div>
        <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-2 mb-0">
          {rich(tr('pf.risk.summary', {
            positions: pl('pf.risk.nPositions', data.perTrade.length),
            names: pl('pf.risk.nNames', names),
            amount: pm ? MASK : fmtCur(data.totalRiskDollars),
          }), {}, 'text-[var(--color-text)]')}
        </p>
      </div>

      {data.totalLockedDollars > 0 && (
        <div className="flex items-baseline justify-between mt-2 text-[11px]">
          <span className="text-[var(--color-text-muted)]">
            {pl('pf.risk.locked', data.lockedCount)}
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
        {hiddenCount > 0 && <Hidden rows={data.perTrade.slice(10)} pm={pm} tr={tr} />}
      </div>

      <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-3 pt-3
                    border-t border-[var(--color-border-light)] mb-0">
        <span className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mr-2">
          {tr('pf.risk.method')}
        </span>
        {rich(tr('pf.risk.methodBody'), {
          worst: !pm && worstPct != null
            ? rich(tr('pf.risk.methodWorst', { ticker: worst.ticker, pct: worstPct.toFixed(2) }))
            : null,
        })}
        {markDate && rich(tr('pf.risk.methodMarks', { date: markDate }))}
      </p>

      {riskPct != null && (
        <p className="text-[11px] leading-relaxed text-[var(--color-text-secondary)] mt-2 mb-0">
          <span className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] mr-2">
            {tr('pf.risk.rule')}
          </span>
          {rich(tr('pf.risk.rule.book', { ceiling: LIMITS.bookMax.toFixed(0) }), {
            book: <b className={riskPct > LIMITS.bookMax ? 'text-[var(--color-signal-caution)]'
                                                         : 'text-[var(--color-text)]'}>
              {riskPct.toFixed(2)}%
            </b>,
            verdict: riskPct > LIMITS.bookMax
              ? <b className="text-[var(--color-signal-caution)]">{tr('pf.risk.rule.over', { n: (riskPct - LIMITS.bookMax).toFixed(2) })}</b>
              : tr('pf.risk.rule.room', { n: (LIMITS.bookMax - riskPct).toFixed(2) }),
          })}
          {worstPct != null && rich(tr('pf.risk.rule.largest', { target: LIMITS.perTradeTarget }), {
            worst: <b className={worstPct > LIMITS.perTradeMax
                  ? 'text-[var(--color-signal-caution)]' : 'text-[var(--color-text)]'}>
                {worstPct.toFixed(2)}%
              </b>,
            tail: worstPct > LIMITS.perTradeMax
              ? rich(tr('pf.risk.rule.tailOver'), {
                  past: <b className="text-[var(--color-signal-caution)]">{tr('pf.risk.rule.past', { max: LIMITS.perTradeMax })}</b>,
                })
              : tr('pf.risk.rule.tailOk', { max: LIMITS.perTradeMax }),
          })}
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
function Hidden({ rows, pm, tr }) {
  const risky = rows.filter(r => r.atRisk)
  const risk = risky.reduce((s, r) => s + r.riskDollars, 0)
  const n = rows.length
  const form = n === 1 ? 'one' : 'other'
  const amt = pm ? MASK : fmtCur(risk)
  return (
    <div className="text-[11px] text-[var(--color-text-muted)] mt-1">
      {risky.length === 0
        ? tr(`pf.risk.hidden.none.${form}`, { n })
        : risky.length === n
          ? tr(`pf.risk.hidden.all.${form}`, { n, amt })
          : tr('pf.risk.hidden.some', { n, k: risky.length, amt })}
    </div>
  )
}
