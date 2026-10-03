import { useState, useMemo } from 'react'
import { usePortfolio, PortfolioProvider } from '../portfolio/context/PortfolioContext'
import { computeStopSim } from './lib/stopSim'
import StatCard from '../portfolio/ui/StatCard'
import { DivergingBars } from './lib/MiniBars'
import { fmtCur, fmtPct, fmt, clr } from '../portfolio/lib/portfolioFormat'
import { useLanguage } from '../../i18n/LanguageContext'
import { word } from '../screener/richText'

export default function RiskTab() {
  return (
    <PortfolioProvider>
      <RiskTabInner />
    </PortfolioProvider>
  )
}

function RiskTabInner() {
  const { state } = usePortfolio()
  const { t } = useLanguage()
  const [mode, setMode] = useState(3)

  const simData2 = useMemo(
    () => computeStopSim(state.trades, state.dailyPrices, 2),
    [state.trades, state.dailyPrices]
  )
  const simData3 = useMemo(
    () => computeStopSim(state.trades, state.dailyPrices, 3),
    [state.trades, state.dailyPrices]
  )

  const simData = mode === 2 ? simData2 : simData3

  /* One chart: which trades this system would have helped or hurt, and by
     how much — the question the six stat cards below only answer in
     aggregate. Sorted by |diff| so the trades worth looking at are on top;
     capped at 24 rows so the chart stays a shape you can read in one look,
     not a second table (the real table is still below it). Computed above
     the early return — a hook cannot sit after one. */
  const diffRows = useMemo(() => (simData?.rows ?? []).length === 0 ? [] : [...simData.rows]
    .sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff))
    .slice(0, 24)
    .map((r) => ({ key: r.ticker, value: r.diff })), [simData])

  if (!simData || simData.rows.length === 0) {
    return (
      <div className="text-center py-16 text-[var(--color-text-muted)]">
        {t('jn.st.none')}
      </div>
    )
  }

  const { rows, summary } = simData
  const hasHistoryGap = rows.some(r => !r.hasHistory)

  const cards = [
    { label: t('jn.st.actualPL'), value: fmtCur(summary.totalActualPL), color: clr(summary.totalActualPL) },
    { label: t('jn.st.simPL', { n: mode }), value: fmtCur(summary.totalSimPL), color: clr(summary.totalSimPL) },
    { label: t('jn.st.diff'), value: fmtCur(summary.totalDiff), color: clr(summary.totalDiff), sub: summary.totalDiff > 0 ? t('jn.st.save', { n: mode }) : summary.totalDiff < 0 ? t('jn.st.cost', { n: mode }) : t('jn.st.noChange') },
    { label: t('jn.st.actualLoss'), value: fmtPct(summary.avgActualLoss), color: 'text-[var(--color-loss)]' },
    { label: t('jn.st.simLoss', { n: mode }), value: fmtPct(summary.avgSimLoss), color: 'text-[var(--color-loss)]' },
    { label: t('jn.st.affected'), value: `${summary.tradesAffected} / ${summary.totalTrades}`, color: '', sub: t('jn.st.triggered') },
  ]

  const numStops = rows[0]?.stops?.length || mode

  return (
    <div>
      <h3 className="text-[13px] font-semibold text-[var(--color-text)] mb-3">{t('jn.st.title')}</h3>
      <p className="text-[13px] text-[var(--color-text-muted)] mb-4">
        {t('jn.st.lede')}
      </p>

      {/* Segmented toggle */}
      <div className="flex mb-4">
        <button
          onClick={() => setMode(2)}
          className={`px-4 py-1.5 text-[13px] font-semibold rounded-l-md border cursor-pointer ${
            mode === 2
              ? 'bg-[var(--color-accent-solid)] text-white border-[var(--color-accent)]'
              : 'bg-transparent text-[var(--color-text-muted)] border-[var(--color-border)]'
          }`}
        >
          {t('jn.st.mode', { n: 2 })}
        </button>
        <button
          onClick={() => setMode(3)}
          className={`px-4 py-1.5 text-[13px] font-semibold rounded-r-md border border-l-0 cursor-pointer ${
            mode === 3
              ? 'bg-[var(--color-accent-solid)] text-white border-[var(--color-accent)]'
              : 'bg-transparent text-[var(--color-text-muted)] border-[var(--color-border)]'
          }`}
        >
          {t('jn.st.mode', { n: 3 })}
        </button>
      </div>

      {hasHistoryGap && (
        <div className="p-3 bg-[color-mix(in_srgb,var(--color-signal-caution)_30%,transparent)] border border-[color-mix(in_srgb,var(--color-signal-caution)_30%,transparent)] rounded-md mb-4 text-[13px] text-[var(--color-signal-caution)]">
          {t('jn.st.gap')}
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {cards.map((c, i) => (
          <StatCard key={i} label={c.label} value={c.value} colorClass={c.color} sub={c.sub} />
        ))}
      </div>

      {diffRows.length > 0 && (
        <div className="bg-[var(--color-surface)] rounded-3xl p-4 mb-6">
          <div className="flex items-baseline justify-between mb-2">
            <h4 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
              {t('jn.st.changed')}
            </h4>
            <span className="text-[11px] text-[var(--color-text-muted)]">
              {t('jn.st.changedN', { n: diffRows.length, of: rows.length })}
            </span>
          </div>
          <DivergingBars rows={diffRows} formatValue={(v) => fmtCur(v)} />
          <p className="text-[11px] text-[var(--color-text-muted)] mt-2 mb-0">
            {t('jn.st.legend', { n: mode })}
          </p>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-[13px] font-mono">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-[11px] text-[var(--color-text-muted)] uppercase tracking-wider">
              <th className="text-left py-2 px-2">{t('jn.k.ticker')}</th>
              <th className="text-left py-2 px-1">{t('jn.k.dir')}</th>
              <th className="text-right py-2 px-2">{t('jn.k.qty')}</th>
              <th className="text-right py-2 px-2">{t('jn.k.entry')}</th>
              <th className="text-right py-2 px-2">{t('jn.k.stop')}</th>
              <th className="text-right py-2 px-2">R</th>
              {Array.from({ length: numStops }, (_, i) => (
                <th key={i} className="text-right py-2 px-2">{t('jn.st.h.stopN', { i: i + 1 })}</th>
              ))}
              <th className="text-right py-2 px-2">{t('jn.st.h.avgExit')}</th>
              <th className="text-right py-2 px-2">{t('jn.st.h.actualPL')}</th>
              <th className="text-right py-2 px-2">{t('jn.st.h.simPL', { n: mode })}</th>
              <th className="text-right py-2 px-2">{t('jn.st.h.diff')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id} className="border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
                <td className="py-2 px-2 font-semibold text-[var(--color-accent)]">{r.ticker}</td>
                <td className={`py-2 px-1 font-semibold text-[var(--color-text-secondary)]`}>
                  {word(t, `jn.dir.${r.direction}`, r.direction).toUpperCase()}
                </td>
                <td className="text-right py-2 px-2">{r.qty}</td>
                <td className="text-right py-2 px-2">{fmtCur(r.entryPrice)}</td>
                <td className="text-right py-2 px-2">{fmtCur(r.stopPrice)}</td>
                <td className="text-right py-2 px-2">{fmt(r.R, 2)}</td>
                {r.stops.map((stop, i) => (
                  <td key={i} className={`text-right py-2 px-2 ${stop.triggered ? 'text-[var(--color-loss)] font-semibold' : 'text-[var(--color-text-muted)]'}`}>
                    {fmtCur(stop.level)}
                  </td>
                ))}
                <td className="text-right py-2 px-2">{fmtCur(r.actualAvgExit)}</td>
                <td className={`text-right py-2 px-2 ${clr(r.actualPL)}`}>{fmtCur(r.actualPL)}</td>
                <td className={`text-right py-2 px-2 ${clr(r.simPL)}`}>{fmtCur(r.simPL)}</td>
                <td className={`text-right py-2 px-2 font-semibold ${clr(r.diff)}`}>{fmtCur(r.diff)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
