const SIGNAL_LABELS = {
  below_20sma: 'Price closes below 20 SMA',
  stoch_cross: 'Fast stochastic below slow stochastic',
  stoch_down: 'Fast & slow stochastic curved down',
  lower_lows: '3 consecutive days of lower lows',
  close_below_lows: 'Close lower than 3 previous lows',
}

export default function DangerPanel({ title, danger }) {
  if (!danger?.signals) return null
  const count = danger.count ?? 0
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-4 py-3">
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          {title}
        </h3>
        <span className={`text-[10px] font-mono ${count >= 4 ? 'text-[var(--color-loss)]' : count >= 2 ? 'text-[var(--color-signal-caution)]' : 'text-[var(--color-text-secondary)]'}`}>
          {count} / 5 active
        </span>
      </div>
      <ul className="space-y-1.5">
        {Object.entries(SIGNAL_LABELS).map(([key, label]) => {
          const active = danger.signals[key] === true
          return (
            <li key={key} className="flex items-center justify-between text-[11px]">
              <span className={active ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)]'}>
                {label}
              </span>
              <span className={`w-2 h-2 rounded-full ${active ? 'bg-[var(--color-loss)]' : 'bg-[var(--color-border)]'}`} />
            </li>
          )
        })}
      </ul>
    </div>
  )
}
