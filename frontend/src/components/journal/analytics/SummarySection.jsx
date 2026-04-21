import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import StatCard from '../../portfolio/ui/StatCard'
import { fmtCur, fmtPct, fmt, clr } from '../../portfolio/lib/portfolioFormat'

export default function SummarySection({ enriched, closedTrades, monthlyStats, performanceData, insights, startingCapital }) {
  // Summary stats
  const stats = useMemo(() => {
    if (closedTrades.length === 0) return null
    const winners = closedTrades.filter(t => t.totalPL > 0)
    const losers = closedTrades.filter(t => t.totalPL <= 0)
    const grossGains = winners.reduce((s, t) => s + t.totalPL, 0)
    const grossLosses = Math.abs(losers.reduce((s, t) => s + t.totalPL, 0))

    return {
      totalTrades: closedTrades.length,
      winRate: (winners.length / closedTrades.length) * 100,
      avgR: closedTrades.reduce((s, t) => s + (t.rr || 0), 0) / closedTrades.length,
      expectancy: closedTrades.reduce((s, t) => s + t.totalPL, 0) / closedTrades.length,
      avgHold: closedTrades.reduce((s, t) => s + t.holdingDays, 0) / closedTrades.length,
      profitFactor: grossLosses > 0 ? grossGains / grossLosses : Infinity,
    }
  }, [closedTrades])

  if (!stats) {
    return <div className="text-center py-16 text-[var(--color-text-muted)]">No closed trades to analyze.</div>
  }

  return (
    <div className="space-y-5">
      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard label="Total Trades" value={stats.totalTrades} />
        <StatCard label="Win Rate" value={fmtPct(stats.winRate)} colorClass={stats.winRate >= 50 ? 'text-green-600' : 'text-red-500'} />
        <StatCard label="Avg R-Multiple" value={`${fmt(stats.avgR, 1)}R`} colorClass={stats.avgR >= 1 ? 'text-green-600' : 'text-red-500'} />
        <StatCard label="Expectancy" value={fmtCur(stats.expectancy)} colorClass={clr(stats.expectancy)} />
        <StatCard label="Avg Hold" value={`${fmt(stats.avgHold, 0)}d`} />
        <StatCard label="Profit Factor" value={fmt(stats.profitFactor, 2)} colorClass={stats.profitFactor >= 1 ? 'text-green-600' : 'text-red-500'} />
      </div>

      {/* Equity curve */}
      {performanceData.length > 1 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            Equity Curve
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${v.toFixed(0)}%`} />
              <Tooltip
                contentStyle={{ fontSize: 11, background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
                formatter={(v, name) => [`${Number(v).toFixed(2)}%`, name === 'returnPct' ? 'Portfolio' : name]}
                labelFormatter={l => l}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="returnPct" name="Portfolio" stroke="#5b8fa8" dot={false} strokeWidth={2} />
              {performanceData[0]?.SPY != null && (
                <Line type="monotone" dataKey="SPY" name="SPY" stroke="#999" dot={false} strokeWidth={1} strokeDasharray="4 2" />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Monthly performance table */}
      {monthlyStats.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            Monthly Performance
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  {['Month', 'Return%', '# Trades', 'Win%', 'Avg R', 'Max Gain%', 'Max Loss%', 'Days(W)', 'Days(L)'].map(h => (
                    <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {monthlyStats.map((m, i) => (
                  <tr key={m.month} className={i % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'}>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] font-medium">{m.month}</td>
                    <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${clr(m.monthlyRetPct)}`}>{fmtPct(m.monthlyRetPct)}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.totalTrades}</td>
                    <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${m.winPct >= 50 ? 'text-green-600' : 'text-red-500'}`}>{m.totalTrades > 0 ? fmtPct(m.winPct) : '—'}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.totalTrades > 0 ? fmt(m.returnPct / (m.totalTrades || 1), 1) : '—'}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-green-600">{m.largestGain > 0 ? fmtPct(m.largestGain) : '—'}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-red-500">{m.largestLoss < 0 ? fmtPct(m.largestLoss) : '—'}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.avgHoldWin > 0 ? fmt(m.avgHoldWin, 0) : '—'}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.avgHoldLoss > 0 ? fmt(m.avgHoldLoss, 0) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Insights */}
      {insights.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            Insights
          </h3>
          <div className="space-y-2">
            {insights.map((ins, i) => (
              <div key={i} className="flex gap-2 text-sm">
                <span className={`flex-shrink-0 ${ins.type === 'positive' ? 'text-green-600' : ins.type === 'warning' ? 'text-amber-500' : 'text-[var(--color-text-muted)]'}`}>
                  {ins.type === 'positive' ? '+' : ins.type === 'warning' ? '!' : '-'}
                </span>
                <span className="text-[var(--color-text-secondary)]">{ins.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
