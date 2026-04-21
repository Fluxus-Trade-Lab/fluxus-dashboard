import { lookupPrice } from './calculations'

// ── Default rules ──

export const DEFAULT_RULES = {
  capital: 1000000,
  riskPerTrade: 0.0025,    // 0.25%
  buffer: 0.0025,          // 0.25%
  minRR: 3,                // 3:1 minimum R/R
  overtradingWindow: 5,    // trading days
  overtradingMax: 8,       // max entries in window
  sizingToleranceLow: 0.6, // 60% of target = too small
  sizingToleranceHigh: 1.4,// 140% of target = too big
  circuitBreakerStreak: 6, // consecutive demons to trigger stop
  maxTotalHeat: 0.03,      // 3% max total risk exposure
  maxSectorHeat: 0.015,    // 1.5% max per sector/theme
  tacticalTrimTarget: 0.33,// first trim should be ~1/3 of position
  tacticalTrimRR: 3,       // first trim at ~3R profit
}

// ── Market signal reconstruction ──

function getSpyPrices(dailyPrices, upToDate, daysNeeded = 250) {
  const prices = []
  const d = new Date(upToDate)
  for (let i = 0; i < daysNeeded + 100; i++) {
    const key = `SPY:${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    const p = dailyPrices[key]
    if (p != null) prices.unshift({ date: key.split(':')[1], close: p })
    d.setDate(d.getDate() - 1)
  }
  return prices
}

function computeEMA(prices, span) {
  const k = 2 / (span + 1)
  let ema = prices[0]
  for (let i = 1; i < prices.length; i++) {
    ema = prices[i] * k + ema * (1 - k)
  }
  return ema
}

function computeSMA(prices, period) {
  if (prices.length < period) return null
  const slice = prices.slice(-period)
  return slice.reduce((s, v) => s + v, 0) / period
}

export function reconstructSignal(date, dailyPrices) {
  const history = getSpyPrices(dailyPrices, date, 250)
  if (history.length < 200) return null

  const closes = history.map(h => h.close)
  const close = closes[closes.length - 1]
  const ema8 = computeEMA(closes, 8)
  const ema21 = computeEMA(closes, 21)
  const sma50 = computeSMA(closes, 50)
  const sma200 = computeSMA(closes, 200)

  if (sma50 == null || sma200 == null) return null

  if (ema8 > ema21 && ema21 > sma50 && sma50 > sma200) {
    return { signal: 'POWER_3', color: 'green' }
  } else if (ema8 > ema21 && close > sma200) {
    return { signal: 'CAUTION', color: 'yellow' }
  } else if (close > sma200) {
    return { signal: 'WARNING', color: 'orange' }
  }
  return { signal: 'RISK_OFF', color: 'red' }
}

// ── Demon detectors ──

function detectBadEnvironment(trade, dailyPrices) {
  const sig = reconstructSignal(trade.entryDate, dailyPrices)
  if (!sig) return false
  return sig.signal === 'WARNING' || sig.signal === 'RISK_OFF'
}

function detectFightingTrend(trade, dailyPrices) {
  const history = getSpyPrices(dailyPrices, trade.entryDate, 30)
  if (history.length < 21) return false

  const closes = history.map(h => h.close)
  const ema21 = computeEMA(closes, 21)
  const close = closes[closes.length - 1]

  if (trade.direction === 'long' && close < ema21) return true
  if (trade.direction === 'short' && close > ema21) return true
  return false
}

function detectOvertrading(trade, allTrades, rules) {
  const entryDate = new Date(trade.entryDate)
  const windowStart = new Date(entryDate)
  windowStart.setDate(windowStart.getDate() - (rules.overtradingWindow * 1.5)) // ~5 trading days ≈ 7 calendar days

  const entriesInWindow = allTrades.filter(t => {
    const d = new Date(t.entryDate)
    return d >= windowStart && d <= entryDate
  })

  return entriesInWindow.length > rules.overtradingMax
}

function detectPoorRR(trade, rules) {
  const riskPerShare = Math.abs(trade.entryPrice - trade.stopPrice)
  if (riskPerShare === 0) return false
  // For the R/R check, we look at the risk distance relative to a reasonable target
  // A 3:1 R/R means the reward target should be 3x the risk
  // We flag if the risk is too wide (stop too far) making 3:1 unrealistic
  // Simple check: is the stop distance > 10% of entry? That makes 30% target needed
  const riskPct = riskPerShare / trade.entryPrice
  if (riskPct > 0.10) return true // stop too far for reasonable R/R
  // Also flag if explicit R/R is below minimum (when we have exit data)
  if (trade.isClosed && trade.rr != null && trade.rr < 0 && Math.abs(trade.rr) > 1) return false // normal loss
  return false
}

function detectBetTooBig(trade, rules) {
  const riskPerShare = Math.abs(trade.entryPrice - trade.stopPrice)
  const positionRisk = riskPerShare * trade.originalQty
  const targetRisk = rules.capital * rules.riskPerTrade
  return positionRisk > targetRisk * rules.sizingToleranceHigh
}

function detectBetTooSmall(trade, rules) {
  const riskPerShare = Math.abs(trade.entryPrice - trade.stopPrice)
  const positionRisk = riskPerShare * trade.originalQty
  const targetRisk = rules.capital * rules.riskPerTrade
  return positionRisk < targetRisk * rules.sizingToleranceLow
}

function detectTotalHeatExceeded(trade, allTrades, rules, dailyPrices) {
  // Check: at the time of this trade's entry, was total open heat > maxTotalHeat?
  const entryDate = trade.entryDate
  const openAtEntry = allTrades.filter(t => {
    if (t.entryDate > entryDate) return false // opened after
    if (t.isClosed) {
      const trims = t.trims || []
      const lastTrim = trims[trims.length - 1]
      if (lastTrim && lastTrim.date <= entryDate) return false // closed before
    }
    return true
  })

  let totalHeat = 0
  for (const t of openAtEntry) {
    const riskPerShare = Math.abs(t.entryPrice - t.stopPrice)
    const qty = t.currentQty || t.originalQty
    totalHeat += riskPerShare * qty
  }

  return totalHeat / rules.capital > rules.maxTotalHeat
}

function detectSectorHeatExceeded(trade, allTrades, rules) {
  if (!trade.sector) return false
  const entryDate = trade.entryDate

  const sectorOpenAtEntry = allTrades.filter(t => {
    if (t.sector !== trade.sector) return false
    if (t.entryDate > entryDate) return false
    if (t.isClosed) {
      const trims = t.trims || []
      const lastTrim = trims[trims.length - 1]
      if (lastTrim && lastTrim.date <= entryDate) return false
    }
    return true
  })

  let sectorHeat = 0
  for (const t of sectorOpenAtEntry) {
    const riskPerShare = Math.abs(t.entryPrice - t.stopPrice)
    const qty = t.currentQty || t.originalQty
    sectorHeat += riskPerShare * qty
  }

  return sectorHeat / rules.capital > rules.maxSectorHeat
}

function detectNotInPlan() {
  // Placeholder — will cross-reference screener snapshots when available
  return false
}

// ── Tactical discipline analysis ──

export function computeTacticalStats(enrichedTrades) {
  const tradesWithTrims = enrichedTrades.filter(t => (t.trims || []).length > 0)
  if (tradesWithTrims.length === 0) return null

  const analyses = tradesWithTrims.map(t => {
    const firstTrim = t.trims[0]
    const trimRatio = firstTrim.qty / t.originalQty
    const dir = t.direction === 'long' ? 1 : -1
    const riskPerShare = Math.abs(t.entryPrice - t.stopPrice)
    const profitPerShare = (firstTrim.price - t.entryPrice) * dir
    const trimRR = riskPerShare > 0 ? profitPerShare / riskPerShare : 0
    const daysToTrim = Math.max(0, Math.round((new Date(firstTrim.date) - new Date(t.entryDate)) / 86400000))

    return {
      ticker: t.ticker,
      entryDate: t.entryDate,
      trimDate: firstTrim.date,
      trimRatio,
      trimRR,
      daysToTrim,
      isGoodSize: trimRatio >= 0.25 && trimRatio <= 0.40, // ~1/3
      isGoodRR: trimRR >= 2.0, // at least 2R
    }
  })

  const goodSizeCount = analyses.filter(a => a.isGoodSize).length
  const goodRRCount = analyses.filter(a => a.isGoodRR).length
  const avgTrimRatio = analyses.reduce((s, a) => s + a.trimRatio, 0) / analyses.length
  const avgTrimRR = analyses.reduce((s, a) => s + a.trimRR, 0) / analyses.length
  const avgDaysToTrim = analyses.reduce((s, a) => s + a.daysToTrim, 0) / analyses.length

  return {
    totalTrades: tradesWithTrims.length,
    avgTrimRatio,
    avgTrimRR,
    avgDaysToTrim,
    goodSizeRate: (goodSizeCount / analyses.length) * 100,
    goodRRRate: (goodRRCount / analyses.length) * 100,
    trades: analyses,
  }
}

// ── Main analysis ──

export const DEMONS = [
  { id: 'bad-environment', name: 'Bad Environment', icon: '\u26C8', desc: 'Entered in WARNING or RISK_OFF market' },
  { id: 'fighting-trend', name: 'Fighting Trend', icon: '\u2194', desc: 'Traded against SPY 21EMA direction' },
  { id: 'overtrading', name: 'Overtrading', icon: '\u26A1', desc: 'Too many entries in a short window' },
  { id: 'poor-rr', name: 'Poor R/R', icon: '\u2696', desc: 'Entry R/R below minimum threshold' },
  { id: 'bet-too-big', name: 'Bet Too Big', icon: '\u2B06', desc: 'Position risk exceeds tolerance band' },
  { id: 'bet-too-small', name: 'Bet Too Small', icon: '\u2B07', desc: 'Position risk below tolerance band' },
  { id: 'total-heat', name: 'Total Heat', icon: '\uD83D\uDD25', desc: 'Total open risk > 3% of equity' },
  { id: 'sector-heat', name: 'Sector Heat', icon: '\uD83C\uDFAF', desc: 'Sector risk > 1.5% of equity' },
  { id: 'not-in-plan', name: 'Not In Plan', icon: '\u2753', desc: 'Ticker not on screener at entry time' },
]

export function analyzeTrades(enrichedTrades, dailyPrices, rules = DEFAULT_RULES) {
  // Sort by entry date chronologically
  const sorted = [...enrichedTrades].sort((a, b) => a.entryDate.localeCompare(b.entryDate))

  const results = sorted.map(trade => {
    const demons = []

    if (detectBadEnvironment(trade, dailyPrices)) demons.push('bad-environment')
    if (detectFightingTrend(trade, dailyPrices)) demons.push('fighting-trend')
    if (detectOvertrading(trade, sorted, rules)) demons.push('overtrading')
    if (detectPoorRR(trade, rules)) demons.push('poor-rr')
    if (detectBetTooBig(trade, rules)) demons.push('bet-too-big')
    if (detectBetTooSmall(trade, rules)) demons.push('bet-too-small')
    if (detectTotalHeatExceeded(trade, sorted, rules, dailyPrices)) demons.push('total-heat')
    if (detectSectorHeatExceeded(trade, sorted, rules)) demons.push('sector-heat')
    if (detectNotInPlan()) demons.push('not-in-plan')

    return {
      ...trade,
      demons,
      isClean: demons.length === 0,
    }
  })

  return results
}

export function computeDemonStats(analyzedTrades, rules = DEFAULT_RULES) {
  const last30 = analyzedTrades.slice(-30)

  return DEMONS.map(demon => {
    const fireCount = last30.filter(t => t.demons.includes(demon.id)).length
    const fireRate = last30.length > 0 ? (fireCount / last30.length) * 100 : 0

    // Compute current streak and longest streak
    let currentStreak = 0
    let longestStreak = 0
    let streak = 0

    for (const trade of analyzedTrades) {
      if (trade.demons.includes(demon.id)) {
        streak++
        longestStreak = Math.max(longestStreak, streak)
      } else {
        streak = 0
      }
    }
    currentStreak = streak

    const isCircuitBreaker = currentStreak >= rules.circuitBreakerStreak

    // Win rate comparison: trades WITH this demon vs WITHOUT
    const withDemon = analyzedTrades.filter(t => t.demons.includes(demon.id) && t.isClosed)
    const withoutDemon = analyzedTrades.filter(t => !t.demons.includes(demon.id) && t.isClosed)
    const winRateWith = withDemon.length > 0
      ? (withDemon.filter(t => t.totalPL > 0).length / withDemon.length) * 100 : null
    const winRateWithout = withoutDemon.length > 0
      ? (withoutDemon.filter(t => t.totalPL > 0).length / withoutDemon.length) * 100 : null

    return {
      ...demon,
      fireCount,
      fireRate,
      currentStreak,
      longestStreak,
      isCircuitBreaker,
      winRateWith,
      winRateWithout,
    }
  })
}

export function getActiveCircuitBreakers(demonStats) {
  return demonStats.filter(d => d.isCircuitBreaker)
}
