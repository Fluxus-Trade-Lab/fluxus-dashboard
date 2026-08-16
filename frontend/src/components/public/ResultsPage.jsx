import { useState, useEffect } from 'react'

// Real H1 2026 figures — source: data/portfolio/reviews/h1_2026.json.
// These are the FALLBACKS; performance.json carries the same numbers. They used
// to be invented placeholders (72% win rate, 347 trades) sitting on a public page.
const SAMPLE_STATS = {
  winRate: 39.9,
  avgReturn: 0.88,
  totalTrades: 331,
  profitFactor: 2.48,
  avgHoldDays: 7.5,
  // Deepest MTM decline BY PERCENT: -17.9% (2026-01-28 -> 2026-03-19).
  //
  // Two conventions exist and they disagree. compute_mtm_drawdown() in
  // pipeline/portfolio/h1_report.py returns both and calls the DOLLAR-max one
  // canonical: -11.1% / -$223k (2026-06-02 -> 2026-06-10, on a ~$2.00M peak).
  // The masterclass (L15.4) and the Track Record standard both say percent, on
  // the grounds that a later dollar-drop on a bigger account understates the
  // real damage. We publish the percent figure to stay consistent with those.
  // If the canonical label in h1_report.py is the one that is right, this
  // number and the course both need to change — it is a decision, not a bug.
  maxDrawdown: -17.9,
}

const SAMPLE_MONTHLY = [
  { month: 'Jan 2026', trades: 36, pnl: 43710 },
  { month: 'Feb 2026', trades: 23, pnl: 9569 },
  { month: 'Mar 2026', trades: 58, pnl: 20370 },
  { month: 'Apr 2026', trades: 59, pnl: 141337 },
  { month: 'May 2026', trades: 70, pnl: 319907 },
  { month: 'Jun 2026', trades: 57, pnl: 271142 },
  { month: 'Jul 2026', trades: 28, pnl: 99220 },
]

const SAMPLE_RECENT = [
  { ticker: 'ALAB', entry: '2026-05-12', exit: '2026-06-23', returnR: 21.0, result: 'win' },
  { ticker: 'DOCN', entry: '2026-04-14', exit: '2026-07-09', returnR: 17.4, result: 'win' },
  { ticker: 'BE',   entry: '2026-04-08', exit: '2026-04-28', returnR: 7.3,  result: 'win' },
  { ticker: 'SNDK', entry: '2026-06-24', exit: '2026-06-25', returnR: 4.1,  result: 'win' },
  { ticker: 'BABA', entry: '2026-01-11', exit: '2026-04-23', returnR: -4.2, result: 'loss' },
  { ticker: 'CRCL', entry: '2026-05-10', exit: '2026-05-15', returnR: -1.3, result: 'loss' },
]

function StatCard({ label, value, suffix }) {
  return (
    <div className="py-4">
      <div className="font-mono text-2xl sm:text-3xl font-medium text-[var(--color-text)]">
        {value}{suffix}
      </div>
      <div className="public-label mt-1">{label}</div>
    </div>
  )
}

export default function ResultsPage() {
  const [performance, setPerformance] = useState(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/output/performance.json`)
      .then(r => r.ok ? r.json() : null)
      .then(setPerformance)
      .catch(() => setPerformance(null))
  }, [])

  const stats = performance?.stats || SAMPLE_STATS
  const monthly = performance?.monthly || SAMPLE_MONTHLY
  const recent = performance?.recentTrades || SAMPLE_RECENT

  return (
    <div>
      {/* Header */}
      <section className="public-section public-section-wide pt-16 sm:pt-24 pb-8">
        <h1 className="public-h1">Results</h1>
        <p className="public-body mt-4 text-[var(--color-text-secondary)] max-w-[540px]">
          Real trades. Real numbers. No cherry-picking.
        </p>
      </section>

      {/* Stats grid */}
      <section className="public-section public-section-wide pb-12">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-8 gap-y-2 max-w-[600px]">
          <StatCard label="Win Rate" value={stats.winRate} suffix="%" />
          <StatCard label="Avg Return" value={stats.avgReturn} suffix="R" />
          <StatCard label="Total Trades" value={stats.totalTrades} suffix="" />
          <StatCard label="Profit Factor" value={stats.profitFactor} suffix="" />
          <StatCard label="Avg Hold" value={stats.avgHoldDays} suffix=" days" />
          <StatCard label="Max Drawdown" value={stats.maxDrawdown} suffix="%" />
        </div>
      </section>

      {/* Monthly breakdown */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="public-section public-section-wide py-12">
          <h2 className="public-h2">Monthly Breakdown</h2>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-sm max-w-[600px]">
              <thead>
                <tr className="border-b border-[var(--color-border)]">
                  <th className="text-left py-2 font-medium text-[var(--color-text-muted)] uppercase text-xs tracking-wide">Month</th>
                  <th className="text-right py-2 font-medium text-[var(--color-text-muted)] uppercase text-xs tracking-wide">Trades</th>
                  <th className="text-right py-2 font-medium text-[var(--color-text-muted)] uppercase text-xs tracking-wide">P&amp;L</th>
                </tr>
              </thead>
              <tbody>
                {monthly.map(m => (
                  <tr key={m.month} className="border-b border-[var(--color-border-light)]">
                    <td className="py-2 text-[var(--color-text)]">{m.month}</td>
                    <td className="py-2 text-right font-mono text-[var(--color-text-secondary)]">{m.trades}</td>
                    <td className={`py-2 text-right font-mono ${m.pnl >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                      {m.pnl >= 0 ? '+' : '-'}${Math.abs(m.pnl).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Recent trades */}
      <section className="border-t border-[var(--color-border)]">
        <div className="public-section public-section-wide py-12">
          <h2 className="public-h2">Recent Trades</h2>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-sm max-w-[600px]">
              <thead>
                <tr className="border-b border-[var(--color-border)]">
                  <th className="text-left py-2 font-medium text-[var(--color-text-muted)] uppercase text-xs tracking-wide">Ticker</th>
                  <th className="text-left py-2 font-medium text-[var(--color-text-muted)] uppercase text-xs tracking-wide">Entry</th>
                  <th className="text-left py-2 font-medium text-[var(--color-text-muted)] uppercase text-xs tracking-wide">Exit</th>
                  <th className="text-right py-2 font-medium text-[var(--color-text-muted)] uppercase text-xs tracking-wide">Return</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((t, i) => (
                  <tr key={i} className="border-b border-[var(--color-border-light)]">
                    <td className="py-2 font-mono font-medium text-[var(--color-text)]">{t.ticker}</td>
                    <td className="py-2 text-[var(--color-text-secondary)]">{t.entry}</td>
                    <td className="py-2 text-[var(--color-text-secondary)]">{t.exit}</td>
                    <td className={`py-2 text-right font-mono ${t.returnR >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                      {t.returnR >= 0 ? '+' : ''}{t.returnR}R
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="public-section public-section-prose py-8">
          <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
            Past performance is not indicative of future results. All returns
            shown are measured in R-multiples (risk units), not dollar amounts.
            Individual results will vary based on account size, risk tolerance,
            and execution. Trading involves substantial risk of loss.
          </p>
        </div>
      </section>
    </div>
  )
}
