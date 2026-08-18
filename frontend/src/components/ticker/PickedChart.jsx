import { useMemo, useState } from 'react'
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
  const { symbol, isDefault, stale, names, panel, pick } = useChartPick()
  const shortlist = useShortlist()
  const [span, setSpan] = useState('D')
  const [query, setQuery] = useState('')

  /**
   * ANY name on today's file, not just the ones on the default screen.
   *
   * The chip strip below is one door and it only opens onto True Market
   * Leaders. This is the other: type three letters and chart anything the
   * nightly run has readings for. It is deliberately NOT a click on the name
   * cells in the grids — those cells are already a ticker, a theme mark and a
   * number inside about 90px, and a third target in there would be a worse
   * version of both gestures. Reaching a name is a keystroke; that is cheap.
   */
  const matches = useMemo(() => {
    const q = query.trim().toUpperCase()
    if (q.length < 1) return []
    return shortlist.universe
      .filter((r) => r.ticker.startsWith(q))
      .slice(0, 8)
  }, [query, shortlist.universe])

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
          {/* THE STRIP IS NOT THE SCREEN, AND IT IS NOT THE CARD EITHER.
              The panel ships a `count` and a `truncated`, so a bare chip count
              would claim the screen found 25 when it found 27 — the silent
              truncation this file is written against.
              It then collided with something worse: on Today's List the same
              panel's own card was reporting 16/27 at the same moment, because
              that card obeys the page's view switches (the RS floor was on)
              and this strip does not. One panel, one screen, two numbers.
              Both were true and the pair was unreadable. The strip now names
              what it counts — how many names this chart can reach — in words
              the card does not use, and the note below says the switches do
              not reach here. Making it obey them instead was the wrong cure:
              this same card also sits on the Screener, which has no such
              switches, and the strip would then mean two different things on
              two pages. */}
          <span className="text-[10px] font-mono tabular-nums text-[var(--color-text-muted)]">
            {panel.truncated > 0
              ? `${names.length} chartable of the screen's ${panel.count}`
              : `${names.length} chartable`}
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

      {/* the second door: anything on tonight's file, by name */}
      <div className="relative">
        <input type="search" value={query} onChange={(e) => setQuery(e.target.value)}
               placeholder="chart any name on tonight's file…"
               aria-label="find a name to chart"
               className="w-full bg-[var(--color-surface-raised)] border-none rounded
                          px-2.5 py-[5px] text-[11px] font-mono text-[var(--color-text)]
                          placeholder:text-[var(--color-text-secondary)]" />
        {matches.length > 0 && (
          <ul className="list-none m-0 mt-1 p-0 max-h-[168px] overflow-y-auto
                         rounded bg-[var(--color-surface-raised)]">
            {matches.map((r) => (
              <li key={r.ticker}>
                <button type="button"
                        onClick={() => { pick(r.ticker); setQuery('') }}
                        className="w-full flex items-baseline gap-2 text-left px-2.5 py-[5px]
                                   bg-transparent border-none cursor-pointer
                                   hover:bg-[var(--color-surface)]">
                  <span className="text-[11px] font-mono font-semibold
                                   text-[var(--color-text-bold)]">{r.ticker}</span>
                  <span className="min-w-0 flex-1 truncate text-[10px]
                                   text-[var(--color-text-muted)]">{r.from}</span>
                  {r.rs_1m != null && (
                    <span className="text-[10px] font-mono tabular-nums
                                     text-[var(--color-text-secondary)]">{r.rs_1m}</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
        {query.trim() && matches.length === 0 && (
          <p className="m-0 mt-1 px-2.5 text-[10px] text-[var(--color-text-muted)]">
            No name starting with <span className="font-mono">{query.trim().toUpperCase()}</span> on
            tonight&rsquo;s file. That means no scan found it &mdash; not that it does not exist.
          </p>
        )}
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
        This strip is the screen&rsquo;s own list and <b>no view switch on the page narrows
        it</b> &mdash; a card here may well be showing a smaller count for the same screen,
        because those cards obey the switches and this does not.
        The screen is: {panel.recipe}. It is a <b>qualification, not an entry</b> &mdash;
        nothing here says buy this, and the chart is TradingView&rsquo;s, drawn from their
        data rather than from the nightly file.
      </p>
    </section>
  )
}
