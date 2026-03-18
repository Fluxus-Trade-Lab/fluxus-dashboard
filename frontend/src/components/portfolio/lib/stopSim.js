/**
 * Walk daily close prices to determine which stop levels were triggered.
 * Checks sequentially: stop k must trigger before stop k+1.
 *
 * @param {string} ticker - Stock ticker symbol
 * @param {string} entryDate - Trade entry date (YYYY-MM-DD)
 * @param {Array} trims - Array of trim objects with { date, qty, price }
 * @param {number[]} stopLevels - Array of N stop price levels, ordered innermost to outermost
 * @param {number} dir - Direction: 1 for long, -1 for short
 * @param {Object} dailyPrices - Price cache { 'TICKER:YYYY-MM-DD': closePrice }
 * @returns {{ triggered: boolean[], hasHistory: boolean }}
 */
function checkStopTriggers(ticker, entryDate, trims, stopLevels, dir, dailyPrices) {
  const N = stopLevels.length
  const lastExitDate = trims.length > 0 ? trims[trims.length - 1].date : entryDate
  const start = new Date(entryDate)
  const end = new Date(lastExitDate)
  const triggered = new Array(N).fill(false)
  let hasHistory = false
  let nextStop = 0  // which stop level to check next

  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const dateStr = d.toISOString().split('T')[0]
    const key = `${ticker}:${dateStr}`
    const price = dailyPrices[key]

    if (price == null) continue
    hasHistory = true

    // For longs: stop triggers when price drops to/below stop level
    // For shorts: stop triggers when price rises to/above stop level
    while (nextStop < N) {
      const breached = dir === 1
        ? price <= stopLevels[nextStop]
        : price >= stopLevels[nextStop]
      if (breached) {
        triggered[nextStop] = true
        nextStop++
      } else {
        break
      }
    }

    if (nextStop >= N) break  // All stops triggered
  }

  return { triggered, hasHistory }
}

/**
 * Compute N-stop simulation for all closed trades.
 *
 * N-stop system: divides position into N equal parts, with graduated stops:
 *   Stop k: entry - (k/N * R) * dir   for k = 1..N
 * where R = |entry - stop| and direction determines sign.
 *
 * For each closed trade, walks daily close prices to check if stops triggered.
 * If no daily price data available, assumes worst case (all stops triggered).
 *
 * @param {Array} trades - All trades from portfolio state
 * @param {Object} dailyPrices - Price cache { 'TICKER:YYYY-MM-DD': closePrice }
 * @param {number} numStops - Number of stop levels (e.g. 2 or 3)
 * @returns {Object} { rows: SimRow[], summary: SummaryStats }
 */
export function computeStopSim(trades, dailyPrices, numStops) {
  const N = numStops
  const closedTrades = trades.filter(t => t.isClosed && t.stopPrice > 0)

  const rows = closedTrades.map(t => {
    const dir = t.direction === 'long' ? 1 : -1
    const R = Math.abs(t.entryPrice - t.stopPrice)

    // Compute N stop levels: stop_k = entry - (k/N * R) * dir for k=1..N
    const stopLevels = []
    for (let k = 1; k <= N; k++) {
      stopLevels.push(t.entryPrice - (k / N) * R * dir)
    }

    // Split quantity into N equal parts; last tranche gets remainder
    const Q = t.originalQty
    const baseQty = Math.floor(Q / N)
    const quantities = []
    for (let k = 0; k < N; k++) {
      if (k < N - 1) {
        quantities.push(baseQty)
      } else {
        quantities.push(Q - baseQty * (N - 1))  // remainder gets last tranche
      }
    }

    // Actual P&L from trims
    const trims = t.trims || []
    const actualPL = trims.reduce((s, tr) => s + tr.qty * (tr.price - t.entryPrice) * dir, 0)
    const actualAvgExit = trims.length > 0
      ? trims.reduce((s, tr) => s + tr.qty * tr.price, 0) / trims.reduce((s, tr) => s + tr.qty, 0)
      : t.entryPrice

    // Walk daily prices to check stop triggers
    const { triggered, hasHistory } = checkStopTriggers(
      t.ticker, t.entryDate, trims, stopLevels, dir, dailyPrices
    )

    let simPL
    if (actualPL >= 0) {
      // Winning trade: N-stop doesn't affect winners — it's downside protection only
      simPL = actualPL
    } else if (!hasHistory) {
      // Losing trade with no history: assume all N stops triggered (worst case)
      simPL = 0
      for (let k = 0; k < N; k++) {
        simPL += quantities[k] * (stopLevels[k] - t.entryPrice) * dir
      }
    } else {
      // Losing trade with history: compute based on which stops actually triggered
      let remainingQty = Q
      simPL = 0

      for (let k = 0; k < N; k++) {
        if (triggered[k]) {
          simPL += quantities[k] * (stopLevels[k] - t.entryPrice) * dir
          remainingQty -= quantities[k]
        }
      }

      // Remaining shares (not stopped out) use actual avg exit price
      if (remainingQty > 0) {
        simPL += remainingQty * (actualAvgExit - t.entryPrice) * dir
      }
    }

    const diff = simPL - actualPL
    const actualPLPct = t.entryPrice > 0 ? (actualPL / (Q * t.entryPrice)) * 100 : 0
    const simPLPct = t.entryPrice > 0 ? (simPL / (Q * t.entryPrice)) * 100 : 0

    // Build stops array with { level, qty, triggered } for each stop
    const stops = stopLevels.map((level, k) => ({
      level,
      qty: quantities[k],
      triggered: triggered[k],
    }))

    return {
      id: t.id,
      ticker: t.ticker,
      direction: t.direction,
      qty: Q,
      entryPrice: t.entryPrice,
      stopPrice: t.stopPrice,
      R,
      stops,
      actualAvgExit,
      actualPL, actualPLPct,
      simPL, simPLPct,
      diff,
      triggered,
      hasHistory,
    }
  })

  // Sort by diff descending (biggest improvement first)
  rows.sort((a, b) => b.diff - a.diff)

  // Summary stats
  const totalActualPL = rows.reduce((s, r) => s + r.actualPL, 0)
  const totalSimPL = rows.reduce((s, r) => s + r.simPL, 0)
  const totalDiff = totalSimPL - totalActualPL

  const actualLosers = rows.filter(r => r.actualPL < 0)
  const simLosers = rows.filter(r => r.simPL < 0)
  const avgActualLoss = actualLosers.length > 0
    ? actualLosers.reduce((s, r) => s + r.actualPLPct, 0) / actualLosers.length : 0
  const avgSimLoss = simLosers.length > 0
    ? simLosers.reduce((s, r) => s + r.simPLPct, 0) / simLosers.length : 0

  const tradesAffected = rows.filter(r => r.triggered.some(Boolean)).length

  return {
    rows,
    summary: {
      totalActualPL, totalSimPL, totalDiff,
      avgActualLoss, avgSimLoss,
      tradesAffected, totalTrades: rows.length,
    },
  }
}

/**
 * Backward-compatible wrapper: compute 3-stop simulation.
 * Produces identical results to the original computeThreeStopSim.
 *
 * @param {Array} trades - All trades from portfolio state
 * @param {Object} dailyPrices - Price cache { 'TICKER:YYYY-MM-DD': closePrice }
 * @returns {Object} { rows: SimRow[], summary: SummaryStats }
 */
export function computeThreeStopSim(trades, dailyPrices) {
  return computeStopSim(trades, dailyPrices, 3)
}
