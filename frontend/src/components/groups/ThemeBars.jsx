import { useState } from 'react'

/**
 * The ranking: one bar per theme, ordered on the window chosen at page level.
 *
 * FOLDED BY DEFAULT. Seventy-two rows is a wall, and the middle fifty are
 * themes within a point or two of SPY — the distribution strip already says
 * "nothing much here" about them collectively. What shows: the head (where
 * leadership is), the tail (where the damage is), and every selected theme
 * with one neighbour of context so its rank reads as a place, not a number.
 * The hidden stretches are labelled with their count and expand on click —
 * a fold that says how much it holds is a decision; one that hides silently
 * is a lie of omission.
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

/* v3 charter (2026-08-15): the four states are data states, not poles and not
   constraints, so they live on the grey floor. The grammar stays two-channel
   — tone × fill — it just stops borrowing the pair's blue: Leading is the
   bold ink solid, Weakening the same ink outlined (was-strong, hollowing),
   Improving the light grey solid (substance arriving), Lagging light grey
   outlined (neither strength nor substance). Blue now appears on this page
   only where its red twin can appear too. */
const STATE_MARK = {
  Leading:   { tone: 'var(--color-text-bold)', solid: true },
  Weakening: { tone: 'var(--color-text-bold)', solid: false },
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

const HEAD = 8
const TAIL = 4
const NEIGHBOURS = 1

export default function ThemeBars({ rows, scale, colourOf, onToggle, atLimit, dim }) {
  const [showAll, setShowAll] = useState(false)
  const sorted = [...rows]
    .filter((r) => Number.isFinite(r._value))
    .sort((a, b) => b._value - a._value)
  if (!sorted.length) return null

  // Which ranks stay visible when folded.
  const keep = new Set()
  if (showAll || sorted.length <= HEAD + TAIL + 4) {
    sorted.forEach((_, i) => keep.add(i))
  } else {
    for (let i = 0; i < HEAD; i++) keep.add(i)
    for (let i = sorted.length - TAIL; i < sorted.length; i++) keep.add(i)
    sorted.forEach((r, i) => {
      if (colourOf(r.group)) {
        for (let d = -NEIGHBOURS; d <= NEIGHBOURS; d++) {
          const j = i + d
          if (j >= 0 && j < sorted.length) keep.add(j)
        }
      }
    })
  }

  // Rows plus gap markers, in rank order.
  const display = []
  let hidden = 0
  sorted.forEach((r, i) => {
    if (keep.has(i)) {
      if (hidden > 0) { display.push({ gap: hidden }); hidden = 0 }
      display.push({ r, i })
    } else hidden += 1
  })
  if (hidden > 0) display.push({ gap: hidden })

  return (
    <div>
      {display.map((d) => d.gap ? (
        <button key={`gap-after-${display.indexOf(d)}`} type="button"
                onClick={() => setShowAll(true)}
                className="w-full py-[5px] pl-1 grid grid-cols-[24px_1fr] gap-2 items-center
                           bg-transparent border-0 cursor-pointer text-left
                           text-[10px] font-mono text-[var(--color-text-muted)]
                           hover:text-[var(--color-text)]">
          <span className="text-right">⋮</span>
          <span>{d.gap} more — show</span>
        </button>
      ) : (() => {
        const { r, i } = d
        const v = r._value
        const pos = v > 0
        const frac = Math.min(1, Math.abs(v) / scale)
        const colour = colourOf(r.group)
        const blocked = atLimit && !colour
        // With a selection active, unselected rows become ghosts: a faint
        // name and a faint bar, their numbers surfacing only on hover. The
        // bar alone is still an honest mark — the shared axis carries scale —
        // and the numbers are one hover away, not gone.
        const ghost = dim && !colour
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
               className={`group grid grid-cols-[24px_minmax(126px,206px)_1fr_66px_18px]
                          gap-2 items-center py-[3px] pl-1 transition-opacity
                          outline-none focus-visible:ring-1
                          focus-visible:ring-[var(--color-text-muted)]
                          hover:bg-[var(--color-hover-bg)] hover:opacity-100
                          ${ghost ? 'opacity-30' : ''}`}>
            <span className={`text-[10px] font-mono tabular-nums text-right
                             text-[var(--color-text-muted)]
                             ${ghost ? 'opacity-0 group-hover:opacity-100' : ''}`}>{i + 1}</span>
            {/* the denominator moved off the surface into the tooltip — one
                hover away, same as a ghost row's numbers, not deleted */}
            <span className="text-[12.5px] truncate"
                  style={colour ? { color: colour, fontWeight: 600 } : undefined}
                  title={`${r.members} member${r.members === 1 ? '' : 's'}${r.tickers?.length ? ' · ' + r.tickers.join(' · ') : ''}`}>
              {r.group}
            </span>
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
            <span className={`text-[12.5px] font-mono tabular-nums text-right
                              ${ghost ? 'opacity-0 group-hover:opacity-100' : ''}`}>
              {v > 0 ? '+' : ''}{(v * 100).toFixed(1)}%
            </span>
            <span aria-hidden
                  className={`text-[12.5px] text-center text-[var(--color-text-muted)]
                              ${blocked ? 'invisible'
                                        : 'opacity-0 group-hover:opacity-100'}`}>
              {colour ? '−' : '+'}
            </span>
          </div>
        )
      })())}
      {showAll && sorted.length > HEAD + TAIL + 4 && (
        <button type="button" onClick={() => setShowAll(false)}
                className="w-full py-[6px] pl-1 grid grid-cols-[24px_1fr] gap-2
                           bg-transparent border-0 cursor-pointer text-left
                           text-[10px] font-mono text-[var(--color-text-muted)]
                           hover:text-[var(--color-text)]">
          <span className="text-right">⌃</span>
          <span>show fewer</span>
        </button>
      )}
    </div>
  )
}
