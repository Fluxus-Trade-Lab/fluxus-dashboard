export default function MarketMonitor({ data }) {
  const mm = data?.mm
  if (!mm) return null

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
        Stockbee Market Monitor
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Primary */}
        <div>
          <div className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
            Primary
          </div>
          <div className="flex flex-col gap-1">
            <Row label="Up 4% today" value={mm.up_4pct} />
            <Row label="Down 4% today" value={mm.down_4pct} />
            <Row label="Ratio 5D" value={mm.ratio_5d?.toFixed(2)} color={ratioColor(mm.ratio_5d)} />
            <Row label="Ratio 10D" value={mm.ratio_10d?.toFixed(2)} color={ratioColor(mm.ratio_10d)} />
            <Row label="Up 25% Qtr" value={mm.up_25pct_qtr} />
            <Row label="Down 25% Qtr" value={mm.down_25pct_qtr} />
          </div>
        </div>

        {/* Secondary */}
        <div>
          <div className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
            Secondary
          </div>
          <div className="flex flex-col gap-1">
            <Row label="Up 25% Mo" value={mm.up_25pct_month} />
            <Row label="Down 25% Mo" value={mm.down_25pct_month} />
            <Row label="Up 50% Mo" value={mm.up_50pct_month} />
            <Row label="Down 50% Mo" value={mm.down_50pct_month} />
          </div>
        </div>

        {/* Reference */}
        <div>
          <div className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
            Reference
          </div>
          <div className="flex flex-col gap-1">
            <Row label="Worden" value={data.universe_size?.toLocaleString()} />
            <Row
              label="T2108"
              value={data.breadth?.t2108 != null ? `${data.breadth.t2108.toFixed(1)}%` : '—'}
              color={pctColor(data.breadth?.t2108)}
            />
            <Row
              label="SPX"
              value={data.spx_close?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, color = '' }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[11px] text-[var(--color-text-secondary)]">{label}</span>
      <span className={`font-mono tabular-nums text-[12.5px] text-[var(--color-text)] ${color}`}>
        {value ?? '—'}
      </span>
    </div>
  )
}

/* Tints on the site's own tokens. These read `text-green-600 / text-amber-600
 * / text-red-500` — raw Tailwind, in no palette the brand declares, and
 * coloured type rather than a mark. */
function tint(level) {
  if (level === 'high') return 'bg-[color-mix(in_srgb,var(--color-took)_28%,transparent)] rounded-sm px-1'
  if (level === 'mid') return 'bg-[color-mix(in_srgb,var(--color-signal-caution)_20%,transparent)] rounded-sm px-1'
  return 'bg-[color-mix(in_srgb,var(--color-refused)_26%,transparent)] rounded-sm px-1'
}

function ratioColor(val) {
  if (val == null) return ''
  return tint(val >= 1.0 ? 'high' : val >= 0.5 ? 'mid' : 'low')
}

function pctColor(val) {
  if (val == null) return ''
  return tint(val >= 60 ? 'high' : val >= 40 ? 'mid' : 'low')
}
