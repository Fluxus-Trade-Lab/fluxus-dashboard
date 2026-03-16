import { signalColor, signalLabel } from '../../lib/format'

const TICKERS = ['SPY', 'QQQ', 'IWM', 'RSP']

function signalTextColor(color) {
  const map = {
    green: 'text-green-600',
    yellow: 'text-amber-600',
    orange: 'text-orange-500',
    red: 'text-red-500',
  }
  return map[color] || 'text-[var(--color-text-muted)]'
}

export default function MarketConditions({ signals }) {
  if (!signals) return null

  return (
    <div>
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        Market Conditions
      </h3>
      <div className="flex flex-col gap-1.5">
        {TICKERS.map((ticker) => {
          const s = signals[ticker]
          if (!s) return null
          return (
            <div
              key={ticker}
              className="grid grid-cols-[48px_1fr_auto] items-center gap-2"
            >
              <span className="font-mono text-sm text-[var(--color-text-bold)]">
                {ticker}
              </span>
              <span className="font-mono text-xs text-[var(--color-text)]">
                {s.close != null ? s.close.toFixed(2) : '--'}
              </span>
              <span
                className={`text-[10px] font-medium uppercase tracking-wide ${signalTextColor(s.color)}`}
              >
                {signalLabel(s.signal)}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
