/**
 * Pure sizing statistics for the Van Tharp curriculum (SQN, expectancy,
 * bootstrap Monte-Carlo). No React. Sources: Van Tharp, "Definitive Guide
 * to Position Sizing"; LordFed, "Size Matters".
 */

/** Deterministic PRNG (mulberry32) so simulations don't reshuffle every render. */
export function mulberry32(seed) {
  let a = seed >>> 0
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/**
 * R-multiples of closed trades that had a real initial stop.
 * Consumes the rr already computed by enrichTrades (anchored to the
 * locked-at-entry stop) — never recomputes R.
 *
 * Non-finite rr (NaN, ±Infinity, missing) is DROPPED, not coerced to 0: this is
 * the single boundary where the whole module's finiteness is guaranteed. A single
 * Infinity downstream makes sqn() return NaN and makes buildHistogram compute a
 * NaN bin index — which silently zeroes every bucket instead of throwing.
 */
export function closedR(enrichedTrades) {
  return (enrichedTrades || [])
    .filter(t => t.isClosed)
    .filter(t => {
      const stop = t.initialStop ?? t.stopPrice
      return Math.abs(t.entryPrice - stop) > 0
    })
    .map(t => t.rr)
    .filter(Number.isFinite)
}

/** n, mean R, sample stdev (n−1), win rate, payoff (avg win R ÷ avg |loss R|). */
export function expectancyStats(rs) {
  const n = rs.length
  if (!n) return { n: 0, meanR: 0, stdevR: 0, winRate: 0, payoff: 0 }
  const meanR = rs.reduce((s, r) => s + r, 0) / n
  const stdevR = n > 1
    ? Math.sqrt(rs.reduce((s, r) => s + (r - meanR) ** 2, 0) / (n - 1))
    : 0
  const wins = rs.filter(r => r > 0)
  const losses = rs.filter(r => r < 0)
  const avgWin = wins.length ? wins.reduce((s, r) => s + r, 0) / wins.length : 0
  const avgLoss = losses.length
    ? Math.abs(losses.reduce((s, r) => s + r, 0) / losses.length)
    : 0
  return {
    n, meanR, stdevR,
    winRate: wins.length / n,
    payoff: avgLoss > 0 ? avgWin / avgLoss : 0,
  }
}

/** Tharp caps the trade count at 100 in the SQN formula. */
const SQN_N_CAP = 100

/**
 * Tharp's System Quality Number = √min(N,100) × meanR ÷ stdevR. Null when undefined.
 *
 * The N ≤ 100 cap is Tharp's own and is what keeps the quality bands
 * (Poor…Holy Grail) calibrated: without it √N grows without bound and a merely
 * long track record scores as a better system. At 331 closed trades the
 * uncapped form inflates the score ~1.8× (√331 = 18.2 vs √100 = 10), which is
 * the difference between "Good" and "Excellent" on a book that did not change.
 * The cap applies to the √N factor ONLY — expectancyStats keeps the true n,
 * which the UI displays as the real closed-trade count.
 */
export function sqn(rs) {
  const { n, meanR, stdevR } = expectancyStats(rs)
  if (n < 2 || stdevR === 0) return null
  return Math.sqrt(Math.min(n, SQN_N_CAP)) * meanR / stdevR
}

/**
 * Tharp's SQN quality bands (Definitive Guide to Position Sizing).
 * Non-finite input (NaN from a bad R series, ±Infinity) is unknown, not top-band —
 * NaN fails every comparison below and would otherwise fall through to "Holy Grail".
 */
export function sqnBand(value) {
  if (value == null || !Number.isFinite(value)) return { label: '—', tone: 'muted' }
  if (value < 1.6) return { label: 'Poor', tone: 'bad' }
  if (value < 2.0) return { label: 'Below average', tone: 'warn' }
  if (value < 2.5) return { label: 'Average', tone: 'neutral' }
  if (value < 3.0) return { label: 'Good', tone: 'good' }
  if (value <= 5.0) return { label: 'Excellent', tone: 'good' }
  if (value < 7.0) return { label: 'Superb', tone: 'good' }
  return { label: 'Holy Grail', tone: 'good' }
}

/**
 * Tharp's position-sizing-to-objectives Monte-Carlo: bootstrap-resample the
 * account's own R-distribution at a given risk % per trade. Each path applies
 * equity *= 1 + (riskPct/100) * R for `horizon` draws, tracking max drawdown.
 * i.i.d. bootstrap — ignores serial correlation and regime shifts by design;
 * the UI must caption that caveat.
 */
export function bootstrapObjective(rs, {
  riskPct, horizon, paths = 2000, targetReturnPct, maxDDPct, seed = 42,
}) {
  if (!rs?.length) return null
  const rand = mulberry32(seed)
  const f = riskPct / 100
  const endReturns = new Array(paths)
  const maxDDs = new Array(paths)
  let reach = 0
  let breach = 0
  for (let p = 0; p < paths; p++) {
    let eq = 1
    let peak = 1
    let maxDD = 0
    for (let i = 0; i < horizon; i++) {
      const r = rs[Math.floor(rand() * rs.length)]
      eq *= 1 + f * r
      if (eq <= 0) { eq = 0; maxDD = 1; break } // busted
      if (eq > peak) peak = eq
      const dd = 1 - eq / peak
      if (dd > maxDD) maxDD = dd
    }
    const ret = (eq - 1) * 100
    endReturns[p] = ret
    maxDDs[p] = maxDD * 100
    if (ret >= targetReturnPct) reach++
    if (maxDD * 100 > maxDDPct) breach++
  }
  endReturns.sort((a, b) => a - b)
  maxDDs.sort((a, b) => a - b)
  const pct = (arr, q) => arr[Math.min(arr.length - 1, Math.floor(q * arr.length))]
  return {
    endReturns,
    pReachTarget: (reach / paths) * 100,
    pBreachDD: (breach / paths) * 100,
    medianReturn: pct(endReturns, 0.5),
    p5: pct(endReturns, 0.05),
    p95: pct(endReturns, 0.95),
    medianMaxDD: pct(maxDDs, 0.5),
    histogram: buildHistogram(endReturns, 24),
  }
}

/** Bucket a sorted array into `bins` equal-width bins; x = bin midpoint. */
function buildHistogram(sorted, bins) {
  if (!sorted.length) return []
  const lo = sorted[0]
  const hi = sorted[sorted.length - 1]
  const width = (hi - lo || 1) / bins
  const counts = new Array(bins).fill(0)
  for (const v of sorted) {
    counts[Math.min(bins - 1, Math.floor((v - lo) / width))]++
  }
  return counts.map((count, i) => ({ x: lo + (i + 0.5) * width, count }))
}
