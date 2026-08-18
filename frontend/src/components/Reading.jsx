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
function linkify(text, tickers, onTicker) {
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
              title={`chart ${m[1]}`}
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
  if (!text) return null
  return (
    <div className="pl-4 border-l-2 border-[var(--color-text)] max-w-[108ch] mb-4">
      <p className="text-[17px] leading-[1.45] text-[var(--color-text)] m-0">
        {linkify(text, tickers, onTicker)}
      </p>
    </div>
  )
}

const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`

/** Below this share of its own range, a vote is sitting on its line. */
const ON_LINE = 0.08
const RANGE = {
  ratio_5d: 1.5, ratio_10d: 1.5, thrust: 300, qtr_spread: 400,
  spread_13_34: 400, nh_nl: 200, mcclellan: 70, pct200: 20,
  t2108_zone: 20, spy_danger: 5, qqq_danger: 5, bench_trend: 1,
}

/**
 * Market State. The interesting fact most days is not the score — it is how
 * much of the score is resting on votes that have nearly crossed.
 */
export function readMarketState(verdict) {
  if (!verdict?.votes) return null
  const side = verdict.score >= 0 ? 'bull' : 'bear'
  const agree = Object.values(verdict.votes).filter((v) => v === side).length
  const detail = verdict.vote_detail ?? []

  const onLine = detail.filter(
    (d) => d.measurable && Math.abs(d.margin / (RANGE[d.key] ?? 1)) < ON_LINE,
  ).length
  const uncounted = detail.filter((d) => !d.measurable && d.key !== 'bench_trend').length

  if (!detail.length) return null
  const lead = `${plural(agree, 'signal says', 'signals say')} ${side === 'bull' ? 'yes' : 'no'}.`

  if (onLine >= 2) {
    return `${lead} ${plural(onLine, 'of them is', 'of them are')} sitting on ${
      onLine === 1 ? 'its' : 'their'} own line.`
  }
  if (uncounted >= 1) {
    return `${lead} ${plural(uncounted, 'could', 'could')} not be counted today — absence, not calm.`
  }
  return `${lead} None of them is close to turning.`
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
export function readThemes(rows, winKey = '3M') {
  const ok = (rows ?? []).filter(
    (r) => Number.isFinite(r._value) && r.rs_accel_rate != null,
  )
  if (ok.length < 8) return null

  const [leader] = [...ok].sort((a, b) => b._value - a._value)
  if (!leader) return null
  const window = winKey === '1W' ? 'the week'
    : winKey === '1M' ? 'the month' : 'the quarter'
  const pct = `${leader._value > 0 ? '+' : ''}${(leader._value * 100).toFixed(1)}%`
  const lead = `${leader.group} leads ${window} at ${pct}`

  const turning = ok.filter((r) => r._value < 0 && r.rs_accel_rate > 0)
    .sort((a, b) => b.rs_accel_rate - a.rs_accel_rate)
  const names = turning.slice(0, 2).map((r) => r.group).join(' and ')

  if (turning.length >= 5) {
    return `${lead}, while ${names} accelerate from behind it.`
  }
  if (leader.rs_accel_rate < 0) {
    return `${lead}, but its pace is already falling.`
  }
  return `${lead}, and it is still speeding up.`
}

/**
 * Screener. The list ranks by what has already stacked, so the honest reading is
 * about concentration, not about promise.
 */
export function readScreener(data) {
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
  if (top && top[1] / rows.length >= 0.25) parts.push(`${top[0]} carries ${top[1]} of ${rows.length} names`)
  if (fresh) parts.push(`${fresh} arrived within the last week`)
  if (lead?.score != null) parts.push(`${lead.ticker} leads at ${lead.score.toFixed(1)}`)
  return parts.length ? parts.join(' · ') + '.' : null
}
