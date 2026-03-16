import StatCard from '../ui/StatCard'
import { fmtPct, fmt, clr, RISK_FREE_RATE } from '../lib/portfolioFormat'

const METRIC_NOTES = {
  annualizedReturn: {
    title: 'Annualized Return',
    desc: 'Projected yearly return based on your actual cumulative equity curve, geometrically scaled to 252 trading days. Positive means your portfolio is growing; negative means shrinking.',
  },
  maxDrawdown: {
    title: 'Max Drawdown',
    desc: 'Largest peak-to-trough decline in your equity curve. Measures worst-case loss from any high point. Above -10% is mild; -10% to -20% is moderate; below -20% is significant. Lower (closer to 0%) is better.',
  },
  correlation: {
    title: 'Correlation',
    desc: 'How closely your portfolio moves with the benchmark. Range: -1 to +1. Near 0 = market-neutral. Near +1 = highly market-dependent. Near -1 = inverse to market. Low correlation suggests diversification.',
  },
  beta: {
    title: 'Beta',
    desc: 'Sensitivity to market moves. Beta = 1.0 means 1:1 with market. Above 1.0 = more volatile than market (amplifies moves). Below 1.0 = less volatile. Below 0 = moves opposite to market. A beta of 0.5 means half the market\'s swings.',
  },
  alpha: {
    title: 'Alpha (Jensen\'s)',
    desc: 'Excess annualized return above what your market exposure (beta) alone would predict. Positive alpha = genuine outperformance. Zero = market-matched for your risk level. Negative = underperforming vs what beta exposure should deliver.',
  },
  sharpe: {
    title: 'Sharpe Ratio',
    desc: 'Risk-adjusted return per unit of total volatility. Formula: (Rp - Rf) / sigma * sqrt(252). Above 1.0 is good. Above 2.0 is excellent. Below 0 means you\'re underperforming the risk-free rate. Higher is always better.',
  },
  sortino: {
    title: 'Sortino Ratio',
    desc: 'Like Sharpe but only penalizes downside volatility — upside variance is treated as a feature, not a flaw. Above 1.5 is good. Above 3.0 is excellent. Better than Sharpe for portfolios with asymmetric returns.',
  },
}

export default function RiskTab({ riskMetrics, benchmarkTicker }) {
  if (!riskMetrics) {
    return <div className="text-center py-16 text-[var(--color-text-muted)]">Need ~20 trading days of data. Load history on the Performance tab.</div>
  }

  const metrics = [
    { key: 'annualizedReturn', value: fmtPct(riskMetrics.annualizedReturn), color: clr(riskMetrics.annualizedReturn) },
    { key: 'maxDrawdown', value: fmtPct(-riskMetrics.maxDrawdown), color: 'text-red-500' },
    ...(riskMetrics.correlation != null ? [{ key: 'correlation', label: `Corr (${benchmarkTicker})`, value: fmt(riskMetrics.correlation, 3), color: '' }] : []),
    ...(riskMetrics.beta != null ? [{ key: 'beta', value: fmt(riskMetrics.beta, 3), color: '' }] : []),
    ...(riskMetrics.alpha != null ? [{ key: 'alpha', value: fmtPct(riskMetrics.alpha), color: clr(riskMetrics.alpha) }] : []),
    { key: 'sharpe', value: fmt(riskMetrics.sharpe, 3), color: clr(riskMetrics.sharpe), sub: `RF: ${(RISK_FREE_RATE * 100).toFixed(1)}%` },
    { key: 'sortino', value: fmt(riskMetrics.sortino, 3), color: clr(riskMetrics.sortino), sub: `RF: ${(RISK_FREE_RATE * 100).toFixed(1)}%` },
  ]

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {metrics.map(m => (
          <StatCard
            key={m.key}
            label={m.label || METRIC_NOTES[m.key]?.title || m.key}
            value={m.value}
            colorClass={m.color}
            sub={m.sub}
          />
        ))}
      </div>

      <div className="mt-6 space-y-2.5">
        {metrics.map(m => {
          const note = METRIC_NOTES[m.key]
          if (!note) return null
          return (
            <div key={m.key} className="p-3 bg-[var(--color-bg)] rounded-md border border-[var(--color-border-light)]">
              <div className="text-[11px] font-semibold text-[var(--color-text-secondary)] mb-0.5">{note.title}</div>
              <div className="text-[11px] text-[var(--color-text-muted)] leading-relaxed">{note.desc}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
