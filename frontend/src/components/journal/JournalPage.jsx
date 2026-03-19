import { useState } from 'react'
import AnalyticsTab from './AnalyticsTab'
import CoachTab from './CoachTab'
import RiskTab from './RiskTab'

const STRATEGIES = [
  { key: 'analytics', label: 'Analytics' },
  { key: 'risk', label: 'Risk Management' },
  { key: 'news-failure', label: 'News Failure' },
  { key: 'option-positioning', label: 'Option Positioning' },
  { key: 'tape-reading', label: 'Tape Reading' },
  { key: 'thematic-investing', label: 'Thematic Investing' },
  { key: 'episodic-pivot', label: 'Episodic Pivot' },
  { key: 'vcp', label: 'VCP' },
  { key: 'breakout', label: 'Breakout' },
]

const BLANK_TABS = ['news-failure', 'option-positioning', 'tape-reading', 'thematic-investing']

function BlankTab({ label }) {
  return (
    <div className="text-center py-20">
      <div className="text-sm font-semibold text-[var(--color-text-muted)] mb-2">{label}</div>
      <div className="text-xs text-[var(--color-text-muted)]">Coming soon</div>
    </div>
  )
}

export default function JournalPage() {
  const [activeStrategy, setActiveStrategy] = useState('analytics')

  const activeLabel = STRATEGIES.find(s => s.key === activeStrategy)?.label ?? ''

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      <h2 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-4">
        AI Coach
      </h2>

      {/* Strategy tabs */}
      <div className="flex gap-1 mb-5 flex-wrap">
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
      ) : activeStrategy === 'risk' ? (
        <RiskTab />
      ) : BLANK_TABS.includes(activeStrategy) ? (
        <BlankTab label={activeLabel} />
      ) : (
        <CoachTab strategy={activeStrategy} />
      )}
    </div>
  )
}
