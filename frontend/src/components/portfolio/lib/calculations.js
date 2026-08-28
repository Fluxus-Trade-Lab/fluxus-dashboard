import { daysBetween, todayStr, RISK_FREE_RATE } from './portfolioFormat'

/**
 * Look up the best available price for a ticker on a date, AND say which day
 * it actually came from.
 *
 * The walk-back is why the caller needs the date. Asking for today and getting
 * Friday's close is correct behaviour for a market value; it is a lie for a
 * "1D" column, because the number underneath is then Friday-vs-Thursday while
 * the header still says today. `null` when nothing was found within ten days.
 */
export function lookupPriceAt(ticker, date, dailyPrices) {
  for (let d = 0; d < 10; d++) {
    const checkDate = new Date(date)
    checkDate.setDate(checkDate.getDate() - d)
    const iso = checkDate.toISOString().split('T')[0]
    const hit = dailyPrices[`${ticker}:${iso}`]
    if (hit != null) return { price: hit, date: iso }
  }
  return null
}

/**
 * Look up the best available price for a ticker on a date.
 * Tries exact date, then walks back up to 10 days for weekends/holidays.
 * Returns `fallback` as last resort.
 */
export function lookupPrice(ticker, date, dailyPrices, fallback) {
  return lookupPriceAt(ticker, date, dailyPrices)?.price ?? fallback
}

/**
 * Reject one-bar "reverting spikes" from a chronological price series.
 *
 * A reverting spike is a bar that deviates from BOTH its neighbours in the same
 * multiplicative direction (a V or inverted-V) — the signature of a split/feed
 * mis-scale that registers for a single bar and re-aligns the next day. The
 * canonical case: a leveraged ETF whose Yahoo close is briefly on the wrong
 * split scale, so qty(as-traded) × close(adjusted) craters one day's MTM and
 * "recovers" the next. We forward-fill the last good price for that bar.
 *
 * A persistent move (gap up/down that STAYS at the new level) is NOT a revert,
 * so legitimate large daily moves — including a real 3x-ETF rip — pass through.
 *
 * @param {(number|null)[]} prices  chronological closes (null = no data)
 * @param {number} spikeFactor      min multiplicative deviation vs both neighbours
 * @returns {(number|null)[]}       cleaned series, same length
 */
export function rejectRevertingSpikes(prices, spikeFactor = 1.6) {
  const clean = prices.slice()
  for (let i = 1; i < prices.length - 1; i++) {
    const c = prices[i]
    const prev = clean[i - 1]
    const next = prices[i + 1]
    if (c == null || prev == null || next == null || prev <= 0 || next <= 0) continue
    const dPrev = c / prev
    const dNext = c / next
    const isUpSpike = dPrev > spikeFactor && dNext > spikeFactor
    const isDownSpike = dPrev < 1 / spikeFactor && dNext < 1 / spikeFactor
    if (isUpSpike || isDownSpike) clean[i] = prev // forward-fill last good
  }
  return clean
}

/** Net cash committed to all trades (positive = cash out for longs) */
export function computeCashUsed(trades) {
  return trades.reduce((s, t) => {
    const dir = t.direction === 'long' ? 1 : -1
    let net = t.originalQty * t.entryPrice * dir
    ;(t.trims || []).forEach(tr => { net -= tr.qty * tr.price * dir })
    return s + net
  }, 0)
}

/**
 * Enrich trades with computed P/L fields.
 * Uses dailyPrices for current prices instead of stored lastPrice/prevClose.
 */
export function enrichTrades(trades, totalPortfolioValue, dailyPrices) {
  const today = todayStr()
  return trades.map(t => {
    const dir = t.direction === 'long' ? 1 : -1
    const trims = t.trims || []
    const totalSoldQty = trims.reduce((s, tr) => s + tr.qty, 0)
    const costBasis = t.originalQty * t.entryPrice
    // R-multiples are anchored to the locked-at-entry stop. Trailing the live
    // `stopPrice` after the fact must never rewrite historical R.
    // No initialStop means no R anchor, so riskUnit is unknown and every rr
    // below comes out null. Falling back to the live `stopPrice` here would
    // re-anchor a closed trade's R to whatever the stop was last dragged to,
    // which is exactly what the comment above forbids.
    const initialStop = t.initialStop ?? null
    const riskUnit = initialStop == null
      ? null : Math.abs(t.entryPrice - initialStop)

    // Realized P/L from trims
    let realizedPL = 0
    trims.forEach(tr => { realizedPL += tr.qty * (tr.price - t.entryPrice) * dir })
    const realizedPLPct = totalSoldQty > 0 && t.entryPrice > 0
      ? (realizedPL / (totalSoldQty * t.entryPrice)) * 100
      : 0

    const lastExitDate = trims.length > 0 ? trims[trims.length - 1].date : null
    const holdingDays = t.isClosed && lastExitDate
      ? daysBetween(t.entryDate, lastExitDate)
      : daysBetween(t.entryDate, today)

    const trimCount = trims.length
    const trimStatus = t.isClosed ? 'Closed' : trimCount > 0 ? `${trimCount} trim${trimCount > 1 ? 's' : ''}` : 'Open'

    if (t.isClosed) {
      const totalReturnPct = costBasis > 0 ? (realizedPL / costBasis) * 100 : 0
      const rrPrice = totalSoldQty > 0
        ? trims.reduce((s, tr) => s + tr.qty * tr.price, 0) / totalSoldQty
        : t.entryPrice
      const rr = riskUnit > 0 ? ((rrPrice - t.entryPrice) * dir) / riskUnit : 0
      return {
        ...t, marketVal: 0, change1D: 0, pl1D: 0, weight: 0,
        unrealizedPL: 0, unrealizedPLPct: 0, realizedPL, realizedPLPct,
        totalPL: realizedPL, totalReturnPct, holdingDays, rr, trimStatus, costBasis,
      }
    }

    // Open: look up current price from dailyPrices
    const lastHit = lookupPriceAt(t.ticker, today, dailyPrices)
    const lastP = lastHit?.price ?? t.entryPrice
    // Previous close: look up yesterday (or most recent prior trading day)
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const prevHit = lookupPriceAt(t.ticker, yesterday.toISOString().split('T')[0], dailyPrices)
    const prevC = prevHit?.price ?? lastP

    const marketVal = t.currentQty * lastP

    /* THE 1D BASELINE IS WHERE WE STARTED HOLDING, NOT YESTERDAY'S CLOSE.
     *
     * Reported by Andy and reproduced by the data side against the real MRNA
     * 2026-08-19 shape (DATA_CONTRACTS §七, 2026-08-28): prev close 62.96 →
     * gapped → entered at 106.34 → closed 174.38, 1,000 shares. Taking the
     * prev close as the base charged us the ENTIRE GAP we were not in:
     * `pl1D` read +$111,420 against a true +$68,040, and `change1D` read
     * +176.97% against +63.98% — 2.8×. It is symmetric and worse the other
     * way: buy a gap-down and the table shows a loss you never took.
     *
     * `unrealizedPL` on the same trade was right all along; it anchors on the
     * entry price. So does the equity curve. Only these two columns were wrong,
     * and nothing cumulative was ever built on them.
     */
    const openedToday = String(t.entryDate ?? '').slice(0, 10) >= today

    /* AND IT IS "NOT MEASURED", NEVER ZERO, WHEN TODAY HAS NO PRICE.
     *
     * `lookupPriceAt` walks back up to ten days, so before a refresh both ends
     * land on the same older session and the old code printed 0 — which reads
     * as "flat today" and is a claim we cannot make. Same rule §六 already
     * holds for `regime.score`: null shows as not-measured, never as 0. The
     * column renders '—' on null, and the neutral tone, without any change to
     * the table.
     */
    const haveToday = lastHit?.date === today
    const base1D = !haveToday ? null
      : openedToday ? t.entryPrice
      : (prevHit && prevHit.date !== lastHit.date ? prevHit.price : null)

    const change1D = base1D != null && base1D > 0 ? ((lastP - base1D) / base1D) * 100 : null
    const pl1D = base1D != null ? t.currentQty * (lastP - base1D) * dir : null
    const weight = totalPortfolioValue > 0 ? (marketVal / totalPortfolioValue) * 100 : 0
    const unrealizedPL = t.currentQty * (lastP - t.entryPrice) * dir
    const unrealizedPLPct = t.entryPrice > 0 ? ((lastP - t.entryPrice) / t.entryPrice) * 100 * dir : 0
    const totalTradePL = unrealizedPL + realizedPL
    const totalReturnPct = costBasis > 0 ? (totalTradePL / costBasis) * 100 : 0
    const rr = riskUnit > 0 ? ((lastP - t.entryPrice) * dir) / riskUnit : 0

    return {
      ...t, lastPrice: lastP, prevClose: prevC,
      marketVal, change1D, pl1D, weight, unrealizedPL, unrealizedPLPct,
      realizedPL, realizedPLPct, totalPL: totalTradePL, totalReturnPct,
      holdingDays, rr, trimStatus, costBasis,
    }
  })
}

export function computeMonthlyStats(enrichedTrades, performanceData) {
  const byMonth = {}
  enrichedTrades.filter(t => t.isClosed).forEach(t => {
    const trims = t.trims || []
    const lastTrim = trims[trims.length - 1]
    const m = lastTrim?.date?.slice(0, 7) || 'Unknown'
    if (!byMonth[m]) byMonth[m] = []
    byMonth[m].push({
      retPct: t.totalReturnPct || 0,
      holdingDays: t.holdingDays || 0,
      pl: t.totalPL || 0,
    })
  })

  // Per-trim realized P&L attributed to the month of EACH trim (not last-trim).
  // Captures partial gains/losses on multi-month trades in the month they actually happened.
  // Includes trims from still-open positions.
  const realizedByMonth = {}
  enrichedTrades.forEach(t => {
    const dir = t.direction === 'long' ? 1 : -1
    ;(t.trims || []).forEach(tr => {
      const m = tr.date?.slice(0, 7)
      if (!m) return
      realizedByMonth[m] = (realizedByMonth[m] || 0) + dir * (tr.price - t.entryPrice) * tr.qty
    })
  })

  // Monthly portfolio return from equity curve
  const monthlyPortRet = {}
  if (performanceData.length > 1) {
    const monthEnds = {}
    performanceData.forEach(pt => { monthEnds[pt.date.slice(0, 7)] = pt.returnPct })
    const months = Object.keys(monthEnds).sort()
    months.forEach((m, i) => {
      const endCum = monthEnds[m]
      const prevCum = i > 0 ? monthEnds[months[i - 1]] : 0
      const endFactor = 1 + endCum / 100
      const prevFactor = 1 + prevCum / 100
      monthlyPortRet[m] = prevFactor > 0 ? (endFactor / prevFactor - 1) * 100 : 0
    })
  }

  // A month is a row when something happened in it. The union below picks up
  // the equity curve's first partial month, which has no closed trade, no
  // realized P&L and — being the first — a return of exactly 0 by
  // construction: a row of dashes that reads as a flat month rather than as
  // no month at all. Andy asked for 2025-12 to go; the rule rather than the
  // date, so the next one does not arrive.
  //
  // All three tests, not just the trade count: holding through a month without
  // closing anything is a real month, and its mark-to-market return is the
  // whole point of showing it.
  const allMonths = [...new Set([
    ...Object.keys(byMonth),
    ...Object.keys(monthlyPortRet),
    ...Object.keys(realizedByMonth),
  ])].sort().filter((m) => (
    (byMonth[m]?.length ?? 0) > 0
    || Math.abs(realizedByMonth[m] ?? 0) > 1e-9
    || Math.abs(monthlyPortRet[m] ?? 0) > 1e-9
  ))

  return allMonths.map(m => {
    const tds = byMonth[m] || []
    const wins = tds.filter(x => x.retPct > 0)
    const losses = tds.filter(x => x.retPct <= 0)
    return {
      month: m, totalTrades: tds.length,
      monthlyRetPct: monthlyPortRet[m] || 0,
      totalPL: realizedByMonth[m] || 0,
      returnPct: tds.length ? tds.reduce((s, x) => s + x.retPct, 0) / tds.length : 0,
      winPct: tds.length ? (wins.length / tds.length) * 100 : 0,
      avgGain: wins.length ? wins.reduce((s, x) => s + x.retPct, 0) / wins.length : 0,
      avgLoss: losses.length ? losses.reduce((s, x) => s + x.retPct, 0) / losses.length : 0,
      largestGain: wins.length ? Math.max(...wins.map(x => x.retPct)) : 0,
      largestLoss: losses.length ? Math.min(...losses.map(x => x.retPct)) : 0,
      avgHoldWin: wins.length ? wins.reduce((s, x) => s + x.holdingDays, 0) / wins.length : 0,
      avgHoldLoss: losses.length ? losses.reduce((s, x) => s + x.holdingDays, 0) / losses.length : 0,
    }
  })
}

export function computeYtdStats(enrichedTrades, totalReturnPct) {
  const allExits = enrichedTrades.filter(t => t.isClosed).map(t => ({
    retPct: t.totalReturnPct || 0,
    holdingDays: t.holdingDays || 0,
  }))
  if (!allExits.length) return null
  const wins = allExits.filter(x => x.retPct > 0)
  const losses = allExits.filter(x => x.retPct <= 0)
  return {
    totalTrades: allExits.length,
    returnPct: totalReturnPct,
    winPct: (wins.length / allExits.length) * 100,
    avgGain: wins.length ? wins.reduce((s, x) => s + x.retPct, 0) / wins.length : 0,
    avgLoss: losses.length ? losses.reduce((s, x) => s + x.retPct, 0) / losses.length : 0,
    largestGain: wins.length ? Math.max(...wins.map(x => x.retPct)) : 0,
    largestLoss: losses.length ? Math.min(...losses.map(x => x.retPct)) : 0,
    avgHoldWin: wins.length ? wins.reduce((s, x) => s + x.holdingDays, 0) / wins.length : 0,
    avgHoldLoss: losses.length ? losses.reduce((s, x) => s + x.holdingDays, 0) / losses.length : 0,
  }
}

export function computeRiskMetrics(performanceData, benchmarkTicker) {
  if (performanceData.length < 20) return null
  const pr = []
  for (let i = 1; i < performanceData.length; i++) {
    const pE = 1 + performanceData[i - 1].returnPct / 100
    const cE = 1 + performanceData[i].returnPct / 100
    if (pE > 0) pr.push((cE - pE) / pE)
  }
  if (pr.length < 20) return null

  const n = pr.length
  const avgP = pr.reduce((s, r) => s + r, 0) / n

  // Geometric annualized return from actual cumulative performance
  const cumReturn = performanceData[performanceData.length - 1].returnPct / 100
  const annRet = n > 0 ? ((1 + cumReturn) ** (252 / n) - 1) * 100 : 0

  // Max drawdown — CANONICAL MTM method: peak-to-trough on the actual daily
  // mark-to-market equity `value` (cash + open positions), identical to
  // equityCurve.js computeDrawdown and the Python mtm.drawdown used in the
  // performance report. (The old version compounded per-day returnPct into an
  // index; this uses the equity dollars directly and also yields the DD window.)
  let peakV = -Infinity, maxDD = 0, ddPeakDate = null, ddTroughDate = null, curPeakDate = null
  performanceData.forEach(pt => {
    const v = pt.value
    if (v == null) return
    if (v > peakV) { peakV = v; curPeakDate = pt.date }
    if (peakV > 0) {
      const dd = (peakV - v) / peakV
      if (dd > maxDD) { maxDD = dd; ddTroughDate = pt.date; ddPeakDate = curPeakDate }
    }
  })

  let correlation = null, beta = null, alpha = null
  if (performanceData.some(p => p[benchmarkTicker] != null)) {
    const br = []
    for (let i = 1; i < performanceData.length; i++) {
      const pE = 1 + (performanceData[i - 1][benchmarkTicker] ?? 0) / 100
      const cE = 1 + (performanceData[i][benchmarkTicker] ?? 0) / 100
      if (pE > 0) br.push((cE - pE) / pE)
    }
    const m = Math.min(pr.length, br.length)
    if (m > 20) {
      const prs = pr.slice(-m), brs = br.slice(-m)
      const aP = prs.reduce((s, r) => s + r, 0) / m
      const aB = brs.reduce((s, r) => s + r, 0) / m
      let cov = 0, vP = 0, vB = 0
      for (let i = 0; i < m; i++) {
        cov += (prs[i] - aP) * (brs[i] - aB)
        vP += (prs[i] - aP) ** 2
        vB += (brs[i] - aB) ** 2
      }
      correlation = vP > 0 && vB > 0 ? cov / Math.sqrt(vP * vB) : 0
      beta = vB > 0 ? cov / vB : 0
      alpha = (aP - RISK_FREE_RATE / 252 - beta * (aB - RISK_FREE_RATE / 252)) * 252 * 100
    }
  }

  const rfD = RISK_FREE_RATE / 252
  const std = Math.sqrt(pr.reduce((s, r) => s + (r - avgP) ** 2, 0) / (n - 1))
  const sharpe = std > 0 ? ((avgP - rfD) / std) * Math.sqrt(252) : 0
  const ds = pr.filter(r => r < rfD)
  const dsDev = ds.length > 0 ? Math.sqrt(ds.reduce((s, r) => s + (r - rfD) ** 2, 0) / ds.length) : 0
  const sortino = dsDev > 0 ? ((avgP - rfD) / dsDev) * Math.sqrt(252) : 0

  return { annualizedReturn: annRet, maxDrawdown: maxDD * 100, ddPeakDate, ddTroughDate,
           correlation, beta, alpha, sharpe, sortino }
}

export function computeSectorData(openTrades) {
  const s = {}
  openTrades.forEach(t => {
    const k = t.sector || 'Unknown'
    s[k] = (s[k] || 0) + (t.marketVal || 0)
  })
  return Object.entries(s).map(([name, value]) => ({ name, value: Math.round(value) })).sort((a, b) => b.value - a.value)
}

export function computeHoldingsData(openTrades) {
  return openTrades
    .map(t => ({ name: t.ticker, value: Math.round(t.marketVal || 0), weight: parseFloat(t.weight?.toFixed(1) || 0) }))
    .sort((a, b) => b.value - a.value)
}

/** Merge repeated tickers into single entries for pie chart display */
export function computeMergedHoldingsData(openTrades) {
  const byTicker = {}
  openTrades.forEach(t => {
    const key = t.ticker
    if (!byTicker[key]) byTicker[key] = { name: key, value: 0, weight: 0 }
    byTicker[key].value += Math.round(t.marketVal || 0)
    byTicker[key].weight = parseFloat((byTicker[key].weight + (t.weight || 0)).toFixed(1))
  })
  return Object.values(byTicker).sort((a, b) => b.value - a.value)
}
