import { useMemo } from 'react'
import Squares from '../Squares'
import { barStyle } from './ThemeBars'
import { useUniverse } from '../../hooks/useUniverse'

/**
 * The stocks inside one chosen theme, on the screener's own measurements.
 *
 * A theme's bar is an average, and an average is a claim about a set you
 * cannot see. This is the set. Nothing here is computed for this view —
 * every column already existed in universe.json or groups.json and had never
 * been put next to the theme it belongs to.
 *
 * LAZY BY MOUNT. universe.json is 5,615 rows; it is fetched the first time a
 * members panel actually opens, not when the page loads. The browser cache
 * makes the second panel free.
 *
 * `top_quartile` squares are the same construction as TSF's «6/6»: the count
 * of windows on which a stock sat in the top 25% of its own cohort — built
 * here before we saw theirs, and ours prints its denominator because the
 * denominator varies (3 windows or 5, depending on the cohort).
 *
 * Rows the theme claims but the universe does not carry are counted out
 * loud. A member list that silently shrinks is a member count that lies.
 */

// The state word wears the grammar's own glyph (tone × fill via barStyle) —
// an earlier version gave Weakening a caution-yellow of its own, which put a
// third colour claim on a two-channel encoding.

const pct = (v) =>
  v == null || !Number.isFinite(v) ? '—' : `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)}%`
const num = (v) => (v == null || !Number.isFinite(v) ? '—' : String(Math.round(v)))

export default function ThemeMembers({ theme, colour, rsByTicker }) {
  const { universe } = useUniverse()

  const { rows, missing } = useMemo(() => {
    if (!theme?.tickers || !universe) return { rows: [], missing: 0 }
    const byTicker = new Map(universe.map((r) => [r.ticker, r]))
    const found = []
    let gone = 0
    for (const t of theme.tickers) {
      const u = byTicker.get(t)
      if (!u) { gone += 1; continue }
      found.push({ ...u, rs: rsByTicker?.[t] })
    }
    // ranked as the theme itself ranks — by the 3M window — so the drill-down
    // and the bar above it tell the same story in the same order
    found.sort((a, b) => ((b.rs_3m ?? b.rs_63d) ?? -Infinity) - ((a.rs_3m ?? a.rs_63d) ?? -Infinity))
    return { rows: found, missing: gone }
  }, [theme, universe, rsByTicker])

  if (!universe) {
    return <p className="m-0 py-3 text-[11px] text-[var(--color-text-muted)]">Loading universe…</p>
  }
  if (!rows.length) {
    return (
      <p className="m-0 py-3 text-[11px] text-[var(--color-text-muted)]">
        None of this theme&rsquo;s {theme.members} members are in the screener universe.
      </p>
    )
  }

  return (
    <div>
      {missing > 0 && (
        <p className="m-0 pb-1.5 text-[10px] text-[var(--color-text-muted)]">
          {rows.length} of {theme.members} carried by the screener universe · {missing} not in it
        </p>
      )}
      <div className="max-h-[340px] overflow-auto">
        <table className="w-full text-[11px] border-collapse">
          <thead>
            <tr className="text-[10px] font-mono uppercase tracking-wider
                           text-[var(--color-text-muted)] sticky top-0
                           bg-[var(--color-bg)]">
              <th className="text-left py-1 pr-3 font-medium">Ticker</th>
              <th className="text-left py-1 pr-3 font-medium">State</th>
              <th className="text-right py-1 pr-3 font-medium">RS 1M</th>
              <th className="text-right py-1 pr-3 font-medium">RS 3M</th>
              <th className="text-right py-1 pr-3 font-medium"
                  title="percentile within its own industry — a 90 here beside a soft RS says the whole industry is soft">Ind pct</th>
              <th className="text-right py-1 pr-3 font-medium">1W</th>
              <th className="text-right py-1 pr-3 font-medium">1M</th>
              <th className="text-left py-1 pr-3 font-medium">Top quartile</th>
              <th className="text-right py-1 pr-3 font-medium">From 52wH</th>
              <th className="text-right py-1 font-medium">Rel vol</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.ticker}
                  className="border-t border-[var(--color-border-light)]
                             hover:bg-[var(--color-hover-bg)]">
                <td className="py-[3px] pr-3 font-mono font-semibold"
                    style={colour ? { color: colour } : undefined}>{r.ticker}</td>
                <td className="py-[3px] pr-3 text-[10px]">
                  {r.rs?.state ? (
                    <span className="text-[var(--color-text-secondary)] whitespace-nowrap">
                      <i className="inline-block w-[7px] h-[7px] rounded-[1px] mr-[5px] align-[-0.5px]"
                         style={barStyle(r.rs.state)} />
                      {r.rs.state}
                    </span>
                  ) : <span className="text-[var(--color-text-muted)]">—</span>}
                </td>
                <td className="py-[3px] pr-3 text-right tabular-nums">{num(r.rs_1m ?? r.rs_21d)}</td>
                <td className="py-[3px] pr-3 text-right tabular-nums">{num(r.rs_3m ?? r.rs_63d)}</td>
                <td className="py-[3px] pr-3 text-right tabular-nums">{num(r.rs?.group_pctile)}</td>
                <td className="py-[3px] pr-3 text-right tabular-nums">{pct(r.perf_1w)}</td>
                <td className="py-[3px] pr-3 text-right tabular-nums">{pct(r.perf_1m)}</td>
                <td className="py-[3px] pr-3 whitespace-nowrap">
                  <Squares n={r.rs?.persistence} of={r.rs?.persistence_of ?? 5}
                    title={r.rs?.persistence_of
                      ? `Top quartile of its cohort on ${r.rs.persistence} of ${r.rs.persistence_of} windows`
                      : undefined} />
                </td>
                <td className="py-[3px] pr-3 text-right tabular-nums">
                  {/* high_52w_dist is a fraction, not a percent — ×100 or −8.4% prints as −0.1% */}
                  {r.high_52w_dist == null ? '—' : `${(r.high_52w_dist * 100).toFixed(1)}%`}
                </td>
                <td className="py-[3px] text-right tabular-nums">
                  {r.rel_volume == null ? '—' : r.rel_volume.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
