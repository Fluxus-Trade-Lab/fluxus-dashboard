/**
 * Capital efficiency — return on deployed capital.
 *
 * Deployed capital = cost basis of open positions (held qty × entry, as-traded),
 * summed per trading day. Return on deployed = total realized P&L ÷ average daily
 * deployed capital — P&L per dollar actually at risk (vs return on total capital).
 * Cost-basis based, so it needs no price feed.
 */
export function computeReturnOnDeployed(trades, startingCapital) {
  if (!trades?.length) return null
  const dayDeployed = {}
  let totalPnl = 0
  for (const t of trades) {
    const dir = t.direction === 'long' ? 1 : -1
    for (const tr of t.trims || []) totalPnl += dir * (tr.price - t.entryPrice) * tr.qty

    const entry = (t.entryDate || '').slice(0, 10)
    const exit = t.trims?.length ? t.trims[t.trims.length - 1].date.slice(0, 10) : entry
    const d = new Date(entry)
    const end = new Date(exit)
    while (d <= end) {
      if (d.getDay() !== 0 && d.getDay() !== 6) {
        const ds = d.toISOString().split('T')[0]
        const sold = (t.trims || []).filter(tr => tr.date <= ds).reduce((s, tr) => s + tr.qty, 0)
        const held = (t.originalQty || 0) - sold
        if (held > 0.5) dayDeployed[ds] = (dayDeployed[ds] || 0) + held * (t.entryPrice || 0)
      }
      d.setDate(d.getDate() + 1)
    }
  }
  const vals = Object.values(dayDeployed)
  if (!vals.length) return null
  const avgDeployed = vals.reduce((a, b) => a + b, 0) / vals.length
  const peakDeployed = Math.max(...vals)
  return {
    returnOnDeployed: avgDeployed ? (totalPnl / avgDeployed) * 100 : null,
    avgDeployedPct: startingCapital ? (avgDeployed / startingCapital) * 100 : null,
    peakDeployedPct: startingCapital ? (peakDeployed / startingCapital) * 100 : null,
    totalReturnPct: startingCapital ? (totalPnl / startingCapital) * 100 : null,
  }
}
