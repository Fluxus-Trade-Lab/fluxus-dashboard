import { useState, useEffect } from 'react'

export function useHash() {
  const [hash, setHash] = useState(window.location.hash || '#/')

  useEffect(() => {
    const onHashChange = () => setHash(window.location.hash || '#/')
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  /* Changing the hash scrolls nothing: the hash names no element, so the
     browser has nothing to jump to and React keeps the scroll position it had.
     Reading the dashboard down to 681px and then clicking Themes left you 681px
     into a page you had never seen.

     Only a change of PAGE resets — the first segment. Sub-routes (`#/review/hold`,
     `#/watchlist/momentum`) are navigation WITHIN a page, and throwing the
     reader back to the top of it is the same defect wearing the other sign. */
  const navigate = (newHash) => {
    const seg = (h) => (h || '').replace(/^#\/?/, '').split('/')[0]
    const changedPage = seg(newHash) !== seg(window.location.hash)
    window.location.hash = newHash
    if (changedPage) window.scrollTo(0, 0)
  }

  return [hash, navigate]
}
