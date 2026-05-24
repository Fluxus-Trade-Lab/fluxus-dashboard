import { useState, useEffect } from 'react'

const INDEX_URL = '/data/output/trades/_index.json'

/**
 * Fetch the trade journal index — summary row per trade for the
 * journal table. Each entry: { trade_id, ticker, direction, entry_date,
 * exit_date, closed, realized_R, optimal_R, capture_pct, setup_type,
 * lesson, hold_days }.
 */
export function useTradeJournal() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(INDEX_URL)
      .then(res => res.ok ? res.json() : null)
      .then(j => { setData(j); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return { trades: data?.trades || [], loading, generatedAt: data?.generated_at }
}

/**
 * Fetch a single trade's post-mortem record (full detail).
 */
export function useTradePostmortem(tradeId) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!tradeId) { setLoading(false); return }
    setLoading(true); setError(null)
    fetch(`/data/output/trades/${tradeId}.json`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(j => { setData(j); setLoading(false) })
      .catch(e => { setError(e); setLoading(false) })
  }, [tradeId])

  return { data, loading, error }
}
