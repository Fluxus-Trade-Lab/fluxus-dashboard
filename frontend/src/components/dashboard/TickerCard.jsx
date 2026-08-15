/**
 * One benchmark, two lines — Andy's layout, 2026-08-16.
 *
 *   line 1   ticker · and RISK OFF, red, right-aligned, when that is the state
 *   line 2   price left · move right, and the move wears the pair
 *
 * What the previous card carried and this one deliberately does not:
 *
 *   the dot        the signal light. It repeated the printed word in hue, and
 *                  hue that only restates a word is decoration by our own rule.
 *   POWER 3 etc.   price-structure states. Market state details carries the
 *                  full read; on a strip of ten small cards they were noise.
 *                  RISK OFF alone survives, because a lone red on this site
 *                  means the binding constraint — it is the one signal that
 *                  should stop the eye here.
 *   the 3px bar    the shared-scale mark. The move number now carries the
 *                  pair directly (Andy's call), and a coloured figure plus a
 *                  coloured bar is the same reading twice.
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

/** The left edge wears the day's direction — Andy 2026-08-16, off a
 *  reference card. Same pair as the move figure; a stripe and a figure is
 *  not double-speak the way bar+figure was, because the stripe reads at
 *  strip-scan distance where the number cannot. No measured move, no
 *  stripe: an unmeasured day has no direction to paint. */
export default function TickerCard({ ticker, signal, etf }) {
  // signal data comes from signals.json (SPY, QQQ, IWM, BTC-USD, ^VIX)
  // etf data comes from etf_data.json (DIA, RSP, QQQE, GLD, TLT)
  // one or both may be present
  const price = signal?.close ?? etf?.close ?? null
  const change = etf?.change_pct ?? null
  const riskOff = signal?.signal === 'RISK_OFF'

  const displayName = ticker === 'BTC-USD' ? 'BTC' : ticker === '^VIX' ? 'VIX' : ticker

  const dir = Number.isFinite(change)
    ? (change > 0 ? 'var(--color-took)' : 'var(--color-refused)') : null

  return (
    <div className="relative bg-[var(--color-surface)] rounded-2xl px-4 py-3 min-w-0 overflow-hidden">
      {dir && (
        <span aria-hidden className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full"
              style={{ background: dir }} />
      )}
      <div className="flex items-baseline justify-between gap-2 mb-1">
        {/* Every ticker on the site is bold ink (Andy 2026-08-16). It is the
            card's identity, not a caption for it. */}
        <span className="text-[10px] font-mono font-semibold uppercase tracking-[.24em]
                         text-[var(--color-text-bold)] truncate">
          {displayName}
        </span>
        {riskOff && (
          <span className="text-[10px] font-mono font-semibold uppercase tracking-[.12em]
                           text-[var(--color-signal-riskoff)] shrink-0">
            RISK OFF
          </span>
        )}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <span className="font-mono text-[17px] tabular-nums leading-tight
                         text-[var(--color-text-bold)]">
          {formatPrice(price)}
        </span>
        <span className="font-mono text-[12.5px] tabular-nums font-medium"
              style={{ color: changeColour(change) }}
              title={change == null ? 'no move measured for this instrument' : undefined}>
          {formatChange(change)}
        </span>
      </div>
    </div>
  )
}
