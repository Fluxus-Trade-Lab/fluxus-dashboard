import { fmtCur } from '../portfolio/lib/portfolioFormat'

/**
 * Trend & Indicators — narrative reads of MAs, RSI, ATR-based stop sizing,
 * 52W position, volatility regime, setup type.
 */
export default function TickerTrendIndicators({ tickerData }) {
  const t = tickerData?.technicals
  const price = tickerData?.current_price
  if (!t) {
    return (
      <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
        <div className="font-semibold mb-3 text-[14px]">Trend & Indicators</div>
        <div className="text-[var(--color-text-muted)] text-[14px]">No technical data available.</div>
      </div>
    )
  }

  // Derived reads
  const maStack = (() => {
    if (!t.ma20 || !t.ma50 || !t.ma200) return '—'
    if (t.ma20 > t.ma50 && t.ma50 > t.ma200) return 'MA20 > MA50 > MA200 — Golden alignment'
    if (t.ma20 < t.ma50 && t.ma50 < t.ma200) return 'MA20 < MA50 < MA200 — Death cross alignment'
    return 'Mixed'
  })()

  const trend = (() => {
    if (!price || !t.ma20 || !t.ma50 || !t.ma200) return '—'
    if (price > t.ma20 && price > t.ma50 && price > t.ma200) return 'Above MA20 / MA50 / MA200 — stacked bullish'
    if (price < t.ma20 && price < t.ma50 && price < t.ma200) return 'Below MA20 / MA50 / MA200 — stacked bearish'
    if (price > t.ma200 && price < t.ma20) return 'Long-term up, short-term pullback'
    return 'Mixed signals'
  })()

  const rsi = t.rsi14
  const rsiRead = rsi == null ? '—' :
    rsi >= 70 ? `${rsi.toFixed(1)} — overbought` :
    rsi >= 60 ? `${rsi.toFixed(1)} — strong, not overbought` :
    rsi >= 40 ? `${rsi.toFixed(1)} — neutral` :
    rsi >= 30 ? `${rsi.toFixed(1)} — weak` :
    `${rsi.toFixed(1)} — oversold`

  const volRegime = (() => {
    const pct = t.atr14_pct
    if (pct == null) return '—'
    if (pct >= 8) return 'High — wide stops needed'
    if (pct >= 5) return 'Elevated — high-beta'
    if (pct >= 3) return 'Normal'
    return 'Low'
  })()

  const setupType = (() => {
    if (!price || !t.ma20 || !t.ma50 || !t.high_52w) return '—'
    const above_long_term = price > t.ma50 && price > t.ma200
    const near_high = price >= t.high_52w * 0.92
    const pullback_to_ma = Math.abs(price - t.ma20) / price < 0.04 && price > t.ma50
    if (above_long_term && near_high) return 'Trending — near 52W high'
    if (pullback_to_ma) return 'Pullback in uptrend'
    if (price < t.ma50) return 'Trend break / downtrend'
    return 'Consolidation'
  })()

  const stop15Atr = t.atr14 ? t.atr14 * 1.5 : null

  const rows = [
    ['Trend (price vs MAs)', trend],
    ['MA stack', maStack],
    ['RSI(14)', rsiRead],
    ['ATR(14) — stop sizing', t.atr14 ? `${fmtCur(t.atr14)} (${t.atr14_pct.toFixed(1)}% of price)` : '—'],
    ['1.5× ATR stop ref', stop15Atr ? `≈ ${fmtCur(stop15Atr)} wide` : '—'],
    ['Position in 52W range', t.position_in_52w_range_pct != null ? `${t.position_in_52w_range_pct.toFixed(1)}% (low → high)` : '—'],
    ['Volatility regime', volRegime],
    ['Setup type', setupType],
  ]

  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] p-5">
      <div className="font-semibold mb-3 text-[14px]">Trend & Indicators</div>
      <table className="w-full text-[12.5px]">
        <thead>
          <tr className="text-left text-[10px] text-[var(--color-text-muted)] uppercase tracking-wide border-b border-[var(--color-border-light)]">
            <th className="px-2 py-1.5">Indicator</th>
            <th className="px-2 py-1.5">Read</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label} className="border-b border-[var(--color-border-light)]">
              <td className="px-2 py-1.5 font-semibold whitespace-nowrap">{label}</td>
              <td className="px-2 py-1.5 text-[var(--color-text-secondary)]">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
