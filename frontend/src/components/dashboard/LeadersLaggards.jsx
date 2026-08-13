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

function Row({ etf, ranks, changeKey, windowLabel, cohort, scale }) {
  const name = etfName(etf.ticker)
  const change = etf[changeKey]
  const rs = ranks.get(etf.ticker)
  const ok = Number.isFinite(change) && scale > 0
  const up = change > 0
  // half the track each side of a shared zero, so two rows are comparable
  const w = ok ? Math.min(Math.abs(change) / scale, 1) * 50 : 0
  return (
    <div className="h-[36px] flex flex-col justify-center gap-[3px]">
      <div className="flex items-center gap-2.5">
        <span className="w-7 shrink-0 text-center text-[10px] font-mono tabular-nums
                         leading-[17px] rounded-sm"
              style={rsTone(rs)}
              title={rs == null ? 'no reading for this window'
                                : `${windowLabel} RS ${rs} of 99 — ranked among ${cohort} funds`}>
          {fmtRs(rs)}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-[12.5px] font-mono font-medium leading-[12px]
                           text-[var(--color-text-bold)]">{etf.ticker}</span>
          {/* absent rather than guessed when the vendor had no name */}
          <span className="block text-[10px] leading-[12px] truncate
                           text-[var(--color-text-muted)]" title={name ?? undefined}>
            {name ?? '\u00a0'}
          </span>
        </span>
        {/* The number no longer carries the colour — the bar under it does, and
            a figure that labels its own mark does not need to repeat it. */}
        <span className="shrink-0 text-[12.5px] font-mono tabular-nums
                         text-[var(--color-text-secondary)]">
          {ok ? `${up ? '+' : ''}${(change * 100).toFixed(2)}%` : '—'}
        </span>
      </div>
      {/* the mark: same zero, same scale, so length is comparable down the column */}
      <div className="relative h-[3px]"
           title={ok ? `${(change * 100).toFixed(2)}% of a ±${(scale * 100).toFixed(1)}% ${windowLabel} range`
                     : 'no move measured'}>
        <span className="absolute inset-y-[-1px] w-px left-1/2 bg-[var(--color-border)]" />
        {ok && (
          <span className="absolute top-0 h-[3px] rounded-[1px]"
                style={{ background: up ? 'var(--color-took)' : 'var(--color-refused)',
                         left: up ? '50%' : `${50 - w}%`, width: `${w}%` }} />
        )}
      </div>
    </div>
  )
}

function Column({ label, rows, ranks, changeKey, windowLabel, cohort, scale }) {
  return (
    <div>
      <h4 className="text-[10px] font-mono font-medium uppercase tracking-[.2em]
                     text-[var(--color-text-muted)] mb-1">{label}</h4>
      {rows.map((e) => (
        <Row key={e.ticker} etf={e} ranks={ranks} changeKey={changeKey}
             windowLabel={windowLabel} cohort={cohort} scale={scale} />
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
      // The bar's scale is this window's full-cohort extreme — the same
      // denominator the RS rank uses. Taking it from the six rows shown would
      // make every card's longest bar look identical no matter the day.
      const vals = sorted.map((e) => Math.abs(e[changeKey]))
      return {
        w, changeKey, ranks: rankWithin(etfs, changeKey),
        scale: vals.length ? Math.max(...vals) : 0,
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
        <span className="text-[10px] text-[var(--color-text-muted)]">
          {etfs.length} funds
        </span>
        <span className="ml-auto text-[10px] font-mono text-[var(--color-text-muted)]"
              title="each window's bars are scaled to that window's widest move across the whole cohort">
          {cols.map((c) => `${c.w} ±${(c.scale * 100).toFixed(1)}%`).join('  ·  ')}
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
                    cohort={etfs.length} scale={c.scale} />
          ))}
        </div>
        <div className="grid gap-x-4"
             style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(0, 1fr))` }}>
          {cols.map((c) => (
            <Column key={`${c.w}-lag`} label={`${c.w} laggards`} rows={c.laggards}
                    ranks={c.ranks} changeKey={c.changeKey} windowLabel={c.w}
                    cohort={etfs.length} scale={c.scale} />
          ))}
        </div>
      </div>
    </section>
  )
}
