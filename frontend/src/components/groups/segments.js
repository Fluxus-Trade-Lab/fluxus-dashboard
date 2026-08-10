/**
 * The four disjoint RS stretches, oldest first — one owner.
 *
 * Both the trajectory panel and the "where the lead was earned" table draw
 * these; a second copy would drift the first time a window changes upstream
 * (pipeline/themes/rs_engine.py BUCKETS is the source of truth).
 *
 * `inQuarter: false` is load-bearing: 3–6m sits OUTSIDE the three-month total,
 * and a reader who sums a row across gets a number that means nothing.
 */
export const SEGMENTS = [
  { key: 'rs_3m_6m', label: '3–6m ago', note: 'the quarter before this one — outside the 3m total', inQuarter: false },
  { key: 'rs_1m_3m', label: '1–3m', note: 'two months back', inQuarter: true },
  { key: 'rs_1w_1m', label: '1w–1m', note: 'the last month, minus the last week', inQuarter: true },
  { key: 'rs_0_1w', label: 'this week', note: 'the last five sessions', inQuarter: true },
]
