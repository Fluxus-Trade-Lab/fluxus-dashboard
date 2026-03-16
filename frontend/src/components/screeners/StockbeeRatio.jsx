export default function StockbeeRatio({ data }) {
  if (!data) return null

  const ratio = data.ratio_5d
  const ratioColor =
    ratio < 0.5
      ? 'text-red-500'
      : ratio <= 1.0
        ? 'text-amber-600'
        : 'text-green-600'

  const signalColor =
    data.signal === 'COLLAPSE' || data.signal === 'RISK_OFF'
      ? 'text-red-500'
      : data.signal === 'CAUTION' || data.signal === 'WARNING'
        ? 'text-amber-600'
        : 'text-green-600'

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        Stockbee Ratio
      </h3>

      <div className="flex items-baseline gap-3 mb-3">
        <span className={`text-3xl font-mono font-medium ${ratioColor}`}>
          {ratio != null ? ratio.toFixed(4) : '\u2014'}
        </span>
        <span className={`text-xs font-medium uppercase tracking-wide ${signalColor}`}>
          {data.signal}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            Gainers Today
          </span>
          <span className="font-mono text-[var(--color-text)]">{data.gainers_today}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            Losers Today
          </span>
          <span className="font-mono text-[var(--color-text)]">{data.losers_today}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            Gainers 5D
          </span>
          <span className="font-mono text-[var(--color-text)]">{data.gainers_5d}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            Losers 5D
          </span>
          <span className="font-mono text-[var(--color-text)]">{data.losers_5d}</span>
        </div>
      </div>
    </div>
  )
}
