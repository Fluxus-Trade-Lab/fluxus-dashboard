import { signalColor, signalLabel, signalTextColor } from '../../lib/format'

/**
 * One benchmark, on the market half's own type ladder and its own palette.
 *
 * Until 2026-08-12 this card was the only component on the Dashboard still
 * written in Tailwind's named type scale (text-xl / text-xs) while everything
 * around it used explicit px, and the only one painting a market move in
 * profit-green / loss-red while the Industries and Sectors cards beside it
 * painted the same kind of number in took / refused. Two ladders and two
 * palettes for one row of evidence.
 *
 *   name    10px mono, .24em — the site's standard small label
 *   level   15px mono — card headline, one tier under the 26px page subject
 *           and one over the 12px table numbers
 *   move    12px mono, took / refused — the same colours every other
 *           percentage on the market half wears
 *   signal  9px mono label, traffic-light hue. Kept, because this is a named
 *           four-level signal from the pipeline rather than a direction, and
 *           the hue only ever reinforces a word that is already printed —
 *           it is never the sole carrier.
 *
 * A move the feed did not carry (BTC and VIX are absent from etf_data) prints
 * an em-dash rather than nothing: an unmeasured move is a fact about the
 * feed, and a silently blank slot reads as a flat day.
 */

function formatPrice(val) {
  if (val == null) return '—'
  if (val >= 10000) return val.toLocaleString('en-US', { maximumFractionDigits: 0 })
  return val.toFixed(2)
}

function formatChange(val) {
  if (val == null || isNaN(val)) return '—'
  const pct = val * 100
  return `${pct > 0 ? '+' : ''}${pct.toFixed(2)}%`
}

function changeColour(val) {
  if (val == null || isNaN(val)) return 'var(--color-text-muted)'
  return val > 0 ? 'var(--color-took)' : 'var(--color-refused)'
}

export default function TickerCard({ ticker, signal, etf }) {
  // signal data comes from signals.json (SPY, QQQ, IWM, BTC-USD, ^VIX)
  // etf data comes from etf_data.json (DIA, RSP, QQQE, GLD, TLT)
  // one or both may be present
  const price = signal?.close ?? etf?.close ?? null
  const change = etf?.change_pct ?? null
  const sigColor = signal?.color ?? null
  const sigLabel = signal?.signal ? signalLabel(signal.signal) : null

  const displayName = ticker === 'BTC-USD' ? 'BTC' : ticker === '^VIX' ? 'VIX' : ticker

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)]
                    rounded-lg px-3.5 py-2.5 min-w-0">
      <div className="flex items-center gap-1.5 mb-1">
        {sigColor && (
          <span className={`w-[6px] h-[6px] rounded-full shrink-0 ${signalColor(sigColor)}`} />
        )}
        <span className="text-[10px] font-mono font-medium uppercase tracking-[.24em]
                         text-[var(--color-text-muted)] truncate">
          {displayName}
        </span>
      </div>

      <div className="font-mono text-[15px] tabular-nums leading-tight
                      text-[var(--color-text-bold)]">
        {formatPrice(price)}
      </div>

      <div className="flex items-baseline gap-2 mt-0.5 flex-wrap">
        <span className="font-mono text-[12px] tabular-nums"
              style={{ color: changeColour(change) }}
              title={change == null ? 'no move measured for this instrument' : undefined}>
          {formatChange(change)}
        </span>
        {sigLabel && (
          <span className={`text-[9px] font-mono font-medium uppercase tracking-[.14em] ${signalTextColor(sigColor)}`}>
            {sigLabel}
          </span>
        )}
      </div>
    </div>
  )
}
