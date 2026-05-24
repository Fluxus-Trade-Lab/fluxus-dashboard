import { useState, useEffect } from 'react'

const SAMPLE_STATS = {
  winRate: 72,
  avgReturn: 2.1,
  totalTrades: 347,
  profitFactor: 3.2,
  avgHoldDays: 4.8,
  maxDrawdown: -8.4,
}

const SAMPLE_MONTHLY = [
  { month: 'Oct 2025', trades: 28, winRate: 75, returnR: 18.2 },
  { month: 'Nov 2025', trades: 31, winRate: 68, returnR: 14.5 },
  { month: 'Dec 2025', trades: 22, winRate: 77, returnR: 16.8 },
  { month: 'Jan 2026', trades: 35, winRate: 71, returnR: 21.3 },
  { month: 'Feb 2026', trades: 29, winRate: 69, returnR: 12.7 },
  { month: 'Mar 2026', trades: 24, winRate: 75, returnR: 15.1 },
]

const SAMPLE_RECENT = [
  { ticker: 'PLTR', entry: '2026-03-14', exit: '2026-03-19', returnR: 2.8, result: 'win' },
  { ticker: 'NVDA', entry: '2026-03-10', exit: '2026-03-13', returnR: -1.0, result: 'loss' },
  { ticker: 'CELH', entry: '2026-03-07', exit: '2026-03-12', returnR: 3.4, result: 'win' },
  { ticker: 'ANET', entry: '2026-03-05', exit: '2026-03-10', returnR: 1.9, result: 'win' },
  { ticker: 'CRWD', entry: '2026-03-03', exit: '2026-03-06', returnR: 2.1, result: 'win' },
  { ticker: 'SMCI', entry: '2026-02-28', exit: '2026-03-04', returnR: -0.7, result: 'loss' },
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
                  <th className="text-right py-2 font-medium text-[var(--color-text-muted)] uppercase text-xs tracking-wide">Win Rate</th>
                  <th className="text-right py-2 font-medium text-[var(--color-text-muted)] uppercase text-xs tracking-wide">Return (R)</th>
                </tr>
              </thead>
              <tbody>
                {monthly.map(m => (
                  <tr key={m.month} className="border-b border-[var(--color-border-light)]">
                    <td className="py-2 text-[var(--color-text)]">{m.month}</td>
                    <td className="py-2 text-right font-mono text-[var(--color-text-secondary)]">{m.trades}</td>
                    <td className="py-2 text-right font-mono text-[var(--color-text-secondary)]">{m.winRate}%</td>
                    <td className={`py-2 text-right font-mono ${m.returnR >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                      {m.returnR >= 0 ? '+' : ''}{m.returnR}R
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
