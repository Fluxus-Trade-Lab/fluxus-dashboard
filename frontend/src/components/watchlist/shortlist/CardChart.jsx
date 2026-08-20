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

export default function CardChart({ series, marks = [], height = 190 }) {
  const c = series?.c
  if (!c?.length) return null
  const n = c.length

  // The scale takes the moving averages in too: a chart framed on price alone
  // would clip the 50-day on a name that just reclaimed it, which is exactly
  // the name the v-reversal seat exists to show.
  const all = [c, series.e21, series.s50].filter(Boolean).flat().filter((v) => v != null)
  const lo = Math.min(...all), hi = Math.max(...all)
  const span = hi - lo || 1
  const x = (i) => PAD + (i / Math.max(1, n - 1)) * (W - PAD * 2)
  const y = (v) => PAD + (1 - (v - lo) / span) * (PRICE_H - PAD * 2)

  const line = (arr) => arr && arr.every((v) => v != null)
    ? arr.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
    : null

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
        {line(series.s50) && (
          <polyline points={line(series.s50)} fill="none" strokeWidth="1.2"
                    stroke="var(--color-text-muted)" opacity="0.55"
                    vectorEffect="non-scaling-stroke" />
        )}
        {line(series.e21) && (
          <polyline points={line(series.e21)} fill="none" strokeWidth="1.2"
                    stroke="var(--color-text-secondary)" opacity="0.8"
                    vectorEffect="non-scaling-stroke" />
        )}
        <polyline points={line(c)} fill="none" strokeWidth="1.9"
                  stroke="var(--color-text)" vectorEffect="non-scaling-stroke"
                  strokeLinejoin="round" strokeLinecap="round" />

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
