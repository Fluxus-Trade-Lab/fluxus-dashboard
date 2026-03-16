export default function ClassicBreadth({ data }) {
  const b = data?.breadth
  if (!b) return null

  return (
    <div className="bg-white border border-stone-200 rounded-lg p-5">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-3">
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
        <Stat
          label="McClellan"
          value={b.mcclellan_osc?.toFixed(1)}
          color={b.mcclellan_osc >= 0 ? 'text-green-600' : 'text-red-500'}
        />
      </div>
    </div>
  )
}

function Stat({ label, value, color = '' }) {
  return (
    <div className="bg-stone-50 rounded p-3">
      <div className="text-[10px] text-stone-500 font-medium uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className={`text-lg font-mono tabular-nums text-stone-900 ${color}`}>
        {value ?? '—'}
      </div>
    </div>
  )
}

function fmt1(val) {
  if (val == null) return '—'
  return `${val.toFixed(1)}%`
}

function pctColor(val) {
  if (val == null) return ''
  if (val >= 60) return 'text-green-600'
  if (val >= 40) return 'text-amber-600'
  return 'text-red-500'
}
