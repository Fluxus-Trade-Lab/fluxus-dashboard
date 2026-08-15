/**
 * Bull vs Bear Summary — two-column case bullets from AI synthesis.
 */
export default function TickerBullBear({ tickerData }) {
  const synth = tickerData?.ai_synthesis
  const bull = synth?.bull_case || []
  const bear = synth?.bear_case || []

  if (!bull.length && !bear.length) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[14px]">Bull vs Bear Summary</div>
        <div className="text-[var(--color-text-muted)] text-[12.5px]">
          Awaiting AI synthesis. Run <code className="bg-[var(--color-surface)] px-1 rounded">/tearsheet {tickerData?.ticker}</code> to generate.
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[14px] flex items-center justify-between">
        <span>Bull vs Bear Summary</span>
        {synth?.synthesized_at && (
          <span className="text-[10px] text-[var(--color-text-muted)] font-normal">
            synthesized {String(synth.synthesized_at).slice(0, 10)}
          </span>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[12.5px]">
        <div className="bg-[color-mix(in_srgb,var(--color-profit)_5%,transparent)] rounded p-3 border border-[color-mix(in_srgb,var(--color-profit)_20%,transparent)]">
          <div className="text-[10px] uppercase tracking-wide font-bold text-[var(--color-profit)] mb-2">Bull Case</div>
          <ul className="flex flex-col gap-1.5 list-disc pl-4 text-[var(--color-text)]">
            {bull.map((b, i) => <li key={i}>{b}</li>)}
          </ul>
        </div>
        <div className="bg-[color-mix(in_srgb,var(--color-loss)_5%,transparent)] rounded p-3 border border-[color-mix(in_srgb,var(--color-loss)_20%,transparent)]">
          <div className="text-[10px] uppercase tracking-wide font-bold text-[var(--color-loss)] mb-2">Bear Case</div>
          <ul className="flex flex-col gap-1.5 list-disc pl-4 text-[var(--color-text)]">
            {bear.map((b, i) => <li key={i}>{b}</li>)}
          </ul>
        </div>
      </div>
    </div>
  )
}
