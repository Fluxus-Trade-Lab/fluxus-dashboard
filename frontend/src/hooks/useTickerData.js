import { useState, useEffect } from 'react'

const BASE = '/data/output/tickers'

/**
 * Fetch per-ticker fundamentals JSON.
 * Returns { data, loading, error }. data is null if not yet fetched.
 */
export function useTickerData(symbol) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!symbol) {
      setData(null); setLoading(false); return
    }
    setLoading(true)
    setError(null)
    const safe = String(symbol).toUpperCase().replace(/[\/\^]/g, '_')
    fetch(`${BASE}/${safe}.json`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(j => { setData(j); setLoading(false) })
      .catch(e => {
        setData(null)
        setError(e)
        setLoading(false)
      })
  }, [symbol])

  return { data, loading, error }
}
