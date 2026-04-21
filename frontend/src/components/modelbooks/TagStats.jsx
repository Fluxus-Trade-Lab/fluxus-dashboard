import { useState, useMemo } from 'react'

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

const ERA_FILTERS = [
  { label: 'All Time', value: 'all' },
  { label: '2020s', value: '2020' },
  { label: '2010s', value: '2010' },
  { label: '2000s', value: '2000' },
]

function formatPattern(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function getDecade(year) {
  return `${Math.floor(year / 10) * 10}`
}

export default function TagStats({ cards }) {
  const [era, setEra] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')

  // Derive unique sources
  const allSources = useMemo(() => {
    const set = new Set()
    cards.forEach(c => set.add(c.source))
    return [...set].sort()
  }, [cards])

  // Filter cards by era + source
  const filtered = useMemo(() => {
    return cards.filter(card => {
      if (era !== 'all' && getDecade(card.year) !== era) return false
      if (sourceFilter !== 'all' && card.source !== sourceFilter) return false
      return true
    })
  }, [cards, era, sourceFilter])

  // Count untagged
  const untaggedCount = useMemo(() => {
    return filtered.filter(c => !c.patterns || c.patterns.length === 0).length
  }, [filtered])

  // Compute per-pattern stats
  const stats = useMemo(() => {
    const map = {}

    for (const card of filtered) {
      for (const pattern of card.patterns) {
        if (!map[pattern]) {
          map[pattern] = { pattern, count: 0, gains: [], durations: [] }
        }
        map[pattern].count++
        if (card.gain_pct != null) map[pattern].gains.push(card.gain_pct)
        if (card.duration_days != null) map[pattern].durations.push(card.duration_days)
      }
    }

    return Object.values(map)
      .map(entry => ({
        pattern: entry.pattern,
        count: entry.count,
        avgGain: entry.gains.length > 0
          ? entry.gains.reduce((a, b) => a + b, 0) / entry.gains.length
          : null,
        avgDuration: entry.durations.length > 0
          ? entry.durations.reduce((a, b) => a + b, 0) / entry.durations.length
          : null,
      }))
      .sort((a, b) => b.count - a.count)
  }, [filtered])

  const maxCount = stats.length > 0 ? Math.max(...stats.map(s => s.count)) : 1
  const maxGain = Math.max(...stats.filter(s => s.avgGain != null).map(s => s.avgGain), 1)

  return (
    <div className="space-y-4">
      {/* Filters row */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Era toggles */}
        <div className="flex gap-1">
          {ERA_FILTERS.map(f => (
            <button
              key={f.value}
              onClick={() => setEra(f.value)}
              className={`px-2.5 py-1 text-[10px] font-medium rounded cursor-pointer transition-colors ${
                era === f.value
                  ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Source dropdown */}
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

        {/* Summary */}
        <span className="text-[10px] text-[var(--color-text-muted)] ml-auto">
          {filtered.length} setups
          {untaggedCount > 0 && (
            <span className="ml-2 text-amber-600 dark:text-amber-400">
              {untaggedCount} untagged
            </span>
          )}
        </span>
      </div>

      {/* Stats grid */}
      {stats.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-surface-alt)] gap-2">
          <span className="text-xs text-[var(--color-text-muted)]">No tagged patterns in this selection</span>
          {untaggedCount > 0 && (
            <span className="text-[10px] text-amber-600 dark:text-amber-400">
              {untaggedCount} setups need pattern tags
            </span>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {stats.map(({ pattern, count, avgGain, avgDuration }) => {
            const badgeColors = PATTERN_COLORS[pattern] || 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
            const countPct = (count / maxCount) * 100
            const gainPct = avgGain != null ? (avgGain / maxGain) * 100 : 0
            return (
              <div
                key={pattern}
                className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 space-y-2.5"
              >
                {/* Pattern badge */}
                <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded-full ${badgeColors}`}>
                  {formatPattern(pattern)}
                </span>

                {/* Stats with inline bars */}
                <div className="space-y-2">
                  <div>
                    <div className="flex items-baseline justify-between mb-0.5">
                      <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">Count</span>
                      <span className="text-[11px] font-semibold text-[var(--color-text)]">{count}</span>
                    </div>
                    <div className="w-full h-1 bg-[var(--color-border)] rounded-full overflow-hidden">
                      <div className="h-full bg-[var(--color-text-muted)] rounded-full" style={{ width: `${countPct}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-baseline justify-between mb-0.5">
                      <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">Avg Gain</span>
                      <span className="text-[11px] font-medium text-green-700 dark:text-green-400">
                        {avgGain != null ? `${avgGain.toFixed(0)}%` : '—'}
                      </span>
                    </div>
                    <div className="w-full h-1 bg-[var(--color-border)] rounded-full overflow-hidden">
                      <div className="h-full bg-green-500 dark:bg-green-600 rounded-full" style={{ width: `${gainPct}%` }} />
                    </div>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">Avg Duration</span>
                    <span className="text-[11px] font-medium text-[var(--color-text-secondary)]">
                      {avgDuration != null ? `${Math.round(avgDuration)}d` : '—'}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
