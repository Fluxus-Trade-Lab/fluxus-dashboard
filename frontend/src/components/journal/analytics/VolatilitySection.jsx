import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import StatCard from '../../portfolio/ui/StatCard'
import { fmt, fmtPct, fmtCur } from '../../portfolio/lib/portfolioFormat'

export default function VolatilitySection({ volContrib, portfolioVol, spyVol, dailyPrices, spyHistory }) {

  // Merge rolling vol series for chart
  const rollingData = useMemo(() => {
    if (!portfolioVol?.rolling?.length) return []

    const byDate = {}
    portfolioVol.rolling.forEach(r => {
      byDate[r.date] = { date: r.date, portfolioVol: Number(r.portfolioVol.toFixed(1)) }
    })
    if (spyVol?.rolling) {
      spyVol.rolling.forEach(r => {
        if (byDate[r.date]) byDate[r.date].spyVol = Number(r.spyVol.toFixed(1))
        else byDate[r.date] = { date: r.date, spyVol: Number(r.spyVol.toFixed(1)) }
      })
    }

    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date))
  }, [portfolioVol, spyVol])

  // High-beta watchlist
  const highBeta = useMemo(() =>
    volContrib.filter(v => v.beta != null && v.beta > 1.5),
    [volContrib]
  )

  return (
    <div className="space-y-5">
      {/* Portfolio vol summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          label="Portfolio Vol (ann.)"
          value={portfolioVol ? fmtPct(portfolioVol.annualizedVol) : '—'}
          colorClass={portfolioVol && portfolioVol.annualizedVol > 25 ? 'text-amber-500' : ''}
        />
        <StatCard
          label="SPY Vol (ann.)"
          value={spyVol ? fmtPct(spyVol.annualizedVol) : '—'}
        />
        <StatCard
          label="Vol Ratio"
          value={portfolioVol && spyVol ? fmt(portfolioVol.annualizedVol / spyVol.annualizedVol, 2) + 'x' : '—'}
          sub={portfolioVol && spyVol ? (portfolioVol.annualizedVol / spyVol.annualizedVol > 1.5 ? 'High relative vol' : 'Moderate') : ''}
          colorClass={portfolioVol && spyVol && portfolioVol.annualizedVol / spyVol.annualizedVol > 1.5 ? 'text-amber-500' : ''}
        />
        <StatCard
          label="Daily Vol"
          value={portfolioVol ? fmtPct(portfolioVol.dailyVol) : '—'}
        />
      </div>

      {/* Rolling vol chart */}
      {rollingData.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            Rolling 20-Day Volatility
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={rollingData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${v}%`} />
              <Tooltip
                contentStyle={{ fontSize: 11, background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
                formatter={(v, name) => [`${v}%`, name]}
                labelFormatter={l => l}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="portfolioVol" name="Portfolio" stroke="#5b8fa8" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="spyVol" name="SPY" stroke="#999" dot={false} strokeWidth={1} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Per-position vol contribution */}
      {volContrib.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            Per-Position Volatility Contribution
          </h3>
          {volContrib.slice(0, 3).some(v => v.volContribution != null) && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-md px-3 py-2 text-xs text-amber-400 mb-4">
              Top 3 vol contributors: {volContrib.slice(0, 3).filter(v => v.volContribution != null).map(v => `${v.ticker} (${fmt(v.volContribution, 2)}%)`).join(', ')}
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  {['Ticker', 'Weight%', 'Daily Vol', 'Ann. Vol', 'Beta', 'Vol Contrib%'].map(h => (
                    <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {volContrib.map((v, i) => (
                  <tr key={v.id || v.ticker + i} className={i % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'}>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] font-medium">{v.ticker}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(v.weight, 1)}%</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{v.dailyVol != null ? fmtPct(v.dailyVol) : '—'}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{v.annualizedVol != null ? fmtPct(v.annualizedVol) : '—'}</td>
                    <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${v.beta != null && v.beta > 1.5 ? 'text-amber-500 font-semibold' : ''}`}>
                      {v.beta != null ? fmt(v.beta, 2) : '—'}
                    </td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold">{v.volContribution != null ? fmtPct(v.volContribution) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* High-beta watchlist */}
      {highBeta.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            High-Beta Watchlist (Beta &gt; 1.5)
          </h3>
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-md px-3 py-2 text-xs text-amber-400 mb-4">
            {highBeta.length} position{highBeta.length > 1 ? 's' : ''} with beta above 1.5. Consider sizing these smaller or widening stops.
          </div>
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                {['Ticker', 'Beta', 'Weight%', 'Mkt Val', 'SPY Equiv'].map(h => (
                  <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {highBeta.map((v, i) => (
                <tr key={v.id || v.ticker + i} className={i % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'}>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] font-medium">{v.ticker}</td>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-amber-500 font-semibold">{fmt(v.beta, 2)}</td>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmt(v.weight, 1)}%</td>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(v.mktVal)}</td>
                  <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(v.mktVal * v.beta)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
