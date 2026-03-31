import { useState, useMemo, useEffect, useCallback } from 'react'
import OhlcvChart from './OhlcvChart'

/* -- Constants ---------------------------------------------------------- */

const PATTERN_COLORS = {
  cup_with_handle: 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  flat_base: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300',
  vcp: 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300',
  high_tight_flag: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  pocket_pivot: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300',
  episodic_pivot: 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300',
  range_breakout: 'bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300',
  base_on_base: 'bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300',
  double_bottom: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300',
  ipo_base: 'bg-lime-50 text-lime-700 dark:bg-lime-950 dark:text-lime-300',
  faulty_base: 'bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400',
  cup_without_handle: 'bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-300',
}

const TABLE_COLUMNS = [
  { key: 'ticker', label: 'Ticker', width: 'w-14' },
  { key: 'year', label: 'Year', width: 'w-12' },
  { key: 'patterns', label: 'Pattern(s)', width: 'w-24' },
  { key: 'gain_pct', label: 'Gain%', width: 'w-14' },
  { key: 'source', label: 'Src', width: 'w-16' },
]

/* Source abbreviation map */
const SOURCE_ABBREV = {
  'Mark Minervini': 'MM',
  'William O\'Neil': 'WON',
  'IBD': 'IBD',
  'Stan Weinstein': 'SW',
  'Nicolas Darvas': 'ND',
  'Jesse Livermore': 'JL',
  'Richard Dennis': 'RD',
}

function abbreviateSource(source) {
  if (!source) return '\u2014'
  if (SOURCE_ABBREV[source]) return SOURCE_ABBREV[source]
  // Abbreviate: take initials of multi-word, or first 3 chars
  const words = source.split(/\s+/)
  if (words.length >= 2) return words.map(w => w[0]).join('').toUpperCase()
  return source.length > 4 ? source.slice(0, 4) : source
}

/* -- Helpers ------------------------------------------------------------ */

function formatPattern(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function PatternBadge({ pattern }) {
  const colors = PATTERN_COLORS[pattern] || 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
  return (
    <span className={`inline-block px-1.5 py-0.5 text-[9px] font-medium rounded-full ${colors} leading-tight`}>
      {formatPattern(pattern)}
    </span>
  )
}

function matchesSearch(card, query) {
  const q = query.toLowerCase()
  if (card.ticker.toLowerCase().includes(q)) return true
  if (card.outcome?.toLowerCase().includes(q)) return true
  if (card.key_lessons?.some(l => l.toLowerCase().includes(q))) return true
  return false
}

/* -- Sort comparator ---------------------------------------------------- */

function compareEntries(a, b, sortKey, sortDir) {
  let av, bv
  if (sortKey === 'patterns') {
    av = a.patterns?.[0] || ''
    bv = b.patterns?.[0] || ''
  } else {
    av = a[sortKey]
    bv = b[sortKey]
  }
  if (av == null && bv == null) return 0
  if (av == null) return 1
  if (bv == null) return -1
  if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
  return sortDir === 'asc' ? av - bv : bv - av
}

/* -- Notes Panel -------------------------------------------------------- */

function NotesPanel({ entry, onTickerClick }) {
  if (!entry) {
    return (
      <div className="flex items-center justify-center h-48 rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-surface-alt)]">
        <span className="text-xs text-[var(--color-text-muted)]">Select an entry to view details</span>
      </div>
    )
  }

  return (
    <div className="p-4 border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] space-y-3">
      {/* Ticker + year */}
      <div>
        <button
          onClick={() => onTickerClick(entry.ticker)}
          className="text-base font-semibold text-[var(--color-text-bold)] hover:text-blue-700 dark:hover:text-blue-400 hover:underline cursor-pointer"
        >
          {entry.ticker}
        </button>
        <span className="ml-2 text-xs text-[var(--color-text-muted)]">{entry.year}</span>
      </div>

      {/* Source */}
      <p className="text-[11px] text-[var(--color-text-muted)]">{entry.source}</p>

      {/* Pattern badges */}
      {entry.patterns.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {entry.patterns.map(p => (
            <PatternBadge key={p} pattern={p} />
          ))}
        </div>
      )}

      {/* Gain + Duration stat row */}
      <div className="flex items-center gap-4 text-xs">
        {entry.gain_pct != null && (
          <span>
            <span className="text-[var(--color-text-muted)]">Gain </span>
            <span className={`font-semibold ${entry.gain_pct > 0 ? 'text-green-700 dark:text-green-400' : 'text-[var(--color-text-secondary)]'}`}>
              {entry.gain_pct.toFixed(1)}%
            </span>
          </span>
        )}
        {entry.duration_days != null && (
          <span>
            <span className="text-[var(--color-text-muted)]">Duration </span>
            <span className="font-medium text-[var(--color-text)]">{entry.duration_days}d</span>
          </span>
        )}
      </div>

      {/* Key lessons as margin notes */}
      {entry.key_lessons?.length > 0 ? (
        <div className="space-y-2 pt-1">
          <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">
            Key Lessons
          </span>
          {entry.key_lessons.map((lesson, i) => (
            <blockquote
              key={i}
              className="border-l-2 border-[var(--color-border)] pl-3 text-xs italic text-[var(--color-text-secondary)] leading-relaxed"
            >
              {lesson}
            </blockquote>
          ))}
        </div>
      ) : (
        <p className="text-[11px] text-[var(--color-text-muted)] italic pt-1">No annotations yet</p>
      )}

      {/* Outcome */}
      {entry.outcome && (
        <p className="text-[11px] text-[var(--color-text-muted)] pt-1 border-t border-[var(--color-border-light)]">
          {entry.outcome}
        </p>
      )}
    </div>
  )
}

/* -- Main Component ----------------------------------------------------- */

export default function BrowseView({ cards }) {
  const [patternFilter, setPatternFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('gain_pct')
  const [sortDir, setSortDir] = useState('desc')
  const [selectedId, setSelectedId] = useState(null)
  const [ohlcvData, setOhlcvData] = useState(null)
  const [ohlcvLoading, setOhlcvLoading] = useState(false)
  const [showSpy, setShowSpy] = useState(false)
  const [spyData, setSpyData] = useState(null)
  const [isLg, setIsLg] = useState(() => window.matchMedia('(min-width: 1024px)').matches)
  const [isMd, setIsMd] = useState(() => window.matchMedia('(min-width: 768px)').matches)

  // Responsive breakpoints
  useEffect(() => {
    const lgMql = window.matchMedia('(min-width: 1024px)')
    const mdMql = window.matchMedia('(min-width: 768px)')
    const lgHandler = (e) => setIsLg(e.matches)
    const mdHandler = (e) => setIsMd(e.matches)
    lgMql.addEventListener('change', lgHandler)
    mdMql.addEventListener('change', mdHandler)
    return () => {
      lgMql.removeEventListener('change', lgHandler)
      mdMql.removeEventListener('change', mdHandler)
    }
  }, [])

  const chartHeight = isLg ? 350 : 280

  // Derive unique filter options
  const allPatterns = useMemo(() => {
    const set = new Set()
    cards.forEach(c => c.patterns.forEach(p => set.add(p)))
    return [...set].sort()
  }, [cards])

  const allSources = useMemo(() => {
    const set = new Set()
    cards.forEach(c => set.add(c.source))
    return [...set].sort()
  }, [cards])

  // Filter + sort
  const filtered = useMemo(() => {
    let result = cards.filter(card => {
      if (patternFilter !== 'all' && !card.patterns.includes(patternFilter)) return false
      if (sourceFilter !== 'all' && card.source !== sourceFilter) return false
      if (search && !matchesSearch(card, search)) return false
      return true
    })
    return result.sort((a, b) => compareEntries(a, b, sortKey, sortDir))
  }, [cards, patternFilter, sourceFilter, search, sortKey, sortDir])

  // Selected entry
  const selectedEntry = useMemo(() => {
    if (!selectedId) return filtered[0] || null
    return filtered.find(c => c.id === selectedId) || filtered[0] || null
  }, [filtered, selectedId])

  // Auto-select first entry on load or when filters change
  useEffect(() => {
    if (filtered.length > 0 && !filtered.find(c => c.id === selectedId)) {
      setSelectedId(filtered[0].id)
    }
  }, [filtered]) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-select first on mount
  useEffect(() => {
    if (cards.length > 0 && !selectedId) {
      const sorted = [...cards].sort((a, b) => (b.gain_pct || 0) - (a.gain_pct || 0))
      setSelectedId(sorted[0].id)
    }
  }, [cards]) // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch OHLCV on selection change
  useEffect(() => {
    if (!selectedEntry?.ohlcv_file) {
      setOhlcvData(null)
      return
    }

    let cancelled = false
    setOhlcvLoading(true)
    setOhlcvData(null)

    fetch(`/data/modelbooks/${selectedEntry.ohlcv_file}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        if (!cancelled) {
          setOhlcvData(data)
          setOhlcvLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setOhlcvData(null)
          setOhlcvLoading(false)
        }
      })

    return () => { cancelled = true }
  }, [selectedEntry?.id, selectedEntry?.ohlcv_file])

  // Fetch SPY OHLCV when overlay is enabled
  useEffect(() => {
    if (!showSpy || !selectedEntry || !ohlcvData?.length) {
      setSpyData(null)
      return
    }

    let cancelled = false
    const year = selectedEntry.year

    fetch(`/data/modelbooks/ohlcv/spy-${year}.json`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        if (cancelled) return
        const firstTime = ohlcvData[0].time
        const lastTime = ohlcvData[ohlcvData.length - 1].time
        const filtered = data.filter(d => d.time >= firstTime && d.time <= lastTime)
        setSpyData(filtered.length > 0 ? filtered : null)
      })
      .catch(() => {
        if (!cancelled) setSpyData(null)
      })

    return () => { cancelled = true }
  }, [showSpy, selectedEntry?.id, selectedEntry?.year, ohlcvData])

  const toggleSort = useCallback((key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }, [sortKey])

  // Keyboard navigation: arrow keys to browse entries
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
      if (!filtered.length) return

      const currentIdx = filtered.findIndex(c => c.id === selectedEntry?.id)
      if (e.key === 'ArrowDown' || e.key === 'j') {
        e.preventDefault()
        const next = Math.min(currentIdx + 1, filtered.length - 1)
        setSelectedId(filtered[next].id)
        document.querySelector(`[data-entry-id="${filtered[next].id}"]`)?.scrollIntoView({ block: 'nearest' })
      } else if (e.key === 'ArrowUp' || e.key === 'k') {
        e.preventDefault()
        const prev = Math.max(currentIdx - 1, 0)
        setSelectedId(filtered[prev].id)
        document.querySelector(`[data-entry-id="${filtered[prev].id}"]`)?.scrollIntoView({ block: 'nearest' })
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [filtered, selectedEntry?.id])

  // Per-ticker drill-down: clicking ticker in notes panel filters the table
  const handleTickerClick = useCallback((ticker) => {
    setSearch(ticker)
  }, [])

  /* -- Chart block (reused in both layouts) ----------------------------- */
  const chartBlock = selectedEntry ? (
    <div className="flex flex-col min-h-0">
      {/* Chart header (SPY toggle only -- ticker info moved to notes panel) */}
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-sm font-semibold text-[var(--color-text-bold)]">
          {selectedEntry.ticker}
        </h3>
        <span className="text-xs text-[var(--color-text-muted)]">{selectedEntry.year}</span>
        <button
          onClick={() => setShowSpy(s => !s)}
          className={`ml-auto text-[10px] font-medium px-2 py-1 rounded border transition-colors ${
            showSpy
              ? 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950 dark:text-indigo-300 dark:border-indigo-800'
              : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] border-[var(--color-border)] hover:text-[var(--color-text-secondary)]'
          }`}
        >
          SPY Overlay
        </button>
      </div>

      <div className="border border-[var(--color-border)] rounded-lg overflow-hidden bg-[var(--color-surface)]">
        {ohlcvLoading ? (
          <div className="flex items-center justify-center text-xs text-[var(--color-text-muted)]" style={{ height: chartHeight }}>
            Loading chart data...
          </div>
        ) : !selectedEntry.ohlcv_file ? (
          <div className="flex items-center justify-center text-xs text-[var(--color-text-muted)]" style={{ height: chartHeight }}>
            No chart data available for this entry
          </div>
        ) : (
          <OhlcvChart data={ohlcvData} height={chartHeight} spyData={showSpy ? spyData : null} showControls />
        )}
      </div>
    </div>
  ) : (
    <div className="flex items-center justify-center h-64 rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-surface-alt)]">
      <span className="text-xs text-[var(--color-text-muted)]">Select an entry to view its chart</span>
    </div>
  )

  const notesBlock = <NotesPanel entry={selectedEntry} onTickerClick={handleTickerClick} />

  /* -- Filter table ----------------------------------------------------- */
  const tableBlock = (
    <div className="flex flex-col min-h-0 h-full">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <input
          type="text"
          placeholder="Search ticker, lessons..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-2 py-1.5 w-36 focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
        />
        <select
          value={patternFilter}
          onChange={e => setPatternFilter(e.target.value)}
          className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-1.5 py-1.5 cursor-pointer focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
        >
          <option value="all">All Patterns</option>
          {allPatterns.map(p => (
            <option key={p} value={p}>{formatPattern(p)}</option>
          ))}
        </select>
        <select
          value={sourceFilter}
          onChange={e => setSourceFilter(e.target.value)}
          className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-1.5 py-1.5 cursor-pointer focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
        >
          <option value="all">All Sources</option>
          {allSources.map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <span className="text-[10px] text-[var(--color-text-muted)] ml-auto">
          {filtered.length}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-y-auto border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] flex-1 max-h-[40vh] lg:max-h-none">
        <table className="w-full text-xs">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-[var(--color-border)] bg-[var(--color-bg)]">
              {TABLE_COLUMNS.map(col => (
                <th
                  key={col.key}
                  onClick={() => toggleSort(col.key)}
                  className={`px-1.5 py-1.5 text-left cursor-pointer hover:bg-[var(--color-hover-bg)] font-medium text-[10px] text-[var(--color-text-secondary)] uppercase tracking-wide ${col.width}`}
                >
                  {col.label}
                  {sortKey === col.key && (sortDir === 'asc' ? ' \u2191' : ' \u2193')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={TABLE_COLUMNS.length} className="px-4 py-8 text-center text-xs text-[var(--color-text-muted)]">
                  No entries match the current filters
                </td>
              </tr>
            ) : (
              filtered.map(card => {
                const isSelected = selectedEntry?.id === card.id
                return (
                  <tr
                    key={card.id}
                    data-entry-id={card.id}
                    onClick={() => setSelectedId(card.id)}
                    className={`border-b border-[var(--color-border-light)] cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-[var(--color-hover-bg)] ring-1 ring-inset ring-[var(--color-input-border)]'
                        : 'even:bg-[var(--color-surface-alt)] hover:bg-[var(--color-hover-bg)]'
                    }`}
                  >
                    <td className="px-1.5 py-1.5 text-[11px] font-semibold text-blue-700 dark:text-blue-400">{card.ticker}</td>
                    <td className="px-1.5 py-1.5 text-[10px] text-[var(--color-text-secondary)] font-mono">{card.year}</td>
                    <td className="px-1.5 py-1.5">
                      <div className="flex flex-wrap gap-0.5">
                        {card.patterns.slice(0, 2).map(p => (
                          <PatternBadge key={p} pattern={p} />
                        ))}
                        {card.patterns.length > 2 && (
                          <span className="text-[9px] text-[var(--color-text-muted)]">+{card.patterns.length - 2}</span>
                        )}
                      </div>
                    </td>
                    <td className={`px-1.5 py-1.5 text-[11px] font-mono ${
                      card.gain_pct != null && card.gain_pct > 0 ? 'text-green-700 dark:text-green-400' : 'text-[var(--color-text-secondary)]'
                    }`}>
                      {card.gain_pct != null ? `${card.gain_pct.toFixed(0)}%` : '\u2014'}
                    </td>
                    <td className="px-1.5 py-1.5 text-[10px] text-[var(--color-text-muted)] truncate max-w-[60px]" title={card.source}>
                      {abbreviateSource(card.source)}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )

  /* -- Layout ----------------------------------------------------------- */

  // Desktop (lg+): 22% | 48% | 30%
  if (isLg) {
    return (
      <div className="flex gap-4" style={{ minHeight: 0 }}>
        <div className="flex flex-col min-h-0" style={{ width: '22%', flexShrink: 0 }}>
          {tableBlock}
        </div>
        <div className="flex flex-col min-h-0 sticky top-4 self-start" style={{ width: '48%', flexShrink: 0 }}>
          {chartBlock}
        </div>
        <div className="flex flex-col min-h-0 sticky top-4 self-start" style={{ width: '30%', flexShrink: 0 }}>
          {notesBlock}
        </div>
      </div>
    )
  }

  // Tablet (md to lg): 35% table | 65% (chart stacked above notes)
  if (isMd) {
    return (
      <div className="flex gap-4" style={{ minHeight: 0 }}>
        <div className="flex flex-col min-h-0" style={{ width: '35%', flexShrink: 0 }}>
          {tableBlock}
        </div>
        <div className="flex flex-col gap-4 min-h-0" style={{ width: '65%', flexShrink: 0 }}>
          {chartBlock}
          {notesBlock}
        </div>
      </div>
    )
  }

  // Mobile: vertical stack
  return (
    <div className="flex flex-col gap-4">
      {tableBlock}
      {chartBlock}
      {notesBlock}
    </div>
  )
}
