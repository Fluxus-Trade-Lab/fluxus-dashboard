/**
 * Sources — numbered footnote refs from the AI synthesis.
 */
export default function TickerSources({ tickerData }) {
  const sources = tickerData?.ai_synthesis?.sources || []
  if (!sources.length) return null

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[14px]">Sources</div>
      <ol className="text-[11px] flex flex-col gap-1.5 list-decimal pl-5">
        {sources.map(s => (
          <li key={s.id}>
            {s.title}{s.source ? ` — ${s.source}` : ''}{s.date ? ` (${String(s.date).slice(0, 10)})` : ''}
            {s.url && (
              <>
                {' '}
                <a
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--color-accent)] hover:underline"
                >
                  {extractDomain(s.url)}
                </a>
              </>
            )}
          </li>
        ))}
      </ol>
      <div className="text-[10px] text-[var(--color-text-muted)] mt-3 pt-3 border-t border-[var(--color-border-light)]">
        Quotes, financials, ratios, estimates, peers, analyst data: yfinance (numeric) + Claude Code with WebSearch/WebFetch (narrative synthesis),
        {tickerData?.ai_synthesis?.synthesized_at && ` ${String(tickerData.ai_synthesis.synthesized_at).slice(0, 10)}`} snapshot. Technical indicators
        computed from daily OHLCV. For informational purposes only — not investment advice.
      </div>
    </div>
  )
}

function extractDomain(url) {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return url }
}
