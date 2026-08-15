export const RISK_FREE_RATE = 0.043
export const MASK = '****'

export const fmt = (n, d = 2) =>
  n == null || isNaN(n) ? '—' : Number(n).toFixed(d)

export const fmtCur = (n) =>
  n == null || isNaN(n)
    ? '—'
    : '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const fmtPct = (n) =>
  n == null || isNaN(n) ? '—' : `${Number(n).toFixed(2)}%`

export const fmtPctSigned = (n) =>
  n == null || isNaN(n) ? '—' : `${n > 0 ? '+' : ''}${Number(n).toFixed(2)}%`

/** Privacy-aware formatters — return MASK when hidden */
export const priv = (val, formatter, hidden) => hidden ? MASK : formatter(val)

/** Returns a Tailwind text-color class */
export const clr = (v) =>
  v > 0 ? 'text-[var(--color-profit)]' : v < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-text-secondary)]'

/** Returns hex for Recharts / inline use */
export const clrHex = (v) =>
  v > 0 ? 'var(--color-profit)' : v < 0 ? 'var(--color-loss)' : 'var(--color-neutral)'

export const daysBetween = (a, b) =>
  Math.max(0, Math.round((new Date(b) - new Date(a)) / 86400000))

export const todayStr = () => new Date().toISOString().split('T')[0]

/* Sector identity — eleven muted hues that say WHICH sector, never which
   side. Kept off the pair's blue and red so a sector chip can never be read
   as a direction. */
export const SECTOR_COLORS = [
  '#7a8b94', '#8b9480', '#9c9078', '#8d8397', '#997f7f',
  '#75908c', '#918a70', '#8a7d92', '#7f8b9c', '#94867a', '#7e8f7e',
]

export const TABS = ['Overview', 'Exposure', 'Risk', 'Options Port']
