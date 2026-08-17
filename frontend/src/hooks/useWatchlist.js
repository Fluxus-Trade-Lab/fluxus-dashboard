import { useState, useEffect } from 'react'

// Module-level cache — the page and the rail badge both want this file.
let cache = null
let inflight = null

/**
 * watchlist.json, fetched once per session.
 *
 * The nightly job writes six zones, each a QUESTION, each holding panels with
 * the recipe that produced them. Note `measured` on every panel: a panel that
 * has not been measured is not a panel that found nothing, and the page has to
 * keep the two apart.
 */
export function useWatchlist() {
  const [data, setData] = useState(cache)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    if (cache) return () => { cancelled = true }
    if (!inflight) {
      inflight = fetch('/data/output/watchlist.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => { cache = j; return j })
        .catch(() => null)
        .finally(() => { inflight = null })
    }
    inflight.then((j) => {
      if (cancelled) return
      setData(j)
      if (!j) setFailed(true)
    })
    return () => { cancelled = true }
  }, [])

  return { data, failed }
}
