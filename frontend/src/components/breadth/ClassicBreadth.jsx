export default function ClassicBreadth({ data }) {
  if (!data?.breadth) return null

  const b = data.breadth

  const mcColor =
    b.mcclellan_osc > 0 ? 'text-green-600' : b.mcclellan_osc < 0 ? 'text-red-500' : 'text-stone-700'

  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-3">
        Classic Breadth
      </h3>

      <div className="grid grid-cols-3 gap-3">
        {/* % Above MAs */}
        <div className="space-y-1">
          <PctBar label="% > 200 SMA" value={b.pct_above_200sma} />
          <PctBar label="% > 50 SMA" value={b.pct_above_50sma} />
          <PctBar label="% > 20 SMA" value={b.pct_above_20sma} />
        </div>

        {/* A/D */}
        <div className="space-y-1">
          <Row label="Advances" value={b.advances} className="text-green-600" />
          <Row label="Declines" value={b.declines} className="text-red-500" />
          <Row label="A/D Line" value={b.ad_line?.toLocaleString()} />
          <Row label="McClellan" value={b.mcclellan_osc} className={mcColor} />
        </div>

        {/* NH / NL */}
        <div className="space-y-1">
          <Row label="New Highs" value={b.new_highs} className="text-green-600" />
          <Row label="New Lows" value={b.new_lows} className="text-red-500" />
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

function PctBar({ label, value }) {
  const pct = value ?? 0
  const barColor =
    pct >= 60 ? 'bg-green-500' : pct >= 40 ? 'bg-amber-500' : 'bg-red-500'

  return (
    <div>
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[10px] font-medium uppercase tracking-wide text-stone-500">
          {label}
        </span>
        <span className="font-mono text-xs text-stone-700">
          {pct.toFixed(1)}%
        </span>
      </div>
      <div className="h-1 bg-stone-100 rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
