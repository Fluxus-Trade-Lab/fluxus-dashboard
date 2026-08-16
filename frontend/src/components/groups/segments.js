/**
 * The four disjoint RS stretches, oldest first — one owner.
 *
 * Both the trajectory panel and the "where the lead was earned" table draw
 * these; a second copy would drift the first time a window changes upstream
 * (pipeline/themes/rs_engine.py BUCKETS is the source of truth).
 *
 * `inQuarter: false` is load-bearing: 3–6m sits OUTSIDE the three-month total,
 * and a reader who sums a row across gets a number that means nothing.
 *
 * `sessions` is how long each stretch IS, and it is the reason the trajectory
 * panel divides by it. The engine builds these buckets by chaining apart the
 * cumulative Finviz columns — perf_1w, perf_1m, perf_3m, perf_6m — which are
 * roughly 5, 21, 63 and 126 trading sessions; each disjoint bucket is the gap
 * between two of them. So the stretches are 63, 42, 16 and 5 sessions long,
 * and a number measured over 5 sessions is smaller than one measured over 42
 * for reasons that have nothing to do with the theme. Plotted raw, every
 * theme on the page appears to fade toward the present.
 */
export const SEGMENTS = [
  { key: 'rs_3m_6m', label: '3–6m ago', note: 'the quarter before this one — outside the 3m total', inQuarter: false, sessions: 63 },
  { key: 'rs_1m_3m', label: '1–3m', note: 'two months back', inQuarter: true, sessions: 42 },
  { key: 'rs_1w_1m', label: '1w–1m', note: 'the last month, minus the last week', inQuarter: true, sessions: 16 },
  { key: 'rs_0_1w', label: 'this week', note: 'the last five sessions', inQuarter: true, sessions: 5 },
]

/** The three stretches that make up the quarter the page ranks on. */
export const QUARTER_SEGMENTS = SEGMENTS.filter((s) => s.inQuarter)

/**
 * A stretch's excess expressed as excess PER SESSION — the only form in which
 * the three stretches are comparable to each other.
 */
export function ratePerSession(row, seg) {
  const v = row?.[seg.key]
  return Number.isFinite(v) ? v / seg.sessions : null
}

/**
 * The change in pace: how fast a theme is running lately against how fast it
 * ran before, both per session.
 *
 * The engine ships `rs_accel` for this, and it is NOT the same number. That one
 * subtracts a 42-session bucket's TOTAL from a 21-session bucket's total, so a
 * theme running at a perfectly constant pace scores negative — the longer
 * bucket simply accumulated more. High Octane is the clearest case: rs_accel
 * −0.173, which reads as a collapse and classifies it Weakening, while its
 * pace went 0.83% per session to 0.80% — a rounding error by comparison.
 * Across the 76 themes the two disagree in SIGN on nine of them.
 *
 * rs_accel is not wrong — rs_engine.py records that the scheme was validated
 * across 139 ETFs over two years and the Leading-minus-Lagging spread held up
 * on all four tests, so the bias may well be load-bearing as a stricter filter.
 * It is simply not a comparison of pace, which is what a chart of per-session
 * bars is showing. Sorting those bars by rs_accel would put visibly flat rows
 * at the top of a "decelerating" list.
 *
 * So this is computed here, in the units the bars are drawn in, and it is
 * named for what it measures rather than borrowing the engine's word.
 */
export function paceChange(row) {
  const [prior, ...recent] = QUARTER_SEGMENTS
  const priorRate = ratePerSession(row, prior)
  if (priorRate == null) return null
  let sum = 0, sessions = 0
  for (const s of recent) {
    const v = row?.[s.key]
    if (!Number.isFinite(v)) return null
    sum += v; sessions += s.sessions
  }
  return sessions ? sum / sessions - priorRate : null
}
