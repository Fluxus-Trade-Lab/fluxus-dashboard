import { useState, useEffect } from 'react'

const BASE = '/data/output'

/**
 * Industry + theme group layer.
 *
 * Themes carry a `publish` flag set by the pipeline: it is true only when the
 * market agrees the members co-move (validated), when the theme is a single
 * fund whose reading is exact by construction, or when it is a factor grouping
 * that never claimed co-movement. Provisional themes are returned separately
 * rather than filtered out here, so the page can show that they exist and why
 * they are being withheld — silently dropping them would make an unproven
 * theme indistinguishable from one that was never built.
 */
export function useGroups() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetch(`${BASE}/groups.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`groups.json ${res.status}`)
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

  const themes = data?.themes ?? []
  return {
    // per-ticker RS payload (rs windows, state, cohort percentile,
    // top_quartile) — keyed by ticker, computed by rs_engine
    stocks: data?.stocks ?? {},
    date: data?.date ?? null,
    benchmark: data?.benchmark ?? 'SPY',
    industries: data?.industries ?? [],
    themes: themes.filter((t) => t.publish),
    provisional: themes.filter((t) => !t.publish),
    summary: data?.summary ?? null,
    loading,
    error,
  }
}
