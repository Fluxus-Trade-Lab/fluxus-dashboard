/**
 * Which of the four stages to work on this period, and why.
 *
 * The head coach does not produce a fifth analysis. It ranks the four and
 * names one, because Andy is one person and can change one thing at a time —
 * telling him at once that he sizes big, trims early, chases, and stops tight
 * is the same as telling him nothing.
 *
 * The criterion is not invented. Every closed trade already carries what it
 * made and what was there to be made; the gap between them is what that stage
 * left on the table. Per trade, not in total, or the stage that simply sees
 * more trades always wins.
 *
 * Measured on the real book, 2026-08-17: holding leaks 5.7R a trade against
 * selection's 1.9R, on totals that are nearly equal (397.8R vs 361.8R). The
 * totals alone would have called it a tie.
 */

/** A trade's lesson names the stage it belongs to. Good execution leaks nothing. */
export const STAGE_OF_LESSON = {
  'Failed setup': 'select',
  'Choppy / no edge': 'select',
  'Premature trim': 'hold',
  'Stopped too tight': 'hold',
}

export const STAGES = [
  { key: 'select', label: '选', en: 'Selection', asks: '该不该进这一笔' },
  { key: 'size', label: '定量', en: 'Sizing', asks: '该下多大' },
  { key: 'hold', label: '持有', en: 'Holding', asks: '什么时候减 · 止损怎么移' },
  { key: 'stop', label: '收手', en: 'Stopping', asks: '亏到什么程度该停' },
]

/**
 * Tickers whose split-adjusted history is not on the same scale as the fills.
 * The pipeline flags these as "Insufficient data" from 2026-08-17, so this is
 * belt and braces for an index generated before that — one SOXS trade reported
 * a best exit of +4,827R and would own any ranking it appeared in.
 */
const MAX_PLAUSIBLE_OPTIMAL_R = 100

/** Per-stage leak. Returns rows sorted worst-per-trade first. */
export function stageLeaks(trades = []) {
  const acc = new Map()
  for (const t of trades) {
    if (!t?.closed) continue
    const stage = STAGE_OF_LESSON[t.lesson]
    if (!stage) continue
    const realized = t.realized_R
    const optimal = t.optimal_R
    if (typeof realized !== 'number' || typeof optimal !== 'number') continue
    if (Math.abs(optimal) > MAX_PLAUSIBLE_OPTIMAL_R) continue
    const row = acc.get(stage) || { stage, n: 0, leak: 0, realized: 0, lessons: {} }
    row.n += 1
    row.leak += Math.max(0, optimal - realized)
    row.realized += realized
    row.lessons[t.lesson] = (row.lessons[t.lesson] || 0) + 1
    acc.set(stage, row)
  }
  return [...acc.values()]
    .map((r) => ({ ...r, perTrade: r.n ? r.leak / r.n : 0 }))
    .sort((a, b) => b.perTrade - a.perTrade)
}

/** The largest lesson inside a stage — what to actually practise. */
function dominantLesson(row) {
  const [best] = Object.entries(row.lessons || {}).sort((a, b) => b[1] - a[1])
  return best ? { lesson: best[0], n: best[1] } : null
}

/**
 * One sentence, or null when there is not enough closed history to rank on.
 * Null is a reading — a page that always has a verdict is not measuring.
 */
export function headline(trades = [], minTrades = 20) {
  const rows = stageLeaks(trades)
  if (rows.length < 2) return null
  const total = rows.reduce((s, r) => s + r.n, 0)
  if (total < minTrades) return null

  const [worst, ...rest] = rows
  const best = rest[rest.length - 1]
  const lesson = dominantLesson(worst)
  return {
    stage: worst.stage,
    worst,
    best,
    lesson,
    // The comparison is the argument. "Holding leaks most" alone is unfalsifiable
    // to a reader; "5.7R a trade against selection's 1.9R" can be checked.
    parts: {
      worstLabel: STAGES.find((s) => s.key === worst.stage)?.label,
      bestLabel: STAGES.find((s) => s.key === best.stage)?.label,
      worstPerTrade: worst.perTrade,
      bestPerTrade: best.perTrade,
      worstN: worst.n,
      bestN: best.n,
    },
  }
}
