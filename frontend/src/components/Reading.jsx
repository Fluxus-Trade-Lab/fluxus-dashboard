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
 * And it is computed, never typed. A sentence written by hand is a sentence that
 * goes stale, which is exactly how the Briefing page ended up serving March in
 * August. Every clause here is produced by a rule that points at a count, and
 * when no rule fires the component renders nothing at all. An empty narrator is
 * honest; a generic one is filler.
 */
export default function Reading({ text }) {
  if (!text) return null
  return (
    <div className="pl-4 border-l-2 border-[var(--color-text)] max-w-[68ch] mb-4">
      <p className="text-[17px] leading-[1.45] text-[var(--color-text)] m-0">{text}</p>
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
 * Themes. Level and acceleration disagreeing is the whole reason the page has
 * two columns, so the line reports that disagreement when it exists.
 */
export function readThemes(rows) {
  const ok = (rows ?? []).filter(
    (r) => r.excess_3m != null && r.rs_accel != null,
  )
  if (ok.length < 8) return null

  const top = [...ok].sort((a, b) => b.excess_3m - a.excess_3m).slice(0, 4)
  const fading = top.filter((r) => r.rs_accel < 0).length
  const turning = ok.filter((r) => r.excess_3m < 0 && r.rs_accel > 0).length

  if (fading === top.length && turning >= 3) {
    return `Every one of the four strongest themes is decelerating, while ${
      plural(turning, 'theme is', 'themes are')} accelerating from behind.`
  }
  if (fading === top.length) {
    return 'Every one of the four strongest themes is decelerating.'
  }
  if (turning >= 5) {
    return `${plural(turning, 'theme is', 'themes are')} accelerating while still behind the benchmark.`
  }
  return null
}

/**
 * Screener. The list ranks by what has already stacked, so the honest reading is
 * about concentration, not about promise.
 */
export function readScreener(data) {
  const rows = data?.rows ?? []
  if (rows.length < 5) return null
  const QUALITY = new Set(['episodic_pivot', 'vcp', 'momentum_97'])
  const withQuality = rows.filter(
    (r) => (r.screeners ?? []).some((s) => QUALITY.has(s.name)),
  ).length
  if (withQuality === rows.length) {
    return `All ${rows.length} names here cleared at least one quality screen — which is what put them here, not what makes them work.`
  }
  const share = Math.round((withQuality / rows.length) * 100)
  if (share <= 60) {
    return `${withQuality} of ${rows.length} names cleared a quality screen; the rest are here on participation alone.`
  }
  return null
}
