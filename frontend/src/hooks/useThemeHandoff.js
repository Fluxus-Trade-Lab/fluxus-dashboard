import { useEffect, useRef, useState } from 'react'
import { MAX_COMPARE } from '../components/groups/useThemeCompare'

const PICKS_KEY = 'themes-compare'
const SEEN_KEY = 'screener-handoff-seen'

/** The Themes page's current comparison picks, read from where that page keeps them. */
function readPicks() {
  try {
    const raw = JSON.parse(localStorage.getItem(PICKS_KEY) ?? '[]')
    if (!Array.isArray(raw)) return []
    return raw.slice(0, MAX_COMPARE)
      .map((p) => (p && typeof p === 'object' ? p.name : null))
      .filter((n) => typeof n === 'string' && n)
  } catch {
    return []
  }
}

const sign = (names) => [...names].sort().join('|')

/**
 * Carrying the Themes page's picks into the Screener's theme filter.
 *
 * ONE DIRECTION, ONE DESTINATION. Themes → Screener, and no further. The
 * measurement behind that: narrowing this table to three picked themes takes
 * it from 2,548 rows to 42; doing the same to Today's List takes 277 names to
 * 5 and empties twelve of its seventeen scans. A page built on "the six
 * questions were already asked" cannot answer them with the filter's zero.
 *
 * APPLIED ONCE PER PICK-SET, NEVER RE-APPLIED. The signature of the set that
 * was last handed over is remembered, so clearing the filter here does not
 * start a fight with the other page: the same picks will not come back. Change
 * the picks next door and the new set arrives, because that is a fresh
 * decision rather than the one already declined.
 *
 * IT ONLY EVER FILLS AN EMPTY FILTER. If a theme is already chosen here, that
 * is the reader's own hand on this page's control, and another page does not
 * get to overwrite it.
 */
export function useThemeHandoff(themes, setThemes) {
  const [from, setFrom] = useState(null)
  const applied = useRef(false)

  useEffect(() => {
    if (applied.current) return
    applied.current = true

    const picks = readPicks()
    if (!picks.length) return
    const sig = sign(picks)
    let seen = null
    try { seen = localStorage.getItem(SEEN_KEY) } catch { /* storage off */ }
    if (seen === sig) return
    try { localStorage.setItem(SEEN_KEY, sig) } catch { /* storage off */ }

    // a filter already set by hand on this page outranks the other page's
    if (themes.size) return

    setThemes(new Set(picks))
    setFrom(picks)
  }, [themes, setThemes])

  /** the picks this visit inherited, so the bar can say where they came from */
  return from && [...themes].length && sign(themes) === sign(from) ? from : null
}
