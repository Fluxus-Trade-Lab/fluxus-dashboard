import { atrBadgeColor } from '../../lib/format'

export default function TickerGrid({ tickers }) {
  if (!tickers || tickers.length === 0) return null

  return (
    <div className="flex flex-wrap gap-1">
      {tickers.map((t, i) => (
        <span
          key={`${t.ticker}-${i}`}
          className={`px-1.5 py-0.5 rounded text-[11px] font-mono font-medium ${atrBadgeColor(t.atr_ext)}`}
        >
          {t.ticker}
        </span>
      ))}
    </div>
  )
}
