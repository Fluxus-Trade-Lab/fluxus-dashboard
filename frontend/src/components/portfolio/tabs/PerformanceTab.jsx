import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { usePortfolio } from '../context/PortfolioContext'
import { usePrices } from '../hooks/usePrices'
import StatCard from '../ui/StatCard'
import Button from '../ui/Button'
import { fmtPct, clr } from '../lib/portfolioFormat'

export default function PerformanceTab({ performanceData, totalReturnPct, riskMetrics }) {
  const { state } = usePortfolio()
  const { fetchFullHistory } = usePrices()

  // Compute SPY YTD return from benchmark history
  const spyYtd = (() => {
    const hist = state.benchmarkHistories?.SPY
    if (!hist?.length) return null
    const sorted = [...hist].sort((a, b) => a.date.localeCompare(b.date))
    const currentYear = new Date().getFullYear().toString()
    const ytdStart = sorted.find(h => h.date >= currentYear + '-01-01') || sorted[0]
    const ytdEnd = sorted[sorted.length - 1]
    return ytdStart.close > 0 ? ((ytdEnd.close - ytdStart.close) / ytdStart.close) * 100 : 0
  })()

  const hasSPY = state.benchmarkHistories?.SPY?.length > 0

  return (
    <div>
      {!hasSPY && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-md mb-4 text-xs text-[var(--color-accent)] flex items-center justify-between">
          <span>Load historical prices for the equity curve and SPY comparison.</span>
          <Button onClick={fetchFullHistory} disabled={state.loading}>
            {state.loading ? 'Loading...' : 'Load History'}
          </Button>
        </div>
      )}

      {performanceData.length > 2 ? (
        <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
          <div className="font-semibold mb-3 text-sm flex justify-between items-center">
            <span>Portfolio vs SPY</span>
            {hasSPY && (
              <Button variant="ghost" onClick={fetchFullHistory} disabled={state.loading}>
                {state.loading ? 'Loading...' : 'Refresh History'}
              </Button>
            )}
          </div>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10 }}
                tickFormatter={d => d.slice(5)}
                interval={Math.max(1, Math.floor(performanceData.length / 10))}
              />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${Number(v).toFixed(0)}%`} />
              <Tooltip formatter={v => `${Number(v).toFixed(2)}%`} />
              <Legend />
              <Line type="monotone" dataKey="returnPct" stroke="#2d5f8a" strokeWidth={2.5} dot={false} name="Portfolio" />
              {hasSPY && (
                <Line type="monotone" dataKey="SPY" stroke="#d4a574" strokeWidth={1.5} dot={false} name="SPY" strokeDasharray="4 4" />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="text-center py-16 text-[var(--color-text-muted)]">Need trades to build equity curve.</div>
      )}

      <div className="flex gap-4 flex-wrap mt-4">
        <StatCard label="Portfolio Return" value={fmtPct(totalReturnPct)} colorClass={clr(totalReturnPct)} />
        {spyYtd != null && <StatCard label="SPY YTD" value={fmtPct(spyYtd)} colorClass={clr(spyYtd)} />}
{/* Alpha shown on Risk tab with full context */}
      </div>
    </div>
  )
}
