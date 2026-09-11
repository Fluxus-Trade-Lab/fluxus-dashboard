import { useEffect, useState } from 'react'

let cache = null
let inflight = null

/**
 * market_light.json — the course's morning read (Lessons 6, 6B, 7), produced
 * by DATA ALEX on Studio Q's ruling (docs/plans/2026-09-11-market-state-by-
 * the-course.md §五, DATA_CONTRACTS §七 e5546418). Read-only here.
 *
 * Shape the page reads — every field optional; an absent block renders as
 * "not measured", never as a zero:
 *
 *   date
 *   ma_type                 'EMA' | 'SMA'   (a parameter until Andy rules — NEEDS_ANDY gap 1)
 *   spy / qqq:
 *     checks: [{ key: 'fast_above_slow'|'fast_rising'|'slow_rising', pass, a, b }]
 *     checks_passed         0–3
 *     light                 'green' | 'red'   (anything short of 3/3 is red — L6:183)
 *     plus_n                consecutive closes vs the 21-day, ≤4-day noise runs dropped
 *     gear: { n, label }    Lesson 6B.2's seven gears
 *     history: [{ date, close, fast, slow, checks_passed }]
 *   brightness:
 *     setups: { count }     Q1 — names with a playbook today
 *     leaders: [{ ticker, theme, status: 'holding'|'extending'|'basing'|'broken' }]   Q2
 *   verdict                 'full' | 'dim' | 'avoid'
 */
export function useMarketLight() {
  const [state, setState] = useState({ data: cache, loading: !cache })

  useEffect(() => {
    let dead = false
    if (cache) return () => { dead = true }
    if (!inflight) {
      inflight = fetch('/data/output/market_light.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => { cache = j; return j })
        .catch(() => null)
        .finally(() => { inflight = null })
    }
    inflight.then((j) => { if (!dead) setState({ data: j, loading: false }) })
    return () => { dead = true }
  }, [])

  return state
}

/** Tests only: the module cache outlives one render, so two tests feeding two
 *  different files would otherwise see the first one's. */
export function resetMarketLightCache() { cache = null; inflight = null }
