import { useEffect, useState } from 'react'

let cache = null
let inflight = null

/**
 * The TICK band, nightly (DATA_CONTRACTS §七, 2026-08-22).
 *
 * A timing reading, not a risk one — the pipeline's own note says so and the
 * evidence field proves it: entering the contracted band cuts the next 21 days'
 * median return roughly in half, and DROPS the probability of a 5% drawdown
 * (9.9% vs 15.4% over 17 years). Grind, not crash.
 */
export function useTickCycle() {
  const [state, setState] = useState({ data: cache, loading: !cache })

  useEffect(() => {
    let dead = false
    if (cache) return () => { dead = true }
    if (!inflight) {
      inflight = fetch('/data/output/tick_cycle.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => { cache = j; return j })
        .catch(() => null)
        .finally(() => { inflight = null })
    }
    inflight.then((j) => { if (!dead) setState({ data: j, loading: false }) })
    return () => { dead = true }
  }, [])

  return state
}
