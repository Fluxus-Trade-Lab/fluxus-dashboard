import { useState } from 'react'
import TickerChart from './TickerChart'
import { useChartPick } from '../../hooks/useChartPick'

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
  const { symbol, isDefault, stale, names, panel, pick } = useChartPick()
  const [span, setSpan] = useState('D')

  if (!panel) return null

  const current = names.find((n) => n.ticker === symbol) ?? null

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

      {/* the screen, as a strip you can click. It is the card's only control
          besides the timeframe — the ticker links in the panels below still go
          to the tear-sheet, and taking that gesture away to steer this chart
          would have cost a working door to buy a new one. */}
      <div>
        <div className="flex items-baseline gap-2 mb-1.5">
          <span className="text-[10px] font-mono uppercase tracking-[.2em]
                           text-[var(--color-text-muted)]">
            {panel.label}
          </span>
          {/* THE STRIP IS NOT THE SCREEN. The panel ships a `count` and a
              `truncated`, and this list is the untruncated head of it — today
              25 chips out of 27 names. Printing the chip count alone would
              claim the screen found 25, which is the silent-truncation failure
              this whole file is written against. */}
          <span className="text-[10px] font-mono tabular-nums text-[var(--color-text-muted)]">
            {panel.truncated > 0
              ? `${names.length} of ${panel.count} · ${panel.truncated} not listed here`
              : names.length}
          </span>
        </div>
        <div className="flex gap-1.5 overflow-x-auto pb-1">
          {names.map((n) => {
            const on = n.ticker === symbol
            return (
              <button key={n.ticker} type="button" onClick={() => pick(n.ticker)}
                      aria-pressed={on}
                      title={`${n.group} · ${n.group_state} · RS 1M ${n.rs_1m ?? '—'}`}
                      className={`shrink-0 px-2 py-[3px] text-[11px] font-mono rounded
                                  cursor-pointer border-none transition-colors ${on
                        ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] font-semibold'
                        : 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'}`}>
                {n.ticker}
              </button>
            )
          })}
        </div>
      </div>

      <p className="m-0 text-[10px] leading-relaxed text-[var(--color-text-muted)]">
        {stale && (
          <><b className="text-[var(--color-text-secondary)]">{stale} is not on this
          screen today</b>, so the card went back to its default. </>
        )}
        {isDefault
          ? <>Nothing picked, so this is the <b className="text-[var(--color-text-secondary)]">first
              name</b> out of True Market Leaders, in the file&rsquo;s own order. </>
          : <>Your pick. </>}
        The screen is: {panel.recipe}. It is a <b>qualification, not an entry</b> &mdash;
        nothing here says buy this, and the chart is TradingView&rsquo;s, drawn from their
        data rather than from the nightly file.
      </p>
    </section>
  )
}
