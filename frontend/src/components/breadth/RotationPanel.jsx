import { useRotation } from '../../hooks/useRotation'
import StateRibbon from '../shared/StateRibbon'
import { useLanguage } from '../../i18n/LanguageContext'
import { dataName } from '../../i18n/names'

/**
 * Style rotation, sitting under the verdict and above the board.
 *
 * **Why here and not on Themes.** Placement follows the decision a reading
 * feeds, not what it resembles. These baskets are styles, so the question is
 * "is the market paying for risk" — the risk-budget question, the same one the
 * regime score answers from the other side. Themes answers "which one", a
 * different decision. Filed there, this panel would be read as a stock screen.
 *
 * **Why adjacent to the score specifically.** The two readings are usually in
 * tension and the tension is the information: today the board is Extended while
 * rotation says the turn is two weeks old and the month still disagrees. Apart,
 * a reader believes whichever they saw; together, "not yet a regime" has
 * something to contradict.
 *
 * The sentence is the product. The chart underneath is there so the sentence
 * can be checked, not so it can be skimmed instead.
 *
 * 2026-09-11: the three-cut table became one chart (fortnight solid, month
 * outline, both against a zero line — "do the horizons agree" is now a shape,
 * not two columns to compare), and the eleven baskets with their ten-week
 * ribbons were removed. Andy: 「11个主题百分比可以删除」 — Themes already
 * carries that board, and here it read as a stock screen.
 */

const pp = (v) => (v == null ? '—' : `${(v * 100 >= 0 ? '+' : '')}${(v * 100).toFixed(1)}pp`)

const PHASES = new Set(['established', 'turning', 'split'])

/** A cut's display name: the pipeline's label in English, the dictionary's in
 *  Chinese (keyed by the cut's stable key; an unknown key keeps the label). */
function cutLabel(c, lang, t) {
  if (lang !== 'zh') return c.label
  const k = `rot.cut.${c.key}`
  const z = t(k)
  return z === k ? c.label : z
}

/** Chinese verdict sentence, rebuilt from the same fields
 *  pipeline/rotation/engine.py::verdict composes the English one from. English
 *  keeps printing the pipeline's own `sentence` untouched. */
function zhSentence(v, cuts, t) {
  const word = (c) => t(`rot.word.${c}`)
  if (!v.of) return t('rot.v.none')
  if (v.call == null) return t('rot.v.split')
  let s = v.agree === v.of
    ? t('rot.v.leadAll', { word: word(v.call), n: v.of })
    : t('rot.v.leadSome', { agree: v.agree, of: v.of, word: word(v.call) })
  const sized = (cuts ?? []).filter((c) => c.vote === v.call && c.spread != null)
  if (sized.length) {
    const w = sized.reduce((a, b) => (Math.abs(b.spread) > Math.abs(a.spread) ? b : a))
    s += t('rot.v.widest', { cut: cutLabel(w, 'zh', t), pp: pp(w.spread) })
  }
  if (v.month_call === v.call) s += t('rot.v.tailRegime')
  else if (v.month_call == null) s += t('rot.v.tailNoMonth')
  else s += t('rot.v.tailMonthOther', { word: word(v.month_call), agree: v.month_agree, of: v.month_of })
  return s
}

/** '10–8w ago' / 'Last 2w' arrive as data; Chinese reads them through a template. */
function bucketLabel(l, lang, t) {
  if (lang !== 'zh' || typeof l !== 'string') return l
  let m = l.match(/^(\d+)–(\d+)w ago$/)
  if (m) return t('rot.bucketAgo', { a: m[1], b: m[2] })
  m = l.match(/^Last (\d+)w$/)
  if (m) return t('rot.bucketLast', { n: m[1] })
  return l
}

export default function RotationPanel() {
  const { rotation, loading, error } = useRotation()
  const { lang, t } = useLanguage()

  // A missing rotation.json costs this panel and nothing else. Silence would be
  // worse than absence: the page would look complete while a reading it claims
  // to carry was gone.
  if (loading) return null
  if (error || !rotation?.verdict) {
    return (
      <div className="bg-[var(--color-bg)] rounded-2xl p-4">
        <h3 className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] m-0">
          {t('rot.title')}
        </h3>
        <p className="mt-2 mb-0 text-[13px] text-[var(--color-text-muted)]">
          {t('rot.unavailable')}
        </p>
      </div>
    )
  }

  const { verdict: v, cuts, baskets, bucket_labels: rawLabels, state_windows: win } = rotation
  const labels = rawLabels?.map((l) => bucketLabel(l, lang, t))
  const windowNote = t('rot.windowNote',
    { level: win?.level_sessions ?? 63, near: win?.near_sessions ?? 21 })
  // Was a paragraph under the panel; now the chart's hover note — Andy 09-06:
  // no explanatory text on the card, method goes where the curious look.
  const caveat = t('rot.caveat')
  const sentence = lang === 'zh' ? zhSentence(v, cuts, t) : v.sentence

  return (
    <div className="bg-[var(--color-bg)] rounded-2xl p-4">
      <div className="flex items-baseline justify-between gap-3 mb-3">
        <h3 className="text-[11px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] m-0">
          {t('rot.title')}
        </h3>
        <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
          {t('rot.vsBench', { bench: rotation.benchmark, date: rotation.date })}
        </span>
      </div>

      {/* The one line. Everything below exists to let it be checked. */}
      {/* a whole sentence in the encoding colour was the loudest instance of
          the leak — the phase note under it carries the reading in words */}
      <p className="m-0 text-[13px] leading-snug font-medium text-[var(--color-text)]">
        {sentence}
      </p>
      {PHASES.has(v.phase) && (
        <p className="mt-1 mb-0 text-[11px] text-[var(--color-text-muted)]">
          {t(`rot.phase.${v.phase}`)}
        </p>
      )}

      <CutsChart cuts={cuts} caveat={caveat} lang={lang} t={t} />

      {/* Back in, 09-11 (Andy: 「如果是有内容被删除了, 那我希望被删除的内容先放在折叠页里面」)
          — this whole panel already lives in a fold, so the eleven baskets and
          their ten-week ribbons return under the chart, unchanged. */}
      {baskets?.length > 0 && (
        <div className="mt-5">
          <div className="grid grid-cols-[minmax(96px,auto)_1fr_auto] gap-x-3 gap-y-[6px] items-center">
            {baskets.map((b) => (
              <div key={b.ticker} className="contents">
                <span className="text-[11px] truncate" title={`${dataName(b.name, lang)} (${b.ticker})`}>
                  {dataName(b.name, lang)}
                </span>
                <StateRibbon steps={b.ribbon} labels={labels} windowNote={windowNote} />
                <span className={`text-[11px] font-mono tabular-nums w-[52px] text-right ${
                  b.side === 'risk_on' ? 'text-[var(--color-text-secondary)]'
                                       : 'text-[var(--color-text-muted)]'}`}>
                  {b.level == null ? '—' : `${(b.level * 100).toFixed(1)}%`}
                </span>
              </div>
            ))}
            <span />
            <span className="grid mt-1 text-[11px] font-mono text-[var(--color-text-muted)]"
                  style={{ gridTemplateColumns: `repeat(${labels?.length ?? 5}, minmax(0, 1fr))`, gap: '2px' }}>
              {labels?.map((l) => <span key={l} className="text-center">{l}</span>)}
            </span>
            <span />
          </div>
        </div>
      )}

      <p className="mt-4 pt-3 border-t border-[var(--color-border)] m-0
                    text-[11px] leading-relaxed text-[var(--color-text-muted)]">
        {caveat}{lang === 'zh' ? '' : ' '}{t('rot.ribbonFoot', { note: lang === 'zh' ? windowNote : windowNote.charAt(0).toLowerCase() + windowNote.slice(1) })}
      </p>
    </div>
  )
}

/* ── the three cuts, one chart ─────────────────────────────────────────── */

const CW = 760, CROW = 44, CL = 230, CR = 60, CTOP = 24

function CutsChart({ cuts, caveat, lang, t }) {
  if (!cuts?.length) return null
  const vals = cuts.flatMap((c) => [c.spread, c.month_spread]).filter(Number.isFinite).map((v) => v * 100)
  const lo = Math.min(-1, Math.floor(Math.min(...vals)))
  const hi = Math.max(1, Math.ceil(Math.max(...vals)))
  const x = (v) => CL + ((v - lo) / (hi - lo)) * (CW - CL - CR)
  const H = CTOP + cuts.length * CROW + 20
  const ticks = []
  for (let v = lo; v <= hi; v += 1) ticks.push(v)
  const bar = (v, y, solid, key) => {
    if (!Number.isFinite(v)) return null
    const a = x(Math.min(0, v)), b = x(Math.max(0, v))
    return (
      <g key={key}>
        <rect x={a} y={y} width={Math.max(1, b - a)} height="9" rx="2"
              fill={solid ? 'var(--color-took)' : 'none'} stroke="var(--color-took)" strokeWidth="1.2" />
        <text x={v >= 0 ? b + 6 : a - 6} y={y + 8} fontSize="11" textAnchor={v >= 0 ? 'start' : 'end'}
              style={{ fill: 'var(--color-text-secondary)' }}>{v > 0 ? '+' : ''}{v.toFixed(1)}</text>
      </g>
    )
  }
  return (
    <div className="mt-4" title={caveat}>
      <svg viewBox={`0 0 ${CW} ${H}`} className="w-full h-auto block" role="img"
           aria-label={t('rot.chartAria')}>
        {ticks.map((v) => (
          <g key={v}>
            <line x1={x(v)} x2={x(v)} y1={CTOP - 8} y2={H - 18}
                  stroke={v === 0 ? 'var(--color-text)' : 'var(--color-border-light)'} strokeWidth={v === 0 ? 1.2 : 1} />
            <text x={x(v)} y={H - 4} fontSize="11" textAnchor="middle"
                  style={{ fill: 'var(--color-text-muted)' }}>{v > 0 ? `+${v}` : v}pp</text>
          </g>
        ))}
        <text x={x(lo)} y={CTOP - 12} fontSize="11" style={{ fill: 'var(--color-text-muted)' }}>{t('rot.axisOff')}</text>
        <text x={x(hi)} y={CTOP - 12} fontSize="11" textAnchor="end" style={{ fill: 'var(--color-text-muted)' }}>{t('rot.axisOn')}</text>
        {cuts.map((c, i) => {
          const y = CTOP + i * CROW
          const label = cutLabel(c, lang, t)
          return (
            <g key={c.key}>
              <title>{t('rot.barTitle', { label, f: pp(c.spread), m: pp(c.month_spread), s: pp(c.delta) })}</title>
              <text x="0" y={y + 12} fontSize="13" fontWeight="600" style={{ fill: 'var(--color-text)' }}>{label}</text>
              <text x="0" y={y + 28} fontSize="11" style={{ fill: 'var(--color-text-muted)' }}>
                {t('rot.cutSub', { long: c.long.join('/'), short: c.short.join('/'), speed: pp(c.delta) })}
              </text>
              {bar(c.spread * 100, y + 2, true, 'f')}
              {bar(c.month_spread * 100, y + 15, false, 'm')}
            </g>
          )
        })}
      </svg>
      <div className="flex gap-4 mt-1 text-[11px] text-[var(--color-text-muted)]">
        <span><i className="inline-block w-3 h-[8px] mr-1.5 align-[0px] rounded-sm bg-[var(--color-took)]" />{t('rot.fortnight')}</span>
        <span><i className="inline-block w-3 h-[8px] mr-1.5 align-[0px] rounded-sm border border-[var(--color-took)]" />{t('rot.month')}</span>
      </div>
    </div>
  )
}
