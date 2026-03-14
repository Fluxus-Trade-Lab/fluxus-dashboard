import { useState } from 'react'
import { useUniverse } from '../../hooks/useUniverse'
import { usePresets } from '../../hooks/usePresets'
import { applyFilters } from '../../lib/screenerFilter'
import PresetBar from './PresetBar'
import FilterPanel from './FilterPanel'
import ResultsTable from './ResultsTable'

const DEFAULT_FILTERS = {
  marketCapEnabled: true,
  marketCapMin: 1.0,
  vol50dEnabled: true,
  vol50dMin: 1.0,
  excludeHealthcare: false,
}

export default function ScreenerPage() {
  const { universe, loading } = useUniverse()
  const { allPresets, activePreset, setActivePreset, savePreset, deletePreset } = usePresets()
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [tickerSearch, setTickerSearch] = useState('')
  const [results, setResults] = useState(null)

  const handleSelectPreset = (preset) => {
    setActivePreset(preset)
    if (preset) {
      setFilters({ ...DEFAULT_FILTERS, ...preset.filters })
    }
  }

  const handleSave = (name) => {
    savePreset(name, filters)
  }

  const handleRun = () => {
    const filtered = applyFilters(universe, filters, tickerSearch)
    setResults(filtered)
  }

  const tickerList = results ? results.map(r => r.ticker).join(',') : ''

  if (loading) {
    return (
      <div className="text-stone-400 text-sm font-medium uppercase tracking-wide text-center py-20">
        Loading universe...
      </div>
    )
  }

  return (
    <div>
      <PresetBar
        presets={allPresets}
        activePreset={activePreset}
        onSelect={handleSelectPreset}
        onSave={handleSave}
        onDelete={(name) => { deletePreset(name); setActivePreset(null) }}
      />

      <FilterPanel
        filters={filters}
        onChange={setFilters}
        onSearch={setTickerSearch}
      />

      <div className="flex items-center gap-4 mb-4">
        <button
          onClick={handleRun}
          className="px-4 py-1.5 bg-green-600 text-white text-xs font-semibold uppercase tracking-wide rounded hover:bg-green-700"
        >
          Run Screener
        </button>
        {results && (
          <span className="text-green-600 text-sm font-semibold">
            {results.length} stocks matched
          </span>
        )}
      </div>

      {tickerList && (
        <div className="mb-4 p-2 bg-stone-50 border border-stone-200 rounded text-xs font-mono text-stone-600 break-all select-all">
          {tickerList}
        </div>
      )}

      {results && <ResultsTable rows={results} />}
    </div>
  )
}
