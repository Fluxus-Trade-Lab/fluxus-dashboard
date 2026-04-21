import { lookupPrice } from './calculations'
import { todayStr } from './portfolioFormat'

/**
 * Compute 60-day rolling beta for a ticker vs SPY.
 * beta = cov(ticker_returns, spy_returns) / var(spy_returns)
 */
export function computeBeta(ticker, dailyPrices, spyHistory) {
  if (!spyHistory?.length) return null

  const sorted = [...spyHistory].sort((a, b) => a.date.localeCompare(b.date))
  const last60 = sorted.slice(-61) // need 61 points for 60 returns
  if (last60.length < 21) return null

  const spyReturns = []
  const tickerReturns = []

  for (let i = 1; i < last60.length; i++) {
    const spyPrev = last60[i - 1].close
    const spyCur = last60[i].close
    if (!spyPrev || !spyCur) continue

    const date = last60[i].date
    const prevDate = last60[i - 1].date
    const tCur = lookupPrice(ticker, date, dailyPrices, null)
    const tPrev = lookupPrice(ticker, prevDate, dailyPrices, null)
    if (tCur == null || tPrev == null || tPrev === 0) continue

    spyReturns.push((spyCur - spyPrev) / spyPrev)
    tickerReturns.push((tCur - tPrev) / tPrev)
  }

  if (spyReturns.length < 20) return null

  const n = spyReturns.length
  const avgSpy = spyReturns.reduce((s, r) => s + r, 0) / n
  const avgTicker = tickerReturns.reduce((s, r) => s + r, 0) / n

  let cov = 0, varSpy = 0
  for (let i = 0; i < n; i++) {
    cov += (tickerReturns[i] - avgTicker) * (spyReturns[i] - avgSpy)
    varSpy += (spyReturns[i] - avgSpy) ** 2
  }

  return varSpy > 0 ? cov / varSpy : null
}

/**
 * Portfolio heat: sum of (position size × distance-to-stop%) for each open position.
 * Returns { totalHeat, positions: [{ ticker, heat, hasStop, weight, distToStop }] }
 */
export function computePortfolioHeat(openTrades, dailyPrices, portfolioValue) {
  const today = todayStr()
  const positions = []
  let totalHeat = 0
  let noStopCount = 0

  openTrades.forEach(t => {
    const price = lookupPrice(t.ticker, today, dailyPrices, t.entryPrice)
    const mktVal = t.currentQty * price
    const weight = portfolioValue > 0 ? (mktVal / portfolioValue) * 100 : 0
    const dir = t.direction === 'long' ? 1 : -1

    if (!t.stopPrice || t.stopPrice === 0) {
      noStopCount++
      positions.push({ ticker: t.ticker, id: t.id, heat: null, hasStop: false, weight, distToStop: null, mktVal })
      return
    }

    const distToStop = Math.abs(price - t.stopPrice) / price * 100
    const heat = portfolioValue > 0 ? (mktVal * Math.abs(price - t.stopPrice) / price) / portfolioValue * 100 : 0
    totalHeat += heat

    positions.push({ ticker: t.ticker, id: t.id, heat, hasStop: true, weight, distToStop, mktVal })
  })

  positions.sort((a, b) => (b.heat ?? 0) - (a.heat ?? 0))

  return { totalHeat, positions, noStopCount }
}

/**
 * Trim analysis: for each closed trade with trims, compare trim price vs max price
 * in N trading days after the trim.
 */
export function computeTrimAnalysis(closedTrades, dailyPrices, lookAheadDays = 10) {
  const results = []

  closedTrades.forEach(t => {
    const trims = t.trims || []
    if (trims.length === 0) return
    const dir = t.direction === 'long' ? 1 : -1

    trims.forEach((trim, idx) => {
      const trimDate = trim.date?.slice(0, 10)
      if (!trimDate) return

      // Find peak price in lookAheadDays after trim
      let peak = null
      let peakDate = null
      for (let d = 1; d <= lookAheadDays * 2; d++) { // *2 to account for weekends
        const checkDate = new Date(trimDate)
        checkDate.setDate(checkDate.getDate() + d)
        if (checkDate.getDay() === 0 || checkDate.getDay() === 6) continue

        const dateStr = checkDate.toISOString().split('T')[0]
        const price = lookupPrice(t.ticker, dateStr, dailyPrices, null)
        if (price == null) continue

        if (dir === 1) {
          if (peak == null || price > peak) { peak = price; peakDate = dateStr }
        } else {
          if (peak == null || price < peak) { peak = price; peakDate = dateStr }
        }
      }

      if (peak == null) return

      const leftOnTable = dir === 1
        ? ((peak - trim.price) / trim.price) * 100
        : ((trim.price - peak) / trim.price) * 100
      const captured = (t.entryPrice !== peak)
        ? ((trim.price - t.entryPrice) * dir) / (Math.abs(peak - t.entryPrice)) * 100
        : 100

      results.push({
        ticker: t.ticker,
        direction: t.direction,
        entryPrice: t.entryPrice,
        trimPrice: trim.price,
        trimDate,
        trimQty: trim.qty,
        trimIndex: idx + 1,
        peakAfterTrim: peak,
        peakDate,
        leftOnTable: Math.max(0, leftOnTable),
        captured: Math.min(100, Math.max(0, captured)),
        tooEarly: leftOnTable > 5,
      })
    })
  })

  results.sort((a, b) => b.leftOnTable - a.leftOnTable)
  return results
}

/**
 * Stop analysis: identify stopped-out trades and check if stock recovered.
 */
export function computeStopAnalysis(closedTrades, dailyPrices, lookAheadDays = 10) {
  const results = []

  closedTrades.forEach(t => {
    const trims = t.trims || []
    if (trims.length === 0) return
    if (!t.stopPrice || t.stopPrice === 0) return

    const lastTrim = trims[trims.length - 1]
    const exitPrice = lastTrim.price
    const exitDate = lastTrim.date?.slice(0, 10)
    if (!exitDate) return

    const dir = t.direction === 'long' ? 1 : -1
    // Check if exit was near the stop (within 1%)
    const distToStop = Math.abs(exitPrice - t.stopPrice) / t.stopPrice
    if (distToStop > 0.01) return // Not a stop-out

    // Find recovery peak after stop-out
    let recoveryPeak = null
    let recoveryDate = null
    for (let d = 1; d <= lookAheadDays * 2; d++) {
      const checkDate = new Date(exitDate)
      checkDate.setDate(checkDate.getDate() + d)
      if (checkDate.getDay() === 0 || checkDate.getDay() === 6) continue

      const dateStr = checkDate.toISOString().split('T')[0]
      const price = lookupPrice(t.ticker, dateStr, dailyPrices, null)
      if (price == null) continue

      if (dir === 1) {
        if (recoveryPeak == null || price > recoveryPeak) { recoveryPeak = price; recoveryDate = dateStr }
      } else {
        if (recoveryPeak == null || price < recoveryPeak) { recoveryPeak = price; recoveryDate = dateStr }
      }
    }

    if (recoveryPeak == null) return

    const recoveryPct = dir === 1
      ? ((recoveryPeak - exitPrice) / exitPrice) * 100
      : ((exitPrice - recoveryPeak) / exitPrice) * 100

    results.push({
      ticker: t.ticker,
      direction: t.direction,
      entryPrice: t.entryPrice,
      stopPrice: t.stopPrice,
      exitPrice,
      exitDate,
      recoveryPeak,
      recoveryDate,
      recoveryPct,
      stopTooTight: recoveryPct > 5,
      stopDistPct: Math.abs(t.stopPrice - t.entryPrice) / t.entryPrice * 100,
    })
  })

  results.sort((a, b) => b.recoveryPct - a.recoveryPct)
  return results
}

/**
 * Per-position volatility contribution.
 * Vol contribution ≈ weight × daily_vol (simplified).
 */
export function computeVolContribution(openTrades, dailyPrices, spyHistory, portfolioValue) {
  const today = todayStr()
  const results = []

  openTrades.forEach(t => {
    const price = lookupPrice(t.ticker, today, dailyPrices, t.entryPrice)
    const mktVal = t.currentQty * price
    const weight = portfolioValue > 0 ? mktVal / portfolioValue : 0

    // Compute daily vol from last 20 trading days
    const returns = []
    if (spyHistory?.length) {
      const sorted = [...spyHistory].sort((a, b) => a.date.localeCompare(b.date))
      const recent = sorted.slice(-21)
      for (let i = 1; i < recent.length; i++) {
        const prev = lookupPrice(t.ticker, recent[i - 1].date, dailyPrices, null)
        const cur = lookupPrice(t.ticker, recent[i].date, dailyPrices, null)
        if (prev && cur && prev > 0) returns.push((cur - prev) / prev)
      }
    }

    const dailyVol = returns.length >= 10
      ? Math.sqrt(returns.reduce((s, r) => s + (r - returns.reduce((a, b) => a + b, 0) / returns.length) ** 2, 0) / (returns.length - 1))
      : null
    const annualizedVol = dailyVol != null ? dailyVol * Math.sqrt(252) * 100 : null

    const beta = computeBeta(t.ticker, dailyPrices, spyHistory)
    const volContribution = dailyVol != null ? weight * dailyVol * 100 : null

    results.push({
      ticker: t.ticker,
      id: t.id,
      weight: weight * 100,
      mktVal,
      dailyVol: dailyVol != null ? dailyVol * 100 : null,
      annualizedVol,
      beta,
      volContribution,
    })
  })

  results.sort((a, b) => (b.volContribution ?? 0) - (a.volContribution ?? 0))
  return results
}

/**
 * Compute portfolio-level volatility from equity curve.
 */
export function computePortfolioVol(performanceData) {
  if (!performanceData || performanceData.length < 21) return null

  const returns = []
  for (let i = 1; i < performanceData.length; i++) {
    const prev = 1 + performanceData[i - 1].returnPct / 100
    const cur = 1 + performanceData[i].returnPct / 100
    if (prev > 0) returns.push((cur - prev) / prev)
  }

  if (returns.length < 20) return null

  const avg = returns.reduce((s, r) => s + r, 0) / returns.length
  const variance = returns.reduce((s, r) => s + (r - avg) ** 2, 0) / (returns.length - 1)
  const dailyVol = Math.sqrt(variance)

  // Rolling 20-day vol
  const rolling = []
  for (let i = 19; i < returns.length; i++) {
    const window = returns.slice(i - 19, i + 1)
    const wAvg = window.reduce((s, r) => s + r, 0) / window.length
    const wVar = window.reduce((s, r) => s + (r - wAvg) ** 2, 0) / (window.length - 1)
    rolling.push({
      date: performanceData[i + 1]?.date || performanceData[i].date,
      portfolioVol: Math.sqrt(wVar) * Math.sqrt(252) * 100,
    })
  }

  return {
    dailyVol: dailyVol * 100,
    annualizedVol: dailyVol * Math.sqrt(252) * 100,
    rolling,
  }
}

/**
 * Compute SPY rolling vol from benchmark history.
 */
export function computeSpyVol(spyHistory) {
  if (!spyHistory?.length || spyHistory.length < 21) return null

  const sorted = [...spyHistory].sort((a, b) => a.date.localeCompare(b.date))
  const returns = []
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i - 1].close > 0) {
      returns.push((sorted[i].close - sorted[i - 1].close) / sorted[i - 1].close)
    }
  }

  if (returns.length < 20) return null

  const avg = returns.reduce((s, r) => s + r, 0) / returns.length
  const variance = returns.reduce((s, r) => s + (r - avg) ** 2, 0) / (returns.length - 1)
  const dailyVol = Math.sqrt(variance)

  // Rolling 20-day vol
  const rolling = []
  for (let i = 19; i < returns.length; i++) {
    const window = returns.slice(i - 19, i + 1)
    const wAvg = window.reduce((s, r) => s + r, 0) / window.length
    const wVar = window.reduce((s, r) => s + (r - wAvg) ** 2, 0) / (window.length - 1)
    rolling.push({
      date: sorted[i + 1]?.date || sorted[i].date,
      spyVol: Math.sqrt(wVar) * Math.sqrt(252) * 100,
    })
  }

  return {
    annualizedVol: dailyVol * Math.sqrt(252) * 100,
    rolling,
  }
}

/**
 * Rule-based insights from trade data.
 */
export function computeInsights(enrichedTrades, monthlyStats, trimAnalysis, stopAnalysis) {
  const insights = []
  const closed = enrichedTrades.filter(t => t.isClosed)
  if (closed.length === 0) return insights

  const winners = closed.filter(t => t.totalPL > 0)
  const losers = closed.filter(t => t.totalPL <= 0)
  const winRate = (winners.length / closed.length) * 100

  // Win rate vs profit factor
  const grossGains = winners.reduce((s, t) => s + t.totalPL, 0)
  const grossLosses = Math.abs(losers.reduce((s, t) => s + t.totalPL, 0))
  const profitFactor = grossLosses > 0 ? grossGains / grossLosses : Infinity

  if (winRate < 50 && profitFactor > 1.5) {
    insights.push({ type: 'positive', text: `Low win rate (${winRate.toFixed(0)}%) but strong profit factor (${profitFactor.toFixed(1)}) — your winners more than compensate for frequent small losses.` })
  } else if (winRate > 60 && profitFactor < 1) {
    insights.push({ type: 'warning', text: `High win rate (${winRate.toFixed(0)}%) but profit factor below 1.0 — your losses are too large relative to gains. Consider tighter risk management.` })
  }

  // Holding period patterns
  const avgWinHold = winners.length > 0 ? winners.reduce((s, t) => s + t.holdingDays, 0) / winners.length : 0
  const avgLoseHold = losers.length > 0 ? losers.reduce((s, t) => s + t.holdingDays, 0) / losers.length : 0
  if (avgLoseHold > avgWinHold * 1.5 && losers.length >= 3) {
    insights.push({ type: 'warning', text: `Losers held ${avgLoseHold.toFixed(0)} days avg vs ${avgWinHold.toFixed(0)} for winners — consider cutting losers faster.` })
  } else if (avgWinHold > avgLoseHold * 1.3 && winners.length >= 3) {
    insights.push({ type: 'positive', text: `Winners held ${avgWinHold.toFixed(0)} days avg vs ${avgLoseHold.toFixed(0)} for losers — good discipline letting winners run.` })
  }

  // Consecutive loss streaks
  let maxStreak = 0, curStreak = 0
  const sortedByExit = [...closed].sort((a, b) => {
    const aDate = a.trims?.[a.trims.length - 1]?.date || a.entryDate
    const bDate = b.trims?.[b.trims.length - 1]?.date || b.entryDate
    return aDate.localeCompare(bDate)
  })
  sortedByExit.forEach(t => {
    if (t.totalPL <= 0) { curStreak++; maxStreak = Math.max(maxStreak, curStreak) }
    else curStreak = 0
  })
  if (maxStreak >= 5) {
    insights.push({ type: 'warning', text: `Max consecutive loss streak: ${maxStreak} trades. Consider reducing size after 3+ losses in a row.` })
  }

  // Trim analysis insights
  if (trimAnalysis?.length > 0) {
    const tooEarlyPct = trimAnalysis.filter(t => t.tooEarly).length / trimAnalysis.length * 100
    const avgLeftOnTable = trimAnalysis.reduce((s, t) => s + t.leftOnTable, 0) / trimAnalysis.length
    if (tooEarlyPct > 40) {
      insights.push({ type: 'warning', text: `${tooEarlyPct.toFixed(0)}% of trims were too early (stock ran 5%+ higher within 10 days). Avg left on table: ${avgLeftOnTable.toFixed(1)}%.` })
    }
  }

  // Stop analysis insights
  if (stopAnalysis?.length > 0) {
    const tooTightPct = stopAnalysis.filter(t => t.stopTooTight).length / stopAnalysis.length * 100
    if (tooTightPct > 30) {
      const avgStopDist = stopAnalysis.reduce((s, t) => s + t.stopDistPct, 0) / stopAnalysis.length
      insights.push({ type: 'warning', text: `${tooTightPct.toFixed(0)}% of stopped-out trades recovered 5%+. Avg stop distance was ${avgStopDist.toFixed(1)}% — consider widening stops.` })
    }
  }

  // Monthly consistency
  if (monthlyStats?.length >= 3) {
    const profitable = monthlyStats.filter(m => m.monthlyRetPct > 0).length
    const consistency = (profitable / monthlyStats.length) * 100
    if (consistency >= 70) {
      insights.push({ type: 'positive', text: `${consistency.toFixed(0)}% of months are profitable — strong consistency.` })
    } else if (consistency < 40) {
      insights.push({ type: 'warning', text: `Only ${consistency.toFixed(0)}% of months are profitable — review position sizing and trade selection.` })
    }
  }

  return insights
}
