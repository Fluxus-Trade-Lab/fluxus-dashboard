/**
 * Market State, minimal (Andy 2026-10-03): data first, no annotations.
 *
 * 「重点是数据呈现，少注解和状态判断」「做到极简」, modelled on TradersLab's
 * cards: a label, one big number, one line under it. Everything here is a
 * pure read of files the page already loads; the arithmetic that decides
 * anything (the light, the votes) stays in the pipeline.
 */
const num = (v) => (Number.isFinite(v) ? v : null)

/** The verdict word and the readings it is made of (Andy: 「DIM的这个状态太简单了…需要展现出来」). */
export function verdictParts(ml) {
  if (!ml) return null
  const leaders = ml.brightness?.leaders ?? []
  const hold = leaders.filter((l) => l.status === 'holding').length
  const env = ml.brightness?.breadth?.env ?? null
  return {
    verdict: ml.verdict ?? null,
    parts: [
      { key: 'spy', label: 'SPY', value: ml.spy?.light ?? null, detail: ml.spy ? `${ml.spy.checks_passed}/3` : null, good: ml.spy?.light === 'green' },
      { key: 'qqq', label: 'QQQ', value: ml.qqq?.light ?? null, detail: ml.qqq ? `${ml.qqq.checks_passed}/3` : null, good: ml.qqq?.light === 'green' },
      { key: 'leaders', label: 'Leaders', value: leaders.length ? `${hold}/${leaders.length}` : null, detail: 'above 50-day', good: leaders.length ? hold / leaders.length >= 0.6 : null },
      { key: 'breadth', label: 'Breadth', value: env, detail: null, good: env === 'BULLISH' ? true : env === 'BEARISH' ? false : null },
    ],
  }
}

/** Four index cards from etf_data, the light where the pipeline has one. */
export function indexCards(etfs, ml) {
  const by = Object.fromEntries((etfs ?? []).map((e) => [e.ticker, e]))
  // Andy 2026-10-03: 「index里面需要加QQQE和DIA」
  return ['SPY', 'QQQ', 'QQQE', 'DIA', 'IWM', 'RSP'].filter((t) => by[t]).map((t) => {
    const e = by[t]
    const light = ml?.[t.toLowerCase()]?.light ?? null
    return {
      ticker: t, close: num(e.close), chg: num(e.change_pct), w1: num(e.perf_1w),
      fromHigh: num(e.high_52w_dist), aboveSma50: num(e.dist_sma50_atr) == null ? null : e.dist_sma50_atr > 0, light,
    }
  })
}

/** The six breadth tiles. Each: label, value, sub-line, sign for the edge colour. */
export function breadthTiles(rows) {
  const r = rows ?? []
  const t = r.at(-1), y = r.at(-2)
  if (!t) return []
  const d = (k) => (num(t[k]) != null && num(y?.[k]) != null ? t[k] - y[k] : null)
  const net = num(t.advances) != null && num(t.declines) != null ? t.advances - t.declines : null
  const hli = num(t.high_low_index), rhp = num(t.record_high_pct)
  return [
    { key: 'adv', label: 'Net advances', value: net, sub: net == null ? null : `${t.advances.toLocaleString()} up · ${t.declines.toLocaleString()} down`, sign: net },
    // Standard reading (METRIC_SOURCES 2026-08-31): High-Low Index = 10-day
    // mean of NH/(NH+NL), common stocks. 50 is neutral.
    { key: 'hli', label: 'High-Low Index', value: hli, sub: num(t.new_highs_common) == null ? null : `${t.new_highs_common} highs · ${t.new_lows_common} lows${rhp == null ? '' : ` · today ${Math.round(rhp)}%`}`, sign: hli == null ? null : hli - 50 },
    { key: 'p20', label: 'Above 20-day', value: num(t.pct_above_20sma), unit: '%', delta: d('pct_above_20sma'), sign: num(t.pct_above_20sma) == null ? null : t.pct_above_20sma - 50 },
    { key: 'p200', label: 'Above 200-day', value: num(t.pct_above_200sma), unit: '%', delta: d('pct_above_200sma'), sign: num(t.pct_above_200sma) == null ? null : t.pct_above_200sma - 50 },
    { key: 'mco', label: 'McClellan · NDX', value: num(t.mcclellan_osc_ndx), delta: d('mcclellan_osc_ndx'), sign: num(t.mcclellan_osc_ndx) },
    { key: 'up4', label: 'Up 4% / down 4%', value: num(t.up_4pct_stockbee) == null ? null : `${t.up_4pct_stockbee} / ${t.down_4pct_stockbee}`, sub: num(t.t2108) == null ? null : `T2108 ${Math.round(t.t2108)}%`, sign: num(t.up_4pct_stockbee) == null ? null : t.up_4pct_stockbee - t.down_4pct_stockbee },
  ]
}

/** Cross-asset strip: VIX level plus five ETFs with their week against SPY. */
export function crossAsset(etfs, signals) {
  const by = Object.fromEntries((etfs ?? []).map((e) => [e.ticker, e]))
  const spyW = num(by.SPY?.perf_1w)
  const vix = num(signals?.['^VIX']?.close)
  const out = [{ ticker: 'VIX', last: vix, chg: null, w1: null, vsSpy: null }]
  for (const t of ['TLT', 'UUP', 'USO', 'GLD', 'IBIT']) {
    const e = by[t]
    if (!e) continue
    out.push({ ticker: t, last: num(e.close), chg: num(e.change_pct), w1: num(e.perf_1w), vsSpy: num(e.perf_1w) != null && spyW != null ? e.perf_1w - spyW : null })
  }
  return out
}
