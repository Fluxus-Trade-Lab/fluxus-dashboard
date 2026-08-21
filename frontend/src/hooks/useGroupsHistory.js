import { useEffect, useState } from 'react'

// Module-level cache — the path chart and the ribbon both want this file.
let cache = null
let inflight = null

/**
 * One row per group per session, as it was published that day.
 *
 * A theme has no price history. It is a cross-sectional aggregate of a column
 * that `universe.json` overwrites every session, so yesterday's median is
 * simply gone — `pipeline/themes/group_history.py` says exactly this, and picks
 * the only honest way out: store one row per group per session from here on.
 * That started 2026-08-07 and needs ten weeks before it can draw what a
 * ten-week chart draws.
 *
 * So this file is EXPECTED to be short, and every surface reading it prints how
 * many sessions it holds against how many it wants. A partial series drawn
 * without its denominator is a claim about ten weeks made off ten days.
 *
 * `data/history/` is not served — Vercel copies only `data/output` — so this is
 * the pipeline's published projection of that archive, not the archive itself.
 */
const TARGET_SESSIONS = 50   // ten weeks, the depth the ribbon was designed for

export function useGroupsHistory() {
  const [state, setState] = useState({ data: cache, loading: !cache, failed: false })

  useEffect(() => {
    let dead = false
    if (cache) return () => { dead = true }
    if (!inflight) {
      inflight = fetch('/data/output/groups_history.json')
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

  const n = state.data?.sessions ?? state.data?.dates?.length ?? 0
  return { ...state, sessions: n, target: state.data?.target_sessions ?? TARGET_SESSIONS }
}
