/**
 * Quarterly Metrics — 5-quarter table of Revenue / YoY / Gross Profit / GM% /
 * Op Inc / EPS / Cash / Op CF.
 */
export default function TickerQuarterlyMetrics({ tickerData }) {
  const quarters = tickerData?.quarterly_metrics || []
  if (!quarters.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[14px]">Key Quarterly Metrics</div>
        <div className="text-[var(--color-text-muted)] text-[14px]">No quarterly data available.</div>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5 overflow-x-auto">
      <div className="font-semibold mb-3 text-[14px]">Key Quarterly Metrics</div>
      <table className="w-full text-[12.5px]">
        <thead>
          <tr className="text-left text-[10px] text-[var(--color-text-muted)] uppercase tracking-wide border-b border-[var(--color-border-light)]">
            <th className="px-2 py-1.5">Period</th>
            <th className="px-2 py-1.5 text-right">Revenue</th>
            <th className="px-2 py-1.5 text-right">YoY</th>
            <th className="px-2 py-1.5 text-right">Gross Profit</th>
            <th className="px-2 py-1.5 text-right">GM%</th>
            <th className="px-2 py-1.5 text-right">Op Inc</th>
            <th className="px-2 py-1.5 text-right">EPS</th>
            <th className="px-2 py-1.5 text-right">Cash</th>
            <th className="px-2 py-1.5 text-right">Op CF</th>
          </tr>
        </thead>
        <tbody>
          {quarters.map((q, i) => (
            <tr key={i} className="border-b border-[var(--color-border-light)]">
              <td className="px-2 py-1.5">{String(q.period_end).slice(0, 10)}</td>
              <td className="px-2 py-1.5 text-right tabular-nums">{fmtMoney(q.revenue)}</td>
              <td className={`px-2 py-1.5 text-right tabular-nums ${q.yoy_pct == null ? '' : q.yoy_pct >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                {q.yoy_pct == null ? '—' : `${q.yoy_pct >= 0 ? '+' : ''}${q.yoy_pct.toFixed(1)}%`}
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">{fmtMoney(q.gross_profit)}</td>
              <td className="px-2 py-1.5 text-right tabular-nums">{q.gross_margin_pct == null ? '—' : `${q.gross_margin_pct.toFixed(1)}%`}</td>
              <td className={`px-2 py-1.5 text-right tabular-nums ${q.operating_income == null ? '' : q.operating_income >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                {fmtMoney(q.operating_income)}
              </td>
              <td className={`px-2 py-1.5 text-right tabular-nums ${q.eps == null ? '' : q.eps >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                {q.eps == null ? '—' : `${q.eps >= 0 ? '$' : '-$'}${Math.abs(q.eps).toFixed(2)}`}
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">{fmtMoney(q.cash)}</td>
              <td className={`px-2 py-1.5 text-right tabular-nums ${q.operating_cashflow == null ? '' : q.operating_cashflow >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                {fmtMoney(q.operating_cashflow)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function fmtMoney(v) {
  if (v == null) return '—'
  const abs = Math.abs(v)
  const sign = v < 0 ? '-' : ''
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(2)}B`
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(1)}M`
  if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(0)}K`
  return `${sign}$${abs.toFixed(0)}`
}
