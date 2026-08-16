import { useState } from 'react'
import { QUARTER_SEGMENTS, ratePerSession, paceChange } from './segments'

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
 * 2026-08-16 — THE FIELD LAYER IS GONE. The strip above this plotted the same
 * 76 values, on the same scale, from the same props: dots where these are
 * bars. A sorted diverging chart already IS a distribution — reading its
 * extents down the page gives the shape the strip gave.
 *
 * The strip's median rule and middle-half band were carried over here for one
 * revision and then dropped at Andy's call. So the page no longer states the
 * median anywhere: that reading is gone, not relocated. Written down because
 * a thing deliberately removed and a thing forgotten look identical later.
 *
 * THE STRETCHES CAME TOO. "Where the lead was earned" was a separate section
 * showing the same themes in the same order with their quarter decomposed —
 * which made it the ranking's own head, printed twice, in a block that did not
 * follow the window the page was ranking on. It is three cells per row now.
 *
 * Uniform geometry, varying ink: same width, same height, only the density
 * changes. Andy's read on the earlier version was that bars of varying height
 * looked ragged, and he was right — height was carrying the value, so three
 * cells came out three different sizes for no reason a reader benefits from.
 *
 * And the sort follows: rank by the window, or rank by the change in pace.
 * Because the cells are per session, choosing pace puts rows at the top that
 * visibly darken left to right. The chart shows why it is sorted that way.
 *
 * Rows are selection targets (same gesture as the dots and the search). The
 * affordance is shown, not written: a + surfaces on hover at the row's end,
 * flipping to − when the row is already picked, and the not-allowed cursor
 * refuses a fourth pick before the click. Identity colour goes on the NAME
 * and a left rule only — the bar keeps the state grammar, because "which line
 * is this" must never overwrite "what state is this in".
 *
 * 2026-08-16 — MIRRORED. The zero has been centred since this was written, but
 * the name sat in a fixed left column, which pushed the axis out to about
 * two-thirds of the row: geometrically a diverging chart, visually a left-
 * aligned bar chart with a line through it. The name now sits in the half the
 * bar does not use — a theme that beats SPY grows right and is named on the
 * left, one that trails grows left and is named on the right — so the two
 * sides read as two sides, and the centre is where the eye already is.
 *
 * The fill still carries STATE, not direction. In a diverging bar the side
 * already says the sign; coloring by sign would be the same fact twice, which
 * is the rule this page applied when it took the hue off the ticker cards.
 * State is the one thing position cannot say.
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

/* Measured, not chosen: in the two-column layout the ranking came out 357px
   against the comparison's 446, and the row pitch is 25px — so four more
   rows at the head close the gap. Balanced for the DEFAULT state, folds
   closed, which is the state the page is usually looked at in. Opening a
   members table adds about 285px to the right and no static head count can
   answer both states at once. */
const HEAD = 12
const TAIL = 4
const NEIGHBOURS = 1

export default function ThemeBars({ rows, scale, colourOf, onToggle, atLimit, dim,
                                   sortKey = 'window' }) {
  const [showAll, setShowAll] = useState(false)
  const key = sortKey === 'pace' ? paceChange : (r) => r._value
  const sorted = [...rows]
    .filter((r) => Number.isFinite(r._value) && key(r) != null)
    .sort((a, b) => key(b) - key(a))
  if (!sorted.length) return null

  // One scale for every cell on screen, so a darker cell is a bigger number
  // in any row and any column.
  const legScale = sorted.reduce((m, r) =>
    QUARTER_SEGMENTS.reduce((mm, sg) => {
      const v = ratePerSession(r, sg)
      return v == null ? mm : Math.max(mm, Math.abs(v))
    }, m), 0) || 1



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
               className={`group grid grid-cols-[24px_1fr_18px]
                          sm:grid-cols-[24px_1fr_84px_18px]
                          gap-2 items-center py-[3px] pl-1 transition-opacity
                          outline-none focus-visible:ring-1
                          focus-visible:ring-[var(--color-text-muted)]
                          hover:bg-[var(--color-hover-bg)] hover:opacity-100
                          ${ghost ? 'opacity-30' : ''}`}>
            <span className={`text-[10px] font-mono tabular-nums text-right
                             text-[var(--color-text-muted)]
                             ${ghost ? 'opacity-0 group-hover:opacity-100' : ''}`}>{i + 1}</span>

            {/* One grid cell holding two stacked things, not two cells. As
                siblings the mobile name claimed a column of its own and pushed
                the whole chart into the 18px affordance column. */}
            <span className="block min-w-0">
            {/* Below sm the name rides above its bar: mirroring needs twice
                the width, because a name and a bar cannot share half a row —
                at 390px the names truncated to 71px, which is not a ranking. */}
            <span className="sm:hidden block text-[12px] truncate pb-[1px]"
                  style={colour ? { color: colour, fontWeight: 600 } : undefined}>
              {r.group}
              <span className="ml-2 font-mono tabular-nums text-[11px]
                               text-[var(--color-text-secondary)]">
                {v > 0 ? '+' : ''}{(v * 100).toFixed(1)}%
              </span>
            </span>

            {/* One field, split at the middle. Everything inside is positioned
                against that centre, so the axis is the row's spine rather than
                a line that happens to fall two-thirds along it. The gutters
                hold the value labels at a bar's far end. */}
            <span className="relative block h-[15px] mx-0 sm:mx-[68px]">
              {/* the rule overshoots the row so the segments join into one
                  continuous zero — an axis with holes is not an axis */}
              <i className="absolute top-[-3px] bottom-[-3px] left-1/2 w-px
                            bg-[var(--color-text-muted)]" />

              <i className="absolute top-[1.5px] bottom-[1.5px] rounded-[2px]" style={{
                ...barStyle(r.state),
                left: pos ? '50%' : `${50 - frac * 50}%`,
                width: `${frac * 50}%`,
              }} />

              {/* the name takes the half the bar left empty */}
              <span className={`hidden sm:block absolute top-1/2 -translate-y-1/2 text-[12.5px] truncate
                                ${pos ? 'right-[calc(50%+9px)] text-right' : 'left-[calc(50%+9px)] text-left'}`}
                    style={{ maxWidth: 'calc(50% - 12px)',
                             ...(colour ? { color: colour, fontWeight: 600 } : {}) }}
                    title={`${r.members} member${r.members === 1 ? '' : 's'}${r.tickers?.length ? ' · ' + r.tickers.join(' · ') : ''}`}>
                {r.group}
              </span>

              {/* the number rides the bar's far end, outside it */}
              <span className={`hidden sm:block absolute top-1/2 -translate-y-1/2 text-[12px] font-mono
                                tabular-nums whitespace-nowrap
                                ${ghost ? 'opacity-0 group-hover:opacity-100' : ''}`}
                    style={pos
                      ? { left: `calc(${50 + frac * 50}% + 8px)` }
                      : { right: `calc(${50 + frac * 50}% + 8px)` }}>
                {v > 0 ? '+' : ''}{(v * 100).toFixed(1)}%
              </span>
            </span>
            </span>

            {/* the quarter's three stretches, oldest at the left. Equal cells;
                only the ink moves. */}
            <span className="hidden sm:flex gap-[2px] items-center">
              {QUARTER_SEGMENTS.map((sg) => {
                const v = ratePerSession(r, sg)
                if (v == null) {
                  return <i key={sg.key} className="flex-1 h-[11px] rounded-[2px] border border-dashed"
                            style={{ borderColor: 'var(--color-untested)' }}
                            title={`${sg.label}: not measured`} />
                }
                return (
                  <i key={sg.key} className="flex-1 h-[11px] rounded-[2px]"
                     style={{ background: v > 0 ? 'var(--color-took)' : 'var(--color-refused)',
                              opacity: (0.12 + Math.min(1, Math.abs(v) / legScale) * 0.88).toFixed(2) }}
                     title={`${sg.label}: ${v > 0 ? '+' : ''}${(v * 100).toFixed(2)}% per session`
                       + ` · ${sg.sessions} sessions, ${r[sg.key] > 0 ? '+' : ''}${(r[sg.key] * 100).toFixed(1)}% over the stretch`} />
                )
              })}
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
