/**
 * DID IT CHANGE SIDES, AND WHICH WAY — the page's one graded channel.
 *
 * Andy, 2026-08-24: colour on this page now grades. Until then colour said
 * only "which theme did you pick", and the field printed that rule on itself;
 * the trajectory work made the rule cost too much — a reader looking at eleven
 * sessions of movement could not see who had crossed into a stronger state and
 * who had fallen out of one without reading four labels. So the pair's blue
 * and red take that job, and identity moves to the channel that survives a
 * greyscale screenshot anyway: the dash pattern and the label.
 *
 * WHAT COUNTS AS A CHANGE is the state published on the first session this
 * theme was measured versus the state published on the last. Nothing in
 * between: a theme that went Lagging → Leading → Lagging reads as unchanged,
 * because over the window it is. The states are the ones stored that night —
 * `group_history.py` refuses to recompute them, and so does this.
 *
 * IT IS NOT A RETURN. Crossing into Leading says the theme's excess and
 * acceleration both turned positive; it says nothing about what it paid.
 */

/** Strongest first. Two states compare by this and nothing else. */
export const STATE_RANK = { Leading: 0, Improving: 1, Weakening: 2, Lagging: 3 }

/**
 * @param {Array<string|null>} states one entry per session, nulls for the
 *   sessions this group was not measured (it may have joined the pool late).
 * @returns {'up'|'down'|null} null when it never changed sides, or when there
 *   are fewer than two real readings to compare — which is not "no change".
 */
export function changeOf(states) {
  const got = (states ?? []).filter((s) => s != null && s in STATE_RANK)
  if (got.length < 2) return null
  const d = STATE_RANK[got[0]] - STATE_RANK[got[got.length - 1]]
  return d > 0 ? 'up' : d < 0 ? 'down' : null
}

/** The pair, and only the pair. No third hue — unchanged is ink, not a colour. */
export function changeColour(dir) {
  return dir === 'up' ? 'var(--color-took)'
    : dir === 'down' ? 'var(--color-refused)'
    : null
}

export const CHANGE_WORD = {
  up: 'moved to a stronger state',
  down: 'moved to a weaker state',
}

/**
 * Build the lookup the figures take, from `groups_history.json`'s shape.
 * Returns a plain function so a figure never has to know about the file.
 */
export function changeLookup(history) {
  const groups = history?.groups
  if (!groups) return () => null
  const cache = new Map()
  return (name) => {
    if (!cache.has(name)) cache.set(name, changeOf(groups[name]?.state))
    return cache.get(name)
  }
}
