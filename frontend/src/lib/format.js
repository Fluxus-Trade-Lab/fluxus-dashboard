export function fmtPct(val) {
  if (val == null || isNaN(val)) return '—'
  const pct = val * 100
  const sign = pct > 0 ? '+' : ''
  return `${sign}${pct.toFixed(1)}%`
}

/**
 * Neutral. This handed the money palette (profit/loss green-red) to six
 * market-half components, every one of them printing a naked figure with no
 * mark of its own to belong to. The encoding colour lives in marks; a signed
 * number already says which way it went.
 */
export function pctColor(val) {
  if (val == null || isNaN(val)) return 'text-[var(--color-text-muted)]'
  return 'text-[var(--color-text-secondary)]'
}

/** A badge IS a mark, so it keeps its colour — but on the site's tokens
 *  rather than raw Tailwind, and as a tint the figure sits on. */
export function atrBadgeColor(atrExt) {
  if (atrExt == null) return 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
  if (atrExt <= 4) return 'bg-[color-mix(in_srgb,var(--color-took)_28%,transparent)]'
  if (atrExt <= 6) return 'bg-[color-mix(in_srgb,var(--color-signal-caution)_20%,transparent)]'
  return 'bg-[color-mix(in_srgb,var(--color-refused)_26%,transparent)]'
}

/**
 * A / B / C is a rank, and a rank has no adverse pole — so it is drawn in ink
 * density, not in hue. It survived every colour audit until now because it
 * returned Tailwind class names (blue-500 / emerald-500 / amber-500) rather
 * than hex, which is exactly the shape the greps were looking for.
 *
 * The chip's letter is the surface, so each step keeps its own contrast:
 * 15.3 / 6.2 / 4.9 on light, 14.7 / 6.1 / 4.3 on dark.
 */
export function abcColor(abc) {
  if (abc === 'A') return 'bg-[var(--color-text)]'
  if (abc === 'B') return 'bg-[var(--color-text-secondary)]'
  return 'bg-[var(--color-text-muted)]'
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
