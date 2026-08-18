import { useState } from 'react'
import TickerChart from './TickerChart'
import { useChartPick } from '../../hooks/useChartPick'
import { useShortlist } from '../../hooks/useShortlist'

/**
 * The fixed chart card — page 3's middle tier.
 *
 * ANDY'S RULING, 2026-08-18. The first proposal made this card grow: unpicked,
 * the scan grid was largest; pick a name and the chart took the page. He turned
 * it down. The card is FIXED — same place, same size, every session — and only
 * its contents change. Two things that buys:
 *
 *   · a click never reflows the page, so the grid you were reading is still
 *     where you left it;
 *   · arriving is never an empty frame, because the card already has a name
 *     before you have done anything.
 *
 * That name is the first True Market Leader (see useChartPick). The card says
 * which screen it came from and what the screen's recipe is, because a chart
 * with a symbol on it and no provenance is the one object on this page that
 * could be mistaken for a recommendation.
 *
 * MONTH / WEEK / DAY. Andy asked for all three timeframes; `interval` was
 * hardcoded to 'D' and the component only accepted `{symbol, height}`. It
 * takes the interval now and this is the switch.
 */

const SPANS = [
  { key: 'M', label: 'Month', tv: 'M' },
  { key: 'W', label: 'Week',  tv: 'W' },
  { key: 'D', label: 'Day',   tv: 'D' },
]

export default function PickedChart({ height = 460 }) {
  const { symbol, isDefault, names, panel, pick } = useChartPick()
  const shortlist = useShortlist()
  const [span, setSpan] = useState('D')

  if (!panel) return null

  const current = names.find((n) => n.ticker === symbol)
    ?? shortlist.universe.find((r) => r.ticker === symbol)
    ?? null
  const onList = symbol ? shortlist.has(symbol) : false

  return (
    <section className="rounded-3xl bg-[var(--color-surface)] p-4 flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <h2 className="m-0 text-[17px] leading-none font-semibold
                       text-[var(--color-text-bold)] font-mono">
          {symbol ?? '—'}
        </h2>
        {current && (
          <span className="text-[11px] text-[var(--color-text-muted)]">
            {current.group}
            {current.group_state && <> &middot; {current.group_state}</>}
            {current.rs_1m != null && <> &middot; RS 1M <span className="font-mono tabular-nums">{current.rs_1m}</span></>}
          </span>
        )}
        {/* The block that carried the screen, its recipe and the not-an-entry
            line is gone at Andy's call, 2026-08-18 — with the table below now
            charting a name on click, the strip and its search were two doors
            nobody needed and the paragraph was three lines of standing text
            under a chart that changes on every click.
            What could not go with it is WHERE THE DEFAULT CAME FROM: a symbol
            on a chart with no stated origin is the one thing on this page a
            reader could mistake for a recommendation. So it survives as a
            clause on a line that already exists, and the recipe rides in its
            tooltip rather than on the page. */}
        {isDefault && symbol && (
          <span className="text-[11px] text-[var(--color-text-muted)]"
                title={`${panel.label} — ${panel.recipe}`}>
            &middot; default: first {panel.label}
          </span>
        )}
        {symbol && (
          /* the decision point. You looked at the chart; this is where the
             looking turns into a name you leave with. */
          <button type="button"
                  onClick={() => (onList ? shortlist.remove(symbol)
                                         : shortlist.add(symbol, current ?? {},
                                                         current?.from ?? panel.label))}
                  aria-pressed={onList}
                  className={`text-[10px] font-mono uppercase tracking-[.14em] px-2 py-[3px]
                              rounded border-none cursor-pointer transition-colors ${onList
                    ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                    : 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'}`}>
            {onList ? 'on shortlist \u2212' : 'add to shortlist +'}
          </button>
        )}
        <div className="ml-auto flex gap-1" role="group" aria-label="timeframe">
          {SPANS.map((s) => (
            <button key={s.key} type="button" onClick={() => setSpan(s.key)}
                    aria-pressed={span === s.key}
                    className={`px-2 py-[2px] text-[10px] font-mono rounded cursor-pointer
                                border-none transition-colors ${span === s.key
                      ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                      : 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'}`}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {panel.measured && symbol ? (
        <TickerChart symbol={symbol} height={height}
                     interval={SPANS.find((s) => s.key === span).tv} />
      ) : (
        /* not zero, and not an empty frame: the screen did not run */
        <div className="rounded-3xl flex items-center justify-center p-6"
             style={{ height, backgroundImage:
               'repeating-linear-gradient(45deg,var(--color-border-light) 0 1px,transparent 1px 7px)' }}>
          <p className="m-0 max-w-[42ch] text-center text-[11px] leading-relaxed
                        text-[var(--color-text-muted)]">
            True Market Leaders was <b className="text-[var(--color-text-secondary)]">not
            measured</b> in tonight&rsquo;s run, so there is no name for this card to open on.
            That is different from the screen finding nobody.
          </p>
        </div>
      )}

    </section>
  )
}
