import { useState, useEffect, useCallback } from 'react'

const BASE = '/data/output'

const FILES = [
  'signals',
  'etf_data',
  'momentum_97',
  'gainers_4pct',
  'vol_up_gainers',
  'ema21_watch',
  'healthy_charts',
  'vcp',
  'stockbee_ratio',
  'breadth',
]

export function useMarketData() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  const fetchData = useCallback(async () => {
    try {
      const results = await Promise.all(
        FILES.map(async (name) => {
          const res = await fetch(`${BASE}/${name}.json`)
          if (!res.ok) throw new Error(`Failed to fetch ${name}`)
          const json = await res.json()
          // etf_data.json wraps its rows behind `as_of` so the file's own
          // freshness date is checkable (T-0926-56); unwrap here so the rest
          // of the app keeps reading a bare array, same as before.
          return [name, name === 'etf_data' ? (json.data ?? []) : json]
        })
      )
      const obj = Object.fromEntries(results)

      // The two EP screeners (split by author 2026-09-18, replacing the retired
      // episodic_pivot.json). Optional: a missing file is "not arrived" (null),
      // never a reason to fail the whole page.
      for (const name of ['ep_stockbee', 'ep_qullamaggie']) {
        try {
          const r = await fetch(`${BASE}/${name}.json`)
          obj[name] = r.ok ? await r.json() : null
        } catch {
          obj[name] = null
        }
      }

      // market_health is optional — tolerate absence (pipeline may not have shipped it yet)
      try {
        const mh = await fetch(`${BASE}/market_health.json`)
        obj.market_health = mh.ok ? await mh.json() : null
      } catch {
        obj.market_health = null
      }

      // etf_data is an array, rest have timestamp
      const timestamp = obj.signals?.timestamp || null
      setData(obj)
      setLastUpdated(timestamp)
      setLoading(false)
    } catch (err) {
      console.error('Failed to load market data:', err)
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()

    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000)

    const handleOnline = () => setIsOffline(false)
    const handleOffline = () => setIsOffline(true)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      clearInterval(interval)
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [fetchData])

  return { data, loading, lastUpdated, isOffline }
}
