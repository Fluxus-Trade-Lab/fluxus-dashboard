import { fmtCur, fmtPct, clr } from '../portfolio/lib/portfolioFormat'

/**
 * Tear-sheet header — symbol + name + meta + live price + back link.
 * Falls back gracefully when fields are missing from universe data.
 */
export default function TickerHeader({ symbol, universe }) {
  const u = universe || {}
  const price = u.close ?? null
  const changePct = u.change_pct != null ? u.change_pct * 100 : null
  const sector = u.sector || 'Unknown'
  const industry = u.industry || ''
  const atrPct = u.adr_pct
  return (
    <div className="border-b border-[var(--color-border)] pb-4 mb-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex flex-col gap-1 min-w-0">
          <button
            onClick={() => window.history.back()}
            className="text-[11px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer w-fit"
          >
            ← Back
          </button>
          <h1 className="text-[26px] font-bold tracking-tight">
            {symbol}
            {industry && (
              <span className="ml-2 text-[13px] font-normal text-[var(--color-text-muted)]">{industry}</span>
            )}
          </h1>
          <div className="text-[11px] text-[var(--color-text-muted)] flex items-center gap-2 flex-wrap">
            <span>{sector}</span>
            {atrPct != null && (
              <>
                <span>·</span>
                <span>ATR {atrPct.toFixed(1)}%</span>
              </>
            )}
          </div>
        </div>
        {price != null && (
          <div className="text-right">
            <div className="text-[26px] font-bold tabular-nums">{fmtCur(price)}</div>
            {changePct != null && (
              <div className={`text-[13px] tabular-nums ${clr(changePct)}`}>
                {fmtPct(changePct)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
