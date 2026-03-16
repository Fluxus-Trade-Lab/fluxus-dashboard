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
  'episodic_pivot',
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
          return [name, await res.json()]
        })
      )
      const obj = Object.fromEntries(results)

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
