import { useMemo, useState } from 'react'
import { applyFilters } from '../../lib/screenerFilter'

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
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }
  return (
    <button
      onClick={handleCopy}
      className="ml-2 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide border border-[var(--color-border)] rounded bg-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-text-secondary)] cursor-pointer transition-colors"
    >
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function WatchlistCard({ name, tickers }) {
  const display = tickers.slice(0, MAX_DISPLAY)
  const hasMore = tickers.length > MAX_DISPLAY
  const tickerStr = tickers.join(',')

  return (
    <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <span className="font-semibold text-sm text-[var(--color-text)]">{name}</span>
          {tickers.length > 0 && <CopyButton text={tickerStr} />}
        </div>
        <div className="text-xs font-semibold text-green-600">{tickers.length} tickers</div>
      </div>
      <div className="grid grid-cols-5 gap-x-3 gap-y-1.5">
        {display.map(t => (
          <div key={t} className="text-xs font-mono text-[var(--color-text-secondary)] text-center">{t}</div>
        ))}
        {hasMore && (
          <div className="text-xs text-[var(--color-text-muted)] text-center italic">etc.</div>
        )}
      </div>
      {tickers.length === 0 && (
        <div className="text-xs text-[var(--color-text-muted)] text-center py-4">No matches</div>
      )}
    </div>
  )
}

export default function WatchlistTab({ universe, presets }) {
  const watchlistData = useMemo(() => {
    if (!universe || !presets) return []
    return presets
      .filter(p => p.readonly)
      .map(preset => {
        const rows = applyFilters(universe, { ...DEFAULT_FILTERS, ...preset.filters }, '')
        // Sort by rs_21d descending (RS 1M)
        rows.sort((a, b) => (b.rs_21d ?? 0) - (a.rs_21d ?? 0))
        return {
          name: preset.name,
          tickers: rows.map(r => r.ticker),
        }
      })
  }, [universe, presets])

  const topTickers = useMemo(() => {
    const counts = {}
    for (const item of watchlistData) {
      for (const t of item.tickers) {
        counts[t] = (counts[t] || 0) + 1
      }
    }
    return Object.entries(counts)
      .filter(([, c]) => c >= 2)
      .sort((a, b) => b[1] - a[1])
      .slice(0, TOP_COUNT)
  }, [watchlistData])

  const now = new Date()
  const dateStr = now.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
  const topTickerStr = topTickers.map(([t]) => t).join(',')

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <span className="text-lg font-bold text-[var(--color-text)]">Today's Watchlist</span>
          <span className="text-sm text-[var(--color-text-muted)] ml-3">{dateStr}</span>
        </div>
        <div className="text-xs text-[var(--color-text-muted)]">Sorted by RS1M</div>
      </div>

      {topTickers.length > 0 && (
        <div className="border border-green-600/30 rounded-lg bg-[var(--color-surface)] p-4 mb-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center">
              <span className="font-semibold text-sm text-green-600">Top Overlap</span>
              <span className="text-xs text-[var(--color-text-muted)] ml-2">Tickers appearing in 2+ screeners</span>
              <CopyButton text={topTickerStr} />
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {topTickers.map(([ticker, count]) => (
              <div key={ticker} className="flex items-center gap-1 px-2.5 py-1 rounded bg-green-600/10 border border-green-600/20">
                <span className="text-xs font-mono font-semibold text-green-600">{ticker}</span>
                <span className="text-[10px] text-green-600/70">{count}x</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {watchlistData.map(item => (
          <WatchlistCard key={item.name} name={item.name} tickers={item.tickers} />
        ))}
      </div>
    </div>
  )
}
