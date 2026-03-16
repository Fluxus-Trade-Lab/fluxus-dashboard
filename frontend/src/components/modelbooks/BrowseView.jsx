import { useState, useMemo } from 'react'

const PATTERN_COLORS = {
  cup_with_handle: 'bg-blue-50 text-blue-700',
  flat_base: 'bg-green-50 text-green-700',
  vcp: 'bg-purple-50 text-purple-700',
  high_tight_flag: 'bg-amber-50 text-amber-700',
  pocket_pivot: 'bg-cyan-50 text-cyan-700',
  episodic_pivot: 'bg-rose-50 text-rose-700',
  range_breakout: 'bg-orange-50 text-orange-700',
  base_on_base: 'bg-teal-50 text-teal-700',
  double_bottom: 'bg-indigo-50 text-indigo-700',
  ipo_base: 'bg-lime-50 text-lime-700',
  faulty_base: 'bg-red-50 text-red-600',
  cup_without_handle: 'bg-sky-50 text-sky-700',
}

function formatPattern(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function getDecade(year) {
  return `${Math.floor(year / 10) * 10}s`
}

function PatternBadge({ pattern }) {
  const colors = PATTERN_COLORS[pattern] || 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
  return (
    <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded-full ${colors}`}>
      {formatPattern(pattern)}
    </span>
  )
}

function CardDetail({ card, onClose }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30" />

      {/* Modal */}
      <div
        className="relative bg-[var(--color-surface)] rounded-lg border border-[var(--color-border)] shadow-lg max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 w-7 h-7 flex items-center justify-center rounded-full bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-hover-bg)] transition-colors cursor-pointer text-sm"
        >
          x
        </button>

        {/* Chart placeholder */}
        <div className="bg-[var(--color-surface-raised)] rounded-t-lg h-52 flex items-center justify-center">
          <span className="text-3xl font-bold text-[var(--color-text-muted)] tracking-wide">
            {card.ticker}
          </span>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          <div className="flex items-baseline justify-between">
            <h3 className="text-sm font-semibold text-[var(--color-text-bold)]">
              {card.ticker}
            </h3>
            <span className="text-xs text-[var(--color-text-muted)]">{card.year}</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
              Source
            </span>
            <span className="text-xs text-[var(--color-text-secondary)]">{card.source}</span>
          </div>

          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1.5">
              Patterns
            </span>
            <div className="flex flex-wrap gap-1.5">
              {card.patterns.map(p => (
                <PatternBadge key={p} pattern={p} />
              ))}
            </div>
          </div>

          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1.5">
              Key Lessons
            </span>
            <ul className="space-y-1">
              {card.key_lessons.map((lesson, i) => (
                <li key={i} className="text-xs text-[var(--color-text-secondary)] flex gap-2">
                  <span className="text-[var(--color-text-muted)] select-none shrink-0">&bull;</span>
                  {lesson}
                </li>
              ))}
            </ul>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
              Outcome
            </span>
            <span className="text-xs font-medium text-[var(--color-text)]">{card.outcome}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function BrowseView({ cards }) {
  const [patternFilter, setPatternFilter] = useState('all')
  const [eraFilter, setEraFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [selectedCard, setSelectedCard] = useState(null)

  // Derive unique filter options
  const allPatterns = useMemo(() => {
    const set = new Set()
    cards.forEach(c => c.patterns.forEach(p => set.add(p)))
    return [...set].sort()
  }, [cards])

  const allEras = useMemo(() => {
    const set = new Set()
    cards.forEach(c => set.add(getDecade(c.year)))
    return [...set].sort()
  }, [cards])

  const allSources = useMemo(() => {
    const set = new Set()
    cards.forEach(c => set.add(c.source))
    return [...set].sort()
  }, [cards])

  // Filter cards
  const filtered = useMemo(() => {
    return cards.filter(card => {
      if (patternFilter !== 'all' && !card.patterns.includes(patternFilter)) return false
      if (eraFilter !== 'all' && getDecade(card.year) !== eraFilter) return false
      if (sourceFilter !== 'all' && card.source !== sourceFilter) return false
      return true
    })
  }, [cards, patternFilter, eraFilter, sourceFilter])

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <select
          value={patternFilter}
          onChange={e => setPatternFilter(e.target.value)}
          className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-2 py-1.5 cursor-pointer focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
        >
          <option value="all">All Patterns</option>
          {allPatterns.map(p => (
            <option key={p} value={p}>{formatPattern(p)}</option>
          ))}
        </select>

        <select
          value={eraFilter}
          onChange={e => setEraFilter(e.target.value)}
          className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-2 py-1.5 cursor-pointer focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
        >
          <option value="all">All Eras</option>
          {allEras.map(e => (
            <option key={e} value={e}>{e}</option>
          ))}
        </select>

        <select
          value={sourceFilter}
          onChange={e => setSourceFilter(e.target.value)}
          className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-2 py-1.5 cursor-pointer focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
        >
          <option value="all">All Sources</option>
          {allSources.map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <span className="text-[10px] text-[var(--color-text-muted)] ml-1">
          {filtered.length} result{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Card grid */}
      {filtered.length === 0 ? (
        <div className="flex items-center justify-center h-48 rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-surface-alt)]">
          <span className="text-xs text-[var(--color-text-muted)]">No cards match the current filters</span>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {filtered.map(card => (
            <button
              key={card.id}
              onClick={() => setSelectedCard(card)}
              className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden text-left hover:border-[var(--color-input-border)] hover:shadow-sm transition-all cursor-pointer group"
            >
              {/* Chart placeholder */}
              <div className="bg-[var(--color-surface-raised)] h-40 flex items-center justify-center group-hover:bg-[var(--color-hover-bg)] transition-colors">
                <span className="text-xl font-bold text-[var(--color-text-muted)] tracking-wide group-hover:text-[var(--color-text-muted)] transition-colors">
                  {card.ticker}
                </span>
              </div>

              {/* Info */}
              <div className="p-3 space-y-2">
                <div className="flex items-baseline justify-between">
                  <span className="text-xs font-semibold text-[var(--color-text)]">{card.ticker}</span>
                  <span className="text-[10px] text-[var(--color-text-muted)]">{card.year}</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {card.patterns.map(p => (
                    <PatternBadge key={p} pattern={p} />
                  ))}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Detail modal */}
      {selectedCard && (
        <CardDetail card={selectedCard} onClose={() => setSelectedCard(null)} />
      )}
    </div>
  )
}
