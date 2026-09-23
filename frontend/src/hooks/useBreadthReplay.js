import { useEffect, useState } from 'react'

let cache = null
let inflight = null

/**
 * breadth_replay.json as a flat, date-ordered row list — the same file the
 * Time Machine loads, fetched once per session. It is the only served file
 * with the whole archive (590 sessions from 2024-05-15), which the index-over-
 * breadth panes need for a 252-session σ ruler; breadth.json's 100 rows are
 * the fallback while it loads. DATA ALEX is asked for a slim daily file
 * (T-0923 task); until then this is ~1.4MB once.
 */
export function useBreadthReplay() {
  const [state, setState] = useState({ rows: cache, loading: !cache, failed: false })

  useEffect(() => {
    let dead = false
    if (cache) return () => { dead = true }
    if (!inflight) {
      inflight = fetch('/data/output/breadth_replay.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => {
          if (!j?.dates || !j?.rows) return null
          cache = j.dates.map((d) => j.rows[d]).filter(Boolean)
          return cache
        })
        .catch(() => null)
        .finally(() => { inflight = null })
    }
    inflight.then((rows) => { if (!dead) setState({ rows, loading: false, failed: !rows }) })
    return () => { dead = true }
  }, [])

  return state
}

export function resetBreadthReplayCache() { cache = null; inflight = null }
