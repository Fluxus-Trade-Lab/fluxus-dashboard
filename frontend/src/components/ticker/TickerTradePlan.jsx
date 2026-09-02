/**
 * Trade Plan — two parallel setups (Long Continuation + Short Fade) with
 * Trigger / Entry / Stop / Targets / R:R / Sizing.
 */
export default function TickerTradePlan({ tickerData }) {
  const synth = tickerData?.ai_synthesis
  const longSetup = synth?.trade_plan_long
  const shortSetup = synth?.trade_plan_short

  if (!longSetup && !shortSetup) {
    return (
      <div className="bg-[var(--color-bg)] rounded-3xl p-5">
        <div className="font-semibold mb-3 text-[13px]">Trade Plan</div>
        <div className="text-[var(--color-text-muted)] text-[13px]">
          Awaiting AI synthesis. Run <code className="bg-[var(--color-surface)] px-1 rounded">/tearsheet {tickerData?.ticker}</code> to generate.
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-3xl p-5">
      <div className="font-semibold mb-3 text-[13px] flex items-center justify-between">
        <span>Trade Plan</span>
        <span className="text-[11px] text-[var(--color-text-muted)] font-normal">for swing trading; not investment advice</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[13px]">
        {longSetup && <SetupCard tone="long" setup={longSetup} />}
        {shortSetup && <SetupCard tone="short" setup={shortSetup} />}
      </div>
      {synth?.earnings_risk_note && (
        <div className="mt-4 p-3 rounded bg-[color-mix(in_srgb,var(--color-signal-caution)_5%,transparent)] border border-[color-mix(in_srgb,var(--color-signal-caution)_30%,transparent)] text-[11px] text-[var(--color-text)]">
          <span className="font-semibold text-[var(--color-signal-caution)]">Earnings risk: </span>
          {synth.earnings_risk_note}
        </div>
      )}
    </div>
  )
}

function SetupCard({ tone, setup }) {
  const isLong = tone === 'long'
  const wrapClass = isLong
    ? 'bg-[color-mix(in_srgb,var(--color-profit)_5%,transparent)] border-[color-mix(in_srgb,var(--color-profit)_30%,transparent)]'
    : 'bg-[color-mix(in_srgb,var(--color-loss)_5%,transparent)] border-[color-mix(in_srgb,var(--color-loss)_30%,transparent)]'
  const headerClass = isLong ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'
  const heading = isLong ? 'LONG SETUP' : 'SHORT / FADE SETUP'

  return (
    <div className={`rounded p-3 border ${wrapClass} flex flex-col gap-2.5`}>
      <div className={`text-[11px] uppercase tracking-wide font-bold ${headerClass}`}>
        {heading}{setup.name ? ` — ${setup.name}` : ''}
      </div>
      <Row label="Trigger" value={setup.trigger} />
      <Row label="Entry zone" value={setup.entry_zone} />
      <Row label="Stop" value={setup.stop} />
      {setup.targets && setup.targets.length > 0 && (
        <Row
          label="Targets"
          value={(
            <ul className="list-disc pl-4 flex flex-col gap-0.5">
              {setup.targets.map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          )}
        />
      )}
      {setup.rr_note && <Row label="R:R" value={setup.rr_note} />}
      {setup.sizing_note && <Row label="Sizing" value={setup.sizing_note} />}
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex flex-col">
      <span className="text-[11px] uppercase tracking-wide text-[var(--color-text-muted)]">{label}</span>
      <span className="text-[var(--color-text)]">{value}</span>
    </div>
  )
}
