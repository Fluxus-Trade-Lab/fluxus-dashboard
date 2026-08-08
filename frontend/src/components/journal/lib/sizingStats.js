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
 */
export function closedR(enrichedTrades) {
  return (enrichedTrades || [])
    .filter(t => t.isClosed)
    .filter(t => {
      const stop = t.initialStop ?? t.stopPrice
      return Math.abs(t.entryPrice - stop) > 0
    })
    .map(t => t.rr || 0)
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

/** Tharp's System Quality Number = √N × meanR ÷ stdevR. Null when undefined. */
export function sqn(rs) {
  const { n, meanR, stdevR } = expectancyStats(rs)
  if (n < 2 || stdevR === 0) return null
  return Math.sqrt(n) * meanR / stdevR
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
