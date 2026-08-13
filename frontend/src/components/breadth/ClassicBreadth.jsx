export default function ClassicBreadth({ data }) {
  const b = data?.breadth
  if (!b) return null

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
        Classic Breadth
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        <Stat label="% > 200 SMA" value={fmt1(b.pct_above_200sma)} color={pctColor(b.pct_above_200sma)} />
        <Stat label="% > 50 SMA" value={fmt1(b.pct_above_50sma)} color={pctColor(b.pct_above_50sma)} />
        <Stat label="% > 20 SMA" value={fmt1(b.pct_above_20sma)} color={pctColor(b.pct_above_20sma)} />
        <Stat label="Advances" value={b.advances?.toLocaleString()} />
        <Stat label="Declines" value={b.declines?.toLocaleString()} />
        <Stat label="New Highs" value={b.new_highs?.toLocaleString()} />
        <Stat label="New Lows" value={b.new_lows?.toLocaleString()} />
        <Stat label="A/D Line" value={b.ad_line?.toLocaleString()} />
        {/* neutral like its five neighbours — the sign is on the number */}
        <Stat label="McClellan" value={b.mcclellan_osc?.toFixed(1)} />
      </div>
    </div>
  )
}

function Stat({ label, value, color = '' }) {
  return (
    <div className="bg-[var(--color-bg)] rounded p-3">
      <div className="text-[10px] text-[var(--color-text-secondary)] font-medium uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className={`text-lg font-mono tabular-nums text-[var(--color-text)] ${color}`}>
        {value ?? '—'}
      </div>
    </div>
  )
}

function fmt1(val) {
  if (val == null) return '—'
  return `${val.toFixed(1)}%`
}

/* a tint behind the figure, not coloured type — the same construction the
 * breadth table and the screener's RS cells use */
function pctColor(val) {
  if (val == null) return ''
  if (val >= 60) return 'bg-[color-mix(in_srgb,var(--color-took)_28%,transparent)] rounded-sm px-1'
  if (val >= 40) return 'bg-[color-mix(in_srgb,var(--color-signal-caution)_20%,transparent)] rounded-sm px-1'
  return 'bg-[color-mix(in_srgb,var(--color-refused)_26%,transparent)] rounded-sm px-1'
}
