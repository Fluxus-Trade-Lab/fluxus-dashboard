import { useState, useEffect } from 'react'

// Module-level cache: ticker_events.json is large, fetch it at most once
// per session no matter how many ticker pages are visited.
let cache = null
let inflight = null

export function useTickerEvents(symbol) {
  const [events, setEvents] = useState(() => (cache ? cache.events?.[symbol] ?? [] : null))
  const [loading, setLoading] = useState(!cache)

  useEffect(() => {
    let cancelled = false

    const apply = (data) => {
      if (cancelled) return
      setEvents(data?.events?.[symbol] ?? [])
      setLoading(false)
    }

    if (cache) {
      apply(cache)
      return () => { cancelled = true }
    }

    if (!inflight) {
      inflight = fetch('/data/output/ticker_events.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((json) => { cache = json; return json })
        .catch(() => { cache = null; return null })
        .finally(() => { inflight = null })
    }
    inflight.then(apply)

    return () => { cancelled = true }
  }, [symbol])

  return { events: events ?? [], loading }
}
