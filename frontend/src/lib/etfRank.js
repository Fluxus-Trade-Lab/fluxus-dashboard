import NAMES from './etfNames.json'

/**
 * Relative strength for an ETF, straight off the pipeline.
 *
 * `rrs_1w/1m/3m` are computed in pipeline/adapters/yfinance_adapter.py as the
 * percentile of today's rolling volatility-adjusted RS-vs-SPY inside the last
 * 5 / 21 / 63 sessions. 100 means today is the strongest reading of that
 * stretch, 0 the weakest. It is a rank in time, not a return, and not a
 * cross-sectional rank against other funds.
 *
 * The front end does NOT recompute this. An earlier version of this file
 * ranked each fund against its group here, which was a second definition of
 * "RS" living in the UI — same three letters, different construction, and no
 * way for a reader to know which one they were looking at.
 *
 * There is no 1-day window on purpose: a percentile needs something to rank
 * against and a single session ranks against nothing.
 */
export const RS_WINDOWS = [
  { key: 'rrs_1w', label: '1W', note: 'percentile within the last 5 sessions' },
  { key: 'rrs_1m', label: '1M', note: 'percentile within the last 21 sessions' },
  { key: 'rrs_3m', label: '3M', note: 'percentile within the last 63 sessions' },
]

/** Performance columns, for the leader/laggard sort and the printed change. */
export const PERF_WINDOWS = {
  '1D': 'change_pct',
  '1W': 'perf_1w',
  '1M': 'perf_1m',
}

/** The RS window that matches a performance window, so a row's rank and its
 *  change describe the same stretch of time. */
export const RS_FOR_PERF = { '1D': 'rrs_1w', '1W': 'rrs_1w', '1M': 'rrs_1m' }

/** Display name, or null when the vendor had none — never a guess. */
export function etfName(ticker) {
  return NAMES[ticker] ?? null
}

/**
 * Rank → background tint. Three steps, not a gradient: the eye cannot read a
 * continuous ramp back to a number, and the number is printed on top of it.
 * Strong / middle / weak is all the fill is asked to carry.
 */
export function rankTone(rank) {
  if (rank == null) return { color: 'var(--color-text-muted)' }
  if (rank >= 67) return { background: 'color-mix(in srgb, var(--color-took) 30%, transparent)' }
  if (rank <= 33) return { background: 'color-mix(in srgb, var(--color-refused) 26%, transparent)' }
  return { color: 'var(--color-text-secondary)' }
}
