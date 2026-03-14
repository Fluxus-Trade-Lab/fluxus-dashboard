export default function RangeFilter({ label, filterKey, value, onChange }) {
  const enabled = value?.enabled || false
  const min = value?.min ?? ''
  const max = value?.max ?? ''

  const update = (field, val) => {
    onChange(filterKey, { ...value, enabled: true, [field]: val === '' ? '' : Number(val) })
  }

  return (
    <div className="flex items-center gap-2">
      <label className="flex items-center gap-1.5 min-w-[120px]">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => onChange(filterKey, { ...value, enabled: e.target.checked })}
          className="rounded border-stone-300"
        />
        <span className="text-xs text-stone-600">{label}</span>
      </label>
      <div className="flex items-center gap-1">
        <span className="text-[10px] text-stone-400">Min</span>
        <input
          type="number"
          value={min}
          onChange={(e) => update('min', e.target.value)}
          className="border border-stone-300 rounded px-1.5 py-0.5 text-xs w-16 text-center"
          disabled={!enabled}
        />
        <button onClick={() => update('min', (Number(min) || 0) - 1)} disabled={!enabled}
          className="text-stone-400 hover:text-stone-600 text-xs disabled:opacity-30">-</button>
        <button onClick={() => update('min', (Number(min) || 0) + 1)} disabled={!enabled}
          className="text-stone-400 hover:text-stone-600 text-xs disabled:opacity-30">+</button>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-[10px] text-stone-400">Max</span>
        <input
          type="number"
          value={max}
          onChange={(e) => update('max', e.target.value)}
          className="border border-stone-300 rounded px-1.5 py-0.5 text-xs w-16 text-center"
          disabled={!enabled}
        />
        <button onClick={() => update('max', (Number(max) || 0) - 1)} disabled={!enabled}
          className="text-stone-400 hover:text-stone-600 text-xs disabled:opacity-30">-</button>
        <button onClick={() => update('max', (Number(max) || 0) + 1)} disabled={!enabled}
          className="text-stone-400 hover:text-stone-600 text-xs disabled:opacity-30">+</button>
      </div>
    </div>
  )
}
