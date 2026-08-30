import { todayET } from '../../../lib/tradingDate'

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

/* The market's day, not the browser's. This was `toISOString()` — today in
   UTC — until 2026-08-31; on a JST clock that names tomorrow's session for the
   whole of Andy's morning, which is when he reads the page. See
   `src/lib/tradingDate.js` for what that broke. */
export const todayStr = () => todayET()

/* Sector identity — eleven muted hues that say WHICH sector, never which
   side. Kept off the pair's blue and red so a sector chip can never be read
   as a direction. */
export const SECTOR_COLORS = [
  '#7a8b94', '#8b9480', '#9c9078', '#8d8397', '#997f7f',
  '#75908c', '#918a70', '#8a7d92', '#7f8b9c', '#94867a', '#7e8f7e',
]

// 'Options Port' unwired 2026-08-17 (Andy: 暂时下线). This array and
// PortfolioLayout's TAB_KEYS are indexed together — they must stay the
// same length, which is why removing one meant touching both.
export const TABS = ['Overview', 'Exposure', 'Risk']
