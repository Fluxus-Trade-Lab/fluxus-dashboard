import { useMemo } from 'react'
import { etfName, rsTone, fmtRs, rankWithin, PERF_WINDOWS } from '../../lib/etfRank'

/**
 * Best and worst industries, four things per row.
 *
 *   RS        0-99 percentile of this row's own window, ranked inside this
 *             card's group — the scale run_all.rank_tradeable puts on stocks.
 *             It briefly read rrs_*, which ranks today against recent sessions
 *             rather than against peers, so a fund 5.8pp behind on the month
 *             could show 100.
 *   ticker    the instrument
 *   name      what it is exposed to
 *   change    the move over that window
 *
 * Price is deliberately gone. A fund's dollar level says nothing about the
 * market and was taking the width the exposure needed — "GDX / Gold Miners"
 * reads at a glance, "$83.92" does not.
 */

function Row({ etf, ranks, changeKey, windowLabel, cohort }) {
  const name = etfName(etf.ticker)
  const change = etf[changeKey]
  const rs = ranks.get(etf.ticker)
  const up = change > 0
  return (
    <div className="flex items-center gap-2.5 h-[34px]">
      <span className="w-7 shrink-0 text-center text-[10px] font-mono tabular-nums
                       leading-[17px] rounded-sm"
            style={rsTone(rs)}
            title={rs == null ? 'no reading for this window'
                              : `${windowLabel} RS ${rs} of 99 — ranked among ${cohort} funds`}>
        {fmtRs(rs)}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[12px] font-mono font-medium leading-[13px]
                         text-[var(--color-text-bold)]">{etf.ticker}</span>
        {/* absent rather than guessed when the vendor had no name */}
        <span className="block text-[10px] leading-[13px] truncate
                         text-[var(--color-text-muted)]" title={name ?? undefined}>
          {name ?? '\u00a0'}
        </span>
      </span>
      <span className="shrink-0 text-[12px] font-mono tabular-nums"
            style={{ color: up ? 'var(--color-took)' : 'var(--color-refused)' }}>
        {up ? '+' : ''}{(change * 100).toFixed(2)}%
      </span>
    </div>
  )
}

function Column({ label, rows, ranks, changeKey, windowLabel, cohort }) {
  return (
    <div>
      <h4 className="text-[9px] font-mono font-medium uppercase tracking-[.2em]
                     text-[var(--color-text-muted)] mb-1">{label}</h4>
      {rows.map((e) => (
        <Row key={e.ticker} etf={e} ranks={ranks} changeKey={changeKey}
             windowLabel={windowLabel} cohort={cohort} />
      ))}
    </div>
  )
}

export default function LeadersLaggards({
  etfs, windows = ['1W', '1M'], limit = 3, title = 'Industries',
}) {
  const cols = useMemo(() => {
    if (!etfs?.length) return []
    return windows.map((w) => {
      const changeKey = PERF_WINDOWS[w]
      const sorted = [...etfs].filter((e) => Number.isFinite(e[changeKey]))
        .sort((a, b) => b[changeKey] - a[changeKey])
      return {
        w, changeKey, ranks: rankWithin(etfs, changeKey),
        leaders: sorted.slice(0, limit),
        laggards: sorted.slice(-limit).reverse(),
      }
    })
  }, [etfs, windows, limit])

  if (!etfs?.length) return null

  return (
    <section className="bg-[var(--color-surface)] border border-[var(--color-border)]
                        rounded-lg overflow-hidden flex flex-col">
      <div className="px-3 py-1.5 border-b border-[var(--color-border)] flex items-baseline gap-3">
        <span className="text-[10px] font-mono font-medium uppercase tracking-[.2em]
                         text-[var(--color-text-secondary)]">{title}</span>
        <span className="text-[9px] text-[var(--color-text-muted)]">
          {etfs.length} funds
        </span>
      </div>
      {/* Two stacked grids rather than one four-cell grid. A single grid gives
          every row the height of the tallest, so when this card stretches to
          match the sectors card beside it the gap opens between leaders and
          laggards — in the middle, where it reads as missing rows. Stacked,
          the slack lands at the bottom where it reads as space. */}
      <div className="px-3 py-2 flex-1 flex flex-col gap-3">
        <div className="grid gap-x-4"
             style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(0, 1fr))` }}>
          {cols.map((c) => (
            <Column key={`${c.w}-lead`} label={`${c.w} leaders`} rows={c.leaders}
                    ranks={c.ranks} changeKey={c.changeKey} windowLabel={c.w}
                    cohort={etfs.length} />
          ))}
        </div>
        <div className="grid gap-x-4"
             style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(0, 1fr))` }}>
          {cols.map((c) => (
            <Column key={`${c.w}-lag`} label={`${c.w} laggards`} rows={c.laggards}
                    ranks={c.ranks} changeKey={c.changeKey} windowLabel={c.w}
                    cohort={etfs.length} />
          ))}
        </div>
      </div>
    </section>
  )
}
