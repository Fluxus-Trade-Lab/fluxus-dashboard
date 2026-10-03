import StatCard from '../../portfolio/ui/StatCard'
import Empty from '../Empty'
import { fmtPct, fmt, clr, RISK_FREE_RATE } from '../../portfolio/lib/portfolioFormat'
import { useLanguage } from '../../../i18n/LanguageContext'

// Title and explanation per metric: jn.ra.<key>.title / jn.ra.<key>.desc.
const METRIC_NOTES = new Set(['annualizedReturn', 'maxDrawdown', 'correlation', 'beta', 'alpha', 'sharpe', 'sortino'])

/**
 * Sharpe, Sortino, max drawdown, alpha — read off the equity curve.
 *
 * These were on the Portfolio page, which answers "what am I carrying right
 * now". They are not that: they are statistics about a long past, and what
 * they tell you is how much damage this way of trading takes before it pays.
 * That is the question the stopping stage asks, so they live here now. The
 * beta-weighted exposure that was here went the other way, to Portfolio.
 */
export default function RiskAdjustedSection({ riskMetrics, benchmarkTicker }) {
  const { t } = useLanguage()
  if (!riskMetrics) {
    return <Empty k="empty.needHistory" />
  }

  const metrics = [
    { key: 'annualizedReturn', value: fmtPct(riskMetrics.annualizedReturn), color: clr(riskMetrics.annualizedReturn) },
    { key: 'maxDrawdown', value: fmtPct(-riskMetrics.maxDrawdown), color: 'text-[var(--color-loss)]',
      sub: riskMetrics.ddPeakDate ? `${riskMetrics.ddPeakDate} → ${riskMetrics.ddTroughDate}` : undefined },
    ...(riskMetrics.correlation != null ? [{ key: 'correlation', label: t('jn.ra.corr', { b: benchmarkTicker }), value: fmt(riskMetrics.correlation, 3), color: '' }] : []),
    ...(riskMetrics.beta != null ? [{ key: 'beta', value: fmt(riskMetrics.beta, 3), color: '' }] : []),
    ...(riskMetrics.alpha != null ? [{ key: 'alpha', value: fmtPct(riskMetrics.alpha), color: clr(riskMetrics.alpha) }] : []),
    { key: 'sharpe', value: fmt(riskMetrics.sharpe, 3), color: clr(riskMetrics.sharpe), sub: t('jn.ra.rf', { v: (RISK_FREE_RATE * 100).toFixed(1) }) },
    { key: 'sortino', value: fmt(riskMetrics.sortino, 3), color: clr(riskMetrics.sortino), sub: t('jn.ra.rf', { v: (RISK_FREE_RATE * 100).toFixed(1) }) },
  ]

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {metrics.map(m => (
          <StatCard
            key={m.key}
            label={m.label || (METRIC_NOTES.has(m.key) ? t(`jn.ra.${m.key}.title`) : m.key)}
            value={m.value}
            colorClass={m.color}
            sub={m.sub}
          />
        ))}
      </div>

      <div className="mt-6 space-y-2.5">
        {metrics.map(m => {
          if (!METRIC_NOTES.has(m.key)) return null
          return (
            <div key={m.key} className="p-3 bg-[var(--color-bg)] rounded-2xl">
              <div className="text-[11px] font-semibold text-[var(--color-text-secondary)] mb-0.5">{t(`jn.ra.${m.key}.title`)}</div>
              <div className="text-[11px] text-[var(--color-text-muted)] leading-relaxed">{t(`jn.ra.${m.key}.desc`)}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
