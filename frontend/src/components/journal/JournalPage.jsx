import { useState } from 'react'
import AnalyticsTab from './AnalyticsTab'
import CoachTab from './CoachTab'
import RiskTab from './RiskTab'
import SizingTab from './SizingTab'
import PageHeader from '../PageHeader'
import { useLanguage } from '../../i18n/LanguageContext'
import StageCard from './StageCard'
import { useTradeJournal } from '../../hooks/useTradeJournal'
import { stageLeaks, STAGES } from './lib/headCoach'
import HoldCaptureSection from './analytics/HoldCaptureSection'
import AfterLossSection from './analytics/AfterLossSection'
import SetupEdgeSection from './analytics/SetupEdgeSection'


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

export default function JournalPage({ stage: routeStage }) {
  const { t } = useLanguage()
  const { trades } = useTradeJournal()
  const [section, setSection] = useState(null)

  const go = (key) => { window.location.hash = key ? `#/review/${key}` : '#/review' }

  // The stage the ranking points at. It decides which card wears the flag —
  // and that flag, plus the four readings beside it, is the whole verdict.
  // The sentence that used to sit above them said the same thing again.
  const lead = stageLeaks(trades)[0]?.stage

  // ── Overview ───────────────────────────────────────────────────────────
  if (!routeStage || !SECTIONS[routeStage]) {
    return (
      <div className="max-w-5xl mx-auto py-6 px-4">
        <PageHeader group="book" title={t('nav.journal')} />
        <p className="text-[13px] text-[var(--color-text-secondary)] mt-1 mb-5 max-w-[62ch]">
          {t('rev.overview.lede')}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {STAGES.map(({ key }) => (
            <StageCard key={key} stageKey={key} trades={trades}
                       lead={key === lead} onOpen={go} />
          ))}
        </div>

        {/* Andy's own words about the period. Not inside a stage — it is about
            all four — and its own entrance, per his call. */}
        <details className="mt-6">
          <summary className="text-[11px] font-mono uppercase tracking-[.18em]
                              text-[var(--color-text-muted)] cursor-pointer list-none
                              hover:text-[var(--color-text)]">{t('rev.monthly')} +</summary>
          <div className="mt-3"><AnalyticsTab initialSection="monthly-review" /></div>
        </details>

        <p className="text-[11px] text-[var(--color-text-muted)] mt-5 max-w-[70ch]">
          {t('rev.report.hint')}
        </p>
        <code className="inline-block mt-1.5 text-[10.5px] font-mono
                         text-[var(--color-text-secondary)]
                         bg-[var(--color-hover-bg)] rounded px-2 py-1">
          {t('rev.report.cmd')}
        </code>
      </div>
    )
  }

  // ── One stage ──────────────────────────────────────────────────────────
  const list = SECTIONS[routeStage]
  const active = section && list.some((x) => x.key === section) ? section : list[0].key

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      <button type="button" onClick={() => go(null)}
              className="text-[11px] font-mono text-[var(--color-text-muted)] bg-transparent
                         border-none p-0 cursor-pointer hover:text-[var(--color-text)]">
        ‹ {t('nav.journal')}
      </button>
      <h1 className="text-[34px] font-bold leading-tight mt-1 mb-0.5">
        {t(`rev.stage.${routeStage}`)}
      </h1>
      <p className="text-[12.5px] text-[var(--color-text-muted)] m-0 mb-5">
        {t(`rev.asks.${routeStage}`)}
      </p>

      {list.length > 1 && (
        <div className="flex gap-1 mb-5 flex-wrap">
          {list.map(({ key }) => (
            <button key={key} onClick={() => setSection(key)}
              className={`px-2.5 py-1 text-[11px] rounded cursor-pointer transition-colors ${
                active === key
                  ? 'text-[var(--color-text)] font-semibold bg-[var(--color-hover-bg)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'}`}>
              {t(`rev.sec.${key}`)}
            </button>
          ))}
        </div>
      )}

      {active === 'hold-capture' ? <HoldCaptureSection />
        : active === 'after-loss' ? <AfterLossSection />
        : active === 'setup-edge' ? <SetupEdgeSection />
        : active === 'sizing' ? <SizingTab />
        : active === 'stop-sim' ? <RiskTab />
        : ANALYTICS_KEYS.has(active) ? <AnalyticsTab initialSection={active} key={active} />
        : <CoachTab strategy={active} />}
    </div>
  )
}
