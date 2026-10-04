import { useState, useEffect } from 'react'

// Module-level cache: the ledger and the page-level reading both want this
// file, and they should not fetch it twice.
let cache = null
let inflight = null
// true once the fetch has come back either way — lets a page tell "still
// loading" from "the file is not there" (null in both cases otherwise)
let settled = false

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
        .finally(() => { inflight = null; settled = true })
    }
    inflight.then((j) => { if (!cancelled) setData(j) })
    return () => { cancelled = true }
  }, [])

  return data
}

/** The same file, plus whether the fetch has finished: { data, settled }. */
export function useHeatingUpState() {
  const data = useHeatingUp()
  const [done, setDone] = useState(settled)
  useEffect(() => {
    if (done) return
    let cancelled = false
    const tick = () => {
      if (cancelled) return
      if (settled) setDone(true)
      else setTimeout(tick, 50)
    }
    tick()
    return () => { cancelled = true }
  }, [done])
  return { data, settled: done || Boolean(data) }
}
