import { useCallback, useSyncExternalStore } from 'react'
import { useWatchlist } from './useWatchlist'

const KEY = 'page3-chart-pick'

/**
 * Which name the fixed chart on page 3 is showing.
 *
 * THE DEFAULT IS A SCREEN, NOT A FAVOURITE. Andy, 2026-08-18: the chart card
 * is fixed — it never moves and it is never an empty frame — and it opens on
 * the first name out of one named screen. The screen is TRUE MARKET LEADERS:
 * a liquid leader whose home theme or industry is itself Leading, with RS 1M
 * at or above 80. It is the one panel in the file whose recipe already answers
 * the question page 3 exists to answer — is this name moving alone, or is the
 * whole water moving — so the chart opens on the strongest name for which the
 * answer is "the water".
 *
 * ORDER IS THE FILE'S, NOT OURS. The panel arrives sorted by hybrid RS and the
 * first row is taken as the first row. Re-sorting here to pick a "better"
 * default would be this page inventing a ranking the pipeline did not ship.
 *
 * ONE STORE, NOT ONE PER CALLER. It began as a plain useState hook, which was
 * fine while the chart card was its only reader and wrong the moment the
 * Screener's table started charting a name on click: the table set its own
 * copy, the card kept drawing the old symbol, and clicking a row appeared to
 * do nothing. This is the second time that exact shape has bitten in this
 * round — the shortlist did it first — so it is worth naming plainly. Two
 * components holding two states over one fact is the defect this codebase
 * chases out of its colour encodings, and localStorage is the persistence,
 * never the channel between two live components.
 *
 * A PICK IS ANY SYMBOL, NOT A MEMBER OF THE SCREEN. This started life gating
 * the pick on membership of True Market Leaders, which was harmless while the
 * chip strip was the only way to choose and became a real bug the moment the
 * Screener's table started charting a row on click: most names in that table
 * are not among the 27, so the pick was accepted, stored, and then silently
 * discarded in favour of the default. Clicking a row looked like it did
 * nothing. The screen decides the DEFAULT; it does not decide what you are
 * allowed to look at.
 */
function read() {
  try { return localStorage.getItem(KEY) || null } catch { return null }
}

let snapshot = read()
const subs = new Set()

function commit(next) {
  snapshot = next
  try {
    if (next) localStorage.setItem(KEY, next)
    else localStorage.removeItem(KEY)
  } catch { /* private mode — the pick just does not survive the reload */ }
  subs.forEach((fn) => fn())
}

const subscribe = (fn) => { subs.add(fn); return () => subs.delete(fn) }
const getSnapshot = () => snapshot
const getServerSnapshot = () => null

export function useChartPick() {
  const { data } = useWatchlist()
  const pick = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)

  const panel = data?.zones
    ?.find((z) => z.key === 'leaders')
    ?.panels?.find((p) => p.key === 'true_market_leaders') ?? null

  const names = panel?.measured ? (panel.tickers ?? []) : []
  const fallback = names[0]?.ticker ?? null
  const symbol = pick ?? fallback

  return {
    /** the symbol the chart should draw, or null when nothing is picked and the panel is unmeasured */
    symbol,
    /** true while nothing has been picked — the card says so rather than implying a choice */
    isDefault: !pick,
    /** today's screen, in the file's own order */
    names,
    panel,
    pick: useCallback((t) => commit(snapshot === t ? null : t), []),
    clear: useCallback(() => commit(null), []),
  }
}
