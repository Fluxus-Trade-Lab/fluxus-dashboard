import { useMemo } from 'react'
import { etfName, rsTone, fmtExcess, excessOver, RS_WINDOWS } from '../../lib/etfRank'

/**
 * The eleven sectors, each with its relative strength on three clocks.
 *
 * Design: TSF's sector table, taken for the shape and not the palette.
 *
 * Three numbers per row rather than one, because a single RS reading cannot
 * tell a sector that has been strong all month from one that turned strong
 * today — and the turn is the tradeable half. Left to right is backwards in
 * time: today, five sessions, twenty-one.
 *
 * Each is excess over SPY in percentage points, the definition rs_engine uses
 * for themes. It used to read rrs_*, which ranks today's reading inside recent
 * sessions instead of measuring strength against SPY — a fund 5.8pp behind on
 * the month could print 100 there.
 *
 * Sorted by the shortest window, so what is working now comes first. Sorting
 * by the long window would rank the board by what has already happened, which
 * is exactly the failure the three columns exist to avoid.
 *
 * Row height is pinned to the same 34px the industries card uses, so the two
 * sit side by side without either one deciding the other's layout.
 */

export default function SectorStrength({ etfs, benchmark, title = 'Sectors' }) {
  const rows = useMemo(() => {
    if (!etfs?.length) return []
    const key = RS_WINDOWS[0].key
    return [...etfs].sort((a, b) => {
      const av = excessOver(a, benchmark, key)
      const bv = excessOver(b, benchmark, key)
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      return bv - av
    })
  }, [etfs, benchmark])

  if (!rows.length) return null

  return (
    <section className="bg-[var(--color-surface)] border border-[var(--color-border)]
                        rounded-lg overflow-hidden flex flex-col">
      <div className="px-3 py-1.5 border-b border-[var(--color-border)] flex items-baseline gap-3">
        <span className="text-[10px] font-mono uppercase tracking-[.2em]
                         text-[var(--color-text-secondary)]">{title}</span>
        <span className="text-[9px] text-[var(--color-text-muted)]">
          relative strength vs SPY, three clocks
        </span>
      </div>

      <div className="px-3 py-2 flex-1">
        <div className="grid grid-cols-[repeat(3,42px)_1fr_54px] gap-x-2 mb-1">
          {RS_WINDOWS.map((w) => (
            <span key={w.key} title={w.note}
                  className="text-[9px] font-mono uppercase tracking-wide text-center
                             text-[var(--color-text-muted)]">{w.label}</span>
          ))}
          <span className="text-[9px] font-mono uppercase tracking-[.2em]
                           text-[var(--color-text-muted)]">Sector</span>
          <span className="text-[9px] font-mono uppercase tracking-wide text-right
                           text-[var(--color-text-muted)]">Day</span>
        </div>

        {rows.map((e) => {
          const name = etfName(e.ticker)
          const day = e.change_pct
          return (
            <div key={e.ticker}
                 className="grid grid-cols-[repeat(3,42px)_1fr_54px] gap-x-2 items-center
                            h-[34px]">
              {RS_WINDOWS.map((w) => {
                const v = excessOver(e, benchmark, w.key)
                return (
                  <span key={w.key}
                        className="text-center text-[10px] font-mono tabular-nums
                                   leading-[17px] rounded-sm"
                        style={rsTone(v)}
                        title={v == null ? 'no benchmark reading for this window'
                                         : `${fmtExcess(v)}pp vs SPY — ${w.note}`}>
                    {fmtExcess(v)}
                  </span>
                )
              })}
              <span className="min-w-0">
                <span className="block text-[12px] font-mono font-medium leading-[13px]
                                 text-[var(--color-text-bold)]">{e.ticker}</span>
                <span className="block text-[10px] leading-[13px] truncate
                                 text-[var(--color-text-muted)]" title={name ?? undefined}>
                  {name ?? ' '}
                </span>
              </span>
              <span className="text-right text-[12px] font-mono tabular-nums"
                    style={{ color: !Number.isFinite(day) ? 'var(--color-text-muted)'
                      : day > 0 ? 'var(--color-took)' : 'var(--color-refused)' }}>
                {!Number.isFinite(day) ? '—'
                  : `${day > 0 ? '+' : ''}${(day * 100).toFixed(2)}%`}
              </span>
            </div>
          )
        })}
      </div>

      <p className="px-3 pb-2 m-0 text-[9.5px] leading-snug text-[var(--color-text-muted)]">
        Each number is this sector&rsquo;s return minus SPY&rsquo;s over that window, in
        percentage points. Left to right is backwards in time, so a row that climbs to
        the left is a sector turning up. One colour scale across all three columns, which
        is why 1D is mostly uncoloured — beating SPY by two points in a single session is
        rare, and a scale that tinted it anyway would make a normal day look like a move.
      </p>
    </section>
  )
}
