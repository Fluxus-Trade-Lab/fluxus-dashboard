/**
 * Rotation — the arithmetic behind the three cards, nothing else.
 *
 * Point · Line · Plane (Andy 2026-09-03): the page is three cards and each is
 * one visual primitive. TERRAIN is a plane — the two-week board's four-state
 * counts stacked by session (`theme_ladder.json`). MOMENTUM & ACCELERATION
 * is points — every theme as one dot on three vertical axes. FLUX is lines —
 * up to three themes' two-week relative strength against the benchmark over
 * ten weeks. The spec is frozen in
 * docs/plans/2026-09-02-themes-screener-brainstorm-brief.md §18.22.
 *
 * Colour: the charter's pair and greys. The three Flux lines are blue, red,
 * ink — identity, not grade. The four states are a grey ladder, Leading
 * darkest.
 */
export const STATES = ['Leading', 'Weakening', 'Improving', 'Lagging']
export const STATE_LADDER = {
  Leading: 'var(--color-slot-1)', Weakening: 'var(--color-slot-2)', Improving: 'var(--color-slot-3)', Lagging: 'var(--color-untested)',
}
/** the three Flux lines: pair + ink — never greys, two greys cannot be told apart (brief §18.9) */
export const LINE = ['var(--color-took)', 'var(--color-refused)', 'var(--color-text)']
/** the Flux y-axis is fixed so adding a line never rescales the others (Andy 2026-09-04: ±20%) */
export const Y_MAX = 0.20
/** share of the half-height kept for values past ±Y_MAX — the saturating tail */
export const Y_TAIL = 0.12

/**
 * The Flux y-scale: linear to ±Y_MAX, then a saturating tail.
 *
 * NOT normalisation (that rescales a series to a common range). This is soft
 * clipping — the same idea as matplotlib's `symlog`, linear where the reader
 * does arithmetic and compressed where they only need "off the scale". Inside
 * ±Y_MAX every labelled gridline is honest, so distances between −20% and +20%
 * still read as percentages. Past it the overflow x = |v|/max − 1 is squashed
 * by x/(1+x), which approaches the frame without reaching it: +25%, +40% and
 * +100% land at three visibly different heights and none glues itself to the
 * top edge (Andy 2026-09-04: 「仍然是在上沿，但不要太贴在顶部了」). tanh was the
 * first try and saturates too fast — it put +40% and +100% on the same pixel.
 * The hover reads the true value, so nothing is hidden, only bent.
 *
 * @returns signed fraction of the half-height, in (−1, 1)
 */
export function yFrac(v, max = Y_MAX, tail = Y_TAIL) {
  if (!Number.isFinite(v)) return null
  const lin = 1 - tail
  const t = v / max
  if (Math.abs(t) <= 1) return t * lin
  const over = Math.abs(t) - 1
  return Math.sign(t) * (lin + tail * (over / (1 + over)))
}
/** two-week relative strength = ten sessions */
export const R2W_LAG = 10
/** Flux plots one point a week, not one a day (Andy 2026-09-06: 「选每周好」).
 *
 * The quantity is unchanged — it is the same two-week strength TSF plots, and
 * theirs is this line sampled every ten sessions (brief §18.25). Measured over
 * the three themes on screen that day, the daily line changed direction 24.7
 * times per line; weekly 4.3; every three sessions 9.0 for the same distortion
 * (3.1pp vs 3.5pp against the unplotted days). Three-day sampling bought half
 * the calm at the full price, and its points drift across weekdays where a
 * five-session step lands on the same one. */
export const FLUX_STEP = 5

/** the plotted sessions: every `step` back from the last, never earlier than `lag` */
export function sampleIndices(n, lag = R2W_LAG, step = FLUX_STEP) {
  const out = []
  for (let i = n - 1; i >= lag; i -= step) out.unshift(i)
  return out
}
/** the prior three weeks (rs_1w_1m) as weeks, for a per-week pace */
export const PRIOR_WEEKS = 3.2
/** `word` is a translation key — the cards speak one language at a time */
export const BOARDS = [
  { key: 'rs2w', word: 'rot.burst', title: 'RS 0–2w' },
  { key: 'acc', word: 'rot.turn', title: 'Acceleration' },
  { key: 'long', word: 'rot.persist', title: 'Quarter' },
]
export const WINDOWS = ['rot.win0', 'rot.win1', 'rot.win2', 'rot.win3', 'rot.win4']

/**
 * The first session Terrain draws: the start of the oldest window the select
 * offers. The archive runs deeper than the page reads (90 sessions against ten
 * weeks), and drawing what no control can reach is just a longer picture
 * (Andy 2026-09-04: 「不需要展示更早以前的数据」).
 */
export function visibleFrom(dates, windows = WINDOWS) {
  return windowBounds(dates, windows.length - 1)?.start ?? 0
}

export const fmtPct = (x, d = 1) => (x == null || !Number.isFinite(x) ? '—' : `${x >= 0 ? '+' : '−'}${Math.abs(x * 100).toFixed(d)}%`)

/** this week's pace minus the prior three weeks' pace — the turn detector */
export function wkAccel(r) {
  return r.rs_0_1w - r.rs_1w_1m / PRIOR_WEEKS
}

/** rolling two-week strength from a relative index: rel[t] / rel[t − lag] − 1, null where either is missing */
export function r2wSeries(rel, lag = R2W_LAG) {
  if (!rel) return []
  return rel.map((v, i) => {
    const p = rel[i - lag]
    return v == null || p == null || i < lag ? null : v / p - 1
  })
}

/** the last finite value of a series, or null */
export function lastOf(xs) {
  for (let i = (xs?.length ?? 0) - 1; i >= 0; i -= 1) if (Number.isFinite(xs[i])) return xs[i]
  return null
}

/**
 * The three boards. `rs2w` comes from the ladder's relative index when the
 * group has one (the same arithmetic as the two-week board's level axis); a
 * group without a series falls back to this week plus one week of the prior
 * three — an approximation, flagged as `approx` so the card can say so.
 */
export function boardsOf(rows, seriesOf) {
  const items = rows.map((r) => {
    const r2w = lastOf(r2wSeries(seriesOf(r.group)?.rel))
    const haveWeeks = Number.isFinite(r.rs_0_1w) && Number.isFinite(r.rs_1w_1m)
    return {
      r,
      rs2w: r2w != null ? r2w : haveWeeks ? r.rs_0_1w + r.rs_1w_1m / PRIOR_WEEKS : null,
      approx: r2w == null && haveWeeks,
      acc: haveWeeks ? wkAccel(r) : null,
      long: Number.isFinite(r.excess_3m) ? r.excess_3m : null,
    }
  })
  const board = (k) => items.filter((it) => Number.isFinite(it[k])).sort((a, b) => b[k] - a[k])
  return { rs2w: board('rs2w'), acc: board('acc'), long: board('long'), approx: items.some((it) => it.approx) }
}

/** the default Flux lines: the top of each board, skipping a name already taken — three names when three boards have one */
export function defaultPicks(boards) {
  const out = []
  BOARDS.forEach(({ key }) => {
    const hit = (boards[key] ?? []).find((it) => !out.includes(it.r.group))
    if (hit) out.push(hit.r.group)
  })
  return out
}

/** dot radius grows with the value: the leaders read bigger and take more room (Andy 2026-09-03) */
export function radius(v, lo, hi, rMin = 3.5, rMax = 10) {
  return rMin + (rMax - rMin) * ((v - lo) / (hi - lo || 1))
}

/**
 * Circle packing for a vertical strip: dots are placed largest first at the
 * axis; a dot that would touch one already placed steps sideways two pixels
 * at a time, and only when a level is full gives a little vertically (up to
 * `dyMax`). Returns [{x, y}] in input order; no two circles overlap.
 */
export function pack(items, x0, { dxMax = 56, dyMax = 14, gap = 1.5 } = {}) {
  const candidates = (dyLim) => {
    const cand = []
    for (let dy = 0; dy <= dyLim; dy += 2) {
      for (let dx = 0; dx <= dxMax; dx += 2) {
        for (const sx of dx ? [-1, 1] : [1]) for (const sy of dy ? [-1, 1] : [1]) cand.push([sx * dx, sy * dy])
      }
    }
    return cand.sort((a, b) => (a[0] ** 2 + 4 * a[1] ** 2) - (b[0] ** 2 + 4 * b[1] ** 2))
  }
  const order = items.map((it, i) => ({ it, i })).sort((a, b) => b.it.r - a.it.r)
  const placed = [], out = new Array(items.length)
  const free = (x, y, r) => !placed.some((p) => Math.hypot(p.x - x, p.y - y) < p.r + r + gap)
  order.forEach(({ it, i }) => {
    let pos = null
    // the vertical give widens only when a cluster is denser than the strip can hold — never leave a dot overlapping
    for (let dyLim = dyMax; pos == null && dyLim <= 512; dyLim *= 2) {
      for (const [dx, dy] of candidates(dyLim)) {
        const x = x0 + dx, y = it.y + dy
        if (free(x, y, it.r)) { pos = { x, y }; break }
      }
    }
    pos = pos ?? { x: x0, y: it.y }
    placed.push({ ...pos, r: it.r }); out[i] = pos
  })
  return out
}

/** labels pushed apart so none overlap; returns [{item, y, y0}] sorted by y */
export function spreadLabels(items, yOf, gap = 14) {
  const sorted = items.map((item) => ({ item, y: yOf(item) })).sort((a, b) => a.y - b.y)
  let prev = -Infinity
  return sorted.map((e) => { const y = Math.max(e.y, prev + gap); prev = y; return { item: e.item, y, y0: e.y } })
}

/** a smooth path through points — Catmull-Rom as cubic Béziers; a solid line, no dashes (Andy) */
export function smoothPath(pts) {
  if (!pts.length) return ''
  if (pts.length < 3) return `M${pts.map((p) => `${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' L')}`
  let d = `M${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`
  for (let i = 0; i < pts.length - 1; i += 1) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2
    d += ` C${(p1[0] + (p2[0] - p0[0]) / 6).toFixed(1)} ${(p1[1] + (p2[1] - p0[1]) / 6).toFixed(1)} ${(p2[0] - (p3[0] - p1[0]) / 6).toFixed(1)} ${(p2[1] - (p3[1] - p1[1]) / 6).toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`
  }
  return d
}

/**
 * Calendar-week windows counted back from the latest session (TSF's "Last 2w
 * / 2–4w ago / …"): window k covers (D − 14(k+1) days, D − 14k days].
 * Returns {start, end} as indices into `dates`, or null when the window has
 * no session.
 */
export function windowBounds(dates, k, days = 14) {
  if (!dates?.length) return null
  const DAY = 86400e3, D0 = Date.parse(dates[dates.length - 1])
  const hi = D0 - days * k * DAY, lo = D0 - days * (k + 1) * DAY
  let end = -1, start = -1
  dates.forEach((d, i) => { const t = Date.parse(d); if (t <= hi) end = i; if (t > lo && start < 0) start = i })
  if (end < 0 || start < 0 || start > end) return null
  return { start, end }
}

/** the four counts on session `i` of the ladder history */
export function countsAt(history, i) {
  const out = {}
  STATES.forEach((s) => { out[s] = history?.[s]?.[i] ?? 0 })
  return out
}

/** who sat in each state on session `i` — from per-group `states_2w`, or today's rung when `i` is the last session */
export function namesByState(names, seriesOf, todayOf, i, last) {
  const out = { Leading: [], Weakening: [], Improving: [], Lagging: [] }
  let known = false
  names.forEach((n) => {
    const st = seriesOf(n)?.states_2w?.[i] ?? (i === last ? todayOf(n) : null)
    if (st && st in out) { out[st].push(n); known = true }
  })
  STATES.forEach((s) => out[s].sort())
  return { byState: out, known }
}
