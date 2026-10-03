import { voteFrac, ON_THE_LINE } from './breadth/VoteGlyphs'
import { useLanguage } from '../i18n/LanguageContext'
import { dataName } from '../i18n/names'
import dashboard from '../i18n/parts/dashboard'

/**
 * Default translator for the read*() sentences: the English column of the
 * dashboard dictionary, so a caller that passes nothing gets exactly the
 * English it always got. Pass the page's `t` (and `lang`) for Chinese.
 */
const enT = (key, vars) => {
  const str = dashboard.en[key] ?? key
  return vars ? String(str).replace(/\{(\w+)\}/g, (m, k) => (vars[k] != null ? String(vars[k]) : m)) : str
}
/**
 * The narrator's line — one per page, at reading size, above the numbers.
 *
 * Design: DESIGN.md §3 (解读语域 · solid left rule) and the exploration
 * Fluxus_Brand/visual/explorations/2026-08-08/today_material.html
 *
 * Two rules it exists to hold.
 *
 * It observes, it does not instruct. "The leaders stopped leading" is a reading.
 * "Trade full size" is an instruction, it needs an R and a ceiling, and those
 * are personal — so it lives behind an account, not on a market page.
 *
 * MEASURE, 2026-08-18 (Andy: 最多两行，可以向右多延伸一些). It ran at 68ch —
 * a body measure — and the Screener's line, which names every theme in the
 * filter, took three lines and pushed the page down. It is one sentence at
 * display size, not a paragraph, so the 65–75ch reading-comfort rule is the
 * wrong rule for it: nobody tracks back to a second line here more than once.
 *
 * It is widened rather than CLAMPED. `line-clamp-2` would have held the two
 * lines by hiding the end of a computed sentence, and a reading whose last
 * clause is cut is the same failure as a silently truncated list. Width is the
 * honest lever; if a sentence is ever long enough to need a third line it gets
 * one, whole.
 *
 * And it is computed, never typed. A sentence written by hand is a sentence that
 * goes stale, which is exactly how the Briefing page ended up serving March in
 * August. Every clause here is produced by a rule that points at a count, and
 * when no rule fires the component renders nothing at all. An empty narrator is
 * honest; a generic one is filler.
 */
/**
 * THE NAMES IN THE SENTENCE ARE CLICKABLE, where the page has somewhere to
 * send them (Andy, 2026-08-18). The reading ends "Front of the board: QLYS,
 * OKTA, TENB" — three names it just argued for, and until now the only way to
 * act on them was to go and find them again in the table underneath.
 *
 * MATCHED AGAINST A KNOWN LIST, NEVER GUESSED. A regex for capitalised runs
 * would light up SPY, RS, All, States and every theme name in the line. The
 * caller passes the tickers it actually has, so a token becomes a control only
 * when it is one — and on pages with no chart to send it to, no handler is
 * passed and the sentence renders exactly as before.
 */
function linkify(text, tickers, onTicker, t = enT) {
  if (!onTicker || !tickers?.length) return text
  // longest first, so a symbol that prefixes another cannot swallow it
  const alts = [...new Set(tickers)].sort((a, b) => b.length - a.length)
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const re = new RegExp(`\\b(${alts.join('|')})\\b`, 'g')
  const out = []
  let last = 0
  for (const m of text.matchAll(re)) {
    if (m.index > last) out.push(text.slice(last, m.index))
    out.push(
      <button key={`${m[1]}-${m.index}`} type="button" onClick={() => onTicker(m[1])}
              title={t('db.read.chart', { t: m[1] })}
              className="bg-transparent border-none p-0 font-inherit text-[length:inherit]
                         cursor-pointer text-[var(--color-accent)] underline
                         decoration-dotted underline-offset-[3px]
                         hover:decoration-solid">
        {m[1]}
      </button>,
    )
    last = m.index + m[1].length
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

export default function Reading({ text, tickers, onTicker }) {
  const { t } = useLanguage()
  if (!text) return null
  return (
    <div className="pl-4 border-l-2 border-[var(--color-text)] max-w-[108ch] mb-4">
      <p className="text-[17px] leading-[1.45] text-[var(--color-text)] m-0">
        {linkify(text, tickers, onTicker, t)}
      </p>
    </div>
  )
}

/**
 * Market State. The interesting fact most days is not the score — it is how
 * much of the score is resting on votes that have nearly crossed.
 */
export function readMarketState(verdict, t = enT) {
  if (!verdict?.votes) return null
  const side = verdict.score >= 0 ? 'bull' : 'bear'
  const agree = Object.values(verdict.votes).filter((v) => v === side).length
  const detail = verdict.vote_detail ?? []

  const onLine = detail.filter(
    (d) => d.measurable && Math.abs(voteFrac(d)) < ON_THE_LINE,
  ).length
  const uncounted = detail.filter((d) => !d.measurable && d.key !== 'bench_trend').length

  if (!detail.length) return null
  const lead = t(`db.read.says${side === 'bull' ? 'Yes' : 'No'}${agree === 1 ? 'One' : 'Many'}`, { n: agree })

  if (onLine >= 2) {
    return t('db.read.onLineMany', { lead, n: onLine })
  }
  if (uncounted >= 1) {
    return t('db.read.uncounted', { lead, n: uncounted })
  }
  return t('db.read.calm', { lead })
}

/**
 * Themes.
 *
 * It follows the WINDOW. Until 2026-08-16 it did not — it read excess_3m no
 * matter which of 1W / 1M / 3M was selected, so a reader looking at the week
 * got a sentence about the quarter. Andy caught it the obvious way: Memory &
 * Storage was up 15.6% on the week, plainly the standout on screen, and the
 * line was talking about something else entirely.
 *
 * Two clauses, and the second only when it has something to say.
 *
 * The first names who leads the window the reader chose. That is a restatement
 * of the top bar, and it earns its place anyway: it is the anchor the rest of
 * the sentence hangs off, and a narrator that never says the obvious thing
 * reads as evasive.
 *
 * The second is the part the charts cannot say at a glance — the disagreement
 * between where a theme IS and where it is GOING. Either the leader's own pace
 * is falling, or there are themes still behind the benchmark that are speeding
 * up. Named, not counted: "26 themes are accelerating from behind" is a number
 * nobody can act on; the two furthest along are two places to look.
 *
 * Slope comes from `rs_accel_rate`, never `rs_accel`. The engine ships both and
 * only the first is a slope — the second scores a steady outperformer negative
 * on purpose, because it is the validated gate behind the four states.
 */
export function readThemes(rows, winKey = '3M', t = enT, lang = 'en') {
  const ok = (rows ?? []).filter(
    (r) => Number.isFinite(r._value) && r.rs_accel_rate != null,
  )
  if (ok.length < 8) return null

  const [leader] = [...ok].sort((a, b) => b._value - a._value)
  if (!leader) return null
  const window = t(winKey === '1W' ? 'db.read.week'
    : winKey === '1M' ? 'db.read.month' : 'db.read.quarter')
  const pct = `${leader._value > 0 ? '+' : ''}${(leader._value * 100).toFixed(1)}%`
  const lead = t('db.read.leads', { name: dataName(leader.group, lang), window, pct })

  const turning = ok.filter((r) => r._value < 0 && r.rs_accel_rate > 0)
    .sort((a, b) => b.rs_accel_rate - a.rs_accel_rate)
  const names = turning.slice(0, 2).map((r) => dataName(r.group, lang)).join(t('db.read.and'))

  if (turning.length >= 5) {
    return t('db.read.accel', { lead, names })
  }
  if (leader.rs_accel_rate < 0) {
    return t('db.read.fading', { lead })
  }
  return t('db.read.speeding', { lead })
}

/**
 * Screener. The list ranks by what has already stacked, so the honest reading is
 * about concentration, not about promise.
 */
export function readScreener(data, t = enT, lang = 'en') {
  const rows = data?.rows ?? []
  if (rows.length < 5) return null
  // Three things a reader trades on: where the heat concentrates, how much of
  // it is fresh, and who leads. (An earlier version printed an epistemology
  // lesson here; Andy's rule 2026-08-11 — page copy is judgment and execution
  // only.)
  const bySector = new Map()
  for (const r of rows) if (r.sector) bySector.set(r.sector, (bySector.get(r.sector) ?? 0) + 1)
  const top = [...bySector.entries()].sort((a, b) => b[1] - a[1])[0]
  const asOf = data.as_of ? new Date(data.as_of) : null
  const fresh = asOf ? rows.filter((r) =>
    r.first_seen && (asOf - new Date(r.first_seen)) / 86400000 <= 7).length : 0
  const lead = rows[0]
  const parts = []
  if (top && top[1] / rows.length >= 0.25) parts.push(t('db.read.carries', { sector: dataName(top[0], lang), n: top[1], total: rows.length }))
  if (fresh) parts.push(t('db.read.fresh', { n: fresh }))
  if (lead?.score != null) parts.push(t('db.read.leadAt', { ticker: lead.ticker, score: lead.score.toFixed(1) }))
  return parts.length ? parts.join(' · ') + t('db.read.end') : null
}
