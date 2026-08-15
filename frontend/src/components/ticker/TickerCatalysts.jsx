/**
 * Recent Catalysts & News — raw from yfinance .news. Phase 3d will replace
 * this with AI-synthesized narrative bullets via the /tearsheet slash command.
 */
export default function TickerCatalysts({ tickerData }) {
  const news = tickerData?.news || []
  const synth = tickerData?.ai_synthesis?.catalysts

  if (synth && synth.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[14px] flex items-center justify-between">
          <span>Recent Catalysts & News</span>
          <span className="text-[10px] text-[var(--color-text-muted)] font-normal">AI-synthesized</span>
        </div>
        <ul className="text-[12.5px] flex flex-col gap-1.5 list-disc pl-4 text-[var(--color-text)]">
          {synth.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      </div>
    )
  }

  if (!news.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[14px]">Recent Catalysts & News</div>
        <div className="text-[var(--color-text-muted)] text-[14px]">No recent news.</div>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[14px] flex items-center justify-between">
        <span>Recent News</span>
        <span className="text-[10px] text-[var(--color-text-muted)] font-normal">
          Run <code className="bg-[var(--color-surface)] px-1 rounded">/tearsheet {tickerData.ticker}</code> for AI synthesis
        </span>
      </div>
      <ul className="text-[12.5px] flex flex-col gap-2 max-h-96 overflow-y-auto">
        {news.slice(0, 10).map((n, i) => (
          <li key={i} className="flex flex-col gap-0.5 pb-1.5 border-b border-[var(--color-border-light)]">
            <div className="text-[10px] text-[var(--color-text-muted)] flex gap-2">
              <span>{String(n.date || '').slice(0, 10)}</span>
              {n.source && <span>· {n.source}</span>}
            </div>
            {n.url ? (
              <a
                href={n.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[var(--color-text)] hover:text-[var(--color-accent)] hover:underline leading-snug"
              >
                {n.title}
              </a>
            ) : (
              <span className="text-[var(--color-text)] leading-snug">{n.title}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
