import { useEffect, useState } from 'react'

// Module-level cache — the Terrain card and the Flux card both read this file.
let cache = null
let inflight = null

/**
 * The five-rung theme ladder (`pipeline/themes/short_window.py`), published
 * nightly as `theme_ladder.json`.
 *
 * `history['2w']` is the two-week board's four-state counts by session — the
 * reading TSF's "Current Leadership" makes (brief §18.20: 60% name-for-name,
 * 89% on the strong/weak axis, on 2026-09-02). `series[name].rel` is each
 * group's equal-weight basket over the benchmark on `series_dates`, the input
 * of the Flux line; `series[name].states_2w` the same group's two-week state
 * on `history['2w'].dates`. Both fields arrive with the first nightly run
 * after the pipeline change ships — until then the page says so instead of
 * drawing something else.
 */
export function useThemeLadder() {
  const [state, setState] = useState({ data: cache, loading: !cache, failed: false })

  useEffect(() => {
    let dead = false
    if (cache) return () => { dead = true }
    if (!inflight) {
      inflight = fetch('/data/output/theme_ladder.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => { cache = j; return j })
        .catch(() => null)
        .finally(() => { inflight = null })
    }
    inflight.then((j) => {
      if (dead) return
      setState({ data: j, loading: false, failed: !j })
    })
    return () => { dead = true }
  }, [])

  return state
}
