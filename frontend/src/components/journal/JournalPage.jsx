import { useState } from 'react'
import AnalyticsTab from './AnalyticsTab'
import CoachTab from './CoachTab'

const STRATEGIES = [
  { key: 'analytics', label: 'Analytics' },
  { key: 'episodic-pivot', label: 'Episodic Pivot' },
  { key: 'vcp', label: 'VCP' },
  { key: 'breakout', label: 'Breakout' },
]

export default function JournalPage() {
  const [activeStrategy, setActiveStrategy] = useState('analytics')

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      <h2 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-4">
        AI Coach
      </h2>

      {/* Strategy tabs */}
      <div className="flex gap-1 mb-5">
        {STRATEGIES.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveStrategy(key)}
            className={`px-3 py-1.5 text-[11px] font-medium rounded cursor-pointer transition-colors ${
              activeStrategy === key
                ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {activeStrategy === 'analytics' ? (
        <AnalyticsTab />
      ) : (
        <CoachTab strategy={activeStrategy} />
      )}
    </div>
  )
}
