import { useMemo } from 'react'
import { fmtPct, pctColor } from '../../lib/format'

/**
 * Best and worst industries over a set of windows.
 *
 * Two mounts, one component. The Today strip shows weekly + monthly at top-1 —
 * TSF's giant best/worst cards, answered with fields etf_data already carried
 * (perf_1m was computed all along and simply never drawn). The reference grid
 * keeps daily + weekly at top-3. `limit` exists so top-1 can become top-3
 * without touching the component again.
 */
const WINDOWS = {
  daily: { key: 'change_pct', label: 'Daily' },
  weekly: { key: 'perf_1w', label: 'Weekly' },
  monthly: { key: 'perf_1m', label: 'Monthly' },
}

function TopList({ title, items }) {
  if (!items || items.length === 0) return null
  return (
    <div>
      <h4 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] mb-1.5">
        {title}
      </h4>
      <div className="flex flex-col gap-1">
        {items.map((etf) => (
          <div key={etf.ticker} className="flex items-center justify-between gap-2">
            <span className="font-mono text-xs font-medium text-[var(--color-text-bold)]">
              {etf.ticker}
            </span>
            <span className={`font-mono text-xs ${pctColor(etf.change)}`}>
              {fmtPct(etf.change)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function LeadersLaggards({ etfs, windows = ['daily', 'weekly'], limit = 3, title = 'Industries' }) {
  const lists = useMemo(() => {
    if (!etfs || etfs.length === 0) return []
    return windows.map((w) => {
      const { key, label } = WINDOWS[w]
      const sorted = [...etfs].sort((a, b) => (b[key] ?? 0) - (a[key] ?? 0))
      return {
        w,
        leaders: { title: `${label} Leaders`, items: sorted.slice(0, limit).map((e) => ({ ticker: e.ticker, change: e[key] })) },
        laggards: { title: `${label} Laggards`, items: sorted.slice(-limit).reverse().map((e) => ({ ticker: e.ticker, change: e[key] })) },
      }
    })
  }, [etfs, windows, limit])

  if (!etfs || etfs.length === 0) return null

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
      <div className="px-3 py-1.5 border-b border-[var(--color-border)]">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          {title}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-3 px-3 py-2.5">
        {lists.map(({ w, leaders }) => <TopList key={`${w}-l`} {...leaders} />)}
        {lists.map(({ w, laggards }) => <TopList key={`${w}-g`} {...laggards} />)}
      </div>
    </div>
  )
}
