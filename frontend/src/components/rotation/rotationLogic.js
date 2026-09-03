/**
 * Rotation — the pure arithmetic behind the five instruments.
 *
 * Everything here reads the fields `groups.json` already ships per group:
 * the four disjoint stretches (rs_3m_6m · rs_1m_3m · rs_1w_1m · rs_0_1w),
 * the quarter level (excess_3m), the acceleration gate and slope (rs_accel,
 * rs_accel_rate). No history is needed for the three questions; history only
 * feeds the field, the leadership counts and the compare lines.
 *
 * ANDY'S THREE QUESTIONS (2026-09-02), as shapes across the stretches:
 *   ① Building  — prior 3 weeks up, this week up and at least as fast, and
 *                 not already strong 1–3 months ago (it is NEW strength).
 *   ② Igniting  — weak for months (3–6m or the quarter negative), quiet for
 *                 the prior 3 weeks, this week turned up and faster.
 *   ③ Fading    — ahead for months, the acceleration slope has turned
 *                 negative, and this week is still slower than the prior 3.
 * The two caps are placeholders the page exposes under How to read; the brief
 * (docs/plans/2026-09-02-themes-screener-brainstorm-brief.md §10–§12) has the
 * backtests that shaped them. Stretches are converted to a per-week pace
 * before comparing: 5 sessions a week, 21 a month.
 *
 * COLOUR ON THE PAGE (Andy 2026-09-03: the pair and greys, nothing else): a
 * dot is blue when the group moved to a stronger state over the window, red
 * when weaker, ink otherwise — `stateChange.js`'s grammar, reused. The
 * ribbons read the four states as a grey ladder, strongest darkest.
 */
export const WEEKS = { rs_3m_6m: 12.6, rs_1m_3m: 8.4, rs_1w_1m: 3.2, rs_0_1w: 1 }
export const STATES = ['Leading', 'Improving', 'Weakening', 'Lagging']
export const QUESTIONS = ['q1', 'q2', 'q3']
export const QUESTION_WORD = { q1: 'Building', q2: 'Igniting', q3: 'Fading' }
export const DEFAULT_THRESHOLDS = { q1PriorCap: 0.05, q2PriorCap: 0.02 }
/** the four states as a grey ladder, strongest darkest: ahead-and-accelerating … behind-and-falling */
export const STATE_LADDER = {
  Leading: 'var(--color-slot-1)', Weakening: 'var(--color-slot-2)', Improving: 'var(--color-slot-3)', Lagging: 'var(--color-untested)',
}
/** how many sessions back the field's colour looks when it asks "did it change sides" */
export const CHANGE_WINDOW = 5

const STRETCHES = ['rs_3m_6m', 'rs_1m_3m', 'rs_1w_1m', 'rs_0_1w']

/** true when every field the shapes read is a finite number */
export function measurable(r) {
  return [...STRETCHES, 'excess_3m', 'rs_accel_rate'].every((k) => Number.isFinite(r?.[k]))
}

/** per-week pace of each stretch, oldest first */
export function paces(r) {
  return STRETCHES.map((k) => r[k] / WEEKS[k])
}

/** this week's pace minus the prior three weeks' pace — the turn detector */
export function wkAccel(r) {
  return r.rs_0_1w - r.rs_1w_1m / WEEKS.rs_1w_1m
}

export function questionOf(r, t = DEFAULT_THRESHOLDS) {
  if (!measurable(r)) return null
  const pn = r.rs_0_1w
  const pp = r.rs_1w_1m / WEEKS.rs_1w_1m
  const q1 = pp > 0 && pn > 0 && pn >= pp && r.rs_1m_3m <= t.q1PriorCap
  const q2 = (r.rs_3m_6m < 0 || r.excess_3m < 0) && r.rs_1w_1m <= t.q2PriorCap && r.rs_0_1w > 0 && pn > pp
  const q3 = r.excess_3m > 0 && r.rs_1m_3m > 0 && r.rs_accel_rate < 0 && pn <= pp
  return q1 ? 'q1' : q2 ? 'q2' : q3 ? 'q3' : null
}

/** how each list is ordered — the strength of the turn, in that question's own terms */
export const QUESTION_SORT = {
  q1: (r) => wkAccel(r),
  q2: (r) => r.rs_0_1w,
  q3: (r) => -r.rs_accel_rate,
}

export function questionLists(rows, t = DEFAULT_THRESHOLDS) {
  const out = { q1: [], q2: [], q3: [] }
  rows.forEach((r) => { const q = questionOf(r, t); if (q) out[q].push(r) })
  QUESTIONS.forEach((k) => out[k].sort((a, b) => QUESTION_SORT[k](b) - QUESTION_SORT[k](a)))
  return out
}

/** the top of each question, up to three — what Compare shows before anyone picks */
export function defaultPicks(lists) {
  return QUESTIONS.map((k) => lists[k][0]).filter(Boolean).slice(0, 3)
}

/**
 * State counts for the cohort at session `i` of the history (or today when
 * `i` is null). `historyOf(name)` returns `{excess, rs_accel, state}` arrays
 * or null; a group with no row that day is simply not counted — absence is
 * not a state.
 */
export function stateCounts(rows, historyOf, i = null) {
  const c = { Leading: 0, Improving: 0, Weakening: 0, Lagging: 0 }
  rows.forEach((r) => {
    const s = i == null ? r.state : historyOf(r.group)?.state?.[i]
    if (s && s in c) c[s] += 1
  })
  return c
}

/** the names that changed sides over the window ending at session `i` — {up: [...], down: [...]} */
export function sideChanges(rows, historyOf, i, changeOf, window = CHANGE_WINDOW) {
  const out = { up: [], down: [] }
  rows.forEach((r) => {
    const states = historyOf(r.group)?.state
    if (!states) return
    const dir = changeOf(states.slice(Math.max(0, i - window), i + 1))
    if (dir) out[dir].push(r.group)
  })
  return out
}

/** the fastest movers by weekly acceleration — right (speeding up) and left (slowing) */
export function fastest(rows, nRight = 4, nLeft = 2) {
  const sorted = rows.slice().sort((a, b) => wkAccel(b) - wkAccel(a))
  return { up: sorted.slice(0, nRight).filter((r) => wkAccel(r) > 0), down: sorted.slice(-nLeft).reverse().filter((r) => wkAccel(r) < 0) }
}

/** the headline: names, never counts. `[{text, strong}]` */
export function summaryParts(lists) {
  const names = (list, n = 3) => list.slice(0, n).map((r) => r.group).join(', ')
  const parts = []
  if (lists.q2.length) parts.push({ text: 'Igniting: ', strong: names(lists.q2) + '.' })
  if (lists.q1.length) parts.push({ text: 'Building: ', strong: names(lists.q1) + '.' })
  if (lists.q3.length) parts.push({ text: 'Fading: ', strong: names(lists.q3) + (lists.q3.length > 3 ? ` and ${lists.q3.length - 3} more` : '') + '.' })
  if (!parts.length) parts.push({ text: 'Nothing is turning today.' })
  return parts
}

/** position of a group at a fractional session `t` — linear between the two sessions around it */
export function positionAt(h, t) {
  if (!h?.excess?.length) return null
  const n = h.excess.length
  const a = Math.max(0, Math.min(n - 1, Math.floor(t))), b = Math.min(n - 1, a + 1), f = Math.min(1, Math.max(0, t - a))
  const xa = h.excess[a], ya = h.rs_accel[a], xb = h.excess[b], yb = h.rs_accel[b]
  if (xa == null || ya == null) return null
  if (xb == null || yb == null || b === a) return { x: xa, y: ya, state: h.state?.[a] }
  return { x: xa + (xb - xa) * f, y: ya + (yb - ya) * f, state: h.state?.[f <= 0.5 ? a : b] }   // the nearer session's state; the midpoint keeps the earlier one
}

/** end labels pushed apart so none overlap; returns [{item, y, y0}] sorted by y */
export function spreadLabels(items, yOf, gap = 14) {
  const sorted = items.map((item) => ({ item, y: yOf(item) })).sort((a, b) => a.y - b.y)
  let prev = -Infinity
  return sorted.map((e) => { const y = Math.max(e.y, prev + gap); prev = y; return { item: e.item, y, y0: e.y } })
}

/** deterministic swarm stacking: a level per dot so neighbours within `minGap` step outward */
export function swarmLevels(xs, minGap = 10) {
  const taken = []
  return xs.map((x) => {
    let lvl = 0
    while (taken.some(([tx, tl]) => Math.abs(tx - x) < minGap && tl === lvl)) lvl += 1
    taken.push([x, lvl])
    return lvl
  })
}
