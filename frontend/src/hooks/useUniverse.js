import { useState, useEffect, useMemo } from 'react'

const BASE = '/data/output'

/**
 * The universe, in two shapes, because a list and a lookup want different ones.
 *
 * Andy 2026-08-17: names he cannot trade should not appear in results at all —
 * he will not buy a $200M shell on $400k of volume however well it scores. So
 * every RESULTS surface reads `universe`, which is the tradeable subset.
 *
 * "Results" means the Screener and the watchlist — the surfaces that answer
 * "what should I look at". The other three callers are not that, and all read
 * `all`: the ticker page and the portfolio overview LOOK UP a symbol he named
 * or already owns (a position that has fallen under the floor must not become
 * un-lookable), and the theme member panel DESCRIBES what a theme is made of —
 * it counts members it cannot find as missing, so filtering there would report
 * a theme's untradeable constituents as gone.
 *
 * `tradeable` is the pipeline's own column (cap >= $1B and >= $2M daily dollar
 * volume; DATA_CONTRACTS §4.5). It is deliberately NOT re-derived here: the
 * frontend computing its own version of a pipeline definition is how the site
 * ended up with two Watchlists and two EMA21 screens.
 *
 * Until that column ships, `gated` is false and `universe` is everything — a
 * filter that cannot run must not pretend it ran. The Screener says so out
 * loud rather than letting the reader assume a gate is in force.
 */
export function useUniverse() {
  const [all, setAll] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${BASE}/universe.json`)
      .then((res) => res.json())
      .then((data) => {
        setAll(data.rows || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const { universe, gated, dropped } = useMemo(() => {
    if (!all) return { universe: all, gated: false, dropped: 0 }
    const has = all.some((r) => typeof r.tradeable === 'boolean')
    if (!has) return { universe: all, gated: false, dropped: 0 }
    const keep = all.filter((r) => r.tradeable)
    return { universe: keep, gated: true, dropped: all.length - keep.length }
  }, [all])

  return { universe, all, loading, gated, dropped }
}
