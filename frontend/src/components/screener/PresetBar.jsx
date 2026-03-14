import { useState } from 'react'

export default function PresetBar({ presets, activePreset, onSelect, onSave, onDelete }) {
  const [newName, setNewName] = useState('')

  return (
    <div className="flex items-center gap-3 mb-4 flex-wrap">
      <label className="text-xs font-medium uppercase tracking-wide text-stone-500">
        Select Strategy Preset
      </label>
      <select
        value={activePreset?.name || ''}
        onChange={(e) => {
          const p = presets.find(p => p.name === e.target.value)
          onSelect(p || null)
        }}
        className="border border-stone-300 rounded px-2 py-1 text-sm bg-white min-w-[200px]"
      >
        <option value="">— None —</option>
        {presets.map(p => (
          <option key={p.name} value={p.name}>{p.name}</option>
        ))}
      </select>

      {activePreset && !activePreset.readonly && (
        <button
          onClick={() => onDelete(activePreset.name)}
          className="text-xs px-2 py-1 border border-stone-300 rounded hover:bg-stone-100"
        >
          Delete Selected Preset
        </button>
      )}

      <div className="flex items-center gap-2 ml-auto">
        <label className="text-xs font-medium uppercase tracking-wide text-stone-500">
          New Preset Name
        </label>
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="border border-stone-300 rounded px-2 py-1 text-sm w-40"
          placeholder=""
        />
        <button
          onClick={() => {
            if (newName.trim()) {
              onSave(newName.trim())
              setNewName('')
            }
          }}
          className="text-xs px-3 py-1 border border-stone-300 rounded hover:bg-stone-100 font-medium"
        >
          Save Current Settings
        </button>
      </div>
    </div>
  )
}
