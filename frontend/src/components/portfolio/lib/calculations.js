import { daysBetween, todayStr, RISK_FREE_RATE } from './portfolioFormat'

/**
 * Look up the best available price for a ticker on a date.
 * Tries exact date, then walks back up to 5 days for weekends/holidays.
 * Returns entryPrice as last resort.
 */
export function lookupPrice(ticker, date, dailyPrices, fallback) {
  for (let d = 0; d < 5; d++) {
    const checkDate = new Date(date)
    checkDate.setDate(checkDate.getDate() - d)
    const key = `${ticker}:${checkDate.toISOString().split('T')[0]}`
    if (dailyPrices[key] != null) return dailyPrices[key]
  }
  return fallback
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
    const riskUnit = Math.abs(t.entryPrice - t.stopPrice)

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
    const lastP = lookupPrice(t.ticker, today, dailyPrices, t.entryPrice)
    // Previous close: look up yesterday (or most recent prior trading day)
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const prevC = lookupPrice(t.ticker, yesterday.toISOString().split('T')[0], dailyPrices, lastP)

    const marketVal = t.currentQty * lastP
    const change1D = prevC > 0 && lastP !== prevC ? ((lastP - prevC) / prevC) * 100 : 0
    const pl1D = t.currentQty * (lastP - prevC) * dir
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
  enrichedTrades.forEach(t => (t.trims || []).forEach(tr => {
    const m = tr.date?.slice(0, 7) || 'Unknown'
    if (!byMonth[m]) byMonth[m] = []
    const dir = t.direction === 'long' ? 1 : -1
    byMonth[m].push({
      retPct: t.entryPrice > 0 ? ((tr.price - t.entryPrice) / t.entryPrice) * 100 * dir : 0,
      holdingDays: daysBetween(t.entryDate, tr.date),
      pl: tr.qty * (tr.price - t.entryPrice) * dir,
    })
  }))

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

  const allMonths = [...new Set([...Object.keys(byMonth), ...Object.keys(monthlyPortRet)])].sort()

  return allMonths.map(m => {
    const tds = byMonth[m] || []
    const wins = tds.filter(x => x.retPct > 0)
    const losses = tds.filter(x => x.retPct <= 0)
    return {
      month: m, totalTrades: tds.length,
      monthlyRetPct: monthlyPortRet[m] || 0,
      totalPL: tds.reduce((s, x) => s + x.pl, 0),
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
  const allExits = []
  enrichedTrades.forEach(t => (t.trims || []).forEach(tr => {
    const dir = t.direction === 'long' ? 1 : -1
    allExits.push({
      retPct: t.entryPrice > 0 ? ((tr.price - t.entryPrice) / t.entryPrice) * 100 * dir : 0,
      holdingDays: daysBetween(t.entryDate, tr.date),
    })
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

  let peak = 1, maxDD = 0, eq = 1
  pr.forEach(r => {
    eq *= (1 + r)
    if (eq > peak) peak = eq
    const dd = (peak - eq) / peak
    if (dd > maxDD) maxDD = dd
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

  return { annualizedReturn: annRet, maxDrawdown: maxDD * 100, correlation, beta, alpha, sharpe, sortino }
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
