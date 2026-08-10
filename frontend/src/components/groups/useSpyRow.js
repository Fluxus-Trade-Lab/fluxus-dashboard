import { useEffect, useState } from 'react'

/**
 * The benchmark's own perf row, for the one window groups.json cannot answer
 * alone.
 *
 * 1W excess ships on every theme (rs_0_1w — see rs_engine: the first disjoint
 * bucket minus the benchmark's is exactly perf_1w − SPY.perf_1w), and 3M ships
 * as excess_3m. The 1M window has no precomputed excess, so the page derives
 * it with the same construction excess_3m uses — theme return minus benchmark
 * return, same window — which needs SPY's perf_1m from etf_data.json.
 *
 * Until the row arrives the 1M switch is disabled rather than approximated:
 * a zero line at the wrong height is worse than a button that waits.
 */
export function useSpyRow() {
  const [spy, setSpy] = useState(null)

  useEffect(() => {
    let dead = false
    fetch('/data/output/etf_data.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((rows) => {
        if (dead || !Array.isArray(rows)) return
        setSpy(rows.find((e) => e.ticker === 'SPY') ?? null)
      })
      .catch(() => {})
    return () => { dead = true }
  }, [])

  return spy
}
