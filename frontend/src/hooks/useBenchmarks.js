import { useState, useEffect } from 'react'

const URL = '/data/output/tickers/_benchmarks.json'

/**
 * Fetch SPY + QQQ 1y close history for the RS rebased chart.
 */
export function useBenchmarks() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(URL)
      .then(res => res.ok ? res.json() : null)
      .then(j => { setData(j); setLoading(false) })
      .catch(() => { setLoading(false) })
  }, [])

  return { data, loading }
}
