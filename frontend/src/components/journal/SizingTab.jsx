import { useState, useMemo } from 'react'
import { usePortfolio, PortfolioProvider } from '../portfolio/context/PortfolioContext'
import { enrichTrades, lookupPrice } from '../portfolio/lib/calculations'
import { todayStr } from '../portfolio/lib/portfolioFormat'
import TharpLessons from './sizing/TharpLessons'
import SqnReadout from './sizing/SqnReadout'
import ObjectiveSimulator from './sizing/ObjectiveSimulator'
import { closedR, rDenominatorStop } from './lib/sizingStats'
import { useLanguage } from '../../i18n/LanguageContext'

/* ── Educational Content ─────────────────────────────────── */

// Every visible word lives in the dictionary under jn.sz.<key>.* — title, sub,
// desc, formula, example, and pro.<i> / con.<i>. Only the shape is kept here.
const METHODS = [
  { key: 'fixed-dollar', pros: 2, cons: 3, verdict: 'beginner' },
  { key: 'fixed-pct', pros: 2, cons: 3, verdict: 'intermediate' },
  { key: 'fixed-risk', pros: 3, cons: 2, verdict: 'professional' },
  { key: 'dynamic', pros: 3, cons: 3, verdict: 'advanced' },
]

const VERDICT_COLORS = {
  beginner: 'text-[var(--color-signal-caution)]',
  intermediate: 'text-[var(--color-text-secondary)]',
  professional: 'text-[var(--color-profit)]',
  advanced: 'text-[var(--color-text-secondary)]',
}

const range = (n) => Array.from({ length: n }, (_, i) => i)

/* ── Position Size Calculator ────────────────────────────── */

function SizingCalculator({ startingCapital }) {
  const { t } = useLanguage()
  const [entry, setEntry] = useState('')
  const [stop, setStop] = useState('')
  const [riskPct, setRiskPct] = useState(0.25)

  const calc = useMemo(() => {
    const e = parseFloat(entry)
    const s = parseFloat(stop)
    if (!e || !s || e === s) return null

    const capital = startingCapital || 1000000
    const riskDollar = capital * (riskPct / 100)
    const stopDist = Math.abs(e - s)
    const stopPct = (stopDist / e) * 100
    const shares = Math.floor(riskDollar / stopDist)
    const positionValue = shares * e
    const positionPct = (positionValue / capital) * 100
    const rTarget1 = e + stopDist * (e > s ? 3 : -3)
    const rTarget2 = e + stopDist * (e > s ? 5 : -5)

    return { riskDollar, stopDist, stopPct, shares, positionValue, positionPct, rTarget1, rTarget2 }
  }, [entry, stop, riskPct, startingCapital])

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-4 space-y-4">
      <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
        {t('jn.sz.calc')}
      </h3>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">{t('jn.sz.entryPrice')}</label>
          <input
            type="number"
            value={entry}
            onChange={e => setEntry(e.target.value)}
            placeholder="150.00"
            className="w-full text-[13px] bg-[var(--color-bg)] rounded-3xl px-2 py-1.5 text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
          />
        </div>
        <div>
          <label className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">{t('jn.sz.stopPrice')}</label>
          <input
            type="number"
            value={stop}
            onChange={e => setStop(e.target.value)}
            placeholder="145.00"
            className="w-full text-[13px] bg-[var(--color-bg)] rounded-3xl px-2 py-1.5 text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
          />
        </div>
        <div>
          <label className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">{t('jn.sz.riskPct')}</label>
          <input
            type="number"
            value={riskPct}
            onChange={e => setRiskPct(parseFloat(e.target.value) || 0)}
            step="0.05"
            className="w-full text-[13px] bg-[var(--color-bg)] rounded-3xl px-2 py-1.5 text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
          />
        </div>
      </div>

      {calc && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-[var(--color-border-light)]">
          <div>
            <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">{t('jn.sz.shares')}</span>
            <span className="text-[13px] font-semibold text-[var(--color-text)]">{calc.shares.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">{t('jn.sz.posValue')}</span>
            <span className="text-[13px] font-medium text-[var(--color-text)]">${calc.positionValue.toLocaleString()}</span>
            <span className="text-[11px] text-[var(--color-text-muted)] ml-1">({calc.positionPct.toFixed(1)}%)</span>
          </div>
          <div>
            <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">{t('jn.sz.atRisk')}</span>
            <span className="text-[13px] font-medium text-[var(--color-loss)]">${calc.riskDollar.toLocaleString()}</span>
            <span className="text-[11px] text-[var(--color-text-muted)] ml-1">{t('jn.sz.stopPctSub', { v: calc.stopPct.toFixed(1) })}</span>
          </div>
          <div>
            <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">{t('jn.sz.rTargets')}</span>
            <span className="text-[13px] font-mono text-[var(--color-text)]">
              3R: ${calc.rTarget1.toFixed(2)} · 5R: ${calc.rTarget2.toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Portfolio Sizing Audit ──────────────────────────────── */

function PortfolioAudit({ trades, dailyPrices, startingCapital }) {
  const { t: tr } = useLanguage()
  const audit = useMemo(() => {
    if (!trades?.length) return null

    const capital = startingCapital || 1000000
    const targetRisk = capital * 0.0025 // 0.25%
    const today = todayStr()

    const openTrades = trades.filter(t => !t.isClosed && t.currentQty > 0)
    if (!openTrades.length) return null

    let totalHeat = 0
    const positions = openTrades.map(t => {
      const dir = t.direction === 'long' ? 1 : -1
      // Sizing analysis is anchored to the locked-at-entry stop — trailing the
      // live stop would distort both the heat number and the sizing ratio.
      const initialStop = rDenominatorStop(t)
      // Unknown anchor contributes no heat and no sizing ratio. Counting it
      // off the live stop would understate heat exactly where a stop has
      // been trailed up, which is where heat matters most.
      const stopDist = initialStop == null
        ? null : Math.abs(t.entryPrice - initialStop)
      const riskDollar = stopDist == null ? null : t.currentQty * stopDist
      const riskPct = riskDollar == null ? null : (riskDollar / capital) * 100
      if (riskPct != null) totalHeat += riskPct

      const targetShares = stopDist > 0 ? Math.floor(targetRisk / stopDist) : 0  // null → 0
      const sizeRatio = targetShares > 0 ? t.originalQty / targetShares : 0

      let status = 'ok'
      if (sizeRatio < 0.6) status = 'undersized'
      else if (sizeRatio > 1.4) status = 'oversized'

      const lastP = lookupPrice(t.ticker, today, dailyPrices, t.entryPrice)
      const riskUnit = stopDist > 0 ? stopDist : 1
      const rr = ((lastP - t.entryPrice) * dir) / riskUnit

      return {
        ticker: t.ticker,
        originalQty: t.originalQty,
        currentQty: t.currentQty,
        entryPrice: t.entryPrice,
        stopPrice: t.stopPrice,
        stopDist,
        riskDollar,
        riskPct,
        targetShares,
        sizeRatio,
        status,
        rr,
      }
    }).sort((a, b) => b.riskPct - a.riskPct)

    return { positions, totalHeat, capital, targetRisk }
  }, [trades, dailyPrices, startingCapital])

  if (!audit) {
    return (
      <div className="text-[13px] text-[var(--color-text-muted)] py-4 text-center">
        {tr('jn.sz.noOpen')}
      </div>
    )
  }

  const STATUS_COLORS = {
    ok: 'text-[var(--color-profit)]',
    undersized: 'text-[var(--color-signal-caution)]',
    oversized: 'text-[var(--color-loss)]',
  }

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          {tr('jn.sz.audit')}
        </h3>
        <span className={`text-[13px] font-mono font-semibold ${audit.totalHeat > 3 ? 'text-[var(--color-loss)]' : 'text-[var(--color-text)]'}`}>
          {tr('jn.sz.totalHeat', { v: audit.totalHeat.toFixed(2) })}
          {audit.totalHeat > 3 && ' ⚠'}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
              <th className="text-left px-2 py-1.5">{tr('jn.k.ticker')}</th>
              <th className="text-right px-2 py-1.5">{tr('jn.k.qty')}</th>
              <th className="text-right px-2 py-1.5">{tr('jn.k.entry')}</th>
              <th className="text-right px-2 py-1.5">{tr('jn.k.stop')}</th>
              <th className="text-right px-2 py-1.5">{tr('jn.sz.h.riskD')}</th>
              <th className="text-right px-2 py-1.5">{tr('jn.sz.h.riskP')}</th>
              <th className="text-right px-2 py-1.5">{tr('jn.sz.h.target')}</th>
              <th className="text-right px-2 py-1.5">R</th>
              <th className="text-center px-2 py-1.5">{tr('jn.sz.h.status')}</th>
            </tr>
          </thead>
          <tbody>
            {audit.positions.map(p => (
              <tr key={p.ticker} className="border-b border-[var(--color-border-light)]">
                <td className="px-2 py-1.5 font-semibold text-[var(--color-accent)] dark:text-[var(--color-accent)]">{p.ticker}</td>
                <td className="px-2 py-1.5 text-right font-mono">{p.currentQty}</td>
                <td className="px-2 py-1.5 text-right font-mono">${p.entryPrice.toFixed(2)}</td>
                <td className="px-2 py-1.5 text-right font-mono">${p.stopPrice.toFixed(2)}</td>
                <td className="px-2 py-1.5 text-right font-mono text-[var(--color-loss)]">${p.riskDollar.toLocaleString()}</td>
                <td className="px-2 py-1.5 text-right font-mono">{p.riskPct.toFixed(2)}%</td>
                <td className="px-2 py-1.5 text-right font-mono text-[var(--color-text-muted)]">{p.targetShares}</td>
                <td className={`px-2 py-1.5 text-right font-mono ${p.rr >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                  {p.rr.toFixed(1)}R
                </td>
                <td className={`px-2 py-1.5 text-center font-medium ${STATUS_COLORS[p.status]}`}>
                  {p.status === 'ok' ? '✓' : p.status === 'undersized' ? tr('jn.sz.small') : tr('jn.sz.large')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ── Main Tab ────────────────────────────────────────────── */

export default function SizingTab() {
  return (
    <PortfolioProvider>
      <SizingTabInner />
    </PortfolioProvider>
  )
}

function SizingTabInner() {
  const { state } = usePortfolio()
  const { t } = useLanguage()
  const [expandedMethod, setExpandedMethod] = useState('fixed-risk')

  const enriched = useMemo(() => {
    if (!state.trades?.length) return []
    return enrichTrades(state.trades, state.startingCapital || 1000000, state.dailyPrices)
  }, [state.trades, state.startingCapital, state.dailyPrices])

  const rs = useMemo(() => closedR(enriched), [enriched])

  return (
    <div className="space-y-6">
      {/* Section 1: Framework Education */}
      <div>
        <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
          {t('jn.sz.methods')}
        </h3>
        <div className="space-y-2">
          {METHODS.map(method => {
            const isExpanded = expandedMethod === method.key
            const m = (f) => t(`jn.sz.${method.key}.${f}`)
            return (
              <div
                key={method.key}
                className="bg-[var(--color-surface)] rounded-3xl overflow-hidden"
              >
                {/* Header — always visible */}
                <button
                  onClick={() => setExpandedMethod(isExpanded ? null : method.key)}
                  className="w-full flex items-center justify-between px-4 py-3 text-left cursor-pointer hover:bg-[var(--color-hover-bg)] transition-colors"
                >
                  <div>
                    <span className="text-[13px] font-semibold text-[var(--color-text)]">{m('title')}</span>
                    <span className="text-[11px] text-[var(--color-text-muted)] ml-2">{m('sub')}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[11px] font-medium uppercase tracking-wide ${VERDICT_COLORS[method.verdict]}`}>
                      {t(`jn.sz.v.${method.verdict}`)}
                    </span>
                    <span className="text-[var(--color-text-muted)] text-[13px]">{isExpanded ? '−' : '+'}</span>
                  </div>
                </button>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="px-4 pb-4 space-y-3 border-t border-[var(--color-border-light)]">
                    <p className="text-[13px] text-[var(--color-text-secondary)] leading-relaxed pt-3">
                      {m('desc')}
                    </p>

                    {/* Formula */}
                    <div className="bg-[var(--color-bg)] rounded px-3 py-2">
                      <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">{t('jn.sz.formula')}</span>
                      <code className="text-[13px] font-mono text-[var(--color-text)]">{m('formula')}</code>
                    </div>

                    {/* Example */}
                    <div className="bg-[var(--color-bg)] rounded px-3 py-2">
                      <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">{t('jn.sz.example')}</span>
                      <span className="text-[13px] text-[var(--color-text-secondary)]">{m('example')}</span>
                    </div>

                    {/* Pros / Cons */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-profit)] block mb-1">{t('jn.sz.pros')}</span>
                        <ul className="space-y-0.5">
                          {range(method.pros).map((i) => (
                            <li key={i} className="text-[11px] text-[var(--color-text-secondary)] flex gap-1.5">
                              <span className="text-[var(--color-profit)] shrink-0">+</span>{m(`pro.${i}`)}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-loss)] block mb-1">{t('jn.sz.cons')}</span>
                        <ul className="space-y-0.5">
                          {range(method.cons).map((i) => (
                            <li key={i} className="text-[11px] text-[var(--color-text-secondary)] flex gap-1.5">
                              <span className="text-[var(--color-loss)] shrink-0">−</span>{m(`con.${i}`)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Van Tharp curriculum */}
      <TharpLessons />

      {/* Live system quality — SQN + expectancy from the real trade book */}
      <SqnReadout rs={rs} />

      {/* Size-to-objectives Monte-Carlo on the same live R-distribution */}
      <ObjectiveSimulator rs={rs} />

      {/* Section 2: Calculator */}
      <SizingCalculator startingCapital={state.startingCapital || 1000000} />

      {/* Section 3: Portfolio Audit */}
      <PortfolioAudit
        trades={enriched}
        dailyPrices={state.dailyPrices}
        startingCapital={state.startingCapital || 1000000}
      />
    </div>
  )
}
