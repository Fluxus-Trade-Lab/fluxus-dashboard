import { fmtCur } from '../portfolio/lib/portfolioFormat'

/**
 * Compact 7-stat horizontal strip below the header. AAOI-reference style.
 *
 * Sourced primarily from per-ticker JSON (tickerData.info). Falls back to
 * universe.json fields when ticker data isn't fetched.
 */
export default function TickerQuickStats({ tickerData, universe }) {
  const info = tickerData?.info || {}
  const u = universe || {}

  const stats = [
    ['Mkt Cap', formatMktCap(info.marketCap ?? u.market_cap)],
    // universe carries the 52-week bounds as DISTANCES on every name, nightly;
    // the info block carries them as prices and was empty for half the site on
    // 2026-08-20. Prefer the live one, fall back to the file, then say absent.
    ['52W Range', format52wRange(
      info.fiftyTwoWeekLow ?? implied(u.close, u.low_52w),
      info.fiftyTwoWeekHigh ?? implied(u.close, u.high_52w_dist))],
    ['Avg Vol 20D', formatVolume(info.averageVolume10days || info.averageVolume || u.avg_volume)],
    ['ATR / %PX', formatAtrPx(u.atr, u.adr_pct)],
    ['Fwd P/S', formatRatio(info.priceToSalesTrailing12Months ?? info.priceToBook)],
    ['Fwd P/E', formatRatio(info.forwardPE)],
    ['Next ER', formatNextER(tickerData?.next_earnings)],
  ]

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-4 mb-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {stats.map(([label, value]) => (
          <div key={label} className="flex flex-col">
            <span className="text-[11px] text-[var(--color-text-muted)] uppercase tracking-wide">{label}</span>
            <span className="tabular-nums text-[13px] font-semibold">{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/** close / (1 + dist) — the same recovery Key Levels uses, checked there. */
function implied(close, dist) {
  if (close == null || dist == null) return null
  const p = close / (1 + dist)
  return Number.isFinite(p) ? p : null
}

function formatMktCap(v) {
  if (v == null) return '—'
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`
  return `$${v.toFixed(0)}`
}

function format52wRange(low, high) {
  if (low == null || high == null) return '—'
  return `${fmtCur(low)}–${fmtCur(high)}`
}

function formatVolume(v) {
  if (v == null) return '—'
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`
  return `${(v / 1e3).toFixed(0)}K`
}

function formatAtrPx(atr, adrPct) {
  if (atr == null && adrPct == null) return '—'
  if (atr != null && adrPct != null) return `${fmtCur(atr)} / ${adrPct.toFixed(1)}%`
  if (atr != null) return fmtCur(atr)
  return `${adrPct.toFixed(1)}%`
}

function formatRatio(v) {
  if (v == null || v <= 0) return '—'
  return `${v.toFixed(1)}×`
}

function formatNextER(ne) {
  if (!ne || !ne.date) return '—'
  const d = String(ne.date).slice(0, 10)
  return d
}
