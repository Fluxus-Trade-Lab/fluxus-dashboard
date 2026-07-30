import { todayStr, RISK_FREE_RATE } from './portfolioFormat'
import { lookupPrice, rejectRevertingSpikes } from './calculations'
import { unadjustClose } from './splitTable'

const _median = (a) => {
  const s = [...a].sort((x, y) => x - y)
  const m = Math.floor(s.length / 2)
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}

/**
 * Fill-anchored split correction — the robust valuation basis.
 *
 * The feed is retroactively split-adjusted, and split feeds are unreliable for
 * leveraged ETFs (yfinance even misses some). Rather than detect/snap a split
 * per trade (which fails on repeated splits and false-flags straddles, leaving a
 * position marked at the raw inflated feed = a phantom spike), we anchor each
 * position's marks to its OWN as-traded fills:
 *   ratio(fill) = fill_price / feed_close_on_fill_date
 * grouped into eras that break on a >30% jump (a split). The per-era median is
 * the multiplier that puts that era's feed closes back on the as-traded scale.
 * A ratio inside [0.67, 1.5] means "fills ≈ closes" → no split → factor 1, so
 * ordinary (non-split) tickers are never perturbed. Realized P&L (from the log)
 * is untouched; only the daily marks are corrected.
 *
 * @returns {(ticker:string, date:string)=>number} correction factor (default 1)
 */
export function buildFillAnchoredCorrections(trades, dailyPrices) {
  const fills = {}
  for (const t of trades) {
    const pts = [[(t.entryDate || '').slice(0, 10), t.entryPrice],
      ...(t.trims || []).map(tr => [(tr.date || '').slice(0, 10), tr.price])]
    for (const [d, px] of pts) {
      const f = lookupPrice(t.ticker, d, dailyPrices, null)
      if (f != null && f > 0 && px > 0) (fills[t.ticker] ||= []).push([d, px / f])
    }
  }
  const eras = {}
  for (const [tk, pts] of Object.entries(fills)) {
    pts.sort((a, b) => (a[0] < b[0] ? -1 : 1))
    const es = []
    for (const [d, r] of pts) {
      const last = es[es.length - 1]
      if (last && Math.abs(r - _median(last.f)) / _median(last.f) < 0.30) {
        last.f.push(r); last.end = d
      } else {
        es.push({ start: d, end: d, f: [r] })
      }
    }
    for (const e of es) {
      const m = _median(e.f)
      e.factor = (m > 0.67 && m < 1.5) ? 1 : m // near 1 → no split → don't perturb
    }
    eras[tk] = es
  }
  const dd = (a, b) => Math.abs((new Date(a) - new Date(b)) / 86400000)
  return (tk, date) => {
    const es = eras[tk]
    if (!es || !es.length) return 1
    for (const e of es) if (e.start <= date && date <= e.end) return e.factor
    let best = es[0], bd = Infinity
    for (const e of es) {
      const g = Math.min(dd(date, e.start), dd(date, e.end))
      if (g < bd) { bd = g; best = e }
    }
    return best.factor
  }
}

/**
 * Build the equity curve: daily portfolio value from first trade to today.
 *
 * Trades are valued AS-TRADED (never mutated). Each daily mark uses an
 * "effective" price on the as-traded scale:
 *   1. the frozen snapshot (immutable truth), if present for that ticker/date;
 *   2. else the live feed un-adjusted via the explicit SPLIT_TABLE.
 * This makes MTM immune to retroactive split re-scaling — the class of bug that
 * produced the ~6000% May spike (a leveraged ETF that reverse-split repeatedly,
 * whose feed was inflated ~90× while shares stayed as-traded).
 *
 * @param {object} [options]
 * @param {Record<string,number>} [options.frozenPrices]  `TICKER:DATE` → asTraded close
 * @param {object} [options.splitTable]                    defaults to SPLIT_TABLE
 */
export function buildEquityCurve(trades, startingCapital, dailyPrices, benchmarkHistories, options = {}) {
  if (!trades.length) return []
  // splitTable defaults to {} (no-op) so the legacy caller — which passes
  // already-adjusted trades — is never double-corrected. The new as-traded model
  // opts in by passing an explicit splitTable (and/or frozenPrices).
  const { frozenPrices = {} } = options

  // Fill-anchored correction derived from these trades' own fills — robust to
  // repeated splits, missing split data, and false straddle flags (the residual
  // 05-17 spike). No-op (factor 1) for non-split tickers and already-adjusted fills.
  // This supersedes the explicit split-table un-adjust (which double-corrected).
  const correctionFor = buildFillAnchoredCorrections(trades, dailyPrices)

  // Effective as-traded-scale price: frozen snapshot (immutable truth) first;
  // else the feed put back on the as-traded scale via the fill-anchored factor.
  const effAt = (tk, date) => {
    const key = `${tk}:${date}`
    if (frozenPrices[key] != null) return frozenPrices[key]
    const adj = lookupPrice(tk, date, dailyPrices, null)
    if (adj == null) return null
    return adj * correctionFor(tk, date)
  }

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
    const raw = datePoints.map(d => effAt(tk, d))
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
        ?? effAt(t.ticker, date)
        ?? t.entryPrice
      marketValue += qtyAtDate * price * dir
    })

    const totalValue = cash + marketValue
    return {
      date,
      value: totalValue,
      returnPct: ((totalValue - startingCapital) / startingCapital) * 100,
      cash,
      marketValue,
      cashPct: totalValue ? (cash / totalValue) * 100 : 100,
      deployedPct: totalValue ? (marketValue / totalValue) * 100 : 0,
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
export function getPortfolioValueAtDate(trades, startingCapital, asOfDate, dailyPrices, options = {}) {
  // splitTable defaults to {} (no-op) so the legacy caller — which passes
  // already-adjusted trades — is never double-corrected. The new as-traded model
  // opts in by passing an explicit splitTable (and/or frozenPrices).
  const { frozenPrices = {}, splitTable = {} } = options
  const effAt = (tk, date) => {
    const key = `${tk}:${date}`
    if (frozenPrices[key] != null) return frozenPrices[key]
    return unadjustClose(lookupPrice(tk, date, dailyPrices, null), tk, date, splitTable)
  }
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

    mktVal += qtyAtDate * (effAt(t.ticker, asOfDate) ?? t.entryPrice) * dir
  })

  return cash + mktVal
}

/**
 * Max drawdown on the mark-to-market equity curve — the reporting standard
 * (peak-to-trough of daily net-liq incl. open positions, as % of the peak).
 * @param {{date:string, value:number}[]} curve
 */
export function computeDrawdown(curve) {
  let peak = -Infinity, peakDate = null
  let maxDrawdown = 0, maxDrawdownPct = 0, troughDate = null, atPeak = null
  for (const pt of curve) {
    if (pt.value > peak) { peak = pt.value; peakDate = pt.date }
    if (peak <= 0) continue
    const dd = pt.value - peak
    if (dd < maxDrawdown) {
      maxDrawdown = dd
      maxDrawdownPct = (dd / peak) * 100
      troughDate = pt.date
      atPeak = peakDate
    }
  }
  return { maxDrawdown, maxDrawdownPct, peakDate: atPeak, troughDate }
}

/**
 * Sharpe / Sortino / Calmar and annualized stats from the daily MTM curve.
 * Daily returns are computed on the (weekday) value series and annualized ×252.
 */
export function computeRiskRatios(curve, options = {}) {
  const rf = options.riskFreeRate ?? RISK_FREE_RATE // annualized
  const PPY = 252
  const rets = []
  for (let i = 1; i < curve.length; i++) {
    const prev = curve[i - 1].value
    if (prev > 0) rets.push(curve[i].value / prev - 1)
  }
  if (rets.length < 2) return { sharpe: null, sortino: null, calmar: null, cagr: null, volAnn: null }

  const mean = rets.reduce((a, b) => a + b, 0) / rets.length
  const variance = rets.reduce((a, b) => a + (b - mean) ** 2, 0) / (rets.length - 1)
  const sd = Math.sqrt(variance)
  const downSq = rets.filter(r => r < 0).reduce((a, b) => a + b * b, 0) / rets.length
  const downside = Math.sqrt(downSq)
  const rfDaily = rf / PPY

  const sharpe = sd > 0 ? ((mean - rfDaily) / sd) * Math.sqrt(PPY) : null
  const sortino = downside > 0 ? ((mean - rfDaily) / downside) * Math.sqrt(PPY) : null

  const first = curve[0].value, last = curve[curve.length - 1].value
  const years = rets.length / PPY
  const cagr = years > 0 && first > 0 ? Math.pow(last / first, 1 / years) - 1 : null
  const { maxDrawdownPct } = computeDrawdown(curve)
  const calmar = cagr != null && maxDrawdownPct < 0 ? cagr / (Math.abs(maxDrawdownPct) / 100) : null

  return { sharpe, sortino, calmar, cagr, volAnn: sd * Math.sqrt(PPY), maxDrawdownPct }
}
