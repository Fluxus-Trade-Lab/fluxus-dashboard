import { useState } from 'react'

export default function PresetBar({ presets, activePreset, onSelect, onSave, onDelete, onReset }) {
  const [newName, setNewName] = useState('')

  const handleSave = () => {
    const name = newName.trim()
    if (name) {
      onSave(name)
      setNewName('')
    } else if (activePreset && !activePreset.readonly) {
      onSave(activePreset.name)
    }
  }

  return (
    <div className="flex items-center gap-3 mb-4 flex-wrap">
      <label className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
        Select Strategy Preset
      </label>
      <select
        value={activePreset?.name || ''}
        onChange={(e) => {
          const p = presets.find(p => p.name === e.target.value)
          onSelect(p || null)
        }}
        className="border border-[var(--color-input-border)] rounded px-2 py-1 text-sm bg-[var(--color-input-bg)] min-w-[200px]"
      >
        <option value="">— None —</option>
        {presets.map(p => (
          <option key={p.name} value={p.name}>{p.name}</option>
        ))}
      </select>

      {activePreset && !activePreset.readonly && (
        <button
          onClick={() => onDelete(activePreset.name)}
          className="text-xs px-2 py-1 border border-[var(--color-input-border)] rounded hover:bg-[var(--color-hover-bg)]"
        >
          Delete
        </button>
      )}

      <button
        onClick={onReset}
        className="text-xs px-2 py-1 border border-[var(--color-input-border)] rounded hover:bg-[var(--color-hover-bg)] text-[var(--color-text-muted)]"
      >
        Reset Filters
      </button>

      <div className="flex items-center gap-2 ml-auto">
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="border border-[var(--color-input-border)] rounded px-2 py-1 text-sm w-40"
          placeholder="New preset name"
        />
        <button
          onClick={handleSave}
          className="text-xs px-3 py-1 border border-[var(--color-input-border)] rounded hover:bg-[var(--color-hover-bg)] font-medium"
        >
          {!newName.trim() && activePreset && !activePreset.readonly ? 'Update Preset' : 'Save Current Settings'}
        </button>
      </div>
    </div>
  )
}
