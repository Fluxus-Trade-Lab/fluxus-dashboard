import { useState, useEffect } from 'react'

// Module-level cache: the ledger and the page-level reading both want this
// file, and they should not fetch it twice.
let cache = null
let inflight = null

/** heating_up.json, fetched once per session. */
export function useHeatingUp() {
  const [data, setData] = useState(cache)

  useEffect(() => {
    let cancelled = false
    if (cache) return () => { cancelled = true }
    if (!inflight) {
      inflight = fetch('/data/output/heating_up.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => { cache = j; return j })
        .catch(() => null)
        .finally(() => { inflight = null })
    }
    inflight.then((j) => { if (!cancelled) setData(j) })
    return () => { cancelled = true }
  }, [])

  return data
}
