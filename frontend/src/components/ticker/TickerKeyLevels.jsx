import { fmtCur } from '../portfolio/lib/portfolioFormat'

/**
 * Key Levels table — 52W high/low, recent highs/lows, MA20/50/200 prices,
 * with notes. Sourced from per-ticker JSON technicals.
 */
export default function TickerKeyLevels({ tickerData }) {
  const t = tickerData?.technicals
  const price = tickerData?.current_price
  if (!t) {
    return (
      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
        <div className="font-semibold mb-3 text-sm">Key Levels</div>
        <div className="text-[var(--color-text-muted)] text-sm">No technical data available.</div>
      </div>
    )
  }

  const rows = [
    ['52W High / Resistance', t.high_52w, 'Major upside breakout level'],
    ['20-day high', t.high_20d, 'Reclaim = continuation'],
    ['MA20', t.ma20, t.ma20 && price ? (price > t.ma20 ? 'Price above — bullish first support' : 'Price below — broken first support') : '—'],
    ['MA50', t.ma50, t.ma50 && price ? (price > t.ma50 ? 'Trend support intact' : 'Trend support lost — caution') : '—'],
    ['MA200', t.ma200, t.ma200 && price ? (price > t.ma200 ? 'Above long-term trend' : 'Below long-term trend') : '—'],
    ['10-day low', t.low_10d, 'Short-term swing low'],
    ['5-day low', t.low_5d, 'Last-week structural floor'],
    ['52W Low', t.low_52w, 'Reference only'],
  ]

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
      <div className="font-semibold mb-3 text-sm">Key Levels</div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-[10px] text-[var(--color-text-muted)] uppercase tracking-wide border-b border-[var(--color-border-light)]">
            <th className="px-2 py-1.5">Level</th>
            <th className="px-2 py-1.5 text-right">Price</th>
            <th className="px-2 py-1.5">Notes</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, value, note]) => (
            <tr key={label} className="border-b border-[var(--color-border-light)]">
              <td className="px-2 py-1.5 font-semibold">{label}</td>
              <td className="px-2 py-1.5 text-right tabular-nums">{value != null ? fmtCur(value) : '—'}</td>
              <td className="px-2 py-1.5 text-[var(--color-text-muted)] text-[11px]">{note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
