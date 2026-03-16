export default function MarketMonitor({ data }) {
  if (!data) return null

  const mm = data.mm || {}
  const breadth = data.breadth || {}

  const ratioColor = (val) =>
    val >= 2.0 ? 'text-green-600' : val <= 0.5 ? 'text-red-500' : 'text-stone-700'

  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-3">
        Stockbee Market Monitor
      </h3>

      <div className="grid grid-cols-3 gap-3">
        {/* Primary */}
        <div>
          <div className="text-[9px] font-medium uppercase tracking-wide text-stone-400 mb-2">
            Primary
          </div>
          <div className="space-y-1">
            <Row label="Up 4%" value={mm.up_4pct} />
            <Row label="Down 4%" value={mm.down_4pct} />
            <Row
              label="Ratio 5D"
              value={mm.ratio_5d?.toFixed(2)}
              className={ratioColor(mm.ratio_5d)}
            />
            <Row
              label="Ratio 10D"
              value={mm.ratio_10d?.toFixed(2)}
              className={ratioColor(mm.ratio_10d)}
            />
            <Row label="Up 25% Qtr" value={mm.up_25pct_qtr} />
            <Row label="Down 25% Qtr" value={mm.down_25pct_qtr} />
          </div>
        </div>

        {/* Secondary */}
        <div>
          <div className="text-[9px] font-medium uppercase tracking-wide text-stone-400 mb-2">
            Secondary
          </div>
          <div className="space-y-1">
            <Row label="Up 25% Mo" value={mm.up_25pct_month} />
            <Row label="Down 25% Mo" value={mm.down_25pct_month} />
            <Row label="Up 50% Mo" value={mm.up_50pct_month} />
            <Row label="Down 50% Mo" value={mm.down_50pct_month} />
          </div>
        </div>

        {/* Reference */}
        <div>
          <div className="text-[9px] font-medium uppercase tracking-wide text-stone-400 mb-2">
            Reference
          </div>
          <div className="space-y-1">
            <Row label="Worden" value={data.universe_size?.toLocaleString()} />
            <Row
              label="T2108"
              value={breadth.t2108 != null ? `${breadth.t2108}%` : '\u2014'}
            />
            <Row
              label="SPX"
              value={data.spx_close != null ? data.spx_close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '\u2014'}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, className = 'text-stone-700' }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[10px] font-medium uppercase tracking-wide text-stone-500">
        {label}
      </span>
      <span className={`font-mono text-xs ${className}`}>
        {value ?? '\u2014'}
      </span>
    </div>
  )
}
