const ENV_STYLE = {
  BULLISH: 'text-[var(--color-profit)]',
  BEARISH: 'text-[var(--color-loss)]',
  MIXED: 'text-[var(--color-signal-caution)]',
  OVERSOLD: 'text-[var(--color-signal-caution)]',
  OVERBOUGHT: 'text-[var(--color-signal-caution)]',
}

const ENV_LABEL = {
  BULLISH: 'Bullish market environment',
  BEARISH: 'Bearish market environment',
  MIXED: 'Mixed market environment',
  OVERSOLD: 'Oversold — reversal watch',
  OVERBOUGHT: 'Overbought — chase risk',
}

export default function VerdictBanner({ verdict, dataQuality }) {
  if (!verdict) return null
  const v = verdict

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <div className="flex items-baseline justify-between mb-3">
        <div className="flex items-baseline gap-3">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            Market Environment · Decision First
          </h3>
          {dataQuality?.stale && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-[var(--color-signal-caution)] uppercase tracking-wide">
              Stale data · as of {dataQuality.as_of ?? '—'}
            </span>
          )}
        </div>
        <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
          score {v.score >= 0 ? `+${v.score}` : v.score} / 12
        </span>
      </div>

      <div className={`text-xl font-semibold mb-4 ${ENV_STYLE[v.env] ?? ''}`}>
        {ENV_LABEL[v.env] ?? v.env}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-4">
        <Col label="Risk level" value={v.risk} sub={`${v.warn_total} total warnings`} />
        <Col label="Exposure" value={v.exposure} />
        <Col label="SPY" value={v.spy_state ?? '—'} />
        <Col label="QQQ" value={v.qqq_state ?? '—'} />
        <Col label="Alignment" value={v.alignment ?? '—'} />
        <Col label="Breadth confirmation" value={v.confirmation} />
        <Col label="Playbook" value={v.playbook} />
      </div>

      <p className="text-[12px] text-[var(--color-text)] border-t border-[var(--color-border-light)] pt-3">
        <span className="font-medium">Guidance:</span> {v.guidance}
      </p>
      {v.notes?.length > 0 && (
        <ul className="mt-2 space-y-0.5">
          {v.notes.map((n) => (
            <li key={n} className="text-[11px] text-[var(--color-text-secondary)]">· {n}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Col({ label, value, sub }) {
  return (
    <div>
      <div className="text-[9px] font-medium uppercase tracking-wider text-[var(--color-text-muted)] mb-1">
        {label}
      </div>
      <div className="text-[12px] text-[var(--color-text)] leading-snug">{value}</div>
      {sub && <div className="text-[10px] text-[var(--color-text-secondary)]">{sub}</div>}
    </div>
  )
}
