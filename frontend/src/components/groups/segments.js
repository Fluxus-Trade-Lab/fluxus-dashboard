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
