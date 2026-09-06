/**
 * How wide the dot strips are and how their labels behave.
 *
 * The strip is 370 user units wide because that is roughly the pixel width one
 * of three columns gets on a laptop — so a 13-unit label renders at about 13px,
 * the size Andy asked for (2026-09-06). The axis sits at 29% of the width,
 * after 21% and 25% (same day).
 *
 * That leaves 213 units for the label, and two of our thirty names do not fit:
 * "Physical AI & Humanoid Robotics +10.0%" measures 244 at 13px. The old layout
 * would have cut it mid-word the first day that theme reached the top five.
 * Rather than shrink every label for the sake of two, a label that overruns is
 * condensed into the room available (`textLength`) — exact, applied only where
 * it is needed, and never a cut word.
 */
export const STRIP_W = 370
export const STRIP_H = 620
export const STRIP_PAD = { t: 46, b: 20 }
export const STRIP_X0 = 107
export const LABEL_DX = 44
export const LABEL_FS = 13
export const LABEL_ROOM = STRIP_W - STRIP_X0 - LABEL_DX - 6

/** the width to condense a label to, or undefined when it already fits */
export function squeezeTo(width, room = LABEL_ROOM) {
  return Number.isFinite(width) && width > room ? room : undefined
}

/**
 * Width of a string in the app's own face, in user units.
 *
 * Measured with a canvas so it is exact for the font actually loaded; where
 * there is no canvas (tests, a server render) a per-character estimate stands
 * in. Either way `textLength` does the condensing exactly, so a bad estimate
 * costs a label that condenses when it did not have to — never a cut word.
 */
const measured = new Map()
let ctx = null
export function textWidth(s, size = LABEL_FS) {
  const key = `${size}:${s}`
  if (measured.has(key)) return measured.get(key)
  let w = s.length * size * 0.52
  try {
    ctx = ctx || document.createElement('canvas').getContext('2d')
    ctx.font = `${size}px ${getComputedStyle(document.body).fontFamily}`
    const m = ctx.measureText(s).width
    if (m > 0) w = m
  } catch { /* no canvas: the estimate stands */ }
  measured.set(key, w)
  return w
}
