/**
 * The post-mortem narrative, in the reader's language.
 *
 * The pipeline writes `narrative` in English only
 * (pipeline/portfolio/trade_postmortem.py `_generate_narrative`). Every number
 * in it is also in the same file as a field, so for any other language the
 * three sentences are rebuilt here from those fields — same branches, same
 * rounding, one translated template per clause. When the file ever carries
 * `narrative_<lang>` that wins; English keeps the pipeline's own sentence
 * untouched.
 *
 * `t` is the page's translator; `word` resolves the setup / lesson labels.
 */
const f2 = (v) => Number(v).toFixed(2)
const signed2 = (v) => `${v >= 0 ? '+' : ''}${f2(v)}`

export function narrativeFor(data, lang, t, word) {
  if (!data) return ''
  const twin = data[`narrative_${lang}`]
  if (twin != null) return twin
  if (lang === 'en' || !data.trade) return data.narrative

  const tr = data.trade
  const snap = data.entry_snapshot || {}
  const a = data.path_analytics || {}
  const initial = tr.initial_stop
  const hasR = initial != null
  const trailed = hasR && tr.stop_price != null && Math.abs(tr.stop_price - initial) > 0.01

  // Sentence 1 — entry context.
  const stop = !hasR ? t('jn.nar.noStop')
    : trailed ? t('jn.nar.stopTrailed', { s: f2(initial), c: f2(tr.stop_price) })
      : t('jn.nar.stop', { s: f2(initial) })
  const entry = t('jn.nar.entry', {
    tk: tr.ticker,
    dir: word(`jn.dir.${tr.direction === 'long' ? 'long' : 'short'}`, tr.direction),
    date: String(tr.entry_date).slice(0, 10),
    px: f2(tr.entry_price),
    stop,
  })
  const oneR = hasR && tr.r_pct_of_entry != null
    ? t('jn.nar.oneR', { rps: f2(Math.abs(tr.entry_price - initial)), pct: Number(tr.r_pct_of_entry).toFixed(1) })
    : t('jn.nar.noOneR')
  const s1 = t('jn.nar.pair', { a: entry, b: oneR })

  // Sentence 2 — technical setup. Truthiness checks mirror the pipeline's.
  const { close: px, ma20, ma50, ma200, rsi14: rsi } = snap
  const pos = snap.position_in_52w_range_pct
  const atr = snap.atr14_pct
  const bits = []
  if (px && ma20) bits.push(t(px > ma20 ? 'jn.nar.above20' : 'jn.nar.below20', { v: f2(ma20) }))
  if (ma20 && ma50 && ma200) {
    bits.push(t(ma20 > ma50 && ma50 > ma200 ? 'jn.nar.golden'
      : ma20 < ma50 && ma50 < ma200 ? 'jn.nar.death' : 'jn.nar.mixed'))
  }
  if (rsi != null) bits.push(t('jn.nar.rsi', { v: Number(rsi).toFixed(0) }))
  if (pos != null) bits.push(t('jn.nar.pos', { v: Number(pos).toFixed(0) }))
  if (atr != null) bits.push(t('jn.nar.atr', { v: Number(atr).toFixed(1) }))
  const setup = word(`jn.setup.${data.setup_type}`, data.setup_type)
  const s2 = bits.length
    ? t('jn.nar.setupBits', { setup, bits: bits.join(t('jn.nar.sep')) })
    : t('jn.nar.setup', { setup })

  // Sentence 3 — outcome, or the open position's state.
  let s3
  if (tr.closed) {
    let outcome = ''
    if (a.realized_R != null) {
      outcome = t('jn.nar.realized', { r: signed2(a.realized_R) })
      if (a.optimal_R != null && a.optimal_R > 0) {
        outcome += t('jn.nar.peak', { opt: f2(a.optimal_R), date: a.optimal_exit_date })
        if (a.days_to_optimal != null) outcome += t('jn.nar.day', { d: a.days_to_optimal })
        if (a.capture_pct != null) outcome += t('jn.nar.captured', { c: Number(a.capture_pct).toFixed(0) })
      }
    }
    outcome += t('jn.nar.end')
    const lesson = t('jn.nar.lesson', { lesson: word(`rev.lesson.${data.lesson}`, data.lesson) })
    s3 = t('jn.nar.pair', { a: outcome, b: lesson })
  } else {
    s3 = a.mfe_R != null && a.mae_R != null
      ? t('jn.nar.open', { mfe: f2(a.mfe_R), mae: f2(a.mae_R) })
      : t('jn.nar.openBare')
  }

  return t('jn.nar.all', { s1, s2, s3 })
}
