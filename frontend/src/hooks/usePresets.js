import { useState, useEffect } from 'react'

const LS_KEY = 'fluxus-screener-presets'

export function usePresets() {
  const [defaults, setDefaults] = useState([])
  const [custom, setCustom] = useState([])
  const [activePreset, setActivePreset] = useState(null)

  useEffect(() => {
    fetch('/data/screener-presets.json')
      .then(r => r.json())
      .then(setDefaults)
      .catch(() => {})

    try {
      const stored = JSON.parse(localStorage.getItem(LS_KEY) || '[]')
      setCustom(stored)
    } catch { setCustom([]) }
  }, [])

  const allPresets = [...defaults, ...custom]

  const savePreset = (name, filters) => {
    const preset = { name, readonly: false, filters }
    const updated = [...custom.filter(p => p.name !== name), preset]
    setCustom(updated)
    localStorage.setItem(LS_KEY, JSON.stringify(updated))
  }

  const deletePreset = (name) => {
    const updated = custom.filter(p => p.name !== name)
    setCustom(updated)
    localStorage.setItem(LS_KEY, JSON.stringify(updated))
  }

  return { allPresets, activePreset, setActivePreset, savePreset, deletePreset }
}
