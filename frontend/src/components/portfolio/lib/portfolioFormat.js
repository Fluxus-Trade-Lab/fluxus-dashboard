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
  v > 0 ? 'text-green-600' : v < 0 ? 'text-red-500' : 'text-stone-500'

/** Returns hex for Recharts / inline use */
export const clrHex = (v) =>
  v > 0 ? '#16a34a' : v < 0 ? '#dc2626' : '#78716c'

export const daysBetween = (a, b) =>
  Math.max(0, Math.round((new Date(b) - new Date(a)) / 86400000))

export const todayStr = () => new Date().toISOString().split('T')[0]

export const SECTOR_COLORS = [
  '#5b8fa8', '#8fbc8f', '#d4a574', '#9b8ec2', '#c7796d',
  '#6db6b0', '#b8a960', '#a87fb8', '#7da6c4', '#c4917d', '#82b882',
]

export const TABS = ['P/L', 'Exposure', 'Performance', 'Monthly', 'Risk', '3-Stop Sim', 'Options']
