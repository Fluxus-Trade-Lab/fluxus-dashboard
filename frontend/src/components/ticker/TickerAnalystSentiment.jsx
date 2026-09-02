/**
 * Analyst Sentiment — consensus, ratings split, price targets,
 * recent rating changes.
 */
export default function TickerAnalystSentiment({ tickerData }) {
  const a = tickerData?.analyst
  if (!a || Object.keys(a).length === 0) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[13px]">Analyst Sentiment</div>
        <div className="text-[var(--color-text-muted)] text-[13px]">No analyst data available.</div>
      </div>
    )
  }

  const current = tickerData?.current_price ?? a.current_price
  const avg = a.avg_price_target
  const impliedPct = (current && avg) ? ((avg - current) / current * 100) : null

  const consensus = a.consensus || '—'
  const consensusColor = (
    consensus === 'Strong Buy' ? 'text-[var(--color-profit)] font-bold' :
    consensus === 'Buy' ? 'text-[var(--color-profit)]' :
    consensus === 'Hold' ? 'text-[var(--color-signal-caution)]' :
    consensus === 'Sell' || consensus === 'Strong Sell' ? 'text-[var(--color-loss)]' :
    'text-[var(--color-text-muted)]'
  )

  const recent = a.recent_rating_changes || []

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[13px]">Analyst Sentiment</div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-[13px] mb-3">
        <div className="flex justify-between border-b border-[var(--color-border-light)] pb-1">
          <span className="text-[var(--color-text-muted)]">Consensus</span>
          <span className={consensusColor}>{consensus}</span>
        </div>
        <div className="flex justify-between border-b border-[var(--color-border-light)] pb-1">
          <span className="text-[var(--color-text-muted)]">Total ratings</span>
          <span className="tabular-nums font-semibold">{a.total_ratings ?? '—'}</span>
        </div>
        <div className="flex justify-between border-b border-[var(--color-border-light)] pb-1">
          <span className="text-[var(--color-text-muted)]">Bull / Neutral / Bear</span>
          <span className="tabular-nums font-semibold">
            <span className="text-[var(--color-profit)]">{a.bullish ?? 0}</span>
            {' / '}
            <span className="text-[var(--color-signal-caution)]">{a.neutral ?? 0}</span>
            {' / '}
            <span className="text-[var(--color-loss)]">{a.bearish ?? 0}</span>
          </span>
        </div>
        <div className="flex justify-between border-b border-[var(--color-border-light)] pb-1">
          <span className="text-[var(--color-text-muted)]">Avg PT</span>
          <span className="tabular-nums font-semibold">{avg != null ? `$${avg.toFixed(2)}` : '—'}</span>
        </div>
        <div className="flex justify-between border-b border-[var(--color-border-light)] pb-1">
          <span className="text-[var(--color-text-muted)]">High PT</span>
          <span className="tabular-nums font-semibold">{a.high_price_target != null ? `$${a.high_price_target.toFixed(2)}` : '—'}</span>
        </div>
        <div className="flex justify-between border-b border-[var(--color-border-light)] pb-1">
          <span className="text-[var(--color-text-muted)]">Low PT</span>
          <span className="tabular-nums font-semibold">{a.low_price_target != null ? `$${a.low_price_target.toFixed(2)}` : '—'}</span>
        </div>
        <div className="flex justify-between border-b border-[var(--color-border-light)] pb-1 col-span-2">
          <span className="text-[var(--color-text-muted)]">Implied % vs current</span>
          <span className={`tabular-nums font-bold ${impliedPct == null ? '' : impliedPct > 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
            {impliedPct == null ? '—' : `${impliedPct > 0 ? '+' : ''}${impliedPct.toFixed(1)}%`}
          </span>
        </div>
      </div>

      {recent.length > 0 && (
        <>
          <div className="text-[11px] uppercase text-[var(--color-text-muted)] tracking-wide mb-1">Recent rating changes</div>
          <div className="text-[11px] flex flex-col gap-0.5 max-h-40 overflow-y-auto">
            {recent.slice(0, 5).map((r, i) => (
              <div key={i} className="flex justify-between gap-3">
                <span className="text-[var(--color-text-muted)] truncate flex-1">
                  {String(r.date || '').slice(0, 10)} · {r.firm || 'Anon'}
                </span>
                <span className="text-[var(--color-text)] whitespace-nowrap">
                  {r.from_grade ? `${r.from_grade} → ` : ''}{r.to_grade || r.action || '—'}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
