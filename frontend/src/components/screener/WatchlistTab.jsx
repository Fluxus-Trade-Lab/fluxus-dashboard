import { useMemo, useState } from 'react'
import { applyFilters } from '../../lib/screenerFilter'
import TickerLink from '../ticker/TickerLink'

/**
 * The preset lists, and the names that appear on more than one of them.
 *
 * Rewritten 2026-08-13 (Andy: 夜色几乎为0，极其枯燥 · 蓝色的 ticker 看不清晰).
 * Two faults, one visual and one measurable:
 *
 * COLOUR. The overlap chips printed their ticker in `--color-took` on the dark
 * surface — 2.19:1, which is why they could not be read. took is a FILL: its
 * place in the measured greyscale ladder (L* 38.8) was set for a solid block
 * on the ground, never for text on top of it. The chips now use it as a fill
 * with light type over it, 5.38:1, which is the role it was measured for.
 *
 * TONE. Nine identical boxes at one value, in Tailwind's named type scale
 * while the Screener tab beside it — the same page — spoke in explicit px and
 * mono labels. Sorting by size and letting the empty lists collapse gives the
 * page a range: the full lists lead with a grid of names, the empty ones
 * become a single quiet line. An empty list stays on the page, because a
 * screen that found nothing today is a reading; it just stops taking the room
 * of one that found 196.
 */

const MAX_DISPLAY = 30
const TOP_COUNT = 15

const DEFAULT_FILTERS = {
  marketCapEnabled: true,
  marketCapMin: 1.0,
  vol50dEnabled: true,
  vol50dMin: 1.0,
  excludeHealthcare: false,
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  return (
    <button type="button"
      onClick={() => navigator.clipboard.writeText(text).then(() => {
        setCopied(true); setTimeout(() => setCopied(false), 1500)
      }).catch(() => {})}
      className="bg-transparent border-none p-0 cursor-pointer text-[10px] font-mono font-medium
                 uppercase tracking-[.14em] text-[var(--color-text-muted)]
                 hover:text-[var(--color-text)] outline-none focus-visible:ring-1">
      {copied ? 'copied' : 'copy'}
    </button>
  )
}

function WatchlistCard({ name, tickers }) {
  const display = tickers.slice(0, MAX_DISPLAY)
  const hidden = tickers.length - display.length

  if (!tickers.length) {
    return (
      <div className="border border-[var(--color-border-light)] rounded-lg
                      bg-[var(--color-surface)] px-3.5 py-2.5 flex items-baseline gap-3 opacity-70">
        <span className="text-[10px] font-mono font-medium uppercase tracking-[.18em]
                         text-[var(--color-text-muted)]">{name}</span>
        <span className="ml-auto text-[10px] text-[var(--color-text-muted)]">0 today</span>
      </div>
    )
  }

  return (
    <div className="rounded-3xl
                    bg-[var(--color-surface)] px-3.5 py-3">
      <div className="flex items-baseline gap-2.5 mb-2">
        <span className="text-[10px] font-mono font-medium uppercase tracking-[.18em]
                         text-[var(--color-text-secondary)]">{name}</span>
        <CopyButton text={tickers.join(',')} />
        <span className="ml-auto text-[10px] font-mono tabular-nums
                         text-[var(--color-text-muted)]">{tickers.length}</span>
      </div>
      <div className="grid grid-cols-5 gap-x-2 gap-y-1">
        {display.map((t) => (
          <TickerLink key={t} symbol={t}
            className="text-[11px] font-mono text-[var(--color-text-secondary)]" />
        ))}
      </div>
      {hidden > 0 && (
        <p className="m-0 mt-1.5 text-[10px] text-[var(--color-text-muted)]">
          + {hidden} more, in the copied list
        </p>
      )}
    </div>
  )
}

export default function WatchlistTab({ universe, presets }) {
  const watchlistData = useMemo(() => {
    if (!universe || !presets) return []
    return presets
      .filter((p) => p.readonly)
      .map((preset) => {
        const rows = applyFilters(universe, { ...DEFAULT_FILTERS, ...preset.filters }, '')
        rows.sort((a, b) => ((b.rs_1m ?? b.rs_21d) ?? 0) - ((a.rs_1m ?? a.rs_21d) ?? 0))
        return { name: preset.name, tickers: rows.map((r) => r.ticker) }
      })
      // longest first: the page gets a top and a bottom instead of nine equals
      .sort((a, b) => b.tickers.length - a.tickers.length)
  }, [universe, presets])

  const topTickers = useMemo(() => {
    const counts = {}
    for (const item of watchlistData) {
      for (const t of item.tickers) counts[t] = (counts[t] || 0) + 1
    }
    return Object.entries(counts)
      .filter(([, c]) => c >= 2)
      .sort((a, b) => b[1] - a[1])
      .slice(0, TOP_COUNT)
  }, [watchlistData])

  const live = watchlistData.filter((d) => d.tickers.length)
  const empty = watchlistData.filter((d) => !d.tickers.length)

  return (
    <div>
      {topTickers.length > 0 && (
        <section className="mb-5">
          <div className="flex items-baseline gap-3 pb-2">
            <span className="text-[10px] font-mono font-medium uppercase tracking-[.24em]
                             text-[var(--color-text-muted)]">Top overlap</span>
            {/* the count is of NAMES, not of lists — it briefly read
                "on 15 lists at once", which is the cap on this board */}
            <span className="text-[11px] text-[var(--color-text-secondary)]">
              {topTickers.length} names on two or more of the {watchlistData.length} lists
            </span>
            <CopyButton text={topTickers.map(([t]) => t).join(',')} />
            <i className="flex-1 h-px bg-[var(--color-border)]" />
          </div>
          {/* v3: overlap has no adverse pole, so the chip is ink, not blue —
              solid fill with ground-coloured type, same contrast logic as
              before (fill + light text, never coloured text on ground). */}
          <div className="flex flex-wrap gap-1.5">
            {topTickers.map(([ticker, count]) => (
              <span key={ticker}
                className="inline-flex items-baseline gap-1.5 px-2 py-[3px] rounded"
                style={{ background: 'var(--color-text-bold)' }}
                title={`${ticker} — on ${count} of the preset lists`}>
                <TickerLink symbol={ticker}
                  className="text-[12.5px] font-mono font-medium text-[var(--color-bg)]" />
                <span className="text-[10px] font-mono tabular-nums text-[var(--color-bg)] opacity-75">
                  {count}
                </span>
              </span>
            ))}
          </div>
        </section>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {live.map((item) => (
          <WatchlistCard key={item.name} name={item.name} tickers={item.tickers} />
        ))}
      </div>

      {empty.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 mt-3">
          {empty.map((item) => (
            <WatchlistCard key={item.name} name={item.name} tickers={item.tickers} />
          ))}
        </div>
      )}
    </div>
  )
}
