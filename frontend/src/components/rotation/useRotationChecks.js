import { useCallback, useEffect, useState } from 'react'

/**
 * The verify / watch checks under Compare, kept per session date.
 *
 * F3 (Andy 2026-09-02): the checks are the funnel's only quality measure —
 * a hit rate needs a record of what was looked at. This browser is the record
 * for now: `fluxus-rotation-checks:<date>` in localStorage, one entry per
 * theme, exportable as JSON so the archive can take it. A server-side store is
 * a §七 ask, not something the page can grant itself.
 */
const key = (date) => `fluxus-rotation-checks:${date ?? 'unknown'}`

function load(date) {
  try { return JSON.parse(localStorage.getItem(key(date)) || '{}') } catch { return {} }
}

export function useRotationChecks(date) {
  const [checks, setChecks] = useState(() => load(date))
  useEffect(() => { setChecks(load(date)) }, [date])

  const toggle = useCallback((theme, field, list) => {
    setChecks((prev) => {
      const cur = prev[theme] ?? { verified: false, watch: false }
      const next = { ...prev, [theme]: { ...cur, [field]: !cur[field], list: list ?? cur.list ?? '', updatedAt: new Date().toISOString() } }
      try { localStorage.setItem(key(date), JSON.stringify(next)) } catch { /* storage may be unavailable; the checks still live in memory */ }
      return next
    })
  }, [date])

  const exportJson = useCallback(() => JSON.stringify({ date, checks }, null, 2), [date, checks])

  const verified = Object.values(checks).filter((c) => c.verified).length
  const watched = Object.values(checks).filter((c) => c.watch).length
  return { checks, toggle, exportJson, verified, watched }
}
