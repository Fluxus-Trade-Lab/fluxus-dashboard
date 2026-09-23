/**
 * Arithmetic for the index-over-breadth panes (Andy 09-23, after his
 * TradingView "NASDAQ / net new highs" screenshot): one indicator under the
 * index on a shared time axis, read against its own history. Pure functions
 * over breadth_replay.json rows (or breadth.json history rows as a fallback).
 *
 * Two rulers, both ours where the source gives none:
 *   · absolute — the raw reading; "oversold" = the lowest `pct` of the window
 *   · σ — z-score against the prior Z_WIN sessions (Alex reads MCO/MCSI in σ
 *     units on TradersLab; his window is not published, so 252 is ours)
 * Everything self-made is named in `rule` so the page can print it.
 */

export const Z_WIN = 252
export const Z_MIN_SESSIONS = 60
export const RECENT = 15
export const AFTER = 20

const num = (v) => (Number.isFinite(v) ? v : null)

/** The indicators the panes can show, each over the pool columns it has. */
export const INDICATORS = {
  nhnl: { label: '52-week highs − lows', unit: 'names', zero: true,
    pools: { all: (r) => (num(r.new_highs) != null && num(r.new_lows) != null ? r.new_highs - r.new_lows : null) },
    note: 'raw counts (SPAC included) — the common-stock series starts 2026-08-28, too short to chart' },
  mco: { label: 'McClellan oscillator', unit: '', zero: true,
    pools: { all: (r) => num(r.mcclellan_osc) },
    note: 'all-market pool; the Nasdaq-100 version is pending (T-0923-03)' },
  p20: { label: '% above the 20-day', unit: '%', zero: false, lines: [50],
    pools: { all: (r) => num(r.pct_above_20sma), sp500: (r) => num(r.pct_above_20sma_sp500) },
    note: 'TradersLab reads its 21 EMA cousin at 25 oversold / 75 overbought' },
  t2108: { label: 'T2108 · % above the 40-day', unit: '%', zero: false, lines: [20, 50, 80],
    pools: { all: (r) => num(r.t2108), sp500: (r) => num(r.t2108_sp500) },
    note: 'Stockbee: under 20 oversold, over 80 overbought' },
  net4: { label: 'Up 4% − down 4% (Stockbee)', unit: 'names', zero: true,
    pools: { all: (r) => (num(r.up_4pct_stockbee) != null && num(r.down_4pct_stockbee) != null ? r.up_4pct_stockbee - r.down_4pct_stockbee
      : num(r.up_4pct) != null && num(r.down_4pct) != null ? r.up_4pct - r.down_4pct : null) },
    note: 'Stockbee three-leg count from 2026-09-04; the price-only count before that' },
  adv: { label: 'Net advances', unit: 'names', zero: true,
    pools: { all: (r) => num(r.net_advances) },
    note: 'the daily increment of the A/D line' },
}

export const POOLS = [
  { key: 'all', label: 'All market' },
  { key: 'sp500', label: 'S&P 500', note: 'members-only columns since 2026-09-10' },
  { key: 'ndx', label: 'Nasdaq-100', pending: 'T-0923-03' },
]

/** Rolling z-score: each point against the prior Z_WIN sessions (itself included). */
export function zscore(arr, win = Z_WIN, min = Z_MIN_SESSIONS) {
  const out = new Array(arr.length).fill(null)
  let buf = []
  for (let i = 0; i < arr.length; i += 1) {
    if (Number.isFinite(arr[i])) buf.push(arr[i])
    if (buf.length > win) buf = buf.slice(buf.length - win)
    if (!Number.isFinite(arr[i]) || buf.length < min) continue
    const m = buf.reduce((a, b) => a + b, 0) / buf.length
    const sd = Math.sqrt(buf.reduce((a, b) => a + (b - m) * (b - m), 0) / buf.length) || 1
    out[i] = (arr[i] - m) / sd
  }
  return out
}

/** Soft clip beyond ±3: inside is linear (the grid is true), outside compresses. */
export const softClip = (v, lim = 3) => (v > lim ? lim + (v - lim) / (1 + (v - lim)) : v < -lim ? -lim - (-lim - v) / (1 + (-lim - v)) : v)

/**
 * Build the two series for the panes.
 * @returns {{dates, index, value, raw, threshold, bands, recentFrom, rule, poolNote}}
 */
export function buildPanes(rows, { indicator = 'nhnl', pool = 'all', scale = 'abs', window = 250, pct = 0.1 } = {}) {
  const ind = INDICATORS[indicator] ?? INDICATORS.nhnl
  const all = rows ?? []
  const readAll = ind.pools.all
  const readPool = ind.pools[pool]
  let poolNote = ''
  let read = readAll
  if (pool !== 'all') {
    if (readPool) read = readPool
    else poolNote = `${ind.label} has no ${POOLS.find((p) => p.key === pool)?.label ?? pool} series yet — showing the all-market pool.`
  }
  const rawFull = all.map((r) => read(r))
  const zFull = scale === 'z' ? zscore(rawFull).map((v) => (v == null ? null : softClip(v))) : rawFull
  const s = Math.max(0, all.length - window)
  const dates = all.slice(s).map((r) => r.date)
  const index = all.slice(s).map((r) => num(r.spx_close))
  const value = zFull.slice(s)
  const raw = rawFull.slice(s)
  const finite = value.filter(Number.isFinite)
  let threshold = null
  if (finite.length < Z_MIN_SESSIONS) poolNote += `${poolNote ? ' ' : ''}Only ${finite.length} sessions in this series — no oversold cut until it has ${Z_MIN_SESSIONS}.`
  else if (scale === 'z') threshold = pct <= 0.1 ? -2 : -1
  else threshold = [...finite].sort((a, b) => a - b)[Math.floor(finite.length * pct)]
  // oversold runs; runs ≤3 sessions apart are one episode
  let bands = [], run = null
  value.forEach((v, j) => {
    if (Number.isFinite(v) && threshold != null && v <= threshold) { if (!run) run = [j, j]; else run[1] = j }
    else if (run) { bands.push(run); run = null }
  })
  if (run) bands.push(run)
  bands = bands.reduce((acc, r) => { const l = acc[acc.length - 1]; if (l && r[0] - l[1] <= 4) l[1] = r[1]; else acc.push([...r]); return acc }, [])
  const episodes = bands.map(([a, b]) => {
    let mi = a; for (let j = a; j <= b; j += 1) if (value[j] < value[mi]) mi = j
    const e = Math.min(value.length - 1, b + AFTER)
    const ret = e > b && index[e] != null && index[b] ? index[e] / index[b] - 1 : null
    return { from: dates[a], to: dates[b], days: b - a + 1, min: value[mi], minRaw: raw[mi], after: ret, partial: e - b < AFTER }
  })
  return {
    indicator: ind, dates, index, value, raw, threshold, bands, episodes,
    recentFrom: Math.max(0, value.length - RECENT),
    poolNote,
    rule: scale === 'z'
      ? `σ = z-score against the prior ${Z_WIN} sessions (our window; Alex does not publish his). Axis fixed at ±3σ, soft-clipped beyond. Oversold line at ${threshold}σ (Alex: −1σ alert, −2σ deep).`
      : `Oversold = the lowest ${Math.round(pct * 100)}% of the window shown (our cut); runs ≤3 sessions apart count as one episode; "after" = the index ${AFTER} sessions past the episode's end.`,
  }
}
