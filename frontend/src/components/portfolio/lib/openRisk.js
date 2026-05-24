/**
 * Per-trade open-risk and locked-in-gain computations.
 *
 * For a LONG position:
 *   at-risk per share   = max(0, entry - current_stop)    (lose if stop hits)
 *   locked-in per share = max(0, current_stop - entry)    (guaranteed gain if stop hits)
 *
 * For a SHORT position the math inverts:
 *   at-risk per share   = max(0, current_stop - entry)
 *   locked-in per share = max(0, entry - current_stop)
 *
 * Risk and gain are mutually exclusive — a stop either sits below entry (long)
 * meaning risk, OR above entry (long) meaning locked gain. Never both.
 */

export function tradeRisk(trade) {
  const { entryPrice, stopPrice, currentQty, direction } = trade
  if (!currentQty || currentQty <= 0) {
    return { riskDollars: 0, gainDollars: 0, atRisk: false }
  }
  const long = direction === 'long'
  const riskPerShare = long
    ? Math.max(0, entryPrice - stopPrice)
    : Math.max(0, stopPrice - entryPrice)
  const gainPerShare = long
    ? Math.max(0, stopPrice - entryPrice)
    : Math.max(0, entryPrice - stopPrice)
  return {
    riskDollars: riskPerShare * currentQty,
    gainDollars: gainPerShare * currentQty,
    atRisk: riskPerShare > 0,
  }
}

/**
 * Total open risk + locked across an array of open trades.
 * R-multiple computed using fixedR (default $2,500).
 */
export function aggregate(trades, fixedR = 2500) {
  let totalRisk = 0
  let totalLocked = 0
  let atRiskCount = 0
  let lockedCount = 0
  const perTrade = []
  for (const t of trades) {
    if (!t.currentQty || t.currentQty <= 0) continue
    const r = tradeRisk(t)
    totalRisk += r.riskDollars
    totalLocked += r.gainDollars
    if (r.atRisk) atRiskCount++
    else if (r.gainDollars > 0) lockedCount++
    perTrade.push({
      id: t.id,
      ticker: t.ticker,
      direction: t.direction,
      riskDollars: r.riskDollars,
      gainDollars: r.gainDollars,
      atRisk: r.atRisk,
    })
  }
  // sort by risk desc (biggest exposure first), then by locked gain desc
  perTrade.sort((a, b) => {
    if (a.atRisk !== b.atRisk) return a.atRisk ? -1 : 1
    if (a.atRisk) return b.riskDollars - a.riskDollars
    return b.gainDollars - a.gainDollars
  })
  return {
    totalRiskDollars: totalRisk,
    totalLockedDollars: totalLocked,
    totalRiskR: fixedR > 0 ? totalRisk / fixedR : 0,
    atRiskCount,
    lockedCount,
    perTrade,
  }
}
