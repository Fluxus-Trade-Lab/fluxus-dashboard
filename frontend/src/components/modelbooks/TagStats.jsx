import { useMemo } from 'react'

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

export default function TagStats({ cards }) {
  const stats = useMemo(() => {
    const map = {}

    for (const card of cards) {
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
  }, [cards])

  if (stats.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-surface-alt)]">
        <span className="text-xs text-[var(--color-text-muted)]">No pattern data available</span>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
      {stats.map(({ pattern, count, avgGain, avgDuration }) => {
        const badgeColors = PATTERN_COLORS[pattern] || 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
        return (
          <div
            key={pattern}
            className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 space-y-2.5"
          >
            {/* Pattern badge */}
            <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded-full ${badgeColors}`}>
              {formatPattern(pattern)}
            </span>

            {/* Stats */}
            <div className="space-y-1.5">
              <div className="flex items-baseline justify-between">
                <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">Count</span>
                <span className="text-[11px] font-semibold text-[var(--color-text)]">{count}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">Avg Gain</span>
                <span className="text-[11px] font-medium text-[var(--color-text-secondary)]">
                  {avgGain != null ? `${avgGain.toFixed(1)}%` : '—'}
                </span>
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
  )
}
