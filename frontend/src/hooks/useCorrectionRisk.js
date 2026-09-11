import { useEffect, useState } from 'react'

let cache = null
let inflight = null

/**
 * correction_risk.json, fetched once per session — RND Linda's file, written
 * nightly by pipeline/risk/correction_risk.py. Read-only here: which fields may
 * appear and how is her ruling (DATA_CONTRACTS §七, 2026-09-11), not ours.
 */
export function useCorrectionRisk() {
  const [state, setState] = useState({ data: cache, loading: !cache })

  useEffect(() => {
    let dead = false
    if (cache) return () => { dead = true }
    if (!inflight) {
      inflight = fetch('/data/output/correction_risk.json')
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
