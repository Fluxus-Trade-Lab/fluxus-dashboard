import { useState } from 'react'
import PageHeader from '../PageHeader'
import Reading, { readScreener } from '../Reading'
import { useHeatingUp } from '../../hooks/useHeatingUp'
import { useUniverse } from '../../hooks/useUniverse'
import { usePresets } from '../../hooks/usePresets'
import { applyFilters } from '../../lib/screenerFilter'
import PresetBar from './PresetBar'
import FilterPanel from './FilterPanel'
import ResultsTable from './ResultsTable'
import WatchlistTab from './WatchlistTab'
import HeatingUp from './HeatingUp'
import HowToRead from '../HowToRead'

const DEFAULT_FILTERS = {
  marketCapEnabled: true,
  marketCapMin: 1.0,
  vol50dEnabled: true,
  vol50dMin: 1.0,
  excludeHealthcare: false,
}

const TABS = ['Screener', 'Watchlist']

export default function ScreenerPage() {
  const { universe, loading } = useUniverse()
  const { allPresets, activePreset, setActivePreset, savePreset, deletePreset } = usePresets()
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [tickerSearch, setTickerSearch] = useState('')
  const [results, setResults] = useState(null)
  const [activeTab, setActiveTab] = useState(0)
  // Every hook runs before the `loading` early-return below. Calling this one
  // after it made the hook count change the moment the universe resolved, and
  // React tore the page down — the same conditional-hook bug already filed
  // against ExposureTab, committed here by the person who filed it.
  const heat = useHeatingUp()
  const [copied, setCopied] = useState(false)

  const handleSelectPreset = (preset) => {
    setActivePreset(preset)
    if (preset) {
      setFilters({ ...DEFAULT_FILTERS, ...preset.filters })
    }
  }

  const handleSave = (name) => {
    savePreset(name, filters)
  }

  const handleReset = () => {
    setFilters(DEFAULT_FILTERS)
    setTickerSearch('')
    setResults(null)
    setActivePreset(null)
  }

  const handleRun = () => {
    const filtered = applyFilters(universe, filters, tickerSearch)
    setResults(filtered)
  }

  const tickerList = results ? results.map(r => r.ticker).join(',') : ''

  if (loading) {
    return (
      <div className="text-[var(--color-text-muted)] text-sm font-medium uppercase tracking-wide text-center py-20">
        Loading universe...
      </div>
    )
  }


  return (
    <div>
      <PageHeader group="market" title="Screener"
        blurb="Seven screeners run every session. This ranks the names that show up in more than one of them — one mark is one appearance."
        meta={['quality tier — EP · VCP · MOM · weight ×3',
               'participation — 21D · 4% · CHART · VOL · weight ×1',
               'counts above 8 are printed, not drawn']} />
      {/* Page level, same as Themes and Market State. Counted over the rows the
          ledger actually renders, because the sentence says "here". */}
      <Reading text={readScreener(heat && { ...heat, rows: (heat.rows ?? []).slice(0, 25) })} />
      {/* Tab bar */}
      <div className="flex gap-0 border-b border-[var(--color-border)] mb-5" role="tablist">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === i}
            onClick={() => setActiveTab(i)}
            className={`px-5 py-2.5 font-semibold text-sm cursor-pointer bg-transparent border-none border-b-2 transition-colors ${
              activeTab === i
                ? 'border-green-600 text-green-600'
                : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 0 && (
        <>
          <PresetBar
            presets={allPresets}
            activePreset={activePreset}
            onSelect={handleSelectPreset}
            onSave={handleSave}
            onDelete={(name) => { deletePreset(name); setActivePreset(null) }}
            onReset={handleReset}
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
            <div className="mb-4 p-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-xs font-mono text-[var(--color-text-secondary)] break-all select-all flex items-start gap-2">
              <span className="flex-1">{tickerList}</span>
              <button
                onClick={() => { navigator.clipboard.writeText(tickerList).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500) }).catch(() => {}) }}
                className="shrink-0 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide border border-[var(--color-border)] rounded bg-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-text-secondary)] cursor-pointer transition-colors"
              >
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
          )}

          <div className="mb-4">
            <HeatingUp />
          </div>
          {results && <ResultsTable rows={results} />}
        </>
      )}

      {activeTab === 1 && (
        <WatchlistTab universe={universe} presets={allPresets} />
      )}

      <HowToRead>
        <p>
          The ledger is a record of <b>which screens a name cleared, on which
          sessions</b> — not a recommendation and not a ranking of quality. A name
          appears because it passed a test, and the test is named beside it.
        </p>
        <p>
          Heat is <b>how many screens a name cleared and how recently</b>, with the
          quality screens weighted more heavily. It is a count, not a score out of
          anything; the marks beside the number are the appearances that produced
          it, so the arithmetic is checkable by eye.
        </p>
        <p>
          Appearances are only counted from sessions the archive actually holds. Where
          a name's price history stops short of the last screener run, the rows that
          fall past the end are <b>counted out loud rather than silently dropped</b> —
          a gap in the record is a fact about the record, not about the stock.
        </p>
        <p>
          The filter panel narrows what you are looking at. It does not change what
          any mark means: <b>filtering never re-encodes</b>, so a bar you saw before
          filtering is the same bar afterwards.
        </p>
      </HowToRead>
    </div>
  )
}
