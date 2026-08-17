import { usable } from './headCoach'

/**
 * Did holding longer actually capture more?
 *
 * The head coach says the leak is in holding. The obvious next sentence —
 * "so hold longer" — is an assumption, and this is the view that checks it
 * rather than repeating it.
 *
 * WHAT IT CANNOT SAY, and the reason the caption says so out loud: this is a
 * correlation. Trades that ran for weeks had more on offer partly BECAUSE they
 * were working; winners last longer by construction. The right column exists
 * so that confound is visible rather than hidden — if the opportunity itself
 * rises with holding time, the comparison is not like for like, and the honest
 * reading is "the trades worth holding are in the long bucket", not "holding
 * longer pays".
 *
 * Turning it into cause needs a counterfactual — re-run each exit under a
 * hold-to-day-N rule — which is the stop simulator's machinery pointed at time
 * instead of price. Not built.
 */

export const BUCKETS = [
  { key: 'd1', lo: 0, hi: 1, label: '1' },
  { key: 'd2', lo: 2, hi: 3, label: '2–3' },
  { key: 'd4', lo: 4, hi: 7, label: '4–7' },
  { key: 'd8', lo: 8, hi: 20, label: '8–20' },
  { key: 'd21', lo: 21, hi: Infinity, label: '21+' },
]

/** Capture is meaningless when there was nothing on offer to capture. */
const MIN_OPPORTUNITY_R = 0.2

const median = (xs) => {
  if (!xs.length) return null
  const s = [...xs].sort((a, b) => a - b)
  const m = s.length >> 1
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}

/**
 * One row per bucket that has enough trades to say anything.
 * `minTrades` guards against a bucket of three deciding the shape of the page.
 */
export function holdCapture(trades = [], minTrades = 5) {
  const rows = BUCKETS.map((b) => {
    const inBucket = trades.filter((t) =>
      usable(t)
      && t.optimal_R > MIN_OPPORTUNITY_R
      && (t.hold_days ?? 0) >= b.lo
      && (t.hold_days ?? 0) <= b.hi)
    return {
      ...b,
      n: inBucket.length,
      capture: median(inBucket.map((t) => t.realized_R / t.optimal_R)),
      opportunity: median(inBucket.map((t) => t.optimal_R)),
      trades: inBucket,
    }
  }).filter((r) => r.n >= minTrades)

  // Does opportunity itself rise with holding time? If it does, the buckets
  // are not comparable and the page must say so instead of implying cause.
  const opps = rows.map((r) => r.opportunity)
  const confounded = opps.length >= 3
    && opps[opps.length - 1] > opps[0] * 1.5

  return { rows, confounded }
}
