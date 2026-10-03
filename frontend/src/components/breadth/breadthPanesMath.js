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

import { tEn } from './marketStateMinMath'

export const Z_WIN = 252
export const Z_MIN_SESSIONS = 60
export const RECENT = 15
export const AFTER = 20

const num = (v) => (Number.isFinite(v) ? v : null)

/**
 * The indicators the panes can show, each over the pool columns it has.
 * `label` / `primary` / extra `label` / `note` are the English text; the
 * reader's language comes from the msMain keys `ms.ind.<key>.label|primary|note`
 * and `ms.ind.<key>.extra.<extraKey>` (see indicatorText).
 */
export const INDICATORS = {
  // Common stocks only (SPAC / ETF / closed-end fund / preferred excluded) --
  // the standard pool, and the one the engine votes on and the morning read
  // prints. Until 2026-10-03 this pane drew the older SPAC-inclusive count and
  // the two disagreed in sign on 2026-10-02 (old 44 − 31 = +13, common
  // 7 − 27 = −20), so the page said "more highs" here and "more lows" above.
  // Andy 2026-10-03: 「该切换的应该更改」. No fallback to the old count: a
  // series that splices two pools would draw a jump that is not in the market.
  nhnl: { label: '52-week highs − lows', unit: 'names', zero: true,
    pools: { all: (r) => (num(r.new_highs_common) != null && num(r.new_lows_common) != null ? r.new_highs_common - r.new_lows_common : null) },
    note: 'common stocks only (SPAC, ETF, closed-end fund, preferred excluded); this series starts 2026-08-28 — the older SPAC-inclusive count is no longer charted' },
  // Andy 2026-10-03: 「应该above 20-DAY, ABOVE 50-DAY ABOVE-200 DAY都放在market state的图里面」.
  // One pane, three lines; the 20-day is the primary series (oversold cut and
  // σ read it), the 50 and 200 ride along as overlays.
  kma: { label: '% above 20 / 50 / 200-day', primary: '% above 20-day', unit: '%', zero: false, range: [0, 100], lines: [50],
    pools: { all: (r) => num(r.pct_above_20sma), sp500: (r) => num(r.pct_above_20sma_sp500) },
    extra: [
      { key: 'p50', label: '50-day', pools: { all: (r) => num(r.pct_above_50sma), sp500: (r) => num(r.pct_above_50sma_sp500) } },
      { key: 'p200', label: '200-day', pools: { all: (r) => num(r.pct_above_200sma), sp500: (r) => num(r.pct_above_200sma_sp500) } },
    ],
    note: 'share of stocks above each moving average' },
  // Andy 2026-10-03 选 A: the Advanced fold's separate NDX oscillator chart
  // came off the page, so the NDX line rides here as an overlay (from 09-23).
  mco: { label: 'McClellan oscillator', primary: 'All market', unit: '', zero: true,
    pools: { all: (r) => num(r.mcclellan_osc) },
    extra: [{ key: 'ndx', label: 'NDX', pools: { all: (r) => num(r.mcclellan_osc_ndx) } }],
    note: 'all-market pool; the Nasdaq-100 line starts 2026-09-23' },
  // The three series below lived only as separate charts in Advanced breadth
  // until 2026-10-03 (Andy 选 A: 「信息一条不少」, the duplicate charts went).
  msi: { label: 'McClellan summation (NDX)', primary: 'Summation', unit: '', zero: true,
    pools: { all: (r) => num(r.mcclellan_summation_ndx) },
    // its 10-day average (mcclellan_summation_ndx_ma10) is shipped all-null
    // as of 2026-10-02, so it is not drawn — a legend for a missing line misleads
    note: 'Nasdaq-100 summation index, from 2026-09-23' },
  // Stockbee's own ratio is the one that votes; the older point-to-point count
  // rides dashed so the history does not vanish — two lines, never spliced.
  ratio: { label: 'Up/down ratio · 5 / 10-day (Stockbee)', primary: '5-day', unit: '', zero: false, lines: [1],
    pools: { all: (r) => num(r.ratio_5d_stockbee) },
    extra: [
      { key: 'r10', label: '10-day', pools: { all: (r) => num(r.ratio_10d_stockbee) } },
      { key: 'old5', label: '5-day, old count', dash: true, pools: { all: (r) => num(r.ratio_5d) } },
    ],
    note: 'Stockbee ratios from 2026-09-11; the older count dashed' },
  q25: { label: 'Quarterly ±25% spread (Stockbee)', primary: 'Stockbee', unit: 'names', zero: true,
    pools: { all: (r) => (num(r.up_25pct_qtr_stockbee) != null && num(r.down_25pct_qtr_stockbee) != null ? r.up_25pct_qtr_stockbee - r.down_25pct_qtr_stockbee : null) },
    extra: [{ key: 'old', label: 'old count', dash: true, pools: { all: (r) => (num(r.up_25pct_qtr) != null && num(r.down_25pct_qtr) != null ? r.up_25pct_qtr - r.down_25pct_qtr : null) } }],
    note: 'stocks up 25%+ in a quarter minus those down 25%+; the older count dashed' },
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

/** Interface text for one indicator in the reader's language (t from useLanguage). */
export function indicatorText(key, t = tEn) {
  const k = INDICATORS[key] ? key : 'nhnl'
  const ind = INDICATORS[k]
  const label = t(`ms.ind.${k}.label`)
  return {
    label,
    primary: ind.primary ? t(`ms.ind.${k}.primary`) : label,
    note: t(`ms.ind.${k}.note`),
    extra: Object.fromEntries((ind.extra ?? []).map((e) => [e.key, t(`ms.ind.${k}.extra.${e.key}`)])),
    unit: ind.unit === 'names' ? t('ms.unit.names') : ind.unit,
  }
}

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
export function buildPanes(rows, { indicator = 'nhnl', pool = 'all', scale = 'abs', window = 250, pct = 0.1, t = tEn } = {}) {
  const ind = INDICATORS[indicator] ?? INDICATORS.nhnl
  const txt = indicatorText(indicator, t)
  const all = rows ?? []
  const readAll = ind.pools.all
  const readPool = ind.pools[pool]
  let poolNote = ''
  let read = readAll
  if (pool !== 'all') {
    if (readPool) read = readPool
    else poolNote = t('ms.pane.noPoolSeries', { label: txt.label, pool: POOLS.find((p) => p.key === pool) ? t(`ms.pool.${pool}`) : pool })
  }
  const rawFull = all.map((r) => read(r))
  const zFull = scale === 'z' ? zscore(rawFull).map((v) => (v == null ? null : softClip(v))) : rawFull
  const s = Math.max(0, all.length - window)
  const dates = all.slice(s).map((r) => r.date)
  const index = all.slice(s).map((r) => num(r.spx_close))
  const value = zFull.slice(s)
  // overlays (kma): absolute ruler only, same pool as the primary when it has one
  const extras = scale === 'z' ? [] : (ind.extra ?? []).map((e) => {
    const rd = (pool !== 'all' && e.pools[pool]) || e.pools.all
    return { key: e.key, label: e.label, dash: e.dash, values: all.slice(s).map((r) => rd(r)) }
  })
  const raw = rawFull.slice(s)
  const finite = value.filter(Number.isFinite)
  let threshold = null
  if (finite.length < Z_MIN_SESSIONS) poolNote += `${poolNote ? ' ' : ''}${t('ms.pane.tooShort', { n: finite.length, min: Z_MIN_SESSIONS })}`
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
    indicator: ind, text: txt, dates, index, value, raw, extras, threshold, bands, episodes,
    recentFrom: Math.max(0, value.length - RECENT),
    poolNote,
    rule: scale === 'z'
      ? t('ms.pane.ruleZ', { win: Z_WIN, th: String(threshold) })
      : t('ms.pane.ruleAbs', { pct: Math.round(pct * 100), after: AFTER }),
  }
}
