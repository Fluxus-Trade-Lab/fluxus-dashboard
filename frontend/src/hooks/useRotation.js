import { useState, useEffect } from 'react'

const BASE = '/data/output'

/**
 * Style rotation — the risk-on / risk-off read.
 *
 * Deliberately separate from `useBreadth`: rotation is built from ETF bars on
 * their own cadence, so a stale or missing rotation.json must cost the Market
 * State page one panel and never its verdict.
 */
export function useRotation() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetch(`${BASE}/rotation.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`rotation.json ${res.status}`)
        return res.json()
      })
      .then((json) => {
        if (cancelled) return
        setData(json)
        setLoading(false)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err)
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  return { rotation: data, loading, error }
}
