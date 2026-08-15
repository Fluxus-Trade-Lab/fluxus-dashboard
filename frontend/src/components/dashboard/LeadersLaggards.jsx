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
  const ok = Number.isFinite(change)
  // Andy 2026-08-16: the bar retires and the move wears the pair directly —
  // same call as the ticker cards, a coloured figure plus a coloured bar was
  // one reading twice.
  return (
    <div className="h-[32px] flex items-center gap-2.5">
      <span className="w-7 shrink-0 text-center text-[10px] font-mono tabular-nums
                       leading-[17px] rounded-sm"
            style={rsTone(rs)}
            title={rs == null ? 'no reading for this window'
                              : `${windowLabel} RS ${rs} of 99 — ranked among ${cohort} funds`}>
        {fmtRs(rs)}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[12.5px] font-mono font-semibold leading-[12px]
                         text-[var(--color-text-bold)]">{etf.ticker}</span>
        {/* absent rather than guessed when the vendor had no name */}
        <span className="block text-[10px] leading-[12px] truncate
                         text-[var(--color-text-muted)]" title={name ?? undefined}>
          {name ?? '\u00a0'}
        </span>
      </span>
      <span className="shrink-0 text-[12.5px] font-mono tabular-nums font-medium"
            style={{ color: !ok ? 'var(--color-text-muted)'
                          : change > 0 ? 'var(--color-took)' : 'var(--color-refused)' }}>
        {ok ? `${change > 0 ? '+' : ''}${(change * 100).toFixed(2)}%` : '—'}
      </span>
    </div>
  )
}

/** `label` is the window, and only the TOP block carries it: the column
 *  establishes 1D / 1W / 1M once, and the laggards under the rule inherit it
 *  (Andy 2026-08-16). A second identical row of headers was the same word
 *  printed twice in one column. */
function Column({ label, rows, ranks, changeKey, windowLabel, cohort }) {
  return (
    <div>
      {label && (
        <h4 className="text-[10px] font-mono font-medium uppercase tracking-[.2em]
                       text-[var(--color-text-muted)] mb-1.5">{label}</h4>
      )}
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
    // The title moved OUT of the card (Andy 2026-08-16): it names the block,
    // so it stands on the ground like every other section heading, and the
    // card holds only the data.
    <div className="flex flex-col min-w-0">
      {/* breathing room above and below: the heading sits between the ticker
          strip and its card, and needs air on both sides to read as a
          heading rather than a squeezed caption. Tooltip cut (Andy). */}
      <div className="text-[17px] font-semibold leading-tight text-[var(--color-text-bold)]
                      mt-4 mb-3 px-1">
        {title}
      </div>
      <section className="bg-[var(--color-surface)] rounded-3xl overflow-hidden flex flex-col flex-1 pt-4">
      {/* Two stacked grids rather than one four-cell grid. A single grid gives
          every row the height of the tallest, so when this card stretches to
          match the sectors card beside it the gap opens between leaders and
          laggards — in the middle, where it reads as missing rows. Stacked,
          the slack lands at the bottom where it reads as space. */}
      {/* The window words went with the bars: the title already says leaders
          then laggards, so the blocks are separated by a hairline and air
          instead of by repeating the words six times. */}
      <div className="px-5 pb-4 flex-1 flex flex-col">
        <div className="grid gap-x-4"
             style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(0, 1fr))` }}>
          {cols.map((c) => (
            <Column key={`${c.w}-lead`} label={c.w} rows={c.leaders}
                    ranks={c.ranks} changeKey={c.changeKey} windowLabel={c.w}
                    cohort={etfs.length} />
          ))}
        </div>
        <i className="block h-px bg-[var(--color-border-light)] my-3" />
        <div className="grid gap-x-4"
             style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(0, 1fr))` }}>
          {cols.map((c) => (
            <Column key={`${c.w}-lag`} label={null} rows={c.laggards}
                    ranks={c.ranks} changeKey={c.changeKey} windowLabel={c.w}
                    cohort={etfs.length} />
          ))}
        </div>
      </div>
      </section>
    </div>
  )
}
