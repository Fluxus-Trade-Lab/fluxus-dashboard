import { useEffect, useState } from 'react'

/**
 * The recap's cross-asset sentences. The local claire-recap-sidecar run writes
 * frontend/public/data/recap_cross.json after the recap ships (~10:45 JST);
 * a commit touching it redeploys the site. Missing file → no notes, no error.
 */
export function useRecapCross() {
  const [doc, setDoc] = useState(null)
  useEffect(() => {
    let dead = false
    fetch(`${import.meta.env.BASE_URL}data/recap_cross.json`, { cache: 'no-cache' })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (!dead) setDoc(d) })
      .catch(() => {})
    return () => { dead = true }
  }, [])
  return doc
}
