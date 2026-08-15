/**
 * Management — CEO/CFO + headcount + AI-synthesized commentary.
 */
export default function TickerManagement({ tickerData }) {
  const info = tickerData?.info || {}
  const officers = info.companyOfficers || []
  const ceo = officers.find(o => /CEO|Chief Exec/i.test(o.title || ''))
  const cfo = officers.find(o => /CFO|Chief Fin/i.test(o.title || ''))
  const headcount = info.fullTimeEmployees
  const commentary = tickerData?.ai_synthesis?.management?.commentary

  if (!ceo && !cfo && !headcount && !commentary) {
    return null
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[14px]">Management</div>
      <div className="text-[12.5px] flex flex-col gap-1.5">
        {ceo && (
          <div>
            <span className="text-[var(--color-text-muted)]">CEO: </span>
            <span className="text-[var(--color-text)]">{ceo.name}{ceo.title ? ` — ${ceo.title}` : ''}</span>
          </div>
        )}
        {cfo && (
          <div>
            <span className="text-[var(--color-text-muted)]">CFO: </span>
            <span className="text-[var(--color-text)]">{cfo.name}{cfo.title ? ` — ${cfo.title}` : ''}</span>
          </div>
        )}
        {headcount != null && (
          <div>
            <span className="text-[var(--color-text-muted)]">Headcount: </span>
            <span className="text-[var(--color-text)] tabular-nums">{headcount.toLocaleString()} employees</span>
          </div>
        )}
        {commentary && (
          <div className="mt-2 pt-2 border-t border-[var(--color-border-light)]">
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-text-muted)] mb-1">Recent commentary</div>
            <div className="text-[var(--color-text)] leading-snug">{commentary}</div>
          </div>
        )}
      </div>
    </div>
  )
}
