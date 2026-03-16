export default function DateNav({ date, onChange }) {
  const shift = (days) => {
    const d = new Date(date)
    d.setDate(d.getDate() + days)
    onChange(d.toISOString().split('T')[0])
  }

  const fmtDate = (iso) => {
    const d = new Date(iso + 'T12:00:00')
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  }

  return (
    <div className="flex items-center gap-2">
      <button onClick={() => shift(-1)} className="px-2 py-0.5 text-xs text-stone-500 hover:text-stone-800 bg-transparent border border-stone-200 rounded cursor-pointer">
        &#9664;
      </button>
      <span className="text-xs font-mono text-stone-700 min-w-[120px] text-center">
        {fmtDate(date)}
      </span>
      <button onClick={() => shift(1)} className="px-2 py-0.5 text-xs text-stone-500 hover:text-stone-800 bg-transparent border border-stone-200 rounded cursor-pointer">
        &#9654;
      </button>
    </div>
  )
}
