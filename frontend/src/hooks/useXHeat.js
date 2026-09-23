import { useState, useEffect } from 'react'

// Module-level cache: same shape as useTickerEvents — one fetch per session,
// shared across every ticker page visited.
let cache = null
let inflight = null

/**
 * data/output/x_heat.json: how many distinct X accounts mentioned this
 * ticker in the trailing window (DATA_CONTRACTS §七 2026-09-23). Returns the
 * whole file (`window`, `rows`, ...) so callers can look up their own symbol
 * and read the file's own window dates instead of recomputing "7 days ago".
 */
export function useXHeat() {
  const [xHeat, setXHeat] = useState(cache)
  const [loading, setLoading] = useState(!cache)

  useEffect(() => {
    let cancelled = false

    if (cache) {
      setXHeat(cache)
      setLoading(false)
      return () => { cancelled = true }
    }

    if (!inflight) {
      inflight = fetch('/data/output/x_heat.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((json) => { cache = json; return json })
        .catch(() => { cache = null; return null })
        .finally(() => { inflight = null })
    }
    inflight.then((json) => {
      if (cancelled) return
      setXHeat(json)
      setLoading(false)
    })

    return () => { cancelled = true }
  }, [])

  return { xHeat, loading }
}
