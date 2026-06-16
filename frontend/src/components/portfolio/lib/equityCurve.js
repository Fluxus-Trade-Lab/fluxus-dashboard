import { todayStr } from './portfolioFormat'
import { lookupPrice, rejectRevertingSpikes } from './calculations'

/**
 * Build the equity curve: daily portfolio value from first trade to today.
 * Uses dailyPrices (from GAS/Finnhub candle data) for accurate daily valuation.
 *
 * This fixes the original bug where entry price was used as fallback,
 * creating flat lines between trade events.
 */
export function buildEquityCurve(trades, startingCapital, dailyPrices, benchmarkHistories) {
  if (!trades.length) return []

  // 1. Find date range
  const firstEntry = trades.reduce(
    (min, t) => (t.entryDate < min ? t.entryDate : min),
    todayStr()
  )
  const lastDate = todayStr()

  // 2. Generate every weekday in range
  const datePoints = []
  for (let d = new Date(firstEntry); d <= new Date(lastDate); d.setDate(d.getDate() + 1)) {
    if (d.getDay() !== 0 && d.getDay() !== 6) {
      datePoints.push(d.toISOString().split('T')[0])
    }
  }

  // 3. Build a spike-cleaned close series per ticker across datePoints.
  // Raw daily close still drives MTM (so the curve reconciles with the live
  // header), but one-bar reverting spikes — a split/feed mis-scale that hits a
  // single bar and re-aligns the next day — are forward-filled. This is what
  // caused the 2026-04-21 dip: a held leveraged ETF whose Yahoo close was
  // briefly on the wrong split scale, valued as qty(as-traded) × close(adjusted).
  // Today's bar is the last point and never an interior index, so it is left
  // raw and the curve's final value still equals the header.
  const cleanByTicker = {}
  ;[...new Set(trades.map(t => t.ticker))].forEach(tk => {
    const raw = datePoints.map(d => lookupPrice(tk, d, dailyPrices, null))
    const cleaned = rejectRevertingSpikes(raw)
    const map = {}
    datePoints.forEach((d, i) => { if (cleaned[i] != null) map[d] = cleaned[i] })
    cleanByTicker[tk] = map
  })

  // 4. For each date, compute total portfolio value.
  const curve = datePoints.map(date => {
    let cash = startingCapital
    let marketValue = 0

    trades.forEach(t => {
      if (t.entryDate.slice(0, 10) > date) return // Trade not yet open

      const dir = t.direction === 'long' ? 1 : -1

      // Cash impact of entry
      cash -= t.originalQty * t.entryPrice * dir

      // Cash impact of trims before this date
      const trimsBeforeDate = (t.trims || []).filter(tr => tr.date <= date)
      trimsBeforeDate.forEach(tr => { cash += tr.qty * tr.price * dir })

      // Remaining qty
      const soldQty = trimsBeforeDate.reduce((s, tr) => s + tr.qty, 0)
      const qtyAtDate = t.originalQty - soldQty
      if (qtyAtDate <= 0) return

      const price = cleanByTicker[t.ticker]?.[date]
        ?? lookupPrice(t.ticker, date, dailyPrices, t.entryPrice)
      marketValue += qtyAtDate * price * dir
    })

    const totalValue = cash + marketValue
    return {
      date,
      value: totalValue,
      returnPct: ((totalValue - startingCapital) / startingCapital) * 100,
    }
  })

  // 5. Add benchmark return series
  if (benchmarkHistories) {
    Object.entries(benchmarkHistories).forEach(([ticker, history]) => {
      if (!history?.length) return
      const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date))
      const baseClose = sorted[0].close
      if (!baseClose) return

      curve.forEach(pt => {
        let closestPrice = null
        for (let i = sorted.length - 1; i >= 0; i--) {
          if (sorted[i].date <= pt.date) { closestPrice = sorted[i].close; break }
        }
        pt[ticker] = closestPrice != null
          ? ((closestPrice - baseClose) / baseClose) * 100
          : 0
      })
    })
  }

  return curve
}

/**
 * Compute portfolio value at a specific date.
 * Used for weight-based position sizing.
 */
export function getPortfolioValueAtDate(trades, startingCapital, asOfDate, dailyPrices) {
  let cash = startingCapital
  let mktVal = 0

  trades.forEach(t => {
    if (t.entryDate.slice(0, 10) > asOfDate) return

    const dir = t.direction === 'long' ? 1 : -1
    const trimsBeforeDate = (t.trims || []).filter(tr => new Date(tr.date) <= new Date(asOfDate))
    const soldQty = trimsBeforeDate.reduce((s, tr) => s + tr.qty, 0)
    const qtyAtDate = t.originalQty - soldQty

    cash -= t.originalQty * t.entryPrice * dir
    trimsBeforeDate.forEach(tr => { cash += tr.qty * tr.price * dir })

    if (qtyAtDate <= 0) return

    const price = lookupPrice(t.ticker, asOfDate, dailyPrices, t.entryPrice)
    mktVal += qtyAtDate * price * dir
  })

  return cash + mktVal
}
