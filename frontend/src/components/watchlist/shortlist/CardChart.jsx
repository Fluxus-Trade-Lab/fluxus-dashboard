/**
 * 130 sessions, three lines, and the days something happened.
 *
 * Drawn by hand rather than with lightweight-charts, for three reasons that
 * were checked before the decision (see the frontend review of the Short List
 * plan): lightweight-charts cannot read CSS variables — the four places this
 * repo already uses it all resolve tokens to literals and rebuild the chart on
 * a theme flip, and twenty cards would be twenty rebuilds; twenty canvases and
 * twenty ResizeObservers for a 130-bar thumbnail is not a trade worth making;
 * and its marker vocabulary is a fixed set of shapes, while the marks here have
 * to say five different things.
 *
 * The plot stretches with `preserveAspectRatio="none"`, which is why the marks
 * are HTML positioned OVER the svg rather than shapes inside it — a glyph drawn
 * inside a non-uniformly scaled viewBox comes out squashed, the same reason the
 * conditions line keeps its labels outside.
 */

const W = 1000, H = 190, PAD = 3
const PRICE_H = 140, GAP = 12
const VOL_TOP = PRICE_H + GAP, VOL_H = H - VOL_TOP - PAD

/**
 * Five kinds, two channels.
 *
 * Five identities on shape alone is more than shape can carry — so position is
 * the first channel and shape the second. Something that HAPPENED on the day
 * (a repricing, a 4% day, a new high with the RS line) sits above the close and
 * is filled; a line that was CROSSED sits below it and is open. Inside each
 * group there are at most three shapes, which is what shape can hold.
 *
 * No hue anywhere: this page's colour budget belongs to the took/refused pair,
 * and none of these five is a side.
 */
const GLYPH = {
  'EP':    { side: 'up', d: 'M4 0 8 8H0z', fill: true },
  '4%':    { side: 'up', d: 'M4 1a3 3 0 100 6 3 3 0 100-6', fill: true },
  'NH+RS': { side: 'up', d: 'M4 0 8 4 4 8 0 4z', fill: true },
  'x21':   { side: 'down', d: 'M4 1.2a2.8 2.8 0 100 5.6 2.8 2.8 0 100-5.6', fill: false },
  'x50':   { side: 'down', d: 'M1.2 1.2h5.6v5.6H1.2z', fill: false },
}
export const MARK_KINDS = Object.keys(GLYPH)

export function MarkGlyph({ kind, size = 9 }) {
  const g = GLYPH[kind]
  // A kind the data started sending that this file has never heard of gets a
  // ring, not a silent nothing — an unknown mark is information.
  if (!g) {
    return (
      <svg viewBox="0 0 8 8" width={size} height={size} aria-hidden="true">
        <circle cx="4" cy="4" r="3.2" fill="none" stroke="currentColor" strokeWidth="1"
                strokeDasharray="1.5 1.5" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 8 8" width={size} height={size} aria-hidden="true">
      <path d={g.d} fill={g.fill ? 'currentColor' : 'none'}
            stroke="currentColor" strokeWidth={g.fill ? 0 : 1.1} />
    </svg>
  )
}

/** The first session of each month, thinned so labels never collide. Without
 *  it the plot has no WHEN, and the history fold below the card lists dates
 *  that cannot be found on it. */
function monthTicks(dates, maxLabels = 5) {
  const marks = []
  let prev = null
  dates.forEach((d, i) => {
    const m = d?.slice(0, 7)
    if (!m || m === prev) return
    prev = m
    marks.push({ i, label: new Date(`${m}-02T00:00:00Z`)
      .toLocaleString('en', { month: 'short', timeZone: 'UTC' }) })
  })
  const step = Math.max(1, Math.ceil(marks.length / maxLabels))
  return marks.filter((_, ord) => ord % step === 0)
}

/**
 * Linear, or log when one day dwarfs the rest.
 *
 * Measured on the MRNA case the Library article is about: over its last 130
 * sessions the month of footprints the article is ABOUT occupies 7.9% of the
 * chart's height, and the single EP day eats 83%. A +177% bar against a
 * 62-to-64 base flattens everything that led to it into one line — the picture
 * would contradict the text under it. Shortening the window does not help; a
 * 2.8x single-day gap squashes any linear scale it is drawn on.
 *
 * A log axis is the honest instrument for a chart read as PERCENTAGE MOVES,
 * which is what every reading on this site already is (ATR distances, RS
 * percentiles, 20-day highs). It is not the default: on an ordinary name a log
 * axis is a needless distortion of a shape people read by eye. The caller asks
 * for it, and the page says so on the chart — an axis that has changed meaning
 * without saying so is worse than a squashed one.
 */
export default function CardChart({ series, marks = [], height = 190, scale = 'linear' }) {
  const c = series?.c
  if (!c?.length) return null
  const n = c.length

  // The scale takes the moving averages in too: a chart framed on price alone
  // would clip the 50-day on a name that just reclaimed it, which is exactly
  // the name the v-reversal seat exists to show.
  const all = [c, series.e21, series.s50].filter(Boolean).flat().filter((v) => v != null)
  const lo = Math.min(...all), hi = Math.max(...all)
  // a log axis needs every value strictly positive; a price series that is not
  // falls back rather than dropping points nobody was told about
  const log = scale === 'log' && lo > 0
  const f = log ? Math.log : (v) => v
  const flo = f(lo), fspan = (f(hi) - flo) || 1
  const x = (i) => PAD + (i / Math.max(1, n - 1)) * (W - PAD * 2)
  const y = (v) => PAD + (1 - (f(v) - flo) / fspan) * (PRICE_H - PAD * 2)

  /**
   * One polyline per unbroken run, not one per series.
   *
   * This demanded every value be present and returned null otherwise, which
   * meant the 50-day average was ABSENT FROM EVERY CARD and nothing said so:
   * a 130-bar window carries 32 leading nulls for a 50-day mean (it has no
   * history yet to average), so `every` was false on all six. The chart claimed
   * price against its 21- and 50-day and drew two lines.
   *
   * A line that starts partway across is the honest picture — the average does
   * not exist before it has its window — and joining across the gap would draw
   * a value nobody computed.
   */
  const segments = (arr) => {
    if (!arr) return []
    const runs = []
    let cur = []
    arr.forEach((v, i) => {
      if (v == null) { if (cur.length > 1) runs.push(cur); cur = []; return }
      cur.push(`${x(i).toFixed(1)},${y(v).toFixed(1)}`)
    })
    if (cur.length > 1) runs.push(cur)
    return runs.map((r) => r.join(' '))
  }

  const vols = series.v || []
  const vMax = Math.max(1, ...vols.filter((v) => v != null))
  const bw = Math.max(1, (W - PAD * 2) / n - 0.6)

  const at = Object.fromEntries(series.d.map((d, i) => [d, i]))
  const placed = marks
    .map((m) => ({ ...m, i: at[m.d] }))
    .filter((m) => m.i != null)

  const ticks = monthTicks(series.d)
  const last = c[n - 1]

  return (
    <>
    <div className="relative w-full" style={{ height }}>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full block"
           preserveAspectRatio="none" role="img"
           aria-label={`${n} sessions of price with the 21-day and 50-day averages`}>
        {/* the 50-day first and palest, then the 21, then price on top: the
            reading is price AGAINST them, so they are ground, not figure */}
        {segments(series.s50).map((pts, i) => (
          <polyline key={`s${i}`} points={pts} fill="none" strokeWidth="1.2"
                    stroke="var(--color-text-muted)" opacity="0.55"
                    vectorEffect="non-scaling-stroke" />
        ))}
        {segments(series.e21).map((pts, i) => (
          <polyline key={`e${i}`} points={pts} fill="none" strokeWidth="1.2"
                    stroke="var(--color-text-secondary)" opacity="0.8"
                    vectorEffect="non-scaling-stroke" />
        ))}
        {segments(c).map((pts, i) => (
          <polyline key={`c${i}`} points={pts} fill="none" strokeWidth="1.9"
                    stroke="var(--color-text)" vectorEffect="non-scaling-stroke"
                    strokeLinejoin="round" strokeLinecap="round" />
        ))}

        {/* volume, on its own baseline so it never reads as part of the price */}
        <line x1={PAD} x2={W - PAD} y1={H - PAD} y2={H - PAD} strokeWidth="1"
              stroke="var(--color-border)" vectorEffect="non-scaling-stroke" />
        {vols.map((v, i) => v == null ? null : (
          <rect key={i} x={x(i) - bw / 2} width={bw}
                y={H - PAD - (v / vMax) * VOL_H} height={(v / vMax) * VOL_H}
                fill="var(--color-text-muted)" opacity="0.42" />
        ))}
      </svg>

      {/* Marks in HTML over the plot — undistorted at any card width, and each
          one carries its own day's numbers rather than a shared legend line. */}
      {placed.map((m) => {
        const kinds = m.kinds || []
        const ups = kinds.filter((k) => GLYPH[k]?.side === 'up' || !GLYPH[k])
        const downs = kinds.filter((k) => GLYPH[k]?.side === 'down')
        const left = `${(x(m.i) / W) * 100}%`
        const top = `${(y(c[m.i]) / H) * 100}%`
        const title = `${m.d} · ${kinds.join(' + ')}` +
          `${m.chg != null ? ` · ${m.chg > 0 ? '+' : ''}${m.chg}%` : ''}` +
          `${m.rv != null ? ` · vol ${m.rv}x` : ''}`
        return (
          <div key={m.d} className="absolute -translate-x-1/2 pointer-events-none"
               style={{ left, top }}>
            <div className="absolute left-1/2 -translate-x-1/2 bottom-[6px] flex flex-col-reverse
                            items-center gap-[2px] pointer-events-auto
                            text-[var(--color-text-bold)]" title={title}>
              {ups.map((k) => <MarkGlyph key={k} kind={k} />)}
            </div>
            <div className="absolute left-1/2 -translate-x-1/2 top-[6px] flex flex-col
                            items-center gap-[2px] pointer-events-auto
                            text-[var(--color-text-muted)]" title={title}>
              {downs.map((k) => <MarkGlyph key={k} kind={k} />)}
            </div>
          </div>
        )
      })}

      {/* An axis that has changed meaning has to say so. */}
      {log && (
        <span className="absolute left-0 top-0 text-[10px] font-mono
                         text-[var(--color-text-muted)] pointer-events-none"
              title="纵轴按对数：等距离 = 等百分比。一天 +177% 会把线性轴上的其余部分压平">
          log
        </span>
      )}

      {/* one anchor on the price axis — the last close, where the line ends */}
      <span className="absolute right-0 -translate-y-1/2 px-1 text-[10px] font-mono
                       tabular-nums font-semibold pointer-events-none"
            style={{ top: `${(y(last) / H) * 100}%`,
                     background: 'var(--color-text)', color: 'var(--color-bg)' }}>
        {last}
      </span>
    </div>

    <div className="relative h-[13px]">
      {ticks.map((t) => {
        const frac = x(t.i) / W
        const edge = frac < 0.04 ? 'left' : frac > 0.96 ? 'right' : null
        return (
          <span key={t.i}
                className={`absolute text-[10px] font-mono text-[var(--color-text-muted)]
                            whitespace-nowrap ${edge ? '' : '-translate-x-1/2'}`}
                style={edge === 'left' ? { left: 0 } : edge === 'right' ? { right: 0 }
                     : { left: `${frac * 100}%` }}>
            {t.label}
          </span>
        )
      })}
    </div>
    </>
  )
}
