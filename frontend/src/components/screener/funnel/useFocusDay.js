import { useEffect, useState } from 'react'

/**
 * Where the daily focus-notes file lives: this app's own public folder.
 *
 * DATA ALEX, 2026-10-01 (DATA_CONTRACTS §七, T-1001-06): data/output/ keeps a
 * single writer, so the daily run writes frontend/public/data/focus.json and
 * a commit touching it redeploys the site (about ten minutes after the run).
 * The per-day archive stays in data/research/screener_redesign/focus/.
 */
export const FOCUS_URL = '/data/focus.json'

export function useFocusDay() {
  const [state, setState] = useState({ doc: null, status: 'loading' })
  useEffect(() => {
    let dead = false
    fetch(`${import.meta.env.BASE_URL}data/focus.json`, { cache: 'no-cache' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((doc) => { if (!dead) setState({ doc, status: 'ok' }) })
      .catch(() => { if (!dead) setState({ doc: null, status: 'missing' }) })
    return () => { dead = true }
  }, [])
  return state
}
