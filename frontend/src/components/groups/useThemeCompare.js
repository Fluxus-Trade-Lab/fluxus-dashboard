import { useCallback, useEffect, useState } from 'react'

/**
 * Selection state for the theme-comparison instrument: up to three themes,
 * each wearing a stable identity colour, persisted across reloads.
 *
 * THREE is a hard cap and it is a perceptual number, not a technical one.
 * Three overlaid trajectories are the most a reader can follow through a
 * crossing; TSF lands on the same limit. At the cap, every unselected target
 * shows cursor:not-allowed — the pointer itself says "full", before a dead
 * click has to.
 *
 * IDENTITY IS NO LONGER A HUE (Andy, 2026-08-24). Colour on this page grades
 * now — blue for a theme that moved to a stronger state, red for one that fell
 * out of one (see `stateChange.js`). Identity keeps the two channels it was
 * always better at and which survive a greyscale screenshot: the DASH pattern
 * and the label. What is left of the slot colour is a neutral lightness ladder
 * used for chrome — the ring around a picked dot, the rule down a picked row,
 * the chip in the compare bar — never for a data mark's fill.
 *
 * The hues did not go for taste. slot-1 measured 1.02 to one against the
 * page's own ink while its comment promised a reader could say "the blue one";
 * slot-2 and slot-3 were green and orange under a comment claiming Okabe-Ito.
 * They had been measured — against each other and against the card ground —
 * just never against the ink they shared a figure with.
 *
 * A freed slot is reused by the next pick, so the slot follows the POSITION,
 * not the theme — two sessions comparing different themes still read the same.
 */
/* Chrome only. These are neutral by design; the graded pair lives in
   `stateChange.js` and never appears here. */
export const SLOT_COLOURS = [
  'var(--color-slot-1)', 'var(--color-slot-2)', 'var(--color-slot-3)',
]

/**
 * The second channel. Three lines told apart by colour alone are one line in
 * a greyscale screenshot, and this page travels as screenshots — so the slot
 * also owns a stroke pattern, and the pattern is what survives the print.
 * Indexed the same way as the colours, so slot and dash never disagree.
 */
export const SLOT_DASHES = [null, '7 3', '2 3']

export function slotDash(colour) {
  const i = SLOT_COLOURS.indexOf(colour)
  return i >= 0 ? SLOT_DASHES[i] : null
}
export const MAX_COMPARE = SLOT_COLOURS.length

const KEY = 'themes-compare'

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? '[]')
    if (!Array.isArray(raw)) return []
    // Picks persist across sessions, and the slot colours became CSS variables
    // on 2026-08-16 — a pick saved before that carries a literal hex. Left
    // alone it would render its old colour AND leave its new slot looking
    // unused, so the next pick would get a colour already on screen. The slot
    // is the position, so reassigning by index is the whole migration.
    return raw.slice(0, MAX_COMPARE)
      .map((p, i) => (p && typeof p === 'object' && p.name
        ? { name: p.name, colour: SLOT_COLOURS[i] } : null))
      .filter(Boolean)
  } catch {
    return []
  }
}

export function useThemeCompare() {
  // [{name, colour}] in pick order; colour is the slot's, assigned on pick.
  const [picks, setPicks] = useState(load)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(picks))
  }, [picks])

  const toggle = useCallback((name) => {
    setPicks((prev) => {
      const found = prev.find((p) => p.name === name)
      if (found) return prev.filter((p) => p.name !== name)
      if (prev.length >= MAX_COMPARE) return prev  // full — the cursor already said so
      const used = new Set(prev.map((p) => p.colour))
      const colour = SLOT_COLOURS.find((c) => !used.has(c))
      return [...prev, { name, colour }]
    })
  }, [])

  const clear = useCallback(() => setPicks([]), [])

  const colourOf = useCallback(
    (name) => picks.find((p) => p.name === name)?.colour ?? null,
    [picks],
  )

  return {
    picks,
    toggle,
    clear,
    colourOf,
    atLimit: picks.length >= MAX_COMPARE,
  }
}
