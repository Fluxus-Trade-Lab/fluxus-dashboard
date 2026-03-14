import { useState, useEffect } from 'react'

const BASE = '/data/output'

export function useUniverse() {
  const [universe, setUniverse] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${BASE}/universe.json`)
      .then(res => res.json())
      .then(data => {
        setUniverse(data.rows || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  return { universe, loading }
}
