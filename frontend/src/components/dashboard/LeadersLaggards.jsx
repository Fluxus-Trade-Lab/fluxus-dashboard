import { useMemo } from 'react'
import { etfName, rsTone, fmtRs, rankAllWindows, RS_WINDOWS } from '../../lib/etfRank'

/**
 * Best and worst industries, in the exact row grammar the sectors card uses:
 * three RS clocks · the instrument · today's move. The two cards sit side by
 * side, and until 2026-08-11 they spoke different layouts — six mini-sections
 * with their own headers here, one table there. Same anatomy now, so the pair
 * reads as one instrument at two grains (Andy: 统一设计，左右和谐对称).
 *
 * Ranks are 0-99 within the full industry list (the cohort is printed in the
 * header), not within the twelve rows shown — a leader's 99 means best of 68,
 * not best of what fits on the card. Sorted by the shortest clock; the top
 * six and bottom six of that sort are shown, worst last, with the cut marked.
 */

export default function LeadersLaggards({ etfs, limit = 6, title = 'Industries' }) {
  const ranks = useMemo(() => rankAllWindows(etfs), [etfs])
  const { leaders, laggards } = useMemo(() => {
    if (!etfs?.length) return { leaders: [], laggards: [] }
    const near = ranks[RS_WINDOWS[0].key]
    const sorted = [...etfs].sort(
      (a, b) => (near.get(b.ticker) ?? -1) - (near.get(a.ticker) ?? -1))
    return { leaders: sorted.slice(0, limit), laggards: sorted.slice(-limit) }
  }, [etfs, ranks, limit])

  if (!leaders.length) return null

  const Row = ({ e }) => {
    const name = etfName(e.ticker)
    const day = e.change_pct
    return (
      <div className="grid grid-cols-[repeat(3,28px)_1fr_54px] gap-x-2 items-center h-[34px]">
        {RS_WINDOWS.map((w) => {
          const v = ranks[w.key].get(e.ticker)
          return (
            <span key={w.key}
                  className="text-center text-[10px] font-mono tabular-nums
                             leading-[17px] rounded-sm"
                  style={rsTone(v)}
                  title={v == null ? 'no reading for this window'
                                   : `RS ${v} of 99 — ${w.note}`}>
              {fmtRs(v)}
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
  }

  return (
    <section className="bg-[var(--color-surface)] border border-[var(--color-border)]
                        rounded-lg overflow-hidden flex flex-col">
      <div className="px-3 py-1.5 border-b border-[var(--color-border)] flex items-baseline gap-3">
        <span className="text-[10px] font-mono uppercase tracking-[.2em]
                         text-[var(--color-text-secondary)]">{title}</span>
        <span className="text-[9px] text-[var(--color-text-muted)]">
          relative strength within {etfs.length} funds, three clocks · top {limit} and bottom {limit} by today
        </span>
      </div>

      <div className="px-3 py-2 flex-1">
        <div className="grid grid-cols-[repeat(3,28px)_1fr_54px] gap-x-2 mb-1">
          {RS_WINDOWS.map((w) => (
            <span key={w.key} title={w.note}
                  className="text-[9px] font-mono uppercase tracking-wide text-center
                             text-[var(--color-text-muted)]">{w.label}</span>
          ))}
          <span className="text-[9px] font-mono uppercase tracking-[.2em]
                           text-[var(--color-text-muted)]">Industry</span>
          <span className="text-[9px] font-mono uppercase tracking-wide text-right
                           text-[var(--color-text-muted)]">Day</span>
        </div>

        {leaders.map((e) => <Row key={e.ticker} e={e} />)}

        {/* the cut between the top and bottom of the ranked list — the middle
            is not shown, and a hidden middle should look cut, not continuous */}
        <div className="flex items-center gap-2 h-[20px]">
          <span className="flex-1 border-t border-dashed border-[var(--color-border)]" />
          <span className="text-[8.5px] font-mono uppercase tracking-[.2em]
                           text-[var(--color-text-muted)]">{etfs.length - 2 * limit} not shown</span>
          <span className="flex-1 border-t border-dashed border-[var(--color-border)]" />
        </div>

        {laggards.map((e) => <Row key={e.ticker} e={e} />)}
      </div>

      <p className="px-3 pb-2 m-0 text-[9.5px] leading-snug text-[var(--color-text-muted)]">
        Each number is a 0-99 rank of that window&rsquo;s return among
        all {etfs.length}{' '}industry funds — the same three clocks as the sectors card. Left to right is
        backwards in time, so a row that climbs to the left is an industry turning up.
      </p>
    </section>
  )
}
