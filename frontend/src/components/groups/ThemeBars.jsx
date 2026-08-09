import { useMemo, useState } from 'react'

/**
 * One bar per theme, ranked. The page's subject.
 *
 * Design: Fluxus_Brand/visual/2026-08-09_WHAT_TO_SHOW.md §3, §6.1
 *
 * We already had this number — `excess_3m` — but as the third column of an
 * eight-column table, weighted the same as `method` and `validation`. TSF gives
 * the identical measurement a page of its own with nothing else on it, and that
 * is why theirs reads at a glance and ours did not. Not more data: fewer things
 * competing to be the subject.
 *
 * Two measurements, one at a time. Level and acceleration answer different
 * questions and drawn side by side neither wins; the switch changes WHICH
 * quantity is drawn, never HOW it is drawn — the encoding is a bar on a shared
 * zero rule in both cases, so a reader never has to relearn the picture.
 *
 * The scale is the widest actual value, printed above the chart. Nothing is
 * clamped and nothing is rescaled per row, so a bar twice as long is twice the
 * number, and the outlier that sets the scale is the one you can see.
 */

const METRICS = [
  { key: 'excess_3m', label: 'Relative strength', note: 'against SPY, 3 months' },
  { key: 'rs_accel', label: 'Acceleration', note: 'is that gap still widening' },
]

/**
 * Four states on two channels, because the state IS two binaries: where a theme
 * stands (strong or weak against SPY) crossed with where it is going (the gap
 * widening or narrowing). Giving all four to hue alone needed four hues nobody
 * can hold, and the first attempt quietly gave Leading and Improving the same
 * one — a legend naming four categories while drawing three.
 *
 *   strong + widening   Leading      solid, strong tone
 *   strong + narrowing   Weakening   outlined, strong tone
 *   weak   + widening   Improving    solid, weak tone
 *   weak   + narrowing   Lagging     outlined, weak tone
 *
 * Fill answers "is it still working", tone answers "from how far ahead", and
 * neither carries the sign — that is the bar's side of the zero rule.
 */
const STATE_MARK = {
  Leading:   { tone: 'var(--color-took)',      solid: true },
  Weakening: { tone: 'var(--color-took)',      solid: false },
  Improving: { tone: 'var(--color-untested)',  solid: true },
  Lagging:   { tone: 'var(--color-untested)',  solid: false },
}
const FALLBACK = { tone: 'var(--color-text-secondary)', solid: true }

/** Solid fills; narrowing themes are drawn as an outline of the same tone. */
function barStyle(state) {
  const { tone, solid } = STATE_MARK[state] ?? FALLBACK
  return solid
    ? { background: tone }
    : { border: `1px solid ${tone}`, background: 'transparent' }
}

export default function ThemeBars({ rows }) {
  const [metric, setMetric] = useState('excess_3m')

  const { sorted, scale } = useMemo(() => {
    const withValue = rows.filter((r) => r[metric] != null)
    const out = [...withValue].sort((a, b) => b[metric] - a[metric])
    const widest = out.reduce((m, r) => Math.max(m, Math.abs(r[metric])), 0)
    return { sorted: out, scale: widest || 1 }
  }, [rows, metric])

  if (!rows.length) return null

  const missing = rows.length - sorted.length
  const active = METRICS.find((m) => m.key === metric)

  return (
    <section>
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 pb-2
                      border-b border-[var(--color-v2-ink)]">
        <div className="flex items-baseline gap-4">
          {METRICS.map((m) => (
            <button key={m.key} type="button" onClick={() => setMetric(m.key)}
                    className={`bg-transparent border-0 p-0 cursor-pointer text-[13px]
                                ${m.key === metric
                                  ? 'text-[var(--color-text)] font-semibold'
                                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'}`}>
              {m.label}
            </button>
          ))}
          <span className="text-[11px] text-[var(--color-text-muted)]">{active.note}</span>
        </div>
        <span className="text-[11px] text-[var(--color-text-muted)] font-mono">
          scale ±{(scale * 100).toFixed(0)}% · {sorted.length} ranked
          {missing > 0 && ` · ${missing} unmeasured, not drawn`}
        </span>
      </div>

      <div className="mt-1">
        {sorted.map((r) => {
          const v = r[metric]
          const pos = v > 0
          const frac = Math.abs(v) / scale
          return (
            <div key={r.group}
                 className="grid grid-cols-[minmax(150px,230px)_34px_1fr_66px] gap-2 items-center
                            py-[3px] hover:bg-[var(--color-hover-bg)]">
              <span className="text-[12.5px] truncate" title={r.tickers?.join(' · ')}>
                {r.group}
              </span>
              {/* the denominator, on every row: a theme of one stock is one stock */}
              <span className="text-[11px] tabular-nums text-right
                               text-[var(--color-text-muted)]">{r.members}</span>
              <span className="relative block h-[12px]">
                {/* The rule extends past the bar by the row's own padding so the
                    segments join into one continuous zero across the chart. A
                    dashed line of gaps is not an axis. */}
                <i className="absolute top-[-3px] bottom-[-3px] left-1/2 w-px
                              bg-[var(--color-text-muted)]" />
                <i className="absolute top-0 bottom-0" style={{
                  ...barStyle(r.state),
                  left: pos ? '50%' : `${50 - frac * 50}%`,
                  width: `${frac * 50}%`,
                }} />
              </span>
              <span className="text-[12px] tabular-nums text-right">
                {(v * 100).toFixed(1)}%
              </span>
            </div>
          )
        })}
      </div>

      <div className="flex flex-wrap gap-x-5 gap-y-1 pt-3 text-[10px]
                      text-[var(--color-text-muted)]">
        {Object.keys(STATE_MARK).map((name) => (
          <span key={name} className="flex items-center gap-1.5">
            <i className="block w-3 h-[9px]" style={barStyle(name)} />{name}
          </span>
        ))}
        <span>
          · solid is still widening, outlined is narrowing; the tone says strong or
          weak, and the sign is which side of the rule the bar sits on
        </span>
      </div>
    </section>
  )
}
