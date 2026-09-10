/**
 * Two small bar primitives shared by the "tools" under Review — the 2026-09-11
 * pass that turned four virtual-scroll tables into a knob + a chart.
 *
 * Neither invents a number: every value passed in is one the tool already
 * computed (stopSim's `diff`, trimAnalysis's `captured`, demonFinder's
 * tacticalStats). This file only draws them.
 */

/** A single bar, 0 → max, with an optional target tick — for a value read
 *  against a fixed goal (avg trim size vs. the 25–40% band, e.g.). `color` is
 *  a CSS colour value (a `var(--...)` token), not a Tailwind class. */
export function Bar({ label, value, max, target, unit = '%', color = 'var(--color-accent)', sub }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  const tPct = target != null ? Math.max(0, Math.min(100, (target / max) * 100)) : null
  return (
    <div className="py-1.5">
      <div className="flex items-baseline justify-between gap-2 mb-1">
        <span className="text-[11px] text-[var(--color-text-muted)] uppercase tracking-wide">{label}</span>
        <span className="text-[13px] font-mono font-semibold" style={{ color }}>
          {value.toFixed(1)}{unit}
        </span>
      </div>
      <div className="h-[6px] relative rounded-full overflow-hidden bg-[var(--color-border-light)]">
        <div className="h-full absolute left-0 top-0 rounded-full"
             style={{ width: `${pct}%`, background: color }} />
        {tPct != null && (
          <div className="absolute top-[-2px] bottom-[-2px] w-[2px] bg-[var(--color-text)]"
               style={{ left: `${tPct}%` }} title={`target ${target}${unit}`} />
        )}
      </div>
      {sub && <div className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{sub}</div>}
    </div>
  )
}

/** N compact rows, one bar each, 0 → max — for a ranked list where a stacked
 *  card-per-row (`Bar`) would run the page too tall. `colorOf(row)` picks the
 *  bar's colour per row (a threshold colour, e.g.); defaults to the accent. */
export function RankedBars({ rows, max, colorOf, formatValue, height = 14 }) {
  if (!rows?.length) return null
  const m = max ?? Math.max(1, ...rows.map((r) => Math.abs(r.value)))
  return (
    <div>
      {rows.map((r) => (
        <div key={r.key} className="flex items-center gap-2 py-[3px]">
          <span className="text-[11px] font-mono w-[64px] shrink-0 truncate text-right
                           text-[var(--color-text-secondary)]" title={r.key}>{r.key}</span>
          <div className="flex-1 rounded-sm overflow-hidden bg-[var(--color-border-light)]" style={{ height }}>
            <div className="h-full rounded-sm"
                 style={{
                   width: `${Math.max(0, Math.min(100, (r.value / m) * 100))}%`,
                   background: colorOf ? colorOf(r) : 'var(--color-accent)',
                 }} />
          </div>
          <span className="text-[11px] font-mono w-[52px] shrink-0 text-[var(--color-text-secondary)]">
            {formatValue ? formatValue(r.value) : r.value}
          </span>
        </div>
      ))}
    </div>
  )
}

/** N bars growing from a shared zero line, either direction — for a value
 *  that can help or hurt (stopSim's diff, a re-add's net P&L). Bars are
 *  pre-sorted by the caller; this only draws what it is given. */
export function DivergingBars({ rows, max, formatValue, height = 16 }) {
  if (!rows?.length) return null
  const m = max ?? Math.max(1, ...rows.map((r) => Math.abs(r.value)))
  return (
    <div>
      {rows.map((r) => {
        const frac = Math.max(-1, Math.min(1, r.value / m))
        const up = frac >= 0
        return (
          <div key={r.key} className="flex items-center gap-2 py-[3px]">
            <span className="text-[11px] font-mono w-[68px] shrink-0 truncate text-right
                             text-[var(--color-text-secondary)]" title={r.key}>{r.key}</span>
            <div className="flex-1 relative" style={{ height }}>
              <div className="absolute left-1/2 top-0 bottom-0 w-px bg-[var(--color-border)]" />
              <div className="absolute top-0 bottom-0 rounded-sm"
                   style={{
                     left: up ? '50%' : `${50 + frac * 50}%`,
                     width: `${Math.abs(frac) * 50}%`,
                     background: up ? 'var(--color-profit)' : 'var(--color-loss)',
                   }} />
            </div>
            <span className={`text-[11px] font-mono w-[64px] shrink-0 ${up ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
              {formatValue ? formatValue(r.value) : r.value}
            </span>
          </div>
        )
      })}
    </div>
  )
}
