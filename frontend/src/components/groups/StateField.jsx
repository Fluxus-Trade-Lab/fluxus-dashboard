import { useMemo, useState } from 'react'

/**
 * The four states, drawn as what they are.
 *
 * `pipeline/themes/rs_engine.py:180` classifies with two numbers and two cuts:
 *
 *   classify(excess_3m, rs_accel):
 *     excess_3m > 0  →  rs_accel > 0 ? Leading   : Weakening
 *     excess_3m <= 0 →  rs_accel > 0 ? Improving : Lagging
 *
 * So the four labels ARE the four quadrants of those two axes, both cut at
 * zero. Replayed over all 75 published themes this figure reproduces the
 * pipeline's own `state` field 75 times out of 75, with no disagreement. That
 * is why this drawing exists and why it is the largest thing on the page: it
 * is not a second view of the four states, it is their definition.
 *
 * TWO CONSEQUENCES, both load-bearing:
 *
 *   1. THE DOTS CARRY NO STATE COLOUR. Position already says the state — a dot
 *      in the upper right IS Leading — so colouring by state would print one
 *      fact twice. Same reason the old Field strip was deleted on 2026-08-16:
 *      it plotted the same values as the bars beneath it. Colour on this
 *      figure only ever answers "which one did I pick".
 *
 *   2. IT DOES NOT FOLLOW THE WINDOW SWITCH. The states are defined on the
 *      quarter and the month; the 1W / 1M / 3M control moves the ranking under
 *      it. Andy's call, 2026-08-18 — the alternative, letting the switch drive
 *      the x-axis, would put a dot in the Leading cell wearing the word
 *      Weakening, because the payload's `state` would still be the quarter's.
 *      A figure that ignores a control has to say so, so it says so, on itself.
 *
 * SIZE IS THE THIRD CHANNEL: `persistence`, how many of the five horizons
 * (1w/1m/3m/6m/1y) a theme leads on at once. rs_engine calls it the third
 * dimension in its own comment — level and change say nothing about how many
 * timescales agree. It is the half of Andy's question acceleration cannot
 * answer: what is durably strong, as against what merely started running.
 * Most themes score zero on it, and that is a reading, not a gap.
 */

/** Dot radius from persistence 0…5. Zero still draws — a theme leading on no
 *  horizon is information, not an absence. */
const R_MIN = 2.4
const R_STEP = 0.92
const radius = (p) => R_MIN + (Number.isFinite(p) ? p : 0) * R_STEP

const CELLS = [
  { state: 'Leading',   x: 'right', y: 'top',    hint: 'ahead, and pulling further' },
  { state: 'Weakening', x: 'right', y: 'bottom', hint: 'still ahead, no longer gaining' },
  { state: 'Improving', x: 'left',  y: 'top',    hint: 'behind, and closing' },
  { state: 'Lagging',   x: 'left',  y: 'bottom', hint: 'behind, and falling further' },
]

const pct = (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)}%`

/**
 * Which dots wear their name. A rule, printed under the figure, rather than
 * "the ones that happened to fit" — so the labelled set is something the
 * reader can check instead of an artefact of how crowded the plot came out.
 *
 *   · persistence >= 3 — the durable ones, which is why size is on this chart
 *   · the three fastest accelerators inside Improving — "came from behind",
 *     the other half of this page's question
 */
function labelled(rows) {
  const keep = new Set(rows.filter((r) => (r.persistence ?? 0) >= 3).map((r) => r.group))
  rows.filter((r) => r.state === 'Improving')
    .sort((a, b) => b.rs_accel - a.rs_accel)
    .slice(0, 3)
    .forEach((r) => keep.add(r.group))
  return keep
}

const LABEL_PX = 12
const CHAR_W = 6.1          // Plex Sans at 12px — close enough to reserve a box
const LINE_H = 13

/**
 * Where each name goes, and which names lose.
 *
 * Two failures the 2026-08-16 variant round produced, which this must not
 * repeat: names running off the right edge, and names stacking on each other
 * in the crowded middle. Both are solved the same way — reserve a box per
 * label, place in importance order, and DROP a name whose box collides with
 * one already placed rather than drawing over the top of it.
 *
 * A dropped name is not lost: it appears on hover, drawn last and therefore
 * above everything. Importance is persistence first, then distance from the
 * origin, so the durable and the extreme keep their names while the pile near
 * zero — which is most of the board, and is itself the reading — gives them up.
 */
function place(rows, names, x, y, radius, W, PAD) {
  const taken = []
  const hits = (b) => taken.some((t) => !(b.x2 < t.x1 || b.x1 > t.x2 || b.y2 < t.y1 || b.y1 > t.y2))
  const out = new Map()
  const order = rows.filter((r) => names.has(r.group)).sort((a, b) =>
    (b.persistence ?? 0) - (a.persistence ?? 0)
    || Math.hypot(b.excess_3m, b.rs_accel) - Math.hypot(a.excess_3m, a.rs_accel))

  for (const r of order) {
    const px = x(r.excess_3m), py = y(r.rs_accel), rad = radius(r.persistence)
    const w = r.group.length * CHAR_W
    // flip to the dot's left when the right-hand box would leave the plot
    const right = px + rad + 4 + w <= W - PAD.r
    const x1 = right ? px + rad + 4 : px - rad - 4 - w
    const box = { x1, x2: x1 + w, y1: py - LINE_H / 2, y2: py + LINE_H / 2 }
    if (box.x1 < PAD.l || hits(box)) continue
    taken.push(box)
    out.set(r.group, { anchor: right ? 'start' : 'end', dx: right ? rad + 4 : -(rad + 4) })
  }
  return out
}

export default function StateField({ rows, colourOf, onToggle, atLimit }) {
  const [hover, setHover] = useState(null)

  const plot = useMemo(() => {
    const ok = rows.filter((r) => Number.isFinite(r.excess_3m) && Number.isFinite(r.rs_accel))
    if (!ok.length) return null
    // The extents are the cohort's own and they are printed on the axes. An
    // axis padded to round numbers would be a scale nobody measured.
    const ax = Math.max(...ok.map((r) => Math.abs(r.excess_3m)))
    const ay = Math.max(...ok.map((r) => Math.abs(r.rs_accel)))
    return { ok, ax, ay, names: labelled(ok), proxies: ok.filter((r) => r.members === 1).length }
  }, [rows])

  if (!plot) {
    return (
      <p className="m-0 py-8 text-[11px] text-[var(--color-text-muted)]">
        Neither axis was measurable for any theme &mdash; not measured.
      </p>
    )
  }

  const { ok, ax, ay, names, proxies } = plot
  const W = 1000, H = 560, PAD = { t: 26, r: 26, b: 34, l: 34 }
  const x = (v) => PAD.l + ((v / ax + 1) / 2) * (W - PAD.l - PAD.r)
  const y = (v) => PAD.t + ((1 - v / ay) / 2) * (H - PAD.t - PAD.b)
  const x0 = x(0), y0 = y(0)
  const placed = place(ok, names, x, y, radius, W, PAD)
  const dropped = names.size - placed.size

  return (
    <div>
      {/* the figure keeps a floor width and scrolls inside its own box on
          narrow screens. Scaled into a 375px column it would render its type
          at about 4px, and this site holds a hard 10px floor. */}
      <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block min-w-[900px]" role="img"
           aria-label={`${ok.length} themes plotted by quarterly excess against acceleration; the four quadrants are the four states`}>
        {/* the two cuts. Full weight, because they are the classifier itself:
            every state label on this page is decided by which side a dot
            falls on. */}
        <line x1={x0} x2={x0} y1={PAD.t} y2={H - PAD.b}
              stroke="var(--color-text-muted)" strokeWidth="1" />
        <line x1={PAD.l} x2={W - PAD.r} y1={y0} y2={y0}
              stroke="var(--color-text-muted)" strokeWidth="1" />

        {/* the cells wear the state names, so the census that used to be a row
            of chips above the ranking now sits inside the figure defining it */}
        {CELLS.map((c) => {
          const n = ok.filter((r) => r.state === c.state).length
          const tx = c.x === 'right' ? W - PAD.r - 6 : PAD.l + 6
          const ty = c.y === 'top' ? PAD.t + 15 : H - PAD.b - 20
          return (
            <g key={c.state} textAnchor={c.x === 'right' ? 'end' : 'start'}>
              <text x={tx} y={ty} fill="var(--color-text-secondary)"
                    style={{ fontSize: 15, fontWeight: 600 }}>
                {c.state}
                <tspan fill="var(--color-text-muted)"
                       style={{ fontSize: 13, fontWeight: 400,
                                fontFamily: 'var(--font-mono)' }}> {n}</tspan>
              </text>
              <text x={tx} y={ty + 14} fill="var(--color-text-muted)"
                    style={{ fontSize: 11 }}>{c.hint}</text>
            </g>
          )
        })}

        {/* the extents, printed. A scale nobody can read is not a scale. */}
        <text x={W - PAD.r} y={y0 + 15} textAnchor="end" fill="var(--color-text-muted)"
              style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>
          ahead of SPY on the quarter &rarr; {pct(ax)}
        </text>
        <text x={PAD.l} y={y0 + 15} textAnchor="start" fill="var(--color-text-muted)"
              style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>
          {pct(-ax)} &larr; behind
        </text>
        <text x={x0 - 7} y={PAD.t + 4} textAnchor="end" fill="var(--color-text-muted)"
              style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>
          accelerating {pct(ay)}
        </text>
        <text x={x0 - 7} y={H - PAD.b} textAnchor="end" fill="var(--color-text-muted)"
              style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>
          {pct(-ay)}
        </text>

        {/* dots. Unpicked ones are ink; a picked one wears its slot's identity
            colour, which answers "which line is mine" and never grades. */}
        {/* hovered last: its label has to be able to sit over its neighbours */}
        {[...ok].sort((a, b) => (a.group === hover ? 1 : 0) - (b.group === hover ? 1 : 0))
          .map((r) => {
          const c = colourOf?.(r.group) ?? null
          const on = hover === r.group
          const at = placed.get(r.group)
          // hover and picks bypass the collision rule: they are drawn last, so
          // overlapping a neighbour is the correct behaviour for them
          const lay = at ?? { anchor: 'start', dx: radius(r.persistence) + 4 }
          const show = at || c || on
          const px = x(r.excess_3m), py = y(r.rs_accel), rad = radius(r.persistence)
          return (
            <g key={r.group}
               onMouseEnter={() => setHover(r.group)}
               onMouseLeave={() => setHover((h) => (h === r.group ? null : h))}
               onClick={() => onToggle?.(r.group)}
               style={{ cursor: !c && atLimit ? 'not-allowed' : 'pointer' }}>
              <title>
                {`${r.group} · ${r.state} · ${r.members === 1 ? '1 fund' : `${r.members} names`}`
                 + `\nquarter vs SPY ${pct(r.excess_3m)} · acceleration ${pct(r.rs_accel)}`
                 + `\nleads on ${r.persistence ?? 0} of ${r.persistence_of ?? 5} horizons`}
              </title>
              <circle cx={px} cy={py} r={rad}
                      fill={c ?? 'var(--color-text)'}
                      fillOpacity={c || on ? 1 : .62} />
              {on && !c && (
                <circle cx={px} cy={py} r={rad + 3.5} fill="none"
                        stroke="var(--color-accent)" strokeWidth="1.5" />
              )}
              {show && (
                <text x={px + lay.dx} y={py + 4} textAnchor={lay.anchor}
                      style={{ fontSize: LABEL_PX, fontWeight: c || on ? 600 : 400 }}
                      fill={c ?? (on ? 'var(--color-text)' : 'var(--color-text-secondary)')}>
                  {r.group}
                </text>
              )}
            </g>
          )
        })}
      </svg>
      </div>

      {/* the size ramp, and the two things the figure has to admit about
          itself: what it ignores, and who got named */}
      <div className="mt-2 flex flex-wrap items-center gap-x-6 gap-y-2
                      text-[10px] text-[var(--color-text-muted)]">
        <span className="flex items-center gap-2">
          <span>size = horizons led</span>
          <svg width="90" height="16" aria-hidden="true">
            {[0, 1, 2, 3, 4, 5].map((p, i) => (
              <circle key={p} cx={7 + i * 15} cy={8} r={radius(p)}
                      fill="var(--color-text)" fillOpacity=".62" />
            ))}
          </svg>
          <span className="font-mono">0&ndash;5</span>
        </span>
        <span>colour only says which theme you picked &mdash; it never grades one</span>
      </div>
      <p className="m-0 mt-2 text-[10px] leading-relaxed text-[var(--color-text-muted)] max-w-[92ch]">
        <b className="text-[var(--color-text-secondary)]">This figure reads the quarter and
        does not follow the window switch above.</b> The four states are defined on
        quarterly excess and month-scale acceleration; the switch moves the ranking
        underneath. Every dot&rsquo;s quadrant is its state, recomputed from those two
        numbers &mdash; which is also why nothing here is coloured by state. Named dots are
        the ones leading on 3 or more horizons, plus the three fastest accelerators inside
        Improving{dropped > 0 ? `, less ${dropped} whose name had no room beside its dot` : ''};
        the rest name themselves on hover.
        {proxies > 0 && (
          <> {' '}<b className="text-[var(--color-text-secondary)]">{proxies} of {ok.length} are
          a single fund</b> standing in for the theme rather than a basket &mdash; they plot
          the same as a 60-name group and carry no members to check.</>
        )}
      </p>
    </div>
  )
}
