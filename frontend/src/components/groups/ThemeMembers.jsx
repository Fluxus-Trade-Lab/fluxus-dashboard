import { useMemo } from 'react'
import Squares from '../Squares'
import { useUniverse } from '../../hooks/useUniverse'
import { useGroups } from '../../hooks/useGroups'

/**
 * The stocks inside one theme, on the screener's own measurements.
 *
 * Design: Fluxus_Brand/visual/2026-08-10_TSF_PAGE_MAP.md §一.2
 *
 * A theme's bar is an average, and an average is a claim about a set you
 * cannot see. This is the set. Nothing here is computed for this view — every
 * column already existed in universe.json or groups.json and had never been
 * put next to the theme it belongs to.
 *
 * `persistence` is worth naming: it is the count of windows on which a stock
 * sat in the top quartile of its own cohort. That is the same construction as
 * TSF's «6/6 = number of signals where the stock is in the top 25% of its own
 * theme» — we built it before seeing theirs, and ours prints its denominator
 * because the denominator varies (3 windows or 5, depending on the cohort).
 *
 * The rows a theme claims but the universe does not carry are counted out
 * loud. A member list that silently shrinks is a member count that lies.
 */

const HEAD = [
  ['Ticker', 'left'],
  ['State', 'left'],
  ['RS 21d', 'right'],
  ['RS 63d', 'right'],
  ['1W', 'right'],
  ['1M', 'right'],
  ['Top quartile', 'left'],
  ['From 52wH', 'right'],
  ['Rel vol', 'right'],
]

const STATE_TONE = {
  Leading: 'var(--color-took)',
  Improving: 'var(--color-took)',
  Weakening: 'var(--color-signal-caution)',
  Lagging: 'var(--color-untested)',
}

const pct = (v, digits = 1) =>
  v == null || !Number.isFinite(v) ? '—' : `${v > 0 ? '+' : ''}${(v * 100).toFixed(digits)}%`
const num = (v, digits = 1) =>
  v == null || !Number.isFinite(v) ? '—' : v.toFixed(digits)

export default function ThemeMembers({ theme, onClose }) {
  const { universe } = useUniverse()
  const { stocksByTicker } = useGroups()

  const { rows, missing } = useMemo(() => {
    if (!theme?.tickers || !universe) return { rows: [], missing: 0 }
    const byTicker = new Map(universe.map((r) => [r.ticker, r]))
    const found = []
    let gone = 0
    for (const t of theme.tickers) {
      const u = byTicker.get(t)
      if (!u) { gone += 1; continue }
      found.push({ ...u, rs: stocksByTicker?.[t] })
    }
    // ranked the way the theme itself is ranked, so the drill-down and the bar
    // above it are telling the same story in the same order
    found.sort((a, b) => (b.rs_63d ?? -Infinity) - (a.rs_63d ?? -Infinity))
    return { rows: found, missing: gone }
  }, [theme, universe, stocksByTicker])

  if (!theme) return null

  return (
    <section className="border border-[var(--color-border)] rounded-lg mt-3
                        bg-[var(--color-surface)]">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-2.5
                      border-b border-[var(--color-border)]">
        <h3 className="text-[16px] font-semibold m-0"
            style={{ fontFamily: 'var(--font-cond)' }}>{theme.group}</h3>
        <span className="text-[11px] text-[var(--color-text-muted)]">
          {rows.length} of {theme.members} members carried by the screener universe
          {missing > 0 && ` · ${missing} not in it`}
        </span>
        <span className="text-[11px] font-mono tabular-nums text-[var(--color-text-secondary)]">
          theme RS {pct(theme.excess_3m)} · accel {pct(theme.rs_accel)}
        </span>
        <button type="button" onClick={onClose}
                className="ml-auto text-[11px] bg-transparent border-0 p-0 cursor-pointer
                           text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
          close
        </button>
      </div>

      {!universe ? (
        <div className="px-4 py-6 text-[12px] text-[var(--color-text-muted)]">Loading universe…</div>
      ) : rows.length === 0 ? (
        <div className="px-4 py-6 text-[12px] text-[var(--color-text-muted)]">
          None of this theme&rsquo;s {theme.members} members are in the screener universe —
          it is built from a different list.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-[12px] border-collapse">
            <thead>
              <tr className="text-[9px] font-mono uppercase tracking-wider
                             text-[var(--color-text-muted)]">
                {HEAD.map(([label, align]) => (
                  <th key={label} className={`px-3 py-1.5 font-medium text-${align}`}>{label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.ticker}
                    className="border-t border-[var(--color-border-light)]
                               hover:bg-[var(--color-hover-bg)]">
                  <td className="px-3 py-1.5 font-mono font-medium">{r.ticker}</td>
                  <td className="px-3 py-1.5 text-[11px]"
                      style={{ color: STATE_TONE[r.rs?.state] ?? 'var(--color-text-muted)' }}>
                    {r.rs?.state ?? '—'}
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{num(r.rs_21d)}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{num(r.rs_63d)}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{pct(r.perf_1w)}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{pct(r.perf_1m)}</td>
                  <td className="px-3 py-1.5 whitespace-nowrap">
                    <Squares n={r.rs?.persistence} of={r.rs?.persistence_of ?? 5}
                      title={r.rs?.persistence_of
                        ? `Top quartile of its cohort on ${r.rs.persistence} of ${r.rs.persistence_of} windows`
                        : undefined} />
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums">
                    {r.high_52w_dist == null ? '—' : `${r.high_52w_dist.toFixed(1)}%`}
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{num(r.rel_volume, 2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="px-4 py-2 m-0 text-[10.5px] leading-relaxed text-[var(--color-text-muted)]
                    border-t border-[var(--color-border-light)]">
        <b>Top quartile</b> counts the windows on which a stock sat in the top 25% of its
        own cohort — the filled squares are the count, the empty ones the denominator, and
        the denominator varies by cohort. RS values are relative-strength ranks, not
        percentages.
      </p>
    </section>
  )
}
