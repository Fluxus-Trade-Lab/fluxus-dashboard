import { useState } from 'react'
import AnalyticsTab from './AnalyticsTab'
import CoachTab from './CoachTab'
import RiskTab from './RiskTab'
import SizingTab from './SizingTab'
import PageHeader from '../PageHeader'
import HeadCoach from './HeadCoach'
import { STAGES } from './lib/headCoach'

/**
 * Four coaches and one head coach — formerly eighteen tabs.
 *
 * The eighteen were sorted by KIND of metric, so several answered the same
 * question and four were empty shells with "Coming soon" under them. These
 * four are sorted by WHEN the decision happens in a trade's life, which means
 * any trade lands in exactly one of them and the overlaps dissolve.
 *
 * The head coach does not add a fifth reading. It ranks these four by what
 * each left on the table per trade and names one, because a person changes one
 * thing at a time.
 *
 * The LLM chats (Episodic Pivot, VCP, Breakout) are setup conversations and
 * belong to Selection. News Failure, Option Positioning and Tape Reading were
 * never built and are gone rather than promised.
 */
const SECTIONS = {
  select: [
    { key: 'episodic-pivot', label: 'Episodic Pivot' },
    { key: 'vcp', label: 'VCP' },
    { key: 'breakout', label: 'Breakout' },
  ],
  size: [
    { key: 'sizing', label: 'Sizing' },
  ],
  hold: [
    { key: 'trim-stops', label: 'Trim & Stops' },
    { key: 'volatility', label: 'Volatility' },
  ],
  stop: [
    { key: 'risk', label: 'Risk Management' },
    { key: 'demon-finder', label: 'Demon Finder' },
    { key: 'behavior', label: 'Behavior' },
    { key: 'diagnosis', label: 'Diagnosis' },
  ],
}

/** Sections that live inside AnalyticsTab and are reached by its own key. */
const ANALYTICS_KEYS = new Set(['trim-stops', 'volatility', 'demon-finder', 'behavior', 'diagnosis'])

export default function JournalPage() {
  const [stage, setStage] = useState('hold')
  const [section, setSection] = useState(SECTIONS.hold[0].key)

  const pickStage = (key) => {
    setStage(key)
    setSection(SECTIONS[key][0].key)
  }

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      <PageHeader group="book" title="Review" />

      <HeadCoach onGo={pickStage} />

      {/* The four stages, in the order a trade lives through them. */}
      <div className="flex gap-1 mb-3 flex-wrap">
        {STAGES.map(({ key, label, asks }) => (
          <button
            key={key}
            onClick={() => pickStage(key)}
            title={asks}
            className={`px-3 py-1.5 text-[12px] font-medium rounded cursor-pointer transition-colors ${
              stage === key
                ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* What that stage asks, spelled out — four one-character labels are only
          legible to whoever wrote them. */}
      <p className="text-[11.5px] text-[var(--color-text-muted)] m-0 mb-3">
        {STAGES.find((s) => s.key === stage)?.asks}
      </p>

      <div className="flex gap-1 mb-5 flex-wrap">
        {SECTIONS[stage].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setSection(key)}
            className={`px-2.5 py-1 text-[11px] rounded cursor-pointer transition-colors ${
              section === key
                ? 'text-[var(--color-text)] font-semibold bg-[var(--color-hover-bg)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {section === 'sizing' ? (
        <SizingTab />
      ) : section === 'risk' ? (
        <RiskTab />
      ) : ANALYTICS_KEYS.has(section) ? (
        <AnalyticsTab initialSection={section} key={section} />
      ) : (
        <CoachTab strategy={section} />
      )}
    </div>
  )
}
