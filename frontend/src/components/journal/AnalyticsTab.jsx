export default function AnalyticsTab() {
  // Phase 1: Mock data. Phase 2: Pull from PortfolioContext via shared store
  const mockStats = {
    totalTrades: 47,
    winRate: 61.7,
    avgR: 1.8,
    avgHoldDays: 12,
    byStrategy: [
      { name: 'Episodic Pivot', trades: 18, winRate: 72.2, avgR: 2.3, avgHold: 8 },
      { name: 'VCP', trades: 15, winRate: 60.0, avgR: 1.5, avgHold: 16 },
      { name: 'Breakout', trades: 14, winRate: 50.0, avgR: 1.1, avgHold: 11 },
    ],
    insights: [
      'Your Episodic Pivot trades are your strongest setup (72% win rate, 2.3R avg)',
      'VCP entries have decent win rate but lower R — consider tighter stops',
      'Breakout trades underperform — review your entry timing',
      'Average hold time is shorter on winners (8 days) vs losers (18 days)',
    ]
  }

  return (
    <div className="space-y-5">
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Trades" value={mockStats.totalTrades} />
        <StatCard label="Win Rate" value={`${mockStats.winRate}%`} color={mockStats.winRate >= 50 ? 'text-green-600' : 'text-red-500'} />
        <StatCard label="Avg R-Multiple" value={`${mockStats.avgR}R`} color="text-green-600" />
        <StatCard label="Avg Hold" value={`${mockStats.avgHoldDays}d`} />
      </div>

      {/* By Strategy table */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
          Performance by Strategy
        </h3>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              <th className="text-left py-2 text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">Strategy</th>
              <th className="text-right py-2 text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">Trades</th>
              <th className="text-right py-2 text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">Win Rate</th>
              <th className="text-right py-2 text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">Avg R</th>
              <th className="text-right py-2 text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">Avg Hold</th>
            </tr>
          </thead>
          <tbody>
            {mockStats.byStrategy.map((s, i) => (
              <tr key={s.name} className={`border-b border-[var(--color-border-light)] ${i % 2 === 1 ? 'bg-[var(--color-surface-alt)]/50' : ''}`}>
                <td className="py-2 font-medium text-[var(--color-text-bold)]">{s.name}</td>
                <td className="py-2 text-right font-mono tabular-nums text-[var(--color-text-secondary)]">{s.trades}</td>
                <td className={`py-2 text-right font-mono tabular-nums ${s.winRate >= 60 ? 'text-green-600' : s.winRate >= 50 ? 'text-amber-600' : 'text-red-500'}`}>{s.winRate}%</td>
                <td className={`py-2 text-right font-mono tabular-nums ${s.avgR >= 1.5 ? 'text-green-600' : 'text-[var(--color-text-secondary)]'}`}>{s.avgR}R</td>
                <td className="py-2 text-right font-mono tabular-nums text-[var(--color-text-secondary)]">{s.avgHold}d</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* AI Insights */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
          Insights
        </h3>
        <div className="space-y-2">
          {mockStats.insights.map((insight, i) => (
            <div key={i} className="flex gap-2 text-sm text-[var(--color-text-secondary)]">
              <span className="text-[var(--color-text-muted)] flex-shrink-0">&rarr;</span>
              <span>{insight}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Phase notice */}
      <div className="text-center py-4 text-[10px] text-[var(--color-text-muted)] uppercase tracking-wide">
        Showing sample data — connect your portfolio in Phase 2
      </div>
    </div>
  )
}

function StatCard({ label, value, color = 'text-[var(--color-text)]' }) {
  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-4">
      <div className="text-[10px] text-[var(--color-text-secondary)] font-medium uppercase tracking-wide mb-1">{label}</div>
      <div className={`text-xl font-bold font-mono tabular-nums ${color}`}>{value}</div>
    </div>
  )
}
