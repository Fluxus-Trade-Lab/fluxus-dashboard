/**
 * Market State, minimal (Andy 2026-10-03): data first, no annotations.
 *
 * 「重点是数据呈现，少注解和状态判断」「做到极简」, modelled on TradersLab's
 * cards: a label, one big number, one line under it. Everything here is a
 * pure read of files the page already loads; the arithmetic that decides
 * anything (the light, the votes) stays in the pipeline.
 */
import msMain from '../../i18n/parts/msMain'

const num = (v) => (Number.isFinite(v) ? v : null)

/**
 * Default translator: the English column of the msMain dictionary, so callers
 * that pass no `t` (tests, older imports) get exactly the strings they always
 * got. The page passes the context's `t` for the reader's language.
 */
const fill = (s, vars) => (vars ? String(s).replace(/\{(\w+)\}/g, (m, k) => (vars[k] != null ? String(vars[k]) : m)) : s)

export function tEn(key, vars) {
  return fill(msMain.en[key] ?? key, vars)
}

/**
 * The context's `t`, made safe for {placeholders} everywhere: outside a
 * LanguageProvider (isolated component tests) useLanguage's fallback `t`
 * ignores vars. Filling twice is a no-op once the braces are gone.
 */
export const withVars = (t) => (key, vars) => fill(t(key, vars), vars)

/** The verdict word and the readings it is made of (Andy: 「DIM的这个状态太简单了…需要展现出来」). */
export function verdictParts(ml, t = tEn) {
  if (!ml) return null
  const leaders = ml.brightness?.leaders ?? []
  const hold = leaders.filter((l) => l.status === 'holding').length
  const env = ml.brightness?.breadth?.env ?? null
  return {
    verdict: ml.verdict ?? null,
    parts: [
      { key: 'spy', label: 'SPY', value: ml.spy?.light ?? null, detail: ml.spy ? `${ml.spy.checks_passed}/3` : null, good: ml.spy?.light === 'green' },
      { key: 'qqq', label: 'QQQ', value: ml.qqq?.light ?? null, detail: ml.qqq ? `${ml.qqq.checks_passed}/3` : null, good: ml.qqq?.light === 'green' },
      { key: 'leaders', label: t('ms.v.leaders'), value: leaders.length ? `${hold}/${leaders.length}` : null, detail: t('ms.v.above50'), good: leaders.length ? hold / leaders.length >= 0.6 : null },
      { key: 'breadth', label: t('ms.v.breadth'), value: env, detail: null, good: env === 'BULLISH' ? true : env === 'BEARISH' ? false : null },
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
export function breadthTiles(rows, t = tEn) {
  const r = rows ?? []
  const z = r.at(-1), y = r.at(-2)
  if (!z) return []
  const d = (k) => (num(z[k]) != null && num(y?.[k]) != null ? z[k] - y[k] : null)
  const net = num(z.advances) != null && num(z.declines) != null ? z.advances - z.declines : null
  const hli = num(z.high_low_index), rhp = num(z.record_high_pct)
  return [
    { key: 'adv', label: t('ms.tile.adv'), value: net, sub: net == null ? null : t('ms.tile.advSub', { up: z.advances.toLocaleString(), down: z.declines.toLocaleString() }), sign: net },
    // Standard reading (METRIC_SOURCES 2026-08-31): High-Low Index = 10-day
    // mean of NH/(NH+NL), common stocks. 50 is neutral.
    { key: 'hli', label: t('ms.tile.hli'), value: hli, sub: num(z.new_highs_common) == null ? null : `${t('ms.tile.hliSub', { h: z.new_highs_common, l: z.new_lows_common })}${rhp == null ? '' : t('ms.tile.hliToday', { v: Math.round(rhp) })}`, sign: hli == null ? null : hli - 50 },
    { key: 'p20', label: t('ms.tile.p20'), value: num(z.pct_above_20sma), unit: '%', delta: d('pct_above_20sma'), sign: num(z.pct_above_20sma) == null ? null : z.pct_above_20sma - 50 },
    { key: 'p200', label: t('ms.tile.p200'), value: num(z.pct_above_200sma), unit: '%', delta: d('pct_above_200sma'), sign: num(z.pct_above_200sma) == null ? null : z.pct_above_200sma - 50 },
    { key: 'mco', label: t('ms.tile.mco'), value: num(z.mcclellan_osc_ndx), delta: d('mcclellan_osc_ndx'), sign: num(z.mcclellan_osc_ndx) },
    { key: 'up4', label: t('ms.tile.up4'), value: num(z.up_4pct_stockbee) == null ? null : `${z.up_4pct_stockbee} / ${z.down_4pct_stockbee}`, sub: num(z.t2108) == null ? null : `T2108 ${Math.round(z.t2108)}%`, sign: num(z.up_4pct_stockbee) == null ? null : z.up_4pct_stockbee - z.down_4pct_stockbee },
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

/**
 * The recap's cross-asset sentences for this session (Andy 2026-10-03:
 * 「选B，搬复盘原句，先不做门禁。」). Shown only when the recap is for the same
 * session as the data — between the 08:30 data and the 10:30 recap the page
 * would otherwise pair today's numbers with yesterday's words.
 */
export function recapNotes(doc, asof, lang = 'en') {
  if (!doc || !asof || doc.asof !== asof) return []
  const n = doc.notes ?? {}
  return (n[lang] ?? n.en ?? []).filter((x) => x?.text)
}

/** Split the recap's <b>lead</b> markup into plain parts — no HTML injection. */
export function boldParts(text) {
  return String(text ?? '').split(/(<b>.*?<\/b>)/).filter(Boolean)
    .map((s) => (s.startsWith('<b>') ? { b: true, t: s.slice(3, -4) } : { b: false, t: s }))
}
