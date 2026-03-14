import { useState, useEffect } from 'react'

export function useHash() {
  const [hash, setHash] = useState(window.location.hash || '#/dashboard')

  useEffect(() => {
    const onHashChange = () => setHash(window.location.hash || '#/dashboard')
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const navigate = (newHash) => {
    window.location.hash = newHash
  }

  return [hash, navigate]
}
