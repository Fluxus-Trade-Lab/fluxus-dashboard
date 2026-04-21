export function fmtPct(val) {
  if (val == null || isNaN(val)) return '—'
  const pct = val * 100
  const sign = pct > 0 ? '+' : ''
  return `${sign}${pct.toFixed(1)}%`
}

export function pctColor(val) {
  if (val == null || isNaN(val)) return 'text-[var(--color-text-muted)]'
  return val > 0 ? 'text-[var(--color-profit)]' : val < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-text-secondary)]'
}

export function atrBadgeColor(atrExt) {
  if (atrExt == null) return 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
  if (atrExt <= 4) return 'bg-green-500/10 text-[var(--color-profit)]'
  if (atrExt <= 6) return 'bg-amber-500/10 text-[var(--color-signal-caution)]'
  return 'bg-red-500/10 text-[var(--color-loss)]'
}

export function abcColor(abc) {
  if (abc === 'A') return 'bg-blue-500'
  if (abc === 'B') return 'bg-emerald-500'
  return 'bg-amber-500'
}

export function signalColor(color) {
  const map = {
    green: 'bg-[var(--color-signal-power3)]',
    yellow: 'bg-[var(--color-signal-caution)]',
    orange: 'bg-[var(--color-signal-warning)]',
    red: 'bg-[var(--color-signal-riskoff)]',
  }
  return map[color] || 'bg-[var(--color-text-muted)]'
}

export function signalLabel(signal) {
  const map = {
    POWER_3: 'POWER 3',
    CAUTION: 'CAUTION',
    WARNING: 'WARNING',
    RISK_OFF: 'RISK OFF',
  }
  return map[signal] || signal
}

export function signalTextColor(color) {
  const map = {
    green: 'text-[var(--color-signal-power3)]',
    yellow: 'text-[var(--color-signal-caution)]',
    orange: 'text-[var(--color-signal-warning)]',
    red: 'text-[var(--color-signal-riskoff)]',
  }
  return map[color] || 'text-[var(--color-text-muted)]'
}

// For values already in percent (e.g., pct_to_pivot = 0.1 means 0.1%)
export function fmtPctRaw(val) {
  if (val == null || isNaN(val)) return '—'
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(1)}%`
}

export function formatTimestamp(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  })
}
