/**
 * The ranking: one bar per theme, ordered on the window chosen at page level.
 *
 * Pure rows. The section header, the scale note, the state counts and the
 * teaching all live on the page — this component draws marks and nothing
 * else, which is what finally made the page quiet: every object used to
 * carry its own captions, and seven captions is a textbook, not a panel.
 *
 * Rows are selection targets (same gesture as the dots and the search). The
 * affordance is shown, not written: a + surfaces on hover at the row's end,
 * flipping to − when the row is already picked, and the not-allowed cursor
 * refuses a fourth pick before the click. Identity colour goes on the NAME
 * and a left rule only — the bar keeps the state grammar, because "which line
 * is this" must never overwrite "what state is this in".
 */

const STATE_MARK = {
  Leading:   { tone: 'var(--color-took)',      solid: true },
  Weakening: { tone: 'var(--color-took)',      solid: false },
  Improving: { tone: 'var(--color-untested)',  solid: true },
  Lagging:   { tone: 'var(--color-untested)',  solid: false },
}
const FALLBACK = { tone: 'var(--color-text-secondary)', solid: true }

export function barStyle(state) {
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

  return (
    <div>
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
               onKeyDown={(e) => {
                 if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggle(r.group) }
               }}
               aria-pressed={!!colour}
               style={{
                 cursor: blocked ? 'not-allowed' : 'pointer',
                 borderLeft: colour ? `3px solid ${colour}` : '3px solid transparent',
               }}
               className="group grid grid-cols-[24px_minmax(126px,206px)_34px_1fr_66px_18px]
                          gap-2 items-center py-[3px] pl-1
                          hover:bg-[var(--color-hover-bg)]">
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
            <span aria-hidden
                  className={`text-[13px] text-center text-[var(--color-text-muted)]
                              ${blocked ? 'invisible'
                                        : 'opacity-0 group-hover:opacity-100'}`}>
              {colour ? '−' : '+'}
            </span>
          </div>
        )
      })}
    </div>
  )
}
