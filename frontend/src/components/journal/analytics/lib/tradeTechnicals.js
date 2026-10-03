/**
 * Point-in-time technicals for a single trade, computed from a ticker's daily
 * OHLC array (the `ohlc_2y` / `ohlc_1y` block in data/output/tickers/<T>.json).
 *
 * Everything is evaluated *as of the entry date* — using only bars up to and
 * including that date — so a card shows what the chart looked like when the
 * trade was put on, not today. All pure functions; no fetching, no lookahead.
 */

import { toJstDate } from '../../../../lib/tradingDate'

const val = b => (typeof b === 'number' ? b : b?.close)

/** Simple moving average of the last `n` closes ending at index `end` (inclusive). */
export function sma(closes, n, end) {
  if (end + 1 < n) return null
  let s = 0
  for (let i = end - n + 1; i <= end; i++) s += closes[i]
  return s / n
}

/** EMA of period `n` evaluated at index `end`, seeded with the SMA of the first `n`. */
export function ema(closes, n, end) {
  if (end + 1 < n) return null
  const k = 2 / (n + 1)
  let e = 0
  for (let i = 0; i < n; i++) e += closes[i]
  e /= n
  for (let i = n; i <= end; i++) e = closes[i] * k + e * (1 - k)
  return e
}

/** Wilder ATR(14) at index `end`, using true range (needs high/low/prevClose). */
export function atr14(bars, end, period = 14) {
  if (end < period) return null
  const tr = []
  for (let i = end - period + 1; i <= end; i++) {
    const h = bars[i].high, l = bars[i].low, pc = bars[i - 1].close
    tr.push(Math.max(h - l, Math.abs(h - pc), Math.abs(l - pc)))
  }
  return tr.reduce((a, b) => a + b, 0) / period
}

/** Index of the last bar dated on or before `dateStr` (ISO). -1 if none. */
function indexAsOf(bars, dateStr) {
  let idx = -1
  for (let i = 0; i < bars.length; i++) {
    if (bars[i].date <= dateStr) idx = i
    else break
  }
  return idx
}

/**
 * Compute the technical snapshot for a trade.
 * @param bars  array of {date,open,high,low,close,volume} sorted ascending
 * @param trade {entryDate, entryPrice, direction}
 */
export function computeTradeTechnicals(bars, trade) {
  if (!Array.isArray(bars) || bars.length < 20) return null
  const entryDate = toJstDate(trade.entryDate)
  const idx = indexAsOf(bars, entryDate)
  if (idx < 20) return null // not enough history before the entry
  const closes = bars.map(val)
  // Reference price = the entry-day ADJUSTED close, so it shares the OHLC's
  // split/dividend scale. Comparing the raw as-traded fill to adjusted MAs would
  // mix scales (the old split bug); the fill only matters for P&L/R, not charts.
  const px = closes[idx]

  const ema20 = ema(closes, 20, idx)
  const sma50 = sma(closes, 50, idx)
  const sma200 = sma(closes, 200, idx)
  const sma50Prior = sma(closes, 50, Math.max(0, idx - 20))
  const atr = atr14(bars, idx)
  const prevClose = idx >= 1 ? bars[idx - 1].close : null

  // 20-day high/low into the entry (prior 20 bars, excluding entry bar)
  let hi20 = -Infinity, lo20 = Infinity
  for (let i = Math.max(0, idx - 20); i < idx; i++) { hi20 = Math.max(hi20, bars[i].high); lo20 = Math.min(lo20, bars[i].low) }

  const extAtr = atr ? (px - ema20) / atr : null            // + = above 20EMA (extended long)
  const stack = ema20 != null && sma50 != null
    ? (sma200 != null
        ? (ema20 > sma50 && sma50 > sma200 ? 'bull' : ema20 < sma50 && sma50 < sma200 ? 'bear' : 'mixed')
        : (ema20 > sma50 ? 'bull*' : 'bear*'))
    : null
  const sma50Slope = (sma50 != null && sma50Prior != null) ? (sma50 - sma50Prior) / sma50Prior * 100 : null

  return {
    asOf: bars[idx].date,
    refPrice: px,
    ema20, sma50, sma200, atr,
    atrPct: atr && px ? atr / px * 100 : null,
    extAtr,
    aboveEma20: ema20 != null ? px > ema20 : null,
    aboveSma50: sma50 != null ? px > sma50 : null,
    aboveSma200: sma200 != null ? px > sma200 : null,
    stack,
    sma50Slope,
    distHi20Pct: isFinite(hi20) ? (px - hi20) / hi20 * 100 : null,
    gapPct: prevClose ? (px - prevClose) / prevClose * 100 : null,
  }
}

/**
 * Label the setup. Winners → winning-type, losers → mistake-type. `isReattack`
 * is supplied by the caller (needs the full trade set to know prior red entries).
 *
 * `type` / `notes` are the English labels; `code` / `noteCodes` name the same
 * labels for the dictionary (jn.cs.type.<code>, jn.cs.note.<k>) with whatever
 * number they carry, so the page can print them in either language.
 */
export function classifyTrade(trade, tech, isReattack) {
  const long = trade.direction !== 'short'
  const win = (trade.realizedPL ?? trade.totalPL ?? 0) > 0
  const ext = tech?.extAtr
  const notes = []
  const noteCodes = []
  if (tech?.atrPct != null && tech.atrPct > 6) { notes.push('high-vol name'); noteCodes.push({ k: 'highVol' }) }

  if (win) {
    let type = 'Momentum long', code = 'momentumLong'
    if (!long) [type, code] = tech?.stack?.startsWith('bear') ? ['Trend short', 'trendShort'] : ['Counter-trend short', 'counterShort']
    else if (ext != null && ext > 3) [type, code] = ['Extended momentum (chased & worked)', 'extendedWorked']
    else if (tech?.stack?.startsWith('bull') && tech?.aboveEma20 && ext != null && ext >= 0.3) [type, code] = ['Momentum breakout', 'momentumBreakout']
    else if (tech?.aboveSma50 && ext != null && ext < 0.5 && tech?.sma50Slope > 0) [type, code] = ['Pullback continuation', 'pullbackCont']
    else if (tech?.stack?.startsWith('bull')) [type, code] = ['Trend continuation', 'trendCont']
    return { type, code, win: true, notes, noteCodes }
  }

  // losers — mistake taxonomy
  let type = 'Failed momentum', code = 'failedMomentum', vars
  if (isReattack) [type, code] = ['Re-attack (avg down into red)', 'reattack']
  else if (long && ext != null && ext > 2) {
    [type, code, vars] = [`Chased extended (+${ext.toFixed(1)} ATR over 20EMA)`, 'chased', { ext: ext.toFixed(1) }]
  }
  else if (long && tech?.aboveSma50 === false && tech?.sma50Slope != null && tech.sma50Slope < -1) [type, code] = ['Knife-catch (below a falling 50SMA)', 'knife']
  else if (long && tech?.stack === 'bear') [type, code] = ['Bought a downtrend (bear MA stack)', 'boughtDown']
  const R = trade.rr ?? null
  if (R != null && R < -1.5) { notes.push(`blew through stop (${R.toFixed(1)}R)`); noteCodes.push({ k: 'blew', vars: { r: R.toFixed(1) } }) }
  return { type, code, vars, win: false, notes, noteCodes }
}
