/**
 * One bar per theme, ranked on the window chosen at page level.
 *
 * Design: Fluxus_Brand/visual/2026-08-09_WHAT_TO_SHOW.md §3, §6.1
 *
 * The window switch moved OUT of this component: distribution, ranking and
 * the trajectory highlight all read one switch, because they are one
 * instrument. Two switches would let the strip above and the bars below show
 * different windows on what claims to be one axis — a chart quietly lying
 * about its own x-scale.
 *
 * Rows are selection targets. Clicking a row toggles the theme into the
 * comparison (same gesture as the chips and the dots — one selection, three
 * entry points), so the reader who found a theme by RANK does not have to
 * re-find it by NAME in the chip wall. At the three-theme cap, unselected
 * rows show cursor:not-allowed like everything else.
 *
 * Identity vs encoding, strictly: a selected row wears its slot colour on the
 * NAME and a left rule only. The bar keeps the state grammar (tone + fill) —
 * colour that says "which line is this" must never overwrite colour that says
 * "what state is this in".
 *
 * The scale is the widest actual value, shared with the strip above via the
 * caller. Nothing clamps, nothing rescales per row.
 */

const STATE_MARK = {
  Leading:   { tone: 'var(--color-took)',      solid: true },
  Weakening: { tone: 'var(--color-took)',      solid: false },
  Improving: { tone: 'var(--color-untested)',  solid: true },
  Lagging:   { tone: 'var(--color-untested)',  solid: false },
}
const FALLBACK = { tone: 'var(--color-text-secondary)', solid: true }

function barStyle(state) {
  const { tone, solid } = STATE_MARK[state] ?? FALLBACK
  return solid
    ? { background: tone }
    : { border: `1px solid ${tone}`, background: 'transparent' }
}

export default function ThemeBars({ rows, scale, colourOf, onToggle, atLimit }) {
  const sorted = [...rows]
    .filter((r) => Number.isFinite(r._value))
    .sort((a, b) => b._value - a._value)
  if (!sorted.length) return null
  const missing = rows.length - sorted.length

  return (
    <section>
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 pb-2
                      border-b border-[var(--color-v2-ink)]">
        <span className="text-[11px] text-[var(--color-text-muted)]">
          click a row to add it to the comparison
        </span>
        <span className="text-[11px] text-[var(--color-text-muted)] font-mono">
          scale ±{(scale * 100).toFixed(0)}% · {sorted.length} ranked
          {missing > 0 && ` · ${missing} unmeasured, not drawn`}
        </span>
      </div>

      <div className="mt-1">
        {sorted.map((r, i) => {
          const v = r._value
          const pos = v > 0
          const frac = Math.min(1, Math.abs(v) / scale)
          const colour = colourOf(r.group)
          const blocked = atLimit && !colour
          return (
            <div key={r.group}
                 role="button" tabIndex={0}
                 onClick={() => onToggle(r.group)}
                 onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggle(r.group) } }}
                 aria-pressed={!!colour}
                 style={{
                   cursor: blocked ? 'not-allowed' : 'pointer',
                   borderLeft: colour ? `3px solid ${colour}` : '3px solid transparent',
                 }}
                 className="grid grid-cols-[24px_minmax(126px,206px)_34px_1fr_66px] gap-2
                            items-center py-[3px] pl-1 hover:bg-[var(--color-hover-bg)]">
              <span className="text-[9px] font-mono tabular-nums text-right
                               text-[var(--color-text-muted)]">{i + 1}</span>
              <span className="text-[12.5px] truncate"
                    style={colour ? { color: colour, fontWeight: 600 } : undefined}
                    title={r.tickers?.join(' · ')}>
                {r.group}
              </span>
              {/* the denominator, on every row: a theme of one stock is one stock */}
              <span className="text-[11px] tabular-nums text-right
                               text-[var(--color-text-muted)]">{r.members}</span>
              <span className="relative block h-[12px]">
                {/* the rule overshoots the row so the segments join into one
                    continuous zero — an axis with holes is not an axis */}
                <i className="absolute top-[-3px] bottom-[-3px] left-1/2 w-px
                              bg-[var(--color-text-muted)]" />
                <i className="absolute top-0 bottom-0" style={{
                  ...barStyle(r.state),
                  left: pos ? '50%' : `${50 - frac * 50}%`,
                  width: `${frac * 50}%`,
                }} />
              </span>
              <span className="text-[12px] font-mono tabular-nums text-right">
                {v > 0 ? '+' : ''}{(v * 100).toFixed(1)}%
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
