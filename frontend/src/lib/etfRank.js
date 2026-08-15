import NAMES from './etfNames.json'

/**
 * Relative strength as a 0-99 score, on the scale the pipeline already uses.
 *
 * `pipeline/screeners/run_all.py::rank_tradeable` is the definition:
 *
 *     sub.rank(pct=True, na_option='bottom') * 99
 *
 * a cross-sectional percentile of the window's return, times 99 — the IBD
 * scale, which is where universe.json's `rs_1m` (perf_1m) and `rs_3m`
 * (perf_3m) come from. This file applies the same construction to ETFs, which
 * are not in universe.json and so have no rs_* of their own.
 *
 * COHORT. universe.json ranks a stock among ~3,000 tradeable names. Here the
 * cohort is the card's own group — eleven sectors, or the industry ETF list.
 * Same scale, different denominator, so a sector's 75 and a stock's 75 are not
 * the same claim. Every card that prints these says what the cohort was.
 *
 * NOT `rrs_1w/1m/3m` from etf_data, which an earlier version of this file used
 * and which is a different measurement wearing the same three letters: the
 * percentile of today's rolling reading *inside the last N sessions*, a rank in
 * time. REMX printed rrs_1w = 100 while sitting 5.8pp behind SPY on the month,
 * because today was its strongest reading of a bad stretch.
 */

/** The windows a card can rank on, nearest first. */
export const RS_WINDOWS = [
  { key: 'change_pct', label: '1D', note: 'today, ranked within this group' },
  { key: 'perf_1w', label: '1W', note: 'five sessions, ranked within this group' },
  { key: 'perf_1m', label: '1M', note: 'twenty-one sessions, ranked within this group' },
]

/** Performance columns, for sorting leaders and printing the raw move. */
export const PERF_WINDOWS = {
  '1D': 'change_pct',
  '1W': 'perf_1w',
  '1M': 'perf_1m',
  '3M': 'perf_3m',
}

/** The IBD scale tops out at 99, not 100 — kept so these read the same as
 *  universe.json's rs_* rather than almost the same. */
const SCALE = 99

/**
 * Percentile rank of each ETF within `etfs`, on `key`, as 0-99.
 *
 * Ties share a rank: two funds that returned the same cannot be ordered by
 * where they happened to sit in the array. Rows missing the column rank at the
 * bottom, matching `na_option='bottom'` upstream — a fund with no reading is
 * not a fund in the middle.
 */
export function rankWithin(etfs, key) {
  const rows = etfs ?? []
  if (rows.length < 2) return new Map()

  const scored = rows.filter((e) => Number.isFinite(e?.[key]))
  const missing = rows.filter((e) => !Number.isFinite(e?.[key]))
  const sorted = [...scored].sort((a, b) => a[key] - b[key])

  const out = new Map()
  // Missing values occupy the lowest positions, so real readings start above them.
  for (const e of missing) out.set(e.ticker, 0)

  const offset = missing.length
  const total = rows.length
  // First and last index of each tie block, in one pass each.
  const firstAt = new Map()
  const lastAt = new Map()
  sorted.forEach((e, i) => {
    if (!firstAt.has(e[key])) firstAt.set(e[key], i)
    lastAt.set(e[key], i)
  })
  for (const e of sorted) {
    // average rank of the tie block, 1-based, as pandas rank(pct=True) does
    const avg = offset + (firstAt.get(e[key]) + lastAt.get(e[key])) / 2 + 1
    out.set(e.ticker, Math.round((avg / total) * SCALE))
  }
  return out
}

/** All three windows at once, so a row can show its shape over time. */
export function rankAllWindows(etfs) {
  const out = {}
  for (const w of RS_WINDOWS) out[w.key] = rankWithin(etfs, w.key)
  return out
}

/** Display name, or null when the vendor had none — never a guess. */
export function etfName(ticker) {
  return NAMES[ticker] ?? null
}

/**
 * Score → background tint. Three steps, not a gradient: the eye cannot read a
 * continuous ramp back to a number, and the number is printed on top of it.
 * Top and bottom third, which is what a percentile makes meaningful.
 */
/* v3: an RS percentile is a position in a ranking, not a pole around zero, so
   the chip lives on the grey floor — strong third raised, weak third faded,
   middle plain. The bar beside it already carries the pair for the actual
   two-poled quantity (the move); tinting the rank as well was saying one
   thing twice in two vocabularies. */
export function rsTone(score) {
  if (score == null) return { color: 'var(--color-text-muted)' }
  if (score >= 67) return { background: 'var(--color-surface-raised)', color: 'var(--color-text-bold)' }
  if (score <= 33) return { color: 'var(--color-text-muted)' }
  return { color: 'var(--color-text-secondary)' }
}

export function fmtRs(v) {
  return v == null ? '—' : String(v)
}
