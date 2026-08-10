import NAMES from './etfNames.json'

/**
 * Relative strength for an ETF: its return minus the benchmark's, same window.
 *
 * This is the definition the pipeline already uses — rs_engine.relative_strength
 * subtracts the benchmark's bucket from the row's, and excess_3m is "the
 * three-month return minus the benchmark's". Reusing it means the number beside
 * an industry means the same thing as the number beside a theme.
 *
 * It is NOT `rrs_1w/1m/3m` from etf_data, which an earlier version of this file
 * used and which was wrong here. Those are the percentile of today's rolling
 * volatility-adjusted RS reading *inside the last N sessions* — a rank in time,
 * not strength against SPY. The two disagree hard: REMX was down 3.4% on the
 * month and 5.8pp behind SPY while its rrs_1w read 100, because today was its
 * strongest reading of a bad stretch. Same three letters, different question.
 *
 * Units are percentage points of excess, not a 0-100 score. A rank would need a
 * cohort to rank against and would hide the size of the lead, which is the part
 * that decides whether a group is worth the attention.
 */
export const RS_WINDOWS = [
  { key: 'change_pct', label: '1D', note: 'today, against SPY' },
  { key: 'perf_1w', label: '1W', note: 'five sessions, against SPY' },
  { key: 'perf_1m', label: '1M', note: 'twenty-one sessions, against SPY' },
]

/** Performance columns, for sorting leaders and printing the raw move. */
export const PERF_WINDOWS = {
  '1D': 'change_pct',
  '1W': 'perf_1w',
  '1M': 'perf_1m',
  '3M': 'perf_3m',
}

/**
 * Excess over the benchmark for one window, in percentage points.
 * Null when either side is missing — an unmeasured leg must not read as zero.
 */
export function excessOver(etf, benchmark, key) {
  const mine = etf?.[key]
  const theirs = benchmark?.[key]
  if (!Number.isFinite(mine) || !Number.isFinite(theirs)) return null
  return (mine - theirs) * 100
}

/** Display name, or null when the vendor had none — never a guess. */
export function etfName(ticker) {
  return NAMES[ticker] ?? null
}

/**
 * Excess → background tint. Three steps, not a gradient: the eye cannot read a
 * continuous ramp back to a number, and the number is printed on top of it.
 *
 * The cuts are at ±2 percentage points against SPY, which is a real move at
 * these horizons rather than noise, and the same cut is used at every window so
 * a row's colour can be compared across columns.
 */
export function rsTone(excess) {
  if (excess == null) return { color: 'var(--color-text-muted)' }
  if (excess >= 2) return { background: 'color-mix(in srgb, var(--color-took) 30%, transparent)' }
  if (excess <= -2) return { background: 'color-mix(in srgb, var(--color-refused) 26%, transparent)' }
  return { color: 'var(--color-text-secondary)' }
}

/** One decimal, always signed: the sign is the whole point of an excess. */
export function fmtExcess(v) {
  if (v == null) return '—'
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}`
}
