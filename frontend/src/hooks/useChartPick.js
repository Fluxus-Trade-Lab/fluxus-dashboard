import { useCallback, useEffect, useState } from 'react'
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
 * A STORED PICK THAT FELL OFF THE SCREEN IS NOT SILENTLY KEPT. Yesterday's
 * name may not qualify today, and quietly charting it would make a dropped
 * name look like a current one. The hook reports `stale` so the card can say
 * so, and shows the default instead.
 */
export function useChartPick() {
  const { data } = useWatchlist()
  const [pick, setPick] = useState(() => {
    try { return localStorage.getItem(KEY) || null } catch { return null }
  })

  useEffect(() => {
    try {
      if (pick) localStorage.setItem(KEY, pick)
      else localStorage.removeItem(KEY)
    } catch { /* private mode — the pick just does not survive the reload */ }
  }, [pick])

  const panel = data?.zones
    ?.find((z) => z.key === 'leaders')
    ?.panels?.find((p) => p.key === 'true_market_leaders') ?? null

  const names = panel?.measured ? (panel.tickers ?? []) : []
  const fallback = names[0]?.ticker ?? null
  const onScreen = pick != null && names.some((n) => n.ticker === pick)
  const symbol = onScreen ? pick : fallback

  return {
    /** the symbol the chart should draw, or null when the panel is unmeasured */
    symbol,
    /** true while nothing has been picked — the card says so rather than implying a choice */
    isDefault: !onScreen,
    /** a pick that no longer qualifies for the screen; the card names it */
    stale: pick != null && !onScreen ? pick : null,
    /** today's screen, in the file's own order */
    names,
    panel,
    pick: useCallback((t) => setPick((cur) => (cur === t ? null : t)), []),
    clear: useCallback(() => setPick(null), []),
  }
}
