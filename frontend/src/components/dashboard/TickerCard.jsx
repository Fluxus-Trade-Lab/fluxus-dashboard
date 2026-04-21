import { signalColor, signalLabel, signalTextColor } from '../../lib/format'

function formatPrice(val) {
  if (val == null) return '--'
  if (val >= 10000) return val.toLocaleString('en-US', { maximumFractionDigits: 0 })
  return val.toFixed(2)
}

function formatChange(val) {
  if (val == null || isNaN(val)) return '--'
  const pct = val * 100
  const sign = pct > 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

function changeColor(val) {
  if (val == null || isNaN(val)) return 'text-[var(--color-text-muted)]'
  return val > 0 ? 'text-[var(--color-profit)]' : val < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-text-secondary)]'
}

export default function TickerCard({ ticker, signal, etf }) {
  // signal data comes from signals.json (SPY, QQQ, IWM, BTC-USD, ^VIX)
  // etf data comes from etf_data.json (DIA, RSP, QQQE, GLD, TLT)
  // one or both may be present

  const price = signal?.close ?? etf?.close ?? null
  const change = etf?.change_pct ?? null
  const sigColor = signal?.color ?? null
  const sigLabel = signal?.signal ? signalLabel(signal.signal) : null

  // Display name mapping
  const displayName = ticker === 'BTC-USD' ? 'BTC' : ticker === '^VIX' ? 'VIX' : ticker

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3 min-w-[140px] flex-shrink-0">
      {/* Ticker + signal dot */}
      <div className="flex items-center gap-2 mb-1.5">
        {sigColor && (
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${signalColor(sigColor)}`} />
        )}
        <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          {displayName}
        </span>
      </div>

      {/* Price */}
      <div className="font-mono text-xl font-semibold text-[var(--color-text-bold)] leading-tight">
        {formatPrice(price)}
      </div>

      {/* Change % and/or signal label */}
      <div className="flex items-center gap-2 mt-1">
        {change != null && (
          <span className={`font-mono text-xs ${changeColor(change)}`}>
            {formatChange(change)}
          </span>
        )}
        {sigLabel && (
          <span className={`text-[10px] font-medium uppercase tracking-wide ${signalTextColor(sigColor)}`}>
            {sigLabel}
          </span>
        )}
      </div>
    </div>
  )
}
