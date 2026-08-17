import { useState } from 'react'
import AnalyticsTab from './AnalyticsTab'
import CoachTab from './CoachTab'
import RiskTab from './RiskTab'
import SizingTab from './SizingTab'
import PageHeader from '../PageHeader'
import { useLanguage } from '../../i18n/LanguageContext'
import HeadCoach from './HeadCoach'
import HoldCaptureSection from './analytics/HoldCaptureSection'
import AfterLossSection from './analytics/AfterLossSection'
import SetupEdgeSection from './analytics/SetupEdgeSection'
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
    // First, because it tests whether this stage is a lever at all.
    { key: 'setup-edge', label: 'Setup edge' },
    { key: 'episodic-pivot', label: 'Episodic Pivot' },
    { key: 'vcp', label: 'VCP' },
    { key: 'breakout', label: 'Breakout' },
  ],
  size: [
    // Already built and, until now, unreachable: retiring the Summary layer
    // took PositionSizeChart with it, and the correlation it computes is
    // exactly this stage's question. Surfaced rather than rebuilt.
    { key: 'size-vs-r', label: 'Size vs R' },
    { key: 'sizing', label: 'Sizing' },
  ],
  hold: [
    // First, because it is the question the verdict raises and the only one
    // here that tests an assumption rather than reporting a number.
    { key: 'hold-capture', label: 'Hold & capture' },
    { key: 'trim-stops', label: 'Trim & Stops' },
    // Was labelled "Risk Management", which named the file rather than what it
    // does: it re-runs the book against a different stop. That is a question
    // about holding, not about when to stop trading.
    { key: 'stop-sim', label: 'Stop Simulator' },
    { key: 'volatility', label: 'Volatility' },
  ],
  stop: [
    // First, because "when do I step away" is the stage's question and this is
    // the only section here that tests an answer to it.
    { key: 'after-loss', label: 'After a loss' },
    // Sharpe, Sortino, max drawdown — arrived from the Portfolio page. How much
    // damage this way of trading takes before it pays.
    { key: 'risk-adjusted', label: 'Risk-adjusted' },
    { key: 'demon-finder', label: 'Demon Finder' },
    { key: 'behavior', label: 'Behavior' },
    { key: 'diagnosis', label: 'Diagnosis' },
  ],
}

/** Sections that live inside AnalyticsTab and are reached by its own key. */
const ANALYTICS_KEYS = new Set(['trim-stops', 'volatility', 'demon-finder', 'behavior',
                                'diagnosis', 'risk-adjusted', 'size-vs-r'])

export default function JournalPage() {
  const { t } = useLanguage()
  const [stage, setStage] = useState('hold')
  const [section, setSection] = useState(SECTIONS.hold[0].key)

  const pickStage = (key) => {
    setStage(key)
    setSection(SECTIONS[key][0].key)
  }

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      <PageHeader group="book" title={t('nav.journal')} />

      <HeadCoach onGo={pickStage} />

      {/* Andy's own words about the same period the verdict above is about.
          Retiring the Summary layer took this with it — it holds a textarea
          writing into monthlyReviews, so the restructure made his own writing
          unreachable. Nothing was lost (the portfolio still persists and syncs
          it), but an entrance that disappears is how writing gets abandoned.
          It sits with the head coach rather than inside a stage because it is
          about the period, not about one part of a trade. */}
      <details className="mb-5">
        <summary className="text-[11px] font-mono uppercase tracking-[.18em]
                            text-[var(--color-text-muted)] cursor-pointer list-none
                            hover:text-[var(--color-text)]">
          {t('rev.monthly')} +
        </summary>
        <div className="mt-3">
          <AnalyticsTab initialSection="monthly-review" />
        </div>
      </details>

      {/* The four stages, in the order a trade lives through them. */}
      <div className="flex gap-1 mb-3 flex-wrap">
        {STAGES.map(({ key }) => (
          <button
            key={key}
            onClick={() => pickStage(key)}
            title={t(`rev.asks.${key}`)}
            className={`px-3 py-1.5 text-[12px] font-medium rounded cursor-pointer transition-colors ${
              stage === key
                ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'
            }`}
          >
            {t(`rev.stage.${key}`)}
          </button>
        ))}
      </div>

      {/* What that stage asks, spelled out — four one-character labels are only
          legible to whoever wrote them. */}
      <p className="text-[11.5px] text-[var(--color-text-muted)] m-0 mb-3">
        {t(`rev.asks.${stage}`)}
      </p>

      <div className="flex gap-1 mb-5 flex-wrap">
        {SECTIONS[stage].map(({ key }) => (
          <button
            key={key}
            onClick={() => setSection(key)}
            className={`px-2.5 py-1 text-[11px] rounded cursor-pointer transition-colors ${
              section === key
                ? 'text-[var(--color-text)] font-semibold bg-[var(--color-hover-bg)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            {t(`rev.sec.${key}`)}
          </button>
        ))}
      </div>

      {section === 'hold-capture' ? (
        <HoldCaptureSection />
      ) : section === 'after-loss' ? (
        <AfterLossSection />
      ) : section === 'setup-edge' ? (
        <SetupEdgeSection />
      ) : section === 'sizing' ? (
        <SizingTab />
      ) : section === 'stop-sim' ? (
        <RiskTab />
      ) : ANALYTICS_KEYS.has(section) ? (
        <AnalyticsTab initialSection={section} key={section} />
      ) : (
        <CoachTab strategy={section} />
      )}
    </div>
  )
}
