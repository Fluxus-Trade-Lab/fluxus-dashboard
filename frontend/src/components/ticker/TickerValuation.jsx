/**
 * Valuation Snapshot — 2-column table of valuation + balance-sheet metrics.
 */
export default function TickerValuation({ tickerData }) {
  const info = tickerData?.info
  if (!info) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[14px]">Valuation Snapshot</div>
        <div className="text-[var(--color-text-muted)] text-[14px]">No valuation data available.</div>
      </div>
    )
  }

  const rows = [
    ['Market Cap', formatLarge(info.marketCap, '$')],
    ['Enterprise Value', formatLarge(info.enterpriseValue, '$')],
    ['Total Revenue (TTM)', formatLarge(info.totalRevenue, '$')],
    ['P/S TTM', formatRatio(info.priceToSalesTrailing12Months)],
    ['EV / Sales TTM', formatRatio(info.enterpriseToRevenue)],
    ['Fwd P/E', formatRatio(info.forwardPE)],
    ['P/E TTM', info.trailingPE != null && info.trailingPE < 0 ? 'neg.' : formatRatio(info.trailingPE)],
    ['Gross Margin', formatPct(info.grossMargins)],
    ['Op Margin', formatPct(info.operatingMargins)],
    ['Profit Margin', formatPct(info.profitMargins)],
    ['Total Cash', formatLarge(info.totalCash, '$')],
    ['Free Cash Flow', formatLarge(info.freeCashflow, '$')],
    ['Total Debt', formatLarge(info.totalDebt, '$')],
    ['Debt / Equity', formatRatio(info.debtToEquity ? info.debtToEquity / 100 : null)],
    ['Current Ratio', formatRatio(info.currentRatio)],
    ['Beta', formatRatio(info.beta)],
  ]

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[14px]">Valuation Snapshot</div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-[12.5px]">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between border-b border-[var(--color-border-light)] pb-1">
            <span className="text-[var(--color-text-muted)]">{label}</span>
            <span className="tabular-nums font-semibold">{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function formatLarge(v, prefix = '') {
  if (v == null) return '—'
  const abs = Math.abs(v)
  const sign = v < 0 ? '-' : ''
  if (abs >= 1e12) return `${sign}${prefix}${(abs / 1e12).toFixed(2)}T`
  if (abs >= 1e9) return `${sign}${prefix}${(abs / 1e9).toFixed(2)}B`
  if (abs >= 1e6) return `${sign}${prefix}${(abs / 1e6).toFixed(0)}M`
  return `${sign}${prefix}${abs.toFixed(0)}`
}

function formatPct(v) {
  if (v == null) return '—'
  return `${(v * 100).toFixed(1)}%`
}

function formatRatio(v) {
  if (v == null) return '—'
  if (v <= 0) return 'neg.'
  return `${v.toFixed(2)}×`
}
