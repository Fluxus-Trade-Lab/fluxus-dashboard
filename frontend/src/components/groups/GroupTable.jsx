import { useMemo, useState } from 'react'
import StateBadge from './StateBadge'
import Squares from '../Squares'

const pct = (v) => (v == null ? '—' : `${(v * 100).toFixed(2)}%`)

const COLS = [
  { key: 'group', label: 'Group', align: 'left' },
  { key: 'members', label: 'n', align: 'right' },
  { key: 'excess_3m', label: 'RS 3M', align: 'right', fmt: pct },
  { key: 'rs_accel', label: 'Accel', align: 'right', fmt: pct },
  { key: 'persistence', label: 'Persist', align: 'right' },
  { key: 'state', label: 'State', align: 'left' },
]

export default function GroupTable({ rows, showMethod = false, emptyNote }) {
  const [sortKey, setSortKey] = useState('excess_3m')
  const [asc, setAsc] = useState(false)

  const sorted = useMemo(() => {
    const out = [...rows]
    out.sort((a, b) => {
      const x = a[sortKey], y = b[sortKey]
      if (x == null && y == null) return 0
      if (x == null) return 1
      if (y == null) return -1
      if (typeof x === 'string') return asc ? x.localeCompare(y) : y.localeCompare(x)
      return asc ? x - y : y - x
    })
    return out
  }, [rows, sortKey, asc])

  if (!rows.length) {
    return (
      <div className="text-[var(--color-text-muted)] text-[14px] py-6 text-center">
        {emptyNote ?? 'Nothing to show'}
      </div>
    )
  }

  const toggle = (key) => {
    if (key === sortKey) setAsc(!asc)
    else { setSortKey(key); setAsc(false) }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[14px] border-collapse">
        <thead>
          <tr className="text-[var(--color-text-muted)] text-[11px] uppercase tracking-wide">
            {COLS.map((c) => (
              <th
                key={c.key}
                onClick={() => toggle(c.key)}
                className={`px-2 py-1.5 cursor-pointer select-none font-medium
                            text-${c.align} hover:text-[var(--color-text)]`}
              >
                {c.label}
                {sortKey === c.key && <span className="ml-1">{asc ? '▲' : '▼'}</span>}
              </th>
            ))}

          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
            <tr
              key={r.group}
              className="border-t border-[var(--color-border)] hover:bg-[var(--color-surface-hover)]"
            >
              <td className="px-2 py-1.5">
                {/* How a group was built is provenance, not a reading — it
                    rode a column of its own until 2026-08-12 and now rides
                    the name's tooltip, still checkable, no longer in the way. */}
                <span className="font-medium"
                      title={showMethod && r.method
                        ? `${r.method}${r.validation ? ` · ${r.validation}` : ''}`
                        : undefined}>{r.group}</span>
                {r.tickers?.length > 0 && (
                  <span
                    className="ml-2 text-[11px] text-[var(--color-text-muted)]"
                    title={r.tickers.join(' · ')}
                  >
                    {r.tickers.slice(0, 4).join(' ')}
                    {r.tickers.length > 4 ? ' …' : ''}
                  </span>
                )}
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">{r.members}</td>
              <td className="px-2 py-1.5"><Axis v={r.excess_3m} range={0.7} /></td>
              <td className="px-2 py-1.5"><Axis v={r.rs_accel} range={0.6} /></td>
              {/* Drawn, not printed. The denominator varies — a group scored
                  against its cohort gets 5 windows, a proxy benchmarked against
                  SPY gets 3 — so it is carried by the empty marks rather than by
                  a slash, and two different scales cannot read as one. */}
              <td className="px-2 py-1.5 text-right whitespace-nowrap">
                <Squares n={r.persistence} of={r.persistence_of ?? 5}
                  title={r.persistence_of
                    ? `Top quartile on ${r.persistence} of ${r.persistence_of} horizons`
                    : undefined} />
              </td>
              <td className="px-2 py-1.5"><StateBadge state={r.state} /></td>

            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/**
 * One mark instead of one number, on a shared axis with zero drawn.
 *
 * Design: Fluxus_Brand/visual/explorations/2026-08-08/market_today.html
 *
 * Two columns of signed percentages could only be compared by reading both and
 * subtracting. Drawn against a common zero they compare by looking, and the
 * reading the page exists for becomes visible without a sentence: the strongest
 * themes have long bars in the level column and bars pointing the other way in
 * acceleration.
 *
 * Sign is carried by direction from zero, not by hue alone — the bar is on the
 * left or the right of the rule, so it survives greyscale. The number stays
 * printed, because a bar answers "which is bigger" and a number answers
 * "by how much", and this table is asked both.
 *
 * `range` is the half-width in the column's own unit. Values beyond it clamp
 * and are marked, rather than being silently rescaled — a clamped bar that
 * looks like a full one would misreport the outlier that matters most.
 */
function Axis({ v, range }) {
  if (v == null) return <span className="text-[var(--color-text-muted)]">—</span>
  const frac = Math.max(-1, Math.min(1, v / range))
  const clamped = Math.abs(v) > range
  const pos = v > 0
  return (
    <span className="flex items-center gap-2">
      <span className="relative block flex-1 min-w-[54px] h-[11px]">
        {/* zero has to be visible: sign is carried by which side of it the bar
            sits on, so a rule you cannot see takes the encoding with it */}
        <i className="absolute top-[-3px] bottom-[-3px] left-1/2 w-px bg-[var(--color-text-muted)]" />
        <i className="absolute top-0 bottom-0" style={{
          background: pos ? 'var(--color-took)' : 'var(--color-refused)',
          left: pos ? '50%' : `${50 + frac * 50}%`,
          width: `${Math.abs(frac) * 50}%`,
        }} />
        {clamped && (
          <i className="absolute top-0 bottom-0 w-[2px] bg-[var(--color-text-bold)]"
             style={{ [pos ? 'right' : 'left']: 0 }} title="beyond the axis" />
        )}
      </span>
      <span className="tabular-nums text-right w-[62px] shrink-0">{pct(v)}</span>
    </span>
  )
}
