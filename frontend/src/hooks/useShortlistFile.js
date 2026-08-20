import { useState, useEffect } from 'react'

// Module-level cache — the tab and the rail count both want this file.
let cache = null
let inflight = null

/**
 * shortlist.json, fetched once per session.
 *
 * NOT `useShortlist` — that name was taken, by the tray's store, and this file
 * spent fifteen minutes wearing it. Same word, two different things: the tray
 * holds the names YOU picked this morning and lives in localStorage; this
 * holds the six seats the engine picked overnight and lives in a file. The
 * build does not type-check and no test covered the tray, so the only symptom
 * was a tray that had quietly stopped having an `add`.
 *
 * Six seats, each a QUESTION, and a card per name carrying everything needed
 * to draw it — series, signal marks, readings, and a verdict sentence the
 * engine composed from a fixed template. The page computes nothing about the
 * market; that is the contract (DATA_CONTRACTS §四点十).
 *
 * `failed` is kept apart from `data === null`: the file not existing yet and
 * the fetch dying are different states, and a page that shows the same empty
 * frame for both is lying about one of them.
 */
export function useShortlistFile() {
  const [data, setData] = useState(cache)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    if (cache) return () => { cancelled = true }
    if (!inflight) {
      inflight = fetch('/data/output/shortlist.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => { cache = j; return j })
        .catch(() => null)
        .finally(() => { inflight = null })
    }
    inflight.then((j) => {
      if (cancelled) return
      if (j) setData(j)
      else setFailed(true)
    })
    return () => { cancelled = true }
  }, [])

  return { data, failed }
}
