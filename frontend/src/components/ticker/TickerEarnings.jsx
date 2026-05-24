/**
 * Earnings — next + last 4Q table.
 */
export default function TickerEarnings({ tickerData }) {
  const next = tickerData?.next_earnings || {}
  const history = tickerData?.earnings_history || []

  if (!next.date && history.length === 0) {
    return (
      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
        <div className="font-semibold mb-3 text-sm">Earnings</div>
        <div className="text-[var(--color-text-muted)] text-sm">No earnings data available.</div>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
      <div className="font-semibold mb-3 text-sm">Earnings — Next + Last 4Q</div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-[10px] text-[var(--color-text-muted)] uppercase tracking-wide border-b border-[var(--color-border-light)]">
            <th className="px-2 py-1.5">Period</th>
            <th className="px-2 py-1.5">Date</th>
            <th className="px-2 py-1.5 text-right">EPS Act / Est</th>
            <th className="px-2 py-1.5 text-right">Surprise %</th>
          </tr>
        </thead>
        <tbody>
          {next.date && (
            <tr className="bg-amber-500/5 border-b border-[var(--color-border-light)]">
              <td className="px-2 py-1.5 font-semibold text-[var(--color-signal-caution)]">Next</td>
              <td className="px-2 py-1.5">{String(next.date).slice(0, 10)}</td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                {next.eps_estimate != null ? `est ${Number(next.eps_estimate).toFixed(2)}` : '—'}
              </td>
              <td className="px-2 py-1.5 text-right text-[10px] text-[var(--color-text-muted)]">
                {next.revenue_estimate != null
                  ? `Rev est $${(next.revenue_estimate / 1e6).toFixed(0)}M`
                  : ''}
              </td>
            </tr>
          )}
          {history.slice(0, 4).map((row, i) => {
            const surprise = row.eps_surprise_pct
            const beat = surprise != null && surprise > 0
            return (
              <tr key={i} className="border-b border-[var(--color-border-light)]">
                <td className="px-2 py-1.5 text-[var(--color-text-secondary)]">{String(row.period_end).slice(0, 10)}</td>
                <td className="px-2 py-1.5 text-[10px] text-[var(--color-text-muted)]">—</td>
                <td className="px-2 py-1.5 text-right tabular-nums">
                  {fmtEps(row.eps_actual)} / {fmtEps(row.eps_estimate)}
                </td>
                <td className={`px-2 py-1.5 text-right tabular-nums ${surprise == null ? '' : beat ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                  {surprise == null ? '—' : `${beat ? '✓ ' : '✗ '}${(surprise * 100).toFixed(1)}%`}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function fmtEps(v) {
  if (v == null) return '—'
  return Number(v) >= 0 ? `$${Number(v).toFixed(2)}` : `-$${Math.abs(v).toFixed(2)}`
}
