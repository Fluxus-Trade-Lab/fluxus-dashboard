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
          className="rounded border-[var(--color-input-border)]"
        />
        <span className="text-xs text-[var(--color-text-secondary)]">{label}</span>
      </label>
      <div className="flex items-center gap-1">
        <span className="text-[10px] text-[var(--color-text-muted)]">Min</span>
        <input
          type="number"
          value={min}
          onChange={(e) => update('min', e.target.value)}
          className="border border-[var(--color-input-border)] rounded px-1.5 py-0.5 text-xs w-16 text-center"
          disabled={!enabled}
        />
        <button onClick={() => update('min', (Number(min) || 0) - 1)} disabled={!enabled}
          className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] text-xs disabled:opacity-30">-</button>
        <button onClick={() => update('min', (Number(min) || 0) + 1)} disabled={!enabled}
          className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] text-xs disabled:opacity-30">+</button>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-[10px] text-[var(--color-text-muted)]">Max</span>
        <input
          type="number"
          value={max}
          onChange={(e) => update('max', e.target.value)}
          className="border border-[var(--color-input-border)] rounded px-1.5 py-0.5 text-xs w-16 text-center"
          disabled={!enabled}
        />
        <button onClick={() => update('max', (Number(max) || 0) - 1)} disabled={!enabled}
          className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] text-xs disabled:opacity-30">-</button>
        <button onClick={() => update('max', (Number(max) || 0) + 1)} disabled={!enabled}
          className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] text-xs disabled:opacity-30">+</button>
      </div>
    </div>
  )
}
