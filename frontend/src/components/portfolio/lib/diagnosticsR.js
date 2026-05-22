import { daysBetween } from './portfolioFormat'

/**
 * R-multiple framework + exit-style / behavioral diagnostics ported from
 * the standalone Python analytics module. These complement (do not replace)
 * the existing calculations.js / diagnostics.js — they add coaching signals
 * the dashboard didn't have before.
 *
 * All functions take ENRICHED trades (post enrichTrades), which provide
 * `realizedPL`, `entryDate`, `isClosed`, etc.
 */

/**
 * 1R dollar risk = |entry - stop| × originalQty.
 * Uses ORIGINAL qty so R-multiples stay comparable across the trade's life;
 * switching to current qty would make R change every time you trim.
 */
export function rRisk(t) {
  if (t.stopPrice == null || t.stopPrice <= 0) return null
  return Math.abs(t.entryPrice - t.stopPrice) * t.originalQty
}

/**
 * R-multiple = realizedPL / rRisk. +2R = made 2x what was risked at entry;
 * -1R = clean stop-out; +5R = home run.
 */
export function rMultiple(t) {
  const risk = rRisk(t)
  if (risk == null || risk === 0) return null
  return (t.realizedPL ?? 0) / risk
}

/**
 * Classify how trim prices were sequenced. Direction-adjusted so "better"
 * always means "more profitable" regardless of long/short.
 *   strength  — trims monotonically improving (sold into rising strength)
 *   weakness  — trims monotonically deteriorating (trimmed into pullbacks)
 *   mixed     — non-monotonic; usually your biggest winners ("let it breathe")
 *   stop_only — single losing exit, no profit-taking trims first
 */
export function classifyExitStyle(t) {
  const trims = t.trims || []
  if (trims.length === 0) return 'stop_only'

  const pnl = t.realizedPL ?? 0
  const p = trims.map(tr => t.direction === 'long' ? tr.price : -tr.price)

  if (p.length === 1) return pnl > 0 ? 'strength' : 'stop_only'

  let ascending = true
  let descending = true
  for (let i = 0; i < p.length - 1; i++) {
    if (p[i] > p[i + 1]) ascending = false
    if (p[i] < p[i + 1]) descending = false
  }

  if (ascending && !descending) return 'strength'
  if (descending && !ascending) return 'weakness'
  if (ascending && descending) return 'strength' // all prices equal
  return 'mixed'
}

/**
 * Aggregate exit-style breakdown across closed trades:
 *   { strength|weakness|mixed|stop_only: { count, totalPL, avgPL, wins, losses } }
 */
export function computeExitStyleStats(enrichedTrades) {
  const buckets = { strength: [], weakness: [], mixed: [], stop_only: [] }
  enrichedTrades.filter(t => t.isClosed).forEach(t => {
    buckets[classifyExitStyle(t)].push(t.realizedPL ?? 0)
  })
  const out = {}
  Object.entries(buckets).forEach(([style, pls]) => {
    out[style] = {
      count: pls.length,
      totalPL: pls.reduce((s, p) => s + p, 0),
      avgPL: pls.length ? pls.reduce((s, p) => s + p, 0) / pls.length : 0,
      wins: pls.filter(p => p > 0).length,
      losses: pls.filter(p => p < 0).length,
    }
  })
  return out
}

/**
 * R-multiple aggregates over closed trades. Returns null if no trades
 * with a valid stop are available.
 */
export function computeRMultipleStats(enrichedTrades) {
  const closed = enrichedTrades.filter(t => t.isClosed)
  const withR = closed
    .map(t => ({ t, r: rMultiple(t) }))
    .filter(x => x.r != null)

  if (!withR.length) return null

  const rs = withR.map(x => x.r)
  const sorted = [...rs].sort((a, b) => a - b)
  const median = sorted.length % 2 === 0
    ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
    : sorted[Math.floor(sorted.length / 2)]
  const wins = rs.filter(r => r > 0)
  const losses = rs.filter(r => r < 0)

  return {
    n: rs.length,
    avgR: rs.reduce((s, r) => s + r, 0) / rs.length,
    medianR: median,
    avgWinR: wins.length ? wins.reduce((s, r) => s + r, 0) / wins.length : 0,
    avgLossR: losses.length ? losses.reduce((s, r) => s + r, 0) / losses.length : 0,
    perTrade: withR.map(({ t, r }) => ({
      ticker: t.ticker,
      entryDate: t.entryDate,
      direction: t.direction,
      r,
      realizedPL: t.realizedPL ?? 0,
    })),
  }
}

/**
 * Detect revenge-trading: ≥minStops losing closed trades on the same ticker
 * within a rolling windowDays window from the cluster's first entry.
 *
 * Catches the BABA pattern — repeated re-attacks on a thesis that already
 * failed. Returns clusters sorted worst-PL-first.
 */
export function computeRevengeTradeClusters(enrichedTrades, windowDays = 30, minStops = 2) {
  const byTicker = {}
  enrichedTrades.forEach(t => {
    if (t.isClosed && (t.realizedPL ?? 0) < 0) {
      if (!byTicker[t.ticker]) byTicker[t.ticker] = []
      byTicker[t.ticker].push(t)
    }
  })

  const clusters = []
  Object.entries(byTicker).forEach(([ticker, ts]) => {
    ts.sort((a, b) => a.entryDate.localeCompare(b.entryDate))
    let cluster = []
    ts.forEach(t => {
      if (cluster.length === 0) {
        cluster = [t]
      } else if (daysBetween(cluster[0].entryDate, t.entryDate) <= windowDays) {
        cluster.push(t)
      } else {
        if (cluster.length >= minStops) {
          clusters.push({
            ticker,
            trades: cluster,
            totalPL: cluster.reduce((s, x) => s + (x.realizedPL ?? 0), 0),
          })
        }
        cluster = [t]
      }
    })
    if (cluster.length >= minStops) {
      clusters.push({
        ticker,
        trades: cluster,
        totalPL: cluster.reduce((s, x) => s + (x.realizedPL ?? 0), 0),
      })
    }
  })

  clusters.sort((a, b) => a.totalPL - b.totalPL) // most negative first
  return clusters
}

/**
 * Panic-trim leak for a single trade: for a winner whose trim prices
 * deteriorated, how much more would you have made if every trim had hit
 * the best-priced trim instead?
 *
 * Returns null for losers, single-trim trades, or trades where the trim
 * sequence didn't monotonically deteriorate. Sum across all winners is
 * your "panic-trim tax" — should trend toward zero as discipline improves.
 */
export function panicTrimLeak(t) {
  const trims = t.trims || []
  if (trims.length < 2) return null
  const pnl = t.realizedPL ?? 0
  if (pnl <= 0) return null

  const prices = trims.map(tr => tr.price)
  let deteriorating
  let bestPrice

  if (t.direction === 'long') {
    deteriorating = prices.every((p, i) => i === 0 || prices[i - 1] >= p)
    if (!deteriorating || prices[0] === prices[prices.length - 1]) return null
    bestPrice = Math.max(...prices)
  } else {
    deteriorating = prices.every((p, i) => i === 0 || prices[i - 1] <= p)
    if (!deteriorating || prices[0] === prices[prices.length - 1]) return null
    bestPrice = Math.min(...prices)
  }

  const totalQty = trims.reduce((s, tr) => s + tr.qty, 0)
  const sign = t.direction === 'long' ? 1 : -1
  const bestPnl = sign * (bestPrice - t.entryPrice) * totalQty
  return bestPnl - pnl
}

/**
 * Aggregate panic-trim leak across all winners.
 * Returns { count, totalLeak, perTrade: [...] sorted by leak desc }.
 */
export function computePanicTrimSummary(enrichedTrades) {
  const items = []
  enrichedTrades.forEach(t => {
    const leak = panicTrimLeak(t)
    if (leak != null && leak > 0) {
      items.push({
        ticker: t.ticker,
        direction: t.direction,
        entryDate: t.entryDate,
        realizedPL: t.realizedPL ?? 0,
        leak,
      })
    }
  })
  items.sort((a, b) => b.leak - a.leak)
  return {
    count: items.length,
    totalLeak: items.reduce((s, x) => s + x.leak, 0),
    perTrade: items,
  }
}
