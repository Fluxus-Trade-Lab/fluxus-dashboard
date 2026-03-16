export function fmtPct(val) {
  if (val == null || isNaN(val)) return '—'
  const pct = val * 100
  const sign = pct > 0 ? '+' : ''
  return `${sign}${pct.toFixed(1)}%`
}

export function pctColor(val) {
  if (val == null || isNaN(val)) return 'text-[var(--color-text-muted)]'
  return val > 0 ? 'text-green-600' : val < 0 ? 'text-red-500' : 'text-[var(--color-text-secondary)]'
}

export function atrBadgeColor(atrExt) {
  if (atrExt == null) return 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
  if (atrExt <= 4) return 'bg-green-50 text-green-700'
  if (atrExt <= 6) return 'bg-amber-50 text-amber-700'
  return 'bg-red-50 text-red-700'
}

export function abcColor(abc) {
  if (abc === 'A') return 'bg-blue-500'
  if (abc === 'B') return 'bg-emerald-500'
  return 'bg-amber-500'
}

export function signalColor(color) {
  const map = {
    green: 'bg-green-500',
    yellow: 'bg-amber-600',
    orange: 'bg-orange-500',
    red: 'bg-red-500',
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
