import { rMultiple } from './diagnosticsR'

/**
 * Position size per trade, and whether size predicts anything.
 *
 * Lifted out of PositionSizeChart so the Review card and the chart it opens
 * read the same numbers. They were about to be computed twice — the card
 * needed "avg 8.3%, corr −0.02" and the chart already had it — and the last
 * time a quantity got two implementations in this repo it got three names and
 * two of them were wrong.
 *
 * Size is notional at entry ÷ equity at entry, so a position taken at $1M and
 * the same position taken at $1.9M are not called the same size. Rows come
 * back in exit order, which is the order the RR chart uses, so the two charts
 * line up one bar to one bar.
 */
export function positionSizeStats(enrichedTrades, performanceData, startingCapital) {
  const eq = performanceData || []
  const equityAt = (date) => {
    const d = (date || '').slice(0, 10)
    let v = startingCapital
    for (const p of eq) { if (p.date <= d) v = p.value; else break }
    return v || startingCapital
  }

  const rows = (enrichedTrades || [])
    .filter((t) => t.isClosed)
    .map((t) => {
      const exit = (t.trims?.length ? t.trims[t.trims.length - 1].date : t.entryDate) || ''
      const notional = (t.originalQty || 0) * (t.entryPrice || 0)
      const size = notional / equityAt(t.entryDate) * 100
      return {
        size: Math.round(size * 100) / 100,
        r: rMultiple(t),
        pl: t.realizedPL ?? t.totalPL ?? 0,
        ticker: t.ticker,
        exit: exit.slice(0, 10),
      }
    })
    .filter((d) => d.size > 0)
    .sort((a, b) => (a.exit < b.exit ? -1 : 1))
    .map((d, i) => ({ ...d, i }))

  if (rows.length < 3) return { data: [], avg: null, corr: null, lossShareTopQ: null }

  const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length
  const std = (a) => { const m = mean(a); return Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / a.length) }

  // Correlation only over trades that carried a stop — a trade with no R has
  // no y to pair the x with, and dropping it is not the same as scoring it 0.
  let corr = null
  const paired = rows.filter((d) => d.r != null)
  if (paired.length > 2 && std(paired.map((d) => d.size)) > 0 && std(paired.map((d) => d.r)) > 0) {
    const ms = mean(paired.map((d) => d.size))
    const mr = mean(paired.map((d) => d.r))
    const cov = mean(paired.map((d) => (d.size - ms) * (d.r - mr)))
    corr = cov / (std(paired.map((d) => d.size)) * std(paired.map((d) => d.r)))
  }

  // What share of the gross loss came out of the biggest quarter of positions.
  // A book where size is harmless has this near 25%; well above it means the
  // big bets are where the damage is.
  const order = [...rows].sort((a, b) => b.size - a.size)
  const topQ = new Set(order.slice(0, Math.max(1, Math.floor(rows.length / 4))).map((d) => d.i))
  const grossLoss = rows.filter((d) => d.pl < 0).reduce((s, d) => s + -d.pl, 0) || 1
  const lossTopQ = rows.filter((d) => topQ.has(d.i) && d.pl < 0).reduce((s, d) => s + -d.pl, 0)

  return {
    data: rows,
    avg: mean(rows.map((d) => d.size)),
    corr,
    lossShareTopQ: lossTopQ / grossLoss * 100,
    pairedN: paired.length,
  }
}
