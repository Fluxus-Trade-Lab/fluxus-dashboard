import { useMemo } from 'react'
import { useTickerEvents } from '../../hooks/useTickerEvents'

const LABELS = {
  episodic_pivot: 'Episodic Pivot',
  vcp: 'VCP',
  momentum_97: 'Momentum 97',
  gainers_4pct: 'Up 4% day',
  vol_up_gainers: 'Volume-up gainer',
  ema21_watch: '21 EMA watch',
  healthy_charts: 'Healthy chart',
}

const QUALITY = new Set(['episodic_pivot', 'vcp', 'momentum_97'])

function detail(e) {
  const bits = []
  if (e.change_pct != null) bits.push(`${(e.change_pct * 100).toFixed(1)}%`)
  if (e.rel_volume != null) bits.push(`${e.rel_volume.toFixed(1)}× vol`)
  if (e.num_contractions != null) bits.push(`${e.num_contractions} contractions`)
  if (e.pct_to_pivot != null) bits.push(`${(e.pct_to_pivot * 100).toFixed(1)}% to pivot`)
  if (e.group) bits.push(`RS ${e.group}`)
  return bits.join(' · ')
}

export default function TickerSignalHistory({ symbol, trades }) {
  const { events, loading } = useTickerEvents(symbol)

  const timeline = useMemo(() => {
    const signalItems = events.map((e) => ({
      kind: 'signal', date: e.date, screener: e.screener, detail: detail(e),
    }))
    const tradeItems = (trades ?? [])
      .filter((t) => t.ticker === symbol && t.entryDate)
      .map((t) => ({
        kind: 'trade',
        date: String(t.entryDate).slice(0, 10),
        direction: t.direction,
        price: t.entryPrice,
        qty: t.shares ?? t.currentQty,
      }))
    return [...signalItems, ...tradeItems].sort((a, b) => b.date.localeCompare(a.date))
  }, [events, trades, symbol])

  if (loading || !timeline.length) return null

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
        Signal History · screener appearances and your fills
      </h3>
      <ul className="space-y-1">
        {timeline.map((item, i) => (
          <li key={`${item.date}-${item.kind}-${i}`} className="flex items-baseline gap-3 text-[11px]">
            <span className="font-mono tabular-nums text-[var(--color-text-muted)] w-20 shrink-0">
              {item.date}
            </span>
            {item.kind === 'trade' ? (
              <>
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  item.direction === 'long' ? 'bg-[var(--color-profit)]' : 'bg-[var(--color-loss)]'
                }`} />
                <span className="font-medium text-[var(--color-text)]">
                  {item.direction === 'long' ? 'BOUGHT' : 'SOLD SHORT'}
                  {item.qty ? ` ${item.qty}` : ''}
                  {item.price != null ? ` @ ${item.price}` : ''}
                </span>
              </>
            ) : (
              <>
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  QUALITY.has(item.screener) ? 'bg-[var(--color-signal-caution)]' : 'bg-[var(--color-border)]'
                }`} />
                <span className="text-[var(--color-text)]">
                  {LABELS[item.screener] ?? item.screener}
                </span>
                <span className="text-[var(--color-text-secondary)]">{item.detail}</span>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
